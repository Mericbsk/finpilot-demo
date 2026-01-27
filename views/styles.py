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
