# High FPS Exploration - IMX296 Global Shutter Camera

## Research Summary

Investigation into achieving maximum frame rates with the Raspberry Pi Global Shutter Camera (IMX296 sensor), including exploration of 800+ fps claims and raw frame capture alternatives.

## Maximum Achievable Frame Rates

### Verified Achievements
- **571 fps @ 96x88** - Smallest usable crop, Pi5, C++ libcamera (May 2024)
- **536 fps @ 128x96** - Well-documented, reliable, zero frameskips
- **536 fps @ 320x96** - Wider aspect ratio, sustained 5-second recordings
- **402 fps @ 688x136** - Current configuration in this project

### Sensor Specifications
- **Full resolution**: 1456×1088 @ 60 fps (official spec)
- **Sensor**: Sony IMX296LQR global shutter CMOS
- **Interface**: MIPI CSI-2 (1-lane) - **key bandwidth bottleneck**
- **Pixel size**: 3.45 × 3.45 µm
- **Bit depth**: 10-bit

## The 900 FPS Claim Investigation

**Conclusion**: No verified reports of 800+ or 900+ fps found in:
- Raspberry Pi forums (2023-2025)
- Hermann-SW's extensive GS camera documentation
- Sony IMX296 datasheets
- Picamera2 GitHub discussions

**Most likely explanations for the claim**:
1. Different sensor (IMX477 HQ camera had different experiments reaching 1000 fps at 640×80)
2. Raw sensor readout mode (theoretical, not sustained recording)
3. Misremembering/exaggeration
4. Theoretical calculation from libcamera (sensor reports capabilities ignoring pipeline bottlenecks)

## GScrop Tool - How High FPS is Achieved

### What is GScrop?

A bash script that configures extreme frame rates by manipulating sensor crop settings using low-level media-ctl commands.

**GitHub**: https://gist.github.com/Hermann-SW/e6049fe1a24fc2b5a53c654e0e9f6b9c

### How It Works

1. **Sensor Cropping via media-ctl**: Configures a centered crop region on the sensor
   ```bash
   media-ctl -d /dev/media0 --set-v4l2 "'imx296 10-001a':0 \
     [fmt:SBGGR10_1X10/128x96 crop:(656,496)/128x96]"
   ```

2. **Frame Rate Math**: Smaller crop = fewer pixels to read = faster readout = higher FPS
   - Relationship is roughly linear within sensor limits
   - Halve the pixels, approximately double the FPS

3. **Timestamp Analysis**: Post-recording validation of actual achieved frame rates
   - Detects frame skips
   - Confirms sustained vs theoretical rates

### Usage
```bash
./GScrop width height framerate ms [us]
# Example: 128x96 @ 536 fps for 5000ms with 500µs shutter
./GScrop 128 96 536 5000 500
```

### Constraints
- Width and height **must be even numbers** (hardware requirement)
- Crop is centered on sensor
- Requires Pi5 for best performance
- `--no-raw` flag needed on Bookworm OS

## Why You Can't Just Keep Going Faster

### Hardware Bottlenecks (in order of impact)

1. **MIPI CSI-2 Interface Bandwidth**
   - Single-lane interface: ~125 MB/s per lane
   - Finite data throughput regardless of sensor capability
   - **Primary limiting factor**

2. **Sensor Readout Architecture**
   - Even global shutter has minimum time per row
   - Physical electron transfer limits
   - Charge storage node read speed

3. **Raspberry Pi Processing Pipeline**
   - ISP (Image Signal Processor) throughput
   - H.264 encoder bandwidth
   - Memory bandwidth (especially on Pi4)

4. **Storage/Recording**
   - RAM buffer fills quickly at high FPS
   - Disk write speed for sustained recording

### Practical Ceiling: 536-571 FPS

This represents the achievable maximum with current Raspberry Pi hardware, whether using:
- H.264 encoded video (what we use)
- Raw frame capture (see below)
- Different recording formats

**Note**: H.264 encoding is NOT the bottleneck - gscrop achieves 536 fps WITH encoding.

## Raw Frame Capture Alternative

### Concept

Instead of encoding to H.264 video during capture, capture raw frames directly to memory buffers, then process afterwards.

### Implementation Approach

Using Picamera2's `capture_array()` or circular buffer:

```python
from picamera2 import Picamera2
import numpy as np

picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (320, 96), "format": "RGB888"},
    controls={"FrameRate": 536}
)
picam2.configure(config)
picam2.start()

# Capture burst to RAM
frames = []
duration_sec = 0.5
num_frames = int(536 * duration_sec)  # ~268 frames

for i in range(num_frames):
    frame = picam2.capture_array()
    frames.append(frame)

# Post-process: save as images or encode to video
for i, frame in enumerate(frames):
    cv2.imwrite(f"frame_{i:04d}.png", frame)
```

### Advantages for Golf Impact Camera

1. **Individual frame access** - Pick exact impact frame
2. **No compression artifacts** - Better for analysis/zooming
3. **Post-processing flexibility**:
   - Adjust exposure after capture
   - Create composite images
   - Select specific frames for analysis
   - Different encoding options (H.264, H.265, ProRes, etc.)

4. **Manageable storage for short bursts**:
   - 536 fps × 0.5 sec = 268 frames
   - At 128×96×1 byte = ~3.1 MB total
   - At 320×96×1 byte = ~7.8 MB total
   - At 688×136×1 byte = ~24 MB total

### Disadvantages

1. **More complex implementation**
   - Requires careful buffer management
   - Memory constraints for longer captures
   - Post-processing step required

2. **No immediate video preview**
   - Can't watch the video right after capture
   - Need encoding step before playback

3. **Frame rate limitations remain**
   - Still limited by MIPI/sensor bandwidth
   - Won't achieve higher FPS than H.264 recording

4. **Memory constraints**:
   - Pi5: 4-8 GB RAM
   - 1 second @ 536fps @ 320×96×3 bytes = ~46 MB
   - 2 seconds = ~92 MB (feasible)
   - 5 seconds = ~230 MB (still feasible)
   - Beyond that, circular buffer or streaming to disk required

### Implementation Complexity: Medium-High

**Required changes**:
1. Add new recording mode to `camera_backends.py`
2. Implement circular buffer or fixed-size burst capture
3. Create post-processing pipeline:
   - Frame extraction
   - Video encoding (FFmpeg or similar)
   - Metadata generation
4. Update web interface for two-step workflow:
   - Step 1: Capture burst
   - Step 2: Preview frames, select range, encode
5. Storage management for raw frames vs encoded video

**Estimated effort**: 1-2 days development + testing

## Integration with Picamera2

### Method 1: Burst Capture with capture_array()

```python
class RawBurstBackend(CameraBackend):
    def record(self, output_path, config):
        """Capture burst of raw frames to memory"""
        frames = []
        fps = config['fps']
        duration = config['duration']
        num_frames = int(fps * duration)

        # Configure high-speed mode
        video_config = self.picam2.create_video_configuration(
            main={"size": (config['width'], config['height'])},
            controls={"FrameRate": fps}
        )
        self.picam2.configure(video_config)
        self.picam2.start()

        # Capture burst
        for i in range(num_frames):
            frame = self.picam2.capture_array()
            frames.append(frame)

        # Save frames as numpy array
        np.save(output_path.replace('.h264', '.npy'), frames)
        return output_path
```

### Method 2: Circular Buffer (for longer recordings)

```python
from picamera2.outputs import CircularOutput

# Create circular buffer (last 2 seconds @ 536fps)
output = CircularOutput(buffersize=536*2)
encoder = H264Encoder()

# Start recording to circular buffer
picam2.start_recording(encoder, output)

# On trigger, save buffer + following seconds
output.fileoutput = "triggered_event.h264"
output.start()
time.sleep(1)  # Record 1 more second
picam2.stop_recording()
```

## Recommendations

### For Current Golf Swing Application

**Stick with H.264 encoding at 400-536 fps**:
- ✅ Proven reliable
- ✅ Immediate video playback
- ✅ Good balance of speed vs field of view
- ✅ Already implemented
- ✅ Sufficient for golf ball tracking

### When Raw Capture Makes Sense

Consider raw burst capture if:
- Need **exact impact frame** identification
- Require **frame-by-frame analysis** (ball spin, club face angle)
- Want **highest quality** for zooming/enhancement
- Can tolerate **two-step workflow** (capture → process)
- Only need **short bursts** (0.5-2 seconds)

### Experimental Presets to Add

1. **Ultra High Speed - 571 FPS** (96×88)
   - Smallest usable crop
   - Maximum verified frame rate
   - Very narrow field of view (close-up only)

2. **High Speed Burst - 536 FPS** (128×96)
   - Well-tested reliable configuration
   - Zero frameskips documented
   - Wider than 96×88, still very fast

3. **Wide High Speed - 536 FPS** (320×96)
   - Panoramic aspect ratio
   - Good for tracking ball flight
   - Proven on Pi5 for 5-second recordings

## Next Steps

### If Implementing Raw Capture:

1. **Prototype burst capture mode**
   - Test memory limits on Pi5
   - Measure actual achievable fps
   - Validate frame timing accuracy

2. **Create processing pipeline**
   - Frame extraction tools
   - FFmpeg encoding scripts
   - Quality comparison tests

3. **UI/UX design**
   - Two-step workflow
   - Frame browser/selector
   - Encoding options interface

4. **Testing**
   - Actual golf swing captures
   - Storage requirements
   - Processing time benchmarks

### If Sticking with H.264:

1. **Add extreme FPS presets** (571, 536 fps modes)
2. **Test field of view** at small crops
3. **Optimize for your specific use case** (club impact vs ball flight)

## References

- GScrop tool: https://gist.github.com/Hermann-SW/e6049fe1a24fc2b5a53c654e0e9f6b9c
- Hermann-SW GS camera documentation: https://stamm-wilbrandt.de/GS/
- Raspberry Pi Forums - High frame rates discussion: https://forums.raspberrypi.com/viewtopic.php?t=363481
- Picamera2 manual: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf

## Date

Research conducted: 2025-11-03
