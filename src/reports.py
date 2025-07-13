import json
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, TypeVar, Union

import pandas as pd

# Настройка логгера
logger = logging.getLogger("reports")
logger.setLevel(logging.INFO)

# Типы для аннотаций
Transaction = Dict[str, Any]
T = TypeVar("T")


def save_to_file(filename: str = "default_report.txt") -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Декоратор для сохранения результатов отчетов в файл"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            result = func(*args, **kwargs)

            try:
                if isinstance(result, (dict, list)):
                    with open(filename, "w", encoding="utf-8") as f:
                        json.dump(result, f, ensure_ascii=False, indent=4)
                else:
                    with open(filename, "a", encoding="utf-8") as f:
                        f.write(str(result) + "\n")
                logger.info(f"Отчет сохранен в файл: {filename}")
            except Exception as e:
                logger.error(f"Ошибка при сохранении отчета: {str(e)}")

            return result

        return wrapper

    return decorator


def parse_transaction_date(date_str: str) -> datetime:
    """Парсит дату транзакции из различных форматов"""
    try:
        # Пробуем разные форматы дат
        for fmt in ["%d.%m.%Y %H:%M:%S", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        logger.warning(f"Не удалось распознать дату: {date_str}")
        return datetime.min
    except Exception as e:
        logger.error(f"Ошибка парсинга даты: {str(e)}")
        return datetime.min


@save_to_file("category_spending_report.json")
def process_transactions(
    transactions: Union[pd.DataFrame, List[Transaction]], category: str, date: Union[str, datetime, None] = None
) -> List[Transaction]:
    try:
        # 1. Определяем конечную дату периода
        end_date = (
            datetime.now()
            if date is None
            else (datetime.strptime(date, "%Y-%m-%d") if isinstance(date, str) else date)
        )

        # 2. Вычисляем дату 3 месяца назад
        start_date = end_date - timedelta(days=90)

        # 3. Конвертируем DataFrame в список словарей с явным приведением типов
        if isinstance(transactions, pd.DataFrame):
            transactions = [
                {str(k): v for k, v in d.items()}  # Гарантируем строковые ключи
                for d in transactions.where(pd.notnull(transactions), None).to_dict("records")
            ]

        # 4. Фильтрация транзакций
        filtered_transactions: List[Transaction] = []
        for transaction in transactions:
            try:
                # Проверка категории
                if str(transaction.get("Категория", "")).strip() != str(category).strip():
                    continue

                # Парсинг даты
                date_str = transaction.get("Дата операции")
                if not date_str:
                    continue

                transaction_date = parse_transaction_date(str(date_str))

                # Проверка даты и суммы
                if start_date <= transaction_date <= end_date and float(transaction.get("Сумма платежа", 0)) < 0:
                    filtered_transactions.append(transaction)

            except Exception as e:
                logger.warning(f"Ошибка обработки транзакции: {str(e)}")
                continue

        logger.info(f"Найдено {len(filtered_transactions)} транзакций по категории '{category}'")
        return filtered_transactions

    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
        return []
