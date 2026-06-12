# FinPilot — Kullanım Kılavuzu

> **Sürüm:** 2026-06-12 · **Ortam:** Docker Compose (finpilot_web :3001 · finpilot_api :8001)

---

## İçindekiler

1. [Sistem Nedir?](#1-sistem-nedir)
2. [Ne Yapıyor? — Otomatik İş Akışı](#2-ne-yapıyor--otomatik-iş-akışı)
3. [Sinyal Yaşam Döngüsü](#3-sinyal-yaşam-döngüsü)
4. [Sistemi Başlatmak / Durdurmak](#4-sistemi-başlatmak--durdurmak)
5. [Dashboard — Ne Nerede Görülür?](#5-dashboard--ne-nerede-görülür)
6. [Tarama Sonuçlarını Okumak](#6-tarama-sonuçlarını-okumak)
7. [API Referansı — Temel Endpoint'ler](#7-api-referansı--temel-endpointler)
8. [Agent Sistemi](#8-agent-sistemi)
9. [Konfigürasyon](#9-konfigürasyon)
10. [İzleme ve Sağlık Kontrolü](#10-izleme-ve-sağlık-kontrolü)
11. [Sık Sorulan Sorular](#11-sık-sorulan-sorular)

---

## 1. Sistem Nedir?

FinPilot, **hisse senedi tarama, risk yönetimi ve kâr izleme** süreçlerini otomatize eden bir yapay zeka platformudur.

```
┌──────────────────────────────────────────────────────────┐
│  Web Arayüzü (Next.js)            :3001                  │
│  ┌───────────┐  ┌──────────┐  ┌───────────┐             │
│  │  Scanner  │  │ Portfolio│  │  Academy  │             │
│  └───────────┘  └──────────┘  └───────────┘             │
└──────────────────────────┬───────────────────────────────┘
                           │ REST/JSON
┌──────────────────────────▼───────────────────────────────┐
│  FastAPI Backend                  :8001                  │
│  ┌─────────┐  ┌──────────┐  ┌──────────────────────┐    │
│  │ Scanner │  │  Agents  │  │ Scheduler (APSched)  │    │
│  │   API   │  │   API    │  │  Saatlik otomatik    │    │
│  └─────────┘  └──────────┘  └──────────────────────┘    │
└──────────────────────────┬───────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   SQLite DB           Redis Cache       LLM Router
   (sinyal, KPI)    (geçici önbellek)  (Claude/Gemini/Groq)
```

**Temel özellikler:**
- **Otomatik saatlik tarama** — 500+ sembol üzerinde teknik + LLM analizi
- **Risk metrikleri** — Sharpe, Sortino, MaxDD, yıllık getiri hesaplama
- **Dinamik pozisyon boyutlandırma** — Kelly criterion + rejim ölçeği
- **Bull/Bear araştırması** — Her sembol için ayrı yükseliş/düşüş tezi (LLM)
- **Sosyal zeka** — Reddit/HN/Polymarket sentiment (FinBERT)
- **Kağıt portföy** — Onaylanan sinyaller otomatik simülasyon işlemi
- **Backtest** — Rejime göre strateji geriye dönük test
- **Telegram alarmları** — Kritik sinyal ve portföy olayları

---

## 2. Ne Yapıyor? — Otomatik İş Akışı

Sistem **her saat** otomatik olarak şu adımları çalıştırır:

```
┌─────────────────────────────────────────────────────────────┐
│  SAATLIK DÖNGÜ (core/scheduler.py → run_cycle_once)         │
│                                                             │
│  0. Piyasa Zekası     → Rejim tespiti (trend/chop/volatile) │
│  0b. Veri Kalitesi    → Sorunlu semboller belirlenir        │
│                                                             │
│  1. TARAMA            → Teknik filtreler + risk metrikleri  │
│     + Social          → Reddit/HN/Polymarket sentiment      │
│     + Bull/Bear       → LLM tez üretimi (paralel)           │
│                                                             │
│  2. Araştırma         → Haber + bağlam zenginleştirme       │
│  3. Backtest          → Rejime göre strateji testi          │
│  4. Strateji Opt.     → Parametre önerileri                 │
│  5. Performans        → KPI/drawdown kontrolü               │
│  6. Rapor             → Günlük Markdown raporu              │
│                                                             │
│  AYRI CRONLAR:                                              │
│  30dk: auto_approve   → p_win ≥ 0.65 → kağıt işlem         │
│  2sa: reconcile       → açık sinyallerin sonuç kaydı       │
│  Haftalık: retrain    → kalibrasyon modeli yeniden eğit     │
└─────────────────────────────────────────────────────────────┘
```

**Feedback döngüsü:**
- Strateji optimizeri iyi parametreler bulunca `data/scanner_config.json`'a yazar
- Veri kalitesi ajanı sorunlu sembolleri 24 saat dışlar
- Portföy drawdown tespitinde Kelly fraction otomatik azalır (×0.70)
- Alpha Tracker win-rate'e göre tarama eşiğini otomatik ayarlar

---

## 3. Sinyal Yaşam Döngüsü

Her sinyal şu aşamalardan geçer — `signal_events` tablosunda izlenebilir:

```
SCANNED ──────────────────────────────────────────────────────────
  (ScannerAgent filtreler, finpilot_score üretir)
    │
    ├── Social sentiment eklenir (Reddit/HN/Polymarket buzz)
    ├── Bull tezi üretilir (3-5 yükseliş argümanı)
    └── Bear riski üretilir (3-5 risk faktörü)
         │
SCORED ───────────────────────────────────────────────────────────
  (Kalibrasyon: ham_skor → p_win olasılığı)
    │
DECIDED ──────────────────────────────────────────────────────────
  (RiskAgent + auto_approve politikası: p_win ≥ 0.65 → onayla)
    │
    ├── REJECTED → ARCHIVED (gerekçe kaydı)
    │
APPROVED ─────────────────────────────────────────────────────────
  (AlertAgent Telegram'a gönderir)
  (PaperPortfolio açık pozisyon oluşturur)
    │
OPEN ─────────────────────────────────────────────────────────────
  (T+3, T+5, T+10 günlerde sonuç kontrolü)
    │
RESOLVED ─────────────────────────────────────────────────────────
  (Kâr/zarar kaydı → AlphaTracker → PerformanceMonitor)
```

---

## 4. Sistemi Başlatmak / Durdurmak

### Başlatma
```powershell
# İlk kurulum / güncelleme sonrası
cd C:\Users\meric\Borsa
docker compose build
docker compose up -d

# Sadece yeniden başlat (kod değişikliği yoksa)
docker compose restart
```

### Durdurma
```powershell
docker compose down          # container'ları durdur (data korunur)
docker compose down -v       # ⚠️ volume'ları da sil (data silinir!)
```

### Tek container yenileme (hızlı)
```powershell
docker compose restart api   # sadece backend
docker compose restart web   # sadece frontend
```

### Logları izleme
```powershell
docker logs finpilot_api --tail 50 -f   # API logları (canlı)
docker logs finpilot_web --tail 20      # Web logları
```

### Migration (DB şema güncellemesi)
```powershell
cd C:\Users\meric\Borsa
python -m alembic upgrade head
```

---

## 5. Dashboard — Ne Nerede Görülür?

**Ana URL:** http://localhost:3001

| Sayfa | URL | Ne Gösterir |
|---|---|---|
| **Scanner** | `/dashboard/scanner` | Tarama sonuçları, Sharpe/Vol%, dinamik pozisyon boyutu |
| **Portfolio** | `/dashboard/portfolio` | Kağıt portföy, açık/kapalı pozisyonlar |
| **Signals** | `/dashboard/signals` | Onaylanan/bekleyen sinyaller, p_win |
| **Backtest** | `/dashboard/backtest` | Strateji geriye dönük test sonuçları |
| **Academy** | `/dashboard/academy` | Eğitim modülleri |
| **Settings** | `/dashboard/settings` | API anahtarları, Telegram, tercihler |

### Scanner Sayfası — Sütun Açıklamaları

| Sütun | Açıklama |
|---|---|
| **Score** | `finpilot_score` — 0–4 arası bileşik teknik skor |
| **Entry** | `entry_ok` — tüm giriş koşulları sağlanıyor mu? |
| **P** | Fiyat |
| **R/R** | Risk/Ödül oranı (hedef / stop mesafesi) |
| **Sharpe** | 252 günlük yıllık Sharpe oranı (>1 = iyi, >2 = çok iyi) |
| **Vol%** | Yıllık volatilite yüzdesi |
| **Shares** | Dinamik pozisyon büyüklüğü (Kelly + rejim) |

### Detay Paneli — Risk Metrikleri

Scanner'da bir satıra tıklayınca sağ panelde açılır:

```
Risk Metrikleri
  Sharpe Oranı:    2.45   ✓ >1 = kabul edilebilir
  Sortino Oranı:   2.54   (aşağı yönlü volatilite odaklı)
  Calmar Oranı:    7.16   (yıllık getiri / max drawdown)
  Max Drawdown:   -12.3%
  Yıllık Vol:     18.7%
  Yıllık Getiri:  +87.9%
  EV/işlem:        0.82   (beklenen değer: >0 = pozitif edge)

Dinamik Pozisyon (Trade Plan)
  Paylar:          50
  Teorik büyüklük: $7,500
  Risk yüzdesi:     0.5%  (hesap büyüklüğüne göre)
  Kelly oranı:     12.4%
  Rejim ölçeği:     0.75  (<1 = muhafazakâr)
```

---

## 6. Tarama Sonuçlarını Okumak

### Nasıl Çalışır?

Scanner sayfasında **"Tara"** düğmesine basınca veya scheduler saatlik döngüde çalışınca:

1. Seçilen semboller `GET /api/v1/scan` ile taranır
2. Her sembol için teknik + risk metrikleri hesaplanır
3. Sonuçlar `finpilot_score` ile sıralanır, üst 5 sembol belirlenir
4. Bull/Bear ve Social analiz (saatlik döngüde) üst sembollere uygulanır

### Sinyali Yorumlamak

```
AAPL  score=3.2  entry_ok=✓  R/R=2.8  Sharpe=2.1  Vol=16%
```

- `score ≥ 2.5` + `entry_ok = ✓` → güçlü sinyal
- `R/R ≥ 2.0` → risk/ödül yeterli
- `Sharpe ≥ 1.0` → tarihsel getiri tatmin edici
- `Vol < 30%` → kontrol edilebilir volatilite

### Otomatik Onay Koşulları

`auto_approve` işi (30dk'da bir):
- `p_win ≥ 0.65` → sinyal otomatik onaylanır
- Onaylanan sinyal → kağıt portföyüne BUY işlemi açılır
- Telegram'a bildirim gider

---

## 7. API Referansı — Temel Endpoint'ler

**Base URL:** `http://localhost:8001/api/v1`

Tüm endpoint'ler için dokümantasyon: http://localhost:8001/docs

### Kimlik Doğrulama

```bash
# Token al
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Token'ı header'a ekle
Authorization: Bearer <token>
```

### Tarama

```bash
# Manuel tarama başlat
POST /api/v1/scan
{
  "symbols": ["AAPL","NVDA","MSFT"],
  "kelly_fraction": 0.5
}

# Sonuç: finpilot_score, entry_ok, risk metrikleri, dinamik pozisyon
```

### Agent Sistemi

```bash
# Agent çalıştır (full pipeline)
POST /api/v1/agent/run
{"task": "full", "symbols": ["AAPL","NVDA"], "kelly_fraction": 0.5}

# task seçenekleri:
#   "scan"    → sadece tarama
#   "analyze" → tarama + analiz
#   "risk"    → risk değerlendirmesi
#   "full"    → tam pipeline
#   "auto"    → tüm fazlar (social+bull_bear+backtest+synthesize)
#   "advisory"→ danışman persona

# Agent durumları
GET /api/v1/agent/status

# Agent kaydı
GET /api/v1/agent/registry

# Registry doğrulama (kod vs kayıt farkları)
GET /api/v1/agent/registry/audit

# Pipeline olayları (sinyal yaşam döngüsü izleme)
GET /api/v1/agent/signal-events?symbol=AAPL&limit=50
GET /api/v1/agent/signal-events?cycle_id=cycle-abc123def456

# Scheduler durumu
GET /api/v1/agent/scheduler

# KPI metrikleri
GET /api/v1/agent/kpis

# Son olaylar
GET /api/v1/agent/events?limit=20
```

### Portföy

```bash
# Kağıt portföy durumu
GET /api/v1/portfolio/paper

# Açık pozisyonlar
GET /api/v1/portfolio/open

# İzleme listesi
GET /api/v1/watchlist
POST /api/v1/watchlist/add  {"symbol":"AAPL"}
```

### Sinyaller

```bash
# Aktif sinyaller
GET /api/v1/signals

# Belirli sinyal detayı
GET /api/v1/signals/{signal_id}
```

### Sistem Sağlığı

```bash
GET /api/v1/health    # hızlı durum
GET /api/v1/ready     # tüm bağımlılıklar hazır mı?
```

---

## 8. Agent Sistemi

### Gerçek Çalışan Agent'lar (Üretim)

| Agent | Görevi | Tetikleyici |
|---|---|---|
| **ScannerAgent** | Teknik filtreler + risk metrikleri | Saatlik döngü, API |
| **MarketIntelligenceAgent** | Piyasa rejimi tespiti | Saatlik döngü başı |
| **DataQualityAgent** | Veri doğrulama kapısı | Saatlik döngü |
| **ResearchAgent** | Haber ve bağlam zenginleştirme | Saatlik döngü |
| **SocialIntelligenceAgent** | Reddit/HN/Polymarket sentiment | Pipeline `stages={"social"}` |
| **BullResearcherAgent** | 3-5 yükseliş tezi (LLM) | Pipeline `stages={"bull_bear"}` |
| **BearResearcherAgent** | 3-5 düşüş riski (LLM) | Pipeline `stages={"bull_bear"}` |
| **BacktestAgent** | Strateji geriye dönük testi | Saatlik döngü |
| **RiskAgent** | Pozisyon boyutu + Kelly | Pipeline, API |
| **AlertAgent** | Telegram bildirimi | Pipeline |
| **PerformanceMonitorAgent** | KPI + drawdown izleme | Saatlik döngü |
| **StrategyOptimizerAgent** | Parametre optimizasyonu | Her N döngü |
| **ReportAgent** | Günlük Markdown raporu | Günlük cron |
| **AlphaTrackerAgent** | Win-rate + skor eşiği | Saatlik döngü |

### Advisory Persona'lar (İsteğe Bağlı)

15 LLM persona — `POST /api/v1/agent/run {"task":"advisory","agent_key":"cto"}` ile çalıştırılır. Saatlik döngüde otomatik çalışmaz (devre dışı bırakıldı — maliyet optimizasyonu).

Mevcut persona'lar: `cto`, `cpo`, `cmo`, `senior_dev`, `frontend_dev`, `ai_ml_dev`, `devops`, `growth_marketer`, `content_strategist`, `biz_dev`, `competitive_intel`, `qa_test`, `code_review`, `pm`, `customer_success`

### Pipeline Mimarisi

```
core/pipeline.run_cycle(symbols, task, stages)
    ├── task="scan"    → 1. Tarama
    ├── task="analyze" → 1. Tarama → 2. Analiz
    ├── task="risk"    → 1. Tarama → 3. Risk
    ├── task="full"    → 1→2→3→4 (Tarama→Analiz→Risk→Alert)
    │
    └── stages={"social"}     → + Sosyal zeka
        stages={"bull_bear"}  → + Bull/Bear tez
        stages={"backtest"}   → + Backtest
        stages={"synthesize"} → + Bileşik güven skoru
```

---

## 9. Konfigürasyon

### Ortam Değişkenleri (`.env` veya `docker-compose.yml`)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/finpilot.db` | Veritabanı bağlantısı |
| `REDIS_URL` | `redis://redis:6379/0` | Redis (opsiyonel; yoksa in-memory fallback) |
| `ANTHROPIC_API_KEY` | — | Claude LLM |
| `GOOGLE_API_KEY` | — | Gemini LLM |
| `GROQ_API_KEY` | — | Groq LLM (hız öncelikli) |
| `SOCIAL_SENTIMENT_ENABLED` | `true` | Sosyal zeka on/off |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bildirimleri |
| `TELEGRAM_CHAT_ID` | — | Telegram hedef chat |
| `ALPACA_API_KEY` | — | Gerçek işlem (opsiyonel) |

### Scanner Konfigürasyonu

`data/scanner_config.json` — strateji optimizeri tarafından otomatik güncellenir:

```json
{
  "kelly_fraction": 0.5,
  "min_score": 2.0,
  "min_rr": 1.5,
  "_updated_cycle": 42
}
```

### Kelly Fraction Otomatik Ayarı

- Portföy **WARN** (drawdown > %10) → kelly × 0.70
- Portföy **STOP** (drawdown > %20) → kelly × 0.70
- Ayar `scanner_config.json`'a kalıcı olarak yazılır

---

## 10. İzleme ve Sağlık Kontrolü

### Hızlı Kontrol

```powershell
# API sağlığı
Invoke-RestMethod http://localhost:8001/api/v1/health

# Scheduler durumu
Invoke-RestMethod http://localhost:8001/api/v1/agent/scheduler

# Son 5 pipeline olayı
Invoke-RestMethod "http://localhost:8001/api/v1/agent/signal-events?limit=5"

# KPI özeti
Invoke-RestMethod http://localhost:8001/api/v1/agent/kpis
```

### Örnek Scheduler Çıktısı

```json
{
  "running": true,
  "cycle_count": 18,
  "last_run": "2026-06-12T17:00:04Z",
  "last_status": "ok",
  "next_run_approx": "2026-06-12T18:00:00Z"
}
```

### Pipeline Olaylarını İzleme

```powershell
# Belirli bir sembolün son olayları
Invoke-RestMethod "http://localhost:8001/api/v1/agent/signal-events?symbol=NVDA&limit=20"

# Tüm döngüler (son 100 olay)
Invoke-RestMethod "http://localhost:8001/api/v1/agent/signal-events?symbol=*&limit=100"

# Belirli döngü (cycle_id pipeline state'ten okunur)
Invoke-RestMethod "http://localhost:8001/api/v1/agent/signal-events?cycle_id=cycle-abc123def456"
```

### Örnek Olay Çıktısı

```json
{
  "events": [
    {
      "id": 42,
      "signal_id": "cycle-3f7a9c2b1d4e",
      "symbol": "AAPL",
      "from_state": "init",
      "to_state": "scan_done",
      "agent": "scanner",
      "payload": {"n_symbols": 50, "top": ["AAPL","NVDA","MSFT","GOOGL","AMZN"]},
      "ts": "2026-06-12 17:00:08",
      "success": true,
      "error": null
    }
  ],
  "count": 1
}
```

### Registry Doğrulama (Kod vs Kayıt)

```powershell
Invoke-RestMethod http://localhost:8001/api/v1/agent/registry/audit
# "ok": true → registry kodla örtüşüyor
# "in_code_not_registry": [...] → kodda var, registry'de yok → ekle
# "in_registry_not_code": [...] → registry'de var, kodda yok → sil/güncelle
```

### Telegram Alarmları

Sistem şu durumlarda otomatik Telegram mesajı gönderir:

| Olay | Mesaj |
|---|---|
| p_win ≥ 0.65 sinyal | `✅ Auto-Approve — N sinyal onaylandı` |
| Portföy WARN | `⚠️ PORTFÖY WARN — Cycle #N` |
| Portföy STOP | `🛑 PORTFÖY STOP — En kötü: SEMBOL DD=X%` |
| Onaylı ama işlensiz | `⚠️ Auto-Approve Alarm — N sembol kağıt işlem bekliyor` |
| Günlük rapor | Markdown özet |

---

## 11. Sık Sorulan Sorular

### "Tarama sonuçları neden geliyor ama bazı alanlar boş?"

Bull/Bear ve Social veriler yalnızca `stages={"social","bull_bear"}` ile çalıştırıldığında dolar — bu saatlik scheduler döngüsünde otomatik olur. Manuel "Tara" butonu yalnızca temel taramayı (`task="scan"`) çalıştırır. Tam pipeline için `task="auto"` veya `task="full"` kullanın.

### "Sharpe oranı neden bazı sembollerde eksik?"

Yeterli tarihsel veri yoksa (`< 30 bar`) hesap yapılamaz ve alan `null` döner. Şirketler için `window=None` ile 252 günlük hesap varsayılan olarak kullanılır.

### "Sistem saatlik çalışıyor ama Telegram'dan mesaj gelmedi?"

1. `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` env'de tanımlı mı?
2. `scheduler durumu: Invoke-RestMethod http://localhost:8001/api/v1/agent/scheduler` — `running: true` mu?
3. `docker logs finpilot_api --tail 50` — hata var mı?
4. p_win eşiği aşıldı mı? KPI kontrolü: `http://localhost:8001/api/v1/agent/kpis`

### "Redis yok ama sistem çalışıyor — sorun var mı?"

Redis olmadan sistem çalışır ama iki fark olur:
- Feedback mesajları in-memory'de tutulur → **process restart'ta kaybolur**
- DQ exclusion listesi in-memory'de tutulur → **restart'ta sıfırlanır**
- Cache olmadığından LLM çağrıları tekrarlanır → **daha yavaş + daha pahalı**

Redis kurmak için `docker-compose.yml`'de `redis` servisi ekleyin.

### "Kağıt portföy ile gerçek işlem farkı nedir?"

- **Kağıt portföy** (`core/paper_portfolio.py`): Gerçek para kullanmaz, sadece simülasyon. `UNIT_NOTIONAL` (varsayılan $1000) üzerinden sanal pozisyon açar.
- **Gerçek işlem**: `ALPACA_API_KEY` tanımlıysa `broker/` katmanı üzerinden Alpaca'ya emir gönderir. Dashboard'da "Trade" butonunu kullanın.

### "Score ne anlama geliyor?"

`finpilot_score` 0–4 arası bir bileşik teknik skor:
- 0–1: Zayıf, giriş koşulları sağlanmıyor
- 1–2: Orta, daha beklenmeli
- 2–3: İyi, değerlendirilebilir
- 3–4: Güçlü, giriş koşulları sağlanıyor

`entry_ok = true` için genellikle `score ≥ 2.0` ve ek koşullar (hacim, trend, stop-loss mesafesi) gerekir.

### "Eski scanner kodu ile yeni arasındaki fark?"

Yeni tarayıcı (`scanner/evaluate.py` + `scanner/risk_metrics.py` + `scanner/position_sizer.py`) şunları ekler:
- **Risk metrikleri**: Sharpe, Sortino, Calmar, MaxDD, yıllık getiri
- **Dinamik pozisyon**: Kelly criterion + piyasa rejimine göre ölçekleme
- **Beklenen değer (EV)**: İşlem başına beklenen kâr/zarar

### "agent/registry/audit endpoint'i ne işe yarıyor?"

Kod ile registry arasındaki farkları gösterir. Yeni bir agent sınıfı eklendiğinde ama registry'ye kaydedilmediğinde `in_code_not_registry` listesinde görünür. Arşivlenen ama registry'den silinmeyen sınıflar `in_registry_not_code`'da çıkar.

```
GET /api/v1/agent/registry/audit
→ "ok": true  ← her şey senkronize
→ "ok": false ← drift var, bakım gerekiyor
```

### "Hangi log dosyaları nerede?"

```
data/daily_reports/      ← Günlük rapor Markdown'ları
logs/                    ← Uygulama logları
data/signal_archive/     ← Eski sinyal verileri
data/finpilot.db         ← Tüm kayıtlar (SQLite)
```

### "Yeni semboller nasıl eklenir?"

1. Scanner sayfasında üst alana sembol yazıp "Tara" basın (tek seferlik)
2. `user_settings.json` içinde `watchlist` listesine ekleyin (kalıcı)
3. Scheduler otomatik olarak saatlik döngüde çalıştırır

### "API dokümantasyonu nerede?"

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
