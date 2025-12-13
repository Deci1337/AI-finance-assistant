"""Transaction models"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class TransactionExtractionRequest(BaseModel):
    """Request model for transaction extraction"""
    user_message: str
    context: Optional[str] = None


class TransactionExtractionResponse(BaseModel):
    """Response model for transaction extraction"""
    extraction_id: str
    extraction_date: str
    transactions: List[Dict]
    extracted_info: Optional[Dict] = None
    analysis: Optional[str] = None
    questions: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    extracted_parameters: Optional[Dict] = None


class InsightRequest(BaseModel):
    """Request model for insights"""
    transactions: List[Dict]
    current_month: Optional[str] = None


class InsightResponse(BaseModel):
    """Response model for insights"""
    insight: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    transaction_count: Optional[int] = None
    low_importance_count: Optional[int] = None
    low_importance_percent: Optional[float] = None
    previous_month_amount: Optional[float] = None
    percent_of_total: Optional[float] = None
    timestamp: Optional[str] = None


class ForecastRequest(BaseModel):
    """Request model for forecast"""
    transactions: List[Dict]
    user_message: str
    months: Optional[int] = 3


class ForecastResponse(BaseModel):
    """Response model for forecast"""
    category: Optional[str] = None
    current_monthly: Optional[float] = None
    change_percent: Optional[float] = None
    new_monthly: Optional[float] = None
    months: Optional[int] = None
    monthly_forecast: Optional[List[Dict]] = None
    total_savings: Optional[float] = None
    description: Optional[str] = None
    timestamp: Optional[str] = None


