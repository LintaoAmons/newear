"""Local Whisper transcription using faster-whisper."""

import numpy as np
import threading
import queue
import time
from typing import Optional, Generator, Dict, Any, List
from dataclasses import dataclass

from faster_whisper import WhisperModel
from rich.console import Console

from .models import ModelManager

console = Console()


@dataclass
class TranscriptionResult:
    """Result of transcription with timing information."""
    text: str
    start_time: float
    end_time: float
    confidence: float
    language: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
            "language": self.language
        }


class WhisperTranscriber:
    """Real-time transcription using faster-whisper."""
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None, 
                 device: str = "cpu", compute_type: str = "int8"):
        """Initialize the transcriber.
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            language: Target language code (None for auto-detection)
            device: Device to use ("cpu" or "cuda")
            compute_type: Compute type for inference ("int8", "float16", "float32")
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        
        self.model_manager = ModelManager()
        self.model: Optional[WhisperModel] = None
        self.is_loaded = False
        
        # Performance monitoring
        self.transcription_times: List[float] = []
        
    def load_model(self) -> bool:
        """Load the Whisper model."""
        if self.is_loaded:
            return True
            
        try:
            console.print(f"[blue]Loading Whisper model: {self.model_size}[/blue]")
            
            # Validate model name
            if not self.model_manager.validate_model_name(self.model_size):
                console.print(f"[red]Invalid model name: {self.model_size}[/red]")
                return False
            
            # Load model with faster-whisper
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            
            self.is_loaded = True
            console.print(f"[green]Model loaded successfully: {self.model_size}[/green]")
            
            # Print model info
            model_info = self.model_manager.get_model_info(self.model_size)
            if model_info:
                console.print(f"[dim]Model size: {model_info.size_mb}MB, {model_info.description}[/dim]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Failed to load model: {e}[/red]")
            return False
    
    def transcribe_audio(self, audio_data: np.ndarray, 
                        sample_rate: int = 16000) -> Optional[TranscriptionResult]:
        """Transcribe audio data.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio data
            
        Returns:
            TranscriptionResult or None if transcription failed
        """
        if not self.is_loaded:
            if not self.load_model():
                return None
        
        try:
            start_time = time.time()
            
            # Ensure audio is float32 and normalized
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio to [-1, 1] range if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,
                task="transcribe",
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(min_silence_duration_ms=500),
                word_timestamps=False
            )
            
            # Collect all segments
            transcription_segments = list(segments)
            
            if not transcription_segments:
                return None
            
            # Combine segments into single result
            full_text = " ".join([segment.text.strip() for segment in transcription_segments])
            
            if not full_text.strip():
                return None
            
            # Get timing information
            start_seg_time = transcription_segments[0].start
            end_seg_time = transcription_segments[-1].end
            
            # Calculate average confidence (if available)
            avg_confidence = sum(getattr(seg, 'avg_logprob', 0) for seg in transcription_segments) / len(transcription_segments)
            # Convert log probability to confidence score (0-1)
            confidence = min(1.0, max(0.0, (avg_confidence + 1.0) / 2.0))
            
            # Record transcription time for performance monitoring
            transcription_time = time.time() - start_time
            self.transcription_times.append(transcription_time)
            
            # Keep only recent times for rolling average
            if len(self.transcription_times) > 20:
                self.transcription_times = self.transcription_times[-20:]
            
            result = TranscriptionResult(
                text=full_text,
                start_time=start_seg_time,
                end_time=end_seg_time,
                confidence=confidence,
                language=info.language if info else None
            )
            
            return result
            
        except Exception as e:
            console.print(f"[red]Transcription error: {e}[/red]")
            return None
    
    def transcribe_chunk_stream(self, audio_chunks: Generator[np.ndarray, None, None],
                               sample_rate: int = 16000) -> Generator[TranscriptionResult, None, None]:
        """Transcribe streaming audio chunks.
        
        Args:
            audio_chunks: Generator yielding audio chunks
            sample_rate: Sample rate of audio data
            
        Yields:
            TranscriptionResult objects
        """
        if not self.is_loaded:
            if not self.load_model():
                return
        
        console.print("[green]Starting real-time transcription...[/green]")
        
        for chunk in audio_chunks:
            if chunk is None:
                continue
                
            # Only transcribe if there's sufficient audio energy
            rms = np.sqrt(np.mean(chunk ** 2))
            if rms < 0.001:  # Same threshold as Phase 1
                continue
            
            result = self.transcribe_audio(chunk, sample_rate)
            if result and result.text.strip():
                yield result
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.transcription_times:
            return {"avg_transcription_time": 0, "total_transcriptions": 0}
        
        avg_time = sum(self.transcription_times) / len(self.transcription_times)
        
        return {
            "avg_transcription_time": avg_time,
            "total_transcriptions": len(self.transcription_times),
            "model_size": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type
        }
    
    def cleanup(self):
        """Clean up resources."""
        if self.model:
            # faster-whisper models are automatically cleaned up
            self.model = None
        self.is_loaded = False
        console.print("[yellow]Transcriber cleaned up[/yellow]")
    
    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()