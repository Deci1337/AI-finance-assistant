"""Portfolio Service - Portfolio analysis business logic"""
from datetime import datetime
from typing import Dict, List

from mock_data import get_mock_portfolio, calculate_portfolio_metrics
from .ai_service import AIService


class PortfolioService:
    """Service for portfolio-related operations"""
    
    @staticmethod
    def get_mock_data() -> Dict:
        """Get mock portfolio data"""
        return get_mock_portfolio()
    
    @staticmethod
    def analyze(
        portfolio_data: Dict = None, 
        analysis_type: str = "full",
        use_mock_data: bool = False
    ) -> Dict:
        """Analyze portfolio and return results"""
        
        # Determine which data to use
        if use_mock_data or not portfolio_data:
            portfolio_data = get_mock_portfolio()
            is_mock = True
        else:
            is_mock = False
        
        # Calculate metrics
        metrics = calculate_portfolio_metrics(portfolio_data)
        
        # Generate AI recommendations
        ai_advice = AIService.generate_financial_advice(portfolio_data, analysis_type)
        
        # Extract data from AI response
        if isinstance(ai_advice, dict):
            ai_recommendations = ai_advice.get("recommendations", [])
            detailed_analysis = ai_advice.get("detailed_analysis")
            risk_assessment = ai_advice.get("risk_assessment")
            questions = ai_advice.get("questions")
            next_steps = ai_advice.get("next_steps")
        else:
            ai_recommendations = ai_advice if isinstance(ai_advice, list) else []
            detailed_analysis = None
            risk_assessment = None
            questions = None
            next_steps = None
        
        # Combine recommendations
        all_recommendations = ai_recommendations + metrics.get("recommendations", [])
        
        # Generate analysis ID
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Build details
        details = {
            "analysis_type": analysis_type,
            "assets_count": metrics.get("assets_count", 0),
            "sectors_distribution": metrics.get("sectors_distribution", {}),
            "is_mock_data": is_mock,
            "ai_recommendations_count": len(ai_recommendations)
        }
        
        if is_mock or (isinstance(portfolio_data, dict) and len(str(portfolio_data)) < 10000):
            details["portfolio_data"] = portfolio_data
        
        return {
            "analysis_id": analysis_id,
            "portfolio_value": metrics.get("portfolio_value", 0.0),
            "risk_score": metrics.get("risk_score", 0.0),
            "recommendations": all_recommendations[:10],
            "analysis_date": datetime.now().isoformat(),
            "details": details,
            "detailed_analysis": detailed_analysis,
            "risk_assessment": risk_assessment,
            "questions": questions,
            "next_steps": next_steps
        }

