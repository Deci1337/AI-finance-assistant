"""
Mock данные для тестирования и разработки
"""

from typing import Dict, List
from datetime import datetime, timedelta

# Mock данные портфеля
MOCK_PORTFOLIO_DATA = {
    "total_value": 125000.0,
    "currency": "RUB",
    "assets": [
        {
            "id": "AAPL",
            "name": "Apple Inc.",
            "type": "stock",
            "quantity": 50,
            "current_price": 175.50,
            "purchase_price": 165.00,
            "value": 8775.0,
            "weight": 0.07,
            "sector": "Technology",
            "change_percent": 6.36
        },
        {
            "id": "MSFT",
            "name": "Microsoft Corporation",
            "type": "stock",
            "quantity": 30,
            "current_price": 380.25,
            "purchase_price": 350.00,
            "value": 11407.5,
            "weight": 0.09,
            "sector": "Technology",
            "change_percent": 8.64
        },
        {
            "id": "GOOGL",
            "name": "Alphabet Inc.",
            "type": "stock",
            "quantity": 20,
            "current_price": 142.80,
            "purchase_price": 135.00,
            "value": 2856.0,
            "weight": 0.023,
            "sector": "Technology",
            "change_percent": 5.78
        },
        {
            "id": "SBER",
            "name": "Сбербанк",
            "type": "stock",
            "quantity": 100,
            "current_price": 285.50,
            "purchase_price": 270.00,
            "value": 28550.0,
            "weight": 0.23,
            "sector": "Finance",
            "change_percent": 5.74
        },
        {
            "id": "GAZP",
            "name": "Газпром",
            "type": "stock",
            "quantity": 200,
            "current_price": 165.30,
            "purchase_price": 180.00,
            "value": 33060.0,
            "weight": 0.26,
            "sector": "Energy",
            "change_percent": -8.17
        },
        {
            "id": "BOND_RU_001",
            "name": "ОФЗ 26207",
            "type": "bond",
            "quantity": 10,
            "current_price": 985.50,
            "purchase_price": 1000.00,
            "value": 9855.0,
            "weight": 0.079,
            "sector": "Government",
            "yield": 7.5,
            "maturity_date": "2025-12-31"
        },
        {
            "id": "BOND_RU_002",
            "name": "ОФЗ 26238",
            "type": "bond",
            "quantity": 15,
            "current_price": 1020.00,
            "purchase_price": 1000.00,
            "value": 15300.0,
            "weight": 0.122,
            "sector": "Government",
            "yield": 6.8,
            "maturity_date": "2026-06-30"
        },
        {
            "id": "CASH",
            "name": "Наличные средства",
            "type": "cash",
            "quantity": 1,
            "current_price": 1.0,
            "purchase_price": 1.0,
            "value": 10196.5,
            "weight": 0.082,
            "sector": "Cash"
        }
    ],
    "summary": {
        "stocks_value": 80648.5,
        "bonds_value": 25155.0,
        "cash_value": 10196.5,
        "total_value": 125000.0,
        "total_cost": 118500.0,
        "total_profit": 6500.0,
        "profit_percent": 5.49
    },
    "risk_metrics": {
        "volatility": 0.18,
        "beta": 1.12,
        "sharpe_ratio": 0.85,
        "max_drawdown": -0.12
    },
    "diversification": {
        "sectors": {
            "Technology": 0.183,
            "Finance": 0.23,
            "Energy": 0.26,
            "Government": 0.201,
            "Cash": 0.082
        },
        "asset_types": {
            "stocks": 0.645,
            "bonds": 0.201,
            "cash": 0.082
        }
    },
    "last_updated": (datetime.now() - timedelta(hours=1)).isoformat()
}


def get_mock_portfolio() -> Dict:
    """Возвращает mock данные портфеля"""
    return MOCK_PORTFOLIO_DATA.copy()


def calculate_portfolio_metrics(portfolio_data: Dict) -> Dict:
    """
    Вычисляет метрики портфеля на основе данных
    
    Args:
        portfolio_data: Данные портфеля
        
    Returns:
        Словарь с вычисленными метриками
    """
    if not portfolio_data or "assets" not in portfolio_data:
        portfolio_data = get_mock_portfolio()
    
    assets = portfolio_data.get("assets", [])
    
    # Расчет общей стоимости
    total_value = sum(asset.get("value", 0) for asset in assets)
    
    # Расчет общего риска (на основе волатильности активов)
    risk_scores = {
        "stock": 0.7,
        "bond": 0.3,
        "cash": 0.0
    }
    
    weighted_risk = 0.0
    for asset in assets:
        asset_type = asset.get("type", "stock")
        weight = asset.get("weight", 0)
        risk = risk_scores.get(asset_type, 0.5)
        weighted_risk += weight * risk
    
    # Расчет рекомендаций
    recommendations = []
    
    # Проверка диверсификации
    stocks_weight = sum(
        asset.get("weight", 0) 
        for asset in assets 
        if asset.get("type") == "stock"
    )
    bonds_weight = sum(
        asset.get("weight", 0) 
        for asset in assets 
        if asset.get("type") == "bond"
    )
    
    if stocks_weight > 0.7:
        recommendations.append("Высокая доля акций. Рекомендуется увеличить долю облигаций для снижения риска.")
    
    if bonds_weight > 0.5:
        recommendations.append("Высокая доля облигаций. Рассмотрите возможность увеличения доли акций для роста.")
    
    # Проверка концентрации по секторам
    sectors = {}
    for asset in assets:
        sector = asset.get("sector", "Unknown")
        weight = asset.get("weight", 0)
        sectors[sector] = sectors.get(sector, 0) + weight
    
    max_sector_weight = max(sectors.values()) if sectors else 0
    if max_sector_weight > 0.4:
        recommendations.append(f"Высокая концентрация в одном секторе ({max_sector_weight:.1%}). Рекомендуется диверсификация.")
    
    # Общие рекомендации
    if not recommendations:
        recommendations.append("Портфель хорошо диверсифицирован.")
    
    if weighted_risk > 0.6:
        recommendations.append("Высокий уровень риска. Рассмотрите возможность консервативных инвестиций.")
    elif weighted_risk < 0.3:
        recommendations.append("Низкий уровень риска. Возможен переход к более агрессивной стратегии.")
    
    return {
        "portfolio_value": total_value,
        "risk_score": min(weighted_risk, 1.0),
        "recommendations": recommendations,
        "assets_count": len(assets),
        "sectors_distribution": sectors
    }

