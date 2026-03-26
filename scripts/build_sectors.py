#!/usr/bin/env python3
"""
Build sector data files from CSV sources.

Reads all .csv files in data/tickers/sectors/ and generates:
- sector_index.json  (master index with metadata + full symbol lists)
- {sector}.txt       (one symbol per line)

Usage:
    python scripts/build_sectors.py
"""

import csv
import json
import os
from pathlib import Path

SECTOR_DIR = Path("data/tickers/sectors")

# Sector metadata (Turkish names, icons, descriptions)
SECTOR_META = {
    "consumer_discretionary": {
        "name": "Tüketici İhtiyari",
        "icon": "🛍️",
        "description": "Otomobil, perakende, otelcilik, medya — NASDAQ ihtiyari tüketim",
    },
    "consumer_staples": {
        "name": "Temel Tüketim",
        "icon": "🛒",
        "description": "İçecek, gıda, tüketim ürünleri — NASDAQ sektör tarama",
    },
    "energy": {
        "name": "Enerji",
        "icon": "⚡",
        "description": "Petrol, gaz, yenilenebilir, kömür — NASDAQ sektör tarama",
    },
    "finance": {
        "name": "Finans",
        "icon": "🏦",
        "description": "Bankacılık, brokerage, sigorta, fintech — NASDAQ sektör tarama",
    },
    "health_care": {
        "name": "Sağlık",
        "icon": "💊",
        "description": "Biyotek, medikal cihaz, ilaç — NASDAQ sektör tarama",
    },
    "industrials": {
        "name": "Sanayi",
        "icon": "🏭",
        "description": "Havacılık, savunma, lojistik, üretim — NASDAQ sektör tarama",
    },
    "miscellaneous": {
        "name": "Enerji Depolama & Çeşitli",
        "icon": "🔋",
        "description": "Batarya, enerji depolama, çok sektörlü — NASDAQ sektör tarama",
    },
    "real_estate": {
        "name": "Gayrimenkul & Platformlar",
        "icon": "🏠",
        "description": "REIT, e-ticaret, gayrimenkul platformları — NASDAQ sektör tarama",
    },
    "technology": {
        "name": "Teknoloji",
        "icon": "💻",
        "description": "Yarı iletken, yazılım, siber güvenlik — NASDAQ sektör tarama",
    },
    "telecommunications": {
        "name": "Telekomünikasyon",
        "icon": "📡",
        "description": "Kablo, uydu, iletişim ekipmanları — NASDAQ sektör tarama",
    },
    "utilities": {
        "name": "Altyapı Hizmetleri",
        "icon": "🔌",
        "description": "Elektrik, su, doğalgaz dağıtım — NASDAQ sektör tarama",
    },
}


def extract_symbols_from_csv(csv_path: Path) -> list[str]:
    """Extract Symbol column from a CSV file, preserving order."""
    symbols = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sym = row.get("Symbol", "").strip()
            if sym:
                symbols.append(sym)
    return symbols


def build_all():
    """Main build function."""
    csv_files = sorted(SECTOR_DIR.glob("*.csv"))
    if not csv_files:
        print("❌ No CSV files found in", SECTOR_DIR)
        return

    index = {}
    total_symbols = 0

    for csv_path in csv_files:
        sector_key = csv_path.stem  # e.g. "technology"
        symbols = extract_symbols_from_csv(csv_path)
        count = len(symbols)
        total_symbols += count

        # Write .txt file
        txt_path = SECTOR_DIR / f"{sector_key}.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(symbols) + "\n")

        # Build index entry
        meta = SECTOR_META.get(sector_key, {})
        index[sector_key] = {
            "name": meta.get("name", sector_key.replace("_", " ").title()),
            "icon": meta.get("icon", "📊"),
            "description": meta.get("description", ""),
            "file": f"{sector_key}.txt",
            "csv_file": f"{sector_key}.csv",
            "symbol_count": count,
            "symbols": symbols,
        }

        print(f"  ✅ {sector_key}: {count} symbols → {txt_path.name}")

    # Write sector_index.json
    index_path = SECTOR_DIR / "sector_index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    unique = len({s for entry in index.values() for s in entry["symbols"]})
    print(f"\n📊 Toplam: {len(index)} sektör, {total_symbols} sembol ({unique} benzersiz)")
    print(f"📁 Index: {index_path}")


if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent.parent)
    print("🔨 Building sector data files...\n")
    build_all()
    print("\n✅ Done!")
