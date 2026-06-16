"""Write updated edge_report.html with real barrier + regime data."""

import json
from pathlib import Path

d = json.loads(Path("data/barrier_audit.json").read_text(encoding="utf-8"))
r = json.loads(Path("data/regime_cross_section.json").read_text(encoding="utf-8"))

# barrier schemas
new100 = d["schemas"]["new_100 (score>18, composite 0-100)"]
old_filter = d["schemas"]["old_filter (score 0-3, filter_score)"]
old_raw = d["schemas"]["old_raw (score 3-18, raw reco score)"]
combined = d["schemas"]["all_combined"]

bull = r["segments"]["by_regime"]["Bull"]
bear = r["segments"]["by_regime"]["Bear"]
bull_q = r["segments"]["score_quartile_by_regime"]["Bull"]
bear_q = r["segments"]["score_quartile_by_regime"]["Bear"]
overall = r["segments"]["overall"]


def pct(v):
    return f"+{v:.2f}%" if v >= 0 else f"{v:.2f}%"


def cls(v):
    return "pos" if v >= 0 else "neg"


dec = new100["deciles"]


def decile_row(d_item, highlight=False):
    wr_px = int(d_item["win_rate"] * 200)
    bar_cls = "g" if d_item["win_rate"] >= 0.45 else ("y" if d_item["win_rate"] >= 0.35 else "r")
    star = " &#11088;" if highlight else ""
    td_cls = ' class="hl2"' if highlight else ""
    return f"""  <tr{td_cls}>
    <td><strong>{d_item['decile']}</strong>{star}</td>
    <td>{int(d_item['score_min'])}&ndash;{int(d_item['score_max'])}</td>
    <td>{d_item['n']}</td>
    <td>{d_item['win_rate']*100:.1f}%</td>
    <td><div class="bar-w"><div class="bar {bar_cls}" style="width:{wr_px}px"></div></div></td>
    <td class="{cls(d_item['avg_pct'])}">{pct(d_item['avg_pct'])}</td>
    <td class="{cls(d_item['median_pct'])}">{pct(d_item['median_pct'])}</td>
  </tr>"""


# find best decile (D3 = index 2)
best_d = max(dec, key=lambda x: x["win_rate"])

decile_rows = "\n".join(
    decile_row(d_item, highlight=(d_item["decile"] == best_d["decile"])) for d_item in dec
)

html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FinPilot &mdash; Full Edge Audit v2</title>
<style>
  :root {{--bg:#0f1117;--card:#1a1d27;--border:#2a2d3e;--text:#e2e8f0;--muted:#8892a4;--accent:#6366f1;--green:#22c55e;--red:#ef4444;--yellow:#f59e0b;}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Inter',system-ui,sans-serif;padding:24px;max-width:1400px;margin:0 auto}}
  h1{{font-size:1.6rem;font-weight:800;margin-bottom:4px}}
  .subtitle{{color:var(--muted);font-size:.875rem;margin-bottom:28px}}
  .section{{margin-bottom:32px}}
  .section-title{{font-size:1rem;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}}
  .dot{{width:8px;height:8px;border-radius:50%;background:var(--accent);flex-shrink:0}}
  .card{{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px}}
  .grid-4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:16px}}
  .grid-3{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:16px}}
  .grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px}}
  .kpi-label{{font-size:.7rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:6px}}
  .kpi{{font-size:1.8rem;font-weight:700}}
  .kpi.green{{color:var(--green)}}.kpi.red{{color:var(--red)}}.kpi.yellow{{color:var(--yellow)}}.kpi.neutral{{color:var(--text)}}
  .badge{{display:inline-block;padding:3px 10px;border-radius:99px;font-size:.72rem;font-weight:700}}
  .badge.fail{{background:rgba(239,68,68,.13);color:var(--red)}}
  .badge.warn{{background:rgba(245,158,11,.13);color:var(--yellow)}}
  .badge.pass{{background:rgba(34,197,94,.13);color:var(--green)}}
  .badge.info{{background:rgba(99,102,241,.13);color:#6366f1}}
  table{{width:100%;border-collapse:collapse;font-size:.85rem}}
  th{{text-align:left;padding:9px 12px;background:rgba(255,255,255,.04);color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.05em}}
  td{{padding:9px 12px;border-bottom:1px solid var(--border)}}
  tr:last-child td{{border-bottom:none}}
  tr.hl td{{background:rgba(99,102,241,.07)}}
  tr.hl2 td{{background:rgba(34,197,94,.06)}}
  .bar-w{{display:flex;align-items:center;gap:6px;min-width:80px}}
  .bar{{height:7px;border-radius:4px;min-width:3px}}
  .bar.g{{background:var(--green)}}.bar.r{{background:var(--red)}}.bar.y{{background:var(--yellow)}}
  .verdict-box{{border-radius:12px;padding:18px;margin-bottom:22px}}
  .verdict-box.fail{{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.28)}}
  .verdict-box.warn{{background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.28)}}
  .verdict-box h3{{font-size:.95rem;font-weight:700;margin-bottom:8px}}
  .verdict-box p{{font-size:.85rem;color:var(--muted);line-height:1.65}}
  .insight-box{{background:rgba(245,158,11,.05);border:1px solid rgba(245,158,11,.22);border-radius:12px;padding:18px;margin-bottom:22px}}
  .insight-box h3{{font-size:.9rem;font-weight:700;color:var(--yellow);margin-bottom:10px}}
  .insight-box li{{font-size:.85rem;color:var(--text);line-height:1.8;margin-left:18px}}
  .tag{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:.68rem;font-weight:700;margin-left:5px}}
  .tag.new{{background:rgba(34,197,94,.15);color:var(--green)}}
  .tag.old{{background:rgba(239,68,68,.15);color:var(--red)}}
  .pos{{color:var(--green);font-weight:600}}.neg{{color:var(--red);font-weight:600}}.zero{{color:var(--muted)}}
  footer{{margin-top:32px;padding-top:14px;border-top:1px solid var(--border);font-size:.75rem;color:var(--muted);text-align:center}}
</style>
</head>
<body>

<h1>FinPilot &mdash; Full Edge Audit v2</h1>
<p class="subtitle">2026-06-12 &nbsp;&middot;&nbsp; Barrier (TP/SL/21g) + T+5 + Regime Cross-Section &nbsp;&middot;&nbsp; {combined['n']:,} barrier-çözümlü sinyal</p>

<div class="verdict-box fail">
  <h3>&#9888; Genel Teşhis: TÜM ŞEMALARDA EDGE YOK veya ZAYIF</h3>
  <p>
    Tüm şemalar birleşik: barrier decile_lift = <strong>{combined['decile_lift']:.3f}</strong>, perm_p={combined['permutation_p']:.3f} &rarr; FAIL.
    0-100 ölçek izole: decile_lift=<strong>{new100['decile_lift']:.3f}</strong>, perm_p={new100['permutation_p']:.3f}.
    Corr(score, return)=<strong>{overall['corr_score_return']:+.4f}</strong> (neredeyse sıfır, hafif negatif).
    <strong>Tek pozitif sinyal:</strong> Bear rejimde Q2 skoru: wr={bear_q['Q2']['win_rate']*100:.1f}%, avg={pct(bear_q['Q2']['avg_pct'])}.
    Bu segment Faz 1 öncelidir. old_filter perm_p=0.04 geçiyor ancak lift=1.058 &mdash; ekonomik anlam zayıf.
  </p>
</div>

<div class="section">
<div class="section-title"><span class="dot"></span> Veri Durumu</div>
<div class="grid-4">
  <div class="card"><div class="kpi-label">Barrier Çözümlü</div><div class="kpi green">{combined['n']:,}</div></div>
  <div class="card"><div class="kpi-label">Genel Win Rate</div><div class="kpi yellow">{combined['overall']['hit_rate_barrier']*100:.1f}%</div></div>
  <div class="card"><div class="kpi-label">Genel Ort. Getiri</div><div class="kpi green">{pct(combined['overall']['expectancy_pct'])}</div></div>
  <div class="card"><div class="kpi-label">Corr(skor, getiri)</div><div class="kpi {'red' if overall['corr_score_return'] < 0 else 'green'}">{overall['corr_score_return']:+.4f}</div></div>
</div>
</div>

<div class="section">
<div class="section-title"><span class="dot"></span> Şema Bazlı Barrier Analizi</div>
<div class="card">
<table>
<thead><tr><th>Şema</th><th>n</th><th>Win Rate</th><th>Ort. Getiri</th><th>Medyan</th><th>PF</th><th>Decile Lift</th><th>Perm. p</th><th>Durum</th></tr></thead>
<tbody>
  <tr>
    <td><strong>0-100 Kompozit</strong> <span class="tag new">YENİ</span></td><td>{new100['n']}</td>
    <td>{new100['overall']['hit_rate_barrier']*100:.1f}%</td>
    <td class="{cls(new100['overall']['expectancy_pct'])}">{pct(new100['overall']['expectancy_pct'])}</td>
    <td class="{cls(new100['overall']['median_pct'])}">{pct(new100['overall']['median_pct'])}</td>
    <td>{new100['overall']['profit_factor']:.2f}</td>
    <td class="neg">{new100['decile_lift']:.3f}</td>
    <td class="neg">{new100['permutation_p']:.3f}</td>
    <td><span class="badge fail">NO EDGE</span></td>
  </tr>
  <tr>
    <td><strong>0-3 Filtre Skoru</strong> <span class="tag old">MID</span></td><td>{old_filter['n']:,}</td>
    <td>{old_filter['overall']['hit_rate_barrier']*100:.1f}%</td>
    <td class="{cls(old_filter['overall']['expectancy_pct'])}">{pct(old_filter['overall']['expectancy_pct'])}</td>
    <td class="{cls(old_filter['overall']['median_pct'])}">{pct(old_filter['overall']['median_pct'])}</td>
    <td>{old_filter['overall']['profit_factor']:.2f}</td>
    <td class="zero">{old_filter['decile_lift']:.3f}</td>
    <td class="pos">{old_filter['permutation_p']:.3f}</td>
    <td><span class="badge warn">ZAYIF (p&lt;0.05, lift&lt;1.3)</span></td>
  </tr>
  <tr>
    <td><strong>0-18 Ham Skor</strong> <span class="tag old">ESKİ</span></td><td>{old_raw['n']}</td>
    <td>{old_raw['overall']['hit_rate_barrier']*100:.1f}%</td>
    <td class="{cls(old_raw['overall']['expectancy_pct'])}">{pct(old_raw['overall']['expectancy_pct'])}</td>
    <td class="{cls(old_raw['overall']['median_pct'])}">{pct(old_raw['overall']['median_pct'])}</td>
    <td>{old_raw['overall']['profit_factor']:.2f}</td>
    <td class="neg">{old_raw['decile_lift']:.3f}</td>
    <td class="neg">{old_raw['permutation_p']:.3f}</td>
    <td><span class="badge warn">KARMA (wr yüksek, lift düşük)</span></td>
  </tr>
  <tr class="hl">
    <td><strong>Birleşik</strong></td><td>{combined['n']:,}</td>
    <td>{combined['overall']['hit_rate_barrier']*100:.1f}%</td>
    <td class="{cls(combined['overall']['expectancy_pct'])}">{pct(combined['overall']['expectancy_pct'])}</td>
    <td class="{cls(combined['overall']['median_pct'])}">{pct(combined['overall']['median_pct'])}</td>
    <td>{combined['overall']['profit_factor']:.2f}</td>
    <td class="zero">{combined['decile_lift']:.3f}</td>
    <td class="neg">{combined['permutation_p']:.3f}</td>
    <td><span class="badge warn">EŞİKTE (lift~1.3, p FAIL)</span></td>
  </tr>
</tbody>
</table>
</div>
</div>

<div class="section">
<div class="section-title"><span class="dot"></span> Rejim Kesit Analizi ({combined['n']:,} barrier sinyal)</div>
<div class="grid-2">
  <div class="card">
    <div style="font-size:.8rem;font-weight:700;margin-bottom:12px;color:#6366f1">Bull vs Bear</div>
    <table>
    <thead><tr><th>Rejim</th><th>n</th><th>Win Rate</th><th>Ort. Getiri</th><th>PF</th><th>Corr(s,r)</th></tr></thead>
    <tbody>
      <tr>
        <td>&#127836; Bull</td><td>{bull['n']:,}</td>
        <td>{bull['win_rate']*100:.1f}%</td>
        <td class="{cls(bull['avg_pct'])}">{pct(bull['avg_pct'])}</td>
        <td>{bull['profit_factor']:.2f}</td>
        <td class="pos">{bull['corr_score_return']:+.4f}</td>
      </tr>
      <tr class="hl2">
        <td><strong>&#128308; Bear</strong></td><td>{bear['n']:,}</td>
        <td><strong>{bear['win_rate']*100:.1f}%</strong></td>
        <td class="{cls(bear['avg_pct'])}"><strong>{pct(bear['avg_pct'])}</strong></td>
        <td><strong>{bear['profit_factor']:.2f}</strong></td>
        <td class="neg">{bear['corr_score_return']:+.4f}</td>
      </tr>
    </tbody>
    </table>
    <p style="margin-top:10px;font-size:.78rem;color:var(--yellow)">Bear rejimde yüksek PF={bear['profit_factor']:.2f}. Corr negatif &rarr; düşük/orta skor Bear'da daha iyi (geri dönüş fırsatı).</p>
  </div>
  <div class="card">
    <div style="font-size:.8rem;font-weight:700;margin-bottom:12px;color:#6366f1">Skor Çeyreği &times; Rejim (en kritik tablo)</div>
    <table>
    <thead><tr><th>Rejim</th><th>Çeyrek</th><th>n</th><th>Win Rate</th><th>Ort. %</th><th>PF</th></tr></thead>
    <tbody>
      <tr><td>Bull</td><td>Q1 düşük</td><td>{bull_q['Q1_low']['n']}</td><td>{bull_q['Q1_low']['win_rate']*100:.1f}%</td><td class="pos">{pct(bull_q['Q1_low']['avg_pct'])}</td><td>{bull_q['Q1_low']['profit_factor']:.2f}</td></tr>
      <tr><td>Bull</td><td>Q2</td><td>{bull_q['Q2']['n']}</td><td>{bull_q['Q2']['win_rate']*100:.1f}%</td><td class="{cls(bull_q['Q2']['avg_pct'])}">{pct(bull_q['Q2']['avg_pct'])}</td><td>{bull_q['Q2']['profit_factor']:.2f}</td></tr>
      <tr><td>Bull</td><td>Q3</td><td>{bull_q['Q3']['n']}</td><td>{bull_q['Q3']['win_rate']*100:.1f}%</td><td class="{cls(bull_q['Q3']['avg_pct'])}">{pct(bull_q['Q3']['avg_pct'])}</td><td>{bull_q['Q3']['profit_factor']:.2f}</td></tr>
      <tr><td>Bull</td><td>Q4 yüksek</td><td>{bull_q['Q4_high']['n']}</td><td>{bull_q['Q4_high']['win_rate']*100:.1f}%</td><td class="{cls(bull_q['Q4_high']['avg_pct'])}">{pct(bull_q['Q4_high']['avg_pct'])}</td><td>{bull_q['Q4_high']['profit_factor']:.2f}</td></tr>
      <tr><td>Bear</td><td>Q1 düşük</td><td>{bear_q['Q1_low']['n']}</td><td>{bear_q['Q1_low']['win_rate']*100:.1f}%</td><td class="{cls(bear_q['Q1_low']['avg_pct'])}">{pct(bear_q['Q1_low']['avg_pct'])}</td><td>{bear_q['Q1_low']['profit_factor']:.2f}</td></tr>
      <tr class="hl2"><td><strong>Bear</strong></td><td><strong>Q2 &#11088;</strong></td><td>{bear_q['Q2']['n']}</td><td><strong>{bear_q['Q2']['win_rate']*100:.1f}%</strong></td><td class="pos"><strong>{pct(bear_q['Q2']['avg_pct'])}</strong></td><td><strong>{bear_q['Q2']['profit_factor']:.2f}</strong></td></tr>
      <tr><td>Bear</td><td>Q3</td><td>{bear_q['Q3']['n']}</td><td>{bear_q['Q3']['win_rate']*100:.1f}%</td><td class="{cls(bear_q['Q3']['avg_pct'])}">{pct(bear_q['Q3']['avg_pct'])}</td><td>{bear_q['Q3']['profit_factor']:.2f}</td></tr>
      <tr><td>Bear</td><td>Q4 yüksek</td><td>{bear_q['Q4_high']['n']}</td><td>{bear_q['Q4_high']['win_rate']*100:.1f}%</td><td class="{cls(bear_q['Q4_high']['avg_pct'])}">{pct(bear_q['Q4_high']['avg_pct'])}</td><td>{bear_q['Q4_high']['profit_factor']:.2f}</td></tr>
    </tbody>
    </table>
  </div>
</div>
<div class="insight-box">
  <h3>&#128273; Kritik Bulgular</h3>
  <ul>
    <li><strong>Bear Q2 en güçlü segment:</strong> wr={bear_q['Q2']['win_rate']*100:.1f}%, avg={pct(bear_q['Q2']['avg_pct'])}, PF={bear_q['Q2']['profit_factor']:.2f} (n={bear_q['Q2']['n']}) &mdash; Bu segmenti izole etmek Faz 1'in #1 öncelidir.</li>
    <li><strong>Bear Q4 (yüksek skor) zayıf:</strong> wr={bear_q['Q4_high']['win_rate']*100:.1f}% &mdash; Momentum zirvesi = yakın dönüş riski, Bear'da da geçerli.</li>
    <li><strong>vol_regime + sector_rs tamamen NULL:</strong> 4.066 kaydın tamamı bu alanları boş döndürüyor. Sadece June 2026 sonrası sinyallerde mevcut.</li>
    <li><strong>Bull Q3 en kötü:</strong> wr={bull_q['Q3']['win_rate']*100:.1f}%, PF={bull_q['Q3']['profit_factor']:.2f} &mdash; "orta-yüksek skor + Bull" kombinasyonundan kaçın.</li>
  </ul>
</div>
</div>

<div class="section">
<div class="section-title"><span class="dot"></span> Decile Analizi &mdash; 0-100 Kompozit (n={new100['n']}, barrier label)</div>
<div class="card">
<table>
<thead><tr><th>Decile</th><th>Skor Aral.</th><th>n</th><th>Win Rate</th><th>Bar</th><th>Ort. %</th><th>Medyan %</th></tr></thead>
<tbody>
{decile_rows}
</tbody>
</table>
<p style="margin-top:10px;font-size:.78rem;color:var(--yellow)">n={new100['n']} küçük örneklem. Decile 3 (skor 36-42) = {best_d['win_rate']*100:.1f}% wr en yüksek. Decile 10 (yüksek skor) = 25.0% wr en düşük.</p>
</div>
</div>

<div class="section">
<div class="section-title"><span class="dot"></span> Sonraki Adımlar (Öncelik Sırası)</div>
<div class="grid-3">
  <div class="card">
    <div class="kpi-label">FAZ 1 &mdash; Hemen (P1)</div>
    <ul style="font-size:.82rem;line-height:1.9;padding-left:16px;margin-top:8px">
      <li><strong>Bear + Q2 Filtresi:</strong> Sadece Bear rejimde orta skor bandında al &rarr; expected wr={bear_q['Q2']['win_rate']*100:.1f}%</li>
      <li><strong>Yüksek skor suppression:</strong> Decile 10 (62+) pozisyon boyutunu yarıya indir</li>
      <li><strong>vol_regime kaydı:</strong> June+ sinyaller yazılıyor &mdash; ilerleyen analizde mevcut olacak</li>
    </ul>
  </div>
  <div class="card">
    <div class="kpi-label">FAZ 1 &mdash; Veri Birikmesi (P1.5)</div>
    <ul style="font-size:.82rem;line-height:1.9;padding-left:16px;margin-top:8px">
      <li>Yang-Zhang vol ile TP/SL hesapla (ATR yerine)</li>
      <li>Double-sort momentum x turnover segment analizi</li>
      <li>Walk-forward weight optimizer (altyapı hazır)</li>
    </ul>
  </div>
  <div class="card">
    <div class="kpi-label">FAZ 2 &mdash; Edge Kanıtı Sonrası</div>
    <ul style="font-size:.82rem;line-height:1.9;padding-left:16px;margin-top:8px">
      <li>Meta-labeling XGBoost (core/calibration.py yükseltme)</li>
      <li>SJM + Hurst rejim tespiti</li>
      <li>Black-Litterman portföy çerçevesi</li>
      <li style="color:var(--red)">OFI/Order Book: L2 veri yok &mdash; REDDET</li>
    </ul>
  </div>
</div>
</div>

<div class="section">
<div class="section-title"><span class="dot"></span> Uygulanan Değişiklikler (Bu Oturum)</div>
<div class="card">
<table>
<thead><tr><th>Değişiklik</th><th>Dosya</th><th>Etki</th><th>Durum</th></tr></thead>
<tbody>
  <tr><td>finpilot_score write-back</td><td>api/routers/scan.py</td><td>Yeni sinyallerden finpilot_score DB'ye yazılıyor</td><td><span class="badge pass">&#10003; Uygulandı</span></td></tr>
  <tr><td>extract_score öncelikleri</td><td>scripts/profitcore_audit.py</td><td>Audit composite_score'u score yerine okuyor</td><td><span class="badge pass">&#10003; Uygulandı</span></td></tr>
  <tr><td>resolve_open_signals.py</td><td>scripts/ (yeni)</td><td>T+5 + barrier ikili etiket; 4.566 sinyal çözüldü</td><td><span class="badge pass">&#10003; Çalıştı</span></td></tr>
  <tr><td>Scheduler haftalık job</td><td>core/scheduler.py</td><td>Pzt 03:00 UTC otomatik çalışır</td><td><span class="badge pass">&#10003; Eklendi</span></td></tr>
  <tr><td>barrier_audit.py</td><td>scripts/ (yeni)</td><td>DB tabanlı şema-izole barrier analizi</td><td><span class="badge pass">&#10003; Çalıştı</span></td></tr>
  <tr><td>regime_cross_section.py</td><td>scripts/ (yeni)</td><td>Regime x skor kesit analizi</td><td><span class="badge pass">&#10003; Çalıştı</span></td></tr>
</tbody>
</table>
</div>
</div>

<footer>
  FinPilot Edge Audit v2 &nbsp;&middot;&nbsp; 2026-06-12 &nbsp;&middot;&nbsp; {combined['n']:,} barrier-çözümlü sinyal
  &nbsp;&middot;&nbsp; Sonraki otomatik çalışma: Pazartesi 03:00 UTC
  &nbsp;&middot;&nbsp; <strong>Uyarı:</strong> Seviye-2 edge kanıtlanana kadar canlı performans iddiası yok.
</footer>
</body>
</html>"""

out = Path("data/edge_report.html")
out.write_text(html, encoding="utf-8")
print(f"Written {len(html)} chars to {out}")
