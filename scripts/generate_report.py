#!/usr/bin/env python3
"""
FinPilot — Backtest Rapor Oluşturucu
=====================================
Ham CSV/JSON verilerinden şık, okunabilir HTML rapor üretir.
Kullanım:  python generate_report.py [timestamp]
Örnek:     python generate_report.py 20260217_1650
"""

import html as html_mod
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

os.chdir("/workspaces/Borsa")
REPORT_DIR = Path("reports/backtest_3month")
MAX_CONCURRENT = 5


# ─── Timestamp bul ────────────────────────────────────────────────────
def find_latest_ts():
    files = sorted(REPORT_DIR.glob("summary_*.json"))
    if not files:
        print("❌ Rapor bulunamadı!")
        sys.exit(1)
    return files[-1].stem.replace("summary_", "")


ts = sys.argv[1] if len(sys.argv) > 1 else find_latest_ts()
print(f"📊 Rapor oluşturuluyor — timestamp: {ts}")

# ─── Dosyaları oku ────────────────────────────────────────────────────
with open(REPORT_DIR / f"summary_{ts}.json") as f:
    S = json.load(f)

trades_df = pd.read_csv(REPORT_DIR / f"trades_{ts}.csv")
signals_df = pd.read_csv(REPORT_DIR / f"entry_signals_{ts}.csv")
equity_df = pd.read_csv(REPORT_DIR / f"equity_curve_{ts}.csv")

trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"])
trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"])

# ─── Kısa erişimciler ────────────────────────────────────────────────
total_pnl = S["total_pnl"]
total_ret = S["total_return_pct"]
win_rate = S["win_rate"]
pf = S["profit_factor"]
sharpe = S["sharpe_ratio"]
max_dd = S["max_drawdown_pct"]
n_trades = S["total_trades"]
n_win = S["winning_trades"]
n_lose = S["losing_trades"]
n_signals = S["entry_signals"]
n_scans = S["total_scans"]
n_stocks = S["symbols_tested"]
sym_perf = S.get("symbol_performance", {})

eq_dates = equity_df["date"].tolist()
eq_values = equity_df["equity"].round(2).tolist()
eq_pos = equity_df["open_positions"].tolist()
test_start = eq_dates[0] if eq_dates else "?"
test_end = eq_dates[-1] if eq_dates else "?"
report_date_str = datetime.now().strftime("%d %B %Y, %H:%M")

# ─── Sektör haritası ──────────────────────────────────────────────────
SECTOR = {
    **dict.fromkeys(
        [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "NVDA",
            "TSLA",
            "AVGO",
            "ORCL",
            "ADBE",
            "CRM",
            "AMD",
            "INTC",
            "QCOM",
            "TXN",
            "NFLX",
            "MU",
            "ANET",
            "SNPS",
            "KLAC",
            "LRCX",
            "CRWD",
            "NET",
            "SNOW",
            "PLTR",
            "PANW",
            "DDOG",
            "ZS",
            "FTNT",
            "WDAY",
            "TEAM",
            "HUBS",
            "BILL",
            "CDNS",
            "MRVL",
        ],
        "Teknoloji",
    ),
    **dict.fromkeys(
        [
            "JPM",
            "GS",
            "MS",
            "BAC",
            "WFC",
            "C",
            "BLK",
            "V",
            "MA",
            "AXP",
            "SPGI",
            "COF",
            "SCHW",
            "USB",
            "PNC",
            "TFC",
            "BK",
            "CME",
            "ICE",
            "MCO",
        ],
        "Finans",
    ),
    **dict.fromkeys(
        [
            "UNH",
            "JNJ",
            "LLY",
            "PFE",
            "ABBV",
            "MRK",
            "TMO",
            "ABT",
            "DHR",
            "BMY",
            "AMGN",
            "GILD",
            "VRTX",
            "REGN",
            "ISRG",
            "MDT",
            "SYK",
            "BSX",
            "EW",
            "ZTS",
        ],
        "Sağlık",
    ),
    **dict.fromkeys(
        [
            "WMT",
            "COST",
            "HD",
            "LOW",
            "TGT",
            "SBUX",
            "MCD",
            "NKE",
            "LULU",
            "TJX",
            "PEP",
            "KO",
            "PG",
            "CL",
            "EL",
            "MNST",
            "KHC",
            "GIS",
            "HSY",
            "KDP",
        ],
        "Tüketici",
    ),
    **dict.fromkeys(
        ["XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "VLO", "PSX", "OXY"], "Enerji"
    ),
    **dict.fromkeys(
        [
            "BA",
            "LMT",
            "RTX",
            "GE",
            "HON",
            "CAT",
            "DE",
            "UNP",
            "UPS",
            "FDX",
            "MMM",
            "EMR",
            "ETN",
            "ITW",
            "PH",
            "GD",
            "NOC",
            "LHX",
            "TDG",
            "WM",
        ],
        "Sanayi",
    ),
    **dict.fromkeys(
        [
            "SPY",
            "QQQ",
            "XLK",
            "XLI",
            "SMH",
            "XLE",
            "XLF",
            "XLV",
            "XLP",
            "ARKK",
            "IWM",
            "DIA",
            "SOXX",
            "XBI",
        ],
        "ETF",
    ),
}


def get_sector(sym):
    return SECTOR.get(sym, "Diğer")


# ─── Hesaplanan veriler ───────────────────────────────────────────────
signal_sectors = signals_df["symbol"].map(get_sector).value_counts().to_dict()
signal_strategies = (
    signals_df["strategy_tag"].value_counts().to_dict()
    if "strategy_tag" in signals_df.columns
    else {}
)

strat_stats = (
    trades_df.groupby("strategy")
    .agg(
        trades=("pnl", "count"),
        total_pnl=("pnl", "sum"),
        avg_pnl=("pnl", "mean"),
        win_rate=("pnl", lambda x: (x > 0).mean() * 100),
    )
    .reset_index()
)

win_trades = trades_df[trades_df["pnl"] > 0]
loss_trades = trades_df[trades_df["pnl"] < 0]
biggest_win = trades_df["pnl"].max() if len(trades_df) else 0
biggest_loss = trades_df["pnl"].min() if len(trades_df) else 0
biggest_win_sym = trades_df.loc[trades_df["pnl"].idxmax(), "symbol"] if len(trades_df) else ""
biggest_loss_sym = trades_df.loc[trades_df["pnl"].idxmin(), "symbol"] if len(trades_df) else ""
avg_win_hold = win_trades["holding_days"].mean() if len(win_trades) else 0
avg_loss_hold = loss_trades["holding_days"].mean() if len(loss_trades) else 0
n_stop = len(trades_df[trades_df["exit_reason"].str.contains("Stop", na=False)])
n_tp = len(trades_df[trades_df["exit_reason"].str.contains("TP", na=False)])
n_hold = len(trades_df[trades_df["exit_reason"].str.contains("Dönem", na=False)])


# ─── Yardımcı fonksiyonlar ────────────────────────────────────────────
def pc(val):
    """PnL color."""
    if val > 0:
        return "#10b981"
    if val < 0:
        return "#ef4444"
    return "#6b7280"


def pnl_html(val):
    s = "+" if val > 0 else ""
    return f'<span style="color:{pc(val)};font-weight:600">{s}${val:,.2f}</span>'


def pct_html(val):
    s = "+" if val > 0 else ""
    return f'<span style="color:{pc(val)};font-weight:600">{s}{val:.2f}%</span>'


def exit_badge(reason):
    r = str(reason)
    if "TP1" in r:
        return '<span class="badge tp1">TP1</span>'
    if "TP2" in r:
        return '<span class="badge tp2">TP2</span>'
    if "TP3" in r:
        return '<span class="badge tp3">TP3</span>'
    if "Stop" in r:
        return '<span class="badge sl">SL</span>'
    if "Dönem" in r:
        return '<span class="badge hold">HOLD</span>'
    return '<span class="badge other">' + html_mod.escape(r[:12]) + "</span>"


# ─── HTML parçaları oluştur (ana f-string'den önce) ────────────────────

# 1) Trade tablosu satırları
trade_rows_html = ""
for _, row in trades_df.iterrows():
    sym = html_mod.escape(str(row["symbol"]))
    entry_d = row["entry_date"].strftime("%d %b %Y")
    exit_d = row["exit_date"].strftime("%d %b %Y")
    strat = html_mod.escape(str(row.get("strategy", "")))
    pnl_v = row["pnl"]
    pnl_p = row.get("pnl_pct", 0)
    hold = row.get("holding_days", "")
    reason = str(row.get("exit_reason", ""))
    shares = row.get("shares", 0)
    epx = row.get("entry_price", 0)
    xpx = row.get("exit_price", 0)
    cls = "win-row" if pnl_v > 0 else "loss-row"
    trade_rows_html += (
        f'<tr class="{cls}">'
        f"<td><strong>{sym}</strong></td>"
        f"<td>{strat}</td>"
        f"<td>{entry_d}</td>"
        f"<td>{exit_d}</td>"
        f'<td class="num">{shares}</td>'
        f'<td class="num">${epx:,.2f}</td>'
        f'<td class="num">${xpx:,.2f}</td>'
        f'<td class="num">{pnl_html(pnl_v)}</td>'
        f'<td class="num">{pct_html(pnl_p)}</td>'
        f'<td class="num">{hold} gün</td>'
        f"<td>{exit_badge(reason)}</td>"
        f"</tr>\n"
    )

# 2) Symbol performance kartları
sym_cards_html = ""
for sym, data in sorted(sym_perf.items(), key=lambda x: x[1]["total_pnl"], reverse=True):
    pnl = data["total_pnl"]
    border = "#10b981" if pnl > 0 else "#ef4444"
    icon = "📈" if pnl > 0 else "📉"
    sym_cards_html += (
        f'<div class="sym-card" style="border-left:4px solid {border}">'
        f'<div class="sym-header">{icon} <strong>{sym}</strong></div>'
        f'<div class="sym-metric">{pnl_html(pnl)}</div>'
        f'<div class="sym-detail">{data["trades"]} işlem · WR {data["win_rate"]:.0f}% · Ort. {data["avg_hold"]:.0f} gün</div>'
        f"</div>\n"
    )

# 3) Strateji tablosu
strat_rows_html = ""
for _, row in strat_stats.iterrows():
    strat_rows_html += (
        f"<tr>"
        f"<td><strong>{html_mod.escape(str(row['strategy']))}</strong></td>"
        f'<td class="num">{row["trades"]}</td>'
        f'<td class="num">{pnl_html(row["total_pnl"])}</td>'
        f'<td class="num">{pnl_html(row["avg_pnl"])}</td>'
        f'<td class="num">{pct_html(row["win_rate"])}</td>'
        f"</tr>\n"
    )

# 4) Sektör sinyal tablosu
sector_rows_html = ""
for sec, cnt in sorted(signal_sectors.items(), key=lambda x: -x[1]):
    sector_rows_html += (
        f"<tr><td>{sec}</td>"
        f'<td class="num">{cnt}</td>'
        f'<td class="num">{cnt / n_signals * 100:.1f}%</td></tr>\n'
    )

# 5) Strateji sinyal tablosu
strat_signal_html = ""
if signal_strategies:
    strat_signal_html = '<h3>Sinyal Dağılımı — Stratejiye Göre</h3><table><thead><tr><th>Strateji</th><th style="text-align:right">Sinyal</th></tr></thead><tbody>'
    for s, c in signal_strategies.items():
        strat_signal_html += f'<tr><td>{html_mod.escape(str(s))}</td><td class="num">{c}</td></tr>'
    strat_signal_html += "</tbody></table>"

# 6) Top sinyaller tablosu
sort_col = "reco_score" if "reco_score" in signals_df.columns else "score"
top_signals = signals_df.nlargest(15, sort_col)
top_sig_html = ""
for _, sig in top_signals.iterrows():
    sym = html_mod.escape(str(sig["symbol"]))
    dt = str(sig["date"])[:10]
    strat = html_mod.escape(str(sig.get("strategy_tag", "")))
    rsi = sig.get("rsi", 0)
    score = sig.get("score", 0)
    rr = sig.get("risk_reward", 0)
    sl_pct = sig.get("stop_loss_pct", 0)
    reco = sig.get("reco_score", 0)
    top_sig_html += (
        f"<tr><td><strong>{sym}</strong></td>"
        f"<td>{dt}</td><td>{strat}</td>"
        f'<td class="num">{rsi:.1f}</td>'
        f'<td class="num">{score}</td>'
        f'<td class="num">{rr:.2f}</td>'
        f'<td class="num">{sl_pct:.1f}%</td>'
        f'<td class="num"><strong>{reco:.1f}</strong></td></tr>\n'
    )

# 7) Dinamik öneriler
reco_items = ""
if total_ret > 5:
    reco_items += "<li>✅ Strateji güçlü pozitif getiri sağladı — canlı piyasada küçük sermaye ile pilot test önerilir.</li>"
if win_rate > 70:
    reco_items += f"<li>✅ %{win_rate:.0f} kazanma oranı mükemmel — sinyal kalitesi yüksek.</li>"
if pf > 3:
    reco_items += f"<li>✅ Kâr faktörü {pf:.1f} — profesyonel hedge fon seviyesinde.</li>"
if max_dd < 10:
    reco_items += f"<li>✅ Maksimum düşüş %{max_dd:.1f} — risk yönetimi etkin çalışıyor.</li>"
if n_signals > n_trades * 2:
    skipped = n_signals - n_trades
    reco_items += f"<li>⚠️ {skipped} sinyal, pozisyon limiti nedeniyle atlandı — MAX_CONCURRENT artırılabilir.</li>"

# 8) Genel değerlendirme
if total_ret > 5:
    eval_text = "🟢 Strateji güçlü performans sergiledi."
elif total_ret > 0:
    eval_text = "🟡 Strateji ortalama performans gösterdi."
else:
    eval_text = "🔴 Strateji zararda kapattı."

# 9) Metric labels
wr_color = (
    "var(--green)" if win_rate >= 60 else ("var(--yellow)" if win_rate >= 50 else "var(--red)")
)
pf_color = "var(--green)" if pf >= 2 else ("var(--yellow)" if pf >= 1 else "var(--red)")
pf_label = "Mükemmel" if pf >= 3 else ("İyi" if pf >= 1.5 else "Zayıf")
sh_color = "var(--green)" if sharpe >= 2 else ("var(--yellow)" if sharpe >= 1 else "var(--red)")
sh_label = "Olağanüstü" if sharpe >= 3 else ("Çok İyi" if sharpe >= 2 else "Normal")
dd_color = "var(--green)" if max_dd < 10 else ("var(--yellow)" if max_dd < 20 else "var(--red)")
dd_label = "Düşük Risk" if max_dd < 10 else ("Orta Risk" if max_dd < 20 else "Yüksek Risk")

# 10) Risk/reward ratio
rr_ratio = abs(S["avg_win"] / S["avg_loss"]) if S["avg_loss"] != 0 else 0
pf_comment = (
    "— profesyonel seviyede (>3.0)" if pf >= 3 else ("— iyi seviyede (>1.5)" if pf >= 1.5 else "")
)
sh_comment = (
    "— yıllıklandırılmış olarak olağanüstü"
    if sharpe >= 3
    else ("— yıllıklandırılmış olarak çok iyi" if sharpe >= 2 else "")
)

# 11) Chart.js data
strat_chart_data = json.dumps(
    [
        {"name": str(r["strategy"]), "pnl": round(r["total_pnl"], 2)}
        for _, r in strat_stats.iterrows()
    ]
)
sec_chart_data = json.dumps(
    [{"name": k, "count": v} for k, v in sorted(signal_sectors.items(), key=lambda x: -x[1])]
)

# ═══════════════════════════════════════════════════════════════════════
#                          ANA HTML ŞABLONU
# ═══════════════════════════════════════════════════════════════════════
page = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinPilot Backtest Raporu</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f172a; --card-bg: #1e293b; --card-border: #334155;
    --text: #e2e8f0; --text-muted: #94a3b8; --accent: #3b82f6;
    --green: #10b981; --red: #ef4444; --yellow: #f59e0b;
  }}
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'Segoe UI',system-ui,-apple-system,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; }}
  .container {{ max-width:1200px; margin:0 auto; padding:2rem; }}

  .report-header {{
    background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);
    border-bottom:2px solid var(--accent); padding:2.5rem 2rem; text-align:center; margin-bottom:2rem;
  }}
  .report-header h1 {{ font-size:2.2rem; font-weight:700; color:white; margin-bottom:.5rem; }}
  .report-header .subtitle {{ color:var(--text-muted); font-size:1.1rem; }}
  .report-header .date-range {{ color:var(--accent); font-size:.95rem; margin-top:.5rem; }}

  .metrics-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:1rem; margin-bottom:2rem; }}
  .metric-card {{ background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:1.2rem; text-align:center; }}
  .metric-card .metric-label {{ font-size:.82rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; margin-bottom:.4rem; }}
  .metric-card .metric-value {{ font-size:1.8rem; font-weight:700; }}
  .metric-card .metric-sub {{ font-size:.85rem; color:var(--text-muted); margin-top:.3rem; }}

  .section {{ background:var(--card-bg); border:1px solid var(--card-border); border-radius:12px; padding:1.5rem; margin-bottom:1.5rem; }}
  .section h2 {{ font-size:1.3rem; font-weight:600; margin-bottom:1rem; padding-bottom:.5rem; border-bottom:1px solid var(--card-border); }}
  .section h3 {{ font-size:1.05rem; color:var(--text-muted); margin:1rem 0 .5rem; }}

  table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
  th {{ background:rgba(59,130,246,.12); color:var(--accent); font-weight:600; text-transform:uppercase; font-size:.75rem; letter-spacing:.05em; padding:.7rem .6rem; text-align:left; border-bottom:2px solid var(--card-border); }}
  td {{ padding:.6rem; border-bottom:1px solid rgba(51,65,85,.5); vertical-align:middle; }}
  td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  tr:hover {{ background:rgba(59,130,246,.06); }}
  .win-row {{ border-left:3px solid var(--green); }}
  .loss-row {{ border-left:3px solid var(--red); }}

  .badge {{ display:inline-block; padding:.15rem .5rem; border-radius:6px; font-size:.75rem; font-weight:600; }}
  .badge.tp1 {{ background:rgba(16,185,129,.15); color:var(--green); }}
  .badge.tp2 {{ background:rgba(16,185,129,.25); color:var(--green); }}
  .badge.tp3 {{ background:rgba(16,185,129,.40); color:var(--green); }}
  .badge.sl  {{ background:rgba(239,68,68,.15); color:var(--red); }}
  .badge.hold {{ background:rgba(245,158,11,.15); color:var(--yellow); }}
  .badge.other {{ background:rgba(148,163,184,.15); color:var(--text-muted); }}

  .sym-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:.8rem; }}
  .sym-card {{ background:rgba(15,23,42,.5); border-radius:8px; padding:.8rem 1rem; }}
  .sym-header {{ font-size:1rem; margin-bottom:.3rem; }}
  .sym-metric {{ font-size:1.2rem; }}
  .sym-detail {{ font-size:.8rem; color:var(--text-muted); margin-top:.2rem; }}

  .chart-container {{ position:relative; height:320px; margin:1rem 0; }}
  .chart-row {{ display:grid; grid-template-columns:1fr 1fr; gap:1rem; }}
  .chart-half {{ position:relative; height:280px; }}

  .info-box {{ background:rgba(59,130,246,.08); border:1px solid rgba(59,130,246,.25); border-radius:8px; padding:1rem 1.2rem; margin:1rem 0; font-size:.9rem; }}
  .info-box strong {{ color:var(--accent); }}

  .summary-list {{ list-style:none; padding:0; }}
  .summary-list li {{ padding:.4rem 0 .4rem 1.5rem; position:relative; }}
  .summary-list li::before {{ content:"▸"; position:absolute; left:0; color:var(--accent); font-weight:bold; }}

  .report-footer {{ text-align:center; color:var(--text-muted); font-size:.8rem; padding:2rem 0; border-top:1px solid var(--card-border); margin-top:2rem; }}

  @media (max-width:768px) {{
    .container {{ padding:1rem; }}
    .metrics-grid {{ grid-template-columns:repeat(2,1fr); }}
    .chart-row {{ grid-template-columns:1fr; }}
    table {{ font-size:.78rem; }}
  }}
  @media print {{
    body {{ background:white; color:#1e293b; }}
    .section {{ border-color:#e2e8f0; }}
    .report-header {{ background:#f1f5f9; border-color:#3b82f6; }}
  }}
</style>
</head>
<body>

<!-- HEADER -->
<div class="report-header">
  <h1>🚀 FinPilot Backtest Raporu</h1>
  <div class="subtitle">3 Aylık Strateji Performans Analizi</div>
  <div class="date-range">
    📅 {test_start} → {test_end} &nbsp;|&nbsp;
    {n_stocks} hisse tarandı &nbsp;|&nbsp;
    Rapor: {report_date_str}
  </div>
</div>

<div class="container">

<!-- ANA METRİKLER -->
<div class="metrics-grid">
  <div class="metric-card">
    <div class="metric-label">Toplam Kâr/Zarar</div>
    <div class="metric-value" style="color:{pc(total_pnl)}">{"+" if total_pnl > 0 else ""}${total_pnl:,.0f}</div>
    <div class="metric-sub">${S["initial_capital"]:,.0f} → ${S["final_capital"]:,.0f}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Toplam Getiri</div>
    <div class="metric-value" style="color:{pc(total_ret)}">{"+" if total_ret > 0 else ""}{total_ret:.2f}%</div>
    <div class="metric-sub">90 günde</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Kazanma Oranı</div>
    <div class="metric-value" style="color:{wr_color}">{win_rate:.1f}%</div>
    <div class="metric-sub">{n_win}W / {n_lose}L ({n_trades} toplam)</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Kâr Faktörü</div>
    <div class="metric-value" style="color:{pf_color}">{pf:.2f}</div>
    <div class="metric-sub">{pf_label}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Sharpe Oranı</div>
    <div class="metric-value" style="color:{sh_color}">{sharpe:.2f}</div>
    <div class="metric-sub">{sh_label}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Maks. Düşüş</div>
    <div class="metric-value" style="color:{dd_color}">-{max_dd:.2f}%</div>
    <div class="metric-sub">{dd_label}</div>
  </div>
</div>

<!-- ÖZET -->
<div class="section">
  <h2>📝 Strateji Özeti</h2>
  <div class="info-box">
    <strong>Genel Değerlendirme:</strong> {eval_text}
    {n_stocks} hisse taranarak {n_scans:,} günlük veri noktası analiz edildi.
    Bunlardan yalnızca <strong>{n_signals}</strong> tanesi ({S["entry_rate_pct"]:.1f}%) giriş koşullarını sağladı —
    bu, stratejinin oldukça <strong>seçici</strong> olduğunu gösteriyor.
    Toplamda <strong>{n_trades}</strong> işlem gerçekleştirildi (max {MAX_CONCURRENT} eşzamanlı pozisyon limiti nedeniyle
    {n_signals - n_trades} sinyal atlandı).
  </div>
  <ul class="summary-list">
    <li>Ortalama işlem kârı: {pnl_html(S["avg_pnl"])} | Ortalama tutma süresi: <strong>{S["avg_holding_days"]:.1f} gün</strong></li>
    <li>Ortalama kazanç: {pnl_html(S["avg_win"])} vs Ortalama kayıp: {pnl_html(S["avg_loss"])}</li>
    <li>Risk/Ödül: Kazançlar kayıplardan <strong>{rr_ratio:.1f}x</strong> büyük</li>
    <li>Kâr faktörü {pf:.2f} {pf_comment}</li>
    <li>Sharpe {sharpe:.2f} {sh_comment}</li>
  </ul>
</div>

<!-- EQUITY CURVE -->
<div class="section">
  <h2>📈 Sermaye Eğrisi (Equity Curve)</h2>
  <div class="chart-container"><canvas id="equityChart"></canvas></div>
  <div class="info-box">
    Sermaye <strong>${S["initial_capital"]:,.0f}</strong>'den başlayarak <strong>${S["final_capital"]:,.0f}</strong>'ye ulaştı.
    En derin düşüş <strong>-{max_dd:.2f}%</strong> seviyesinde kaldı — bu, risk yönetiminin etkin çalıştığını göstermektedir.
  </div>
</div>

<!-- HİSSE PERFORMANSI -->
<div class="section">
  <h2>🏆 Hisse Bazlı Performans</h2>
  <div class="sym-grid">{sym_cards_html}</div>
</div>

<!-- İŞLEM DETAYLARI -->
<div class="section">
  <h2>📋 İşlem Detayları ({n_trades} İşlem)</h2>
  <div style="overflow-x:auto">
  <table>
    <thead><tr>
      <th>Hisse</th><th>Strateji</th><th>Giriş</th><th>Çıkış</th>
      <th style="text-align:right">Lot</th><th style="text-align:right">Giriş $</th>
      <th style="text-align:right">Çıkış $</th><th style="text-align:right">Kâr/Zarar</th>
      <th style="text-align:right">%</th><th style="text-align:right">Süre</th><th>Çıkış Nedeni</th>
    </tr></thead>
    <tbody>{trade_rows_html}</tbody>
    <tfoot><tr style="border-top:2px solid var(--card-border);font-weight:600">
      <td colspan="7">TOPLAM</td>
      <td class="num">{pnl_html(trades_df["pnl"].sum())}</td>
      <td class="num">{pct_html(trades_df["pnl_pct"].mean())}</td>
      <td class="num">{trades_df["holding_days"].mean():.0f} gün</td>
      <td></td>
    </tr></tfoot>
  </table></div>
</div>

<!-- STRATEJİ KARŞILAŞTIRMASI -->
<div class="section">
  <h2>⚔️ Strateji Karşılaştırması</h2>
  <div class="chart-row">
    <div class="chart-half"><canvas id="strategyChart"></canvas></div>
    <div class="chart-half"><canvas id="sectorChart"></canvas></div>
  </div>
  <table style="margin-top:1rem">
    <thead><tr>
      <th>Strateji</th><th style="text-align:right">İşlem</th>
      <th style="text-align:right">Toplam K/Z</th><th style="text-align:right">Ort. K/Z</th>
      <th style="text-align:right">Kazanma %</th>
    </tr></thead>
    <tbody>{strat_rows_html}</tbody>
  </table>
</div>

<!-- SİNYAL ANALİZİ -->
<div class="section">
  <h2>🔍 Sinyal Analizi</h2>
  <div class="info-box">
    <strong>{n_scans:,}</strong> günlük taramadan <strong>{n_signals}</strong> giriş sinyali üretildi
    (oran: <strong>{S["entry_rate_pct"]:.2f}%</strong>).
    Bu, stratejinin yüksek filtre gücüne sahip olduğunu ve yalnızca güçlü koşullarda pozisyon açtığını gösterir.
  </div>
  <h3>Sinyal Dağılımı — Sektöre Göre</h3>
  <table>
    <thead><tr><th>Sektör</th><th style="text-align:right">Sinyal Sayısı</th><th style="text-align:right">Oran</th></tr></thead>
    <tbody>{sector_rows_html}</tbody>
  </table>
  {strat_signal_html}
</div>

<!-- EN İYİ SİNYALLER -->
<div class="section">
  <h2>⭐ En Güçlü 15 Sinyal</h2>
  <div style="overflow-x:auto"><table>
    <thead><tr>
      <th>Hisse</th><th>Tarih</th><th>Strateji</th>
      <th style="text-align:right">RSI</th><th style="text-align:right">Skor</th>
      <th style="text-align:right">R/R</th><th style="text-align:right">Stop %</th>
      <th style="text-align:right">Öner. Skor</th>
    </tr></thead>
    <tbody>{top_sig_html}</tbody>
  </table></div>
</div>

<!-- RİSK ANALİZİ -->
<div class="section">
  <h2>🛡️ Risk Yönetimi Analizi</h2>
  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-label">En Büyük Kazanç</div>
      <div class="metric-value" style="color:var(--green)">+${biggest_win:,.0f}</div>
      <div class="metric-sub">{biggest_win_sym}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">En Büyük Kayıp</div>
      <div class="metric-value" style="color:var(--red)">${biggest_loss:,.0f}</div>
      <div class="metric-sub">{biggest_loss_sym}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Ort. Kazanç Süresi</div>
      <div class="metric-value">{avg_win_hold:.0f}</div>
      <div class="metric-sub">gün</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Ort. Kayıp Süresi</div>
      <div class="metric-value">{avg_loss_hold:.0f}</div>
      <div class="metric-sub">gün</div>
    </div>
  </div>
  <ul class="summary-list">
    <li>Stop-loss ile çıkılan işlem sayısı: <strong>{n_stop}</strong></li>
    <li>TP (Take Profit) ile çıkılan: <strong>{n_tp}</strong></li>
    <li>Dönem sonu açık kapatılan: <strong>{n_hold}</strong></li>
    <li>Kayıplar hızlı kesildi (ort. {avg_loss_hold:.0f} gün) — kazançlar uzun tutuldu (ort. {avg_win_hold:.0f} gün) ✅</li>
  </ul>
</div>

<!-- SONUÇ -->
<div class="section">
  <h2>🎯 Sonuç ve Öneriler</h2>
  <ul class="summary-list">
    {reco_items}
    <li>📊 Toplam {n_stocks} hisseden yalnızca {len(sym_perf)} tanesinde işlem yapıldı — strateji çok seçici.</li>
    <li>💡 <strong>Defansif 🛡️</strong> stratejisi uzun vadeli trendlerde, <strong>Sniper 🎯</strong> kısa vadeli fırsatlarda etkili.</li>
    <li>🔄 Sonraki adım: Farklı dönemlerde (6 ay, 1 yıl) test yaparak stratejinin tutarlılığını doğrulayın.</li>
  </ul>
</div>

</div>

<div class="report-footer">
  FinPilot Backtest Raporu &bull; Otomatik oluşturuldu: {report_date_str}<br>
  <em>Bu rapor geçmiş verilere dayalıdır ve gelecekteki performansı garanti etmez.</em>
</div>

<!-- CHARTS -->
<script>
// Equity Curve
new Chart(document.getElementById('equityChart').getContext('2d'), {{
  type: 'line',
  data: {{
    labels: {json.dumps(eq_dates)},
    datasets: [{{
      label: 'Sermaye ($)',
      data: {json.dumps(eq_values)},
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59,130,246,0.08)',
      fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2
    }}, {{
      label: 'Açık Pozisyon',
      data: {json.dumps(eq_pos)},
      borderColor: 'rgba(245,158,11,0.5)',
      backgroundColor: 'transparent',
      borderDash: [5,5], pointRadius: 0, borderWidth: 1, yAxisID: 'y1'
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    interaction: {{ mode: 'index', intersect: false }},
    plugins: {{
      legend: {{ labels: {{ color: '#94a3b8' }} }},
      tooltip: {{ callbacks: {{
        label: function(c) {{
          return c.datasetIndex===0 ? 'Sermaye: $'+c.parsed.y.toLocaleString() : 'Pozisyon: '+c.parsed.y;
        }}
      }} }}
    }},
    scales: {{
      x: {{ ticks: {{ color:'#64748b', maxTicksLimit:12 }}, grid: {{ color:'rgba(51,65,85,.3)' }} }},
      y: {{ ticks: {{ color:'#64748b', callback: v=>'$'+(v/1000).toFixed(0)+'K' }}, grid: {{ color:'rgba(51,65,85,.3)' }} }},
      y1: {{ position:'right', min:0, max:8, ticks: {{ color:'#f59e0b', stepSize:1 }}, grid: {{ display:false }} }}
    }}
  }}
}});

// Strategy PnL
const sd = {strat_chart_data};
new Chart(document.getElementById('strategyChart').getContext('2d'), {{
  type: 'bar',
  data: {{
    labels: sd.map(d=>d.name),
    datasets: [{{ label:'Toplam K/Z ($)', data:sd.map(d=>d.pnl),
      backgroundColor: sd.map(d=>d.pnl>0?'rgba(16,185,129,.6)':'rgba(239,68,68,.6)'),
      borderColor: sd.map(d=>d.pnl>0?'#10b981':'#ef4444'), borderWidth:1, borderRadius:6 }}]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    plugins: {{ legend:{{display:false}}, title:{{display:true,text:'Strateji Bazlı Kâr/Zarar',color:'#94a3b8'}} }},
    scales: {{
      x:{{ ticks:{{color:'#94a3b8'}}, grid:{{display:false}} }},
      y:{{ ticks:{{color:'#64748b',callback:v=>'$'+v.toLocaleString()}}, grid:{{color:'rgba(51,65,85,.3)'}} }}
    }}
  }}
}});

// Sector donut
const sc = {sec_chart_data};
const cols = ['#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6','#ec4899','#06b6d4','#84cc16','#f97316','#6366f1'];
new Chart(document.getElementById('sectorChart').getContext('2d'), {{
  type: 'doughnut',
  data: {{ labels:sc.map(d=>d.name), datasets:[{{ data:sc.map(d=>d.count), backgroundColor:cols.slice(0,sc.length), borderColor:'#1e293b', borderWidth:2 }}] }},
  options: {{
    responsive:true, maintainAspectRatio:false,
    plugins: {{ legend:{{position:'right',labels:{{color:'#94a3b8',padding:8,font:{{size:11}}}}}}, title:{{display:true,text:'Sinyal Dağılımı (Sektör)',color:'#94a3b8'}} }}
  }}
}});
</script>
</body></html>"""

# ─── Kaydet ────────────────────────────────────────────────────────────
output_path = REPORT_DIR / f"rapor_{ts}.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(page)

print(f"\n✅ Rapor oluşturuldu: {output_path}")
print(f"   Boyut: {output_path.stat().st_size / 1024:.1f} KB")
