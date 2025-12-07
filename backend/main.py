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
from gigachat_integration import (
    analyze_emotions_with_fallback, 
    generate_financial_advice_with_fallback,
    generate_comprehensive_advice_with_fallback, 
    extract_transactions_with_fallback,
    transcribe_audio_with_fallback,
    analyze_friendliness_with_fallback,
    generate_insights_with_fallback,
    generate_forecast_with_fallback,
    get_access_token,
    chat_completion,
    GigaChatAIClient
)

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


# Хранение токена GigaChat (кэширование)
_gigachat_token: Optional[str] = None


def get_gigachat_token() -> Optional[str]:
    """Получить или обновить токен GigaChat"""
    global _gigachat_token
    if _gigachat_token is None:
        _gigachat_token = get_access_token()
    return _gigachat_token


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
        
        # Генерируем рекомендации через GigaChat с fallback
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
        # Анализ эмоций через GigaChat с fallback на простой анализ
        result = analyze_emotions_with_fallback(request.text, request.context)
        
        # Извлекаем данные из ответа
        if isinstance(result, dict) and "emotions" in result:
            emotions = result["emotions"]
            analysis = result.get("analysis")
            questions = result.get("questions")
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
        
        return FriendlinessResponse(
            friendliness_score=result.get("friendliness_score", 0.5),
            sentiment=result.get("sentiment", "neutral"),
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
    Чат с ИИ-ассистентом (GigaChat)
    
    Отправляет сообщение пользователя в GigaChat и возвращает ответ.
    Контекст может включать информацию о финансах пользователя.
    """
    try:
        token = get_gigachat_token()
        if not token:
            # Если токен не получен, возвращаем заглушку
            return ChatResponse(
                response="Извините, сервис временно недоступен. Попробуйте позже.",
                timestamp=datetime.now().isoformat()
            )
        
        # Формируем системный промпт для финансового ассистента
        system_context = """Ты - AI-ассистент по личным финансам внутри веб-приложения.

У тебя есть история расходов пользователя по месяцам и категориям (например: доставка еды, покупки, услуги).
Каждая транзакция содержит: date, amount, category.
Система уже посчитала для тебя агрегированные суммы по месяцам и категориям.

ТВОИ ЗАДАЧИ:

1. СИМУЛЯЦИЯ БУДУЩИХ РАСХОДОВ:
   Пользователь может задать вопрос вида:
   - "Что будет в январе, если я уменьшу траты на доставку на 30%?"
   - "Если я буду тратить на еду на 2000 рублей меньше каждый месяц, сколько сэкономлю за полгода?"
   - "Покажи прогноз на 3 месяца, если сократить развлечения на 25%"
   
   На вход ты получаешь:
   - Базовый сценарий (средние месячные траты по категориям за последние N месяцев из контекста)
   - Желаемые изменения (процент или фиксированная сумма по одной или нескольким категориям из вопроса пользователя)
   - Горизонт прогноза (количество месяцев из вопроса пользователя, если не указано - используй 1 месяц)
   
   Ты возвращаешь:
   - Прогнозируемые траты по месяцам в новом сценарии (покажи помесячно)
   - Общую сумму экономии за период
   - Короткое текстовое объяснение на понятном языке (2-4 предложения)
   
   Пример ответа:
   "Если уменьшить траты на доставку на 30%, то:
   - Январь: 35000 руб (было 40000, экономия 5000)
   - Февраль: 35000 руб (экономия 5000)
   - Март: 35000 руб (экономия 5000)
   Общая экономия за 3 месяца: 15000 руб.
   Вы сможете сэкономить 5000 рублей в месяц, отказавшись от части заказов доставки. Это составит 15% от ваших текущих расходов на эту категорию."

2. ПОИСК КАТЕГОРИЙ, КОТОРЫЕ ИМЕЕТ СМЫСЛ СОКРАТИТЬ:
   Если пользователь не предлагает сценарий сам, ты анализируешь его историю и:
   - Находишь категории с наибольшими расходами (топ-3)
   - Находишь категории, которые заметно выросли по сравнению со средним (например, на 20-30% и больше)
   - Предлагаешь 2-3 конкретных совета в формате:
     "Ты тратишь на доставку X ₽ в месяц (Y% всех расходов). Если снизить на 25%, ты сэкономишь Z ₽ за 3 месяца."
   
   Пример ответа:
   "Анализ ваших расходов показывает:
   1. Доставка еды: 12000 руб/мес (30% всех расходов). Если снизить на 25%, сэкономите 3000 руб/мес (9000 за 3 месяца).
   2. Развлечения: 8000 руб/мес (20% всех расходов), выросли на 35% по сравнению со средним. Если вернуться к среднему уровню, сэкономите 2800 руб/мес.
   3. Транспорт: 6000 руб/мес (15% всех расходов). Если оптимизировать на 20%, сэкономите 1200 руб/мес."

ОГРАНИЧЕНИЯ:
- НЕ придумывай фейковые данные, используй ТОЛЬКО те агрегаты и параметры сценария, которые тебе передал бэкенд в контексте
- Если данных мало для адекватного прогноза (например, только один месяц), явно напиши об этом и всё равно сделай простой линейный прогноз без сложной математики
- НЕ давай юридических, налоговых или инвестиционных советов
- Фокус ТОЛЬКО на экономии и перераспределении расходов
- Не давай финансовых или инвестиционных рекомендаций

ФОРМАТ ДАННЫХ:
В контексте могут быть предоставлены:
- Агрегированные суммы по месяцам и категориям
- Средние месячные траты по категориям
- История транзакций
Используй ТОЛЬКО эти данные для расчетов.

Отвечай на русском языке, кратко, конкретно, с числами и расчетами."""
        
        # Добавляем контекст пользователя если есть
        full_message = request.message
        if request.context:
            full_message = f"""КОНТЕКСТ ФИНАНСОВЫХ ДАННЫХ ПОЛЬЗОВАТЕЛЯ:
{request.context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {request.message}

ИНСТРУКЦИЯ: Используй данные из контекста выше для расчетов. Если в контексте есть агрегированные суммы по месяцам и категориям, используй их как базовый сценарий. Если есть история транзакций, можешь их проанализировать для поиска категорий для сокращения."""
        else:
            full_message = f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {request.message}\n\nПримечание: Для выполнения расчетов и симуляций нужны данные о транзакциях или агрегированные суммы по месяцам и категориям. Попроси пользователя предоставить эту информацию или используй данные из истории расходов."
        
        # Отправляем запрос в GigaChat
        result = chat_completion(token, f"{system_context}\n\n{full_message}")
        
        if 'error' in result:
            # Сбрасываем токен при ошибке авторизации
            global _gigachat_token
            _gigachat_token = None
            return ChatResponse(
                response="Произошла ошибка при обработке запроса. Попробуйте ещё раз.",
                timestamp=datetime.now().isoformat()
            )
        
        # Извлекаем ответ из результата
        ai_response = result.get('choices', [{}])[0].get('message', {}).get('content', 'Не удалось получить ответ.')
        
        return ChatResponse(
            response=ai_response,
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
