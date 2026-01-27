# 🚀 FinPilot Demo - Deployment Guide

## Streamlit Cloud ile Yükleme (5 Dakika)

### 1. GitHub'a Push
```bash
git add demo_standalone.py requirements-demo.txt .streamlit/config.toml
git add views/demo.py views/translations.py views/components/stock_presets.py
git commit -m "feat: Add standalone demo for public deployment"
git push origin main
```

### 2. Streamlit Cloud Ayarları

1. [share.streamlit.io](https://share.streamlit.io) adresine gidin
2. **New app** tıklayın
3. Aşağıdaki bilgileri girin:
   - **Repository:** `{your-username}/Borsa`
   - **Branch:** `main`
   - **Main file path:** `demo_standalone.py`
4. **Advanced settings** açın:
   - **Python version:** 3.11
   - **Requirements file:** `requirements-demo.txt`
5. **Deploy!** tıklayın

### 3. Custom Domain (Opsiyonel)

Streamlit Cloud'da:
1. App settings → Custom domain
2. `demo.finpilot.ai` gibi subdomain ekleyin
3. DNS'te CNAME kaydı oluşturun:
   ```
   demo.finpilot.ai → your-app.streamlit.app
   ```

## Dosya Yapısı

```
Borsa/
├── demo_standalone.py      # Ana demo uygulaması
├── requirements-demo.txt   # Minimal bağımlılıklar
├── .streamlit/
│   └── config.toml         # Tema ve ayarlar
├── views/
│   ├── demo.py             # Demo sayfası mantığı
│   ├── translations.py     # Çoklu dil desteği
│   └── components/
│       └── stock_presets.py # Hisse presetleri
└── data/
    └── waitlist.json       # Email listesi (otomatik oluşur)
```

## Özellikler

| Özellik | Durum |
|---------|-------|
| 🌐 Çoklu dil (EN/DE/TR) | ✅ |
| 📊 Canlı piyasa verisi | ✅ |
| 🤖 AI skor hesaplama | ✅ |
| 📈 Plotly grafikler | ✅ |
| 📧 Waitlist toplama | ✅ |
| 🎨 Dark tema | ✅ |

## Waitlist Verileri

Toplanan emailler `data/waitlist.json` dosyasında saklanır:

```json
[
  {
    "email": "user@example.com",
    "name": "John Doe",
    "source": "demo",
    "timestamp": "2026-01-27T14:00:00"
  }
]
```

⚠️ **Not:** Streamlit Cloud'da dosya sistemi ephemeral'dır.
Production için Supabase/Firebase gibi bir veritabanı kullanın.

## Monitoring

Streamlit Cloud dashboard'da:
- Visitor sayısı
- Uptime
- Error logs

Görüntülenebilir.

## Güncelleme

```bash
git add .
git commit -m "Update demo"
git push origin main
```

Streamlit Cloud otomatik olarak yeniden deploy eder (2-3 dakika).

---

📧 Sorular için: support@finpilot.ai
