"""
AI Finance Assistant - Backend API
FastAPI application entry point
"""
import os
import sys
import uvicorn

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.core.config import settings

# Create FastAPI application
app = create_app()


def main():
    """Run the application"""
    # For Termux (Android) disable reload for stability
    is_termux = os.path.exists("/data/data/com.termux")
    reload_enabled = not is_termux and settings.DEBUG
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=reload_enabled,
        log_level="info"
    )


if __name__ == "__main__":
    main()
