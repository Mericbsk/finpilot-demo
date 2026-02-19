"""
Telegram Bot Yapılandırması

Kimlik bilgileri artık .env dosyasından okunuyor.
Örnek .env dosyası için .env.example'a bakın.
"""

import os
from pathlib import Path

# python-dotenv ile .env dosyasını yükle
try:
    from dotenv import load_dotenv

    # Proje kök dizinindeki .env dosyasını bul
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # dotenv yüklü değilse ortam değişkenlerini doğrudan kullan

# Ortam değişkenlerinden oku (güvenli)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def validate_telegram_config() -> dict:
    """Telegram yapılandırmasını doğrula ve durum raporu döndür."""
    issues = []
    if not BOT_TOKEN:
        issues.append("TELEGRAM_BOT_TOKEN ortam değişkeni ayarlanmamış.")
    if not CHAT_ID:
        issues.append("TELEGRAM_CHAT_ID ortam değişkeni ayarlanmamış.")
    return {
        "valid": len(issues) == 0,
        "bot_token_set": bool(BOT_TOKEN),
        "chat_id_set": bool(CHAT_ID),
        "issues": issues,
    }


# Doğrulama
_config_status = validate_telegram_config()
if not _config_status["valid"]:
    import warnings

    for issue in _config_status["issues"]:
        warnings.warn(f"Telegram: {issue} .env dosyasını kontrol edin.")
