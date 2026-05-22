# FinPilot Feature Flags

Sprint 16 (S16-09) — Experimental modules are off by default until a live edge
is demonstrated through the closed-loop calibration audit.

| Env Var | Default | Module | Status |
|---|---|---|---|
| `FINPILOT_ENABLE_DRL` | `0` (de-facto via `_W_DRL=0.0`) | `scanner/finpilot_score.py` | Layer-2 PPO weight zeroed; flip `_W_DRL` after WFO sign-off |
| `FINPILOT_ENABLE_LGBM_RANKER` | `0` | `research/lgbm_ranker.py` | PoC; no consumer wired yet |
| `FINPILOT_ENABLE_REGIME_WEIGHTS` | `0` | `core/regime_weights.py` | Bull/bear/range weights; consumer pending |

## How to check

```python
from research.lgbm_ranker import is_enabled as lgbm_enabled
from core.regime_weights import is_enabled as regime_enabled

if lgbm_enabled():
    ...  # call LGBMRanker
```

## Promotion rules

A module graduates from feature-flagged to default-on only when:

1. Walk-forward AUC / Brier improvement vs. champion is ≥ 5 % on ≥ 100 resolved signals.
2. The closed-loop audit log shows `promoted` (not `rolled_back`) on the new model.
3. A consumer integration ships in the same PR as the flag flip.

## Sprint 16 status

- `lgbm_ranker.is_enabled()` — exposed; no consumer yet (deferred to Sprint 17).
- `regime_weights.is_enabled()` — exposed; consumer wiring deferred to Sprint 17.
- `_W_DRL=0.0` in `scanner/finpilot_score.py` — already gates DRL output.
