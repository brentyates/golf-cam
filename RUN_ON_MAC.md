# Running on Mac

You can run the web interface on your Mac in **three modes**:

1. **With Mac Camera** - Real video recording using your webcam
2. **Demo Mode** - UI testing without camera
3. **Automatic** - System picks best available

## Quick Start

### 1. Install Dependencies

```bash
cd ~/projects/swing-cam  # or wherever you cloned the project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Mac-friendly dependencies (includes OpenCV for camera)
pip install -r requirements-mac.txt
```

### 2. Enable Camera Access (For Real Recording)

If you want to use your Mac's camera:

1. Go to **System Settings** → **Privacy & Security** → **Camera**
2. Enable **Terminal** (or your terminal app)
3. Restart your terminal

### 3. Run the Application

```bash
source venv/bin/activate

# Automatic mode (uses Mac camera if available, else demo)
python web_interface.py

# Force demo mode (no camera needed)
python web_interface.py --demo
```

### 4. Open Browser

Visit: **http://localhost:5000**

## What Works in Demo Mode

✅ **Full Web Interface**
- Beautiful UI
- All pages load perfectly
- Settings page fully functional

✅ **Configuration Management**
- Edit camera settings
- Load presets
- Save configuration
- Test different values

✅ **Google Drive Setup**
- Upload credentials
- Complete OAuth flow
- Test connection
- Configure upload destination

✅ **Recording Simulation**
- Click "Record" button
- Simulates recording duration
- Creates dummy files
- Shows in recordings list

## What Doesn't Work

❌ **Actual Video Capture**
- No real camera access
- Creates placeholder files instead
- Good enough to test the workflow

❌ **Hardware-Specific Features**
- No real frame rate testing
- No actual shutter control

## Perfect For

- 👀 **Previewing the UI** before deploying to Pi
- ⚙️ **Testing configuration changes**
- 📱 **Seeing how it looks on different devices**
- 🧪 **Experimenting with Google Drive setup**
- 🎨 **Checking responsive design**
- 📝 **Writing documentation**

## Example Commands

### Basic Demo Mode
```bash
python web_interface.py --demo
```

### Custom Port
```bash
python web_interface.py --demo --port 8080
```

### Custom Config File
```bash
python web_interface.py --demo --config my-config.json
```

## Notes

- Demo mode automatically activates if camera libraries aren't installed
- All settings are saved to `config.json` as normal
- You can configure everything, then deploy the config to your Pi
- Great for testing before buying hardware!

## Testing Google Drive

You can fully test Google Drive integration on your Mac:

1. Start in demo mode: `python web_interface.py --demo`
2. Go to Settings
3. Upload your Google credentials
4. Authenticate
5. Test connection - works perfectly!
6. Enable upload
7. "Record" creates a dummy file
8. The dummy file gets uploaded to Drive!

This lets you verify your Google Drive setup works **before** deploying to the Pi.

## Deployment Workflow

**Develop on Mac:**
```bash
# Test UI and configuration
python web_interface.py --demo

# Adjust settings via web interface
# Test Google Drive setup
# Verify everything looks good
```

**Deploy to Pi:**
```bash
# Copy to Pi
./deploy.sh

# On Pi, run for real
python web_interface.py  # No --demo flag
```

Perfect workflow! 🎉

