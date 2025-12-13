"""Transaction routes"""
from datetime import datetime
from fastapi import APIRouter, HTTPException

from app.models.transactions import (
    TransactionExtractionRequest,
    TransactionExtractionResponse,
    InsightRequest,
    InsightResponse,
    ForecastRequest,
    ForecastResponse
)
from app.models.comprehensive import ComprehensiveAnalysisRequest, ComprehensiveAnalysisResponse
from app.services.transaction_service import TransactionService
from app.services.ai_service import AIService

router = APIRouter()


@router.post("/extract-transactions", response_model=TransactionExtractionResponse)
async def extract_transactions(request: TransactionExtractionRequest) -> TransactionExtractionResponse:
    """
    Extract transactions from user message
    
    Analyzes user message and extracts structured transaction information:
    - Transaction type (income/expense)
    - Amount
    - Category
    - Date
    - Title/description
    """
    try:
        result = TransactionService.extract(request.user_message, request.context)
        return TransactionExtractionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting transactions: {str(e)}")


@router.post("/comprehensive-analysis", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analysis(request: ComprehensiveAnalysisRequest) -> ComprehensiveAnalysisResponse:
    """
    Comprehensive financial analysis
    
    Provides:
    - Situation analysis
    - Financial goals analysis
    - Risk assessment
    - Emotional analysis
    - Personalized recommendations
    - Financial plan
    """
    try:
        result = AIService.generate_comprehensive_advice(
            request.user_message,
            request.portfolio_data,
            request.context
        )
        
        analysis_id = f"comprehensive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ComprehensiveAnalysisResponse(
            analysis_id=analysis_id,
            analysis_date=datetime.now().isoformat(),
            comprehensive_analysis=result.get("comprehensive_analysis"),
            financial_goals_analysis=result.get("financial_goals_analysis"),
            risk_assessment=result.get("risk_assessment"),
            emotional_analysis=result.get("emotional_analysis"),
            personalized_recommendations=result.get("personalized_recommendations"),
            financial_plan=result.get("financial_plan"),
            questions_to_clarify=result.get("questions_to_clarify"),
            warnings_and_considerations=result.get("warnings_and_considerations"),
            extracted_parameters=result.get("extracted_parameters")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in comprehensive analysis: {str(e)}")


@router.post("/insights", response_model=InsightResponse)
async def get_insights(request: InsightRequest) -> InsightResponse:
    """
    Get personal insights based on user transactions
    
    Analyzes patterns in transactions and generates personal recommendations.
    """
    try:
        result = TransactionService.get_insights(request.transactions, request.current_month)
        return InsightResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")


@router.post("/forecast", response_model=ForecastResponse)
async def get_forecast(request: ForecastRequest) -> ForecastResponse:
    """
    Get financial forecast
    
    Generates expense forecast based on user data and request.
    """
    try:
        result = TransactionService.get_forecast(
            request.transactions,
            request.user_message,
            request.months
        )
        return ForecastResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")


