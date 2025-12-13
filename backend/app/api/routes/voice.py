"""Voice transcription routes"""
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.models.voice import VoiceTranscriptionResponse
from app.services.ai_service import AIService
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.post("/transcribe-voice", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(
    audio: UploadFile = File(...),
    audio_format: Optional[str] = Form("wav")
) -> VoiceTranscriptionResponse:
    """
    Speech recognition from voice message
    
    Accepts audio file and returns transcribed text.
    Supported formats: wav, mp3, oggopus, opus, flac, pcm16
    """
    try:
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        transcribed_text = AIService.transcribe_audio(audio_data, audio_format)
        
        if not transcribed_text:
            return VoiceTranscriptionResponse(
                transcription_id=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                transcription_date=datetime.now().isoformat(),
                text="",
                error="Could not recognize speech. Check audio quality and file format."
            )
        
        transcription_id = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return VoiceTranscriptionResponse(
            transcription_id=transcription_id,
            transcription_date=datetime.now().isoformat(),
            text=transcribed_text,
            confidence=0.9
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing speech: {str(e)}")


@router.post("/transcribe-and-extract", response_model=Dict)
async def transcribe_and_extract(
    audio: UploadFile = File(...),
    audio_format: Optional[str] = Form("wav"),
    context: Optional[str] = Form(None)
) -> Dict:
    """
    Speech recognition and automatic transaction extraction
    
    Combined endpoint that:
    1. Recognizes speech from audio
    2. Automatically extracts transactions from recognized text
    """
    try:
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        transcribed_text = AIService.transcribe_audio(audio_data, audio_format)
        
        if not transcribed_text:
            return {
                "success": False,
                "error": "Could not recognize speech",
                "transcription": "",
                "transactions": []
            }
        
        result = TransactionService.extract(transcribed_text, context)
        
        return {
            "success": True,
            "transcription": transcribed_text,
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing voice message: {str(e)}")


