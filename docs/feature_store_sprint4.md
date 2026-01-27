# Sprint 4 – Feature Store Mimari Özeti

Bu sprint, FinPilot'un DRL motoru için eğitim (offline) ve gerçek zamanlı (online) süreçlerde aynı özellik tanımlarını kullanan tutarlı bir Feature Store katmanı sağlar.

## 🎯 Hedefler

- Offline walk-forward eğitiminde kullanılan zaman serisi özelliklerini performant, partition'lı bir depoda saklamak.
- Online inference sırasında en güncel özellikleri düşük gecikmeyle sunmak.
- Feature sözleşmelerini (contract) sürümleyerek değişiklikleri izlemek ve DRL ajanının doğru versiyonları tüketmesini garanti etmek.
- Eğitimde uygulanan ölçeklendirme (scaler) artefaktlarını inference aşamasında yeniden kullanarak training-serving skew problemini önlemek.

## 💾 Depolama Katmanları

| Depo Tipi | Kullanım Senaryosu | Teknik Uygulama |
| --- | --- | --- |
| **Offline Store** | Walk-forward eğitim, model validasyonu ve retrospektif analiz | Alt veri ETL'lerinin ürettiği temizlenmiş feature setleri **time-series partitioning** stratejisiyle Parquet dosyalarına yazılır. Partition anahtarı olarak `asset`, `feature_group`, `event_date` gibi kolonlar kullanılır. |
| **Online Store** | Gerçek zamanlı sinyal üretimi, fail-safe tetikleyicileri | Redis tabanlı bir key-value katmanı (veya Feast/Tecton benzeri managed servis) her varlık için son 48 saatlik sentiment, güncel rejim etiketi gibi "sıcak" özellikleri tutar. DRL inference servisi bu katmana milisaniye seviyesinde erişir. |

> **Tek Doğruluk Kaynağı:** Tüm özellik tanımları offline/online katmanlarda aynı sözleşmeyi takip eder; sürüm kontrolü olmadan hiçbir feature prod ortamına alınmaz.

## 📜 Feature Sözleşmesi & Versiyonlama

- Her özellik JSON formatında tanımlanır:

  ```json
  {
    "feature_name": "wtd_sentiment_score",
    "type": "float",
    "normalization": "z_score",
    "source_module": "feature_generators.py",
    "version": "1.0.1",
    "metadata": {
      "window": "48h",
      "weights": "volume"
    }
  }
  ```

- `version` değeri, algoritma/pencere gibi hesaplama mantığı değiştiğinde artırılır.
- DRL ajanı hangi sözleşme versiyonuyla eğitildiyse inference sırasında aynı versiyon zorunlu tutulur.
- Sözleşme JSON'ları Git içinde saklanır; ayrıca MLflow run artefaktı olarak iliştirilir.

## 🔄 Scaler Artefakt Senkronizasyonu

1. Eğitim pipeline'ı (`walk_forward_training`) feature DataFrame'lerine `StandardScaler` gibi dönüşümleri uygular.
2. Kullanılan scaler nesneleri `.pkl` olarak seri hale getirilip MLflow/W&B artefaktı olarak kaydedilir.
3. Inference servisi, modeli yüklerken eşleşen scaler'ı da indirir ve gelen canlı veriye aynı normalize adımlarını uygular.
4. Böylece **training-serving skew** minimize edilir; model çıkışları beklenen dağılımda kalır.

## 🔁 Uçtan Uca Akış

1. Prefect tabanlı ETL, AltData kaynaklarından gelen ham veriyi doğrular (`great_expectations`) ve Parquet partition'larına yazar.
2. `alignment_helpers` ve `feature_generators` modülleri sözleşmede tanımlı feature'ları üretir.
3. Oluşan feature frame, offline store'a appendedilir; aynı zamanda son snapshot online store'a yansıtılır.
4. MLflow run'u feature sözleşmesi ve scaler artefaktıyla birlikte kaydedilir.
5. DRL inference servisi, istenen feature versiyonu ve scaler ile online store'dan sinyal üretimine başlar.

## 📌 Sprint 4 Sonrası Odaklar

- Feature sözleşmesi doğrulaması: CI pipeline'ında JSON sözleşmesi ile üretilen DataFrame şemasını karşılaştıran kontroller eklemek.
- Online store backfill mekanizması: Offline partition'lardan seçili aralıkları Redis'e yeniden yüklemek için Prefect task'i.
- Latency profili: Online katmandaki sorgu sürelerini ölçmek için temel metrikler.

Bir sonraki sprint, bu yapıyı sürekli izlenebilir kılmak için Observability katmanını devreye alacaktır (bkz. **Sprint 5 Roadmap**).
