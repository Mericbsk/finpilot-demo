# FinPilot DRL Yol Haritası – Sonraki Adımlar

Bu doküman, mevcut mimarinin üzerine inşa edilecek geliştirme başlıklarını detaylandırır. Her bölümde hedefler, önerilen uygulama stratejileri, gerekli bağımlılıklar ve doğrulama adımları listelenmiştir.

## 0. Yeni oluşturulan altyapı parçacıkları

- `drl.persistence`: FeaturePipeline scaler istatistiklerini JSON/artefact deposuna yazıp yeniden yüklemek için `FeaturePipelineArtifact`, `build_artifact`, `save_artifact`, `restore_pipeline` yardımcıları.
- `drl.data_sources.base`: Haber, zincir üstü vb. kaynaklar için ortak `DataAdapter` protokolü ve `BaseAdapter` sınıfı.
- `drl.data_sources.news`: Harici API’lerden gelen ham haber verisini `sentiment_score` ve `news_volume` sütunlarına dönüştüren adapter şablonu.
- `drl.data_sources.onchain`: On-chain metrikleri (`onchain_active_addresses`, `onchain_tx_volume`, `stablecoin_ratio`) içeren veri çerçeveleri üreten adapter şablonu.
- `drl.data_sources.async_base`: Prefect entegrasyonuna hazır asenkron HTTP istemcisi, rate-limit, retry ve fallback adaptör altyapısı.
- `drl.etl`: Prefect tabanlı ETL flow iskeleti (`alternative_data_etl_flow`), Pydantic/Great Expectations doğrulama yardımcıları ve Parquet partition yazıcıları.
- `drl.feature_generators`: Ağırlıklı sentiment, momentum ve lag özellikleri için jeneratör fonksiyonları.
- `drl.alignment_helpers`: Çoklu frekanstaki veri setlerini hizalamak için resample/forward-fill yardımcıları.
- `WalkForwardTrainer` ve `ml_agent` CLI’si artık pipeline artefaktlarını diske kaydetme (`--save-pipeline-artifacts`, `--pipeline-artifact-dir`) ve mevcut artefaktı yükleyerek eğitim başlatma (`--load-pipeline-artifact`, `--allow-pipeline-mismatch`) desteği sunuyor.

Bu yapı taşları, aşağıdaki yol haritası adımlarını uygularken doğrudan kullanılabilir.

## 1. Alternatif Veri Entegrasyonu ve FeaturePipeline Kalıcılığı

### 1.1 Veri Kanalları

- **Haber duyarlılığı (News API / Aylık RSS)**
  - Haber sağlayıcısından (ör. NewsAPI, AYLIŞ, Bloomberg) başlık & özet çekme.
  - Metinleri Türkçe/İngilizce ayrıştırıp `transformers` veya `finetuned` BERT modelleriyle duyarlılık skorları üretmek.
  - Günlük/saathlik bucket’lar oluşturup `sentiment_score`, `news_sentiment_vol` gibi yeni kolonlar eklemek.
- **On-chain metrikler (Glassnode, IntoTheBlock, Dune)**
  - API anahtarı ile zincir üstü metrikleri (aktif adres, işlem hacmi, stablecoin girişleri) çektirip zaman serisine dönüştürmek.
  - `onchain_active_addresses`, `onchain_tx_volume`, `stablecoin_ratio` vb. sütunlara map etmek.
- **Alternatif (Twitter/X, GDELT, Google Trends)**
  - Rate limit’ler için asenkron görev kuyruğu (Celery/Redis) kullanmak.
  - Veri kalite kontrolü: eksik günleri doldurma, uç değerleri Winsorize etme.

### 1.2 Pipeline Kalıcılık Yardımcıları

- `FeaturePipeline.export_state()` sonucunu JSON/MsgPack olarak kaydetmek için `drl/persistence.py` modülü.
- MLflow/W&B artefact deposuna push etmek; model yeniden yüklenirken `load_state()` çağrısı.
- Versiyon takip: `schema_version` ve `feature_hash` ekleyip prod/test uyumsuzluğunu erken yakalamak.

### 1.3 İş Akışı

1. Veri toplayıcı mikro servis -> `data/raw/{source}/{symbol}.parquet` olarak sakla.
2. Günlük ETL jobu (Prefect/Airflow) -> feature enjeksiyonu -> `data/features/{date}/{symbol}.parquet`.
3. Pipeline fit -> state export -> artefact store.
4. Eğitim sırasında state’i yükle ve yalnızca transform uygula.

### 1.4 Feature Dönüşüm Sprint 3

- `feature_generators.py` haber ve on-chain verisinden üstel ağırlıklı sentiment (`calculate_weighted_sentiment`), momentum (`calculate_momentum`) ve gecikmeli özellikleri (`create_lag_features`) üretir.
- `alignment_helpers.py` farklı frekanslardaki veri setlerini (`resample_frame`, `align_frames`) tek zaman eksenine taşır ve forward-fill stratejilerini soyutlar.
- `tests/test_feature_generators.py` ve `tests/test_alignment_helpers.py` NaN, boş DataFrame, negatif değer gibi edge case’leri doğrular; % değişim ve lag kontrolleri için regression testleri sağlar.
- Bir sonraki adım: Bu özellikleri FeaturePipeline’a bağlayıp Feature Store sözleşmesine (schema versioning, scaler artefact’ları) aktararak eğitim/inference tutarlılığını sağlamak.

## 2. Model Eğitim Derinliği

### 2.1 Hyperparametre Arama

- `optuna` ile `WalkForwardTrainer` etrafında `study.optimize` sarmalayıcı.
- Arama alanı: öğrenme oranı, gamma, gae_lambda, reward ağırlıkları, PilotShield limitleri.
- Hesaplama yoğunluğu için Ray Tune veya Optuna federated sampler (ör. `TPESampler`, `CmaEsSampler`).

### 2.2 Çoklu Algoritma Desteği

- Mevcut PPO/SAC’ye ek olarak TD3, A2C, DDPG varyantları.
- Politik mimariler: CNN+LSTM hibrit (zaman serisi + rejim sinyalleri), attention tabanlı encoder.
- Ortak arayüz: `create_model(algo: str)` -> SB3 veya kendi PyTorch ajanınızı oluşturur.

### 2.3 Eğitim Metriklerinin Loglanması

- MLflow eksperimenti `FinPilot-DRL` altında
  - Parametreler: pipeline state hash, veri sürümü, hyperparametre seti.
  - Metrikler: ödül, Sharpe, max DD, trade sayısı, kazanç/kayıp oranı.
  - Artefakt: eğitilmiş model `.zip`, pipeline state `.json`, hyperparametre raporu `.html`.
- Alternatif olarak Weights & Biases
  - Sweep konfigürasyonları, canlı chart’lar, Discord/Slack entegrasyonu.

## 3. Gerçekçi Değerlendirme ve Stres Testleri

### 3.1 Backtest + Canlı Simülasyon

- `backtest.py`yi `WalkForwardTrainer` sonuçlarıyla uyumlu hale getir.
- Paper trading katmanını, broker API (Polygon, Alpaca, IBKR) simülasyonu için mock adapter ile besle.

### 3.2 Metrik Doğrulama

- Ek metrikler: Ulcer Index, Sortino, Calmar, Hit Ratio, Avg Holding Time.
- `numpy` tabanlı hesap yerine `empyrical` veya `pyfolio` alternatifleri (lisans uyumunu kontrol et).

### 3.3 Stres Senaryoları ve PilotShield Kalibrasyonu

- 1987, 2008, 2020 şok senaryolarını CSV olarak sakla; yoğun volatilite rejiminde reward cezalarını yeniden ağırlıkla.
- Monte Carlo + bootstrapping ile risk tolerans testi; limit aşımlarını heatmap olarak raporla.

## 4. Test ve Otomasyon

### 4.1 Birim Testleri

- `tests/test_feature_pipeline.py`
  - Missing column, optional column, scaler testleri.
  - State export/import round-trip kontrolü.
- `tests/test_market_env.py`
  - Reward hesaplarının, pozisyon sınırlarının, tarihçe çıktısının doğrulanması.

### 4.2 Smoke Test & CI

- GitHub Actions / Azure DevOps pipeline
  - `python -m compileall` + `pytest -m "not slow"`
  - Opsiyonel: nightly heavy test (walk-forward demo).
- Kod stili: `ruff` veya `flake8`, `mypy` tip kontrolü.

### 4.3 Bağımlılık Yönetimi

- `pyproject.toml` veya `requirements.txt` güncellenmeli: `stable-baselines3`, `optuna`, `mlflow`, `wandb`, `prefect`, `pandas`, `numpy`, `scikit-learn` (opsiyonel).
- `pip-tools` veya `uv` ile kilit dosyası üretimi.

## 5. Ürün Entegrasyonu

### 5.1 `panel_new.py` Entegrasyonu

- CLI çağrısını arka planda tetikleyen `asyncio` / threading task.
- Eğitim sonuçlarını (metrik tabloları, grafikleri) Streamlit dashboard’da göster.
- Pipeline state ve model dosyalarını kullanıcı seçimine göre yükle/indir.

### 5.2 Model Dosya Yönetimi

- Artefakt deposu (S3, Azure Blob, Google Cloud Storage).
- Versiyon etiketleme: `model-{symbol}-{algo}-{timestamp}` formatı.
- Rollback mekanizması ve canary deploy planı.

### 5.3 Güvenli Devreye Alma

- Permission katmanı: yalnızca yetkili kullanıcı modeli canlı ortama push edebilir.
- Sağlık kontrolleri: eğitimden sonra minimal smoke trade simülasyonu.
- Audit trail: kim, ne zaman, hangi modeli etkinleştirdi.

---

Bu plan, mevcut demosu çalışan DRL altyapısını üretim ortamına taşımak için sıralı olarak izlenebilecek geliştirme paketlerini ortaya koyar. Her başlık için ayrıntılı iş kartları açmak ve efor tahminleri eklemek bir sonraki adım olacaktır.
