"""Health check routes"""
from datetime import datetime
from typing import Dict
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check_legacy() -> Dict[str, str]:
    """Legacy health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME
    }


@router.get("/api/v1/status")
async def api_status() -> Dict[str, str]:
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "operational"
    }

