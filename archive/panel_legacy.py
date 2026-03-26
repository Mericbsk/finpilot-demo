import datetime
import glob
import math
import os
import re
from functools import lru_cache
from html import escape
from pathlib import Path
from textwrap import dedent

import pandas as pd
import scanner
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
from scanner import build_explanation, build_reason, compute_recommendation_score, load_symbols

st.set_page_config(page_title="FinPilot Panel", layout="wide", page_icon="🛫")


def is_advanced_view() -> bool:
    return st.session_state.get("view_mode", "advanced") == "advanced"


GLOBAL_CSS = """
<style>
    border:1px solid transparent;
    }
    .status-badge.badge-idle {
        background:rgba(148, 163, 184, 0.25);
        border-color:rgba(148, 163, 184, 0.35);
        color:#e2e8f0;
    }
    .status-badge.badge-loading {
        background:rgba(14, 165, 233, 0.18);
        border-color:rgba(14, 165, 233, 0.45);
        color:#38bdf8;
    }
    .status-badge.badge-success {
        background:rgba(34, 197, 94, 0.18);
        border-color:rgba(34, 197, 94, 0.4);
        color:#4ade80;
    }
    .status-badge.badge-error {
        background:rgba(239, 68, 68, 0.18);
        border-color:rgba(239, 68, 68, 0.4);
        color:#fca5a5;
    }
    .cta-sticky .cta-primary .stButton>button {
        width: 100%;
        padding: 0.9rem 1.4rem;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 14px;
        border: none;
        background: linear-gradient(90deg,#00e6e6,#0ea5e9);
        color: #0f172a;
        box-shadow: 0 20px 60px -25px rgba(14,165,233,0.75);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .cta-sticky .cta-primary .stButton>button:hover {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 32px 76px -26px rgba(14,165,233,0.95);
    }
    .cta-sticky .cta-secondary .stButton>button {
        width: 100%;
        padding: 0.85rem 1.2rem;
        font-weight: 600;
        border-radius: 14px;
        border: 1px solid rgba(0, 230, 230, 0.35);
        background: rgba(15, 23, 42, 0.55);
        color: #cbd5f5;
        transition: transform 0.25s ease, background 0.25s ease, box-shadow 0.25s ease;
    }
    .cta-sticky .cta-secondary .stButton>button:hover {
        transform: translateY(-1px);
        background: rgba(14, 165, 233, 0.22);
        color: #fff;
        box-shadow: 0 18px 48px -28px rgba(14,165,233,0.55);
    }
    .cta-sticky .cta-tertiary .stButton>button {
        width: 100%;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        background: rgba(15,23,42,0.35);
        border: 1px dashed rgba(148, 163, 184, 0.45);
        color: #cbd5f5;
        font-weight: 500;
    }
    .analysis-empty {
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        padding: 32px;
        background: rgba(30, 41, 59, 0.65);
    }
    .analysis-empty h3 {
        color: #e2e8f0;
    }
    .analysis-card {
        border-radius: 16px;
        background: rgba(15,23,42,0.7);
        border: 1px solid rgba(148,163,184,0.25);
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 12px 28px -18px rgba(14,165,233,0.45);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    .analysis-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.35);
        box-shadow: 0 28px 64px -36px rgba(14,165,233,0.65);
    }
    .analysis-card .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 14px;
    }
    .analysis-card .badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.82rem;
        letter-spacing: 0.02em;
    }
    .analysis-card .badge.buy {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .analysis-card .badge.hold {
        background: rgba(148, 163, 184, 0.18);
        color: #cbd5f5;
        border: 1px solid rgba(148, 163, 184, 0.35);
    }
    .analysis-card .badge.sell {
        background: rgba(239, 68, 68, 0.18);
        color: #fca5a5;
        border: 1px solid rgba(239, 68, 68, 0.35);
    }
    .analysis-card .badge.info {
        background: rgba(59, 130, 246, 0.18);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.35);
    }
    .analysis-card .badge[title] {
        cursor: help;
    }
    .analysis-card .metric-label {
        color: rgba(226, 232, 240, 0.65);
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .analysis-card .metric-value {
        font-size: 1.2rem;
        font-weight: 600;
        color: #fff;
    }
    .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .status-chip.success {
        background: rgba(34, 197, 94, 0.18);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .status-chip.warning {
        background: rgba(249, 115, 22, 0.18);
        color: #fb923c;
        border: 1px solid rgba(249, 115, 22, 0.35);
    }
    .status-chip.neutral {
        background: rgba(148, 163, 184, 0.18);
        color: rgba(226, 232, 240, 0.85);
        border: 1px solid rgba(148, 163, 184, 0.25);
    }
    .status-chip .chip-icon {
        font-size: 0.9rem;
        line-height: 1;
    }
    .status-chip-row,
    .chip-stack {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
    }
    .chip-stack {
        margin-top: 6px;
    }
    .info-banner {
        border-radius: 16px;
        border: 1px solid rgba(59, 130, 246, 0.35);
        background: rgba(15, 23, 42, 0.72);
        padding: 16px 20px;
        margin-bottom: 20px;
        display: flex;
        gap: 14px;
        align-items: flex-start;
    }
    .info-banner .icon {
        font-size: 1.3rem;
    }
    .info-banner .content {
        color: rgba(226, 232, 240, 0.9);
        font-size: 0.92rem;
    }
    .view-mode-toggle {
        margin: 18px 0 26px;
        padding: 18px 22px;
        background: rgba(15, 23, 42, 0.72);
        border: 1px solid rgba(148, 163, 184, 0.24);
        border-radius: 18px;
        box-shadow: 0 18px 44px -36px rgba(14, 165, 233, 0.45);
    }
    .view-mode-toggle .toggle-intro h4 {
        margin: 0 0 6px;
        font-size: 1.02rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(226, 232, 240, 0.92);
    }
    .view-mode-toggle .toggle-intro p {
        margin: 0;
        color: rgba(148, 163, 184, 0.85);
        font-size: 0.9rem;
    }
    .summary-panel {
        border-radius: 18px;
        border: 1px solid rgba(34, 197, 94, 0.28);
        background: rgba(15, 23, 42, 0.8);
        padding: 22px 24px;
        margin-top: 24px;
        box-shadow: 0 26px 60px -40px rgba(34, 197, 94, 0.55);
    }
    .summary-panel h4 {
        margin: 0 0 12px;
        font-size: 1.1rem;
        letter-spacing: 0.04em;
        color: #bbf7d0;
    }
    .summary-panel ul {
        margin: 0;
        padding: 0;
        list-style: none;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 12px;
    }
    .summary-panel li {
        display: flex;
        gap: 8px;
        align-items: center;
        color: rgba(226,232,240,0.88);
    }
    .summary-panel li span.icon {
        font-size: 1rem;
    }
    .process-intro {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 22px 26px;
        margin-bottom: 24px;
        box-shadow: 0 22px 48px -36px rgba(14, 165, 233, 0.55);
    }
    .process-intro p {
        margin: 0 0 10px;
        color: rgba(226, 232, 240, 0.92);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .process-intro p:last-child {
        margin-bottom: 0;
    }
    .process-status {
        border-radius: 20px;
        border: 1px solid rgba(30, 64, 175, 0.35);
        background: linear-gradient(145deg, rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.68));
        padding: 22px 26px;
        margin-bottom: 24px;
        box-shadow: 0 18px 42px -30px rgba(59, 130, 246, 0.55);
    }
    .process-status .status-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 16px;
    }
    .process-status .status-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: rgba(148, 163, 184, 0.75);
        display: block;
    }
    .process-status .status-subtitle {
        color: rgba(226, 232, 240, 0.92);
        font-weight: 600;
        font-size: 1rem;
        margin-top: 6px;
        display: block;
    }
    .process-status .status-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #38bdf8;
        min-width: 64px;
        text-align: right;
    }
    .process-progress-bar {
        height: 12px;
        border-radius: 999px;
        background: rgba(30, 41, 59, 0.85);
        overflow: hidden;
        position: relative;
    }
    .process-progress-bar__inner {
        height: 100%;
        background: linear-gradient(90deg, #0ea5e9 0%, #38bdf8 100%);
        transition: width 0.6s ease;
    }
    .process-progress-bar__inner.active {
        background: linear-gradient(90deg, #0ea5e9 0%, #38bdf8 100%);
    }
    .process-progress-bar__inner.error {
        background: linear-gradient(90deg, #f97316 0%, #ef4444 100%);
    }
    .process-progress-bar__inner.completed {
        background: linear-gradient(90deg, #34d399 0%, #22c55e 100%);
    }
    .process-current {
        margin-top: 12px;
        color: rgba(148, 163, 184, 0.78);
        font-size: 0.88rem;
    }
    .process-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 18px;
    }
    .process-card {
        border-radius: 18px;
        border: 1px solid rgba(59, 130, 246, 0.25);
        background: rgba(15, 23, 42, 0.72);
        padding: 18px 20px;
        display: flex;
        flex-direction: column;
        gap: 14px;
        position: relative;
        min-height: 220px;
        box-shadow: 0 20px 40px -34px rgba(14, 165, 233, 0.55);
        transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .process-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 24px 50px -28px rgba(14, 165, 233, 0.7);
    }
    .process-card.completed {
        border-color: rgba(34, 197, 94, 0.35);
        box-shadow: 0 20px 46px -34px rgba(34, 197, 94, 0.55);
    }
    .process-card.active {
        border-color: rgba(14, 165, 233, 0.45);
    }
    .process-card.upcoming {
        border-color: rgba(148, 163, 184, 0.22);
        box-shadow: none;
    }
    .process-card.error {
        border-color: rgba(248, 113, 113, 0.4);
        box-shadow: 0 20px 46px -34px rgba(248, 113, 113, 0.55);
    }
    .process-card .card-header {
        display: flex;
        gap: 12px;
        align-items: flex-start;
    }
    .process-card .card-icon {
        font-size: 1.6rem;
        line-height: 1;
    }
    .process-card .card-title {
        font-size: 1.05rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        color: #f8fafc;
        margin-bottom: 6px;
    }
    .process-card .state-tag {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }
    .process-card.completed .state-tag {
        background: rgba(34, 197, 94, 0.18);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.35);
    }
    .process-card.active .state-tag {
        background: rgba(14, 165, 233, 0.18);
        color: #38bdf8;
        border: 1px solid rgba(14, 165, 233, 0.35);
    }
    .process-card.upcoming .state-tag {
        background: rgba(148, 163, 184, 0.18);
        color: rgba(226, 232, 240, 0.7);
        border: 1px solid rgba(148, 163, 184, 0.25);
    }
    .process-card.error .state-tag {
        background: rgba(248, 113, 113, 0.18);
        color: #fca5a5;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }
    .process-card .card-body {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }
    .process-card .card-row {
        display: grid;
        grid-template-columns: auto 1fr auto;
        gap: 10px;
        align-items: flex-start;
    }
    .process-card .row-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(148, 163, 184, 0.75);
        padding-top: 3px;
        white-space: nowrap;
    }
    .process-card .row-text {
        color: rgba(226, 232, 240, 0.9);
        font-size: 0.9rem;
        line-height: 1.45;
    }
    .process-card .tooltip-icon {
        font-size: 0.78rem;
        opacity: 0.65;
        cursor: help;
        padding-top: 2px;
    }
    .process-card .tooltip-icon:hover {
        opacity: 1;
    }
    @media (max-width: 992px) {
        .process-grid {
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        }
    }
    @media (max-width: 640px) {
        .process-intro {
            padding: 18px 20px;
        }
        .process-card {
            padding: 16px;
        }
        .process-card .card-row {
            grid-template-columns: 1fr;
        }
        .process-card .tooltip-icon {
            display: none;
        }
    }
    .cta-sticky .cta-tertiary .stButton>button:hover {
        background: rgba(148, 163, 184, 0.12);
        border-color: rgba(148, 163, 184, 0.65);
    }
    .stepper {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 16px 20px;
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.16);
        background: rgba(15, 23, 42, 0.6);
        margin-bottom: 24px;
        box-shadow: 0 16px 36px -28px rgba(14, 165, 233, 0.55);
    }
    .stepper::-webkit-scrollbar { display: none; }
    .step {
        display: flex;
        flex-direction: column;
        gap: 6px;
        min-width: 0;
        flex: 1;
        position: relative;
    }
    .step .bullet {
        width: 36px;
        height: 36px;
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        color: #0f172a;
        background: rgba(148, 163, 184, 0.35);
        transition: all 0.25s ease;
    }
    .step .label {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 0.9rem;
        color: rgba(226, 232, 240, 0.7);
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .step .label-icon {
        font-size: 1rem;
    }
    .step .label-text {
        white-space: nowrap;
    }
    .step.completed .bullet {
        background: linear-gradient(90deg, #22d3ee, #3b82f6);
        box-shadow: 0 18px 46px -28px rgba(14, 165, 233, 0.75);
    }
    .step.completed .label {
        color: #bae6fd;
    }
    .step.active .bullet {
        background: rgba(14, 165, 233, 0.9);
        box-shadow: 0 24px 52px -26px rgba(14, 165, 233, 0.85);
    }
    .step.active .label {
        color: #e2e8f0;
    }
    .step-line {
        flex: 0 0 42px;
        height: 2px;
        border-radius: 999px;
        background: rgba(148, 163, 184, 0.28);
        transition: background 0.25s ease;
    }
    .step-line.completed {
        background: linear-gradient(90deg, #0ea5e9, #22d3ee);
    }
    .step-line.active {
        background: rgba(14, 165, 233, 0.65);
    }
    .section-gap {
        width: 100%;
        height: 28px;
    }
    .upload-shell {
        border-radius: 16px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        background: rgba(15, 23, 42, 0.55);
        padding: 18px 20px;
    }
    .guide-tooltip {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 14px;
        background: rgba(14, 165, 233, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.35);
        color: #e0f2fe;
        font-size: 0.9rem;
        margin-bottom: 16px;
        box-shadow: 0 18px 36px -30px rgba(14, 165, 233, 0.6);
    }
    .guide-tooltip .icon {
        font-size: 1.1rem;
    }
    .demo-note {
        border-radius: 16px;
        border: 1px dashed rgba(56, 189, 248, 0.45);
        background: rgba(14, 165, 233, 0.1);
        padding: 18px 20px;
        color: #e0f2fe;
        margin: 18px 0;
    }
    .action-checklist {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(56, 189, 248, 0.35);
        border-radius: 24px;
        padding: 28px 32px;
        margin: 36px 0 18px;
        box-shadow: 0 28px 64px -42px rgba(14, 165, 233, 0.7);
        transition: border-color 0.25s ease, box-shadow 0.25s ease;
    }
    .action-checklist h3 {
        margin: 0 0 10px;
        font-size: 1.45rem;
        letter-spacing: 0.04em;
        color: #f8fafc;
    }
    .action-checklist p.lead {
        margin: 0 0 22px;
        color: rgba(226, 232, 240, 0.85);
        font-size: 0.98rem;
    }
    .action-checklist .checklist-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 18px;
    }
    .action-checklist .bucket {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 20px 22px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        box-shadow: 0 20px 48px -38px rgba(14, 165, 233, 0.45);
        transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
    }
    .action-checklist .bucket:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.32);
        box-shadow: 0 26px 58px -34px rgba(14, 165, 233, 0.6);
    }
    .action-checklist .bucket h4 {
        margin: 0;
        font-size: 1.05rem;
        color: #e2e8f0;
        letter-spacing: 0.03em;
    }
    .action-checklist .bucket h4 span {
        margin-right: 10px;
    }
    .action-checklist ul {
        margin: 0;
        padding: 0;
        list-style: none;
        display: flex;
        flex-direction: column;
        gap: 12px;
    }
    .action-checklist li {
        display: flex;
        gap: 10px;
        align-items: flex-start;
        color: rgba(226, 232, 240, 0.9);
        font-size: 0.93rem;
        line-height: 1.45;
    }
    .action-checklist li span.icon {
        font-size: 1.15rem;
        line-height: 1.15;
        color: #38bdf8;
    }
    @media (max-width: 768px) {
        .action-checklist {
            padding: 24px;
        }
    }
    .desktop-table {
        display: block;
    }
    .signal-table-wrapper {
        border-radius: 18px;
        border: 1px solid rgba(59, 130, 246, 0.25);
        background: rgba(15, 23, 42, 0.82);
        overflow: hidden;
        box-shadow: 0 22px 54px -36px rgba(14, 165, 233, 0.45);
        margin-bottom: 20px;
    }
    .signal-table {
        width: 100%;
        border-collapse: collapse;
    }
    .signal-table th,
    .signal-table td {
        padding: 14px 16px;
        border-bottom: 1px solid rgba(148, 163, 184, 0.16);
        color: rgba(226, 232, 240, 0.92);
        font-size: 0.92rem;
        text-align: left;
    }
    .signal-table th {
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(148, 163, 184, 0.75);
    }
    .signal-table td.numeric {
        text-align: right;
        font-variant-numeric: tabular-nums;
    }
    .signal-table tbody tr:hover {
        background: rgba(56, 189, 248, 0.08);
    }
    .signal-table tbody tr:last-child td {
        border-bottom: none;
    }
    .signal-table .symbol-cell {
        min-width: 160px;
    }
    .signal-table .timestamp-cell {
        white-space: nowrap;
        font-size: 0.85rem;
        color: rgba(148, 163, 184, 0.85);
    }
    .mobile-card-stack {
        display: none;
    }
    .analysis-card.mobile-only {
        display: none;
    }
    @media (max-width: 900px) {
        .cta-sticky {
            top: 78px;
            padding: 14px;
        }
        .analysis-card .metric-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .layout-grid {
            padding: 0 1.1rem;
        }
        .action-checklist .checklist-grid,
        .summary-panel ul {
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        }
        .stepper {
            gap: 12px;
            padding: 14px 16px;
        }
        .section-gap {
            height: 22px;
        }
        .guide-tooltip {
            font-size: 0.85rem;
            margin-bottom: 14px;
        }
        .desktop-table {
            display: none !important;
        }
        .signal-table-wrapper {
            display: none !important;
        }
        .mobile-card-stack {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .analysis-card.mobile-only {
            display: block;
        }
    }
    @media (max-width: 600px) {
        .analysis-card .metric-grid {
            grid-template-columns: repeat(1, minmax(0, 1fr));
        }
        .stepper {
            padding: 12px 14px;
            gap: 10px;
            overflow-x: auto;
        }
        .step-line {
            flex: 0 0 32px;
        }
        .step .label-text {
            display: none;
        }
        .section-gap {
            height: 16px;
        }
        .upload-shell {
            padding: 16px;
        }
        .guide-tooltip {
            font-size: 0.82rem;
            padding: 10px 14px;
            margin-bottom: 12px;
        }
        .demo-note {
            padding: 16px;
            margin: 16px 0;
        }
        .layout-grid {
            padding: 0 0.85rem;
        }
        .action-checklist .checklist-grid,
        .summary-panel ul {
            grid-template-columns: 1fr;
        }
    }
    </style>
"""


st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


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


if "has_seen_landing" not in st.session_state:
    st.session_state.has_seen_landing = False

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "advanced"

if "view_mode_choice" not in st.session_state:
    st.session_state.view_mode_choice = "Gelişmiş"


def render_finpilot_landing():
    hero_section = """
        <div class='layout-grid'>
            <div style='background: linear-gradient(100deg,#131b2b 55%,#1e2b40 100%); border-radius:24px; padding:50px 36px; margin-bottom:36px; box-shadow:0 24px 60px -32px rgba(8,47,73,0.65);'>
                <div style='display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:32px;'>
                    <div style='flex:2; min-width:290px;'>
                        <span style='font-size:3em; font-weight:800; color:#00e6e6; letter-spacing:0.02em;'>FinPilot</span><br>
                        <span style='font-size:1.6em; font-weight:500; color:#f8fafc;'>Yapay zekâ destekli alım-satım kokpitin.</span><br>
                        <span style='font-size:1.1em; color:rgba(186,228,236,0.92);'>Riskini otomatik yönet, fırsatları sırala, kararlarını veriye bağla.</span>
                        <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; margin-top:28px;'>
                            <div style='background:rgba(30,41,59,0.65); border-radius:16px; padding:20px 22px;'>
                                <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                                    <span style='font-size:2rem;'>⚡</span>
                                    <div style='font-size:1.1rem; font-weight:600; color:#38bdf8;'>Anlık Tarama Motoru</div>
                                </div>
                                <ul style='list-style:disc; margin:0; padding-left:1.2rem; color:#cbd5f5; font-size:0.96rem; line-height:1.55;'>
                                    <li>500+ sembolü saniyeler içinde ML modelleriyle tarar.</li>
                                    <li>Likit segment ve momentum eşikleri otomatik kalibre edilir.</li>
                                    <li>Gürültüyü azaltan adaptif filtre sonucu net sinyaller sunar.</li>
                                </ul>
                            </div>
                            <div style='background:rgba(30,41,59,0.65); border-radius:16px; padding:20px 22px;'>
                                <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                                    <span style='font-size:2rem;'>🛡️</span>
                                    <div style='font-size:1.1rem; font-weight:600; color:#4ade80;'>Risk Pilot Otomasyonu</div>
                                </div>
                                <ul style='list-style:disc; margin:0; padding-left:1.2rem; color:#cbd5f5; font-size:0.96rem; line-height:1.55;'>
                                    <li>Kelly, ATR ve volatilite limitlerine göre lot büyüklüğü önerir.</li>
                                    <li>Stop-loss &amp; take-profit seviyelerini risk/ödül hedefiyle hizalar.</li>
                                    <li>Senaryo bazlı uyarılarla portföyünü korumanı kolaylaştırır.</li>
                                </ul>
                            </div>
                            <div style='background:rgba(30,41,59,0.65); border-radius:16px; padding:20px 22px;'>
                                <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                                    <span style='font-size:2rem;'>📊</span>
                                    <div style='font-size:1.1rem; font-weight:600; color:#fbbf24;'>Şeffaf Analitik Kokpiti</div>
                                </div>
                                <ul style='list-style:disc; margin:0; padding-left:1.2rem; color:#cbd5f5; font-size:0.96rem; line-height:1.55;'>
                                    <li>Her sinyalin metrik ve veri kaynağı tek kartta görünür.</li>
                                    <li>Backtest ve canlı performans sonuçları aynı ekranda izlenir.</li>
                                    <li>Sentiment &amp; on-chain verileriyle fikirlerini hızla doğrularsın.</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div style='flex:1; min-width:260px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                        <a href='#' style='background:#00e6e6; color:#0f172a; font-weight:700; padding:18px 42px; border-radius:14px; text-decoration:none; font-size:1.25em; margin-bottom:18px; box-shadow:0 26px 58px -30px rgba(14,165,233,0.75); transition:transform 0.25s ease, box-shadow 0.25s ease;'>Ücretsiz Dene</a>
                        <a href='#' style='background:rgba(30,41,59,0.75); color:#fff; font-weight:600; padding:16px 40px; border-radius:14px; text-decoration:none; font-size:1.12em; display:flex; align-items:center; gap:10px; border:1px solid rgba(148,163,184,0.28);'>
                            <span style='font-size:1.3em;'>▶️</span> Demo İzle
                        </a>
                        <img src='https://cdn.jsdelivr.net/gh/feathericons/feather/icons/compass.svg' width='118' style='opacity:0.12; margin-top:28px;'>
                    </div>
                </div>
            </div>
        </div>
        """

    features_section = """
        <div class='layout-grid'>
            <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:24px; margin-bottom:40px;'>
                <div class='feature-card' style='background:rgba(15,23,42,0.75); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(14,165,233,0.45);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>🧠</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#38bdf8;'>Akıllı Strateji Motoru</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#cbd5f5; font-size:0.98rem; line-height:1.6;'>
                        <li>Trend, momentum ve hacmi birlikte puanlayan ML/DRL orkestrasyonu.</li>
                        <li>Regime &amp; segment bazlı eşikler ile yanlış pozitifler azalır.</li>
                        <li>Her taramada yeni veriye göre skorlar anında yeniden kalibre edilir.</li>
                    </ul>
                </div>
                <div class='feature-card' style='background:rgba(23,32,48,0.78); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(34,197,94,0.45);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>🧭</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#4ade80;'>Risk &amp; Sermaye Kılavuzu</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#d1fae5; font-size:0.98rem; line-height:1.6;'>
                        <li>Kelly fraksiyonu, ATR ve volatilite ile uyumlu pozisyon boyutları.</li>
                        <li>Anlık risk/ödül hesaplarıyla stop &amp; hedefler aynı ekranda.</li>
                        <li>Portföy yoğunluğu ve korelasyon uyarılarıyla aşırı risk engellenir.</li>
                    </ul>
                </div>
                <div class='feature-card' style='background:rgba(24,31,48,0.78); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(251,191,36,0.4);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>🔍</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#fbbf24;'>Şeffaf Sonuç Raporu</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#fde68a; font-size:0.98rem; line-height:1.6;'>
                        <li>Her sinyal kartında kullanılan veri ve skor bileşenleri açıkça listelenir.</li>
                        <li>Backtest, canlı performans ve alternatif veriler tek kokpitte.</li>
                        <li>Paylaşılabilir rapor ve uyarılar ekip içinde aksiyona dönüşür.</li>
                    </ul>
                </div>
            </div>
        </div>
        """

    checklist_html = """
        <div class='layout-grid'>
            <div class='action-checklist'>
                <h3>📋 Pilot'un Aksiyon Kontrol Listesi</h3>
                <p class='lead'>Analiz sonrası hangi adımları atacağını saniyeler içinde hatırla. FinSense bu panelde seninle birlikte.</p>
                <div class='checklist-grid'>
                    <div class='bucket'>
                        <h4><span>🛠️</span>Eylemsel Basitleştirme</h4>
                        <ul>
                            <li><span class='icon'>✅</span> Kural basit: Yeşil sinyalleri (AL) R/R oranına göre filtrele.</li>
                            <li><span class='icon'>⏱️</span> Stop-Loss ve Take-Profit seviyelerini belirle, beklemeye geç.</li>
                        </ul>
                    </div>
                    <div class='bucket'>
                        <h4><span>🛫</span>Uçuş Öncesi Kontrol</h4>
                        <ul>
                            <li><span class='icon'>🟢</span> Yeşil (AL) sinyalleri filtrele.</li>
                            <li><span class='icon'>🏆</span> Kazananları önce listele.</li>
                            <li><span class='icon'>📈</span> R/R &gt; 2.0 fırsatlara odaklan.</li>
                            <li><span class='icon'>📝</span> Stop-Loss ve Take-Profit seviyeni kaydet.</li>
                        </ul>
                    </div>
                    <div class='bucket'>
                        <h4><span>💡</span>Yardım &amp; İpuçları</h4>
                        <ul>
                            <li><span class='icon'>🛡️</span> R/R oranı kontrolü (PilotShield önerisi).</li>
                            <li><span class='icon'>🌙</span> Piyasalar kapalıyken stop-loss güncelleme hatırlatması.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """

    st.markdown(hero_section, unsafe_allow_html=True)
    st.markdown(features_section, unsafe_allow_html=True)
    st.markdown(checklist_html, unsafe_allow_html=True)

    action_cols = st.columns([1, 1, 1])
    with action_cols[1]:
        if st.button("Panele Geç", key="landing_enter_panel"):
            st.session_state.has_seen_landing = True
            trigger_rerun()

    st.caption("🎉 Bu tanıtım ekranı sadece ilk oturumda gösterilir.")
    st.stop()


if not st.session_state.has_seen_landing:
    render_finpilot_landing()

# Sayfa seçici (landing sonrası)
page = st.sidebar.selectbox("Sayfa Seç", ["Panel", "Kişiselleştirme", "Geçmiş Sinyaller"])


@lru_cache(maxsize=1)
def load_settingscard_markup():
    """Load the compiled SettingsCard bundle and inline CSS/JS for Streamlit."""
    dist_dir = Path(__file__).resolve().parent / "SettingsCard" / "dist"
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


HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


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
    segment_key_cast = None if segment_key in (None, "") else str(segment_key)
    segment_labels = {
        "high_liquidity": "Yüksek hacim",
        "mid_liquidity": "Orta hacim",
        "low_liquidity": "Düşük hacim",
    }
    segment_label = segment_labels.get(segment_key_cast, segment_key_cast or "")

    z_abs = abs(z_val)
    if math.isfinite(z_abs):
        cdf = 0.5 * (1 + math.erf(z_abs / math.sqrt(2)))
        unusual_pct = cdf * 100.0
    else:
        unusual_pct = None

    variant = ("success" if z_val >= 0 else "warning") if z_abs >= threshold_val else "neutral"

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
            reason_raw = build_reason(data)
        except Exception:
            reason_raw = data.get("reason")
        try:
            summary_raw = build_explanation(data)
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
        segment_display = {
            "high_liquidity": "Yüksek hacim",
            "mid_liquidity": "Orta hacim",
            "low_liquidity": "Düşük hacim",
        }.get(segment_key, segment_key or "—")
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


def render_summary_panel(df: pd.DataFrame, buyable: pd.DataFrame = None):
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
                    <div>
                        <div class='metric-label'>Zaman</div>
                        <div class='metric-value'>{timestamp_display}</div>
                    </div>
                </div>
            </div>
            """
        ).strip()
        cards.append(card_html)

    if cards:
        st.markdown(
            "<div class='mobile-card-stack mobile-card-stack--symbols'>"
            + "".join(cards)
            + "</div>",
            unsafe_allow_html=True,
        )


def render_mobile_recommendation_cards(df: pd.DataFrame):
    """Render recommendation cards for mobile layouts."""
    if df is None or df.empty:
        return

    df_cards = df.fillna("")

    def fmt(value, decimals=2):
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        if value in ("", None):
            return "-"
        return value

    cards = []
    for _, row in df_cards.iterrows():
        is_buy = bool(row.get("Alım?"))
        badge_type = "buy" if is_buy else "hold"
        badge_label = "AL" if is_buy else "İzle"
        summary_clean = normalize_narrative(row.get("Özet", ""))
        reason_clean = normalize_narrative(row.get("Neden", ""))
        summary_html = escape(summary_clean) if summary_clean else ""
        reason_html = escape(reason_clean) if reason_clean else ""
        regime_value = row.get("Rejim", "-")
        regime_text = normalize_narrative(regime_value) or "-"
        regime_hint = escape(get_regime_hint(regime_value))
        regime_html = escape(regime_text)
        sentiment_value = row.get("Sentiment", "-")
        sentiment_display = fmt(sentiment_value)
        sentiment_hint = escape(get_sentiment_hint(sentiment_value))
        sentiment_html = escape(str(sentiment_display))
        symbol_label = escape(str(row.get("Sembol", "-")))
        price_text = escape(str(fmt(row.get("Fiyat"))))
        score_text = escape(str(fmt(row.get("Skor"), 0)))
        strength_text = escape(str(fmt(row.get("Güç (0-100)"), 0)))
        onchain_text = escape(str(fmt(row.get("Onchain"))))
        card_html = dedent(
            f"""
            <div class='analysis-card mobile-only'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                    <div style='font-size:1.1rem; font-weight:600; letter-spacing:0.02em;'>{symbol_label}</div>
                    <span class='badge {badge_type}'>{badge_label}</span>
                </div>
                <div class='metric-grid'>
                    <div>
                        <div class='metric-label'>Fiyat</div>
                        <div class='metric-value'>{price_text}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Skor</div>
                        <div class='metric-value'>{score_text}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Güç</div>
                        <div class='metric-value'>{strength_text}</div>
                    </div>
                    <div>
                        <div class='metric-label'>Rejim</div>
                        <div class='metric-value'><span class='badge info' title='{regime_hint}'>{regime_html}</span></div>
                    </div>
                    <div>
                        <div class='metric-label'>Sentiment</div>
                        <div class='metric-value'><span class='badge hold' title='{sentiment_hint}'>{sentiment_html}</span></div>
                    </div>
                    <div>
                        <div class='metric-label'>Onchain</div>
                        <div class='metric-value'>{onchain_text}</div>
                    </div>
                </div>
                <div style='color:#e2e8f0; font-weight:500; margin-bottom:6px;'>{summary_html}</div>
                <div style='color:rgba(148,163,184,0.85); font-size:0.82rem;'>{reason_html}</div>
            </div>
            """
        ).strip()
        cards.append(card_html)

    if cards:
        st.markdown(
            "<div class='mobile-card-stack mobile-card-stack--recommendations'>"
            + "".join(cards)
            + "</div>",
            unsafe_allow_html=True,
        )


# --- Panel Ana Sayfa ---
if page == "Panel":
    if "scan_status" not in st.session_state:
        st.session_state["scan_status"] = "idle"
    if "scan_message" not in st.session_state:
        st.session_state["scan_message"] = None
    if "scan_df" not in st.session_state:
        st.session_state["scan_df"] = pd.DataFrame()
    if "scan_src" not in st.session_state:
        st.session_state["scan_src"] = None
    if "scan_time" not in st.session_state:
        st.session_state["scan_time"] = None
    if "guide_tooltip_shown" not in st.session_state:
        st.session_state["guide_tooltip_shown"] = False

    st.markdown("## 📊 Panel Özeti")
    st.write("Analiz sonuçları, risk ölçüleri ve strateji uyumu aşağıdaki bölümlerde sunulur.")

    # --- Alım Fırsatı İpuçları Expander ---
    with st.expander("💡 Alım Fırsatı İpuçları", expanded=False):
        st.markdown(
            dedent(
                """
                - <span style='color:#00e6e6;'>Trend yukarı ve hacim artışı varsa, sinyal daha güçlüdür.</span>
                - <span style='color:#2196f3;'>ML/DRL skorları yüksekse, algoritmik güven artar.</span>
                - <span style='color:#ffeb3b;'>Kişisel risk iştahınıza göre pozisyon büyüklüğünü ayarlayın.</span>
                - <span style='color:#fff;'>Geçmiş performans tablosunu inceleyin, şeffaflık için her sinyalin geçmişini görün.</span>
                - <span style='color:#00e6e6;'>Alternatif veri (sentiment/on-chain) pozitifse, ek onay sağlar.</span>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    # ...mevcut panel özet kutuları ve grafikler aşağıda devam edecek...

elif page == "Kişiselleştirme":
    st.markdown("## ⚙️ Kişiselleştirme Paneli")
    st.markdown(
        "Risk profili, strateji tercihi ve bildirim seçenekleri gibi tüm FinPilot ayarlarını bu sayfadan yönetebilirsiniz."
    )
    st.caption(
        "Ayarlarınızı güncelledikten sonra panodaki analizleri yenileyerek son durumu görebilirsiniz."
    )
    render_settings_card()

# --- Geçmiş Sinyaller Sayfası ---
elif page == "Geçmiş Sinyaller":
    st.markdown("# � FinPilot Performans Analizi")
    signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
    st.markdown("## 🚦 Strateji, Risk ve Getiri Analizi")
    if os.path.exists(signal_log_path):
        log_df = pd.read_csv(signal_log_path, header=None)
        log_df.columns = [
            "Tarih",
            "Sembol",
            "Fiyat",
            "Stop-Loss",
            "Take-Profit",
            "Skor",
            "Güç",
            "Rejim",
            "Sentiment",
            "Onchain",
            "Alım?",
            "Özet",
            "Neden",
        ]
        # Filtreler
        col1, col2, col3 = st.columns([2, 2, 2])
        unique_dates = log_df["Tarih"].unique().tolist()
        selected_date = col1.selectbox("Tarih Seç", ["Tümü"] + unique_dates)
        unique_symbols = log_df["Sembol"].unique().tolist()
        selected_symbol = col2.selectbox("Sembol Seç", ["Tümü"] + unique_symbols)
        regime_options = log_df["Rejim"].unique().tolist()
        selected_regime = col3.selectbox("Rejim Filtrele", ["Tümü"] + regime_options)

        filtered = log_df.copy()
        if selected_date != "Tümü":
            filtered = filtered[filtered["Tarih"] == selected_date]
        if selected_symbol != "Tümü":
            filtered = filtered[filtered["Sembol"] == selected_symbol]
        if selected_regime != "Tümü":
            filtered = filtered[filtered["Rejim"] == selected_regime]

        # 1. Getiri & Hedefleme
        avg_gain = (filtered["Take-Profit"] - filtered["Fiyat"]).mean() if len(filtered) > 0 else 0
        cagr = (
            ((filtered["Take-Profit"] / filtered["Fiyat"]).mean() - 1) * 100
            if len(filtered) > 0
            else 0
        )
        take_profit = filtered["Take-Profit"].mean() if len(filtered) > 0 else 0

        # 2. Risk & Uçurum
        avg_loss = (filtered["Fiyat"] - filtered["Stop-Loss"]).mean() if len(filtered) > 0 else 0
        rr_ratio = avg_gain / avg_loss if avg_loss != 0 else 0
        kelly = (rr_ratio - (1 - rr_ratio)) / rr_ratio if rr_ratio > 0 else 0
        max_drawdown = avg_loss  # örnek, daha gelişmiş hesaplama eklenebilir

        # 3. Strateji & Uyum
        total_signals = len(filtered)
        success_signals = filtered[filtered["Alım?"]].shape[0] if total_signals > 0 else 0
        win_rate = (success_signals / total_signals * 100) if total_signals > 0 else 0
        avg_score = filtered["Skor"].mean() if total_signals > 0 else 0

        st.markdown("### 🚦 Risk/Ödül Kartı")
        rr_color = "#10b981" if rr_ratio >= 2 else ("#f59e42" if rr_ratio >= 1 else "#ef4444")
        st.markdown(
            f"<div style='background:{rr_color};color:#fff;padding:16px;border-radius:12px;font-size:1.3em;font-weight:bold;'>R/R Oranı: {rr_ratio:.2f} | Maksimum Kayıp: {max_drawdown:.2f} | Kelly: {kelly:.2f}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### 📈 Getiri & Hedefleme")
        st.markdown(f"Hedef Getiri: %{take_profit:.2f} | CAGR: %{cagr:.2f}")

        st.markdown("### 🤖 Strateji & Uyum")
        st.markdown(f"Başarı Oranı (Win Rate): %{win_rate:.1f} | Ortalama Skor: {avg_score:.2f}")

        st.dataframe(filtered, width="stretch")

        # Simülasyon ve Pozisyon Girişi
        st.markdown("---")
        st.markdown("### 🔬 Simülasyon & Pozisyon Girişi")
        st.button("Geriye Dönük Testi Çalıştır", key="backtest_run")
        st.button("Pozisyonu Ayarla / Emri Gönder", key="order_run")
        # ...eski hata yakalama ve grafik kodları kaldırıldı...


# --- Detay Analiz: Ana içerikten sonra, geniş ve ortada ---
# ...removed unreachable/indented code...
# ...existing code...


def latest_csv(prefix: str):
    if prefix == "shortlist":
        search_dir = os.path.join(os.getcwd(), "data", "shortlists")
    elif prefix == "suggestions":
        search_dir = os.path.join(os.getcwd(), "data", "suggestions")
    else:
        search_dir = os.getcwd()

    files = sorted(
        glob.glob(os.path.join(search_dir, f"{prefix}_*.csv")), key=os.path.getmtime, reverse=True
    )
    return files[0] if files else None


def load_csv(path: str):
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()


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


# Sidebar - Portföy Ayarları
with st.sidebar:
    st.markdown("# ⚙️ Ayarlar")
    st.markdown("**Portföy ve Risk**")
    portfolio_value = st.number_input("Portföy ($)", value=10000, step=1000, min_value=1000)
    risk_percent = st.slider("Risk (%)", min_value=1.0, max_value=5.0, value=2.0, step=0.5)
    kelly_fraction = st.slider("Kelly (0.1-1.0)", min_value=0.1, max_value=1.0, value=0.5, step=0.1)

    st.markdown("**Tarama Modu**")
    aggressive_mode = st.toggle(
        "Agresif Mod", value=False, help="Daha fazla fırsat için eşikleri gevşetir."
    )

    st.markdown("**Veri Ayarları**")
    use_adjusted = st.toggle("Temettü/Bölünme Ayarlı Fiyat", value=True)
    include_prepost = st.toggle("Pre/After-hours Dahil", value=False)

    st.markdown("**Z-Skoru Ayarları**")
    lookback_options = [20, 40, 60, 90, 120]
    baseline_window_ui = st.select_slider(
        "Lookback Penceresi (gün)",
        options=lookback_options,
        value=60,
        help="Z-skor hesabında kullanılacak tarih aralığını belirler.",
    )
    dynamic_window_ui = st.select_slider(
        "Dinamik Pencere (gün)",
        options=[40, 60, 80, 100, 120, 160],
        value=60,
        help="Rolling pencere uzunluğu, adaptif eşikleri kalibre eder.",
    )
    dynamic_enabled_ui = st.toggle(
        "Dinamik z-eşiği",
        value=True,
        help="Z-eşiği, son pencere dağılımına göre otomatik ayarlansın.",
    )
    dynamic_quantile_ui = st.slider(
        "Dinamik Eşik Yüzdesi",
        min_value=0.90,
        max_value=0.995,
        value=0.975,
        step=0.005,
        help="Yüzdelik 0.95-0.99 aralığında daha sıkı, 0.90-0.94 daha esnek sinyal üretir.",
    )
    segment_enabled_ui = st.toggle(
        "Likidite bazlı presetler", value=True, help="Hacme göre ±σ eşiklerini otomatik seç."
    )
    st.caption(
        "20/60/120 günlük lookback karşılaştırmaları için baseline seçeneğini değiştirerek basit backtest yapılabilir."
    )

    st.markdown("**Telegram Uyarı Durumu**")
    try:
        from telegram_config import BOT_TOKEN, CHAT_ID

        if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" and CHAT_ID != "YOUR_CHAT_ID_HERE":
            st.success("Telegram aktif!")
            send_panel_telegram = st.toggle("Telegram'a gönder", value=True)
        else:
            st.warning("Telegram yapılandırılmamış")
            send_panel_telegram = False
    except ImportError:
        st.error("Telegram modülü yok")
        send_panel_telegram = False

    st.markdown("---")
    st.markdown("### Yardım ve İpuçları")
    st.info(
        "Portföy, risk ve Kelly ayarlarını portföy büyüklüğüne göre seçin. Agresif mod daha fazla sinyal üretir. Telegram ile anlık bildirim alabilirsiniz."
    )
    settings = scanner.DEFAULT_SETTINGS.copy()
    if aggressive_mode:
        overrides = scanner.AGGRESSIVE_OVERRIDES.copy()
        settings.update(overrides)

    settings["auto_adjust"] = bool(use_adjusted)
    settings["prepost"] = bool(include_prepost)
    settings["momentum_baseline_window"] = int(baseline_window_ui)
    settings["momentum_dynamic_enabled"] = bool(dynamic_enabled_ui)
    settings["momentum_dynamic_window"] = int(dynamic_window_ui)
    settings["momentum_dynamic_quantile"] = float(dynamic_quantile_ui)
    settings["momentum_dynamic_alpha"] = float(settings.get("momentum_dynamic_alpha", 0.6))
    settings["momentum_segment_thresholds"] = (
        scanner.DEFAULT_SETTINGS["momentum_segment_thresholds"].copy() if segment_enabled_ui else {}
    )
    scanner.SETTINGS = settings

col1, col2 = st.columns([3, 2], gap="large")

with col1:
    st.markdown("## 📊 Analiz Sonuçları")
    st.markdown(
        """
        <div class='process-intro'>
            <p>Bu bölüm, seçtiğiniz semboller üzerinde yürüttüğümüz taramanın adım adım nasıl ilerlediğini ve hangi çıktıları ürettiğini gösterir.</p>
            <p>Amaç, karar verme sürecinizi yalın, güvenilir ve şeffaf metriklerle desteklemek; böylece FinPilot'un bilimsel süreçlerini şeffaf biçimde takip edebilmenizi sağlamaktır.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    progress_slot = st.container()
    tooltip_slot = st.empty()

    status_for_label = st.session_state.get("scan_status", "idle")
    if status_for_label == "loading":
        primary_label = "⏳ Tarama yapılıyor…"
    elif status_for_label == "completed":
        primary_label = "🔁 Tarama tamamlandı – yeniden başlat"
    else:
        primary_label = "▶️ Taramayı Çalıştır"

    status_badge_map = {
        "idle": ("Inactive", "badge-idle"),
        "loading": ("Çalışıyor", "badge-loading"),
        "completed": ("Hazır", "badge-success"),
        "error": ("Hata", "badge-error"),
    }
    badge_text, badge_class = status_badge_map.get(
        status_for_label, (status_for_label, "badge-idle")
    )

    with st.container():
        st.markdown("<div class='cta-sticky'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.7, 1.1, 1.1])
        with c1:
            st.markdown("<div class='cta-primary'>", unsafe_allow_html=True)
            run_btn = st.button(
                primary_label, key="run_btn", disabled=status_for_label == "loading"
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='cta-secondary'>", unsafe_allow_html=True)
            refresh_btn = st.button(
                "🔄 Yenile", key="refresh_btn", disabled=status_for_label == "loading"
            )
            st.markdown("</div>", unsafe_allow_html=True)
        with c3:
            st.markdown("<div class='cta-tertiary'>", unsafe_allow_html=True)
            load_btn = st.button(
                "📥 Son Shortlist'i Yükle", key="load_btn", disabled=status_for_label == "loading"
            )
            st.markdown("</div>", unsafe_allow_html=True)
        badge_html = f"<span class='status-badge {badge_class}'>{badge_text}</span>"
        st.markdown(f"<div class='status-bar'>Durum: {badge_html}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    last_run = st.session_state.get("scan_time") or "Henüz çalıştırılmadı"
    source_label = st.session_state.get("scan_src") or "—"
    info_banner = f"""
    <div class='info-banner'>
        <div class='icon'>🧭</div>
        <div class='content'>
            <strong>Şeffaflık Notu:</strong> FinPilot sinyalleri; HMM rejim analizi, ML/DRL skoru ve alternatif veri doğrulamalarıyla oluşturulur.<br>
            <span style='display:block; margin-top:6px;'>Fiyat ve hacim verileri 15 dk gecikmeli; sentiment/on-chain katmanları gün içinde 3 kez yenilenir.</span>
            <span style='display:block; margin-top:6px;'>Son tarama: {escape(str(last_run))} · Kaynak: {escape(str(source_label))}</span>
        </div>
    </div>
    """
    st.markdown(info_banner, unsafe_allow_html=True)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    with st.expander("📥 Veri Kaynağı", expanded=False):
        st.markdown("<div class='upload-shell'>", unsafe_allow_html=True)
        uploaded_csv = st.file_uploader(
            "CSV yükle (Symbol/Ticker sütunu)", type=["csv"], key="csv_uploader_main"
        )
        st.caption(
            "📎 Beklenen şema: **Symbol** veya **Ticker** başlıklı bir sütun. İsteğe bağlı ek sütunlar yok sayılır."
        )
        st.caption(
            "ℹ️ CSV UTF-8 formatında olmalı; tekrar eden semboller otomatik benzersizleştirilir."
        )
        if uploaded_csv is not None:
            uploaded_csv.seek(0)
            try:
                preview_df = pd.read_csv(uploaded_csv)
                symbol_col = detect_symbol_column(preview_df)
                row_count = len(preview_df)
                if symbol_col:
                    st.success(f"✅ {row_count} satır algılandı. Sembol sütunu: `{symbol_col}`")
                else:
                    st.warning(
                        "⚠️ 'Symbol' veya 'Ticker' sütunu algılanamadı. Lütfen dosyayı kontrol edin."
                    )
                st.dataframe(preview_df.head(5), use_container_width=True)
            except Exception as preview_err:
                st.error(f"Ön izleme başarısız: {preview_err}")
            finally:
                uploaded_csv.seek(0)
        else:
            st.caption("Örnek CSV:\n```\nSymbol\nAAPL\nMSFT\nNVDA\n```")
        csv_scan_btn = st.button(
            "▶️ CSV'yi Tara",
            key="csv_scan_btn",
            disabled=(uploaded_csv is None or status_for_label == "loading"),
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if run_btn:
        st.session_state["scan_status"] = "loading"
        st.session_state["scan_message"] = "Tarama başlatıldı."
        with st.spinner("Semboller analiz ediliyor..."):
            import datetime

            symbols = load_symbols()
            backtest_kelly = kelly_fraction if kelly_fraction else 0.5
            results = scanner.evaluate_symbols_parallel(symbols, kelly_fraction=backtest_kelly)
            df = pd.DataFrame(results)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df["timestamp"] = now
            st.session_state["scan_df"] = df
            st.session_state["scan_src"] = "live"
            st.session_state["scan_time"] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = f"{len(df)} sembol analiz edildi."
    elif refresh_btn:
        st.cache_data.clear()
        st.session_state["scan_status"] = "loading"
        st.session_state["scan_message"] = "Tarama yenileniyor."
        with st.spinner("Yeniden analiz ediliyor..."):
            import datetime

            symbols = load_symbols()
            results = scanner.evaluate_symbols_parallel(symbols)
            df = pd.DataFrame(results)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df["timestamp"] = now
            st.session_state["scan_df"] = df
            st.session_state["scan_src"] = "live"
            st.session_state["scan_time"] = now
        st.session_state["scan_status"] = "completed" if not df.empty else "idle"
        st.session_state["scan_message"] = "Tarama yenilendi."
    elif load_btn:
        st.session_state["scan_status"] = "loading"
        path = latest_csv("shortlist")
        if path:
            import datetime

            df = load_csv(path)
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if not df.empty:
                df["timestamp"] = now
            st.session_state["scan_df"] = df
            st.session_state["scan_src"] = os.path.basename(path)
            st.success(f"Son CSV yüklendi: {os.path.basename(path)}")
            st.session_state["scan_time"] = now
            st.session_state["scan_status"] = "completed" if not df.empty else "idle"
            st.session_state["scan_message"] = f"CSV'den {len(df)} satır yüklendi."
        else:
            st.warning("Yüklenecek shortlist CSV bulunamadı.")
            df = st.session_state.get("scan_df", pd.DataFrame())
            st.session_state["scan_status"] = "error"
    elif csv_scan_btn and uploaded_csv is not None:
        try:
            st.session_state["scan_status"] = "loading"
            import datetime

            uploaded_csv.seek(0)
            df_in = pd.read_csv(uploaded_csv)
            symbols = extract_symbols_from_df(df_in)
            if not symbols:
                st.error("❌ CSV içinde 'Symbol' veya 'Ticker' sütunu bulunamadı.")
                st.session_state["scan_status"] = "error"
                df = st.session_state.get("scan_df", pd.DataFrame())
            else:
                with st.spinner(f"CSV'den {len(symbols)} sembol analiz ediliyor..."):
                    results = scanner.evaluate_symbols_parallel(symbols)
                    df = pd.DataFrame(results)
                    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    if not df.empty:
                        df["timestamp"] = now
                    st.session_state["scan_df"] = df
                    st.session_state["scan_src"] = (
                        f"csv:{getattr(uploaded_csv, 'name', 'uploaded.csv')}"
                    )
                    st.session_state["scan_time"] = now
                    st.session_state["scan_status"] = "completed" if not df.empty else "idle"
                    st.session_state["scan_message"] = f"CSV'den {len(df)} sembol analiz edildi."

                if send_panel_telegram and df is not None and not df.empty:
                    try:
                        from telegram_alerts import TelegramNotifier
                        from telegram_config import BOT_TOKEN, CHAT_ID

                        telegram = TelegramNotifier(BOT_TOKEN, CHAT_ID)
                        if telegram.is_configured():
                            df_rec = df.copy()
                            df_rec["recommendation_score"] = df_rec.apply(
                                compute_recommendation_score, axis=1
                            )
                            df_rec = df_rec.sort_values(
                                ["entry_ok", "recommendation_score"], ascending=[False, False]
                            )
                            top10 = df_rec.head(10).copy()
                            telegram.send_recommendations(top10)
                            buyable = df[df["entry_ok"]]
                            best_signal = buyable.iloc[0].to_dict() if len(buyable) > 0 else None
                            telegram.send_daily_summary(len(buyable), best_signal)
                    except Exception as _e:
                        st.warning(f"Telegram gönderimi başarısız: {_e}")
        except Exception as e:
            st.error(f"CSV okunamadı: {e}")
            df = st.session_state.get("scan_df", pd.DataFrame())
            st.session_state["scan_status"] = "error"
    else:
        df = st.session_state.get("scan_df", pd.DataFrame())

    current_status = st.session_state.get("scan_status", "idle")
    scan_src = st.session_state.get("scan_src")
    df = st.session_state.get("scan_df", pd.DataFrame())

    render_progress_tracker(
        progress_slot,
        current_status,
        has_source=bool(scan_src),
        has_results=bool(df is not None and not df.empty),
    )

    if not st.session_state.get("guide_tooltip_shown", False):
        tooltip_slot.markdown(
            "<div class='guide-tooltip'><span class='icon'>💡</span><span>Adım kartlarındaki ℹ️ simgelerine gelerek sürecin detaylarını ve önerilen aksiyonları okuyabilirsiniz.</span></div>",
            unsafe_allow_html=True,
        )
        st.session_state["guide_tooltip_shown"] = True
    else:
        tooltip_slot.empty()

    if current_status == "loading":
        st.markdown(
            "<div class='feature-card' style='height:120px; background:#212e44;'></div>",
            unsafe_allow_html=True,
        )
        st.stop()

    if df is None or df.empty:
        if DEMO_MODE_ENABLED:
            st.markdown(
                """
                <div class='demo-note'>
                    <strong>🎯 Demo verisi görüntüleniyor.</strong><br>
                    Gerçek sonuçları görmek için üstteki "Taramayı Çalıştır" adımını izleyin veya veri kaynağını yükleyin.
                </div>
                """,
                unsafe_allow_html=True,
            )
            df = get_demo_scan_results()
        else:
            st.markdown(
                """
            <div class='analysis-empty' style='text-align:center; margin:32px 0;'>
                <h3>🔍 Uygun hisse bulunamadı</h3>
                <p style='color:rgba(226,232,240,0.75);'>Filtreleri gevşetmeyi deneyin veya taramayı yeniden başlatın.</p>
                <p style='color:rgba(148,163,184,0.75); font-size:0.85rem;'>İpucu: Risk eşiğini artırabilir veya hacim filtrelerini genişletebilirsiniz.</p>
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.stop()

    if st.session_state.get("error", None):
        st.toast(f"Hata: {st.session_state['error']}", icon="❌")

    scan_time = st.session_state.get("scan_time")
    scan_src = st.session_state.get("scan_src")
    scan_message = st.session_state.get("scan_message")
    if scan_time:
        st.info(f"Son tarama zamanı: {scan_time} | Kaynak: {scan_src}")
    if scan_message:
        st.caption(f"📝 {scan_message}")

    st.markdown("<div class='view-mode-toggle'>", unsafe_allow_html=True)
    toggle_intro, toggle_control = st.columns([2.2, 1], gap="large")
    with toggle_intro:
        st.markdown(
            "<div class='toggle-intro'><h4>Görünüm</h4><p>Basit mod özet ve kritik metrikleri sunar. Gelişmiş mod tam analitikleri ve derinlemesine tabloları açar.</p></div>",
            unsafe_allow_html=True,
        )
    with toggle_control:
        selected_view = st.radio(
            "Görünüm modu",
            options=["Basit", "Gelişmiş"],
            horizontal=True,
            key="view_mode_choice",
            label_visibility="collapsed",
        )
    st.markdown("</div>", unsafe_allow_html=True)
    st.session_state.view_mode = "advanced" if selected_view == "Gelişmiş" else "simple"
    show_advanced = is_advanced_view()
    if not show_advanced:
        st.caption(
            "Basit görünümde gelişmiş tablolar gizlendi. 'Gelişmiş' moduna geçerek tüm analitiği açabilirsiniz."
        )

    buyable = df[df["entry_ok"]]
    if len(buyable) > 0:
        st.success(f"🟢 **{len(buyable)} ALIM FIRSATI!**")

        display_cols = [
            "symbol",
            "price",
            "score",
            "stop_loss",
            "take_profit",
            "position_size",
            "risk_reward",
            "timestamp",
        ]
        buyable_display = buyable[display_cols].copy()
        buyable_display.columns = [
            "Sembol",
            "Fiyat",
            "Skor",
            "Stop-Loss",
            "Take-Profit",
            "Lot",
            "R/R",
            "Zaman",
        ]
        buyable_display["Strength"] = buyable.apply(scanner.compute_recommendation_strength, axis=1)
        if "regime" in buyable.columns:
            buyable_display["Rejim"] = buyable["regime"].fillna("-")

        st.markdown("### 🟢 Alım Fırsatları Tablosu")
        st.caption(
            "Durum yongaları sinyal gücü, rejim ve risk/ödül durumunu gösterir. Sıralama için aşağıdaki ham tabloyu kullanabilirsiniz."
        )
        render_buyable_table(buyable)
        if show_advanced:
            with st.expander("Ham tablo (sıralanabilir)"):
                st.dataframe(buyable_display, use_container_width=True)
        else:
            st.caption("Ham tablo basit modda gizlendi. Gelişmiş modda tam tabloyu açabilirsiniz.")

        csv_download = buyable_display.to_csv(index=False).encode("utf-8")
        st.download_button(
            "CSV olarak indir",
            csv_download,
            file_name=f"buy_signals_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="download_buy_signals",
        )

        if show_advanced:
            st.markdown("#### 🎯 Kart görünümü")
            render_buyable_cards(buyable)
    else:
        st.info(
            "Şu anda alım kriterlerini karşılayan sembol bulunmuyor. Filtreleri güncellemek için üstteki CTA'ları kullanabilirsiniz."
        )

    render_summary_panel(df, buyable)

    simple_cols = [
        "symbol",
        "price",
        "score",
        "filter_score",
        "entry_ok",
        "risk_reward",
        "timestamp",
    ]
    df_simple = df[simple_cols].copy()
    df_simple.columns = ["Sembol", "Fiyat", "Skor", "Filtre", "Alım?", "R/R", "Zaman"]

    if show_advanced:
        st.markdown("### 📋 Tüm Semboller")
        st.markdown("<div class='desktop-table'>", unsafe_allow_html=True)
        st.dataframe(df_simple, width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
        render_mobile_symbol_cards(df)

        st.markdown("### 🔝 Öneriler (Top 10)")
        df_rec = df.copy()
        if not df_rec.empty:
            df_rec["recommendation_score"] = df_rec.apply(compute_recommendation_score, axis=1)
            df_rec["strength"] = df_rec["recommendation_score"].map(
                scanner.compute_recommendation_strength
            )
            df_rec = df_rec.sort_values(
                ["entry_ok", "recommendation_score"], ascending=[False, False]
            )
            top10 = df_rec.head(10).copy()

            def safe_explanation(row):
                row_dict = row.to_dict()
                try:
                    built = build_explanation(row_dict)
                except Exception:
                    built = row_dict.get("why")
                return normalize_narrative(built)

            def safe_reason(row):
                row_dict = row.to_dict()
                try:
                    built = build_reason(row_dict)
                except Exception:
                    built = row_dict.get("reason")
                return normalize_narrative(built)

            top10["why"] = top10.apply(safe_explanation, axis=1)
            top10["reason"] = top10.apply(safe_reason, axis=1)
            show_cols = [
                "symbol",
                "price",
                "recommendation_score",
                "strength",
                "entry_ok",
                "regime",
                "sentiment",
                "onchain_metric",
                "why",
                "reason",
            ]
            pretty = top10[show_cols].copy()
            pretty.columns = [
                "Sembol",
                "Fiyat",
                "Skor",
                "Güç (0-100)",
                "Alım?",
                "Rejim",
                "Sentiment",
                "Onchain",
                "Özet",
                "Neden",
            ]
            st.markdown("#### 📋 Sonuç Tablosu Açıklaması")
            st.caption(
                "Tabloda en güçlü alım fırsatları, rejim, sentiment ve onchain metrikleri ile birlikte gösterilir. 'Alım?' sütunu öneri durumunu belirtir."
            )
            st.markdown("<div class='desktop-table'>", unsafe_allow_html=True)
            st.dataframe(pretty, width="stretch")
            st.markdown("</div>", unsafe_allow_html=True)
            render_mobile_recommendation_cards(pretty)

            import csv
            import datetime

            signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            if st.session_state.get("scan_src", None) == "live":
                with open(signal_log_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    for _, row in top10.iterrows():
                        writer.writerow(
                            [
                                now,
                                row["symbol"],
                                row["price"],
                                row.get("stop_loss", ""),
                                row.get("take_profit", ""),
                                row.get("recommendation_score", ""),
                                row.get("strength", ""),
                                row.get("regime", ""),
                                row.get("sentiment", ""),
                                row.get("onchain_metric", ""),
                                row.get("entry_ok", ""),
                                row.get("why", ""),
                                row.get("reason", ""),
                            ]
                        )
    else:
        st.markdown("### 📋 Semboller (Basit)")
        st.caption(
            "Basit görünümde en güçlü sembollerin hızlı özeti gösterilir. Tüm detaylar için 'Gelişmiş' moduna geçin."
        )
        render_symbol_snapshot(df)
        render_mobile_symbol_cards(df.head(6))

with col2:
    if not show_advanced:
        st.markdown("## 🧭 Gelişmiş Analitik")
        st.info(
            "Basit görünümde gelişmiş performans analizi gizlenir. Tüm detaylara erişmek için 'Gelişmiş' moduna geçebilirsiniz."
        )
    else:
        st.markdown("## � Gelişmiş Öneri Performans Analizi")
        # scan_df panelde mevcutsa, gelişmiş analiz modülünü doğrudan entegre et
        if (
            "scan_df" in st.session_state
            and st.session_state["scan_df"] is not None
            and not st.session_state["scan_df"].empty
        ):
            import scanner

            df = st.session_state["scan_df"]
            # Demo/mock data if empty
            if df is None or df.empty:
                demo_data = {
                    "symbol": ["AAPL", "MSFT", "GOOGL"],
                    "price": [170.5, 320.1, 135.2],
                    "close": [171.0, 321.0, 136.0],
                    "entry_ok": [True, False, True],
                    "risk_reward": [2.1, 1.8, 2.5],
                    "regime": ["Trend", "Yan", "Trend"],
                    "kelly_fraction": [0.5, 0.3, 0.7],
                    "score": [88, 75, 92],
                    "filter_score": [3, 2, 3],
                    "recommendation_score": [95, 80, 98],
                    "strength": [90, 70, 95],
                    "sentiment": [0.7, 0.2, 0.8],
                    "onchain_metric": [60, 40, 75],
                    "timestamp": ["2025-10-14 09:00", "2025-10-14 09:00", "2025-10-14 09:00"],
                    "why": ["Güçlü trend", "Yan piyasa", "Yüksek momentum"],
                    "reason": ["ML/DRL onaylı", "Filtre düşük", "Sentiment yüksek"],
                    # Eksik sütunlar için varsayılan değerler:
                    "time": ["2025-10-14 09:00", "2025-10-14 09:00", "2025-10-14 09:00"],
                    "signal_type": ["AL", "BEKLE", "AL"],
                    "strategy": ["ML", "DRL", "ML"],
                    "note": ["Demo", "Demo", "Demo"],
                    "volatility": [0.15, 0.22, 0.18],
                    "sharpe": [1.2, 0.8, 1.5],
                    "sortino": [1.5, 1.0, 1.7],
                }
                df = pd.DataFrame(demo_data)
                st.info("Demo verilerle gösterim: Canlı veri yoksa örnek sinyaller yüklendi.")
            # Canlı veri için eksik sütunları ekle
            required_cols = [
                "time",
                "signal_type",
                "strategy",
                "note",
                "volatility",
                "sharpe",
                "sortino",
            ]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = ["-" for _ in range(len(df))]
            # KeyError 'close' fix
            if "close" not in df.columns:
                if "Close" in df.columns:
                    df["close"] = df["Close"]
                elif "price" in df.columns:
                    df["close"] = df["price"]
            user_portfolio = None
            start_date = None
            end_date = None
            top_n = 10
            scanner.analyze_recommendations(
                df,
                user_portfolio=user_portfolio,
                start_date=start_date,
                end_date=end_date,
                top_n=top_n,
            )

            # --- Sembol seçimi ve detay analizi (tek ve hatasız) ---
            selected = st.selectbox(
                "Detay için sembol seç:", df["symbol"].tolist(), key="detail_symbol_panel"
            )
            if selected:
                row = df[df["symbol"] == selected].iloc[0]
                # Örnek JSON veri (gerçek API ile entegre edilecek)
                example_json = {
                    "aciklamaKatmanlari": {
                        "tldr": "Trend güçlü, momentum taze, HMM alımı destekliyor.",
                        "basit": "200 EMA üzerinde, RSI 65, volatilite normal.",
                        "ileri": "HMM bullish regime, DRL skoru 0.88, Kelly %5 öneriyor.",
                    },
                    "egitim": {
                        "aksiyonKartlari": [
                            {
                                "baslik": "Pozisyon Büyüklüğü Nasıl Ayarlanır?",
                                "icerik": "Kelly kriterine göre, portföyünüzün en fazla %5'i ile işlem önerilir.",
                            }
                        ],
                        "sozlukKartlari": [
                            {
                                "baslik": "R/R Oranı Nedir? (2.7)",
                                "icerik": "Risk/Ödül oranı, riskinizin 2.7 katı kadar kazanç potansiyeli sunar.",
                            }
                        ],
                        "ornekAnalizKartlari": [
                            {
                                "baslik": f"{selected} neden AL?",
                                "icerik": "Apple, 200 EMA üzerinde güçlü trendde. Son 3 günde %2.5 yükseldi, hacim normalin 1.8 katı. HMM rejim analizi ‘bullish regime’ gösteriyor.",
                            }
                        ],
                    },
                }
                with st.expander(f"Detay: {selected}", expanded=True):
                    st.markdown("### Mum Grafiği ve Sinyal Noktaları")
                    try:
                        df_chart = yf.download(
                            selected, interval="1d", period="60d", progress=False
                        )
                        if (
                            df_chart is not None
                            and hasattr(df_chart, "empty")
                            and not df_chart.empty
                        ):
                            import altair as alt

                            chart = (
                                alt.Chart(df_chart.reset_index())
                                .mark_line(color="#1f77b4")
                                .encode(
                                    x="Date:T",
                                    y=alt.Y("Close:Q", title="Kapanış Fiyatı"),
                                    tooltip=["Date:T", "Close:Q"],
                                )
                                .properties(title=f"{selected} Son 60 Gün Mum Grafiği")
                            )
                            st.altair_chart(chart, use_container_width=True)
                        else:
                            st.warning("Grafik için yeterli veri yok.")
                    except Exception as e:
                        st.error(f"Grafik yüklenemedi: {e}")
                # Katmanlı açıklama
                st.markdown(f"**TL;DR:** {example_json['aciklamaKatmanlari']['tldr']}")
                st.markdown(f"**Detay:** {example_json['aciklamaKatmanlari']['basit']}")
                st.markdown(f"**İleri Analiz:** {example_json['aciklamaKatmanlari']['ileri']}")
                # Eğitim kartları
                for card in example_json["egitim"]["aksiyonKartlari"]:
                    st.info(f"**{card['baslik']}**\n{card['icerik']}")
                for card in example_json["egitim"]["sozlukKartlari"]:
                    st.warning(f"**{card['baslik']}**\n{card['icerik']}")
                for card in example_json["egitim"]["ornekAnalizKartlari"]:
                    st.success(f"**{card['baslik']}**\n{card['icerik']}")
                st.button("Portföye Ekle", key=f"add_{selected}")
                st.button("Telegram'a Gönder", key=f"telegram_{selected}")
        # --- Gelişmiş Detay Görünümü (Expander/Modal) ---
        selected = st.selectbox(
            "Detay için sembol seç:", df["symbol"].tolist(), key="detail_symbol"
        )
        if selected:
            row = df[df["symbol"] == selected].iloc[0]
            with st.expander(f"Detay: {selected}", expanded=False):
                st.markdown("### Mum Grafiği ve Sinyal Noktaları")
                try:
                    df_chart = yf.download(selected, interval="1d", period="60d", progress=False)
                    if df_chart is not None and hasattr(df_chart, "empty") and not df_chart.empty:
                        import altair as alt

                        chart = (
                            alt.Chart(df_chart.reset_index())
                            .mark_line(color="#1f77b4")
                            .encode(
                                x="Date:T",
                                y=alt.Y("Close:Q", title="Kapanış Fiyatı"),
                                tooltip=["Date:T", "Close:Q"],
                            )
                            .properties(title=f"{selected} Son 60 Gün Mum Grafiği")
                        )
                        st.altair_chart(chart, use_container_width=True)
                    else:
                        st.warning("Grafik için yeterli veri yok.")
                except Exception:
                    st.error("Grafik yüklenemedi.")
                st.markdown(f"**Geçerli Rejim:** {row.get('regime', '-')}")
                st.markdown(
                    f"**Risk Uyarısı:** Kelly Kriteri Pozisyonu: {row.get('kelly_fraction', '-')}"
                )
                st.markdown(
                    f"**WFO Doğrulaması:** Out-of-Sample Başarı: {row.get('wfo_success', '-')}"
                )
                st.button("Portföye Ekle")
                st.button("Telegram'a Gönder")

# Footer
# --- Geçmiş Sinyaller Paneli ---
signal_log_path = os.path.join(os.getcwd(), "data", "logs", "signal_log.csv")
if os.path.exists(signal_log_path):
    st.markdown("---")
    st.markdown("## 📅 Geçmiş Sinyaller ve Performans")
    try:
        log_df = pd.read_csv(signal_log_path, header=None)
        log_df.columns = [
            "Tarih",
            "Sembol",
            "Fiyat",
            "Stop-Loss",
            "Take-Profit",
            "Skor",
            "Güç",
            "Rejim",
            "Sentiment",
            "Onchain",
            "Alım?",
            "Özet",
            "Neden",
        ]
        log_df["__timestamp"] = pd.to_datetime(log_df["Tarih"], errors="coerce")
        log_df = log_df.sort_values("__timestamp", ascending=False)

        col1, col2 = st.columns([2, 2])
        with col1:
            unique_dates = log_df["Tarih"].astype(str).dropna().unique().tolist()
            selected_date = st.selectbox("Tarih Seç", ["Tümü"] + unique_dates)
        with col2:
            unique_symbols = log_df["Sembol"].astype(str).dropna().unique().tolist()
            selected_symbol = st.selectbox("Sembol Seç", ["Tümü"] + unique_symbols)

        filtered = log_df.copy()
        if selected_date != "Tümü":
            filtered = filtered[filtered["Tarih"].astype(str) == selected_date]
        if selected_symbol != "Tümü":
            filtered = filtered[filtered["Sembol"].astype(str) == selected_symbol]

        if "Özet" in filtered.columns:
            summary_text = filtered["Özet"].fillna("")
            toggle_map = {
                "ana_trend": "Uzun vadeli trend",
                "orta_trend": "Orta vadeli trend",
                "kisa_sinyal": "Kısa vadeli sinyal",
                "hacim_artisi": "Hacim artışı",
                "momentum": "momentum",
                "trend_gucu": "Trend gücü",
            }
            for flag, keyword in toggle_map.items():
                flag_value = locals().get(flag, True)
                if flag_value is False:
                    mask = summary_text.str.contains(keyword, case=False, na=False)
                    filtered = filtered[mask]
                    summary_text = summary_text[mask]

        filtered_display = filtered.drop(columns="__timestamp", errors="ignore")

        tab_summary, tab_table, tab_export = st.tabs(["Özet", "Tablo", "Dışa Aktar"])
        with tab_summary:
            render_signal_history_overview(filtered_display)
        with tab_table:
            if filtered_display.empty:
                st.info("Gösterilecek kayıt yok.")
            else:
                st.dataframe(filtered_display, use_container_width=True, height=320)
        with tab_export:
            if filtered_display.empty:
                st.info("İndirilebilir veri yok.")
            else:
                csv_bytes = filtered_display.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "CSV olarak indir",
                    csv_bytes,
                    file_name=f"signal_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                )
    except Exception as e:
        st.warning(f"Geçmiş sinyal dosyası okunamadı: {e}")
# --- Sayfa Altı: Canlı Fiyat ve Optimizasyon Sonuçları ---
st.markdown("---")
st.markdown("### 🟢 Yahoo Finance Canlı Fiyat")
st.markdown("### 📈 Son Optimizasyon Sonuçları (Grid/WFO)")
wfo_path = os.path.join(os.getcwd(), "wfo_grid_search_results.csv")
grid_path = os.path.join(os.getcwd(), "grid_search_results.csv")
df_wfo = None
df_grid = None
if os.path.exists(wfo_path):
    try:
        df_wfo = pd.read_csv(wfo_path)
    except Exception:
        df_wfo = None
if os.path.exists(grid_path):
    try:
        df_grid = pd.read_csv(grid_path)
    except Exception:
        df_grid = None
if df_wfo is not None and not df_wfo.empty:
    st.markdown("#### WFO Grid Search Sonuçları")
    st.dataframe(df_wfo.tail(5), width="stretch")
elif df_grid is not None and not df_grid.empty:
    st.markdown("#### Grid Search Sonuçları")
    st.dataframe(df_grid.head(5), width="stretch")
else:
    st.info("Henüz optimizasyon sonucu bulunamadı.")
live_symbol = st.text_input(
    "Canlı fiyat için sembol girin (ör: AAPL, MSFT, TSLA)", value="AAPL", key="yahoo_live_symbol"
)
if live_symbol:
    try:
        ticker = yf.Ticker(live_symbol)
        hist_1m = ticker.history(period="1d", interval="1m")
        hist_15m = ticker.history(period="5d", interval="15m")
        hist_close = ticker.history(period="2d")
        shown = False
        if not hist_1m.empty:
            price_1m = hist_1m["Close"][-1]
            date_1m = hist_1m.index[-1].strftime("%Y-%m-%d %H:%M")
            st.info(f"1dk: {price_1m} | {date_1m} (15dk gecikmeli olabilir)")
            st.caption(
                "Son bar zamanı genellikle ABD piyasası kapanış saatidir (Türkiye saatiyle 23:00, yaz/kış değişebilir). Piyasa kapalıysa veri güncellenmez."
            )
            shown = True
        if not hist_15m.empty:
            price_15m = hist_15m["Close"][-1]
            date_15m = hist_15m.index[-1].strftime("%Y-%m-%d %H:%M")
            st.info(f"15dk: {price_15m} | {date_15m} (15dk gecikmeli olabilir)")
            st.caption(
                "Son bar zamanı genellikle ABD piyasası kapanış saatidir (Türkiye saatiyle 23:00, yaz/kış değişebilir). Piyasa kapalıysa veri güncellenmez."
            )
            shown = True
        if not hist_close.empty:
            price_close = hist_close["Close"][-1]
            date_close = hist_close.index[-1].strftime("%Y-%m-%d %H:%M")
            st.success(f"Kapanış: {price_close} | {date_close}")
            if pd.Timestamp.now().date() != hist_close.index[-1].date():
                st.warning("⚠️ Bu fiyat son kapanış fiyatıdır, gün içi canlı değildir.")
            shown = True
        if not shown:
            st.warning("Veri bulunamadı.")
    except Exception as e:
        st.error(f"Yahoo Finance hata: {e}")

# Karşılaştırmalı analiz ve rejim geçişi görselleştirme
with st.expander("🔬 Karşılaştırmalı Strateji Analizi ve Rejim Geçişleri", expanded=False):
    st.markdown("### Farklı Strateji Sonuçları Karşılaştırması")
    wfo_path = os.path.join(os.getcwd(), "wfo_grid_search_results.csv")
    grid_path = os.path.join(os.getcwd(), "grid_search_results.csv")
    df_wfo = pd.read_csv(wfo_path) if os.path.exists(wfo_path) else pd.DataFrame()
    df_grid = pd.read_csv(grid_path) if os.path.exists(grid_path) else pd.DataFrame()
    if not df_wfo.empty:
        st.markdown("#### WFO Grid Search Sonuçları (Son 20)")
        st.dataframe(df_wfo.tail(20), width="stretch")
        if "regime" in df_wfo.columns and "timestamp" in df_wfo.columns:
            st.markdown("#### Rejim Geçişleri (WFO)")
            st.line_chart(df_wfo.set_index("timestamp")["regime"])
    if not df_grid.empty:
        st.markdown("#### Grid Search Sonuçları (Son 20)")
        st.dataframe(df_grid.tail(20), width="stretch")
    if not df_wfo.empty and "score" in df_wfo.columns and "kelly_fraction" in df_wfo.columns:
        st.markdown("#### Kelly Fraksiyonu ve Skor Heatmap")
        import altair as alt

        heatmap = (
            alt.Chart(df_wfo)
            .mark_rect()
            .encode(x="kelly_fraction:O", y="score:O", color="regime:Q")
        )
        st.altair_chart(heatmap, use_container_width=True)

st.markdown("---")
st.markdown("🔥 **Basit Strateji:** Yeşil olanları al, stop ve hedefle bekle!")
