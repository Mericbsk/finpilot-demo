# FinPilot Finance Academy

Self-evolving finansal eğitim sistemi. 8 agent, 12 domain, tamamen otomatik içerik döngüsü.

## Hızlı Başlangıç

```bash
cd Borsa/FinanceAcademy

# Tam pipeline (seed + daily + rapor)
python run.py

# Sadece başlangıç içeriğini yükle
python run.py --seed

# Kullanıcı onboard
python run.py --onboard mericbsk

# Kullanıcı dashboard
python run.py --dashboard mericbsk

# Ders içeriğini göster
python run.py --lesson TA-001-grafik-tipleri

# Sistem durumu
python run.py --status

# Haftalık rapor
python run.py --weekly
```

## API Sunucusu (opsiyonel)

```bash
pip install fastapi uvicorn
python app.py           # http://localhost:8001
# Docs: http://localhost:8001/docs
```

## Agent Mimarisi

| Agent | Görev | Tetiklenme |
|-------|-------|-----------|
| ContentGenerator | LLM ile ders üretir | Gap Detector, Trend Scout, API |
| QualityGuard | Finansal doğruluk + pedagoji denetimi | Her yeni içerik |
| Personalization | Kişisel öğrenme yolu | Kullanıcı aktivitesi |
| GapDetector | Eksik içerik tespiti | Günlük 02:00 |
| AnalyticsAgent | Performans raporu | Haftalık Pazartesi |
| ContentUpdater | İçerik tazelik denetimi | 90 günde bir |

## Notlar

- **LLM bağlantısı olmadan**: Mock içerikle çalışır, Quality Guard reddeder → gerçek ders üretilmez
- **LLM ile**: `GROQ_API_KEY` env değişkenini ayarla, tam otomatik içerik üretilir
- **DB**: Kendi bilgisayarında `data/academy.db`'ye yazar (Borsa'ya dokunmaz)
