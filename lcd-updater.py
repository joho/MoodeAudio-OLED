#!/usr/bin/env python3
"""LCD Updater script for MoodeAudio - replaces /var/local/www/commandw/lcd-updater.py

This script is automatically called by MoodeAudio's LCD Update Engine
whenever the UI state changes (track changes, volume changes, etc.).

To install: Copy this file to /var/local/www/commandw/lcd-updater.py
"""

import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Optional

# Add our project to Python path so we can import our modules
# Assumes the MoodeAudio-OLED project is in the user's home directory
def setup_python_path():
    """Set up Python path to find our modules."""
    possible_paths = [
        "/home/pi/MoodeAudio-OLED/src",
        "/home/moode/MoodeAudio-OLED/src", 
        "/home/*/MoodeAudio-OLED/src",  # Will be expanded below
    ]
    
    # Expand the wildcard path
    import glob
    expanded_paths = []
    for path in possible_paths:
        if '*' in path:
            expanded_paths.extend(glob.glob(path))
        else:
            expanded_paths.append(path)
    
    # Find the first existing path
    for path in expanded_paths:
        if os.path.exists(path):
            sys.path.insert(0, path)
            return path
    
    return None

# Try to set up our module path
project_path = setup_python_path()

# Set up minimal logging
logging.basicConfig(
    level=logging.ERROR,  # Only errors to avoid spam in MoodeAudio logs
    format="%(asctime)s - OLED - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def simple_oled_update():
    """Simple OLED update using basic libraries if our modules aren't available."""
    try:
        # Try to read currentsong file
        currentsong_file = Path("/var/local/www/currentsong.txt")
        if not currentsong_file.exists():
            return False
            
        content = currentsong_file.read_text().strip()
        if not content:
            return False
        
        # Parse basic info
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try key=value format
            data = {}
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    data[key.strip()] = value.strip()
        
        # Try to import and use our display module
        try:
            import board
            import busio
            import adafruit_ssd1306
            from PIL import Image, ImageDraw, ImageFont
            
            # Initialize display
            i2c = busio.I2C(board.SCL, board.SDA)
            display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)
            
            # Create image
            image = Image.new("1", (128, 64))
            draw = ImageDraw.Draw(image)
            
            # Get basic info
            artist = data.get('artist', data.get('Artist', 'Unknown'))
            title = data.get('title', data.get('Title', 'Unknown'))
            state = data.get('state', data.get('State', 'unknown'))
            
            # Clear display
            draw.rectangle((0, 0, 128, 64), outline=0, fill=0)
            
            if state.lower() == 'stop':
                draw.text((20, 20), "Music Stopped", fill=255)
            else:
                # Draw basic info (truncate if too long)
                artist_text = artist[:18] if len(artist) > 18 else artist
                title_text = title[:18] if len(title) > 18 else title
                
                draw.text((2, 10), artist_text, fill=255)
                draw.text((2, 25), title_text, fill=255)
                
                # Volume if available
                volume = data.get('volume', data.get('Volume', ''))
                if volume:
                    draw.text((2, 50), f"Vol: {volume}", fill=255)
            
            # Update display
            display.image(image)
            display.show()
            return True
            
        except ImportError as e:
            logger.error(f"Display libraries not available: {e}")
            return False
        except Exception as e:
            logger.error(f"Display update failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Simple update failed: {e}")
        return False

def main():
    """Main function called by MoodeAudio LCD Update Engine."""
    try:
        # Method 1: Try to use our full module if available
        if project_path:
            try:
                from moode_oled.lcd_updater import LCDUpdater
                updater = LCDUpdater()
                success = updater.update_display_once()
                if success:
                    return
            except ImportError:
                logger.info("Full module not available, using simple mode")
            except Exception as e:
                logger.error(f"Full module failed: {e}")
        
        # Method 2: Fallback to simple update
        simple_oled_update()
        
    except Exception as e:
        logger.error(f"LCD updater failed: {e}")

if __name__ == "__main__":
    main()
