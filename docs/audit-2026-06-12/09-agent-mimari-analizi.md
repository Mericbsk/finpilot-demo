# FinPilot Agent Mimarisi — Kod Düzeyinde Analiz ve Yeniden Tasarım

**Tarih:** 2026-06-12 · **Yöntem:** registry.py, ceo.py, base.py, feedback.py, core/pipeline.py, core/auto_pipeline.py, core/scheduler.py, api/routers/agent.py ve tüm agent dosyalarının okunması + çağrı zinciri (import) taraması. Tahmin yok; her iddia kod referanslı.

---

## 1) AGENT ENVANTERİ

Sistemde "agent" kelimesi **üç farklı şeyi** ifade ediyor — sorunların yarısının kökü bu:

### A. Gerçek işçi agent'lar (BaseAgent kontratı: AgentContext → run() → AgentResult)

| Agent | Dosya (LOC) | Ne yapıyor | Kim çağırıyor |
|---|---|---|---|
| Scanner | scanner_agent.py | Tarama pipeline'ını agent olarak sarar; scan_results üretir | pipeline, auto_pipeline, ceo, agent router |
| Research | research_agent.py (217) | Haber + bağlam toplar (headroom ile zenginleştirilmiş) | pipeline, auto_pipeline, ceo, scheduler, router |
| Analysis | analysis_agent.py (197) | Sembol başına teknik+bağlamsal analiz | pipeline, auto_pipeline, ceo |
| Risk | risk_agent.py | Pozisyon riski / Kelly değerlendirmesi | pipeline, auto_pipeline, ceo |
| Alert | alert_agent.py | Onaylı sinyali Telegram'a gönderir | pipeline, auto_pipeline, ceo |
| Backtest | backtest_agent.py | Rejime göre strateji backtest'i; **feedback kuyruğunu okuyan TEK agent** | auto_pipeline, scheduler, router |
| Bull Researcher | bull_researcher.py | Sembol için boğa tezi (INT-5) | **YALNIZ ceo.py** |
| Bear Researcher | bear_researcher.py | Sembol için ayı tezi (INT-5) | **YALNIZ ceo.py** |
| Social Intelligence | social_intelligence_agent.py (268) | Polymarket/HN/DDG sosyal sinyal (Haziran'da eklendi) | **YALNIZ ceo.py** |

### B. Tier-2 bağımsız analitik agent'lar (scheduler/router'dan tekil çağrı)

| Agent | Ne yapıyor | Tetik |
|---|---|---|
| Market Intelligence (244) | Rejim tespiti (trend/chop/volatile) + sentiment; döngünün 1. adımı | scheduler her saat + router |
| Data Quality (151) | Sembol/veri şema doğrulama — pipeline öncesi kapı | scheduler (1b adımı) |
| Strategy Optimizer (236) | Parametre optimizasyonu, walk-forward | scheduler (her N döngü) + router |
| Performance Monitor (178) | KPI/decay izleme; kötü KPI'da feedback + Telegram drawdown alarmı | scheduler (5. adım) + router |
| Alpha Tracker (396) | Sembol bazlı rolling win-rate/PF; skor eşiği önerisi; **get_score_floor scan router'da gerçekten kullanılıyor** | router + scan akışı |
| Combo Testing (168) | Strateji kombinasyon matrisi, overfit kontrolü | yalnız router (manuel) |
| Report (142) | Günlük Markdown raporu | scheduler + router |

### C. Advisory persona'lar (LLM rol-sarmalayıcı, salt metin — 15 adet)
cto, cpo, cmo, senior_dev, frontend_dev, ai_ml_dev, devops, growth_marketer, content_strategist, biz_dev, competitive_intel, qa_test, code_review, pm, customer_success (`advisory.py`, 375 LOC). Trading yapmazlar; **FinPilot'un kendisi hakkında** tavsiye metni üretirler. Scheduler ~10 döngüde bir "advisory review" yazdırır.

### D. Orkestratörler (4 adet!)

| Orkestratör | Durum |
|---|---|
| `agents/ceo.py` — LangGraph StateGraph (285 LOC) | **Legacy.** S17-03 commit'iyle üretimde `core/pipeline.run_cycle` ile değiştirildi; ama silinmedi, `agents/__init__` hâlâ export ediyor, health-check import ediyor |
| `core/pipeline.py` — run_cycle | **Kanonik.** scheduler + API scan/analyze/risk/full buradan |
| `core/auto_pipeline.py` — run_auto_pipeline | API task="auto"; 7 faz (scan→research→analysis→risk→backtest→synthesize→alert), composite_confidence üretir |
| `academy/orchestrator.py` | Yazılmış, hiçbir scheduler'a bağlı değil (bkz. 06-academy raporu) |

**Ayrıca:** `agents/registry.py` 23 agent'lık 6 katmanlı bir "organizasyon şeması" tanımlıyor — ama bu liste implementasyonla örtüşmüyor (aşağıda §3.2).

---

## 2) AMAÇ VE GÖREV ANALİZİ — gerçek otomatik döngü bugün ne yapıyor?

Scheduler'ın saatlik `run_cycle_once` akışı (kod sırasıyla):

```
1.  MarketIntelligence  → rejim etiketi (30g lookback, LLM'li)
1b. DataQuality         → sembol doğrulama kapısı
2.  run_cycle("scan")   → scanner pipeline (CEO graph DEĞİL — pipeline.py)
2b. Research            → rejim bağlamı + scan sonuçlarıyla zenginleştirme
3.  Backtest            → rejime göre strateji seçimi; sonuçlar KPI tracker'a
4.  StrategyOptimizer   → her N döngüde parametre önerisi
5.  PerformanceMonitor  → KPI değerlendirme
    ├─ win_rate < 50 → emit_feedback(→backtest, "switch strategy")
    ├─ drawdown     → emit_feedback + Telegram kritik alarm
6.  ~10 döngüde bir     → advisory persona "haftalık review" metni
Ayrı cron'lar: eval, reconcile (outcome), calibration, weekly retrain,
resolve_open_signals, weekly report, research pipeline, drift, CEO raporu,
auto_approve (p_win ≥ 0.65 → sinyal otomatik onay, 60dk)
```

**Bu akış gerçekten iyi tasarlanmış bir kapalı döngünün yarısıdır:** algıla (1-2) → düşün (2b-3) → öğren (5, reconcile, calibration) → karar (auto_approve). Neden-sonuç zinciri kurulmuş: rejim → strateji seçimi → backtest → KPI → feedback → (teoride) strateji değişimi.

---

## 3) EKSİK / YANLIŞ / GEREKSİZ NOKTALAR

### 3.1 Kopuk: En yeni yatırım, ölü koldan sarkıyor (P0 bulgu)
`social_intelligence_agent` (Haziran), `bull_researcher`, `bear_researcher` **yalnızca `agents/ceo.py`'den çağrılıyor.** Ama üretim akışı S17-03'te ceo graph'tan `pipeline.run_cycle`'a taşındı ve pipeline bu üç agent'ı İÇERMİYOR; auto_pipeline da içermiyor.
**Neden-sonuç:** Orkestratör değiştirilirken node listesi taşınmadı → sosyal istihbarat ve bull/bear tez üretimi hiçbir otomatik döngüde çalışmıyor → headroom+sosyal agent yatırımı (commit 209c3f2) fiilen kullanım dışı; "scan all throttling" optimizasyonları bu agent'ların yokluğunda ölçüldü.

### 3.2 Yanlış: Registry bir kurgu — kod gerçeğiyle örtüşmüyor
`registry.py` 23 agent / 6 katman ilan ediyor; CEO'yu "LangGraph workflow yönetimi, aktif, üretimde" diye tanımlıyor (artık değil). 15'i persona (gerçek işçi değil), "Quant Research/Combination Testing" gibi adlar dosya adlarıyla eşleşmiyor, `key` alanları kısmen API task'larına denk geliyor kısmen gelmiyor.
**Neden-sonuç:** Registry, dashboard'a "23 agent'lık şirket" görüntüsü vermek için yazılmış vitrin → yeni geliştirici (veya yatırımcı due diligence'ı) gerçek mimariyi koddan tersine mühendislikle çıkarmak zorunda → tek güvenilir harita yok.

### 3.3 Gereksiz: Üç orkestratör aynı zinciri üç kez tanımlıyor
scan→analyze→risk→alert zinciri ceo.py'de (LangGraph), pipeline.py'de (sıralı) ve auto_pipeline.py'de (7 fazlı, paralel) ayrı ayrı yazılmış. Her biri farklı yöne drift etmiş: synthesize/composite_confidence yalnız auto_pipeline'da, social/bull/bear yalnız ceo'da, scheduler entegrasyonu yalnız pipeline'da.
**Neden-sonuç:** Yeni bir aşama eklemek 3 yerde değişiklik ister → pratikte tek yere ekleniyor → drift büyüyor (3.1 tam olarak böyle oluştu).

### 3.4 Yarım: Feedback sinir sistemi tek nöronlu
`feedback.py` Redis kuyruk altyapısı düzgün (TTL, cap, in-memory fallback). Ama: **üretici 2** (scheduler, performance_monitor), **tüketici 1** (backtest_agent, 5 mesaj). Alpha Tracker'ın eşik önerileri scan'e `get_score_floor` ile gidiyor (iyi — tek gerçek kapalı mikro-döngü), fakat optimizer önerileri, DQ bulguları, drawdown alarmları hiçbir agent'ın davranışını değiştirmiyor.
**Neden-sonuç:** "Agent'lar birbirine feedback verir" mimari vaadi tek kenarlı graf → sistem öğreniyor ama öğrendiğini eyleme çevirme yolları bağlanmamış. In-memory fallback'te mesajlar süreç ölünce kayboluyor → Redis kapalı dev ortamında feedback fiilen yok.

### 3.5 Tiyatro: Advisory persona'ların çıktısını kimse okumuyor
Scheduler 10 döngüde bir persona review'u "scheduler" kullanıcısının oturumuna yazıyor. Bu metinleri tüketen bir yüzey/rapor/karar mekanizması yok. 15 persona LLM maliyeti üretiyor, ölçülen değer sıfır.
**Neden-sonuç:** "Şirket simülasyonu" konsepti eğlenceli ama ürün döngüsüne bağlanmadı → token gideri + kod yüzeyi + registry şişkinliği.

### 3.6 Sessizlik: Her şey best-effort, hiçbir şey görünür değil
pipeline/auto_pipeline/scheduler'da her faz try/except ile yutuluyor (`errors` listesine ekleniyor) — doğru dayanıklılık deseni, ama errors listesini izleyen panel/alarm yok (önceki rapor Sorun #5 ile aynı kök). Watchdog timeout var; job-run geçmişi yok.
**Neden-sonuç:** Sosyal agent'ın aylardır çalışmaması gibi kopukluklar ancak elle kod okuyunca fark ediliyor.

### 3.7 Eksik halka: Karar → eylem köprüsü
auto_approve p_win≥0.65 sinyali onaylıyor; ama onaylanan sinyalin paper-trade'e dönüşmesi ayrı script'lerin (daily_paper_trading.py) insiyatifinde. "Onaylandı ama işlenmedi" durumu izlenmiyor.

---

## 4) İDEAL OTOMATİK İŞ AKIŞI — Sinyal Yaşam Döngüsü

Doğru soyutlama "agent şirketi" değil, **tek varlığın (sinyal) durum makinesi**dir. Her agent, bir durum geçişinin işleyicisidir:

```
                    ┌─────────────── SAATLIK DÖNGÜ ───────────────┐
[SENSE]   regime(MarketIntel) + universe(DataQuality kapısı)
   │
   ▼
SCANNED   ← ScannerAgent (aday üretir)
   │
[ENRICH]  ← Research + SocialIntel + Bull/Bear (paralel, top-N için)
   ▼
SCORED    ← finpilot_score + calibration → p_win
   │
[DECIDE]  ← RiskAgent (boyut/Kelly) + DD-gate + auto_approve politikası (p_win eşiği)
   ▼
APPROVED ─── reddedilen → ARCHIVED (gerekçeli)
   │
[ACT]     ← PaperTrader (otomatik emir) + AlertAgent (Telegram/UI)
   ▼
OPEN
   │  (T+3/5/10 cron)
[LEARN]   ← OutcomeReconciler → RESOLVED → AlphaTracker (eşik) →
            PerformanceMonitor (decay) → StrategyOptimizer (parametre) →
            Calibration retrain (haftalık)
   ▼
RESOLVED → [REPORT] ReportAgent günlük + CEO haftalık + (V6) bülten
```

**Kurallar:** (1) Her durum geçişi `signal_events` tablosuna yazılır — feedback kuyruğu da, job-görünürlüğü de, bülten hammaddesi de aynı tablodan çıkar. (2) Bir agent yalnız kendi geçişinden sorumludur; başka agent'ı çağırmaz — orkestratör (tek!) geçişleri sürür. (3) Hata = geçiş başarısız + event kaydı; sessiz yutma yok.

---

## 5) ÖNERİLEN YENİ MİMARİ

### 5.1 Katmanlar (23 sahte katman yerine 6 gerçek rol)

| Rol | Agent'lar | Giriş | Çıkış | Tetikleyici | Bağımlılık |
|---|---|---|---|---|---|
| **SENSE** | MarketIntel, DataQuality, SocialIntel | OHLCV, haber, sosyal | regime, geçerli evren, social_score | Saatlik cron | Veri sağlayıcılar |
| **THINK** | Scanner, Research, Bull/Bear, Analysis | SENSE çıktıları | adaylar + tez + skor girdileri | SENSE tamamlanınca | SENSE |
| **DECIDE** | Risk, Calibration(p_win), auto_approve politikası | skorlanmış adaylar | APPROVED/REJECTED + boyut | THINK tamamlanınca | THINK + KPI durumu |
| **ACT** | PaperTrader, Alert | onaylı sinyal | açık pozisyon + bildirim | DECIDE geçişi (event) | DECIDE |
| **LEARN** | Reconciler, AlphaTracker, PerfMonitor, Optimizer, Backtest | RESOLVED sonuçlar | eşik/parametre/strateji güncellemesi | T+k cron + haftalık | ACT sonuçları |
| **REPORT** | ReportAgent, CEO-haftalık, (V6 bülten) | signal_events | insan/abone çıktısı | Günlük/haftalık cron | Hepsi (salt-okur) |

Advisory persona'lar bu mimaride **agent değildir** — `personas/` altına taşınır, yalnız kullanıcı sorduğunda (router task="advisory") çalışır; cron'dan çıkarılır.

### 5.2 Tek orkestratör
`core/pipeline.py` kanonik kalır ve genişler: auto_pipeline'ın research/backtest/synthesize fazları + ceo'nun social/bull/bear node'ları pipeline'a opsiyonel aşama olarak taşınır (`stages=` parametresi). `agents/ceo.py` (LangGraph) ve `core/auto_pipeline.py` arşivlenir. LangGraph bağımlılığı tamamen düşer (zaten S17-03 bu yöndeydi — yarım kalmış).

### 5.3 Tek event omurgası
`signal_events(signal_id, from_state, to_state, agent, payload, ts, success, error)` tablosu: feedback.py'nin Redis kuyruğu yerine geçer (Redis cache olarak kalır); job-run görünürlüğü dashboard "Sistem Sağlığı" kartından okunur; Academy'nin simülasyon ajanı (06 raporu A8) gerçek vakaları buradan çeker.

### 5.4 Registry = kodun aynası
registry.py elle yazılmış 23 kayıt yerine, gerçek agent sınıflarından (BaseAgent alt sınıfları + rol/etap dekoratörü) otomatik üretilir. Dashboard'daki agent sayfası yalan söyleyemez hale gelir.

---

## 6) ÖNCELİKLİ DÜZELTME LİSTESİ

| # | Aksiyon | Neden | Efor | Etki |
|---|---|---|---|---|
| 1 | Social + Bull/Bear'ı `pipeline.run_cycle`'a opsiyonel aşama olarak taşı | Haziran yatırımı şu an hiçbir otomatik akışta çalışmıyor (§3.1) | 0.5-1 gün | Yüksek |
| 2 | `signal_events` tablosu + her faz geçişinin kaydı + dashboard kartı | Sessiz kopuklukların bir daha aylarca gizlenmemesi (§3.6) | 2-3 gün | Yüksek |
| 3 | auto_pipeline'ı pipeline'a birleştir; ceo.py'yi arşivle; `__init__`/health'ten çıkar | 3 orkestratör drift'i = kopuklukların üreme zemini (§3.3) | 1-2 gün | Yüksek |
| 4 | Advisory cron review'u kapat; persona'ları on-demand'e indir | Okunmayan LLM çıktısı = saf maliyet (§3.5) | 1 saat | Orta |
| 5 | Registry'yi koddan üret; persona'ları ayrı listele | Tek güvenilir mimari harita (§3.2) | 1 gün | Orta |
| 6 | Feedback tüketicilerini bağla: Optimizer önerisi → scanner config; DQ bulgusu → evren dışlama. Bağlanmayacaksa kuyruğu kaldır | Tek kenarlı feedback grafı (§3.4) | 2 gün | Orta |
| 7 | APPROVED→ACT köprüsü: auto_approve onayı doğrudan paper-trade emri üretsin; "onaylı ama işlenmemiş" alarmı | Karar-eylem kopukluğu (§3.7) | 1-2 gün | Yüksek |
| 8 | Redis-yokken feedback/in-memory davranışını testle sabitle | Dev ortamında sessiz veri kaybı (§3.4) | 0.5 gün | Düşük |

**Sıra mantığı:** 1→2→3 ilk hafta (kopukluğu kapat, görünürlük kur, dripti durdur); 4-6 ikinci hafta (sadeleştir); 7 üçüncü hafta (döngüyü uçtan uca kapat). Bu listeden sonra sistem, §4'teki yaşam döngüsünün tamamını insansız döndürür; insan yalnız haftalık raporu okur.
