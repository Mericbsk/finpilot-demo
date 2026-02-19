"""
🔔 TELEGRAM UYARI SİSTEMİ
Yeni sinyaller için anında bildirim gönderir
"""

import os
from datetime import datetime

import requests


class TelegramNotifier:
    def __init__(self, bot_token=None, chat_id=None):
        """
        Telegram bildirim sistemi

        Kurulum:
        1. @BotFather ile bot oluştur
        2. Bot token'ı al
        3. @userinfobot ile chat ID'ni öğren
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_signal_alert(self, signal_data):
        """
        Yeni sinyal uyarısı gönder
        """
        try:
            # Mesaj formatı oluştur
            message = self._format_signal_message(signal_data)

            # Telegram'a gönder
            success = self._send_message(message)

            if success:
                print(f"✅ Telegram uyarısı gönderildi: {signal_data['symbol']}")
            else:
                print(f"❌ Telegram uyarısı gönderilemedi: {signal_data['symbol']}")

            return success

        except Exception as e:
            print(f"❌ Telegram hatası: {e}")
            return False

    def send_daily_summary(self, signals_count, best_signal=None):
        """
        Günlük özet gönder
        """
        try:
            message = f"""
📊 **GÜNLÜK ÖZET** - {datetime.now().strftime("%Y-%m-%d")}

🎯 **Toplam Sinyal:** {signals_count} adet

{f"🏆 **En İyi Fırsat:** {best_signal['symbol']} (R/R: {best_signal['risk_reward']})" if best_signal else "💤 **Bugün sinyal yok**"}

💡 **Not:** Sadece kaliteli sinyaller gösteriliyor!
            """.strip()

            return self._send_message(message)

        except Exception as e:
            print(f"❌ Günlük özet hatası: {e}")
            return False

    def _format_signal_message(self, signal):
        """
        Sinyal mesajını formatla
        """
        # Emoji ve durum
        emoji = "🚀" if signal.get("is_premium_symbol") else "⚡"
        quality = "PREMIUM" if signal.get("is_premium_symbol") else "NORMAL"

        # Filtre durumu
        filters = []
        if signal.get("volume_spike"):
            filters.append("📈 Hacim")
        if signal.get("price_momentum"):
            filters.append("🚀 Momentum")
        if signal.get("trend_strength"):
            filters.append("💪 Trend")
        if signal.get("timeframe_aligned"):
            filters.append("⏰ Uyum")

        filter_text = " | ".join(filters) if filters else "Temel filtreler"

        # Ana mesaj
        message = f"""
{emoji} **ALIM SİNYALİ** - {quality}

🎯 **Sembol:** {signal["symbol"]}
💰 **Fiyat:** ${signal["price"]}
🛡️ **Stop-Loss:** ${signal["stop_loss"]} ({signal["stop_loss_percent"]:.1f}%)
🎯 **Hedef:** ${signal["take_profit"]}
📊 **R/R Oranı:** {signal["risk_reward"]:.1f}
📈 **Lot:** {signal["position_size"]} adet

✨ **Aktif Filtreler:** {filter_text}
📊 **Sinyal Skoru:** {signal["score"]}/4
🔥 **Filtre Skoru:** {signal["filter_score"]}/3

⏰ **Zaman:** {signal["timestamp"]}

💡 **Strateji:**
• Giriş: ${signal["price"]}
• Stop: ${signal["stop_loss"]}
• Hedef: ${signal["take_profit"]}
• Risk: %{signal["stop_loss_percent"]:.1f} | Hedef: %{((signal["take_profit"] - signal["price"]) / signal["price"] * 100):.1f}
        """.strip()

        return message

    def _send_message(self, message):
        """
        Telegram API ile mesaj gönder
        """
        try:
            payload = {"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"}

            response = requests.post(self.api_url, json=payload, timeout=10)

            if response.status_code == 200:
                return True
            else:
                print(f"❌ Telegram API hatası: {response.status_code}")
                print(f"Response: {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"❌ Bağlantı hatası: {e}")
            return False

    def send_recommendations(self, recommendations):
        """
        Öneri listesi (Top 10) mesajı gönderir.
        recommendations: list[dict] veya pandas DataFrame (records)
        """
        try:
            # DataFrame geldiyse sözlüklere çevir
            if hasattr(recommendations, "to_dict"):
                records = recommendations.to_dict(orient="records")
            else:
                records = list(recommendations)

            lines = ["🔝 *Öneriler (Top 10)*", f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

            for i, r in enumerate(records[:10], 1):
                sym = r.get("symbol")
                score = r.get("recommendation_score")
                # strength (0-100) destekle
                strength = r.get("strength")
                try:
                    score_txt = f"{float(score):.2f}" if score is not None else "-"
                except Exception:
                    score_txt = str(score)
                entry = "Evet" if r.get("entry_ok") else "Hayır"
                why = r.get("why") or ""
                reason = r.get("reason") or ""
                if strength is None:
                    lines.append(f"{i}. {sym} | Skor: {score_txt} | Entry: {entry}")
                else:
                    lines.append(
                        f"{i}. {sym} | Skor: {score_txt} ({int(strength)}/100) | Entry: {entry}"
                    )
                if why:
                    lines.append(f"   -> {why}")
                if reason:
                    lines.append(f"   -> {reason}")

            msg = "\n".join(lines)
            # Telegram 4096 karakter sınırı – güvenli kırpma
            if len(msg) > 3800:
                msg = msg[:3700] + "\n…"
            return self._send_message(msg)
        except Exception as e:
            print(f"❌ Öneri listesi gönderim hatası: {e}")
            return False

    def test_connection(self):
        """
        Bağlantıyı test et
        """
        test_message = f"""
🔧 **TEST MESAJI**

✅ Telegram uyarı sistemi aktif!
⏰ {datetime.now().strftime("%Y-%m-%d %H:%M")}

Bot çalışıyor ve uyarılar gelmeye hazır! 🚀
        """.strip()

        success = self._send_message(test_message)

        if success:
            print("✅ Telegram bağlantısı başarılı!")
        else:
            print("❌ Telegram bağlantısı başarısız!")
            print("Kontrol edin:")
            print(f"- Bot Token: {self.bot_token[:10]}...")
            print(f"- Chat ID: {self.chat_id}")

        return success

    def is_configured(self):
        """
        Bot yapılandırılmış mı kontrol et
        """
        return bool(self.bot_token and self.chat_id)


# 🔧 KOLAY KURULUM FONKSIYONU
def setup_telegram_bot():
    """
    Telegram bot kurulumu için yardımcı
    """
    print("🔔 TELEGRAM BOT KURULUM REHBERİ")
    print("=" * 40)
    print()
    print("1️⃣ **Bot Oluştur:**")
    print("   - Telegram'da @BotFather ile konuş")
    print("   - /newbot komutunu gönder")
    print("   - Bot adı ver (örn: Trading Signals)")
    print("   - Bot username ver (örn: my_trading_bot)")
    print("   - TOKEN'ı kopyala")
    print()
    print("2️⃣ **Chat ID Öğren:**")
    print("   - Botunla /start yap")
    print("   - @userinfobot ile konuş")
    print("   - Chat ID'ni kopyala")
    print()
    print("3️⃣ **.env Dosyasını Güncelle:**")
    print("   TELEGRAM_BOT_TOKEN=your_token_here")
    print("   TELEGRAM_CHAT_ID=your_chat_id_here")
    print()
    print("✅ Bilgileri .env dosyanıza ekleyin!")
    print("📝 .env.example dosyasını referans olarak kullanabilirsiniz.")


if __name__ == "__main__":
    # Test için
    setup_telegram_bot()

    print("\n🧪 TEST MODU:")
    print("Bot bilgilerinizi girdikten sonra test edebilirsiniz:")
    print("python telegram_alerts.py")
