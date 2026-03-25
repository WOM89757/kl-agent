import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
import os

from app.config import BASE_DIR


def setup_logger(
    name: str = __name__,
    level: int = None,
    log_to_file: bool = None,
    log_to_console: bool = None,
    log_dir: Path = None,
) -> logging.Logger:
    if level is None:
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)

    if log_to_file is None:
        log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"

    if log_to_console is None:
        log_to_console = os.getenv("LOG_TO_CONSOLE", "true").lower() == "true"

    if log_dir is None:
        log_dir = BASE_DIR.parent / "logs"

    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file:
        log_file = log_dir / f"{name}.log"
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


root_logger = setup_logger("root")


def get_logger(name: str) -> logging.Logger:
    return setup_logger(name)
