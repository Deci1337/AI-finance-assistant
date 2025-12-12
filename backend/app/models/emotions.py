"""Emotions analysis models"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class EmotionsAnalysisRequest(BaseModel):
    """Request model for emotions analysis"""
    text: str
    context: Optional[str] = None


class EmotionsAnalysisResponse(BaseModel):
    """Response model for emotions analysis"""
    emotions: Dict[str, float]
    dominant_emotion: str
    sentiment_score: float
    analysis_date: str
    analysis: Optional[str] = None
    questions: Optional[List[str]] = None
    recommendations: Optional[str] = None

