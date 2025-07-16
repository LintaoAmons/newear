"""Configuration file support for newear."""

import os
import yaml
import toml
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field

from rich.console import Console

console = Console()


def expand_env_vars(data: Any) -> Any:
    """Recursively expand environment variables in configuration data."""
    if isinstance(data, dict):
        return {key: expand_env_vars(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Replace ${VAR} and ${VAR:-default} patterns
        def replace_var(match):
            var_expr = match.group(1)
            if ':-' in var_expr:
                var_name, default_value = var_expr.split(':-', 1)
                return os.getenv(var_name, default_value)
            else:
                return os.getenv(var_expr, match.group(0))  # Return original if not found
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, data)
    else:
        return data


@dataclass
class AudioConfig:
    """Audio configuration settings."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration: float = 5.0
    buffer_size: int = 4096
    device_index: Optional[int] = None


@dataclass
class TranscriptionConfig:
    """Transcription configuration settings."""
    model_size: str = "base"
    language: Optional[str] = None
    device: str = "cpu"
    compute_type: str = "int8"
    confidence_threshold: float = 0.7


@dataclass
class OutputConfig:
    """Output configuration settings."""
    default_format: str = "txt"
    show_timestamps: bool = True
    show_confidence: bool = False
    auto_save: bool = True
    output_dir: Optional[str] = None
    formats: List[str] = field(default_factory=lambda: ["txt", "continuous"])


@dataclass
class DisplayConfig:
    """Display configuration settings."""
    rich_ui: bool = True
    max_lines: int = 6
    show_stats: bool = True
    update_interval: float = 0.1
    color_scheme: str = "auto"


@dataclass
class ModelConfig:
    """Custom model configuration settings."""
    models: Dict[str, str] = field(default_factory=dict)  # name -> path mapping
    model_dir: Optional[str] = None  # Default directory for models


@dataclass
class HookConfig:
    """Hook configuration settings."""
    enabled: bool = True
    hooks: List[Dict[str, Any]] = field(default_factory=list)  # List of hook definitions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'enabled': self.enabled,
            'hooks': self.hooks
        }


@dataclass
class NewearConfig:
    """Complete newear configuration."""
    audio: AudioConfig = field(default_factory=AudioConfig)
    transcription: TranscriptionConfig = field(default_factory=TranscriptionConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    hooks: HookConfig = field(default_factory=HookConfig)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NewearConfig':
        """Create from dictionary."""
        return cls(
            audio=AudioConfig(**data.get('audio', {})),
            transcription=TranscriptionConfig(**data.get('transcription', {})),
            output=OutputConfig(**data.get('output', {})),
            display=DisplayConfig(**data.get('display', {})),
            models=ModelConfig(**data.get('models', {})),
            hooks=HookConfig(**data.get('hooks', {}))
        )


class ConfigManager:
    """Manages configuration files for newear."""
    
    DEFAULT_CONFIG_PATHS = [
        Path.cwd() / "newear.yaml",
        Path.cwd() / "newear.toml",
        Path.cwd() / ".newear.yaml",
        Path.cwd() / ".newear.toml",
        Path.home() / ".newear" / "config.yaml",
        Path.home() / ".newear" / "config.toml",
        Path.home() / ".config" / "newear" / "config.yaml",
        Path.home() / ".config" / "newear" / "config.toml"
    ]
    
    def __init__(self):
        """Initialize configuration manager."""
        self.config = NewearConfig()
        self.config_file: Optional[Path] = None
        
    def find_config_file(self) -> Optional[Path]:
        """Find the first available configuration file."""
        for path in self.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path
        return None
    
    def load_config(self, config_file: Optional[Path] = None) -> NewearConfig:
        """Load configuration from file."""
        if config_file is None:
            config_file = self.find_config_file()
        elif isinstance(config_file, str):
            config_file = Path(config_file)
        
        if config_file is None:
            console.print("[dim]No configuration file found, using defaults[/dim]")
            return self.config
        
        try:
            self.config_file = config_file
            console.print(f"[blue]Loading configuration from: {config_file}[/blue]")
            
            with open(config_file, 'r') as f:
                if config_file.suffix == '.yaml' or config_file.suffix == '.yml':
                    data = yaml.safe_load(f)
                elif config_file.suffix == '.toml':
                    data = toml.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {config_file.suffix}")
            
            if data:
                # Expand environment variables
                data = expand_env_vars(data)
                self.config = NewearConfig.from_dict(data)
                console.print("[green]Configuration loaded successfully[/green]")
            
        except Exception as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
            console.print("[yellow]Using default configuration[/yellow]")
        
        return self.config
    
    def save_config(self, config_file: Optional[Path] = None, format: str = "yaml") -> bool:
        """Save configuration to file."""
        if config_file is None:
            if self.config_file:
                config_file = self.config_file
            else:
                config_file = Path.home() / ".newear" / f"config.{format}"
        
        try:
            # Ensure directory exists
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = self.config.to_dict()
            
            with open(config_file, 'w') as f:
                if format == "yaml" or config_file.suffix in ['.yaml', '.yml']:
                    yaml.dump(data, f, default_flow_style=False, indent=2)
                elif format == "toml" or config_file.suffix == '.toml':
                    toml.dump(data, f)
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            console.print(f"[green]Configuration saved to: {config_file}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error saving configuration: {e}[/red]")
            return False
    
    def create_default_config(self, config_file: Optional[Path] = None) -> bool:
        """Create a default configuration file."""
        if config_file is None:
            config_file = Path.home() / ".newear" / "config.yaml"
        
        # Reset to defaults
        self.config = NewearConfig()
        
        # Save the default config
        return self.save_config(config_file)
    
    def get_config_template(self) -> str:
        """Get a configuration template as a string."""
        template = """# Newear Configuration File
# This file contains all configuration options for newear

# Audio capture settings
audio:
  sample_rate: 16000        # Audio sample rate in Hz
  channels: 1               # Number of audio channels (1 for mono)
  chunk_duration: 5.0       # Audio chunk duration in seconds
  buffer_size: 4096         # Audio buffer size
  device_index: null        # Audio device index (null for auto-detect)

# Transcription settings
transcription:
  model_size: "base"        # Whisper model size (tiny, base, small, medium, large)
  language: null            # Language code (null for auto-detect)
  device: "cpu"             # Processing device (cpu, cuda)
  compute_type: "int8"      # Compute type (int8, float16, float32)
  confidence_threshold: 0.7 # Confidence threshold for high-confidence chunks

# Output settings
output:
  default_format: "txt"     # Default output format
  show_timestamps: true     # Include timestamps in output
  show_confidence: false    # Show confidence scores in console
  auto_save: true          # Automatically save transcripts
  output_dir: null         # Output directory (null for current directory)
  formats: ["txt", "continuous"]  # Output formats to generate

# Display settings
display:
  rich_ui: true            # Use rich terminal UI
  max_lines: 6             # Maximum lines to show in terminal
  show_stats: true         # Show statistics
  update_interval: 0.1     # Display update interval in seconds
  color_scheme: "auto"     # Color scheme (auto, light, dark)

# Custom model settings
models:
  model_dir: null          # Default directory for custom models
  models:                  # Custom model definitions
    # my-model: "/path/to/custom/model"
    # finetuned: "~/models/my-finetuned-whisper"
    # large-v3: "openai/whisper-large-v3"

# Hook settings
hooks:
  enabled: true            # Enable/disable hook system
  hooks:                   # Hook definitions
    # Example: Console log hook
    # - type: "console_log"
    #   enabled: true
    #   config:
    #     show_confidence: true
    #
    # Example: Translation hook (command-line)
    # - type: "translation"
    #   enabled: true
    #   config:
    #     target_language: "es"
    #     service: "command"
    #     command: "trans -brief en:es '{text}'"
    #     print_translation: true
    #
    # Example: OpenAI translation hook
    # - type: "openai_translation"
    #   enabled: true
    #   config:
    #     api_key: "${OPENAI_API_KEY}"  # Use environment variable
    #     base_url: null  # Optional: "https://openrouter.ai/api/v1" for OpenRouter
    #     target_language: "Chinese"
    #     model: "gpt-3.5-turbo"  # or "openai/gpt-3.5-turbo" for OpenRouter
    #     max_tokens: 1000
    #     temperature: 0.3
    #     print_translation: true
    #     output_prefix: ""  # Optional prefix for translations (e.g., "🤖", "AI:", etc.)
    #
    # Example: File append hook
    # - type: "file_append"
    #   enabled: true
    #   config:
    #     file_path: "hooks.log"
    #     format: "[{timestamp}] {text}"
    #
    # Example: Command hook
    # - type: "command"
    #   enabled: true
    #   config:
    #     command: "echo 'Transcribed: {text}' | notify-send"
    #     timeout: 10
    #
    # Example: Webhook hook
    # - type: "webhook"
    #   enabled: true
    #   config:
    #     url: "https://api.example.com/webhook"
    #     timeout: 10
    #     headers:
    #       Authorization: "Bearer YOUR_TOKEN"
"""
        return template
    
    def print_config(self):
        """Print current configuration."""
        from rich.tree import Tree
        from rich.syntax import Syntax
        
        tree = Tree("📋 Current Configuration")
        
        # Audio section
        audio_tree = tree.add("🎵 Audio")
        audio_tree.add(f"Sample Rate: {self.config.audio.sample_rate} Hz")
        audio_tree.add(f"Channels: {self.config.audio.channels}")
        audio_tree.add(f"Chunk Duration: {self.config.audio.chunk_duration}s")
        audio_tree.add(f"Buffer Size: {self.config.audio.buffer_size}")
        audio_tree.add(f"Device Index: {self.config.audio.device_index or 'auto-detect'}")
        
        # Transcription section
        trans_tree = tree.add("🧠 Transcription")
        trans_tree.add(f"Model Size: {self.config.transcription.model_size}")
        trans_tree.add(f"Language: {self.config.transcription.language or 'auto-detect'}")
        trans_tree.add(f"Device: {self.config.transcription.device}")
        trans_tree.add(f"Compute Type: {self.config.transcription.compute_type}")
        trans_tree.add(f"Confidence Threshold: {self.config.transcription.confidence_threshold}")
        
        # Output section
        output_tree = tree.add("📄 Output")
        output_tree.add(f"Default Format: {self.config.output.default_format}")
        output_tree.add(f"Show Timestamps: {self.config.output.show_timestamps}")
        output_tree.add(f"Show Confidence: {self.config.output.show_confidence}")
        output_tree.add(f"Auto Save: {self.config.output.auto_save}")
        output_tree.add(f"Output Dir: {self.config.output.output_dir or 'current directory'}")
        output_tree.add(f"Formats: {', '.join(self.config.output.formats)}")
        
        # Display section
        display_tree = tree.add("🖥️ Display")
        display_tree.add(f"Rich UI: {self.config.display.rich_ui}")
        display_tree.add(f"Max Lines: {self.config.display.max_lines}")
        display_tree.add(f"Show Stats: {self.config.display.show_stats}")
        display_tree.add(f"Update Interval: {self.config.display.update_interval}s")
        display_tree.add(f"Color Scheme: {self.config.display.color_scheme}")
        
        # Models section
        models_tree = tree.add("🤖 Models")
        models_tree.add(f"Model Directory: {self.config.models.model_dir or 'default'}")
        if self.config.models.models:
            custom_models_tree = models_tree.add("Custom Models")
            for name, path in self.config.models.models.items():
                custom_models_tree.add(f"{name}: {path}")
        else:
            models_tree.add("No custom models configured")
        
        # Hooks section
        hooks_tree = tree.add("🪝 Hooks")
        hooks_tree.add(f"Enabled: {self.config.hooks.enabled}")
        if self.config.hooks.hooks:
            hooks_list_tree = hooks_tree.add("Configured Hooks")
            for i, hook in enumerate(self.config.hooks.hooks):
                hook_type = hook.get('type', 'unknown')
                hook_enabled = hook.get('enabled', True)
                status = "✓" if hook_enabled else "✗"
                hooks_list_tree.add(f"{status} {hook_type}")
        else:
            hooks_tree.add("No hooks configured")
        
        console.print(tree)
    
    def merge_with_cli_args(self, **kwargs):
        """Merge configuration with CLI arguments."""
        # Audio settings
        if 'device' in kwargs and kwargs['device'] is not None:
            self.config.audio.device_index = kwargs['device']
        if 'sample_rate' in kwargs and kwargs['sample_rate'] is not None:
            self.config.audio.sample_rate = kwargs['sample_rate']
        if 'chunk_duration' in kwargs and kwargs['chunk_duration'] is not None:
            self.config.audio.chunk_duration = kwargs['chunk_duration']
        
        # Transcription settings
        if 'model' in kwargs and kwargs['model'] is not None:
            self.config.transcription.model_size = kwargs['model']
        if 'language' in kwargs and kwargs['language'] is not None:
            self.config.transcription.language = kwargs['language']
        
        # Output settings
        if 'timestamps' in kwargs and kwargs['timestamps'] is not None:
            self.config.output.show_timestamps = kwargs['timestamps']
        if 'show_confidence' in kwargs and kwargs['show_confidence'] is not None:
            self.config.output.show_confidence = kwargs['show_confidence']
