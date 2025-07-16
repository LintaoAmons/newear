"""File-based transcription for video and audio files."""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List, Iterator
import time

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn

from newear.transcription.whisper_local import WhisperTranscriber, TranscriptionResult
from newear.utils.logging import get_logger

console = Console()
logger = get_logger()


class FileTranscriber:
    """Handles transcription of video and audio files."""
    
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.aiff', '.aif'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v'}
    
    def __init__(self, model_size: str = "base", language: Optional[str] = None, 
                 device: str = "cpu", compute_type: str = "int8"):
        """Initialize file transcriber."""
        self.model_size = model_size
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.transcriber = None
        
    def _initialize_transcriber(self):
        """Initialize the Whisper transcriber."""
        if self.transcriber is None:
            console.print(f"[blue]Initializing Whisper model: {self.model_size}[/blue]")
            self.transcriber = WhisperTranscriber(
                model_size=self.model_size,
                language=self.language,
                device=self.device,
                compute_type=self.compute_type
            )
            console.print("[green]Model loaded successfully[/green]")
    
    def _is_supported_format(self, file_path: Path) -> bool:
        """Check if file format is supported."""
        suffix = file_path.suffix.lower()
        return suffix in self.SUPPORTED_AUDIO_FORMATS or suffix in self.SUPPORTED_VIDEO_FORMATS
    
    def _is_video_format(self, file_path: Path) -> bool:
        """Check if file is a video format."""
        return file_path.suffix.lower() in self.SUPPORTED_VIDEO_FORMATS
    
    def _extract_audio_from_video(self, video_path: Path) -> Path:
        """Extract audio from video file using ffmpeg."""
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg is required for video processing. Install with: brew install ffmpeg")
        
        # Create temporary audio file
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio.close()
        temp_audio_path = Path(temp_audio.name)
        
        console.print(f"[blue]Extracting audio from video: {video_path.name}[/blue]")
        
        try:
            # Use ffmpeg to extract audio
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output file
                str(temp_audio_path)
            ]
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True
            ) as progress:
                task = progress.add_task("Extracting audio...", total=None)
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    check=True
                )
                
                progress.update(task, completed=True)
            
            console.print("[green]Audio extraction completed[/green]")
            return temp_audio_path
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error extracting audio: {e.stderr}[/red]")
            # Clean up temp file
            if temp_audio_path.exists():
                temp_audio_path.unlink()
            raise
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            # Clean up temp file
            if temp_audio_path.exists():
                temp_audio_path.unlink()
            raise
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _get_file_duration(self, file_path: Path) -> Optional[float]:
        """Get file duration using ffprobe."""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(file_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            return None
    
    def transcribe_file(self, file_path: Path, chunk_size: int = 30) -> Iterator[TranscriptionResult]:
        """Transcribe a video or audio file.
        
        Args:
            file_path: Path to the video or audio file
            chunk_size: Size of chunks in seconds for processing
            
        Yields:
            TranscriptionResult: Individual transcription results
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self._is_supported_format(file_path):
            supported = list(self.SUPPORTED_AUDIO_FORMATS | self.SUPPORTED_VIDEO_FORMATS)
            raise ValueError(f"Unsupported file format. Supported formats: {supported}")
        
        # Initialize transcriber
        self._initialize_transcriber()
        
        # Extract audio if it's a video file
        temp_audio_path = None
        audio_path = file_path
        
        if self._is_video_format(file_path):
            temp_audio_path = self._extract_audio_from_video(file_path)
            audio_path = temp_audio_path
        
        try:
            # Get file duration for progress tracking
            duration = self._get_file_duration(audio_path)
            
            console.print(f"[blue]Starting transcription of: {file_path.name}[/blue]")
            if duration:
                console.print(f"[blue]File duration: {duration:.1f} seconds[/blue]")
            
            # Transcribe the audio file
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                "[progress.percentage]{task.percentage:>3.0f}%",
                "•",
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                if duration:
                    task = progress.add_task("Transcribing...", total=duration)
                else:
                    task = progress.add_task("Transcribing...", total=None)
                
                # Use the transcriber to process the file
                start_time = time.time()
                
                # Create a generator that yields transcription results
                for result in self.transcriber.transcribe_file(str(audio_path)):
                    if result and result.text.strip():
                        # Update progress based on time elapsed
                        if duration:
                            elapsed = time.time() - start_time
                            progress.update(task, completed=min(elapsed, duration))
                        
                        yield result
                
                # Complete the progress bar
                if duration:
                    progress.update(task, completed=duration)
                else:
                    progress.update(task, completed=100)
            
            console.print("[green]Transcription completed successfully[/green]")
            
        finally:
            # Clean up temporary audio file if created
            if temp_audio_path and temp_audio_path.exists():
                temp_audio_path.unlink()
                logger.debug(f"Cleaned up temporary audio file: {temp_audio_path}")
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return sorted(list(self.SUPPORTED_AUDIO_FORMATS | self.SUPPORTED_VIDEO_FORMATS))
    
    def cleanup(self):
        """Clean up resources."""
        if self.transcriber:
            self.transcriber.cleanup()