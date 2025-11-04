"""
Camera backend abstraction layer.
Supports multiple camera systems with graceful degradation:
1. Picamera2 with global shutter (Raspberry Pi - best quality)
2. OpenCV/AVFoundation (Mac/generic - good for testing)
3. Demo mode (no camera - UI testing only)
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class CameraBackend(ABC):
    """Abstract base class for camera backends."""
    
    @abstractmethod
    def setup(self, config):
        """Configure camera with given settings."""
        pass
    
    @abstractmethod
    def start(self):
        """Start the camera."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the camera."""
        pass
    
    @abstractmethod
    def record(self, output_path, duration, cancel_event=None):
        """Record video to output_path for duration seconds.

        Args:
            output_path: Path to save the recording
            duration: Maximum recording duration in seconds
            cancel_event: Optional threading.Event to allow early cancellation
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up camera resources."""
        pass
    
    @abstractmethod
    def get_name(self):
        """Get backend name for logging."""
        pass


class PiCamera2Backend(CameraBackend):
    """High-performance Raspberry Pi camera with global shutter support."""

    def __init__(self):
        from picamera2 import Picamera2
        from picamera2.encoders import H264Encoder
        from picamera2.outputs import FfmpegOutput
        import libcamera

        self.Picamera2 = Picamera2
        self.H264Encoder = H264Encoder
        self.FfmpegOutput = FfmpegOutput
        self.libcamera = libcamera
        self.camera = None
        self.config = None

    def _apply_sensor_crop(self, width, height):
        """Apply sensor-level cropping via media-ctl to unlock high FPS modes.

        The IMX296 sensor can achieve 120+ FPS when using smaller sensor crop sizes.
        This must be applied BEFORE initializing PiCamera2.

        Args:
            width: Crop width (will be rounded to even number)
            height: Crop height (will be rounded to even number)

        Returns:
            True if crop applied successfully, False otherwise
        """
        import subprocess

        # Ensure dimensions are even (Pi 5 requirement)
        width = width + (width % 2)
        height = height + (height % 2)

        # IMX296 sensor recommended recording area (not full 1456x1088)
        # Sony specs: 1440x1088 is recommended recording pixels
        # This matches GScrop implementation for proven 500+ FPS performance
        SENSOR_WIDTH = 1440
        SENSOR_HEIGHT = 1088

        # Calculate centered crop offset
        crop_x = (SENSOR_WIDTH - width) // 2
        crop_y = (SENSOR_HEIGHT - height) // 2

        # Ensure offsets are even numbers
        crop_x = crop_x - (crop_x % 2)
        crop_y = crop_y - (crop_y % 2)

        # Try all media device numbers (0-5) and I2C addresses
        # Scan order matches GScrop: 0->1->2->3->4->5
        for media_num in range(6):  # /dev/media0 through /dev/media5
            for camera_addr in ['11-001a', '10-001a']:  # Try both I2C addresses
                crop_cmd = f"'imx296 {camera_addr}':0 [fmt:SBGGR10_1X10/{width}x{height} crop:({crop_x},{crop_y})/{width}x{height}]"

                try:
                    result = subprocess.run(
                        ['media-ctl', '-d', f'/dev/media{media_num}', '--set-v4l2', crop_cmd, '-v'],
                        capture_output=True,
                        text=True,
                        timeout=3
                    )

                    if result.returncode == 0:
                        logger.info(f"Sensor crop applied: {width}x{height} centered at ({crop_x},{crop_y}) (media{media_num}, {camera_addr})")
                        return True

                except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                    continue

        logger.warning(f"Could not apply sensor crop {width}x{height}")
        return False

    def setup(self, config):
        """Configure Pi camera with optimal settings for high-speed capture."""
        self.config = config

        # Close existing camera if reconfiguring
        if self.camera:
            if self.camera.started:
                self.camera.stop()
            self.camera.close()
            self.camera = None

        # Always apply sensor crop BEFORE initializing camera
        # This ensures the sensor is properly configured for the target resolution
        # For high FPS (>60), smaller crops unlock 120-500+ FPS
        # For full resolution modes, this resets the sensor to full size
        if not self._apply_sensor_crop(config['width'], config['height']):
            logger.warning(f"Sensor crop failed for {config['width']}x{config['height']}")
            if config['fps'] > 60:
                logger.warning("Will be limited to ~60 FPS")

        # Initialize camera and configure
        self.camera = self.Picamera2()

        # Create video configuration
        # Note: FrameDurationLimits set in start() method, not here
        # Support indoor/outdoor modes via config
        controls = {
            "NoiseReductionMode": self.libcamera.controls.draft.NoiseReductionModeEnum.Off,
        }

        # Auto-exposure mode (indoor friendly)
        if config.get('auto_exposure', False):
            controls["AeEnable"] = True
            controls["AwbEnable"] = True  # Auto white balance with auto exposure
            # Set exposure limits to avoid too slow shutter
            controls["AeExposureMode"] = self.libcamera.controls.AeExposureModeEnum.Normal
        else:
            # Manual exposure mode (outdoor/high-speed capture)
            controls["ExposureTime"] = config['shutter_speed']
            controls["AnalogueGain"] = config.get('analogue_gain', 1.0)
            controls["AeEnable"] = False
            controls["AwbEnable"] = False

        video_config = self.camera.create_video_configuration(
            main={
                "size": (config['width'], config['height']),
                "format": "YUV420"
            },
            controls=controls,
            buffer_count=15
        )

        # For high FPS with sensor crop, disable raw stream which doesn't match crop size
        # PiCamera2 auto-creates a raw stream at full sensor size, causing mismatch
        if config['fps'] > 60 and 'raw' in video_config:
            logger.info(f"Disabling raw stream for high-FPS mode (sensor cropped to {config['width']}x{config['height']})")
            video_config['raw'] = None

        self.camera.configure(video_config)

        # Query and log actual achieved FPS
        try:
            controls = self.camera.camera_controls
            if 'FrameDurationLimits' in controls:
                frame_duration_min = controls['FrameDurationLimits'][0]
                actual_fps = round(1_000_000 / frame_duration_min, 2)
                logger.info(f"Camera configured: {config['width']}x{config['height']} @ {actual_fps} FPS")
            else:
                logger.info(f"Camera configured: {config['width']}x{config['height']} @ {config['fps']} FPS (requested)")
        except Exception:
            logger.info(f"Camera configured: {config['width']}x{config['height']} @ {config['fps']} FPS (requested)")
    
    def start(self):
        """Start Pi camera."""
        if self.camera and not self.camera.started:
            self.camera.start()

            # Set frame duration as runtime control AFTER starting
            # This is more reliable than setting in configuration
            frame_duration_us = int(1_000_000 / self.config['fps'])
            controls_to_set = {
                "FrameDurationLimits": (frame_duration_us, frame_duration_us)
            }

            # Also re-apply exposure time if in manual mode (not auto-exposure)
            # This ensures the shutter speed actually takes effect
            if not self.config.get('auto_exposure', False):
                controls_to_set["ExposureTime"] = self.config['shutter_speed']
                controls_to_set["AeEnable"] = False

            self.camera.set_controls(controls_to_set)
            logger.info(f"Set FrameDurationLimits: {frame_duration_us}us ({self.config['fps']} FPS)")
            if not self.config.get('auto_exposure', False):
                logger.info(f"Set ExposureTime: {self.config['shutter_speed']}us")

            time.sleep(0.5)
            logger.info("PiCamera2 started")
    
    def stop(self):
        """Stop Pi camera."""
        if self.camera and self.camera.started:
            self.camera.stop()
            logger.info("PiCamera2 stopped")
    
    def record(self, output_path, duration, cancel_event=None):
        """Record with Pi camera using hardware encoding."""
        # Convert h264 to mp4 for browser compatibility
        output_str = str(output_path)
        if output_str.endswith('.h264'):
            output_str = output_str[:-5] + '.mp4'

        # Log actual FPS settings before recording
        target_fps = self.config.get('fps', 120)
        frame_duration_us = int(1_000_000 / target_fps)
        logger.info(f"Starting recording at {target_fps} FPS (frame duration: {frame_duration_us}us)")
        logger.info(f"Resolution: {self.config['width']}x{self.config['height']}, Format: YUV420 (full color)")

        # Re-apply camera controls before recording to ensure they stick
        # PiCamera2 may reset controls when starting a recording
        controls_to_set = {
            "FrameDurationLimits": (frame_duration_us, frame_duration_us)
        }
        if not self.config.get('auto_exposure', False):
            controls_to_set["ExposureTime"] = self.config['shutter_speed']
            controls_to_set["AeEnable"] = False
            logger.info(f"Setting recording exposure: {self.config['shutter_speed']}µs (1/{int(1000000/self.config['shutter_speed'])}s)")

        self.camera.set_controls(controls_to_set)

        # Always use FfmpegOutput for MP4 container (browser-compatible)
        encoder = self.H264Encoder(bitrate=10000000)
        output = self.FfmpegOutput(output_str)
        self.camera.start_recording(encoder, output)

        # Sleep with cancel event checking
        start_time = time.time()
        while (time.time() - start_time) < duration:
            if cancel_event and cancel_event.is_set():
                elapsed = time.time() - start_time
                logger.info(f"Recording cancelled after {elapsed:.1f}s (shot detected)")
                break
            time.sleep(0.1)  # Check every 100ms

        self.camera.stop_recording()

        logger.info(f"Recorded at {self.config.get('fps', 120)}fps - all frames preserved")
        return output_str
    
    def cleanup(self):
        """Clean up Pi camera."""
        if self.camera:
            if self.camera.started:
                self.camera.stop()
            self.camera.close()
    
    def get_name(self):
        return "PiCamera2 (Global Shutter)"


class OpenCVBackend(CameraBackend):
    """Generic camera support via OpenCV (Mac, USB cameras, etc)."""
    
    def __init__(self):
        import cv2
        self.cv2 = cv2
        self.camera = None
        self.config = None
        self.writer = None
    
    def setup(self, config):
        """Configure OpenCV camera (limited settings vs Pi)."""
        self.config = config
        self.camera = self.cv2.VideoCapture(0)
        
        self.camera.set(self.cv2.CAP_PROP_FRAME_WIDTH, config['width'])
        self.camera.set(self.cv2.CAP_PROP_FRAME_HEIGHT, config['height'])
        self.camera.set(self.cv2.CAP_PROP_FPS, config['fps'])
        
        actual_width = int(self.camera.get(self.cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.camera.get(self.cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.camera.get(self.cv2.CAP_PROP_FPS))
        
        logger.info(f"OpenCV camera configured: {actual_width}x{actual_height} @ {actual_fps}fps")
        logger.warning("Note: OpenCV backend has limited control vs Pi camera")
        logger.warning("Global shutter, fast exposure, and manual controls not available")
    
    def start(self):
        """Start OpenCV camera."""
        if self.camera and not self.camera.isOpened():
            self.camera.open(0)
        logger.info("OpenCV camera started")
    
    def stop(self):
        """Stop OpenCV camera."""
        if self.writer:
            self.writer.release()
            self.writer = None
        logger.info("OpenCV camera stopped")
    
    def record(self, output_path, duration, cancel_event=None):
        """Record with OpenCV (software encoding)."""
        # Use H.264 codec for browser compatibility
        # Try different codec options in order of preference
        width = int(self.camera.get(self.cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera.get(self.cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.config.get('fps', 30)

        output_str = str(output_path)
        if output_str.endswith('.h264'):
            output_str = output_str[:-5] + '.mp4'

        # Try H.264 codecs in order of availability
        codecs = ['avc1', 'H264', 'h264', 'X264', 'mp4v']
        self.writer = None

        for codec in codecs:
            try:
                fourcc = self.cv2.VideoWriter_fourcc(*codec)
                self.writer = self.cv2.VideoWriter(
                    output_str,
                    fourcc,
                    fps,
                    (width, height)
                )
                if self.writer.isOpened():
                    logger.info(f"Using codec: {codec}")
                    break
                else:
                    self.writer.release()
                    self.writer = None
            except:
                pass

        if not self.writer or not self.writer.isOpened():
            # Fallback to default
            fourcc = self.cv2.VideoWriter_fourcc(*'mp4v')
            self.writer = self.cv2.VideoWriter(
                output_str,
                fourcc,
                fps,
                (width, height)
            )
            logger.warning("Using mp4v codec - may not play in all browsers")

        start_time = time.time()
        frame_count = 0

        while (time.time() - start_time) < duration:
            # Check for cancellation
            if cancel_event and cancel_event.is_set():
                elapsed = time.time() - start_time
                logger.info(f"Recording cancelled after {elapsed:.1f}s (shot detected)")
                break

            ret, frame = self.camera.read()
            if ret:
                self.writer.write(frame)
                frame_count += 1
            else:
                logger.warning("Failed to read frame")
                break

        self.writer.release()
        self.writer = None

        logger.info(f"Recorded {frame_count} frames in {duration}s at {fps}fps - preserving all frames")

        return output_str
    
    def cleanup(self):
        """Clean up OpenCV camera."""
        if self.writer:
            self.writer.release()
        if self.camera:
            self.camera.release()
    
    def get_name(self):
        return "OpenCV (Generic Camera)"


class DemoBackend(CameraBackend):
    """Demo backend for UI testing without camera hardware."""

    def __init__(self):
        self.config = None
        self.has_cv2 = False
        try:
            import cv2
            self.cv2 = cv2
            self.has_cv2 = True
        except ImportError:
            pass
    
    def setup(self, config):
        """Simulate camera setup."""
        self.config = config
        logger.info(f"Demo camera configured: {config['width']}x{config['height']} @ {config['fps']}fps")
    
    def start(self):
        """Simulate camera start."""
        logger.info("Demo camera started (simulated)")
    
    def stop(self):
        """Simulate camera stop."""
        logger.info("Demo camera stopped (simulated)")
    
    def record(self, output_path, duration, cancel_event=None):
        """Simulate recording by creating a demo video file."""
        logger.info(f"Demo recording for {duration}s (simulated)")

        # Convert h264 to mp4 for web browser compatibility
        output_str = str(output_path)
        if output_str.endswith('.h264'):
            output_str = output_str[:-5] + '.mp4'

        if self.has_cv2:
            # Create a real video file with cv2
            width = self.config.get('width', 1456)
            height = self.config.get('height', 1088)
            fps = self.config.get('fps', 120)

            # Try to create a video writer
            fourcc = self.cv2.VideoWriter_fourcc(*'mp4v')
            writer = self.cv2.VideoWriter(output_str, fourcc, fps, (width, height))

            if writer.isOpened():
                import numpy as np

                # Generate demo frames with animation
                num_frames = int(fps * duration)
                for i in range(num_frames):
                    # Create a gradient background
                    frame = np.zeros((height, width, 3), dtype=np.uint8)

                    # Animated moving circle
                    center_x = int(width * (0.2 + 0.6 * (i / num_frames)))
                    center_y = height // 2
                    radius = min(width, height) // 8

                    self.cv2.circle(frame, (center_x, center_y), radius, (0, 255, 0), -1)

                    # Add text overlay
                    text = f"DEMO MODE - Frame {i+1}/{num_frames}"
                    font = self.cv2.FONT_HERSHEY_SIMPLEX
                    text_size = self.cv2.getTextSize(text, font, 1, 2)[0]
                    text_x = (width - text_size[0]) // 2
                    text_y = 50
                    self.cv2.putText(frame, text, (text_x, text_y), font, 1, (255, 255, 255), 2)

                    writer.write(frame)

                writer.release()
                logger.info(f"Created demo video with {num_frames} frames at {fps}fps")
                return output_str

        # Fallback: create a minimal dummy file
        time.sleep(duration)
        with open(output_str, 'wb') as f:
            f.write(b'DEMO VIDEO FILE - Generated in demo mode\n')
            f.write(f'Would have recorded: {self.config["width"]}x{self.config["height"]} @ {self.config["fps"]}fps\n'.encode())
            f.write(f'Duration: {duration}s\n'.encode())

        logger.warning("Demo mode: cv2 not available, created placeholder file")
        return output_str
    
    def cleanup(self):
        """Simulate cleanup."""
        logger.info("Demo camera cleaned up (simulated)")
    
    def get_name(self):
        return "Demo Mode (No Camera)"


def create_camera_backend(force_demo=False):
    """
    Factory function to create the best available camera backend.
    
    Priority:
    1. PiCamera2 with global shutter (Raspberry Pi)
    2. OpenCV (Mac/generic USB camera)
    3. Demo mode (no camera)
    
    Args:
        force_demo: Force demo mode even if cameras are available
        
    Returns:
        CameraBackend instance
    """
    if force_demo:
        logger.info("Demo mode forced")
        return DemoBackend()
    
    try:
        logger.info("Attempting to initialize PiCamera2...")
        backend = PiCamera2Backend()
        logger.info("✓ PiCamera2 available - using global shutter camera")
        return backend
    except ImportError:
        logger.info("PiCamera2 not available (expected on non-Pi systems)")
    except Exception as e:
        logger.warning(f"PiCamera2 initialization failed: {e}")
    
    try:
        logger.info("Attempting to initialize OpenCV camera...")
        import cv2
        test_cam = cv2.VideoCapture(0)
        if test_cam.isOpened():
            test_cam.release()
            backend = OpenCVBackend()
            logger.info("✓ OpenCV camera available - using generic camera")
            return backend
        else:
            logger.info("No OpenCV camera detected")
            test_cam.release()
    except ImportError:
        logger.info("OpenCV not available")
    except Exception as e:
        logger.warning(f"OpenCV initialization failed: {e}")
    
    logger.info("No camera hardware detected - using demo mode")
    return DemoBackend()

