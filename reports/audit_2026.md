# FinPilot — Tam Sistem Denetimi (Master Prompt Audit)

**Versiyon:** 1.0
**Tarih:** Sprints 1–15 sonrası snapshot
**Rol:** Chief Systems Audit & Evolution Architect
**Prensip:** Önce görünürlük → kalite → sadeleştirme → otomasyon → otonomi.

---

## 1) Yönetici Özeti

FinPilot mühendislik açısından zengin: 17 dashboard sayfası, 9 scheduler job'u, 18 agent, 3 DRL PPO modeli, 3 LLM provider, araştırma pipeline + LightGBM ranker + Optuna, closed-loop kalibrasyon + drift KS-testi, Alpaca paper broker, JWT auth.

**Kritik sorun:** Çekirdek değer (= günlük güvenilir sinyal) ile bileşen sayısı arasındaki oran kötü. Tek geliştirici için sistem 3–5× fazla karmaşık. "Self-improving" iddiası dağıtılmış kapılarla destekleniyor ama **kapalı döngünün ürettiği gerçek edge ölçüsü (champion'ın paper P&L'i, kalibrasyon iyileşmesi) hiçbir yerde görünmüyor.**

**En önemli sadeleştirme fırsatları:**
1. Dashboard 17 → 5 sayfa
2. LangGraph CEO + 18 agent → tek `pipeline.run_cycle()` + 4–5 saf modül
3. Multi-LLM → tek provider + cache
4. 6 requirements → 1 + extras
5. DRL stack → feature-flag arkasına (ölçülmüş edge gösterilene kadar)
6. Advisory + ai-lab + agent-hub + finsense + autonomy → tek "Lab" sayfasında

**Otonomi seviyesi:** Bugün **Seviye 2** (modüler otomasyon, görünürlük eksik). Sprint 14–15 ile Seviye 3 altyapısı kuruldu ama telemetrisi yok.

---

## 2) Tam Sistem Haritası

| Modül | Amaç | Bağımlılık | Kritiklik | Durum |
|---|---|---|---|---|
| `scanner/` | Sinyal üretimi (skor + indikatör + features) | yfinance | **ÇEKİRDEK** | ✅ |
| `core/kpi_tracker.py` | Sinyal kaydı, outcome update | Redis/SQLite | **ÇEKİRDEK** | ✅ |
| `core/outcome_reconciler.py` | T+1/T+5/T+20 eşleme | yfinance | **ÇEKİRDEK** | ✅ |
| `core/calibration.py` | Brier/ECE + isotonic refit + KS drift | scipy | **ÇEKİRDEK** | ✅ (drift yeni) |
| `core/scheduler.py` (~1200 LOC) | 9 APScheduler job | ALL | **ÇEKİRDEK** | ⚠ Şişkin |
| `core/quality_gate.py` | Sistem degraded state | calibration, eval | Yüksek | ✅ |
| `research/registry.py` | Champion/challenger 2-gate + strike | walkforward | Yüksek | ✅ |
| `research/walkforward.py` | 12-fold WF cross-val | scanner | Yüksek | ✅ |
| `research/sweep.py` | Optuna 200-trial sweep | walkforward | Orta | ⚠ Pahalı |
| `research/lgbm_ranker.py` | Layer-2 LGBM ranker | scanner | Orta | 🔴 **Yazıldı, bağlı değil** |
| `core/regime_weights.py` | Bull/bear/range × 10 ağırlık | yfinance SPY | Orta | 🔴 **Yazıldı, tüketici yok** |
| `scanner/features.py` | sector_rs + vol_regime | yfinance ETF | Orta | ✅ (cache'li) |
| `scanner/earnings_blackout.py` | Earnings filtresi | yfinance | Orta | ✅ |
| `api/main.py` + 14 router | REST API | core, agents | **ÇEKİRDEK** | ✅ |
| `web/` (Next.js, 17 sayfa) | Frontend | api | Yüksek | ⚠ Şişkin |
| `agents/ceo.py` (LangGraph) | Multi-agent orkestratör | 17 agent | Orta | ⚠ Karmaşıklık ≫ değer |
| `agents/{18 dosya}` | Görev wrapper'ları | scanner, llm | Düşük-Orta | ⚠ İnce wrapper'lar |
| `agents/advisory.py` | CTO/COO chat | llm | Düşük | 🔴 Vanity |
| `drl/` (28 dosya, PPO×3) | RL adaptive policy | gym, sb3 | Düşük | 🔴 Ölçülmüş edge yok |
| `llm/` (3 provider+router) | LLM çoklu sağlayıcı | API keys | Düşük | ⚠ Tek yeterli |
| `broker/alpaca_broker.py` | Paper trade execution | alpaca-py | Yüksek | ✅ |
| `core/paper_portfolio.py` | In-memory portföy | kpi_tracker | Yüksek | ✅ |
| `auth/` (10 dosya) | JWT + sessions + repos | SQLite/PG | Yüksek | ✅ |
| `monitoring/` | Prometheus, Grafana, alerts | Sentry | Orta | ⚠ Tetiklenmiş mi? |
| `archive/`, `views/` | Legacy | — | — | 🗑 Dead |
| 6 `requirements-*.txt` | Profile parçalanması | — | — | ⚠ Birleştir |

---

## 3) Çalışan / Çalışmayan / Gereksiz Analizi

| Modül | Durum | Kanıt | Etki | Karar |
|---|---|---|---|---|
| Scanner score + signals | Tam çalışıyor | API + scheduler her saat | Çekirdek | **Keep** |
| KPI tracker + reconciler | Tam çalışıyor | T+1/5/20 closed-loop | Çekirdek | **Keep** |
| Calibration + KS drift | Yeni çalışıyor | Sprint 14 | Yüksek | **Keep + telemetri** |
| Champion/challenger gate | Çalışıyor | 2-koşul + strike | Yüksek | **Keep** |
| Walk-forward | Çalışıyor | Pazar 02:00 UTC | Yüksek | **Keep** |
| Optuna sweep (200 trial) | Kısmen | "Daha iyi mi" raporu yok | Orta | **Simplify (50 trial)** |
| LGBM ranker | Kod var, bağlı değil | `rank_signals()` çağrılmıyor | Sıfır | **Wire OR Archive** |
| Regime weights | Kod var, tüketici yok | `get_active_weights()` consume edilmiyor | Sıfır | **Wire OR Archive** |
| Alpha features (sector_rs, vol_regime) | Bağlı, kullanan yok | evaluate.py dict'e ekliyor, ranker yok | Düşük | **Wire to scoring** |
| DRL ensemble | Kod var, edge yok | W_DRL=0 default | Şüpheli | **Freeze + flag** |
| Multi-agent CEO LangGraph | Çalışıyor, redundant | Her agent saf fonksiyon olabilir | Yük ≫ değer | **Simplify** |
| Advisory (CTO/COO) | Vanity | Karar etkisi sıfır | Sıfır | **Freeze** |
| ai-lab/agent-hub/autonomy/finsense/drl pages | UI var, kullanım yok | Test yok | Düşük | **Merge → Lab** |
| 3 LLM provider | Gereksiz | Failover gerçekten tetiklendi mi? | Düşük | **1 provider** |
| Telegram alerts | Çalışıyor | Drift + STOP | Yüksek | **Keep** |
| Streamlit `views/`, `archive/` | Dead | api/main.py import etmiyor | Sıfır | **Remove** |
| Auto-approve (30dk) | Çalışıyor, persist etmiyor | In-memory flag | Risk | **Persist veya kaldır** |

---

## 4) Çekirdek vs Destek Katmanları

| Katman | Bileşenler | Değere etkisi |
|---|---|---|
| **Çekirdek (para üreten)** | scanner score + signals + earnings_blackout | ÇOK YÜKSEK |
| **Doğrulama** | kpi_tracker + outcome_reconciler + calibration | ÇOK YÜKSEK |
| **Risk/kalite kapısı** | quality_gate + registry champion gate + drift KS | YÜKSEK |
| **Operasyonel görünürlük** | Telegram + weekly report + Prometheus | ORTA |
| **UX (minimal)** | scanner, portfolio, history, calibration pages | ORTA |
| **Destekleyici** | auth, broker (paper), regime detection | ORTA |
| **Premature complexity** | LangGraph CEO, 18 agent, advisory chat, ai-lab/finsense/autonomy/agent-hub, drl page, 3 LLM, LGBM ranker (bağsız), regime_weights (bağsız), Optuna 200-trial, DRL PPO | NEGATİF |

**Sistemin gerçek çekirdeği:** `scanner/evaluate.py` → `kpi_tracker.record()` → `outcome_reconciler` → `calibration` → `registry`. Bu 5 modül + Telegram + minimal dashboard yeterli bir ürün.

---

## 5) Optimizasyon Tablosu

| Modül | Optimize alanı | Beklenen kazanç | Ölçüm | Öncelik |
|---|---|---|---|---|
| `scanner/evaluate.py` | Look-ahead / leakage audit | Backtest vs paper Brier farkı görünür olur | Brier delta | **P0** |
| `kpi_tracker` outcome | Slippage + spread modeli | Gerçek edge tahmini | Paper P&L vs simülasyon | **P0** |
| `calibration` | Refit telemetrisi (ECE before/after) | "Refit zarar veriyor mu?" | ECE_before/after audit | **P0** |
| `registry` champion | Paper Brier'i canlı raporla | Gerçek edge görünür | Dashboard tile | **P0** |
| `scheduler` | 9 → 4 job | Latency, başarısızlık alanı ↓ | Job count | **P1** |
| `scanner` data fetcher | OHLCV Redis cache (5dk) | Latency 3–10× ↓ | p50/p95 scan | **P1** |
| `research/sweep` | 200 → 50 trial | Haftalık 4× hızlı | Sweep duration | **P1** |
| `regime_weights` + `lgbm_ranker` | Wire OR archive | Ölü kod eksilir | Coverage | **P1** |
| `llm/router` | 3 → 1 provider + cache | Bakım ↓ | Provider count | **P2** |
| `requirements*.txt` ×6 | pyproject extras | Onboarding kolay | Dosya sayısı | **P2** |
| `web/dashboard` | 17 → 5 sayfa | UX netlik | Page count | **P2** |
| `drl/` | Feature flag, default off | Bilişsel yük ↓↓ | Import count | **P2** |

---

## 6) Sadeleştirme Kararları

| Karar | Bileşen | Gerekçe |
|---|---|---|
| **Keep** | scanner, kpi_tracker, outcome_reconciler, calibration, registry, walkforward, paper_portfolio, alpaca broker, auth, Telegram | Çekirdek + zorunlu destek |
| **Simplify** | scheduler (9→4), sweep (200→50), LLM router (3→1), advisory (static report), agents/* (fonksiyon olarak) | Karmaşıklık değere orantısız |
| **Merge** | Dashboard sayfaları → 5 ana + 1 Lab | Kullanıcı boğulur |
| **Merge** | 6 requirements → pyproject extras | Tek kaynak |
| **Feature-flag** | drl, lgbm_ranker, regime_weights | Edge gösterilene kadar default off |
| **Freeze** | advisory, ai-lab, finsense, telegram_bot_runner | Bakım yapma |
| **Archive** | views/, streamlit_app.py | Dead |
| **Remove** | Root CSV'leri + scanner.py + demo + live_compare + telegram_test | Artifact |

---

## 7) Mimari ve Operasyonel Bulgular

| Bulgu | Risk | Ciddiyet | Öneri |
|---|---|---|---|
| scheduler.py 1200 LOC, 9 job, single SPOF | Bir job bozarsa tümü etkilenir | **Yüksek** | Job'ları ayrı modül + per-job test |
| Auto-approve in-memory, persist yok | Restart'ta state kaybı | **Yüksek** | Redis persist veya feature kaldır |
| Champion'ın paper P&L'i dashboard'da yok | Self-improving edge ölçülmüyor | **Yüksek** | Champion edge tile |
| Calibration refit telemetrisi (ECE before/after) yok | Refit zarar verirse fark etmeyiz | **Yüksek** | audit_log payload genişlet |
| 6 requirements + pyproject paralel | Env tutarsızlığı | Orta | pyproject extras'a göç |
| 3 LLM provider; failover hiç görülmedi mi? | Karmaşıklık edge olmadan | Orta | 1 provider + cache |
| 17 dashboard, UX testi yok | Kullanıcı boğulur | Orta | 5 sayfa + analytics |
| drl/ 28 dosya, edge metriği yok | Bakım yükü, "smart" görüntü | Orta | Edge raporuna kadar feature flag |
| Test coverage raporu yok | Yeşil yalanı | Orta | pytest --cov CI |
| Sentry/Prometheus alert hiç tetiklenmiş mi? | "Monitoring kuruldu" ≠ "çalışıyor" | Orta | Sentetik test alert |
| Root artifact dosyaları | Git noise | Düşük | Sil → ✅ (S16-01) |
| LangGraph CEO; agent ince wrapper | Stack trace okunmaz | Orta | Pipeline fonksiyonu |
| archive/ 5000+ LOC | Grep noise | Düşük | Branch tag + sil |

---

## 8) Otonomi Olgunluk Değerlendirmesi

| Seviye | Tanım | Biz neredeyiz? | Eksik |
|---|---|---|---|
| 0 Manuel | Cron yok | Geçtik | — |
| 1 Kısmi otomasyon | Scanner cron | Geçtik | — |
| 2 Modüler kopuk otomasyon | Job'lar var, closed-loop edge ölçülmüyor | **BURADAYIZ** | bkz. Seviye 3 |
| 3 Ölçülmüş + kalite-kapılı | Refit/promote önce-sonra ölçüsüyle raporlanır | Yakın | ECE before/after, champion edge tile, auto-approve persist |
| 4 Kontrollü self-improving | Suggest→Validate→Paper-test→Promote→Monitor→Rollback tam zincir | Erken | Paper sandbox, audit trail, tek modül |
| 5 Minimum-insan otonomi | 4 hafta stabil paper edge | Çok erken | Seviye 3+4 tamamlanmadan konuşulmaz |

**Net karar: bugün Seviye 2.** Sprint 14–15 ile Seviye 3 altyapısı kuruldu, **telemetri** ile kapanır.

---

## 9) İnsan Müdahalesi Azaltma Matrisi

| İş | Full auto | Approval | Manual | Not |
|---|---|---|---|---|
| Scanner run (hourly) | ✅ | | | Mevcut |
| Sinyal kayıt | ✅ | | | Mevcut |
| Outcome reconciliation | ✅ | | | Mevcut |
| Telegram alert | ✅ | | | Mevcut |
| Weekly report | ✅ | | | Mevcut |
| Drift detect + refit tetik | ✅ | | | Mevcut (Sprint 14) + telemetri ekle |
| Calibration refit | ✅ | | | Karar loglanmalı |
| Champion promote | | ✅ | | Paper P&L görünmeden tehlikeli |
| Recalibration (WF+Optuna) | | ✅ | | Promote insan onayı |
| Auto-approve | | ✅ | | Önce persist çöz |
| Quality gate degraded | ✅ | | | Mevcut |
| Rollback | | ✅ | | Bir-tıkla UI yeterli |
| **Live trading / real broker** | | | ❌ ASLA | Paper only |
| Dashboard refresh | ✅ | | | Polling |
| Repo commit / migration | | | ❌ Manuel | Tek geliştirici |

---

## 10) Self-Improving Loop Tasarımı

```
Measure → Detect → Diagnose → Suggest → Validate → Paper-test → Promote → Monitor → Rollback
```

| Adım | Veri | Metrik | Otomatik? | Onay? | Log |
|---|---|---|---|---|---|
| Measure | Sinyal + outcome | Brier, ECE, WR, PF, paper P&L | — | — | kpi_tracker |
| Detect | Skor dağılımı | KS p<0.05; ΔBrier > +%10 | ✅ | — | drift_job |
| Diagnose | Per-regime/sector | Hangi bozuldu? | Yarı | İnsan inceler | CEO report |
| Suggest | WF + Optuna | Yeni params + Brier | ✅ | — | registry |
| Validate | Champion gate | ΔBrier < -%3 AND ΔSharpe > +0.1 | ✅ | — | strike log |
| **Paper-test** | 30g sandbox | Slippage-aware P&L | ⚠ **EKSİK** | — | **research/paper_sandbox.py** |
| Promote | Paper geçti | İlk 3 ay onay | ✅ (gelecek) | ✅ (şimdi) | audit_log + Telegram |
| Monitor | 7g rolling Brier | ΔBrier > +%10 → rollback | ✅ | — | quality_gate |
| Rollback | 2-strike | Otomatik prev-champion | ✅ | Opsiyonel veto | registry |

**Şu an eksik:**
1. Challenger paper sandbox
2. Refit/promote audit log (önce/sonra metrik)
3. Live edge görünürlük tile

---

## 11) Doğru Sorular Çerçevesi

### `scanner/evaluate.py`
- **Tanı:** Skor paper'da gerçekten outcome ile korele mi? Look-ahead var mı?
- **Optimizasyon:** Hangi feature gerçek lift veriyor? Sector_rs/vol_regime gerçekten ayırt edici mi?
- **Evrim:** Hangi metrik bozulursa (ECE > 0.10) recalibration zorunlu?

### `core/calibration.py`
- **Tanı:** ECE refit sonrası gerçekten düşüyor mu? Refit ne sıklıkla zarar veriyor?
- **Optimizasyon:** Isotonic/Platt/sigmoid — hangisi bu veri için en iyi?
- **Evrim:** Refit kararı drift_job'a tam delege edilebilir mi?

### `research/registry.py`
- **Tanı:** Şimdiye kadar kaç promote oldu? Promote sonrası gerçekten iyi mi?
- **Optimizasyon:** 2-gate yeterli mi? Paper sandbox eklenmeli mi?
- **Evrim:** Promote insan onayından otomatiğe ne zaman geçer?

### `core/scheduler.py`
- **Tanı:** Hangi job en çok başarısız? Hangisinin watchdog'u tetikleniyor?
- **Optimizasyon:** 9 job'un kaçı gerçek değer üretiyor vs log noise?
- **Evrim:** Event-driven mi cron mu?

### `drl/ensemble_router.py`
- **Tanı:** DRL'in ölçülmüş edge'i var mı? W_DRL=0 neden?
- **Optimizasyon:** Edge yoksa freeze; varsa A/B framework.
- **Evrim:** Meta-learner sürekli mi çeyrekte bir mi güncellenir?

### `agents/ceo.py`
- **Tanı:** LangGraph gerçek bir karar mı veriyor, lineer pipeline mı?
- **Optimizasyon:** Lineer ise LangGraph'i çıkar.
- **Evrim:** Paralel branch + conditional join gerekiyorsa tut.

### `web/dashboard/*`
- **Tanı:** Son 30g hangi sayfa açıldı? Analytics?
- **Optimizasyon:** Top 5 + diğer Lab.
- **Evrim:** Kullanıcı geldikçe geri aç.

---

## 12) Evrim Senaryosu

**Faz A — Görünürlük (1–2 hafta):** Champion edge tile, refit audit log, promote audit, coverage badge, sentetik alert.

**Faz B — Sadeleştirme (2–3 hafta):** pyproject extras, root cleanup, 17→5 sayfa, 3→1 LLM, LangGraph→pipeline, 9→4 job, drl/lgbm/regime_weights flag.

**Faz C — Kalite Kapıları (2 hafta):** Look-ahead audit, slippage modeli, auto-approve persist, challenger paper sandbox.

**Faz D — Kontrollü Otomasyon (2 hafta):** Promote insan onayı UI, bir-tıkla rollback, günlük edge dashboard.

**Faz E — Self-Improving Loop (sürekli):** Tam zincir tek `evolution_loop.py`. DRL/LGBM/regime gerçekten edge gösterirse aç.

---

## 13) Execution Roadmap

### Bugün (5 iş)
1. Root artifact temizliği
2. Audit raporu commit
3. Auto-approve persist gap dökümante
4. Champion edge API
5. Requirements env-mapping (DEPENDENCIES.md zaten yapmış)

### Bu hafta (10 iş)
6. Champion edge dashboard tile
7. Calibration refit audit log
8. requirements → pyproject extras
9. drl/lgbm_ranker/regime_weights → feature flag
10. 17 → 5 sayfa (10 sayfa ?lab=1 arkası)
11. 3 → 1 LLM provider + cache
12. Scheduler 9 → 4 job
13. Test coverage badge
14. Look-ahead audit script
15. LangGraph CEO → pipeline.run_cycle()

### Bu ay (15 iş)
- Auto-approve persist veya kaldır
- Slippage/spread modeli
- Challenger paper sandbox
- Promote insan onayı UI
- Bir-tıkla rollback UI
- sector_rs/vol_regime lift raporu
- lgbm_ranker wire or archive
- regime_weights wire or archive
- Optuna 200→50
- Sentetik alert ping
- CEO report'a promote/rollback tarihçesi
- Test coverage %60
- README'yi ürün odağına indir
- archive/ git tag + sil
- views/ + streamlit_app.py sil

### 90 gün
- Self-improving loop tam zincir (`evolution_loop.py`)
- 30g paper edge raporu
- DRL/LGBM/regime — ölçülmüş edge raporu; lift yoksa repo'dan çıkar
- Multi-market (XETRA) sadece tek pazarda edge kanıtlandıktan sonra
- PostgreSQL prod (kullanıcı > 10)
- ADR klasörü + 10 ADR
- K8s/scale (kullanıcı zorluyorsa)

---

## 14) Son Karar

**FinPilot bugün "kapasitesi yüksek, ürün netliği düşük, edge ölçüsü görünmez" bir sistemdir.**

Çekirdek (scanner + closed-loop kalibrasyon + champion gate) güçlü ve korunmalı. Etrafındaki LangGraph multi-agent, 3-LLM router, DRL PPO, advisory chat, 17 dashboard, 6 requirements, kullanılmayan LGBM ranker ve regime_weights **tek geliştirici için sürdürülebilir değil** ve çekirdek mühendisliğinden dikkati çalıyor.

**Yapılacak tek doğru şey:** önce champion edge görünürlüğü, sonra agresif sadeleştirme, ondan sonra self-improving loop'u kapat. "Daha çok feature" değil, "daha ölçülebilir, daha sade, daha güvenilir" doğru yön.

**Otonomi seviyesi:** Bugün **Seviye 2**, bu hafta önerilen telemetri ile **Seviye 3** kapanabilir. Seviye 4 için **daha az kod, daha çok ölçüm.**
