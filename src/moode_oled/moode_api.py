#!/usr/bin/env python3
"""MoodeAudio REST API and metadata file integration."""

import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MoodeMetadata:
    """Fetches metadata from MoodeAudio using multiple methods."""
    
    def __init__(self, host: str = "localhost", port: int = 80) -> None:
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.currentsong_file = Path("/var/local/www/currentsong.txt")
        
    def _fetch_rest_api(self, endpoint: str) -> Optional[str]:
        """Fetch data from MoodeAudio REST API."""
        try:
            url = f"{self.base_url}/command/?cmd={endpoint}"
            logger.debug(f"Fetching from REST API: {url}")
            
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.read().decode('utf-8').strip()
                
        except urllib.error.URLError as e:
            logger.error(f"REST API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in REST API request: {e}")
            return None
    
    def _read_currentsong_file(self) -> Optional[str]:
        """Read current song info from MoodeAudio's metadata file."""
        try:
            if self.currentsong_file.exists():
                content = self.currentsong_file.read_text().strip()
                logger.debug(f"Read currentsong file: {content[:100]}...")
                return content
            else:
                logger.warning(f"Currentsong file not found: {self.currentsong_file}")
                return None
        except Exception as e:
            logger.error(f"Error reading currentsong file: {e}")
            return None
    
    def _parse_currentsong_data(self, data: str) -> Dict[str, str]:
        """Parse currentsong data (JSON or text format)."""
        if not data or data.strip() == "":
            return self._empty_result()
            
        # Try JSON format first
        try:
            parsed = json.loads(data)
            if isinstance(parsed, dict):
                return self._format_metadata(parsed)
        except json.JSONDecodeError:
            pass
        
        # Try text format (key=value pairs)
        try:
            result = {}
            for line in data.split('\n'):
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    result[key.strip()] = value.strip()
            
            if result:
                return self._format_metadata(result)
        except Exception as e:
            logger.error(f"Error parsing text format: {e}")
        
        # Fallback: treat as plain text
        logger.warning(f"Could not parse currentsong data, treating as plain text: {data[:50]}...")
        return {
            "state": "unknown",
            "artist": "Unknown",
            "title": data[:50] + "..." if len(data) > 50 else data,
            "eltime": "0:00:00",
            "volume": 0,
            "audio_info": "",
        }
    
    def _format_metadata(self, data: Dict) -> Dict[str, str]:
        """Format metadata into consistent structure."""
        # Handle different key formats that MoodeAudio might use
        artist = (
            data.get('artist') or 
            data.get('Artist') or 
            data.get('ARTIST') or 
            'Unknown Artist'
        )
        
        title = (
            data.get('title') or 
            data.get('Title') or 
            data.get('TITLE') or 
            data.get('song') or
            'Unknown Title'
        )
        
        # Handle volume - could be string or int
        volume_raw = data.get('volume', data.get('Volume', 0))
        try:
            volume = int(volume_raw) if volume_raw else 0
        except (ValueError, TypeError):
            volume = 0
        
        # Handle elapsed time
        elapsed = data.get('elapsed', data.get('Elapsed', '0:00:00'))
        if isinstance(elapsed, (int, float)):
            # Convert seconds to time string
            hours, remainder = divmod(int(elapsed), 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed = f"{hours}:{minutes:02d}:{seconds:02d}"
        elif not isinstance(elapsed, str):
            elapsed = "0:00:00"
        
        # Handle state
        state = data.get('state', data.get('State', 'unknown')).lower()
        
        # Handle audio format info
        audio_info = ""
        if 'bitrate' in data and 'format' in data:
            audio_info = f"{data['format']} {data['bitrate']}kbps"
        elif 'audio' in data:
            audio_info = str(data['audio'])
        
        return {
            "state": state,
            "artist": str(artist),
            "title": str(title),
            "eltime": str(elapsed),
            "volume": volume,
            "audio_info": str(audio_info),
        }
    
    def _empty_result(self) -> Dict[str, str]:
        """Return empty/stopped state."""
        return {
            "state": "stop",
            "artist": "Not Playing",
            "title": "",
            "eltime": "0:00:00",
            "volume": 0,
            "audio_info": "",
        }
    
    def fetch_metadata(self) -> Dict[str, str]:
        """Fetch current track metadata using best available method."""
        # Method 1: Try REST API first
        rest_data = self._fetch_rest_api("get_currentsong")
        if rest_data:
            try:
                return self._parse_currentsong_data(rest_data)
            except Exception as e:
                logger.error(f"Error parsing REST API response: {e}")
        
        # Method 2: Try reading the file directly
        file_data = self._read_currentsong_file()
        if file_data:
            try:
                return self._parse_currentsong_data(file_data)
            except Exception as e:
                logger.error(f"Error parsing currentsong file: {e}")
        
        # Method 3: Try to get volume at least
        try:
            volume_data = self._fetch_rest_api("get_volume")
            volume = int(volume_data) if volume_data and volume_data.isdigit() else 0
            
            result = self._empty_result()
            result["volume"] = volume
            return result
        except Exception:
            pass
        
        # Fallback: return empty state
        logger.warning("All metadata fetch methods failed")
        return self._empty_result()
    
    def get_output_format(self) -> str:
        """Get current audio output format."""
        format_data = self._fetch_rest_api("get_output_format")
        return format_data or "Unknown"
    
    def is_metadata_enabled(self) -> bool:
        """Check if metadata file generation is enabled in MoodeAudio."""
        return self.currentsong_file.exists()
