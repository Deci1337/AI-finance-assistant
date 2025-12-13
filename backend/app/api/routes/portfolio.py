"""Portfolio analysis routes"""
from typing import Dict
from fastapi import APIRouter, HTTPException

from app.models.portfolio import PortfolioAnalysisRequest, PortfolioAnalysisResponse
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/mock/portfolio")
async def get_mock_portfolio_data() -> Dict:
    """Get mock portfolio data for testing"""
    return PortfolioService.get_mock_data()


@router.post("/analyze", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(request: PortfolioAnalysisRequest) -> PortfolioAnalysisResponse:
    """
    Analyze portfolio
    
    Accepts portfolio data and returns analysis:
    - Portfolio value estimation
    - Risk assessment
    - Optimization recommendations
    """
    try:
        result = PortfolioService.analyze(
            portfolio_data=request.portfolio_data,
            analysis_type=request.analysis_type,
            use_mock_data=request.use_mock_data
        )
        return PortfolioAnalysisResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing portfolio: {str(e)}")


