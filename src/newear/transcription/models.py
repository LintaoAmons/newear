"""Model management for Whisper transcription."""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union
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
    path: Optional[str] = None  # For custom models
    is_custom: bool = False


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
    
    def __init__(self, models_dir: Optional[Path] = None, custom_models: Optional[Dict[str, str]] = None):
        """Initialize model manager.
        
        Args:
            models_dir: Directory for model storage
            custom_models: Dict mapping custom model names to paths
        """
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
        
        # Initialize custom models registry
        self.custom_models = custom_models or {}
        self._register_custom_models()
    
    def _register_custom_models(self):
        """Register custom models in the main models registry."""
        for name, path in self.custom_models.items():
            if name not in self.MODELS:  # Don't override built-in models
                self.MODELS[name] = ModelInfo(
                    name=name,
                    size_mb=0,  # Unknown size for custom models
                    description="Custom model",
                    recommended_use="User-defined model",
                    path=path,
                    is_custom=True
                )
    
    def add_custom_model(self, name: str, path: str, description: str = "Custom model"):
        """Add a custom model to the registry.
        
        Args:
            name: Name to use for the model
            path: Path to the model (file or directory)
            description: Optional description
        """
        resolved_path = self._resolve_model_path(path)
        if not self._validate_model_path(resolved_path):
            raise ValueError(f"Invalid model path: {path}")
        
        self.custom_models[name] = path
        self.MODELS[name] = ModelInfo(
            name=name,
            size_mb=0,  # Could be enhanced to detect size
            description=description,
            recommended_use="User-defined model",
            path=path,
            is_custom=True
        )
    
    def _resolve_model_path(self, model_input: str) -> str:
        """Resolve model input to actual path or model name.
        
        Args:
            model_input: Model name, file path, or directory path
            
        Returns:
            Resolved path or model name for faster-whisper
        """
        # Check if it's a built-in model
        if model_input in self.MODELS and not self.MODELS[model_input].is_custom:
            return model_input
        
        # Check if it's a custom model name
        if model_input in self.custom_models:
            return self._resolve_model_path(self.custom_models[model_input])
        
        # Check if it's a file path
        if os.path.sep in model_input or model_input.startswith('~'):
            # Expand user home directory
            path = Path(model_input).expanduser().resolve()
            return str(path)
        
        # Check if it's a relative path without separator
        if Path(model_input).exists():
            return str(Path(model_input).resolve())
        
        # If not found, assume it's a model name (let faster-whisper handle it)
        return model_input
    
    def _validate_model_path(self, path: str) -> bool:
        """Validate that a model path exists and is accessible.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid, False otherwise
        """
        # If it's a built-in model name, it's valid
        if path in self.MODELS and not self.MODELS[path].is_custom:
            return True
        
        # Check if path exists
        path_obj = Path(path)
        if not path_obj.exists():
            return False
        
        # Check if it's a file or directory
        if path_obj.is_file():
            # Could add more sophisticated model file validation here
            return True
        elif path_obj.is_dir():
            # Check if directory contains model files
            # This is a basic check - could be enhanced
            return any(path_obj.glob('*.bin')) or any(path_obj.glob('*.pt')) or any(path_obj.glob('*.onnx'))
        
        return False
    
    def get_model_validation_error(self, model_input: str) -> Optional[str]:
        """Get detailed validation error message for a model.
        
        Args:
            model_input: Model name or path to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        try:
            resolved_path = self._resolve_model_path(model_input)
            
            # If it's a built-in model, it's valid
            if resolved_path in self.MODELS and not self.MODELS[resolved_path].is_custom:
                return None
            
            # Check if path exists
            path_obj = Path(resolved_path)
            if not path_obj.exists():
                if model_input in self.custom_models:
                    return f"Custom model '{model_input}' points to non-existent path: {resolved_path}"
                elif os.path.sep in model_input or model_input.startswith('~'):
                    return f"Model file/directory does not exist: {resolved_path}"
                else:
                    available_models = list(self.MODELS.keys())
                    return f"Unknown model '{model_input}'. Available models: {', '.join(available_models)}"
            
            # Check if it's a valid model file/directory
            if path_obj.is_file():
                # Basic file validation
                if not path_obj.suffix.lower() in ['.bin', '.pt', '.onnx']:
                    return f"Unsupported model file format: {path_obj.suffix}. Expected .bin, .pt, or .onnx"
                return None
            elif path_obj.is_dir():
                # Check if directory contains model files
                has_model_files = any(path_obj.glob('*.bin')) or any(path_obj.glob('*.pt')) or any(path_obj.glob('*.onnx'))
                if not has_model_files:
                    return f"Directory '{resolved_path}' does not contain model files (.bin, .pt, .onnx)"
                return None
            else:
                return f"Path '{resolved_path}' is neither a file nor a directory"
                
        except Exception as e:
            return f"Error validating model '{model_input}': {str(e)}"
    
    def is_custom_model(self, model_name: str) -> bool:
        """Check if a model is a custom model."""
        return model_name in self.MODELS and self.MODELS[model_name].is_custom
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available locally."""
        # Try to resolve the model path
        try:
            resolved_path = self._resolve_model_path(model_name)
            return self._validate_model_path(resolved_path)
        except Exception:
            return False
    
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
        try:
            resolved_path = self._resolve_model_path(model_name)
            return self._validate_model_path(resolved_path)
        except Exception:
            return False
    
    def print_model_info(self):
        """Print information about all available models."""
        console.print("\n[bold]Available Whisper Models:[/bold]")
        console.print("-" * 80)
        
        # Separate built-in and custom models
        built_in_models = {k: v for k, v in self.MODELS.items() if not v.is_custom}
        custom_models = {k: v for k, v in self.MODELS.items() if v.is_custom}
        
        # Print built-in models
        console.print("[bold]Built-in Models:[/bold]")
        for model_name, info in built_in_models.items():
            console.print(f"[bold cyan]{model_name:<12}[/bold cyan] {info.size_mb:>4}MB  {info.description}")
            console.print(f"[dim]             Use case: {info.recommended_use}[/dim]")
            console.print()
        
        # Print custom models if any
        if custom_models:
            console.print("[bold]Custom Models:[/bold]")
            for model_name, info in custom_models.items():
                console.print(f"[bold green]{model_name:<12}[/bold green] Custom  {info.description}")
                console.print(f"[dim]             Path: {info.path}[/dim]")
                console.print(f"[dim]             Use case: {info.recommended_use}[/dim]")
                console.print()
        
        console.print("[yellow]Note: Built-in models are downloaded automatically on first use[/yellow]")
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
            raise ValueError(f"Invalid model name or path: {model_name}")
        
        # Resolve the model path
        return self._resolve_model_path(model_name)
    
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
            "recommended_model": self.get_recommended_model(),
            "custom_models": self.custom_models
        }
