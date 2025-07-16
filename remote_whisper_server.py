#!/usr/bin/env python3
"""
Remote Whisper Server for GPU-accelerated transcription.

Run this on a machine with GPU (like your Windows machine with RTX 5070)
to provide transcription services to other machines.

Usage:
    python remote_whisper_server.py --model base --device cuda --port 8765
"""

import argparse
import asyncio
import json
import base64
import wave
import io
import time
from typing import Dict, Any, Optional

import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: faster-whisper not installed. Install with: pip install faster-whisper")


class TranscriptionRequest(BaseModel):
    """Request model for transcription."""
    audio_data: str  # base64 encoded WAV
    sample_rate: int
    language: Optional[str] = None
    task: str = "transcribe"


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


class RemoteWhisperServer:
    """Remote Whisper transcription server."""
    
    def __init__(self, model_size: str = "base", device: str = "cuda", compute_type: str = "float16"):
        """Initialize the server.
        
        Args:
            model_size: Whisper model size
            device: Device to use (cuda, cpu)
            compute_type: Compute type (float16, int8, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        self.is_loaded = False
        
        # Statistics
        self.total_requests = 0
        self.total_processing_time = 0.0
        
    def load_model(self) -> bool:
        """Load the Whisper model."""
        if self.is_loaded:
            return True
            
        if not WHISPER_AVAILABLE:
            print("Error: faster-whisper not available")
            return False
        
        try:
            print(f"Loading Whisper model: {self.model_size} on {self.device}")
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
            self.is_loaded = True
            print(f"Model loaded successfully")
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def decode_audio(self, audio_b64: str) -> Optional[np.ndarray]:
        """Decode base64 WAV audio data."""
        try:
            # Decode base64
            wav_data = base64.b64decode(audio_b64)
            
            # Read WAV from bytes
            wav_buffer = io.BytesIO(wav_data)
            with wave.open(wav_buffer, 'rb') as wav_file:
                # Get audio parameters
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                
                # Convert to numpy array
                if sample_width == 1:
                    dtype = np.uint8
                elif sample_width == 2:
                    dtype = np.int16
                elif sample_width == 4:
                    dtype = np.int32
                else:
                    raise ValueError(f"Unsupported sample width: {sample_width}")
                
                audio_data = np.frombuffer(frames, dtype=dtype)
                
                # Convert to float32 and normalize
                if dtype == np.uint8:
                    audio_data = (audio_data.astype(np.float32) - 128) / 128
                elif dtype == np.int16:
                    audio_data = audio_data.astype(np.float32) / 32768
                elif dtype == np.int32:
                    audio_data = audio_data.astype(np.float32) / 2147483648
                
                # Handle stereo -> mono
                if channels == 2:
                    audio_data = audio_data.reshape(-1, 2).mean(axis=1)
                
                return audio_data
                
        except Exception as e:
            print(f"Error decoding audio: {e}")
            return None
    
    def transcribe(self, request: TranscriptionRequest) -> TranscriptionResponse:
        """Transcribe audio from request."""
        if not self.is_loaded:
            if not self.load_model():
                return TranscriptionResponse(
                    success=False,
                    error="Model not loaded"
                )
        
        try:
            start_time = time.time()
            
            # Decode audio
            audio_data = self.decode_audio(request.audio_data)
            if audio_data is None:
                return TranscriptionResponse(
                    success=False,
                    error="Failed to decode audio"
                )
            
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                audio_data,
                language=request.language,
                task=request.task,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Collect segments
            transcription_segments = list(segments)
            
            if not transcription_segments:
                return TranscriptionResponse(
                    success=True,
                    result={
                        "text": "",
                        "start_time": 0.0,
                        "end_time": 0.0,
                        "confidence": 0.0,
                        "language": info.language if info else None
                    }
                )
            
            # Combine segments
            full_text = " ".join([segment.text.strip() for segment in transcription_segments])
            start_seg_time = transcription_segments[0].start
            end_seg_time = transcription_segments[-1].end
            
            # Calculate confidence
            avg_confidence = sum(getattr(seg, 'avg_logprob', 0) for seg in transcription_segments) / len(transcription_segments)
            confidence = min(1.0, max(0.0, (avg_confidence + 1.0) / 2.0))
            
            # Update statistics
            processing_time = time.time() - start_time
            self.total_requests += 1
            self.total_processing_time += processing_time
            
            return TranscriptionResponse(
                success=True,
                result={
                    "text": full_text,
                    "start_time": start_seg_time,
                    "end_time": end_seg_time,
                    "confidence": confidence,
                    "language": info.language if info else None
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            return TranscriptionResponse(
                success=False,
                error=f"Transcription error: {str(e)}"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        avg_time = self.total_processing_time / self.total_requests if self.total_requests > 0 else 0
        return {
            "model": self.model_size,
            "device": self.device,
            "compute_type": self.compute_type,
            "total_requests": self.total_requests,
            "total_processing_time": self.total_processing_time,
            "avg_processing_time": avg_time,
            "is_loaded": self.is_loaded
        }


# Global server instance
server = None


# FastAPI app
app = FastAPI(title="Remote Whisper Server", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model": server.model_size if server else "not loaded",
        "device": server.device if server else "unknown",
        "version": "1.0.0"
    }


@app.get("/stats")
async def get_stats():
    """Get server statistics."""
    if not server:
        return {"error": "Server not initialized"}
    return server.get_stats()


@app.post("/transcribe")
async def transcribe_audio(request: TranscriptionRequest):
    """Transcribe audio via HTTP."""
    if not server:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Server not initialized"}
        )
    
    response = server.transcribe(request)
    return response.dict()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription."""
    await websocket.accept()
    print("WebSocket client connected")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Create request object
            request = TranscriptionRequest(**request_data)
            
            # Transcribe
            response = server.transcribe(request)
            
            # Send response
            await websocket.send_text(json.dumps(response.dict()))
            
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()


def main():
    """Main function."""
    global server
    
    parser = argparse.ArgumentParser(description="Remote Whisper Server")
    parser.add_argument("--model", default="base", help="Whisper model size")
    parser.add_argument("--device", default="cuda", help="Device (cuda, cpu)")
    parser.add_argument("--compute-type", default="float16", help="Compute type")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    # Initialize server
    server = RemoteWhisperServer(
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type
    )
    
    # Load model
    print("Initializing Whisper model...")
    if not server.load_model():
        print("Failed to load model. Exiting.")
        return
    
    print(f"Starting server on {args.host}:{args.port}")
    print(f"Model: {args.model} on {args.device}")
    print("Endpoints:")
    print(f"  Health: http://{args.host}:{args.port}/health")
    print(f"  Stats: http://{args.host}:{args.port}/stats")
    print(f"  Transcribe: http://{args.host}:{args.port}/transcribe")
    print(f"  WebSocket: ws://{args.host}:{args.port}/ws")
    
    # Start server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info"
    )


if __name__ == "__main__":
    main()