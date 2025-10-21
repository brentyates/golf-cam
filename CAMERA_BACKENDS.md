# Camera Backend System

The swing camera now supports **multiple camera backends** with automatic detection and graceful degradation!

## 🎯 Supported Backends

### 1. **PiCamera2 (Best - Raspberry Pi Global Shutter)**
- ✅ Hardware H.264 encoding
- ✅ Global shutter support
- ✅ Manual exposure control
- ✅ High frame rates (120-240 FPS)
- ✅ Low latency
- ✅ Minimal rolling shutter artifacts
- 🎯 **Perfect for golf swings**

**Availability**: Raspberry Pi 5 with global shutter camera

### 2. **OpenCV (Good - Mac/Generic USB Cameras)**
- ✅ Works on Mac, Windows, Linux
- ✅ Standard webcam support
- ✅ Actual video recording
- ⚠️ Software encoding (higher CPU usage)
- ⚠️ Rolling shutter (standard cameras)
- ⚠️ Limited manual controls
- ⚠️ Lower frame rates typically
- 🧪 **Perfect for development/testing**

**Availability**: Mac, Linux, Windows with USB camera or built-in webcam

### 3. **Demo Mode (UI Testing)**
- ✅ No hardware required
- ✅ All UI features work
- ⚠️ Creates dummy files only
- 📱 **Perfect for UI preview**

**Availability**: Any system (fallback)

## 🔄 Automatic Selection

The system automatically selects the best available backend:

```
1. Try PiCamera2 (Raspberry Pi)
   └─ Success? → Use global shutter camera ✓
   └─ Failed? → Continue...

2. Try OpenCV (Generic camera)
   └─ Camera detected? → Use OpenCV backend ✓
   └─ No camera? → Continue...

3. Fallback to Demo Mode ✓
```

## 💻 Usage Examples

### On Raspberry Pi (Automatic - Best Quality)
```bash
python web_interface.py
```
Output: `✓ PiCamera2 available - using global shutter camera`

### On Mac with Camera (Automatic - Real Recording)
```bash
python web_interface.py
```
Output: `✓ OpenCV camera available - using generic camera`

### Force Demo Mode (Any System)
```bash
python web_interface.py --demo
```
Output: `Using camera backend: Demo Mode (No Camera)`

## 🎬 Recording Differences

### PiCamera2 (Pi with Global Shutter)
```python
Resolution: 1456x1088 @ 120fps
Encoding: Hardware H.264
Shutter: 1/500s (2000μs) - Fast!
Rolling Shutter: None (global shutter)
File: .h264 or .mp4
Quality: Excellent for fast motion
```

### OpenCV (Mac/Generic)
```python
Resolution: Varies by camera (e.g., 1280x720)
Encoding: Software (MP4)
Shutter: Automatic (camera dependent)
Rolling Shutter: Yes (typical webcams)
File: .mp4
Quality: Good for testing, may have motion blur
```

### Demo Mode
```python
Resolution: N/A (simulated)
Encoding: N/A
File: Dummy placeholder
Quality: UI testing only
```

## 🛠️ Installation

### For Raspberry Pi
```bash
# Already includes PiCamera2
pip install -r requirements.txt
```

### For Mac/Generic (with camera support)
```bash
# Includes OpenCV for camera access
pip install -r requirements-mac.txt
```

### For Demo Only
```bash
# Minimal install
pip install Flask google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## 📊 Feature Comparison

| Feature | PiCamera2 | OpenCV | Demo |
|---------|-----------|--------|------|
| Real Recording | ✅ | ✅ | ❌ |
| High FPS (120+) | ✅ | ⚠️ Limited | N/A |
| Global Shutter | ✅ | ❌ | N/A |
| Manual Exposure | ✅ | ⚠️ Limited | N/A |
| Hardware Encoding | ✅ | ❌ | N/A |
| Mac Support | ❌ | ✅ | ✅ |
| Pi Support | ✅ | ⚠️ Works | ✅ |
| UI Testing | ✅ | ✅ | ✅ |
| Golf Swing Quality | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | N/A |

## 🎨 Code Architecture

The system uses a clean **Strategy Pattern**:

```python
camera_backends.py
├── CameraBackend (Abstract Base Class)
│   ├── setup()
│   ├── start()
│   ├── stop()
│   ├── record()
│   ├── cleanup()
│   └── get_name()
│
├── PiCamera2Backend
│   └── Optimized for global shutter
│
├── OpenCVBackend
│   └── Generic camera support
│
└── DemoBackend
    └── No hardware required

swing_camera.py
└── Uses backend via abstraction
    └── Backend-agnostic
```

**Benefits:**
- ✨ Clean separation of concerns
- ✨ Easy to add new backends
- ✨ No conditionals in main code
- ✨ Each backend optimized independently

## 🧪 Development Workflow

### On Mac (with actual camera)
```bash
# Install with camera support
pip install -r requirements-mac.txt

# Run with your Mac camera
python web_interface.py

# System detects camera automatically
# Records actual video!
# Test settings, presets, uploads
```

### Deploy to Pi
```bash
# Transfer to Pi
./deploy.sh

# On Pi, same command
python web_interface.py

# Automatically uses PiCamera2!
# Full global shutter features
```

## 🔍 Detecting Your Backend

Check the console output when starting:

```bash
# PiCamera2 (Pi)
INFO - Attempting to initialize PiCamera2...
INFO - ✓ PiCamera2 available - using global shutter camera
INFO - Using camera backend: PiCamera2 (Global Shutter)

# OpenCV (Mac)
INFO - PiCamera2 not available (expected on non-Pi systems)
INFO - Attempting to initialize OpenCV camera...
INFO - ✓ OpenCV camera available - using generic camera
INFO - Using camera backend: OpenCV (Generic Camera)

# Demo (No camera)
INFO - PiCamera2 not available (expected on non-Pi systems)
INFO - OpenCV not available
INFO - No camera hardware detected - using demo mode
INFO - Using camera backend: Demo Mode (No Camera)
```

## ⚙️ Advanced: Backend-Specific Settings

### PiCamera2 Settings (Full Control)
- Resolution: Up to native sensor size
- FPS: Up to 200+ depending on resolution
- Shutter speed: Microsecond precision
- Gain: Manual analog gain
- Auto controls: Can be disabled
- Buffer management: Configurable

### OpenCV Settings (Limited)
- Resolution: Camera-dependent
- FPS: Camera-dependent
- Shutter speed: Usually automatic
- Gain: Usually automatic
- Auto controls: Camera firmware dependent
- Buffer management: Fixed

The web interface works the same regardless of backend - settings that aren't supported are gracefully handled!

## 💡 Tips

1. **Development on Mac**: Use OpenCV backend to test everything with real video
2. **UI Testing**: Use `--demo` flag for instant startup without camera
3. **Production on Pi**: Automatic selection gives best quality
4. **Testing settings**: OpenCV lets you verify configurations before Pi deployment

## 🐛 Troubleshooting

### "No camera detected" on Mac
```bash
# Check camera permissions in System Preferences
# → Security & Privacy → Camera
# → Allow Terminal/Your App

# Test camera works
python -c "import cv2; cam = cv2.VideoCapture(0); print('OK' if cam.isOpened() else 'FAIL')"
```

### "PiCamera2 failed" on Pi
```bash
# Check camera connection
vcgencmd get_camera

# Should show: detected=1

# Enable camera interface
sudo raspi-config
# → Interface Options → Camera → Enable
```

### Want to force a specific backend?
Modify `swing_camera.py`:
```python
# Force demo mode
backend = DemoBackend()

# Force OpenCV on Pi (for testing)
backend = OpenCVBackend()
```

---

**The beauty of this system**: Same code, same web interface, different backends - automatically selected for optimal performance on each platform! 🎉

