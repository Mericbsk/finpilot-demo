#!/usr/bin/env python3
"""
ASAMA 1 — Skor Agirlik Yeniden Fit + Ablasyon + Squeeze Reweight
=================================================================
enriched_signals_v2.csv uzerinde calisir (short/float + ATR/gap/RVOL + sonuclar).
Amac: FinPilot skorunu iyilestirmek icin KANITA DAYALI agirliklar bulmak.

Testler:
  T1  Tek-degisken lift (recap)
  T2  Cok-degiskenli agirlik fit'i (IS 2025'te fit -> OOS 2026'da dogrula)  [overfitting korumali]
  T2b Yeni kompozit skor vs ESKI finpilot 'score': OOS lift + AUC karsilastirmasi
  T3  Squeeze reweight: short-only / 50-50 / short-agir (70-30) hangisi iyi
  Cikti: onerilen entegre agirliklar (score_engine.py icin)

Kullanim:  python score_lab_1_weights.py
(Tum ciktiyi Claude'a yapistir.)
"""

import csv
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
CSVP = os.path.join(ROOT, "data", "backtest_out", "enriched_signals_v2.csv")
IS_END = "2026-01-01"

try:
    import numpy as np
except ImportError:
    raise SystemExit("pip install numpy")
HAVE_SK = False
try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score

    HAVE_SK = True
except Exception:
    pass


def ff(x):
    try:
        return float(x)
    except:
        return None


rows = list(csv.DictReader(open(CSVP)))


def val(r, k, default):
    v = ff(r.get(k))
    return v if v is not None else default


# ---- ozellik muhendisligi ----
def feats(r):
    fl = val(r, "float_shares", None)
    float_tight = max(0.0, 1.0 - fl / 50e6) if (fl and fl > 0) else 0.0  # kod pivotu 50M
    return dict(
        short=val(r, "short_pct", 0.0),
        atr=val(r, "atr_pct", 0.0),
        gap=val(r, "gap_pct", 0.0),
        rvol=val(r, "rvol", 1.0),
        float_tight=float_tight,
        dist52=val(r, "dist_52w_high", 0.9),
        score=val(r, "score", 0.0),  # ESKI finpilot skoru
        rr=val(r, "rr", 0.0),
        regime=1.0
        if str(r.get("regime", "")).strip() in ("0", "False", "Range")
        else 0.0,  # Range=1 (pozitif yon)
    )


def y5(r):
    v = ff(r.get("resolved_pct_t5"))
    return None if v is None else (1 if v >= 5 else 0)


def y10(r):
    v = ff(r.get("resolved_pct_t5"))
    return None if v is None else (1 if v >= 10 else 0)


data = [(feats(r), y5(r), y10(r), (r.get("signal_date") or "")) for r in rows if y5(r) is not None]
N = len(data)
FKEYS = ["short", "atr", "gap", "rvol", "float_tight", "dist52", "score", "rr", "regime"]
base5 = sum(d[1] for d in data) / N
base10 = sum(d[2] for d in data) / N
print(f"n={N}  baz(>=5%)={base5*100:.1f}%  baz(>=10%)={base10*100:.1f}%")


# ---- T1: tek degisken lift (>=10% hedefi, squeeze icin en anlamli) ----
def lift_single(key, thr, ykey):
    sub = [d for d in data if d[0][key] >= thr]
    if len(sub) < 30:
        return None
    b = base10 if ykey == 2 else base5
    h = sum(d[ykey] for d in sub) / len(sub)
    return len(sub), h, h / b


print("\n=== T1: TEK-DEGISKEN (>=10% hedef) ===")
for key, thr in [
    ("short", 20),
    ("short", 15),
    ("atr", 4),
    ("atr", 6),
    ("gap", 3),
    ("rvol", 3),
    ("float_tight", 0.6),
    ("dist52", 0.9),
]:
    r = lift_single(key, thr, 2)
    if r:
        print(f"  {key}>={thr:<5} n={r[0]:>5} hit={r[1]*100:>5.1f}% lift={r[2]:.2f}")

# ---- standardize ----
X = np.array([[d[0][k] for k in FKEYS] for d in data], float)
mu = X.mean(0)
sd = X.std(0)
sd[sd == 0] = 1
Xs = (X - mu) / sd
Y5 = np.array([d[1] for d in data])
Y10 = np.array([d[2] for d in data])
dates = [d[3] for d in data]
ISmask = np.array([dt < IS_END for dt in dates])
OOSmask = ~ISmask


def fit_predict(Xtr, ytr, Xte):
    if HAVE_SK:
        m = LogisticRegression(max_iter=1000, C=1.0)
        m.fit(Xtr, ytr)
        return m.coef_[0], m.predict_proba(Xte)[:, 1]
    # fallback: lineer olasilik modeli (numpy en kucuk kareler)
    A = np.hstack([np.ones((len(Xtr), 1)), Xtr])
    coef, _, _, _ = np.linalg.lstsq(A, ytr, rcond=None)
    b = coef[0]
    w = coef[1:]
    Ate = np.hstack([np.ones((len(Xte), 1)), Xte])
    return w, Ate @ coef


def auc(y, p):
    if HAVE_SK:
        try:
            return roc_auc_score(y, p)
        except Exception:
            return float("nan")
    # manuel AUC
    order = np.argsort(p)
    y = y[order]
    pos = y.sum()
    neg = len(y) - pos
    if pos == 0 or neg == 0:
        return float("nan")
    ranks = np.arange(1, len(y) + 1)
    return (ranks[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg)


# ---- T2: cok-degiskenli agirlik (IS'te fit, coefficient tablosu) ----
for tgt, Y in [(">=10%", Y10), (">=5%", Y5)]:
    w_is, _ = fit_predict(Xs[ISmask], Y[ISmask], Xs[OOSmask])
    print(f"\n=== T2: COK-DEGISKENLI AGIRLIK ({tgt}, IS 2025'te fit) ===")
    order = np.argsort(-np.abs(w_is))
    for i in order:
        sign = "+" if w_is[i] >= 0 else "-"
        print(f"  {FKEYS[i]:12s} katsayi={w_is[i]:+.3f}  {sign}")
    # T2b: OOS performans — yeni model vs eski score
    _, p_oos = fit_predict(Xs[ISmask], Y[ISmask], Xs[OOSmask])
    yoos = Y[OOSmask]
    bO = yoos.mean()
    # yeni: top-quintile
    thr = np.quantile(p_oos, 0.8)
    topN = yoos[p_oos >= thr]
    new_lift = (topN.mean() / bO) if bO > 0 and len(topN) else float("nan")
    new_auc = auc(yoos, p_oos)
    # eski score: top-quintile by raw score
    sc_oos = X[OOSmask][:, FKEYS.index("score")]
    sthr = np.quantile(sc_oos, 0.8)
    old_top = yoos[sc_oos >= sthr]
    old_lift = (old_top.mean() / bO) if bO > 0 and len(old_top) else float("nan")
    old_auc = auc(yoos, sc_oos.astype(float))
    print(f"  --- T2b OOS 2026 ({tgt}, baz {bO*100:.1f}%) ---")
    print(f"    YENI kompozit: top-20% lift={new_lift:.2f}  AUC={new_auc:.3f}  (n_top={len(topN)})")
    print(f"    ESKI 'score' : top-20% lift={old_lift:.2f}  AUC={old_auc:.3f}")

# ---- T3: squeeze reweight (short vs float) ----
print(f"\n=== T3: SQUEEZE REWEIGHT (>=10% hedef, baz %{base10 * 100:.1f}) ===")


def squeeze_variant(ws, wf):
    # short_comp = min(1, short/20), float_comp = float_tight (zaten 0-1)
    scores = []
    for d in data:
        sc = min(1.0, d[0]["short"] / 20.0)
        fc = d[0]["float_tight"]
        scores.append(ws * sc + wf * fc)
    scores = np.array(scores)
    thr = np.quantile(scores, 0.9)  # en yuksek %10 squeeze
    sub = Y10[scores >= thr]
    return len(sub), sub.mean(), sub.mean() / base10


for name, ws, wf in [
    ("short-only (1.0/0.0)", 1.0, 0.0),
    ("mevcut 50/50", 0.5, 0.5),
    ("short-agir 70/30", 0.7, 0.3),
    ("short-agir 80/20", 0.8, 0.2),
]:
    n, h, l = squeeze_variant(ws, wf)
    print(f"  {name:22s} en-yuksek%10: n={n:>4} hit={h*100:>5.1f}% lift={l:.2f}")

# ---- onerilen entegre agirliklar (T2 >=10% katsayilarindan normalize) ----
w_is, _ = fit_predict(Xs[ISmask], Y10[ISmask], Xs[OOSmask])
pos = np.clip(w_is, 0, None)
norm = 10 * pos / pos.max() if pos.max() > 0 else pos
print("\n=== ONERILEN ENTEGRE AGIRLIK (0-10, >=10% edge'ine gore) ===")
for i in np.argsort(-norm):
    if norm[i] > 0.3:
        print(f"  {FKEYS[i]:12s} -> {norm[i]:.1f}")
print("\nNot: negatif/sifir katsayili ozellikler (score, dist52 vb.) skoru dusurmeli/cikarilmali.")
print("Bu ciktinin TAMAMINI Claude'a yapistir.")
