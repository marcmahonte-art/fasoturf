"""
Configuration centralisée du logging pour le scraper PMU'B.
"""

import logging
import sys
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Path | None = None) -> None:
    """
    Configure le logging pour l'ensemble du scraper.

    Args:
        level: Niveau de logging (DEBUG, INFO, WARNING, ERROR).
        log_file: Chemin optionnel vers un fichier de log.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Format détaillé avec timestamp
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configuration du logger racine
    root_logger = logging.getLogger("pmub")
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Handler fichier (optionnel)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

    root_logger.info("Logging initialisé — niveau: %s", level.upper())


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger enfant du logger pmub."""
    return logging.getLogger(f"pmub.{name}")
