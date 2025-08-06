#!/usr/bin/env python3
"""Debug script to understand MPD behavior with different audio sources."""

import time
from mpd import MPDClient, MPDError

def debug_mpd():
    """Debug MPD connection and status."""
    client = MPDClient()
    
    try:
        print("Connecting to MPD...")
        client.connect("localhost", 6600)
        print("✅ Connected to MPD successfully")
        
        for i in range(60):  # Run for 60 seconds
            try:
                print(f"\n--- Update {i+1} ---")
                
                # Get current song
                song = client.currentsong()
                print(f"Current song: {song}")
                
                # Get status
                status = client.status()
                print(f"Status: {status}")
                
                # Check what audio source is active
                state = status.get('state', 'unknown')
                print(f"Player state: {state}")
                
                if 'audio' in status:
                    print(f"Audio format: {status['audio']}")
                
                if song:
                    artist = song.get('artist', 'N/A')
                    title = song.get('title', 'N/A')
                    file = song.get('file', 'N/A')
                    print(f"Playing: {artist} - {title}")
                    print(f"File: {file}")
                else:
                    print("No current song")
                
                # Check if there are any queue items
                playlist = client.playlistinfo()
                print(f"Playlist length: {len(playlist)}")
                
                time.sleep(5)
                
            except MPDError as e:
                print(f"MPD Error: {e}")
                time.sleep(5)
            except Exception as e:
                print(f"Other error: {e}")
                time.sleep(5)
                
    except Exception as e:
        print(f"Failed to connect: {e}")
    finally:
        try:
            client.close()
            client.disconnect()
        except:
            pass

if __name__ == "__main__":
    debug_mpd()
