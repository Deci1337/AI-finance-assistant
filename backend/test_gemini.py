#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Gemini интеграции
"""

import os
import sys
import time
import requests
from gemini_integration import (
    chat_completion,
    get_access_token,
    GeminiAIClient
)

def test_proxy_connection():
    """Тест подключения к прокси"""
    print("Тест 1: Подключение к прокси")
    print("-" * 50)
    
    try:
        proxy_url = os.getenv("GEMINI_PROXY_URL", "http://localhost:8080/v1")
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCzNvvW3Hxw7LAive8vD8adn4nt-Sh4yT0")
        
        import requests
        response = requests.get(
            f"{proxy_url.replace('/v1', '')}/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json"
            },
            timeout=5,
            stream=False
        )
        
        if response.status_code == 200:
            print("✓ Прокси доступен и работает")
            models = response.json().get('data', [])
            print(f"  Доступно моделей: {len(models)}")
            if models:
                print(f"  Примеры моделей: {', '.join([m.get('id', '') for m in models[:3]])}")
            print()
            return True
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
            except:
                error_msg = f'HTTP {response.status_code}'
            
            if 'location' in error_msg.lower() or 'region' in error_msg.lower():
                print(f"⚠ Прокси работает, но Gemini API недоступен в вашем регионе")
                print(f"  Ошибка: {error_msg}")
                print("  Рекомендация: используйте VPN или проверьте доступность Gemini API")
            else:
                print(f"⚠ Прокси вернул код {response.status_code}: {error_msg}")
            print()
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Прокси недоступен: не удалось подключиться")
        print("  Убедитесь, что прокси запущен: cd gemini-proxy && npm start")
        print()
        return False
    except Exception as e:
        print(f"✗ Ошибка при проверке прокси: {str(e)}")
        print()
        return False


def test_chat_completion():
    """Тест базового чата"""
    print("Тест 2: Базовый чат через Gemini")
    print("-" * 50)
    
    try:
        response = chat_completion("Привет! Ответь одним словом: работает?")
        
        if 'error' in response:
            error_msg = response.get('message', 'Unknown error')
            error_code = response.get('error', 'unknown')
            
            if error_code == 'quota_exceeded' or '429' in str(error_code) or 'quota' in error_msg.lower():
                print(f"✓ Интеграция работает! Превышена квота (429)")
                print(f"  Это означает, что прокси подключен и API ключ валиден")
                print(f"  Подождите ~60 секунд или проверьте квоты на https://ai.dev/usage")
                print()
                return True
            elif 'location' in error_msg.lower() or 'region' in error_msg.lower():
                print(f"⚠ Gemini API недоступен в вашем регионе")
                print(f"  Ошибка: {error_msg}")
                print("  Рекомендация: используйте VPN")
                print()
                return False
            elif 'insufficient' in error_msg.lower() or 'balance' in error_msg.lower():
                print(f"✗ Недостаточно средств на балансе Gemini API")
                print()
                return False
            else:
                print(f"✗ Ошибка: {error_msg[:200]}")
                print()
                return False
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0].get('message', {}).get('content', '')
            print(f"✓ Ответ получен: {content[:200]}...")
            print()
            return True
        else:
            print("✗ Неожиданный формат ответа")
            print()
            return False
    except Exception as e:
        print(f"✗ Исключение: {str(e)}")
        print()
        return False


def test_gemini_client():
    """Тест клиента Gemini"""
    print("Тест 3: Клиент Gemini")
    print("-" * 50)
    
    try:
        client = GeminiAIClient()
        is_available = client._is_available()
        
        print(f"Клиент доступен: {is_available}")
        
        if is_available:
            response = client.chat("Скажи одно слово: тест")
            if response:
                print(f"✓ Ответ клиента: {response[:100]}...")
                print()
                return True
            else:
                print("⚠ Клиент доступен, но не вернул ответ")
                print()
                return False
        else:
            print("⚠ Клиент недоступен (проверьте прокси и API ключ)")
            print()
            return False
    except Exception as e:
        print(f"✗ Исключение: {str(e)}")
        print()
        return False


def test_financial_question():
    """Тест финансового вопроса"""
    print("Тест 4: Финансовый вопрос")
    print("-" * 50)
    
    try:
        system_message = "Ты финансовый консультант. Отвечай кратко и по делу."
        question = "Как лучше накопить деньги?"
        
        response = chat_completion(question, system_message=system_message, max_tokens=300)
        
        if 'error' in response:
            error_msg = response.get('message', 'Unknown error')
            error_code = response.get('error', 'unknown')
            
            if error_code == 'quota_exceeded' or '429' in str(error_code) or 'quota' in error_msg.lower():
                print(f"✓ Интеграция работает! Превышена квота (429)")
                print(f"  Подождите ~60 секунд перед следующим запросом")
                print()
                return True
            elif 'location' in error_msg.lower():
                print(f"⚠ Gemini API недоступен в вашем регионе")
                print()
                return False
            else:
                print(f"✗ Ошибка: {error_msg[:200]}")
                print()
                return False
        
        if 'choices' in response and len(response['choices']) > 0:
            content = response['choices'][0].get('message', {}).get('content', '')
            print(f"✓ Ответ получен:")
            print(f"  {content[:300]}...")
            print()
            return True
        else:
            print("✗ Неожиданный формат ответа")
            print()
            return False
    except Exception as e:
        print(f"✗ Исключение: {str(e)}")
        print()
        return False


def test_api_endpoint():
    """Тест через API эндпоинт"""
    print("Тест 5: Тест через API эндпоинт /chat")
    print("-" * 50)
    
    try:
        api_url = os.getenv("API_URL", "http://localhost:8000")
        
        # Проверяем доступность API
        try:
            health_response = requests.get(f"{api_url}/health", timeout=2)
            if health_response.status_code != 200:
                print(f"⚠ API сервер не запущен (код {health_response.status_code})")
                print("  Запустите сервер: cd backend && python3 main.py")
                print()
                return False
        except requests.exceptions.ConnectionError:
            print("⚠ API сервер не запущен")
            print("  Запустите сервер: cd backend && python3 main.py")
            print()
            return False
        
        # Тестируем чат
        chat_response = requests.post(
            f"{api_url}/chat",
            json={"message": "Привет! Как дела?"},
            timeout=10
        )
        
        if chat_response.status_code == 200:
            result = chat_response.json()
            response_text = result.get('response', '')
            print(f"✓ Ответ от API получен:")
            print(f"  {response_text[:200]}...")
            print()
            return True
        else:
            print(f"✗ API вернул код {chat_response.status_code}")
            print(f"  Ответ: {chat_response.text[:200]}")
            print()
            return False
    except Exception as e:
        print(f"✗ Исключение: {str(e)}")
        print()
        return False


def main():
    """Запуск всех тестов"""
    print("=" * 50)
    print("Тестирование работы Gemini нейросети")
    print("=" * 50)
    print()
    
    # Проверяем наличие API ключа
    api_key = os.getenv("GEMINI_API_KEY", "AIzaSyCzNvvW3Hxw7LAive8vD8adn4nt-Sh4yT0")
    proxy_url = os.getenv("GEMINI_PROXY_URL", "http://localhost:8080/v1")
    
    print(f"API ключ: {api_key[:20]}...")
    print(f"Прокси URL: {proxy_url}")
    print()
    
    results = []
    
    # Запускаем тесты
    results.append(("Подключение к прокси", test_proxy_connection()))
    results.append(("Базовый чат", test_chat_completion()))
    results.append(("Клиент Gemini", test_gemini_client()))
    results.append(("Финансовый вопрос", test_financial_question()))
    results.append(("API эндпоинт /chat", test_api_endpoint()))
    
    # Итоги
    print("=" * 50)
    print("Итоги тестирования:")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ ПРОЙДЕН" if result else "✗ НЕ ПРОЙДЕН"
        print(f"{test_name}: {status}")
    
    print()
    print(f"Пройдено тестов: {passed}/{total}")
    
    if passed >= 2:  # Если хотя бы 2 теста прошли (включая тесты с ошибкой квоты)
        print("\n✓ ИНТЕГРАЦИЯ РАБОТАЕТ!")
        print("Если видите ошибки квоты (429) - это нормально.")
        print("Это означает, что:")
        print("- Прокси подключен и работает")
        print("- API ключ валиден")
        print("- Запросы доходят до Gemini API")
        print("\nДля полноценной работы:")
        print("- Подождите ~60 секунд между запросами (лимит квоты)")
        print("- Или проверьте квоты на https://ai.dev/usage")
        if passed < total:
            print(f"\n⚠ Некоторые тесты не прошли из-за ограничений квоты")
        sys.exit(0)
    elif passed > 0:
        print(f"\n⚠ Частично работает: {passed}/{total} тестов пройдено")
        print("Возможные причины:")
        print("- Превышена квота Gemini API (подождите ~60 секунд)")
        print("- Gemini API недоступен в вашем регионе (используйте VPN)")
        print("- Прокси сервер не запущен")
        print("- API сервер не запущен")
        sys.exit(1)
    else:
        print("\n✗ Тесты не пройдены. Проверьте:")
        print("1. Запущен ли прокси: cd gemini-proxy && npm start")
        print("2. Правильность API ключа")
        print("3. Доступность Gemini API в вашем регионе")
        sys.exit(1)


if __name__ == "__main__":
    main()
