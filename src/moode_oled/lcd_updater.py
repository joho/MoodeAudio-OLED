#!/usr/bin/env python3
"""LCD Updater script for MoodeAudio LCD Update Engine integration."""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

from .display import OLEDDisplay

# Set up minimal logging for LCD updater mode
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors to avoid spam
    format="%(asctime)s - LCD Updater - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LCDUpdater:
    """One-shot LCD updater for MoodeAudio LCD Update Engine."""
    
    def __init__(self) -> None:
        self.currentsong_file = Path("/var/local/www/currentsong.txt")
        self.display = OLEDDisplay()
        
    def read_currentsong(self) -> Optional[Dict]:
        """Read and parse the currentsong file."""
        try:
            if not self.currentsong_file.exists():
                logger.error(f"Currentsong file not found: {self.currentsong_file}")
                return None
                
            content = self.currentsong_file.read_text().strip()
            if not content:
                return None
                
            # Try to parse as JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try key=value format
                data = {}
                for line in content.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        data[key.strip()] = value.strip()
                return data if data else None
                
        except Exception as e:
            logger.error(f"Error reading currentsong file: {e}")
            return None
    
    def format_metadata(self, raw_data: Dict) -> Dict[str, str]:
        """Format raw metadata into display format."""
        # Handle different possible key formats
        artist = (
            raw_data.get('artist') or 
            raw_data.get('Artist') or 
            raw_data.get('ARTIST') or 
            'Unknown Artist'
        )
        
        title = (
            raw_data.get('title') or 
            raw_data.get('Title') or 
            raw_data.get('TITLE') or 
            raw_data.get('song') or
            'Unknown Title'
        )
        
        # Handle state
        state = raw_data.get('state', raw_data.get('State', 'unknown')).lower()
        
        # Handle volume
        volume_raw = raw_data.get('volume', raw_data.get('Volume', 0))
        try:
            volume = int(volume_raw) if volume_raw else 0
        except (ValueError, TypeError):
            volume = 0
        
        # Handle elapsed time
        elapsed = raw_data.get('elapsed', raw_data.get('Elapsed', '0:00:00'))
        if isinstance(elapsed, (int, float)):
            hours, remainder = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed = f"{hours}:{minutes:02d}:{seconds:02d}"
        elif not isinstance(elapsed, str):
            elapsed = "0:00:00"
        
        # Handle audio format
        audio_info = ""
        if 'bitrate' in raw_data and 'format' in raw_data:
            audio_info = f"{raw_data['format']} {raw_data['bitrate']}kbps"
        elif 'audio' in raw_data:
            audio_info = str(raw_data['audio'])
        
        return {
            "state": state,
            "artist": str(artist),
            "title": str(title),
            "eltime": str(elapsed),
            "volume": volume,
            "audio_info": str(audio_info),
        }
    
    def update_display_once(self) -> bool:
        """Update the display once and exit."""
        try:
            # Read current song data
            raw_data = self.read_currentsong()
            
            if raw_data:
                # Format for display
                display_data = self.format_metadata(raw_data)
                logger.info(f"Updating display: {display_data['artist']} - {display_data['title']}")
            else:
                # No data available
                display_data = {
                    "state": "stop",
                    "artist": "Not Playing",
                    "title": "",
                    "eltime": "0:00:00",
                    "volume": 0,
                    "audio_info": "",
                }
            
            # Update the display
            self.display.update_display(display_data)
            return True
            
        except Exception as e:
            logger.error(f"Error updating display: {e}")
            # Try to show error on display
            try:
                error_data = {
                    "state": "error",
                    "artist": "Display Error",
                    "title": "Check Logs",
                    "eltime": "0:00:00",
                    "volume": 0,
                    "audio_info": "",
                }
                self.display.update_display(error_data)
            except Exception:
                pass  # If even error display fails, just exit
            return False


def main() -> None:
    """Main entry point for LCD updater."""
    updater = LCDUpdater()
    success = updater.update_display_once()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
