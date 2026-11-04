# FRM_probe.py - R4 audit (Formula and Feature Registry) offline probes.
# Read-only: no network, no scanner package import (standalone file loads of
# side-effect-free modules + AST extraction of pure functions). Writes only
# <audit>/data/FRM_*.{json,csv}. Feature-flag env vars are cleared in-process.
import __future__
import ast
import csv
import glob
import hashlib
import importlib.util
import io
import json
import logging
import math
import os
import time
from statistics import median
from typing import Any

import numpy as np
import pandas as pd

T0 = time.time()
ROOT = r"C:\Users\meric\Borsa"
AUD = os.path.join(ROOT, "reports", "scanner_intelligence_audit_v1_2026-10-19")
OUT = os.path.join(AUD, "data")
os.makedirs(OUT, exist_ok=True)
RES = {}
FLAGS = ["FINPILOT_ENABLE_SQUEEZE_FACTOR", "FINPILOT_ENABLE_EDGAR_CATALYST",
         "FINPILOT_ENABLE_LOTTERY_FADE", "FINPILOT_ENABLE_OVERNIGHT_GAP",
         "FINPILOT_ENABLE_FRED_MACRO", "FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING",
         "FINPILOT_ENABLE_ALPHA_V2", "FINPILOT_ENABLE_CONVICTION_TIERS",
         "FINPILOT_ENABLE_PORTFOLIO_ADV_LIMIT", "FINPILOT_MAX_POSITION_ADV_FRACTION"]
for _k in FLAGS:
    os.environ.pop(_k, None)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_standalone(rel, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(ROOT, rel))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def extract(rel, names, g):
    path = os.path.join(ROOT, rel)
    tree = ast.parse(open(path, encoding="utf-8").read())
    body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    code = compile(ast.Module(body=body, type_ignores=[]), path, "exec",
                   flags=__future__.annotations.compiler_flag, dont_inherit=True)
    ns = dict(g)
    exec(code, ns)
    miss = [n for n in names if n not in ns]
    if miss:
        print("EXTRACT-MISSING", rel, miss)
    return ns


def run(name):
    def deco(fn):
        try:
            fn()
        except Exception as exc:
            print("SECTION-ERROR", name, type(exc).__name__, str(exc)[:200])
            RES[name] = {"error": "%s: %s" % (type(exc).__name__, str(exc)[:200])}
        return fn
    return deco


# ---------------- line finder ----------------
SNIPS = [
    ("ev.dd_gate", "scanner/evaluate.py", "if daily_dd_breached(threshold=0.03)"),
    ("ev.full_hist", "scanner/evaluate.py", "_has_full_history = len(df_1d) >= 200"),
    ("ev.regime", "scanner/evaluate.py", "regime = c_daily > e200_daily"),
    ("ev.direction", "scanner/evaluate.py", "direction = c_daily > e50_daily"),
    ("ev.raw_rsi", "scanner/evaluate.py", 'if 30 <= safe_float(row["rsi"]) <= 70'),
    ("ev.raw_vol", "scanner/evaluate.py", 'safe_float(row["vol_med20"]) * 1.2'),
    ("ev.raw_macd", "scanner/evaluate.py", 'if safe_float(row["macd_hist"]) > 0 and'),
    ("ev.last_price", "scanner/evaluate.py", 'last_price = df_15m["Close"].iloc[-1]'),
    ("ev.filter_score", "scanner/evaluate.py", "filter_score = int(volume_spike)"),
    ("ev.vol_mult", "scanner/evaluate.py", "volume_multiple = (current_vol / avg_vol)"),
    ("ev.ema_gap", "scanner/evaluate.py", "ema_gap_pct = (((ema50 - ema200) / ema200) * 100)"),
    ("ev.min_score", "scanner/evaluate.py", "min_score_threshold = 3"),
    ("ev.core_signal", "scanner/evaluate.py", "core_signal = bool("),
    ("ev.entry_ok", "scanner/evaluate.py", "entry_ok = bool(score == 3)"),
    ("ev.price_ok_true", "scanner/evaluate.py", "price_ok = True"),
    ("ev.avgvol_ok_true", "scanner/evaluate.py", "avg_vol_ok = True"),
    ("ev.liquidity_ok", "scanner/evaluate.py", "liquidity_ok = bool(price_ok and avg_vol_ok)"),
    ("ev.rsi_score", "scanner/evaluate.py", "rsi_score = max(0, min(100,"),
    ("ev.mom_score", "scanner/evaluate.py", "momentum_score = (rsi_score * 0.4)"),
    ("ev.mom_score50", "scanner/evaluate.py", "momentum_score = 50"),
    ("ev.vol_regime", "scanner/evaluate.py", 'vol_regime_val = alpha.get("vol_regime", 1)'),
    ("ev.lottery", "scanner/evaluate.py", "lottery_factor = compute_lottery_factor(df_1d)"),
    ("ev.overnight", "scanner/evaluate.py", "overnight_gap_factor = compute_overnight_gap_factor(df_1d)"),
    ("ev.composite", "scanner/evaluate.py", "_composite_score = compute_recommendation_strength("),
    ("ev.ann_vol", "scanner/evaluate.py", "_ann_vol_pct = float("),
    ("ev.dyn_pos", "scanner/evaluate.py", "_dyn_pos = calculate_dynamic_position("),
    ("ev.atr_pct", "scanner/evaluate.py", "_atr_pct_daily = compute_atr_pct(df_1d)"),
    ("ev.conviction", "scanner/evaluate.py", "compute_conviction("),
    ("ev.legacy_rvol", "scanner/evaluate.py", "rvol=(1.0 + float(alpha_rvol) * 2.0"),
    ("ev.pos_cap", "scanner/evaluate.py", "_position_cap = position_cap("),
    ("ev.ret_pos_size", "scanner/evaluate.py", '"position_size": risk_data["position_size"]'),
    ("ev.ret_pos_cap", "scanner/evaluate.py", "**_position_cap,"),
    ("ev.pos_gated", "scanner/evaluate.py", '"position_size_gated": int('),
    ("ev.kelly_default", "scanner/evaluate.py", "kelly_fraction: float = 0.5"),
    ("se.max", "scanner/score_engine.py", "MAX_RECO_SCORE: float = 16.5"),
    ("se.filter15", "scanner/score_engine.py", 'score += float(row.get("filter_score", 0)) * 1.5'),
    ("se.vs05", "scanner/score_engine.py", 'score += 0.5 if bool(row.get("volume_spike"'),
    ("se.mom_w", "scanner/score_engine.py", "mom_weight = _VOL_REGIME_MOM_WEIGHTS.get(vol_regime, 2.0)"),
    ("se.bd_filter", "scanner/score_engine.py", '"filter_score": float(row.get("filter_score", 0)) * 1.5'),
    ("se.bd_vs", "scanner/score_engine.py", '"volume_spike": 0.5 if'),
    ("se.leg_base", "scanner/score_engine.py", "base = 2.0 * float(regime)"),
    ("se.leg_total", "scanner/score_engine.py", "(base + 1.5 * atr"),
    ("se.strength", "scanner/score_engine.py", "strength = max(0.0, min(100.0,"),
    ("sg.spike", "scanner/signals.py", 'return current_vol > avg_vol * SETTINGS.get("vol_multiplier", 1.5)'),
    ("sg.baseline", "scanner/signals.py", "recent_window = momentum_series.tail(baseline_window)"),
    ("sg.std0", "scanner/signals.py", "std_fraction = float(recent_window.std(ddof=0))"),
    ("sg.seg_thr", "scanner/signals.py", "z_threshold = float(segment_threshold or base_threshold)"),
    ("sg.thr_clip", "scanner/signals.py", "z_threshold = max(dynamic_min, min(dynamic_max, float(z_threshold)))"),
    ("sg.positive", "scanner/signals.py", 'positive = any(item["zscore"] >= z_threshold'),
    ("sg.trend_thr", "scanner/signals.py", 'return strength_pct >= SETTINGS.get("trend_gap_pct", 3.0)'),
    ("sg.ema20_1h", "scanner/signals.py", "ewm(span=20).mean()"),
    ("sg.trend_1d", "scanner/signals.py", "trend_1d = price_1d > ema200_1d"),
    ("sg.align_ratio", "scanner/signals.py", "alignment_ratio = bullish_count / total_count"),
    ("sg.macd15", "scanner/signals.py", "if macd_15m > 0.01"),
    ("sg.macd4h", "scanner/signals.py", "if macd_4h > 0.01"),
    ("sg.conf_ratio", "scanner/signals.py", "confluence_ratio = confluence_score / max_score"),
    ("ps.gt62", "scanner/position_sizer.py", "composite_score > 62"),
    ("ps.kelly_frac", "scanner/position_sizer.py", "DEFAULT_KELLY_FRAC = 0.25"),
    ("ps.win_rate", "scanner/position_sizer.py", "win_rate = _clamp(0.30"),
    ("ps.adj_risk", "scanner/position_sizer.py", "adjusted_risk_pct = min(base_risk_pct * reg_scale, kelly_sz)"),
    ("ps.vol_scale", "scanner/position_sizer.py", "vol_scale = _clamp(baseline_vol / ann_vol_pct, 0.4, 2.0)"),
    ("rk.tail", "scanner/risk_engine.py", "tail = df[needed].tail(window + 1).copy()"),
    ("rk.yz_call", "scanner/risk_engine.py", "yz_val = yang_zhang_vol(df, window=yz_window)"),
    ("rk.stop", "scanner/risk_engine.py", "stop_loss = price - (atr_val * stop_mult)"),
    ("rk.tp", "scanner/risk_engine.py", "take_profit = tp2"),
    ("rk.pos1000", "scanner/risk_engine.py", "position_size = 1000"),
    ("ft.conv_prob", "scanner/features.py", "_CONV_PROB = {"),
    ("ft.atr_loop", "scanner/features.py", "for j in range(len(df) - 14, len(df)):"),
    ("ft.rvol_win", "scanner/features.py", 'window = df["Volume"].iloc[-21:-1]'),
    ("ft.rv", "scanner/features.py", "rv = float(daily_rets.iloc[-20:].std() * (252**0.5))"),
    ("ft.lottery", "scanner/features.py", "lottery = 0.30 * max_comp + 0.30 * ivol_comp"),
    ("ep.adv_frac", "scanner/execution_policy.py", "MAX_POSITION_ADV_FRACTION = 0.005"),
    ("ep.tp_atr2", "scanner/execution_policy.py", '"tp_atr": 2.0,'),
    ("ep.cap", "scanner/execution_policy.py", '"position_notional": round(min(requested, cap)'),
    ("in.volmed", "scanner/indicators.py", 'df["vol_med20"] = vol.rolling(20).median()'),
    ("in.atr_ewm", "scanner/indicators.py", "return tr.ewm(alpha=1 / period, adjust=False).mean()"),
    ("cf.dyn_on", "scanner/config.py", '"momentum_dynamic_enabled": True'),
    ("cf.base_win", "scanner/config.py", '"momentum_baseline_window": 60'),
    ("cf.seg", "scanner/config.py", '"momentum_segment_thresholds": {'),
    ("cf.min_avg_vol", "scanner/config.py", '"min_avg_vol": 300000'),
]
_cache = {}
LINES = {}
for label, rel, snip in SNIPS:
    if rel not in _cache:
        _cache[rel] = open(os.path.join(ROOT, rel), encoding="utf-8").read().splitlines()
    hits = [i + 1 for i, line in enumerate(_cache[rel]) if snip in line]
    LINES[label] = "%s:%s" % (rel.split("/")[-1], ",".join(map(str, hits)) if hits else "NOTFOUND")
RES["lines"] = LINES
items = ["%s=%s" % (k, v) for k, v in LINES.items()]
print("== LINES ==")
for i in range(0, len(items), 4):
    print("  " + " | ".join(items[i:i + 4]))

# ---------------- module loading ----------------
cfg_tree = ast.parse(open(os.path.join(ROOT, "scanner/config.py"), encoding="utf-8").read())
SETTINGS = None
for n in cfg_tree.body:
    if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == "DEFAULT_SETTINGS":
        SETTINGS = ast.literal_eval(n.value)
se = load_standalone("scanner/score_engine.py", "frm_score_engine")
ps = load_standalone("scanner/position_sizer.py", "frm_position_sizer")
ft = load_standalone("scanner/features.py", "frm_features")
ep = load_standalone("scanner/execution_policy.py", "frm_execution_policy")
G = {"pd": pd, "np": np, "math": math, "os": os, "median": median, "Any": Any,
     "logger": logging.getLogger("frm"), "SETTINGS": dict(SETTINGS)}
sg = extract("scanner/signals.py", ["safe_float", "check_volume_spike", "analyze_price_momentum",
                                    "check_trend_strength", "check_timeframe_alignment",
                                    "check_momentum_confluence"], G)
ind = extract("scanner/indicators.py", ["ema", "rsi", "macd_hist", "atr"], G)
rk = extract("scanner/risk_engine.py", ["yang_zhang_vol", "calculate_risk_management",
                                        "calculate_risk_management_yz"], G)
print("SETTINGS(default):", {k: SETTINGS.get(k) for k in (
    "vol_multiplier", "trend_gap_pct", "momentum_windows", "momentum_baseline_window",
    "momentum_z_threshold", "momentum_dynamic_enabled", "momentum_dynamic_alpha",
    "momentum_dynamic_min", "momentum_dynamic_max", "momentum_segment_thresholds")})


def mkrow(**kw):
    r = dict(regime=False, direction=False, score=0, alignment_ratio=0.0, momentum_ratio=0.0,
             volume_spike=False, price_momentum=False, trend_strength=False, vol_regime=1)
    r.update(kw)
    r["filter_score"] = int(r["volume_spike"]) + int(r["price_momentum"]) + int(r["trend_strength"])
    return r


@run("P1_composite")
def _p1():
    b0 = se.compute_recommendation_score(mkrow())
    eff = {}
    for k, kw in [("volume_spike", {"volume_spike": True}), ("price_momentum", {"price_momentum": True}),
                  ("trend_strength", {"trend_strength": True}), ("regime", {"regime": True}),
                  ("direction", {"direction": True}), ("raw_score_1pt", {"score": 1}),
                  ("alignment_1.0", {"alignment_ratio": 1.0}),
                  ("momentum_1.0_vr0", {"momentum_ratio": 1.0, "vol_regime": 0}),
                  ("momentum_1.0_vr1", {"momentum_ratio": 1.0, "vol_regime": 1}),
                  ("momentum_1.0_vr2", {"momentum_ratio": 1.0, "vol_regime": 2})]:
        d = se.compute_recommendation_score(mkrow(**kw)) - b0
        eff[k] = (round(d, 3), round(d / se.MAX_RECO_SCORE * 100, 2))
    mx = {}
    for vr in (0, 1, 2):
        r = mkrow(regime=True, direction=True, score=3, alignment_ratio=1.0, momentum_ratio=1.0,
                  volume_spike=True, price_momentum=True, trend_strength=True, vol_regime=vr)
        mx[vr] = (se.compute_recommendation_score(r), se.compute_recommendation_strength(r))
    rng = np.random.default_rng(1)
    maxdiff, ncase = 0.0, 0
    keys4 = FLAGS[:4]
    for combo in range(16):
        for j, k in enumerate(keys4):
            os.environ[k] = "1" if (combo >> j) & 1 else "0"
        for _i in range(150):
            fl = [bool(rng.integers(0, 2)) for _f in range(3)]
            r = mkrow(regime=bool(rng.integers(0, 2)), direction=bool(rng.integers(0, 2)),
                      score=int(rng.integers(0, 4)), alignment_ratio=float(rng.choice([0, 0.5, 2 / 3, 1.0])),
                      momentum_ratio=float(rng.integers(0, 7)) / 6, volume_spike=fl[0],
                      price_momentum=fl[1], trend_strength=fl[2], vol_regime=int(rng.integers(0, 3)))
            r.update(squeeze_factor=float(rng.uniform(-0.2, 1.2)), catalyst_factor=float(rng.uniform(-1.2, 1.2)),
                     lottery_factor=float(rng.uniform(0, 1.2)), overnight_gap_factor=float(rng.uniform(0, 1.2)))
            sent = None if rng.random() < 0.5 else float(rng.uniform(0, 1))
            a = se.compute_recommendation_score(r, sentiment_score=sent)
            b = se.score_component_breakdown(r, sentiment_score=sent)["total"]
            maxdiff = max(maxdiff, abs(a - b))
            ncase += 1
    for k in keys4:
        os.environ.pop(k, None)
    rnan = mkrow()
    rnan["momentum_ratio"] = float("nan")
    nan_info = {
        "strength(nan scalar)": se.compute_recommendation_strength(float("nan")),
        "strength(row momentum_ratio=nan)": se.compute_recommendation_strength(rnan),
        "legacy(atr_pct=0)": se.compute_legacy_quality_score(regime=True, direction=True, raw_score=3, atr_pct=0.0, rvol=None),
        "legacy(atr_pct=nan)": se.compute_legacy_quality_score(regime=True, direction=True, raw_score=3, atr_pct=float("nan"), rvol=None),
    }
    n = 30
    dfa = pd.DataFrame({"High": np.linspace(11, 12, n), "Low": np.linspace(9, 10, n), "Close": np.linspace(10, 11, n)})
    dfb = dfa.copy()
    dfb.loc[n - 3, "High"] = np.nan
    nan_info["atr_pct(clean)"] = ft.compute_atr_pct(dfa)
    nan_info["atr_pct(one NaN High in last 14)"] = ft.compute_atr_pct(dfb)
    leg = {
        "max_no_squeeze": se.compute_legacy_quality_score(regime=True, direction=True, raw_score=3, atr_pct=6.0, rvol=3.0,
                                                          squeeze_factor=0.0, lottery_factor=0.0, overnight_gap_factor=0.0),
        "max_squeeze": se.compute_legacy_quality_score(regime=True, direction=True, raw_score=3, atr_pct=6.0, rvol=3.0,
                                                       squeeze_factor=1.0, lottery_factor=0.0, overnight_gap_factor=0.0),
        "min": se.compute_legacy_quality_score(regime=False, direction=False, raw_score=0, atr_pct=0.0, rvol=None,
                                               squeeze_factor=0.0, lottery_factor=1.0, overnight_gap_factor=1.0),
        "entry_base(reg,dir,raw3)": se.compute_legacy_quality_score(regime=True, direction=True, raw_score=3, atr_pct=0.0, rvol=None),
    }
    RES["P1_composite"] = {"effective_weights(raw,composite_pts)": eff, "max_by_vol_regime": mx,
                           "breakdown_vs_score_maxdiff": maxdiff, "n_cases": ncase, "nan": nan_info, "legacy_range": leg}
    print("== P1 ==", json.dumps(RES["P1_composite"], default=str))


@run("P2_regime_mult")
def _p2():
    mism = []
    for bull in (True, False):
        for cs in range(0, 101):
            g = se.regime_gate_mult(bull, cs)
            r = ps._regime_scale(cs, bull)
            if abs(g - r) > 1e-12:
                mism.append((bull, cs, g, r))
    ranges = {}
    for bull, cs, g, r in mism:
        key = "%s gate=%s dyn=%s" % ("bull" if bull else "bear", g, r)
        ranges.setdefault(key, []).append(cs)
    RES["P2_regime_mult"] = {"n_mismatch_of_202": len(mism),
                             "ranges": {k: (min(v), max(v), len(v)) for k, v in ranges.items()}}
    print("== P2 ==", json.dumps(RES["P2_regime_mult"]))


@run("P4_dynamic_position")
def _p4():
    grid = [(cs, rr, vol, kf, bull) for cs in range(0, 101, 5) for rr in (2.6, 2.75, 3.33, 3.67, 4.33)
            for vol in (10.0, 20.0, 40.0, 80.0) for kf in (0.25, 0.5) for bull in (True, False)]

    def calc():
        return [ps.calculate_dynamic_position(price=50.0, stop_loss=48.0, composite_score=cs, is_bull_regime=bull,
                                              risk_reward=rr, ann_vol_pct=vol, kelly_fraction=kf)
                for (cs, rr, vol, kf, bull) in grid]
    orig = calc()
    saved = ps._regime_scale
    ps._regime_scale = lambda c, b: 1.0
    neutral = calc()
    ps._regime_scale = saved
    boost = [i for i, g in enumerate(grid) if (not g[4]) and 30 <= g[0] <= 55]
    supp = [i for i, g in enumerate(grid) if g[4] and g[0] > 62]

    def ndiff(ix):
        return sum(1 for i in ix if (orig[i]["shares"], orig[i]["risk_pct"]) != (neutral[i]["shares"], neutral[i]["risk_pct"]))
    kbind = 0
    for (cs, rr, vol, kf, bull) in grid:
        wr = ps._clamp(0.30 + (cs / 100.0) * 0.35, 0.30, 0.65)
        if ps._kelly_size(wr, max(rr, 1.0), 1.0, kf) < 0.02 * saved(cs, bull):
            kbind += 1
    RES["P4_dynamic_position"] = {"grid_n": len(grid), "boost_zone_n": len(boost), "boost_zone_changed": ndiff(boost),
                                  "suppress_zone_n": len(supp), "suppress_zone_changed": ndiff(supp),
                                  "kelly_binding_n": kbind}
    print("== P4 ==", json.dumps(RES["P4_dynamic_position"]))


@run("P5_macd_scale")
def _p5():
    rng = np.random.default_rng(7)
    path = np.exp(np.cumsum(rng.normal(0.0002, 0.004, 600)))
    out = {}
    for p0 in (2.0, 10.0, 50.0, 250.0):
        mh = ind["macd_hist"](pd.Series(p0 * path)).iloc[50:]
        out[str(p0)] = {"frac_gt_0.01": round(float((mh > 0.01).mean()), 3), "frac_gt_0": round(float((mh > 0).mean()), 3)}
    RES["P5_macd_scale"] = out
    print("== P5 ==", json.dumps(out))


@run("P6_yz_vs_atr")
def _p6():
    rng = np.random.default_rng(11)
    days, steps, sig_d, sig_on = 300, 78, 0.02, 0.005
    rows, prev = [], 50.0
    for _d in range(days):
        o = prev * math.exp(rng.normal(0, sig_on))
        p = o * np.exp(np.cumsum(rng.normal(0, sig_d / math.sqrt(steps), steps)))
        rows.append((o, max(o, p.max()), min(o, p.min()), p[-1]))
        prev = p[-1]
    df = pd.DataFrame(rows, columns=["Open", "High", "Low", "Close"])
    atr_s = ind["atr"](df)
    ratios = [float(atr_s.iloc[t] / rk["yang_zhang_vol"](df.iloc[:t + 1], window=20)) for t in range(60, days)]
    price = float(df["Close"].iloc[-1])
    tiers = {}
    for ms in (75, 60, 40):
        yz = rk["calculate_risk_management_yz"](price=price, df=df, momentum_score=ms)
        at = rk["calculate_risk_management"](price=price, atr_val=float(atr_s.iloc[-1]), momentum_score=ms)
        tiers[ms] = {"rr": yz["risk_reward_ratio"], "stop_pct_yz": yz["stop_loss_percent"],
                     "stop_pct_atr": at["stop_loss_percent"], "pos": yz["position_size"]}
    os.environ["FINPILOT_ENABLE_ALPHA_V2"] = "1"
    rr_a = {ms: rk["calculate_risk_management_yz"](price=price, df=df, momentum_score=ms)["risk_reward_ratio"] for ms in (75, 60, 40)}
    os.environ.pop("FINPILOT_ENABLE_ALPHA_V2", None)
    tier_rsi = {}
    for rsi_v in (30.0, 47.4, 47.5, 70.0):
        rs = max(0, min(100, (rsi_v - 30) / 70 * 100))
        tier_rsi[rsi_v] = int(rs * 0.4 + 100 * 0.3 + 100 * 0.3)
    RES["P6_yz_vs_atr"] = {"n": len(ratios), "atr_over_yz_median": round(float(np.median(ratios)), 3),
                           "p10": round(float(np.percentile(ratios, 10)), 3), "p90": round(float(np.percentile(ratios, 90)), 3),
                           "tiers": tiers, "rr_alpha_v2": rr_a, "entry_momentum_score_by_rsi(replica)": tier_rsi}
    print("== P6 ==", json.dumps(RES["P6_yz_vs_atr"]))


def mom_df(close, va):
    d = pd.DataFrame({"Close": close})
    d["vol_avg10"] = float(va)
    return d


@run("P7_momentum_z")
def _p7():
    rng = np.random.default_rng(3)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 250)))
    c[-1] = c[-2] * 1.5
    an = sg["analyze_price_momentum"](mom_df(pd.Series(c), 2e6))
    z1 = [m["zscore"] for m in an["metrics"] if m["horizon"] == 1][0]
    s = pd.Series(c).pct_change(1).dropna()
    W = int(SETTINGS["momentum_baseline_window"])
    ex = s.iloc[-(W + 1):-1]
    z_ex = float((s.iloc[-1] - ex.mean()) / ex.std(ddof=0))
    out = {"jump50pct_z_incl": round(z1, 3), "z_excl_t": round(z_ex, 2), "samuelson_bound": round(math.sqrt(W - 1), 3)}
    for seg, va in (("high", 2e6), ("mid", 6e5), ("low", 2e5)):
        pos = h1 = 0
        thr = []
        N = 400
        for _i in range(N):
            cc = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, 300)))
            a = sg["analyze_price_momentum"](mom_df(pd.Series(cc), va))
            pos += bool(a["positive"])
            thr.append(a["z_threshold_effective"])
            zz = [m["zscore"] for m in a["metrics"] if m["horizon"] == 1]
            h1 += bool(zz and zz[0] >= a["z_threshold_effective"])
        out["null_" + seg] = {"n": N, "any_horizon_rate": pos / N, "h1_only_rate": h1 / N,
                              "thr_p10_med_p90": [round(float(np.percentile(thr, q)), 3) for q in (10, 50, 90)]}
    RES["P7_momentum_z"] = out
    print("== P7 ==", json.dumps(out))


def vol_df(prev, vt, n=30):
    v = pd.Series([prev] * (n - 1) + [vt], dtype=float)
    d = pd.DataFrame({"Volume": v})
    d["vol_med20"] = v.rolling(20).median()  # replica of indicators.py vol_med20
    d["vol_avg10"] = v.rolling(10).mean()  # replica of indicators.py vol_avg10
    return d


def min_ratio(pred):
    lo, hi = 1.0, 5.0
    for _i in range(60):
        mid = (lo + hi) / 2
        if pred(mid):
            hi = mid
        else:
            lo = mid
    return round(hi, 4)


@run("P8_volume_thresholds")
def _p8():
    spike = min_ratio(lambda r: bool(sg["check_volume_spike"](vol_df(1e6, r * 1e6))))
    rawv = min_ratio(lambda r: bool(vol_df(1e6, r * 1e6).pipe(lambda d: d["Volume"].iloc[-1] > d["vol_med20"].iloc[-1] * 1.2)))
    rvf = min_ratio(lambda r: ft.compute_rvol_factor(vol_df(1e6, r * 1e6)) > 0)
    d = vol_df(1e6, spike * 1e6)
    RES["P8_volume_thresholds"] = {"spike_min_ratio_vs_prev_mean": spike, "raw_score_vol_min_ratio": rawv,
                                   "rvol_factor_min_ratio": rvf,
                                   "volume_multiple_at_spike_threshold": round(float(d["Volume"].iloc[-1] / d["vol_avg10"].iloc[-1]), 4)}
    print("== P8 ==", json.dumps(RES["P8_volume_thresholds"]))


@run("P10_conviction_cap")
def _p10():
    os.environ["FINPILOT_ENABLE_CONVICTION_TIERS"] = "1"
    cnt = {}
    for sq in (0.0, 0.5):
        for gp in (0.0, 0.2, 0.6):
            for rv in (0.0, 0.25):
                for at in (0.0, 4.0):
                    t = ft.compute_conviction(sq, gp, rv, at)
                    cnt[str(t)] = cnt.get(str(t), 0) + 1
    os.environ.pop("FINPILOT_ENABLE_CONVICTION_TIERS", None)
    cap = ep.position_cap(2_000_000.0, 1000 * 50.0)
    RES["P10_conviction_cap"] = {"conv_prob_const": ft._CONV_PROB, "tier_counts_on_grid24": cnt,
                                 "cap_example(adv=2e6,req=1000*50)": cap,
                                 "position_size_after_cap": cap["position_notional"] / 50.0,
                                 "position_size_gated_examples": {m: int(1000 * m) for m in (0.5, 0.75, 1.0, 1.3)}}
    print("== P10 ==", json.dumps(RES["P10_conviction_cap"], default=str))


def scan_text(dirs, exts, keys):
    out = {k: [] for k in keys}
    for d in dirs:
        for dp, dns, fns in os.walk(os.path.join(ROOT, d)):
            dns[:] = [x for x in dns if x not in ("node_modules", "__pycache__", ".next")]
            for fn in fns:
                if not fn.endswith(exts):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    lines = open(fp, encoding="utf-8", errors="replace").read().splitlines()
                except Exception:
                    continue
                rel = os.path.relpath(fp, ROOT).replace("\\", "/")
                for i, line in enumerate(lines, 1):
                    for k in keys:
                        if k in line:
                            out[k].append("%s:%d" % (rel, i))
    return out


@run("P11_consumers_tests")
def _p11():
    cons = scan_text(["api", "core", "distribution", "web/src"], (".py", ".ts", ".tsx"),
                     ["position_size_gated", "dyn_shares", "dyn_risk_pct", "exit_profile(", "regime_gate_mult",
                      "conviction_prob", "ranking_score", "legacy_quality_score", "risk_reward"])
    RES["consumers"] = {k: {"n": len(v), "first": v[:5]} for k, v in cons.items()}
    print("== CONSUMERS (api, core, distribution, web/src) ==")
    for k, v in cons.items():
        print("  %s n=%d %s" % (k, len(v), ", ".join(v[:4])))
    names = ["check_volume_spike", "analyze_price_momentum", "check_trend_strength", "check_timeframe_alignment",
             "check_momentum_confluence", "compute_recommendation_score", "score_component_breakdown",
             "compute_recommendation_strength", "regime_gate_mult", "compute_legacy_quality_score",
             "calculate_dynamic_position", "_regime_scale", "calculate_risk_management_yz", "yang_zhang_vol",
             "compute_lottery_factor", "compute_overnight_gap_factor", "compute_conviction", "compute_rvol_factor",
             "compute_atr_pct", "compute_vol_regime_from_df", "position_cap", "add_indicators"]
    tf = []
    for dp, dns, fns in os.walk(os.path.join(ROOT, "tests")):
        dns[:] = [x for x in dns if x != "__pycache__"]
        for fn in fns:
            if fn.endswith(".py"):
                fp = os.path.join(dp, fn)
                try:
                    tf.append((os.path.relpath(fp, ROOT).replace("\\", "/"), open(fp, encoding="utf-8", errors="replace").read()))
                except Exception:
                    pass
    tests = {}
    print("== TESTS (substring, tests/**/*.py n=%d) ==" % len(tf))
    for nm in names:
        hit = [f for f, txt in tf if nm in txt]
        tests[nm] = hit
        print("  %s: %d %s" % (nm, len(hit), ", ".join(x.replace("tests/", "") for x in hit[:4])))
    RES["tests"] = tests


@run("P12_shortlists")
def _p12():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "shortlists", "shortlist_202610*.csv")))
    COLS = ["score", "filter_score", "volume_spike", "price_momentum", "trend_strength", "regime", "direction",
            "alignment_ratio", "momentum_ratio", "ema_gap_pct", "volume_multiple", "momentum_best_zscore",
            "momentum_3d_pct", "composite_score", "legacy_quality_score", "ranking_score", "v2_score", "vol_regime",
            "lottery_factor", "overnight_gap_factor", "squeeze_factor", "rvol_daily", "gap_pct", "dist_52w_high",
            "risk_reward", "stop_loss_percent", "regime_gate_mult", "dyn_regime_scale", "entry_ok",
            "timeframe_aligned", "momentum_confluence", "conviction_prob", "momentum_z_effective"]
    meta, frames, hashes = [], [], []
    for fp in files:
        h = sha256(fp)
        hashes.append(h)
        rows = list(csv.reader(io.StringIO(open(fp, encoding="utf-8", errors="replace").read())))
        if not rows:
            meta.append({"file": os.path.basename(fp), "sha256": h, "rows": 0, "cols": 0, "bad": 0, "present": ""})
            continue
        hdr = rows[0]
        good = [r for r in rows[1:] if len(r) == len(hdr)]
        df = pd.DataFrame(good, columns=hdr)
        df = df.loc[:, ~df.columns.duplicated()]
        pres = [c for c in COLS if c in df.columns]
        meta.append({"file": os.path.basename(fp), "sha256": h, "rows": len(good), "cols": len(hdr),
                     "bad": len(rows) - 1 - len(good), "present": len(pres)})
        keep = pres + [c for c in ("symbol", "timestamp", "conviction_tier") if c in df.columns]
        sub = df[keep].copy()
        sub["_file"] = os.path.basename(fp)
        frames.append(sub)
    pd.DataFrame(meta).to_csv(os.path.join(OUT, "FRM_shortlist_schema.csv"), index=False)
    combined = hashlib.sha256("".join(hashes).encode()).hexdigest()
    print("== P12 shortlists == files=%d combined_sha256=%s" % (len(files), combined))
    sch = {}
    for m in meta:
        sch.setdefault((m["cols"], m["present"]), []).append(m["file"])
    for k, v in sch.items():
        print("  schema cols=%s present_components=%s files=%d (%s..%s) bad_rows=%d" % (
            k[0], k[1], len(v), v[0], v[-1], sum(m["bad"] for m in meta if m["file"] in v)))
    if not frames:
        return
    allf = pd.concat(frames, ignore_index=True, sort=False)
    n_raw = len(allf)
    if "symbol" in allf.columns and "timestamp" in allf.columns:
        allf = allf.drop_duplicates(subset=["symbol", "timestamp"])
    num = pd.DataFrame(index=allf.index)
    for c in COLS:
        if c in allf.columns:
            s2 = allf[c].astype(str).str.strip()
            v = pd.to_numeric(s2, errors="coerce")
            b = s2.str.lower().map({"true": 1.0, "false": 0.0})
            num[c] = v.where(v.notna(), b)
    usable = [c for c in num.columns if num[c].notna().sum() >= 30 and num[c].nunique() > 1]
    corr = num[usable].corr(method="spearman", min_periods=30)
    corr.to_csv(os.path.join(OUT, "FRM_shortlist_corr.csv"))
    print("  rows_raw=%d rows_dedup(symbol,timestamp)=%d usable_cols=%d missing=%s" % (
        n_raw, len(allf), len(usable), [c for c in COLS if c not in num.columns or c not in usable]))
    pairs = [("volume_spike", "filter_score"), ("price_momentum", "filter_score"), ("trend_strength", "filter_score"),
             ("trend_strength", "ema_gap_pct"), ("regime", "direction"), ("regime", "alignment_ratio"),
             ("direction", "alignment_ratio"), ("volume_spike", "volume_multiple"), ("volume_spike", "score"),
             ("price_momentum", "momentum_best_zscore"), ("composite_score", "legacy_quality_score"),
             ("ranking_score", "legacy_quality_score"), ("composite_score", "filter_score"),
             ("composite_score", "momentum_ratio"), ("legacy_quality_score", "lottery_factor"),
             ("legacy_quality_score", "rvol_daily"), ("alignment_ratio", "momentum_ratio"),
             ("vol_regime", "composite_score")]
    pr = {}
    for a, b in pairs:
        if a in corr.columns and b in corr.columns:
            nn = int((num[a].notna() & num[b].notna()).sum())
            pr["%s~%s" % (a, b)] = (round(float(corr.loc[a, b]), 3) if pd.notna(corr.loc[a, b]) else None, nn)
    print("  spearman(pair)=(rho,n):", json.dumps(pr))
    desc = {}
    for c in ("risk_reward", "regime_gate_mult", "dyn_regime_scale", "vol_regime", "score", "filter_score"):
        if c in num.columns:
            vc = num[c].round(2).value_counts().head(8)
            desc[c] = {"nunique": int(num[c].nunique()), "top": {str(k): int(v) for k, v in vc.items()}}
    for c in ("composite_score", "legacy_quality_score", "ranking_score"):
        if c in num.columns and num[c].notna().any():
            desc[c + "_min_max_neg"] = (float(num[c].min()), float(num[c].max()), int((num[c] < 0).sum()))
    if {"ranking_score", "legacy_quality_score"} <= set(num.columns):
        m = num["ranking_score"].notna() & num["legacy_quality_score"].notna()
        desc["ranking_eq_legacy"] = (int(((num["ranking_score"] - num["legacy_quality_score"]).abs() < 1e-6)[m].sum()), int(m.sum()))
    if {"regime", "direction"} <= set(num.columns):
        m = num["regime"].notna() & num["direction"].notna()
        desc["regime_eq_direction"] = (int((num["regime"] == num["direction"])[m].sum()), int(m.sum()))
    if {"trend_strength", "ema_gap_pct"} <= set(num.columns):
        m = num["trend_strength"].notna() & num["ema_gap_pct"].notna()
        desc["trend_eq_gap_ge_3"] = (int((num["trend_strength"] == (num["ema_gap_pct"] >= 3.0).astype(float))[m].sum()), int(m.sum()))
    fs = ["filter_score", "volume_spike", "price_momentum", "trend_strength"]
    if set(fs) <= set(num.columns):
        m = num[fs].notna().all(axis=1)
        desc["filter_eq_sum_flags"] = (int((num["filter_score"] == num[fs[1:]].sum(axis=1))[m].sum()), int(m.sum()))
    need = ["regime", "direction", "score", "filter_score", "alignment_ratio", "momentum_ratio", "volume_spike",
            "price_momentum", "trend_strength", "vol_regime", "composite_score"]
    if set(need) <= set(num.columns):
        sub = num[need].dropna()
        rec = []
        for _, r in sub.iterrows():
            row = {k: r[k] for k in need[:-1]}
            row["vol_regime"] = int(r["vol_regime"])
            rec.append(se.compute_recommendation_strength(row))
        dif = (pd.Series(rec, index=sub.index) - sub["composite_score"]).abs()
        desc["composite_recompute_exact"] = (int((dif < 0.5).sum()), int(len(sub)), float(dif.max()) if len(dif) else None)
    if "conviction_tier" in allf.columns:
        desc["conviction_tier"] = {str(k): int(v) for k, v in allf["conviction_tier"].fillna("").value_counts().head(5).items()}
    RES["P12_shortlists"] = {"files": len(files), "combined_sha256": combined, "rows_raw": n_raw,
                             "rows_dedup": len(allf), "pairs": pr, "desc": desc}
    print("  desc:", json.dumps(desc, default=str))


with open(os.path.join(OUT, "FRM_probe_results.json"), "w", encoding="utf-8") as f:
    json.dump(RES, f, indent=1, default=str)
print("DONE seconds=%.1f" % (time.time() - T0))
