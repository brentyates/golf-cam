#!/usr/bin/env python3
"""
Physical button trigger for golf swing camera.
Connect a button between GPIO 17 and ground.
"""

import signal
import sys
from gpiozero import Button
from swing_camera import SwingCamera
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    camera = SwingCamera('config.json')
    camera.start()
    
    logger.info("Golf Swing Camera with Button Trigger Ready!")
    logger.info("Press the button to record...")
    
    button = Button(17, pull_up=True, bounce_time=0.1)
    
    def on_button_press():
        if not camera.recording:
            logger.info("Button pressed! Starting recording...")
            camera.capture_swing()
        else:
            logger.warning("Already recording, please wait...")
    
    button.when_pressed = on_button_press
    
    def signal_handler(sig, frame):
        logger.info("\nShutting down...")
        camera.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    signal.pause()


if __name__ == '__main__':
    main()

