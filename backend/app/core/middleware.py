"""Middleware configuration"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings


def setup_cors(app: FastAPI) -> None:
    """Setup CORS middleware for the application"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
            "Access-Control-Request-Method",
            "Access-Control-Request-Headers",
        ],
        expose_headers=["*"],
        max_age=3600,
    )

