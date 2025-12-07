"""
GigaChat Integration Module
Модуль для работы с GigaChat API для анализа эмоций и генерации финансовых советов
"""

import requests
import urllib3
import json
import re
from typing import Dict, List, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MODEL = "GigaChat-Pro"


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


def chat_completion(access_token, message, model=MODEL):
    """Выполнение запроса к GigaChat API"""
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
        'temperature': 0.7,
        'max_tokens': 1000
    }
    response = requests.request("POST", url, headers=headers, json=payload, verify=False)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': response.status_code, 'message': response.text}


class GigaChatAIClient:
    """Клиент для работы с GigaChat API для анализа эмоций и финансовых советов"""
    
    def __init__(self):
        self.model = MODEL
        
    def _is_available(self) -> bool:
        """Проверка доступности GigaChat API"""
        try:
            token = get_access_token()
            return token is not None
        except Exception:
            return False
    
    def analyze_emotions(self, text: str, context: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Анализ эмоций в тексте через GigaChat
        
        Args:
            text: Текст для анализа
            context: Дополнительный контекст
            
        Returns:
            Словарь с вероятностями эмоций или None
        """
        if not self._is_available():
            return None
            
        context_part = f"\nКонтекст: {context}" if context else ""
        
        prompt = f"""Проанализируй эмоциональную окраску следующего текста и определи вероятность каждой эмоции (от 0.0 до 1.0).

Текст: {text}{context_part}

ВАЖНО: Верни ответ ТОЛЬКО в формате JSON без дополнительного текста:
{{
    "joy": число от 0.0 до 1.0,
    "fear": число от 0.0 до 1.0,
    "anger": число от 0.0 до 1.0,
    "sadness": число от 0.0 до 1.0,
    "surprise": число от 0.0 до 1.0,
    "neutral": число от 0.0 до 1.0
}}

Сумма всех значений должна быть примерно равна 1.0."""
        
        try:
            token = get_access_token()
            if not token:
                return None
                
            response = chat_completion(token, prompt, model=self.model)
            
            if 'error' in response:
                return None
                
            if 'choices' in response and len(response['choices']) > 0:
                text_response = response['choices'][0].get('message', {}).get('content', '')
                json_match = self._extract_json(text_response)
                if json_match:
                    emotions = json.loads(json_match)
                    return self._normalize_emotions(emotions)
        except Exception as e:
            print(f"GigaChat emotions analysis error: {str(e)}")
        
        return None
    
    def generate_financial_advice(self, portfolio_data: Dict, analysis_type: str = "full") -> Optional[List[str]]:
        """
        Генерация финансовых советов через GigaChat
        
        Args:
            portfolio_data: Данные портфеля
            analysis_type: Тип анализа (full, risk, performance)
            
        Returns:
            Список рекомендаций или None
        """
        if not self._is_available():
            return None
            
        portfolio_summary = self._format_portfolio_summary(portfolio_data)
        
        prompt = f"""Ты финансовый консультант. Проанализируй следующий портфель и дай конкретные рекомендации.

Данные портфеля:
{portfolio_summary}

Тип анализа: {analysis_type}

Дай 3-5 конкретных рекомендаций по улучшению портфеля. Каждая рекомендация должна быть краткой (1-2 предложения) и практичной.

ВАЖНО: Верни ответ ТОЛЬКО в формате JSON массива строк без дополнительного текста:
["рекомендация 1", "рекомендация 2", "рекомендация 3"]"""
        
        try:
            token = get_access_token()
            if not token:
                return None
                
            response = chat_completion(token, prompt, model=self.model)
            
            if 'error' in response:
                return None
                
            if 'choices' in response and len(response['choices']) > 0:
                text_response = response['choices'][0].get('message', {}).get('content', '')
                json_match = self._extract_json(text_response)
                if json_match:
                    recommendations = json.loads(json_match)
                    if isinstance(recommendations, list):
                        return recommendations
        except Exception as e:
            print(f"GigaChat advice generation error: {str(e)}")
        
        return None
    
    def _extract_json(self, text: str) -> Optional[str]:
        """Извлечение JSON из текста ответа"""
        json_match = re.search(r'\[.*\]|\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group()
        return None
    
    def _normalize_emotions(self, emotions: Dict[str, float]) -> Dict[str, float]:
        """Нормализация эмоций (сумма должна быть ~1.0)"""
        total = sum(emotions.values())
        if total > 0:
            return {k: v / total for k, v in emotions.items()}
        return emotions
    
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


def analyze_emotions_with_fallback(text: str, context: Optional[str] = None) -> Dict[str, float]:
    """
    Анализ эмоций с fallback на простой анализ
    
    Args:
        text: Текст для анализа
        context: Дополнительный контекст
        
    Returns:
        Словарь с вероятностями эмоций
    """
    client = GigaChatAIClient()
    
    if client._is_available():
        result = client.analyze_emotions(text, context)
        if result:
            return result
    
    return _simple_emotion_analysis(text)


def generate_financial_advice_with_fallback(portfolio_data: Dict, analysis_type: str = "full") -> List[str]:
    """
    Генерация финансовых советов с fallback
    
    Args:
        portfolio_data: Данные портфеля
        analysis_type: Тип анализа
        
    Returns:
        Список рекомендаций
    """
    client = GigaChatAIClient()
    
    if client._is_available():
        result = client.generate_financial_advice(portfolio_data, analysis_type)
        if result:
            return result
    
    return _simple_financial_advice(portfolio_data, analysis_type)


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
