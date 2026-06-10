"""Consolidate stock_presets.json from 34 presets into 9 unified presets.

Merges small sector/thematic/strategy presets WITH the FP: full-sector presets
into a single flat structure.  Validates every symbol against the Alpaca
symbols table (tradable=1) — removes delisted tickers automatically.

Writes:
  - data/stock_presets.json
  - web/public/stock_presets.json  (identical copy for the Next.js frontend)

Usage
-----
    python scripts/consolidate_presets.py              # update both JSON files
    python scripts/consolidate_presets.py --dry-run    # print stats, no writes
    python scripts/consolidate_presets.py --stats      # show group sizes only
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core.config import DB_PATH  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
)
logger = logging.getLogger("consolidate_presets")

PRESETS_SRC = REPO_ROOT / "data" / "stock_presets.json"
PRESETS_WEB = REPO_ROOT / "web" / "public" / "stock_presets.json"

# ---------------------------------------------------------------------------
# Consolidation map: new_key → list of old preset keys to merge
# ---------------------------------------------------------------------------
CONSOLIDATION: dict[str, dict] = {
    "technology": {
        "name": "Teknoloji",
        "name_en": "Technology",
        "icon": "💻",
        "description": "Yarı iletken, bulut, SaaS, kurumsal yazılım, AI, telekom",
        "category": "Sektör",
        "sources": [
            "tech_giants",
            "semiconductors",
            "cloud_saas",
            "enterprise_software",
            "fp_technology",
            "fp_telecommunications",
        ],
    },
    "healthcare_biotech": {
        "name": "Sağlık & Biyoteknoloji",
        "name_en": "Healthcare & Biotech",
        "icon": "🧬",
        "description": "Büyük biyotek, yükselen biyotek, sağlık hizmetleri, ilaç pipeline, tıbbi cihaz",
        "category": "Sektör",
        "sources": [
            "biotech_large",
            "biotech_emerging",
            "healthcare_services",
            "pharma_pipeline",
            "medical_devices",
            "fp_health_care",
        ],
    },
    "finance": {
        "name": "Finans",
        "name_en": "Finance",
        "icon": "🏦",
        "description": "Bankalar, fintek, sigorta, çeşitlendirilmiş finans, gayrimenkul (REIT)",
        "category": "Sektör",
        "sources": [
            "finance_banks",
            "finance_fintech",
            "insurance",
            "finance_diversified",
            "fp_finance",
            "fp_real_estate",
        ],
    },
    "energy_industrials": {
        "name": "Enerji & Sanayi",
        "name_en": "Energy & Industrials",
        "icon": "⚙️",
        "description": "Petrol & gaz, yenilenebilir enerji, sanayi, savunma, altyapı & kamu hizmetleri",
        "category": "Sektör",
        "sources": [
            "energy_oil",
            "energy_renewable",
            "industrials",
            "space_defense",
            "fp_energy",
            "fp_industrials",
            "fp_utilities",
        ],
    },
    "consumer": {
        "name": "Tüketici",
        "name_en": "Consumer",
        "icon": "🛒",
        "description": "Perakende, restoran, turizm, ihtiyari ve temel tüketim",
        "category": "Sektör",
        "sources": [
            "consumer_retail",
            "fp_consumer_discretionary",
            "fp_consumer_staples",
        ],
    },
    "growth_thematic": {
        "name": "Büyüme & Tematik",
        "name_en": "Growth & Thematic",
        "icon": "🚀",
        "description": "Yapay zeka, elektrikli araç, kripto & blockchain, uzay, momentum & çeşitli",
        "category": "Strateji",
        "sources": [
            "ai_leaders",
            "ev_mobility",
            "crypto_blockchain",
            "growth_momentum",
            "trending_momentum",
            "fp_miscellaneous",
        ],
    },
    "small_cap_growth": {
        "name": "Küçük Cap Büyüme",
        "name_en": "Small Cap Growth",
        "icon": "🌱",
        "description": "Russell 2000 küçük sermayeli büyüme şirketleri ($50M–$300M piyasa değeri)",
        "category": "Strateji",
        "sources": ["small_cap_growth"],
        # small_cap_growth will be refreshed from iwm_300m DB list post-enrich
    },
    "value_income": {
        "name": "Değer & Temettü",
        "name_en": "Value & Income",
        "icon": "💎",
        "description": "Düşük değerlemeli kaliteli şirketler ve yüksek temettü geliri (%4+)",
        "category": "Strateji",
        "sources": ["value_picks", "high_dividend"],
    },
    "international": {
        "name": "Uluslararası",
        "name_en": "International",
        "icon": "🌍",
        "description": "Çin ADR, İngiltere & Avrupa, küresel çeşitlilik",
        "category": "Bölgesel",
        "sources": ["uk_europe", "china_adr", "international_mix"],
    },
}


def get_tradable_set(db_path: Path) -> set[str]:
    if not db_path.exists():
        logger.warning("DB not found at %s — skipping validation", db_path)
        return set()
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute("SELECT ticker FROM symbols WHERE tradable=1").fetchall()
    return {r[0] for r in rows}


def get_iwm_300m_list(db_path: Path) -> list[str]:
    """Pull the iwm_300m list from symbol_lists if available."""
    if not db_path.exists():
        return []
    with sqlite3.connect(str(db_path)) as conn:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='symbol_lists'"
        ).fetchone()
        if not exists:
            return []
        rows = conn.execute(
            "SELECT ticker FROM symbol_lists WHERE list_name='iwm_300m' ORDER BY ticker"
        ).fetchall()
    return [r[0] for r in rows]


def consolidate(
    src_presets: dict,
    tradable: set[str],
    iwm_300m: list[str],
) -> dict:
    """Build new consolidated preset dict."""
    new_presets: dict[str, dict] = {}

    for new_key, meta in CONSOLIDATION.items():
        merged: dict[str, None] = {}  # ordered set via dict

        # Special case: small_cap_growth — prefer iwm_300m list from DB
        if new_key == "small_cap_growth" and iwm_300m:
            for sym in iwm_300m:
                merged[sym] = None
            logger.info("  small_cap_growth: %d symbols from iwm_300m DB list", len(merged))
        else:
            for src_key in meta["sources"]:
                src = src_presets.get(src_key, {})
                for sym in src.get("symbols", []):
                    sym = sym.strip().upper()
                    if sym:
                        merged[sym] = None

        # Validate against Alpaca tradable set
        if tradable:
            before = len(merged)
            merged = {s: None for s in merged if s in tradable}
            removed = before - len(merged)
            if removed:
                logger.info("  %s: removed %d delisted symbols", new_key, removed)

        symbols = list(merged.keys())
        logger.info("  %-22s %d symbols", new_key, len(symbols))

        new_presets[new_key] = {
            "name": meta["name"],
            "name_en": meta["name_en"],
            "icon": meta["icon"],
            "description": meta["description"],
            "category": meta["category"],
            "symbols": symbols,
        }

    return new_presets


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate stock_presets.json from 34 → 9")
    parser.add_argument("--dry-run", action="store_true", help="Print stats only, no writes")
    parser.add_argument("--stats", action="store_true", help="Show group sizes")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument(
        "--out-dir",
        default=None,
        help="Write output files to this directory instead of default paths (useful when in-place write is not permitted)",
    )
    args = parser.parse_args()

    if not PRESETS_SRC.exists():
        logger.error("Source presets not found: %s", PRESETS_SRC)
        return 1

    src = json.loads(PRESETS_SRC.read_text(encoding="utf-8"))
    logger.info("Source: %d presets loaded from %s", len(src), PRESETS_SRC)

    tradable = get_tradable_set(Path(args.db))
    logger.info("Tradable symbols in DB: %d", len(tradable))

    iwm_300m = get_iwm_300m_list(Path(args.db))
    if iwm_300m:
        logger.info("iwm_300m list from DB: %d symbols", len(iwm_300m))
    else:
        logger.warning(
            "iwm_300m list not found in DB — small_cap_growth will use existing preset symbols. "
            "Run enrich_market_caps.py first for best results."
        )

    logger.info("\nConsolidating %d → %d presets:", len(src), len(CONSOLIDATION))
    new_presets = consolidate(src, tradable, iwm_300m)

    total_old = sum(len(v.get("symbols", [])) for v in src.values())
    total_new = sum(len(v["symbols"]) for v in new_presets.values())
    unique_new = len({s for v in new_presets.values() for s in v["symbols"]})

    print(f"\n{'─' * 55}")
    print(f"  Old presets : {len(src):>4}  ({total_old} total symbol refs)")
    print(f"  New presets : {len(new_presets):>4}  ({total_new} total symbol refs)")
    print(f"  Unique syms : {unique_new:>4}")
    print(f"\n  {'Group':<25} {'Symbols':>7}")
    print(f"  {'-' * 25} {'-' * 7}")
    for key, preset in new_presets.items():
        print(f"  {key:<25} {len(preset['symbols']):>7}")
    print(f"{'─' * 55}\n")

    if args.dry_run or args.stats:
        logger.info("Dry run — no files written")
        return 0

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        dest_data = out_dir / "stock_presets.json"
        dest_web = out_dir / "stock_presets_web.json"
    else:
        dest_data = PRESETS_SRC
        dest_web = PRESETS_WEB
        dest_web.parent.mkdir(parents=True, exist_ok=True)

    out = json.dumps(new_presets, ensure_ascii=False, indent=2)
    dest_data.write_text(out, encoding="utf-8")
    logger.info("Written: %s", dest_data)

    dest_web.write_text(out, encoding="utf-8")
    logger.info("Written: %s", dest_web)

    return 0


if __name__ == "__main__":
    sys.exit(main())
