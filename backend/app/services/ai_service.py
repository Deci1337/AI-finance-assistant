"""AI Service - Gemini integration and fallbacks"""
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for gemini_integration import
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Try to import Gemini integration
try:
    from gemini_integration import (
        chat_completion_for_chat as gemini_chat_completion,
        get_access_token,
        GeminiAIClient
    )
    GEMINI_AVAILABLE = True
    print("Gemini integration loaded successfully")
except ImportError as e:
    GEMINI_AVAILABLE = False
    print(f"Warning: Gemini integration not available: {e}")


class AIService:
    """Service for AI-related operations"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if AI service is available"""
        return GEMINI_AVAILABLE
    
    @staticmethod
    def analyze_emotions(text: str, context: Optional[str] = None) -> Dict:
        """Analyze emotions in text"""
        return {
            "emotions": {
                "joy": 0.3, "fear": 0.1, "anger": 0.1, 
                "sadness": 0.1, "surprise": 0.1, "neutral": 0.3
            },
            "analysis": None,
            "questions": None
        }
    
    @staticmethod
    def generate_financial_advice(portfolio_data: Dict, analysis_type: str = "full") -> Dict:
        """Generate financial advice for portfolio"""
        return {
            "recommendations": [
                "Регулярно пересматривайте портфель",
                "Диверсифицируйте инвестиции"
            ]
        }
    
    @staticmethod
    def generate_comprehensive_advice(
        user_message: str, 
        portfolio_data: Optional[Dict] = None, 
        context: Optional[str] = None
    ) -> Dict:
        """Generate comprehensive financial advice"""
        return {
            "comprehensive_analysis": "Для получения детального анализа рекомендуется настроить AI интеграцию"
        }
    
    @staticmethod
    def extract_transactions(user_message: str, context: Optional[str] = None) -> Dict:
        """Extract transactions from user message"""
        amounts = re.findall(r'(\d+)\s*(?:рубл|руб|₽)', user_message, re.IGNORECASE)
        transactions = []
        for amount in amounts[:5]:
            transactions.append({
                "type": "expense",
                "title": user_message[:50],
                "amount": float(amount[0] if isinstance(amount, tuple) else amount),
                "category": "Other",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "confidence": 0.5
            })
        return {
            "transactions": transactions,
            "extracted_info": {},
            "analysis": "",
            "questions": [],
            "warnings": []
        }
    
    @staticmethod
    def transcribe_audio(audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
        """Transcribe audio to text"""
        return None
    
    @staticmethod
    def analyze_friendliness(text: str) -> Dict:
        """Analyze friendliness of message"""
        return {
            "friendliness_score": 0.5,
            "sentiment": "neutral",
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def generate_insights(transactions: List[Dict], current_month: Optional[str] = None) -> Optional[Dict]:
        """Generate insights from transactions"""
        if not transactions:
            return None
        return {
            "insight": "Проанализируйте свои транзакции для получения инсайтов",
            "category": "Other"
        }
    
    @staticmethod
    def generate_forecast(
        transactions: List[Dict], 
        user_message: str, 
        months: int = 3
    ) -> Optional[Dict]:
        """Generate financial forecast"""
        return {
            "category": "Other",
            "description": "Для получения прогноза настройте AI интеграцию"
        }
    
    @staticmethod
    def chat(message: str, context: Optional[str] = None) -> str:
        """Chat with AI assistant"""
        system_context = """Ты - дружелюбный AI-ассистент по личным финансам. Твоё имя - Финансовый Помощник.

ВАЖНО: Отвечай на вопрос пользователя напрямую! Не начинай анализировать расходы, если тебя об этом не просят.

ЧТО ТЫ УМЕЕШЬ:
1. Вести обычный диалог и отвечать на вопросы
2. Помогать с финансовыми вопросами и давать советы
3. Анализировать расходы (только если пользователь просит)
4. Делать прогнозы трат (только если пользователь просит)
5. Отвечать на общие вопросы

Отвечай на русском языке, дружелюбно и по делу."""
        
        full_message = message
        if context:
            full_message = f"""ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (используй только если пользователь просит анализ):
{context}

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {message}

ВАЖНО: Отвечай на сообщение пользователя напрямую."""
        else:
            full_message = f"СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {message}"
        
        # Try Gemini if available
        if GEMINI_AVAILABLE:
            try:
                token = get_access_token()
                if token:
                    result = gemini_chat_completion(token, f"{system_context}\n\n{full_message}")
                    if 'error' not in result:
                        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        error_type = result.get('error', '')
                        if error_type == 'quota_exceeded':
                            return "⚠️ Превышен лимит запросов к AI. Подождите минуту и попробуйте снова."
                        print(f"Gemini API returned error: {result}")
            except Exception as e:
                print(f"Gemini API error: {e}")
        
        # Fallback responses
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["привет", "здравствуй", "добрый день"]):
            return "Привет! Я твой финансовый помощник. Могу помочь с учётом расходов, анализом трат или ответить на вопросы о финансах. Чем могу помочь?"
        elif any(word in message_lower for word in ["что умеешь", "помощь", "help"]):
            return """Я могу помочь тебе с:
- Учётом доходов и расходов
- Анализом трат по категориям
- Прогнозом расходов
- Советами по экономии
- Ответами на финансовые вопросы
Просто напиши, что тебя интересует!"""
        else:
            return "Для полноценной работы чата необходимо настроить AI интеграцию (например, Gemini). Сейчас доступны только базовые функции."

