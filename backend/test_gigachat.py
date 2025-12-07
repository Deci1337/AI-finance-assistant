
#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы GigaChat API
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gigachat_integration import (
    get_access_token,
    chat_completion,
    GigaChatAIClient,
    extract_transactions_with_fallback,
    is_transaction_message
)

def test_token():
    """Тест получения токена"""
    print("=" * 60)
    print("ТЕСТ 1: Получение токена доступа")
    print("=" * 60)
    
    try:
        token = get_access_token()
        if token:
            print(f"✅ Токен получен успешно!")
            print(f"   Токен (первые 20 символов): {token[:20]}...")
            return token
        else:
            print("❌ Не удалось получить токен")
            return None
    except Exception as e:
        print(f"❌ Ошибка при получении токена: {str(e)}")
        return None

def test_chat_completion(token):
    """Тест простого запроса к API"""
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Простой запрос к GigaChat API")
    print("=" * 60)
    
    if not token:
        print("⚠️  Пропущено: нет токена")
        return False
    
    try:
        test_message = "Привет! Как дела?"
        print(f"Отправка сообщения: '{test_message}'")
        
        response = chat_completion(token, test_message, max_tokens=100)
        
        if 'error' in response:
            print(f"❌ Ошибка API: {response.get('error')}")
            print(f"   Сообщение: {response.get('message', '')[:200]}")
            return False
        
        if 'choices' in response and len(response['choices']) > 0:
            answer = response['choices'][0].get('message', {}).get('content', '')
            print(f"✅ API работает!")
            print(f"   Ответ: {answer[:100]}...")
            return True
        else:
            print("❌ Неожиданный формат ответа")
            print(f"   Ответ: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при запросе: {str(e)}")
        return False

def test_transaction_extraction():
    """Тест извлечения транзакций"""
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Извлечение транзакций")
    print("=" * 60)
    
    test_messages = [
        # Простые транзакции
        "Купил хлеб за 50 рублей и молоко за 80 рублей",
        "Получил зарплату 85000 рублей",
        "Вчера потратил 2000 на обед в ресторане",
        
        # Множественные транзакции
        "Сегодня купил продукты на 1500 рублей, заплатил за интернет 500 рублей и купил билеты в кино за 800 рублей",
        "Получил зарплату 85000 рублей и премию 15000 рублей",
        
        # Транзакции с датами
        "15 декабря потратил 3000 на подарки",
        "В прошлую пятницу получил 5000 рублей за фриланс",
        
        # Транзакции с категориями
        "Заплатил за бензин 2500 рублей",
        "Купил лекарства на 1200 рублей в аптеке",
        "Получил дивиденды 5000 рублей",
        
        # Сложные формулировки
        "Потратил около 5000 рублей на продукты в магазине",
        "Заработал примерно 30000 рублей на подработке",
        "Заплатил за коммунальные услуги 4500 рублей за ноябрь",
        
        # Транзакции без явной суммы
        "Купил кофе",
        "Получил деньги",
        
        # С разными валютами
        "Потратил 100 долларов на покупки",
        "Получил 500 евро",
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Тест {i}: '{message}' ---")
        try:
            result = extract_transactions_with_fallback(message)
            
            if result and result.get("transactions"):
                transactions = result.get("transactions", [])
                print(f"✅ Извлечено транзакций: {len(transactions)}")
                
                for j, trans in enumerate(transactions, 1):
                    print(f"\n   Транзакция {j}:")
                    print(f"   - Тип: {trans.get('type', 'N/A')}")
                    print(f"   - Сумма: {trans.get('amount', 'N/A')}")
                    print(f"   - Категория: {trans.get('category', 'N/A')}")
                    print(f"   - Дата: {trans.get('date', 'N/A')}")
                    print(f"   - Название: {trans.get('title', 'N/A')}")
                
                if result.get("analysis"):
                    print(f"\n   Анализ: {result.get('analysis')[:100]}...")
                
                if result.get("warnings"):
                    print(f"\n   ⚠️  Предупреждения: {result.get('warnings')}")
            else:
                print("❌ Транзакции не извлечены")
                
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")
            import traceback
            traceback.print_exc()

def test_client_availability():
    """Тест доступности клиента"""
    print("\n" + "=" * 60)
    print("ТЕСТ 4: Проверка доступности GigaChatAIClient")
    print("=" * 60)
    
    try:
        client = GigaChatAIClient()
        is_available = client._is_available()
        
        if is_available:
            print("✅ GigaChatAIClient доступен")
        else:
            print("❌ GigaChatAIClient недоступен")
            print("   Будет использоваться fallback метод")
        
        return is_available
    except Exception as e:
        print(f"❌ Ошибка: {str(e)}")
        return False

def test_message_classification():
    """Тест классификации сообщений (транзакция vs вопрос)"""
    print("\n" + "=" * 60)
    print("ТЕСТ 5: Классификация сообщений")
    print("=" * 60)
    
    test_cases = [
        # Транзакции (должны вернуть True)
        ("Купил хлеб за 50 рублей", True),
        ("Получил зарплату 85000", True),
        ("Потратил 2000 на обед", True),
        ("Заработал 30000 рублей", True),
        ("Заплатил за интернет 500 рублей", True),
        ("Купил продукты на 1500 рублей", True),
        
        # Вопросы (должны вернуть False)
        ("Как сэкономить деньги?", False),
        ("Что такое бюджет?", False),
        ("Почему я трачу так много?", False),
        ("Когда лучше инвестировать?", False),
        ("Где можно взять кредит?", False),
        ("Сколько нужно откладывать?", False),
        ("Какой банк лучше?", False),
        ("Какая процентная ставка?", False),
        ("Как правильно вести бюджет?", False),
        ("Что делать с долгами?", False),
        
        # Смешанные случаи
        ("Сколько я потратил в этом месяце?", False),  # Вопрос о транзакциях
        ("Как добавить транзакцию?", False),  # Вопрос о функции
        ("Купил хлеб, сколько это стоит?", True),  # Есть транзакция + вопрос
        ("Что делать если потратил слишком много?", False),  # Вопрос, не транзакция
    ]
    
    passed = 0
    failed = 0
    
    for message, expected in test_cases:
        result = is_transaction_message(message)
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} '{message[:50]}...' -> {result} (ожидалось {expected})")
    
    print(f"\nРезультат: {passed} пройдено, {failed} провалено из {len(test_cases)}")


def test_chat_responses():
    """Тест обычных вопросов в чате"""
    print("\n" + "=" * 60)
    print("ТЕСТ 6: Ответы на обычные вопросы")
    print("=" * 60)
    
    token = get_access_token()
    if not token:
        print("⚠️  Пропущено: нет токена")
        return
    
    questions = [
        "Как сэкономить деньги?",
        "Что такое бюджет?",
        "Как правильно инвестировать?",
        "Какие есть способы накопления?",
        "Что делать если не хватает денег?",
        "Как вести учет расходов?",
        "Какие ошибки в управлении финансами самые частые?",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n--- Вопрос {i}: '{question}' ---")
        try:
            response = chat_completion(token, question, max_tokens=200)
            
            if 'error' in response:
                print(f"❌ Ошибка: {response.get('error')}")
            else:
                answer = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                print(f"✅ Ответ получен ({len(answer)} символов)")
                print(f"   Ответ: {answer[:150]}...")
        except Exception as e:
            print(f"❌ Ошибка: {str(e)}")

def main():
    """Основная функция тестирования"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ GIGACHAT API")
    print("=" * 60 + "\n")
    
    # Тест 1: Получение токена
    token = test_token()
    
    # Тест 2: Простой запрос
    if token:
        test_chat_completion(token)
    
    # Тест 3: Проверка доступности клиента
    test_client_availability()
    
    # Тест 4: Извлечение транзакций
    test_transaction_extraction()
    
    # Тест 5: Классификация сообщений
    test_message_classification()
    
    # Тест 6: Ответы на обычные вопросы
    test_chat_responses()
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print("\nПроверьте логи выше для диагностики проблем.")
    print("Если все тесты пройдены успешно, GigaChat API работает корректно.")

if __name__ == "__main__":
    main()

