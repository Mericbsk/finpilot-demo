# -*- coding: utf-8 -*-
"""
FinPilot Grid Layout Component
==============================

Responsive CSS Grid layouts for dashboard cards.
Provides consistent, mobile-friendly layouts.

Usage:
    from views.components.grid import render_grid, GridConfig

    with render_grid(columns=4):
        for item in items:
            st.markdown(render_card(item))
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

import streamlit as st

# ============================================
# 📐 Grid Configuration
# ============================================


@dataclass
class GridConfig:
    """Grid layout configuration."""

    columns: int = 4
    gap: str = "1rem"
    min_card_width: str = "250px"

    # Responsive breakpoints
    mobile_columns: int = 1
    tablet_columns: int = 2
    desktop_columns: int = 4

    # Breakpoint values (px)
    mobile_breakpoint: int = 480
    tablet_breakpoint: int = 768


# Default configs for common use cases
GRID_COMPACT = GridConfig(columns=6, gap="0.5rem", min_card_width="150px")
GRID_STANDARD = GridConfig(columns=4, gap="1rem", min_card_width="250px")
GRID_WIDE = GridConfig(columns=3, gap="1.5rem", min_card_width="300px")
GRID_FEATURED = GridConfig(columns=2, gap="2rem", min_card_width="400px")


# ============================================
# 🎨 Grid CSS Generation
# ============================================


def _generate_grid_css(config: GridConfig, container_id: str) -> str:
    """Generate responsive CSS for grid layout."""
    return f"""
    <style>
    #{container_id} {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax({config.min_card_width}, 1fr));
        gap: {config.gap};
        width: 100%;
        padding: 0.5rem 0;
    }}

    /* Mobile */
    @media (max-width: {config.mobile_breakpoint}px) {{
        #{container_id} {{
            grid-template-columns: repeat({config.mobile_columns}, 1fr);
            gap: 0.75rem;
        }}
    }}

    /* Tablet */
    @media (min-width: {config.mobile_breakpoint + 1}px) and (max-width: {config.tablet_breakpoint}px) {{
        #{container_id} {{
            grid-template-columns: repeat({config.tablet_columns}, 1fr);
        }}
    }}

    /* Desktop */
    @media (min-width: {config.tablet_breakpoint + 1}px) {{
        #{container_id} {{
            grid-template-columns: repeat({config.desktop_columns}, 1fr);
        }}
    }}

    /* Grid item styling */
    #{container_id} > div {{
        min-width: 0;  /* Prevent overflow */
    }}
    </style>
    """


def inject_grid_styles() -> None:
    """Inject global responsive grid styles."""
    st.markdown(
        """
    <style>
    /* FinPilot Responsive Grid System */

    .fp-grid {
        display: grid;
        gap: 1rem;
        width: 100%;
    }

    .fp-grid-2 { grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }
    .fp-grid-3 { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
    .fp-grid-4 { grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); }
    .fp-grid-6 { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); }

    /* Card base styling */
    .fp-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        overflow: hidden;
    }

    .fp-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }

    /* Card variants */
    .fp-card-buy {
        border-left: 4px solid #22c55e;
    }

    .fp-card-sell {
        border-left: 4px solid #ef4444;
    }

    .fp-card-hold {
        border-left: 4px solid #94a3b8;
    }

    .fp-card-featured {
        background: linear-gradient(145deg, #1e3a5f, #0f172a);
        border: 2px solid rgba(59, 130, 246, 0.3);
    }

    /* Score bar */
    .fp-score-bar {
        width: 100%;
        height: 6px;
        background: #334155;
        border-radius: 3px;
        overflow: hidden;
        margin-top: 0.5rem;
    }

    .fp-score-bar-fill {
        height: 100%;
        border-radius: 3px;
        transition: width 0.3s ease;
    }

    /* Mobile optimizations */
    @media (max-width: 480px) {
        .fp-card {
            padding: 1rem;
        }

        .fp-grid-4, .fp-grid-6 {
            grid-template-columns: 1fr;
        }
    }

    /* Tablet */
    @media (min-width: 481px) and (max-width: 768px) {
        .fp-grid-4 {
            grid-template-columns: repeat(2, 1fr);
        }

        .fp-grid-6 {
            grid-template-columns: repeat(3, 1fr);
        }
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# ============================================
# 📦 Grid Components
# ============================================


def render_grid_start(grid_class: str = "fp-grid-4", custom_id: Optional[str] = None) -> None:
    """
    Start a grid container.

    Args:
        grid_class: CSS class for grid (fp-grid-2, fp-grid-3, fp-grid-4, fp-grid-6)
        custom_id: Optional custom ID for the grid
    """
    id_attr = f'id="{custom_id}"' if custom_id else ""
    st.markdown(f'<div class="fp-grid {grid_class}" {id_attr}>', unsafe_allow_html=True)


def render_grid_end() -> None:
    """End a grid container."""
    st.markdown("</div>", unsafe_allow_html=True)


def render_card_html(
    symbol: str,
    price: float,
    score: float,
    is_buy: bool = False,
    regime: str = "-",
    target: Optional[float] = None,
    stop: Optional[float] = None,
    extra_content: str = "",
) -> str:
    """
    Generate HTML for a signal card.

    Args:
        symbol: Stock symbol
        price: Current price
        score: Recommendation score (0-100)
        is_buy: Whether this is a buy signal
        regime: Market regime
        target: Take profit target
        stop: Stop loss level
        extra_content: Additional HTML content

    Returns:
        Card HTML string
    """
    variant = "fp-card-buy" if is_buy else "fp-card-hold"
    score_color = "#22c55e" if score >= 80 else "#eab308" if score >= 60 else "#ef4444"
    badge = (
        '<span style="background:#22c55e; color:white; padding:2px 8px; border-radius:4px; font-size:0.7rem;">AL</span>'
        if is_buy
        else ""
    )

    targets_html = ""
    if target is not None and stop is not None:
        targets_html = f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.85rem; margin-top: 1rem;">
            <div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: 6px; text-align: center;">
                <div style="color: #94a3b8; font-size: 0.7rem;">HEDEF</div>
                <div style="color: #22c55e; font-weight: 600;">${target:.2f}</div>
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 0.5rem; border-radius: 6px; text-align: center;">
                <div style="color: #94a3b8; font-size: 0.7rem;">STOP</div>
                <div style="color: #ef4444; font-weight: 600;">${stop:.2f}</div>
            </div>
        </div>
        """

    return f"""
    <div class="fp-card {variant}">
        <div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: {score_color};"></div>

        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div>
                <h3 style="margin: 0; font-size: 1.5rem; font-weight: 800; color: #f8fafc;">
                    {symbol} {badge}
                </h3>
                <span style="font-size: 0.9rem; color: #94a3b8;">{regime}</span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.3rem; font-weight: 700; color: #f8fafc;">${price:.2f}</div>
            </div>
        </div>

        <div style="margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                <span style="font-size: 0.8rem; color: #94a3b8;">Sinyal Gücü</span>
                <span style="font-size: 0.8rem; font-weight: 600; color: {score_color};">{score:.1f}/100</span>
            </div>
            <div class="fp-score-bar">
                <div class="fp-score-bar-fill" style="width: {score}%; background: {score_color};"></div>
            </div>
        </div>

        {targets_html}
        {extra_content}
    </div>
    """


def render_signal_cards_grid(df, limit: int = 8, grid_class: str = "fp-grid-4") -> None:
    """
    Render signal cards in a responsive grid.

    Args:
        df: DataFrame with signal data
        limit: Maximum number of cards to show
        grid_class: Grid class for layout
    """
    if df is None or df.empty:
        st.info("📭 Gösterilecek sinyal yok.")
        return

    # Inject styles
    inject_grid_styles()

    # Filter and sort
    display_df = df.copy()
    if "recommendation_score" in display_df.columns:
        display_df = display_df.sort_values("recommendation_score", ascending=False)

    # Generate cards HTML
    cards_html = []
    for _, row in display_df.head(limit).iterrows():
        card = render_card_html(
            symbol=row.get("symbol", "-"),
            price=row.get("price", 0),
            score=row.get("recommendation_score", 50),
            is_buy=row.get("entry_ok", False),
            regime=row.get("regime", "-"),
            target=row.get("take_profit"),
            stop=row.get("stop_loss"),
        )
        cards_html.append(card)

    # Render grid
    st.markdown(f'<div class="fp-grid {grid_class}">', unsafe_allow_html=True)
    st.markdown("".join(cards_html), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_metric_grid(metrics: List[dict], grid_class: str = "fp-grid-4") -> None:
    """
    Render metric cards in a grid.

    Args:
        metrics: List of dicts with label, value, delta (optional), color (optional)
        grid_class: Grid class for layout
    """
    inject_grid_styles()

    cards_html = []
    for m in metrics:
        label = m.get("label", "-")
        value = m.get("value", "-")
        delta = m.get("delta")
        color = m.get("color", "#f8fafc")

        delta_html = ""
        if delta is not None:
            delta_color = "#22c55e" if delta >= 0 else "#ef4444"
            delta_sign = "+" if delta >= 0 else ""
            delta_html = (
                f'<span style="color: {delta_color}; font-size: 0.8rem;">{delta_sign}{delta}</span>'
            )

        cards_html.append(
            f"""
        <div class="fp-card" style="text-align: center; padding: 1rem;">
            <div style="color: #94a3b8; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">
                {label}
            </div>
            <div style="color: {color}; font-size: 1.5rem; font-weight: 700;">
                {value}
            </div>
            {delta_html}
        </div>
        """
        )

    st.markdown(f'<div class="fp-grid {grid_class}">', unsafe_allow_html=True)
    st.markdown("".join(cards_html), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


__all__ = [
    "GridConfig",
    "GRID_COMPACT",
    "GRID_STANDARD",
    "GRID_WIDE",
    "GRID_FEATURED",
    "inject_grid_styles",
    "render_grid_start",
    "render_grid_end",
    "render_card_html",
    "render_signal_cards_grid",
    "render_metric_grid",
]
