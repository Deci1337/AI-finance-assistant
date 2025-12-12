"""Transaction Service - Transaction extraction and analysis"""
from datetime import datetime
from typing import Dict, List, Optional

from .ai_service import AIService


class TransactionService:
    """Service for transaction-related operations"""
    
    @staticmethod
    def extract(user_message: str, context: Optional[str] = None) -> Dict:
        """Extract transactions from user message"""
        result = AIService.extract_transactions(user_message, context)
        
        extraction_id = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "extraction_id": extraction_id,
            "extraction_date": datetime.now().isoformat(),
            "transactions": result.get("transactions", []),
            "extracted_info": result.get("extracted_info"),
            "analysis": result.get("analysis"),
            "questions": result.get("questions"),
            "warnings": result.get("warnings"),
            "extracted_parameters": result.get("extracted_parameters")
        }
    
    @staticmethod
    def get_insights(transactions: List[Dict], current_month: Optional[str] = None) -> Dict:
        """Get insights from transactions"""
        result = AIService.generate_insights(transactions, current_month)
        
        if result:
            return {
                "insight": result.get("insight"),
                "category": result.get("category"),
                "amount": result.get("amount"),
                "transaction_count": result.get("transaction_count"),
                "low_importance_count": result.get("low_importance_count"),
                "low_importance_percent": result.get("low_importance_percent"),
                "previous_month_amount": result.get("previous_month_amount"),
                "percent_of_total": result.get("percent_of_total"),
                "timestamp": result.get("timestamp", datetime.now().isoformat())
            }
        
        return {
            "insight": None,
            "category": None,
            "amount": None,
            "transaction_count": None,
            "low_importance_count": None,
            "low_importance_percent": None,
            "previous_month_amount": None,
            "percent_of_total": None,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_forecast(
        transactions: List[Dict], 
        user_message: str, 
        months: int = 3
    ) -> Dict:
        """Get financial forecast"""
        result = AIService.generate_forecast(transactions, user_message, months)
        
        if result:
            return {
                "category": result.get("category"),
                "current_monthly": result.get("current_monthly"),
                "change_percent": result.get("change_percent"),
                "new_monthly": result.get("new_monthly"),
                "months": result.get("months"),
                "monthly_forecast": result.get("monthly_forecast"),
                "total_savings": result.get("total_savings"),
                "description": result.get("description"),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "category": None,
            "description": "Для получения прогноза настройте AI интеграцию",
            "timestamp": datetime.now().isoformat()
        }

