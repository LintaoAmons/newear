#!/usr/bin/env python3
"""Test script for audio capture functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from newear.audio import AudioCapture, AudioConfig


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
    capture.list_devices()
    print()
    
    # Test audio capture
    try:
        print("Testing audio capture...")
        success = capture.test_capture(duration=10.0)
        
        if success:
            print("✅ Audio capture test successful!")
            print("\nDevice info:")
            info = capture.get_device_info()
            for key, value in info.items():
                print(f"  {key}: {value}")
        else:
            print("❌ Audio capture test failed!")
            print("\nTroubleshooting:")
            print("1. Install BlackHole: brew install blackhole-2ch")
            print("2. Create a Multi-Output Device in Audio MIDI Setup")
            print("3. Set the Multi-Output Device as your system output")
            
    except Exception as e:
        print(f"❌ Error during audio capture test: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have the required dependencies installed:")
        print("   pip install sounddevice numpy")
        print("2. Install BlackHole virtual audio device:")
        print("   brew install blackhole-2ch")
        print("3. Configure your system audio routing")


if __name__ == "__main__":
    main()