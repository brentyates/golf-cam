#!/usr/bin/env python3
"""
Development file watcher that auto-syncs changes to Raspberry Pi.

Usage:
    python dev-watch.py [pi_hostname] [username] [remote_path]

Default:
    python dev-watch.py raspberrypi.local pi /home/pi/swing-cam

Configuration:
    Create a .env.local file with PI_IP_ADDRESS, PI_USER, PI_REMOTE_PATH
    to avoid passing arguments each time.

Requirements:
    pip install watchdog
"""

import sys
import time
import subprocess
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class CodeSyncHandler(FileSystemEventHandler):
    """Handles file system events and syncs changes to Pi."""

    def __init__(self, pi_host, pi_user, remote_path, local_path):
        self.pi_host = pi_host
        self.pi_user = pi_user
        self.remote_path = remote_path
        self.local_path = local_path
        self.last_sync = 0
        self.sync_delay = 1.0  # Wait 1 second to batch changes
        self.pending_sync = False

    def should_sync(self, path):
        """Check if file should trigger a sync."""
        # Ignore patterns
        ignore_patterns = [
            'venv/', '__pycache__/', '.pyc', '.git/',
            '.DS_Store', 'recordings/', '*.swp', '*.swo'
        ]

        path_str = str(path)
        for pattern in ignore_patterns:
            if pattern in path_str:
                return False
        return True

    def sync_to_pi(self):
        """Rsync changes to the Pi."""
        cmd = [
            'rsync', '-av',
            '--exclude', 'venv',
            '--exclude', '__pycache__',
            '--exclude', '*.pyc',
            '--exclude', '.git',
            '--exclude', 'recordings',
            '--exclude', '*.h264',
            '--exclude', '*.mp4',
            f'{self.local_path}/',
            f'{self.pi_user}@{self.pi_host}:{self.remote_path}/'
        ]

        try:
            print(f"[{time.strftime('%H:%M:%S')}] Syncing changes to Pi...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Only show files that changed (filter out directory lines)
                output_lines = [l for l in result.stdout.split('\n') if l and not l.endswith('/')]
                if output_lines:
                    print(f"[{time.strftime('%H:%M:%S')}] Synced {len(output_lines)} files")
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] No changes to sync")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Sync failed: {result.stderr}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Sync error: {e}")

        self.last_sync = time.time()
        self.pending_sync = False

    def on_any_event(self, event):
        """Handle any file system event."""
        if event.is_directory:
            return

        if not self.should_sync(event.src_path):
            return

        # Mark that we have pending changes
        self.pending_sync = True

        # Debounce: only sync if enough time has passed
        time_since_sync = time.time() - self.last_sync
        if time_since_sync >= self.sync_delay:
            self.sync_to_pi()


def load_env_config():
    """Load configuration from .env.local if it exists."""
    env_file = Path(__file__).parent / '.env.local'
    config = {}

    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    return config


def main():
    """Main entry point."""
    # Load config from .env.local
    env_config = load_env_config()

    # Parse arguments (command line args override env file)
    pi_host = sys.argv[1] if len(sys.argv) > 1 else env_config.get('PI_IP_ADDRESS', 'raspberrypi.local')
    pi_user = sys.argv[2] if len(sys.argv) > 2 else env_config.get('PI_USER', 'pi')
    remote_path = sys.argv[3] if len(sys.argv) > 3 else env_config.get('PI_REMOTE_PATH', '/home/pi/swing-cam')

    local_path = Path(__file__).parent.absolute()

    print(f"🔍 Watching: {local_path}")
    print(f"📡 Syncing to: {pi_user}@{pi_host}:{remote_path}")
    print(f"⚡ Auto-reload enabled on Pi (make sure to run with --debug)")
    print(f"\nPress Ctrl+C to stop\n")

    # Initial sync
    handler = CodeSyncHandler(pi_host, pi_user, remote_path, local_path)
    handler.sync_to_pi()

    # Start watching
    observer = Observer()
    observer.schedule(handler, str(local_path), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
            # Check if we have pending changes to sync
            if handler.pending_sync:
                time_since_sync = time.time() - handler.last_sync
                if time_since_sync >= handler.sync_delay:
                    handler.sync_to_pi()
    except KeyboardInterrupt:
        print("\n\n👋 Stopping file watcher...")
        observer.stop()

    observer.join()


if __name__ == '__main__':
    main()
