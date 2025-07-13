import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
import json
from src.utils import (
    get_time_for_greeting,
    get_path_and_period,
    get_card_with_spend,
    get_top_transactions,
    get_currency,
    get_stock,
)


# Тестовые данные
@pytest.fixture
def sample_excel_file(tmp_path):
    """Создает тестовый Excel файл"""
    data = {
        "Дата операции": ["01.01.2023", "15.01.2023", "31.01.2023", "01.02.2023"],
        "Номер карты": ["1234****5678", "8765****4321", "1234****5678", "9999****8888"],
        "Сумма операции": [100, -200, -300, 400],
        "Кэшбэк": [1, 2, 3, 4],
        "Сумма операции с округлением": [100, -200, -300, 400],
        "Дата платежа": ["01.01.2023", "15.01.2023", "31.01.2023", "01.02.2023"],
        "Категория": ["Food", "Transport", "Shopping", "Entertainment"],
        "Описание": ["Lunch", "Taxi", "Clothes", "Cinema"],
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "test_data.xlsx"
    df.to_excel(file_path, sheet_name="Отчет по операциям", index=False)
    return file_path


@pytest.fixture
def sample_json_file(tmp_path):
    """Создает тестовый JSON файл"""
    data = {"user_currencies": ["USD", "EUR"], "user_stocks": ["AAPL", "GOOGL"]}
    file_path = tmp_path / "test_data.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    return file_path


# Тесты для функций
@pytest.mark.parametrize(
    "time, expected",
    [
        ("2023-01-01 05:00:00", "Доброе утро"),
        ("2023-01-01 11:59:59", "Доброе утро"),
        ("2023-01-01 12:00:00", "Добрый день"),
        ("2023-01-01 17:59:59", "Добрый день"),
        ("2023-01-01 18:00:00", "Добрый вечер"),
        ("2023-01-01 21:59:59", "Добрый вечер"),
        ("2023-01-01 22:00:00", "Доброй ночи"),
        ("2023-01-01 04:59:59", "Доброй ночи"),
    ],
)
def test_get_time_for_greeting(time, expected):
    assert get_time_for_greeting(time) == expected


@pytest.mark.parametrize(
    "date_time, date_format, expected",
    [
        ("2023-01-15 12:30:45", "%Y-%m-%d %H:%M:%S", ["01.01.2023 00:00:00", "15.01.2023 12:30:45"]),
        ("2023-02-28 23:59:59", "%Y-%m-%d %H:%M:%S", ["01.02.2023 00:00:00", "28.02.2023 23:59:59"]),
    ],
)
def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Возвращает начало месяца (с временем 00:00:00) и переданную дату в формате DD.MM.YYYY HH:MM:SS"""
    dt = datetime.strptime(date_time, date_format)

    # Начало месяца с временем 00:00:00
    start_of_month = dt.replace(day=1, hour=0, minute=0, second=0)

    formatted_start_of_month = start_of_month.strftime("%d.%m.%Y %H:%M:%S")
    formatted_date_time = dt.strftime("%d.%m.%Y %H:%M:%S")

    return [formatted_start_of_month, formatted_date_time]


def test_get_path_and_period(sample_excel_file):
    period = ["01.01.2023 00:00:00", "31.01.2023 23:59:59"]
    result = get_path_and_period(str(sample_excel_file), period)
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3  # Три операции в январе
    assert all(result["Дата операции"].dt.month == 1)


def test_get_card_with_spend(sample_excel_file):
    period = ["01.01.2023 00:00:00", "31.01.2023 23:59:59"]
    df = get_path_and_period(str(sample_excel_file), period)
    result = get_card_with_spend(df)
    assert len(result) == 2  # Две карты с расходами
    assert all(item["total_spent"] > 0 for item in result)


@pytest.mark.parametrize("top_n", [1, 2, 3])
def test_get_top_transactions(sample_excel_file, top_n):
    period = ["01.01.2023 00:00:00", "31.01.2023 23:59:59"]
    df = get_path_and_period(str(sample_excel_file), period)
    result = get_top_transactions(df, top_n)
    assert len(result) == min(top_n, len(df))
    assert all("amount" in item for item in result)


@patch("src.utils.requests.request")
def test_get_currency(mock_request, sample_json_file):
    # Настраиваем мок для API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"query": {"from": "USD"}, "result": 75.50}
    mock_request.return_value = mock_response

    result = get_currency(str(sample_json_file))
    assert len(result) == 2  # USD и EUR
    assert any(item["currency"] == "USD" for item in result)
    assert any(item["rate"] == "75.5" for item in result)


@patch("src.utils.requests.request")
@patch("src.utils.datetime")
def test_get_stock(mock_datetime, mock_request, sample_json_file):
    # Настраиваем мок для даты
    mock_datetime.now.return_value = datetime(2023, 1, 15)
    mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

    # Настраиваем мок для API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Time Series (Daily)": {"2023-01-14": {"1. open": "150.50"}, "2023-01-13": {"1. open": "149.75"}}
    }
    mock_request.return_value = mock_response

    result = get_stock(str(sample_json_file))
    assert len(result) == 2  # AAPL и GOOGL
    assert any("AAPL" in item for item in result)


def test_empty_data_handling(tmp_path):
    # Тест для пустых данных
    empty_file = tmp_path / "empty.xlsx"
    with pd.ExcelWriter(empty_file) as writer:
        pd.DataFrame(
            columns=[
                "Дата операции",
                "Номер карты",
                "Сумма операции",
                "Кэшбэк",
                "Сумма операции с округлением",
                "Дата платежа",
                "Категория",
                "Описание",
            ]
        ).to_excel(writer, sheet_name="Отчет по операциям", index=False)

    period = ["01.01.2023 00:00:00", "31.01.2023 23:59:59"]
    result = get_path_and_period(str(empty_file), period)
    assert result.empty


@patch("src.utils.requests.request")
def test_get_currency_api_error(mock_request, sample_json_file):
    # Тест обработки ошибки API
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_request.return_value = mock_response

    result = get_currency(str(sample_json_file))
    assert result == []


def test_invalid_json_handling(tmp_path):
    # Тест обработки невалидного JSON
    invalid_json = tmp_path / "invalid.json"
    with open(invalid_json, "w") as f:
        f.write("{invalid json}")

    with pytest.raises(json.JSONDecodeError):
        get_currency(str(invalid_json))
