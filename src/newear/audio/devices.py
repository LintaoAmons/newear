"""Audio device detection and management for macOS."""

import sounddevice as sd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class AudioDevice:
    """Represents an audio device."""
    index: int
    name: str
    max_input_channels: int
    max_output_channels: int
    default_samplerate: float
    hostapi: int


class AudioDeviceManager:
    """Manages audio devices for macOS system audio capture."""
    
    def __init__(self):
        self.devices = self._get_devices()
        
    def _get_devices(self) -> List[AudioDevice]:
        """Get all available audio devices."""
        devices = []
        device_list = sd.query_devices()
        
        for i, device in enumerate(device_list):
            devices.append(AudioDevice(
                index=i,
                name=device['name'],
                max_input_channels=device['max_input_channels'],
                max_output_channels=device['max_output_channels'],
                default_samplerate=device['default_samplerate'],
                hostapi=device['hostapi']
            ))
        
        return devices
    
    def find_blackhole_device(self) -> Optional[AudioDevice]:
        """Find BlackHole virtual audio device."""
        for device in self.devices:
            if 'blackhole' in device.name.lower():
                return device
        return None
    
    def find_system_audio_devices(self) -> List[AudioDevice]:
        """Find devices that might capture system audio."""
        candidates = []
        
        # Look for BlackHole first (preferred)
        blackhole = self.find_blackhole_device()
        if blackhole:
            candidates.append(blackhole)
        
        # Look for other virtual audio devices
        for device in self.devices:
            name_lower = device.name.lower()
            if any(keyword in name_lower for keyword in ['soundflower', 'loopback', 'aggregate']):
                if device not in candidates:
                    candidates.append(device)
        
        return candidates
    
    def get_default_input_device(self) -> Optional[AudioDevice]:
        """Get the default input device."""
        try:
            default_device = sd.default.device[0]  # Input device index
            if default_device is not None:
                return self.devices[default_device]
        except (IndexError, TypeError):
            pass
        return None
    
    def print_devices(self) -> None:
        """Print all available audio devices."""
        print("Available Audio Devices:")
        print("-" * 50)
        
        for device in self.devices:
            device_type = []
            if device.max_input_channels > 0:
                device_type.append("Input")
            if device.max_output_channels > 0:
                device_type.append("Output")
            
            print(f"{device.index:2d}: {device.name}")
            print(f"    Type: {', '.join(device_type)}")
            print(f"    Channels: In={device.max_input_channels}, Out={device.max_output_channels}")
            print(f"    Sample Rate: {device.default_samplerate} Hz")
            print()
    
    def validate_device_for_capture(self, device: AudioDevice) -> bool:
        """Validate if a device can be used for audio capture."""
        return device.max_input_channels > 0
    
    def get_recommended_device(self) -> Optional[AudioDevice]:
        """Get the recommended device for system audio capture."""
        # Try BlackHole first
        blackhole = self.find_blackhole_device()
        if blackhole and self.validate_device_for_capture(blackhole):
            return blackhole
        
        # Try other system audio devices
        system_devices = self.find_system_audio_devices()
        for device in system_devices:
            if self.validate_device_for_capture(device):
                return device
        
        return None
