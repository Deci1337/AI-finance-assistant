"""Emotions analysis routes"""
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.emotions import EmotionsAnalysisRequest, EmotionsAnalysisResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/emotions", response_model=EmotionsAnalysisResponse)
async def analyze_emotions(request: EmotionsAnalysisRequest) -> EmotionsAnalysisResponse:
    """
    Analyze emotions in text
    
    Returns:
    - Emotion distribution
    - Dominant emotion
    - Overall sentiment score
    """
    try:
        result = AIService.analyze_emotions(request.text, request.context)
        
        if isinstance(result, dict) and "emotions" in result:
            emotions = result["emotions"]
            analysis = result.get("analysis")
            questions = result.get("questions")
            recommendations = result.get("recommendations")
        else:
            emotions = result if isinstance(result, dict) else {}
            analysis = None
            questions = None
            recommendations = None
        
        # Determine dominant emotion
        dominant_emotion = max(emotions, key=emotions.get) if emotions else "neutral"
        
        # Calculate sentiment score
        positive = emotions.get("joy", 0) + emotions.get("surprise", 0)
        negative = emotions.get("fear", 0) + emotions.get("anger", 0) + emotions.get("sadness", 0)
        total = positive + negative + 0.1
        sentiment_score = (positive - negative) / total if total > 0 else 0.0
        
        return EmotionsAnalysisResponse(
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            sentiment_score=sentiment_score,
            analysis_date=datetime.now().isoformat(),
            analysis=analysis,
            questions=questions,
            recommendations=recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing emotions: {str(e)}")

