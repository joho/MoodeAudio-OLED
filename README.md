# MoodeAudio OLED Display (2025 Edition)

Modern OLED display integration for MoodeAudio 9.x running on Raspberry Pi OS Bookworm.

> **Note**: This is a modernized fork of [naisema/MoodeAudio-OLED](https://github.com/naisema/MoodeAudio-OLED), updated for 2025 with Python 3.11+, modern packaging, and current best practices.

![OLED Display](OLED%20128x64.jpg)

## Features

- 🎵 Real-time display of current playing track
- 📊 Shows artist, title, audio format, elapsed time, and volume
- 🔄 Auto-scrolling for long text
- 🚀 Modern Python 3.11+ with type hints and logging
- ⚡ Fast dependency management with uv
- 🔒 Secure systemd service with resource limits
- 🔌 Plug-and-play with MoodeAudio 9.2.6

## Supported Hardware

- **Raspberry Pi**: Zero 2 W, 3, 4, 5 (tested on Zero 2 W)
- **Display**: SSD1306 128x64 OLED (I2C)
- **OS**: Raspberry Pi OS Bookworm 64-bit
- **MoodeAudio**: Version 9.2.6 or later

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/naisema/MoodeAudio-OLED.git
cd MoodeAudio-OLED

# Run the automated installer
chmod +x install.sh
./install.sh
```

The installer will:
- ✅ Install uv package manager
- ✅ Set up Python virtual environment
- ✅ Install all dependencies
- ✅ Configure systemd service
- ✅ Set up hardware permissions

## Hardware Wiring

Connect your SSD1306 OLED display to the Raspberry Pi:

| OLED Pin | RPi Pin | RPi GPIO |
|----------|---------|----------|
| VCC      | Pin 1   | 3.3V     |
| GND      | Pin 6   | Ground   |
| SDA      | Pin 3   | GPIO 2   |
| SCL      | Pin 5   | GPIO 3   |

## Usage

### Starting the Service

```bash
# Start the service
sudo systemctl start moode-oled.service

# Check status
sudo systemctl status moode-oled.service

# View live logs
sudo journalctl -u moode-oled.service -f
```

### Manual Testing

```bash
# Activate the virtual environment
source ~/MoodeAudio-OLED/.venv/bin/activate

# Test MoodeAudio API (recommended first)
python test_moode_api.py

# Run standard mode (MPD only)
python -m moode_oled.main

# Run enhanced mode (all sources including Spotify/Bluetooth) ⭐
python -m moode_oled.main_enhanced
```

## Configuration

### Enable I2C (if not already enabled)

```bash
sudo raspi-config
```
Navigate to: `Interfacing Options` → `I2C` → `Enable`

### Speed up I2C (optional)

For better performance, add to `/boot/firmware/config.txt`:
```
dtparam=i2c_baudrate=1000000
```

## Development

### Prerequisites
- Python 3.11+
- uv package manager

### Setup Development Environment

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv .venv --python 3.11
source .venv/bin/activate

# Install in development mode
uv pip install -e ".[dev]"
```

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

## ✨ Enhanced Multi-Source Support

This modernized version supports **ALL MoodeAudio sources** including Spotify and Bluetooth!

### 🎯 **Two Display Modes Available**

#### **Standard Mode** (MPD only)
- Uses traditional MPD connection
- Works with: Local files, Internet radio, UPnP/DLNA
- Run with: `python -m moode_oled.main`

#### **Enhanced Mode** (All sources) ⭐
- Uses MoodeAudio's REST API + MPD fallback  
- Works with: **Everything above PLUS Spotify Connect, Bluetooth, AirPlay**
- Run with: `python -m moode_oled.main_enhanced`

### ✅ **Enhanced Mode Support**
- **Spotify Connect**: Full track metadata ✅
- **Bluetooth**: Track info when available ✅
- **AirPlay**: Track metadata ✅
- **Local music library**: Full metadata ✅
- **Internet radio**: Station and track info ✅
- **UPnP/DLNA**: Full metadata ✅

### ⚙️ **Setup for Enhanced Mode**

Enable metadata file in MoodeAudio:
1. Go to **Configure** → **Audio** → **General**
2. Set **Metadata file** to **ON**
3. Click **APPLY**

Then use the enhanced version for all audio sources!

## Troubleshooting

### Display Not Working
1. Check I2C is enabled: `sudo i2cdetect -y 1`
2. Verify wiring connections
3. Check service logs: `sudo journalctl -u moode-oled.service`

### MPD Connection Issues
1. Ensure MoodeAudio is running
2. Check MPD status: `sudo systemctl status mpd`
3. Test MPD connection: `telnet localhost 6600`
4. Run debug script: `python debug_mpd.py`

### Connection Drops
The display now automatically reconnects to MPD if the connection is lost. If you see "Reconnecting..." messages, this is normal behavior.

### Permission Errors
1. Ensure user is in gpio group: `groups`
2. Check file permissions in project directory

### Audio Source Debugging
Use the included debug scripts:
```bash
cd ~/MoodeAudio-OLED
source .venv/bin/activate

# Test MoodeAudio API (for Spotify/Bluetooth)
python test_moode_api.py

# Test MPD connection (for local files/radio)
python debug_mpd.py
```

### Spotify/Bluetooth Not Working
1. Ensure "Metadata file" is enabled in MoodeAudio Audio Config
2. Run `python test_moode_api.py` to verify API access
3. Use enhanced mode: `python -m moode_oled.main_enhanced`
4. Check that `/var/local/www/currentsong.txt` exists and updates

## Migration from Old Version

If upgrading from the original Python 2.7 version:

1. Stop the old service: `sudo systemctl stop moode-oled`
2. Remove old files and dependencies
3. Follow the installation steps above
4. The new version uses different font paths and library imports

**Note**: The installer automatically detects your current user, so it works with any username (not just 'pi').

## License

MIT License - see original project for attribution.

## Credits

- **Original project**: [naisema/MoodeAudio-OLED](https://github.com/naisema/MoodeAudio-OLED) by Suwat Saisema
- **Modernization**: Updated for 2025 with current best practices
- **Libraries**: Uses Adafruit CircuitPython libraries
- **License**: MIT License (maintained from original)
