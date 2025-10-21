#!/bin/bash
# Quick preset switcher for recording modes
#
# Usage: ./switch_preset.sh [120|240|standard]

if [ $# -eq 0 ]; then
    echo "Usage: $0 [120|240|standard]"
    echo ""
    echo "Available presets:"
    echo "  120      - 728x544 @ 120 FPS (2x slow-mo, tested working)"
    echo "  240      - 512x384 @ 240 FPS (4x slow-mo, recommended for golf impact)"
    echo "  standard - 1456x1088 @ 60 FPS (full resolution)"
    echo ""
    echo "Example: $0 240"
    exit 1
fi

PRESET=$1
CONFIG_FILE=""

case $PRESET in
    120)
        CONFIG_FILE="config_120fps.json"
        echo "Switching to 120 FPS preset (728x544)..."
        ;;
    240)
        CONFIG_FILE="config_240fps.json"
        echo "Switching to 240 FPS preset (512x384)..."
        ;;
    standard|60)
        CONFIG_FILE="config.json.backup"
        echo "Switching to standard preset (1456x1088 @ 60 FPS)..."
        ;;
    *)
        echo "Error: Unknown preset '$PRESET'"
        echo "Available: 120, 240, standard"
        exit 1
        ;;
esac

# Backup current config
if [ ! -f config.json.backup ]; then
    cp config.json config.json.backup
    echo "Created backup of original config"
fi

# Copy preset
if [ "$CONFIG_FILE" = "config.json.backup" ]; then
    cp config.json.backup config.json
else
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Preset file $CONFIG_FILE not found"
        exit 1
    fi
    cp "$CONFIG_FILE" config.json
fi

echo "✓ Configuration updated"
echo ""
echo "To apply changes, restart the server:"
echo "  pkill -f web_interface"
echo "  source venv/bin/activate"
echo "  python web_interface.py --debug"
