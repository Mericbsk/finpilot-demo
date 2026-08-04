#!/usr/bin/env python3
"""FinPilot repo-native ortak beyin — Work Item / Handoff / Evidence CLI.

Yalnizca standart kutuphane. Windows/PowerShell uyumlu. Kayitlar .finpilot/ altinda
JSON'dur (v1). Amac: Copilot, Claude Code, Cowork ve Meric'in AYNI is durumunu
tek yerden gormesi.

Komutlar:
    validate [--all | <path>]        semalara + secret/redaksiyon kurallarina gore dogrula
    list [--status S] [--owner O]    work item ozetleri
    show <WI-ID>                     bir work item + handoff + evidence
    active                           in_progress/review/blocked isler
    create-wi --title T --owner O --level {A,B,C} [--requested-by R]
    handoff --wi WI --from A --to B --summary S [--next N]
    transition <WI-ID> <status> [--approved]
    accept <HO-ID>

Level guard: Level B/C is, --approved (insan onayi) olmadan 'done' olamaz.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from datetime import UTC, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FP = os.path.join(ROOT, ".finpilot")
DIRS = {
    "work-item": os.path.join(FP, "work-items"),
    "handoff": os.path.join(FP, "handoffs"),
    "evidence": os.path.join(FP, "evidence"),
}
SCHEMAS = os.path.join(FP, "schemas")

STATUSES = ["proposed", "ready", "in_progress", "blocked", "review", "done", "cancelled"]
# izin verilen durum gecisleri
TRANSITIONS = {
    "proposed": {"ready", "cancelled"},
    "ready": {"in_progress", "cancelled"},
    "in_progress": {"blocked", "review", "cancelled"},
    "blocked": {"in_progress", "cancelled"},
    "review": {"in_progress", "done", "cancelled"},
    "done": set(),
    "cancelled": set(),
}

# Secret/redaksiyon: bu desenler hicbir kayitta bulunmamali (fail-closed).
SECRET_KEY_RE = re.compile(
    r"(secret|token|password|passwd|api[_-]?key|private[_-]?key|credential)", re.I
)
SECRET_VAL_RE = re.compile(
    r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,})"
)


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(path: str, obj: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _schema(kind: str) -> dict:
    return _load(os.path.join(SCHEMAS, f"{kind}.schema.json"))


def _kind_of(path: str) -> str:
    p = path.replace("\\", "/")
    if "/work-items/" in p:
        return "work-item"
    if "/handoffs/" in p:
        return "handoff"
    if "/evidence/" in p:
        return "evidence"
    return "work-item"


def _secret_scan(obj, trail="") -> list[str]:
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if SECRET_KEY_RE.search(str(k)):
                hits.append(f"{trail}.{k}: secret-benzeri ALAN ADI")
            hits += _secret_scan(v, f"{trail}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += _secret_scan(v, f"{trail}[{i}]")
    elif isinstance(obj, str):
        if SECRET_VAL_RE.search(obj):
            hits.append(f"{trail}: secret-benzeri DEGER")
    return hits


def _validate_obj(obj: dict, schema: dict) -> list[str]:
    errs = []
    # unknown schema version -> fail-closed
    if obj.get("schema_version") != 1:
        errs.append(f"schema_version {obj.get('schema_version')!r} desteklenmiyor (v1 bekleniyor)")
    props = schema.get("properties", {})
    for req in schema.get("required", []):
        if req not in obj:
            errs.append(f"zorunlu alan eksik: {req}")
    for key, val in obj.items():
        spec = props.get(key)
        if not spec:
            continue
        if "enum" in spec and val not in spec["enum"]:
            errs.append(f"{key}={val!r} enum disi ({spec['enum']})")
        if "const" in spec and val != spec["const"]:
            errs.append(f"{key}={val!r} sabit degil ({spec['const']})")
        if "pattern" in spec and isinstance(val, str) and not re.match(spec["pattern"], val):
            errs.append(f"{key}={val!r} desene uymuyor ({spec['pattern']})")
        t = spec.get("type")
        if t == "string" and not isinstance(val, str):
            errs.append(f"{key} string olmali")
        if t == "array" and not isinstance(val, list):
            errs.append(f"{key} array olmali")
    errs += _secret_scan(obj)
    return errs


def cmd_validate(args) -> int:
    if args.path:
        paths = [args.path]
    else:
        paths = sorted(glob.glob(os.path.join(FP, "**", "*.json"), recursive=True))
        paths = [
            p
            for p in paths
            if not any(
                x in p.replace("\\", "/")
                for x in ("/schemas/", "/templates/", "/inbox/", "/outbox/")
            )
        ]
    total_err = 0
    for p in paths:
        try:
            obj = _load(p)
        except Exception as e:
            print(f"HATA {p}: okunamadi ({e})")
            total_err += 1
            continue
        errs = _validate_obj(obj, _schema(_kind_of(p)))
        rel = os.path.relpath(p, ROOT)
        if errs:
            total_err += len(errs)
            print(f"GECERSIZ {rel}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"OK       {rel}")
    print(f"\n{'BASARILI' if total_err == 0 else 'BASARISIZ'}: {total_err} hata")
    return 0 if total_err == 0 else 1


def _all_wi() -> list[dict]:
    return [_load(p) for p in sorted(glob.glob(os.path.join(DIRS["work-item"], "*.json")))]


def cmd_list(args) -> int:
    items = _all_wi()
    for wi in items:
        if args.status and wi.get("status") != args.status:
            continue
        if args.owner and wi.get("owner") != args.owner:
            continue
        print(
            f"{wi['work_item_id']}  [{wi['status']:<11}] L{wi['decision_level']}  "
            f"{wi.get('owner', ''):<16} {wi['title']}"
        )
    return 0


def cmd_active(args) -> int:
    args.status = None
    args.owner = None
    for wi in _all_wi():
        if wi.get("status") in ("in_progress", "review", "blocked"):
            print(f"{wi['work_item_id']}  [{wi['status']}]  {wi.get('owner', '')}  {wi['title']}")
    return 0


def cmd_show(args) -> int:
    wid = args.wi_id
    wp = os.path.join(DIRS["work-item"], f"{wid}.json")
    if not os.path.exists(wp):
        print(f"bulunamadi: {wid}")
        return 1
    print(json.dumps(_load(wp), ensure_ascii=False, indent=2))
    for kind in ("handoff", "evidence"):
        for p in sorted(glob.glob(os.path.join(DIRS[kind], "*.json"))):
            o = _load(p)
            if o.get("work_item_id") == wid:
                print(
                    f"\n[{kind}] {os.path.basename(p)}: "
                    f"{o.get('state', o.get('outcome', ''))} — {o.get('summary', o.get('locator', ''))}"
                )
    return 0


def _next_id(prefix: str, directory: str) -> str:
    day = datetime.now(UTC).strftime("%Y%m%d")
    n = 1
    for p in glob.glob(os.path.join(directory, f"{prefix}-{day}-*.json")):
        try:
            n = max(n, int(os.path.basename(p).split("-")[2].split(".")[0]) + 1)
        except Exception:
            pass
    return f"{prefix}-{day}-{n:03d}"


def cmd_create_wi(args) -> int:
    wid = _next_id("WI", DIRS["work-item"])
    obj = {
        "schema_version": 1,
        "work_item_id": wid,
        "title": args.title,
        "status": "proposed",
        "owner": args.owner,
        "requested_by": args.requested_by,
        "decision_level": args.level,
        "authority_refs": ["AGENTS.md", "_instructions/00-core.md"],
        "decision_refs": [],
        "acceptance_criteria": [],
        "risk_flags": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    errs = _validate_obj(obj, _schema("work-item"))
    if errs:
        print("olusturulamadi:", errs)
        return 1
    _save(os.path.join(DIRS["work-item"], f"{wid}.json"), obj)
    print("olusturuldu:", wid)
    return 0


def cmd_handoff(args) -> int:
    hid = _next_id("HO", DIRS["handoff"])
    obj = {
        "schema_version": 1,
        "handoff_id": hid,
        "work_item_id": args.wi,
        "from_actor": getattr(args, "from"),
        "to_actor": args.to,
        "state": "ready",
        "summary": args.summary,
        "next_action": args.next or "",
        "blocked_by": [],
        "created_at": _now(),
    }
    errs = _validate_obj(obj, _schema("handoff"))
    if errs:
        print("olusturulamadi:", errs)
        return 1
    _save(os.path.join(DIRS["handoff"], f"{hid}.json"), obj)
    print("handoff:", hid, "->", args.to)
    return 0


def cmd_transition(args) -> int:
    wp = os.path.join(DIRS["work-item"], f"{args.wi_id}.json")
    if not os.path.exists(wp):
        print("bulunamadi:", args.wi_id)
        return 1
    wi = _load(wp)
    cur, new = wi["status"], args.status
    if new not in STATUSES:
        print("gecersiz durum:", new)
        return 1
    if new not in TRANSITIONS.get(cur, set()):
        print(f"gecersiz gecis: {cur} -> {new} (izinli: {sorted(TRANSITIONS.get(cur, set()))})")
        return 1
    # Level guard
    if new == "done" and wi["decision_level"] in ("B", "C") and not args.approved:
        print(
            f"REDDEDILDI: Level {wi['decision_level']} is Meric onayi (--approved) olmadan 'done' olamaz."
        )
        return 1
    if wi["decision_level"] == "C" and new == "done":
        print("REDDEDILDI: Level C 'done' insan tarafindan, ajan CLI'siyle degil.")
        return 1
    wi["status"] = new
    wi["updated_at"] = _now()
    _save(wp, wi)
    print(f"{args.wi_id}: {cur} -> {new}")
    return 0


def cmd_accept(args) -> int:
    hp = os.path.join(DIRS["handoff"], f"{args.ho_id}.json")
    if not os.path.exists(hp):
        print("bulunamadi:", args.ho_id)
        return 1
    ho = _load(hp)
    ho["state"] = "accepted"
    _save(hp, ho)
    wp = os.path.join(DIRS["work-item"], f"{ho['work_item_id']}.json")
    if os.path.exists(wp):
        wi = _load(wp)
        wi["owner"] = ho["to_actor"]
        wi["updated_at"] = _now()
        _save(wp, wi)
    print(f"{args.ho_id} accepted; {ho['work_item_id']} owner -> {ho['to_actor']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="handoff.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate")
    v.add_argument("path", nargs="?", default=None)
    v.add_argument("--all", action="store_true")
    v.set_defaults(fn=cmd_validate)
    li = sub.add_parser("list")
    li.add_argument("--status")
    li.add_argument("--owner")
    li.set_defaults(fn=cmd_list)
    sub.add_parser("active").set_defaults(fn=cmd_active)
    sh = sub.add_parser("show")
    sh.add_argument("wi_id")
    sh.set_defaults(fn=cmd_show)
    c = sub.add_parser("create-wi")
    c.add_argument("--title", required=True)
    c.add_argument("--owner", required=True)
    c.add_argument("--level", required=True, choices=["A", "B", "C"])
    c.add_argument("--requested-by", default="meric", dest="requested_by")
    c.set_defaults(fn=cmd_create_wi)
    h = sub.add_parser("handoff")
    h.add_argument("--wi", required=True)
    h.add_argument("--from", required=True)
    h.add_argument("--to", required=True)
    h.add_argument("--summary", required=True)
    h.add_argument("--next", default="")
    h.set_defaults(fn=cmd_handoff)
    t = sub.add_parser("transition")
    t.add_argument("wi_id")
    t.add_argument("status")
    t.add_argument("--approved", action="store_true")
    t.set_defaults(fn=cmd_transition)
    a = sub.add_parser("accept")
    a.add_argument("ho_id")
    a.set_defaults(fn=cmd_accept)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
