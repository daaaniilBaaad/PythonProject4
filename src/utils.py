import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import requests
from pandas import DataFrame

from src.config import API_KEY_CURRENCIES, API_KEY_Stocks, URL_Currense, URL_Stocks
from src.logger_config import get_logger

logger = get_logger("utils")


def get_time_for_greeting(date_time: str) -> str:
    """Функция возвращает приветствие в зависимости от текущего времени"""
    current_time = datetime.strptime(date_time, "%Y-%m-%d %H:%M:%S")
    hour = current_time.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_data_time(date_time: str, date_format: str = "%Y-%m-%d %H:%M:%S") -> list[str]:
    """Возвращает начало месяца и переданную дату в формате DD.MM.YYYY HH:MM:SS"""
    dt = datetime.strptime(date_time, date_format)
    start_of_month = dt.replace(day=1)

    formatted_start_of_month = start_of_month.strftime("%d.%m.%Y %H:%M:%S")
    formatted_date_time = dt.strftime("%d.%m.%Y %H:%M:%S")

    return [formatted_start_of_month, formatted_date_time]


def get_path_and_period(path_fo_file: str, period_date: list) -> DataFrame:
    """
    Функция принимает путь к Excel файлу и список дат,
    и возвращает таблицу в заданном периоде
    """
    df = pd.read_excel(path_fo_file, sheet_name="Отчет по операциям")

    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
    start_date = datetime.strptime(period_date[0], "%d.%m.%Y %H:%M:%S")
    end_date = datetime.strptime(period_date[1], "%d.%m.%Y %H:%M:%S")

    filtered_df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]
    sorted_df = filtered_df.sort_values(by="Дата операции", ascending=True)
    return sorted_df


def get_card_with_spend(sorted_df: DataFrame) -> list[dict[str, Any]]:
    """
    Функция принимает DataFrame и возвращает список карт с расходами
    """
    card_spent_transactions = []

    # Фильтруем только операции с расходами (отрицательные значения)
    expenses_df = sorted_df[sorted_df["Сумма операции"] < 0].copy()

    # Группируем по номеру карты и суммируем показатели
    grouped = (
        expenses_df.groupby("Номер карты").agg({"Сумма операции с округлением": "sum", "Кэшбэк": "sum"}).reset_index()
    )

    # Создаем список словарей с агрегированными данными
    for _, row in grouped.iterrows():
        last_digits = str(row["Номер карты"]).replace("*", "")
        total_spent = abs(row["Сумма операции с округлением"])
        cashback = row["Кэшбэк"]

        card_row = {
            "last_digits": last_digits,
            "total_spent": total_spent,
            "cashback": cashback,
        }
        card_spent_transactions.append(card_row)

    return card_spent_transactions


def get_top_transactions(sorted_df: DataFrame, get_top: int) -> List[Dict[str, str]]:
    """
    Функция принмает DataFrame и возвращает get_top Топ-транзакций по sum платежа
    """
    top_pay_transactions: List[Dict[str, str]] = []
    sorted_pay_df = sorted_df.sort_values(by="Сумма операции", ascending=False)
    top_transactions = sorted_pay_df.head(get_top)
    top_transactions_sorted = top_transactions[["Дата платежа", "Сумма операции", "Категория", "Описание"]]

    for index, row in top_transactions_sorted.iterrows():
        transaction = {
            "date": f"{row['Дата платежа']}",
            "amount": f"{row['Сумма операции']}",
            "category": f"{row['Категория']}",
            "description": f"{row['Описание']}",
        }
        top_pay_transactions.append(transaction)
    logger.info("возвращает топ-транзакций по sum платежа")
    return top_pay_transactions


def get_currency(path_to_json: str) -> list[dict[str, str]]:
    """
    Функция принимает на вход переменную path_to_json и возвращает Курс-валют
    """
    currency_rates: list[dict[str, str]] = []
    with open(path_to_json, "r", encoding="utf-8") as file:
        data: Dict[str, Any] = json.load(file)
        currences = data["user_currencies"]

        for currence in currences:
            # Явно преобразуем все значения в строки и проверяем на None
            amount_str = str(1)
            from_currency = str(currence)
            to_currency = "RUB"
            api_key = str(API_KEY_CURRENCIES) if API_KEY_CURRENCIES else ""

            params = {"amount": amount_str, "from": from_currency, "to": to_currency}
            headers = {"apikey": api_key}

            response = requests.get(URL_Currense, headers=headers, params=params)

            if response.status_code == 200:
                result = response.json()
                currency_code_response = str(result["query"]["from"])
                currency_amount = round(result["result"], 2)
                currency_rates.append(
                    {
                        "currency": currency_code_response,
                        "rate": str(currency_amount),
                    }
                )

    return currency_rates


def get_stock(path_to_json: str) -> List[Dict[str, str]]:
    """Функция принимает файл json и выдает список словарей
    с содержанием акций и их актуальной стоимостью
    """
    stock_rates: List[Dict[str, str]] = []
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    with open(path_to_json, "r", encoding="utf-8") as file:
        data: Dict[str, Any] = json.load(file)
        stocks: List[str] = data["user_stocks"]

        for stock in stocks:
            # Явно преобразуем все значения в строки и проверяем на None
            function = "TIME_SERIES_DAILY"
            symbol = str(stock)
            api_key = str(API_KEY_Stocks) if API_KEY_Stocks else ""

            params = {"function": function, "symbol": symbol, "apikey": api_key}

            try:
                response = requests.get(URL_Stocks, params=params)
                response.raise_for_status()

                result = response.json()
                daily_data = result.get("Time Series (Daily)", {})

                if yesterday in daily_data:
                    price = str(daily_data[yesterday]["1. open"])
                    stock_rates.append({"stock": symbol, "price": price})
                else:
                    logger.warning(f"Дата {yesterday} отсутствует в ответе API для {stock}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при запросе данных акции {stock}: {str(e)}")

    return stock_rates
