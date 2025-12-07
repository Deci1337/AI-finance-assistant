"""
GigaChat Integration Module
Модуль для работы с GigaChat API для анализа эмоций и генерации финансовых советов
"""

import requests
import urllib3
import json
import re
import base64
from typing import Dict, List, Optional
from datetime import datetime
from io import BytesIO

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Приоритет моделей: базовая GigaChat как основная (экономия токенов), Pro как fallback
# Примечание: GigaChat-Lite не существует в API, используем базовую GigaChat
PREFERRED_MODELS = ["GigaChat", "GigaChat-Plus", "GigaChat-Pro"]
MODEL = "GigaChat"  # По умолчанию используем базовую GigaChat как основную модель
SALUTE_SPEECH_URL = "https://smartspeech.sber.ru/rest/v1/speech:recognize"

# Кэш для проверенных моделей
_available_model_cache = None


def get_access_token():
    """Получение access token для GigaChat API"""
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    payload = {'scope': 'GIGACHAT_API_PERS'}
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'e1cda52c-b57a-477c-a65a-d9f896176e6d',
        'Authorization': 'Basic MDE5YWY3ZDktNTc4OC03MjVkLTliMGMtOWFhY2IzOTk3OTU2OjYzZTY1NTkzLTg3NDUtNGM1ZS05M2YwLTFlZDU1YTcwZGY1Mw=='
    }
    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None


def get_models(access_token):
    """Получение списка доступных моделей GigaChat"""
    url = "https://gigachat.devices.sberbank.ru/api/v1/models"
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.request("GET", url, headers=headers, verify=False)
    return response.text


def detect_available_model() -> str:
    """
    Автоматическое определение доступной модели GigaChat
    
    Пробует модели в порядке приоритета и возвращает первую доступную.
    Кэширует результат для оптимизации.
    
    Returns:
        Название доступной модели или "GigaChat-Pro" по умолчанию
    """
    global _available_model_cache
    
    # Используем кэш, если модель уже определена
    if _available_model_cache is not None:
        return _available_model_cache
    
    token = get_access_token()
    if not token:
        print("Warning: Cannot get access token, using default model GigaChat")
        _available_model_cache = "GigaChat"
        return _available_model_cache
    
    # Пробуем каждую модель из списка приоритетов
    for model_name in PREFERRED_MODELS:
        try:
            # Простой тестовый запрос для проверки доступности модели
            test_response = chat_completion(token, "тест", model=model_name, max_tokens=10)
            
            if 'error' in test_response:
                error_code = test_response.get('error')
                error_msg = test_response.get('message', '')
                
                # Если модель не найдена (404), пробуем следующую
                if error_code == 404 or "No such model" in str(error_msg):
                    print(f"Model {model_name} not available, trying next...")
                    continue
                # Если ошибка оплаты (402) для базовой модели, пробуем следующую как fallback
                # Если ошибка для последней модели, используем её (возможно, токены закончатся позже)
                elif error_code == 402:
                    # Если это не последняя модель в списке, пробуем следующую
                    if model_name != PREFERRED_MODELS[-1]:
                        print(f"Warning: Payment required for {model_name}, trying next model as fallback...")
                        continue  # Пробуем следующую модель
                    else:
                        print(f"Warning: Payment required for {model_name}, but model exists")
                        _available_model_cache = model_name
                        return model_name
                else:
                    # Другие ошибки - пробуем следующую модель
                    continue
            else:
                # Модель работает!
                print(f"✅ Using model: {model_name}")
                _available_model_cache = model_name
                return model_name
                
        except Exception as e:
            print(f"Error testing model {model_name}: {str(e)}")
            continue
    
    # Если ни одна модель не работает, используем базовую GigaChat по умолчанию (основная модель)
    print("Warning: Could not detect available model, using GigaChat as default")
    _available_model_cache = "GigaChat"
    return _available_model_cache


def chat_completion(access_token, message, model=None, temperature=0.7, max_tokens=2000):
    """
    Выполнение запроса к GigaChat API
    
    Args:
        access_token: Токен доступа
        message: Сообщение для отправки
        model: Название модели (если None, используется автоматически определенная)
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        
    Returns:
        Ответ от API или словарь с ошибкой
    """
    # Если модель не указана, используем автоматически определенную
    if model is None:
        model = detect_available_model()
    
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    payload = {
        'model': model,
        'messages': [
            {
                'role': 'user',
                'content': message
            }
        ],
        'temperature': temperature,
        'max_tokens': max_tokens
    }
    
    try:
        response = requests.request("POST", url, headers=headers, json=payload, verify=False, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_message = error_json.get('message', error_text)
            except:
                error_message = error_text
            
            return {
                'error': response.status_code,
                'message': error_message,
                'model_used': model
            }
    except requests.exceptions.Timeout:
        return {'error': 'timeout', 'message': 'Request timeout', 'model_used': model}
    except Exception as e:
        return {'error': 'exception', 'message': str(e), 'model_used': model}


def transcribe_audio_salute_speech(access_token: str, audio_data: bytes, audio_format: str = "pcm16") -> Optional[str]:
    """
    Распознавание речи через SaluteSpeech API
    
    Args:
        access_token: Токен доступа GigaChat
        audio_data: Байты аудио файла
        audio_format: Формат аудио (pcm16, oggopus, opus, mp3, wav, flac, alaw, mulaw)
        
    Returns:
        Распознанный текст или None
    """
    try:
        url = SALUTE_SPEECH_URL
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': f'audio/{audio_format}'
        }
        
        response = requests.post(url, headers=headers, data=audio_data, verify=False, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                return result['result']
            elif 'chunks' in result:
                return ' '.join([chunk.get('alternatives', [{}])[0].get('text', '') for chunk in result['chunks']])
        else:
            print(f"SaluteSpeech API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"SaluteSpeech transcription error: {str(e)}")
        return None


def transcribe_audio_gigachat(access_token: str, audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
    """
    Распознавание речи через GigaChat API (если поддерживается)
    
    Args:
        access_token: Токен доступа GigaChat
        audio_data: Байты аудио файла
        audio_format: Формат аудио
        
    Returns:
        Распознанный текст или None
    """
    try:
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        payload = {
            'model': MODEL,
            'messages': [
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'audio',
                            'audio': {
                                'data': audio_base64,
                                'format': audio_format
                            }
                        }
                    ]
                }
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0].get('message', {}).get('content', '')
        else:
            return transcribe_audio_salute_speech(access_token, audio_data, audio_format)
    except Exception as e:
        print(f"GigaChat audio transcription error: {str(e)}")
        return transcribe_audio_salute_speech(access_token, audio_data, audio_format)


def transcribe_audio_with_fallback(audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
    """
    Распознавание речи с fallback на разные методы
    
    Args:
        audio_data: Байты аудио файла
        audio_format: Формат аудио
        
    Returns:
        Распознанный текст или None
    """
    try:
        token = get_access_token()
        if not token:
            return None
        
        result = transcribe_audio_gigachat(token, audio_data, audio_format)
        if result:
            return result
        
        result = transcribe_audio_salute_speech(token, audio_data, audio_format)
        return result
    except Exception as e:
        print(f"Audio transcription error: {str(e)}")
        return None


class GigaChatAIClient:
    """Клиент для работы с GigaChat API для анализа эмоций и финансовых советов"""
    
    def __init__(self):
        # Автоматически определяем доступную модель при создании клиента
        self.model = detect_available_model()
    
    def transcribe_audio(self, audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
        """
        Распознавание речи из аудио данных
        
        Args:
            audio_data: Байты аудио файла
            audio_format: Формат аудио (wav, mp3, oggopus и т.д.)
            
        Returns:
            Распознанный текст или None
        """
        if not self._is_available():
            return None
        
        return transcribe_audio_with_fallback(audio_data, audio_format)
        
    def _is_available(self) -> bool:
        """Проверка доступности GigaChat API"""
        try:
            token = get_access_token()
            return token is not None
        except Exception:
            return False
    
    def analyze_emotions(self, text: str, context: Optional[str] = None) -> Optional[Dict]:
        """
        Анализ эмоций в тексте через GigaChat с детальным анализом и вопросами
        
        Args:
            text: Текст для анализа
            context: Дополнительный контекст
            
        Returns:
            Словарь с эмоциями, анализом и вопросами или None
        """
        if not self._is_available():
            return None
        
        extracted_params = self._extract_parameters_from_message(text)
        params_summary = self._format_extracted_parameters(extracted_params)
        context_part = f"\nКонтекст: {context}" if context else ""
        
        prompt = f"""Ты опытный психолог и финансовый консультант. Проанализируй эмоциональное состояние пользователя на основе его текста, учитывая извлеченные параметры.

Текст пользователя: {text}

ИЗВЛЕЧЕННЫЕ ПАРАМЕТРЫ:
{params_summary}
{context_part}

Проведи глубокий анализ эмоций, учитывая:
- Финансовые цели и приоритеты пользователя
- Упоминаемые суммы и временные рамки
- Уровень опыта и знаний
- Текущую финансовую ситуацию
- Ограничения и предпочтения

Верни ответ в формате JSON:
{{
    "emotions": {{
        "joy": число от 0.0 до 1.0,
        "fear": число от 0.0 до 1.0,
        "anger": число от 0.0 до 1.0,
        "sadness": число от 0.0 до 1.0,
        "surprise": число от 0.0 до 1.0,
        "neutral": число от 0.0 до 1.0
    }},
    "analysis": "детальное описание эмоционального состояния (3-4 предложения), что может вызывать эти эмоции, как они связаны с финансовой ситуацией, учитывая извлеченные параметры",
    "questions": ["наводящий вопрос 1 с учетом контекста", "наводящий вопрос 2 с учетом контекста", "наводящий вопрос 3 с учетом контекста"],
    "recommendations": "конкретные рекомендации по управлению эмоциями в контексте финансов (3-4 предложения), учитывающие финансовые цели и ситуацию пользователя"
}}

Сумма всех значений в emotions должна быть примерно равна 1.0. Вопросы должны быть открытыми и помогать пользователю лучше понять свою ситуацию с учетом его целей и ограничений."""
        
        try:
            token = get_access_token()
            if not token:
                return None
                
            response = chat_completion(token, prompt, model=self.model, temperature=0.8, max_tokens=2000)
            
            if 'error' in response:
                return None
                
            if 'choices' in response and len(response['choices']) > 0:
                text_response = response['choices'][0].get('message', {}).get('content', '')
                json_match = self._extract_json(text_response)
                if json_match:
                    result = json.loads(json_match)
                    if 'emotions' in result:
                        result['emotions'] = self._normalize_emotions(result['emotions'])
                    return result
        except Exception as e:
            print(f"GigaChat emotions analysis error: {str(e)}")
        
        return None
    
    def generate_comprehensive_advice(self, user_message: str, portfolio_data: Optional[Dict] = None, 
                                      context: Optional[str] = None) -> Optional[Dict]:
        """
        Генерация комплексных финансовых советов с учетом множества параметров из сообщения пользователя
        
        Args:
            user_message: Сообщение пользователя с запросом
            portfolio_data: Опциональные данные портфеля
            context: Дополнительный контекст
            
        Returns:
            Словарь с комплексным анализом и рекомендациями или None
        """
        if not self._is_available():
            return None
        
        extracted_params = self._extract_parameters_from_message(user_message)
        portfolio_summary = self._format_portfolio_summary(portfolio_data) if portfolio_data else "Данные портфеля не предоставлены"
        context_part = f"\nДополнительный контекст: {context}" if context else ""
        
        params_summary = self._format_extracted_parameters(extracted_params)
        
        prompt = f"""Ты опытный финансовый консультант и психолог с глубоким пониманием инвестиций, управления финансами и эмоциональных аспектов финансовых решений. 

Твоя задача - провести комплексный анализ запроса пользователя и предоставить персонализированные рекомендации, учитывая ВСЕ извлеченные параметры.

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ:
{user_message}

ИЗВЛЕЧЕННЫЕ ПАРАМЕТРЫ ИЗ СООБЩЕНИЯ:
{params_summary}

ДАННЫЕ ПОРТФЕЛЯ (если доступны):
{portfolio_summary}
{context_part}

ИНСТРУКЦИИ ДЛЯ АНАЛИЗА:

1. ФИНАНСОВЫЕ ЦЕЛИ:
   - Определи приоритетные цели пользователя (накопление, инвестиции, покупка, погашение долга и т.д.)
   - Учти временные рамки (краткосрочные, среднесрочные, долгосрочные)
   - Предложи конкретные шаги для достижения каждой цели

2. ТОЛЕРАНТНОСТЬ К РИСКУ:
   - Учти указанный уровень риска (консервативный, умеренный, агрессивный)
   - Если не указан, определи его на основе сообщения и эмоционального состояния
   - Адаптируй рекомендации под уровень риска

3. ЭМОЦИОНАЛЬНОЕ СОСТОЯНИЕ:
   - Проанализируй эмоциональную окраску сообщения
   - Учти влияние эмоций на финансовые решения
   - Предложи способы управления эмоциями в контексте финансов

4. ФИНАНСОВАЯ СИТУАЦИЯ:
   - Оцени текущую финансовую ситуацию пользователя
   - Учти ограничения (бюджетные, временные, правовые)
   - Предложи решения с учетом реальных возможностей

5. ОПЫТ И ЗНАНИЯ:
   - Адаптируй язык и сложность рекомендаций под уровень опыта
   - Для новичков: объясняй простым языком, давай базовые советы
   - Для опытных: можешь использовать профессиональную терминологию

6. КАТЕГОРИИ И ПРИОРИТЕТЫ:
   - Учти упомянутые категории трат/инвестиций
   - Расставь приоритеты в рекомендациях
   - Предложи оптимизацию по категориям

7. СУММЫ И РЕСУРСЫ:
   - Учти упомянутые суммы денег
   - Предложи конкретные суммы для инвестиций/трат
   - Рассчитай реалистичные планы с учетом доступных ресурсов

Верни ответ в формате JSON:
{{
    "comprehensive_analysis": "развернутый анализ ситуации пользователя (4-5 предложений), учитывающий все извлеченные параметры",
    "financial_goals_analysis": {{
        "identified_goals": ["цель 1", "цель 2"],
        "prioritized_goals": ["приоритетная цель 1", "приоритетная цель 2"],
        "timeframes": {{
            "short_term": "краткосрочные цели и действия",
            "medium_term": "среднесрочные цели и действия",
            "long_term": "долгосрочные цели и действия"
        }}
    }},
    "risk_assessment": {{
        "detected_risk_tolerance": "консервативный/умеренный/агрессивный",
        "risk_analysis": "анализ толерантности к риску (2-3 предложения)",
        "recommended_risk_level": "рекомендуемый уровень риска с обоснованием"
    }},
    "emotional_analysis": {{
        "detected_emotions": ["эмоция 1", "эмоция 2"],
        "emotional_impact": "влияние эмоций на финансовые решения (2-3 предложения)",
        "emotional_management": "рекомендации по управлению эмоциями в финансовом контексте"
    }},
    "personalized_recommendations": [
        {{
            "category": "категория рекомендации",
            "priority": "высокий/средний/низкий",
            "recommendation": "конкретная рекомендация",
            "action_steps": ["шаг 1", "шаг 2", "шаг 3"],
            "expected_outcome": "ожидаемый результат"
        }}
    ],
    "financial_plan": {{
        "current_situation": "оценка текущей ситуации (2-3 предложения)",
        "recommended_actions": [
            {{
                "action": "конкретное действие",
                "timeline": "временные рамки",
                "amount": "рекомендуемая сумма (если применимо)",
                "rationale": "обоснование"
            }}
        ],
        "next_steps": "конкретные следующие шаги (3-4 предложения)"
    }},
    "questions_to_clarify": [
        "уточняющий вопрос 1",
        "уточняющий вопрос 2",
        "уточняющий вопрос 3"
    ],
    "warnings_and_considerations": [
        "важное предупреждение или соображение 1",
        "важное предупреждение или соображение 2"
    ]
}}

ВАЖНО:
- Учитывай ВСЕ извлеченные параметры, даже если они неявно выражены
- Будь конкретным и практичным в рекомендациях
- Адаптируй ответ под уровень опыта пользователя
- Учитывай эмоциональное состояние и предлагай способы его улучшения
- Предлагай реалистичные и достижимые цели
- Если информации недостаточно, задавай уточняющие вопросы
- Всегда учитывай ограничения пользователя"""
        
        try:
            token = get_access_token()
            if not token:
                return None
                
            response = chat_completion(token, prompt, model=self.model, temperature=0.7, max_tokens=4000)
            
            if 'error' in response:
                return None
                
            if 'choices' in response and len(response['choices']) > 0:
                text_response = response['choices'][0].get('message', {}).get('content', '')
                json_match = self._extract_json(text_response)
                if json_match:
                    result = json.loads(json_match)
                    if isinstance(result, dict):
                        result['extracted_parameters'] = extracted_params
                        return result
        except Exception as e:
            print(f"GigaChat comprehensive advice error: {str(e)}")
        
        return None
    
    def _format_extracted_parameters(self, params: Dict) -> str:
        """Форматирование извлеченных параметров для промпта"""
        lines = []
        
        if params.get("amounts"):
            lines.append(f"Суммы: {', '.join(params['amounts'])}")
        
        if params.get("timeframes"):
            lines.append(f"Временные рамки: {', '.join(params['timeframes'])}")
        
        if params.get("goals"):
            lines.append(f"Финансовые цели: {', '.join(params['goals'])}")
        
        if params.get("risk_tolerance"):
            lines.append(f"Толерантность к риску: {params['risk_tolerance']}")
        
        if params.get("categories"):
            lines.append(f"Категории: {', '.join(params['categories'])}")
        
        if params.get("priorities"):
            lines.append(f"Приоритеты: {', '.join(params['priorities'])}")
        
        if params.get("constraints"):
            lines.append(f"Ограничения: {', '.join(params['constraints'])}")
        
        if params.get("experience_level"):
            lines.append(f"Уровень опыта: {params['experience_level']}")
        
        if params.get("emotional_state"):
            lines.append(f"Эмоциональное состояние: {params['emotional_state']}")
        
        if params.get("financial_situation"):
            lines.append(f"Финансовая ситуация: {params['financial_situation']}")
        
        if not lines:
            return "Параметры не были явно указаны в сообщении. Проанализируй сообщение и определи их самостоятельно."
        
        return "\n".join(lines)
    
    def extract_transactions(self, user_message: str, context: Optional[str] = None) -> Optional[Dict]:
        """
        Извлечение транзакций (расходов и доходов) из сообщения пользователя через GigaChat
        
        Args:
            user_message: Сообщение пользователя с информацией о транзакциях
            context: Дополнительный контекст (например, история транзакций)
            
        Returns:
            Словарь с извлеченными транзакциями и анализом или None
        """
        if not self._is_available():
            return None
        
        extracted_params = self._extract_parameters_from_message(user_message)
        params_summary = self._format_extracted_parameters(extracted_params)
        context_part = f"\nДополнительный контекст: {context}" if context else ""
        
        prompt = f"""Ты опытный финансовый аналитик. Твоя задача - извлечь из сообщения пользователя всю информацию о транзакциях (расходах и доходах) и структурировать её.

СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ:
{user_message}

ИЗВЛЕЧЕННЫЕ ПАРАМЕТРЫ:
{params_summary}
{context_part}

ИНСТРУКЦИИ:

1. ИЗВЛЕЧЕНИЕ ТРАНЗАКЦИЙ:
   - Найди ВСЕ упоминания расходов и доходов в сообщении
   - Определи тип каждой транзакции (доход или расход)
   - Извлеки сумму (в рублях, долларах, евро и т.д., конвертируй в рубли если нужно)
   - Определи категорию транзакции (еда, транспорт, работа, развлечения, здоровье, покупки и т.д.)
   - Извлеки название/описание транзакции
   - Определи дату транзакции (если указана, иначе используй сегодняшнюю дату)
   - Если дата указана словами ("вчера", "неделю назад", "15 января"), определи точную дату

2. КАТЕГОРИИ:
   Используй следующие категории:
   - Доходы: Work, Freelance, Investment, Gift, Other
   - Расходы: Food, Transport, Entertainment, Health, Shopping, Housing, Education, Bills, Other

3. ОБРАБОТКА НЕОДНОЗНАЧНОСТЕЙ:
   - Если тип транзакции неясен, определи его по контексту (например, "купил" = расход, "получил" = доход)
   - Если сумма не указана точно, попробуй извлечь из контекста или укажи null
   - Если категория неясна, используй "Other"

4. ДЕТАЛЬНЫЙ ФИНАНСОВЫЙ АНАЛИЗ (ОБЯЗАТЕЛЬНО):
   В поле "analysis" ты ДОЛЖЕН предоставить развернутый финансовый анализ, включающий:
   - Общую оценку транзакций: сумма, количество, типы (доходы/расходы), их соотношение
   - Анализ категорий: какие категории преобладают, почему это важно, какие тенденции наблюдаются
   - Финансовые тренды: если есть несколько транзакций или контекст, выяви паттерны и тренды
   - Конкретные рекомендации: как можно оптимизировать расходы, где сэкономить, что улучшить
   - Предупреждения о рисках: превышение бюджета, необычные или крупные расходы, потенциальные проблемы
   - Практические советы: что делать дальше, на что обратить внимание, как лучше управлять финансами
   - Прогноз и планирование: как эти транзакции влияют на будущее финансовое состояние, что учесть
   
   Анализ должен быть:
   - Развернутым (минимум 8-10 предложений, желательно больше)
   - Конкретным и практичным (не общие фразы, а конкретные рекомендации)
   - Полезным (пользователь должен получить ценную информацию)
   - Структурированным (можно использовать нумерацию или разделы для удобства чтения)

5. ФОРМАТ ОТВЕТА:
   Верни ответ в формате JSON:
   {{
       "transactions": [
           {{
               "type": "income" или "expense",
               "title": "название транзакции",
               "amount": число (сумма в рублях),
               "category": "категория",
               "date": "YYYY-MM-DD" (дата в формате ISO),
               "description": "описание или дополнительные детали (если есть)",
               "confidence": число от 0.0 до 1.0 (уверенность в извлечении данных)
           }}
       ],
       "extracted_info": {{
           "total_income": сумма всех доходов,
           "total_expense": сумма всех расходов,
           "transactions_count": количество транзакций,
           "date_range": {{
               "earliest": "самая ранняя дата",
               "latest": "самая поздняя дата"
           }}
       }},
       "analysis": "развернутый финансовый анализ согласно инструкциям выше (минимум 8-10 предложений)",
       "questions": ["вопросы для уточнения, если информации недостаточно"],
       "warnings": ["предупреждения о неоднозначностях или проблемах"]
   }}

ВАЖНО:
- Извлекай ВСЕ транзакции из сообщения, даже если их несколько
- Если пользователь говорит "купил хлеб за 50 рублей и молоко за 80", это 2 транзакции
- Если пользователь говорит "трачу на еду 5000 в месяц", это одна транзакция с суммой 5000
- Будь точным в извлечении сумм и дат
- Если информации недостаточно, задавай уточняющие вопросы"""
        
        try:
            token = get_access_token()
            if not token:
                print("GigaChat transaction extraction: Cannot get access token")
                return None
                
            response = chat_completion(token, prompt, model=self.model, temperature=0.7, max_tokens=6000)
            
            if 'error' in response:
                error_code = response.get('error')
                error_msg = response.get('message', '')
                model_used = response.get('model_used', self.model)
                
                # Если модель не найдена, пробуем другую модель
                if error_code == 404 or "No such model" in str(error_msg):
                    print(f"Model {model_used} not available, trying fallback...")
                    # Сбрасываем кэш и пробуем другую модель
                    global _available_model_cache
                    _available_model_cache = None
                    self.model = detect_available_model()
                    
                    # Повторяем запрос с новой моделью
                    if self.model != model_used:
                        print(f"Retrying with model: {self.model}")
                        response = chat_completion(token, prompt, model=self.model, temperature=0.7, max_tokens=6000)
                        if 'error' in response:
                            print(f"Fallback model also failed: {response.get('message', '')}")
                            return None
                    else:
                        print("No alternative model available")
                        return None
                elif error_code == 402:
                    print(f"Payment required for model {model_used}. Using fallback method.")
                    # При ошибке оплаты возвращаем None, чтобы использовался fallback метод
                    return None
                else:
                    print(f"GigaChat API error {error_code}: {error_msg}")
                    return None
                
            if 'choices' in response and len(response['choices']) > 0:
                text_response = response['choices'][0].get('message', {}).get('content', '')
                
                # Пробуем извлечь JSON несколько раз с разными методами
                json_match = self._extract_json(text_response)
                
                # Если не получилось с первого раза, пробуем более агрессивное извлечение
                if not json_match:
                    # Пробуем найти JSON, который может быть в тексте с дополнительным контекстом
                    json_match = self._extract_json_aggressive(text_response)
                
                if json_match:
                    try:
                        result = json.loads(json_match)
                        if isinstance(result, dict):
                            # Если есть transactions, используем их
                            if 'transactions' in result:
                                result['extracted_parameters'] = extracted_params
                                # Проверяем, что анализ достаточно развернутый
                                analysis = result.get('analysis', '')
                                if not analysis or len(analysis) < 500:
                                    # Если анализ слишком короткий, извлекаем его из текста ответа или генерируем
                                    if len(text_response) > len(analysis):
                                        # Используем весь текст ответа как анализ, если он длиннее
                                        result['analysis'] = self._extract_analysis_from_text(text_response, result.get('transactions', []))
                                    else:
                                        # Генерируем анализ на основе транзакций
                                        result['analysis'] = self._generate_analysis_from_transactions(result.get('transactions', []), result.get('extracted_info', {}))
                                print(f"✅ Successfully extracted {len(result.get('transactions', []))} transactions using model {self.model}")
                                return result
                            # Если нет transactions, но есть другие данные, пробуем создать структуру
                            elif 'extracted_info' in result or 'analysis' in result:
                                print(f"Response missing 'transactions' key, but has other data. Attempting to extract from text...")
                                # Пробуем извлечь транзакции из текста ответа
                                transactions_from_text = self._extract_transactions_from_text(text_response)
                                if transactions_from_text:
                                    result['transactions'] = transactions_from_text
                                    result['extracted_parameters'] = extracted_params
                                    print(f"✅ Extracted {len(transactions_from_text)} transactions from text using model {self.model}")
                                    return result
                            print(f"Invalid response format: missing 'transactions' key")
                        else:
                            print(f"Invalid response format: result is not a dict")
                            # Пробуем извлечь транзакции из текста ответа
                            transactions_from_text = self._extract_transactions_from_text(text_response)
                            if transactions_from_text:
                                result = {
                                    "transactions": transactions_from_text,
                                    "extracted_info": {
                                        "total_income": sum(t.get('amount', 0) for t in transactions_from_text if t.get('type') == 'income' and t.get('amount')),
                                        "total_expense": sum(t.get('amount', 0) for t in transactions_from_text if t.get('type') == 'expense' and t.get('amount')),
                                        "transactions_count": len(transactions_from_text),
                                        "date_range": {
                                            "earliest": transactions_from_text[0].get('date') if transactions_from_text else None,
                                            "latest": transactions_from_text[-1].get('date') if transactions_from_text else None
                                        }
                                    },
                                    "analysis": self._extract_analysis_from_text(text_response, transactions_from_text),
                                    "questions": [],
                                    "warnings": [],
                                    "extracted_parameters": extracted_params
                                }
                                print(f"✅ Extracted {len(transactions_from_text)} transactions from non-dict response using model {self.model}")
                                return result
                    except json.JSONDecodeError as e:
                        print(f"JSON parsing error: {str(e)}")
                        print(f"Extracted JSON preview: {json_match[:200]}...")
                        # Пробуем исправить JSON
                        fixed_json = self._fix_json(json_match)
                        if fixed_json:
                            try:
                                result = json.loads(fixed_json)
                                if isinstance(result, dict) and 'transactions' in result:
                                    result['extracted_parameters'] = extracted_params
                                    print(f"✅ Successfully extracted {len(result.get('transactions', []))} transactions after JSON fix using model {self.model}")
                                    return result
                            except json.JSONDecodeError:
                                pass
                else:
                    # Если не удалось извлечь JSON, пробуем извлечь транзакции напрямую из текста
                    print("Could not extract JSON from response, trying to extract transactions from text...")
                    transactions_from_text = self._extract_transactions_from_text(text_response)
                    if transactions_from_text:
                        # Создаем структуру ответа на основе извлеченных транзакций
                        total_income = sum(t.get('amount', 0) for t in transactions_from_text if t.get('type') == 'income' and t.get('amount'))
                        total_expense = sum(t.get('amount', 0) for t in transactions_from_text if t.get('type') == 'expense' and t.get('amount'))
                        result = {
                            "transactions": transactions_from_text,
                            "extracted_info": {
                                "total_income": total_income,
                                "total_expense": total_expense,
                                "transactions_count": len(transactions_from_text),
                                "date_range": {
                                    "earliest": transactions_from_text[0].get('date') if transactions_from_text else None,
                                    "latest": transactions_from_text[-1].get('date') if transactions_from_text else None
                                }
                            },
                            "analysis": self._extract_analysis_from_text(text_response, transactions_from_text),
                            "questions": [],
                            "warnings": [],
                            "extracted_parameters": extracted_params
                        }
                        print(f"✅ Extracted {len(transactions_from_text)} transactions from text using model {self.model}")
                        return result
                    print(f"Response preview: {text_response[:300]}...")
            else:
                print("Invalid response format: no 'choices' found")
                
        except Exception as e:
            print(f"GigaChat transaction extraction error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def generate_financial_advice(self, portfolio_data: Dict, analysis_type: str = "full") -> Optional[Dict]:
        """
        Генерация финансовых советов через GigaChat с детальным анализом
        
        Args:
            portfolio_data: Данные портфеля
            analysis_type: Тип анализа (full, risk, performance)
            
        Returns:
            Словарь с рекомендациями, анализом и вопросами или None
        """
        if not self._is_available():
            return None
            
        portfolio_summary = self._format_portfolio_summary(portfolio_data)
        
        prompt = f"""Ты опытный финансовый консультант с глубоким пониманием инвестиций и управления портфелем. Проанализируй следующий портфель и дай развернутые рекомендации.

Данные портфеля:
{portfolio_summary}

Тип анализа: {analysis_type}

Проведи детальный анализ и верни ответ в формате JSON:
{{
    "recommendations": ["конкретная рекомендация 1", "конкретная рекомендация 2", "конкретная рекомендация 3", "конкретная рекомендация 4"],
    "detailed_analysis": "развернутый анализ портфеля (3-4 предложения): сильные стороны, слабые стороны, риски, возможности",
    "risk_assessment": "оценка рисков портфеля (2-3 предложения): какие риски присутствуют, как их можно снизить",
    "questions": ["наводящий вопрос о финансовых целях", "вопрос о толерантности к риску", "вопрос о временном горизонте инвестиций"],
    "next_steps": "конкретные следующие шаги для улучшения портфеля (2-3 предложения)"
}}

Рекомендации должны быть практичными и конкретными. Вопросы должны помочь лучше понять финансовые цели и предпочтения пользователя."""
        
        try:
            token = get_access_token()
            if not token:
                return None
                
            response = chat_completion(token, prompt, model=self.model, temperature=0.8, max_tokens=2500)
            
            if 'error' in response:
                return None
                
            if 'choices' in response and len(response['choices']) > 0:
                text_response = response['choices'][0].get('message', {}).get('content', '')
                json_match = self._extract_json(text_response)
                if json_match:
                    result = json.loads(json_match)
                    if isinstance(result, dict):
                        return result
        except Exception as e:
            print(f"GigaChat advice generation error: {str(e)}")
        
        return None
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Извлечение JSON из текста ответа с улучшенной обработкой"""
        import json
        
        # Сначала проверяем, есть ли JSON в markdown блоке (```json ... ```)
        markdown_json_match = re.search(r'```json\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
        if markdown_json_match:
            json_str = markdown_json_match.group(1)
            json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # Также проверяем markdown блок без указания языка (``` ... ```)
        markdown_match = re.search(r'```\s*(\{.*?\}|\[.*?\])\s*```', text, re.DOTALL)
        if markdown_match:
            json_str = markdown_match.group(1)
            json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                pass
        
        # Сначала пробуем простой поиск JSON объекта или массива
        json_match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            # Удаляем управляющие символы, которые могут вызывать проблемы при парсинге
            # Оставляем только разрешенные: \n, \r, \t
            json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
            
            # Пробуем распарсить для проверки валидности
            try:
                json.loads(json_str)
                return json_str
            except json.JSONDecodeError:
                # Если не получилось, пробуем найти валидный JSON более точно
                # Ищем первый { и соответствующий }
                start_idx = text.find('{')
                if start_idx != -1:
                    depth = 0
                    for i in range(start_idx, len(text)):
                        if text[i] == '{':
                            depth += 1
                        elif text[i] == '}':
                            depth -= 1
                            if depth == 0:
                                json_candidate = text[start_idx:i+1]
                                json_candidate = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_candidate)
                                try:
                                    json.loads(json_candidate)
                                    return json_candidate
                                except json.JSONDecodeError:
                                    pass
                                break
                
                # Если объект не найден, пробуем массив
                start_idx = text.find('[')
                if start_idx != -1:
                    depth = 0
                    for i in range(start_idx, len(text)):
                        if text[i] == '[':
                            depth += 1
                        elif text[i] == ']':
                            depth -= 1
                            if depth == 0:
                                json_candidate = text[start_idx:i+1]
                                json_candidate = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_candidate)
                                try:
                                    json.loads(json_candidate)
                                    return json_candidate
                                except json.JSONDecodeError:
                                    pass
                                break
        
        return None
    
    def _extract_json_aggressive(self, text: str) -> Optional[str]:
        """Более агрессивное извлечение JSON из текста"""
        import json
        
        # Пробуем найти JSON, который может быть окружен текстом
        # Ищем все возможные JSON объекты в тексте
        json_patterns = [
            r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Простые вложенные объекты
            r'\{.*?"transactions".*?\}',  # Объект с ключом transactions
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text, re.DOTALL)
            for match in matches:
                json_str = match.group()
                json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict) and 'transactions' in parsed:
                        return json_str
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def _fix_json(self, json_str: str) -> Optional[str]:
        """Попытка исправить поврежденный JSON"""
        import json
        
        # Убираем лишние запятые в конце объектов/массивов
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # Исправляем одинарные кавычки на двойные (если они используются для ключей)
        json_str = re.sub(r"'(\w+)':", r'"\1":', json_str)
        
        try:
            json.loads(json_str)
            return json_str
        except json.JSONDecodeError:
            return None
    
    def _extract_transactions_from_text(self, text: str) -> List[Dict]:
        """Извлечение транзакций из текстового ответа API"""
        transactions = []
        
        # Ищем паттерны транзакций в тексте
        # Формат: "type": "income/expense", "amount": число, "title": "..."
        transaction_patterns = [
            r'"type"\s*:\s*"(income|expense)"[^}]*"amount"\s*:\s*(\d+\.?\d*)[^}]*"title"\s*:\s*"([^"]+)"',
            r'"amount"\s*:\s*(\d+\.?\d*)[^}]*"type"\s*:\s*"(income|expense)"[^}]*"title"\s*:\s*"([^"]+)"',
        ]
        
        for pattern in transaction_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 3:
                    trans_type = match.group(1) if 'type' in pattern else match.group(2)
                    amount = float(match.group(2) if 'type' in pattern else match.group(1))
                    title = match.group(3)
                    
                    transaction = {
                        "type": trans_type,
                        "title": title,
                        "amount": amount,
                        "category": "Other",
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "description": "",
                        "confidence": 0.7
                    }
                    transactions.append(transaction)
        
        return transactions
    
    def _extract_analysis_from_text(self, text: str, transactions: List[Dict]) -> str:
        """Извлечение анализа из текстового ответа API"""
        # Ищем анализ в тексте - обычно это длинный блок текста после JSON или в отдельном разделе
        analysis_patterns = [
            r'анализ[:\s]+(.*?)(?:\n\n|\n\n\n|$)',
            r'###?\s*Финансовый анализ[:\s]+(.*?)(?:\n\n|\n\n\n|$)',
            r'###?\s*Анализ[:\s]+(.*?)(?:\n\n|\n\n\n|$)',
            r'Общая оценка[:\s]+(.*?)(?:\n\n|\n\n\n|$)',
        ]
        
        for pattern in analysis_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                analysis = match.group(1).strip()
                if len(analysis) > 200:
                    return analysis
        
        # Если не нашли структурированный анализ, берем весь текст после JSON или длинный блок текста
        # Убираем JSON блоки
        text_clean = re.sub(r'```json.*?```', '', text, flags=re.DOTALL)
        text_clean = re.sub(r'\{.*?\}', '', text_clean, flags=re.DOTALL)
        text_clean = text_clean.strip()
        
        # Берем самый длинный абзац
        paragraphs = [p.strip() for p in text_clean.split('\n\n') if len(p.strip()) > 100]
        if paragraphs:
            # Объединяем несколько абзацев
            analysis = '\n\n'.join(paragraphs[:5])
            if len(analysis) > 300:
                return analysis
        
        # Если ничего не нашли, генерируем анализ на основе транзакций
        return self._generate_analysis_from_transactions(transactions, {})
    
    def _generate_analysis_from_transactions(self, transactions: List[Dict], extracted_info: Dict) -> str:
        """Генерация развернутого анализа на основе транзакций"""
        if not transactions:
            return "Транзакции не найдены в сообщении."
        
        total_income = extracted_info.get('total_income', sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income' and t.get('amount')))
        total_expense = extracted_info.get('total_expense', sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense' and t.get('amount')))
        
        income_count = len([t for t in transactions if t.get('type') == 'income'])
        expense_count = len([t for t in transactions if t.get('type') == 'expense'])
        
        # Анализ категорий
        categories = {}
        for t in transactions:
            cat = t.get('category', 'Other')
            categories[cat] = categories.get(cat, 0) + t.get('amount', 0)
        
        dominant_category = max(categories.items(), key=lambda x: x[1])[0] if categories else None
        
        analysis_parts = []
        
        # Общая оценка
        analysis_parts.append(f"### Общая оценка транзакций")
        analysis_parts.append(f"Всего зарегистрировано {len(transactions)} транзакций: {income_count} доходов и {expense_count} расходов.")
        if total_income > 0:
            analysis_parts.append(f"Общая сумма доходов составляет {total_income:,.0f} рублей.")
        if total_expense > 0:
            analysis_parts.append(f"Общая сумма расходов составляет {total_expense:,.0f} рублей.")
        
        balance = total_income - total_expense
        if balance > 0:
            analysis_parts.append(f"Баланс положительный: {balance:,.0f} рублей. Это хороший знак финансовой стабильности.")
        elif balance < 0:
            analysis_parts.append(f"Баланс отрицательный: {abs(balance):,.0f} рублей. Стоит обратить внимание на превышение расходов над доходами.")
        else:
            analysis_parts.append("Доходы и расходы сбалансированы.")
        
        # Анализ категорий
        if categories:
            analysis_parts.append(f"\n### Анализ категорий")
            analysis_parts.append(f"Расходы распределены по следующим категориям: {', '.join(categories.keys())}.")
            if dominant_category:
                analysis_parts.append(f"Наибольшая доля расходов приходится на категорию '{dominant_category}' ({categories[dominant_category]:,.0f} рублей).")
        
        # Рекомендации
        analysis_parts.append(f"\n### Рекомендации")
        if total_expense > total_income * 0.8:
            analysis_parts.append("Расходы составляют более 80% от доходов. Рекомендуется пересмотреть бюджет и найти возможности для экономии.")
        if expense_count > income_count * 2:
            analysis_parts.append("Количество расходов значительно превышает количество доходов. Стоит проанализировать, какие расходы можно оптимизировать.")
        if balance > 0:
            analysis_parts.append("Рекомендуется отложить часть положительного баланса на непредвиденные расходы или инвестиции.")
        
        # Практические советы
        analysis_parts.append(f"\n### Практические советы")
        analysis_parts.append("Для улучшения управления финансами рекомендуется:")
        analysis_parts.append("1. Регулярно отслеживать все транзакции")
        analysis_parts.append("2. Планировать бюджет на месяц вперед")
        analysis_parts.append("3. Анализировать категории расходов и находить возможности для оптимизации")
        analysis_parts.append("4. Создать резервный фонд на случай непредвиденных ситуаций")
        
        # Прогноз
        analysis_parts.append(f"\n### Прогноз и планирование")
        if balance > 0:
            analysis_parts.append("При сохранении текущей динамики доходов и расходов финансовое положение будет стабильным.")
        else:
            analysis_parts.append("Необходимо пересмотреть структуру расходов, чтобы избежать финансовых трудностей в будущем.")
        
        return '\n\n'.join(analysis_parts)
    
    def _normalize_emotions(self, emotions: Dict[str, float]) -> Dict[str, float]:
        """Нормализация эмоций (сумма должна быть ~1.0)"""
        total = sum(emotions.values())
        if total > 0:
            return {k: v / total for k, v in emotions.items()}
        return emotions
    
    def _extract_parameters_from_message(self, message: str) -> Dict:
        """
        Извлечение параметров из сообщения пользователя
        
        Args:
            message: Текст сообщения пользователя
            
        Returns:
            Словарь с извлеченными параметрами
        """
        text_lower = message.lower()
        parameters = {
            "amounts": [],
            "timeframes": [],
            "goals": [],
            "risk_tolerance": None,
            "categories": [],
            "priorities": [],
            "constraints": [],
            "experience_level": None,
            "emotional_state": None,
            "financial_situation": None,
            "preferences": []
        }
        
        amount_patterns = [
            r'(\d+[\s,.]?\d*)\s*(рубл[ейя]|rub|₽|р\.|руб)',
            r'(\d+[\s,.]?\d*)\s*(тысяч|тыс|к|k)',
            r'(\d+[\s,.]?\d*)\s*(миллион|млн|m)',
            r'(\d+[\s,.]?\d*)\s*(доллар|usd|\$|бакс)',
            r'(\d+[\s,.]?\d*)\s*(евро|eur|€)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            parameters["amounts"].extend([match[0] for match in matches])
        
        timeframe_keywords = {
            "краткосрочн": ["месяц", "неделя", "день", "скоро", "быстро", "сейчас"],
            "среднесрочн": ["полгода", "год", "несколько месяцев", "6 месяцев", "12 месяцев"],
            "долгосрочн": ["годы", "несколько лет", "5 лет", "10 лет", "долгосрочн", "на будущее"]
        }
        
        for timeframe_type, keywords in timeframe_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["timeframes"].append(timeframe_type)
        
        goal_keywords = {
            "накопление": ["накопить", "сберечь", "отложить", "накопления", "сбережения"],
            "инвестиции": ["инвестировать", "вложить", "портфель", "акции", "облигации"],
            "покупка": ["купить", "приобрести", "покупка", "приобретение"],
            "погашение_долга": ["долг", "кредит", "займ", "погасить", "вернуть"],
            "пенсия": ["пенсия", "пенсионный", "на пенсию"],
            "образование": ["образование", "учеба", "обучение", "университет"],
            "недвижимость": ["квартира", "дом", "недвижимость", "жилье"]
        }
        
        for goal, keywords in goal_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["goals"].append(goal)
        
        risk_keywords = {
            "консервативный": ["консервативн", "безопасн", "надежн", "низкий риск", "не рисковать"],
            "умеренный": ["умеренн", "сбалансированн", "средний риск"],
            "агрессивный": ["агрессивн", "высокий риск", "рисковать", "максимальная прибыль"]
        }
        
        for risk_level, keywords in risk_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["risk_tolerance"] = risk_level
                break
        
        category_keywords = {
            "еда": ["еда", "продукты", "ресторан", "кафе", "питание"],
            "транспорт": ["транспорт", "машина", "бензин", "такси", "метро"],
            "развлечения": ["развлечения", "кино", "игры", "отдых", "отпуск"],
            "здоровье": ["здоровье", "лечение", "врач", "лекарства", "медицина"],
            "образование": ["образование", "курсы", "обучение", "книги"],
            "жилье": ["жилье", "аренда", "коммунальные", "ремонт"],
            "акции": ["акции", "дивиденды", "фондовый рынок"],
            "облигации": ["облигации", "бонды", "купон"],
            "наличные": ["наличные", "депозит", "вклад", "сбережения"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["categories"].append(category)
        
        priority_keywords = {
            "высокий": ["важно", "приоритет", "срочно", "необходимо", "нужно"],
            "средний": ["желательно", "хотелось бы", "можно"],
            "низкий": ["не важно", "не приоритет", "можно отложить"]
        }
        
        for priority, keywords in priority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["priorities"].append(priority)
        
        constraint_keywords = {
            "ограниченный_бюджет": ["мало денег", "ограничен", "не хватает", "бюджет"],
            "временные_ограничения": ["нет времени", "срочно", "быстро"],
            "правовые_ограничения": ["закон", "налог", "регулирование"]
        }
        
        for constraint, keywords in constraint_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["constraints"].append(constraint)
        
        experience_keywords = {
            "новичок": ["новичок", "начинающ", "не знаю", "не понимаю", "первый раз"],
            "опытный": ["опыт", "знаю", "понимаю", "уже", "давно"],
            "эксперт": ["эксперт", "профессионал", "много лет", "глубокие знания"]
        }
        
        for level, keywords in experience_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["experience_level"] = level
                break
        
        emotional_keywords = {
            "тревога": ["боюсь", "страх", "тревога", "опасение", "беспокоюсь"],
            "радость": ["рад", "счастлив", "отлично", "хорошо", "успех"],
            "грусть": ["грустно", "печаль", "плохо", "убыток"],
            "злость": ["злой", "недоволен", "разозлился"]
        }
        
        for emotion, keywords in emotional_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["emotional_state"] = emotion
                break
        
        situation_keywords = {
            "стабильная": ["стабильн", "нормальн", "хорошо", "все ок"],
            "критическая": ["критическ", "проблема", "сложно", "трудно"],
            "растущая": ["растет", "улучшается", "прогресс", "развивается"]
        }
        
        for situation, keywords in situation_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                parameters["financial_situation"] = situation
                break
        
        return parameters
    
    def _format_portfolio_summary(self, portfolio_data: Dict) -> str:
        """Форматирование данных портфеля для промпта"""
        assets = portfolio_data.get("assets", [])
        summary = portfolio_data.get("summary", {})
        
        lines = [
            f"Общая стоимость: {summary.get('total_value', 0):.2f} {portfolio_data.get('currency', 'RUB')}",
            f"Акции: {summary.get('stocks_value', 0):.2f}",
            f"Облигации: {summary.get('bonds_value', 0):.2f}",
            f"Наличные: {summary.get('cash_value', 0):.2f}",
            f"Прибыль: {summary.get('total_profit', 0):.2f} ({summary.get('profit_percent', 0):.2f}%)",
            "",
            "Активы:"
        ]
        
        for asset in assets[:10]:
            lines.append(
                f"- {asset.get('name', 'Unknown')} ({asset.get('id', 'N/A')}): "
                f"{asset.get('value', 0):.2f} ({asset.get('weight', 0)*100:.1f}%)"
            )
        
        risk_metrics = portfolio_data.get("risk_metrics", {})
        if risk_metrics:
            lines.append("")
            lines.append("Метрики риска:")
            lines.append(f"- Волатильность: {risk_metrics.get('volatility', 0):.2f}")
            lines.append(f"- Beta: {risk_metrics.get('beta', 0):.2f}")
            lines.append(f"- Sharpe Ratio: {risk_metrics.get('sharpe_ratio', 0):.2f}")
        
        return "\n".join(lines)


def analyze_emotions_with_fallback(text: str, context: Optional[str] = None) -> Dict:
    """
    Анализ эмоций с fallback на простой анализ
    
    Args:
        text: Текст для анализа
        context: Дополнительный контекст
        
    Returns:
        Словарь с эмоциями, анализом и вопросами
    """
    client = GigaChatAIClient()
    
    if client._is_available():
        result = client.analyze_emotions(text, context)
        if result and isinstance(result, dict):
            return result
    
    emotions = _simple_emotion_analysis(text)
    return {
        "emotions": emotions,
        "analysis": "Простой анализ на основе ключевых слов в тексте. Для более детального анализа рекомендуется использовать GigaChat API.",
        "questions": [
            "Какие финансовые цели вы преследуете?",
            "Что вызывает у вас наибольшее беспокойство в финансовом плане?",
            "Как вы обычно реагируете на изменения на рынке?"
        ],
        "recommendations": "Рекомендуется проконсультироваться с финансовым консультантом для более детального анализа вашей ситуации."
    }


def generate_comprehensive_advice_with_fallback(user_message: str, portfolio_data: Optional[Dict] = None, 
                                                context: Optional[str] = None) -> Dict:
    """
    Генерация комплексных финансовых советов с fallback
    
    Args:
        user_message: Сообщение пользователя
        portfolio_data: Опциональные данные портфеля
        context: Дополнительный контекст
        
    Returns:
        Словарь с комплексным анализом и рекомендациями
    """
    client = GigaChatAIClient()
    
    if client._is_available():
        result = client.generate_comprehensive_advice(user_message, portfolio_data, context)
        if result and isinstance(result, dict):
            return result
    
    extracted_params = client._extract_parameters_from_message(user_message)
    
    return {
        "comprehensive_analysis": f"Анализ сообщения пользователя с учетом извлеченных параметров. Для более детального анализа рекомендуется использовать GigaChat API.",
        "financial_goals_analysis": {
            "identified_goals": extracted_params.get("goals", []),
            "prioritized_goals": extracted_params.get("goals", [])[:3],
            "timeframes": {
                "short_term": "Краткосрочные цели требуют уточнения",
                "medium_term": "Среднесрочные цели требуют уточнения",
                "long_term": "Долгосрочные цели требуют уточнения"
            }
        },
        "risk_assessment": {
            "detected_risk_tolerance": extracted_params.get("risk_tolerance", "не определен"),
            "risk_analysis": "Для детального анализа рисков рекомендуется использовать GigaChat API.",
            "recommended_risk_level": "Требуется уточнение"
        },
        "emotional_analysis": {
            "detected_emotions": [extracted_params.get("emotional_state", "нейтральное")],
            "emotional_impact": "Для анализа влияния эмоций на финансовые решения рекомендуется использовать GigaChat API.",
            "emotional_management": "Рекомендуется проконсультироваться с финансовым консультантом."
        },
        "personalized_recommendations": [
            {
                "category": "общее",
                "priority": "средний",
                "recommendation": "Для получения персонализированных рекомендаций рекомендуется использовать GigaChat API.",
                "action_steps": ["Уточнить финансовые цели", "Определить толерантность к риску", "Оценить текущую ситуацию"],
                "expected_outcome": "Улучшение финансового планирования"
            }
        ],
        "financial_plan": {
            "current_situation": "Требуется дополнительная информация для оценки ситуации.",
            "recommended_actions": [],
            "next_steps": "Рекомендуется использовать GigaChat API для получения детального финансового плана."
        },
        "questions_to_clarify": [
            "Каковы ваши основные финансовые цели?",
            "Какова ваша толерантность к риску?",
            "Каков ваш временной горизонт для достижения целей?"
        ],
        "warnings_and_considerations": [
            "Для принятия важных финансовых решений рекомендуется консультация с профессиональным финансовым консультантом."
        ],
        "extracted_parameters": extracted_params
    }


def is_transaction_message(user_message: str) -> bool:
    """
    Определяет, является ли сообщение запросом на добавление транзакции
    
    Args:
        user_message: Сообщение пользователя
        
    Returns:
        True если сообщение содержит информацию о транзакции, False если это обычный вопрос
    """
    message_lower = user_message.lower()
    
    # Ключевые слова, указывающие на транзакцию
    transaction_keywords = [
        # Расходы
        "потратил", "потратила", "потратили",
        "купил", "купила", "купили", "купить",
        "заплатил", "заплатила", "заплатили", "заплатить",
        "трата", "траты", "расход", "расходы",
        "затратил", "затратила", "затратили",
        # Доходы
        "получил", "получила", "получили", "получить",
        "заработал", "заработала", "заработали", "заработать",
        "доход", "доходы", "прибыль", "зарплата", "зарплату",
        # Общие
        "добавить", "добавь", "добавить транзакцию",
        "записать", "запиши", "записать транзакцию",
        "внести", "внеси", "внести транзакцию"
    ]
    
    # Проверяем наличие ключевых слов
    has_transaction_keyword = any(keyword in message_lower for keyword in transaction_keywords)
    
    # Проверяем наличие суммы (цифры + валюта)
    amount_patterns = [
        r'\d+\s*(рубл[ейя]|rub|₽|р\.|руб)',
        r'\d+\s*(тысяч|тыс|к|k)',
        r'\d+\s*(миллион|млн|m)',
        r'\d+\s*(доллар|usd|\$|бакс)',
        r'\d+\s*(евро|eur|€)',
        r'\d+\s*р\.',
    ]
    
    has_amount = any(re.search(pattern, message_lower, re.IGNORECASE) for pattern in amount_patterns)
    
    # Если есть ключевое слово транзакции ИЛИ есть сумма - это транзакция
    if has_transaction_keyword or has_amount:
        return True
    
    # Вопросы обычно не являются транзакциями
    question_words = ["как", "что", "почему", "зачем", "когда", "где", "кто", "сколько", "какой", "какая"]
    is_question = any(message_lower.startswith(word) for word in question_words) or "?" in user_message
    
    # Если это вопрос без суммы и ключевых слов транзакции - это не транзакция
    if is_question and not has_amount and not has_transaction_keyword:
        return False
    
    # По умолчанию, если есть сумма - считаем транзакцией
    return has_amount


def extract_transactions_with_fallback(user_message: str, context: Optional[str] = None) -> Dict:
    """
    Извлечение транзакций из сообщения пользователя с fallback
    
    Args:
        user_message: Сообщение пользователя
        context: Дополнительный контекст
        
    Returns:
        Словарь с извлеченными транзакциями
    """
    client = GigaChatAIClient()
    
    # Пробуем использовать GigaChat API
    if client._is_available():
        result = client.extract_transactions(user_message, context)
        # Проверяем, что результат валидный и содержит транзакции
        if result and isinstance(result, dict):
            transactions = result.get("transactions", [])
            # Если есть транзакции, возвращаем результат (даже если анализ короткий, он будет дополнен)
            if transactions and len(transactions) > 0:
                # Убеждаемся, что анализ есть и достаточно развернутый
                if not result.get('analysis') or len(result.get('analysis', '')) < 300:
                    result['analysis'] = client._generate_analysis_from_transactions(transactions, result.get('extracted_info', {}))
                return result
            # Если транзакций нет, но есть анализ или другие данные, пробуем извлечь транзакции из текста
            elif result.get('analysis') or result.get('extracted_info'):
                # Пробуем извлечь транзакции из анализа или других полей
                text_to_extract = result.get('analysis', '') + ' ' + str(result.get('extracted_info', ''))
                transactions_from_text = client._extract_transactions_from_text(text_to_extract)
                if transactions_from_text:
                    result['transactions'] = transactions_from_text
                    if not result.get('analysis') or len(result.get('analysis', '')) < 300:
                        result['analysis'] = client._generate_analysis_from_transactions(transactions_from_text, result.get('extracted_info', {}))
                    return result
    
    # Если GigaChat недоступен или вернул ошибку, используем fallback
    print("Using fallback transaction extraction method")
    return _simple_transaction_extraction(user_message)


def _simple_transaction_extraction(message: str) -> Dict:
    """
    Простое извлечение транзакций без использования API (fallback)
    
    Args:
        message: Сообщение пользователя
        
    Returns:
        Словарь с извлеченными транзакциями
    """
    text_lower = message.lower()
    transactions = []
    
    income_keywords = ["получил", "заработал", "доход", "зарплата", "зарплату", "получила", "заработала", "прибыль", "отправила", "отправил", "подарок", "подарил"]
    expense_keywords = ["потратил", "купил", "заплатил", "расход", "трата", "потратила", "купила", "заплатила"]
    
    # Разбиваем сообщение на части для более точного определения типа транзакции
    def _determine_transaction_type(text_around_amount: str) -> str:
        """Определяет тип транзакции на основе контекста вокруг суммы"""
        text_lower_local = text_around_amount.lower()
        # Проверяем ключевые слова до и после суммы
        has_income = any(keyword in text_lower_local for keyword in income_keywords)
        has_expense = any(keyword in text_lower_local for keyword in expense_keywords)
        
        if has_income and not has_expense:
            return "income"
        elif has_expense:
            return "expense"
        # По умолчанию считаем расходом
        return "expense"
    
    # Ищем суммы с контекстом
    amount_patterns = [
        r'(\d+[\s,.]?\d*)\s*(рубл[ейя]|rub|₽|р\.|руб)',
        r'(\d+[\s,.]?\d*)\s*(тысяч|тыс|к|k)',
        r'(\d+[\s,.]?\d*)\s*(миллион|млн|m)',
        r'(\d+[\s,.]?\d*)\s*(доллар|usd|\$|бакс)',
        r'(\d+[\s,.]?\d*)\s*(евро|eur|€)',
    ]
    
    # Извлекаем суммы с контекстом (50 символов до и после)
    amounts_with_context = []
    for pattern in amount_patterns:
        for match in re.finditer(pattern, message, re.IGNORECASE):
            start = max(0, match.start() - 50)
            end = min(len(message), match.end() + 50)
            context = message[start:end]
            
            amount_str = match.group(1) if match.groups() else match.group(0)
            try:
                amount = float(amount_str.replace(',', '.').replace(' ', ''))
                multiplier = 1
                if 'тысяч' in match.group(0).lower() or 'тыс' in match.group(0).lower() or 'к' in match.group(0).lower():
                    multiplier = 1000
                elif 'миллион' in match.group(0).lower() or 'млн' in match.group(0).lower() or 'm' in match.group(0).lower():
                    multiplier = 1000000
                
                amount *= multiplier
                if amount > 0:
                    amounts_with_context.append((amount, context))
            except ValueError:
                continue
    
    # Если не нашли суммы с валютой, ищем просто числа
    if not amounts_with_context:
        for match in re.finditer(r'\d+[\s,.]?\d*', message):
            start = max(0, match.start() - 50)
            end = min(len(message), match.end() + 50)
            context = message[start:end]
            
            try:
                amount = float(match.group(0).replace(',', '.').replace(' ', ''))
                if amount > 0:
                    amounts_with_context.append((amount, context))
            except ValueError:
                continue
    
    category_keywords = {
        "Food": ["еда", "продукты", "хлеб", "молоко", "ресторан", "кафе", "обед", "ужин", "завтрак"],
        "Transport": ["транспорт", "машина", "бензин", "такси", "метро", "автобус", "проезд"],
        "Entertainment": ["кино", "игры", "развлечения", "отдых", "отпуск", "концерт"],
        "Health": ["здоровье", "лечение", "врач", "лекарства", "медицина", "аптека", "больница"],
        "Shopping": ["покупка", "магазин", "одежда", "обувь", "техника"],
        "Housing": ["жилье", "аренда", "коммунальные", "ремонт", "квартира"],
        "Work": ["работа", "зарплата", "заработок", "проект", "фриланс"],
        "Bills": ["счет", "счета", "оплата", "коммуналка", "интернет", "телефон"]
    }
    
    detected_category = "Other"
    for category, keywords in category_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_category = category
            break
    
    if amounts_with_context:
        for amount, context in amounts_with_context[:5]:  # Ограничиваем до 5 транзакций
            # Определяем тип транзакции для каждой суммы на основе контекста
            trans_type = _determine_transaction_type(context)
            
            # Определяем категорию для этой транзакции
            trans_category = "Other"
            context_lower = context.lower()
            for category, keywords in category_keywords.items():
                if any(keyword in context_lower for keyword in keywords):
                    trans_category = category
                    break
            
            # Извлекаем название из контекста
            title = _extract_title_from_message(context, trans_type)
            
            transaction = {
                "type": trans_type,
                "title": title,
                "amount": float(amount),
                "category": trans_category,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "description": context[:100],
                "confidence": 0.6
            }
            transactions.append(transaction)
    else:
        # Если не нашли суммы, создаем одну транзакцию без суммы
        default_type = "expense"  # По умолчанию считаем расходом
        if any(keyword in text_lower for keyword in income_keywords):
            default_type = "income"
        
        transaction = {
            "type": default_type,
            "title": _extract_title_from_message(message, default_type),
            "amount": None,
            "category": detected_category,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": message[:100],
            "confidence": 0.3
        }
        transactions.append(transaction)
    
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income" and t.get("amount"))
    total_expense = sum(t["amount"] for t in transactions if t["type"] == "expense" and t.get("amount"))
    
    return {
        "transactions": transactions,
        "extracted_info": {
            "total_income": total_income,
            "total_expense": total_expense,
            "transactions_count": len(transactions),
            "date_range": {
                "earliest": transactions[0]["date"] if transactions else None,
                "latest": transactions[-1]["date"] if transactions else None
            }
        },
        "analysis": _generate_fallback_analysis(transactions, total_income, total_expense),
        "questions": ["Пожалуйста, уточните сумму транзакции", "Укажите точную дату транзакции"] if not amounts_with_context else [],
        "warnings": ["Данные извлечены с помощью простого анализа. Для более точного результата используйте GigaChat API."],
        "extracted_parameters": {}
    }


def _generate_fallback_analysis(transactions: List[Dict], total_income: float, total_expense: float) -> str:
    """Генерация развернутого анализа для fallback метода"""
    income_count = len([t for t in transactions if t.get('type') == 'income'])
    expense_count = len([t for t in transactions if t.get('type') == 'expense'])
    
    # Анализ категорий
    categories = {}
    for t in transactions:
        cat = t.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + (t.get('amount', 0) or 0)
    
    dominant_category = max(categories.items(), key=lambda x: x[1])[0] if categories else None
    
    analysis_parts = []
    
    # Общая оценка
    analysis_parts.append("### Общая оценка транзакций")
    analysis_parts.append(f"Всего зарегистрировано {len(transactions)} транзакций: {income_count} доходов и {expense_count} расходов.")
    if total_income > 0:
        analysis_parts.append(f"Общая сумма доходов составляет {total_income:,.0f} рублей.")
    if total_expense > 0:
        analysis_parts.append(f"Общая сумма расходов составляет {total_expense:,.0f} рублей.")
    
    balance = total_income - total_expense
    if balance > 0:
        analysis_parts.append(f"Баланс положительный: {balance:,.0f} рублей. Это хороший знак финансовой стабильности.")
    elif balance < 0:
        analysis_parts.append(f"Баланс отрицательный: {abs(balance):,.0f} рублей. Стоит обратить внимание на превышение расходов над доходами.")
    else:
        analysis_parts.append("Доходы и расходы сбалансированы.")
    
    # Анализ категорий
    if categories:
        analysis_parts.append("\n### Анализ категорий")
        analysis_parts.append(f"Расходы распределены по следующим категориям: {', '.join(categories.keys())}.")
        if dominant_category:
            analysis_parts.append(f"Наибольшая доля расходов приходится на категорию '{dominant_category}' ({categories[dominant_category]:,.0f} рублей).")
    
    # Рекомендации
    analysis_parts.append("\n### Рекомендации")
    if total_expense > total_income * 0.8 if total_income > 0 else True:
        analysis_parts.append("Расходы составляют значительную долю от доходов. Рекомендуется пересмотреть бюджет и найти возможности для экономии.")
    if expense_count > income_count * 2:
        analysis_parts.append("Количество расходов значительно превышает количество доходов. Стоит проанализировать, какие расходы можно оптимизировать.")
    if balance > 0:
        analysis_parts.append("Рекомендуется отложить часть положительного баланса на непредвиденные расходы или инвестиции.")
    analysis_parts.append("Рекомендуется вести учет всех транзакций для лучшего контроля финансов.")
    
    # Практические советы
    analysis_parts.append("\n### Практические советы")
    analysis_parts.append("Для улучшения управления финансами рекомендуется:")
    analysis_parts.append("1. Регулярно отслеживать все транзакции")
    analysis_parts.append("2. Планировать бюджет на месяц вперед")
    analysis_parts.append("3. Анализировать категории расходов и находить возможности для оптимизации")
    analysis_parts.append("4. Создать резервный фонд на случай непредвиденных ситуаций")
    
    # Прогноз
    analysis_parts.append("\n### Прогноз и планирование")
    if balance > 0:
        analysis_parts.append("При сохранении текущей динамики доходов и расходов финансовое положение будет стабильным.")
    else:
        analysis_parts.append("Необходимо пересмотреть структуру расходов, чтобы избежать финансовых трудностей в будущем.")
    
    return '\n\n'.join(analysis_parts)


def _extract_title_from_message(message: str, transaction_type: str) -> str:
    """Извлечение названия транзакции из сообщения"""
    words = message.split()
    
    if transaction_type == "income":
        income_words = ["зарплата", "доход", "прибыль", "заработок"]
        for word in words:
            if any(income in word.lower() for income in income_words):
                return word.capitalize()
        return "Доход"
    else:
        expense_words = ["купил", "потратил", "заплатил", "расход"]
        for i, word in enumerate(words):
            if any(expense in word.lower() for expense in expense_words):
                if i + 1 < len(words):
                    return words[i + 1].capitalize()
        return "Расход"


def generate_financial_advice_with_fallback(portfolio_data: Dict, analysis_type: str = "full") -> Dict:
    """
    Генерация финансовых советов с fallback
    
    Args:
        portfolio_data: Данные портфеля
        analysis_type: Тип анализа
        
    Returns:
        Словарь с рекомендациями, анализом и вопросами
    """
    client = GigaChatAIClient()
    
    if client._is_available():
        result = client.generate_financial_advice(portfolio_data, analysis_type)
        if result and isinstance(result, dict):
            return result
    
    recommendations = _simple_financial_advice(portfolio_data, analysis_type)
    summary = portfolio_data.get("summary", {})
    risk_metrics = portfolio_data.get("risk_metrics", {})
    
    return {
        "recommendations": recommendations,
        "detailed_analysis": f"Портфель стоимостью {summary.get('total_value', 0):.2f} RUB показывает {'прибыль' if summary.get('profit_percent', 0) > 0 else 'убыток'} {abs(summary.get('profit_percent', 0)):.2f}%. " +
                           f"Волатильность портфеля составляет {risk_metrics.get('volatility', 0):.2f}. " +
                           "Для более детального анализа рекомендуется использовать GigaChat API.",
        "risk_assessment": f"Уровень риска портфеля: {'высокий' if risk_metrics.get('volatility', 0) > 0.2 else 'средний' if risk_metrics.get('volatility', 0) > 0.1 else 'низкий'}. " +
                          f"Beta коэффициент: {risk_metrics.get('beta', 0):.2f}.",
        "questions": [
            "Каков ваш инвестиционный горизонт?",
            "Какова ваша толерантность к риску?",
            "Какие финансовые цели вы хотите достичь с помощью этого портфеля?"
        ],
        "next_steps": "Рекомендуется регулярно пересматривать портфель и консультироваться с финансовым консультантом для оптимизации инвестиций."
    }


def _simple_emotion_analysis(text: str) -> Dict[str, float]:
    """
    Простой анализ эмоций без использования API (fallback)
    
    Args:
        text: Текст для анализа
        
    Returns:
        Словарь с вероятностями эмоций
    """
    text_lower = text.lower()
    
    positive_words = ["рад", "счастлив", "отлично", "хорошо", "успех", "прибыль", "рост", "выигрыш"]
    fear_words = ["боюсь", "страх", "опасение", "риск", "опасно", "тревога"]
    anger_words = ["злой", "злюсь", "разозлился", "недоволен", "плохо"]
    sadness_words = ["грустно", "печаль", "потеря", "убыток", "плохо"]
    
    joy_score = sum(1 for word in positive_words if word in text_lower) * 0.15
    fear_score = sum(1 for word in fear_words if word in text_lower) * 0.2
    anger_score = sum(1 for word in anger_words if word in text_lower) * 0.15
    sadness_score = sum(1 for word in sadness_words if word in text_lower) * 0.15
    
    emotions = {
        "joy": min(joy_score + 0.2, 0.9),
        "fear": min(fear_score + 0.1, 0.8),
        "anger": min(anger_score + 0.1, 0.7),
        "sadness": min(sadness_score + 0.1, 0.7),
        "surprise": 0.1,
        "neutral": max(0.2, 1.0 - joy_score - fear_score - anger_score - sadness_score - 0.1)
    }
    
    total = sum(emotions.values())
    return {k: v / total for k, v in emotions.items()}


def _simple_financial_advice(portfolio_data: Dict, analysis_type: str = "full") -> List[str]:
    """
    Простая генерация финансовых советов без использования API (fallback)
    
    Args:
        portfolio_data: Данные портфеля
        analysis_type: Тип анализа
        
    Returns:
        Список рекомендаций
    """
    recommendations = []
    assets = portfolio_data.get("assets", [])
    summary = portfolio_data.get("summary", {})
    
    stocks_weight = summary.get("stocks_value", 0) / summary.get("total_value", 1) if summary.get("total_value", 0) > 0 else 0
    bonds_weight = summary.get("bonds_value", 0) / summary.get("total_value", 1) if summary.get("total_value", 0) > 0 else 0
    
    if stocks_weight > 0.7:
        recommendations.append("Высокая доля акций в портфеле. Рекомендуется увеличить долю облигаций для снижения риска.")
    
    if bonds_weight > 0.5:
        recommendations.append("Высокая доля облигаций. Рассмотрите возможность увеличения доли акций для потенциального роста.")
    
    risk_metrics = portfolio_data.get("risk_metrics", {})
    if risk_metrics:
        volatility = risk_metrics.get("volatility", 0)
        if volatility > 0.2:
            recommendations.append("Высокая волатильность портфеля. Рекомендуется диверсификация по секторам и регионам.")
    
    sectors = {}
    for asset in assets:
        sector = asset.get("sector", "Unknown")
        weight = asset.get("weight", 0)
        sectors[sector] = sectors.get(sector, 0) + weight
    
    max_sector_weight = max(sectors.values()) if sectors else 0
    if max_sector_weight > 0.4:
        recommendations.append(f"Высокая концентрация в одном секторе ({max_sector_weight:.1%}). Рекомендуется диверсификация.")
    
    if not recommendations:
        recommendations.append("Портфель хорошо диверсифицирован. Продолжайте мониторить изменения на рынке.")
    
    profit_percent = summary.get("profit_percent", 0)
    if profit_percent < 0:
        recommendations.append("Портфель показывает убыток. Рассмотрите возможность ребалансировки активов.")
    
    return recommendations[:5]
