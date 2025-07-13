import pytest
from unittest.mock import patch, mock_open
from datetime import datetime
from typing import List, Dict, Any
from src.reports import process_transactions, save_to_file


# Тестовые данные
@pytest.fixture
def sample_transactions() -> List[Dict[str, Any]]:
    return [
        {"Дата операции": "01.01.2023 12:00:00", "Категория": "Еда", "Сумма платежа": -1000, "Описание": "Продукты"},
        {"Дата операции": "15.01.2023 09:30:00", "Категория": "Транспорт", "Сумма платежа": -500, "Описание": "Такси"},
        {"Дата операции": "20.01.2023 18:45:00", "Категория": "Еда", "Сумма платежа": -1500, "Описание": "Ресторан"},
        {"Дата операции": None, "Категория": "Еда", "Сумма платежа": -300, "Описание": "Кофе"},
        {"Дата операции": "invalid_date", "Категория": "Еда", "Сумма платежа": -400, "Описание": "Завтрак"},
        {"Дата операции": "10.01.2023 13:20:00", "Категория": "Еда", "Сумма платежа": -600, "Описание": "Обед"},
    ]


def test_filter_by_date_range(sample_transactions):
    """Тест фильтрации по диапазону дат (3 месяца от указанной даты)"""
    result = process_transactions(sample_transactions, "Еда", "2023-01-31")
    # Ожидаем 3 транзакции за январь 2023 (01.01, 10.01, 15.01, 20.01)
    assert len(result) == 3


def test_string_date_processing(sample_transactions):
    """Тест обработки строковых дат"""
    result = process_transactions(sample_transactions, "Еда", "2023-02-28")
    for t in result:
        if "Дата операции" in t and isinstance(t["Дата операции"], str):
            assert isinstance(parse_transaction_date(t["Дата операции"]), datetime)


def test_invalid_date_handling(sample_transactions):
    """Тест обработки некорректных дат"""
    # Добавляем явно невалидную дату
    sample_transactions.append(
        {
            "Дата операции": "invalid_date_123",
            "Категория": "Еда",
            "Сумма платежа": -100,
            "Описание": "Тестовая транзакция",
        }
    )

    result = process_transactions(sample_transactions, "Еда", "2023-02-28")

    # Проверяем, что невалидные даты не попали в результат
    invalid_transactions = [t for t in result if parse_transaction_date(t.get("Дата операции", "")) == datetime.min]
    assert len(invalid_transactions) == 0  # Невалидные даты должны отфильтровываться

    # Проверяем общее количество транзакций
    assert len(result) == 4  # Только валидные транзакции


def test_datetime_input_handling(sample_transactions):
    """Тест обработки дат в транзакциях"""
    result = process_transactions(sample_transactions, "Еда", "2023-01-31")
    dates = [parse_transaction_date(t["Дата операции"]) for t in result if t.get("Дата операции")]
    assert all(isinstance(d, datetime) for d in dates)


def test_empty_transactions_list():
    """Тест с пустым списком транзакций"""
    result = process_transactions([], "Еда", "2023-01-01")
    assert len(result) == 0


def test_negative_amount_filtering(sample_transactions):
    """Тест фильтрации по отрицательным суммам"""
    # Добавим положительную транзакцию
    sample_transactions.append(
        {"Дата операции": "15.01.2023 12:00:00", "Категория": "Еда", "Сумма платежа": 1000, "Описание": "Возврат"}
    )
    result = process_transactions(sample_transactions, "Еда", "2023-01-31")
    assert all(t["Сумма платежа"] < 0 for t in result)


# Вспомогательная функция для тестов
def parse_transaction_date(date_str: str) -> datetime:
    """Парсит дату транзакции из различных форматов (аналогичная той, что в reports.py)"""
    for fmt in ["%d.%m.%Y %H:%M:%S", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return datetime.min


# Тесты для декоратора save_to_file
def test_decorator_file_creation(tmp_path):
    """Тест создания файла декоратором"""
    test_file = tmp_path / "test_output.txt"

    @save_to_file(str(test_file))
    def test_func():
        return "test_result"

    test_func()

    assert test_file.exists()
    with open(test_file, "r", encoding="utf-8") as f:
        assert "test_result" in f.read()


def test_decorator_with_mocked_file():
    """Тест декоратора с моком файла"""
    mock_file = mock_open()

    with patch("builtins.open", mock_file):

        @save_to_file("test_output.txt")
        def test_func():
            return "test_result"

        result = test_func()

    assert result == "test_result"
    mock_file.assert_called_once_with("test_output.txt", "a", encoding="utf-8")
    mock_file().write.assert_called_once_with("test_result\n")
