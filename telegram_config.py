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

# Bot bilgileri:
# Bot Adı: Gizliajanbot
# Bot Linki: t.me/Gizliajanbot
# Kullanıcı: Meriç

# Doğrulama
if not BOT_TOKEN:
    import warnings

    warnings.warn("TELEGRAM_BOT_TOKEN ortam değişkeni ayarlanmamış. .env dosyasını kontrol edin.")
