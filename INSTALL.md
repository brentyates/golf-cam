# Quick Installation Guide

## On Your Computer (for development)

1. Clone this repository:
```bash
cd ~/projects
git clone <your-repo-url> swing-cam
cd swing-cam
```

2. This is designed to run on Raspberry Pi 5, so just copy the files over using the transfer method below.

## On Raspberry Pi 5

### First-Time Setup

1. **Flash Raspberry Pi OS** (64-bit, Bookworm or later)
   - Use Raspberry Pi Imager
   - Configure WiFi and SSH during imaging

2. **Connect to Pi** via SSH:
```bash
ssh pi@raspberrypi.local
```

3. **Transfer files to Pi**:

From your computer:
```bash
scp -r ~/projects/swing-cam pi@raspberrypi.local:~/
```

Or use rsync:
```bash
rsync -avz ~/projects/swing-cam/ pi@raspberrypi.local:~/swing-cam/
```

4. **Run setup on Pi**:
```bash
cd ~/swing-cam
chmod +x setup.sh
./setup.sh
```

5. **Test the camera**:
```bash
source venv/bin/activate
python swing_camera.py --list
```

6. **Start web interface**:
```bash
python web_interface.py
```

7. **Access from your phone/computer**:
```
http://raspberrypi.local:5000
```

Or find Pi's IP address:
```bash
hostname -I
```

Then visit: `http://192.168.1.XXX:5000`

8. **Configure via Web Interface**:
   - Click **⚙️ Settings** in the web interface
   - Adjust camera settings, load presets
   - Set up Google Drive upload (all in browser!)
   - No need to manually edit config files!

### Optional: Auto-Start on Boot

To make the camera web interface start automatically:

```bash
sudo cp swing-camera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable swing-camera
sudo systemctl start swing-camera
```

Check status:
```bash
sudo systemctl status swing-camera
```

## Quick Test

After setup, test everything works:

```bash
cd ~/swing-cam
source venv/bin/activate
python swing_camera.py
```

Press ENTER when prompted. You should see:
```
Golf Swing Camera Ready!
Press ENTER to record a 10s swing video...
```

Press ENTER, wait 10 seconds, and check the `recordings/` folder.

## Troubleshooting

### Camera not found

```bash
vcgencmd get_camera
```

Should show: `supported=1 detected=1`

If not:
1. Power off Pi
2. Check camera cable connection
3. Power on and run: `sudo raspi-config`
4. Navigate to Interface Options → Camera → Enable
5. Reboot

### Permission errors

```bash
sudo usermod -aG video $USER
logout
```

Then log back in.

### Can't access web interface

1. Check Pi's IP: `hostname -I`
2. Make sure firewall allows port 5000
3. Try accessing from Pi itself: `curl http://localhost:5000`

## Next Steps

- Read `README.md` for full documentation
- Adjust settings in `config.json`
- Set up automatic uploads if desired
- Mount camera on tripod for stable capture

Enjoy capturing your golf swing! ⛳

