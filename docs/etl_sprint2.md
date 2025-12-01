# Sprint 2 – Alternatif Veri ETL Orkestrasyonu

Bu doküman, alternatif veri adaptörlerini Prefect tabanlı ETL akışlarına bağlamak için izlenecek mimarinin ve uygulanacak adımların özetidir.

## 🎯 Amaç

Ham haber/on-chain verisini toplayıp temizleyerek, kalite kontrollerinden geçirip Parquet tabanlı veri gölüne yazmak ve Great Expectations + Pydantic ile şema/kalite garantisi sağlamak.

## 🧱 Yeni Modüller

| Modül | Açıklama |
| --- | --- |
| `drl.etl.run_key` | `(source, symbol, start, end)` değerlerinden deterministik Prefect `run_key` üreten yardımcılar. |
| `drl.etl.schemas` | Pydantic tabanlı `NewsRecordModel`, `OnChainRecordModel` ve DataFrame doğrulama fonksiyonları. |
| `drl.etl.quality` | Great Expectations expectation suite üretimi ve çalıştırma yardımcıları. |
| `drl.etl.storage` | Parquet partition yazımı (`{source}/{symbol}/{YYYY}/{MM}/{DD}`) ve sonuç raporları. |
| `drl.etl.flows` | Prefect `alternative_data_etl_flow` akışı, idempotent run key, kalite ve depolama adımları. |

## 🧭 Akış Adımları

1. **Run Key Oluşturma** – `build_run_key` ile her sembol/pencere eşsiz kimlik alır.
2. **Veri Çekimi** – Async adapter `fetch_async` çağrılır, hata yönetimi Prefect retry ile sağlanır.
3. **Şema Doğrulama** – Pydantic modelleri ile zorunlu sütun/tip kontrolü (`validate_dataframe`).
4. **Kalite Testleri** – Great Expectations beklentileri (ör. sentiment `[-1,1]`, hacim `>=0`). Eksik bağımlılık varsa uyarı loglanır, akış durdurulmaz.
5. **Partition Yazımı** – Gün bazlı partition edilerek Parquet dosyaları oluşturulur, sonuç metrikleri raporlanır.
6. **Sonuç** – `ETLResult`, Prefect `flow_run_id`, satır sayısı, kalite raporu ve depolama özetini döner.

## 🔒 Idempotency

- Run key, sembol+pencere bazında deterministik olduğundan aynı veri tekrar çekilirse Prefect aynı run’ı tespit eder.
- Depolama aşaması partition bazında overwrite yerine idempotent yazım kullanır; ilerleyen sprintte Delta Lake ACID katmanı eklenecek.

## ✅ Kalite Kapıları

- Pydantic hataları `ValidationReport` içinde toplanır ve Prefect log’larına yazılır.
- Great Expectations başarısız olursa `QualityReport` detayları ile uyarı üretilir.
- Bu raporlar ileride Slack/Telegram alerting’e bağlanacak.

## 📦 Bağımlılıklar

`requirements-etl.txt` dosyası Prefect, Pydantic ve Great Expectations gereksinimlerini listeler. Delta Lake / Glue entegrasyonu opsiyonel olup sonraki sprintte eklenebilir.

## 🚀 Sonraki Sprint İçin Notlar

- Prefect Result Storage (S3/GCS) ve deployment ayarları yapılacak.
- Delta Lake ACID katmanı + Glue kataloğu (spark/delta) eklenerek eşzamanlı yazma güvence altına alınacak.
- Great Expectations sonuçları Observability katmanına (Prometheus, Slack uyarıları) bağlanacak.
- Backfill ve cache task’leri için ayrı Prefect flow parametreleri tanımlanacak.

Bu iskelet ile alternatif veri ETL hattı tekrar edilebilir, izlenebilir ve kalite kapılarıyla güvence altına alınabilir. Kod tarafında eksik bağımlılık olması durumunda açıklayıcı hatalar üretir; bağımlılıklar yüklendiğinde Prefect flow’u doğrudan çalışmaya hazırdır.
