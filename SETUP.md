# Raspberry Pi Setup Information

## Hardware
- **Device**: Raspberry Pi 5
- **Camera**: IMX296 Global Shutter Camera
- **Camera Interface**: Connected via CSI port

## Network Configuration
- **IP Address**: Find with `hostname -I` on the Pi
- **Web Interface**: http://raspberrypi.local:5000 (or http://YOUR_PI_IP:5000)
- **SSH Access**: `ssh pi@raspberrypi.local` (or `ssh pi@YOUR_PI_IP`)

## Project Location on Raspberry Pi
- **Directory**: `/home/pi/swing-cam/`
- **Virtual Environment**: `/home/pi/swing-cam/venv/`
- **Main Application**: `web_interface.py`

## Deployment Commands

### Deploy from Mac to Raspberry Pi
```bash
# Sync code to Raspberry Pi (adjust local path as needed)
rsync -av --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  ~/projects/swing-cam/ \
  pi@raspberrypi.local:/home/pi/swing-cam/

# Restart the application
ssh pi@raspberrypi.local "pkill -f 'python web_interface.py'"
ssh pi@raspberrypi.local "cd swing-cam && source venv/bin/activate && python web_interface.py"
```

### Start Application on Raspberry Pi
```bash
ssh pi@raspberrypi.local
cd swing-cam
source venv/bin/activate
python web_interface.py
```

## Camera Configuration
- **Default Resolution**: 1456x1088 (native)
- **Default FPS**: 120
- **Default Shutter Speed**: 2000μs
- **Supported Resolutions**:
  - 1456x1088 (Native, 120fps max)
  - 1152x864 (Balanced, 150fps max)
  - 728x544 (Speed, 200fps+ max)

## Application URLs
- **Home**: http://raspberrypi.local:5000/ (or http://YOUR_PI_IP:5000/)
- **Live Preview**: http://raspberrypi.local:5000/preview
- **Settings**: http://raspberrypi.local:5000/settings
- **Recordings**: http://raspberrypi.local:5000/recordings

## Video Storage
- **Output Directory**: `/home/pi/swing-cam/recordings/`
- **Format**: MP4 (H.264)
- **Naming**: `recording_YYYYMMDD_HHMMSS.mp4`

## Python Environment
- **Python Version**: 3.11+
- **Key Dependencies**:
  - picamera2 (Raspberry Pi camera interface)
  - Flask (web framework)
  - libcamera (camera control library)

## Notes
- The camera uses a global shutter sensor (IMX296) which eliminates rolling shutter artifacts
- All recordings preserve the full frame rate without frame dropping
- Live preview uses MJPEG streaming with real-time camera controls
