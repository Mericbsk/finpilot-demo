# -*- coding: utf-8 -*-
"""
FinPilot Error Messages
=======================
Merkezi Türkçe hata mesajları ve kullanıcı dostu uyarılar.
"""

from typing import Optional

import streamlit as st

# ============================================
# 📋 Hata Mesajı Katalogları
# ============================================

# API ve Bağlantı Hataları
API_ERRORS = {
    "connection_failed": "🔌 Bağlantı hatası. İnternet bağlantınızı kontrol edin.",
    "rate_limit": "⏱️ Çok fazla istek gönderildi. Lütfen birkaç dakika bekleyin.",
    "timeout": "⏳ İstek zaman aşımına uğradı. Lütfen tekrar deneyin.",
    "server_error": "🖥️ Sunucu hatası. Lütfen daha sonra tekrar deneyin.",
    "api_key_missing": "🔑 API anahtarı bulunamadı. Ayarlarınızı kontrol edin.",
    "api_key_invalid": "🔑 API anahtarı geçersiz. Yeni bir anahtar oluşturun.",
}

# Veri Hataları
DATA_ERRORS = {
    "no_data": "📭 Veri bulunamadı. Farklı parametreler deneyin.",
    "invalid_symbol": "❌ Geçersiz sembol. Sembol formatını kontrol edin.",
    "empty_csv": "📄 CSV dosyası boş veya okunamadı.",
    "missing_column": "📋 Gerekli sütun bulunamadı: '{column}'",
    "invalid_format": "📝 Geçersiz dosya formatı. Desteklenen format: {format}",
    "data_stale": "⚠️ Veriler güncel olmayabilir. Son güncelleme: {time}",
}

# Kullanıcı Eylemleri
ACTION_ERRORS = {
    "scan_failed": "🔍 Tarama başarısız oldu. Lütfen tekrar deneyin.",
    "save_failed": "💾 Kaydetme başarısız oldu. Disk alanını kontrol edin.",
    "load_failed": "📂 Yükleme başarısız oldu. Dosya bozuk olabilir.",
    "export_failed": "📤 Dışa aktarma başarısız oldu.",
}

# Başarı Mesajları
SUCCESS_MESSAGES = {
    "scan_complete": "✅ Tarama tamamlandı! {count} sembol analiz edildi.",
    "save_complete": "✅ Başarıyla kaydedildi.",
    "load_complete": "✅ Başarıyla yüklendi.",
    "settings_saved": "✅ Ayarlar kaydedildi.",
    "cache_cleared": "✅ Önbellek temizlendi.",
}

# Uyarı Mesajları
WARNING_MESSAGES = {
    "no_signals": "ℹ️ Şu an kriterlere uyan aktif sinyal bulunmuyor.",
    "limited_data": "⚠️ Sınırlı veri mevcut. Sonuçlar eksik olabilir.",
    "demo_mode": "🎮 Demo modundasınız. Gerçek veriler için tarama yapın.",
    "slow_connection": "🐢 Bağlantı yavaş. İşlemler gecikebilir.",
    "high_load": "⚡ Yoğun trafik. Performans düşük olabilir.",
}


# ============================================
# 🛠️ Yardımcı Fonksiyonlar
# ============================================


def get_error_message(category: str, key: str, **kwargs) -> str:
    """
    Kategoriye göre hata mesajı döndürür.

    Args:
        category: Hata kategorisi (api, data, action)
        key: Mesaj anahtarı
        **kwargs: Mesaj içinde değiştirilecek değerler

    Returns:
        Türkçe hata mesajı
    """
    catalogs = {
        "api": API_ERRORS,
        "data": DATA_ERRORS,
        "action": ACTION_ERRORS,
        "success": SUCCESS_MESSAGES,
        "warning": WARNING_MESSAGES,
    }

    catalog = catalogs.get(category, {})
    message = catalog.get(key, f"Bilinmeyen hata: {key}")

    # Placeholder'ları değiştir
    try:
        return message.format(**kwargs)
    except KeyError:
        return message


def show_error(category: str, key: str, **kwargs) -> None:
    """Streamlit error olarak gösterir."""
    st.error(get_error_message(category, key, **kwargs))


def show_warning(category: str, key: str, **kwargs) -> None:
    """Streamlit warning olarak gösterir."""
    st.warning(get_error_message(category, key, **kwargs))


def show_success(category: str, key: str, **kwargs) -> None:
    """Streamlit success olarak gösterir."""
    st.success(get_error_message(category, key, **kwargs))


def show_info(message: str) -> None:
    """Streamlit info olarak gösterir."""
    st.info(message)


def translate_exception(e: Exception) -> str:
    """
    Python exception'ını Türkçe hata mesajına çevirir.

    Args:
        e: Exception nesnesi

    Returns:
        Kullanıcı dostu Türkçe mesaj
    """
    error_type = type(e).__name__
    error_msg = str(e).lower()

    # Bağlantı hataları
    if "connection" in error_msg or "network" in error_msg:
        return get_error_message("api", "connection_failed")

    # Rate limit
    if "rate limit" in error_msg or "too many requests" in error_msg:
        return get_error_message("api", "rate_limit")

    # Timeout
    if "timeout" in error_msg or "timed out" in error_msg:
        return get_error_message("api", "timeout")

    # File not found
    if error_type == "FileNotFoundError":
        return "📂 Dosya bulunamadı. Dosya yolunu kontrol edin."

    # Permission error
    if error_type == "PermissionError":
        return "🔒 Erişim izni yok. Dosya izinlerini kontrol edin."

    # Value error
    if error_type == "ValueError":
        return f"❌ Geçersiz değer: {str(e)[:100]}"

    # Generic fallback
    return f"⚠️ Beklenmeyen hata oluştu: {str(e)[:200]}"


# ============================================
# 📊 Dashboard-spesifik Mesajlar
# ============================================

DASHBOARD_MESSAGES = {
    "no_scan_data": "📊 Henüz tarama yapılmadı. 'Taramayı Başlat' butonuna tıklayın.",
    "loading_scan": "🔍 Semboller analiz ediliyor...",
    "scan_complete": "✅ Tarama tamamlandı! {count} sembol analiz edildi.",
    "no_buyable": "💤 Şu an alım kriterlerine uyan sinyal bulunmuyor. Ayarları gevşetmeyi deneyin.",
    "drl_not_available": "🤖 DRL modeli henüz eğitilmedi. Eğitim için: `python -m drl.training --train`",
    "ai_research_loading": "🔍 Yapay zeka araştırması yapılıyor...",
    "ai_research_complete": "✅ AI analizi tamamlandı.",
    "csv_upload_hint": "📄 Sembol listesi içeren CSV dosyası yükleyin. (symbol veya ticker sütunu gerekli)",
    "settings_hint": "⚙️ Ayarları değiştirmek için sol kenar çubuğunu kullanın.",
}


def get_dashboard_message(key: str, **kwargs) -> str:
    """Dashboard mesajı döndürür."""
    message = DASHBOARD_MESSAGES.get(key, key)
    try:
        return message.format(**kwargs)
    except KeyError:
        return message
