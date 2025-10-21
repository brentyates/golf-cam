# Development Workflow

This document describes the automated development workflow for the swing camera project.

## Quick Start

**Development Mode (Auto-sync + Auto-reload):**

1. Start the file watcher on your Mac:
   ```bash
   source venv/bin/activate
   python dev-watch.py
   ```

2. Make code changes on your Mac - they'll automatically:
   - Sync to the Pi within 1 second
   - Trigger Flask's auto-reload
   - Update the running web interface

3. Access the web interface via SSH tunnel:
   ```bash
   # In a separate terminal
   ssh -L 5000:localhost:5000 pi@raspberrypi.local  # or pi@YOUR_PI_IP_ADDRESS
   # Then browse to http://localhost:5000
   ```

## How It Works

### File Watcher (`dev-watch.py`)
- Watches local directory for Python, HTML, JS, CSS changes
- Automatically rsyncs changes to Pi
- Batches rapid changes (1 second debounce)
- Ignores venv, __pycache__, recordings, etc.

### Flask Debug Mode (`--debug` flag)
- Monitors Python files for changes
- Automatically reloads the web server when files change
- Shows detailed error pages with stack traces
- Enables Flask development server features

### SSH Tunnel
- Securely forwards port 5000 through SSH
- No need to expose web interface to internet
- All traffic encrypted

## Development Commands

### Start Dev Mode
```bash
# On Mac: Start file watcher
source venv/bin/activate
python dev-watch.py

# Pi should already be running with --debug flag:
# python web_interface.py --debug
```

### Custom Pi Address
```bash
# If your Pi has a different address
python dev-watch.py 192.168.1.100 pi /home/pi/swing-cam
```

### Manual Sync (without watching)
```bash
# One-time sync (adjust your local path as needed)
rsync -av --exclude 'venv' --exclude '__pycache__' --exclude '*.pyc' \
  ~/projects/swing-cam/ pi@raspberrypi.local:~/swing-cam/
```

### Restart Pi Server
```bash
# Restart with debug mode
ssh pi@raspberrypi.local "pkill -f 'python web_interface.py'" && \
ssh pi@raspberrypi.local "cd swing-cam && source venv/bin/activate && python web_interface.py --debug"
```

## Typical Workflow

1. **Morning Setup:**
   ```bash
   # Terminal 1: SSH tunnel
   ssh -L 5000:localhost:5000 pi@raspberrypi.local

   # Terminal 2: File watcher
   cd ~/projects/swing-cam
   source venv/bin/activate
   python dev-watch.py  # Add your Pi's IP if not using default
   ```

2. **Edit Code:**
   - Edit files in your favorite editor on Mac
   - Save the file
   - File watcher syncs to Pi (~1 second)
   - Flask auto-reloads (~1 second)
   - Refresh browser to see changes

3. **View Logs:**
   ```bash
   # SSH into Pi to view Flask logs
   ssh pi@raspberrypi.local
   # Check running processes
   ps aux | grep python
   ```

## Files That Trigger Reload

### Auto-reload triggers:
- `*.py` - Python source files
- `templates/*.html` - Jinja templates
- `static/*.css` - Stylesheets
- `static/*.js` - JavaScript files

### Ignored:
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
- `*.pyc` - Compiled Python
- `recordings/` - Video files
- `.git/` - Git repository

## Production Deployment

When ready to deploy to production:

```bash
# Disable debug mode
ssh pi@raspberrypi.local "cd swing-cam && source venv/bin/activate && python web_interface.py"
```

**Never run `--debug` in production!** It:
- Exposes source code in error pages
- Allows arbitrary code execution via debugger
- Has performance overhead

## Troubleshooting

### File watcher not syncing
```bash
# Check if watchdog is installed
pip list | grep watchdog

# Install if missing
pip install watchdog
```

### Pi not auto-reloading
```bash
# Verify debug mode is enabled
ssh pi@raspberrypi.local "ps aux | grep 'python web_interface.py'"
# Should show --debug flag

# Restart with debug mode
ssh pi@raspberrypi.local "pkill -f 'python web_interface.py'" && \
ssh pi@raspberrypi.local "cd swing-cam && source venv/bin/activate && python web_interface.py --debug"
```

### Connection issues
```bash
# Test SSH connection
ssh pi@raspberrypi.local

# Test rsync
rsync -av --dry-run ~/projects/swing-cam/ pi@raspberrypi.local:~/swing-cam/
```

## Tips

- Keep the file watcher terminal visible to see sync status
- Browser refresh may be cached - use Cmd+Shift+R (Mac) to hard refresh
- Template changes require browser refresh, Python changes auto-reload
- Large file changes may take 2-3 seconds to sync and reload
