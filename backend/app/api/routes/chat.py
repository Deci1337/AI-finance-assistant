"""Chat routes"""
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.chat import ChatRequest, ChatResponse, FriendlinessRequest, FriendlinessResponse
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest) -> ChatResponse:
    """
    Chat with AI assistant (GigaChat)
    
    Sends user message to GigaChat and returns response.
    Context can include user's financial information.
    """
    try:
        response_text = AIService.chat(request.message, request.context)
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.post("/analyze-friendliness", response_model=FriendlinessResponse)
async def analyze_friendliness(request: FriendlinessRequest) -> FriendlinessResponse:
    """
    Analyze friendliness of user message
    
    Returns friendliness score from 0.0 to 1.0:
    - 0.0 - very rude, aggressive message
    - 0.5 - neutral message
    - 1.0 - very friendly, polite message
    """
    try:
        result = AIService.analyze_friendliness(request.message)
        
        score = result.get("friendliness_score", 0.5)
        sentiment = result.get("sentiment", "neutral")
        
        print(f"Friendliness endpoint returning: score={score}, sentiment={sentiment}")
        
        return FriendlinessResponse(
            friendliness_score=score,
            sentiment=sentiment,
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing friendliness: {str(e)}")

