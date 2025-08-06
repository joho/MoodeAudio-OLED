# MoodeAudio-OLED Agent Configuration (2025 Edition)

## Project Context
This is a modernized fork of naisema/MoodeAudio-OLED, updated for 2025 with Python 3.11+, modern packaging, and current best practices. The original project was created by Suwat Saisema for Python 2.7 and older hardware libraries.

## Architecture
Modern Python 3.11+ package with proper structure. Main module `src/moode_oled/display.py` contains OLED display logic and MPD client. Uses CircuitPython libraries for hardware access and python-mpd2 for MPD communication.

## Dependencies & Setup
- uv package manager for fast dependency resolution
- Python 3.11+ with type hints and modern features
- Dependencies: adafruit-circuitpython-ssd1306, python-mpd2, pillow, RPi.GPIO
- Hardware: Raspberry Pi with I2C enabled, SSD1306 OLED display

## Commands
- Install: `./install.sh` (automated installer)
- Dev setup: `uv venv .venv && uv pip install -e ".[dev]"`
- Run: `python -m moode_oled.main` (from venv)
- Service: `sudo systemctl start moode-oled.service`
- Logs: `sudo journalctl -u moode-oled.service -f`
- Format: `black src/` | Lint: `ruff check src/` | Types: `mypy src/`

## Code Style
- Python 3.11+ with type hints (all functions typed)
- Classes: CamelCase | Variables/functions: snake_case
- 88 char line length | Black formatting | Ruff linting
- Logging instead of print statements | Proper error handling
- Use pathlib.Path for file operations
