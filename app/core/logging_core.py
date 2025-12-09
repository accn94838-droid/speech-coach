"""
Конфигурация логирования для приложения.
"""
import logging
import sys
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """
    Настраивает логирование для приложения.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Путь к файлу для записи логов (опционально)
    """
    # Создаём форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Создаём обработчик для stdout
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Получаем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Очищаем существующие обработчики
    root_logger.handlers.clear()

    # Добавляем обработчик
    root_logger.addHandler(console_handler)

    # Если указан файл для логов, добавляем файловый обработчик
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    # Настраиваем логирование для некоторых библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("faster_whisper").setLevel(logging.WARNING)

    # Логируем успешную настройку
    root_logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        root_logger.info(f"Logs will be written to: {log_file}")
