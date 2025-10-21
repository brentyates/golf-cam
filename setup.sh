#!/bin/bash

set -e

echo "==================================="
echo "Golf Swing Camera Setup"
echo "==================================="
echo ""

if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo "Warning: This script is designed for Raspberry Pi"
    echo "Continuing anyway..."
fi

echo "Step 1: Updating system..."
sudo apt update

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-picamera2 python3-libcamera python3-flask ffmpeg rsync libcap-dev

echo ""
echo "Step 3: Creating virtual environment..."
python3 -m venv --system-site-packages venv

echo ""
echo "Step 4: Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Step 5: Creating recordings directory..."
mkdir -p recordings

echo ""
echo "Step 6: Making scripts executable..."
chmod +x swing_camera.py
chmod +x web_interface.py
chmod +x button_trigger.py

echo ""
echo "==================================="
echo "Setup Complete! ✓"
echo "==================================="
echo ""
echo "To start the web interface:"
echo "  source venv/bin/activate"
echo "  python web_interface.py"
echo ""
echo "Then visit: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Or for command line:"
echo "  source venv/bin/activate"
echo "  python swing_camera.py"
echo ""
echo "See README.md for more options!"

