"""Rich terminal display for real-time transcription."""

import threading
import time
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from collections import deque

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.align import Align
from rich.layout import Layout
from rich.status import Status

from newear.transcription.whisper_local import TranscriptionResult


@dataclass
class DisplayConfig:
    """Configuration for terminal display."""
    max_lines: int = 6
    show_timestamps: bool = True
    show_confidence: bool = False
    show_stats: bool = True
    update_interval: float = 0.1
    confidence_threshold: float = 0.7


class RichTerminalDisplay:
    """Rich terminal display for real-time transcription."""
    
    def __init__(self, config: DisplayConfig = None):
        """Initialize the display."""
        self.config = config or DisplayConfig()
        self.console = Console()
        self.live = None
        self.is_running = False
        
        # Thread-safe storage for transcription results
        self.transcription_buffer = deque(maxlen=self.config.max_lines)
        self.stats = {
            'total_chunks': 0,
            'high_confidence_chunks': 0,
            'start_time': None,
            'last_update': None,
            'model_info': None,
            'device_info': None
        }
        self.lock = threading.Lock()
        
        # Current status
        self.current_status = "Initializing..."
        self.is_transcribing = False
        self.model_loading = False
        
    def set_model_info(self, model_size: str, language: str = None):
        """Set model information for display."""
        with self.lock:
            self.stats['model_info'] = {
                'size': model_size,
                'language': language or 'auto-detect'
            }
    
    def set_device_info(self, device_name: str, sample_rate: int, chunk_duration: float):
        """Set audio device information."""
        with self.lock:
            self.stats['device_info'] = {
                'name': device_name,
                'sample_rate': sample_rate,
                'chunk_duration': chunk_duration
            }
    
    def set_status(self, status: str):
        """Update the current status."""
        with self.lock:
            self.current_status = status
    
    def set_model_loading(self, loading: bool):
        """Set model loading state."""
        with self.lock:
            self.model_loading = loading
    
    def set_transcribing(self, transcribing: bool):
        """Set transcription state."""
        with self.lock:
            self.is_transcribing = transcribing
            if transcribing and self.stats['start_time'] is None:
                self.stats['start_time'] = time.time()
    
    def add_transcription(self, result: TranscriptionResult):
        """Add a transcription result to the display."""
        with self.lock:
            self.transcription_buffer.append(result)
            self.stats['total_chunks'] += 1
            self.stats['last_update'] = time.time()
            
            if result.confidence > self.config.confidence_threshold:
                self.stats['high_confidence_chunks'] += 1
    
    def _create_header_panel(self) -> Panel:
        """Create the header panel with model and device info."""
        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left")
        header_table.add_column(justify="center")
        header_table.add_column(justify="right")
        
        # Model info (shorter)
        model_info = self.stats.get('model_info', {})
        model_text = f"{model_info.get('size', 'unknown')}"
        
        # Device info (shorter)
        device_info = self.stats.get('device_info', {})
        device_name = device_info.get('name', 'unknown')
        # Truncate long device names
        if len(device_name) > 15:
            device_name = device_name[:12] + "..."
        device_text = device_name
        
        # Status
        status_text = self.current_status
        if self.model_loading:
            status_text = "🔄 Loading..."
        elif self.is_transcribing:
            status_text = "🎙️ Recording"
        
        header_table.add_row(model_text, status_text, device_text)
        
        return Panel(header_table, title="Newear", 
                    title_align="center", border_style="blue")
    
    def _create_transcription_panel(self) -> Panel:
        """Create the transcription panel with recent results."""
        if not self.transcription_buffer:
            content = Text("Waiting for audio...", style="dim")
            return Panel(Align.center(content), title="Transcript", 
                        title_align="left", border_style="green")
        
        # Create table for transcriptions
        table = Table.grid(expand=True)
        if self.config.show_timestamps:
            table.add_column(style="dim", width=8)
        table.add_column()
        if self.config.show_confidence:
            table.add_column(justify="right", width=6)
        
        # Add recent transcriptions
        for result in self.transcription_buffer:
            row = []
            
            # Timestamp
            if self.config.show_timestamps:
                timestamp = datetime.fromtimestamp(result.start_time or time.time())
                row.append(timestamp.strftime("%H:%M:%S"))
            
            # Text with confidence-based styling
            if result.confidence > 0.8:
                text_style = "green"
            elif result.confidence > 0.5:
                text_style = "yellow"
            else:
                text_style = "red"
            
            row.append(Text(result.text, style=text_style))
            
            # Confidence
            if self.config.show_confidence:
                conf_text = f"{result.confidence:.2f}"
                if result.confidence > 0.8:
                    conf_style = "green"
                elif result.confidence > 0.5:
                    conf_style = "yellow"
                else:
                    conf_style = "red"
                row.append(Text(conf_text, style=conf_style))
            
            table.add_row(*row)
        
        return Panel(table, title="Transcript", title_align="left", border_style="green")
    
    def _create_stats_panel(self) -> Panel:
        """Create the statistics panel."""
        if not self.config.show_stats:
            return None
        
        stats_table = Table.grid(expand=True)
        stats_table.add_column(justify="left")
        stats_table.add_column(justify="center")
        stats_table.add_column(justify="right")
        
        # Calculate statistics
        total_chunks = self.stats['total_chunks']
        high_conf_chunks = self.stats['high_confidence_chunks']
        
        # Runtime
        if self.stats['start_time']:
            runtime = time.time() - self.stats['start_time']
            runtime_text = f"Runtime: {runtime:.0f}s"
        else:
            runtime_text = "Runtime: 0s"
        
        # Chunks processed
        chunks_text = f"Chunks: {total_chunks}"
        
        # Confidence rate
        if total_chunks > 0:
            conf_rate = (high_conf_chunks / total_chunks) * 100
            conf_text = f"High Conf: {conf_rate:.1f}%"
        else:
            conf_text = "High Conf: 0%"
        
        stats_table.add_row(runtime_text, chunks_text, conf_text)
        
        return Panel(stats_table, title="Statistics", 
                    title_align="left", border_style="cyan")
    
    def _create_layout(self) -> Layout:
        """Create the overall layout."""
        layout = Layout()
        
        # Split into header and body
        layout.split_column(
            Layout(self._create_header_panel(), name="header", size=3),
            Layout(name="body")
        )
        
        # Split body into transcript and stats
        if self.config.show_stats:
            layout["body"].split_column(
                Layout(self._create_transcription_panel(), name="transcript"),
                Layout(self._create_stats_panel(), name="stats", size=3)
            )
        else:
            layout["body"].update(self._create_transcription_panel())
        
        return layout
    
    def start(self):
        """Start the live display."""
        if self.is_running:
            return
        
        self.is_running = True
        self.live = Live(self._create_layout(), console=self.console, 
                        refresh_per_second=1/self.config.update_interval,
                        screen=True)
        self.live.start()
    
    def stop(self):
        """Stop the live display."""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.live:
            self.live.stop()
            self.live = None
    
    def update(self):
        """Update the display (called automatically by Live)."""
        if self.live and self.is_running:
            self.live.update(self._create_layout())
    
    def print_summary(self):
        """Print a summary when stopping."""
        if not self.stats['start_time']:
            return
        
        runtime = time.time() - self.stats['start_time']
        total_chunks = self.stats['total_chunks']
        high_conf_chunks = self.stats['high_confidence_chunks']
        
        summary_table = Table(title="Transcription Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Runtime", f"{runtime:.1f} seconds")
        summary_table.add_row("Chunks Processed", str(total_chunks))
        summary_table.add_row("High Confidence", f"{high_conf_chunks}/{total_chunks}")
        
        if total_chunks > 0:
            conf_rate = (high_conf_chunks / total_chunks) * 100
            summary_table.add_row("Confidence Rate", f"{conf_rate:.1f}%")
            
            avg_chunk_time = runtime / total_chunks
            summary_table.add_row("Avg Chunk Time", f"{avg_chunk_time:.2f}s")
        
        self.console.print(summary_table)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
