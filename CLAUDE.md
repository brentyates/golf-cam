# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

High-Speed Impact Camera - A high-performance video capture system for Raspberry Pi 5 with global shutter camera. Optimized for capturing fast motion events (golf swings, ball impacts, etc.) at 120 FPS with minimal rolling shutter artifacts. Features a Flask web interface, Google Drive integration, and multi-platform camera backend support. Supports recording durations from 1 second (impact capture) to longer durations for full motion analysis.

## Core Commands

### Development & Testing

**On Mac (with OpenCV camera support):**
```bash
# Install dependencies for Mac development
pip install -r requirements-mac.txt

# Run web interface (auto-detects Mac camera)
python web_interface.py

# Run in demo mode (no camera required)
python web_interface.py --demo
```

**On Raspberry Pi:**
```bash
# First-time setup
./setup.sh

# Run web interface (uses PiCamera2 backend)
source venv/bin/activate
python web_interface.py

# Run command line interface
python swing_camera.py
```

### Testing

The system has no formal test suite. Testing is done manually:
- Web interface: `python web_interface.py --demo` for UI testing
- Camera backends: Run on respective platforms (Mac/Pi)
- Recording: Test actual video capture on each platform

### Deployment

```bash
# Deploy from Mac to Raspberry Pi
./deploy.sh [pi_hostname] [username] [path]

# Default deployment:
./deploy.sh raspberrypi.local pi ~/swing-cam

# Remote deployment (via public IP):
./deploy.sh YOUR_PI_IP_ADDRESS pi ~/swing-cam
```

## Remote Access & Development Workflow

### Network Configuration

**When using remote access (optional):**

Set up port forwarding on your router if you want remote access:
- Port 22 → SSH (secure with key-based auth, disable password auth)
- Port 5000 → Web interface (optional, SSH tunnel recommended)

**SSH Security Best Practices:**
- Password authentication: DISABLED
- Public key authentication: ENABLED
- Root login: DISABLED

### Remote Access via SSH Tunnel (Recommended)

**Most secure way to access from remote locations:**

```bash
# Create SSH tunnel (from work/remote location)
ssh -L 5000:localhost:5000 pi@YOUR_PI_IP_ADDRESS

# Keep terminal open, then access web interface at:
# http://localhost:5000
```

This approach:
- Only exposes SSH port (already secured)
- Port 5000 never exposed to internet
- All traffic encrypted through SSH
- No web authentication needed

### Development Workflow

**See `DEV_WORKFLOW.md` for complete documentation.**

**Quick Start - Automated Dev Mode:**

1. **Start file watcher on Mac** (auto-syncs code to Pi):
   ```bash
   source venv/bin/activate
   python dev-watch.py
   ```

2. **Start Pi server with debug mode:**
   ```bash
   ssh pi@raspberrypi.local  # or pi@YOUR_PI_IP_ADDRESS
   cd swing-cam
   source venv/bin/activate
   python web_interface.py --debug
   ```

3. **Create SSH tunnel** (in separate terminal):
   ```bash
   ssh -L 5000:localhost:5000 pi@raspberrypi.local  # or pi@YOUR_PI_IP_ADDRESS
   ```

4. **Access web interface:**
   ```
   http://localhost:5000
   ```

**Workflow:**
- Edit code on Mac → File watcher auto-syncs (~1 sec)
- Manually restart Pi server to see changes
- Refresh browser

**Quick restart command:**
```bash
ssh pi@raspberrypi.local "pkill -f 'python web_interface.py' && cd swing-cam && source venv/bin/activate && nohup python web_interface.py --debug > flask.log 2>&1 &"
```

### Development Tools

**File Watcher (`dev-watch.py`):**
- Watches local directory for code changes
- Auto-syncs to Pi via rsync within 1 second
- Batches rapid changes (1 second debounce)
- Ignores: venv, __pycache__, recordings, .git

**Debug Mode (`--debug` flag):**
- Detailed error pages with stack traces
- Flask development features enabled
- **Important:** `use_reloader=False` to prevent camera device busy errors
- Auto-reload disabled due to hardware camera limitation
- Manual restart required after code changes

## Architecture

### Multi-Backend Camera System

The project uses a **Strategy Pattern** with automatic backend selection:

1. **camera_backends.py** - Camera abstraction layer
   - `CameraBackend` - Abstract base class defining camera interface
   - `PiCamera2Backend` - Raspberry Pi global shutter camera (production)
   - `OpenCVBackend` - Generic USB/webcam support (Mac/development)
   - `DemoBackend` - No camera required (UI testing)
   - `create_camera_backend()` - Factory function with automatic detection

2. **swing_camera.py** - Core camera control
   - `SwingCamera` - Main camera controller (backend-agnostic)
   - Uses backend abstraction, never directly accesses hardware
   - Handles recording, metadata, uploads, file management
   - Google Drive integration via `_upload_to_gdrive()`

3. **web_interface.py** - Flask web application
   - Flask views using `MethodView` pattern
   - All API endpoints under `/api/*`
   - OAuth2 flow for Google Drive auth
   - Threaded recording to prevent blocking

4. **button_trigger.py** - Hardware GPIO button support
   - Uses gpiozero library
   - Button on GPIO 17
   - Only works on Raspberry Pi

### Backend Selection Logic

Priority order (first available wins):
1. PiCamera2 (if on Raspberry Pi with camera)
2. OpenCV (if USB/built-in camera detected)
3. Demo mode (always works as fallback)

The main code never knows which backend is in use - all backends implement the same interface.

### Configuration System

#### Configuration Files

1. **recording_presets.json** - SINGLE SOURCE OF TRUTH for all camera presets
   - Contains all 7 camera modes (60fps → 536fps)
   - Organized by category: Standard, Slow Motion, High Speed
   - Includes metadata: resolution, FPS, shutter speed, duration, use cases, lighting requirements
   - UI dynamically loads presets from this file via `/api/preset`
   - **To add new presets:** Edit this file only, NO code changes required

2. **config.json** - Active runtime configuration (auto-managed)
   - Current camera settings applied to the system
   - Updated automatically when user selects preset via UI
   - Comments stored in `_comments` field (preserved during updates)
   - Upload settings (Google Drive folder ID)
   - **DO NOT manually edit** - use Settings UI or `/api/preset` endpoint

3. **gdrive_credentials.json** - Google OAuth2 credentials (not in git)
4. **gdrive_token.pickle** - Google auth token (not in git)

#### How Configuration Works

**User Workflow (Recommended):**
```
1. Open Settings page
2. Select camera mode card
3. Click "Save Camera Mode"
4. Camera automatically reconfigures
```

**API Workflow (Programmatic):**
```bash
# Get available presets
curl http://localhost:5000/api/preset

# Apply a preset
curl -X POST http://localhost:5000/api/preset \
  -H "Content-Type: application/json" \
  -d '{"preset": "high_speed_400fps"}'
```

**Backend Flow:**
```
recording_presets.json (source of truth)
    ↓
/api/preset GET → UI dynamically renders preset cards
    ↓
User selects preset → /api/preset POST
    ↓
PresetView.post() applies settings to config.json
    ↓
Camera backend cleanup → reconfigure → restart
    ↓
New settings active immediately (no app restart needed)
```

#### Adding New Presets

**Steps:**
1. Edit `recording_presets.json`
2. Add new preset under `presets` section
3. Include: name, description, category, width, height, fps, shutter_speed, duration
4. Optional: use_cases, lighting_requirement, tested, reference, hardware_requirement
5. Save file
6. Refresh Settings page - new preset appears automatically

**Example:**
```json
"custom_preset": {
  "name": "Custom Mode - 180 FPS",
  "description": "Custom resolution for specific use case",
  "category": "Slow Motion",
  "width": 600,
  "height": 400,
  "fps": 180,
  "shutter_speed": 2000,
  "duration": 2,
  "format": "h264",
  "quality": "high",
  "auto_exposure": false,
  "use_cases": ["Custom application"],
  "tested": false
}
```

### Web Interface Structure

**Flask Routes:**
- `/` - Main recording interface
- `/settings` - Configuration page
- `/api/record` - POST to start recording
- `/api/status` - GET camera status
- `/api/recordings` - GET list, DELETE all
- `/api/recordings/<filename>` - DELETE single recording
- `/api/download/<filename>` - Download recording
- `/api/config` - GET current config, POST to update (use for duration/format only)
- `/api/preset` - **GET available presets, POST to apply preset (RECOMMENDED for mode changes)**
- `/api/gdrive/setup` - Google Drive OAuth setup
- `/api/gdrive/callback` - OAuth callback
- `/api/test-upload` - Test upload configuration

**Templates:**
- `templates/index.html` - Main UI
- `templates/settings.html` - Settings UI

## Critical Implementation Details

### Camera Backend Requirements

When modifying camera backends:
- All backends MUST implement the `CameraBackend` abstract interface
- `record()` must return the actual output path (may differ from requested)
- PiCamera2 uses hardware H.264 encoding (efficient, Pi-specific)
- OpenCV uses software MP4 encoding (cross-platform)
- Never import camera libraries at module level - import inside backend classes

### Recording Flow

1. User clicks record button → POST to `/api/record`
2. `RecordView.post()` spawns async thread to avoid blocking
3. Thread calls `camera.capture_swing()`
4. `capture_swing()` delegates to `backend.record()`
5. Metadata saved as JSON alongside video file
6. If upload enabled, background thread uploads to Google Drive
7. Recording status tracked via `camera.recording` flag

### Google Drive Integration

- Uses OAuth2 Desktop App flow
- Credentials file must be downloaded from Google Cloud Console
- Token stored in pickle file for reuse
- Uploads video + metadata JSON to specified folder
- Metadata updated with Drive file IDs and links
- Delete operations remove from both local storage and Drive

### File Organization

- `recordings/` - All recorded videos (gitignored)
- Each recording: `swing_YYYYMMDD_HHMMSS.h264` (or .mp4)
- Metadata: `swing_YYYYMMDD_HHMMSS.json`
- Metadata includes: timestamp, resolution, FPS, duration, shutter speed, file size, Drive links

## Platform-Specific Notes

### Raspberry Pi
- Python 3.13+ required
- picamera2 library (system package, not pip)
- Global shutter camera (IMX296) native resolution: 1456x1088
- Max FPS varies by resolution: 120fps @ 1456x1088, 200fps @ 728x544
- Systemd service file provided: `swing-camera.service`

### macOS
- OpenCV provides camera access (requires permissions)
- System Preferences → Security & Privacy → Camera
- Limited camera control vs Raspberry Pi
- Useful for UI development and testing
- Use `--demo` flag to bypass camera entirely

## Common Tasks

### Adding a New Camera Backend

1. Create new class in `camera_backends.py` inheriting from `CameraBackend`
2. Implement all abstract methods: `setup()`, `start()`, `stop()`, `record()`, `cleanup()`, `get_name()`
3. Add detection logic to `create_camera_backend()` factory
4. Update `CAMERA_BACKENDS.md` documentation

### Modifying Recording Settings

**Use the Settings UI (Recommended):**
1. Open `/settings` page
2. Select camera mode from preset cards
3. Adjust duration/format if needed
4. Click "Save Camera Mode"

**Via API:**
```bash
# Change camera mode (resolution, FPS, shutter)
curl -X POST http://localhost:5000/api/preset \
  -H "Content-Type: application/json" \
  -d '{"preset": "high_speed_400fps"}'

# Change duration/format only
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"duration": 5, "format": "h264"}'
```

**Adding New Presets:**
Edit `recording_presets.json` (see Configuration System section above for examples)

**DO NOT directly edit `config.json`** - it's auto-managed. Use Settings UI or `/api/preset` endpoint.

### Google Drive Setup

1. User uploads credentials JSON via web interface
2. Web interface initiates OAuth flow
3. User authorizes in browser
4. Token saved to `gdrive_token.pickle`
5. "Golf Swings" folder created automatically (or existing found)
6. Folder ID saved to `config.json` as `gdrive://folder_id`

### Debugging Recording Issues

- Check logs for backend selection: "Using camera backend: X"
- PiCamera2 errors: Check `vcgencmd get_camera`, cable connection
- OpenCV errors: Check camera permissions, test with `cv2.VideoCapture(0)`
- Demo mode: Always works, creates dummy files in `recordings/`
- Recording state: `camera.recording` flag must be False to start new recording

## Code Style & Conventions

- Python 3.13+ syntax and features
- Docstrings for all classes and public methods
- Logging via Python logging module (not print statements)
- Thread-safe recording with locks (`camera_lock` in web_interface.py)
- Flask views use `MethodView` class-based pattern
- Error handling: Try to gracefully degrade, log errors
- File paths: Use `pathlib.Path`, convert to string only when needed

## Important Constraints

- Only one recording can happen at a time (enforced by `recording` flag)
- PiCamera2 imports will fail on non-Pi systems (expected, graceful fallback)
- Google Drive uploads happen in background threads (non-blocking)
- Web interface runs on port 5000 by default
- Recordings directory created automatically if missing
- Config file preserves `_comments` field during updates
- OAuth flow requires `OAUTHLIB_INSECURE_TRANSPORT=1` for HTTP testing
