"""Application configuration"""
import os
from typing import List


class Settings:
    """Application settings"""
    
    # App info
    APP_NAME: str = "AI Finance Assistant API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Backend API for AI Finance Assistant application"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    DEBUG: bool = ENVIRONMENT == "development"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://127.0.0.1",
        "http://10.0.2.2",  # Android emulator
        "https://localhost",
        "https://127.0.0.1",
    ]
    
    def __init__(self):
        # Add custom origins from environment
        custom_origins = os.getenv("CORS_ORIGINS", "").strip()
        if custom_origins:
            self.CORS_ORIGINS.extend([
                origin.strip() 
                for origin in custom_origins.split(",") 
                if origin.strip()
            ])
        
        # In development, allow all origins
        if self.ENVIRONMENT == "development":
            self.CORS_ORIGINS = ["*"]


settings = Settings()

