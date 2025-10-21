# 📹 High-Speed Impact Camera

A high-performance video capture system built for Raspberry Pi 5 with global shutter camera. Optimized for capturing fast motion events like golf swings, ball impacts, and other high-speed activities with minimal rolling shutter artifacts and excellent detail.

## Features

- **High Frame Rate**: 120 FPS capture (configurable up to 200+ FPS)
- **Global Shutter**: Eliminates rolling shutter artifacts for crisp motion capture
- **Optimized Settings**: Fast shutter speeds (1/500s default) to freeze motion
- **Easy Control**: Web interface + command-line interface
- **Automatic Upload**: Optional automatic upload to S3 or remote server
- **Metadata Tracking**: Automatic recording metadata and timestamps
- **Instant Playback**: Download and review recordings immediately

## Hardware Requirements

- Raspberry Pi 5 (8GB recommended)
- Raspberry Pi Global Shutter Camera (IMX296 or compatible)
- MicroSD card (64GB+ recommended for storing videos)
- Power supply (5V/5A for Pi 5)
- Optional: Physical button for triggering recordings
- Optional: Tripod mount for stable positioning

## Software Setup

### 1. Install Raspberry Pi OS

Use Raspberry Pi Imager to install the latest 64-bit Raspberry Pi OS (Bookworm or later).

**Requirements:**
- Python 3.13 or newer
- Raspberry Pi OS 64-bit

### 2. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Install Dependencies

```bash
sudo apt install -y python3-pip python3-venv python3-picamera2 python3-libcamera
```

### 4. Clone/Copy Project

```bash
cd ~
git clone <your-repo> swing-cam
cd swing-cam
```

### 5. Create Virtual Environment

```bash
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Note:** This project requires Python 3.13 or newer.

## Configuration

Edit `config.json` to customize settings:

```json
{
  "width": 1456,
  "height": 1088,
  "fps": 120,
  "duration": 3,
  "shutter_speed": 2000,
  "format": "h264",
  "upload_enabled": false,
  "upload_destination": ""
}
```

### Key Settings

- **Resolution**: `1456x1088` is native for IMX296. Lower resolutions enable higher FPS
- **FPS**: `120` provides excellent slow-motion. Can go up to 200+ at lower resolutions
- **Shutter Speed**: `2000` microseconds = 1/500s. Adjust based on lighting
- **Duration**: Recording length in seconds (minimum 1s for impact capture, 3-5s typical for swings)
- **Format**: `h264` for raw stream (smaller), `mp4` for container

### Frame Rate vs Resolution Guide

| Resolution | Max FPS | Use Case |
|------------|---------|----------|
| 1456x1088 | 120 | High detail, excellent slow-mo |
| 1152x864 | 150 | Balanced quality and speed |
| 728x544 | 200+ | Maximum speed capture |

## Usage

### Option 1: Web Interface (Recommended)

Start the web server:

```bash
source venv/bin/activate
python web_interface.py
```

Then open a browser and navigate to:
```
http://raspberrypi.local:5000
```

Or use the Pi's IP address:
```
http://192.168.1.XXX:5000
```

The web interface provides:
- One-click recording
- Real-time status display
- Recording history
- Instant download
- **Complete settings management**
- **Built-in Google Drive setup**
- **Configuration presets**

### Option 2: Command Line

Simple interactive mode:
```bash
source venv/bin/activate
python swing_camera.py
```

Press ENTER to trigger each recording.

With custom name:
```bash
python swing_camera.py --name "driver_swing_1"
```

List all recordings:
```bash
python swing_camera.py --list
```

### Option 3: Auto-Start with Systemd

Create `/etc/systemd/system/swing-camera.service`:

```ini
[Unit]
Description=Golf Swing Camera Web Interface
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/swing-cam
ExecStart=/home/pi/swing-cam/venv/bin/python web_interface.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable swing-camera
sudo systemctl start swing-camera
```

## Automatic Upload

### Upload to Google Drive (Recommended)

1. Run the setup script:
```bash
source venv/bin/activate
python setup_gdrive.py
```

This will guide you through getting Google Drive credentials and will automatically create a "Golf Swings" folder.

2. Update `config.json` with the folder ID provided:
```json
{
  "upload_enabled": true,
  "upload_destination": "gdrive://your-folder-id-here"
}
```

See `GDRIVE_SETUP.md` for detailed instructions!

### Upload via rsync (Alternative)

1. Set up SSH key authentication with remote server

2. Update `config.json`:
```json
{
  "upload_enabled": true,
  "upload_destination": "user@yourserver.com:/path/to/swings"
}
```

## Camera Positioning Tips

For best golf swing capture:

1. **Side View** (most common):
   - Position camera perpendicular to target line
   - 10-15 feet away from golfer
   - Waist to chest height
   - Frame should include club at address and full follow-through

2. **Face-On View**:
   - Position camera directly in front or behind golfer
   - Far enough to capture full swing width
   - Useful for checking alignment and posture

3. **Down-the-Line View**:
   - Position behind golfer, looking toward target
   - Great for checking swing plane
   - May need to adjust for ball flight safety

## Optimizing Performance

### Maximize FPS

1. Lower resolution: `728x544` can achieve 200+ FPS
2. Reduce bitrate: Lower values in encoder settings
3. Disable unnecessary services:
```bash
sudo systemctl disable bluetooth
sudo systemctl disable avahi-daemon
```

### Improve Video Quality

1. Adjust shutter speed based on lighting:
   - Bright outdoor: 1000-2000μs (1/1000s - 1/500s)
   - Indoor/cloudy: 3000-5000μs (1/333s - 1/200s)

2. Increase bitrate in `swing_camera.py`:
```python
encoder = H264Encoder(bitrate=15000000)  # 15 Mbps
```

3. Use consistent lighting to avoid auto-exposure changes

## Playback & Analysis

Recorded videos can be played in:
- VLC Media Player (supports h264 streams)
- DaVinci Resolve (for professional analysis)
- Any video player that supports h264/mp4

For slow-motion playback, the 120 FPS videos will play smoothly at 30 FPS (4x slow motion) or 60 FPS (2x slow motion).

## Troubleshooting

### Camera Not Detected

```bash
vcgencmd get_camera
```

Should show `supported=1 detected=1`. If not:
1. Check camera cable connection
2. Enable camera in `raspi-config`
3. Reboot

### Low Frame Rate

1. Check CPU temperature: `vcgencmd measure_temp`
2. Ensure adequate cooling
3. Close unnecessary applications
4. Lower resolution or bitrate

### Storage Full

Recordings are stored in `./recordings/`. To manage:

```bash
rm ./recordings/swing_*.h264
```

Or set up automatic cleanup in config.

## Advanced: Hardware Button Trigger

Add a physical button to GPIO pins for instant recording:

```python
from gpiozero import Button

button = Button(17)  # GPIO 17
button.when_pressed = lambda: camera.capture_swing()
```

## Performance Specs

With Raspberry Pi 5 and IMX296 Global Shutter Camera:

| Setting | Performance |
|---------|-------------|
| 1456x1088 @ 120fps | ~10 Mbps, smooth capture |
| 1152x864 @ 150fps | ~8 Mbps, excellent motion |
| 728x544 @ 200fps | ~5 Mbps, maximum speed |

Recording times per 64GB card:
- At 10 Mbps: ~14 hours
- At 8 Mbps: ~17 hours
- At 5 Mbps: ~28 hours

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - see LICENSE file for details

