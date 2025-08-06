#!/usr/bin/env python3
"""Enhanced OLED display for MoodeAudio with multi-source metadata support."""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

import adafruit_ssd1306
import board
import busio
from PIL import Image, ImageDraw, ImageFont

from .display import MPDConnect, OLEDDisplay  # Import existing classes
from .moode_api import MoodeMetadata

logger = logging.getLogger(__name__)


class EnhancedMetadataFetcher:
    """Enhanced metadata fetcher that tries multiple sources."""
    
    def __init__(self) -> None:
        self.mpd_client = MPDConnect()
        self.moode_api = MoodeMetadata()
        self.preferred_source = "auto"  # auto, mpd, moode_api
        self._last_successful_source = None
        
    def set_preferred_source(self, source: str) -> None:
        """Set preferred metadata source: 'auto', 'mpd', or 'moode_api'."""
        if source in ["auto", "mpd", "moode_api"]:
            self.preferred_source = source
            logger.info(f"Set preferred metadata source to: {source}")
        else:
            logger.warning(f"Invalid source: {source}. Using 'auto'")
            self.preferred_source = "auto"
    
    def _fetch_from_mpd(self) -> Optional[Dict[str, str]]:
        """Fetch metadata from MPD."""
        try:
            self.mpd_client.connect()
            data = self.mpd_client.fetch()
            if data.get("state") != "error":
                logger.debug("Successfully fetched from MPD")
                return data
        except Exception as e:
            logger.debug(f"MPD fetch failed: {e}")
        return None
    
    def _fetch_from_moode_api(self) -> Optional[Dict[str, str]]:
        """Fetch metadata from MoodeAudio API."""
        try:
            data = self.moode_api.fetch_metadata()
            if data.get("state") != "error" and data.get("artist") != "Not Playing":
                logger.debug("Successfully fetched from MoodeAudio API")
                return data
        except Exception as e:
            logger.debug(f"MoodeAudio API fetch failed: {e}")
        return None
    
    def fetch(self) -> Dict[str, str]:
        """Fetch metadata using the best available source."""
        sources_to_try = []
        
        if self.preferred_source == "mpd":
            sources_to_try = ["mpd", "moode_api"]
        elif self.preferred_source == "moode_api":
            sources_to_try = ["moode_api", "mpd"]
        else:  # auto mode
            # Try the last successful source first
            if self._last_successful_source == "mpd":
                sources_to_try = ["mpd", "moode_api"]
            else:
                sources_to_try = ["moode_api", "mpd"]
        
        for source in sources_to_try:
            if source == "mpd":
                data = self._fetch_from_mpd()
            else:  # moode_api
                data = self._fetch_from_moode_api()
            
            if data:
                self._last_successful_source = source
                if source != getattr(self, '_last_logged_source', None):
                    logger.info(f"Using metadata source: {source}")
                    self._last_logged_source = source
                return data
        
        # Fallback: return error state
        logger.warning("All metadata sources failed")
        return {
            "state": "error",
            "artist": "No Metadata",
            "title": "Check Settings",
            "eltime": "0:00:00",
            "volume": 0,
            "audio_info": "",
        }
    
    def disconnect(self) -> None:
        """Disconnect from sources."""
        try:
            self.mpd_client.disconnect()
        except Exception:
            pass


class EnhancedMoodeOLEDApp:
    """Enhanced application with multi-source metadata support."""
    
    def __init__(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        self.metadata_fetcher = EnhancedMetadataFetcher()
        self.display = OLEDDisplay()
        self.running = False
        
        # Check if MoodeAudio metadata file is enabled
        if self.metadata_fetcher.moode_api.is_metadata_enabled():
            logger.info("MoodeAudio metadata file found - will use API for all sources")
            self.metadata_fetcher.set_preferred_source("moode_api")
        else:
            logger.warning("MoodeAudio metadata file not found")
            logger.info("Enable 'Metadata file' in MoodeAudio Audio Config for Spotify/Bluetooth support")
            self.metadata_fetcher.set_preferred_source("mpd")

    def run(self) -> None:
        """Main application loop."""
        logger.info("Starting Enhanced MoodeAudio OLED display")
        logger.info("Supports: MPD sources + Spotify Connect + Bluetooth + AirPlay")
        self.running = True
        
        try:
            while self.running:
                try:
                    info = self.metadata_fetcher.fetch()
                    self.display.update_display(info)
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    # Show error on display but continue running
                    error_info = {
                        "state": "error",
                        "artist": "System Error",
                        "title": "Check logs",
                        "eltime": "0:00:00",
                        "volume": 0,
                        "audio_info": "",
                    }
                    try:
                        self.display.update_display(error_info)
                    except Exception:
                        pass  # If display update fails, just continue
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Clean shutdown."""
        logger.info("Shutting down Enhanced MoodeAudio OLED display")
        self.running = False
        self.metadata_fetcher.disconnect()
        self.display.clear()
        self.display.display.fill(0)
        self.display.display.show()


def main() -> None:
    """Entry point for the enhanced application."""
    app = EnhancedMoodeOLEDApp()
    app.run()


if __name__ == "__main__":
    main()
