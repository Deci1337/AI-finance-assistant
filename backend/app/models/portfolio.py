"""Portfolio models"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class PortfolioAnalysisRequest(BaseModel):
    """Request model for portfolio analysis"""
    portfolio_data: Optional[Dict] = None
    analysis_type: Optional[str] = "full"
    use_mock_data: Optional[bool] = False


class PortfolioAnalysisResponse(BaseModel):
    """Response model for portfolio analysis"""
    analysis_id: str
    portfolio_value: float
    risk_score: float
    recommendations: List[str]
    analysis_date: str
    details: Dict
    detailed_analysis: Optional[str] = None
    risk_assessment: Optional[str] = None
    questions: Optional[List[str]] = None
    next_steps: Optional[str] = None


