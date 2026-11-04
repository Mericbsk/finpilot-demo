"""DQ role: read-only structural inspection of a scan export JSON.

Usage: python -B dq_inspect_export.py <path-to-export.json>
Prints top-level keys, row count, row key frequencies and a few sample values.
No network, no writes.
"""
import collections
import hashlib
import json
import sys


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(path):
    print("FILE", path)
    print("SHA256", sha256(path))
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    print("TYPE", type(data).__name__)
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (list, dict)):
                print("TOP", k, type(v).__name__, len(v))
            else:
                print("TOP", k, repr(v)[:200])
        rows = None
        for key in ("results", "rows", "data", "signals"):
            if isinstance(data.get(key), list):
                rows = data[key]
                print("ROWS_KEY", key)
                break
            if isinstance(data.get(key), dict):
                rows = list(data[key].values())
                print("ROWS_KEY(dict)", key)
                break
    else:
        rows = data
    if not rows:
        print("NO ROWS")
        return
    print("N_ROWS", len(rows))
    freq = collections.Counter()
    for r in rows:
        if isinstance(r, dict):
            freq.update(r.keys())
    for k, c in sorted(freq.items(), key=lambda x: (-x[1], x[0])):
        print("KEY", c, k)
    r0 = rows[0]
    for k in sorted(r0.keys()):
        v = r0[k]
        print("SAMPLE", k, repr(v)[:160])


if __name__ == "__main__":
    main(sys.argv[1])
