# Recording Presets - Quick Guide

## Available Presets

### 240 FPS - Ultra Slow Motion (Recommended for Golf Impact)
- **Resolution:** 512x384
- **Frame Rate:** ~240 FPS
- **Slow Motion:** 4x playback
- **Shutter Speed:** 500μs (1/2000s)
- **Best For:** Golf ball impact, extremely fast motion
- **Config File:** `config_240fps.json`

### 120 FPS - Slow Motion (Tested & Working)
- **Resolution:** 728x544
- **Frame Rate:** ~118 FPS (confirmed)
- **Slow Motion:** 2x playback
- **Shutter Speed:** 1000μs (1/1000s)
- **Best For:** Golf swings, general fast motion
- **Config File:** `config_120fps.json`

### 60 FPS - Standard (Full Resolution)
- **Resolution:** 1456x1088
- **Frame Rate:** 60 FPS
- **Slow Motion:** None (real-time)
- **Shutter Speed:** 2000μs (1/500s)
- **Best For:** Maximum quality, standard recording
- **Config File:** `config.json` (default)

## Quick Switch Methods

### Method 1: Using the Switch Script (Easiest)

```bash
cd ~/swing-cam
./switch_preset.sh 240    # Switch to 240 FPS
./switch_preset.sh 120    # Switch to 120 FPS
./switch_preset.sh standard  # Back to default

# Then restart server:
pkill -f web_interface
source venv/bin/activate
python web_interface.py --debug
```

### Method 2: Manual Copy

```bash
cd ~/swing-cam

# Apply 240 FPS preset:
cp config_240fps.json config.json

# Apply 120 FPS preset:
cp config_120fps.json config.json

# Restart server:
pkill -f web_interface
source venv/bin/activate
python web_interface.py --debug
```

### Method 3: Via Web Interface

1. Go to Settings page
2. Update Width, Height, FPS manually:
   - **240 FPS**: Width=512, Height=384, FPS=240
   - **120 FPS**: Width=728, Height=544, FPS=120
3. Save Settings

## Testing the Preset

After applying a preset and restarting, check the logs:

```bash
tail -50 ~/swing-cam/flask.log | grep -E "(crop|FPS|Camera configured)"
```

You should see:
```
Sensor crop applied: 512x384 (media1, 11-001a)
Camera configured: 512x384 @ 240.96 FPS
```

## Expected FPS Results

| Config FPS | Actual FPS | Resolution | Status |
|-----------|------------|------------|---------|
| 240       | ~240-250   | 512x384    | ⏳ To test |
| 120       | ~118       | 728x544    | ✅ Confirmed |
| 60        | ~60        | 1456x1088  | ✅ Confirmed |

## Notes

- The actual FPS may vary slightly from the requested FPS
- Smaller resolutions = higher FPS (sensor cropping unlocks speed)
- Shutter speed should be roughly 1/(2×FPS) for motion blur
- 240 FPS preset untested but should work based on PiTrac data
- The system automatically applies sensor cropping for FPS > 60
