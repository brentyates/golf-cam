# Recommended Configurations

Different configurations optimized for various scenarios.

## Maximum Detail (Default)
**Best for: Detailed swing analysis, professional use**

```json
{
  "width": 1456,
  "height": 1088,
  "fps": 120,
  "shutter_speed": 2000,
  "duration": 10,
  "format": "h264"
}
```

- Full resolution of IMX296 global shutter camera
- 120 FPS = 4x slow motion at 30fps playback
- 1/500s shutter freezes fast motion
- ~10 Mbps bitrate

## Maximum Speed
**Best for: Ultra slow-motion, driver swings**

```json
{
  "width": 728,
  "height": 544,
  "fps": 200,
  "shutter_speed": 1500,
  "duration": 8,
  "format": "h264"
}
```

- Half resolution for double the frame rate
- 200 FPS = 6.7x slow motion at 30fps playback
- 1/666s shutter for very fast motion
- Great for driver and long iron swings

## Balanced
**Best for: Good detail with high speed, general use**

```json
{
  "width": 1152,
  "height": 864,
  "fps": 150,
  "shutter_speed": 1800,
  "duration": 10,
  "format": "h264"
}
```

- 75% resolution, 25% more FPS
- 150 FPS = 5x slow motion at 30fps playback
- Excellent balance of detail and motion capture

## Indoor / Low Light
**Best for: Indoor practice, cloudy days**

```json
{
  "width": 1456,
  "height": 1088,
  "fps": 90,
  "shutter_speed": 4000,
  "duration": 10,
  "format": "h264"
}
```

- Full resolution
- Reduced FPS to allow more light per frame
- 1/250s shutter (slower but still captures motion)
- May need additional lighting

## Short Form / Social Media
**Best for: Quick captures for Instagram, Twitter**

```json
{
  "width": 1080,
  "height": 1920,
  "fps": 120,
  "shutter_speed": 2000,
  "duration": 5,
  "format": "mp4"
}
```

- Vertical video format (9:16)
- Note: May need to adjust camera physically
- 5 second clips perfect for social media
- MP4 format for easy sharing

## Practice Session
**Best for: Extended practice with multiple swings**

```json
{
  "width": 1152,
  "height": 864,
  "fps": 120,
  "shutter_speed": 2000,
  "duration": 15,
  "format": "h264",
  "upload_enabled": true,
  "upload_destination": "s3://your-bucket/practice-sessions"
}
```

- Balanced quality and file size
- Longer duration to capture full practice swing
- Automatic upload to keep SD card clear

## Testing & Adjustment
**Best for: Fine-tuning your setup**

```json
{
  "width": 1456,
  "height": 1088,
  "fps": 60,
  "shutter_speed": 2000,
  "duration": 5,
  "format": "h264"
}
```

- Lower FPS for faster testing
- Short duration for quick iterations
- Full resolution to evaluate quality

## Shutter Speed Guide

Golf club speeds vary by club and player. Here's a guide:

| Club Speed (mph) | Recommended Shutter | Shutter Speed (μs) |
|------------------|---------------------|-------------------|
| 60-80 (wedges) | 1/400s | 2500 |
| 80-100 (irons) | 1/500s | 2000 |
| 100-120 (driver) | 1/666s | 1500 |
| 120+ (pros) | 1/800s | 1250 |

**Rule of thumb**: 
- Brighter conditions = faster shutter possible
- Indoor/cloudy = slower shutter needed (may get motion blur)
- If video is too dark, increase shutter_speed value (slower shutter)
- If motion is blurry, decrease shutter_speed value (faster shutter)

## FPS vs Resolution Trade-off

The camera has a maximum data rate. Higher resolution requires lower FPS and vice versa:

| Resolution | Max FPS | Notes |
|------------|---------|-------|
| 1456x1088 (Full) | 120 | Best quality |
| 1152x864 (75%) | 150 | Great balance |
| 1088x768 | 170 | Wide aspect |
| 728x544 (Half) | 200+ | Maximum speed |
| 640x480 (VGA) | 240+ | Ultra speed |

## Storage Considerations

Approximate file sizes for 10-second recordings:

| Resolution | FPS | Bitrate | File Size |
|------------|-----|---------|-----------|
| 1456x1088 | 120 | 10 Mbps | ~12 MB |
| 1152x864 | 150 | 8 Mbps | ~10 MB |
| 728x544 | 200 | 5 Mbps | ~6 MB |

On a 64GB SD card:
- Full quality: ~5,300 recordings (884 hours at 10s each)
- Balanced: ~6,400 recordings (1,067 hours)
- Maximum speed: ~10,600 recordings (1,767 hours)

## Lighting Recommendations

For best results:

1. **Outdoor Bright Sun**
   - Use fastest shutter speeds (1/800s - 1/1000s)
   - Maximum FPS possible
   - Consider polarizing filter to reduce glare

2. **Outdoor Cloudy/Shade**
   - Medium shutter speeds (1/400s - 1/500s)
   - May need to reduce FPS slightly
   - Good natural diffused light

3. **Indoor**
   - Slower shutter speeds (1/200s - 1/333s)
   - Reduce FPS to 90-120
   - Add LED panels (5000K-6500K color temp)
   - Need at least 2-3 lights for even coverage

4. **Indoor Practice Net**
   - Minimum 2x 50W LED panels
   - Position lights at 45° angles to subject
   - Avoid harsh shadows
   - May need to compromise on FPS

## Upload Configuration Examples

### Google Drive (Recommended)
```json
{
  "upload_enabled": true,
  "upload_destination": "gdrive://1a2b3c4d5e6f7g8h9i0j"
}
```

Setup:
```bash
python setup_gdrive.py
# Follow the prompts to authenticate
```

See `GDRIVE_SETUP.md` for detailed setup instructions.

### Home Server
```json
{
  "upload_enabled": true,
  "upload_destination": "user@192.168.1.100:/media/golf-videos"
}
```

Setup:
```bash
ssh-keygen -t ed25519
ssh-copy-id user@192.168.1.100
```

### NAS (Network Attached Storage)
```json
{
  "upload_enabled": true,
  "upload_destination": "user@nas.local:/volume1/golf"
}
```

## Testing Your Configuration

After changing config.json, test it:

```bash
source venv/bin/activate
python swing_camera.py --name "test_config"
```

Check the video:
1. Transfer to computer: `scp pi@raspberrypi.local:~/swing-cam/recordings/test_config.h264 .`
2. Play in VLC Media Player
3. Evaluate:
   - Is motion frozen clearly?
   - Is lighting adequate?
   - Is frame rate smooth in slow motion?
   - Is resolution detailed enough?

Adjust settings and repeat until satisfied!

