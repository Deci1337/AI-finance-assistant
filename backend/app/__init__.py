"""
AI Finance Assistant - Backend Application Package
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.middleware import setup_cors
from app.api import api_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description=settings.APP_DESCRIPTION,
        version=settings.APP_VERSION
    )
    
    # Setup CORS
    setup_cors(app)
    
    # Include API routes
    app.include_router(api_router)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": str(exc)
            }
        )
    
    return app

