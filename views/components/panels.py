# -*- coding: utf-8 -*-
"""
FinPilot Panels
===============
UI bileşenleri: özet panelleri ve ilerleme izleyicileri.
"""

import datetime
from html import escape
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st

import scanner
from views.components.helpers import format_decimal


def render_summary_panel(df: pd.DataFrame, buyable: pd.DataFrame | None = None) -> None:
    """Render a compact summary panel highlighting scan statistics."""
    if df is None or df.empty:
        return

    total_symbols = len(df)
    buyable_count = len(buyable) if isinstance(buyable, pd.DataFrame) else 0
    buyable_ratio = (buyable_count / total_symbols * 100.0) if total_symbols else 0.0

    avg_rr = None
    if isinstance(buyable, pd.DataFrame) and not buyable.empty and "risk_reward" in buyable.columns:
        avg_rr = buyable["risk_reward"].dropna().mean()

    avg_score = None
    if "score" in df.columns:
        avg_score = df["score"].dropna().mean()

    mean_strength = None
    try:
        strengths = df.apply(scanner.compute_recommendation_strength, axis=1)
        strengths = strengths[~pd.isna(strengths)]
        mean_strength = strengths.mean() if len(strengths) > 0 else None
    except Exception:
        mean_strength = None

    last_scan_raw = st.session_state.get("scan_time")
    if isinstance(last_scan_raw, (pd.Timestamp, datetime.datetime)):
        last_scan_display = last_scan_raw.strftime("%Y-%m-%d %H:%M")
    else:
        last_scan_display = last_scan_raw or "-"
    last_scan_display = escape(str(last_scan_display))
    source_label = escape(str(st.session_state.get("scan_src") or "—"))

    buyable_ratio_text = format_decimal(buyable_ratio, precision=1, placeholder="0.0")
    avg_rr_text = format_decimal(avg_rr) if avg_rr is not None else "-"
    if avg_rr_text != "-":
        avg_rr_text = f"{avg_rr_text}x"
    avg_score_text = format_decimal(avg_score, precision=1)
    mean_strength_text = "-"
    if mean_strength is not None:
        try:
            mean_strength_text = f"{int(round(float(mean_strength)))} / 100"
        except Exception:
            mean_strength_text = format_decimal(mean_strength, precision=0)

    items = [
        f"<li><span class='icon'>📊</span>{total_symbols} sembol tarandı</li>",
        f"<li><span class='icon'>🟢</span>{buyable_count} fırsat · {buyable_ratio_text}% başarı</li>",
        f"<li><span class='icon'>⚡</span>Ortalama güç: {mean_strength_text}</li>",
        f"<li><span class='icon'>📈</span>Ortalama skor: {avg_score_text}</li>",
        f"<li><span class='icon'>📊</span>Ortalama R/R: {avg_rr_text}</li>",
        f"<li><span class='icon'>🕒</span>Son tarama: {last_scan_display} · Kaynak: {source_label}</li>",
    ]

    summary_html = dedent(
        f"""
        <div class='summary-panel'>
            <h4>FinPilot Özet Kartı</h4>
            <ul>
                {''.join(items)}
            </ul>
        </div>
        """
    ).strip()
    st.markdown(summary_html, unsafe_allow_html=True)


def render_progress_tracker(
    container: Any, status: str, has_source: bool, has_results: bool
) -> None:
    """Render the process tracker with detailed guidance cards."""

    steps = [
        {
            "key": "start",
            "title": "Başlat",
            "icon": "▶️",
            "what": "Tarama motorunu seçtiğiniz portföy ayarları, risk parametreleri ve tarama modu ile başlatıyoruz.",
            "why": "Sistem hangi strateji ve risk çerçevesiyle çalışacağını bu adımda bilir.",
            "message": '"Taramayı Çalıştır" butonuna bastığınızda analiz süreci seçtiğiniz parametrelerle tetiklenir.',
        },
        {
            "key": "data",
            "title": "Veri Kaynağı",
            "icon": "📥",
            "what": "Sembol listenizi (örneğin CSV dosyası) sisteme alıp doğruluyoruz.",
            "why": "Analiz motoru yalnızca sağladığınız veri seti üzerinden çalışır; doğruluk sonuçların güvenilirliğini belirler.",
            "message": '"CSV Yükle" veya "Son Shortlist\'i Yükle" ile veri sağlayarak filtrelemeye hazır hale getirin.',
        },
        {
            "key": "results",
            "title": "Sonuçlar",
            "icon": "📊",
            "what": "Tarama tamamlandığında alım fırsatları, risk/ödül oranları, sentiment ve rejim analizleri üretilir.",
            "why": "Bu metrikler hangi sembollerin öne çıktığını ve hangi stratejilerin uygulanabilir olduğunu gösterir.",
            "message": "Sonuçları tablo halinde inceleyebilir, filtreleyebilir ve geçmiş performansla kıyaslayabilirsiniz.",
        },
    ]

    started = status != "idle" or has_source or has_results
    completions = [started, has_source, has_results]
    try:
        active_index = next(idx for idx, done in enumerate(completions) if not done)
    except StopIteration:
        active_index = None

    completed_count = sum(1 for done in completions if done)
    progress_percent = int((completed_count / len(steps)) * 100) if steps else 0
    if status == "loading" and active_index is not None:
        progress_percent = min(96, progress_percent + 15)
    if status == "error" and active_index is not None:
        progress_percent = max(progress_percent, min(90, progress_percent + 5))
    progress_percent = max(0, min(progress_percent, 100))

    status_text_map = {
        "idle": "Hazır — süreç başlatılabilir",
        "loading": "Analiz sürüyor",
        "completed": "Tarama tamamlandı",
        "error": "Bir adımda hata oluştu",
    }
    status_text = status_text_map.get(status, status.title())

    if active_index is None:
        current_stage_desc = (
            "Tüm adımlar başarıyla tamamlandı. Kartlardan sonuç detaylarını inceleyebilirsiniz."
        )
        progress_class = "completed"
    else:
        current_title = steps[active_index]["title"]
        if status == "error":
            current_stage_desc = f"{current_title} adımında dikkat gerekiyor. Parametreleri ve veri girişini kontrol ederek tekrar deneyin."
            progress_class = "error"
        elif status == "loading":
            current_stage_desc = f"{current_title} adımı çalışıyor. Süreç tamamlandığında sonuçlar otomatik güncellenecek."
            progress_class = "active"
        else:
            current_stage_desc = f"Şu anda {current_title} adımındasınız."
            progress_class = "active"

    state_labels = {
        "completed": "Tamamlandı",
        "active": "Devam ediyor",
        "upcoming": "Sıradaki",
        "error": "Hata",
    }

    cards_html: list[str] = []
    for idx, step in enumerate(steps):
        if active_index is None:
            state = "completed"
        elif idx < active_index:
            state = "completed"
        elif idx == active_index:
            state = "error" if status == "error" else "active"
        else:
            state = "upcoming"

        rows = []
        for label, text in (
            ("Ne yapıyoruz?", step["what"]),
            ("Neden önemli?", step["why"]),
            ("Kullanıcıya mesaj", step["message"]),
        ):
            escaped_text = escape(text)
            escaped_label = escape(label)
            rows.append(
                f"<div class='card-row'><span class='row-label'>{escaped_label}</span>"
                f"<span class='row-text'>{escaped_text}</span>"
                f"<span class='tooltip-icon' title='{escaped_text}'>ℹ️</span></div>"
            )

        cards_html.append(
            dedent(
                f"""
                <div class='process-card {state}'>
                    <div class='card-header'>
                        <span class='card-icon'>{step['icon']}</span>
                        <div>
                            <div class='card-title'>{escape(step['title'])}</div>
                            <span class='state-tag'>{state_labels[state]}</span>
                        </div>
                    </div>
                    <div class='card-body'>
                        {''.join(rows)}
                    </div>
                </div>
                """
            ).strip()
        )

    cards_html_joined = "\n".join(cards_html)

    progress_html = dedent(
        f"""
        <div class='process-status'>
            <div class='status-head'>
                <div>
                    <span class='status-label'>Analiz Süreci İzleme</span>
                    <span class='status-subtitle'>{escape(status_text)}</span>
                </div>
                <span class='status-value'>{progress_percent}%</span>
            </div>
            <div class='process-progress-bar'>
                <div class='process-progress-bar__inner {progress_class}' style='width:{progress_percent}%;'></div>
            </div>
            <div class='process-current'>{escape(current_stage_desc)}</div>
        </div>
        <div class='process-grid'>
            {cards_html_joined}
        </div>
        """
    ).strip()

    container.markdown(progress_html, unsafe_allow_html=True)
