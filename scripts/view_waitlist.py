#!/usr/bin/env python3
"""
FinPilot Waitlist Viewer
========================

View and export collected email addresses from the waitlist.

Usage:
    python scripts/view_waitlist.py           # Show all entries
    python scripts/view_waitlist.py --export  # Export to CSV
    python scripts/view_waitlist.py --count   # Just show count
"""

import json
import argparse
import csv
from pathlib import Path
from datetime import datetime

WAITLIST_FILE = Path("data/waitlist.json")


def load_waitlist() -> list:
    """Load waitlist from JSON file."""
    if not WAITLIST_FILE.exists():
        print("❌ Waitlist file not found: data/waitlist.json")
        return []
    
    with open(WAITLIST_FILE, "r") as f:
        return json.load(f)


def show_waitlist(entries: list) -> None:
    """Display waitlist entries."""
    if not entries:
        print("📭 Waitlist is empty.")
        return
    
    print(f"\n📧 FinPilot Waitlist ({len(entries)} entries)")
    print("=" * 70)
    print(f"{'#':<4} {'Email':<35} {'Name':<15} {'Source':<10} {'Date'}")
    print("-" * 70)
    
    for i, entry in enumerate(entries, 1):
        email = entry.get("email", "")[:33]
        name = entry.get("name", "-")[:13] or "-"
        source = entry.get("source", "demo")[:8]
        timestamp = entry.get("timestamp", "")[:10]
        
        print(f"{i:<4} {email:<35} {name:<15} {source:<10} {timestamp}")
    
    print("-" * 70)
    print(f"Total: {len(entries)} subscribers")


def export_to_csv(entries: list, filename: str = None) -> str:
    """Export waitlist to CSV file."""
    if not entries:
        print("📭 Waitlist is empty, nothing to export.")
        return ""
    
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/waitlist_export_{timestamp}.csv"
    
    Path(filename).parent.mkdir(exist_ok=True)
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["email", "name", "source", "timestamp", "language"])
        writer.writeheader()
        writer.writerows(entries)
    
    print(f"✅ Exported {len(entries)} entries to: {filename}")
    return filename


def show_stats(entries: list) -> None:
    """Show waitlist statistics."""
    if not entries:
        print("📭 Waitlist is empty.")
        return
    
    # Count by source
    sources = {}
    for entry in entries:
        src = entry.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    
    # Count by language
    languages = {}
    for entry in entries:
        lang = entry.get("language", "en")
        languages[lang] = languages.get(lang, 0) + 1
    
    print(f"\n📊 Waitlist Statistics")
    print("=" * 40)
    print(f"Total subscribers: {len(entries)}")
    print(f"\nBy source:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  - {src}: {count}")
    print(f"\nBy language:")
    for lang, count in sorted(languages.items(), key=lambda x: -x[1]):
        lang_name = {"en": "English", "de": "Deutsch", "tr": "Türkçe"}.get(lang, lang)
        print(f"  - {lang_name}: {count}")


def main():
    parser = argparse.ArgumentParser(description="View FinPilot waitlist")
    parser.add_argument("--export", action="store_true", help="Export to CSV")
    parser.add_argument("--count", action="store_true", help="Show only count")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()
    
    entries = load_waitlist()
    
    if args.count:
        print(f"📧 Waitlist count: {len(entries)}")
    elif args.export:
        export_to_csv(entries)
    elif args.stats:
        show_stats(entries)
    else:
        show_waitlist(entries)
        if entries:
            print("\nTip: Use --export to save as CSV, --stats for statistics")


if __name__ == "__main__":
    main()
