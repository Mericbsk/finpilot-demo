# Sprint 5 – Rejim Duyarlı Feature Importance

Bu sprintte, walk-forward eğitim döngüsünden toplanan politika davranışlarını açıklayan SHAP tabanlı bir önem analizi pipeline'ı devreye alınmıştır. Amaç, her piyasa rejimi için hangi göstergelerin ajan kararlarına yön verdiğini ölçüp feature roadmap'ini veri destekli biçimde güncellemektir.

## 🔌 Bağımlılıklar

Rejim bazlı SHAP akışını çalıştırmak için yeni bir `requirements-rl.txt` dosyası eklenmiştir. Kurulum:

```bash
python -m pip install -r requirements-rl.txt
```

> **Not:** Stable-Baselines3 ile uyumluluk için `numpy` 2.x yerine 1.26 serisine sabitlenmiştir. Bu pin, PyTorch ve shap paketleriyle doğrulanmıştır.

## 🧪 Demo Akışı

Demo script'i, sentetik veride PPO ajanını kısa bir yürütmeyle eğitir, ardından politika davranışını bir RandomForest surrogate modeliyle tahmin edip SHAP değerleri üretir.

```bash
python -m scripts.feature_importance_demo \
  --sample-size 256 \
  --timesteps 5000 \
  --output-dir reports/feature_importance_<tarih>
```

Komut tamamlandığında aşağıdaki artefaktlar oluşturulur:

- `global_importance.csv`: Genel (rejim bağımsız) önem sıralaması
- `importance_<regime>.csv`: Trend / Range / Volatility rejimleri için ayrı SHAP tabloları
- `shap_values.npy`, `base_values.npy`: Daha ileri analizler için ham SHAP tensörleri

## 📊 Örnek Sonuçlar (2025-10-20)

| Rejim | İlk 3 Feature | SHAP Skoru |
| --- | --- | --- |
| Global | volume_avg_20, macd_hist, ema_200 | 0.0479 / 0.0343 / 0.0220 |
| Trend | volume_avg_20, macd_hist, macd | 0.0540 / 0.0435 / 0.0250 |
| Range | volume_avg_20, macd_hist, ema_200 | 0.0392 / 0.0301 / 0.0294 |
| Volatility | volume_avg_20, macd_hist, ema_200 | 0.0488 / 0.0286 / 0.0240 |

Bu sonuçlar, hacim-temelli volatilite göstergelerinin tüm rejimlerde baskın olduğunu; trend rejiminde MACD varyantlarının ekstra ağırlık kazandığını doğrulamaktadır.

## 🔄 Entegrasyon Noktaları

- `drl/market_env.py` artık Gymnasium API'siyle uyumludur; `reset` ve `step` çıktıları Gym/Gymnasium farkını otomatik olarak köprüler.
- `drl/training.WalkForwardTrainer` değerlendirme döngüsü, hem 4'lü (Gym) hem 5'li (Gymnasium) step imzalarını destekleyecek şekilde güncellendi.
- SHAP çıktıları, `drl/analysis/feature_importance.py` içerisinde tanımlanan `FeatureImportanceSummary` veri sınıfı üzerinden tüketilebilir.
- Yeni `drl/analysis/explainability.py` modülü, LLM'e giden özetleri sadeleştirmek için iki cümlelik alternatif veri yorumları ve `JSON` tabanlı anlatım çıktıları üretir.

## 🧠 Minimal Okuryazarlık Katmanı

- **Alternatif veri özeti:** Demo betiği artık yalnızca iki sinyali (4 saatlik sentiment delta ve z-skorlu balina akışı) tek cümlede özetliyor. Etkiler renk kodlu (positive/negative/neutral) olarak işaretleniyor.
- **Soru-cevap anlatım:** `build_narrative_payload` çıktısı iki paragraf halinde “Neden hemen şimdi?” ve “En kötü senaryo ne?” sorularını yanıtlıyor; payload JSON formatında döndüğü için frontend doğrudan tüketebiliyor.
- **Stop-loss rehberi:** Paylaşım, kullanıcı limitleri ile rejim bazlı max drawdown'ı harmanlayıp tek tıkla emir üretimine hazır bir `exit_price` sunuyor.

## ✅ Sonraki Adımlar

1. **Volatilite Duyarlılığı:** Rejim + volatilite seviye matrisini çıkararak risk limitlerini dinamikleştir.
2. **Composite Feature Araması:** Yüksek önemli göstergeleri birlikte optimize edecek etkileşim özelliklerini test et.
3. **Model Registry Entegrasyonu:** SHAP raporlarını MLflow run artefaktı olarak iliştirip üretim tanı süreçlerine dahil et.
