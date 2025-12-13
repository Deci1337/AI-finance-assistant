"""Spending analytics service (deterministic calculations for chat requests)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class _Txn:
    date: datetime
    amount: float
    category: str
    title: str
    txn_type: str


class SpendingAnalyticsService:
    @staticmethod
    def try_answer(user_message: str, transactions: Optional[List[Dict]]) -> Optional[str]:
        if not transactions:
            return None

        message_lower = (user_message or "").lower()
        if not SpendingAnalyticsService._is_analytics_request(message_lower):
            return None

        txns = SpendingAnalyticsService._parse_transactions(transactions)
        if not txns:
            return "У вас пока нет транзакций для анализа."

        days = SpendingAnalyticsService._extract_days(message_lower) or 7
        percent = SpendingAnalyticsService._extract_percent(message_lower)

        now = datetime.now()
        start = (now.date() - timedelta(days=days - 1))
        end = now.date()

        cur = [t for t in txns if start <= t.date.date() <= end]
        if not cur:
            return f"За последние {days} дней нет расходов для анализа."

        cur_exp = [t for t in cur if t.txn_type == "expense" and t.amount > 0]
        cur_income = [t for t in cur if t.txn_type == "income" and t.amount > 0]

        total_exp = sum(t.amount for t in cur_exp)
        total_inc = sum(t.amount for t in cur_income)

        by_cat = SpendingAnalyticsService._sum_by_category(cur_exp)
        top_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:5]

        biggest = sorted(cur_exp, key=lambda t: t.amount, reverse=True)[:5]

        prev_start = (start - timedelta(days=days))
        prev_end = (start - timedelta(days=1))
        prev = [t for t in txns if prev_start <= t.date.date() <= prev_end and t.txn_type == "expense" and t.amount > 0]
        prev_total = sum(t.amount for t in prev)
        delta = total_exp - prev_total
        delta_pct = (delta / prev_total * 100.0) if prev_total > 0 else None

        lines: List[str] = []
        lines.append(f"Аналитика затрат за {days} дней ({start.strftime('%d.%m.%Y')}–{end.strftime('%d.%m.%Y')}):")
        lines.append(f"- Расходы: {SpendingAnalyticsService._fmt_money(total_exp)} RUB")
        if total_inc > 0:
            lines.append(f"- Доходы: {SpendingAnalyticsService._fmt_money(total_inc)} RUB")
        lines.append(f"- Среднее в день: {SpendingAnalyticsService._fmt_money(total_exp / max(days, 1))} RUB")

        if delta_pct is not None:
            trend = "выросли" if delta > 0 else "снизились"
            lines.append(
                f"- По сравнению с предыдущими {days} днями расходы {trend} на {SpendingAnalyticsService._fmt_money(abs(delta))} RUB ({abs(delta_pct):.1f}%)"
            )

        if top_cats:
            lines.append("")
            lines.append("Топ категорий по расходам:")
            for name, amt in top_cats:
                share = (amt / total_exp * 100.0) if total_exp > 0 else 0.0
                lines.append(f"- {name}: {SpendingAnalyticsService._fmt_money(amt)} RUB ({share:.1f}%)")

        if biggest:
            lines.append("")
            lines.append("Крупнейшие расходы:")
            for t in biggest:
                lines.append(f"- {t.date.strftime('%d.%m')}: {t.category} — {t.title} — {SpendingAnalyticsService._fmt_money(t.amount)} RUB")

        if percent is not None and total_exp > 0:
            lines.append("")
            lines.append(SpendingAnalyticsService._build_savings_plan(percent, total_exp, top_cats))
        elif any(keyword in message_lower for keyword in ["сократ", "эконом", "уменьш", "сниз"]):
            lines.append("")
            lines.append("Если хотите посчитать экономию, напишите целевой процент, например: 'сократить затраты на 10%' или 'уменьшить расходы на 20%'.")

        return "\n".join(lines).strip()

    @staticmethod
    def _is_analytics_request(message_lower: str) -> bool:
        keys = (
            "аналитик",
            "статистик",
            "сколько я потрат",
            "сколько потрат",
            "траты",
            "затрат",
            "расход",
            "где сэконом",
            "эконом",
            "сократ",
            "уменьш",
            "сниз",
            "сократ",
        )
        return any(k in message_lower for k in keys)

    @staticmethod
    def _extract_days(message_lower: str) -> Optional[int]:
        import re

        m = re.search(r"(\d{1,3})\s*(?:дн|дня|дней)\b", message_lower)
        if m:
            try:
                v = int(m.group(1))
                return v if 1 <= v <= 366 else None
            except Exception:
                return None
        if "за неделю" in message_lower or "за 7 дней" in message_lower:
            return 7
        if "за месяц" in message_lower or "за 30 дней" in message_lower:
            return 30
        return None

    @staticmethod
    def _extract_percent(message_lower: str) -> Optional[float]:
        import re

        # Различные паттерны для поиска процента
        patterns = [
            r"сократ[итьи]*\s+[на]*\s*(\d+(?:[.,]\d+)?)\s*%",  # "сократить на 30%"
            r"уменьш[итьи]*\s+[на]*\s*(\d+(?:[.,]\d+)?)\s*%",  # "уменьшить на 25%"
            r"сниз[итьи]*\s+[на]*\s*(\d+(?:[.,]\d+)?)\s*%",   # "снизить на 20%"
            r"эконом[итьи]*\s+[на]*\s*(\d+(?:[.,]\d+)?)\s*%",  # "сэкономить на 15%"
            r"(\d+(?:[.,]\d+)?)\s*%\s*(?:сократ|уменьш|сниз|эконом)",  # "30% сократить"
            r"на\s*(\d+(?:[.,]\d+)?)\s*%",  # "на 30%"
            r"(\d+(?:[.,]\d+)?)\s*%\b",  # Просто "30%"
        ]
        
        for pattern in patterns:
            m = re.search(pattern, message_lower)
            if m:
                try:
                    v = float(m.group(1).replace(",", "."))
                    if 0 < v < 100:
                        return v
                except Exception:
                    continue
        
        return None

    @staticmethod
    def _parse_transactions(transactions: List[Dict]) -> List[_Txn]:
        parsed: List[_Txn] = []
        for t in transactions:
            try:
                date_raw = str(t.get("date") or "")
                if not date_raw:
                    continue
                # supports "YYYY-MM-DD" and ISO datetime
                if "T" in date_raw:
                    dt = datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
                else:
                    dt = datetime.strptime(date_raw[:10], "%Y-%m-%d")

                amount = float(t.get("amount") or 0)
                txn_type = str(t.get("type") or "").lower()
                if txn_type not in ("expense", "income"):
                    continue
                category = str(t.get("category") or "Other")
                title = str(t.get("title") or "")

                parsed.append(_Txn(date=dt, amount=amount, category=category, title=title, txn_type=txn_type))
            except Exception:
                continue
        return parsed

    @staticmethod
    def _sum_by_category(expenses: List[_Txn]) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for t in expenses:
            out[t.category] = out.get(t.category, 0.0) + float(t.amount)
        return out

    @staticmethod
    def _build_savings_plan(percent: float, total_exp: float, top_cats: List[Tuple[str, float]]) -> str:
        target = total_exp * (1.0 - percent / 100.0)
        savings = total_exp - target
        lines: List[str] = []
        lines.append(f"План экономии (сократить расходы на {percent:.1f}%):")
        lines.append(f"- Цель по расходам: {SpendingAnalyticsService._fmt_money(target)} RUB")
        lines.append(f"- Экономия: {SpendingAnalyticsService._fmt_money(savings)} RUB")

        if top_cats:
            lines.append("Как можно распределить сокращение по топ-категориям (пропорционально доле):")
            for name, amt in top_cats[:3]:
                cut = amt * (percent / 100.0)
                new_amt = amt - cut
                lines.append(
                    f"- {name}: было {SpendingAnalyticsService._fmt_money(amt)} → станет {SpendingAnalyticsService._fmt_money(new_amt)} (экономия {SpendingAnalyticsService._fmt_money(cut)})"
                )
        return "\n".join(lines)

    @staticmethod
    def _fmt_money(v: float) -> str:
        return f"{v:,.0f}".replace(",", " ")


