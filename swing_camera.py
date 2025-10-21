#!/usr/bin/env python3
"""
High-performance golf swing capture system for Raspberry Pi 5 with global shutter camera.
Optimized for capturing fast motion with minimal artifacts.
"""

import os
import time
import json
import pickle
from datetime import datetime
from pathlib import Path
from threading import Thread, Event
import logging
from enum import Enum

from camera_backends import create_camera_backend


class LMState(Enum):
    """Launch Monitor state machine."""
    IDLE = "idle"
    ARMED = "armed"
    PROCESSING = "processing"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SwingCamera:
    """High-performance golf swing camera with multi-backend support."""
    
    def __init__(self, config_path='config.json', demo_mode=False):
        """Initialize the swing camera with configuration."""
        self.config = self._load_config(config_path)
        self.backend = create_camera_backend(force_demo=demo_mode)
        self.recording = False
        self.recording_event = Event()
        self.output_dir = Path(self.config['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Launch monitor state
        self.lm_state = LMState.IDLE
        self.lm_recording_thread = None
        self.lm_temp_file = None
        self.lm_recording_start_time = None
        self.lm_cancel_event = Event()

        logger.info(f"Using camera backend: {self.backend.get_name()}")
        self._setup_camera()
    
    def _load_config(self, config_path):
        """Load configuration from JSON file."""
        default_config = {
            'width': 1456,
            'height': 1088,
            'fps': 120,
            'duration': 10,
            'output_dir': './recordings',
            'format': 'h264',
            'shutter_speed': 2000,
            'pre_record_buffer': 2,
            'upload_enabled': False,
            'upload_destination': '',
            'quality': 'high',
            'lm_max_recording_duration': 60
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _setup_camera(self):
        """Configure camera backend with settings."""
        try:
            self.backend.setup(self.config)
        except Exception as e:
            logger.error(f"Camera setup failed: {e}")
            raise
    
    def start(self):
        """Start the camera backend."""
        try:
            self.backend.start()
        except Exception as e:
            logger.error(f"Camera start failed: {e}")
            raise
    
    def stop(self):
        """Stop the camera backend."""
        try:
            self.backend.stop()
        except Exception as e:
            logger.error(f"Camera stop failed: {e}")
    
    def capture_swing(self, custom_name=None):
        """
        Capture a golf swing video.
        
        Args:
            custom_name: Optional custom name for the recording
            
        Returns:
            Path to the recorded file
        """
        if self.recording:
            logger.warning("Already recording!")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = custom_name if custom_name else f"swing_{timestamp}"
        
        if self.config['format'] == 'h264':
            output_path = self.output_dir / f"{filename}.h264"
        else:
            output_path = self.output_dir / f"{filename}.mp4"
        
        logger.info(f"Starting recording: {output_path}")
        
        try:
            self.recording = True
            self.recording_event.clear()
            
            actual_output_path = self.backend.record(output_path, self.config['duration'])
            # Convert to Path if backend returned a string
            if isinstance(actual_output_path, str):
                actual_output_path = Path(actual_output_path)
            
            self.recording = False
            self.recording_event.set()
            
            logger.info(f"Recording complete: {actual_output_path}")
            
            metadata = self._save_metadata(actual_output_path, timestamp)
            
            if self.config['upload_enabled']:
                self._upload_file(actual_output_path)
            
            return str(actual_output_path)
            
        except Exception as e:
            logger.error(f"Recording failed: {e}")
            self.recording = False
            self.recording_event.set()
            return None
    
    def _save_metadata(self, video_path, timestamp):
        """Save metadata about the recording."""
        metadata = {
            'timestamp': timestamp,
            'filename': os.path.basename(video_path),
            'resolution': f"{self.config['width']}x{self.config['height']}",
            'fps': self.config['fps'],
            'duration': self.config['duration'],
            'shutter_speed': self.config['shutter_speed'],
            'file_size': os.path.getsize(video_path)
        }
        
        metadata_path = video_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata
    
    def _upload_file(self, file_path):
        """Upload file to configured destination."""
        upload_thread = Thread(target=self._upload_worker, args=(file_path,))
        upload_thread.daemon = True
        upload_thread.start()
    
    def _upload_worker(self, file_path):
        """Background worker for uploading files."""
        try:
            destination = self.config['upload_destination']
            logger.info(f"Uploading {file_path} to {destination}")
            
            if destination.startswith('gdrive://'):
                self._upload_to_gdrive(file_path, destination)
            elif destination.startswith('rsync://') or ':' in destination:
                self._upload_via_rsync(file_path, destination)
            else:
                logger.warning(f"Unknown upload destination format: {destination}")
                
        except Exception as e:
            logger.error(f"Upload failed: {e}")
    
    def _upload_to_gdrive(self, file_path, gdrive_path):
        """Upload file to Google Drive."""
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import pickle
        
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        
        creds = None
        token_file = 'gdrive_token.pickle'
        
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('gdrive_credentials.json'):
                    logger.error("Google Drive credentials not found. Run setup_gdrive.py first.")
                    return
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'gdrive_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        service = build('drive', 'v3', credentials=creds)
        
        folder_id = gdrive_path.replace('gdrive://', '')
        
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id] if folder_id else []
        }
        
        media = MediaFileUpload(str(file_path), resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        logger.info(f"Upload complete: {file.get('name')} (ID: {file.get('id')})")
        logger.info(f"View at: {file.get('webViewLink')}")
        
        metadata_path = Path(file_path).with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['gdrive_file_id'] = file.get('id')
            metadata['gdrive_webview_link'] = file.get('webViewLink')
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            metadata_file = {
                'name': metadata_path.name,
                'parents': [folder_id] if folder_id else []
            }
            metadata_media = MediaFileUpload(str(metadata_path), resumable=True)
            metadata_result = service.files().create(
                body=metadata_file,
                media_body=metadata_media,
                fields='id'
            ).execute()
            
            metadata['gdrive_metadata_file_id'] = metadata_result.get('id')
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def _upload_via_rsync(self, file_path, destination):
        """Upload file via rsync."""
        import subprocess
        
        destination = destination.replace('rsync://', '')
        
        cmd = ['rsync', '-avz', '--progress', str(file_path), destination]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Rsync upload complete to {destination}")
            
            metadata_path = Path(file_path).with_suffix('.json')
            if metadata_path.exists():
                subprocess.run(['rsync', '-avz', str(metadata_path), destination])
        else:
            logger.error(f"Rsync failed: {result.stderr}")
    
    def get_recordings(self):
        """Get list of all recordings."""
        recordings = []
        for file in sorted(self.output_dir.glob('swing_*.*')):
            if file.suffix not in ['.h264', '.mp4']:
                continue
            
            metadata_file = file.with_suffix('.json')
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            
            recordings.append({
                'path': str(file),
                'name': file.name,
                'size': os.path.getsize(file),
                'created': os.path.getctime(file),
                'metadata': metadata
            })
        
        return recordings
    
    def delete_recording(self, filename):
        """Delete a recording and its metadata from local storage and Google Drive."""
        file_path = self.output_dir / filename
        metadata_path = file_path.with_suffix('.json')
        
        if not file_path.exists():
            raise FileNotFoundError(f"Recording {filename} not found")
        
        metadata = {}
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        gdrive_file_id = metadata.get('gdrive_file_id')
        gdrive_metadata_file_id = metadata.get('gdrive_metadata_file_id')
        
        if gdrive_file_id and self.config.get('upload_enabled'):
            try:
                self._delete_from_gdrive(gdrive_file_id)
                logger.info(f"Deleted {filename} from Google Drive")
            except Exception as e:
                logger.error(f"Failed to delete video from Google Drive: {e}")
        
        if gdrive_metadata_file_id and self.config.get('upload_enabled'):
            try:
                self._delete_from_gdrive(gdrive_metadata_file_id)
                logger.info(f"Deleted {filename} metadata from Google Drive")
            except Exception as e:
                logger.error(f"Failed to delete metadata from Google Drive: {e}")
        
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"Deleted local file: {filename}")
        
        if metadata_path.exists():
            os.remove(metadata_path)
            logger.info(f"Deleted metadata: {metadata_path.name}")
    
    def delete_all_recordings(self):
        """Delete all recordings."""
        count = 0
        for file in list(self.output_dir.glob('swing_*.*')):
            if file.suffix not in ['.h264', '.mp4', '.json']:
                continue
            
            if file.suffix == '.json':
                continue
            
            try:
                self.delete_recording(file.name)
                count += 1
            except Exception as e:
                logger.error(f"Failed to delete {file.name}: {e}")
        
        return count
    
    def _delete_from_gdrive(self, file_id):
        """Delete a file from Google Drive."""
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            
            token_file = 'gdrive_token.pickle'
            
            if not os.path.exists(token_file):
                logger.warning("No Google Drive credentials found, skipping Drive deletion")
                return
            
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
            
            service = build('drive', 'v3', credentials=creds)
            service.files().delete(fileId=file_id).execute()
            
        except Exception as e:
            logger.error(f"Failed to delete from Google Drive: {e}")
            raise
    
    def arm_launch_monitor(self):
        """
        Arm the launch monitor - start continuous recording until shot detected or timeout.

        Returns:
            dict: Status with state and max_duration
        """
        if self.lm_state != LMState.IDLE:
            logger.warning(f"Cannot arm: already in state {self.lm_state.value}")
            return {'status': 'error', 'message': f'Already {self.lm_state.value}'}

        if self.recording:
            logger.warning("Cannot arm: regular recording in progress")
            return {'status': 'error', 'message': 'Camera busy with regular recording'}

        # Create temp file for continuous recording
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.config['format'] == 'h264':
            self.lm_temp_file = self.output_dir / f"temp_lm_{timestamp}.h264"
        else:
            self.lm_temp_file = self.output_dir / f"temp_lm_{timestamp}.mp4"

        # Start continuous recording in background thread
        self.lm_state = LMState.ARMED
        self.lm_recording_start_time = time.time()
        self.lm_cancel_event.clear()

        self.lm_recording_thread = Thread(target=self._lm_continuous_record)
        self.lm_recording_thread.daemon = True
        self.lm_recording_thread.start()

        logger.info(f"Launch monitor armed, recording to {self.lm_temp_file}")
        return {
            'status': 'armed',
            'max_duration': self.config['lm_max_recording_duration']
        }

    def shot_detected(self):
        """
        Shot detected - stop recording and extract last N seconds.

        Returns:
            dict: Status with filename and path
        """
        if self.lm_state != LMState.ARMED:
            logger.warning(f"Cannot detect shot: not armed (state: {self.lm_state.value})")
            return {'status': 'error', 'message': f'Not armed (state: {self.lm_state.value})'}

        logger.info("Shot detected, stopping recording and extracting clip...")

        # Signal the recording thread to stop
        self.lm_state = LMState.PROCESSING
        self.lm_cancel_event.set()

        # Wait for recording to finish
        if self.lm_recording_thread:
            self.lm_recording_thread.join(timeout=5)

        try:
            # Extract last N seconds from temp file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"swing_{timestamp}"

            if self.config['format'] == 'h264':
                output_path = self.output_dir / f"{filename}.h264"
            else:
                output_path = self.output_dir / f"{filename}.mp4"

            # Use FFmpeg to extract last N seconds
            success = self._extract_clip(self.lm_temp_file, output_path, self.config['duration'])

            if success:
                # Save metadata
                metadata = self._save_metadata(output_path, timestamp)

                # Upload if enabled
                if self.config['upload_enabled']:
                    self._upload_file(output_path)

                logger.info(f"Clip extracted successfully: {output_path}")

                # Reset state
                self.lm_state = LMState.IDLE
                self.lm_temp_file = None
                self.lm_recording_start_time = None

                return {
                    'status': 'success',
                    'filename': output_path.name,
                    'path': str(output_path)
                }
            else:
                # Reset state even on failure
                self.lm_state = LMState.IDLE
                self.lm_temp_file = None
                self.lm_recording_start_time = None

                return {'status': 'error', 'message': 'Failed to extract clip'}

        except Exception as e:
            logger.error(f"Shot detection failed: {e}")
            self.lm_state = LMState.IDLE
            self.lm_temp_file = None
            self.lm_recording_start_time = None
            return {'status': 'error', 'message': str(e)}

    def cancel_launch_monitor(self):
        """
        Cancel launch monitor recording without saving.

        Returns:
            dict: Status message
        """
        if self.lm_state == LMState.IDLE:
            return {'status': 'ok', 'message': 'Already idle'}

        logger.info("Cancelling launch monitor recording...")

        # Signal cancel
        self.lm_cancel_event.set()
        self.lm_state = LMState.IDLE

        # Wait for recording thread to finish
        if self.lm_recording_thread:
            self.lm_recording_thread.join(timeout=5)

        # Delete temp file
        if self.lm_temp_file and self.lm_temp_file.exists():
            try:
                os.remove(self.lm_temp_file)
                logger.info(f"Deleted temp file: {self.lm_temp_file}")
            except Exception as e:
                logger.error(f"Failed to delete temp file: {e}")

        # Reset state
        self.lm_temp_file = None
        self.lm_recording_start_time = None

        return {'status': 'cancelled'}

    def get_lm_status(self):
        """
        Get current launch monitor status.

        Returns:
            dict: Current state and timing info
        """
        recording_duration = 0
        if self.lm_recording_start_time:
            recording_duration = time.time() - self.lm_recording_start_time

        return {
            'state': self.lm_state.value,
            'recording_duration': round(recording_duration, 2),
            'max_duration': self.config['lm_max_recording_duration']
        }

    def _lm_continuous_record(self):
        """Background worker for continuous recording until timeout or cancel."""
        try:
            max_duration = self.config['lm_max_recording_duration']
            logger.info(f"Starting continuous recording (max {max_duration}s)")

            # Start continuous recording using backend
            # Note: We'll record for max_duration, but can be interrupted
            self.recording = True

            try:
                # Record to temp file
                actual_output_path = self.backend.record(self.lm_temp_file, max_duration)

                # Check if we were cancelled during recording
                if self.lm_cancel_event.is_set():
                    logger.info("Continuous recording cancelled")
                else:
                    # Timeout occurred
                    logger.warning(f"Launch monitor timeout ({max_duration}s) - cancelling")
                    self.lm_state = LMState.IDLE

                    # Delete temp file on timeout
                    if self.lm_temp_file and Path(self.lm_temp_file).exists():
                        os.remove(self.lm_temp_file)
                        logger.info("Deleted temp file after timeout")

                    self.lm_temp_file = None
                    self.lm_recording_start_time = None

            finally:
                self.recording = False

        except Exception as e:
            logger.error(f"Continuous recording failed: {e}")
            self.lm_state = LMState.IDLE
            self.recording = False

    def _extract_clip(self, input_path, output_path, duration):
        """
        Extract last N seconds from video file using FFmpeg.

        Args:
            input_path: Path to input video file
            output_path: Path for output video file
            duration: Number of seconds to extract from end

        Returns:
            bool: True if successful, False otherwise
        """
        import subprocess

        try:
            # Use FFmpeg to extract last N seconds
            # -sseof: seek from end of file (negative value)
            # -c copy: copy codec (no re-encoding, fast and lossless)
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-sseof', f'-{duration}',  # Seek to N seconds before end
                '-i', str(input_path),
                '-c', 'copy',  # Copy codec (no re-encoding)
                str(output_path)
            ]

            logger.info(f"Extracting last {duration}s from {input_path}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                logger.info(f"Extraction complete: {output_path}")

                # Delete temp file after successful extraction
                if input_path.exists():
                    os.remove(input_path)
                    logger.info(f"Deleted temp file: {input_path}")

                return True
            else:
                logger.error(f"FFmpeg failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg extraction timed out")
            return False
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return False

    def cleanup(self):
        """Cleanup camera backend."""
        try:
            # Cancel any LM recording in progress
            if self.lm_state != LMState.IDLE:
                self.cancel_launch_monitor()

            if self.recording:
                self.stop()
            self.backend.cleanup()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Golf Swing Camera')
    parser.add_argument('--config', default='config.json', help='Configuration file')
    parser.add_argument('--name', help='Custom name for recording')
    parser.add_argument('--list', action='store_true', help='List all recordings')
    
    args = parser.parse_args()
    
    camera = SwingCamera(args.config)
    
    try:
        if args.list:
            recordings = camera.get_recordings()
            print(f"\nFound {len(recordings)} recordings:\n")
            for rec in recordings:
                print(f"  {rec['name']} - {rec['size'] / 1024 / 1024:.2f} MB")
        else:
            camera.start()
            print("\nGolf Swing Camera Ready!")
            print(f"Press ENTER to record a {camera.config['duration']}s swing video...")
            input()
            
            output_path = camera.capture_swing(args.name)
            if output_path:
                print(f"\n✓ Recording saved: {output_path}")
                print("\nPress ENTER to record another, or Ctrl+C to exit...")
                
                while True:
                    input()
                    output_path = camera.capture_swing()
                    if output_path:
                        print(f"\n✓ Recording saved: {output_path}")
                        print("\nPress ENTER to record another, or Ctrl+C to exit...")
    
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        camera.cleanup()

