"""Chat models"""
from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request model for AI chat"""
    message: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    """Response model for AI chat"""
    response: str
    timestamp: str


class FriendlinessRequest(BaseModel):
    """Request model for friendliness analysis"""
    message: str


class FriendlinessResponse(BaseModel):
    """Response model for friendliness analysis"""
    friendliness_score: float
    sentiment: str
    timestamp: str

