"""System health check script — run inside or outside container."""

import json
import sys
import urllib.error
import urllib.request

BASE = "http://localhost:8000/api/v1"
results = {}


def req(method, path, data=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=10)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {}
        return e.code, body
    except Exception as ex:
        return 0, str(ex)


# 1. Health
s, d = req("GET", "/ready")
results["health"] = "OK" if s == 200 else "FAIL %d" % s

# 2. Login
s, d = req("POST", "/auth/login", {"email": "meric@finpilot.io", "password": "FinPilot2026!"})
token = d.get("access_token", "")
results["login"] = ("OK (token: %s...)" % token[:20]) if token else ("FAIL %d" % s)

# 3. /me
s, d = req("GET", "/auth/me", token=token)
results["me"] = ("OK (%s)" % d.get("email", "?")) if s == 200 else "FAIL %d" % s

# 4. Registry audit
s, d = req("GET", "/agent/registry/audit", token=token)
ok = d.get("ok")
dc = d.get("discovered_count")
rac = d.get("registered_active_count")
drift_in = len(d.get("in_code_not_registry", []))
drift_out = len(d.get("in_registry_not_code", []))
results["registry_audit"] = (
    (
        "OK (ok=%s, discovered=%s, active=%s, drift_in=%d, drift_out=%d)"
        % (ok, dc, rac, drift_in, drift_out)
    )
    if s == 200
    else "FAIL %d" % s
)

# 5. Scan (2 symbols)
s, d = req("POST", "/scan", {"symbols": ["AAPL", "MSFT"], "strategy": "momentum"}, token=token)
if s == 200 and isinstance(d, list) and d:
    r0 = d[0]
    cs = r0.get("composite_score")
    sr = r0.get("sharpe_ratio")
    ds = r0.get("dyn_shares")
    results["scan"] = "OK (%d results | score=%s sharpe=%s dynshares=%s)" % (len(d), cs, sr, ds)
else:
    results["scan"] = "FAIL %d / %s" % (s, str(d)[:100])

# 6. Signal events
s, d = req("GET", "/agent/signal-events?limit=5", token=token)
cnt = len(d) if isinstance(d, list) else d.get("count", "?")
results["signal_events"] = ("OK (%s events)" % cnt) if s == 200 else "FAIL %d" % s

# 7. Trade broker (expect 503)
s, d = req("GET", "/trade/account", token=token)
results["trade_broker"] = (
    ("OK (graceful 503: %s)" % str(d.get("detail", ""))[:50]) if s == 503 else "FAIL %d" % s
)

# 8. Waitlist endpoint
s, d = req("POST", "/waitlist", {"email": "syscheck@finpilot.io"})
results["waitlist"] = "OK" if s in (200, 201, 409) else "FAIL %d" % s

# 9. Watchlist read
s, d = req("GET", "/watchlist", token=token)
wl_count = len(d) if isinstance(d, list) else d.get("count", "?")
results["watchlist"] = ("OK (%s items)" % wl_count) if s == 200 else "FAIL %d" % s

# 10. Market data
s, d = req("GET", "/market-data/price/AAPL")
results["market_data"] = ("OK (price=%s)" % d.get("price")) if s == 200 else "FAIL %d" % s

# Print
print()
print("=" * 60)
print("  FINPILOT SYSTEM HEALTH CHECK  -  2026-06-16")
print("=" * 60)
any_fail = False
for k, v in results.items():
    icon = "✓" if v.startswith("OK") else "✗"
    if not v.startswith("OK"):
        any_fail = True
    print("  %s  %-22s %s" % (icon, k, v))
print("=" * 60)
print("  Overall: %s" % ("ALL OK" if not any_fail else "ISSUES FOUND"))
print()
sys.exit(1 if any_fail else 0)
