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
from gigachat_integration import analyze_emotions_with_fallback, generate_financial_advice_with_fallback

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
        
        # Генерируем рекомендации через YandexGPT с fallback
        ai_recommendations = generate_financial_advice_with_fallback(portfolio_data, request.analysis_type)
        
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
            details=details
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
        # Анализ эмоций через YandexGPT с fallback на простой анализ
        emotions = analyze_emotions_with_fallback(request.text, request.context)
        
        # Определение доминирующей эмоции
        dominant_emotion = max(emotions, key=emotions.get)
        
        # Расчет сентимент-скора
        positive_emotions = emotions.get("joy", 0) + emotions.get("surprise", 0)
        negative_emotions = emotions.get("fear", 0) + emotions.get("anger", 0) + emotions.get("sadness", 0)
        sentiment_score = (positive_emotions - negative_emotions) / (positive_emotions + negative_emotions + 0.1)
        
        return EmotionsAnalysisResponse(
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            sentiment_score=sentiment_score,
            analysis_date=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе эмоций: {str(e)}")


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
