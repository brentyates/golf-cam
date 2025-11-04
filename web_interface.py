#!/usr/bin/env python3
"""
Web interface for easy control of the golf swing camera.
Provides a simple UI to trigger recordings and view captured swings.
"""

import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, jsonify, request, send_file, redirect, session, url_for, Response
from flask.views import MethodView
import threading
import time
import json
import pickle
from pathlib import Path
import io

from swing_camera import SwingCamera


app = Flask(__name__)
app.secret_key = os.urandom(24)
camera = None
camera_lock = threading.Lock()
config_path = 'config.json'


class IndexView(MethodView):
    """Main page view."""
    
    def get(self):
        return render_template('index.html')


class RecordView(MethodView):
    """Handle recording requests."""
    
    def post(self):
        global camera
        
        try:
            data = request.get_json(silent=True) or {}
            custom_name = data.get('name') if data else None
            
            with camera_lock:
                if camera.recording:
                    app.logger.warning("Recording already in progress")
                    return jsonify({'status': 'error', 'message': 'Already recording'}), 400
                
                def record_async():
                    try:
                        output_path = camera.capture_swing(custom_name)
                        if output_path:
                            app.logger.info(f"Recording completed: {output_path}")
                    except Exception as e:
                        app.logger.error(f"Recording failed: {e}", exc_info=True)
                
                thread = threading.Thread(target=record_async)
                thread.daemon = True
                thread.start()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Recording started',
                    'duration': camera.config['duration']
                })
        except Exception as e:
            app.logger.error(f"Failed to start recording: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class StatusView(MethodView):
    """Get camera status."""
    
    def get(self):
        global camera
        
        with camera_lock:
            return jsonify({
                'recording': camera.recording,
                'config': {
                    'fps': camera.config['fps'],
                    'resolution': f"{camera.config['width']}x{camera.config['height']}",
                    'duration': camera.config['duration'],
                    'shutter_speed': camera.config['shutter_speed']
                }
            })


class RecordingsView(MethodView):
    """List all recordings."""
    
    def get(self):
        global camera
        
        with camera_lock:
            recordings = camera.get_recordings()
            return jsonify({'recordings': recordings})


class DownloadView(MethodView):
    """Download a recording."""
    
    def get(self, filename):
        global camera
        
        file_path = camera.output_dir / filename
        
        if not file_path.exists():
            return jsonify({'status': 'error', 'message': 'File not found'}), 404
        
        return send_file(str(file_path), as_attachment=True)


class DeleteRecordingView(MethodView):
    """Delete a recording."""
    
    def delete(self, filename):
        global camera
        
        try:
            file_path = camera.output_dir / filename
            metadata_path = file_path.with_suffix('.json')
            
            if not file_path.exists():
                return jsonify({'status': 'error', 'message': 'File not found'}), 404
            
            camera.delete_recording(filename)
            
            return jsonify({'status': 'success', 'message': f'Deleted {filename}'})
        except Exception as e:
            app.logger.error(f"Failed to delete recording: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class DeleteAllRecordingsView(MethodView):
    """Delete all recordings."""
    
    def delete(self):
        global camera
        
        try:
            count = camera.delete_all_recordings()
            return jsonify({'status': 'success', 'count': count, 'message': f'Deleted {count} recordings'})
        except Exception as e:
            app.logger.error(f"Failed to delete all recordings: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class SettingsView(MethodView):
    """Settings page view."""
    
    def get(self):
        return render_template('settings.html')


class ConfigView(MethodView):
    """Get and update configuration."""
    
    def get(self):
        global config_path
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        gdrive_setup = os.path.exists('gdrive_token.pickle')
        gdrive_credentials = os.path.exists('gdrive_credentials.json')
        
        return jsonify({
            'config': config,
            'gdrive_configured': gdrive_setup,
            'gdrive_credentials_present': gdrive_credentials
        })
    
    def post(self):
        global camera, config_path
        
        new_config = request.get_json()
        
        if not new_config:
            return jsonify({'status': 'error', 'message': 'No configuration provided'}), 400
        
        # Load existing config to preserve comments
        existing_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
        
        # Update only the config values, preserve _comments
        if '_comments' in existing_config:
            new_config['_comments'] = existing_config['_comments']
        
        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=2)
        
        app.logger.info(f"Config saved: upload_enabled={new_config.get('upload_enabled')}, upload_destination={new_config.get('upload_destination')}")

        with camera_lock:
            # Clean up the old camera before reinitializing
            camera.backend.cleanup()

            # Reload config and setup camera with new settings
            camera.config = camera._load_config(config_path)
            camera._setup_camera()
            camera.start()

        return jsonify({'status': 'success', 'message': 'Configuration updated'})


class ShutterSpeedView(MethodView):
    """Update shutter speed on-the-fly without restarting camera."""

    def post(self):
        global camera, config_path

        data = request.get_json()
        shutter_speed = data.get('shutter_speed')

        if not shutter_speed:
            return jsonify({'status': 'error', 'message': 'No shutter speed provided'}), 400

        try:
            shutter_speed = int(shutter_speed)
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid shutter speed value'}), 400

        # Calculate maximum shutter speed for current FPS
        fps = camera.config.get('fps', 30)
        max_shutter = int(1000000 / fps) - 100  # Leave 100µs margin

        if shutter_speed > max_shutter:
            return jsonify({
                'status': 'error',
                'message': f'Shutter speed {shutter_speed}µs exceeds maximum {max_shutter}µs for {fps} FPS'
            }), 400

        if shutter_speed < 50:
            return jsonify({'status': 'error', 'message': 'Shutter speed must be at least 50µs'}), 400

        # Update shutter speed live using PiCamera2 set_controls
        backend_name = camera.backend.get_name()

        if 'PiCamera2' in backend_name:
            try:
                with camera_lock:
                    # Use PiCamera2's set_controls to update shutter speed on-the-fly
                    camera.backend.camera.set_controls({"ExposureTime": shutter_speed})
                    # Update config in memory (don't save to file - preview only)
                    camera.config['shutter_speed'] = shutter_speed

                app.logger.info(f"Shutter speed updated live to {shutter_speed}µs (1/{int(1000000/shutter_speed)}s)")

                return jsonify({
                    'status': 'success',
                    'message': f'Shutter speed updated to {shutter_speed}µs',
                    'shutter_speed': shutter_speed,
                    'fraction': f'1/{int(1000000/shutter_speed)}s'
                })
            except Exception as e:
                app.logger.error(f"Failed to update shutter speed: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
        else:
            return jsonify({
                'status': 'error',
                'message': 'Live shutter speed update only supported on PiCamera2 backend'
            }), 400


class PresetView(MethodView):
    """Load recording presets."""

    def get(self):
        """Get available presets."""
        preset_file = 'recording_presets.json'

        if not os.path.exists(preset_file):
            return jsonify({
                'status': 'error',
                'message': 'Preset file not found'
            }), 404

        with open(preset_file, 'r') as f:
            presets_data = json.load(f)

        return jsonify({
            'status': 'success',
            'presets': presets_data.get('presets', {}),
            'categories': presets_data.get('categories', {}),
            'recommended': presets_data.get('recommended_use_cases', {}),
            'hardware_notes': presets_data.get('hardware_notes', {})
        })

    def post(self):
        """Apply a preset."""
        global camera, config_path

        data = request.get_json()
        preset_name = data.get('preset')

        if not preset_name:
            return jsonify({'status': 'error', 'message': 'No preset specified'}), 400

        preset_file = 'recording_presets.json'

        if not os.path.exists(preset_file):
            return jsonify({'status': 'error', 'message': 'Preset file not found'}), 404

        with open(preset_file, 'r') as f:
            presets_data = json.load(f)

        if preset_name not in presets_data.get('presets', {}):
            return jsonify({'status': 'error', 'message': f'Preset "{preset_name}" not found'}), 404

        preset = presets_data['presets'][preset_name]

        # Load existing config to preserve comments and other settings
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Apply preset values
        config['width'] = preset['width']
        config['height'] = preset['height']
        config['fps'] = preset['fps']
        config['shutter_speed'] = preset['shutter_speed']
        config['duration'] = preset['duration']

        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        app.logger.info(f"Applied preset '{preset_name}': {preset['width']}x{preset['height']} @ {preset['fps']} FPS")

        # Reconfigure camera with new settings
        with camera_lock:
            camera.backend.cleanup()
            camera.config = camera._load_config(config_path)
            camera._setup_camera()
            camera.start()

        return jsonify({
            'status': 'success',
            'message': f'Preset "{preset_name}" applied successfully',
            'preset': preset
        })


class GDriveSetupView(MethodView):
    """Handle Google Drive setup."""
    
    def get(self):
        return jsonify({
            'credentials_present': os.path.exists('gdrive_credentials.json'),
            'authenticated': os.path.exists('gdrive_token.pickle')
        })
    
    def post(self):
        action = request.form.get('action')
        
        if action == 'upload_credentials':
            if 'credentials_file' not in request.files:
                return jsonify({'status': 'error', 'message': 'No file provided'}), 400
            
            file = request.files['credentials_file']
            
            if file.filename == '':
                return jsonify({'status': 'error', 'message': 'No file selected'}), 400
            
            try:
                content = json.load(file)
                
                with open('gdrive_credentials.json', 'w') as f:
                    json.dump(content, f, indent=2)
                
                return jsonify({'status': 'success', 'message': 'Credentials uploaded successfully'})
            except Exception as e:
                return jsonify({'status': 'error', 'message': f'Invalid credentials file: {str(e)}'}), 400
        
        elif action == 'authenticate':
            try:
                auth_url = self._start_oauth_flow()
                return jsonify({'status': 'success', 'auth_url': auth_url})
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 400
        
        return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
    
    def _start_oauth_flow(self):
        from google_auth_oauthlib.flow import Flow
        
        if not os.path.exists('gdrive_credentials.json'):
            raise Exception('Credentials file not found. Please upload it first.')
        
        flow = Flow.from_client_secrets_file(
            'gdrive_credentials.json',
            scopes=['https://www.googleapis.com/auth/drive.file'],
            redirect_uri=url_for('gdrive_callback', _external=True)
        )
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        session['oauth_state'] = state
        
        return authorization_url


class GDriveCallbackView(MethodView):
    """Handle Google Drive OAuth callback."""
    
    def get(self):
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
        import pickle
        
        state = session.get('oauth_state')
        
        if not state:
            return "Error: No OAuth state found. Please try again.", 400
        
        flow = Flow.from_client_secrets_file(
            'gdrive_credentials.json',
            scopes=['https://www.googleapis.com/auth/drive.file'],
            state=state,
            redirect_uri=url_for('gdrive_callback', _external=True)
        )
        
        flow.fetch_token(authorization_response=request.url)
        
        credentials = flow.credentials
        
        with open('gdrive_token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
        
        try:
            service = build('drive', 'v3', credentials=credentials)
            
            results = service.files().list(
                q="name='Golf Swings' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                folder_id = items[0]['id']
            else:
                file_metadata = {
                    'name': 'Golf Swings',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = service.files().create(
                    body=file_metadata,
                    fields='id'
                ).execute()
                folder_id = folder.get('id')
            
            session['gdrive_folder_id'] = folder_id
            
            return redirect('/settings?gdrive_success=true&folder_id=' + folder_id)
        
        except Exception as e:
            return redirect('/settings?gdrive_error=' + str(e))


class TestUploadView(MethodView):
    """Test upload configuration."""

    def post(self):
        data = request.get_json()
        destination = data.get('destination')

        if not destination:
            return jsonify({'status': 'error', 'message': 'No destination provided'}), 400

        try:
            if destination.startswith('gdrive://'):
                result = self._test_gdrive(destination)
            else:
                result = {'status': 'error', 'message': 'Only Google Drive is supported for testing'}

            return jsonify(result)
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 400

    def _test_gdrive(self, destination):
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import pickle

        if not os.path.exists('gdrive_token.pickle'):
            return {'status': 'error', 'message': 'Not authenticated. Please authenticate first.'}

        with open('gdrive_token.pickle', 'rb') as token:
            creds = pickle.load(token)

        service = build('drive', 'v3', credentials=creds)

        folder_id = destination.replace('gdrive://', '')

        try:
            folder = service.files().get(fileId=folder_id, fields='id,name').execute()
            return {
                'status': 'success',
                'message': f'Connection successful! Folder: {folder.get("name")}'
            }
        except Exception as e:
            return {'status': 'error', 'message': f'Cannot access folder: {str(e)}'}


class PreviewView(MethodView):
    """Live preview page."""

    def get(self):
        global camera
        current_resolution = f"{camera.config['width']}x{camera.config['height']}"
        return render_template('preview.html',
                             current_resolution=current_resolution,
                             current_shutter=camera.config['shutter_speed'],
                             current_fps=camera.config['fps'],
                             current_gain=camera.config.get('gain', 1.0))


class VideoFeedView(MethodView):
    """MJPEG video stream for live preview."""

    def get(self):
        return Response(self._generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')

    def _generate_frames(self):
        """Generate MJPEG frames from camera."""
        global camera
        from PIL import Image
        import io

        try:
            # Check backend type
            backend_name = camera.backend.get_name()

            if 'PiCamera2' in backend_name:
                # PiCamera2 streaming - optimized for high FPS cameras
                preview_fps = 30  # Limit preview to 30 FPS regardless of camera FPS
                frame_interval = 1.0 / preview_fps
                last_frame_time = 0

                while True:
                    current_time = time.time()

                    # Limit preview FPS to avoid overwhelming the connection
                    if current_time - last_frame_time < frame_interval:
                        time.sleep(0.01)
                        continue

                    try:
                        # Quick capture without blocking
                        if camera.backend.camera and camera.backend.camera.started:
                            # Use PiCamera2's capture_array to get RGB data directly
                            import numpy as np
                            frame = camera.backend.camera.capture_array("main")

                            # Frame is in YUV420 format - extract Y plane (grayscale is fine for preview)
                            height = camera.config['height']
                            width = camera.config['width']
                            y_plane = frame[:height, :width]

                            # Convert to PIL Image (grayscale)
                            img = Image.fromarray(y_plane, mode='L')

                            # Resize if very large to save bandwidth
                            if width > 1280:
                                new_width = 1280
                                new_height = int(height * 1280 / width)
                                img = img.resize((new_width, new_height), Image.BILINEAR)

                            # Encode to JPEG
                            buffer = io.BytesIO()
                            img.save(buffer, format='JPEG', quality=75)
                            frame_bytes = buffer.getvalue()

                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                            last_frame_time = current_time
                        else:
                            time.sleep(0.1)

                    except Exception as e:
                        app.logger.warning(f"Preview frame error: {e}")
                        time.sleep(0.1)

            elif 'OpenCV' in backend_name or 'Demo' in backend_name:
                # OpenCV or Demo mode streaming
                import cv2

                if 'Demo' in backend_name:
                    # Generate demo frames
                    while True:
                        import numpy as np
                        width = camera.config.get('width', 1456)
                        height = camera.config.get('height', 1088)

                        # Create demo frame
                        frame = np.zeros((height, width, 3), dtype=np.uint8)

                        # Add moving circle animation
                        t = time.time()
                        center_x = int(width * (0.3 + 0.4 * abs(np.sin(t))))
                        center_y = height // 2
                        cv2.circle(frame, (center_x, center_y), min(width, height) // 10, (0, 255, 0), -1)

                        # Add text
                        cv2.putText(frame, 'LIVE PREVIEW - DEMO MODE', (50, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

                        if ret:
                            frame_bytes = buffer.tobytes()
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                        time.sleep(0.033)  # ~30 fps preview

                else:
                    # OpenCV camera streaming
                    while True:
                        with camera_lock:
                            if camera.backend.camera and camera.backend.camera.isOpened():
                                ret, frame = camera.backend.camera.read()

                                if ret:
                                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

                                    if ret:
                                        frame_bytes = buffer.tobytes()
                                        yield (b'--frame\r\n'
                                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                            else:
                                time.sleep(0.1)

        except GeneratorExit:
            pass
        except Exception as e:
            app.logger.error(f"Video feed error: {e}", exc_info=True)


class PreviewSettingsView(MethodView):
    """Update camera settings in real-time for preview (without saving to config)."""

    def post(self):
        global camera

        try:
            settings = request.get_json()

            if not settings:
                return jsonify({'status': 'error', 'message': 'No settings provided'}), 400

            with camera_lock:
                backend_name = camera.backend.get_name()

                if 'PiCamera2' in backend_name:
                    # Check if resolution change is requested (requires reconfiguration)
                    if 'width' in settings and 'height' in settings:
                        width = int(settings['width'])
                        height = int(settings['height'])

                        # Update config temporarily
                        camera.config['width'] = width
                        camera.config['height'] = height

                        # Reconfigure camera
                        camera.backend.camera.stop()
                        camera.backend.setup(camera.config)
                        camera.backend.start()

                        app.logger.info(f"Reconfigured camera to {width}x{height}")

                    # Update PiCamera2 controls in real-time
                    controls = {}

                    if 'shutter_speed' in settings:
                        controls['ExposureTime'] = int(settings['shutter_speed'])

                    if 'fps' in settings:
                        controls['FrameRate'] = float(settings['fps'])

                    if 'gain' in settings:
                        controls['AnalogueGain'] = float(settings['gain'])

                    if controls and camera.backend.camera.started:
                        camera.backend.camera.set_controls(controls)
                        app.logger.info(f"Updated camera controls: {controls}")

                elif 'OpenCV' in backend_name:
                    # OpenCV has limited control, but we can try
                    if 'fps' in settings and camera.backend.camera:
                        import cv2
                        camera.backend.camera.set(cv2.CAP_PROP_FPS, float(settings['fps']))

            return jsonify({'status': 'success', 'message': 'Settings updated'})

        except Exception as e:
            app.logger.error(f"Failed to update preview settings: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class TestMaxFPSView(MethodView):
    """Test the maximum achievable FPS without streaming overhead."""

    def post(self):
        global camera
        try:
            import time

            # Try to acquire the lock with a longer timeout to allow video stream to stop
            # Video stream releases lock between frames, so we retry multiple times
            max_retries = 5
            retry_delay = 0.3
            lock_acquired = False

            for attempt in range(max_retries):
                lock_acquired = camera_lock.acquire(timeout=0.5)
                if lock_acquired:
                    break
                app.logger.info(f"Lock acquisition attempt {attempt + 1}/{max_retries} failed, retrying...")
                time.sleep(retry_delay)

            if not lock_acquired:
                return jsonify({
                    'status': 'error',
                    'message': 'Camera is busy. Please try again in a moment.'
                }), 409  # Conflict status code

            try:
                backend_name = camera.backend.get_name()

                if 'PiCamera2' not in backend_name:
                    return jsonify({
                        'status': 'error',
                        'message': 'FPS testing only available with PiCamera2 backend'
                    }), 400

                # Get current settings
                target_fps = camera.config['fps']
                resolution = f"{camera.config['width']}x{camera.config['height']}"

                app.logger.info(f"Starting FPS test: target {target_fps} FPS at {resolution}")

                # Capture frames for 3 seconds - use capture_array for maximum speed
                test_duration = 3.0
                frames_captured = 0
                start_time = time.time()
                sensor_timestamps = []

                # Capture frames as fast as possible with metadata
                try:
                    while (time.time() - start_time) < test_duration:
                        # Capture frame and metadata together using request API
                        request = camera.backend.camera.capture_request()
                        try:
                            array = request.make_array("main")
                            metadata = request.get_metadata()

                            frames_captured += 1

                            # Get sensor timestamp for ground-truth FPS
                            if 'SensorTimestamp' in metadata:
                                sensor_timestamps.append(metadata['SensorTimestamp'])
                        finally:
                            request.release()

                except Exception as e:
                    app.logger.warning(f"Frame capture error: {e}")
                    if frames_captured == 0:
                        return jsonify({
                            'status': 'error',
                            'message': f'FPS test failed: {str(e)}'
                        }), 500

                actual_duration = time.time() - start_time
                capture_fps = frames_captured / actual_duration if frames_captured > 0 else 0

                # Calculate ground-truth FPS from sensor timestamps (most accurate)
                sensor_intervals = []
                sensor_fps = 0
                if len(sensor_timestamps) > 10:
                    # Sensor timestamps are in nanoseconds
                    sensor_intervals = [(sensor_timestamps[i] - sensor_timestamps[i-1]) / 1_000_000
                                      for i in range(1, min(len(sensor_timestamps), 11))]
                    avg_sensor_interval = sum(sensor_intervals) / len(sensor_intervals) if sensor_intervals else 0

                    # Calculate FPS from average sensor interval
                    if avg_sensor_interval > 0:
                        sensor_fps = 1000.0 / avg_sensor_interval
                else:
                    avg_sensor_interval = 0

                # Use sensor FPS as the "actual" FPS (ground truth)
                actual_fps = sensor_fps if sensor_fps > 0 else capture_fps

                app.logger.info(f"FPS test complete: {actual_fps:.1f} FPS (sensor) / {capture_fps:.1f} FPS (capture)")
                app.logger.info(f"({frames_captured} frames in {actual_duration:.2f}s)")
                app.logger.info(f"Sensor intervals (ms): {[f'{x:.2f}' for x in sensor_intervals[:10]]}")

                return jsonify({
                    'status': 'success',
                    'actual_fps': round(actual_fps, 2),
                    'capture_fps': round(capture_fps, 2),
                    'sensor_fps': round(sensor_fps, 2) if sensor_fps > 0 else None,
                    'target_fps': target_fps,
                    'frames_captured': frames_captured,
                    'duration': round(actual_duration, 2),
                    'resolution': resolution,
                    'diagnostics': {
                        'avg_sensor_interval_ms': round(avg_sensor_interval, 2) if avg_sensor_interval > 0 else None,
                        'sensor_intervals_ms': [round(x, 2) for x in sensor_intervals[:10]]
                    }
                })
            finally:
                camera_lock.release()

        except Exception as e:
            app.logger.error(f"FPS test failed: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class LMArmView(MethodView):
    """Arm the launch monitor - start continuous recording."""

    def post(self):
        global camera

        try:
            with camera_lock:
                result = camera.arm_launch_monitor()
                return jsonify(result)
        except Exception as e:
            app.logger.error(f"Failed to arm launch monitor: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class LMShotDetectedView(MethodView):
    """Shot detected - stop recording and extract clip."""

    def post(self):
        global camera

        try:
            with camera_lock:
                result = camera.shot_detected()
                return jsonify(result)
        except Exception as e:
            app.logger.error(f"Shot detection failed: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class LMCancelView(MethodView):
    """Cancel launch monitor recording."""

    def post(self):
        global camera

        try:
            with camera_lock:
                result = camera.cancel_launch_monitor()
                return jsonify(result)
        except Exception as e:
            app.logger.error(f"Failed to cancel launch monitor: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


class LMStatusView(MethodView):
    """Get launch monitor status."""

    def get(self):
        global camera

        try:
            with camera_lock:
                result = camera.get_lm_status()
                return jsonify(result)
        except Exception as e:
            app.logger.error(f"Failed to get LM status: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': str(e)}), 500


app.add_url_rule('/', view_func=IndexView.as_view('index'))
app.add_url_rule('/settings', view_func=SettingsView.as_view('settings'))
app.add_url_rule('/preview', view_func=PreviewView.as_view('preview'))
app.add_url_rule('/api/record', view_func=RecordView.as_view('record'))
app.add_url_rule('/api/status', view_func=StatusView.as_view('status'))
app.add_url_rule('/api/recordings', view_func=RecordingsView.as_view('recordings'), methods=['GET'])
app.add_url_rule('/api/recordings', view_func=DeleteAllRecordingsView.as_view('delete_all_recordings'), methods=['DELETE'])
app.add_url_rule('/api/recordings/<filename>', view_func=DeleteRecordingView.as_view('delete_recording'), methods=['DELETE'])
app.add_url_rule('/api/download/<filename>', view_func=DownloadView.as_view('download'))
app.add_url_rule('/api/config', view_func=ConfigView.as_view('config'))
app.add_url_rule('/api/shutter-speed', view_func=ShutterSpeedView.as_view('shutter_speed'))
app.add_url_rule('/api/preset', view_func=PresetView.as_view('preset'))
app.add_url_rule('/api/gdrive/setup', view_func=GDriveSetupView.as_view('gdrive_setup'))
app.add_url_rule('/api/gdrive/callback', view_func=GDriveCallbackView.as_view('gdrive_callback'))
app.add_url_rule('/api/test-upload', view_func=TestUploadView.as_view('test_upload'))
app.add_url_rule('/video_feed', view_func=VideoFeedView.as_view('video_feed'))
app.add_url_rule('/api/preview-settings', view_func=PreviewSettingsView.as_view('preview_settings'))
app.add_url_rule('/api/test-max-fps', view_func=TestMaxFPSView.as_view('test_max_fps'))
# Launch monitor API endpoints
app.add_url_rule('/api/lm/arm', view_func=LMArmView.as_view('lm_arm'))
app.add_url_rule('/api/lm/shot-detected', view_func=LMShotDetectedView.as_view('lm_shot_detected'))
app.add_url_rule('/api/lm/cancel', view_func=LMCancelView.as_view('lm_cancel'))
app.add_url_rule('/api/lm/status', view_func=LMStatusView.as_view('lm_status'))


def initialize_camera(config_path='config.json', demo_mode=False):
    """Initialize the camera system."""
    global camera
    
    camera = SwingCamera(config_path, demo_mode=demo_mode)
    camera.start()
    
    if demo_mode:
        app.logger.info("Camera initialized in DEMO MODE (Mac-friendly)")
    else:
        app.logger.info("Camera initialized and started")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Golf Swing Camera Web Interface')
    parser.add_argument('--config', default='config.json', help='Configuration file')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode (no camera required - Mac-friendly)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode with auto-reload')

    args = parser.parse_args()

    initialize_camera(args.config, demo_mode=args.demo)

    try:
        # Debug mode with use_reloader=False prevents the reloader from
        # trying to initialize the camera twice (which causes "device busy" errors)
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True, use_reloader=False)
    finally:
        if camera:
            camera.cleanup()

