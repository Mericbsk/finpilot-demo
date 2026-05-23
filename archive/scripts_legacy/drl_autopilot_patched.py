#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║            DRL RESEARCH AUTOPILOT — FinPilot                        ║
║                                                                      ║
║  Tek komutla çalışan, hafızalı, kendini yöneten araştırma döngüsü.  ║
║                                                                      ║
║  Kullanım:                                                           ║
║    python scripts/drl_autopilot.py              # tam döngü         ║
║    python scripts/drl_autopilot.py --measure    # sadece ölçüm      ║
║    python scripts/drl_autopilot.py --analyze    # sadece analiz     ║
║    python scripts/drl_autopilot.py --report     # sadece rapor      ║
║    python scripts/drl_autopilot.py --top 5      # top N odak        ║
╚══════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime

UTC = UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ─────────────────────────────────────────────────────────────
# SABITLER
# ─────────────────────────────────────────────────────────────
REGISTRY_PATH = ROOT / "models" / "registry.json"
STATE_PATH = ROOT / "data" / "drl_research_state.json"
REPORTS_DIR = ROOT / "data" / "reports_cache"
OPTUNA_RESULTS = {
    "momentum": ROOT / "data" / "optuna_momentum_results.json",
    "conservative": ROOT / "data" / "optuna_conservative_results.json",
    "range": ROOT / "data" / "optuna_range_results.json",
    "swing": ROOT / "data" / "optuna_swing_results.json",
}
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# YARDIMCI: Zaman damgası
# ─────────────────────────────────────────────────────────────
def now_str() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def week_str() -> str:
    d = datetime.now()
    return f"{d.year}-W{d.isocalendar()[1]:02d}"


# ─────────────────────────────────────────────────────────────
# MODÜL 1: ÖLÇÜM
# Tüm modelleri registry'den okur, composite score hesaplar.
# ─────────────────────────────────────────────────────────────


def composite_score(sharpe: float, ret: float, dd: float, trades: int) -> float:
    """
    Composite skor formülü:
      score = (Sharpe × 10) + (Calmar × 0.3) - overtrading_penalty - negatif_ceza

    Calmar = Return / MaxDD  →  birim risk başına kazanç
    Overtrading: >400 trade → -0.3
    Negatif return → -1.0
    """
    if dd <= 0:
        dd = 0.001
    calmar = ret / dd
    overtrade_p = -0.3 if trades > 400 else 0.0
    neg_p = -1.0 if ret < 0 else 0.0
    return (sharpe * 10) + (calmar * 0.3) + overtrade_p + neg_p


def measure(registry_path: Path = REGISTRY_PATH) -> list[dict]:
    """
    Registry'deki tüm modelleri yükler, skorlar ve sıralar.
    Her model için sorun tespiti de yapar.
    """
    if not registry_path.exists():
        print(f"[HATA] Registry bulunamadı: {registry_path}")
        return []

    raw = json.loads(registry_path.read_text())
    models = []

    for mid, m in raw.items():
        metrics = m.get("metrics", {})
        hp = m.get("hyperparameters", {})
        rw = hp.get("reward_weights", {})

        sharpe = float(metrics.get("sharpe_ratio") or 0)
        ret = float(metrics.get("total_return") or 0)
        dd = float(metrics.get("max_drawdown") or 0.001)
        trades = int(metrics.get("n_trades") or 0)
        active = float(metrics.get("active_pct") or 0)

        score = composite_score(sharpe, ret, dd, trades)

        # Sorun tespiti
        issues = []
        if dd > 0.35:
            issues.append(
                {"type": "high_dd", "value": dd, "threshold": 0.35, "severity": "critical"}
            )
        if trades > 400:
            issues.append(
                {"type": "overtrading", "value": trades, "threshold": 400, "severity": "warning"}
            )
        if sharpe < 0.05:
            issues.append(
                {"type": "low_sharpe", "value": sharpe, "threshold": 0.05, "severity": "warning"}
            )
        if ret < 0:
            issues.append(
                {"type": "negative_return", "value": ret, "threshold": 0, "severity": "critical"}
            )
        if active > 99 and sharpe < 0.03:
            issues.append(
                {"type": "always_active", "value": active, "threshold": 99, "severity": "info"}
            )

        models.append(
            {
                "id": mid,
                "name": m.get("name", mid),
                "sharpe": sharpe,
                "return": ret,
                "dd": dd,
                "trades": trades,
                "active": active,
                "calmar": ret / dd,
                "score": score,
                "issues": issues,
                "hp": hp,
                "rw": rw,
                "created": m.get("created_at", ""),
            }
        )

    models.sort(key=lambda x: x["score"], reverse=True)
    return models


# ─────────────────────────────────────────────────────────────
# MODÜL 2: ANALİZ
# Top N modelin ortak zayıflıklarını ve kök nedenlerini bulur.
# ─────────────────────────────────────────────────────────────

# Reward weight önerme kuralları (sorun → öneri)
REWARD_RULES = [
    {
        "issue": "high_dd",
        "param": "dd_weight",
        "current": 0.3,
        "suggested": 0.8,
        "rationale": "MaxDD >35% → dd_weight artırılmalı (0.3→0.8). "
        "Model DD'yi görmezden geliyor çünkü ceza çok düşük.",
        "optuna_range": (0.5, 2.0),
    },
    {
        "issue": "overtrading",
        "param": "turnover_penalty",
        "current": 0.0,
        "suggested": 0.05,
        "rationale": "Trade sayısı >400 → turnover_penalty açılmalı (0→0.05). "
        "Aşırı işlem yapılıyor, her trade maliyet getiriyor.",
        "optuna_range": (0.02, 0.15),
    },
    {
        "issue": "low_sharpe",
        "param": "sharpe_bonus",
        "current": 0.0,
        "suggested": 0.1,
        "rationale": "Sharpe <0.07 → sharpe_bonus açılmalı (0→0.1). "
        "Risk-adjusted return doğrudan optimize edilmiyor.",
        "optuna_range": (0.05, 0.5),
    },
    {
        "issue": "negative_return",
        "param": "pnl_weight",
        "current": 10.0,
        "suggested": 8.0,
        "rationale": "Negatif return → pnl_weight düşürülüp regime_bonus açılabilir. "
        "Ajan yanlış rejimde pozisyon alıyor olabilir.",
        "optuna_range": (6.0, 15.0),
    },
]


def analyze(models: list[dict], top_n: int = 5) -> dict:
    """
    Top N modelin ortak sorunlarını tespit eder.
    Her sorun için öneri üretir.
    """
    top = models[:top_n]
    total = len(top)

    # Sorun frekansları
    issue_counts: dict[str, list[int]] = {}
    for i, m in enumerate(top, 1):
        for issue in m["issues"]:
            itype = issue["type"]
            issue_counts.setdefault(itype, []).append(i)

    # Yaygın sorunlar (>%50 oranında)
    common_issues = {k: v for k, v in issue_counts.items() if len(v) >= total * 0.5}

    # Öneriler üret
    recommendations = []
    for rule in REWARD_RULES:
        if rule["issue"] in common_issues:
            affected_models = common_issues[rule["issue"]]
            recommendations.append(
                {
                    "priority": 1 if rule["issue"] in ("high_dd", "negative_return") else 2,
                    "issue": rule["issue"],
                    "param": rule["param"],
                    "current": rule["current"],
                    "suggested": rule["suggested"],
                    "rationale": rule["rationale"],
                    "optuna_range": rule["optuna_range"],
                    "affects": f"{len(affected_models)}/{total} model (#{affected_models})",
                }
            )

    recommendations.sort(key=lambda x: x["priority"])

    # Optuna geçmiş sonuçlarını yükle
    optuna_insights = _load_optuna_insights()

    # Çeşitlilik analizi
    agent_types = {}
    for m in top:
        base = m["name"].split("_")[1] if "_" in m["name"] else m["name"]
        agent_types[base] = agent_types.get(base, 0) + 1

    diversity_warning = None
    if len(agent_types) < 3:
        dominant = max(agent_types, key=agent_types.get)
        diversity_warning = (
            f"Top {top_n} içinde yalnızca {len(agent_types)} farklı ajan türü var. "
            f"'{dominant}' baskın ({agent_types[dominant]}/{top_n}). "
            "Ensemble için çeşitlilik önerisi: conservative veya swing modeli ekle."
        )

    return {
        "top_n": top_n,
        "common_issues": common_issues,
        "recommendations": recommendations,
        "optuna_insights": optuna_insights,
        "diversity_warning": diversity_warning,
        "agent_type_dist": agent_types,
        "analyzed_at": now_str(),
    }


def _load_optuna_insights() -> dict:
    """Mevcut Optuna sonuçlarından öğrenilenleri özetle."""
    insights = {}
    for agent, path in OPTUNA_RESULTS.items():
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text())
            best_val = data.get("best_value", 0)
            best_params = data.get("best_params", {})
            n_trials = data.get("n_completed_trials", len(data.get("trials", [])))
            insights[agent] = {
                "best_score": round(best_val, 4),
                "n_trials": n_trials,
                "best_params": best_params,
                "key_finding": _extract_key_finding(agent, best_params),
            }
        except Exception:
            pass
    return insights


def _extract_key_finding(agent: str, params: dict) -> str:
    """Optuna sonucundan en önemli bulguyu çıkar."""
    if not params:
        return "Parametre verisi yok"
    pnl = params.get("pnl_weight", 10)
    dd = params.get("dd_weight", 0.3)
    sb = params.get("sharpe_bonus", 0)
    if pnl > 15:
        return f"Yüksek pnl_weight ({pnl:.1f}) → agresif return odağı"
    if dd > 0.5:
        return f"dd_weight={dd:.2f} → DD kontrolü aktif, MaxDD düşüyor"
    if sb > 0.1:
        return f"sharpe_bonus={sb:.2f} → Sharpe optimize ediliyor"
    return f"pnl={pnl:.1f}, dd={dd:.2f}, sharpe_bonus={sb:.2f}"


# ─────────────────────────────────────────────────────────────
# MODÜL 3: KOMUTİÜRETİCİ
# Çalıştırılacak eğitim komutlarını ve config değişikliklerini üret.
# ─────────────────────────────────────────────────────────────


def generate_commands(models: list[dict], analysis: dict, top_n: int = 5) -> list[dict]:
    """
    Her model ve her öneri için çalıştırılabilir komut üret.
    Öncelik sırasına göre döndür.
    """
    top = models[:top_n]
    commands = []
    recs = analysis.get("recommendations", [])

    if not recs:
        return [
            {
                "step": 1,
                "priority": "info",
                "description": "Kritik sorun tespit edilmedi.",
                "action": "Mevcut modeller üzerinde daha uzun süre eğitim dene.",
                "command": None,
            }
        ]

    # En yüksek öncelikli öneriyi al
    top_rec = recs[0]

    for i, m in enumerate(top, 1):
        model_has_issue = any(iss["type"] == top_rec["issue"] for iss in m["issues"])
        if not model_has_issue:
            continue

        agent_type = m["name"].replace("ppo_", "").replace("rppo_", "")

        commands.append(
            {
                "step": i,
                "priority": "🔴 KRİTİK" if top_rec["priority"] == 1 else "🟡 ÖNEMLİ",
                "model": m["name"],
                "model_id": m["id"],
                "issue": top_rec["issue"],
                "description": (f"{m['name']} — {top_rec['rationale'][:80]}..."),
                "param_change": {
                    top_rec["param"]: f"{top_rec['current']} → {top_rec['suggested']}"
                },
                "optuna_command": (
                    f"python scripts/optuna_trio.py "
                    f"--agent {agent_type} "
                    f"--n-trials 15 "
                    f"--{top_rec['param'].replace('_','-')} {top_rec['suggested']}"
                ),
                "retrain_command": (
                    f"python scripts/retrain_models.py "
                    f"--only {agent_type} "
                    f"--{top_rec['param'].replace('_','-')} {top_rec['suggested']}"
                ),
                "expected_improvement": _estimate_improvement(top_rec["issue"], m),
            }
        )

    return commands


def _estimate_improvement(issue: str, model: dict) -> str:
    """Sorun türüne göre beklenen iyileşmeyi tahmin et."""
    estimates = {
        "high_dd": (
            f"MaxDD %{model['dd']*100:.0f} → tahmini %{model['dd']*100*0.6:.0f} "
            f"(dd_weight artışıyla ~%40 azalma bekleniyor)"
        ),
        "overtrading": (
            f"Trade sayısı {model['trades']} → tahmini ~{int(model['trades']*0.5)} "
            "(turnover_penalty ile ~%50 azalma)"
        ),
        "low_sharpe": (
            f"Sharpe {model['sharpe']:.4f} → tahmini {model['sharpe']*2:.4f} "
            "(sharpe_bonus ile ~%100 artış hedefli)"
        ),
        "negative_return": "Pozitif return hedefleniyor (pnl_weight rebalancing)",
    }
    return estimates.get(issue, "Tahmin mevcut değil")


# ─────────────────────────────────────────────────────────────
# MODÜL 4: HAFIZA (Research State)
# Her çalıştırmada ne denediğimizi ve sonuçları kaydeder.
# ─────────────────────────────────────────────────────────────


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text())
    return {
        "version": 1,
        "created_at": now_str(),
        "iteration": 0,
        "active_reward_terms": {
            "pnl_weight": 10.0,
            "dd_weight": 0.3,
            "cost_weight": 0.1,
            "sharpe_bonus": 0.0,
            "turnover_penalty": 0.0,
            "regime_bonus": 0.0,
            "action_smoothing": 0.0,
        },
        "baseline_metrics": {},
        "experiment_log": [],
        "best_per_agent": {},
        "top5_ids": [],
        "next_action": "initial_measure",
    }


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def update_state(state: dict, models: list[dict], analysis: dict, top_n: int = 5) -> dict:
    """State'i güncel ölçümlerle güncelle."""
    state["iteration"] += 1
    state["last_run"] = now_str()

    # Top 5'i kaydet
    top = models[:top_n]
    state["top5_ids"] = [m["id"] for m in top]

    # Baseline metrikleri güncelle (ilk çalıştırma)
    if not state.get("baseline_metrics"):
        state["baseline_metrics"] = {
            m["id"]: {
                "sharpe": m["sharpe"],
                "return": m["return"],
                "dd": m["dd"],
                "score": m["score"],
            }
            for m in top
        }
        print("[STATE] Baseline metrikleri kaydedildi (ilk çalıştırma).")

    # Regresyon tespiti
    regressions = []
    for m in top:
        baseline = state["baseline_metrics"].get(m["id"])
        if baseline and m["sharpe"] < baseline["sharpe"] * 0.9:
            regressions.append(
                {
                    "model": m["id"],
                    "metric": "sharpe",
                    "before": baseline["sharpe"],
                    "after": m["sharpe"],
                    "delta_pct": (m["sharpe"] - baseline["sharpe"])
                    / max(abs(baseline["sharpe"]), 1e-6)
                    * 100,
                }
            )
    if regressions:
        print(f"[UYARI] {len(regressions)} modelde regresyon tespit edildi!")
        state["regressions"] = regressions

    # Sonraki eylem önerisi
    recs = analysis.get("recommendations", [])
    if recs:
        top_rec = recs[0]
        state["next_action"] = (
            f"Optuna ile '{top_rec['param']}' optimize et "
            f"(önerilen: {top_rec['suggested']}, "
            f"aralık: {top_rec['optuna_range']})"
        )
    else:
        state["next_action"] = "Kritik sorun yok — sharpe_bonus dene"

    return state


# ─────────────────────────────────────────────────────────────
# MODÜL 5: RAPOR ÜRETİCİ
# Markdown formatında haftalık araştırma raporu yazar.
# ─────────────────────────────────────────────────────────────


def generate_report(
    models: list[dict],
    analysis: dict,
    commands: list[dict],
    state: dict,
    top_n: int = 5,
) -> str:
    top = models[:top_n]
    recs = analysis.get("recommendations", [])
    optuna = analysis.get("optuna_insights", {})
    diversity_warn = analysis.get("diversity_warning", "")

    lines = [
        f"# 🤖 DRL Araştırma Raporu — {week_str()}",
        f"*Oluşturuldu: {now_str()} | İterasyon: {state.get('iteration', 0)}*",
        "",
        "---",
        "",
        "## 📊 Top 5 Model — Mevcut Durum",
        "",
        "| # | Model | Sharpe | Return | MaxDD | Trades | Skor | Sorunlar |",
        "|---|-------|--------|--------|-------|--------|------|----------|",
    ]

    for i, m in enumerate(top, 1):
        issue_icons = []
        for iss in m["issues"]:
            icon_map = {
                "high_dd": "🔴DD",
                "overtrading": "🟡OT",
                "low_sharpe": "🟡SH",
                "negative_return": "🔴NR",
                "always_active": "ℹ️AA",
            }
            issue_icons.append(icon_map.get(iss["type"], iss["type"]))
        issues_str = " ".join(issue_icons) if issue_icons else "✅"
        lines.append(
            f"| {i} | {m['name']} | {m['sharpe']:.4f} | "
            f"{m['return']:.0%} | {m['dd']:.0%} | "
            f"{m['trades']} | {m['score']:.2f} | {issues_str} |"
        )

    lines += [
        "",
        "**Lejand:** 🔴DD=Yüksek MaxDD | 🟡OT=Overtrading | 🟡SH=Düşük Sharpe | 🔴NR=Negatif Return",
        "",
    ]

    # Çeşitlilik uyarısı
    if diversity_warn:
        lines += [
            "### ⚠️ Çeşitlilik Uyarısı",
            f"> {diversity_warn}",
            "",
        ]

    # Ortak sorunlar
    common = analysis.get("common_issues", {})
    if common:
        lines += ["## 🔍 Tespit Edilen Ortak Sorunlar", ""]
        severity_map = {
            "high_dd": ("🔴 KRİTİK", f"Top {top_n}'in tamamında MaxDD >%35"),
            "overtrading": ("🟡 UYARI", "Trade sayısı >400 — turnover maliyeti yüksek"),
            "low_sharpe": ("🟡 UYARI", "Sharpe <0.07 — risk-adjusted kazanç zayıf"),
            "negative_return": ("🔴 KRİTİK", "Model para kaybediyor"),
            "always_active": ("ℹ️ BİLGİ", "%99+ aktif ama Sharpe düşük — pozisyon seçiciliği yok"),
        }
        for issue_type, affected in common.items():
            sev, desc = severity_map.get(issue_type, ("❓", issue_type))
            lines.append(f"- {sev} **{issue_type}** (#{affected}): {desc}")
        lines.append("")

    # Öneriler
    if recs:
        lines += ["## 💡 Önerilen Müdahaleler (Öncelik Sırasına Göre)", ""]
        for i, rec in enumerate(recs, 1):
            lines += [
                f"### {i}. {rec['param']} — {rec['affects']}",
                f"**Sorun:** `{rec['issue']}`  ",
                f"**Mevcut değer:** `{rec['current']}`  ",
                f"**Önerilen değer:** `{rec['suggested']}`  ",
                f"**Optuna arama aralığı:** `{rec['optuna_range']}`  ",
                "",
                f"> {rec['rationale']}",
                "",
            ]

    # Çalıştırılacak komutlar
    if commands:
        lines += ["## ⚡ Bu Hafta Çalıştırılacak Komutlar", ""]
        for cmd in commands:
            lines.append(f"### {cmd['priority']} {cmd['model']}")
            lines.append(f"**Sorun:** `{cmd['issue']}` — {cmd['description'][:60]}...")
            lines.append(f"**Beklenen iyileşme:** {cmd['expected_improvement']}")
            lines.append("")
            lines.append("```bash")
            lines.append("# 1. Adım: Optuna ile optimum parametreyi bul (~30 dakika)")
            lines.append(cmd["optuna_command"])
            lines.append("")
            lines.append("# 2. Adım: En iyi parametre ile yeniden eğit (~2-4 saat)")
            lines.append(cmd["retrain_command"])
            lines.append("```")
            lines.append("")

    # Optuna geçmiş sonuçları
    if optuna:
        lines += ["## 📈 Geçmiş Optuna Sonuçları", ""]
        for agent, info in optuna.items():
            lines.append(
                f"- **{agent}**: {info['n_trials']} trial | "
                f"En iyi skor: `{info['best_score']}` | "
                f"Bulgu: {info['key_finding']}"
            )
        lines.append("")

    # Regresyon uyarısı
    if state.get("regressions"):
        lines += ["## 🚨 Regresyon Uyarıları", ""]
        for reg in state["regressions"]:
            lines.append(
                f"- **{reg['model']}**: Sharpe "
                f"{reg['before']:.4f} → {reg['after']:.4f} "
                f"(delta: {reg['delta_pct']:+.1f}%)"
            )
        lines.append("")

    # Sonraki adım
    lines += [
        "## 🎯 Sonraki Adım",
        "",
        f"```\n{state.get('next_action', '—')}\n```",
        "",
        "---",
        "*Bu rapor `scripts/drl_autopilot.py` tarafından otomatik üretilmiştir.*",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# MODÜL 6: ENSEMBLE ÖNERİSİ
# Top 5'den sağlıklı bir ensemble kurulumu öner.
# ─────────────────────────────────────────────────────────────


def suggest_ensemble(models: list[dict], top_n: int = 5) -> dict:
    """
    Top N model içinden en iyi ensemble kombinasyonunu öner.
    Çeşitlilik (ajan türü) ve performans dengesini gözetir.
    """
    top = models[:top_n]
    agent_types = {}
    for m in top:
        base = m["name"].replace("ppo_", "").replace("rppo_", "")
        # Birden fazla versiyonu varsa en iyisini al (score ile)
        if base not in agent_types or m["score"] > agent_types[base]["score"]:
            agent_types[base] = m

    # Skor bazlı ağırlık hesapla
    total_score = sum(m["score"] for m in agent_types.values())
    weights = {}
    for _base, m in agent_types.items():
        weight = round(m["score"] / total_score, 3) if total_score > 0 else 1 / len(agent_types)
        weights[m["id"]] = {
            "name": m["name"],
            "weight": weight,
            "sharpe": m["sharpe"],
            "dd": m["dd"],
        }

    return {
        "ensemble_models": weights,
        "n_agents": len(weights),
        "total_weight": round(sum(v["weight"] for v in weights.values()), 3),
        "note": (
            "Ağırlıklar composite score'a göre hesaplanmıştır. "
            "LearnableEnsembleWeights ile production'da dinamik güncellenecektir."
        ),
    }


# ─────────────────────────────────────────────────────────────
# ANA DÖNGÜ
# ─────────────────────────────────────────────────────────────


def run_full(top_n: int = 5, verbose: bool = True) -> None:
    """Tam araştırma döngüsünü çalıştır."""

    print("\n" + "═" * 60)
    print("  DRL RESEARCH AUTOPILOT — Başlatılıyor")
    print(f"  {now_str()}")
    print("═" * 60 + "\n")

    # Adım 1: Ölçüm
    print("📊 [1/5] Modeller ölçülüyor...")
    models = measure()
    if not models:
        print("[HATA] Hiç model bulunamadı. Registry kontrol edin.")
        return
    print(f"  → {len(models)} model yüklendi. Top {top_n} odaklanılıyor.\n")

    # Adım 2: Analiz
    print("🔍 [2/5] Analiz yapılıyor...")
    analysis = analyze(models, top_n=top_n)
    n_issues = sum(len(v) for v in analysis["common_issues"].values())
    print(f"  → {len(analysis['common_issues'])} farklı sorun türü, {n_issues} toplam tespit.\n")

    # Adım 3: Komut üretme
    print("⚙️  [3/5] Komutlar üretiliyor...")
    commands = generate_commands(models, analysis, top_n=top_n)
    print(f"  → {len(commands)} öncelikli komut hazırlandı.\n")

    # Adım 4: State güncelleme
    print("💾 [4/5] Araştırma state'i güncelleniyor...")
    state = load_state()
    state = update_state(state, models, analysis, top_n=top_n)
    save_state(state)
    print(f"  → İterasyon #{state['iteration']} kaydedildi.\n")

    # Adım 5: Rapor
    print("📝 [5/5] Rapor oluşturuluyor...")
    report_md = generate_report(models, analysis, commands, state, top_n=top_n)
    report_path = REPORTS_DIR / f"drl_research_{week_str()}.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"  → Rapor kaydedildi: {report_path.name}\n")

    # Ensemble önerisi
    ensemble = suggest_ensemble(models, top_n=top_n)

    # Terminal özeti
    print("═" * 60)
    print("  ÖZET")
    print("═" * 60)
    print(f"\n  Top {top_n} modeller:")
    for i, m in enumerate(models[:top_n], 1):
        issues_str = ", ".join(iss["type"] for iss in m["issues"])
        print(
            f"  {i}. {m['name']:<25} Skor:{m['score']:.2f}  Sharpe:{m['sharpe']:.4f}  MaxDD:{m['dd']:.0%}  [{issues_str or 'ok'}]"
        )

    print(f"\n  Tespit edilen ortak sorunlar: {list(analysis['common_issues'].keys())}")

    if analysis.get("diversity_warning"):
        print(f"\n  ⚠️  {analysis['diversity_warning'][:80]}...")

    print(f"\n  Sonraki adım: {state['next_action']}")

    print("\n  Bu hafta çalıştır:")
    for cmd in commands[:3]:
        print(f"  → {cmd.get('optuna_command', '')}")

    print(f"\n  Ensemble öneri ({ensemble['n_agents']} ajan):")
    for _mid, info in ensemble["ensemble_models"].items():
        print(f"    {info['name']}: ağırlık={info['weight']} | Sharpe={info['sharpe']:.4f}")

    print(f"\n  Rapor: data/reports_cache/drl_research_{week_str()}.md")
    print("═" * 60 + "\n")


def run_measure_only(top_n: int = 5) -> None:
    """Sadece ölçüm yap ve tabloyu göster."""
    models = measure()
    print(
        f"\n{'#':<3} {'Model':<32} {'Sharpe':>8} {'Return':>8} {'MaxDD':>7} {'Trades':>7} {'Skor':>7}"
    )
    print("─" * 72)
    for i, m in enumerate(models, 1):
        flag = "⭐" if i <= top_n else "  "
        print(
            f"{flag}{i:<2} {m['name']:<32} {m['sharpe']:>8.4f} {m['return']:>8.1%} {m['dd']:>7.1%} {m['trades']:>7} {m['score']:>7.3f}"
        )


def run_report_only(top_n: int = 5) -> None:
    """Sadece rapor üret (mevcut state ile)."""
    models = measure()
    analysis = analyze(models, top_n=top_n)
    commands = generate_commands(models, analysis, top_n=top_n)
    state = load_state()
    report_md = generate_report(models, analysis, commands, state, top_n=top_n)
    report_path = REPORTS_DIR / f"drl_research_{week_str()}.md"
    report_path.write_text(report_md, encoding="utf-8")
    print(f"Rapor: {report_path}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DRL Research Autopilot — FinPilot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--measure", action="store_true", help="Sadece ölçüm yap")
    parser.add_argument("--analyze", action="store_true", help="Sadece analiz yap")
    parser.add_argument("--report", action="store_true", help="Sadece rapor üret")
    parser.add_argument(
        "--top", type=int, default=5, help="Kaç modele odaklanılsın (varsayılan: 5)"
    )
    parser.add_argument("--verbose", action="store_true", help="Detaylı çıktı")
    args = parser.parse_args()

    top_n = args.top

    if args.measure:
        run_measure_only(top_n=top_n)
    elif args.analyze:
        models = measure()
        analysis = analyze(models, top_n=top_n)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    elif args.report:
        run_report_only(top_n=top_n)
    else:
        # Varsayılan: tam döngü
        run_full(top_n=top_n, verbose=args.verbose)


if __name__ == "__main__":
    main()
