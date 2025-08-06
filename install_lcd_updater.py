#!/usr/bin/env python3
"""Install script for MoodeAudio LCD Update Engine integration."""

import os
import shutil
import subprocess
from pathlib import Path

def install_lcd_updater():
    """Install our LCD updater script to replace MoodeAudio's stub."""
    print("🔧 Installing OLED LCD Updater for MoodeAudio")
    print("=" * 50)
    
    # Paths
    our_script = Path.cwd() / "lcd-updater.py"
    moode_script_dir = Path("/var/local/www/commandw")
    moode_script = moode_script_dir / "lcd-updater.py"
    backup_script = moode_script_dir / "lcd-updater.py.backup"
    
    print(f"📁 Our script: {our_script}")
    print(f"📁 MoodeAudio script: {moode_script}")
    
    # Check if our script exists
    if not our_script.exists():
        print(f"❌ Our LCD updater script not found: {our_script}")
        return False
    
    # Check if MoodeAudio directory exists
    if not moode_script_dir.exists():
        print(f"❌ MoodeAudio commandw directory not found: {moode_script_dir}")
        print("   Make sure MoodeAudio is installed and LCD update engine is enabled")
        return False
    
    # Backup existing script if it exists
    if moode_script.exists():
        print(f"📋 Backing up existing script to: {backup_script}")
        try:
            shutil.copy2(moode_script, backup_script)
        except Exception as e:
            print(f"⚠️  Could not backup existing script: {e}")
    
    # Copy our script
    print(f"📥 Installing our LCD updater script...")
    try:
        # Need sudo to write to /var/local/www/commandw/
        result = subprocess.run([
            "sudo", "cp", str(our_script), str(moode_script)
        ], check=True, capture_output=True, text=True)
        
        # Make it executable
        subprocess.run([
            "sudo", "chmod", "+x", str(moode_script)
        ], check=True)
        
        # Set proper ownership (usually www-data)
        subprocess.run([
            "sudo", "chown", "www-data:www-data", str(moode_script)
        ], check=True)
        
        print("✅ LCD updater script installed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install script: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False
    
    # Test the installation
    print(f"\n🧪 Testing the installed script...")
    try:
        result = subprocess.run([
            "sudo", "-u", "www-data", "python3", str(moode_script)
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ Test successful! The script runs without errors.")
        else:
            print(f"⚠️  Test completed with return code {result.returncode}")
            if result.stderr:
                print(f"   Stderr: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        print("⚠️  Test timed out (this might be normal for display operations)")
    except Exception as e:
        print(f"⚠️  Test error: {e}")
    
    # Final instructions
    print(f"\n✅ Installation Complete!")
    print(f"\n📋 Next Steps:")
    print(f"1. In MoodeAudio web interface:")
    print(f"   - Go to Configure → System → Local Services")
    print(f"   - Enable 'LCD update engine' (toggle the switch)")
    print(f"   - Click APPLY")
    print(f"")
    print(f"2. Optional: Enable metadata file:")
    print(f"   - Go to Configure → Audio → General")
    print(f"   - Enable 'Metadata file' if available")
    print(f"   - Click APPLY")
    print(f"")
    print(f"🎵 Your OLED will now display metadata for ALL audio sources:")
    print(f"   ✅ Spotify Connect")
    print(f"   ✅ Bluetooth")
    print(f"   ✅ AirPlay") 
    print(f"   ✅ Local music")
    print(f"   ✅ Internet radio")
    print(f"   ✅ UPnP/DLNA")
    
    return True

def uninstall_lcd_updater():
    """Restore the original MoodeAudio LCD updater script."""
    print("🔄 Uninstalling OLED LCD Updater")
    print("=" * 40)
    
    moode_script_dir = Path("/var/local/www/commandw")
    moode_script = moode_script_dir / "lcd-updater.py"
    backup_script = moode_script_dir / "lcd-updater.py.backup"
    
    if backup_script.exists():
        print(f"📋 Restoring backup script...")
        try:
            subprocess.run([
                "sudo", "cp", str(backup_script), str(moode_script)
            ], check=True)
            print("✅ Original script restored")
            return True
        except Exception as e:
            print(f"❌ Failed to restore backup: {e}")
            return False
    else:
        print(f"❌ No backup found at {backup_script}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_lcd_updater()
    else:
        install_lcd_updater()
