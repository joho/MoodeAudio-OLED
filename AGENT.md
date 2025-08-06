# MoodeAudio-OLED Agent Configuration

## Architecture
Single Python script (`moode-oled.py`) that displays MoodeAudio player information on 128x64 OLED display using Adafruit SSD1306 library. Connects to MPD (Music Player Daemon) via localhost:6600 to fetch current song data.

## Dependencies & Setup
- Manual installation required: Adafruit Python GPIO + SSD1306 libraries, python-mpd, PIL/Pillow
- Hardware: Raspberry Pi with I2C enabled, SSD1306 OLED display on GPIO pins 23/24
- Service: Run via systemd service or MoodeAudio's LCD update engine

## File Structure
- `moode-oled.py`: Main display script with MPD client and OLED rendering
- `moode-oled.service`: systemd service file
- `*.ttf`: Font files (Arial-Unicode, Verdana) for display rendering

## Code Style
- Python 2.7 style (uses `reload(sys)`, `unicode()`)
- Mixed indentation (tabs/spaces) - use existing style
- Classes: CamelCase (e.g., `MPDConnect`)
- Variables: snake_case
- No type hints or modern Python features

## Running/Testing
- Test: `python moode-oled.py` (requires hardware)
- Service: `sudo systemctl start moode-oled.service`
- No unit tests - hardware-dependent display script
