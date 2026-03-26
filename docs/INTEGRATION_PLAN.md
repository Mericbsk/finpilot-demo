# FinPilot Integration Plan

> Next.js Frontend ↔ Streamlit Backend Architecture

## Overview

The new Apple-style Next.js frontend (`/web`) serves as the public-facing website,
while the existing Streamlit application remains the core analysis engine.
This document defines how the two systems integrate.

---

## Architecture

```
┌──────────────────────────┐         ┌──────────────────────────┐
│   Next.js Frontend       │         │   Streamlit Backend      │
│   (Vercel / CDN)         │         │   (Docker / Cloud Run)   │
│                          │         │                          │
│  • Landing page          │  REST   │  • 15 AI models          │
│  • Demo page             │◄───────►│  • DRL agents            │
│  • Waitlist form         │  API    │  • Scanner engine        │
│  • Auth (NextAuth.js)    │         │  • Backtest engine       │
│  • Dashboard (future)    │         │  • FinSense Academy      │
│                          │         │  • Social features       │
└──────────────────────────┘         └──────────────────────────┘
          │                                    │
          ▼                                    ▼
   ┌─────────────┐                    ┌────────────────┐
   │  Supabase    │                   │  PostgreSQL    │
   │  (Auth + DB) │                   │  (analytics)   │
   └─────────────┘                    └────────────────┘
```

## Phase 1 — Static Website (Current)

**Goal:** Professional public presence for YC, grants, and user acquisition.

| Component | Status | Notes |
|-----------|--------|-------|
| Landing page | ✅ Done | Navbar, Hero, Features, Pricing, Waitlist, Footer |
| Demo page | ✅ Done | Interactive stock scanner with sample AI analysis |
| Waitlist form | ⚠️ Simulated | Needs backend API to store emails |
| Deployment | ❌ Pending | Deploy to Vercel via MCP |

### Action Items
1. Connect waitlist form to Supabase or a simple API endpoint
2. Deploy to Vercel with custom domain (`finpilot.ai`)
3. Set up analytics (Vercel Analytics or Plausible)

---

## Phase 2 — API Layer

**Goal:** Expose Streamlit backend capabilities as REST endpoints.

### Proposed API Endpoints

```
POST /api/waitlist          → Store email in database
GET  /api/scanner           → Get latest scan results
GET  /api/analysis/:ticker  → Get AI analysis for a stock
GET  /api/backtest/:ticker  → Run backtest and return results
GET  /api/finsense/:topic   → Get educational content
POST /api/auth/login        → User authentication
POST /api/auth/register     → User registration
```

### Implementation: FastAPI Wrapper

Create a FastAPI service that wraps existing Streamlit/Python logic:

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FinPilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://finpilot.ai", "http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/api/scanner")
async def get_scanner_results():
    # Import existing scanner logic
    from scanner import parallel_scanner
    results = parallel_scanner.run()
    return {"data": results}

@app.get("/api/analysis/{ticker}")
async def get_analysis(ticker: str):
    # Import existing analysis logic
    from views import view_analysis
    result = view_analysis.analyze(ticker)
    return {"data": result}
```

### Key Modules to Expose

| Module | File | API Endpoint |
|--------|------|-------------|
| Scanner | `scanner.py`, `parallel_scanner.py` | `/api/scanner` |
| Analysis | `views/view_analysis.py` | `/api/analysis/:ticker` |
| Backtest | `core/backtest.py` | `/api/backtest/:ticker` |
| DRL Agent | `drl/` | `/api/drl/:ticker` |
| FinSense | `views/view_finsense.py` | `/api/finsense/:topic` |
| Dictionary | `data/dictionary.json` | `/api/dictionary` |

---

## Phase 3 — Authentication & Dashboard

**Goal:** Authenticated user experience with personal portfolios.

### Auth Flow
1. **NextAuth.js** on the frontend (Google, email/password)
2. **Supabase Auth** as the identity provider
3. JWT tokens passed to FastAPI backend
4. Existing `auth/` module bridges Supabase ↔ Streamlit sessions

### Dashboard Features (mapped to existing views)
| Dashboard Section | Existing View File | Priority |
|------------------|--------------------|----------|
| Portfolio | `views/view_portfolio.py` | P0 |
| AI Analysis | `views/view_analysis.py` | P0 |
| Scanner | `views/view_scanner.py` | P0 |
| Backtest | `views/view_backtest.py` | P1 |
| FinSense Academy | `views/view_finsense.py` | P1 |
| Social | `views/view_social.py` | P2 |
| Settings | `views/view_settings.py` | P2 |
| DRL Lab | `views/view_drl_lab.py` | P2 |

---

## Phase 4 — Full Migration

**Goal:** Next.js replaces Streamlit as the primary UI.

| Task | Description |
|------|-------------|
| Real-time data | WebSocket feeds (`core/websocket_feeds.py`) → Next.js via Socket.io |
| Charts | Replace Streamlit charts with Recharts / Lightweight Charts |
| Telegram integration | Keep as-is (already independent: `telegram_bot_runner.py`) |
| Mobile PWA | Next.js + service worker for mobile experience |

---

## Deployment Strategy

```
Production:
  Next.js  → Vercel (free tier → Pro at scale)
  FastAPI  → Google Cloud Run (Docker)
  Database → Supabase (free tier → Pro)
  Models   → Cloud Run GPU (when needed)

Development:
  Next.js  → localhost:3000
  Streamlit → localhost:8501
  FastAPI  → localhost:8000
```

### Docker Compose Addition

```yaml
# Add to existing docker-compose.yml
services:
  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    depends_on:
      - streamlit
```

---

## Timeline

| Phase | Scope | Duration |
|-------|-------|----------|
| 1 | Static site + Vercel deploy | ✅ Now |
| 2 | FastAPI wrapper + Waitlist API | 1-2 weeks |
| 3 | Auth + Dashboard shell | 2-3 weeks |
| 4 | Full migration + real-time | 4-6 weeks |

---

## Key Decisions

1. **FastAPI over Django** — Lighter, async-first, better for wrapping existing code
2. **Supabase over custom auth** — Free tier, built-in Row Level Security, Postgres
3. **Vercel for Next.js** — Zero-config deployment, edge functions, analytics
4. **Keep Streamlit** — Internal tool / power-user interface alongside the new web UI
