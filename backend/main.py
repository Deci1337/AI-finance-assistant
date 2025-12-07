"""
AI Finance Assistant - Backend API
FastAPI application for financial data processing and analysis
"""

from fastapi import FastAPI, HTTPException
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
    get_access_token,
    chat_completion
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
        system_context = """Ты - персональный финансовый ассистент. Твоя задача:
- Помогать пользователю управлять финансами
- Давать советы по бюджетированию и экономии
- Анализировать расходы и доходы
- Отвечать на вопросы о финансах
Отвечай кратко, по делу, на русском языке."""
        
        # Добавляем контекст пользователя если есть
        full_message = request.message
        if request.context:
            full_message = f"Контекст финансов пользователя: {request.context}\n\nВопрос: {request.message}"
        
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
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Автоперезагрузка при изменении кода
        log_level="info"
    )


if __name__ == "__main__":
    main()
