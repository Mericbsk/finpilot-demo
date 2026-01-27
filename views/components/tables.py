# -*- coding: utf-8 -*-
"""
FinPilot Tables
===============
UI bileşenleri: tablo görünümleri.
"""

import datetime
from html import escape
from textwrap import dedent

import pandas as pd
import streamlit as st

from views.components.chips import compose_signal_chips
from views.components.helpers import format_decimal


def render_buyable_table(df: pd.DataFrame) -> None:
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
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
        """
    ).strip()
    st.markdown(table_html, unsafe_allow_html=True)
