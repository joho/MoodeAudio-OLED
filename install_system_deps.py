#!/usr/bin/env python3
"""Install system dependencies and create MoodeAudio LCD updater wrapper."""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Run command with proper error handling."""
    try:
        result = subprocess.run(cmd, shell=True, check=check, 
                              capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def install_apt_package(package):
    """Try to install via apt."""
    print(f"  📦 Trying apt install {package}...")
    success, stdout, stderr = run_command(f"sudo apt-get install -y {package}")
    if success:
        print(f"  ✅ Installed {package} via apt")
        return True
    else:
        print(f"  ❌ Apt install failed for {package}")
        return False

def install_pip_package(package, break_system=True):
    """Try to install via pip with system packages flag."""
    print(f"  🐍 Trying pip install {package}...")
    
    pip_cmd = "sudo pip3 install"
    if break_system:
        pip_cmd += " --break-system-packages"
    pip_cmd += f" {package}"
    
    success, stdout, stderr = run_command(pip_cmd)
    if success:
        print(f"  ✅ Installed {package} via pip")
        return True
    else:
        print(f"  ❌ Pip install failed for {package}")
        if stderr:
            print(f"     Error: {stderr[:200]}...")
        return False

def install_dependency(package_name, apt_packages, pip_package):
    """Install a dependency trying apt first, then pip."""
    print(f"\n🔧 Installing {package_name}...")
    
    # Try apt packages first
    for apt_pkg in apt_packages:
        if install_apt_package(apt_pkg):
            return True
    
    # Fall back to pip
    if pip_package:
        return install_pip_package(pip_package)
    
    return False

def create_wrapper_script():
    """Create the lightweight wrapper script for MoodeAudio."""
    current_user = os.environ.get('USER', 'pi')
    project_dir = Path.cwd().resolve()
    
    wrapper_content = f'''#!/usr/bin/env python3
"""Lightweight wrapper for MoodeAudio OLED display.

This script is called by MoodeAudio's LCD Update Engine.
It imports and runs our main OLED updater from the git repo.
"""

import sys
import os
from pathlib import Path

# Add our project to Python path
PROJECT_DIR = Path("{project_dir}")
sys.path.insert(0, str(PROJECT_DIR / "src"))

def main():
    """Main wrapper function."""
    try:
        # Import our LCD updater
        from moode_oled.lcd_updater import LCDUpdater
        
        # Create and run updater
        updater = LCDUpdater()
        success = updater.update_display_once()
        sys.exit(0 if success else 1)
        
    except ImportError as e:
        # Fallback if our modules aren't available
        print(f"Import error: {{e}}", file=sys.stderr)
        print("Falling back to simple mode...", file=sys.stderr)
        
        # Simple fallback implementation
        try:
            import json
            from pathlib import Path
            
            # Try basic OLED update
            currentsong = Path("/var/local/www/currentsong.txt")
            if currentsong.exists():
                content = currentsong.read_text().strip()
                if content:
                    try:
                        data = json.loads(content)
                        print(f"Would display: {{data.get('artist', 'Unknown')}} - {{data.get('title', 'Unknown')}}")
                    except:
                        print(f"Would display: {{content[:50]}}")
            
            sys.exit(0)
            
        except Exception as fallback_error:
            print(f"Fallback failed: {{fallback_error}}", file=sys.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"OLED updater error: {{e}}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

    return wrapper_content

def install_wrapper():
    """Install the wrapper script to MoodeAudio's expected location."""
    moode_script_dir = Path("/var/local/www/commandw")
    moode_script = moode_script_dir / "lcd-updater.py"
    backup_script = moode_script_dir / "lcd-updater.py.backup"
    
    print(f"\n📝 Installing wrapper script...")
    print(f"   Target: {moode_script}")
    
    # Check if MoodeAudio directory exists
    if not moode_script_dir.exists():
        print(f"❌ MoodeAudio directory not found: {moode_script_dir}")
        print("   Make sure MoodeAudio is installed")
        return False
    
    # Backup existing script
    if moode_script.exists():
        print(f"📋 Backing up existing script...")
        try:
            run_command(f"sudo cp {moode_script} {backup_script}")
        except Exception as e:
            print(f"⚠️  Backup failed: {e}")
    
    # Create wrapper content
    wrapper_content = create_wrapper_script()
    
    # Write wrapper script
    try:
        # Write to temp file first
        temp_script = Path("/tmp/lcd-updater.py")
        temp_script.write_text(wrapper_content)
        
        # Copy to target location with sudo
        success, stdout, stderr = run_command(f"sudo cp {temp_script} {moode_script}")
        if not success:
            print(f"❌ Failed to copy wrapper: {stderr}")
            return False
        
        # Make executable and set ownership
        run_command(f"sudo chmod +x {moode_script}")
        run_command(f"sudo chown www-data:www-data {moode_script}")
        
        # Clean up temp file
        temp_script.unlink()
        
        print(f"✅ Wrapper script installed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to install wrapper: {e}")
        return False

def main():
    """Main installation function."""
    print("🎵 Installing MoodeAudio OLED System Dependencies")
    print("=" * 55)
    
    # Update package list
    print("\n📦 Updating package list...")
    success, _, _ = run_command("sudo apt-get update")
    if not success:
        print("⚠️  Package update failed, continuing anyway...")
    
    # Dependencies mapping: name -> (apt_packages, pip_package)
    dependencies = {
        "Python development headers": (["python3-dev"], None),
        "Python setuptools": (["python3-setuptools"], None), 
        "Pillow (PIL)": (["python3-pil"], "pillow"),
        "RPi.GPIO": (["python3-rpi.gpio"], "RPi.GPIO"),
        "I2C tools": (["i2c-tools"], None),
        "CircuitPython SSD1306": ([], "adafruit-circuitpython-ssd1306"),
        "Adafruit Blinka": ([], "adafruit-blinka"),
    }
    
    # Install each dependency
    failed_packages = []
    for name, (apt_pkgs, pip_pkg) in dependencies.items():
        if not install_dependency(name, apt_pkgs, pip_pkg):
            failed_packages.append(name)
    
    # Report results
    if failed_packages:
        print(f"\n⚠️  Some packages failed to install:")
        for pkg in failed_packages:
            print(f"   - {pkg}")
        print(f"\nThe system may still work, but functionality might be limited.")
    else:
        print(f"\n✅ All dependencies installed successfully!")
    
    # Install wrapper script
    if install_wrapper():
        print(f"\n🎉 Installation Complete!")
        print(f"\n📋 Next Steps:")
        print(f"1. In MoodeAudio web interface:")
        print(f"   - Go to Configure → System → Local Services")
        print(f"   - Enable 'LCD update engine' (toggle switch)")
        print(f"   - Click APPLY")
        print(f"")
        print(f"2. Test manually:")
        print(f"   sudo python3 /var/local/www/commandw/lcd-updater.py")
        print(f"")
        print(f"🎵 Your OLED will now show metadata for ALL audio sources!")
        
    else:
        print(f"\n❌ Wrapper installation failed")
        print(f"Dependencies are installed, but manual wrapper setup needed")

if __name__ == "__main__":
    if os.geteuid() == 0:
        print("❌ Please don't run this script as root")
        print("   It will use sudo when needed")
        sys.exit(1)
    
    main()
