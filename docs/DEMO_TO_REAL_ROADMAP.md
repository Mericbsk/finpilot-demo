# 🗺️ Demo → Real: AI Lab Dönüşüm Yol Haritası

> **Amaç:** Next.js AI Lab dashboardındaki sahte (mock) verileri, mevcut Python backend'deki gerçek yeteneklerle değiştirmek.

---

## 📋 Mevcut Durum Özeti

### Frontend (Next.js) — TAMAMEN MOCK
| Tab | Ne Yapıyor Şimdi | Gerçek mi? |
|-----|-------------------|------------|
| **AI Research** | `genReport()` — hash'ten sahte rapor üretiyor | ❌ Sahte |
| **Hybrid Engine** | `genStock()` → score sırala → top 10, eşik tabanlı sinyal | ❌ Sahte |
| **DRL Models** | 3 hardcoded model (PPO-v3, SAC-v2, TD3-v2), sahte metrik | ❌ Sahte |
| **Ensemble Router** | `(hash + offset) % 7` oylama | ❌ Sahte |
| **Optuna** | `genOptunaTrials()` — 15 sahte trial | ❌ Sahte |

### Backend (Python) — GERÇEK ve ÇALIŞIR
| Bileşen | Dosya | Durum |
|---------|-------|-------|
| Scanner (teknik analiz) | `scanner.py` | ✅ Çalışır — EMA, RSI, MACD, Bollinger, ATR, vol surge |
| DRL Inference | `drl/inference.py` | ✅ 20+ eğitilmiş PPO model |
| Ensemble Router | `drl/ensemble_router.py` | ✅ Çok ajanlı oylama + HMM rejim |
| Model Registry | `drl/model_registry.py` + `models/registry.json` | ✅ 20+ model meta verisi |
| Optuna Sonuçları | `data/optuna_*_results.json` | ✅ Gerçek trial'lar |
| Rejim Tespiti | `scripts/regime_detection.py` | ✅ HMM tabanlı |
| Backtest | `core/backtest.py` | ✅ Sharpe, Sortino, drawdown |
| Inference Cache | `data/inference.json` | ✅ Gerçek sinyal verisi |

### ❌ EKSİK: API Katmanı
Python backend ile Next.js frontend arasında **HTTP API yok**. Bu en kritik boşluk.

---

## 🏗️ Faz Planı

```
Faz 0  ──→  Faz 1  ──→  Faz 2  ──→  Faz 3  ──→  Faz 4  ──→  Faz 5
 API       Models     Hybrid      Ensemble     Optuna     Research
Katmanı    Tab        Engine      Router       Tab        Tab (LLM)
```

---

## Faz 0: FastAPI Backend API Katmanı

**Hedef:** Python backend'i HTTP API olarak sunmak. Next.js'in çağırabileceği endpoint'ler.

### Yapılacaklar

1. **FastAPI uygulaması oluştur** → `/workspaces/Borsa/api/main.py`
   ```python
   from fastapi import FastAPI
   from fastapi.middleware.cors import CORSMiddleware

   app = FastAPI(title="FinPilot API", version="1.0")
   app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], ...)
   ```

2. **Endpoint'ler:**
   ```
   GET  /api/v1/models              → Model registry listesi
   GET  /api/v1/models/{model_id}   → Tek model detay
   POST /api/v1/scan                → Scanner çalıştır (symbols[])
   POST /api/v1/predict             → DRL inference (symbols[], model_id?)
   POST /api/v1/ensemble            → Ensemble tahmin (symbols[])
   GET  /api/v1/optuna/results      → Optuna trial sonuçları
   GET  /api/v1/regime/{symbol}     → Rejim tespiti
   GET  /api/v1/inference-cache     → data/inference.json içeriği
   GET  /api/v1/health              → Sağlık kontrolü
   ```

3. **Backend fonksiyon eşlemeleri:**
   ```
   /api/v1/models     → ModelRegistry.list_models()
   /api/v1/scan       → evaluate_symbols_parallel(symbols)
   /api/v1/predict    → DRLInference.batch_predict(symbols)
   /api/v1/ensemble   → EnsembleRouter.batch_predict(symbols)
   /api/v1/optuna     → JSON dosyaları oku
   ```

4. **Docker-compose güncelle:** FastAPI servisi ekle (port 8000)

5. **Next.js proxy:** `next.config.ts`'e rewrites ekle:
   ```ts
   async rewrites() {
     return [{ source: "/py-api/:path*", destination: "http://localhost:8000/api/v1/:path*" }];
   }
   ```

### Dosya Yapısı
```
api/
├── main.py              # FastAPI app
├── routers/
│   ├── models.py        # GET /models, GET /models/{id}
│   ├── scan.py          # POST /scan
│   ├── predict.py       # POST /predict
│   ├── ensemble.py      # POST /ensemble
│   └── optuna.py        # GET /optuna/results
├── schemas.py           # Pydantic response modelleri
└── requirements.txt     # fastapi, uvicorn
```

### Doğrulama
- `curl http://localhost:8000/api/v1/health` → 200
- `curl http://localhost:8000/api/v1/models` → 20+ model JSON
- `curl -X POST http://localhost:8000/api/v1/predict -d '{"symbols":["AAPL"]}' ` → PredictionResult

---

## Faz 1: DRL Models Tab — Gerçek Model Registry

**Hedef:** Hardcoded 3 model → gerçek 20+ model registry.json verileriyle değiştir.

### Frontend Değişiklikler (`ai-lab/page.tsx`)

1. **Sil:** Hardcoded `drlModels` array (satır 23-44)
2. **Ekle:** `useEffect` ile `/py-api/models` fetch
3. **Map:** Backend `ModelMetadata` → frontend card formatı:
   ```typescript
   // Backend'den gelen:
   {
     model_id: "ppo_trend_20260225_181020",
     name: "ppo_trend",
     algorithm: "PPO",
     created_at: "2026-02-25T18:10:20",
     metrics: { sharpe_ratio: 0.0279, total_return: 0.7925, n_trades: 170 },
     tags: ["trend", "momentum"],
     is_active: true
   }
   // Frontend'e dönüştür:
   {
     id: model_id,
     name: `${algorithm} ${name}`,
     regime: tags[0] → emoji map,
     status: is_active ? "active" : "inactive",
     algo: algorithm,
     trainedOn: created_at formatlı,
     metrics: { sharpe: metrics.sharpe_ratio, ... },
     tags: tags,
     color: algorithm → renk map
   }
   ```
4. **Gerçek equity curve:** Backend'den eğitim sırasında kaydedilen equity verisi varsa kullan, yoksa sparkline fallback

### Backend Endpoint
```python
# api/routers/models.py
@router.get("/models")
def list_models():
    registry = ModelRegistry()
    models = registry.list_models()
    return [asdict(m) for m in models]
```

### Doğrulama
- DRL Models tab'ında 20+ model kartı görünmeli
- Metrikler `registry.json`'daki gerçek değerlerle eşleşmeli

---

## Faz 2: Hybrid Engine — Gerçek Scanner + DRL Consensus

**Hedef:** `genStock()` tabanlı sahte sinyaller → gerçek scanner + DRL inference sonuçları.

### Akış
```
Kullanıcı "Run" tıklar
  → POST /py-api/scan   {symbols: top300}  → Scanner skorları
  → POST /py-api/predict {symbols: top300}  → DRL sinyalleri
  → Frontend birleştirir → Consensus hesaplar → Top 10 gösterir
```

### Frontend Değişiklikler

1. **Sil:** `topHybrid` hesaplama bloğu (satır ~205-226)
2. **Ekle:** Yeni state + fetch:
   ```typescript
   const [hybridData, setHybridData] = useState([]);
   const [loading, setLoading] = useState(false);

   async function runHybridScan() {
     setLoading(true);
     const symbols = allSymbols.slice(0, 300);
     const [scanRes, drlRes] = await Promise.all([
       fetch("/py-api/scan", { method: "POST", body: JSON.stringify({ symbols }) }).then(r => r.json()),
       fetch("/py-api/predict", { method: "POST", body: JSON.stringify({ symbols }) }).then(r => r.json()),
     ]);
     // Birleştir
     const merged = symbols.map(s => ({
       ticker: s,
       scanner: scanRes[s]?.signal || "N/A",
       scannerScore: scanRes[s]?.score || 0,
       drl: drlRes[s]?.action || "N/A",
       drlConfidence: drlRes[s]?.confidence || 0,
       consensus: deriveConsensus(scanRes[s], drlRes[s]),
       confidence: combineConfidence(scanRes[s], drlRes[s]),
       posSize: calculatePosition(scanRes[s], drlRes[s]),
     }));
     setHybridData(merged.sort((a, b) => b.confidence - a.confidence).slice(0, 10));
     setLoading(false);
   }
   ```

### Backend Endpoint
```python
# api/routers/scan.py
@router.post("/scan")
def run_scan(request: ScanRequest):
    results = evaluate_symbols_parallel(
        symbols=request.symbols,
        kelly_fraction=0.5,
    )
    return {r["symbol"]: r for r in results}
```

### İlk Yükleme Optimizasyonu
- İlk render'da `data/inference.json` cache'inden göster (anlık)
- Arka planda taze scan başlat

### Doğrulama
- Hybrid Engine tab'ında gerçek BUY/SELL/HOLD sinyalleri
- Sinyaller her çalıştırmada piyasa verisine göre değişmeli
- Console'da gerçek confidence skorları (0.0-1.0 arası)

---

## Faz 3: Ensemble Router — Gerçek Çok Ajanlı Oylama

**Hedef:** `(hash + offset) % 7` → gerçek EnsembleRouter ile 3+ ajanlı rejim-bazlı oylama.

### Frontend Değişiklikler

1. **Sil:** `topEnsemble` hesaplama bloğu (satır ~229-250)
2. **Ekle:** Ensemble fetch:
   ```typescript
   async function runEnsemble() {
     const symbols = allSymbols.slice(0, 300);
     const res = await fetch("/py-api/ensemble", {
       method: "POST",
       body: JSON.stringify({ symbols, risk_appetite: 5 }),
     }).then(r => r.json());
     // Backend EnsembleResult → frontend format
     setEnsembleData(res.map(r => ({
       ticker: r.symbol,
       trend: findVote(r.votes, "trend"),
       volatile: findVote(r.votes, "volatile"),
       range: findVote(r.votes, "range"),
       consensus: actionToSignal(r.final_action),
       agreement: `${r.agreement_score.toFixed(0)}/3`,
       confidence: Math.round(r.final_confidence * 100),
       regime: r.dominant_regime,
     })));
   }
   ```

### Backend Endpoint
```python
# api/routers/ensemble.py
@router.post("/ensemble")
def ensemble_predict(request: EnsembleRequest):
    router = EnsembleRouter()
    results = router.batch_predict(
        symbols=request.symbols,
        risk_appetite=request.risk_appetite,
    )
    return [asdict(r) for r in results[:request.top_n]]
```

### Tablo Zenginleştirme
- **Yeni sütun:** "Dominant Regime" (Trend/Range/Volatile)
- **Yeni sütun:** "Regime Weights" (küçük bar chart)
- **Tooltip:** Her ajan oyunun detayı

### Doğrulama
- 3+ ajanın bağımsız oyları görünmeli
- Agreement skoru gerçek oy dağılımını yansıtmalı
- Rejim tespiti (Trend/Range/Volatile) doğru etiketlenmeli

---

## Faz 4: Optuna Tab — Gerçek Hiperparametre Sonuçları

**Hedef:** `genOptunaTrials()` sahte 15 trial → gerçek Optuna arama sonuçları.

### Frontend Değişiklikler

1. **Sil:** `genOptunaTrials()` fonksiyonu
2. **Ekle:** Backend'den gerçek trial verisi çek:
   ```typescript
   const [optunaData, setOptunaData] = useState({ trials: [], bestParams: {} });

   useEffect(() => {
     fetch("/py-api/optuna/results")
       .then(r => r.json())
       .then(data => setOptunaData(data));
   }, []);
   ```

### Backend Endpoint
```python
# api/routers/optuna.py
@router.get("/optuna/results")
def get_optuna_results(agent: str = "conservative"):
    # Gerçek sonuç dosyalarını oku
    files = {
        "conservative": "data/optuna_conservative_results.json",
        "momentum": "data/optuna_momentum_results.json",
        "range": "data/optuna_range_results.json",
        "swing": "data/optuna_swing_results.json",
    }
    with open(files.get(agent, files["conservative"])) as f:
        return json.load(f)
```

### UI İyileştirmeler
- Agent seçici dropdown (conservative, momentum, range, swing)
- Her agent için gerçek trial sayısı ve best Sharpe
- Paralel koordinat grafiği (lr, gamma, batch_size vs Sharpe)

### Doğrulama
- 30 gerçek trial görünmeli (15 sahte değil)
- Best trial parametreleri `data/optuna_*_results.json` ile eşleşmeli
- Agent değiştirince farklı sonuçlar yüklenmeli

---

## Faz 5: AI Research Tab — Gerçek LLM Analiz

**Hedef:** `genReport()` hash tabanlı sahte rapor → gerçek haber toplama + LLM analizi.

### Seçenekler (maliyet sırasına göre)

| Yaklaşım | Maliyet | Kalite | Uygulama |
|-----------|---------|--------|----------|
| **A) RSS + Local LLM** | $0 | ⭐⭐ | Ollama + Llama3 |
| **B) News API + Groq** | $0-20/ay | ⭐⭐⭐ | Groq free tier |
| **C) Full Pipeline** | $50+/ay | ⭐⭐⭐⭐⭐ | Groq→Claude→Gemini failover |

### Önerilen: Yaklaşım B (Groq Free Tier)

```
Kullanıcı ticker seçer
  → Backend: yfinance'ten son haberler çek
  → Backend: Groq API ile analiz yap (Llama3-70b, ücretsiz)
  → Frontend: Yapılandırılmış rapor göster
```

### Backend Endpoint
```python
# api/routers/research.py
@router.post("/research")
async def research_ticker(request: ResearchRequest):
    # 1. Veri topla
    info = yf.Ticker(request.symbol).info
    news = yf.Ticker(request.symbol).news

    # 2. LLM analiz
    prompt = f"Analyze {request.symbol}: {json.dumps(info)}\nNews: {json.dumps(news[:5])}"
    analysis = await call_groq(prompt)  # veya Claude/Gemini failover

    # 3. Yapılandırılmış çıktı
    return {
        "symbol": request.symbol,
        "sections": parse_analysis(analysis),
        "timestamp": datetime.utcnow().isoformat(),
    }
```

### Doğrulama
- Rapor güncel haber ve veri içermeli
- Farklı tickerlar tamamen farklı raporlar üretmeli
- "Powered by Groq" etiketi

---

## 📊 Öncelik Matrisi

```
           Kolay ───────────────────── Zor
  Yüksek  │ Faz 4 (Optuna)  │ Faz 2 (Hybrid)   │
  Etki    │ Faz 1 (Models)  │ Faz 3 (Ensemble)  │
          │─────────────────│───────────────────│
  Düşük   │                 │ Faz 5 (Research)  │
  Etki    │                 │                   │
          └─────────────────┴───────────────────┘

  Bloklar: Faz 0 (API) hepsinden önce yapılmalı
```

### Önerilen Sıralama
```
1. Faz 0: API Katmanı         ← HER ŞEYİ BLOKLAR
2. Faz 1: DRL Models           ← En kolay, hızlı kazanım (sadece JSON oku)
3. Faz 4: Optuna               ← Kolay, sadece dosya oku
4. Faz 2: Hybrid Engine        ← Orta zorluk, en büyük etki
5. Faz 3: Ensemble Router      ← Orta-zor, DRL modeller gerekli
6. Faz 5: AI Research          ← En zor, harici API gerekli
```

---

## 🔧 Teknik Gereksinimler

### Python Bağımlılıkları (zaten mevcut)
```
stable-baselines3    # DRL modelleri
yfinance             # Piyasa verisi
hmmlearn             # Rejim tespiti
optuna               # Hiperparametre
pandas, numpy        # Veri işleme
```

### Yeni Bağımlılıklar
```
fastapi              # API framework
uvicorn              # ASGI sunucu
pydantic             # Request/response şemaları
groq                 # LLM API (Faz 5 için)
```

### Altyapı
- FastAPI: Port 8000 (Docker container içinde)
- Next.js: Port 3000 (mevcut, rewrites ile proxy)
- Her iki servis docker-compose'da tanımlı

---

## ⚠️ Riskler ve Çözümler

| Risk | Etki | Çözüm |
|------|------|-------|
| DRL modelleri GPU gerektirir | Yavaş inference | CPU'da çalışır (test edilmiş), batch limit koy |
| Scanner 300 sembol yavaş | Zaman aşımı | Arka plan iş, WebSocket ile sonuç push |
| Groq free tier limit | Araştırma tab kısıtlı | Rate limit + cache (1 saat TTL) |
| Model kalitesi düşük (Sharpe ~0.07) | Yanlış sinyaller | DİKKAT etiketi + "deneysel" badge |
| yfinance rate limit | Veri eksik | Cache katmanı + Alpaca fallback |

---

## 📈 Başarı Kriterleri

### Faz 0
- [ ] `GET /api/v1/health` → 200 OK
- [ ] Swagger docs: `http://localhost:8000/docs`

### Faz 1
- [ ] DRL Models tab'ında 20+ gerçek model görünür
- [ ] Metrikler `registry.json` ile tutarlı

### Faz 2
- [ ] Hybrid Engine gerçek BUY/SELL/HOLD sinyaller üretir
- [ ] Sinyaller piyasa koşullarına göre değişir

### Faz 3
- [ ] 3+ agent bağımsız oy verir
- [ ] Rejim tespiti çalışır (Trend/Range/Volatile)

### Faz 4
- [ ] 30 gerçek Optuna trial görünür
- [ ] 4 farklı agent sonuçları arasında geçiş yapılabilir

### Faz 5
- [ ] Gerçek haberler ve finansal veri kullanılır
- [ ] LLM analiz tutarlı ve güncel

---

## 🚀 Sonuç

Bu yol haritası, mevcut Python backend'in gerçek yeteneklerini (20+ eğitilmiş DRL model, üretim kalitesinde scanner, çok ajanlı ensemble router) Next.js frontend'e bağlar. **Kritik nokta Faz 0'dır** — FastAPI API katmanı tüm diğer fazları mümkün kılar.

Backend zaten çalışıyor. İhtiyaç olan tek şey bir **köprü** (API katmanı) ve frontend'deki **mock verilerin gerçek API çağrılarıyla değiştirilmesi**.
