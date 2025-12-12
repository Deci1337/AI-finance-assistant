"""Comprehensive analysis models"""
from pydantic import BaseModel
from typing import Dict, List, Optional


class ComprehensiveAnalysisRequest(BaseModel):
    """Request model for comprehensive analysis"""
    user_message: str
    portfolio_data: Optional[Dict] = None
    context: Optional[str] = None


class ComprehensiveAnalysisResponse(BaseModel):
    """Response model for comprehensive analysis"""
    analysis_id: str
    analysis_date: str
    comprehensive_analysis: Optional[str] = None
    financial_goals_analysis: Optional[Dict] = None
    risk_assessment: Optional[Dict] = None
    emotional_analysis: Optional[Dict] = None
    personalized_recommendations: Optional[List[Dict]] = None
    financial_plan: Optional[Dict] = None
    questions_to_clarify: Optional[List[str]] = None
    warnings_and_considerations: Optional[List[str]] = None
    extracted_parameters: Optional[Dict] = None

