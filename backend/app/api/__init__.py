"""API routes package"""
from fastapi import APIRouter
from .routes import health, portfolio, emotions, transactions, chat, voice

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(portfolio.router, tags=["Portfolio"])
api_router.include_router(emotions.router, tags=["Emotions"])
api_router.include_router(transactions.router, tags=["Transactions"])
api_router.include_router(chat.router, tags=["Chat"])
api_router.include_router(voice.router, tags=["Voice"])


