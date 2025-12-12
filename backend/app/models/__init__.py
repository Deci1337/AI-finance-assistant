"""Pydantic models for API requests and responses"""
from .portfolio import PortfolioAnalysisRequest, PortfolioAnalysisResponse
from .emotions import EmotionsAnalysisRequest, EmotionsAnalysisResponse
from .transactions import (
    TransactionExtractionRequest, 
    TransactionExtractionResponse,
    InsightRequest,
    InsightResponse,
    ForecastRequest,
    ForecastResponse
)
from .chat import ChatRequest, ChatResponse, FriendlinessRequest, FriendlinessResponse
from .voice import VoiceTranscriptionResponse
from .comprehensive import ComprehensiveAnalysisRequest, ComprehensiveAnalysisResponse

