import json
import pytest
from src.services import analise_cashback


@pytest.fixture
def sample_transactions():
    return [
        {
            "Дата операции": "15.05.2023 12:00:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "-1000.50",
            "Бонусы (включая кэшбэк)": "50.25",
        },
        {
            "Дата операции": "20.05.2023 14:30:00",
            "Категория": "АЗС",
            "Сумма платежа": "-5000",
            "Бонусы (включая кэшбэк)": 250,
        },
        {
            "Дата операции": "15.06.2023 10:15:00",
            "Категория": "Рестораны",
            "Сумма платежа": "-1500",
            "Бонусы (включая кэшбэк)": 75,
        },
    ]


def test_valid_transactions(sample_transactions):
    """Тест корректных транзакций"""
    result = analise_cashback(sample_transactions, 2023, 5)
    data = json.loads(result)
    assert data == {"Супермаркеты": 50.25, "АЗС": 250.0}


def test_wrong_date_format():
    """Тест с неправильным форматом даты"""
    transactions = [
        {
            "Дата операции": "2023/05/15 12:00:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "-1000",
            "Бонусы (включая кэшбэк)": 50,
        }
    ]
    result = analise_cashback(transactions, 2023, 5)
    assert json.loads(result) == {}


def test_missing_required_fields():
    """Тест с отсутствующими обязательными полями"""
    transactions = [
        {"Категория": "Супермаркеты", "Сумма платежа": "-1000"},
        {"Дата операции": "15.05.2023 12:00:00", "Сумма платежа": "-1000"},
        {"Дата операции": "15.05.2023 12:00:00", "Категория": "Супермаркеты"},
    ]
    result = analise_cashback(transactions, 2023, 5)
    assert json.loads(result) == {}


def test_non_negative_payment():
    """Тест с неотрицательной суммой платежа"""
    transactions = [
        {
            "Дата операции": "15.05.2023 12:00:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "1000",
            "Бонусы (включая кэшбэк)": 50,
        }
    ]
    result = analise_cashback(transactions, 2023, 5)
    assert json.loads(result) == {}


def test_zero_bonuses():
    """Тест с нулевыми бонусами"""
    transactions = [
        {
            "Дата операции": "15.05.2023 12:00:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "-1000",
            "Бонусы (включая кэшбэк)": 0,
        }
    ]
    result = analise_cashback(transactions, 2023, 5)
    assert json.loads(result) == {}


def test_string_numeric_values():
    """Тест со строковыми числовыми значениями"""
    transactions = [
        {
            "Дата операции": "15.05.2023 12:00:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "-1000.50",
            "Бонусы (включая кэшбэк)": "50.25",
        }
    ]
    result = analise_cashback(transactions, 2023, 5)
    data = json.loads(result)
    assert data == {"Супермаркеты": 50.25}


def test_multiple_same_category(sample_transactions):
    """Тест нескольких транзакций одной категории"""
    sample_transactions.append(
        {
            "Дата операции": "25.05.2023 18:45:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "-2000",
            "Бонусы (включая кэшбэк)": 100,
        }
    )
    result = analise_cashback(sample_transactions, 2023, 5)
    data = json.loads(result)
    assert data["Супермаркеты"] == 150.25


def test_empty_transactions():
    """Тест с пустым списком транзакций"""
    result = analise_cashback([], 2023, 5)
    assert json.loads(result) == {}


def test_invalid_numeric_values():
    """Тест с нечисловыми значениями сумм"""
    transactions = [
        {
            "Дата операции": "15.05.2023 12:00:00",
            "Категория": "Супермаркеты",
            "Сумма платежа": "invalid",
            "Бонусы (включая кэшбэк)": "50",
        }
    ]
    result = analise_cashback(transactions, 2023, 5)
    assert json.loads(result) == {}


def test_partial_invalid_transactions(sample_transactions):
    """Тест с частично невалидными транзакциями"""
    sample_transactions.append(
        {"Дата операции": "invalid_date", "Категория": "Такси", "Сумма платежа": "-500", "Бонусы (включая кэшбэк)": 25}
    )
    result = analise_cashback(sample_transactions, 2023, 5)
    data = json.loads(result)
    assert "Такси" not in data
    assert len(data) == 2
