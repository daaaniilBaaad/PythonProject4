import pandas as pd

from src.config import PATH_TO_XLSX
from src.reports import process_transactions
from src.services import analise_cashback
from src.views import main_info

if __name__ == "__main__":
    print(main_info("2018-05-20 15:30:00"))

    # Загрузка данных из Excel и преобразование в список словарей
    data = pd.read_excel(PATH_TO_XLSX).to_dict("records")

    # Анализ кэшбэка
    result = analise_cashback(data, 2018, 5)
    with open("cashback_results.json", "w", encoding="utf-8") as f:
        f.write(result)

    # Анализ трат по категории
    process_transactions(data, "Супермаркеты", "2021-12-29")
