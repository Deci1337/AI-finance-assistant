"""AI Service - GigaChat integration"""
import re
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path for gigachat_integration import
backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import GigaChat integration
try:
    from gigachat_integration import (
        chat_completion_for_chat as gigachat_chat_completion,
        get_access_token,
        is_available as gigachat_is_available
    )
    GIGACHAT_AVAILABLE = True
    print("GigaChat integration loaded successfully")
except ImportError as e:
    GIGACHAT_AVAILABLE = False
    print(f"Warning: GigaChat integration not available: {e}")


class AIService:
    """Service for AI-related operations"""
    
    @staticmethod
    def is_available() -> bool:
        """Check if AI service is available"""
        return GIGACHAT_AVAILABLE
    
    @staticmethod
    def analyze_emotions(text: str, context: Optional[str] = None) -> Dict:
        """Analyze emotions in text using GigaChat"""
        if GIGACHAT_AVAILABLE:
            try:
                token = get_access_token()
                if token:
                    system_prompt = """Ты - эксперт по анализу эмоций в тексте.

Твоя задача - определить эмоциональное состояние автора сообщения.

Проанализируй текст и определи интенсивность следующих эмоций (от 0.0 до 1.0):
- joy (радость)
- fear (страх)
- anger (злость, агрессия)
- sadness (грусть)
- surprise (удивление)
- neutral (нейтральность)

Сумма всех эмоций должна быть примерно равна 1.0.

Верни ответ ТОЛЬКО в формате JSON:
{
  "emotions": {
    "joy": число от 0.0 до 1.0,
    "fear": число от 0.0 до 1.0,
    "anger": число от 0.0 до 1.0,
    "sadness": число от 0.0 до 1.0,
    "surprise": число от 0.0 до 1.0,
    "neutral": число от 0.0 до 1.0
  }
}

НЕ добавляй никаких объяснений, только JSON."""

                    user_message = f"Проанализируй эмоции в этом сообщении: {text}"
                    if context:
                        user_message += f"\n\nКонтекст: {context}"
                    
                    result = gigachat_chat_completion(token, user_message, system_message=system_prompt)
                    
                    if 'error' not in result:
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        # Парсим JSON из ответа
                        try:
                            import json
                            import re
                            # Извлекаем JSON из ответа (может быть обернут в markdown или содержать markdown код блоки)
                            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                            json_matches = re.findall(json_pattern, content)
                            
                            for json_str in json_matches:
                                try:
                                    analysis = json.loads(json_str)
                                    if "emotions" in analysis:
                                        emotions = analysis.get("emotions", {})
                                        
                                        # Нормализуем значения
                                        total = sum(emotions.values()) if emotions else 1.0
                                        if total > 0:
                                            emotions = {k: v / total for k, v in emotions.items()}
                                        
                                        return {
                                            "emotions": emotions,
                                            "analysis": None,
                                            "questions": None
                                        }
                                except:
                                    continue
                        except Exception as e:
                            print(f"Error parsing emotions JSON: {e}")
            except Exception as e:
                print(f"Error analyzing emotions with GigaChat: {e}")
        
        # Fallback: простая эвристика
        text_lower = text.lower()
        emotions = {
            "joy": 0.0, "fear": 0.0, "anger": 0.0,
            "sadness": 0.0, "surprise": 0.0, "neutral": 0.5
        }
        
        # Простая эвристика на основе ключевых слов
        if any(word in text_lower for word in ['блять', 'сука', 'пиздец', 'хуйня', 'злой', 'злюсь', 'бесит']):
            emotions["anger"] = 0.6
            emotions["neutral"] = 0.4
        elif any(word in text_lower for word in ['спасибо', 'благодарю', 'отлично', 'хорошо', 'рад']):
            emotions["joy"] = 0.6
            emotions["neutral"] = 0.4
        elif any(word in text_lower for word in ['грустно', 'печально', 'плохо', 'проблема']):
            emotions["sadness"] = 0.5
            emotions["neutral"] = 0.5
        
        return {
            "emotions": emotions,
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
        """Analyze friendliness of message using GigaChat with emotion weights"""
        base_score = 0.5
        sentiment = "neutral"
        
        if GIGACHAT_AVAILABLE:
            try:
                token = get_access_token()
                if token:
                    # Сначала получаем базовый friendliness score
                    system_prompt = """Ты - эксперт по анализу тона и эмоций в тексте.

Твоя задача - определить уровень дружелюбности сообщения пользователя.

Оцени сообщение по шкале от 0.0 до 1.0:
- 0.0-0.2: очень грубое, агрессивное, враждебное сообщение с матом и оскорблениями
- 0.2-0.4: грубое, негативное сообщение с недовольством
- 0.4-0.6: нейтральное сообщение без выраженных эмоций
- 0.6-0.8: дружелюбное, вежливое сообщение
- 0.8-1.0: очень дружелюбное, позитивное, вежливое сообщение

Также определи общий sentiment:
- "positive" - позитивный, дружелюбный тон
- "negative" - негативный, агрессивный тон
- "neutral" - нейтральный тон

Верни ответ ТОЛЬКО в формате JSON:
{
  "friendliness_score": число от 0.0 до 1.0,
  "sentiment": "positive" или "negative" или "neutral"
}

НЕ добавляй никаких объяснений, только JSON."""

                    user_message = f"Проанализируй это сообщение: {text}"
                    
                    result = gigachat_chat_completion(token, user_message, system_message=system_prompt)
                    
                    if 'error' not in result:
                        content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                        
                        # Парсим JSON из ответа
                        try:
                            import json
                            import re
                            # Извлекаем JSON из ответа (может быть обернут в markdown)
                            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                            json_matches = re.findall(json_pattern, content)
                            
                            for json_str in json_matches:
                                try:
                                    analysis = json.loads(json_str)
                                    if "friendliness_score" in analysis or "sentiment" in analysis:
                                        base_score = float(analysis.get("friendliness_score", 0.5))
                                        sentiment = analysis.get("sentiment", "neutral")
                                        break
                                except:
                                    continue
                        except:
                            pass
                    
                    # Теперь получаем эмоции для взвешенного расчета
                    emotions_result = AIService.analyze_emotions(text)
                    emotions = emotions_result.get("emotions", {})
                    
                    # Веса эмоций для расчета позиции на линии от зла (0.0) к добру (1.0)
                    # Положительные веса сдвигают к добру, отрицательные - к злу
                    emotion_weights = {
                        "joy": 0.4,          # Радость сильно сдвигает к добру
                        "surprise": 0.1,     # Удивление немного к добру
                        "neutral": 0.0,      # Нейтральность не влияет
                        "sadness": -0.2,     # Грусть немного к злу
                        "fear": -0.15,       # Страх немного к злу
                        "anger": -0.5        # Злость сильно сдвигает к злу
                    }
                    
                    # Рассчитываем взвешенное смещение от базового score
                    emotion_offset = 0.0
                    for emotion, weight in emotion_weights.items():
                        emotion_value = emotions.get(emotion, 0.0)
                        emotion_offset += emotion_value * weight
                    
                    # Применяем смещение к базовому score
                    # Ограничиваем результат от 0.0 до 1.0
                    final_score = max(0.0, min(1.0, base_score + emotion_offset))
                    
                    return {
                        "friendliness_score": final_score,
                        "sentiment": sentiment,
                        "timestamp": datetime.now().isoformat(),
                        "base_score": base_score,
                        "emotion_offset": emotion_offset,
                        "emotions": emotions
                    }
            except Exception as e:
                print(f"Error analyzing friendliness with GigaChat: {e}")
        
        # Fallback: простая эвристика с учетом эмоций
        text_lower = text.lower()
        negative_words = ['блять', 'сука', 'пиздец', 'хуйня', 'ебанутый', 'говно', 'идиот', 'тупой']
        positive_words = ['спасибо', 'пожалуйста', 'благодарю', 'отлично', 'хорошо', 'помогите']
        
        negative_count = sum(1 for word in negative_words if word in text_lower)
        positive_count = sum(1 for word in positive_words if word in text_lower)
        
        if negative_count > positive_count:
            base_score = max(0.0, 0.5 - negative_count * 0.15)
            sentiment = "negative"
        elif positive_count > negative_count:
            base_score = min(1.0, 0.5 + positive_count * 0.15)
            sentiment = "positive"
        else:
            base_score = 0.5
            sentiment = "neutral"
        
        # Fallback эмоции для взвешивания
        emotions = {
            "joy": 0.0, "fear": 0.0, "anger": 0.0,
            "sadness": 0.0, "surprise": 0.0, "neutral": 1.0
        }
        
        if negative_count > 0:
            emotions["anger"] = min(1.0, negative_count * 0.3)
            emotions["neutral"] = 1.0 - emotions["anger"]
        elif positive_count > 0:
            emotions["joy"] = min(1.0, positive_count * 0.3)
            emotions["neutral"] = 1.0 - emotions["joy"]
        
        # Веса эмоций
        emotion_weights = {
            "joy": 0.4, "surprise": 0.1, "neutral": 0.0,
            "sadness": -0.2, "fear": -0.15, "anger": -0.5
        }
        
        emotion_offset = sum(emotions.get(emotion, 0.0) * weight 
                            for emotion, weight in emotion_weights.items())
        final_score = max(0.0, min(1.0, base_score + emotion_offset))
        
        return {
            "friendliness_score": final_score,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat(),
            "base_score": base_score,
            "emotion_offset": emotion_offset,
            "emotions": emotions
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
- НЕ придумывай фейковые данные, используй ТОЛЬКО те агрегаты и параметры сценария, которые тебе передал бэкенд в контексте
- Если данных мало для адекватного прогноза (например, только один месяц), явно напиши об этом и всё равно сделай простой линейный прогноз без сложной математики
- НЕ давай юридических, налоговых или инвестиционных советов
- Фокус ТОЛЬКО на экономии и перераспределении расходов
- Не давай финансовых или инвестиционных рекомендаций
- НЕ придумывай данные о расходах пользователя
- Если нет данных для анализа, скажи об этом
- НЕ давай юридических или налоговых советов

ФОРМАТ ДАННЫХ:
В контексте могут быть предоставлены:
- Агрегированные суммы по месяцам и категориям
- Средние месячные траты по категориям
- История транзакций
Используй ТОЛЬКО эти данные для расчетов.

Отвечай на русском языке, кратко, конкретно, с числами и расчетами."""
        
        if context:
            full_message = f"""КОНТЕКСТ ФИНАНСОВЫХ ДАННЫХ ПОЛЬЗОВАТЕЛЯ:
{context}

ВОПРОС ПОЛЬЗОВАТЕЛЯ: {message}

ИНСТРУКЦИЯ: Используй данные из контекста выше для расчетов. Если в контексте есть агрегированные суммы по месяцам и категориям, используй их как базовый сценарий. Если есть история транзакций, можешь их проанализировать для поиска категорий для сокращения.
ВАЖНО: Отвечай на сообщение пользователя напрямую. Используй данные выше только если пользователь явно просит анализ расходов."""
        else:
            full_message = f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {message}\n\nПримечание: Для выполнения расчетов и симуляций нужны данные о транзакциях или агрегированные суммы по месяцам и категориям. Попроси пользователя предоставить эту информацию или используй данные из истории расходов."
        
        # Use GigaChat as primary model
        if GIGACHAT_AVAILABLE:
            try:
                token = get_access_token()
                if token:
                    result = gigachat_chat_completion(token, full_message, system_message=system_context)
                    if 'error' not in result:
                        return result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    else:
                        error_type = result.get('error', '')
                        error_message = result.get('message', 'Неизвестная ошибка')
                        print(f"GigaChat API returned error: {error_type} - {error_message}")
                        
                        if error_type == 'rate_limit':
                            return "Превышен лимит запросов GigaChat API. Подождите немного и попробуйте снова."
                        elif error_type == 'unauthorized':
                            return "Ошибка авторизации: неверные учетные данные GigaChat API. Проверьте настройки."
                        elif error_type == 'auth_failed':
                            return "Не удалось получить токен GigaChat API. Проверьте учетные данные."
                        elif error_type == 'timeout':
                            return "Таймаут при обращении к GigaChat API. Попробуйте позже."
                        else:
                            return f"Ошибка GigaChat API: {error_message}"
            except Exception as e:
                print(f"GigaChat API error: {e}")
                return f"Ошибка при обращении к GigaChat API: {str(e)}"
        
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
            return "Для полноценной работы чата необходимо настроить GigaChat интеграцию. Сейчас доступны только базовые функции."

