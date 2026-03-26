# 🏗️ FinPilot Altyapı Hızlandırma Yol Haritası

> **Tarih:** 2026-03 | **Kapsam:** DRL eğitim pipeline, veri besleme, inference, CI/CD
> **Mevcut Durum:** CPU-only, GitHub Codespaces devcontainer
> **Hedef:** Eğitim süresini 10-50x kısaltmak, Optuna HP-arama döngüsünü günlerden saatlere indirmek

---

## 1. MEVCUT ALTYAPI PROFİLİ

| Parametre | Mevcut Değer | Not |
|-----------|-------------|-----|
| **CPU** | AMD Ryzen 7 7730U (16 thread) | Mobil-sınıf, TDP 15-28W |
| **RAM** | 16 GB (8 GB kullanılabilir) | DevContainer sınırı |
| **GPU** | Yok (NVIDIA yok) | `torch.cuda.is_available() = False` |
| **Disk I/O** | ~199 MB/s (SSD/NVMe) | Yeterli — darboğaz burada değil |
| **PyTorch** | 2.10.0+cu128 (CUDA runtime var, GPU yok) | Binary GPU-ready, donanım eksik |
| **SB3** | 2.7.1 | Güncel |
| **Docker Bellek Limiti** | finpilot: 2 GB / scanner: sınırsız | Eğitim için kısıtlayıcı |
| **Ortam** | DevContainer (Python 3.11, Debian 12) | Overlay FS + volume mount |

### Eğitim Profil Özeti (Sprint-18 Loglarından)

| Specialist | Algo | Adım | Süre (CPU) | Sharpe | MaxDD |
|-----------|------|------|------------|--------|-------|
| momentum | PPO | 500K-3M | 315-2605s | 0.047-0.052 | 0.23-0.54 |
| trend | PPO | 3M | 1804-2980s | 0.038-0.057 | 0.36-0.47 |
| conservative | PPO | 2-3M | 783-2310s | 0.012-0.017 | 0.11-0.13 |
| aggressive | PPO | 500K | 406s | 0.007 | 0.52 |
| swing | RPPO | 3M | 3941-12692s | 0.013-0.022 | 0.22-0.49 |
| breakout | PPO | 500K | 324s | -0.125 | 0.39 |
| scalper | PPO | 1M | 929s | -0.052 | 0.09 |
| meanrev | PPO | 500K | 355s | 0.014 | 0.34 |

**Toplam 15 model = 33,148 saniye = 9.2 saat (CPU)**
**Ortalama model başına = 2,210 saniye (37 dakika)**

### Tam Pipeline Projeksiyon (Tahmin)

```
10 specialist × 2-5M adım = ~25,000s = 6.9 saat (tek seferlik eğitim)
10 specialist × 40 Optuna trial = ~1,000,000s = 278 saat = 11.6 gün
```

**→ Optuna ile tam HP arama 12 gün sürüyor. Bu ENGELLEYICI bir darboğaz.**

---

## 2. DARBOĞAZ ANALİZİ

### 🔴 Kritik Darboğazlar (Etkisi > 5x)

| # | Darboğaz | Etki | Kök Neden |
|---|----------|------|-----------|
| **D1** | **GPU yokluğu** | 4-20x yavaşlık | PyTorch tensor işlemleri CPU'da; policy ağı forward/backward pass GPU'dan faydalanamıyor |
| **D2** | **Tek ortam (DummyVecEnv×1)** | 2-8x kayıp | `_create_model()` yalnızca `DummyVecEnv([_make_env])` kullanıyor; paralel env yok |
| **D3** | **Seri specialist eğitimi** | 10x kayıp | 10 specialist sırayla eğitiliyor; bağımsız oldukları için paralel çalışabilirler |
| **D4** | **Optuna seri trial** | 40x kayıp | Her deneme tam eğitim döngüsü; pruning kısıtlı, MedianPruner bile yok |

### 🟡 Orta Darboğazlar (Etkisi 1.5-3x)

| # | Darboğaz | Etki | Kök Neden |
|---|----------|------|-----------|
| **D5** | **yfinance senkron veri çekimi** | 1.5-2x I/O bloğu | Rate limiting + sıralı istek; warm-up süresi artıyor |
| **D6** | **RecurrentPPO LSTM overhead** | 3-5x (swing) | LSTM policy 7.4 MB vs PPO 169 KB; sequential rollout zorunlu |
| **D7** | **VecFrameStack (n=4)** | 1.2-1.5x bellek | obs_dim 20→80; gereksiz kopyalama, bellek baskısı |
| **D8** | **Sabit episode uzunluğu** | 1.1-1.3x | Curriculum callback var ama episode truncation yok |

### 🟢 Düşük Etki (Ama Kolay Düzeltme)

| # | Darboğaz | Etki |
|---|----------|------|
| **D9** | Docker bellek limiti (2 GB) | Büyük model eğitimlerinde OOM riski |
| **D10** | Mixed precision kullanılmıyor | FP32 default; FP16/BF16 ile %30-50 hızlanma potansiyeli |
| **D11** | Model checkpoint sıklığı | Her eval'de save — disk I/O overhead |

---

## 3. HIZLANDIRMA SEÇENEKLERİ KARŞILAŞTIRMASI

### Seçenek Puanlama Matrisi (1-5, 5=en iyi)

| Kriter | A: Yerel GPU İstasyonu | B: Bulut GPU (On-Demand) | C: Hibrit (Burst-to-Cloud) | D: Edge / Spot |
|--------|----------------------|-------------------------|---------------------------|----------------|
| **Performans** | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐⭐ (4) | ⭐⭐⭐ (3) |
| **Maliyet (Başlangıç)** | ⭐⭐ (2) | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐⭐ (4) | ⭐⭐⭐⭐ (4) |
| **Maliyet (1 Yıl)** | ⭐⭐⭐⭐ (4) | ⭐⭐ (2) | ⭐⭐⭐ (3) | ⭐⭐⭐⭐ (4) |
| **Ölçeklenebilirlik** | ⭐⭐ (2) | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐⭐ (4) |
| **Gizlilik** | ⭐⭐⭐⭐⭐ (5) | ⭐⭐⭐ (3) | ⭐⭐⭐⭐ (4) | ⭐⭐⭐ (3) |
| **Operasyonel Karmaşıklık** | ⭐⭐⭐⭐ (4) | ⭐⭐⭐ (3) | ⭐⭐ (2) | ⭐⭐⭐ (3) |
| **TOPLAM** | **22/30** | **23/30** | **22/30** | **21/30** |

### Detaylı Gerekçeler

#### A. Yerel GPU İstasyonu (On-Premise)

```
Donanım Önerisi:
  Bütçe:  RTX 4070 Ti (12 GB VRAM)   → $800
  Orta:   RTX 4090 (24 GB VRAM)      → $1600
  Yüksek: RTX 6000 Ada (48 GB VRAM)  → $6500

Tahmini Hızlanma: 8-15x (SB3 PPO/SAC on single GPU)
```

| Artı | Eksi |
|------|------|
| ✅ Tek seferlik maliyet, süresiz kullanım | ❌ $800-6500 başlangıç yatırımı |
| ✅ Tam veri gizliliği (finansal veriler dışarı çıkmaz) | ❌ Bakım/güncelleme sorumluluğu |
| ✅ Sınırsız eğitim süresi, ek maliyet yok | ❌ Ölçekleme = yeni donanım satın alma |
| ✅ Düşük gecikme (yerel disk & ağ) | ❌ Donanım eskimesi (2-3 yıl) |

**Uygunluk:** Haftada 20+ saat eğitim yapılacaksa, 4-6 ayda geri ödeme.

#### B. Bulut GPU (On-Demand)

```
Platformlar & Tahmini Fiyat:
  Lambda Cloud  T4      → $0.50/saat
  Vast.ai       A10G    → $0.30-0.50/saat
  RunPod        A100    → $1.10-2.49/saat
  AWS p3        V100    → $3.06/saat (on-demand)
  GCP a2        A100    → $3.67/saat (on-demand)
  Spot/Preemptible      → %60-80 indirimle

Tahmini Hızlanma: 4-20x (GPU tipine bağlı)
```

| Artı | Eksi |
|------|------|
| ✅ Sıfır başlangıç maliyeti | ❌ Kullandıkça öde — düzenli kullanımda pahalılanır |
| ✅ Farklı GPU tipleri denenebilir | ❌ Veri transferi gerekli (gizlilik endişesi) |
| ✅ Anında ölçekleme (10 GPU paralel) | ❌ Spot preemption riski (checkpoint gerekli) |
| ✅ Bakım yok, güncellemeler otomatik | ❌ Ağ gecikmesi, data egress maliyeti |

**Uygunluk:** Haftada <10 saat eğitim veya HP arama sprint'leri için ideal.

#### C. Hibrit (On-Prem + Burst-to-Cloud)

```
Model: Rutin eğitim yerelde, Optuna/grid search burst'leri bulutta
  Yerel: RTX 4070 Ti (günlük iterasyon)
  Burst: Lambda/RunPod (HP arama kampanyaları, ayda 1-2 kez)
```

| Artı | Eksi |
|------|------|
| ✅ En iyi maliyet/performans dengesi | ❌ İki ortam yönetimi gerekli |
| ✅ Gizli veriler yerelde, HP arama bulutta | ❌ Ortam pariteleri tutturulmalı (Docker) |
| ✅ Burs'larda sınırsız ölçekleme | ❌ Data sync pipeline gerekli |

**Uygunluk:** Projenin şu anki ölçeği için en uygun seçenek.

#### D. Edge / Spot (Budget)

```
Platformlar:
  GitHub Codespaces GPU (beta) → ~$0.36/saat (T4)
  Google Colab Pro+             → $49.99/ay (A100 sınırlı)
  Kaggle Notebooks              → Ücretsiz T4 (30 saat/hafta)
  Paperspace Gradient           → Ücretsiz GPU (sınırlı)
```

| Artı | Eksi |
|------|------|
| ✅ Düşük/sıfır maliyet | ❌ Sınırlı GPU süresi ve bellek |
| ✅ Hemen kullanılabilir, setup minimal | ❌ Preemption + session timeout |
| ✅ Deneme/prototip için mükemmel | ❌ Üretim workload'ları için güvenilmez |

**Uygunluk:** İlk GPU adaptasyonunu test etmek, tek model eğitimi için.

### 📊 ÖNERİLEN STRATEJİ

```
Kısa Vade (0-4 hafta):  D — Colab/Kaggle ile GPU adaptasyonu test et (SIFIR MALİYET)
Orta Vade (1-3 ay):     B → C — RunPod/Lambda ile HP arama sprint'leri
Uzun Vade (3-12 ay):    C — Yerel GPU + Bulut burst hibrit model
```

---

## 4. HIZLI KAZANIMLAR (Quick Wins) — 1-4 Hafta

Sıfır veya düşük maliyetle uygulanabilen, koda dokunarak elde edilecek hızlanmalar:

### QW-1: SubprocessVecEnv ile Paralel Ortam (Hızlanma: 2-4x | Süre: 1 gün)

**Sorun:** `DummyVecEnv([_make_env])` — tek ortam, tek thread.
**Çözüm:** `SubprocessVecEnv` ile `n_envs=4-8` paralel ortam.

```python
# drl/training.py — _create_model() içinde değişiklik
# ÖNCE:
vec_env = DummyVecEnv([_make_env])

# SONRA:
from stable_baselines3.common.vec_env import SubprocessVecEnv

n_envs = min(8, os.cpu_count() or 4)
vec_env = SubprocessVecEnv([_make_env for _ in range(n_envs)])
```

**Beklenen Etki:**
- 16 thread CPU → 8 paralel env → ~3-4x eğitim hızlanması
- PPO n_steps toplama hızı doğrusal ölçeklenir
- Bellek: ortam başına ~50 MB → 8 env ≈ 400 MB (kabul edilebilir)

**Risk:** Düşük. SB3 native destekli.

---

### QW-2: Optuna Pruning + Paralel Trial (Hızlanma: 3-8x | Süre: 2 gün)

**Sorun:** 40 Optuna trial, hepsi tam süre çalışıyor. Kötü denemeler bile 3M step koşuyor.
**Çözüm:** MedianPruner + SuccessiveHalvingPruner + paralel worker.

```python
# Optuna konfigürasyon önerisi
import optuna

study = optuna.create_study(
    direction="maximize",
    pruner=optuna.pruners.SuccessiveHalvingPruner(
        min_resource=50_000,      # En az 50K step
        reduction_factor=3,       # Her aşamada 1/3'ü ele
        min_early_stopping_rate=0
    ),
    sampler=optuna.samplers.TPESampler(
        n_startup_trials=10,      # İlk 10 rastgele, sonra TPE
        multivariate=True
    )
)

# Trial içinde intermediate reporting:
# Her 100K step'te bir EvalCallback ile Sharpe raporla
# Sharpe < median ise trial pruned → %60-80 zaman tasarrufu
```

**Beklenen Etki:**
- 40 trial'ın ~25-30'u erken kesilir → %60-75 zaman tasarrufu
- Paralel 4 worker ile ek %75 tasarruf → kombine 10-15x hızlanma
- 12 gün → 1-2 gün'e indirilir

---

### QW-3: Eğitim Timestep Optimizasyonu (Hızlanma: 2-3x | Süre: 1 gün)

**Sorun:** Tüm modeller aynı timestep'te (500K-3M) ancak convergence görülmüyor.
**Çözüm:** Erken durdurma (early stopping) + adaptif timestep.

```python
from stable_baselines3.common.callbacks import StopTrainingOnNoModelImprovement, EvalCallback

eval_callback = EvalCallback(
    eval_env,
    eval_freq=10_000,
    n_eval_episodes=5,
    best_model_save_path="./best_model/",
    callback_after_eval=StopTrainingOnNoModelImprovement(
        max_no_improvement_evals=10,  # 10 eval sonucu iyileşme yoksa dur
        min_evals=20,                 # En az 20 eval (200K step) sonra kontrol
        verbose=1
    )
)
```

**Beklenen Etki:**
- Converge etmeyen modeller 200K-500K step'te durur (vs 3M)
- conservative ve scalper gibi hızlı converge edenler erken biter
- Ortalama %40-60 timestep tasarrufu

---

### QW-4: `device="auto"` GPU Desteği Ekleme (Hızlanma: 4-20x* | Süre: 2 saat)

**Sorun:** SB3 model oluşturulurken `device` parametresi geçilmiyor → default CPU.
**Çözüm:** `device="auto"` veya ortam değişkeninden okuma.

```python
# drl/training.py — _create_model() içinde
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"

model = PPO(
    "MlpPolicy",
    vec_env,
    verbose=0,
    device=device,  # ← BU SATIR EKLENMELİ
    seed=self.algo_config.seed,
    **common,
    **on_policy_extras,
)
```

**Not:** Bu değişiklik tek başına hızlanma sağlamaz (GPU olmadan), ama GPU eklendığında anında aktif olur. Hazırlık maliyeti 2 saat.

---

### QW-5: Veri Önbellekleme (Data Caching) (Hızlanma: 1.5-2x I/O | Süre: 1 gün)

**Sorun:** yfinance her eğitimde aynı veriyi tekrar çekiyor. Rate limiting.
**Çözüm:** Yerel parquet/feather cache.

```python
import pandas as pd
from pathlib import Path
import hashlib

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(exist_ok=True)

def cached_fetch(symbol: str, start: str, end: str) -> pd.DataFrame:
    cache_key = hashlib.md5(f"{symbol}_{start}_{end}".encode()).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.parquet"

    if cache_path.exists():
        return pd.read_parquet(cache_path)

    df = yf.download(symbol, start=start, end=end)
    df.to_parquet(cache_path)
    return df
```

**Beklenen Etki:**
- İlk çekimden sonra I/O süresi ~0
- Optuna trial'ları arası veri çekme eliminasyonu
- Özellikle 40+ trial'da kümülatif tasarruf büyük

---

### QW-6: Mixed Precision Training (Hızlanma: 1.3-1.5x* | Süre: 3 saat)

**Sorun:** Tüm eğitim FP32. Modern GPU'larda FP16/BF16 ile %30-50 hızlanma mümkün.
**Çözüm:** PyTorch AMP (Automatic Mixed Precision).

```python
# SB3 v2.x doğrudan mixed precision desteklemez,
# ama custom policy ile eklenebilir:
import torch

# Policy network'ünde:
with torch.cuda.amp.autocast(enabled=True):
    # forward pass FP16'da çalışır
    ...
```

**Not:** SB3'te entegrasyon custom wrapper gerektirir. GPU eklenince implementasyon yapılmalı.

---

### Quick Win Özet Tablosu

| # | Değişiklik | Hızlanma | Süre | Maliyet | Öncelik |
|---|-----------|----------|------|---------|---------|
| QW-1 | SubprocessVecEnv (n=8) | 2-4x | 1 gün | $0 | 🔴 P0 |
| QW-2 | Optuna Pruning + Paralel | 3-8x | 2 gün | $0 | 🔴 P0 |
| QW-3 | Early Stopping Callback | 2-3x | 1 gün | $0 | 🔴 P0 |
| QW-4 | device="auto" GPU readiness | 4-20x* | 2 saat | $0 | 🟡 P1 |
| QW-5 | Data caching (parquet) | 1.5-2x I/O | 1 gün | $0 | 🟡 P1 |
| QW-6 | Mixed Precision hazırlığı | 1.3-1.5x* | 3 saat | $0 | 🟢 P2 |

**Kombine etki (QW1-3): 12-96x hızlanma potansiyeli**
*\* GPU bağımlı — GPU eklenince aktif olur*

---

## 5. ORTA VE UZUN VADELİ YATIRIMLAR

### 5.1 Orta Vade (1-3 Ay)

#### OV-1: GPU Bulut Pipeline (RunPod/Lambda)

**Adımlar:**
1. Docker image'ı CUDA-enabled olarak yeniden build
2. Eğitim script'ini CLI parametreli hale getir
3. RunPod serverless veya Lambda Cloud üzerinde eğitim çalıştır
4. S3/GCS'ye model artifact sync

```yaml
# docker-compose.gpu.yml
services:
  trainer:
    build:
      context: .
      dockerfile: Dockerfile.gpu
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    command: python -m drl.cli train --specialist momentum --steps 2M --device cuda
    volumes:
      - ./models:/app/models
      - ./data:/app/data
```

**Beklenen ROI:**
- RunPod A10G: $0.40/saat → Tam pipeline eğitimi ≈ 1 saat → $0.40/eğitim
- Optuna 40 trial: ~4-6 saat → $2-3/specialist
- 10 specialist full HP: ~$20-30 per sweep

---

#### OV-2: Paralel Specialist Eğitimi

**Sorun:** 10 specialist sırayla eğitiliyor.
**Çözüm:** `multiprocessing` veya `Ray` ile paralel eğitim.

```python
# Basit yaklaşım — concurrent.futures
from concurrent.futures import ProcessPoolExecutor

def train_specialist(spec_name, config):
    trainer = WalkForwardTrainer(config.env, config.algo)
    return trainer.train(config.splits)

with ProcessPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(train_specialist, name, cfg): name
               for name, cfg in specialist_configs.items()}
    for future in as_completed(futures):
        name = futures[future]
        result = future.result()
        print(f"{name} tamamlandı: sharpe={result[0].metrics.sharpe_ratio:.4f}")
```

**Beklenen Etki:**
- 4 paralel worker → toplam süre %75 azalır
- 16 CPU thread → 4 specialist × 4 env/specialist = dengeli kullanım
- GPU'da: farklı specialist'leri sıra ile ama SubprocessVecEnv ile paralel

---

#### OV-3: Offline RL Data Pipeline (SAC Replay Buffer)

**Sorun:** On-policy (PPO) her defasında sıfırdan veri topluyor — veri verimsizliği.
**Çözüm:** SAC/TD3 (off-policy) ile replay buffer + offline pre-fill.

```python
# Geçmiş eğitim verilerinden replay buffer doldur
from stable_baselines3.common.buffers import ReplayBuffer

buffer = ReplayBuffer(
    buffer_size=1_000_000,
    observation_space=env.observation_space,
    action_space=env.action_space,
    device="auto"
)

# Geçmiş episode'lardan buffer'a yükle
for episode in historical_episodes:
    for transition in episode:
        buffer.add(
            obs=transition.obs,
            next_obs=transition.next_obs,
            action=transition.action,
            reward=transition.reward,
            done=transition.done,
            infos=[transition.info]
        )

# SAC replay buffer ile başlat
model = SAC("MlpPolicy", env, replay_buffer=buffer, ...)
```

**Beklenen Etki:**
- Sample efficiency 5-10x artış (off-policy advantage)
- Aynı veri defalarca kullanılabilir → eğitim süresi %50-70 azalır

---

#### OV-4: Feature Pipeline Vektörizasyonu

**Sorun:** `calculate_technical_features()` pandas ile satır satır çalışıyor.
**Çözüm:** NumPy/Numba ile vektörel hesaplama.

```python
import numba

@numba.njit
def fast_rsi(close, period=14):
    """Numba-optimized RSI — 10-50x faster than pandas."""
    n = len(close)
    rsi = np.empty(n)
    rsi[:period] = np.nan
    gains = np.zeros(n)
    losses = np.zeros(n)
    for i in range(1, n):
        delta = close[i] - close[i-1]
        gains[i] = max(delta, 0)
        losses[i] = max(-delta, 0)
    # EMA smoothing...
    return rsi
```

---

### 5.2 Uzun Vade (3-12 Ay)

#### UV-1: Yerel GPU İstasyonu Kurulumu

**Donanım Önerisi:**

| Komponent | Bütçe ($1200) | Performans ($2500) | Profesyonel ($5000) |
|-----------|---------------|--------------------|--------------------|
| GPU | RTX 4070 Ti (12GB) | RTX 4090 (24GB) | RTX 6000 Ada (48GB) |
| CPU | Ryzen 7 7700 (8C/16T) | Ryzen 9 7900X (12C/24T) | Ryzen 9 7950X (16C/32T) |
| RAM | 32 GB DDR5 | 64 GB DDR5 | 128 GB DDR5 |
| Disk | 1 TB NVMe | 2 TB NVMe | 2 TB NVMe RAID |
| PSU | 750W 80+ Gold | 1000W 80+ Platinum | 1200W 80+ Platinum |

**Geri Ödeme Analizi (Bütçe Paket: $1200):**
- Bulut alternatif: RunPod A10G $0.40/saat, haftalık 20 saat = $8/hafta = $416/yıl
- Yerel 62 hafta (1.2 yıl) sonra kâra geçer
- 2 yıllık toplam tasarruf: ~$400-600

---

#### UV-2: Ray/RLlib Migrasyon

**Sorun:** SB3 tek GPU, tek makine sınırlı.
**Çözüm:** Ray RLlib ile dağıtık eğitim.

```python
from ray import tune
from ray.rllib.algorithms.ppo import PPOConfig

config = (
    PPOConfig()
    .environment("FinPilot-MarketEnv-v0")
    .training(
        lr=tune.loguniform(1e-5, 1e-3),
        gamma=tune.uniform(0.95, 0.999),
        num_sgd_iter=tune.choice([5, 10, 20]),
    )
    .rollouts(num_rollout_workers=8)
    .resources(num_gpus=1)
)

tuner = tune.Tuner(
    "PPO",
    param_space=config,
    tune_config=tune.TuneConfig(
        num_samples=40,
        scheduler=tune.schedulers.ASHAScheduler(
            max_t=3_000_000,
            grace_period=100_000,
            reduction_factor=3,
        ),
    ),
    run_config=tune.RunConfig(
        stop={"training_iteration": 100},
    ),
)
results = tuner.fit()
```

**Beklenen Etki:**
- Multi-GPU ve multi-node scaling
- Built-in ASHA scheduler (= Optuna pruning equivalent)
- Paralel trial + paralel env + GPU = kombine 50-100x potansiyelli

**Risk:** Yüksek migrasyon maliyeti (SB3 → RLlib). 2-4 hafta geliştirme.

---

#### UV-3: ONNX Runtime / TensorRT Inference

**Sorun:** Inference latency production'da kritik.
**Çözüm:** Eğitilmiş modeli ONNX'e çevir, TensorRT ile optimize et.

```python
# Model → ONNX export
torch.onnx.export(
    model.policy,
    dummy_input,
    "model.onnx",
    opset_version=17,
    input_names=["observation"],
    output_names=["action"],
)

# ONNX Runtime inference
import onnxruntime as ort
session = ort.InferenceSession("model.onnx")
action = session.run(None, {"observation": obs.numpy()})
# → 2-5x inference speedup, CPU'da bile
```

---

#### UV-4: CI/CD Training Pipeline

```yaml
# .github/workflows/drl-train.yml
name: DRL Training Pipeline
on:
  schedule:
    - cron: '0 2 * * 0'  # Her Pazar 02:00
  workflow_dispatch:
    inputs:
      specialist:
        description: 'Specialist to train'
        type: choice
        options: [momentum, trend, conservative, all]

jobs:
  train:
    runs-on: [self-hosted, gpu]  # veya RunPod ephemeral runner
    steps:
      - uses: actions/checkout@v4
      - name: Train specialist
        run: python -m drl.cli train --specialist ${{ inputs.specialist }}
      - name: Upload model
        uses: actions/upload-artifact@v4
        with:
          name: model-${{ inputs.specialist }}
          path: models/*.zip
```

---

## 6. MALİYET vs FAYDA ANALİZİ

### Senaryo Karşılaştırması (12 Aylık Projeksiyon)

#### Senaryo A: Sadece Quick Wins (Yazılım Optimizasyonu)

```
Maliyet:   $0 (sadece geliştirici zamanı, ~5 gün)
Hızlanma:  12-24x kombine (QW1 + QW2 + QW3)
Sonuç:
  • Tam pipeline: 6.9h → 20-35 dakika
  • Optuna full: 12 gün → 12-24 saat
  • HP arama döngüsü: haftalık yapılabilir hale gelir
Yıllık tasarruf: ~1000 geliştirici saati
```

#### Senaryo B: Quick Wins + Bulut GPU (Sprint-Tabanlı)

```
Maliyet:   ~$50-100/ay (ayda 2-3 HP arama sprint)
Hızlanma:  50-100x kombine
Sonuç:
  • Tam pipeline: 6.9h → 5-15 dakika (GPU)
  • Optuna full: 12 gün → 4-6 saat (GPU + pruning + paralel)
  • HP arama döngüsü: günlük yapılabilir
Yıllık maliyet: $600-1200
Yıllık tasarruf: ~2000 geliştirici saati
ROI: ~50-100x (zaman değerine göre)
```

#### Senaryo C: Quick Wins + Yerel GPU (Uzun Vadeli)

```
Maliyet:   $1200 başlangıç + $50/yıl elektrik
Hızlanma:  30-60x kombine
Sonuç:
  • Tam pipeline: 6.9h → 10-20 dakika
  • Optuna full: 12 gün → 4-8 saat
  • Kâra geçiş: 12-18 ay (bulut alternativine göre)
Yıllık maliyet (sonra): ~$50 elektrik
Yıllık tasarruf: ~1800 geliştirici saati
```

#### Senaryo D: Full Stack (Quick Wins + GPU + Ray)

```
Maliyet:   $1200 GPU + $500 bulut burst (yılda 2-3 kez) + 4 hafta dev
Hızlanma:  100-200x
Sonuç:
  • Tam pipeline: 6.9h → 2-5 dakika
  • Optuna full: 12 gün → 1-2 saat
  • Yeni specialist ekleme: saatler → dakikalar
  • HP arama: otomatik haftalık CI job
Yıllık maliyet: ~$2000
Yıllık tasarruf: ~3000 geliştirici saati
ROI: ~75x
```

### 📊 Maliyet-Zaman Grafiği

```
Hızlanma (x)
    │
200 │                                          ★ D (Full Stack)
    │
100 │                     ★ B (Bulut GPU)
    │
 50 │
    │              ★ C (Yerel GPU)
 25 │
    │  ★ A (Quick Wins)
 10 │
    │
  1 │● Mevcut Durum
    └──────────────────────────────────────── Maliyet ($)
    $0    $500    $1000   $1500   $2000   $2500
```

### Önerilen Uygulama Sırası

```
HAFTA 1-2:    QW-1 + QW-3 (SubprocessVecEnv + Early Stopping)     → 4-12x    $0
HAFTA 2-3:    QW-2 (Optuna Pruning)                                → 3-8x     $0
HAFTA 3-4:    QW-4 + QW-5 (GPU readiness + Data cache)            → hazırlık  $0
              ─── Quick wins tamamlandı: 12-24x hızlanma ───
AY 2:         OV-1 (RunPod GPU pipeline)                           → +4-10x   $50
AY 2-3:       OV-2 (Paralel specialist eğitimi)                   → +2-4x    $0
AY 3:         OV-3 (SAC off-policy pilot)                          → +5-10x   $0
              ─── Orta vade tamamlandı: 50-100x hızlanma ───
AY 4-6:       UV-1 (Yerel GPU istasyonu, opsiyonel)               → sabit     $1200
AY 6-9:       UV-2 (Ray/RLlib migrasyon)                          → +2-5x    dev time
AY 9-12:      UV-4 (CI/CD Training Pipeline)                      → otomatik  $0
              ─── Uzun vade tamamlandı: 100-200x hızlanma ───
```

---

## 7. ÖNCELİK MATRİSİ (Impact vs Effort)

```
          YÜKSEK ETKİ
              │
    QW-2 ◆   │   ◆ OV-1 (Bulut GPU)
  (Pruning)   │   ◆ UV-2 (Ray)
              │
    QW-1 ◆   │   ◆ OV-2 (Paralel)
  (VecEnv)    │
              │
    QW-3 ◆   │   ◆ OV-3 (SAC)
  (EarlyStop) │
──────────────┼──────────────────
    QW-4 ◆   │   ◆ UV-1 (Yerel GPU)
  (device)    │
              │
    QW-5 ◆   │   ◆ UV-3 (ONNX)
  (cache)     │
              │   ◆ UV-4 (CI/CD)
    QW-6 ◆   │
  (FP16)      │
              │
          DÜŞÜK ETKİ
    KOLAY ←───┼───→ ZOR
```

---

## 8. SONUÇ VE TAVSİYELER

### İlk 30 Gün Eylem Planı

1. **Gün 1-2:** `SubprocessVecEnv(n=8)` implementasyonu → ani 3-4x hızlanma
2. **Gün 3-4:** `StopTrainingOnNoModelImprovement` callback ekleme → %40-60 timestep tasarrufu
3. **Gün 5-7:** Optuna `SuccessiveHalvingPruner` + paralel worker → HP arama 12 gün → 1-2 gün
4. **Gün 8:** `device="auto"` tüm model oluşturuculara ekleme → GPU-ready
5. **Gün 9-10:** Parquet data cache implementasyonu → I/O eliminasyonu
6. **Gün 11-14:** Colab/Kaggle T4 ile ilk GPU eğitim testi → ek 4-5x

**30 gün sonunda beklenen durum:**
- CPU-only hızlanma: **12-24x** (6.9 saat → 20-35 dakika)
- GPU ile: **50-100x** (6.9 saat → 5-10 dakika)
- Optuna: **12 gün → 4-12 saat**

### Stratejik Notlar

1. **Model kalitesi > hız.** Sharpe 0.057 iken 100x hızlanma anlamsız. QW-3 (early stopping) ve OV-3 (SAC off-policy) model kalitesini de doğrudan etkiler.
2. **Darboğazları sırayla kaldır.** SubprocessVecEnv başarılı olunca GPU eklemenin etkisi daha büyük olur (Amdahl Yasası).
3. **Bulut maliyetini kontrol altında tut.** Spot/preemptible instance + checkpoint-resume gerekli.
4. **Gizlilik öncelik.** Finansal veri buluta gönderilecekse, şifrelenmiş transfer + ephemeral instance + no-log policy zorunlu.

---

*Bu yol haritası FinPilot projesinin 2026-03 itibarıyla mevcut durumuna göre hazırlanmıştır. Donanım fiyatları ve bulut ücretleri değişkenlik gösterebilir.*
