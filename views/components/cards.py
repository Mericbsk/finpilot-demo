# -*- coding: utf-8 -*-
"""
FinPilot Cards
==============
UI bileşenleri: kart görünümleri.
"""

import datetime
from html import escape
from textwrap import dedent

import pandas as pd
import streamlit as st

import scanner
from views.components.chips import compose_signal_chips
from views.components.helpers import (
    build_badge_html,
    format_decimal,
    format_timestamp_display,
    get_regime_hint,
    get_sentiment_hint,
    normalize_narrative,
)


def render_buyable_cards(df: pd.DataFrame, limit: int = 6) -> None:
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
                    <div style='font-size:1.25rem; font-weight:700; letter-spacing:0.04em;'>{data.get('symbol','-')}</div>
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


def render_symbol_snapshot(df: pd.DataFrame, limit: int = 6) -> None:
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
    col_total.metric(
        "Toplam Sembol", f"{total_symbols}", help="Tarama listesindeki toplam sembol sayısı"
    )
    buyable_delta = f"%{format_decimal(buyable_ratio, precision=1)}"
    col_buyable.metric(
        "Alım Fırsatı",
        f"{buyable_count}",
        delta=buyable_delta if total_symbols else None,
        help="Alım kriterlerini karşılayan sembol sayısı ve toplam içindeki yüzdesi",
    )
    col_rr.metric(
        "Ortalama R/R",
        format_decimal(avg_rr) if avg_rr is not None else "-",
        help="Risk/Ödül Oranı: Potansiyel kazanç / Potansiyel kayıp. 2.0+ değerler tercih edilir.",
    )

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
        badge_html = build_badge_html(entry_ok)
        timestamp_display = format_timestamp_display(row.get("timestamp"))

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


def render_signal_history_overview(df: pd.DataFrame, limit: int = 5) -> None:
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
    col_total.metric(
        "Toplam Sinyal", f"{total_signals}", help="Seçilen dönemde üretilen toplam sinyal sayısı"
    )
    col_buyable.metric(
        "Alım Fırsatı",
        f"{buyable_count}",
        delta=f"%{success_rate:.1f}" if total_signals else None,
        help="Alım sinyali verilen semboller ve toplam içindeki başarı oranı",
    )
    col_score.metric(
        "Ortalama Skor",
        format_decimal(avg_score, precision=1) if avg_score is not None else "-",
        help="Sinyal kalite skoru ortalaması (0-100). Yüksek değerler daha güçlü sinyalleri gösterir.",
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
        badge_html = build_badge_html(entry_ok, font_size="0.72rem")

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
                        {escape(summary) if summary else 'Özet bulunamadı.'}
                    </div>
                    <div style='font-size:0.78rem; color:rgba(148,163,184,0.8);'>
                        {escape(reason) if reason else 'Detay bilgisi bulunamadı.'}
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


def render_mobile_symbol_cards(df: pd.DataFrame) -> None:
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
        timestamp_display = format_timestamp_display(row_dict.get("timestamp"))
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
                        <div class='metric-value'>{format_decimal(row_dict.get('price'))}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Skor</div>
                        <div class='metric-value'>{format_decimal(row_dict.get('score'), precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Filtre</div>
                        <div class='metric-value'>{format_decimal(row_dict.get('filter_score'), precision=0)}</div>
                    </div>
                    <div>
                        <div class='metric-label'>R/R</div>
                        <div class='metric-value'>{format_decimal(row_dict.get('risk_reward'))}</div>
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


def render_mobile_recommendation_cards(df: pd.DataFrame) -> None:
    """Render a compact card stack for recommendation results on mobile viewports."""
    if df is None or df.empty:
        return

    df_cards = df.fillna("")

    cards = []
    for _, row in df_cards.iterrows():
        row_dict = row.to_dict()
        symbol = row_dict.get("Sembol", row_dict.get("symbol", "-"))
        price = row_dict.get("Fiyat", row_dict.get("price", 0))
        score = row_dict.get("Skor", row_dict.get("recommendation_score", 0))
        strength = row_dict.get("Güç (0-100)", row_dict.get("strength", 0))
        entry_ok = row_dict.get("Alım?", row_dict.get("entry_ok", False))
        regime = row_dict.get("Rejim", row_dict.get("regime", "-"))
        sentiment = row_dict.get("Sentiment", row_dict.get("sentiment", 0))
        summary = row_dict.get("Özet", row_dict.get("why", ""))
        reason = row_dict.get("Neden", row_dict.get("reason", ""))

        is_buy = str(entry_ok).lower() in {"1", "true", "evet", "al", "yes"}
        badge_type = "buy" if is_buy else "hold"
        badge_label = "AL" if is_buy else "İzle"

        chip_data = {
            "momentum_best_zscore": row_dict.get("momentum_best_zscore"),
            "strength": strength,
            "regime": regime,
            "risk_reward": row_dict.get("risk_reward"),
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
