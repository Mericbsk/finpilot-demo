"""DQ role: read-only schema probe of data/finpilot.db (symbols/symbol_lists tables).

Opens SQLite strictly read-only (mode=ro + PRAGMA query_only=ON). No writes.
"""
import sqlite3

DB = "file:C:/Users/meric/Borsa/data/finpilot.db?mode=ro"


def main():
    con = sqlite3.connect(DB, uri=True)
    con.execute("PRAGMA query_only=ON")
    tabs = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("TABLES", len(tabs))
    for t in tabs:
        try:
            n = con.execute('SELECT COUNT(*) FROM "%s"' % t.replace('"', '')).fetchone()[0]
        except Exception as exc:  # noqa: BLE001
            n = "ERR %s" % exc
        print("TABLE", t, n)
    for t in ("symbols", "symbol_lists"):
        if t in tabs:
            cols = con.execute('PRAGMA table_info("%s")' % t).fetchall()
            print("COLS", t, [(c[1], c[2]) for c in cols])
            for row in con.execute('SELECT * FROM "%s" LIMIT 3' % t):
                print("ROW", t, row)
    if "symbols" in tabs:
        cols = [c[1] for c in con.execute('PRAGMA table_info("symbols")')]
        for c in ("exchange", "asset_class", "tradable", "status"):
            if c in cols:
                print("DIST", c, con.execute('SELECT %s, COUNT(*) FROM symbols GROUP BY %s ORDER BY 2 DESC' % (c, c)).fetchall()[:20])
        if "market_cap" in cols:
            print("MCAP_NULL", con.execute("SELECT SUM(market_cap IS NULL), COUNT(*) FROM symbols").fetchone())
        for c in ("updated_at", "synced_at", "last_updated", "created_at"):
            if c in cols:
                print("TS", c, con.execute('SELECT MIN(%s), MAX(%s) FROM symbols' % (c, c)).fetchone())
    if "symbol_lists" in tabs:
        print("LISTS", con.execute("SELECT list_name, COUNT(*) FROM symbol_lists GROUP BY list_name").fetchall())
    con.close()


if __name__ == "__main__":
    main()
