"""FinPilot DRL package.

This package hosts production-grade components for the reinforcement learning
engine, including:

- ``feature_pipeline``: transforms raw market, regime, and alternative data into
  normalized feature arrays that satisfy the MarketEnv contract.
- ``market_env``: OpenAI Gym compatible trading environment with reward shaping
  and risk controls.
- ``config``: central configuration schema for feature sets, hyperparameters,
  and risk guardrails (PilotShield integration).
- ``training``: walk-forward training, hyperparameter optimisation, and model
  registry helpers.
- ``persistence``: serialisation utilities for feature pipelines and other
  preprocessing artefacts.
- ``monitoring``: (optional) metrics hooks and drift detection utilities.
- ``feature_generators``: reusable feature engineering helpers (sentiment, momentum, lags).
- ``alignment_helpers``: resampling and forward-fill utilities for multi-frequency data.

Modules are designed to be composable so the Streamlit dashboard, batch jobs,
and paper-trading services can share the same DRL primitives.
"""
