import glob
import json

files = sorted(glob.glob("/app/data/signal_archive/*.json"))
print("archive files:", len(files))
syms = set()
total = 0
for f in files:
    try:
        data = json.load(open(f))
        if isinstance(data, list):
            total += len(data)
            for i in data:
                if isinstance(i, dict):
                    syms.add(i.get("symbol", ""))
    except Exception as e:
        print("ERR", f, e)
print("total items:", total)
print("unique symbols:", len(syms))
print("sample:", list(syms)[:10])
