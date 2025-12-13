"""Voice transcription models"""
from pydantic import BaseModel
from typing import Optional


class VoiceTranscriptionResponse(BaseModel):
    """Response model for voice transcription"""
    transcription_id: str
    transcription_date: str
    text: str
    confidence: Optional[float] = None
    error: Optional[str] = None


