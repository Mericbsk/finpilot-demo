# FinPilot — Tam Spektrum Sistem Audit (Bölüm A–E)

**Tarih:** 2026-06-11
**Kapsam:** Yönetici özeti + en kritik 10 modül + yatay sorunlar + kök neden
**Önceki audit:** [docs/FULL_AUDIT_REPORT.md](../../FULL_AUDIT_REPORT.md) (2026-05-23). Bu belge onu **tekrar etmez**, günceller ve yeni alanları (Academy, Alpaca broker, symbol universe, sinyal edge sorunu) ekler.

---

# BÖLÜM A — Sistem Bağlam Bloğu

| Boyut | Durum |
|-------|-------|
| **Ürün** | AI destekli hisse tarama + sinyal + eğitim platformu (DACH + TR pazarı hedefli SaaS) |
| **Birincil runtime** | Next.js 16 (web, :3001) + FastAPI (api, :8001→8000) + Redis. `docker compose up` |
| **İkincil/legacy** | Streamlit (`views/`, root `Dockerfile`) — açıkça "secondary surface" etiketli |
| **Backend stack** | Python 3.11, FastAPI, 22 router, JWT auth, SQLite (`data/finpilot.db`) |
| **Veri** | yfinance (15dk gecikmeli), Alpaca paper API (`drl/data_sources/alpaca_provider.py`) |
| **ML/DRL** | Stable-Baselines3 PPO/SAC/TD3, Optuna; **şu an donmuş** (Şubat 2026'dan beri) |
| **AI/LLM** | Groq/Claude/Gemini failover (`llm/router.py`); Academy içerik üretimi Groq |
| **Eğitim modülü** | Academy (`academy/` + `FinanceAcademy/`, :8001) — 6 ajan, izole |
| **Bildirim** | Telegram (`telegram_*.py`, root) |
| **Gözlemlenebilirlik** | Prometheus + Grafana + Langfuse (`monitoring/`) |
| **CI/CD** | GitHub Actions (`ci.yml`), pytest, %70 coverage kapısı |
| **Çalışma şekli** | Scanner → finpilot_score → (score_engine, üretimde çalışmıyor) → signals → watchlist → Telegram |

**Kritik gözlem:** Sistem teknik olarak olgun ve modüler, ancak **çekirdek değer önermesi (kârlı sinyal) henüz kanıtlanmadı** (bkz. [WIN_RATE_ANALIZI.md](WIN_RATE_ANALIZI.md)). Mühendislik yatırımı, edge doğrulamasının önünde.

---

# BÖLÜM B — Dosya/Klasör Tarama Tablosu

| Klasör | Durum | Rol | Not |
|--------|-------|-----|-----|
| `api/` | ✅ Aktif | FastAPI backend, 22 router | Üretim çekirdeği |
| `scanner/` | ✅ Aktif | Tarama, indikatör, skor | `score_engine.py` üretimde çağrılmıyor |
| `drl/` | ⚠️ Donmuş | DRL eğitim/inference | Şubat'tan beri yeni model yok |
| `agents/` | ✅ Aktif | 18 LangGraph ajanı | `ceo.py` orchestrator |
| `core/` | ✅ Aktif | config, cache, logging, scheduler | Bir kısmı orphan (FULL_AUDIT) |
| `auth/` | ✅ Aktif | JWT, session, portfolio | SQLite→PG geçişi yarım |
| `llm/` | ✅ Aktif | Provider failover | `router.py` |
| `academy/` | ⚠️ İzole | Eğitim ajanları | Scanner/DRL'ye bağlı değil |
| `FinanceAcademy/` | ⚠️ Ayrı app | Standalone Academy (:8001) | `academy/` ile çift kopya riski |
| `broker/` | ❌ Stub | Sadece `__init__.py` | Alpaca aslında `drl/data_sources/`'da |
| `monitoring/` | ✅ Aktif | Prometheus/Grafana | |
| `scripts/` | ✅ Aktif | backtest, enrich, consolidate | `enrich_market_caps.py`, `consolidate_presets.py` yeni |
| `web/` | ✅ Aktif | Next.js frontend | 1.6GB (node_modules dahil) |
| `views/` | ❌ Legacy | Streamlit | Sadece demo |
| `archive/` | ❌ Legacy | Temizlenmiş eski kod | 2026-05 audit'te ayıklandı |
| `tests/` | ✅ Aktif | 35+ dosya, %70 kapısı | 13 router testsiz |

---

# BÖLÜM C — Kritik 10 Modül Kartı

### C.1 `scanner/` — Tarama & Skorlama ⭐ (en kritik)
- **Dosyalar:** `data_fetcher.py`, `indicators.py`, `signals.py`, `finpilot_score.py`, `score_engine.py`, `risk_engine.py`, `earnings_blackout.py`
- **Çalışıyor:** Çok-zaman-dilimli fetch, RSI/MACD/Bollinger/EMA/ATR, paralel değerlendirme, symbol universe filtresi (yeni: `universe`, `market_cap_min/max`)
- **🔴 KRİTİK SORUN:** `score_engine.py` üretimde çağrılmıyor (FULL_AUDIT). Ayrıca skor **ters-decile** sorunu var: en yüksek skor en kötü getiri (decile_lift=0.728<1, bkz WIN_RATE).
- **Aksiyon:** Skor yön/ağırlık denetimi — en yüksek öncelik.

### C.2 `api/` — FastAPI Backend ⭐
- **22 router:** scan, trade, watchlist, profitcore, closed_loop, academy, advisory, ensemble, inference, optuna, vb.
- **Çalışıyor:** Health/readiness/metrics, JWT, analytics
- **⚠️ Sorun:** 13 router testsiz; JWT bazı route'larda enforce edilmiyor (April audit bulgusu — teyit gerekli)

### C.3 `drl/` — Deep RL ⚠️ Donmuş
- PPO/SAC/TD3, Optuna, walk-forward, `data_sources/alpaca_provider.py` (yeni, tam)
- **Durum:** Sharpe 0.043–0.063, iterasyon 8'de donmuş, `experiment_log` boş
- **Aksiyon:** Üretim iddiası yok; deneysel etiketle

### C.4 `agents/` — Multi-Agent ✅
- 18 ajan: `ceo.py` (orchestrator), advisory, research, backtest, strategy_optimizer, risk, scanner_agent, social_intelligence
- LangGraph StateGraph; LLM bağımlı
- **⚠️ Sorun:** Ajan çıktılarının gerçek edge'e katkısı ölçülmüyor

### C.5 `auth/` — Kimlik & Oturum ✅
- JWT, session, portfolio, `db_backend.py` (SQLite↔PG abstraction)
- **⚠️ Sorun:** PostgreSQL geçişi (S2-1) yarım; SQLite tek-yazıcı limiti ölçeklemede risk

### C.6 `academy/` + `FinanceAcademy/` — Eğitim ⚠️ İzole
- 6 ajan (gap_detector, content_generator, quality_guard, personalization, content_updater, analytics) + orchestrator + scheduler
- 12 domain, 7 seed ders, SQLite, Groq
- **🔴 SORUN:** Çekirdek FinPilot'tan tamamen izole; scanner/DRL sinyallerini kullanmıyor. `academy/` ve `FinanceAcademy/academy/` çift kopya. (Detay: [ACADEMY_SELF_EVOLVING_TASARIM.md](../../academy/ACADEMY_SELF_EVOLVING_TASARIM.md))

### C.7 `llm/` — Provider Failover ✅
- Groq→Claude→Gemini, Langfuse izleme
- **⚠️ Sorun:** Tek noktada başarısızlık riski; maliyet/token izleme dağınık

### C.8 `broker/` + Alpaca — İşlem Katmanı ❌/⚠️
- `broker/` boş stub; gerçek entegrasyon `drl/data_sources/alpaca_provider.py` (paper)
- **🔴 SORUN:** İsimlendirme yanıltıcı; broker mantığı yanlış pakette. Edge kanıtlanana kadar canlı trade kapalı kalmalı.

### C.9 `web/` — Next.js Frontend ✅
- Dashboard, scanner sayfası (9 preset / 1812 sembol), finsense (Academy), kategoriler EN
- **⚠️ Sorun:** Static preset JSON ile backend senkronu manuel (`docker compose cp`)

### C.10 Symbol Universe & Scripts ✅ (yeni)
- `scripts/sync_symbols.py` (market_cap, symbol_lists tablosu), `enrich_market_caps.py` (preset_1500=1449, iwm_300m=366), `consolidate_presets.py` (40→9 preset)
- **Çalışıyor:** DB total=13.852, tradable=13.033, market_cap=1.736
- **⚠️ Sorun:** scanner/drl/scripts image'a baked → değişiklik `docker compose cp` gerektiriyor

---

# BÖLÜM D — Yatay (Sistem Geneli) Sorun Analizi

**D.1 — Kanıtlanmamış edge (🔴 EN KRİTİK):** Out-of-sample testler edge gösteremiyor. Tüm ürün/funding anlatısı bu boşluğun üstünde duruyor.

**D.2 — Ters-decile skorlama:** En yüksek skor en kötü getiri. Skor motoru muhtemelen yanlış yönde optimize/ağırlıklandırılmış.

**D.3 — In-sample / out-of-sample makası:** Backtest (Sharpe 8, S-tier) parlak; walk-forward negatif (DSR -17). Pazarlamada in-sample kullanım riski.

**D.4 — Modül izolasyonu:** Academy tamamen ayrı; broker yanlış pakette; `FinanceAcademy/` çift kopya. Mimari tutarsızlık.

**D.5 — Donmuş DRL:** README "DRL Integration" diye pazarlıyor ama model Şubat'tan beri donmuş, Sharpe ~0.05.

**D.6 — Test boşlukları:** 13 router testsiz; JWT enforcement teyit edilmemiş; SQLite ölçek limiti.

**D.7 — Operasyonel kırılganlık:** Image'a baked kod (scanner/drl/scripts) volume-mount değil → hot-fix için `docker compose cp`. Preset JSON manuel senkron. data/ izin sorunları.

---

# BÖLÜM E — Kök Neden (5-Why) Kartları

### E.1 Neden edge kanıtlanamıyor?
1. Out-of-sample test ediliyor mu? Evet (profitcore). → 2. Sonuç? NO EDGE. → 3. Neden? Skor ters-decile + overfit. → 4. Neden overfit? Az veri (1074 sembol, kısa pencere) + 13.824 kombinasyon grid (data snooping). → 5. **Kök neden: parametre arama uzayı veri miktarına göre çok büyük; deflated Sharpe negatif.**

### E.2 Neden skor ters çalışıyor?
1. Yüksek skor düşük getiri. → 2. `score_engine` üretimde çalışmıyor, `finpilot_score` aktif. → 3. Ağırlıklar in-sample optimize edilmiş. → 4. In-sample momentum sinyalleri OOS'ta tersine dönüyor (mean reversion). → 5. **Kök neden: momentum-ağırlıklı skor, küçük-cap evreninde mean-reversion rejimine karşı kalibre değil.**

### E.3 Neden Academy izole?
1. Ayrı app + ayrı DB. → 2. Bağımsız geliştirildi. → 3. Scanner/DRL API kontratı tanımlanmamış. → 4. Entegrasyon önceliklendirilmemiş. → 5. **Kök neden: Academy "eğitim" silosu olarak tasarlandı; ürün-içi kişiselleştirme (kullanıcının taradığı sembollere göre ders) hiç planlanmadı.**

### E.4 Neden mimari drift var?
1. broker yanlış pakette, FinanceAcademy çift kopya. → 2. Hızlı iterasyon. → 3. Refactor önceliklendirilmedi. → 4. Edge baskısı altında "çalışan" kod taşınmadı. → 5. **Kök neden: ürün-market fit baskısı, mimari borç birikimine yol açtı.**

---

# Özet Öncelik Sırası

| # | Sorun | Etki | Öncelik |
|---|-------|------|---------|
| 1 | Ters-decile skor (D.2/E.2) | Ürün değeri sıfır/negatif | 🔴 P0 |
| 2 | Edge kanıtı yok (D.1/E.1) | Funding/pazarlama riski | 🔴 P0 |
| 3 | In-sample pazarlama riski (D.3) | İtibar/yasal | 🟠 P1 |
| 4 | DRL donmuş ama pazarlanıyor (D.5) | İddia tutarsızlığı | 🟠 P1 |
| 5 | Academy izolasyonu (D.4/E.3) | Kaçırılan değer | 🟡 P2 |
| 6 | broker/FinanceAcademy mimari (D.4) | Bakım borcu | 🟡 P2 |
| 7 | Test/operasyon boşlukları (D.6/D.7) | Kırılganlık | 🟡 P2 |

---
*FinPilot Sistem Audit — 2026-06-11*
