# Sprint 5 – Observability Roadmap

Sprint 5, Feature Store'u temel alan DRL platformunun kalıcı olarak sağlıklı çalışmasını izlemek ve sorunları proaktif şekilde yakalamak için gözlemlenebilirlik (observability) katmanını hayata geçirmeyi hedefler. Bu sprintte kod tabanına `drl/observability.py` yardımcı modülü, ETL ve eğitim katmanlarına Prometheus metrik kancaları, MLflow kayıt akışı ve CLI'dan yönetilebilen metrik sunucusu eklendi.

## 🎯 Hedefler

- Eğitim, ETL ve inference aşamalarında kritik metrikleri toplayıp görselleştirmek.
- Model artefaktlarının yaşam döngüsünü MLflow üzerinden yönetmek.
- Operasyonel ve finansal performans sapmalarına otomatik uyarılar oluşturmak.
- Observability bileşenlerini CI/CD ve Prefect akışlarıyla entegre ederek sürdürmesi kolay bir izleme altyapısı sağlamak.

## ⚙️ Uygulama Katmanları

- **MLflow yapılandırması:** `drl/observability.MLflowSettings` ve `mlflow_run` bağlam yöneticisi, walk-forward eğitiminde hiperparametreleri, performans metriklerini ve feature artefaktlarını otomatik olarak kayıt altına alıyor. `WalkForwardTrainer` artık eğitim/test satır sayılarını, feature pipeline JSON'unu ve opsiyonel sözleşme dosyasını aynı run altında tutuyor.
- **Prometheus kayıtları:** `record_etl_flow` Prefect tabanlı `alternative_data_etl_flow` içinde çağrılıyor; inference tarafında `record_inference_event`, RL model tahmini başına gecikme ölçüyor. `ml_agent` CLI'sı `--prometheus` bayrağı ile gömülü HTTP sunucusunu açabiliyor.
- **Bağımlılıklar:** Opsiyonel bağımlılıklar `requirements-observability.txt` dosyasına taşındı (`mlflow`, `prometheus-client`).

## 🧪 MLflow Entegrasyonu

| Bileşen | Açıklama | Notlar |
| --- | --- | --- |
| **Experiment Tracking** | Her eğitim (walk-forward) run'ında kullanılan feature versiyonu, scaler artefaktı, hiperparametreler ve performans metrikleri (Sharpe, max drawdown, hit rate) kayıt altına alınır. | `WalkForwardTrainer` `mlflow_run` ile her split'i ayrı run olarak işler, hiperparametreleri `mlflow_log_params` üzerinden gönderir. |
| **Model Registry** | "production-candidate", "staging" ve "archived" gibi lifecycle durumları tanımlanır. | Promotion kararları Sharpe & risk eşiklerine bağlanır. |
| **Artefakt Yönetimi** | Model ağırlıkları, JSON feature sözleşmesi ve scaler statistiklerini içeren artefakt JSON'ları tek run altında saklanır. | Inference servisleri run-id üzerinden doğru paketi indirir. |

## 📈 Prometheus Metrikleri

### Pipeline Sağlığı

- `etl_flow_duration_seconds`
- `etl_flow_success_total`, `etl_flow_failure_total`
- `etl_rows_ingested_total`
- `great_expectations_pass_ratio`

### Inference Sağlığı

- `inference_latency_seconds` (histogram)
- `inference_requests_total`
- `feature_cache_hit_ratio`
- `fallback_activation_total`

### Ajan Performansı

- `rolling_reward`
- `rolling_sharpe`
- `regime_drift_score`

Metrikler `drl/observability.configure_prometheus` ile başlatılan HTTP sunucusu üzerinden (`/metrics`) Prometheus tarafından scrape edilir.

### Hızlı Başlangıç

```bash
# Opsiyonel bağımlılıkların kurulumu
python -m pip install -r requirements-observability.txt

# Prometheus ve MLflow entegrasyonlu demo eğitimi
python -m ml_agent --mlflow --prometheus --prometheus-port 9100
```

## 📊 Grafana Panelleri

1. **Operasyonel Panel**
   - API istek hacmi, rate-limit hit sayısı
   - Job queue gecikmesi, worker kapasitesi
2. **Model Performans Paneli**
   - Son 30 gün sinyal doğruluğu
   - Confidence dağılımı, fallback tetikleme oranı
   - Reward/Sharpe trendi ve drift skorları
3. **Veri Kalitesi Paneli**
   - Great Expectations test sonuçları
   - Feature drift uyarıları (örn. KS testi p-değeri)
   - Offline-online feature versiyon senkron durumu

## 🚨 Alerting Stratejisi

| Trigger | Eşik | Aksiyon |
| --- | --- | --- |
| ETL başarısızlık oranı | > %5 (rolling 1h) | Slack #alerts, Prefect retry escalation |
| Inference latency | > 500 ms (p95) | Telegram bot mesajı, autoscale tetikleme |
| Ajan reward | < 0 (rolling 24h) | Fail-safe moduna geçiş, risk ekibine e-posta |
| Feature drift | KS p-değeri < 0.01 | Model registry'de uyarı, yeniden eğitim kuyruğu |

Alertler Prometheus Alertmanager ile yönetilir; Slack & Telegram entegrasyonları webhook üzerinden bağlanır.

## 🔁 Entegrasyon Akışı

1. Prefect flow'ları (`alternative_data_etl_flow`), çalışma süresini ve ingest edilen satır sayısını Prometheus'a rapor ederken aynı zamanda MLflow'a metrik/artefakt gönderir.
2. Flow tamamlandığında Prometheus metrikleri push gateway'e gönderilir veya scrape edilir.
3. Grafana dashboard'ları Prometheus ve MLflow veri kaynaklarını kullanarak güncel görünümleri sunar.
4. Alertmanager eşik aşımlarında ilgili kanallara bildirim yollar; fail-safe tetikleyicileri DRL servislerine API üzerinden bildirilir.

## ✅ Teslim Sonrası Checklist

- [ ] MLflow tracking sunucusu yapılandırıldı (remote veya lokal).
- [ ] Prometheus + Alertmanager docker compose (veya helm chart) hazırlandı.
- [ ] Grafana dashboard JSON'ları versiyon kontrolüne alındı.
- [ ] Inference API'lerinde `/metrics` endpoint'i aktif (`configure_prometheus` çağrısı ile açılıyor).
- [ ] CI pipeline'ı metric/alert config değişikliklerinde validation çalıştırıyor.

## 🚀 Stratejik Etki

- **Şeffaflık:** Teknik ekip ve iş paydaşları sinyal üretim kalitesini gerçek zamanlı izleyebilir.
- **Proaktiflik:** Problemler müşteriye yansımadan önce tespit edilip aksiyon alınır.
- **Sürdürülebilirlik:** Model/feature sağlığı sürekli takip edilerek regresyonlar erken yakalanır, fail-safe mekanizmaları güvenilir hale gelir.
