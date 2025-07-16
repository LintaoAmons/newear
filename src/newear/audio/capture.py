"""Real-time audio capture for macOS system audio."""

import sounddevice as sd
import numpy as np
import threading
import queue
import time
from typing import Optional, Callable, Generator
from dataclasses import dataclass

from .devices import AudioDevice, AudioDevices


@dataclass
class AudioConfig:
    """Audio capture configuration."""
    sample_rate: int = 16000  # Whisper's preferred sample rate
    channels: int = 1  # Mono audio
    chunk_duration: float = 5.0  # Duration of each audio chunk in seconds
    buffer_size: int = 4096  # Audio buffer size
    dtype: str = 'float32'  # Audio data type


class AudioCapture:
    """Handles real-time audio capture from macOS system audio."""
    
    def __init__(self, config):
        # Convert from Config to AudioConfig
        if hasattr(config, 'sample_rate'):
            self.config = AudioConfig(
                sample_rate=config.sample_rate,
                channels=1,
                chunk_duration=config.chunk_duration,
                buffer_size=4096,
                dtype='float32'
            )
        else:
            self.config = config or AudioConfig()
        self.device_manager = AudioDevices()
        self.device: Optional[AudioDevice] = None
        self.stream: Optional[sd.InputStream] = None
        self.audio_queue = queue.Queue()
        self.is_capturing = False
        self._capture_thread: Optional[threading.Thread] = None
        
        # Setup device from config
        device_index = getattr(config, 'device_index', None)
        self.setup_device(device_index)
        
    def setup_device(self, device_index: Optional[int] = None) -> bool:
        """Setup audio device for capture."""
        if device_index is not None:
            # Use specific device
            if device_index < len(self.device_manager.devices):
                self.device = self.device_manager.devices[device_index]
            else:
                raise ValueError(f"Device index {device_index} not found")
        else:
            # Auto-select recommended device
            self.device = self.device_manager.get_recommended_device()
            if not self.device:
                raise RuntimeError("No suitable audio device found. Please install BlackHole or configure a virtual audio device.")
        
        if not self.device_manager.validate_device_for_capture(self.device):
            raise RuntimeError(f"Device '{self.device.name}' cannot be used for audio capture")
        
        return True
    
    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback function for audio stream."""
        if status:
            print(f"Audio callback status: {status}")
        
        # Convert to mono if stereo
        if indata.shape[1] > 1:
            audio_data = np.mean(indata, axis=1, keepdims=True)
        else:
            audio_data = indata
        
        # Put audio data in queue
        self.audio_queue.put(audio_data.flatten())
    
    def start_capture(self) -> bool:
        """Start audio capture."""
        if not self.device:
            raise RuntimeError("No audio device configured. Call setup_device() first.")
        
        if self.is_capturing:
            print("Audio capture already started")
            return True
        
        try:
            self.stream = sd.InputStream(
                device=self.device.index,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                callback=self._audio_callback,
                blocksize=self.config.buffer_size,
                dtype=self.config.dtype
            )
            
            self.stream.start()
            self.is_capturing = True
            print(f"Started audio capture from device: {self.device.name}")
            print(f"Sample rate: {self.config.sample_rate} Hz")
            print(f"Channels: {self.config.channels}")
            return True
            
        except Exception as e:
            print(f"Failed to start audio capture: {e}")
            return False
    
    def stop_capture(self):
        """Stop audio capture."""
        if not self.is_capturing:
            return
        
        self.is_capturing = False
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        print("Audio capture stopped")
    
    def start(self):
        """Start audio capture and begin processing."""
        if not self.start_capture():
            raise RuntimeError("Failed to start audio capture")
        
        # For now, just do basic audio monitoring
        try:
            for chunk in self.get_audio_chunks():
                if chunk is not None:
                    rms = np.sqrt(np.mean(chunk ** 2))
                    if rms > 0.001:  # Only show when there's actual audio
                        print(f"Audio detected: RMS = {rms:.6f}")
        except KeyboardInterrupt:
            self.stop_capture()
            raise
    
    def stop(self):
        """Stop audio capture."""
        self.stop_capture()
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get a single audio chunk from the queue."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_audio_chunks(self) -> Generator[np.ndarray, None, None]:
        """Generator that yields audio chunks continuously."""
        chunk_size = int(self.config.sample_rate * self.config.chunk_duration)
        audio_buffer = np.array([], dtype=np.float32)
        
        while self.is_capturing:
            # Get audio data from queue
            try:
                chunk = self.audio_queue.get(timeout=0.1)
                audio_buffer = np.concatenate([audio_buffer, chunk])
                
                # Yield chunks of the desired size
                while len(audio_buffer) >= chunk_size:
                    yield audio_buffer[:chunk_size]
                    audio_buffer = audio_buffer[chunk_size:]
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in audio chunk generator: {e}")
                break
    
    def test_capture(self, duration: float = 5.0) -> bool:
        """Test audio capture for a specified duration."""
        if not self.setup_device():
            return False
        
        print(f"Testing audio capture for {duration} seconds...")
        
        if not self.start_capture():
            return False
        
        start_time = time.time()
        chunk_count = 0
        
        try:
            while time.time() - start_time < duration:
                chunk = self.get_audio_chunk(timeout=0.5)
                if chunk is not None:
                    chunk_count += 1
                    rms = np.sqrt(np.mean(chunk ** 2))
                    print(f"Chunk {chunk_count}: RMS level = {rms:.6f}")
                else:
                    print("No audio data received")
            
            print(f"Test completed. Received {chunk_count} audio chunks.")
            return chunk_count > 0
            
        finally:
            self.stop_capture()
    
    def list_devices(self):
        """List all available audio devices."""
        self.device_manager.print_devices()
        
        # Highlight recommended device
        recommended = self.device_manager.get_recommended_device()
        if recommended:
            print(f"Recommended device for system audio capture: {recommended.name}")
        else:
            print("No recommended device found. Consider installing BlackHole.")
    
    def get_device_info(self) -> dict:
        """Get information about the current device."""
        if not self.device:
            return {"error": "No device configured"}
        
        return {
            "name": self.device.name,
            "index": self.device.index,
            "max_input_channels": self.device.max_input_channels,
            "max_output_channels": self.device.max_output_channels,
            "default_samplerate": self.device.default_samplerate,
            "configured_samplerate": self.config.sample_rate,
            "channels": self.config.channels,
            "chunk_duration": self.config.chunk_duration
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_capture()