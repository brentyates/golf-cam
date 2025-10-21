# Google Drive Upload Setup

This guide will help you set up automatic uploads to Google Drive for your golf swing videos.

## Quick Setup (5 minutes)

### Step 1: Get Google Drive Credentials

1. **Go to Google Cloud Console**  
   Visit: https://console.cloud.google.com/

2. **Create a New Project**
   - Click "Select a project" at the top
   - Click "New Project"
   - Name it: "Golf Swing Camera"
   - Click "Create"

3. **Enable Google Drive API**
   - In the left menu, go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click on it, then click "Enable"

4. **Configure OAuth Consent Screen** (First time only)
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" (unless you have a Google Workspace)
   - Click "Create"
   - Fill in:
     - App name: "Golf Swing Camera"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Skip "Scopes" (click "Save and Continue")
   - Add yourself as a test user:
     - Click "Add Users"
     - Enter your email
   - Click "Save and Continue"

5. **Create OAuth Client ID**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Application type: **Desktop app**
   - Name: "Golf Swing Camera Desktop"
   - Click "Create"

6. **Download Credentials**
   - You'll see a popup with your client ID
   - Click "Download JSON"
   - Save the file

7. **Rename and Move**
   - Rename the downloaded file to: `gdrive_credentials.json`
   - Move it to your swing-cam directory

### Step 2: Run Setup Script

On your Raspberry Pi:

```bash
cd ~/swing-cam
source venv/bin/activate
python setup_gdrive.py
```

This will:
1. Open a browser window
2. Ask you to sign in to Google
3. Request permission to access your Drive
4. Save the authentication token
5. Create a "Golf Swings" folder in your Drive
6. Display the folder ID

### Step 3: Update Configuration

The setup script will show you the folder ID. Update your `config.json`:

```json
{
  "upload_enabled": true,
  "upload_destination": "gdrive://YOUR_FOLDER_ID_HERE"
}
```

Replace `YOUR_FOLDER_ID_HERE` with the actual folder ID from the setup script.

### Step 4: Test It!

Record a test swing:

```bash
python swing_camera.py --name "gdrive_test"
```

Check your Google Drive "Golf Swings" folder - the video should appear there automatically!

## How It Works

- Videos are uploaded in the background after recording
- Both the video file (.h264) and metadata (.json) are uploaded
- Upload happens automatically without blocking recording
- Files remain on the Pi until you delete them
- You can access videos from any device with Google Drive

## Folder Organization

You can create subfolders in Google Drive and use their IDs:

### Option 1: Use the Root "Golf Swings" Folder
```json
"upload_destination": "gdrive://1a2b3c4d5e6f7g8h9i0j"
```

### Option 2: Create Subfolders

In Google Drive, create:
```
Golf Swings/
  ├── Practice/
  ├── Lessons/
  └── Tournament/
```

Get each folder's ID by:
1. Right-click folder in Drive
2. Click "Share" > "Copy link"
3. Extract the ID from the URL:
   `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

Update config per session:
```json
"upload_destination": "gdrive://PRACTICE_FOLDER_ID"
```

## Multiple Configurations

Create different config files for different scenarios:

**config.practice.json**
```json
{
  "upload_enabled": true,
  "upload_destination": "gdrive://PRACTICE_FOLDER_ID",
  "duration": 15
}
```

**config.tournament.json**
```json
{
  "upload_enabled": true,
  "upload_destination": "gdrive://TOURNAMENT_FOLDER_ID",
  "duration": 10,
  "fps": 150
}
```

Use with:
```bash
python swing_camera.py --config config.practice.json
```

## Troubleshooting

### "gdrive_credentials.json not found"
- Make sure you downloaded the credentials file
- Check it's named exactly `gdrive_credentials.json`
- Verify it's in the swing-cam directory

### "Authentication failed"
- Try running `python setup_gdrive.py` again
- Delete `gdrive_token.pickle` and re-authenticate
- Make sure you're using the same Google account

### "Upload failed" in logs
- Check your internet connection
- Verify the folder ID in config.json
- Make sure the folder wasn't deleted
- Try re-running setup_gdrive.py

### Token expired
The system automatically refreshes tokens. If you see errors:
```bash
rm gdrive_token.pickle
python setup_gdrive.py
```

### Can't access from browser during setup
If you're running setup over SSH without a browser:

1. On your Pi:
```bash
python setup_gdrive.py
```

2. When it tries to open a browser, it will show a URL
3. Copy that URL
4. Open it in a browser on your computer
5. Complete the authentication
6. Copy the authorization code
7. Paste it back in the terminal

## Security Notes

- `gdrive_credentials.json` - Your OAuth client credentials (keep private)
- `gdrive_token.pickle` - Your access token (keep very private!)
- Add both to `.gitignore` (already done)
- Never commit these files to version control

## Viewing Your Videos

Your videos will be in Google Drive at:
```
My Drive > Golf Swings
```

You can:
- View them in the Drive app on your phone
- Download them for analysis
- Share links with your coach
- Organize into subfolders
- Access from any device

## Alternative: Upload to Specific Shared Folder

If you want to upload to a folder shared with your coach:

1. Have them share a folder with you
2. Open the folder in Google Drive
3. Get the folder ID from the URL
4. Use that ID in your config

The coach will automatically see new videos as they're uploaded!

## Bonus: Automatic Cleanup

To save space on your Pi, automatically delete local files after upload:

Add this to `swing_camera.py` after successful upload:

```python
# In _upload_to_gdrive, after the logger.info line:
if self.config.get('delete_after_upload', False):
    os.remove(file_path)
    metadata_path = Path(file_path).with_suffix('.json')
    if metadata_path.exists():
        os.remove(metadata_path)
    logger.info(f"Deleted local file: {file_path}")
```

Then in config.json:
```json
"delete_after_upload": true
```

## Questions?

- Check that Google Drive API is enabled in Cloud Console
- Verify OAuth consent screen is configured
- Make sure you're added as a test user
- Ensure the OAuth client is type "Desktop app"

Happy swinging! ⛳

