# 🏌️ Quick Reference Card

## Fast Commands

### Start Web Interface
```bash
cd ~/swing-cam
source venv/bin/activate
python web_interface.py
```
Access: `http://raspberrypi.local:5000`

**New:** All settings now configurable via web interface! Click ⚙️ Settings

### Command Line Recording
```bash
cd ~/swing-cam
source venv/bin/activate
python swing_camera.py
```
Press ENTER to record

### List Recordings
```bash
python swing_camera.py --list
```

### Button Trigger Mode
```bash
python button_trigger.py
```
Press physical button to record

## Configuration Presets

**Maximum Detail** - 1456x1088 @ 120fps, 1/500s shutter  
**Maximum Speed** - 728x544 @ 200fps, 1/666s shutter  
**Balanced** - 1152x864 @ 150fps, 1/500s shutter  
**Low Light** - 1456x1088 @ 90fps, 1/250s shutter

Edit `config.json` and restart to change.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Camera not found | `vcgencmd get_camera` should show detected=1 |
| Video too dark | Increase `shutter_speed` value in config.json |
| Motion blur | Decrease `shutter_speed` value |
| Can't access web | Check IP: `hostname -I` |
| Low FPS | Lower resolution or close other apps |
| Storage full | Delete old files: `rm recordings/swing_*.h264` |

## File Locations

- **Recordings**: `~/swing-cam/recordings/`
- **Config**: `~/swing-cam/config.json`
- **Logs**: Check terminal output

## Transfer Files

### From Pi to Computer
```bash
scp pi@raspberrypi.local:~/swing-cam/recordings/*.h264 .
```

### View Remotely
```bash
rsync -avz pi@raspberrypi.local:~/swing-cam/recordings/ ./my-swings/
```

## Camera Positioning

**Side View** (most common):
- 10-15 feet away
- Perpendicular to target line  
- Waist to chest height
- Frame full swing arc

**Face-On View**:
- Directly in front or behind
- Check alignment and posture

## Service Management

### Auto-start on boot
```bash
sudo systemctl enable swing-camera
sudo systemctl start swing-camera
```

### Stop service
```bash
sudo systemctl stop swing-camera
```

### Check status
```bash
sudo systemctl status swing-camera
```

## Performance Tips

1. **More FPS**: Lower resolution in config
2. **Better Quality**: Increase bitrate in code
3. **Save Storage**: Lower bitrate or use shorter duration
4. **Faster Upload**: Use wired ethernet instead of WiFi
5. **Consistent Results**: Use manual exposure (already configured)

## Key Settings Explained

```json
{
  "width": 1456,          // Resolution width
  "height": 1088,         // Resolution height  
  "fps": 120,             // Frames per second
  "shutter_speed": 2000,  // Microseconds (2000 = 1/500s)
  "duration": 10,         // Recording length in seconds
  "format": "h264"        // Video format
}
```

## Shutter Speed Quick Ref

- 1000 μs = 1/1000s (very fast, needs bright light)
- 2000 μs = 1/500s (recommended for outdoor)
- 3000 μs = 1/333s (good for cloudy days)
- 5000 μs = 1/200s (indoor with good lighting)

## Support & Info

- Full docs: `README.md`
- Configurations: `CONFIGURATIONS.md`
- Installation: `INSTALL.md`

## Emergency Reset

If something breaks:
```bash
cd ~/swing-cam
git reset --hard  # if using git
cp config.json config.backup.json
# Restore from backup or reinstall
```

---

**Pro Tip**: Keep camera lens clean, use consistent lighting, and position camera before golfer addresses the ball for best results! ⛳

