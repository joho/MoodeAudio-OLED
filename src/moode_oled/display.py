#!/usr/bin/env python3
"""Modern OLED display for MoodeAudio using CircuitPython libraries."""

import logging
import time
from pathlib import Path
from socket import error as socket_error
from typing import Dict, Optional

import adafruit_ssd1306
import board
import busio
from mpd import CommandError, ConnectionError, MPDClient, MPDError
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class MPDConnect:
    """Modern MPD client for MoodeAudio integration."""

    def __init__(self, host: str = "localhost", port: int = 6600) -> None:
        self._mpd_client = MPDClient()
        self._mpd_client.timeout = 10
        self._mpd_connected = False
        self._host = host
        self._port = port

    def connect(self) -> None:
        """Connect to MPD server."""
        if not self._mpd_connected:
            try:
                self._mpd_client.ping()
                self._mpd_connected = True
            except (socket_error, ConnectionError, CommandError):
                try:
                    self._mpd_client.connect(self._host, self._port)
                    self._mpd_connected = True
                    logger.info(f"Connected to MPD at {self._host}:{self._port}")
                except (socket_error, ConnectionError, CommandError) as e:
                    self._mpd_connected = False
                    logger.error(f"Failed to connect to MPD: {e}")

    def _ensure_connected(self) -> bool:
        """Ensure MPD connection is active, reconnect if needed."""
        if not self._mpd_connected:
            self.connect()
            return self._mpd_connected
            
        try:
            # Test connection with ping
            self._mpd_client.ping()
            return True
        except (socket_error, ConnectionError, CommandError, MPDError) as e:
            logger.warning(f"MPD connection lost: {e}")
            self._mpd_connected = False
            # Try to reconnect
            self.connect()
            return self._mpd_connected

    def disconnect(self) -> None:
        """Disconnect from MPD server."""
        try:
            self._mpd_client.close()
            self._mpd_client.disconnect()
            self._mpd_connected = False
            logger.info("Disconnected from MPD")
        except Exception as e:
            logger.error(f"Error disconnecting from MPD: {e}")

    def fetch(self) -> Dict[str, str]:
        """Fetch current song and player status from MPD."""
        # Ensure we have a valid connection
        if not self._ensure_connected():
            return {
                "state": "error",
                "artist": "MPD Disconnected",
                "title": "Retrying...",
                "eltime": "0:00:00",
                "volume": 0,
                "audio_info": "",
            }
        
        try:
            # Get current song info
            song_info = self._mpd_client.currentsong()
            
            # Extract artist and title
            artist = song_info.get("artist", "Unknown Artist")
            title = song_info.get("title", "Unknown Title")
            
            # Get player status
            song_stats = self._mpd_client.status()
            state = song_stats.get("state", "unknown")
            
            # Calculate elapsed time
            elapsed_str = "0:00:00"
            if "elapsed" in song_stats:
                elapsed_seconds = float(song_stats["elapsed"])
                hours, remainder = divmod(elapsed_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                elapsed_str = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
            
            # Extract audio format info
            audio_info = ""
            if "audio" in song_stats:
                audio_parts = song_stats["audio"].split(":")
                if len(audio_parts) >= 2:
                    frequency = int(audio_parts[0])
                    bit_depth = audio_parts[1]
                    bitrate = song_stats.get("bitrate", "0")
                    
                    # Format frequency (convert to kHz if >= 1000 Hz)
                    freq_display = (
                        f"{frequency // 1000}" if frequency % 1000 == 0
                        else f"{frequency / 1000:.1f}"
                    )
                    
                    audio_info = f"{bit_depth}bit {freq_display}kHz {bitrate}kbps"
            
            # Get volume
            volume = int(song_stats.get("volume", 0))
            
            # Debug logging for state changes and detailed info
            if hasattr(self, '_last_state') and self._last_state != state:
                logger.info(f"MPD state changed: {self._last_state} -> {state}")
            self._last_state = state
            
            # Debug log current song info periodically (every 30 seconds)
            if not hasattr(self, '_debug_counter'):
                self._debug_counter = 0
            self._debug_counter += 1
            if self._debug_counter % 30 == 0:
                logger.info(f"MPD Status - State: {state}, Artist: {artist}, Title: {title}, Audio: {audio_info}")
                logger.debug(f"Raw MPD currentsong: {song_info}")
                logger.debug(f"Raw MPD status: {song_stats}")
            
            return {
                "state": state,
                "artist": artist,
                "title": title,
                "eltime": elapsed_str,
                "volume": volume,
                "audio_info": audio_info,
            }
            
        except (socket_error, ConnectionError, CommandError, MPDError) as e:
            logger.error(f"Error fetching MPD data: {e}")
            self._mpd_connected = False
            return {
                "state": "error",
                "artist": "Connection Error",
                "title": "Reconnecting...",
                "eltime": "0:00:00",
                "volume": 0,
                "audio_info": "",
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "state": "error",
                "artist": "System Error",
                "title": str(e)[:20] + "...",
                "eltime": "0:00:00",
                "volume": 0,
                "audio_info": "",
            }


class OLEDDisplay:
    """Modern OLED display controller using CircuitPython."""

    def __init__(self, width: int = 128, height: int = 64) -> None:
        self.width = width
        self.height = height
        
        # Initialize I2C and display
        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self.display = adafruit_ssd1306.SSD1306_I2C(width, height, i2c)
            self.display.fill(0)
            self.display.show()
            logger.info(f"Initialized {width}x{height} OLED display")
        except Exception as e:
            logger.error(f"Failed to initialize OLED display: {e}")
            raise
        
        # Create image buffer
        self.image = Image.new("1", (width, height))
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts with fallback
        self._load_fonts()
        
        # Animation offsets
        self.artist_offset = 2
        self.title_offset = 2
        self.animate_step = 15

    def _load_fonts(self) -> None:
        """Load fonts with fallback to default if custom fonts not found."""
        font_dir = Path(__file__).parent.parent.parent
        
        try:
            self.font_artist = ImageFont.truetype(
                str(font_dir / "Arial-Unicode-Bold.ttf"), 14
            )
            self.font_title = ImageFont.truetype(
                str(font_dir / "Arial-Unicode-Regular.ttf"), 13
            )
            self.font_info = ImageFont.truetype(
                str(font_dir / "Verdana-Italic.ttf"), 10
            )
            self.font_time = ImageFont.truetype(
                str(font_dir / "Verdana.ttf"), 13
            )
            logger.info("Loaded custom fonts")
        except OSError:
            logger.warning("Custom fonts not found, using default font")
            # Fallback to default font
            self.font_artist = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            self.font_info = ImageFont.load_default()
            self.font_time = ImageFont.load_default()

    def clear(self) -> None:
        """Clear the display."""
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

    def update_display(self, info: Dict[str, str]) -> None:
        """Update display with current song information."""
        self.clear()
        
        state = info["state"]
        artist = info["artist"]
        title = info["title"]
        eltime = info["eltime"]
        volume = info["volume"]
        audio_info = info["audio_info"]
        
        if state == "stop":
            # Display stopped state
            self.draw.text((30, 15), "Music Stop", font=self.font_title, fill=255)
            self.draw.text((2, 50), eltime, font=self.font_time, fill=255)
            self.draw.text((75, 50), f"vol: {volume}", font=self.font_time, fill=255)
        else:
            # Display playing state
            self._draw_scrolling_text(artist, self.font_artist, 0, "artist")
            self._draw_scrolling_text(title, self.font_title, 18, "title")
            
            # Audio info (centered if fits, left-aligned if too long)
            audio_bbox = self.draw.textbbox((0, 0), audio_info, font=self.font_info)
            audio_width = audio_bbox[2] - audio_bbox[0]
            audio_x = max(2, (self.width - audio_width) // 2)
            self.draw.text((audio_x, 35), audio_info, font=self.font_info, fill=255)
            
            # Time and volume
            self.draw.text((2, 50), eltime, font=self.font_time, fill=255)
            self.draw.text((75, 50), f"vol: {volume}", font=self.font_time, fill=255)
        
        # Update physical display
        self.display.image(self.image)
        self.display.show()

    def _draw_scrolling_text(
        self, text: str, font: ImageFont.ImageFont, y: int, text_type: str
    ) -> None:
        """Draw text with scrolling animation if it's too long."""
        bbox = self.draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_type == "artist":
            offset = self.artist_offset
        else:
            offset = self.title_offset
            
        if text_width < self.width:
            # Center text if it fits
            x = (self.width - text_width) // 2
            if text_type == "artist":
                self.artist_offset = 2
            else:
                self.title_offset = 2
        else:
            # Scroll text if too long
            x = offset
            if text_type == "title":
                self.title_offset -= self.animate_step
                if (text_width - (self.width + abs(x))) < -120:
                    self.title_offset = 100
        
        self.draw.text((x, y), text, font=font, fill=255)


class MoodeOLEDApp:
    """Main application class."""
    
    def __init__(self) -> None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        self.mpd_client = MPDConnect()
        self.display = OLEDDisplay()
        self.running = False

    def run(self) -> None:
        """Main application loop."""
        logger.info("Starting MoodeAudio OLED display")
        self.running = True
        
        try:
            self.mpd_client.connect()
            
            while self.running:
                try:
                    info = self.mpd_client.fetch()
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
        logger.info("Shutting down MoodeAudio OLED display")
        self.running = False
        self.mpd_client.disconnect()
        self.display.clear()
        self.display.display.fill(0)
        self.display.display.show()


def main() -> None:
    """Entry point for the application."""
    app = MoodeOLEDApp()
    app.run()


if __name__ == "__main__":
    main()
