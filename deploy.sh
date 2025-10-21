#!/bin/bash

echo "=================================="
echo "Golf Swing Camera - Deploy to Pi"
echo "=================================="
echo ""

PI_HOST="${1:-raspberrypi.local}"
PI_USER="${2:-pi}"
PI_PATH="${3:-~/swing-cam}"

echo "Deploying to: $PI_USER@$PI_HOST:$PI_PATH"
echo ""

if ! command -v rsync &> /dev/null; then
    echo "Error: rsync not found. Please install rsync."
    exit 1
fi

echo "Syncing files..."
rsync -avz --exclude 'venv/' \
           --exclude '__pycache__/' \
           --exclude '*.pyc' \
           --exclude 'recordings/' \
           --exclude '.git/' \
           --exclude '.DS_Store' \
           ./ "$PI_USER@$PI_HOST:$PI_PATH/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Files synced successfully!"
    echo ""
    echo "Next steps:"
    echo "1. SSH to Pi: ssh $PI_USER@$PI_HOST"
    echo "2. Run setup: cd $PI_PATH && ./setup.sh"
    echo "3. Start camera: python web_interface.py"
    echo ""
else
    echo ""
    echo "✗ Sync failed. Check connection and try again."
    exit 1
fi

