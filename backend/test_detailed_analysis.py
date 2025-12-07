#!/usr/bin/env python3
"""
Тест детального финансового анализа для конкретного сообщения
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gigachat_integration import GigaChatAIClient

def test_detailed_message():
    """Тест детального анализа конкретного сообщения"""
    
    test_message = "Купил хлеб за 50 рублей, сникерс за 100 рублей, потом мама отправила 10000 рублей за хорошую учебу"
    
    print("=" * 70)
    print("ТЕСТ ДЕТАЛЬНОГО ФИНАНСОВОГО АНАЛИЗА")
    print("=" * 70)
    print(f"\nТестовое сообщение:")
    print(f"  '{test_message}'")
    
    print("\n" + "-" * 70)
    print("ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ:")
    print("-" * 70)
    print("  1. Расход: хлеб, 50 руб, категория Food")
    print("  2. Расход: сникерс, 100 руб, категория Food или Shopping")
    print("  3. Доход: от мамы, 10000 руб, категория Gift")
    print("  Всего расходов: 150 руб")
    print("  Всего доходов: 10000 руб")
    print("  Анализ: минимум 8-10 предложений с рекомендациями")
    
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ ИЗВЛЕЧЕНИЯ ЧЕРЕЗ GIGACHAT:")
    print("=" * 70)
    
    client = GigaChatAIClient()
    
    if not client._is_available():
        print("❌ GigaChat API недоступен")
        return False
    
    print("✅ GigaChat API доступен")
    print("\nИзвлечение транзакций...")
    
    result = client.extract_transactions(test_message)
    
    if not result:
        print("❌ Не удалось извлечь транзакции")
        return False
    
    transactions = result.get('transactions', [])
    extracted_info = result.get('extracted_info', {})
    analysis = result.get('analysis', '')
    
    print(f"\n✅ Успешно извлечено {len(transactions)} транзакций\n")
    
    print("-" * 70)
    print("ДЕТАЛИ ТРАНЗАКЦИЙ:")
    print("-" * 70)
    
    total_expense = 0
    total_income = 0
    
    for i, trans in enumerate(transactions, 1):
        trans_type = trans.get('type', 'N/A')
        amount = trans.get('amount')
        title = trans.get('title', 'N/A')
        category = trans.get('category', 'N/A')
        date = trans.get('date', 'N/A')
        confidence = trans.get('confidence', 'N/A')
        
        print(f"\n  {i}. {trans_type.upper()}")
        print(f"     Название: {title}")
        print(f"     Сумма: {amount} руб" if amount else "     Сумма: не указана")
        print(f"     Категория: {category}")
        print(f"     Дата: {date}")
        print(f"     Уверенность: {confidence}")
        
        if trans_type == "expense" and amount:
            total_expense += amount
        elif trans_type == "income" and amount:
            total_income += amount
    
    print("\n" + "-" * 70)
    print("СВОДКА:")
    print("-" * 70)
    print(f"  Всего транзакций: {extracted_info.get('transactions_count', len(transactions))}")
    print(f"  Всего расходов: {total_expense} руб (ожидалось: 150 руб)")
    print(f"  Всего доходов: {total_income} руб (ожидалось: 10000 руб)")
    print(f"  Баланс: {total_income - total_expense} руб")
    
    if extracted_info:
        print(f"\n  Извлеченная информация:")
        print(f"    - Общая сумма доходов: {extracted_info.get('total_income', 'N/A')}")
        print(f"    - Общая сумма расходов: {extracted_info.get('total_expense', 'N/A')}")
        print(f"    - Количество транзакций: {extracted_info.get('transactions_count', 'N/A')}")
    
    print("\n" + "=" * 70)
    print("ФИНАНСОВЫЙ АНАЛИЗ:")
    print("=" * 70)
    
    if analysis:
        print(f"\n{analysis}")
        
        print("\n" + "-" * 70)
        print("СТАТИСТИКА АНАЛИЗА:")
        print("-" * 70)
        print(f"  Длина: {len(analysis)} символов")
        sentences = analysis.count('.') + analysis.count('!') + analysis.count('?')
        print(f"  Количество предложений: ~{sentences}")
        
        # Проверка элементов
        analysis_lower = analysis.lower()
        checks = {
            "Общая оценка": any(word in analysis_lower for word in ["оценка", "сумма", "количество", "тип", "транзакц"]),
            "Анализ категорий": any(word in analysis_lower for word in ["категория", "категории", "расход", "доход", "food", "gift", "shopping"]),
            "Рекомендации": any(word in analysis_lower for word in ["рекоменд", "совет", "следует", "стоит", "можно", "нужно"]),
            "Практические советы": any(word in analysis_lower for word in ["совет", "рекоменд", "можно", "нужно", "важно", "стоит"]),
            "Прогноз": any(word in analysis_lower for word in ["прогноз", "планирование", "будущее", "влияет", "учесть"]),
        }
        
        print("\n  Проверка элементов анализа:")
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"    {status} {check_name}: {'найдено' if passed else 'не найдено'}")
        
        if len(analysis) >= 500:
            print("\n  ✅ Анализ достаточно развернутый")
        else:
            print("\n  ⚠️  Анализ слишком короткий")
        
        if sentences >= 8:
            print(f"  ✅ Достаточно предложений ({sentences})")
        else:
            print(f"  ⚠️  Мало предложений ({sentences}, ожидалось минимум 8)")
    else:
        print("\n❌ Анализ отсутствует")
    
    if result.get('warnings'):
        print("\n" + "-" * 70)
        print("ПРЕДУПРЕЖДЕНИЯ:")
        print("-" * 70)
        for warning in result.get('warnings', []):
            print(f"  ⚠️  {warning}")
    
    if result.get('questions'):
        print("\n" + "-" * 70)
        print("ВОПРОСЫ ДЛЯ УТОЧНЕНИЯ:")
        print("-" * 70)
        for question in result.get('questions', []):
            print(f"  ❓ {question}")
    
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ ОЦЕНКА:")
    print("=" * 70)
    
    score = 0
    max_score = 7
    
    # Проверка количества транзакций
    if len(transactions) == 3:
        score += 1
        print("✅ Правильное количество транзакций (3)")
    else:
        print(f"❌ Неправильное количество транзакций: {len(transactions)} вместо 3")
    
    # Проверка суммы расходов
    if total_expense == 150:
        score += 1
        print("✅ Правильная сумма расходов (150 руб)")
    else:
        print(f"⚠️  Сумма расходов: {total_expense} руб (ожидалось 150 руб)")
    
    # Проверка суммы доходов
    if total_income == 10000:
        score += 1
        print("✅ Правильная сумма доходов (10000 руб)")
    else:
        print(f"⚠️  Сумма доходов: {total_income} руб (ожидалось 10000 руб)")
    
    # Проверка анализа
    if analysis and len(analysis) >= 500:
        score += 1
        print("✅ Анализ достаточно развернутый")
    else:
        print("❌ Анализ слишком короткий")
    
    # Проверка рекомендаций
    if analysis and any(word in analysis.lower() for word in ["рекоменд", "совет"]):
        score += 1
        print("✅ Анализ содержит рекомендации")
    else:
        print("❌ Анализ не содержит рекомендаций")
    
    # Проверка анализа категорий
    if analysis and any(word in analysis.lower() for word in ["категория", "категории"]):
        score += 1
        print("✅ Анализ содержит анализ категорий")
    else:
        print("❌ Анализ не содержит анализ категорий")
    
    # Проверка количества предложений
    if analysis:
        sentences_count = analysis.count('.') + analysis.count('!') + analysis.count('?')
        if sentences_count >= 8:
            score += 1
            print(f"✅ Достаточно предложений в анализе ({sentences_count})")
        else:
            print(f"⚠️  Мало предложений в анализе ({sentences_count}, ожидалось минимум 8)")
    else:
        print("❌ Анализ отсутствует")
    
    print(f"\n📊 Оценка: {score}/{max_score} ({score*100//max_score}%)")
    
    if score >= 6:
        print("\n🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ! Система работает корректно.")
    elif score >= 4:
        print("\n✅ ХОРОШИЙ РЕЗУЛЬТАТ. Есть небольшие улучшения.")
    else:
        print("\n⚠️  ТРЕБУЕТСЯ УЛУЧШЕНИЕ. Результаты не соответствуют ожиданиям.")
    
    return score >= 6

if __name__ == "__main__":
    test_detailed_message()

