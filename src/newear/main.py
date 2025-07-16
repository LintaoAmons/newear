#!/usr/bin/env python3
"""
Newear CLI: Real-time system audio captioning tool
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from newear.audio.capture import AudioCapture
from newear.audio.devices import AudioDevices
from newear.output.file_writer import FileWriter
from newear.utils.config import Config

app = typer.Typer(
    name="newear",
    help="Real-time system audio captioning CLI tool",
    add_completion=False,
)

console = Console()


@app.command()
def main(
    device: Optional[int] = typer.Option(None, "--device", "-d", help="Audio device index (use --list-devices to see available)"),
    model: str = typer.Option("base", "--model", "-m", help="Whisper model size (tiny, base, small, medium, large)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path for transcript"),
    timestamps: bool = typer.Option(False, "--timestamps", "-t", help="Include timestamps in output"),
    language: Optional[str] = typer.Option(None, "--language", "-l", help="Language code (auto-detect if not specified)"),
    sample_rate: int = typer.Option(16000, "--sample-rate", "-s", help="Audio sample rate in Hz"),
    chunk_duration: float = typer.Option(2.0, "--chunk-duration", "-c", help="Audio chunk duration in seconds"),
    list_devices: bool = typer.Option(False, "--list-devices", help="List available audio devices and exit"),
):
    """Start real-time audio captioning."""
    
    # List devices if requested
    if list_devices:
        devices = AudioDevices()
        devices.list_devices()
        return
    
    # Initialize configuration
    config = Config(
        device_index=device,
        model_size=model,
        output_file=output,
        show_timestamps=timestamps,
        language=language,
        sample_rate=sample_rate,
        chunk_duration=chunk_duration,
    )
    
    # Initialize audio capture
    try:
        audio_capture = AudioCapture(config)
    except Exception as e:
        console.print(f"[red]Error initializing audio capture: {e}[/red]")
        sys.exit(1)
    
    # Initialize file writer
    file_writer = FileWriter(output, timestamps)
    
    # Start captioning
    console.print("[green]Starting Newear audio captioning...[/green]")
    console.print(f"[blue]Model: {model}[/blue]")
    console.print(f"[blue]Device: {device or 'auto-detect'}[/blue]")
    console.print(f"[blue]Sample rate: {sample_rate}Hz[/blue]")
    console.print(f"[blue]Chunk duration: {chunk_duration}s[/blue]")
    
    if output:
        console.print(f"[blue]Output file: {output}[/blue]")
    
    console.print("[yellow]Press Ctrl+C to stop[/yellow]")
    console.print("-" * 50)
    
    try:
        # Open file for writing if specified
        if output:
            file_writer.open_file()
            
        # For now, just start basic audio capture with file output
        if not audio_capture.start_capture():
            console.print("[red]Failed to start audio capture[/red]")
            sys.exit(1)
            
        # Basic audio monitoring with file output
        console.print("[green]Audio capture started. Monitoring audio levels...[/green]")
        
        for chunk in audio_capture.get_audio_chunks():
            if chunk is not None:
                rms = float(chunk.var()) ** 0.5  # RMS calculation
                if rms > 0.001:  # Only show when there's actual audio
                    message = f"Audio detected: RMS = {rms:.6f}"
                    console.print(f"[dim]{message}[/dim]")
                    
                    # Write to file if enabled
                    if output:
                        file_writer.write_entry(message)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Stopping Newear...[/yellow]")
        audio_capture.stop()
        file_writer.close_file()
        
        if output:
            stats = file_writer.get_stats()
            console.print(f"[green]Written {stats['total_entries']} entries to {output}[/green]")
        
        console.print("[green]Goodbye![/green]")
    except Exception as e:
        console.print(f"[red]Error during captioning: {e}[/red]")
        audio_capture.stop()
        file_writer.close_file()
        sys.exit(1)


def cli():
    """Entry point for the CLI."""
    app()

if __name__ == "__main__":
    cli()
