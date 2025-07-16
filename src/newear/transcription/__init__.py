"""Speech transcription module using faster-whisper."""

from .whisper_local import WhisperTranscriber
from .models import ModelManager

__all__ = ["WhisperTranscriber", "ModelManager"]