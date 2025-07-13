import json
from unittest.mock import patch
import pytest
import pandas as pd
from src.views import main_info


@pytest.fixture
def mock_data():
    return {
        "greeting": "Добрый день",
        "cards": [{"card": "*1234", "spend": 1000}, {"card": "*5678", "spend": 2000}],
        "top_transactions": [
            {"Дата": "2023-01-01", "Сумма": 5000, "Категория": "Авиабилеты"},
            {"Дата": "2023-01-02", "Сумма": 4000, "Категория": "Отели"},
        ],
        "currency_rates": {"USD": 75.50, "EUR": 85.30},
        "stock_prices": {"AAPL": 150.25, "GOOGL": 2500.75},
    }


@pytest.fixture
def mock_df():
    data = {
        "Дата операции": ["2023-01-01", "2023-01-02"],
        "Номер карты": ["*1234", "*5678"],
        "Сумма платежа": [-1000, -2000],
        "Категория": ["Супермаркеты", "АЗС"],
    }
    return pd.DataFrame(data)


def test_main_info_success(mock_data, mock_df):
    """Тест успешного выполнения функции main_info"""
    with patch("src.views.get_data_time", return_value=("2023-01-01", "2023-01-31")) as mock_time, patch(
        "src.views.get_path_and_period", return_value=mock_df
    ) as mock_period, patch(
        "src.views.get_time_for_greeting", return_value=mock_data["greeting"]
    ) as mock_greeting, patch(
        "src.views.get_card_with_spend", return_value=mock_data["cards"]
    ) as mock_cards, patch(
        "src.views.get_top_transactions", return_value=mock_data["top_transactions"]
    ) as mock_top, patch(
        "src.views.get_currency", return_value=mock_data["currency_rates"]
    ) as mock_currency, patch(
        "src.views.get_stock", return_value=mock_data["stock_prices"]
    ) as mock_stock:
        result = main_info("2023-01-15 12:00:00")
        data = json.loads(result)

        assert data["greeting"] == mock_data["greeting"]
        assert data["cards"] == mock_data["cards"]
        assert data["top_transactions"] == mock_data["top_transactions"]
        assert data["currency_rates"] == mock_data["currency_rates"]
        assert data["stock_prices"] == mock_data["stock_prices"]

        mock_time.assert_called_once_with("2023-01-15 12:00:00")
        mock_period.assert_called_once()
        mock_greeting.assert_called_once_with("2023-01-15 12:00:00")
        mock_cards.assert_called_once_with(mock_df)
        mock_top.assert_called_once_with(mock_df, 5)
        mock_currency.assert_called_once()
        mock_stock.assert_called_once()


def test_main_info_empty_data():
    """Тест с пустыми данными"""
    with patch("src.views.get_data_time", return_value=("2023-01-01", "2023-01-31")), patch(
        "src.views.get_path_and_period", return_value=pd.DataFrame()
    ), patch("src.views.get_time_for_greeting", return_value=""), patch(
        "src.views.get_card_with_spend", return_value=[]
    ), patch(
        "src.views.get_top_transactions", return_value=[]
    ), patch(
        "src.views.get_currency", return_value={}
    ), patch(
        "src.views.get_stock", return_value={}
    ):
        result = main_info("2023-01-15 12:00:00")
        data = json.loads(result)

        assert data["greeting"] == ""
        assert data["cards"] == []
        assert data["top_transactions"] == []
        assert data["currency_rates"] == {}
        assert data["stock_prices"] == {}


def test_main_info_invalid_input():
    """Тест с невалидным вводом"""
    with pytest.raises(Exception):
        main_info("invalid_date_format")


def test_main_info_json_output(mock_data, mock_df):
    """Тест корректности JSON вывода"""
    with patch("src.views.get_data_time", return_value=("2023-01-01", "2023-01-31")), patch(
        "src.views.get_path_and_period", return_value=mock_df
    ), patch("src.views.get_time_for_greeting", return_value=mock_data["greeting"]), patch(
        "src.views.get_card_with_spend", return_value=mock_data["cards"]
    ), patch(
        "src.views.get_top_transactions", return_value=mock_data["top_transactions"]
    ), patch(
        "src.views.get_currency", return_value=mock_data["currency_rates"]
    ), patch(
        "src.views.get_stock", return_value=mock_data["stock_prices"]
    ):
        result = main_info("2023-01-15 12:00:00")

        # Проверяем что вывод является валидным JSON
        data = json.loads(result)
        assert isinstance(data, dict)

        # Проверяем наличие всех ожидаемых ключей
        expected_keys = ["greeting", "cards", "top_transactions", "currency_rates", "stock_prices"]
        assert all(key in data for key in expected_keys)


def test_main_info_partial_data(mock_df):
    """Тест с частичными данными"""
    partial_data = {
        "greeting": "Добрый вечер",
        "cards": [],
        "top_transactions": None,
        "currency_rates": {"USD": 75.50},
        "stock_prices": {},
    }

    with patch("src.views.get_data_time", return_value=("2023-01-01", "2023-01-31")), patch(
        "src.views.get_path_and_period", return_value=mock_df
    ), patch("src.views.get_time_for_greeting", return_value=partial_data["greeting"]), patch(
        "src.views.get_card_with_spend", return_value=partial_data["cards"]
    ), patch(
        "src.views.get_top_transactions", return_value=partial_data["top_transactions"]
    ), patch(
        "src.views.get_currency", return_value=partial_data["currency_rates"]
    ), patch(
        "src.views.get_stock", return_value=partial_data["stock_prices"]
    ):
        result = main_info("2023-01-15 20:00:00")
        data = json.loads(result)

        assert data["greeting"] == "Добрый вечер"
        assert data["cards"] == []
        assert data["top_transactions"] is None
        assert data["currency_rates"] == {"USD": 75.50}
        assert data["stock_prices"] == {}
