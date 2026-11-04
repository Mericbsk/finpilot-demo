"""Frozen 200-symbol scanner timing run (plan Faz 1). Isolated container only.

Input: production batch sample from data/shortlists/shortlist_20261016_1813.csv (frozen).
Run: python - < research/scanner_perf_baseline_2026_10_17.py   (stdin; no file copy into the API)
Prints one JSON object. Writes no scan artifacts; provider calls are real.
"""

import gc
import json
import os
import sys
import time

os.environ["FINPILOT_SCAN_STAGE_TIMING"] = "1"
sys.path.insert(0, "/app")

SYMBOLS = (
    "BGSF,ALIS,ASRT,BCV,BRR,BWIV,BHAV,CAAS,APUR,BUUU,CCAQ,CATO,AIIA,AMBR,ASUR,AKBA,AMCI,AIFC,ANPA,ASLE,"
    "APYX,AVXL,AP,ASTI,ATRA,AUC,AMPY,COPL,CPOP,AVD,BOTJ,ANIX,AIRG,BMHL,BRT,BMEA,BVFL,BUDA,BCBP,BSBK,"
    "BTMD,BHR,CCLD,BWG,ADCT,CFFI,CHCI,CHGG,DYOR,CING,CHMI,CMRC,CNCK,CNTB,EGHA,CLAR,CNF,EMIS,CNVS,EMPG,"
    "CNTN,COOK,CRDF,CPHC,CRT,ESCA,ETX,CTW,CUE,CRNT,CURV,CYPH,FACT,FATN,CURI,FCT,CVGI,CZWI,DAVA,FLXS,"
    "DERM,DLNG,DFDV,FRAF,DMRC,FSEA,FSHP,FSI,DLTH,DMAC,DMB,GAMB,DSX,ELDN,EGG,DXR,EARN,GLED,EP,GLQ,"
    "ECF,ELME,FNRN,FLWS,GSRF,GSRFU,HAVAU,HBB,EML,HCACU,HCHL,HDRN,EVTL,HFFG,EOD,EPM,ENGN,HQI,EXFY,HYI,"
    "GALT,IAF,EBMT,IGAC,GCTS,EU,FRMM,INAC,FNKO,FSP,GAIA,FBLA,EXOZ,EFT,JLS,JMG,EVG,EOT,FLC,GENC,"
    "FMN,KORE,KPET,FF,GF,LAFA,GGT,GLDG,GMHS,GLO,GPMT,GOSS,GRWG,LFT,HCAC,HELP,HNNA,HOUR,HOFT,HYNE,"
    "LSBK,IBIO,HYFT,IHD,IMDX,MAMK,INSE,MCHX,INVZ,IZEA,JENA,JILL,IMMR,JMM,JRS,KBSX,JACK,KG,KLRS,KULR,"
    "KVHI,LARK,LAKE,LAW,LCUT,LFCR,LFMD,LFS,LFVN,LGCY,LIDR,LITB,LIEN,LNSR,LUD,LVWR,MAIA,MBOT,LTBR,MDAI"
).split(",")

DECISION_FIELDS = (
    "composite_score",
    "filter_score",
    "selection_eligible",
    "entry_ok",
    "conviction_tier",
    "direction",
)


def main() -> None:
    from scanner import evaluate_symbols_parallel
    from scanner import data_fetcher
    from scanner.performance import snapshot

    assert len(SYMBOLS) == 200, len(SYMBOLS)
    data_fetcher.reset_yf_fetch_count()
    gc.collect()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    results = evaluate_symbols_parallel(symbols=SYMBOLS, kelly_fraction=0.5)
    wall_s = time.perf_counter() - wall_started
    cpu_s = time.process_time() - cpu_started

    stages: dict[str, dict] = {}
    for event in snapshot():
        agg = stages.setdefault(event["stage"], {"events": 0, "sum_s": 0.0})
        agg["events"] += 1
        agg["sum_s"] = round(agg["sum_s"] + float(event["elapsed_s"]), 6)

    rows = list(results.values()) if isinstance(results, dict) else list(results)
    decisions = {}
    for row in rows:
        sym = str(row.get("symbol") or row.get("ticker") or "").upper()
        decisions[sym] = {field: row.get(field) for field in DECISION_FIELDS}

    print(
        json.dumps(
            {
                "symbols_requested": len(SYMBOLS),
                "results": len(rows),
                "wall_s": round(wall_s, 3),
                "cpu_process_s": round(cpu_s, 3),
                "yf_fallback": data_fetcher.yf_fetch_count(),
                "stages": stages,
                "decisions": decisions,
            },
            default=str,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
