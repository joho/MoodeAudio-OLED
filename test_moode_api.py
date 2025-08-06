#!/usr/bin/env python3
"""Test script for MoodeAudio REST API and metadata file."""

import json
import time
from src.moode_oled.moode_api import MoodeMetadata

def test_moode_api():
    """Test MoodeAudio API functionality."""
    print("🎵 Testing MoodeAudio REST API and Metadata")
    print("=" * 50)
    
    moode = MoodeMetadata()
    
    # Check if metadata file exists
    print(f"📁 Metadata file enabled: {moode.is_metadata_enabled()}")
    print(f"📁 Metadata file path: {moode.currentsong_file}")
    
    if not moode.is_metadata_enabled():
        print("\n⚠️  IMPORTANT: Metadata file not found!")
        print("   Enable 'Metadata file' in MoodeAudio:")
        print("   Go to: Configure → Audio → General → Metadata file → ON")
        print("   Then restart this test.")
        print()
    
    # Test output format
    try:
        output_format = moode.get_output_format()
        print(f"🎧 Audio output format: {output_format}")
    except Exception as e:
        print(f"❌ Failed to get output format: {e}")
    
    print("\n🔄 Testing metadata fetch (will run for 60 seconds)...")
    print("   Try playing music via Spotify, Bluetooth, or local files")
    print("   Press Ctrl+C to stop early\n")
    
    try:
        for i in range(60):
            print(f"--- Update {i+1}/60 ---")
            
            # Test metadata fetching
            try:
                metadata = moode.fetch_metadata()
                print(f"State: {metadata['state']}")
                print(f"Artist: {metadata['artist']}")
                print(f"Title: {metadata['title']}")
                print(f"Time: {metadata['eltime']}")
                print(f"Volume: {metadata['volume']}")
                print(f"Audio: {metadata['audio_info']}")
                
                # Show pretty JSON
                print("Raw data:", json.dumps(metadata, indent=2))
                
            except Exception as e:
                print(f"❌ Error fetching metadata: {e}")
            
            print()
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test stopped by user")
    
    print("\n✅ Test completed!")
    print("\nIf you saw track info for Spotify/Bluetooth, the enhanced display will work!")
    print("If not, make sure 'Metadata file' is enabled in MoodeAudio settings.")

if __name__ == "__main__":
    test_moode_api()
