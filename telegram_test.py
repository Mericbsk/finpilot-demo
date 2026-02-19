"""
🧪 TELEGRAM UYARI SİSTEMİ TEST
"""

from telegram_alerts import TelegramNotifier


def test_message_format():
    """
    Mesaj formatını test et
    """
    print("🧪 MESAJ FORMATI TESTİ")
    print("=" * 40)

    # Örnek sinyal verisi
    test_signal = {
        "symbol": "AAPL",
        "price": 150.25,
        "stop_loss": 145.50,
        "take_profit": 160.75,
        "position_size": 45,
        "risk_reward": 2.1,
        "stop_loss_percent": 3.2,
        "score": 3,
        "filter_score": 2,
        "timestamp": "2025-09-13 11:30",
        "is_premium_symbol": True,
        "volume_spike": True,
        "price_momentum": False,
        "trend_strength": True,
        "timeframe_aligned": True,
    }

    # Mesaj formatını göster
    notifier = TelegramNotifier()
    message = notifier._format_signal_message(test_signal)

    print("📱 GÖNDERILECEK MESAJ:")
    print("-" * 40)
    print(message)
    print("-" * 40)

    return message


def demo_telegram_setup():
    """
    Telegram kurulum demo
    """
    print("\n🔔 TELEGRAM KURULUM REHBERİ")
    print("=" * 50)

    steps = [
        "1️⃣ Telegram uygulamasını aç",
        "2️⃣ @BotFather ile konuşma başlat",
        "3️⃣ /newbot komutunu gönder",
        "4️⃣ Bot adı gir: 'Trading Signals Bot'",
        "5️⃣ Bot kullanıcı adı gir: 'my_trading_signals_bot'",
        "6️⃣ Verilen TOKEN'ı kopyala",
        "7️⃣ Kendi botunla /start yap",
        "8️⃣ @userinfobot ile chat ID'ni öğren",
        "9️⃣ telegram_config.py'yi düzenle",
    ]

    for step in steps:
        print(f"   {step}")

    print("\n📝 YAPILANDIRMA:")
    print("telegram_config.py dosyasında:")
    print('BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"')
    print('CHAT_ID = "123456789"')

    print("\n✅ KURULUM TAMAMLANDI MI?")
    print("python telegram_test.py run ile test edin!")


def run_real_test():
    """
    Gerçek telegram testi (bot bilgileri gerekli)
    """
    try:
        from telegram_config import BOT_TOKEN, CHAT_ID

        if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ Bot token henüz yapılandırılmamış!")
            print("telegram_config.py dosyasını düzenleyin.")
            return False

        if CHAT_ID == "YOUR_CHAT_ID_HERE":
            print("❌ Chat ID henüz yapılandırılmamış!")
            print("telegram_config.py dosyasını düzenleyin.")
            return False

        print("🔧 Telegram bağlantısı test ediliyor...")
        notifier = TelegramNotifier(BOT_TOKEN, CHAT_ID)

        # Bağlantı testi
        success = notifier.test_connection()

        if success:
            print("\n✅ BAŞARILI! Telegram uyarıları hazır!")

            # Örnek sinyal gönder
            test_signal = {
                "symbol": "TEST",
                "price": 100.00,
                "stop_loss": 95.00,
                "take_profit": 110.00,
                "position_size": 20,
                "risk_reward": 2.0,
                "stop_loss_percent": 5.0,
                "score": 4,
                "filter_score": 3,
                "timestamp": "2025-09-13 11:30",
                "is_premium_symbol": False,
                "volume_spike": True,
                "price_momentum": True,
                "trend_strength": True,
                "timeframe_aligned": True,
            }

            print("\n📱 Örnek sinyal gönderiliyor...")
            notifier.send_signal_alert(test_signal)

        else:
            print("❌ Bağlantı başarısız!")
            print("Bot token ve chat ID'yi kontrol edin.")

        return success

    except ImportError:
        print("❌ telegram_config.py bulunamadı!")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "run":
        # Gerçek test
        run_real_test()
    else:
        # Format testi ve kurulum rehberi
        test_message_format()
        demo_telegram_setup()
