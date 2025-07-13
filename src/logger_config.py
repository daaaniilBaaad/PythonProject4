import logging
from pathlib import Path

# Определяем абсолютный путь к директории логов
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"


def setup_logging() -> None:
    """Настройка системы логирования для всего проекта"""
    LOG_DIR.mkdir(exist_ok=True)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Обработчик для общего файла логов
    main_handler = logging.FileHandler(LOG_DIR / "project.log", encoding="utf-8")
    main_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    root_logger.addHandler(main_handler)


def get_logger(name: str) -> logging.Logger:
    """Возвращает настроенный логгер для модуля"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)  # Важно установить уровень

    # Создаем обработчик для этого логгера
    log_file = LOG_DIR / f"{name}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    # Добавляем обработчик только если его еще нет
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
        logger.addHandler(file_handler)

    return logger
