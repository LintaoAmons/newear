"""Logging configuration for newear."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

# Install rich traceback handler
install_rich_traceback(show_locals=True)

console = Console()


class NewearLogger:
    """Centralized logging for newear."""
    
    def __init__(self, name: str = "newear", level: str = "INFO", 
                 log_file: Optional[Path] = None, enable_rich: bool = True):
        """Initialize logger."""
        self.name = name
        self.level = level
        self.log_file = log_file
        self.enable_rich = enable_rich
        self.logger = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(getattr(logging, self.level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        if self.enable_rich:
            console_handler = RichHandler(
                console=console,
                show_time=True,
                show_path=True,
                rich_tracebacks=True,
                markup=True
            )
        else:
            console_handler = logging.StreamHandler(sys.stdout)
        
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if self.log_file:
            try:
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(self.log_file, mode='a')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Could not setup file logging: {e}")
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger
    
    def log_system_info(self):
        """Log system information."""
        import platform
        import psutil
        
        self.logger.info("=== System Information ===")
        self.logger.info(f"Platform: {platform.system()} {platform.release()}")
        self.logger.info(f"Python: {platform.python_version()}")
        self.logger.info(f"CPU: {platform.processor()}")
        self.logger.info(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        self.logger.info(f"Available Memory: {psutil.virtual_memory().available / (1024**3):.1f} GB")
    
    def log_audio_info(self, device_info: dict):
        """Log audio device information."""
        self.logger.info("=== Audio Configuration ===")
        self.logger.info(f"Device: {device_info.get('name', 'Unknown')}")
        self.logger.info(f"Sample Rate: {device_info.get('configured_samplerate', 'Unknown')} Hz")
        self.logger.info(f"Channels: {device_info.get('channels', 'Unknown')}")
        self.logger.info(f"Chunk Duration: {device_info.get('chunk_duration', 'Unknown')}s")
    
    def log_transcription_info(self, model_size: str, language: str = None):
        """Log transcription configuration."""
        self.logger.info("=== Transcription Configuration ===")
        self.logger.info(f"Model Size: {model_size}")
        self.logger.info(f"Language: {language or 'auto-detect'}")
    
    def log_performance_stats(self, stats: dict):
        """Log performance statistics."""
        self.logger.info("=== Performance Statistics ===")
        for key, value in stats.items():
            self.logger.info(f"{key}: {value}")


# Global logger instance
_logger_instance: Optional[NewearLogger] = None


def get_logger(name: str = "newear") -> logging.Logger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        # Default log file
        log_dir = Path.home() / ".newear" / "logs"
        log_file = log_dir / f"newear_{datetime.now().strftime('%Y%m%d')}.log"
        
        _logger_instance = NewearLogger(
            name=name,
            level="INFO",
            log_file=log_file,
            enable_rich=True
        )
    return _logger_instance.get_logger()


def setup_logging(level: str = "INFO", log_file: Optional[Path] = None, 
                 enable_rich: bool = True) -> NewearLogger:
    """Setup logging configuration."""
    global _logger_instance
    _logger_instance = NewearLogger(
        name="newear",
        level=level,
        log_file=log_file,
        enable_rich=enable_rich
    )
    return _logger_instance


def log_exception(logger: logging.Logger, exception: Exception, context: str = ""):
    """Log an exception with context."""
    if context:
        logger.error(f"Exception in {context}: {type(exception).__name__}: {exception}")
    else:
        logger.error(f"Exception: {type(exception).__name__}: {exception}")
    
    # Log traceback at debug level
    logger.debug("Exception traceback:", exc_info=exception)


def log_performance(logger: logging.Logger, operation: str, duration: float, 
                   additional_info: dict = None):
    """Log performance information."""
    info_str = f"Performance: {operation} took {duration:.3f}s"
    if additional_info:
        info_parts = [f"{k}={v}" for k, v in additional_info.items()]
        info_str += f" ({', '.join(info_parts)})"
    
    logger.info(info_str)


class ErrorHandler:
    """Centralized error handling for newear."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_count = 0
        self.warning_count = 0
    
    def handle_error(self, error: Exception, context: str = "", fatal: bool = False):
        """Handle an error with logging and user feedback."""
        self.error_count += 1
        
        # Log the error
        log_exception(self.logger, error, context)
        
        # User feedback
        if fatal:
            console.print(f"[red]Fatal Error: {error}[/red]")
            console.print("[red]Application will exit[/red]")
        else:
            console.print(f"[red]Error: {error}[/red]")
            if context:
                console.print(f"[dim]Context: {context}[/dim]")
    
    def handle_warning(self, message: str, context: str = ""):
        """Handle a warning with logging and user feedback."""
        self.warning_count += 1
        
        # Log the warning
        full_message = f"{context}: {message}" if context else message
        self.logger.warning(full_message)
        
        # User feedback
        console.print(f"[yellow]Warning: {message}[/yellow]")
        if context:
            console.print(f"[dim]Context: {context}[/dim]")
    
    def get_error_stats(self) -> dict:
        """Get error statistics."""
        return {
            "error_count": self.error_count,
            "warning_count": self.warning_count
        }
    
    def reset_stats(self):
        """Reset error statistics."""
        self.error_count = 0
        self.warning_count = 0


# Global error handler
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler(get_logger())
    return _error_handler