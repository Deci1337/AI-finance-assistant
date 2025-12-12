"""
Gemini Integration Module через OpenAI-совместимый прокси
Модуль для работы с Gemini API через прокси OpenAI для анализа эмоций и генерации финансовых советов
"""

import os
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from openai import OpenAI
import urllib.request
import urllib.parse

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCzNvvW3Hxw7LAive8vD8adn4nt-Sh4yT0")
# Vercel deployment URL (добавьте /v1 в конце для API)
GEMINI_PROXY_URL = os.getenv("GEMINI_PROXY_URL", "https://ai-finance-assistant-tawny.vercel.app/v1")
# Согласно инструкции: если имя начинается с "gemini-", используется указанная модель
# Иначе по умолчанию: gemini-flash-latest для chat/completions
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

_client = None


def get_gemini_client() -> OpenAI:
    """Получение клиента Gemini API через прокси"""
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_PROXY_URL,
            timeout=30.0
        )
    return _client


def chat_completion(message: str, model: str = None, temperature: float = 0.7, max_tokens: int = 2000, system_message: Optional[str] = None) -> Dict:
    """
    Выполнение запроса к Gemini API через прокси
    
    Args:
        message: Сообщение для отправки
        model: Название модели (если None, используется модель по умолчанию)
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        system_message: Системное сообщение (опционально)
        
    Returns:
        Ответ от API или словарь с ошибкой
    """
    try:
        if model is None:
            model = GEMINI_MODEL
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": message})
        
        # Используем urllib напрямую для избежания проблем с gzip
        url = f"{GEMINI_PROXY_URL}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {GEMINI_API_KEY}",
                "Content-Type": "application/json",
                "Accept-Encoding": "identity"  # Отключаем gzip
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'error' in result:
                error_data = result.get('error', {})
                error_msg = error_data.get('message', 'Unknown error')
                error_code = error_data.get('code', response.getcode())
                
                if error_code == 429 or 'quota' in error_msg.lower():
                    return {'error': 'quota_exceeded', 'message': f'Превышена квота Gemini API: {error_msg}', 'model_used': model}
                elif 'location' in error_msg.lower() or 'region' in error_msg.lower():
                    return {'error': 'location_not_supported', 'message': 'Gemini API недоступен в вашем регионе. Используйте VPN или проверьте доступность API.', 'model_used': model}
                elif 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
                    return {'error': 'insufficient_balance', 'message': 'Недостаточно средств на балансе Gemini API', 'model_used': model}
                else:
                    return {'error': error_code, 'message': error_msg, 'model_used': model}
            
            return {
                'choices': [{
                    'message': {
                        'content': result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    }
                }]
            }
    except urllib.error.HTTPError as e:
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            error_msg = error_data.get('error', {}).get('message', f'HTTP {e.code}')
        except:
            error_msg = f'HTTP {e.code}'
        
        if e.code == 429:
            return {'error': 'quota_exceeded', 'message': f'Превышена квота Gemini API: {error_msg}', 'model_used': model or GEMINI_MODEL}
        elif e.code == 401:
            return {'error': 'unauthorized', 'message': 'Неверный API ключ Gemini', 'model_used': model or GEMINI_MODEL}
        else:
            return {'error': e.code, 'message': error_msg, 'model_used': model or GEMINI_MODEL}
    except urllib.error.URLError as e:
        return {'error': 'connection_error', 'message': f'Не удалось подключиться к прокси серверу: {str(e)}. Убедитесь, что прокси запущен.', 'model_used': model or GEMINI_MODEL}
    except Exception as e:
        error_msg = str(e)
        if 'location' in error_msg.lower() or 'region' in error_msg.lower():
            return {'error': 'location_not_supported', 'message': 'Gemini API недоступен в вашем регионе. Используйте VPN или проверьте доступность API.', 'model_used': model or GEMINI_MODEL}
        elif 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
            return {'error': 'insufficient_balance', 'message': 'Недостаточно средств на балансе Gemini API', 'model_used': model or GEMINI_MODEL}
        elif '401' in error_msg or 'unauthorized' in error_msg.lower():
            return {'error': 'unauthorized', 'message': 'Неверный API ключ Gemini', 'model_used': model or GEMINI_MODEL}
        else:
            return {'error': 'exception', 'message': error_msg, 'model_used': model or GEMINI_MODEL}


def transcribe_audio_with_fallback(audio_data: bytes, audio_format: str = "wav") -> Optional[str]:
    """Распознавание речи (не поддерживается через прокси)"""
    return None


class GeminiAIClient:
    """Клиент для работы с Gemini API через прокси"""
    
    def __init__(self):
        self.model = GEMINI_MODEL
    
    def _is_available(self) -> bool:
        """Проверка доступности Gemini API"""
        try:
            test_response = chat_completion("тест", max_tokens=10)
            return 'error' not in test_response
        except Exception:
            return False
    
    def chat(self, message: str, system_message: Optional[str] = None, temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """Простой чат через Gemini"""
        if not self._is_available():
            return None
        
        try:
            response = chat_completion(message, model=self.model, temperature=temperature, max_tokens=max_tokens, system_message=system_message)
            if 'error' in response:
                return None
            if 'choices' in response and len(response['choices']) > 0:
                return response['choices'][0].get('message', {}).get('content', '')
        except Exception:
            return None
        return None


def get_access_token() -> Optional[str]:
    """Функция для совместимости с main.py"""
    return GEMINI_API_KEY


def chat_completion_for_chat(token: str, full_message: str) -> Dict:
    """Функция для совместимости с main.py"""
    return chat_completion(full_message)
