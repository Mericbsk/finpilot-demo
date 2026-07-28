"""Render a distribution preview without queueing or publishing anything."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from distribution import templates
from distribution.concepts import concept_of_the_day
from distribution.jobs import _fetch_karne, _vienna_now
from distribution.market_context import build_context_line
from distribution.prepublish_gate import check_export_health
from distribution.schema import demo_view, validate_snapshot
from distribution.snapshot_builder import (
    SCAN_EXPORT_LATEST,
    build_snapshot,
    load_scan_export_record,
    validate_scan_export,
)


def build_preview() -> dict:
    """Build Telegram and web projections without publication side effects."""
    export = load_scan_export_record(SCAN_EXPORT_LATEST)
    contract_problems = validate_scan_export(export)
    health_problems = check_export_health(export)
    if contract_problems or health_problems:
        problems = list(dict.fromkeys(contract_problems + health_problems))
        raise ValueError("pre-publish gate: " + "; ".join(problems))

    today = _vienna_now().date()
    date_str = str(export.get("date") or "")
    if date_str != today.isoformat():
        raise ValueError(f"scan export is stale: {date_str} != {today.isoformat()}")

    rows = export.get("results", [])
    universe = int(export.get("universe") or len(rows))
    scan_id = export.get("scan_id")
    karne = _fetch_karne()
    snapshot_tr = build_snapshot(
        rows, universe=universe, karne=karne, date_str=date_str, scan_id=scan_id
    )
    snapshot_en = build_snapshot(
        rows,
        universe=universe,
        karne=karne,
        date_str=date_str,
        lang="en",
        scan_id=scan_id,
    )
    if snapshot_tr.get("snapshot_id") != snapshot_en.get("snapshot_id"):
        raise ValueError("Turkish and English snapshot identities differ")

    snapshot_problems = validate_snapshot(snapshot_tr)
    if snapshot_problems:
        raise ValueError("snapshot validation: " + "; ".join(snapshot_problems))

    telegram_text = templates.render_daily_free(
        snapshot_tr,
        concept_line=concept_of_the_day(today),
        context_line=build_context_line("tr"),
    )
    web_public = demo_view(snapshot_en, max_candidates=len(snapshot_en.get("candidates", [])))
    return {
        "date": date_str,
        "scan_id": scan_id,
        "universe": universe,
        "result_count": len(rows),
        "snapshot_id": snapshot_tr.get("snapshot_id"),
        "candidate_count": len(snapshot_tr.get("candidates", [])),
        "warnings": snapshot_tr.get("warnings", []),
        "telegram_text": telegram_text,
        "web_public": web_public,
    }


def render_markdown(preview: dict) -> str:
    """Render a human-reviewable preview document."""
    web = preview["web_public"]
    context = web.get("web_context", [])
    lines = [
        "# FinPilot Publication Preview",
        "",
        f"- Date: `{preview['date']}`",
        f"- Scan ID: `{preview.get('scan_id')}`",
        f"- Snapshot ID: `{preview['snapshot_id']}`",
        f"- Universe: `{preview['universe']}`; results: `{preview['result_count']}`",
        f"- Candidates: `{preview['candidate_count']}`",
        "- Status: `PREVIEW ONLY - NOT PUBLISHED`",
        "",
        "## Telegram Draft",
        "",
        preview["telegram_text"],
        "",
        "## Web Preview",
        "",
        "### Graded Candidate",
        "",
    ]
    if web.get("candidates"):
        for candidate in web["candidates"]:
            lines.extend(
                [
                    f"- **{candidate.get('ticker')}** — {candidate.get('company', '')} · Grade {candidate.get('grade')} · {candidate.get('prob_band')}",
                    f"  {candidate.get('rationale', '')}",
                    f"  Metrics: {json.dumps(candidate.get('metrics', {}), ensure_ascii=False, default=str)}",
                ]
            )
    else:
        lines.append("- No graded candidate")
    lines.extend(
        [
            "",
            "### Web Scan Context",
            "",
            f"The web view includes {len(context)} measurable scan-context names. These are not graded candidates.",
        ]
    )
    for candidate in context:
        lines.extend(
            [
                f"- **{candidate.get('rank')}. {candidate.get('ticker')}** — {candidate.get('company', '')}",
                f"  {candidate.get('rationale', '')}",
                f"  Metrics: {json.dumps(candidate.get('metrics', {}), ensure_ascii=False, default=str)}",
            ]
        )
    lines.extend(
        [
            "",
            "### Web Snapshot JSON",
            "",
            "```json",
            json.dumps(web, ensure_ascii=False, indent=2, default=str),
            "```",
            "",
            "## Warnings",
            "",
        ]
    )
    warnings = preview.get("warnings") or []
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def render_web_html(preview: dict) -> str:
    """Render the public web projection as a local, non-published HTML preview."""
    web = preview["web_public"]
    candidates = web.get("candidates", [])
    cards = []
    for candidate in candidates:
        ticker = html.escape(str(candidate.get("ticker", "")))
        company = html.escape(str(candidate.get("company", "")))
        grade = html.escape(str(candidate.get("grade", "")))
        band = html.escape(str(candidate.get("prob_band", "—")))
        rationale = html.escape(str(candidate.get("rationale", "")))
        badges = "".join(
            f'<span class="badge">{html.escape(str(badge))}</span>'
            for badge in candidate.get("badges", [])
        )
        cards.append(
            '<article class="candidate">'
            f'<div class="seal">{grade}</div>'
            '<div class="candidate-body">'
            f'<p class="eyebrow">{ticker} · {company}</p>'
            f"<h2>Why is it here today?</h2><p>{rationale}</p>"
            f'<p class="band">Historical profile band: <strong>{band}</strong></p>'
            f'<div class="badges">{badges}</div>'
            '<p class="question">Question to watch: will this picture hold for several sessions?</p>'
            "</div></article>"
        )
    if not cards:
        cards.append("<p>Bugün eşik üstünde aday yok. Sessiz bir gün de veridir.</p>")
    context_cards = []
    for item in web.get("web_context", []):
        ticker = html.escape(str(item.get("ticker", "")))
        company = html.escape(str(item.get("company", "")))
        rationale = html.escape(str(item.get("rationale", "")))
        metrics = item.get("metrics", {})
        price = metrics.get("price")
        momentum = metrics.get("momentum_3d_pct")
        volume = metrics.get("volume_multiple")
        context_cards.append(
            "<article class=\"context-card\">"
            f"<p class=\"eyebrow\">#{html.escape(str(item.get('rank', '')))} · {ticker} · {company}</p>"
            f"<p>{rationale}</p>"
            f"<p class=\"metrics\">Price {html.escape(str(price))} · 3d momentum {html.escape(str(momentum))}% · Volume {html.escape(str(volume))}x</p>"
            "</article>"
        )
    date = html.escape(str(preview["date"]))
    snapshot_id = html.escape(str(preview["snapshot_id"]))
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FinPilot Web Preview — {date}</title>
<style>
:root {{ color-scheme: light; --ink:#1b1c1d; --muted:#6b6d6e; --rule:#d9d4c8; --gold:#a47724; --paper:#f8f5ed; }}
* {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font-family: Georgia, serif; }}
main {{ max-width:760px; margin:0 auto; padding:48px 22px 72px; }}
.preview {{ border:1px solid #b47b2a; padding:10px 14px; color:#8a5c16; font:12px/1.4 ui-monospace,monospace; letter-spacing:.08em; text-transform:uppercase; }}
header {{ padding:32px 0 22px; border-bottom:2px solid var(--ink); }} h1 {{ margin:0 0 8px; font-size:clamp(34px,7vw,58px); line-height:.95; }}
.meta,.eyebrow,.band {{ color:var(--muted); font:12px/1.5 ui-monospace,monospace; letter-spacing:.05em; }}
.candidate {{ display:flex; gap:18px; padding:34px 0; border-bottom:1px solid var(--rule); }} .seal {{ flex:none; width:52px; height:52px; border:1px solid var(--gold); display:grid; place-items:center; color:var(--gold); font-weight:bold; }}
.candidate-body {{ flex:1; }} h2 {{ margin:4px 0 10px; font-size:25px; }} .candidate-body p {{ font-size:18px; line-height:1.55; }}
.band {{ margin-top:18px; }} .badges {{ display:flex; flex-wrap:wrap; gap:7px; }} .badge {{ border:1px solid var(--rule); padding:5px 8px; font:11px ui-monospace,monospace; text-transform:uppercase; }}
.question {{ padding-top:8px; color:#76591f; font-style:italic; }} footer {{ margin-top:28px; color:var(--muted); font:12px/1.5 ui-monospace,monospace; }}
.context-card {{ padding:18px 0; border-bottom:1px solid var(--rule); }} .context-card p {{ margin:7px 0; font-size:16px; line-height:1.45; }} .metrics {{ color:var(--muted); font:11px/1.5 ui-monospace,monospace !important; }}
</style></head><body><main>
<div class="preview">Önizleme · yayınlanmadı</div>
<header><h1>FinPilot Daily Ledger</h1><div class="meta">{date} · {html.escape(str(web.get("universe", 0)))} hisse tarandı · snapshot {snapshot_id}</div></header>
<section><p class="eyebrow">Today's lead file</p>{''.join(cards)}</section>
<section><p class="eyebrow">Scan context · not graded candidates</p>{''.join(context_cards)}</section>
<footer>This is a local preview. For research and education only; not investment advice.</footer>
</main></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="also write the preview markdown to this local path",
    )
    parser.add_argument(
        "--web-output",
        type=Path,
        help="also write a local browser-ready web publication preview",
    )
    args = parser.parse_args()

    try:
        preview = build_preview()
        markdown = render_markdown(preview)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"PREVIEW FAILED: {exc}", file=sys.stderr)
        return 1

    print(markdown)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(f"Preview written to {args.output}", file=sys.stderr)
    if args.web_output:
        args.web_output.parent.mkdir(parents=True, exist_ok=True)
        args.web_output.write_text(render_web_html(preview), encoding="utf-8")
        print(f"Web preview written to {args.web_output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
