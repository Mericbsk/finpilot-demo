"""FinPilot DRL package.

This package hosts production-grade components for the reinforcement learning
engine, including:

- ``feature_pipeline``: transforms raw market, regime, and alternative data into
  normalized feature arrays that satisfy the MarketEnv contract.
- ``market_env``: OpenAI Gym compatible trading environment with reward shaping
  and risk controls.
- ``multi_asset_env``: Multi-asset portfolio management environment with softmax
  weight allocation and diversification rewards.
- ``config``: central configuration schema for feature sets, hyperparameters,
  and risk guardrails (PilotShield integration).
- ``training``: walk-forward training supporting PPO, SAC, TD3, A2C algorithms.
- ``optuna_search``: Optuna-powered hyperparameter optimisation over the full
  training loop using the production MarketEnv.
- ``callbacks``: Curriculum learning and training metrics callbacks for SB3.
- ``persistence``: serialisation utilities for feature pipelines and other
  preprocessing artefacts.
- ``monitoring``: (optional) metrics hooks and drift detection utilities.
- ``feature_generators``: reusable feature engineering helpers (sentiment, momentum, lags).
- ``alignment_helpers``: resampling and forward-fill utilities for multi-frequency data.

Modules are designed to be composable so the Streamlit dashboard, batch jobs,
and paper-trading services can share the same DRL primitives.
"""
