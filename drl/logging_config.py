"""
FinPilot Logging Configuration

Proje genelinde tutarlı logging sağlar.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Log formatı
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO", log_file: Optional[str] = None, console: bool = True
) -> logging.Logger:
    """
    Proje genelinde logging yapılandırması.

    Args:
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Opsiyonel log dosyası yolu
        console: Konsola yazdır

    Returns:
        Root logger
    """
    # Root logger'ı yapılandır
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Mevcut handler'ları temizle
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Konsol handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Dosya handler (opsiyonel)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Modül için logger döndürür.

    Kullanım:
        from drl.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Mesaj")
    """
    return logging.getLogger(name)


# Varsayılan yapılandırma (import edildiğinde çalışır)
_default_configured = False


def ensure_configured():
    """İlk kez çağrıldığında varsayılan yapılandırmayı uygular."""
    global _default_configured
    if not _default_configured:
        setup_logging(level="INFO")
        _default_configured = True
