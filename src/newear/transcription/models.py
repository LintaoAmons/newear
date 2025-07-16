"""Model management for Whisper transcription."""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.progress import Progress, DownloadColumn, BarColumn, TextColumn, TimeRemainingColumn

console = Console()


@dataclass
class ModelInfo:
    """Information about a Whisper model."""
    name: str
    size_mb: int
    description: str
    recommended_use: str


class ModelManager:
    """Manages Whisper model downloads and storage."""
    
    # Available models with their approximate sizes
    MODELS: Dict[str, ModelInfo] = {
        "tiny": ModelInfo(
            name="tiny",
            size_mb=39,
            description="Fastest, lowest accuracy",
            recommended_use="Testing, very fast transcription"
        ),
        "base": ModelInfo(
            name="base", 
            size_mb=74,
            description="Balanced speed and accuracy",
            recommended_use="General use, good balance"
        ),
        "small": ModelInfo(
            name="small",
            size_mb=244,
            description="Good accuracy, moderate speed",
            recommended_use="Higher accuracy needs"
        ),
        "medium": ModelInfo(
            name="medium",
            size_mb=769,
            description="High accuracy, slower",
            recommended_use="Best accuracy on English"
        ),
        "large": ModelInfo(
            name="large",
            size_mb=1550,
            description="Highest accuracy, slowest",
            recommended_use="Maximum accuracy, multilingual"
        ),
        "large-v2": ModelInfo(
            name="large-v2",
            size_mb=1550,
            description="Latest large model",
            recommended_use="Maximum accuracy, latest improvements"
        )
    }
    
    def __init__(self, models_dir: Optional[Path] = None):
        """Initialize model manager."""
        if models_dir is None:
            # Default to models/ directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            models_dir = project_root / "models"
        
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        # Create .gitkeep file to ensure directory is tracked
        gitkeep_file = self.models_dir / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.touch()
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available locally."""
        if model_name not in self.MODELS:
            return False
            
        # For faster-whisper, models are downloaded automatically
        # We just need to check if the model name is valid
        return True
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a model."""
        return self.MODELS.get(model_name)
    
    def list_available_models(self) -> List[str]:
        """List all available model names."""
        return list(self.MODELS.keys())
    
    def list_downloaded_models(self) -> List[str]:
        """List models that have been downloaded."""
        # For faster-whisper, models are managed by the library
        # We'll return all valid models since they're downloaded on first use
        return list(self.MODELS.keys())
    
    def get_recommended_model(self) -> str:
        """Get the recommended model for general use."""
        return "base"
    
    def validate_model_name(self, model_name: str) -> bool:
        """Validate that a model name is supported."""
        return model_name in self.MODELS
    
    def print_model_info(self):
        """Print information about all available models."""
        console.print("\n[bold]Available Whisper Models:[/bold]")
        console.print("-" * 80)
        
        for model_name, info in self.MODELS.items():
            console.print(f"[bold cyan]{model_name:<12}[/bold cyan] {info.size_mb:>4}MB  {info.description}")
            console.print(f"[dim]             Use case: {info.recommended_use}[/dim]")
            console.print()
        
        console.print("[yellow]Note: Models are downloaded automatically on first use[/yellow]")
        console.print(f"[blue]Recommended for general use: {self.get_recommended_model()}[/blue]")
    
    def estimate_memory_usage(self, model_name: str) -> Dict[str, int]:
        """Estimate memory usage for a model."""
        if model_name not in self.MODELS:
            return {"disk_mb": 0, "ram_mb": 0}
        
        model_info = self.MODELS[model_name]
        
        # Rough estimates based on model size
        # RAM usage is typically 1.5-2x model size during inference
        disk_mb = model_info.size_mb
        ram_mb = int(model_info.size_mb * 1.8)  # Conservative estimate
        
        return {
            "disk_mb": disk_mb,
            "ram_mb": ram_mb
        }
    
    def get_model_path(self, model_name: str) -> str:
        """Get the path/identifier for a model (for faster-whisper)."""
        if not self.validate_model_name(model_name):
            raise ValueError(f"Invalid model name: {model_name}")
        
        # For faster-whisper, we just return the model name
        # The library handles the actual model management
        return model_name
    
    def cleanup_models(self):
        """Clean up downloaded models (if needed)."""
        # For faster-whisper, models are managed by the library
        # This is a placeholder for potential future cleanup needs
        console.print("[yellow]Model cleanup not needed for faster-whisper[/yellow]")
    
    def get_storage_info(self) -> Dict[str, any]:
        """Get information about model storage."""
        return {
            "models_directory": str(self.models_dir),
            "available_models": self.list_available_models(),
            "downloaded_models": self.list_downloaded_models(),
            "recommended_model": self.get_recommended_model()
        }
