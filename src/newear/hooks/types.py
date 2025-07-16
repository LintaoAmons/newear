"""Types for hook system."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from newear.transcription.whisper_local import TranscriptionResult


@dataclass
class HookContext:
    """Context information passed to hooks."""
    transcription_result: TranscriptionResult
    session_start_time: float
    chunk_index: int
    metadata: Dict[str, Any]


@dataclass
class HookResult:
    """Result returned from a hook."""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None