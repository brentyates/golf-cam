# Private Configuration Setup

This document explains how to configure your private/local settings for the swing camera project.

## Overview

The project uses gitignored files to store your private configuration, so you can:
- Keep sensitive data local (never committed to git)
- Easily use personal IP addresses and credentials
- Share the codebase without exposing private information

## Configuration Files (All Gitignored)

### 1. `.env.local` - Network Configuration

**Purpose:** Store your Raspberry Pi's network information for development tools.

**Setup:**
```bash
# Copy the template
cp .env.local.template .env.local

# Edit with your values
nano .env.local
```

**Example `.env.local`:**
```bash
# Your Raspberry Pi's IP address (public or local)
PI_IP_ADDRESS=192.168.1.100
# Or if using remote access:
# PI_IP_ADDRESS=YOUR_PUBLIC_IP

# SSH username (usually 'pi')
PI_USER=pi

# Remote path on Pi
PI_REMOTE_PATH=/home/pi/swing-cam
```

**Used by:**
- `dev-watch.py` - Auto-sync development tool
- Can be referenced by custom scripts

### 2. `gdrive_credentials.json` - Google Drive OAuth

**Purpose:** Store your Google Drive API credentials.

**Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable Google Drive API
4. Create OAuth 2.0 Desktop credentials
5. Download the JSON file as `gdrive_credentials.json`
6. Place in project root

**Security:**
- Already in `.gitignore`
- Never commit this file
- Keep it secure on your local machine

### 3. `gdrive_token.pickle` - OAuth Token

**Purpose:** Store your authenticated Google Drive session.

**Setup:**
- Auto-generated after first OAuth flow
- Already in `.gitignore`
- Delete this file to re-authenticate

### 4. `config.json` - May Contain Private Data

**Important:** The `config.json` file may contain:
- Google Drive folder IDs (from `upload_destination`)
- Custom settings specific to your setup

**Options:**
1. **Option A:** Keep `config.json` in git with example values
   - Use `config.local.json` for your real settings
   - Copy: `cp config.json config.local.json`
   - Modify `config.local.json` with your values

2. **Option B (Current):** Keep `config.json` in git
   - Google Drive folder IDs are generally safe to share
   - They don't provide access without credentials

## Development Workflow with Private Config

### Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/brentyates/swing-cam.git
   cd swing-cam
   ```

2. **Set up private configuration:**
   ```bash
   # Copy the environment template
   cp .env.local.template .env.local

   # Edit with your Pi's IP address
   nano .env.local
   ```

3. **Set up Google Drive (optional):**
   - Upload credentials via web interface, or
   - Place `gdrive_credentials.json` in project root

4. **Start development:**
   ```bash
   # File watcher will use your .env.local settings
   python dev-watch.py
   ```

## Remote Access Setup

If you want to access your Pi from outside your local network:

### Router Configuration (Private)

1. **Port Forwarding:**
   - Forward port 22 (SSH) to your Pi's local IP
   - Forward port 5000 (web interface) - optional, SSH tunnel is more secure

2. **Find Your Public IP:**
   ```bash
   curl ifconfig.me
   ```

3. **Update `.env.local`:**
   ```bash
   PI_IP_ADDRESS=YOUR_PUBLIC_IP
   ```

### SSH Security Best Practices

**Never commit these to git:**
- Your public IP address
- SSH private keys
- Router admin credentials

**Always enable:**
- SSH key-based authentication
- Disable password authentication
- Use SSH tunnels for web access

## Files That Should NEVER Be Committed

The `.gitignore` already excludes:
- `.env.local` - Your private network config
- `gdrive_credentials.json` - Google OAuth credentials
- `gdrive_token.pickle` - Google auth tokens
- `config.local.json` - Local config overrides
- `.claude/` - Claude Code local settings
- `recordings/` - Your video recordings

## Sharing Your Fork

If you fork this project:

1. ✅ **Safe to share:**
   - All Python code
   - HTML templates
   - Documentation files
   - `config.json` (with generic/example values)
   - `.env.local.template`

2. ❌ **Never share:**
   - `.env.local`
   - `gdrive_credentials.json`
   - `gdrive_token.pickle`
   - Your public IP address
   - Your Google Drive folder IDs (if you want privacy)

## Quick Reference

| File | Purpose | In Git? | Contains Private Data? |
|------|---------|---------|------------------------|
| `.env.local.template` | Template for network config | ✅ Yes | ❌ No |
| `.env.local` | Your actual network config | ❌ No | ✅ Yes |
| `gdrive_credentials.json` | Google OAuth credentials | ❌ No | ✅ Yes |
| `gdrive_token.pickle` | Google auth token | ❌ No | ✅ Yes |
| `config.json` | Camera settings | ✅ Yes | ⚠️ Maybe |
| `config.local.json` | Your local overrides | ❌ No | ✅ Yes |

## Getting Help

If you accidentally commit sensitive data:

1. **Remove from git history:**
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/file" \
     --prune-empty --tag-name-filter cat -- --all
   ```

2. **Or use BFG Repo-Cleaner:**
   ```bash
   bfg --delete-files gdrive_credentials.json
   ```

3. **Force push (if safe):**
   ```bash
   git push origin --force --all
   ```

4. **Rotate credentials:**
   - Generate new Google OAuth credentials
   - Change router passwords if exposed
   - Update SSH keys if needed
