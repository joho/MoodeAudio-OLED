#!/bin/bash
set -e

# Modern MoodeAudio OLED Display Installation Script
# For Raspberry Pi OS Bookworm with MoodeAudio 9.2.6

echo "🎵 Installing MoodeAudio OLED Display (Modern Version)"
echo "======================================================="

# Detect current user and validate
CURRENT_USER="$USER"
CURRENT_HOME="$HOME"

if [ "$CURRENT_USER" = "root" ]; then
    echo "❌ Please do not run this script as root. Run as your regular user."
    echo "   The script will use sudo when needed."
    exit 1
fi

if [ -z "$CURRENT_USER" ] || [ -z "$CURRENT_HOME" ]; then
    echo "❌ Could not detect current user. Please check your environment."
    exit 1
fi

echo "👤 Installing for user: $CURRENT_USER"
echo "🏠 Home directory: $CURRENT_HOME"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "❌ This script must be run on a Raspberry Pi"
    exit 1
fi

# Check if I2C is enabled
if ! ls /dev/i2c* >/dev/null 2>&1; then
    echo "❌ I2C is not enabled. Please run 'sudo raspi-config' and enable I2C"
    exit 1
fi

echo "✅ Raspberry Pi detected with I2C enabled"

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git

# Install system dependencies for hardware access
echo "🔧 Installing system dependencies..."
sudo apt-get install -y python3-dev python3-setuptools

# Install uv (modern Python package manager)
echo "⚡ Installing uv package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add uv to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    # Source bashrc to ensure uv is available
    if [ -f "$HOME/.bashrc" ]; then
        source "$HOME/.bashrc" || true
    fi
fi

# Set up project directory
PROJECT_DIR="$CURRENT_HOME/MoodeAudio-OLED"
echo "📁 Setting up project in $PROJECT_DIR"

if [ ! -d "$PROJECT_DIR" ]; then
    mkdir -p "$PROJECT_DIR"
fi

# Copy project files if running from different location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "$SCRIPT_DIR" != "$PROJECT_DIR" ]; then
    echo "📋 Copying project files to $PROJECT_DIR"
    cp -r "$SCRIPT_DIR"/* "$PROJECT_DIR/"
fi

cd "$PROJECT_DIR"

# Create Python virtual environment with uv
echo "🐍 Creating Python environment with uv..."
uv venv .venv --python 3.11
source .venv/bin/activate

# Install dependencies
echo "📚 Installing Python dependencies..."
uv pip install -e .

# Install additional system packages for Raspberry Pi GPIO
echo "🔌 Installing Raspberry Pi specific packages..."
uv pip install RPi.GPIO adafruit-blinka

# Create systemd service file with dynamic user
echo "⚙️  Setting up systemd service..."
SERVICE_FILE="/tmp/moode-oled.service"
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=MoodeAudio OLED Display (Modern)
After=network.target mpd.service
Wants=mpd.service
 
[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python -m moode_oled.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security and resource limits
PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=$PROJECT_DIR
NoNewPrivileges=true
MemoryMax=128M
TasksMax=10

[Install]
WantedBy=multi-user.target
EOF

sudo cp "$SERVICE_FILE" /etc/systemd/system/moode-oled.service
sudo systemctl daemon-reload
sudo systemctl enable moode-oled.service

# Add user to gpio and i2c groups
echo "👤 Adding user to hardware access groups..."
sudo usermod -a -G gpio,i2c "$CURRENT_USER"

# Test I2C connection
echo "🔍 Testing I2C connection..."
if command -v i2cdetect &> /dev/null; then
    echo "Scanning for I2C devices..."
    sudo i2cdetect -y 1 || echo "No I2C devices detected (this is OK if display isn't connected yet)"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "👤 Installed for user: $CURRENT_USER"
echo "📁 Project location: $PROJECT_DIR"
echo ""
echo "🚀 To start the service:"
echo "   sudo systemctl start moode-oled.service"
echo ""
echo "📊 To check service status:"
echo "   sudo systemctl status moode-oled.service"
echo ""
echo "📝 To view logs:"
echo "   sudo journalctl -u moode-oled.service -f"
echo ""
echo "🔧 Manual testing:"
echo "   cd $PROJECT_DIR"
echo "   source .venv/bin/activate"
echo "   python -m moode_oled.main"
echo ""
echo "🔌 Hardware setup:"
echo "   Connect your SSD1306 OLED display to:"
echo "   - VCC to 3.3V (Pin 1)"
echo "   - GND to Ground (Pin 6)"
echo "   - SDA to GPIO 2 (Pin 3)"
echo "   - SCL to GPIO 3 (Pin 5)"
echo ""
echo "🎵 MoodeAudio integration:"
echo "   The service will automatically connect to MPD on localhost:6600"
echo "   No additional MoodeAudio configuration required!"
echo ""
echo "⚠️  NOTE: You may need to log out and back in for group changes to take effect."
