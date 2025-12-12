"""
Тестовый скрипт для проверки работы голосового ввода через API
"""

import requests
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"


def test_health_check():
    """Проверка доступности API"""
    print("1. Проверка доступности API...")
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("   ✓ API доступен")
            return True
        else:
            print(f"   ✗ API недоступен: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Ошибка подключения: {e}")
        return False


def test_transcribe_voice_endpoint(audio_file_path: str):
    """Тест эндпоинта /transcribe-voice"""
    print(f"\n2. Тест распознавания речи (/transcribe-voice)...")
    
    if not os.path.exists(audio_file_path):
        print(f"   ⚠ Файл {audio_file_path} не найден. Пропуск теста.")
        return False
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
            data = {'audio_format': 'wav'}
            
            response = requests.post(
                f"{API_BASE_URL}/transcribe-voice",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Распознавание успешно")
                print(f"   Текст: {result.get('text', 'Не распознано')}")
                print(f"   Уверенность: {result.get('confidence', 'N/A')}")
                return True
            else:
                print(f"   ✗ Ошибка: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False


def test_transcribe_and_extract_endpoint(audio_file_path: str):
    """Тест комбинированного эндпоинта /transcribe-and-extract"""
    print(f"\n3. Тест распознавания и извлечения транзакций (/transcribe-and-extract)...")
    
    if not os.path.exists(audio_file_path):
        print(f"   ⚠ Файл {audio_file_path} не найден. Пропуск теста.")
        return False
    
    try:
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': (os.path.basename(audio_file_path), audio_file, 'audio/wav')}
            data = {'audio_format': 'wav'}
            
            response = requests.post(
                f"{API_BASE_URL}/transcribe-and-extract",
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Обработка успешна")
                print(f"   Распознанный текст: {result.get('transcription', 'N/A')}")
                
                transactions = result.get('transactions', [])
                print(f"   Найдено транзакций: {len(transactions)}")
                
                for i, transaction in enumerate(transactions, 1):
                    print(f"   Транзакция {i}:")
                    print(f"     Тип: {transaction.get('type', 'N/A')}")
                    print(f"     Название: {transaction.get('title', 'N/A')}")
                    print(f"     Сумма: {transaction.get('amount', 'N/A')}")
                    print(f"     Категория: {transaction.get('category', 'N/A')}")
                
                if result.get('analysis'):
                    print(f"   Анализ: {result.get('analysis')}")
                
                return True
            else:
                print(f"   ✗ Ошибка: {response.status_code}")
                print(f"   Ответ: {response.text}")
                return False
    except Exception as e:
        print(f"   ✗ Ошибка: {e}")
        return False


def test_text_extraction():
    """Тест извлечения транзакций из текста (для сравнения)"""
    print(f"\n4. Тест извлечения транзакций из текста (для сравнения)...")
    
    test_messages = [
        "Купил хлеб за 50 рублей и молоко за 80 рублей",
        "Получил зарплату 85000 рублей",
        "Вчера потратил 2000 на обед в ресторане"
    ]
    
    for message in test_messages:
        try:
            response = requests.post(
                f"{API_BASE_URL}/extract-transactions",
                json={"user_message": message},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                transactions = result.get('transactions', [])
                print(f"   ✓ Сообщение: '{message}'")
                print(f"     Найдено транзакций: {len(transactions)}")
            else:
                print(f"   ✗ Ошибка для сообщения '{message}': {response.status_code}")
        except Exception as e:
            print(f"   ✗ Ошибка: {e}")


def main():
    """Основная функция тестирования"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ГОЛОСОВОГО ВВОДА")
    print("=" * 60)
    
    if not test_health_check():
        print("\n⚠ API недоступен. Убедитесь, что backend запущен:")
        print("   python backend/main.py")
        return
    
    audio_file_path = input("\nВведите путь к тестовому аудио файлу (или нажмите Enter для пропуска): ").strip()
    
    if audio_file_path:
        test_transcribe_voice_endpoint(audio_file_path)
        test_transcribe_and_extract_endpoint(audio_file_path)
    else:
        print("\n⚠ Тесты с аудио файлами пропущены")
    
    test_text_extraction()
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)


if __name__ == "__main__":
    main()

    