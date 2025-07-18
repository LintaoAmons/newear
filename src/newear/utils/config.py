"""Configuration management for newear."""

from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path


@dataclass
class Config:
    """Application configuration."""
    
    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration: float = 5.0
    buffer_size: int = 4096
    
    # Transcription settings
    model_size: str = "base"  # tiny, base, small, medium, large
    language: Optional[str] = None  # Auto-detect if None
    
    # Output settings
    output_file: Optional[Path] = None
    show_timestamps: bool = True
    save_audio: bool = False
    
    # Device settings
    device_index: Optional[int] = None
    
    def __init__(self, device_index=None, model_size="base", output_file=None, 
                 show_timestamps=False, language=None, sample_rate=16000, 
                 chunk_duration=5.0, channels=1, buffer_size=4096, save_audio=False):
        self.device_index = device_index
        self.model_size = model_size
        self.output_file = output_file
        self.show_timestamps = show_timestamps
        self.language = language
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.channels = channels
        self.buffer_size = buffer_size
        self.save_audio = save_audio
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls(
            sample_rate=int(os.getenv("NEWEAR_SAMPLE_RATE", "16000")),
            channels=int(os.getenv("NEWEAR_CHANNELS", "1")),
            chunk_duration=float(os.getenv("NEWEAR_CHUNK_DURATION", "5.0")),
            buffer_size=int(os.getenv("NEWEAR_BUFFER_SIZE", "4096")),
            model_size=os.getenv("NEWEAR_MODEL_SIZE", "base"),
            language=os.getenv("NEWEAR_LANGUAGE"),
            output_file=os.getenv("NEWEAR_OUTPUT_FILE"),
            show_timestamps=os.getenv("NEWEAR_SHOW_TIMESTAMPS", "true").lower() == "true",
            save_audio=os.getenv("NEWEAR_SAVE_AUDIO", "false").lower() == "true",
            device_index=int(os.getenv("NEWEAR_DEVICE_INDEX")) if os.getenv("NEWEAR_DEVICE_INDEX") else None,
        )
    
    def get_model_path(self) -> Path:
        """Get the path where models are stored."""
        return Path.home() / ".newear" / "models"
    
    def get_output_path(self) -> Path:
        """Get the default output directory."""
        return Path.home() / ".newear" / "output"
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        self.get_model_path().mkdir(parents=True, exist_ok=True)
        self.get_output_path().mkdir(parents=True, exist_ok=True)
