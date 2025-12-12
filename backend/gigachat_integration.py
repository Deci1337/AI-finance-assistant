"""
GigaChat Integration Module
Модуль для работы с GigaChat API от Сбербанка
"""

import os
import json
import time
import uuid
import requests
import urllib3
from typing import Dict, Optional
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GigaChat API credentials
GIGACHAT_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID", "019af7d9-5788-725d-9b0c-9aacb3997956")
GIGACHAT_CLIENT_SECRET = os.getenv("GIGACHAT_CLIENT_SECRET", "3be5ce55-22ae-4e42-a0cd-7383fe475a19")
GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

_access_token = None
_token_expires_at = None


def _encode_basic_auth(client_id: str, client_secret: str) -> str:
    """Кодирование Basic Auth для GigaChat"""
    import base64
    credentials = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return encoded


def get_access_token() -> Optional[str]:
    """Получение access token для GigaChat API"""
    global _access_token, _token_expires_at
    
    # Проверяем, не истек ли токен
    if _access_token and _token_expires_at:
        if datetime.now().timestamp() * 1000 < _token_expires_at - 60000:  # Обновляем за минуту до истечения
            return _access_token
    
    try:
        payload = {
            'scope': 'GIGACHAT_API_PERS'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {_encode_basic_auth(GIGACHAT_CLIENT_ID, GIGACHAT_CLIENT_SECRET)}'
        }
        
        response = requests.post(
            GIGACHAT_OAUTH_URL,
            headers=headers,
            data=payload,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            _access_token = data.get('access_token')
            _token_expires_at = data.get('expires_at')
            print(f"GigaChat token получен, действителен до: {datetime.fromtimestamp(_token_expires_at / 1000)}")
            return _access_token
        else:
            print(f"Ошибка получения GigaChat token: {response.status_code} - {response.text}")
            return None
    
    except Exception as e:
        print(f"Ошибка при получении GigaChat token: {e}")
        return None


def chat_completion(
    message: str,
    system_message: Optional[str] = None,
    model: str = "GigaChat",
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> Dict:
    """
    Выполнение запроса к GigaChat API
    
    Args:
        message: Сообщение для отправки
        system_message: Системное сообщение (опционально)
        model: Название модели (по умолчанию GigaChat)
        temperature: Температура генерации
        max_tokens: Максимальное количество токенов
        
    Returns:
        Ответ от API или словарь с ошибкой
    """
    token = get_access_token()
    if not token:
        return {
            'error': 'auth_failed',
            'message': 'Не удалось получить токен GigaChat API',
            'model_used': model
        }
    
    try:
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": message})
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            GIGACHAT_API_URL,
            headers=headers,
            json=payload,
            verify=False,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Парсим ответ GigaChat
            choices = result.get('choices', [])
            if choices and len(choices) > 0:
                content = choices[0].get('message', {}).get('content', '')
                return {
                    'choices': [{
                        'message': {
                            'content': content
                        }
                    }],
                    'model_used': model,
                    'usage': result.get('usage', {})
                }
            else:
                return {
                    'error': 'empty_response',
                    'message': 'GigaChat вернул пустой ответ',
                    'model_used': model
                }
        
        elif response.status_code == 401:
            # Токен истек, пробуем обновить
            global _access_token, _token_expires_at
            _access_token = None
            _token_expires_at = None
            
            return {
                'error': 'unauthorized',
                'message': 'Токен GigaChat истек, требуется обновление',
                'model_used': model
            }
        
        elif response.status_code == 429:
            return {
                'error': 'rate_limit',
                'message': 'Превышен лимит запросов GigaChat API. Подождите немного.',
                'model_used': model
            }
        
        else:
            error_text = response.text[:200]
            return {
                'error': response.status_code,
                'message': f'Ошибка GigaChat API ({response.status_code}): {error_text}',
                'model_used': model
            }
    
    except requests.exceptions.Timeout:
        return {
            'error': 'timeout',
            'message': 'Таймаут при обращении к GigaChat API',
            'model_used': model
        }
    except Exception as e:
        return {
            'error': 'exception',
            'message': f'Ошибка при обращении к GigaChat API: {str(e)}',
            'model_used': model
        }


def chat_completion_for_chat(token: str, full_message: str, system_message: Optional[str] = None) -> Dict:
    """Функция для совместимости с main.py"""
    return chat_completion(full_message, system_message=system_message)


def is_available() -> bool:
    """Проверка доступности GigaChat API"""
    try:
        token = get_access_token()
        if token:
            result = chat_completion("тест", max_tokens=10)
            return 'error' not in result
        return False
    except Exception:
        return False

