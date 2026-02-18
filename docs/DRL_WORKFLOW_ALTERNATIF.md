# 🤖 DRL Workflow - Mevcut Sisteme Ek İş Akışı

Bu dokuman **mevcut scanner sistemini etkilemeden** DRL agent eğitimi ve parallel testing için **alternatif iş akışını** tanımlar.

---

## 📋 Mevcut vs DRL İş Akışı Karşılaştırması

### 🔵 Mevcut Scanner İş Akışı (Değişmeyecek)
```
┌─────────────────────────────────────────────────┐
│          MEVCUT SİSTEM (Dokunulmayacak)        │
└─────────────────────────────────────────────────┘

1. Kullanıcı scanner.py çalıştırır
   ↓
2. Scanner sinyalleri üretir (RSI, MACD, Volume, vb.)
   ↓
3. Streamlit panel_new.py ile görselleştirilir
   ↓
4. Telegram alerts gönderilir
   ↓
5. Kullanıcı manuel/otomatik trade yapar
```

### 🟢 Yeni DRL İş Akışı (Paralel - Opsiyonel)
```
┌─────────────────────────────────────────────────┐
│       DRL SİSTEMİ (Paralel Test Ortamı)        │
└─────────────────────────────────────────────────┘

1. DRL model eğitimi (hafta/ayda bir)
   ↓
2. parallel_scanner.py ile test (günlük)
   ↓
3. Sonuçlar logs/drl/ klasörüne kaydedilir
   ↓
4. drl_comparison_dashboard.py ile analiz
   ↓
5. 3+ ay sonra performance karşılaştırması
   ↓
6. Başarılı ise → Mevcut sisteme entegre edilir
```

---

## 🎯 DRL Eğitimine Nasıl Başlanır?

### Adım 1: Gerekli Paketlerin Yüklenmesi

```bash
# Sadece DRL için gerekli paketler
pip install -r requirements-rl.txt

# İçerik:
# - stable-baselines3[extra]>=2.2
# - gymnasium>=0.29
# - shimmy>=2.0
# - tensorboard (eğitim izleme için)
```

### Adım 2: İlk Model Eğitimi

#### 2.1 Sentetik Data ile Test (Öğrenme Amaçlı)
```bash
# Gerçek piyasa verisi olmadan test
python ml_agent.py --algorithm PPO --timesteps 10000

# Çıktı:
# - Model: models/ppo_YYYYMMDD_HHMMSS.zip
# - Eğitim süresi: ~5 dakika
# - Amaç: Sistemi anlamak
```

**Ne öğretir?**
- Environment'in çalışıp çalışmadığını
- Model kaydetme/yükleme
- Hyperparameter'ların etkisi

#### 2.2 Gerçek Data ile Eğitim
```bash
# Gerçek piyasa verisi ile
python ml_agent.py \
    --algorithm PPO \
    --timesteps 100000 \
    --track-mlflow \
    --mlflow-experiment "FinPilot-Production-Test"

# Çıktı:
# - Model: models/ppo_production_YYYYMMDD.zip
# - Eğitim süresi: ~30-60 dakika
# - MLflow tracking: http://localhost:5000
```

**Eğitim Parametreleri:**
| Parameter | Varsayılan | Açıklama |
|-----------|------------|----------|
| `--timesteps` | 50,000 | Kaç adım eğitim (daha fazla = daha iyi ama yavaş) |
| `--learning-rate` | 3e-4 | Öğrenme hızı (küçük = stabil, büyük = hızlı) |
| `--gamma` | 0.99 | Gelecek ödül indirimi |
| `--algorithm` | PPO | PPO (stabil) veya SAC (agresif) |

#### 2.3 Walk-Forward Training (Production İçin)
```bash
# Zaman serisi doğru şekilde eğit
python ml_agent.py \
    --algorithm PPO \
    --timesteps 200000 \
    --walk-forward \
    --train-size 0.8 \
    --test-size 0.2

# 2022-2023 verisi ile eğit
# 2024 verisi ile test et
# Overfitting önlenir
```

---

## 📊 Eğitim Takibi ve Monitoring

### TensorBoard ile İzleme
```bash
# Eğitim başladıktan sonra başka bir terminalde:
tensorboard --logdir logs/tensorboard

# Tarayıcıda aç: http://localhost:6006

# Görebilecekleriniz:
# - Loss curves
# - Reward progression
# - Policy entropy
```

### MLflow ile İzleme (Önerilen)
```bash
# MLflow server başlat
mlflow ui --port 5000

# Tarayıcıda aç: http://localhost:5000

# Görebilecekleriniz:
# - Her eğitim run'ı
# - Hyperparameter'lar
# - Metrics (Sharpe, drawdown, vb.)
# - Model artifacts
```

---

## 🔄 Eğitim Döngüsü (Production)

### Haftalık/Aylık Retrain Workflow

```bash
# 1. Yeni veri topla (son 90 gün)
python scripts/collect_training_data.py --days 90

# 2. Model eğit
python ml_agent.py \
    --algorithm PPO \
    --timesteps 150000 \
    --data data/training/latest.csv \
    --save-path models/ppo_$(date +%Y%m%d).zip

# 3. Model test et
python parallel_scanner.py \
    --mode drl_only \
    --model models/ppo_$(date +%Y%m%d).zip \
    --symbols test_symbols.txt

# 4. Sonuçları incele
streamlit run drl_comparison_dashboard.py

# 5. İyiyse production'a al
cp models/ppo_$(date +%Y%m%d).zip models/ppo_latest.zip
```

### Cron Job Örneği
```bash
# crontab -e
# Her Pazar 02:00'da yeniden eğit
0 2 * * 0 cd /workspaces/Borsa && /bin/bash scripts/weekly_retrain.sh
```

---

## 🧪 Parallel Testing İş Akışı

### Günlük Test Rutini (Manuel)

```bash
# 1. Mevcut scanner'ı çalıştır (değişmeden)
python scanner.py

# 2. Paralelde DRL test et (ayrı dosya)
python parallel_scanner.py \
    --mode hybrid \
    --model models/ppo_latest.zip \
    --log-dir logs/drl/$(date +%Y%m%d)

# 3. Dashboard'da karşılaştır
streamlit run drl_comparison_dashboard.py

# 4. Her şey normal akışta devam eder
```

### Otomatik Test (Cron)

```bash
# Her gün 09:30'da (piyasa açılışı sonrası)
30 9 * * 1-5 cd /workspaces/Borsa && python parallel_scanner.py --mode hybrid --model models/ppo_latest.zip >> logs/drl/parallel_test.log 2>&1
```

**Önemli:**
- ✅ Mevcut scanner etkilenmez
- ✅ Sadece log tutar
- ✅ Gerçek trade yapmaz
- ✅ İstediğiniz zaman durdurabilirsiniz

---

## 📁 Dizin Yapısı (Öneri)

```
workspaces/Borsa/
│
├── scanner.py                 # Mevcut scanner (DEĞİŞMEZ)
├── panel_new.py              # Mevcut dashboard (DEĞİŞMEZ)
│
├── drl/                      # DRL modülü (AYRI)
│   ├── hybrid_engine.py      # Scanner+DRL birleştirici
│   ├── training.py           # Model eğitimi
│   ├── inference.py          # Model inference
│   └── ...
│
├── parallel_scanner.py       # DRL test script (AYRI İŞ AKIŞI)
├── drl_comparison_dashboard.py  # DRL dashboard (AYRI)
│
├── logs/
│   ├── scanner/              # Mevcut scanner logları
│   └── drl/                  # DRL test logları (YENİ)
│       ├── 20260215/
│       ├── 20260216/
│       └── ...
│
└── models/                   # DRL modelleri
    ├── ppo_latest.zip
    ├── ppo_20260201.zip
    └── ...
```

---

## 🎓 Eğitim Stratejileri

### Strateji 1: Conservative (Muhafazakar)
```python
# config.py
TRAINING_CONFIG = {
    "algorithm": "PPO",
    "timesteps": 100_000,
    "learning_rate": 1e-4,  # Düşük
    "gamma": 0.99,
    "risk_appetite": 3,     # Düşük risk
}
```
**Özellikler:**
- Yavaş öğrenir
- Stabil
- Düşük volatilite
- Yeni başlayanlar için

### Strateji 2: Moderate (Dengeli)
```python
TRAINING_CONFIG = {
    "algorithm": "PPO",
    "timesteps": 200_000,
    "learning_rate": 3e-4,  # Orta
    "gamma": 0.99,
    "risk_appetite": 5,     # Orta risk
}
```
**Özellikler:**
- Dengeli öğrenme
- İyi performans/risk oranı
- Çoğu durum için ideal

### Strateji 3: Aggressive (Agresif)
```python
TRAINING_CONFIG = {
    "algorithm": "SAC",     # Daha agresif algoritma
    "timesteps": 300_000,
    "learning_rate": 5e-4,  # Yüksek
    "gamma": 0.95,
    "risk_appetite": 8,     # Yüksek risk
}
```
**Özellikler:**
- Hızlı öğrenir
- Yüksek volatilite
- Deneyimli kullanıcılar için

---

## 🔍 Eğitim Sonuçlarını Değerlendirme

### İyi Eğitim Sinyalleri ✅
```
Episode Reward: Sürekli artıyor
Sharpe Ratio: > 1.5
Max Drawdown: < %15
Win Rate: > %55
```

### Kötü Eğitim Sinyalleri ❌
```
Episode Reward: Düzensiz/düşüyor
Sharpe Ratio: < 0.5
Max Drawdown: > %30
Win Rate: < %45
```

### Problem Giderme

| Problem | Sebep | Çözüm |
|---------|-------|-------|
| Reward düşüyor | Overfitting | Learning rate azalt |
| Çok yavaş öğreniyor | Underfitting | Timesteps artır |
| Çok agresif | High risk | Risk appetite azalt |
| Düşük Sharpe | Kötü features | Feature engineering |

---

## 📅 Örnek 12 Haftalık Plan

### Hafta 1-2: Setup
- [x] Requirements yükle
- [x] İlk model eğit (test)
- [x] Sistemi anla

### Hafta 3-4: Gerçek Eğitim
- [ ] Gerçek data ile eğit
- [ ] Hyperparameter tuning
- [ ] İlk parallel test

### Hafta 5-8: Parallel Testing
- [ ] Günlük parallel scan
- [ ] Log analizi
- [ ] Dashboard monitoring

### Hafta 9-12: Evaluation
- [ ] Performance comparison
- [ ] Statistical analysis
- [ ] Production kararı

---

## 🚦 Karar Kriterleri

### DRL'yi Production'a Alma
```
TÜM şartlar sağlanmalı:

✅ 3+ ay test verisi
✅ Win rate > Scanner + %10
✅ Sharpe > 1.5
✅ Max DD < Scanner * 0.8
✅ Agreement rate > %60
✅ Statistical significance (p < 0.05)
```

### DRL'yi Durdurma
```
HERHANGİ BİRİ gerçekleşirse:

❌ Consecutive losses > 10
❌ Drawdown > %25
❌ Win rate < %40
❌ Model confidence < %30
❌ Agreement rate < %30
```

---

## 🛠️ Hızlı Başlangıç Komutları

```bash
# 1. İlk model eğit (10 dakika)
python ml_agent.py --algorithm PPO --timesteps 50000

# 2. Test et (scanner etkilenmez)
python parallel_scanner.py --mode scanner_only
python parallel_scanner.py --mode drl_only --model models/ppo_latest.zip

# 3. Karşılaştır
streamlit run drl_comparison_dashboard.py

# 4. Her şey normal devam eder
python scanner.py
streamlit run panel_new.py
```

---

## 📞 Yardım ve Destek

- **DRL Dokümantasyon:** `docs/DRL_PARALLEL_TESTING_GUIDE.md`
- **Test Script:** `python scripts/test_hybrid_setup.py`
- **Mevcut sistem:** Hiçbir değişiklik olmadan çalışmaya devam eder

---

## ⚠️ Önemli Notlar

1. **Mevcut sisteminiz hiç etkilenmez** - DRL tamamen ayrı çalışır
2. **İstediğiniz zaman durdurabilirsiniz** - Risk yok
3. **Sadece log tutar** - Gerçek trade yapmaz
4. **3+ ay test sonrası karar** - Acele etmeyin
5. **Başarısız olsa bile öğreticidir** - Data-driven karar

---

**Sonuç:** DRL eğitimi, mevcut sistemin yanında **gölge modda** çalışan bir deney ortamıdır. Başarılı olursa entegre edilir, olmazsa silinir. Risk sıfır! 🚀
