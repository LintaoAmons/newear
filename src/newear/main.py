#!/usr/bin/env python3
"""
Newear CLI: Real-time system audio captioning tool
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from newear.audio.capture import AudioCapture
from newear.audio.devices import AudioDevices
from newear.output.file_writer import FileWriter
from newear.output.display import RichTerminalDisplay, DisplayConfig
from newear.utils.config import Config
from newear.utils.config_file import ConfigManager
from newear.utils.logging import get_logger, setup_logging, get_error_handler
from newear.transcription.whisper_local import WhisperTranscriber
from newear.transcription.file_transcriber import FileTranscriber
from newear.transcription.remote_whisper import RemoteWhisperTranscriber, RemoteServerConfig
from newear.hooks.manager import HookManager
from newear.hooks.factory import HookFactory

app = typer.Typer(
    name="newear",
    help="Real-time system audio captioning CLI tool",
    add_completion=False,
)

# Add subcommands
config_app = typer.Typer(help="Configuration management commands")
app.add_typer(config_app, name="config")

console = Console()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    device: Optional[int] = typer.Option(None, "--device", "-d", help="Audio device index (use --list-devices to see available)"),
    backend: Optional[str] = typer.Option(None, "--backend", "-b", help="Transcription backend (whisper, remote)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Whisper model size/name or path (tiny, base, small, medium, large, custom name, or file path)"),
    remote_host: Optional[str] = typer.Option(None, "--remote-host", help="Remote server host (for remote backend)"),
    remote_port: Optional[int] = typer.Option(None, "--remote-port", help="Remote server port (for remote backend)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path for transcript (default: newear-YYYYMMDD_HHMMSS.txt)"),
    timestamps: Optional[bool] = typer.Option(None, "--timestamps", "-t", help="Include timestamps in output"),
    show_confidence: Optional[bool] = typer.Option(None, "--confidence", help="Show confidence scores in console output"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language code (auto-detect if not specified)"),
    sample_rate: Optional[int] = typer.Option(None, "--sample-rate", "-s", help="Audio sample rate in Hz"),
    chunk_duration: Optional[float] = typer.Option(None, "--chunk-duration", "-c", help="Audio chunk duration in seconds (3-10s recommended for better accuracy)"),
    list_devices: bool = typer.Option(False, "--list-devices", help="List available audio devices and exit"),
    list_models: bool = typer.Option(False, "--list-models", help="List available models and exit"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Path to configuration file"),
    rich_ui: Optional[bool] = typer.Option(None, "--rich-ui/--no-rich-ui", help="Enable/disable rich terminal UI"),
    formats: Optional[str] = typer.Option(None, "--formats", help="Output formats (comma-separated: txt,json,srt,vtt,csv)"),
    log_level: str = typer.Option("WARNING", "--log-level", help="Log level (DEBUG, INFO, WARNING, ERROR)"),
):
    """Start real-time audio captioning."""
    
    # If subcommand is being called, don't run main logic
    if ctx.invoked_subcommand is not None:
        return
    
    # Load configuration first
    config_manager = ConfigManager()
    try:
        config_manager.load_config(config_file)
        
        # Merge with CLI arguments
        config_manager.merge_with_cli_args(
            device=device, backend=backend, model=model, timestamps=timestamps,
            show_confidence=show_confidence, language=language,
            sample_rate=sample_rate, chunk_duration=chunk_duration,
            remote_host=remote_host, remote_port=remote_port
        )
        
        # Override rich_ui setting only if explicitly provided
        # If --rich-ui or --no-rich-ui is used, override config file
        # Otherwise, use the config file setting
        if rich_ui is not None:
            config_manager.config.display.rich_ui = rich_ui
        
        # Setup logging with the final rich_ui setting
        setup_logging(level=log_level, enable_rich=config_manager.config.display.rich_ui)
        logger = get_logger()
        error_handler = get_error_handler()
        
        logger.info("Configuration loaded and merged with CLI arguments")
        
    except Exception as e:
        # Setup logging with defaults if config loading fails
        setup_logging(level=log_level, enable_rich=rich_ui if rich_ui is not None else True)
        logger = get_logger()
        error_handler = get_error_handler()
        error_handler.handle_error(e, "loading configuration")
        # Continue with defaults
    
    # List devices if requested
    if list_devices:
        devices = AudioDevices()
        devices.list_devices()
        return
    
    # List models if requested
    if list_models:
        from newear.transcription.models import ModelManager
        model_manager = ModelManager(custom_models=config_manager.config.models.models)
        model_manager.print_model_info()
        return
    
    # Set default output file if not specified
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"newear-{timestamp}.txt")
        if not config_manager.config.display.rich_ui:
            console.print(f"[blue]No output file specified, using: {output}[/blue]")
        logger.info(f"Using default output file: {output}")
    
    # Parse output formats
    output_formats = ["txt", "continuous"]
    if formats:
        output_formats = [f.strip() for f in formats.split(",")]
        logger.info(f"Output formats: {output_formats}")
    
    # Initialize configuration (keeping for backward compatibility)
    config = Config(
        device_index=config_manager.config.audio.device_index,
        model_size=config_manager.config.transcription.model_size,
        output_file=output,
        show_timestamps=config_manager.config.output.show_timestamps,
        language=config_manager.config.transcription.language,
        sample_rate=config_manager.config.audio.sample_rate,
        chunk_duration=config_manager.config.audio.chunk_duration,
    )
    
    # Initialize audio capture
    try:
        audio_capture = AudioCapture(config)
        logger.info("Audio capture initialized successfully")
    except Exception as e:
        error_handler.handle_error(e, "initializing audio capture", fatal=True)
        sys.exit(1)
    
    # Initialize file writer
    file_writer = FileWriter(output, config_manager.config.output.show_timestamps)
    
    # Initialize continuous file writer for one-liner output
    continuous_file = output.with_suffix('.continuous.txt')
    continuous_writer = FileWriter(continuous_file, show_timestamps=False)
    
    # Initialize rich terminal display
    display = None
    if config_manager.config.display.rich_ui:
        display_config = DisplayConfig(
            max_lines=config_manager.config.display.max_lines,
            show_timestamps=config_manager.config.output.show_timestamps,
            show_confidence=config_manager.config.output.show_confidence,
            show_stats=config_manager.config.display.show_stats,
            update_interval=config_manager.config.display.update_interval
        )
        display = RichTerminalDisplay(display_config)
    
    # Initialize hook manager
    hook_manager = HookManager()
    if config_manager.config.hooks.enabled:
        hooks = HookFactory.create_hooks_from_config(config_manager.config.hooks.to_dict())
        for hook in hooks:
            hook_manager.register_hook(hook)
        if hooks:
            logger.info(f"Initialized {len(hooks)} hooks")
    else:
        logger.info("Hooks disabled in configuration")
    
    # Initialize transcriber based on backend
    try:
        backend = config_manager.config.transcription.backend
        
        if backend == "remote":
            # Create remote server config
            remote_config = RemoteServerConfig(
                host=config_manager.config.transcription.remote_host,
                port=config_manager.config.transcription.remote_port,
                protocol=config_manager.config.transcription.remote_protocol,
                timeout=config_manager.config.transcription.remote_timeout,
                model_size=config_manager.config.transcription.model_size
            )
            
            transcriber = RemoteWhisperTranscriber(
                remote_config=remote_config,
                language=config_manager.config.transcription.language
            )
            
            if not config_manager.config.display.rich_ui:
                console.print(f"[blue]Connecting to remote Whisper server: {remote_config.host}:{remote_config.port}[/blue]")
            logger.info(f"Using remote Whisper server: {remote_config.host}:{remote_config.port}")
        
        else:  # Default to local whisper
            transcriber = WhisperTranscriber(
                model_size=config_manager.config.transcription.model_size,
                language=config_manager.config.transcription.language,
                device=config_manager.config.transcription.device,
                compute_type=config_manager.config.transcription.compute_type,
                custom_models=config_manager.config.models.models
            )
            if not config_manager.config.display.rich_ui:
                console.print(f"[blue]Initializing Whisper model: {config_manager.config.transcription.model_size}[/blue]")
            logger.info(f"Initializing Whisper model: {config_manager.config.transcription.model_size}")
            
    except Exception as e:
        error_handler.handle_error(e, "initializing transcriber", fatal=True)
        sys.exit(1)
    
    # Start captioning
    if not config_manager.config.display.rich_ui:
        console.print("[green]Starting Newear audio captioning...[/green]")
        if backend == "remote":
            console.print(f"[blue]Backend: Remote ({config_manager.config.transcription.remote_host}:{config_manager.config.transcription.remote_port})[/blue]")
        else:
            console.print(f"[blue]Model: {config_manager.config.transcription.model_size}[/blue]")
        console.print(f"[blue]Device: {config_manager.config.audio.device_index or 'auto-detect'}[/blue]")
        console.print(f"[blue]Sample rate: {config_manager.config.audio.sample_rate}Hz[/blue]")
        console.print(f"[blue]Chunk duration: {config_manager.config.audio.chunk_duration}s[/blue]")
        console.print(f"[blue]Language: {config_manager.config.transcription.language or 'auto-detect'}[/blue]")
        console.print(f"[blue]Output file: {output}[/blue]")
        console.print(f"[blue]Continuous file: {output.with_suffix('.continuous.txt')}[/blue]")
        console.print(f"[blue]Output formats: {', '.join(output_formats)}[/blue]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        console.print("-" * 50)
    
    # Setup rich display if enabled
    if display:
        display.set_model_info(config_manager.config.transcription.model_size, 
                              config_manager.config.transcription.language)
        display.set_device_info(
            audio_capture.device.name if audio_capture.device else "unknown",
            config_manager.config.audio.sample_rate,
            config_manager.config.audio.chunk_duration
        )
        display.set_status("Initializing...")
        display.start()
    
    # Log system and configuration info
    logger.info("=== Newear Session Started ===")
    logger.info(f"Model: {config_manager.config.transcription.model_size}")
    logger.info(f"Language: {config_manager.config.transcription.language or 'auto-detect'}")
    logger.info(f"Output file: {output}")
    logger.info(f"Output formats: {output_formats}")
    
    try:
        # Open files for writing (always enabled now)
        file_writer.open_file()
        continuous_writer.open_file()
            
        # Start audio capture
        if not audio_capture.start_capture():
            console.print("[red]Failed to start audio capture[/red]")
            sys.exit(1)
            
        # Start real-time transcription
        if not config_manager.config.display.rich_ui:
            console.print("[green]Audio capture started. Beginning transcription...[/green]")
        
        if display:
            display.set_status("Transcribing...")
            display.set_transcribing(True)
            display.set_model_loading(False)
        
        logger.info("Starting real-time transcription")
        
        # Use the transcriber's streaming method for real-time processing
        for result in transcriber.transcribe_chunk_stream(
            audio_capture.get_audio_chunks(),
            sample_rate=config_manager.config.audio.sample_rate
        ):
            if result and result.text.strip():
                text = result.text.strip()
                
                # Add to rich display
                if display:
                    display.add_transcription(result)
                    display.update()
                
                # Write to timestamped file (always enabled now)
                try:
                    file_writer.write_entry(text, confidence=result.confidence)
                    continuous_writer.write_continuous(text)
                except Exception as e:
                    error_handler.handle_error(e, "writing to file")
                
                # Execute hooks after processing
                if config_manager.config.hooks.enabled:
                    try:
                        hook_context = hook_manager.create_context(result)
                        hook_results = hook_manager.execute_hooks(hook_context)
                        # Log any hook failures
                        for hook_result in hook_results:
                            if not hook_result.success:
                                logger.warning(f"Hook failed: {hook_result.error}")
                    except Exception as e:
                        error_handler.handle_error(e, "executing hooks")
                
                # Log transcription
                logger.debug(f"Transcribed: {text} (confidence: {result.confidence:.2f})")
        
    except KeyboardInterrupt:
        logger.info("Transcription stopped by user")
        if not config_manager.config.display.rich_ui:
            console.print("\n[yellow]Stopping Newear...[/yellow]")
        
        # Stop rich display
        if display:
            display.set_transcribing(False)
            display.set_status("Stopping...")
            display.stop()
        
        # Cleanup
        audio_capture.stop()
        transcriber.cleanup()
        file_writer.close_file()
        continuous_writer.close_file()
        
        # Write additional formats
        if "json" in output_formats or "srt" in output_formats or "vtt" in output_formats or "csv" in output_formats:
            try:
                file_writer.write_all_formats(output, output_formats)
                logger.info(f"Additional formats written: {output_formats}")
            except Exception as e:
                error_handler.handle_error(e, "writing additional formats")
        
        # Show statistics
        stats = file_writer.get_stats()
        if not config_manager.config.display.rich_ui:
            console.print(f"[green]Written {stats['total_entries']} entries to {output}[/green]")
            console.print(f"[green]Continuous transcript saved to {output.with_suffix('.continuous.txt')}[/green]")
        
        # Show performance stats
        perf_stats = transcriber.get_performance_stats()
        if perf_stats['total_transcriptions'] > 0:
            if not config_manager.config.display.rich_ui:
                console.print(f"[blue]Transcribed {perf_stats['total_transcriptions']} chunks[/blue]")
                console.print(f"[blue]Average transcription time: {perf_stats['avg_transcription_time']:.2f}s[/blue]")
            logger.info(f"Transcription performance: {perf_stats}")
        
        # Show rich display summary
        if display:
            display.print_summary()
        
        # Log final stats
        logger.info("=== Session Complete ===")
        logger.info(f"Total entries: {stats['total_entries']}")
        logger.info(f"Total transcriptions: {perf_stats.get('total_transcriptions', 0)}")
        
        if not config_manager.config.display.rich_ui:
            console.print("[green]Goodbye![/green]")
        
    except Exception as e:
        error_handler.handle_error(e, "during transcription", fatal=True)
        
        # Cleanup
        audio_capture.stop()
        transcriber.cleanup()
        file_writer.close_file()
        continuous_writer.close_file()
        
        if display:
            display.stop()
        
        sys.exit(1)


@config_app.command("show")
def show_config():
    """Show current configuration."""
    config_manager = ConfigManager()
    config_manager.load_config()
    config_manager.print_config()


@config_app.command("create")
def create_config(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("yaml", "--format", "-f", help="Configuration format (yaml, toml)")
):
    """Create a default configuration file."""
    config_manager = ConfigManager()
    if config_manager.create_default_config(output):
        console.print("[green]Default configuration created successfully[/green]")
    else:
        console.print("[red]Failed to create configuration[/red]")


@config_app.command("template")
def show_template():
    """Show configuration template."""
    config_manager = ConfigManager()
    template = config_manager.get_config_template()
    console.print(template)


@app.command("transcribe")
def transcribe_file(
    file_path: Path = typer.Argument(..., help="Path to video or audio file to transcribe"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path (default: input_filename.txt)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Whisper model size/name or path (tiny, base, small, medium, large, custom name, or file path)"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language code (auto-detect if not specified)"),
    formats: Optional[str] = typer.Option(None, "--formats", help="Output formats (comma-separated: txt,json,srt,vtt,csv)"),
    config_file: Optional[Path] = typer.Option(None, "--config", help="Path to configuration file"),
    log_level: str = typer.Option("INFO", "--log-level", help="Log level (DEBUG, INFO, WARNING, ERROR)"),
):
    """Transcribe a video or audio file to text."""
    
    # Load configuration
    config_manager = ConfigManager()
    try:
        config_manager.load_config(config_file)
        
        # Override with CLI arguments if provided
        if model is not None:
            config_manager.config.transcription.model_size = model
        if language is not None:
            config_manager.config.transcription.language = language
        
        # Setup logging
        setup_logging(level=log_level, enable_rich=True)
        logger = get_logger()
        error_handler = get_error_handler()
        
        logger.info("File transcription started")
        
    except Exception as e:
        setup_logging(level=log_level, enable_rich=True)
        logger = get_logger()
        error_handler = get_error_handler()
        error_handler.handle_error(e, "loading configuration")
    
    # Validate file path
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file_path}[/red]")
        raise typer.Exit(1)
    
    # Set default output file if not specified
    if output is None:
        output = file_path.with_suffix('.txt')
        console.print(f"[blue]Output file: {output}[/blue]")
    
    # Parse output formats
    output_formats = ["txt", "continuous"]
    if formats:
        output_formats = [f.strip() for f in formats.split(",")]
        logger.info(f"Output formats: {output_formats}")
    
    # Initialize file transcriber
    file_transcriber = FileTranscriber(
        model_size=config_manager.config.transcription.model_size,
        language=config_manager.config.transcription.language,
        device=config_manager.config.transcription.device,
        compute_type=config_manager.config.transcription.compute_type,
        custom_models=config_manager.config.models.models
    )
    
    # Show supported formats if unsupported file
    try:
        supported_formats = file_transcriber.get_supported_formats()
    except Exception:
        supported_formats = []
    
    # Initialize file writers
    file_writer = FileWriter(output, show_timestamps=True)
    continuous_writer = FileWriter(output.with_suffix('.continuous.txt'), show_timestamps=False)
    
    # Initialize hook manager for file transcription
    hook_manager = HookManager()
    if config_manager.config.hooks.enabled:
        hooks = HookFactory.create_hooks_from_config(config_manager.config.hooks.to_dict())
        for hook in hooks:
            hook_manager.register_hook(hook)
        if hooks:
            logger.info(f"Initialized {len(hooks)} hooks for file transcription")
    
    try:
        # Open files for writing
        file_writer.open_file()
        continuous_writer.open_file()
        
        console.print(f"[green]Starting transcription of: {file_path.name}[/green]")
        console.print(f"[blue]Using model: {config_manager.config.transcription.model_size}[/blue]")
        console.print(f"[blue]Language: {config_manager.config.transcription.language or 'auto-detect'}[/blue]")
        console.print(f"[blue]Output formats: {', '.join(output_formats)}[/blue]")
        
        # Process the file
        total_entries = 0
        for result in file_transcriber.transcribe_file(file_path):
            if result and result.text.strip():
                text = result.text.strip()
                
                # Write to files
                file_writer.write_entry(text, confidence=result.confidence, 
                                      start_time=result.start_time, end_time=result.end_time)
                continuous_writer.write_continuous(text)
                
                # Execute hooks after processing
                if config_manager.config.hooks.enabled:
                    try:
                        hook_context = hook_manager.create_context(result)
                        hook_results = hook_manager.execute_hooks(hook_context)
                        # Log any hook failures
                        for hook_result in hook_results:
                            if not hook_result.success:
                                logger.warning(f"Hook failed: {hook_result.error}")
                    except Exception as e:
                        error_handler.handle_error(e, "executing hooks")
                
                total_entries += 1
                
                # Log progress
                logger.debug(f"Transcribed segment: {text[:50]}... (confidence: {result.confidence:.2f})")
        
        console.print(f"[green]Transcription completed! {total_entries} segments processed.[/green]")
        
        # Write additional formats
        if "json" in output_formats or "srt" in output_formats or "vtt" in output_formats or "csv" in output_formats:
            try:
                file_writer.write_all_formats(output, output_formats)
                console.print(f"[green]Additional formats written: {output_formats}[/green]")
            except Exception as e:
                error_handler.handle_error(e, "writing additional formats")
        
        # Show statistics
        stats = file_writer.get_stats()
        console.print(f"[green]Output file: {output}[/green]")
        console.print(f"[green]Continuous file: {output.with_suffix('.continuous.txt')}[/green]")
        console.print(f"[blue]Total entries: {stats['total_entries']}[/blue]")
        console.print(f"[blue]Total text length: {stats['total_text_length']} characters[/blue]")
        
        if stats['total_entries'] > 0:
            duration = stats.get('duration_seconds', 0)
            if duration > 0:
                console.print(f"[blue]Duration: {duration:.1f} seconds[/blue]")
        
        logger.info(f"File transcription completed: {total_entries} entries")
        
    except Exception as e:
        error_handler.handle_error(e, "transcribing file", fatal=True)
        console.print(f"[red]Transcription failed: {e}[/red]")
        if supported_formats:
            console.print(f"[yellow]Supported formats: {', '.join(supported_formats)}[/yellow]")
        raise typer.Exit(1)
        
    finally:
        # Clean up
        file_writer.close_file()
        continuous_writer.close_file()
        file_transcriber.cleanup()


@app.command("server")
def run_server(
    model: str = typer.Option("base", "--model", "-m", help="Whisper model size (tiny, base, small, medium, large)"),
    device: str = typer.Option("cpu", "--device", "-d", help="Device to use (cpu, cuda)"),
    compute_type: str = typer.Option("float16", "--compute-type", "-c", help="Compute type (float16, int8, float32)"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8765, "--port", "-p", help="Port to bind to"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
    log_level: str = typer.Option("info", "--log-level", help="Log level (debug, info, warning, error)"),
):
    """Start remote Whisper transcription server."""
    
    # Check if server dependencies are available
    try:
        import uvicorn
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError:
        console.print("[red]Server dependencies not installed![/red]")
        console.print("[yellow]Install with: pip install 'fastapi>=0.104.0' 'uvicorn[standard]>=0.24.0' websockets[/yellow]")
        raise typer.Exit(1)
    
    # Check if faster-whisper is available
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        console.print("[red]faster-whisper not installed![/red]")
        console.print("[yellow]Install with: pip install faster-whisper[/yellow]")
        raise typer.Exit(1)
    
    # Import and start the server
    from .server.whisper_server import create_server_app, RemoteWhisperServer
    
    console.print("[green]Starting Remote Whisper Server...[/green]")
    console.print(f"[blue]Model: {model}[/blue]")
    console.print(f"[blue]Device: {device}[/blue]") 
    console.print(f"[blue]Compute Type: {compute_type}[/blue]")
    console.print(f"[blue]Host: {host}[/blue]")
    console.print(f"[blue]Port: {port}[/blue]")
    
    # Create server instance
    server = RemoteWhisperServer(
        model_size=model,
        device=device,
        compute_type=compute_type
    )
    
    # Create FastAPI app
    app_instance = create_server_app(server)
    
    # Load model
    console.print("[blue]Loading Whisper model...[/blue]")
    if not server.load_model():
        console.print("[red]Failed to load model. Exiting.[/red]")
        raise typer.Exit(1)
    
    console.print("[green]Server ready![/green]")
    console.print("Endpoints:")
    console.print(f"  Health: http://{host}:{port}/health")
    console.print(f"  Stats: http://{host}:{port}/stats")
    console.print(f"  Transcribe: http://{host}:{port}/transcribe")
    console.print(f"  WebSocket: ws://{host}:{port}/ws")
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")
    
    # Start server
    try:
        uvicorn.run(
            app_instance,
            host=host,
            port=port,
            workers=workers,
            log_level=log_level
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
        server.cleanup()
    except Exception as e:
        console.print(f"[red]Server error: {e}[/red]")
        server.cleanup()
        raise typer.Exit(1)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
