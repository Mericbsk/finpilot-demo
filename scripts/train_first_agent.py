"""İlk DRL Agent Eğitimi - Hızlı Test

Bu script ilk agentınızı eğitir ve kaydeder.
Süre: ~5-10 dakika
"""

import sys
from datetime import datetime

print("=" * 60)
print("🚀 İLK DRL AGENT EĞİTİMİ")
print("=" * 60)

# 1. Gerekli importlar
print("\n[1/6] Kütüphaneler yükleniyor...")
try:
    import numpy as np
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    print("✅ Stable-Baselines3 yüklendi")
except ImportError as e:
    print(f"❌ Hata: {e}")
    print("Çözüm: pip install stable-baselines3[extra]")
    sys.exit(1)

try:
    from drl.config import DEFAULT_CONFIG
    from drl.feature_pipeline import FeatureFrame, FeaturePipeline
    from drl.market_env import EpisodeData, MarketEnv

    print("✅ DRL modülleri yüklendi")
except ImportError as e:
    print(f"❌ Hata: {e}")
    sys.exit(1)

# 2. Sentetik veri üret
print("\n[2/6] Sentetik test verisi oluşturuluyor...")
import pandas as pd

np.random.seed(42)
n_samples = 500

dates = pd.date_range(end=datetime.now(), periods=n_samples, freq="h")
close = 100 + np.cumsum(np.random.randn(n_samples) * 2)
volume = np.abs(np.random.randn(n_samples) * 1000000)

# DEFAULT_CONFIG feature'larına uygun DataFrame
df = pd.DataFrame(
    {
        "close": close,
        "ema_20": close + np.random.randn(n_samples) * 1,
        "ema_50": close + np.random.randn(n_samples) * 2,
        "ema_200": close + np.random.randn(n_samples) * 5,
        "rsi": 50 + np.random.randn(n_samples) * 15,
        "macd": np.random.randn(n_samples) * 2,
        "macd_signal": np.random.randn(n_samples) * 1.5,
        "macd_hist": np.random.randn(n_samples) * 1,
        "atr": np.abs(np.random.randn(n_samples) * 3),
        "bb_upper": close + np.abs(np.random.randn(n_samples) * 5),
        "bb_lower": close - np.abs(np.random.randn(n_samples) * 5),
        "volume": volume,
        "volume_avg_20": volume * (1 + np.random.randn(n_samples) * 0.1),
        # Regime (basit)
        "regime_trend": np.random.randint(0, 2, n_samples),
        "regime_range": np.random.randint(0, 2, n_samples),
        "regime_volatility": np.random.randint(0, 2, n_samples),
        # Portfolio state (başlangıç değerleri)
        "cash_ratio": np.ones(n_samples) * 0.5,
        "position_ratio": np.ones(n_samples) * 0.5,
        "open_risk": np.random.rand(n_samples) * 0.1,
        "kelly_fraction": np.random.rand(n_samples) * 0.3,
    },
    index=dates,
)

print(f"✅ {n_samples} timestep veri oluşturuldu")

# 3. Environment hazırla
print("\n[3/6] Trading environment hazırlanıyor...")

feature_frame = FeatureFrame(data=df)

episode_data = EpisodeData(
    features=feature_frame, prices=pd.Series(close, index=dates), timestamps=dates
)

pipeline = FeaturePipeline(DEFAULT_CONFIG)
pipeline.fit(feature_frame)


def make_env():
    return MarketEnv(episode_data, pipeline, DEFAULT_CONFIG)


env = DummyVecEnv([make_env])
print("✅ Environment hazır")

# 4. Model oluştur
print("\n[4/6] PPO Agent oluşturuluyor...")

model = PPO(
    "MlpPolicy",
    env,
    learning_rate=3e-4,
    n_steps=128,
    batch_size=64,
    gamma=0.99,
    verbose=1,
    tensorboard_log="./logs/tensorboard/",
)

print("✅ PPO Agent oluşturuldu")
print("   - Policy: MlpPolicy")
print("   - Learning Rate: 3e-4")

# 5. Eğitim
print("\n[5/6] Eğitim başlıyor...")
print("⏱️  Tahmini süre: 5-10 dakika")
print("-" * 60)

try:
    model.learn(total_timesteps=10_000, progress_bar=True)
    print("-" * 60)
    print("✅ Eğitim tamamlandı!")
except Exception as e:
    print(f"❌ Eğitim hatası: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# 6. Model kaydet
print("\n[6/6] Model kaydediliyor...")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
model_path = f"models/ppo_first_{timestamp}.zip"
model.save(model_path)

print(f"✅ Model kaydedildi: {model_path}")

# Test prediction
print("\n" + "=" * 60)
print("🧪 TEST PREDICTION")
print("=" * 60)

obs = env.reset()
action, _states = model.predict(obs, deterministic=True)

print(f"Sample State Shape: {obs[0].shape}")
print(f"Agent Action: {action[0]:.3f}")

if action[0] > 0.3:
    decision = "📈 LONG (AL)"
elif action[0] < -0.3:
    decision = "📉 SHORT (SAT)"
else:
    decision = "⏸️  HOLD (BEKLE)"

print(f"Karar: {decision}")

# Özet
print("\n" + "=" * 60)
print("✅ İLK AGENT EĞİTİMİ TAMAMLANDI!")
print("=" * 60)
print(f"""
📦 Model: {model_path}
🎯 Timesteps: 10,000
🧠 Algoritma: PPO

Sonraki Adımlar:
1. Gerçek data ile test
2. Daha uzun eğitim (100K timesteps)
3. Parallel testing başlat
""")

print("🎉 Tamamlandı!\n")
