# 🚀 Quick Start Guide

## Setup (One Time)

### 1. Deploy to Raspberry Pi

From your Mac:
```bash
cd ~/projects/swing-cam  # or wherever you cloned the project
./deploy.sh raspberrypi.local
```

### 2. Install on Raspberry Pi

SSH into your Pi:
```bash
ssh pi@raspberrypi.local
cd ~/swing-cam
./setup.sh
```

Wait for installation to complete (~5 minutes).

### 3. Start the Web Interface

```bash
source venv/bin/activate
python web_interface.py
```

### 4. Open in Browser

From any device on your network, visit:
```
http://raspberrypi.local:5000
```

Or find your Pi's IP:
```bash
hostname -I
```

Then visit: `http://192.168.1.XXX:5000`

## Configure Settings (First Time)

### Via Web Interface (Easy!)

1. Click **⚙️ Settings** button in the web interface

2. **Camera Settings** are already optimized, but you can:
   - Try different presets (Max Detail, Max Speed, etc.)
   - Adjust resolution, FPS, shutter speed
   - Change recording duration

3. **Google Drive Upload** (optional):
   
   a. **Get Google Drive Credentials:**
      - Visit: https://console.cloud.google.com/
      - Create project → Enable Google Drive API
      - Create OAuth Desktop credentials
      - Download JSON file
   
   b. **Upload in Web Interface:**
      - In Settings → Google Drive section
      - Click "📁 Click to upload gdrive_credentials.json"
      - Select your downloaded file
   
   c. **Authenticate:**
      - Click "🔐 Authenticate with Google"
      - Sign in to Google in the popup
      - Grant permissions
      - You'll be redirected back with folder ID auto-filled!
   
   d. **Enable Upload:**
      - Check "Enable automatic upload"
      - Click "Save Camera Settings"

4. **Test Everything:**
   - Click "🧪 Test Connection" to verify Google Drive
   - Go back to home and record a test swing!

## Daily Use

### Option 1: Web Interface (Easiest)

1. Visit `http://raspberrypi.local:5000`
2. Click **🎥 Record Swing**
3. Swing away!
4. Download or view in Google Drive

### Option 2: Command Line

```bash
cd ~/swing-cam
source venv/bin/activate
python swing_camera.py
```

Press ENTER when ready to record.

### Option 3: Physical Button

Connect a button between GPIO 17 and ground, then:

```bash
python button_trigger.py
```

Press button to record!

## Auto-Start on Boot (Optional)

To make it start automatically:

```bash
sudo cp swing-camera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable swing-camera
sudo systemctl start swing-camera
```

Now the web interface starts on boot!
Access at: `http://raspberrypi.local:5000`

## Quick Tips

### Change Settings
- All settings in web interface under **⚙️ Settings**
- Changes apply immediately
- Try presets for different scenarios

### View Recordings
- Listed on main page
- Click Download to save locally
- Or check your Google Drive "Golf Swings" folder

### Troubleshooting

**Camera not working?**
```bash
vcgencmd get_camera
```
Should show `detected=1`

**Can't access web interface?**
```bash
# Find Pi's IP
hostname -I

# Make sure service is running
sudo systemctl status swing-camera
```

**Video too dark?**
- Go to Settings → increase shutter_speed value

**Motion blur?**
- Go to Settings → decrease shutter_speed value

## That's It! 🎉

You're ready to capture amazing golf swing footage!

**Key Points:**
- 📹 Main page: Record swings
- ⚙️ Settings page: Configure everything
- ☁️ Google Drive: Automatic backup
- 📱 Access from phone/tablet/computer

Happy swinging! ⛳

