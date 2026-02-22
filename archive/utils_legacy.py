import datetime
import math
import os
import re
from functools import lru_cache
from html import escape
from pathlib import Path
from textwrap import dedent

# .env dosyasından ortam değişkenlerini yükle
try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

try:
    import google.generativeai as genai
    from duckduckgo_search import DDGS
    from groq import Groq
except ImportError:
    genai = None
    DDGS = None
    Groq = None

import scanner

DEMO_MODE_ENABLED = True


def trigger_rerun() -> None:
    """Safely trigger a rerun for Streamlit across versions."""
    rerun_callable = getattr(st, "rerun", None)
    if callable(rerun_callable):
        rerun_callable()
        return

    legacy_rerun = getattr(st, "experimental_rerun", None)
    if callable(legacy_rerun):
        legacy_rerun()


REGIME_HINT_CATALOG = {
    "trend": "Trend modu: Fiyat yukarı yönlü momentumda, trend takip stratejileri avantaj sağlar.",
    "bull": "Boğa rejimi: Piyasa yükseliş eğiliminde, long stratejiler öne çıkar.",
    "bear": "Ayı rejimi: Zayıf momentum, risk azaltımı veya hedge tercih edilmeli.",
    "yan": "Yatay/sideways rejim: Net trend yok, range trade veya bekle-gör stratejisi.",
    "side": "Yatay/sideways rejim: Net trend yok, range trade veya bekle-gör stratejisi.",
}

SENTIMENT_HINT_CATALOG = {
    "positive": "Pozitif sentiment: Piyasa hissiyatı destekleyici, haber akışı güçlü.",
    "neg": "Negatif sentiment: Haber ve akış zayıf, risk iştahı düşük.",
    "bull": "Boğa sentiment: Yatırımcılar iyimser, alım iştahı yüksek.",
    "bear": "Ayı sentiment: İyimserlik sınırlı, savunma stratejisi düşünülmeli.",
    "fear": "Korku/Fear modu: Volatilite yüksek, pozisyon boyutları azaltılmalı.",
    "greed": "Greed modu: Risk iştahı yüksek, aşırı ısınma kontrol edilmeli.",
    "neutral": "Nötr sentiment: Net bir eğilim yok, teyit arayın.",
    "mixed": "Karışık sentiment: Göstergeler çelişkili, ek doğrulama gerekli.",
}

HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def is_advanced_view() -> bool:
    return st.session_state.get("view_mode", "advanced") == "advanced"


def normalize_narrative(value) -> str:
    """Normalize narrative text by removing HTML artifacts and collapsing whitespace."""
    if value is None:
        return ""
    try:
        if hasattr(pd, "isna") and pd.isna(value):
            return ""
    except Exception:
        pass
    if isinstance(value, float):
        try:
            if math.isnan(value):
                return ""
        except Exception:
            pass
    text = str(value)
    if not text.strip():
        return ""
    text = dedent(text)
    normalized = text.strip()
    lower = normalized.lower()
    if lower in {"nan", "none"}:
        return ""
    normalized = HTML_TAG_RE.sub(" ", normalized)
    normalized = WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()


def format_decimal(value, precision=2, placeholder="-") -> str:
    """Format numeric values defensively for UI rendering."""
    if value in (None, "", "-"):
        return placeholder
    try:
        if isinstance(value, (int, float)):
            return f"{float(value):.{precision}f}"
        if pd.isna(value):
            return placeholder
        numeric = float(value)
        return f"{numeric:.{precision}f}"
    except Exception:
        return str(value)


def _lookup_hint(value, catalog, default):
    if value in (None, ""):
        return default
    key = str(value).lower()
    for token, hint in catalog.items():
        if token in key:
            return hint
    return default


def get_regime_hint(value):
    return _lookup_hint(
        value,
        REGIME_HINT_CATALOG,
        "Rejim metriği, trend analizi sonucunu ve piyasa yapısını gösterir.",
    )


def get_sentiment_hint(value):
    return _lookup_hint(
        value,
        SENTIMENT_HINT_CATALOG,
        "Sentiment metriği, haber ve veri akışından türetilen piyasa hissiyatını özetler.",
    )


def build_status_chip(label: str, variant: str = "neutral", icon=None, tooltip=None) -> str:
    """Return HTML for a status chip with safe escaping."""
    if not label:
        return ""
    safe_label = escape(str(label))
    tooltip_attr = f" title='{escape(str(tooltip))}'" if tooltip else ""
    icon_html = f"<span class='chip-icon'>{icon}</span>" if icon else ""
    return f"<span class='status-chip {variant}'{tooltip_attr}>{icon_html}{safe_label}</span>"


def build_zscore_chip(data: dict) -> str:
    z_value = data.get("momentum_best_zscore")
    if z_value in (None, "", "NaN"):
        return ""
    try:
        z_val = float(z_value)
    except (TypeError, ValueError):  # noqa: PERF203
        return ""

    threshold = data.get("momentum_z_effective") or scanner.SETTINGS.get(
        "momentum_z_threshold", 1.5
    )
    try:
        threshold_val = float(threshold)
    except (TypeError, ValueError):
        threshold_val = float(scanner.SETTINGS.get("momentum_z_threshold", 1.5))

    baseline = data.get("momentum_baseline_window") or scanner.SETTINGS.get(
        "momentum_baseline_window", 60
    )
    try:
        baseline = int(baseline)
    except (TypeError, ValueError):
        baseline = scanner.SETTINGS.get("momentum_baseline_window", 60)

    horizon = data.get("momentum_best_horizon")
    try:
        horizon = int(horizon) if horizon is not None else None
    except (TypeError, ValueError):
        horizon = None

    segment_key = data.get("momentum_liquidity_segment")
    if segment_key in (None, ""):
        segment_key_cast = None
    else:
        segment_key_cast = str(segment_key)
    segment_labels = {
        "high_liquidity": "Yüksek hacim",
        "mid_liquidity": "Orta hacim",
        "low_liquidity": "Düşük hacim",
    }
    if segment_key_cast:
        segment_label = segment_labels.get(segment_key_cast, segment_key_cast)
    else:
        segment_label = ""

    z_abs = abs(z_val)
    if math.isfinite(z_abs):
        cdf = 0.5 * (1 + math.erf(z_abs / math.sqrt(2)))
        unusual_pct = cdf * 100.0
    else:
        unusual_pct = None

    if z_abs >= threshold_val:
        variant = "success" if z_val >= 0 else "warning"
    else:
        variant = "neutral"

    horizon_text = f"{horizon} periyot" if horizon else "Son getiri"
    baseline_text = f"{baseline} periyot"
    rarity_text = (
        f"Bu hareket, geçmiş dağılımın %{unusual_pct:.1f} dilimi içinde."
        if unusual_pct is not None
        else ""
    )
    threshold_text = f"Eşik: ±{threshold_val:.1f}σ"
    if segment_label:
        threshold_text += f" · Segment: {segment_label}"

    tooltip = (
        f"Z-Skoru, {horizon_text} getirinin {baseline_text} ortalama ve volatilitesine göre normalize edilmiş değeridir. "
        f"{rarity_text} {threshold_text}"
    ).strip()

    label = f"Z · {z_val:+.1f}σ"
    return build_status_chip(label, variant=variant, icon="σ", tooltip=tooltip)


def build_signal_strength_chip(data: dict) -> str:
    strength = data.get("strength")
    if strength in (None, "", "-", "NaN") or (hasattr(pd, "isna") and pd.isna(strength)):
        strength = scanner.compute_recommendation_strength(data)
    try:
        strength_val = float(strength)
        if strength_val <= 1:
            strength_val *= 100
    except Exception:
        strength_val = float(scanner.compute_recommendation_strength(data))
    strength_val = max(0, min(100, int(round(strength_val))))

    if strength_val >= 75:
        variant, descriptor = "success", "Güçlü"
    elif strength_val >= 55:
        variant, descriptor = "warning", "Takip"
    else:
        variant, descriptor = "neutral", "İzle"

    tooltip = "Makine öğrenimi skoru: ≥75 güçlü, 55-74 takip edilmesi gereken, <55 beklemede."
    label = f"{descriptor} · {strength_val}"
    return build_status_chip(label, variant=variant, icon="⚡", tooltip=tooltip)


def build_regime_chip(data: dict) -> str:
    regime = data.get("regime")
    if regime in (None, "", "NaN", "-"):
        return build_status_chip(
            "Rejim · —", variant="neutral", icon="🧭", tooltip="Rejim bilgisi mevcut değil."
        )

    regime_text = str(regime)
    lower = regime_text.lower()
    if any(token in lower for token in ["bull", "trend", "up"]):
        variant, descriptor = "success", "Prospektif"
    elif any(token in lower for token in ["bear", "down", "risk"]):
        variant, descriptor = "warning", "Savunma"
    else:
        variant, descriptor = "neutral", "Nötr"

    tooltip = get_regime_hint(regime)
    label = f"{descriptor} · {regime_text.upper()}"
    return build_status_chip(label, variant=variant, icon="🧭", tooltip=tooltip)


def build_risk_reward_chip(data: dict) -> str:
    rr = data.get("risk_reward") or data.get("risk_reward_ratio")
    if rr is None:
        return ""
    try:
        rr_val = float(rr)
    except Exception:
        return ""

    if rr_val >= 2.0:
        variant, descriptor = "success", "R/R"
    elif rr_val >= 1.2:
        variant, descriptor = "warning", "R/R"
    else:
        variant, descriptor = "neutral", "R/R"

    tooltip = "Risk/ödül oranı. ≥2 güçlü, 1.2-1.99 dikkatle izlenmeli."
    label = f"{descriptor} · {rr_val:.2f}x"
    return build_status_chip(label, variant=variant, icon="📊", tooltip=tooltip)


def compose_signal_chips(data: dict):
    chips = [
        build_zscore_chip(data),
        build_signal_strength_chip(data),
        build_regime_chip(data),
        build_risk_reward_chip(data),
    ]
    return [chip for chip in chips if chip]


def render_buyable_cards(df: pd.DataFrame, limit: int = 6):
    """Render highlighted buyable opportunities as responsive cards."""
    if df is None or df.empty:
        return

    featured = df.copy()
    if "recommendation_score" in featured.columns:
        featured = featured.sort_values(
            ["entry_ok", "recommendation_score"], ascending=[False, False]
        )

    for _, row in featured.head(limit).iterrows():
        data = row.to_dict()
        badge_type = "buy" if data.get("entry_ok") else "hold"
        badge_label = "AL" if data.get("entry_ok") else "İzle"
        price = data.get("price")
        stop_loss = data.get("stop_loss")
        take_profit = data.get("take_profit")
        position_size = data.get("position_size")
        risk_reward = data.get("risk_reward")
        try:
            reason_raw = scanner.build_reason(data)
        except Exception:
            reason_raw = data.get("reason")
        try:
            summary_raw = scanner.build_explanation(data)
        except Exception:
            summary_raw = data.get("why")
        summary_clean = normalize_narrative(summary_raw)
        reason_clean = normalize_narrative(reason_raw)
        summary_html = escape(summary_clean) if summary_clean else ""
        reason_html = escape(reason_clean) if reason_clean else ""
        regime = data.get("regime", "-")
        sentiment = data.get("sentiment", "-")
        onchain = data.get("onchain_metric", "-")
        regime_text = regime if regime not in (None, "") else "-"
        regime_hint = escape(get_regime_hint(regime))
        sentiment_text = format_decimal(sentiment)
        sentiment_hint = escape(get_sentiment_hint(sentiment))
        onchain_text = format_decimal(onchain)
        z_threshold_val = data.get("momentum_z_effective")
        z_threshold_text = (
            format_decimal(z_threshold_val) if z_threshold_val not in (None, "-") else "-"
        )
        segment_key = data.get("momentum_liquidity_segment")
        segment_map = {
            "high_liquidity": "Yüksek hacim",
            "mid_liquidity": "Orta hacim",
            "low_liquidity": "Düşük hacim",
        }
        if segment_key:
            segment_display = segment_map.get(str(segment_key), str(segment_key))
        else:
            segment_display = "—"
        dynamic_samples = data.get("momentum_dynamic_samples") or 0
        baseline_window = data.get("momentum_baseline_window") or scanner.SETTINGS.get(
            "momentum_baseline_window", 60
        )
        dynamic_hint = (
            f"Dinamik kalibrasyon: pencere {baseline_window}, örnek {dynamic_samples}"
            if dynamic_samples
            else f"Dinamik kalibrasyon: pencere {baseline_window}"
        )
        dynamic_hint = escape(dynamic_hint)
        z_threshold_badge = ""
        if z_threshold_text != "-":
            z_threshold_badge = (
                f"<span class='badge info' title='{dynamic_hint}'>Eşik: ±{z_threshold_text}σ</span>"
            )
        segment_badge = ""
        if segment_display:
            segment_badge = (
                f"<span class='badge hold'>Segment: {escape(str(segment_display))}</span>"
            )
        chips = compose_signal_chips(data)
        chip_row_html = ""
        if chips:
            chip_row_html = "<div class='status-chip-row'>" + "".join(chips) + "</div>"

        card_html = dedent(
            f"""
            <div class='analysis-card'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                    <div style='font-size:1.25rem; font-weight:700; letter-spacing:0.04em;'>{data.get("symbol", "-")}</div>
                    <span class='badge {badge_type}'>{badge_label}</span>
                </div>
                {chip_row_html}
                <div class='metric-grid'>
                    <div>
                        <div class='metric-label'>Fiyat</div>
                        <div class='metric-value'>{format_decimal(price)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Stop</div>
                        <div class='metric-value'>{format_decimal(stop_loss)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Take-Profit</div>
                        <div class='metric-value'>{format_decimal(take_profit)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Lot</div>
                        <div class='metric-value'>{format_decimal(position_size, precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Risk/Ödül</div>
                        <div class='metric-value'>{format_decimal(risk_reward)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Rejim</div>
                        <div class='metric-value'><span class='badge info' title='{regime_hint}'>{escape(str(regime_text))}</span></div>
                    </div>
                </div>
                <div style='display:flex; flex-wrap:wrap; gap:12px;margin-bottom:14px;'>
                    <span class='badge hold' title='{sentiment_hint}'>Sentiment: {escape(str(sentiment_text))}</span>
                    <span class='badge hold'>Onchain: {escape(str(onchain_text))}</span>
                    {z_threshold_badge}
                    {segment_badge}
                </div>
                <div style='color:#e2e8f0; font-weight:500; margin-bottom:6px;'>{summary_html}</div>
                <div style='color:rgba(148,163,184,0.85); font-size:0.85rem;'>{reason_html}</div>
            </div>
            """
        ).strip()
        st.markdown(card_html, unsafe_allow_html=True)


def render_buyable_table(df: pd.DataFrame):
    """Render the buyable opportunities table with status chips."""
    if df is None or df.empty:
        return

    rows_html = []
    for _, row in df.iterrows():
        data = row.to_dict()
        symbol = escape(str(data.get("symbol", "-")))
        price = format_decimal(data.get("price"))
        stop_loss = format_decimal(data.get("stop_loss"))
        take_profit = format_decimal(data.get("take_profit"))
        position_size = format_decimal(data.get("position_size"), precision=0)
        risk_reward = format_decimal(data.get("risk_reward"))
        score_display = format_decimal(data.get("score"), precision=0)
        timestamp = data.get("timestamp")
        if isinstance(timestamp, (pd.Timestamp, datetime.datetime)):
            time_display = timestamp.strftime("%Y-%m-%d %H:%M")
        else:
            time_display = str(timestamp) if timestamp not in (None, "", "NaT") else "-"
        time_display = escape(time_display)

        chips = compose_signal_chips(data)
        chip_block = ""
        if chips:
            chip_block = "<div class='chip-stack'>" + "".join(chips) + "</div>"

        rows_html.append(
            dedent(
                f"""
                <tr>
                    <td class='symbol-cell'>
                        <div style='font-weight:600; letter-spacing:0.04em;'>{symbol}</div>
                        {chip_block}
                    </td>
                    <td class='numeric'>{price}</td>
                    <td class='numeric'>{stop_loss}</td>
                    <td class='numeric'>{take_profit}</td>
                    <td class='numeric'>{position_size}</td>
                    <td class='numeric'>{risk_reward}</td>
                    <td class='numeric'>{score_display}</td>
                    <td class='timestamp-cell'>{time_display}</td>
                </tr>
                """
            ).strip()
        )

    table_html = dedent(
        f"""
        <div class='desktop-table signal-table-wrapper'>
            <table class='signal-table'>
                <thead>
                    <tr>
                        <th>Sembol &amp; Durum</th>
                        <th>Fiyat</th>
                        <th>Stop</th>
                        <th>Take-Profit</th>
                        <th>Lot</th>
                        <th>R/R</th>
                        <th>Skor</th>
                        <th>Zaman</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join(rows_html)}
                </tbody>
            </table>
        </div>
        """
    ).strip()
    st.markdown(table_html, unsafe_allow_html=True)


def render_summary_panel(df: pd.DataFrame, buyable: pd.DataFrame | None = None):
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
                {"".join(items)}
            </ul>
        </div>
        """
    ).strip()
    st.markdown(summary_html, unsafe_allow_html=True)


def render_symbol_snapshot(df: pd.DataFrame, limit: int = 6):
    """Render compact metric tiles and mini cards for the simple symbol view."""
    if df is None or df.empty:
        st.info("Henüz sembol verisi yok. Tarama çalıştırarak sonuçları görebilirsiniz.")
        return

    total_symbols = len(df)
    entry_series = (
        pd.Series(df.get("entry_ok", [])) if "entry_ok" in df.columns else pd.Series(dtype="bool")
    )
    buyable_count = (
        int(entry_series.fillna(False).astype(bool).sum()) if not entry_series.empty else 0
    )
    buyable_ratio = (buyable_count / total_symbols * 100.0) if total_symbols else 0.0
    rr_series = (
        pd.Series(df.get("risk_reward", []))
        if "risk_reward" in df.columns
        else pd.Series(dtype="float")
    )
    avg_rr = rr_series.dropna().mean() if not rr_series.empty else None
    last_timestamp = None
    if "timestamp" in df.columns:
        timestamps = pd.to_datetime(df["timestamp"], errors="coerce")
        timestamps = timestamps.dropna()
        if not timestamps.empty:
            last_timestamp = timestamps.max()

    col_total, col_buyable, col_rr = st.columns(3)
    col_total.metric("Toplam Sembol", f"{total_symbols}")
    buyable_delta = f"%{format_decimal(buyable_ratio, precision=1)}"
    col_buyable.metric(
        "Alım Fırsatı", f"{buyable_count}", delta=buyable_delta if total_symbols else None
    )
    col_rr.metric("Ortalama R/R", format_decimal(avg_rr) if avg_rr is not None else "-")
    if last_timestamp is not None:
        st.caption(f"Son güncelleme: {last_timestamp.strftime('%Y-%m-%d %H:%M')}")

    cards_source = df.copy()
    if "score" in cards_source.columns:
        cards_source = cards_source.sort_values(["entry_ok", "score"], ascending=[False, False])

    cards = []
    for _, row in cards_source.head(limit).iterrows():
        symbol = escape(str(row.get("symbol", "-")))
        price = format_decimal(row.get("price"))
        score = format_decimal(row.get("score"), precision=0)
        filt = format_decimal(row.get("filter_score"), precision=0)
        rr_text = format_decimal(row.get("risk_reward"))
        entry_ok = bool(row.get("entry_ok"))
        badge_label = "AL" if entry_ok else "İzle"
        badge_style = (
            "background:rgba(34,197,94,0.18); border:1px solid rgba(34,197,94,0.35); color:#4ade80;"
            if entry_ok
            else "background:rgba(148,163,184,0.18); border:1px solid rgba(148,163,184,0.35); color:#cbd5f5;"
        )
        badge_html = (
            f'<span style="display:inline-flex; align-items:center; padding:4px 10px; border-radius:999px;'
            f' font-size:0.75rem; font-weight:600; letter-spacing:0.04em; {badge_style}">{badge_label}</span>'
        )
        timestamp_raw = row.get("timestamp")
        if isinstance(timestamp_raw, (pd.Timestamp, datetime.datetime)):
            timestamp_display = timestamp_raw.strftime("%Y-%m-%d %H:%M")
        else:
            timestamp_display = (
                str(timestamp_raw) if timestamp_raw not in (None, "", "NaT") else "-"
            )
        timestamp_display = escape(timestamp_display)

        cards.append(
            dedent(
                f"""
                <div style='border-radius:16px; background:rgba(15,23,42,0.78); border:1px solid rgba(148,163,184,0.28); padding:18px 20px; display:flex; flex-direction:column; gap:12px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size:1.05rem; font-weight:600; color:#f8fafc;'>{symbol}</span>
                        {badge_html}
                    </div>
                    <div style='display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px;'>
                        <div>
                            <div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(148,163,184,0.75);'>Fiyat</div>
                            <div style='font-size:1rem; font-weight:600; color:#fff;'>{price}</div>
                        </div>
                        <div>
                            <div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(148,163,184,0.75);'>Skor</div>
                            <div style='font-size:1rem; font-weight:600; color:#fff;'>{score}</div>
                        </div>
                        <div>
                            <div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(148,163,184,0.75);'>Filtre</div>
                            <div style='font-size:1rem; font-weight:600; color:#fff;'>{filt}</div>
                        </div>
                        <div>
                            <div style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:rgba(148,163,184,0.75);'>R/R</div>
                            <div style='font-size:1rem; font-weight:600; color:#fff;'>{rr_text}</div>
                        </div>
                    </div>
                    <div style='font-size:0.78rem; color:rgba(148,163,184,0.75);'>Son güncelleme: {timestamp_display}</div>
                </div>
                """
            ).strip()
        )

    if cards:
        st.markdown(
            "<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; margin-top:20px;'>"
            + "".join(cards)
            + "</div>",
            unsafe_allow_html=True,
        )


def render_signal_history_overview(df: pd.DataFrame, limit: int = 5):
    """Render KPI tiles and quick cards for signal history."""
    if df is None or df.empty:
        st.info("Filtrelenen aralıkta geçmiş sinyal bulunamadı.")
        return

    total_signals = len(df)
    buy_mask = (
        df["Alım?"].astype(str).str.lower().isin({"1", "true", "evet", "al", "yes"})
        if "Alım?" in df.columns
        else pd.Series(dtype=bool)
    )
    buyable_count = int(buy_mask.sum()) if not buy_mask.empty else 0
    success_rate = (buyable_count / total_signals * 100.0) if total_signals else 0.0
    avg_score = None
    if "Skor" in df.columns:
        score_series = pd.to_numeric(df["Skor"], errors="coerce")
        score_series = score_series.dropna()
        if not score_series.empty:
            avg_score = score_series.mean()
    last_date = None
    if "Tarih" in df.columns:
        parsed_dates = pd.to_datetime(df["Tarih"], errors="coerce")
        parsed_dates = parsed_dates.dropna()
        if not parsed_dates.empty:
            last_date = parsed_dates.max()

    col_total, col_buyable, col_score = st.columns(3)
    col_total.metric("Toplam Sinyal", f"{total_signals}")
    col_buyable.metric(
        "Alım Fırsatı", f"{buyable_count}", delta=f"%{success_rate:.1f}" if total_signals else None
    )
    col_score.metric(
        "Ortalama Skor", format_decimal(avg_score, precision=1) if avg_score is not None else "-"
    )
    if last_date is not None:
        st.caption(f"Veri güncellendi: {last_date.strftime('%Y-%m-%d %H:%M')}")

    cards = []
    recent_rows = df.head(limit).copy()
    for _, row in recent_rows.iterrows():
        date_text = escape(str(row.get("Tarih", "-")))
        symbol = escape(str(row.get("Sembol", "-")))
        score_text = format_decimal(row.get("Skor"), precision=0)
        strength_text = format_decimal(row.get("Güç"), precision=0) if "Güç" in row else "-"
        regime_text = escape(str(row.get("Rejim", "-")))
        summary = normalize_narrative(row.get("Özet", ""))
        reason = normalize_narrative(row.get("Neden", ""))
        sentiment = format_decimal(row.get("Sentiment")) if "Sentiment" in row else "-"
        onchain = format_decimal(row.get("Onchain")) if "Onchain" in row else "-"
        entry_ok = str(row.get("Alım?", "")).lower() in {"1", "true", "evet", "al", "yes"}
        badge_label = "AL" if entry_ok else "İzle"
        badge_style = (
            "background:rgba(34,197,94,0.18); border:1px solid rgba(34,197,94,0.35); color:#4ade80;"
            if entry_ok
            else "background:rgba(148,163,184,0.18); border:1px solid rgba(148,163,184,0.35); color:#cbd5f5;"
        )
        badge_html = (
            f'<span style="display:inline-flex; align-items:center; padding:4px 10px; border-radius:999px;'
            f' font-size:0.72rem; font-weight:600; letter-spacing:0.04em; {badge_style}">{badge_label}</span>'
        )

        cards.append(
            dedent(
                f"""
                <div style='border-radius:16px; background:rgba(15,23,42,0.78); border:1px solid rgba(59,130,246,0.25); padding:18px 20px; display:flex; flex-direction:column; gap:10px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <div style='font-size:0.85rem; color:rgba(148,163,184,0.78);'>{date_text}</div>
                            <div style='font-size:1.05rem; font-weight:600; color:#f8fafc;'>{symbol}</div>
                        </div>
                        {badge_html}
                    </div>
                    <div style='font-size:0.9rem; color:#e2e8f0;'>
                        {escape(summary) if summary else "Özet bulunamadı."}
                    </div>
                    <div style='font-size:0.78rem; color:rgba(148,163,184,0.8);'>
                        {escape(reason) if reason else "Detay bilgisi bulunamadı."}
                    </div>
                    <div style='display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; font-size:0.78rem; color:rgba(148,163,184,0.85);'>
                        <div><span style='display:block; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em;'>Skor</span><span style='font-size:0.95rem; color:#fff; font-weight:600;'>{score_text}</span></div>
                        <div><span style='display:block; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em;'>Güç</span><span style='font-size:0.95rem; color:#fff; font-weight:600;'>{strength_text}</span></div>
                        <div><span style='display:block; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em;'>Rejim</span><span style='font-size:0.95rem; color:#fff; font-weight:600;'>{regime_text}</span></div>
                        <div><span style='display:block; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em;'>Sentiment</span><span style='font-size:0.95rem; color:#fff; font-weight:600;'>{sentiment}</span></div>
                        <div><span style='display:block; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em;'>Onchain</span><span style='font-size:0.95rem; color:#fff; font-weight:600;'>{onchain}</span></div>
                    </div>
                </div>
                """
            ).strip()
        )

    if cards:
        st.markdown(
            "<div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:18px; margin-top:18px;'>"
            + "".join(cards)
            + "</div>",
            unsafe_allow_html=True,
        )


def render_progress_tracker(container, status: str, has_source: bool, has_results: bool):
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
            "message": '"CSV Yükle" veya "Son Shortlist’i Yükle" ile veri sağlayarak filtrelemeye hazır hale getirin.',
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
        if active_index is None or idx < active_index:
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
                f"<div class='card-row'><span class='row-label'>{escaped_label}</span><span class='row-text'>{escaped_text}</span><span class='tooltip-icon' title='{escaped_text}'>ℹ️</span></div>"
            )

        cards_html.append(
            dedent(
                f"""
                <div class='process-card {state}'>
                    <div class='card-header'>
                        <span class='card-icon'>{step["icon"]}</span>
                        <div>
                            <div class='card-title'>{escape(step["title"])}</div>
                            <span class='state-tag'>{state_labels[state]}</span>
                        </div>
                    </div>
                    <div class='card-body'>
                        {"".join(rows)}
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


@st.cache_data(ttl=300, show_spinner=False)
def get_demo_scan_results() -> pd.DataFrame:
    """Return a lightweight demo dataframe to showcase the experience when no data exists."""
    import datetime

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    demo_rows = [
        {
            "symbol": "AAPL",
            "price": 186.40,
            "stop_loss": 180.80,
            "take_profit": 198.20,
            "position_size": 12,
            "risk_reward": 2.65,
            "entry_ok": True,
            "filter_score": 3,
            "score": 88,
            "recommendation_score": 95,
            "strength": 90,
            "regime": "Trend",
            "sentiment": 0.74,
            "onchain_metric": 68,
            "why": "Trend ve hacim onaylı.",
            "reason": "ML skoru 0.87, momentum taze.",
        },
        {
            "symbol": "NVDA",
            "price": 469.10,
            "stop_loss": 452.00,
            "take_profit": 505.00,
            "position_size": 6,
            "risk_reward": 2.94,
            "entry_ok": True,
            "filter_score": 3,
            "score": 91,
            "recommendation_score": 97,
            "strength": 92,
            "regime": "Trend",
            "sentiment": 0.81,
            "onchain_metric": 72,
            "why": "AI ivmesi güçlü.",
            "reason": "DRL stratejisi %84 uyum, volatilite kontrollü.",
        },
        {
            "symbol": "MSFT",
            "price": 335.60,
            "stop_loss": 324.00,
            "take_profit": 352.40,
            "position_size": 8,
            "risk_reward": 2.37,
            "entry_ok": True,
            "filter_score": 2,
            "score": 86,
            "recommendation_score": 92,
            "strength": 88,
            "regime": "Trend",
            "sentiment": 0.69,
            "onchain_metric": 63,
            "why": "Kurumsal talep artıyor.",
            "reason": "Kelly %4 öneriyor, earnings momentum pozitif.",
        },
        {
            "symbol": "TSLA",
            "price": 244.30,
            "stop_loss": 232.00,
            "take_profit": 262.50,
            "position_size": 0,
            "risk_reward": 1.95,
            "entry_ok": False,
            "filter_score": 2,
            "score": 78,
            "recommendation_score": 81,
            "strength": 75,
            "regime": "Yan",
            "sentiment": 0.41,
            "onchain_metric": 45,
            "why": "Volatilite yüksek.",
            "reason": "Trend teyidi bekleniyor, risk/ödül sınırlı.",
        },
        {
            "symbol": "AMD",
            "price": 112.80,
            "stop_loss": 106.50,
            "take_profit": 124.00,
            "position_size": 9,
            "risk_reward": 2.20,
            "entry_ok": True,
            "filter_score": 3,
            "score": 84,
            "recommendation_score": 90,
            "strength": 84,
            "regime": "Trend",
            "sentiment": 0.62,
            "onchain_metric": 59,
            "why": "Yarı iletken talebi güçlü.",
            "reason": "Momentum stabil, hacim 30 günlük ortalamanın 1.6x'i.",
        },
        {
            "symbol": "COIN",
            "price": 88.40,
            "stop_loss": 82.20,
            "take_profit": 102.50,
            "position_size": 0,
            "risk_reward": 2.41,
            "entry_ok": False,
            "filter_score": 1,
            "score": 72,
            "recommendation_score": 78,
            "strength": 70,
            "regime": "Yan",
            "sentiment": 0.35,
            "onchain_metric": 52,
            "why": "Regülasyon belirsiz.",
            "reason": "Risk seviyesi yüksek, on-chain hafif zayıf.",
        },
    ]

    df_demo = pd.DataFrame(demo_rows)
    df_demo["timestamp"] = now
    return df_demo


def render_mobile_symbol_cards(df: pd.DataFrame):
    """Render a compact card stack for symbol results on mobile viewports."""
    if df is None or df.empty:
        return

    df_cards = df.fillna("")

    cards = []
    for _, row in df_cards.iterrows():
        row_dict = row.to_dict()
        if "symbol" not in row_dict and "Sembol" in row_dict:
            row_dict["symbol"] = row_dict.get("Sembol")
        if "price" not in row_dict and "Fiyat" in row_dict:
            row_dict["price"] = row_dict.get("Fiyat")
        if "score" not in row_dict and "Skor" in row_dict:
            row_dict["score"] = row_dict.get("Skor")
        if "filter_score" not in row_dict and "Filtre" in row_dict:
            row_dict["filter_score"] = row_dict.get("Filtre")
        if "risk_reward" not in row_dict and "R/R" in row_dict:
            row_dict["risk_reward"] = row_dict.get("R/R")
        if "timestamp" not in row_dict and "Zaman" in row_dict:
            row_dict["timestamp"] = row_dict.get("Zaman")
        if "entry_ok" not in row_dict and "Alım?" in row_dict:
            row_dict["entry_ok"] = row_dict.get("Alım?")

        is_buy = bool(row_dict.get("entry_ok"))
        badge_type = "buy" if is_buy else "hold"
        badge_label = "AL" if is_buy else "İzle"
        chips = compose_signal_chips(row_dict)
        chip_row_html = ""
        if chips:
            chip_row_html = "<div class='status-chip-row'>" + "".join(chips) + "</div>"
        symbol_label = escape(str(row_dict.get("symbol", "-")))
        timestamp_raw = row_dict.get("timestamp")
        if isinstance(timestamp_raw, (pd.Timestamp, datetime.datetime)):
            timestamp_display = timestamp_raw.strftime("%Y-%m-%d %H:%M")
        else:
            timestamp_display = timestamp_raw if timestamp_raw not in (None, "", "NaT") else "-"
        timestamp_display = escape(str(timestamp_display))
        card_html = dedent(
            f"""
            <div class='analysis-card mobile-only'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                    <div style='font-size:1.1rem; font-weight:600; letter-spacing:0.02em;'>{symbol_label}</div>
                    <span class='badge {badge_type}'>{badge_label}</span>
                </div>
                {chip_row_html}
                <div class='metric-grid'>
                    <div>
                        <div class='metric-label'>Fiyat</div>
                        <div class='metric-value'>{format_decimal(row_dict.get("price"))}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Skor</div>
                        <div class='metric-value'>{format_decimal(row_dict.get("score"), precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Filtre</div>
                        <div class='metric-value'>{format_decimal(row_dict.get("filter_score"), precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>R/R</div>
                        <div class='metric-value'>{format_decimal(row_dict.get("risk_reward"))}</div>
                    </div>
                </div>
                <div style='font-size:0.78rem; color:rgba(148,163,184,0.75);'>Son güncelleme: {timestamp_display}</div>
            </div>
            """
        ).strip()
        cards.append(card_html)

    if cards:
        st.markdown(
            "<div style='display:flex; flex-direction:column; gap:14px; margin-top:18px;'>"
            + "".join(cards)
            + "</div>",
            unsafe_allow_html=True,
        )


def render_mobile_recommendation_cards(df: pd.DataFrame):
    """Render a compact card stack for recommendation results on mobile viewports."""
    if df is None or df.empty:
        return

    df_cards = df.fillna("")

    cards = []
    for _, row in df_cards.iterrows():
        row_dict = row.to_dict()
        # Map columns if needed (assuming df has standard columns from pretty print)
        # "Sembol", "Fiyat", "Skor", "Güç (0-100)", "Alım?", "Rejim", "Sentiment", "Onchain", "Özet", "Neden"
        symbol = row_dict.get("Sembol", row_dict.get("symbol", "-"))
        price = row_dict.get("Fiyat", row_dict.get("price", 0))
        score = row_dict.get("Skor", row_dict.get("recommendation_score", 0))
        strength = row_dict.get("Güç (0-100)", row_dict.get("strength", 0))
        entry_ok = row_dict.get("Alım?", row_dict.get("entry_ok", False))
        regime = row_dict.get("Rejim", row_dict.get("regime", "-"))
        sentiment = row_dict.get("Sentiment", row_dict.get("sentiment", 0))
        # onchain = row_dict.get("Onchain", row_dict.get("onchain_metric", 0)) # Unused
        summary = row_dict.get("Özet", row_dict.get("why", ""))
        reason = row_dict.get("Neden", row_dict.get("reason", ""))

        is_buy = str(entry_ok).lower() in {"1", "true", "evet", "al", "yes"}
        badge_type = "buy" if is_buy else "hold"
        badge_label = "AL" if is_buy else "İzle"

        # Reconstruct data dict for chips
        chip_data = {
            "momentum_best_zscore": row_dict.get(
                "momentum_best_zscore"
            ),  # Might be missing in pretty df
            "strength": strength,
            "regime": regime,
            "risk_reward": row_dict.get("risk_reward"),  # Might be missing
        }
        chips = compose_signal_chips(chip_data)
        chip_row_html = ""
        if chips:
            chip_row_html = "<div class='status-chip-row'>" + "".join(chips) + "</div>"

        symbol_label = escape(str(symbol))
        summary_clean = normalize_narrative(summary)
        reason_clean = normalize_narrative(reason)

        card_html = dedent(
            f"""
            <div class='analysis-card mobile-only'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                    <div style='font-size:1.1rem; font-weight:600; letter-spacing:0.02em;'>{symbol_label}</div>
                    <span class='badge {badge_type}'>{badge_label}</span>
                </div>
                {chip_row_html}
                <div class='metric-grid'>
                    <div>
                        <div class='metric-label'>Fiyat</div>
                        <div class='metric-value'>{format_decimal(price)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Skor</div>
                        <div class='metric-value'>{format_decimal(score, precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Güç</div>
                        <div class='metric-value'>{format_decimal(strength, precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Sentiment</div>
                        <div class='metric-value'>{format_decimal(sentiment)}</div>
                    </div>
                </div>
                <div style='font-size:0.9rem; color:#e2e8f0; margin-bottom:4px;'>{escape(summary_clean)}</div>
                <div style='font-size:0.78rem; color:rgba(148,163,184,0.75);'>{escape(reason_clean)}</div>
            </div>
            """
        ).strip()
        cards.append(card_html)

    if cards:
        st.markdown(
            "<div style='display:flex; flex-direction:column; gap:14px; margin-top:18px;'>"
            + "".join(cards)
            + "</div>",
            unsafe_allow_html=True,
        )


def detect_symbol_column(df: pd.DataFrame):
    cols = {c.lower(): c for c in df.columns}
    for name in ["symbol", "ticker"]:
        if name in cols:
            return cols[name]
    return None


def extract_symbols_from_df(df: pd.DataFrame):
    cand = detect_symbol_column(df)
    if cand is None:
        return []
    series = df[cand].dropna().astype(str).map(lambda x: x.strip().upper())
    return [s for s in series.unique().tolist() if s]


@lru_cache(maxsize=1)
def load_settingscard_markup():
    """Load the compiled SettingsCard bundle and inline CSS/JS for Streamlit."""
    dist_dir = Path(__file__).resolve().parent.parent / "SettingsCard" / "dist"
    index_path = dist_dir / "index.html"
    if not index_path.exists():
        return None, "SettingsCard derlemesi bulunamadı. Lütfen önce Vite build çalıştırın."

    html = index_path.read_text(encoding="utf-8")
    css_match = re.search(r'href="(?P<href>[^\"]+\.css)"', html)
    js_match = re.search(r'src="(?P<src>[^\"]+\.js)"', html)

    if js_match is None:
        return None, "SettingsCard index.html içinde JS kaynağı bulunamadı."

    css_content = ""
    if css_match:
        css_path = dist_dir / css_match.group("href").lstrip("/")
        if css_path.exists():
            css_content = css_path.read_text(encoding="utf-8").replace("</style", "<\\/style")

    js_path = dist_dir / js_match.group("src").lstrip("/")
    if not js_path.exists():
        return None, f"JS asset eksik: {js_path.name}"

    js_content = js_path.read_text(encoding="utf-8").replace("</script", "<\\/script")

    markup = f"""<!doctype html>
<html lang=\"tr\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
    <style>{css_content}</style>
  </head>
  <body>
    <div id=\"root\"></div>
    <script type=\"module\">{js_content}</script>
  </body>
</html>"""
    return markup, None


def render_settings_card(height: int = 860):
    """Render the SettingsCard React bundle or show a helpful warning."""
    markup, error = load_settingscard_markup()
    if error:
        st.warning(error)
        st.info(
            "`SettingsCard/dist/` içeriğini oluşturmak için projede `npm run build` çalıştırın."
        )
        return

    if not markup:
        st.warning("SettingsCard içeriği yüklenemedi.")
        return

    components.html(markup, height=height, scrolling=True)


@st.cache_data(ttl=900, show_spinner="🔍 Araştırma yapılıyor...")
def get_gemini_research(symbol: str, language: str = "tr") -> str:
    """
    Fetches research data using DuckDuckGo for news and Gemini for analysis.
    Requires GOOGLE_API_KEY in environment variables or st.secrets.
    """
    if not genai or not DDGS:
        return "⚠️ Gerekli kütüphaneler (google-generativeai, duckduckgo-search) yüklü değil."

    api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

    if not api_key:
        return "⚠️ Google API anahtarı bulunamadı. Lütfen ayarlarınıza (st.secrets) 'GOOGLE_API_KEY' ekleyin."

    try:
        # 1. DuckDuckGo ile Haber Arama (Çok Dilli: EN + DE + TR)
        results = []
        with DDGS() as ddgs:

            def safe_search(query, region="wt-wt", timelimit="w", max_results=3):
                """Hata korumalı ve fallback mekanizmalı arama fonksiyonu"""
                try:
                    # 1. Deneme: İstenen zaman aralığında (örn: son 1 hafta)
                    res = list(
                        ddgs.news(
                            query,
                            region=region,
                            safesearch="off",
                            timelimit=timelimit,
                            max_results=max_results,
                        )
                    )
                    if res:
                        return res

                    # 2. Deneme (Fallback): Eğer sonuç yoksa zaman kısıtını kaldır
                    if timelimit:
                        # print(f"Fallback devreye girdi: {query}")
                        return list(
                            ddgs.news(
                                query,
                                region=region,
                                safesearch="off",
                                timelimit=None,
                                max_results=max_results,
                            )
                        )
                except Exception as e:
                    print(f"DDG Arama Hatası ({query}): {e}")
                    return []
                return []

            # İngilizce Arama (Genel Finans)
            results.extend(
                safe_search(
                    f"{symbol} stock news finance", region="wt-wt", timelimit="w", max_results=5
                )
            )

            # Yasal ve Regülasyon (SEC, Davalar - Öncelik Son 1 Ay)
            results.extend(
                safe_search(
                    f"{symbol} sec filings lawsuit regulation",
                    region="wt-wt",
                    timelimit="m",
                    max_results=3,
                )
            )

            # Almanca Arama
            results.extend(
                safe_search(
                    f"{symbol} aktie finanzen", region="de-de", timelimit="w", max_results=2
                )
            )

            # Türkçe Arama
            results.extend(
                safe_search(
                    f"{symbol} hisse haber borsa", region="tr-tr", timelimit="w", max_results=3
                )
            )

        if not results:
            return f"⚠️ {symbol} için kaynaklarda erişilebilir haber bulunamadı. (Bağlantı sorunu veya veri eksikliği olabilir)"

        # Tekrarlanan haberleri temizle (URL'ye göre)
        seen_urls = set()
        unique_results = []
        for r in results:
            if r.get("url") not in seen_urls:
                unique_results.append(r)
                seen_urls.add(r.get("url"))

        # İlk 12 haberi al
        news_context = "\n\n".join(
            [
                f"Tarih: {r.get('date', 'Belirsiz')}\nBaşlık: {r['title']}\nKaynak: {r['source']}\nÖzet: {r['body']}"
                for r in unique_results[:12]
            ]
        )

        prompts = {
            "tr": f"""
            Sen uzman bir borsa ve hukuk analistisin. Aşağıdaki **güncel** haberleri (İngilizce, Almanca, Türkçe) kullanarak {symbol} hissesi için kapsamlı bir yatırımcı raporu hazırla.

            Özellikle **yasal gelişmeler, regülasyonlar, davalar ve resmi bildirimlere (SEC/KAP)** dikkat et. Haberlerin tarihlerini göz önünde bulundur ve eski haberleri ele.

            Haberler:
            {news_context}

            İstenen Format:
            1. **Piyasa Algısı:** (Olumlu/Olumsuz/Nötr - Nedenleriyle)
            2. **Yasal ve Regülatif Gelişmeler:** (Varsa davalar, cezalar, onaylar, başvurular)
            3. **Öne Çıkan Finansal Gelişmeler:** (Maddeler halinde)
            4. **Riskler ve Fırsatlar:**
            5. **Sonuç Yorumu:** (Yatırımcı ne yapmalı?)
            """,
            "en": f"""
            You are an expert stock market and legal analyst. Create a comprehensive investor report for {symbol} using the **recent** news below.

            Pay special attention to **legal developments, regulations, lawsuits, and official filings (SEC/KAP)**. Consider the dates of the news and filter out outdated information.

            News:
            {news_context}

            Required Format:
            1. **Market Sentiment:** (Bullish/Bearish/Neutral - With reasons)
            2. **Legal & Regulatory Developments:** (Lawsuits, fines, approvals, filings if any)
            3. **Key Financial Developments:** (Bullet points)
            4. **Risks & Opportunities:**
            5. **Conclusion:** (Actionable advice)
            """,
            "de": f"""
            Sie sind ein erfahrener Börsen- und Rechtsanalyst. Erstellen Sie einen umfassenden Investorenbericht für {symbol} unter Verwendung der folgenden **aktuellen** Nachrichten.

            Achten Sie besonders auf **rechtliche Entwicklungen, Vorschriften, Klagen und offizielle Meldungen**. Berücksichtigen Sie die Daten der Nachrichten.

            Nachrichten:
            {news_context}

            Gewünschtes Format:
            1. **Marktstimmung:** (Positiv/Negativ/Neutral)
            2. **Rechtliche & Regulatorische Entwicklungen:**
            3. **Wichtige Finanzentwicklungen:**
            4. **Risiken & Chancen:**
            5. **Fazit:**
            """,
        }

        prompt = prompts.get(language, prompts["tr"])

        # ------------------------------------------------------------------
        # V2 MİMARİSİ: GROQ CLOUD ENTEGRASYONU (HIZLI & LİMİTSİZ)
        # ------------------------------------------------------------------
        # NOT: Google Gemini yerini dünyanın en hızlı LLM motoru Groq'a bıraktı.
        if Groq:
            try:
                # API anahtarını ortam değişkeninden veya Streamlit secrets'dan oku
                GROQ_API_KEY = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")

                if not GROQ_API_KEY:
                    return _generate_offline_report(
                        symbol,
                        unique_results,
                        language,
                        reason="GROQ_API_KEY ortam değişkeni ayarlanmamış",
                    )

                client = Groq(api_key=GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Updated: llama3-70b-8192 deprecated
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a senior financial analyst. Answer in Markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    top_p=1,
                    stream=False,
                    stop=None,
                )
                return completion.choices[0].message.content
            except Exception as groq_error:
                # Fallback to Offline Report with reason
                return _generate_offline_report(
                    symbol, unique_results, language, reason=f"Groq API Hatası: {str(groq_error)}"
                )
        else:
            return _generate_offline_report(
                symbol, unique_results, language, reason="Groq Kütüphanesi Yüklü Değil"
            )

        # Dead code below due to returns above, but kept for structure if Logic changes
        # return _generate_offline_report(symbol, unique_results, language)

    except Exception as e:
        error_msg = str(e)

        # --- DEBUG info for User ---
        # Groq specific debug
        if Groq and "groq" in error_msg.lower():
            return f"⚠️ Groq Bağlantı Hatası: {error_msg}. (Offline moduna geçildi)"

        # --- FALLBACK MECHANISM ---
        if "429" in error_msg or "ResourceExhausted" in error_msg:
            return _generate_offline_report(
                symbol, unique_results, language, reason="API Kotası Doldu"
            )

        # Generic fallback for other errors to ensure user sees something
        return _generate_offline_report(
            symbol, unique_results, language, reason=f"Hata: {error_msg}"
        )
        # --------------------------

        if "403" in error_msg and "leaked" in error_msg:
            return "⚠️ API Anahtarı Hatası: Kullandığınız Google API anahtarı sızdırıldığı için bloke edilmiş. Lütfen Google AI Studio'dan yeni bir anahtar alıp `.streamlit/secrets.toml` dosyasındaki `GOOGLE_API_KEY` değerini güncelleyin."
        if (
            "API_KEY_HTTP_REFERRER_BLOCKED" in error_msg
            or "Requests from referer <empty> are blocked" in error_msg
        ):
            return "⚠️ API Erişim Hatası: Anahtarınız 'HTTP Referrer' kısıtlamasına sahip ancak bu uygulama bir tarayıcı değil. Lütfen Google Cloud Console'dan anahtar kısıtlamasını 'None' (veya IP bazlı) olarak değiştirin."
        if "404" in error_msg and "not found" in error_msg:
            return "⚠️ Model Bulunamadı: Seçilen model (gemini-2.0-flash-lite) şu an kullanılamıyor. Google, modelleri sık sık güncelliyor. Lütfen 'views/utils.py' dosyasındaki model adını kontrol edin (örn: gemini-2.0-flash)."
        return f"Araştırma sırasında hata oluştu: {error_msg}"


def _generate_offline_report(
    symbol: str, news_items: list, language: str, reason: str = None
) -> str:
    """Gemini API limitine takılınca çalışan basit yedek raporlayıcı."""

    # Başlıklar
    headers = {
        "tr": ["Piyasa Algısı", "Son Haber Özeti", "Riskler & Fırsatlar"],
        "en": ["Market Sentiment", "Recent News Summary", "Risks & Opportunities"],
        "de": ["Marktstimmung", "Zusammenfassung aktueller Nachrichten", "Risiken & Chancen"],
    }
    h = headers.get(language, headers["tr"])

    # Basit bir sentiment analizi (kelime bazlı)
    positive_keywords = [
        "surge",
        "jump",
        "high",
        "profit",
        "growth",
        "yükseldi",
        "rekor",
        "kar",
        "büyüme",
        "buy",
        "al",
        "olumlu",
    ]
    negative_keywords = [
        "drop",
        "fall",
        "loss",
        "crash",
        "düşüş",
        "zarar",
        "kriz",
        "sat",
        "sell",
        "olumsuz",
        "lawsuit",
        "dava",
    ]

    combined_text = " ".join([n["title"].lower() + " " + n["body"].lower() for n in news_items])
    pos_count = sum(1 for k in positive_keywords if k in combined_text)
    neg_count = sum(1 for k in negative_keywords if k in combined_text)

    if pos_count > neg_count:
        sentiment = "🟢 Pozitif / Bullish" if language == "tr" else "🟢 Positive / Bullish"
    elif neg_count > pos_count:
        sentiment = "🔴 Negatif / Bearish" if language == "tr" else "🔴 Negative / Bearish"
    else:
        sentiment = "⚪ Nötr / Neutral" if language == "tr" else "⚪ Neutral"

    reason_text = f" ({reason})" if reason else ""

    report = f"""
    ### ⚠️ AI Limit Modu (Offline & Fallback)
    *Yapay Zeka bağlantısı sağlanamadığı için (Groq/Gemini), bu rapor haberlerin otomatik özetlenmesiyle oluşturulmuştur.*
    *{reason_text if reason else ""}*

    #### 1. {h[0]}
    **{sentiment}**
    (Pozitif Anahtar Kelimeler: {pos_count}, Negatif: {neg_count})

    #### 2. {h[1]}
    """

    for item in news_items[:8]:  # İlk 8 haber
        report += f"- **{item['date']}**: {item['title']} ({item['source']})\n"

    report += f"""
    #### 3. {h[2]}
    - **Fırsat:** Haber akışına göre kısa vadeli volatilite değerlendirilebilir.
    - **Risk:** Otomatik analiz şu an devre dışı olduğu için manuel inceleme önerilir.
    """

    return dedent(report)
