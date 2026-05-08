"""
FinPilot — Geçmiş Performans Analizi
=====================================
Tüm shortlist CSV'lerdeki sinyallerin gerçekleşen fiyatlarla karşılaştırılarak
win rate, ortalama kazanç/kayıp ve beklenen değerin hesaplanması.

Mantık:
  Her sinyal için (sembol, giriş fiyatı, SL, TP, tarih):
    - Sonraki taramalardaki fiyatlar takip edilir
    - TP fiyatına ulaşılırsa → WIN
    - SL fiyatına düşülürse → LOSS
    - 60 gün içinde ne TP ne SL → EXPIRED (son fiyatla hesaplanır)
"""

import glob
import os
from datetime import datetime, timedelta

import pandas as pd

# ─────────────────────────────────────────────
# 1. TÜM VERİYİ YÜKLEAbu
# ─────────────────────────────────────────────

BORSA = "/sessions/kind-jolly-galileo/mnt/Borsa"
SHORTLIST_DIR = f"{BORSA}/data/shortlists"
HOLDING_DAYS = 60   # sinyal için maksimum bekleme süresi


def load_all_shortlists() -> pd.DataFrame:
    files = sorted(glob.glob(f"{SHORTLIST_DIR}/*.csv"))
    dfs = []
    for f in files:
        try:
            df = pd.read_csv(f)
            if "stop_loss" not in df.columns or "take_profit" not in df.columns:
                continue
            df["_file"] = os.path.basename(f)
            dfs.append(df)
        except Exception:
            pass
    if not dfs:
        raise RuntimeError("Hiç CSV yüklenemedi!")
    all_df = pd.concat(dfs, ignore_index=True)
    # Timestamp parse
    all_df["ts"] = pd.to_datetime(all_df["timestamp"], errors="coerce")
    all_df = all_df.dropna(subset=["ts", "symbol", "price", "stop_loss", "take_profit"])
    # Numerics
    for col in ["price", "stop_loss", "take_profit", "score", "filter_score",
                "alignment_ratio", "momentum_ratio"]:
        if col in all_df.columns:
            all_df[col] = pd.to_numeric(all_df[col], errors="coerce")
    return all_df.sort_values("ts").reset_index(drop=True)


# ─────────────────────────────────────────────
# 2. SİNYAL TANIMLAMA
# ─────────────────────────────────────────────

def extract_signals(df: pd.DataFrame, mode: str = "all") -> pd.DataFrame:
    """
    mode:
      'all'       → tüm shortlist satırları (tekrarlar birleştirilir)
      'entry_ok'  → yalnızca entry_ok=True sinyaller
      'strategy_b'→ Strateji B parametreleri
      'strategy_a'→ Strateji A (daha sıkı)
    """
    if mode == "entry_ok":
        mask = df["entry_ok"] == True
    elif mode == "strategy_b":
        mask = (
            (df.get("alignment_ratio", 0) >= 0.67) &
            (df.get("momentum_ratio", 0) >= 0.40) &
            (df.get("filter_score", 0) >= 1) &
            (df.get("score", 0) >= 2)
        )
    elif mode == "strategy_a":
        mask = (
            (df.get("alignment_ratio", 0) >= 0.75) &
            (df.get("momentum_ratio", 0) >= 0.60) &
            (df.get("filter_score", 0) >= 2) &
            (df.get("score", 0) >= 3)
        )
    else:
        # 'all': tüm entry_ok=True VEYA filter_score>=1
        if "entry_ok" in df.columns:
            mask = (df["entry_ok"] == True) | (df.get("filter_score", 0) >= 1)
        else:
            mask = df.get("filter_score", 0) >= 1

    subset = df[mask].copy()

    # Her sembol için tarihe göre ilk sinyali al (aynı gün tekrarı önle)
    subset["date"] = subset["ts"].dt.date
    subset = subset.sort_values("ts").drop_duplicates(subset=["symbol", "date"], keep="first")
    return subset.reset_index(drop=True)


# ─────────────────────────────────────────────
# 3. SONUÇLARI HESAPLA
# ─────────────────────────────────────────────

def determine_outcomes(signals: pd.DataFrame, all_df: pd.DataFrame) -> pd.DataFrame:
    """
    Her sinyal için, sinyal tarihinden sonraki gözlemlere bakarak
    WIN / LOSS / EXPIRED sonucunu belirler.
    """
    # Performans için: sembol bazında tüm fiyat serisini hazırla
    price_by_symbol = {}
    for sym, grp in all_df.groupby("symbol"):
        price_by_symbol[sym] = grp[["ts", "price"]].sort_values("ts")

    records = []
    for _, sig in signals.iterrows():
        sym = sig["symbol"]
        entry_price = sig["price"]
        sl = sig["stop_loss"]
        tp = sig["take_profit"]
        sig_ts = sig["ts"]
        cutoff = sig_ts + timedelta(days=HOLDING_DAYS)

        outcome = "OPEN"
        exit_price = entry_price
        days_to_exit = None

        if sym in price_by_symbol:
            future = price_by_symbol[sym]
            future = future[(future["ts"] > sig_ts) & (future["ts"] <= cutoff)]

            for _, obs in future.iterrows():
                obs_price = obs["price"]
                # TP kontrolü
                if obs_price >= tp:
                    outcome = "WIN"
                    exit_price = tp
                    days_to_exit = (obs["ts"] - sig_ts).days
                    break
                # SL kontrolü
                if obs_price <= sl:
                    outcome = "LOSS"
                    exit_price = sl
                    days_to_exit = (obs["ts"] - sig_ts).days
                    break

            if outcome == "OPEN":
                # Süre dolmuş ve ne TP ne SL → son gözlemlenen fiyat
                if len(future) > 0:
                    last_price = future.iloc[-1]["price"]
                    last_ts = future.iloc[-1]["ts"]
                    if last_ts >= cutoff - timedelta(days=5):  # yeterince ilerlemiş
                        outcome = "EXPIRED"
                        exit_price = last_price
                        days_to_exit = (last_ts - sig_ts).days

        if entry_price > 0:
            pnl_pct = (exit_price - entry_price) / entry_price * 100
        else:
            pnl_pct = 0.0

        records.append({
            "symbol": sym,
            "entry_ts": sig_ts,
            "entry_price": entry_price,
            "stop_loss": sl,
            "take_profit": tp,
            "outcome": outcome,
            "exit_price": exit_price,
            "pnl_pct": round(pnl_pct, 2),
            "days_to_exit": days_to_exit,
            "risk_reward": sig.get("risk_reward", None),
            "filter_score": sig.get("filter_score", None),
            "alignment_ratio": sig.get("alignment_ratio", None),
            "momentum_ratio": sig.get("momentum_ratio", None),
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# 4. İSTATİSTİKLER
# ─────────────────────────────────────────────

def compute_stats(outcomes: pd.DataFrame, label: str) -> dict:
    resolved = outcomes[outcomes["outcome"].isin(["WIN", "LOSS", "EXPIRED"])]
    wins = resolved[resolved["outcome"] == "WIN"]
    losses = resolved[resolved["outcome"].isin(["LOSS", "EXPIRED"])]
    losses_strict = resolved[resolved["outcome"] == "LOSS"]

    total = len(resolved)
    n_win = len(wins)
    n_loss = len(losses_strict)
    n_expired = len(resolved[resolved["outcome"] == "EXPIRED"])
    n_open = len(outcomes[outcomes["outcome"] == "OPEN"])

    win_rate = n_win / total * 100 if total > 0 else 0
    avg_gain = wins["pnl_pct"].mean() if len(wins) > 0 else 0
    avg_loss_all = losses["pnl_pct"].mean() if len(losses) > 0 else 0
    avg_loss_strict = losses_strict["pnl_pct"].mean() if len(losses_strict) > 0 else 0

    # Beklenen değer (tüm resolved sinyaller üzerinden)
    expected_value = resolved["pnl_pct"].mean() if total > 0 else 0

    # Profit factor
    gross_profit = wins["pnl_pct"].sum()
    gross_loss = abs(losses["pnl_pct"].sum()) if len(losses) > 0 else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    avg_days = resolved["days_to_exit"].dropna().mean() if total > 0 else 0

    return {
        "label": label,
        "total_signals": len(outcomes),
        "resolved": total,
        "wins": n_win,
        "losses_strict": n_loss,
        "expired": n_expired,
        "open": n_open,
        "win_rate_pct": round(win_rate, 1),
        "avg_gain_pct": round(avg_gain, 2),
        "avg_loss_all_pct": round(avg_loss_all, 2),
        "avg_loss_strict_pct": round(avg_loss_strict, 2),
        "expected_value_pct": round(expected_value, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_days_held": round(avg_days, 1),
    }


def print_stats(s: dict):
    print(f"\n{'='*55}")
    print(f"  {s['label']}")
    print(f"{'='*55}")
    print(f"  Toplam sinyal       : {s['total_signals']:>6}")
    print(f"  Sonuçlananlar       : {s['resolved']:>6}  (open: {s['open']})")
    print(f"  ✅ Kazanan (TP hit) : {s['wins']:>6}")
    print(f"  ❌ Kaybeden (SL hit): {s['losses_strict']:>6}")
    print(f"  ⏰ Süresi dolan     : {s['expired']:>6}")
    print(f"  ─────────────────────────────────")
    print(f"  📊 Win Rate         : {s['win_rate_pct']:>5.1f}%")
    print(f"  📈 Ort. Kazanç      : {s['avg_gain_pct']:>+6.2f}%")
    print(f"  📉 Ort. Kayıp (SL)  : {s['avg_loss_strict_pct']:>+6.2f}%")
    print(f"  📉 Ort. Kayıp (hep) : {s['avg_loss_all_pct']:>+6.2f}%")
    print(f"  💰 Beklenen Değer   : {s['expected_value_pct']:>+6.2f}%")
    print(f"  ⚖️  Profit Factor    : {s['profit_factor']:>6.2f}x")
    print(f"  📅 Ort. Tutma Günü  : {s['avg_days_held']:>6.1f}")


# ─────────────────────────────────────────────
# 5. ZAMAN SERİSİ ANALİZİ
# ─────────────────────────────────────────────

def monthly_performance(outcomes: pd.DataFrame) -> pd.DataFrame:
    resolved = outcomes[outcomes["outcome"].isin(["WIN", "LOSS", "EXPIRED"])].copy()
    resolved["month"] = resolved["entry_ts"].dt.to_period("M")
    monthly = resolved.groupby("month").agg(
        signals=("symbol", "count"),
        wins=("outcome", lambda x: (x == "WIN").sum()),
        avg_pnl=("pnl_pct", "mean"),
    ).reset_index()
    monthly["win_rate"] = (monthly["wins"] / monthly["signals"] * 100).round(1)
    monthly["avg_pnl"] = monthly["avg_pnl"].round(2)
    return monthly


# ─────────────────────────────────────────────
# 6. EN İYİ / EN KÖTÜ SEMBOLLER
# ─────────────────────────────────────────────

def top_bottom_symbols(outcomes: pd.DataFrame, n: int = 10):
    resolved = outcomes[outcomes["outcome"].isin(["WIN", "LOSS", "EXPIRED"])]
    sym_stats = resolved.groupby("symbol").agg(
        trades=("pnl_pct", "count"),
        avg_pnl=("pnl_pct", "mean"),
        wins=("outcome", lambda x: (x == "WIN").sum()),
    ).reset_index()
    sym_stats["win_rate"] = (sym_stats["wins"] / sym_stats["trades"] * 100).round(1)
    sym_stats["avg_pnl"] = sym_stats["avg_pnl"].round(2)
    sym_stats = sym_stats[sym_stats["trades"] >= 2]  # en az 2 işlem
    top = sym_stats.nlargest(n, "avg_pnl")
    bottom = sym_stats.nsmallest(n, "avg_pnl")
    return top, bottom


# ─────────────────────────────────────────────
# 7. KAPSAMLI RAPOR
# ─────────────────────────────────────────────

def run_full_analysis():
    print("\n📊 FinPilot — Geçmiş Performans Analizi")
    print(f"   Holding süresi: {HOLDING_DAYS} gün\n")

    print("⏳ Veriler yükleniyor...")
    all_df = load_all_shortlists()
    print(f"   {len(all_df):,} satır, {all_df['symbol'].nunique():,} sembol yüklendi.")
    print(f"   Tarih aralığı: {all_df['ts'].min().date()} → {all_df['ts'].max().date()}")

    results_by_mode = {}
    modes = [
        ("Tüm Sinyaller (filter_score≥1)", "all"),
        ("entry_ok=True Sinyaller", "entry_ok"),
        ("Strateji B", "strategy_b"),
        ("Strateji A (Sıkı)", "strategy_a"),
    ]

    for label, mode in modes:
        print(f"\n⏳ {label} analiz ediliyor...")
        sigs = extract_signals(all_df, mode)
        print(f"   {len(sigs)} benzersiz sinyal")
        if len(sigs) == 0:
            continue
        outcomes = determine_outcomes(sigs, all_df)
        stats = compute_stats(outcomes, label)
        results_by_mode[mode] = (outcomes, stats)
        print_stats(stats)

    # ── Karşılaştırma tablosu ──
    print(f"\n\n{'='*75}")
    print("  STRATEJİ KARŞILAŞTIRMA TABLOSU")
    print(f"{'='*75}")
    print(f"  {'Strateji':<25} {'Sinyal':>7} {'Win%':>7} {'Kazanç':>8} {'Kayıp':>8} {'BeklDeğ':>8} {'PF':>6}")
    print(f"  {'-'*25} {'-'*7} {'-'*7} {'-'*8} {'-'*8} {'-'*8} {'-'*6}")
    for label, mode in modes:
        if mode not in results_by_mode:
            continue
        _, s = results_by_mode[mode]
        print(f"  {s['label'][:25]:<25} {s['resolved']:>7} {s['win_rate_pct']:>6.1f}% "
              f"{s['avg_gain_pct']:>+7.2f}% {s['avg_loss_strict_pct']:>+7.2f}% "
              f"{s['expected_value_pct']:>+7.2f}% {s['profit_factor']:>6.2f}")

    # ── Aylık performans (Strateji B) ──
    if "strategy_b" in results_by_mode:
        b_outcomes, _ = results_by_mode["strategy_b"]
        monthly = monthly_performance(b_outcomes)
        if len(monthly) > 0:
            print(f"\n\n📅 AYLIK PERFORMANS — Strateji B")
            print(f"  {'Ay':<10} {'Sinyal':>7} {'Kazanan':>8} {'Win%':>7} {'Ort P&L':>9}")
            print(f"  {'-'*10} {'-'*7} {'-'*8} {'-'*7} {'-'*9}")
            for _, row in monthly.iterrows():
                emoji = "✅" if row["avg_pnl"] > 0 else "❌"
                print(f"  {str(row['month']):<10} {row['signals']:>7} {row['wins']:>8} "
                      f"{row['win_rate']:>6.1f}% {row['avg_pnl']:>+8.2f}%  {emoji}")

    # ── En iyi / En kötü semboller (Strateji B) ──
    if "strategy_b" in results_by_mode:
        b_outcomes, _ = results_by_mode["strategy_b"]
        top10, bottom10 = top_bottom_symbols(b_outcomes, n=8)
        print(f"\n\n🏆 EN İYİ 8 SEMBOL — Strateji B")
        print(f"  {'Sembol':<8} {'İşlem':>6} {'Win%':>7} {'Ort P&L':>9}")
        print(f"  {'-'*8} {'-'*6} {'-'*7} {'-'*9}")
        for _, row in top10.iterrows():
            print(f"  {row['symbol']:<8} {row['trades']:>6} {row['win_rate']:>6.1f}% {row['avg_pnl']:>+8.2f}%")

        print(f"\n\n💀 EN KÖTÜ 8 SEMBOL — Strateji B")
        print(f"  {'Sembol':<8} {'İşlem':>6} {'Win%':>7} {'Ort P&L':>9}")
        print(f"  {'-'*8} {'-'*6} {'-'*7} {'-'*9}")
        for _, row in bottom10.iterrows():
            print(f"  {row['symbol']:<8} {row['trades']:>6} {row['win_rate']:>6.1f}% {row['avg_pnl']:>+8.2f}%")

    # ── Risk/Reward dağılımı ──
    if "strategy_b" in results_by_mode:
        b_outcomes, _ = results_by_mode["strategy_b"]
        resolved = b_outcomes[b_outcomes["outcome"].isin(["WIN", "LOSS", "EXPIRED"])]
        if "risk_reward" in resolved.columns:
            rr_bins = [0, 1, 1.5, 2, 2.5, 3, 5, 100]
            rr_labels = ["<1x", "1-1.5x", "1.5-2x", "2-2.5x", "2.5-3x", "3-5x", ">5x"]
            resolved2 = resolved.copy()
            resolved2["rr_bin"] = pd.cut(
                pd.to_numeric(resolved2["risk_reward"], errors="coerce"),
                bins=rr_bins, labels=rr_labels
            )
            rr_stats = resolved2.groupby("rr_bin", observed=True).agg(
                count=("pnl_pct", "count"),
                win_rate=("outcome", lambda x: round((x == "WIN").mean() * 100, 1)),
                avg_pnl=("pnl_pct", lambda x: round(x.mean(), 2)),
            )
            print(f"\n\n⚖️  R/R ORANINA GÖRE PERFORMANS — Strateji B")
            print(f"  {'R/R Aralığı':<10} {'Adet':>6} {'Win%':>7} {'Ort P&L':>9}")
            print(f"  {'-'*10} {'-'*6} {'-'*7} {'-'*9}")
            for rr_bin, row in rr_stats.iterrows():
                if row["count"] > 0:
                    print(f"  {str(rr_bin):<10} {int(row['count']):>6} {row['win_rate']:>6.1f}% {row['avg_pnl']:>+8.2f}%")

    print(f"\n\n{'='*55}")
    print("  ✅ Analiz tamamlandı")
    print(f"{'='*55}\n")

    return results_by_mode


if __name__ == "__main__":
    run_full_analysis()
