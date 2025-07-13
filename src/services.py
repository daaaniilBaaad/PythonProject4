import json
from datetime import datetime
from typing import Dict


def analise_cashback(transactions: list[dict], year: int, month: int) -> str:
    """
    позволяет проанализировать,
    какие категории были наиболее выгодными для выбора в качестве категорий повышенного кешбэка
    """

    def is_valid_transaction(transaction_data: dict) -> bool:
        try:
            date_str = transaction_data["Дата операции"]
            operation_date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
            is_correct_date = operation_date.year == year and operation_date.month == month

            payment_amount = float(transaction_data["Сумма платежа"])
            is_negative = payment_amount < 0

            bonuses = float(transaction_data.get("Бонусы (включая кэшбэк)", 0))
            has_bonuses = bonuses > 0

            return is_correct_date and is_negative and has_bonuses
        except (KeyError, ValueError, TypeError):
            return False

    cashback_by_category: Dict[str, float] = {}

    for tr in transactions:
        if is_valid_transaction(tr):
            try:
                category = tr["Категория"]
                cashback = float(tr.get("Бонусы (включая кэшбэк)", 0))
                cashback_by_category[category] = cashback_by_category.get(category, 0) + cashback
            except (KeyError, ValueError, TypeError):
                continue

    return json.dumps(cashback_by_category, ensure_ascii=False, indent=4)
