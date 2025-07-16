#!/usr/bin/env python3
"""Test script for audio capture functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from newear.audio.capture import AudioCapture, AudioConfig


def main():
    """Test audio capture functionality."""
    print("=== Newear Audio Capture Test ===\n")
    
    # Create audio capture instance
    config = AudioConfig(
        sample_rate=16000,
        channels=1,
        chunk_duration=3.0
    )
    
    capture = AudioCapture(config)
    
    # List available devices
    print("Available audio devices:")
    capture.device_manager.list_devices()
    print()
    
    # Test audio capture
    try:
        print("Testing audio capture for 10 seconds...")
        print("Play some audio (music, video, etc.) to test audio routing...")
        print()
        
        success = capture.test_capture(duration=10.0)
        
        print("\n" + "="*50)
        print("CONCLUSION:")
        print("="*50)
        
        if success:
            print("✅ Audio capture test SUCCESSFUL!")
            print("\n✅ Your system is ready for live captioning!")
            print("✅ BlackHole is properly configured")
            print("✅ Audio routing is working correctly")
            print("\nYou can now run: newear --output transcript.txt")
            
            print("\nDevice info:")
            info = capture.get_device_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("❌ Audio capture test FAILED!")
            print("\n❌ Live captioning will NOT work until this is fixed")
            print("❌ No audio signal detected from BlackHole")
            print("\nTroubleshooting steps:")
            print("1. Install BlackHole: brew install blackhole-2ch")
            print("2. Create a Multi-Output Device in Audio MIDI Setup")
            print("3. Set the Multi-Output Device as your system output")
            print("4. Play some audio and run this test again")
            
    except Exception as e:
        print(f"\n❌ Error during audio capture test: {e}")
        print("\n❌ Live captioning will NOT work until this is fixed")
        print("\nTroubleshooting steps:")
        print("1. Make sure you have the required dependencies installed:")
        print("   pip install sounddevice numpy")
        print("2. Install BlackHole virtual audio device:")
        print("   brew install blackhole-2ch")
        print("3. Configure your system audio routing")
        print("4. Run this test again")


if __name__ == "__main__":
    main()