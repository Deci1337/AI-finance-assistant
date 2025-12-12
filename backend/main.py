"""
AI Finance Assistant - Backend API
FastAPI application for financial data processing and analysis
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import os
from typing import Dict, List, Optional
from datetime import datetime
from mock_data import get_mock_portfolio, calculate_portfolio_metrics

# Импорт Gemini интеграции
try:
    from gemini_integration import (
        chat_completion_for_chat as chat_completion,
        get_access_token,
        GeminiAIClient
    )
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: Gemini integration not available, using fallback functions")

# Fallback функции для AI интеграций
def analyze_emotions_with_fallback(text: str, context: Optional[str] = None) -> Dict:
    """Простой анализ эмоций (fallback)"""
    return {"emotions": {"joy": 0.3, "fear": 0.1, "anger": 0.1, "sadness": 0.1, "surprise": 0.1, "neutral": 0.3}}

def generate_financial_advice_with_fallback(portfolio_data: Dict, analysis_type: str = "full") -> Dict:
    """Простая генерация финансовых советов (fallback)"""
    return {"recommendations": ["Регулярно пересматривайте портфель", "Диверсифицируйте инвестиции"]}

def generate_comprehensive_advice_with_fallback(user_message: str, portfolio_data: Optional[Dict] = None, context: Optional[str] = None) -> Dict:
    """Простая генерация комплексных советов (fallback)"""
    return {"comprehensive_analysis": "Для получения детального анализа рекомендуется настроить AI интеграцию"}

def extract_transactions_with_fallback(user_message: str, context: Optional[str] = None) -> Dict:
    """Простое извлечение транзакций (fallback)"""
    import re
    amounts = re.findall(r'(\d+)\s*(?:рубл|руб|₽)', user_message, re.IGNORECASE)
    transactions = []
    for amount in amounts[:5]:
        transactions.append({
            "type": "expense",
            "title": user_message[:50],
            "amount": float(amount[0]),
            "category": "Other",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "confidence": 0.5
        })
    return {"transactions": transactions, "extracted_info": {}, "analysis": "", "questions": [], "warnings": []}

def transcribe_audio_with_fallback(audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
    """Распознавание речи (fallback - не поддерживается)"""
    return None

def analyze_friendliness_with_fallback(text: str) -> Dict:
    """Простой анализ дружелюбности (fallback)"""
    return {"friendliness_score": 0.5, "sentiment": "neutral", "timestamp": datetime.now().isoformat()}

def generate_insights_with_fallback(transactions: List[Dict], current_month: Optional[str] = None) -> Optional[Dict]:
    """Простая генерация инсайтов (fallback)"""
    if not transactions:
        return None
    return {"insight": "Проанализируйте свои транзакции для получения инсайтов", "category": "Other"}

def generate_forecast_with_fallback(transactions: List[Dict], user_message: str, months: int = 3) -> Optional[Dict]:
    """Простая генерация прогноза (fallback)"""
    return {"category": "Other", "description": "Для получения прогноза настройте AI интеграцию"}

# Создание экземпляра FastAPI приложения
app = FastAPI(
    title="AI Finance Assistant API",
    description="Backend API for AI Finance Assistant application",
    version="1.0.0"
)

# Настройка CORS для работы с MAUI приложением
# MAUI приложения могут работать на разных платформах:
# - Windows: localhost, 127.0.0.1
# - Android эмулятор: 10.0.2.2
# - iOS/Mac: localhost, 127.0.0.1
# - Реальные устройства: IP адрес хоста

# Определение режима работы
environment = os.getenv("ENVIRONMENT", "development").lower()

# Базовые разрешенные источники для MAUI
allowed_origins: List[str] = [
    "http://localhost",
    "http://127.0.0.1",
    "http://10.0.2.2",  # Android эмулятор
    "https://localhost",
    "https://127.0.0.1",
]

# Добавление кастомных источников из переменных окружения (для реальных устройств)
# Формат: CORS_ORIGINS=http://192.168.1.100,http://192.168.1.100:8080
custom_origins = os.getenv("CORS_ORIGINS", "").strip()
if custom_origins:
    allowed_origins.extend([origin.strip() for origin in custom_origins.split(",") if origin.strip()])

# В режиме разработки разрешаем все источники для удобства тестирования
# В продакшене используйте конкретные домены через переменную CORS_ORIGINS
if environment == "development":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
    max_age=3600,  # Кэширование preflight запросов на 1 час
)


# Модели данных для запросов и ответов
class PortfolioAnalysisRequest(BaseModel):
    """Модель запроса для анализа портфеля"""
    portfolio_data: Optional[Dict] = None  # Данные портфеля (акции, облигации и т.д.). Если None, используются mock данные
    analysis_type: Optional[str] = "full"  # Тип анализа: full, risk, performance
    use_mock_data: Optional[bool] = False  # Использовать mock данные вместо переданных


class PortfolioAnalysisResponse(BaseModel):
    """Модель ответа для анализа портфеля"""
    analysis_id: str
    portfolio_value: float
    risk_score: float
    recommendations: List[str]
    analysis_date: str
    details: Dict
    detailed_analysis: Optional[str] = None  # Развернутый анализ портфеля
    risk_assessment: Optional[str] = None  # Оценка рисков
    questions: Optional[List[str]] = None  # Наводящие вопросы
    next_steps: Optional[str] = None  # Следующие шаги


class EmotionsAnalysisRequest(BaseModel):
    """Модель запроса для анализа эмоций"""
    text: str  # Текст для анализа эмоций
    context: Optional[str] = None  # Контекст (например, финансовые новости)


class EmotionsAnalysisResponse(BaseModel):
    """Модель ответа для анализа эмоций"""
    emotions: Dict[str, float]  # Словарь эмоций с их вероятностями
    dominant_emotion: str
    sentiment_score: float  # От -1 (негатив) до 1 (позитив)
    analysis_date: str
    analysis: Optional[str] = None  # Детальный анализ эмоционального состояния
    questions: Optional[List[str]] = None  # Наводящие вопросы
    recommendations: Optional[str] = None  # Рекомендации по управлению эмоциями


class ComprehensiveAnalysisRequest(BaseModel):
    """Модель запроса для комплексного анализа"""
    user_message: str  # Сообщение пользователя с запросом
    portfolio_data: Optional[Dict] = None  # Опциональные данные портфеля
    context: Optional[str] = None  # Дополнительный контекст


class ComprehensiveAnalysisResponse(BaseModel):
    """Модель ответа для комплексного анализа"""
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


class TransactionExtractionRequest(BaseModel):
    """Модель запроса для извлечения транзакций"""
    user_message: str  # Сообщение пользователя с информацией о транзакциях
    context: Optional[str] = None  # Дополнительный контекст


class TransactionExtractionResponse(BaseModel):
    """Модель ответа для извлечения транзакций"""
    extraction_id: str
    extraction_date: str
    transactions: List[Dict]  # Список извлеченных транзакций
    extracted_info: Optional[Dict] = None  # Общая информация об извлеченных транзакциях
    analysis: Optional[str] = None  # Анализ извлеченных транзакций
    questions: Optional[List[str]] = None  # Вопросы для уточнения
    warnings: Optional[List[str]] = None  # Предупреждения
    extracted_parameters: Optional[Dict] = None  # Извлеченные параметры


class ChatRequest(BaseModel):
    """Модель запроса для чата с ИИ"""
    message: str
    context: Optional[str] = None  # Контекст (история расходов, баланс и т.д.)


class ChatResponse(BaseModel):
    """Модель ответа от ИИ"""
    response: str
    timestamp: str


class FriendlinessRequest(BaseModel):
    """Модель запроса для анализа доброты"""
    message: str  # Сообщение пользователя для анализа


class FriendlinessResponse(BaseModel):
    """Модель ответа для анализа доброты"""
    friendliness_score: float  # Оценка доброты от 0.0 до 1.0
    sentiment: str  # "positive", "neutral" или "negative"
    timestamp: str


class InsightRequest(BaseModel):
    """Модель запроса для получения инсайтов"""
    transactions: List[Dict]  # Список транзакций
    current_month: Optional[str] = None  # Текущий месяц для анализа


class InsightResponse(BaseModel):
    """Модель ответа с инсайтом"""
    insight: Optional[str] = None  # Текст инсайта
    category: Optional[str] = None  # Категория, к которой относится инсайт
    amount: Optional[float] = None  # Сумма по категории
    transaction_count: Optional[int] = None  # Количество транзакций по категории
    low_importance_count: Optional[int] = None  # Количество транзакций с низкой важностью
    low_importance_percent: Optional[float] = None  # Процент транзакций с низкой важностью
    previous_month_amount: Optional[float] = None  # Сумма по категории в предыдущем месяце
    percent_of_total: Optional[float] = None  # Процент от общих расходов текущего месяца
    timestamp: Optional[str] = None  # Временная метка


class ForecastRequest(BaseModel):
    """Модель запроса для прогнозирования"""
    transactions: List[Dict]  # Список транзакций пользователя
    user_message: str  # Сообщение пользователя с запросом на прогноз
    months: Optional[int] = 3  # Количество месяцев для прогноза


class ForecastResponse(BaseModel):
    """Модель ответа с прогнозом"""
    category: Optional[str] = None  # Категория для прогноза
    current_monthly: Optional[float] = None  # Текущие средние месячные расходы
    change_percent: Optional[float] = None  # Процент изменения
    new_monthly: Optional[float] = None  # Новые средние месячные расходы
    months: Optional[int] = None  # Количество месяцев прогноза
    monthly_forecast: Optional[List[Dict]] = None  # Прогноз по месяцам
    total_savings: Optional[float] = None  # Общая экономия за период
    description: Optional[str] = None  # Описание прогноза
    timestamp: Optional[str] = None  # Временная метка




# Базовые роуты
@app.get("/")
async def health_check() -> Dict[str, str]:
    """Health check эндпоинт"""
    return {
        "status": "healthy",
        "service": "AI Finance Assistant API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/mock/portfolio")
async def get_mock_portfolio_data() -> Dict:
    """
    Получить mock данные портфеля
    
    Возвращает тестовые данные портфеля для разработки и тестирования
    """
    return get_mock_portfolio()


@app.post("/analyze", response_model=PortfolioAnalysisResponse)
async def analyze_portfolio(request: PortfolioAnalysisRequest) -> PortfolioAnalysisResponse:
    """
    Анализ портфеля
    
    Принимает данные портфеля и возвращает анализ:
    - Оценка стоимости портфеля
    - Оценка рисков
    - Рекомендации по оптимизации
    
    Если portfolio_data не передан или use_mock_data=True, используются mock данные.
    """
    try:
        # Определяем, какие данные использовать
        if request.use_mock_data or not request.portfolio_data:
            portfolio_data = get_mock_portfolio()
            is_mock = True
        else:
            portfolio_data = request.portfolio_data
            is_mock = False
        
        # Вычисляем метрики портфеля
        metrics = calculate_portfolio_metrics(portfolio_data)
        
        # Генерируем рекомендации через AI с fallback
        ai_advice = generate_financial_advice_with_fallback(portfolio_data, request.analysis_type)
        
        # Извлекаем данные из ответа AI
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
        
        # Объединяем рекомендации от AI и базовые метрики
        all_recommendations = ai_recommendations + metrics.get("recommendations", [])
        
        # Генерируем ID анализа
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Формируем детали ответа
        details = {
            "analysis_type": request.analysis_type,
            "assets_count": metrics.get("assets_count", 0),
            "sectors_distribution": metrics.get("sectors_distribution", {}),
            "is_mock_data": is_mock,
            "ai_recommendations_count": len(ai_recommendations)
        }
        
        # Добавляем полные данные портфеля в детали (если не слишком большие)
        if is_mock or (isinstance(portfolio_data, dict) and len(str(portfolio_data)) < 10000):
            details["portfolio_data"] = portfolio_data
        
        return PortfolioAnalysisResponse(
            analysis_id=analysis_id,
            portfolio_value=metrics.get("portfolio_value", 0.0),
            risk_score=metrics.get("risk_score", 0.0),
            recommendations=all_recommendations[:10],
            analysis_date=datetime.now().isoformat(),
            details=details,
            detailed_analysis=detailed_analysis,
            risk_assessment=risk_assessment,
            questions=questions,
            next_steps=next_steps
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе портфеля: {str(e)}")


@app.post("/emotions", response_model=EmotionsAnalysisResponse)
async def analyze_emotions(request: EmotionsAnalysisRequest) -> EmotionsAnalysisResponse:
    """
    Анализ эмоций в тексте
    
    Анализирует эмоциональную окраску текста и возвращает:
    - Распределение эмоций
    - Доминирующую эмоцию
    - Общий сентимент-скор
    """
    try:
        # Анализ эмоций через AI с fallback на простой анализ
        result = analyze_emotions_with_fallback(request.text, request.context)
        
        # Извлекаем данные из ответа
        if isinstance(result, dict) and "emotions" in result:
            emotions = result["emotions"]
            analysis = result["analysis"]
            questions = result["questions"]
            recommendations = result.get("recommendations")
        else:
            emotions = result if isinstance(result, dict) else {}
            analysis = None
            questions = None
            recommendations = None
        
        # Определение доминирующей эмоции
        dominant_emotion = max(emotions, key=emotions.get) if emotions else "neutral"
        
        # Расчет сентимент-скора
        positive_emotions = emotions.get("joy", 0) + emotions.get("surprise", 0)
        negative_emotions = emotions.get("fear", 0) + emotions.get("anger", 0) + emotions.get("sadness", 0)
        sentiment_score = (positive_emotions - negative_emotions) / (positive_emotions + negative_emotions + 0.1) if (positive_emotions + negative_emotions) > 0 else 0.0
        
        return EmotionsAnalysisResponse(
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            sentiment_score=sentiment_score,
            analysis_date=datetime.now().isoformat(),
            analysis=analysis,
            questions=questions,
            recommendations=recommendations
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе эмоций: {str(e)}")


@app.post("/comprehensive-analysis", response_model=ComprehensiveAnalysisResponse)
async def comprehensive_analysis(request: ComprehensiveAnalysisRequest) -> ComprehensiveAnalysisResponse:
    """
    Комплексный анализ финансовой ситуации с учетом множества параметров
    
    Анализирует сообщение пользователя, извлекает параметры и предоставляет:
    - Комплексный анализ ситуации
    - Анализ финансовых целей
    - Оценку рисков
    - Эмоциональный анализ
    - Персонализированные рекомендации
    - Финансовый план
    """
    try:
        result = generate_comprehensive_advice_with_fallback(
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
        raise HTTPException(status_code=500, detail=f"Ошибка при комплексном анализе: {str(e)}")


@app.post("/extract-transactions", response_model=TransactionExtractionResponse)
async def extract_transactions(request: TransactionExtractionRequest) -> TransactionExtractionResponse:
    """
    Извлечение транзакций (расходов и доходов) из сообщения пользователя
    
    Анализирует сообщение пользователя и извлекает структурированную информацию о транзакциях:
    - Тип транзакции (доход/расход)
    - Сумма
    - Категория
    - Дата
    - Название/описание
    
    Примеры сообщений:
    - "Купил хлеб за 50 рублей и молоко за 80 рублей"
    - "Получил зарплату 85000 рублей"
    - "Вчера потратил 2000 на обед в ресторане"
    """
    try:
        result = extract_transactions_with_fallback(
            request.user_message,
            request.context
        )
        
        extraction_id = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return TransactionExtractionResponse(
            extraction_id=extraction_id,
            extraction_date=datetime.now().isoformat(),
            transactions=result.get("transactions", []),
            extracted_info=result.get("extracted_info"),
            analysis=result.get("analysis"),
            questions=result.get("questions"),
            warnings=result.get("warnings"),
            extracted_parameters=result.get("extracted_parameters")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при извлечении транзакций: {str(e)}")


class VoiceTranscriptionResponse(BaseModel):
    """Модель ответа для распознавания речи"""
    transcription_id: str
    transcription_date: str
    text: str
    confidence: Optional[float] = None
    error: Optional[str] = None


@app.post("/transcribe-voice", response_model=VoiceTranscriptionResponse)
async def transcribe_voice(
    audio: UploadFile = File(...),
    audio_format: Optional[str] = Form("wav")
) -> VoiceTranscriptionResponse:
    """
    Распознавание речи из голосового сообщения
    
    Принимает аудио файл и возвращает распознанный текст.
    После распознавания текст можно использовать для извлечения транзакций.
    
    Поддерживаемые форматы: wav, mp3, oggopus, opus, flac, pcm16
    """
    try:
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Пустой аудио файл")
        
        transcribed_text = transcribe_audio_with_fallback(audio_data, audio_format)
        
        if not transcribed_text:
            return VoiceTranscriptionResponse(
                transcription_id=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                transcription_date=datetime.now().isoformat(),
                text="",
                error="Не удалось распознать речь. Проверьте качество аудио и формат файла."
            )
        
        transcription_id = f"transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return VoiceTranscriptionResponse(
            transcription_id=transcription_id,
            transcription_date=datetime.now().isoformat(),
            text=transcribed_text,
            confidence=0.9
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при распознавании речи: {str(e)}")


@app.post("/transcribe-and-extract", response_model=Dict)
async def transcribe_and_extract(
    audio: UploadFile = File(...),
    audio_format: Optional[str] = Form("wav"),
    context: Optional[str] = Form(None)
) -> Dict:
    """
    Распознавание речи и автоматическое извлечение транзакций
    
    Комбинированный эндпоинт, который:
    1. Распознает речь из аудио
    2. Автоматически извлекает транзакции из распознанного текста
    
    Это удобно для голосового ввода в чате.
    """
    try:
        audio_data = await audio.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Пустой аудио файл")
        
        transcribed_text = transcribe_audio_with_fallback(audio_data, audio_format)
        
        if not transcribed_text:
            return {
                "success": False,
                "error": "Не удалось распознать речь",
                "transcription": "",
                "transactions": []
            }
        
        result = extract_transactions_with_fallback(transcribed_text, context)
        
        extraction_id = f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return {
            "success": True,
            "transcription": transcribed_text,
            "extraction_id": extraction_id,
            "extraction_date": datetime.now().isoformat(),
            "transactions": result.get("transactions", []),
            "extracted_info": result.get("extracted_info"),
            "analysis": result.get("analysis"),
            "questions": result.get("questions"),
            "warnings": result.get("warnings"),
            "extracted_parameters": result.get("extracted_parameters")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке голосового сообщения: {str(e)}")


@app.post("/analyze-friendliness", response_model=FriendlinessResponse)
async def analyze_friendliness(request: FriendlinessRequest) -> FriendlinessResponse:
    """
    Анализ доброты/дружелюбности сообщения пользователя
    
    Анализирует сообщение и возвращает оценку доброты от 0.0 до 1.0:
    - 0.0 - очень грубое, агрессивное сообщение
    - 0.5 - нейтральное сообщение
    - 1.0 - очень дружелюбное, вежливое сообщение
    """
    try:
        result = analyze_friendliness_with_fallback(request.message)
        
        score = result.get("friendliness_score", 0.5)
        sentiment = result.get("sentiment", "neutral")
        
        print(f"Friendliness endpoint returning: score={score}, sentiment={sentiment}")
        
        return FriendlinessResponse(
            friendliness_score=score,
            sentiment=sentiment,
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе доброты: {str(e)}")


@app.post("/insights", response_model=InsightResponse)
async def get_insights(request: InsightRequest) -> InsightResponse:
    """
    Получение персональных инсайтов на основе транзакций пользователя
    
    Анализирует паттерны в транзакциях и генерирует персональные рекомендации.
    Например: "Заметил, что вы несколько раз оценивали сыр как необязательную покупку.
    В этом месяце на сыр ушло 1200₽. Возможно, стоит попробовать альтернативный продукт или покупать реже?"
    """
    try:
        result = generate_insights_with_fallback(request.transactions, request.current_month)
        
        if result:
            return InsightResponse(
                insight=result.get("insight"),
                category=result.get("category"),
                amount=result.get("amount"),
                transaction_count=result.get("transaction_count"),
                low_importance_count=result.get("low_importance_count"),
                low_importance_percent=result.get("low_importance_percent"),
                previous_month_amount=result.get("previous_month_amount"),
                percent_of_total=result.get("percent_of_total"),
                timestamp=result.get("timestamp", datetime.now().isoformat())
            )
        else:
            return InsightResponse(
                insight=None,
                category=None,
                amount=None,
                transaction_count=None,
                low_importance_count=None,
                low_importance_percent=None,
                previous_month_amount=None,
                percent_of_total=None,
                timestamp=datetime.now().isoformat()
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при генерации инсайтов: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest) -> ChatResponse:
    """
    Чат с ИИ-ассистентом (Gemini)
    
    Отправляет сообщение пользователя в Gemini и возвращает ответ.
    Контекст может включать информацию о финансах пользователя.
    """
    try:
        # Формируем системный промпт для финансового ассистента
        system_context = """Ты - дружелюбный AI-ассистент по личным финансам. Твоё имя - Финансовый Помощник.

ВАЖНО: Отвечай на вопрос пользователя напрямую! Не начинай анализировать расходы, если тебя об этом не просят.

ЧТО ТЫ УМЕЕШЬ:
1. Вести обычный диалог и отвечать на вопросы
2. Помогать с финансовыми вопросами и давать советы
3. Анализировать расходы (только если пользователь просит)
4. Делать прогнозы трат (только если пользователь просит)
5. Отвечать на общие вопросы

КОГДА АНАЛИЗИРОВАТЬ РАСХОДЫ:
Делай анализ расходов ТОЛЬКО если пользователь явно просит:
- "проанализируй мои расходы"
- "где я могу сэкономить"
- "на что я трачу больше всего"
- "покажи статистику"
- вопросы про прогноз или симуляцию расходов

КОГДА НЕ АНАЛИЗИРОВАТЬ РАСХОДЫ:
- Приветствия ("привет", "здравствуй")
- Общие вопросы ("как дела", "что умеешь")
- Вопросы не связанные с анализом ("что такое инфляция", "как накопить")
- Благодарности ("спасибо")

ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:

Пользователь: "Привет"
Ответ: "Привет! Я твой финансовый помощник. Могу помочь с учётом расходов, анализом трат или ответить на вопросы о финансах. Чем могу помочь?"

Пользователь: "Что ты умеешь?"
Ответ: "Я могу помочь тебе с:
- Учётом доходов и расходов
- Анализом трат по категориям
- Прогнозом расходов
- Советами по экономии
- Ответами на финансовые вопросы
Просто напиши, что тебя интересует!"

Пользователь: "Проанализируй мои расходы"
Ответ: [здесь делаешь анализ на основе контекста]

ОГРАНИЧЕНИЯ:
- НЕ придумывай данные о расходах пользователя
- Если нет данных для анализа, скажи об этом
- НЕ давай юридических или налоговых советов

Отвечай на русском языке, дружелюбно и по делу."""
        
        # Добавляем контекст пользователя если есть
        full_message = request.message
        if request.context:
            full_message = f"""ДАННЫЕ ПОЛЬЗОВАТЕЛЯ (используй только если пользователь просит анализ):
{request.context}

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {request.message}

ВАЖНО: Отвечай на сообщение пользователя напрямую. Используй данные выше только если пользователь явно просит анализ расходов."""
        else:
            full_message = f"СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ: {request.message}"
        
        # Используем Gemini если доступен
        if GEMINI_AVAILABLE:
            try:
                token = get_access_token()
                if token:
                    result = chat_completion(token, f"{system_context}\n\n{full_message}")
                    
                    if 'error' not in result:
                        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', 'Не удалось получить ответ.')
                        return ChatResponse(
                            response=ai_response,
                            timestamp=datetime.now().isoformat()
                        )
            except Exception as e:
                print(f"Gemini API error: {e}")
        
        # Fallback на простые ответы
        message_lower = request.message.lower()
        
        if any(word in message_lower for word in ["привет", "здравствуй", "добрый день"]):
            response_text = "Привет! Я твой финансовый помощник. Могу помочь с учётом расходов, анализом трат или ответить на вопросы о финансах. Чем могу помочь?"
        elif any(word in message_lower for word in ["что умеешь", "помощь", "help"]):
            response_text = """Я могу помочь тебе с:
- Учётом доходов и расходов
- Анализом трат по категориям
- Прогнозом расходов
- Советами по экономии
- Ответами на финансовые вопросы
Просто напиши, что тебя интересует!"""
        else:
            response_text = "Для полноценной работы чата необходимо настроить AI интеграцию (например, Gemini). Сейчас доступны только базовые функции."
        
        return ChatResponse(
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка чата: {str(e)}")


# Дополнительные служебные эндпоинты
@app.get("/health")
async def health_check_legacy() -> Dict[str, str]:
    """Проверка здоровья приложения (legacy endpoint)"""
    return {
        "status": "healthy",
        "service": "AI Finance Assistant API"
    }


@app.get("/api/v1/status")
async def api_status() -> Dict[str, str]:
    """Статус API"""
    return {
        "api_version": "v1",
        "status": "operational"
    }


# Обработка ошибок
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Глобальный обработчик исключений"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc)
        }
    )


def main():
    """Запуск приложения"""
    import sys
    
    # Для Termux (Android) отключаем reload для стабильности
    is_termux = os.path.exists("/data/data/com.termux")
    reload_enabled = not is_termux
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",  # Принимает подключения со всех интерфейсов
        port=8000,
        reload=reload_enabled,  # Автоперезагрузка только на ПК
        log_level="info"
    )


if __name__ == "__main__":
    main()
