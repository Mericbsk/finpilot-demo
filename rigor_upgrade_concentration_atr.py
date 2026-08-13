#!/usr/bin/env python3
"""
rigor_upgrade_concentration_atr.py — Item 1: concentration-limit ve ATR-parity
bulgularini reverse-ranking/extension-exhaustion'i olduren ayni suzgecten gecirir.

Bu script'ten once concentration_portfolio_test.py / atr_sizing_test.py SADECE
nokta-tahmini (point estimate) veriyordu: hicbir CI, hicbir matched-random kontrol,
hicbir gun-ici-otokorelasyon duzeltmesi yoktu. Bu script bunlari ekliyor + YENI,
onceden fark edilmemis bir veri kusuru buldu (asagida NOT 0).

NOT 0 (yeni bulgu, bu script'i yazarken ortaya cikti):
  edge_recheck.csv DEDUP EDILMEMIS: 53,754 satir ama sadece 27,323 essiz
  (symbol,scan_date) anahtari (13,062 tekrarli anahtar). full_universe_enriched.csv
  ile capraz kontrol: gunun ilk-taranan (en-erken scan_ts) satirinin composite_score'u
  edge_recheck'teki 13,062 tekrarli anahtarin %85'inde (11,142/13,062) gruptaki
  satirlardan biriyle tam eslesiyor -> bu satiri "dogru" ilk-tarama satiri olarak
  secebiliyoruz. Kalan %15 icin (scan_ts eslesmesi yok / composite_score kaynak
  dosyada hafif farkli hesaplanmis olabilir) EN-KUCUK-composite_score'lu satir
  deterministik fallback olarak seciliyor (belirtilen bir sinirlama, mukemmel degil
  ama rastgele degil ve tekrarlanabilir).
  ETKI: dedup'siz top-10 gunlerin %68'inde (38/56) AYNI SEMBOL 2 KEZ top-10'a
  giriyordu (coklu intraday tarama, ayni gun) -> o sembolun getirisi o gunun
  portfoy-ortalamasinda YANLISLIKLA CIFT SAYILIYORDU. Bu, concentration_portfolio_test.py
  ve atr_sizing_test.py'nin SIMDIYE KADAR bildirdigi TUM sayilari (kisitli/kisitsiz,
  ATR-agirlikli/esit-agirlikli) gecersiz kiliyor -- capraz kontrol asagida.

NOT 1 (otokorelasyon): c2c5_net bir 5-gunluk ILERI getiri. Ardisik islem
gunlerinin 5-gunluk pencereleri ORTUSUYOR (t gunu ile t+1..t+4 gunleri ayni
fiyat hareketinin bir kismini paylasir) -> gunler ISTATISTIKSEL OLARAK BAGIMSIZ
DEGIL. Naif gun-sayisi (n_gun=52-66) t-testi SE'yi kucumser. Bu script iki
duzeltme uyguluyor: (a) blok-bootstrap (blok=5 ardisik islem gunu, B=5000) CI,
(b) her-5-gunde-bir ORTUSMEYEN alt-orneklem ile "sert" t-testi (effective_n ~
n_gun/5) -- ikisi de raporlaniyor.

NOT 2 (matched-random kontrol): sektor-tavani HER portfoyu (bilgili veya
rastgele secilmis) daha az korele/daha cok cesitlendirilmis yapar -- bu SAF
MATEMATIKSEL bir cesitlendirme etkisidir, score'un bilgisiyle ilgisi yoktur.
Bu yuzden "kisitli std/CVaR daha iyi" bulgusunun score-secimine OZGU olup
olmadigini test etmek icin, HER GUN score yerine RASTGELE N sembol secen
(kisitli ve kisitsiz varyantlarda) bir kontrol portfoyu da kosturuluyor
(R=200 cekilis/gun, ortalamasi alinip o gunun "rastgele-taban" degeri sayiliyor).
Eger score-secimli (kisitli-kisitsiz) fark, rastgele-secimli (kisitli-kisitsiz)
farktan ISTATISTIKSEL OLARAK AYRISMIYORSA -> "concentration-limit score'u
iyilestiriyor" iddiasi cokuyor; sadece "sektor-tavani HERHANGI bir portfoyu
cesitlendirir" (trivial, ama hala faydali bir portfoy-insaası kurali, sadece
"score+cap ozel bir sey" degil).

NOT 3 (ATR-parity icin permutasyon kontrolu): ATR-ters-agirlik, esit-agirliga
gore agirlik DAGILIMINI degistirir (bazi isimlere daha az, bazilarina daha
cok agirlik). Bu farkin GERCEKTEN ATR'nin dogru isim/orani secmesinden mi,
yoksa SADECE agirlik-dagilimi varyansindan mi geldigini ayirmak icin, her gun
o gunun ATR degerleri o gunun secilmis isimleri arasinda KARISTIRILIP
(permute) ATR-agirlikli getiri yeniden hesaplaniyor (P=200 permutasyon/gun).
Gercek ATR-agirlikli getiri, permutasyon dagiliminin disindaysa -> ATR'nin
SPESIFIK bilgisi (yuksek-ATR=daha riskli=daha kucuk pozisyon) isliyor demektir.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

N = 10
MAXK = 3
RAND_DRAWS = 200
PERM_DRAWS = 200
BLOCK = 5
BOOT_B = 5000
RNG = random.Random(2026)


# ---------- 1) DEDUP (NOT 0) ----------
def build_dedup_map():
    """(symbol,scan_date) -> en-erken scan_ts'in composite_score'u (full_universe_enriched.csv'den)."""
    best = {}
    with open("data/backtest_out/full_universe_enriched.csv") as f:
        for r in csv.DictReader(f):
            k = (r["symbol"], r["scan_date"])
            ts = r.get("scan_ts", "")
            if k not in best or ts < best[k][0]:
                best[k] = (ts, r.get("composite_score"))
    return best


def load_deduped_edge_recheck():
    earliest = build_dedup_map()
    groups = defaultdict(list)
    with open("data/backtest_out/edge_recheck.csv") as f:
        for r in csv.DictReader(f):
            groups[(r["symbol"], r["scan_date"])].append(r)

    resolved_by_join, resolved_by_fallback = 0, 0
    out_rows = []
    for k, grp in groups.items():
        if len(grp) == 1:
            out_rows.append(grp[0])
            continue
        target_cs = earliest.get(k, (None, None))[1]
        picked = None
        for r in grp:
            if target_cs is not None and r["composite_score"] == target_cs:
                picked = r
                resolved_by_join += 1
                break
        if picked is None:
            picked = min(grp, key=lambda r: _f(r["composite_score"], 1e18))
            resolved_by_fallback += 1
        out_rows.append(picked)

    print(
        f"[DEDUP] essiz anahtar={len(groups)}  tekrarli-anahtar={sum(1 for v in groups.values() if len(v) > 1)}  "
        f"join-ile-cozulen={resolved_by_join}  fallback(min-score)={resolved_by_fallback}"
    )
    return out_rows


def _f(x, default=None):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


# ---------- 2) VERI HAZIRLAMA ----------
def load_flagged_symbols():
    data = json.load(open("data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-07.json"))
    return set(x["symbol"] for x in data["flagged_symbols"])


def prep_rows(raw_rows, sector_map, flagged, exclude_flagged=True):
    """NOT 0.5 (Item-1 & Item-4 kesisimi): |c2c5_net|>100 satirlarin %75'i (93/124)
    148 price-integrity-flagged sembolle cakisiyor (orn. EDBL +154,445%, INLF +9,146%
    -- gercek getiri degil, muhtemelen ayarlanmamis reverse-split/veri hatasi).
    Bunlari disarida biraktirmadan calisan rastgele-portfoy kontrolu (ADIM 2, Test B/C)
    gunluk ortalamayi +25%'e kadar sisiriyordu -- kendisi bir 'felaket alt-kumesi'
    kontaminasyonu ornegi (Item 4'un tam olarak sordugu sey). Bu yuzden burada
    flagged sembolleri VARSAYILAN OLARAK disariya biraktiriyoruz ve bunu acikca
    logluyoruz; sonuc boylece Item-1 (rigor) ile Item-4 (felaket alt-kumesi) arasinda
    tutarli kaliyor."""
    rows = []
    n_excluded = 0
    for r in raw_rows:
        c2c = _f(r.get("c2c5_net"))
        sc = _f(r.get("composite_score"))
        atr = _f(r.get("atr_pct"))
        if c2c is None or sc is None:
            continue
        if exclude_flagged and r["symbol"] in flagged:
            n_excluded += 1
            continue
        rows.append(
            {
                "symbol": r["symbol"],
                "date": r["scan_date"],
                "c2c": c2c,
                "sc": sc,
                "atr": atr if (atr is not None and atr > 0) else None,
                "sec": sector_map.get(r["symbol"], "UNK"),
            }
        )
    if exclude_flagged:
        print(
            f"[FELAKET-ALT-KUMESI FILTRESI] {n_excluded} satir (148 price-integrity-flagged sembolden) disarida birakildi."
        )
    return rows


def by_date(rows):
    d = defaultdict(list)
    for r in rows:
        d[r["date"]].append(r)
    return d


def pick_unconstrained(grp_sorted, n=N):
    return grp_sorted[:n]


def pick_constrained(grp_sorted, n=N, maxk=MAXK):
    con, sec_count = [], {}
    for r in grp_sorted:
        s = r["sec"]
        if sec_count.get(s, 0) >= maxk:
            continue
        con.append(r)
        sec_count[s] = sec_count.get(s, 0) + 1
        if len(con) >= n:
            break
    return con if len(con) >= n else None


def eq_ret(picks):
    return statistics.mean(r["c2c"] for r in picks)


def atr_ret(picks):
    usable = [r for r in picks if r["atr"] is not None]
    if len(usable) < len(picks) * 0.6:
        return None
    w = [1.0 / r["atr"] for r in usable]
    tw = sum(w)
    return sum(wi * r["c2c"] for wi, r in zip(w, usable, strict=False)) / tw


def perm_atr_ret(picks, rng):
    """ATR degerlerini secilmis isimler arasinda karistirip agirlikli getiriyi yeniden hesapla (NOT 3)."""
    usable = [r for r in picks if r["atr"] is not None]
    if len(usable) < len(picks) * 0.6:
        return None
    atrs = [r["atr"] for r in usable]
    rng.shuffle(atrs)
    w = [1.0 / a for a in atrs]
    tw = sum(w)
    return sum(wi * r["c2c"] for wi, r in zip(w, usable, strict=False)) / tw


def sector_conc(picks):
    cnt = Counter(r["sec"] for r in picks)
    return max(cnt.values()) / len(picks)


# ---------- 3) GUNLUK SERILERI URET ----------
def build_series(rows_by_date):
    series = {
        k: {}
        for k in [
            "score_unc_eq",
            "score_con_eq",
            "score_unc_atr",
            "score_con_atr",
            "rand_unc_eq",
            "rand_con_eq",
            "perm_unc_atr",
            "perm_con_atr",
        ]
    }
    conc = {"score_unc": {}, "score_con": {}, "rand_unc": {}, "rand_con": {}}

    for d, grp in sorted(rows_by_date.items()):
        if len(grp) < N:
            continue
        grp_sorted = sorted(grp, key=lambda r: r["sc"], reverse=True)
        unc = pick_unconstrained(grp_sorted)
        con = pick_constrained(grp_sorted)

        series["score_unc_eq"][d] = eq_ret(unc)
        conc["score_unc"][d] = sector_conc(unc)
        a = atr_ret(unc)
        if a is not None:
            series["score_unc_atr"][d] = a

        if con is not None:
            series["score_con_eq"][d] = eq_ret(con)
            conc["score_con"][d] = sector_conc(con)
            a = atr_ret(con)
            if a is not None:
                series["score_con_atr"][d] = a

        # permutasyon kontrolu (NOT 3) -- gercek ATR-agirlikli getiriyle karsilastirmak icin dagilim
        pu = [perm_atr_ret(unc, RNG) for _ in range(PERM_DRAWS)]
        pu = [x for x in pu if x is not None]
        if pu:
            series["perm_unc_atr"][d] = statistics.mean(pu)
        if con is not None:
            pc = [perm_atr_ret(con, RNG) for _ in range(PERM_DRAWS)]
            pc = [x for x in pc if x is not None]
            if pc:
                series["perm_con_atr"][d] = statistics.mean(pc)

        # matched-random kontrol (NOT 2)
        pool = grp
        if len(pool) >= N:
            ru_vals, rc_vals = [], []
            ru_conc, rc_conc = [], []
            for _ in range(RAND_DRAWS):
                samp = RNG.sample(pool, N)
                ru_vals.append(eq_ret(samp))
                ru_conc.append(sector_conc(samp))
                # rastgele + sektor-tavani: ayni pool'dan rastgele sirayla tarayip cap uygula
                shuffled = pool[:]
                RNG.shuffle(shuffled)
                rc = pick_constrained(shuffled)
                if rc is not None:
                    rc_vals.append(eq_ret(rc))
                    rc_conc.append(sector_conc(rc))
            series["rand_unc_eq"][d] = statistics.mean(ru_vals)
            conc["rand_unc"][d] = statistics.mean(ru_conc)
            if rc_vals:
                series["rand_con_eq"][d] = statistics.mean(rc_vals)
                conc["rand_con"][d] = statistics.mean(rc_conc)

    return series, conc


# ---------- 4) ISTATISTIK YARDIMCILARI ----------
def day_stats(series_dict, label):
    days = sorted(series_dict)
    vals = [series_dict[d] for d in days]
    n = len(vals)
    if n < 5:
        print(f"  {label:24} n=yetersiz({n})")
        return None
    mean = statistics.mean(vals)
    std = statistics.pstdev(vals) if n > 1 else 0.0
    srt = sorted(vals)
    cvar5 = statistics.mean(srt[: max(1, int(n * 0.05))])
    cum = peak = maxdd = 0.0
    for v in vals:
        cum += v
        peak = max(peak, cum)
        maxdd = min(maxdd, cum - peak)
    print(
        f"  {label:24} n_gun={n:4d}  ort={mean:+.4f}  std={std:.4f}  CVaR5%={cvar5:+.4f}  maxDD={maxdd:+.4f}"
    )
    return {"days": days, "vals": vals, "mean": mean, "std": std, "cvar5": cvar5, "maxdd": maxdd}


def paired_diff_series(a_dict, b_dict):
    """b - a, ortak gunlerde (b: kisitli/atr/... , a: kisitsiz/eq/... referans)."""
    common = sorted(set(a_dict) & set(b_dict))
    diffs = [b_dict[d] - a_dict[d] for d in common]
    return common, diffs


def naive_t(diffs):
    n = len(diffs)
    if n < 2:
        return float("nan"), float("nan"), n
    m = statistics.mean(diffs)
    sd = statistics.pstdev(diffs)
    se = sd / math.sqrt(n) if sd else 0.0
    t = m / se if se else float("nan")
    return m, t, n


def block_bootstrap_ci(diffs, block=BLOCK, B=BOOT_B, rng=None):
    """Ardisik-blok bootstrap: otokorelasyonu (ortusen 5-gunluk ileri-pencere) hesaba katar."""
    rng = rng or RNG
    n = len(diffs)
    if n < block + 1:
        return None
    n_blocks_needed = math.ceil(n / block)
    boot_means = []
    for _ in range(B):
        sample = []
        for _ in range(n_blocks_needed):
            start = rng.randrange(0, n - block + 1)
            sample.extend(diffs[start : start + block])
        sample = sample[:n]
        boot_means.append(statistics.mean(sample))
    boot_means.sort()
    lo = boot_means[int(0.025 * B)]
    hi = boot_means[int(0.975 * B)]
    return lo, hi, statistics.mean(boot_means)


def nonoverlapping_subsample_t(days, diffs, step=BLOCK):
    """Her step-gunde-bir (ortusmeyen) alt-orneklem -- 'sert' bagimsizlik varsayimi."""
    idx = list(range(0, len(diffs), step))
    sub = [diffs[i] for i in idx]
    m, t, n = naive_t(sub)
    return m, t, n


def report_pair(label, a_dict, b_dict, note=""):
    days, diffs = paired_diff_series(a_dict, b_dict)
    if len(diffs) < 5:
        print(f"  {label:40} n=yetersiz")
        return
    m_naive, t_naive, n = naive_t(diffs)
    ci = block_bootstrap_ci(diffs)
    m_sub, t_sub, n_sub = nonoverlapping_subsample_t(days, diffs)
    ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
    verdict = "ANLAMLI" if (ci and (ci[0] > 0 or ci[1] < 0)) else "anlamsiz(CI 0'i iceriyor)"
    print(
        f"  {label:40} n_gun={n:4d}  fark-ort={m_naive:+.4f}  naive-t~={t_naive:+.2f}  "
        f"blok-boot-95%CI={ci_str}  [{verdict}]"
    )
    print(
        f"    {'':40} ortusmeyen-alt-orneklem: n={n_sub}  fark-ort={m_sub:+.4f}  t~={t_sub:+.2f}  {note}"
    )


# ---------- 5) MAIN ----------
def main():
    sec = {
        r["symbol"]: r["etf"]
        for r in csv.DictReader(open("data/backtest_out/sector_map_full.csv"))
        if r["etf"]
    }

    print("=" * 90)
    print("ADIM 0 -- DEDUP (yeni bulgu)")
    print("=" * 90)
    raw = load_deduped_edge_recheck()
    flagged = load_flagged_symbols()
    rows = prep_rows(raw, sec, flagged, exclude_flagged=True)
    print(
        f"[VERI] dedup+felaket-filtresi-sonrasi kullanilabilir satir={len(rows)}  essiz-sembol={len({r['symbol'] for r in rows})}"
    )

    rbd = by_date(rows)
    series, conc = build_series(rbd)

    print("\n" + "=" * 90)
    print("ADIM 1 -- GUNLUK SERI ISTATISTIKLERI (dedup-SONRASI, tum varyantlar)")
    print("=" * 90)
    stats = {}
    for k in [
        "score_unc_eq",
        "score_con_eq",
        "score_unc_atr",
        "score_con_atr",
        "rand_unc_eq",
        "rand_con_eq",
    ]:
        stats[k] = day_stats(series[k], k)

    print("\n  -- ortalama en-yogun-sektor-payi --")
    for k, d in conc.items():
        if d:
            print(f"  {k:24} ort-konsantrasyon={statistics.mean(d.values()):.1%}  n={len(d)}")

    print("\n" + "=" * 90)
    print("ADIM 2 -- CONCENTRATION-LIMIT: kisitli-kisitsiz fark, SCORE vs RASTGELE-TABAN")
    print("=" * 90)
    print(" [Test A] Score-secimli: kisitli - kisitsiz (eq-agirlik)")
    report_pair("score: kisitli-kisitsiz", series["score_unc_eq"], series["score_con_eq"])
    print(" [Test B] Rastgele-secimli (matched-random kontrol): kisitli - kisitsiz (NOT 2)")
    report_pair("rastgele: kisitli-kisitsiz", series["rand_unc_eq"], series["rand_con_eq"])
    print(" [Test C] Score'un rastgeleye karsi katkisi (bilgi var mi?)")
    report_pair("kisitsiz: score-rastgele", series["rand_unc_eq"], series["score_unc_eq"])
    report_pair("kisitli:  score-rastgele", series["rand_con_eq"], series["score_con_eq"])
    print(
        " [Test D] Score'un kisitli-kisitsiz farki, rastgelenin ayni farkindan ayrisiyor mu? (interaksiyon)"
    )
    _, d_score = paired_diff_series(series["score_unc_eq"], series["score_con_eq"])
    _, d_rand = paired_diff_series(series["rand_unc_eq"], series["rand_con_eq"])
    common_days = sorted(
        set(series["score_unc_eq"])
        & set(series["score_con_eq"])
        & set(series["rand_unc_eq"])
        & set(series["rand_con_eq"])
    )
    inter = [
        (series["score_con_eq"][d] - series["score_unc_eq"][d])
        - (series["rand_con_eq"][d] - series["rand_unc_eq"][d])
        for d in common_days
    ]
    if len(inter) >= 5:
        m, t, n = naive_t(inter)
        ci = block_bootstrap_ci(inter)
        ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
        verdict = (
            "score'a OZGU (anlamli interaksiyon)"
            if (ci and (ci[0] > 0 or ci[1] < 0))
            else "score'a OZGU DEGIL -- generic cesitlendirme etkisi (CI 0'i iceriyor)"
        )
        print(
            f"  interaksiyon(score_diff - rand_diff)   n_gun={n:4d}  ort={m:+.4f}  naive-t~={t:+.2f}  boot-CI={ci_str}  [{verdict}]"
        )

    print("\n" + "=" * 90)
    print("ADIM 3 -- ATR-PARITY: eq-agirlik vs ATR-ters-agirlik, GERCEK vs PERMUTASYON (NOT 3)")
    print("=" * 90)
    for tag, unc_key, con_key, punc_key, pcon_key in [
        ("kisitsiz", "score_unc_eq", "score_unc_atr", "perm_unc_atr", None),
        ("kisitli", "score_con_eq", "score_con_atr", "perm_con_atr", None),
    ]:
        print(f" [{tag}] gercek ATR-agirlik - eq-agirlik:")
        report_pair(f"{tag}: atr-eq (gercek)", series[unc_key], series[con_key])
        print(
            f" [{tag}] permute-ATR-agirlik - eq-agirlik (gercek ATR bilgisi YOK, sadece agirlik-dagilimi):"
        )
        report_pair(f"{tag}: atr-eq (permute)", series[unc_key], series[punc_key])
        _, d_real = paired_diff_series(series[unc_key], series[con_key])
        _, d_perm = paired_diff_series(series[unc_key], series[punc_key])
        common2 = sorted(set(series[unc_key]) & set(series[con_key]) & set(series[punc_key]))
        inter2 = [
            (series[con_key][d] - series[unc_key][d]) - (series[punc_key][d] - series[unc_key][d])
            for d in common2
        ]
        if len(inter2) >= 5:
            m, t, n = naive_t(inter2)
            ci = block_bootstrap_ci(inter2)
            ci_str = f"[{ci[0]:+.4f}, {ci[1]:+.4f}]" if ci else "n/a"
            verdict = (
                "ATR'nin GERCEK bilgisi isliyor"
                if (ci and (ci[0] > 0 or ci[1] < 0))
                else "ATR'nin ozel bilgisi ayirt edilemiyor (CI 0'i iceriyor) -- agirlik-dagilimi varyansi olabilir"
            )
            print(
                f"  interaksiyon(gercek-atr_diff - permute-atr_diff)  n_gun={n:4d}  ort={m:+.4f}  t~={t:+.2f}  boot-CI={ci_str}  [{verdict}]"
            )
        print()


if __name__ == "__main__":
    main()
