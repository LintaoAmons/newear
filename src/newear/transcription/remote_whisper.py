"""Remote Whisper transcription over HTTP/WebSocket."""

import json
import time
import requests
import websocket
import numpy as np
import threading
import queue
from typing import Optional, Generator, Dict, Any, List, Iterator
from dataclasses import dataclass, asdict
import base64
import wave
import io

from rich.console import Console
from .whisper_local import TranscriptionResult

console = Console()


@dataclass
class RemoteTranscriptionRequest:
    """Request for remote transcription."""
    audio_data: str  # base64 encoded audio
    sample_rate: int
    language: Optional[str] = None
    task: str = "transcribe"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RemoteServerConfig:
    """Configuration for remote transcription server."""
    host: str = "localhost"
    port: int = 8765
    protocol: str = "http"  # "http" or "websocket"
    model_size: str = "base"
    timeout: float = 30.0
    
    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"


class RemoteWhisperTranscriber:
    """Remote transcription using Whisper running on another machine."""
    
    def __init__(self, 
                 remote_config: RemoteServerConfig,
                 language: Optional[str] = None):
        """Initialize the remote transcriber.
        
        Args:
            remote_config: Configuration for remote server
            language: Target language code (None for auto-detection)
        """
        self.remote_config = remote_config
        self.language = language
        self.is_loaded = False
        self.ws = None
        
        # Performance monitoring
        self.transcription_times: List[float] = []
        
        # WebSocket handling
        self.ws_queue = queue.Queue()
        self.ws_thread = None
        self.ws_running = False
        
    def _encode_audio(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """Encode audio data as base64 WAV."""
        # Convert to 16-bit PCM
        if audio_data.dtype != np.int16:
            # Normalize to [-1, 1] if needed
            if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Convert to 16-bit PCM
            audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        # Encode as base64
        wav_data = wav_buffer.getvalue()
        return base64.b64encode(wav_data).decode('utf-8')
    
    def _decode_response(self, response_data: Dict[str, Any]) -> Optional[TranscriptionResult]:
        """Decode transcription response."""
        if not response_data.get('success', False):
            error = response_data.get('error', 'Unknown error')
            console.print(f"[red]Remote transcription error: {error}[/red]")
            return None
        
        result_data = response_data.get('result', {})
        if not result_data.get('text'):
            return None
        
        return TranscriptionResult(
            text=result_data.get('text', ''),
            start_time=result_data.get('start_time', 0.0),
            end_time=result_data.get('end_time', 0.0),
            confidence=result_data.get('confidence', 0.8),
            language=result_data.get('language', self.language)
        )
    
    def load_model(self) -> bool:
        """Test connection to remote server."""
        try:
            console.print(f"[blue]Connecting to remote Whisper server: {self.remote_config.base_url}[/blue]")
            
            # Test connection with a ping
            if self.remote_config.protocol == "http":
                response = requests.get(
                    f"{self.remote_config.base_url}/health",
                    timeout=5.0
                )
                if response.status_code == 200:
                    server_info = response.json()
                    console.print(f"[green]Connected to remote server[/green]")
                    console.print(f"[dim]Server model: {server_info.get('model', 'unknown')}[/dim]")
                    console.print(f"[dim]Server version: {server_info.get('version', 'unknown')}[/dim]")
                    self.is_loaded = True
                    return True
            
            elif self.remote_config.protocol == "websocket":
                # Test WebSocket connection
                ws_url = f"ws://{self.remote_config.host}:{self.remote_config.port}/ws"
                test_ws = websocket.create_connection(ws_url, timeout=5.0)
                test_ws.close()
                console.print(f"[green]WebSocket connection successful[/green]")
                self.is_loaded = True
                return True
            
            return False
            
        except requests.exceptions.ConnectionError:
            console.print(f"[red]Could not connect to remote server at {self.remote_config.base_url}[/red]")
            console.print("[yellow]Make sure the remote Whisper server is running[/yellow]")
            return False
        except Exception as e:
            console.print(f"[red]Error connecting to remote server: {e}[/red]")
            return False
    
    def _setup_websocket(self):
        """Setup WebSocket connection for real-time transcription."""
        if self.remote_config.protocol != "websocket":
            return
        
        def on_message(ws, message):
            try:
                response = json.loads(message)
                result = self._decode_response(response)
                if result:
                    self.ws_queue.put(result)
            except Exception as e:
                console.print(f"[red]WebSocket message error: {e}[/red]")
        
        def on_error(ws, error):
            console.print(f"[red]WebSocket error: {error}[/red]")
        
        def on_close(ws, close_status_code, close_msg):
            console.print("[yellow]WebSocket connection closed[/yellow]")
            self.ws_running = False
        
        def on_open(ws):
            console.print("[green]WebSocket connection opened[/green]")
            self.ws_running = True
        
        try:
            ws_url = f"ws://{self.remote_config.host}:{self.remote_config.port}/ws"
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            # Run WebSocket in a separate thread
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            # Wait for connection
            timeout = 5.0
            start_time = time.time()
            while not self.ws_running and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.ws_running
            
        except Exception as e:
            console.print(f"[red]WebSocket setup error: {e}[/red]")
            return False
    
    def transcribe_audio(self, audio_data: np.ndarray, 
                        sample_rate: int = 16000) -> Optional[TranscriptionResult]:
        """Transcribe audio data using remote server.
        
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
            
            # Encode audio data
            audio_b64 = self._encode_audio(audio_data, sample_rate)
            
            # Create request
            request = RemoteTranscriptionRequest(
                audio_data=audio_b64,
                sample_rate=sample_rate,
                language=self.language,
                task="transcribe"
            )
            
            # Send request based on protocol
            if self.remote_config.protocol == "http":
                response = requests.post(
                    f"{self.remote_config.base_url}/transcribe",
                    json=request.to_dict(),
                    timeout=self.remote_config.timeout
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    result = self._decode_response(response_data)
                    
                    if result:
                        # Record performance
                        transcription_time = time.time() - start_time
                        self.transcription_times.append(transcription_time)
                        
                        # Keep only recent times
                        if len(self.transcription_times) > 20:
                            self.transcription_times = self.transcription_times[-20:]
                    
                    return result
                else:
                    console.print(f"[red]HTTP error: {response.status_code}[/red]")
                    return None
            
            elif self.remote_config.protocol == "websocket":
                if not self.ws_running:
                    if not self._setup_websocket():
                        return None
                
                # Send via WebSocket
                self.ws.send(json.dumps(request.to_dict()))
                
                # Wait for response
                try:
                    result = self.ws_queue.get(timeout=self.remote_config.timeout)
                    
                    # Record performance
                    transcription_time = time.time() - start_time
                    self.transcription_times.append(transcription_time)
                    
                    return result
                except queue.Empty:
                    console.print("[red]WebSocket response timeout[/red]")
                    return None
            
            return None
            
        except requests.exceptions.Timeout:
            console.print(f"[red]Request timeout ({self.remote_config.timeout}s)[/red]")
            return None
        except requests.exceptions.ConnectionError:
            console.print("[red]Connection error to remote server[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Remote transcription error: {e}[/red]")
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
        
        console.print("[green]Starting remote transcription...[/green]")
        
        for chunk in audio_chunks:
            if chunk is None:
                continue
                
            # Only transcribe if there's sufficient audio energy
            rms = np.sqrt(np.mean(chunk ** 2))
            if rms < 0.001:
                continue
            
            result = self.transcribe_audio(chunk, sample_rate)
            if result and result.text.strip():
                yield result
    
    def transcribe_file(self, file_path: str) -> Iterator[TranscriptionResult]:
        """Transcribe an audio file using remote server.
        
        Args:
            file_path: Path to the audio file
            
        Yields:
            TranscriptionResult: Individual transcription segments
        """
        if not self.is_loaded:
            if not self.load_model():
                return
        
        try:
            # For file transcription, we'll send the file path if supported
            # or load the file and send audio data
            
            # For now, implement a simple approach: load file and send chunks
            import soundfile as sf
            
            audio_data, sample_rate = sf.read(file_path)
            
            # Send entire file at once for now
            result = self.transcribe_audio(audio_data, sample_rate)
            if result:
                yield result
                
        except Exception as e:
            console.print(f"[red]Error transcribing file: {e}[/red]")
            return
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.transcription_times:
            return {"avg_transcription_time": 0, "total_transcriptions": 0}
        
        avg_time = sum(self.transcription_times) / len(self.transcription_times)
        
        return {
            "avg_transcription_time": avg_time,
            "total_transcriptions": len(self.transcription_times),
            "backend": "Remote Whisper",
            "remote_host": f"{self.remote_config.host}:{self.remote_config.port}",
            "protocol": self.remote_config.protocol
        }
    
    def cleanup(self):
        """Clean up resources."""
        if self.ws:
            self.ws.close()
            self.ws = None
        
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_running = False
            self.ws_thread.join(timeout=2.0)
        
        self.is_loaded = False
        console.print("[yellow]Remote transcriber cleaned up[/yellow]")
    
    def __enter__(self):
        """Context manager entry."""
        self.load_model()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
    
    @classmethod
    def is_available(cls) -> bool:
        """Check if remote transcription is available."""
        try:
            import requests
            import websocket
            return True
        except ImportError:
            return False