"""Integration test for all new DRL components.

Tests:
1. TD3 + A2C algorithm support in WalkForwardTrainer
2. CurriculumCallback during training
3. Optuna hyperparameter search
4. MultiAssetMarketEnv
"""

from __future__ import annotations

import sys
import time
import traceback

import numpy as np
import pandas as pd

# ============================================================================
# Helpers
# ============================================================================

PASS = "✅"
FAIL = "❌"
results = []


def report(name: str, passed: bool, detail: str = "") -> None:
    status = PASS if passed else FAIL
    results.append((name, passed, detail))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))


def make_synthetic_df(length: int = 512, seed: int = 42) -> pd.DataFrame:
    """Create a synthetic DataFrame matching FinPilot feature contract."""
    rng = np.random.RandomState(seed)
    idx = pd.date_range("2024-01-01", periods=length, freq="h")
    close = 100 + np.cumsum(rng.randn(length) * 0.5)
    close = np.maximum(close, 10)  # keep positive
    df = pd.DataFrame(
        {
            "close": close,
            "ema_20": pd.Series(close).ewm(span=20).mean().values,
            "ema_50": pd.Series(close).ewm(span=50).mean().values,
            "ema_200": pd.Series(close).ewm(span=200).mean().values,
            "rsi": np.clip(50 + rng.randn(length) * 15, 5, 95),
            "macd": rng.randn(length) * 0.5,
            "macd_signal": rng.randn(length) * 0.3,
            "macd_hist": rng.randn(length) * 0.2,
            "atr": np.abs(rng.randn(length)) + 0.5,
            "bb_upper": close + np.abs(rng.randn(length)) * 2 + 1,
            "bb_lower": close - np.abs(rng.randn(length)) * 2 - 1,
            "volume": 1_000_000 + rng.randint(0, 500_000, length).astype(float),
            "volume_avg_20": 1_000_000 + rng.randint(0, 200_000, length).astype(float),
            "regime_trend": rng.uniform(0.0, 1.0, length),
            "regime_range": rng.uniform(0.0, 1.0, length),
            "regime_volatility": rng.uniform(0.0, 1.0, length),
            "sentiment_score": rng.uniform(-1, 1, length),
            "news_sentiment": rng.uniform(-1, 1, length),
            "onchain_active_addresses": rng.uniform(10, 100, length),
            "onchain_tx_volume": rng.uniform(100, 1000, length),
            "cash_ratio": rng.uniform(0.3, 0.8, length),
            "position_ratio": rng.uniform(-0.3, 0.3, length),
            "open_risk": rng.uniform(0.01, 0.2, length),
            "kelly_fraction": rng.uniform(0.1, 0.5, length),
        },
        index=idx,
    )
    return df.bfill().ffill()


def make_episode(df: pd.DataFrame):
    from drl.feature_pipeline import FeatureFrame
    from drl.market_env import EpisodeData

    return EpisodeData(
        features=FeatureFrame(data=df),
        prices=df["close"],
        regimes=df.get("regime_trend").map(lambda x: "trend" if x > 0.5 else "range")
        if "regime_trend" in df.columns
        else None,
        timestamps=df.index,
    )


def make_splits(df: pd.DataFrame, n_splits: int = 2):
    from drl.training import WalkForwardSplit

    split_size = len(df) // (n_splits + 1)
    splits = []
    for i in range(n_splits):
        train_end = split_size * (i + 1)
        test_end = min(train_end + split_size, len(df))
        train_df = df.iloc[:train_end].copy()
        test_df = df.iloc[train_end:test_end].copy()
        splits.append(
            WalkForwardSplit(
                train=make_episode(train_df),
                test=make_episode(test_df),
                label=f"split_{i + 1}",
            )
        )
    return splits


# ============================================================================
# Test 1: TD3 + A2C Algorithm Support
# ============================================================================


def test_algorithm_support():
    print("\n" + "=" * 60)
    print("  TEST 1: TD3 + A2C Algoritma Desteği")
    print("=" * 60)

    from drl.config import DEFAULT_CONFIG
    from drl.training import WalkForwardConfig, WalkForwardTrainer

    df = make_synthetic_df(length=128)
    splits = make_splits(df, n_splits=1)

    for algo in ["PPO", "SAC", "TD3", "A2C"]:
        try:
            config = WalkForwardConfig(
                algorithm=algo,
                total_timesteps=500,  # very short for testing
                seed=42,
            )
            trainer = WalkForwardTrainer(DEFAULT_CONFIG, config)
            results_list = trainer.train(splits)

            has_metrics = (
                results_list
                and results_list[0].metrics is not None
                and results_list[0].metrics.sharpe_ratio is not None
            )
            report(
                f"{algo} eğitimi",
                has_metrics,
                f"sharpe={results_list[0].metrics.sharpe_ratio:.4f}"
                if has_metrics
                else "metrik yok",
            )
        except Exception as e:
            report(f"{algo} eğitimi", False, str(e)[:80])


# ============================================================================
# Test 2: Curriculum Learning Callback
# ============================================================================


def test_curriculum_callback():
    print("\n" + "=" * 60)
    print("  TEST 2: Curriculum Learning Callback")
    print("=" * 60)

    from drl.callbacks import CurriculumCallback, CurriculumConfig, TrainingMetricsCallback
    from drl.config import DEFAULT_CONFIG
    from drl.training import WalkForwardConfig, WalkForwardTrainer

    # Test config phases
    try:
        cc = CurriculumConfig(total_timesteps=1000)
        assert len(cc.phases) == 3, f"Expected 3 phases, got {len(cc.phases)}"
        phase_easy = cc.get_phase(0.1)
        assert phase_easy.name == "easy", f"Expected 'easy', got '{phase_easy.name}'"
        phase_hard = cc.get_phase(0.8)
        assert phase_hard.name == "hard", f"Expected 'hard', got '{phase_hard.name}'"
        report("CurriculumConfig fazları", True, "3 faz doğru tanımlı")
    except Exception as e:
        report("CurriculumConfig fazları", False, str(e)[:80])

    # Test interpolation
    try:
        params_easy = cc.interpolate(0.1)
        params_hard = cc.interpolate(0.9)
        assert (
            params_easy["cost_multiplier"] < params_hard["cost_multiplier"]
        ), "Easy cost should be < hard cost"
        report(
            "Interpolasyon",
            True,
            f"easy_cost={params_easy['cost_multiplier']:.2f} < hard_cost={params_hard['cost_multiplier']:.2f}",
        )
    except Exception as e:
        report("Interpolasyon", False, str(e)[:80])

    # Test callback with actual training
    try:
        df = make_synthetic_df(length=128)
        splits = make_splits(df, n_splits=1)

        curriculum = CurriculumCallback(
            CurriculumConfig(total_timesteps=500),
            verbose=0,
        )
        metrics_cb = TrainingMetricsCallback(log_interval=100, verbose=0)

        config = WalkForwardConfig(algorithm="PPO", total_timesteps=500, seed=42)
        trainer = WalkForwardTrainer(DEFAULT_CONFIG, config)

        # Use the callbacks via _create_model
        from drl.feature_pipeline import FeaturePipeline

        pipeline = FeaturePipeline(DEFAULT_CONFIG)
        pipeline.fit(splits[0].train.features)
        trainer._create_model(pipeline, splits[0].train, callbacks=[curriculum, metrics_cb])

        phase_history = curriculum.get_phase_history()
        report(
            "Callback eğitim entegrasyonu",
            True,
            f"{len(phase_history)} faz geçişi kaydedildi",
        )
    except Exception as e:
        report("Callback eğitim entegrasyonu", False, str(e)[:80])


# ============================================================================
# Test 3: Optuna Hyperparameter Search
# ============================================================================


def test_optuna_search():
    print("\n" + "=" * 60)
    print("  TEST 3: Optuna Hiperparametre Arama")
    print("=" * 60)

    from drl.config import DEFAULT_CONFIG
    from drl.optuna_search import (
        OptunaSearchConfig,
        build_config_from_best,
        run_optuna_search,
    )

    df = make_synthetic_df(length=128)
    splits = make_splits(df, n_splits=1)

    try:
        search_config = OptunaSearchConfig(
            n_trials=3,  # very few for testing
            total_timesteps=300,
            seed=42,
            search_reward_weights=True,
            search_pilotshield=False,
            search_algorithm=False,
            algorithms=("PPO",),
            verbose=False,
            show_progress_bar=False,
        )

        result = run_optuna_search(DEFAULT_CONFIG, splits, search_config)

        report(
            "Optuna arama çalıştı",
            result.n_trials_completed == 3,
            f"{result.n_trials_completed} deneme tamamlandı",
        )
        report(
            "En iyi parametreler bulundu",
            len(result.best_params) > 0,
            f"{len(result.best_params)} parametre: {list(result.best_params.keys())[:4]}...",
        )
        report(
            "En iyi değer",
            result.best_value != float("-inf"),
            f"best_value={result.best_value:.4f}",
        )
    except Exception as e:
        report("Optuna arama", False, str(e)[:120])
        traceback.print_exc()
        return

    # Test config reconstruction
    try:
        env_cfg, algo_cfg = build_config_from_best(DEFAULT_CONFIG, result.best_params)
        assert algo_cfg.learning_rate > 0
        report(
            "Config yeniden oluşturma",
            True,
            f"lr={algo_cfg.learning_rate:.6f}, gamma={algo_cfg.gamma:.4f}",
        )
    except Exception as e:
        report("Config yeniden oluşturma", False, str(e)[:80])


# ============================================================================
# Test 4: Multi-Asset Environment
# ============================================================================


def test_multi_asset_env():
    print("\n" + "=" * 60)
    print("  TEST 4: Multi-Asset Ortam")
    print("=" * 60)

    from drl.config import DEFAULT_CONFIG
    from drl.feature_pipeline import FeaturePipeline
    from drl.multi_asset_env import MultiAssetEpisode, MultiAssetMarketEnv

    # Create synthetic data for 3 assets
    assets = {}
    for i, symbol in enumerate(["AAPL", "MSFT", "GOOGL"]):
        df = make_synthetic_df(length=128, seed=42 + i)
        assets[symbol] = make_episode(df)

    episode = MultiAssetEpisode(assets=assets)

    try:
        assert episode.n_assets == 3
        assert episode.symbols == ["AAPL", "MSFT", "GOOGL"]
        report("MultiAssetEpisode", True, f"{episode.n_assets} varlık")
    except Exception as e:
        report("MultiAssetEpisode", False, str(e)[:80])

    # Test environment
    try:
        pipeline = FeaturePipeline(DEFAULT_CONFIG)
        env = MultiAssetMarketEnv(episode, pipeline, DEFAULT_CONFIG)

        obs, info = env.reset()
        assert obs.shape[0] == env._obs_dim, f"Obs shape mismatch: {obs.shape[0]} vs {env._obs_dim}"
        report(
            "Env reset",
            True,
            f"obs_dim={obs.shape[0]} (per_asset={env._per_asset_features} × {env._n_assets} + {env._portfolio_state_dim})",
        )
    except Exception as e:
        report("Env reset", False, str(e)[:80])
        traceback.print_exc()
        return

    # Test step
    try:
        action = np.array([0.5, 0.3, 0.2], dtype=np.float32)
        obs2, reward, terminated, truncated, info = env.step(action)
        assert "weights" in info
        assert "equity" in info
        weights = info["weights"]
        total_w = sum(weights.values())
        report(
            "Env step",
            abs(total_w - 1.0) < 0.01,
            f"weights sum={total_w:.4f}, equity={info['equity']:.4f}",
        )
    except Exception as e:
        report("Env step", False, str(e)[:80])

    # Test full episode
    try:
        obs, _ = env.reset()
        total_reward = 0.0
        steps = 0
        done = False
        while not done:
            action = env.action_space.sample()
            result = env.step(action)
            obs, r, terminated, truncated, info = result
            total_reward += r
            steps += 1
            done = terminated or truncated

        history = env.get_history()
        portfolio = env.get_portfolio_state()
        report(
            "Tam episod",
            steps > 10 and len(history) == steps,
            f"{steps} adım, toplam_ödül={total_reward:.4f}, son_equity={portfolio.equity:.4f}",
        )
    except Exception as e:
        report("Tam episod", False, str(e)[:80])

    # Test with SB3 PPO training
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv

        def _make():
            p = FeaturePipeline(DEFAULT_CONFIG)
            return MultiAssetMarketEnv(episode, p, DEFAULT_CONFIG)

        vec_env = DummyVecEnv([_make])
        model = PPO("MlpPolicy", vec_env, verbose=0, n_steps=64)
        model.learn(total_timesteps=200)
        report("Multi-asset PPO eğitimi", True, "200 adım başarılı")
    except Exception as e:
        report("Multi-asset PPO eğitimi", False, str(e)[:80])


# ============================================================================
# Test 5: Cross-Component Integration
# ============================================================================


def test_integration():
    print("\n" + "=" * 60)
    print("  TEST 5: Bileşen Arası Entegrasyon")
    print("=" * 60)

    # Test: Optuna search with TD3
    try:
        from drl.config import DEFAULT_CONFIG
        from drl.optuna_search import OptunaSearchConfig, run_optuna_search

        df = make_synthetic_df(length=128)
        splits = make_splits(df, n_splits=1)

        config = OptunaSearchConfig(
            n_trials=2,
            total_timesteps=200,
            seed=42,
            search_algorithm=True,
            algorithms=("PPO", "TD3"),
            search_reward_weights=False,
            verbose=False,
            show_progress_bar=False,
        )
        result = run_optuna_search(DEFAULT_CONFIG, splits, config)
        report(
            "Optuna + çoklu algoritma",
            result.n_trials_completed == 2,
            f"best_algo in params: {'algorithm' in result.best_params}",
        )
    except Exception as e:
        report("Optuna + çoklu algoritma", False, str(e)[:80])

    # Test: Import chain
    try:
        from drl.optuna_search import run_optuna_search

        report("Import zincirleri", True, "Tüm modüller yüklendi")
    except Exception as e:
        report("Import zincirleri", False, str(e)[:80])


# ============================================================================
# MAIN
# ============================================================================


def main():
    print("=" * 60)
    print("  FinPilot DRL — Entegrasyon Testi")
    print("=" * 60)

    start_time = time.time()

    test_algorithm_support()
    test_curriculum_callback()
    test_optuna_search()
    test_multi_asset_env()
    test_integration()

    elapsed = time.time() - start_time

    # Summary
    print("\n" + "=" * 60)
    print("  ÖZET")
    print("=" * 60)
    passed = sum(1 for _, p, _ in results if p)
    failed = sum(1 for _, p, _ in results if not p)
    total = len(results)
    print(f"  Toplam: {total} | Geçti: {passed} | Kaldı: {failed}")
    print(f"  Süre: {elapsed:.1f}s")

    if failed:
        print(f"\n  {FAIL} BAŞARISIZ TESTLER:")
        for name, p, detail in results:
            if not p:
                print(f"    • {name}: {detail}")

    print("=" * 60)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
