#!/usr/bin/env python3
"""Helper script to set up MoodeAudio LCD Update Engine integration."""

import os
import subprocess
from pathlib import Path

def setup_lcd_engine():
    """Help user set up LCD Update Engine integration."""
    print("🔧 MoodeAudio LCD Update Engine Setup Helper")
    print("=" * 50)
    
    # Get current user and project path
    current_user = os.environ.get('USER', 'pi')
    project_dir = Path.cwd()
    venv_python = project_dir / ".venv" / "bin" / "python"
    
    print(f"👤 Current user: {current_user}")
    print(f"📁 Project directory: {project_dir}")
    print(f"🐍 Virtual environment: {venv_python}")
    
    # Check if venv exists
    if not venv_python.exists():
        print(f"\n❌ Virtual environment not found at {venv_python}")
        print("Please run the installer first: ./install.sh")
        return
    
    # Script path for LCD engine
    lcd_script_path = f"{venv_python} -m moode_oled.main_lcd"
    
    print(f"\n✅ LCD Update Engine script path:")
    print(f"   {lcd_script_path}")
    
    print(f"\n📋 Manual Setup Instructions:")
    print(f"1. Open MoodeAudio web interface")
    print(f"2. Go to: Configure → System → Local Services")
    print(f"3. Find: LCD update engine")
    print(f"4. Enter script path: {lcd_script_path}")
    print(f"5. Enable the LCD update engine")
    print(f"6. Click APPLY")
    
    print(f"\n🧪 Test the script manually:")
    print(f"   cd {project_dir}")
    print(f"   source .venv/bin/activate")
    print(f"   python -m moode_oled.main_lcd")
    
    # Test if we can run the script
    print(f"\n🔍 Testing LCD updater script...")
    try:
        os.chdir(project_dir)
        result = subprocess.run([
            str(venv_python), "-m", "moode_oled.main_lcd"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ LCD updater script ran successfully!")
        else:
            print(f"❌ LCD updater script failed with return code {result.returncode}")
            if result.stderr:
                print(f"Error: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        print("⚠️  Script timed out (this might be normal for display operations)")
    except Exception as e:
        print(f"❌ Error testing script: {e}")
    
    # Check for currentsong file
    currentsong_file = Path("/var/local/www/currentsong.txt")
    print(f"\n📄 Checking for currentsong file...")
    if currentsong_file.exists():
        print(f"✅ Found: {currentsong_file}")
        try:
            content = currentsong_file.read_text()[:100]
            print(f"   Content preview: {content}...")
        except Exception as e:
            print(f"   Could not read content: {e}")
    else:
        print(f"❌ Not found: {currentsong_file}")
        print(f"   You may need to enable 'Metadata file' in MoodeAudio settings first")
    
    print(f"\n🎵 This integration supports ALL MoodeAudio sources:")
    print(f"   ✅ Spotify Connect")
    print(f"   ✅ Bluetooth") 
    print(f"   ✅ AirPlay")
    print(f"   ✅ Local music library")
    print(f"   ✅ Internet radio")
    print(f"   ✅ UPnP/DLNA")

if __name__ == "__main__":
    setup_lcd_engine()
