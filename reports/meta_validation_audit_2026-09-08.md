# META-VALIDATION & EVIDENCE AUDIT — FinPilot × FinSense

**Tarih:** 2026-09-08 · **Prompt:** Meta-Validation Master Prompt v1.0
**Level:** A — READ-ONLY / NO IMPLEMENTATION (hiçbir kod/config/veri/flag değiştirilmedi)
**Denetlenen artifact:** `reports/master_project_reality_audit_2026-09-08.md`

---

## A. AUDIT RELIABILITY (önceki denetim ne kadar güvenilir?)

**Önceki audit kalite skoru: 47/60 — GOOD BUT NEEDS TARGETED CORRECTION**

| Boyut | Skor | Not |
|---|---|---|
| Code verification | 4/5 | `.env` + score_engine doğrudan okundu |
| Runtime verification | 4/5 | API/web/DB probları yapıldı |
| Data verification | 4/5 | DB'ler açıldı, sayıldı |
| Research verification | 5/5 | decision-log + reports izlendi |
| Source traceability | 5/5 | Her iddia kaynağa bağlı |
| Reproducibility | 3/5 | Bazı ölçümler tek seferlik |
| Number integrity | 5/5 | 4 rakam ayrımı korundu |
| Contradiction detection | 5/5 | Feature flag çelişkisi yakalandı |
| Production/research separation | 4/5 | Ayrım var ama flag etkisi ölçülmemişti |
| FinPilot/FinSense separation | 4/5 | Ayrım doğru |
| Unknown handling | 4/5 | UNKNOWN'lar işaretlendi |
| Overclaim prevention | 4/5 | — |

**Düzeltme gerektiren:** Önceki audit "flag'ler açık ama doğrulanmamış" dedi ama **skor etkisini ölçmedi.** Bu meta-audit ölçtü (aşağıda) — iddia doğrulandı ve büyütüldü.

---

## B. FEATURE FLAG FORENSIC AUDIT — CRITICAL

**.env runtime değerleri (doğrudan okundu) [V]:**

| Flag | Değer | score_engine'de çağrı |
|---|---|---|
| FINPILOT_ENABLE_SQUEEZE_FACTOR | **1** | 6× |
| FINPILOT_ENABLE_EDGAR_CATALYST | **1** | 8× |
| FINPILOT_ENABLE_LOTTERY_FADE | **1** | 4× |
| FINPILOT_ENABLE_OVERNIGHT_GAP | **1** | 4× |
| FINPILOT_ENABLE_FRED_MACRO | 1 | (macro multiplier) |
| FINPILOT_ENABLE_FUNDAMENTALS | 1 | — |
| FINPILOT_ENABLE_NEWS | 1 | — |
| FINPILOT_ENABLE_ALPHA_V2 | 1 | — |
| FINPILOT_ENABLE_SHADOW_SCORECARD | 1 | — |

**Skor etkisi ölçümü (2026-09-08, bugünkü export, 1.801 satır) [V]:**

| Ölçü | Değer |
|---|---|
| Skoru değişen satır | **1.503 / 1.801 (%83,5)** |
| Anlamlı kayma (\|Δ\|≥0,5) | **775 satır** |
| Ortalama delta | **-0,639** (aşağı çekiyor) |
| Medyan delta | -0,512 |
| Aralık | -2,98 … +1,11 |

**Faktör verisi mevcut (sıfır değil):** squeeze nonzero 1.217, lottery nonzero 1.503, overnight nonzero 1.288.

**Kritik sorunun cevabı:** *"Could the current production score be materially different from the intended validated score because of these flags?"* → **EVET [V].** Flag'ler skoru %83,5 satırda değiştiriyor ve net etki aşağı yönlü (lottery/overnight cezaları squeeze'ten ağır basıyor). Ama bu faktörlerin hiçbiri matched-control ile doğrulanmadı.

**Nuans [I]:** Bu "flag'ler yanlış" demek değil — "flag'ler **doğrulanmamış** ve skoru maddi olarak değiştiriyor" demek. Karar: ya kapat (decision-log'la uzlaştır) ya da component-ablation kanıtı üret. **Hiçbir flag değiştirilmedi (read-only).**

---

## C. CATALYST CACHE INCIDENT FORENSICS

**ROOT CAUSE: PROBABLE (kesin değil)**

Kanıt zinciri:
1. 2026-09-03: canlı-SEC refresh 1.801/548 doldurdu (atomik tmp+replace) [V]
2. 2026-09-07 11:28: cache 8/0'a geriledi [V]
3. Aynı gün kullanıcı **yerel-cache versiyonunu** koştu (`research/catalyst_universe_refresh_2026_09_03.py` — yerel edgar_cache'ten, 1.199/0) — bu **üzerine yazan** process [V, decision-log]
4. Ama 8/0 ≠ 1.199/0 — arada başka bir yazma daha oldu (zaman damgası uyuşmuyor tam)

**Hangi process yazıyor:** `scanner/catalyst.py::refresh_catalyst_cache` (tmp+replace) + kullanıcının yerel script'i. **Race condition kanıtı yok ama iki ayrı yazıcı var** — bu bir çift-yazıcı mimarisi sorunu.

**ROOT CAUSE: PROBABLE = çift-yazıcı + yeniden-çalıştırma.** Kesin kanıt için yazma-log'u yok (kimse yazma olayını loglamıyor). **Cache onarılmadı (read-only).**

---

## D. FINSENSE SOURCE-OF-TRUTH FORENSICS

**İki DB doğrulandı [V]:**
- `C:\Users\meric\Finsense\data\academy.db`: **96 ders (8 published, 88 draft)**
- `C:\Users\meric\Borsa\data\academy.db`: **0 ders (boş)**

**Hangi DB authoritative?** Web'in okuduğu `academy_lessons.json` Finsense'nin export'undan geliyor → **Finsense şu an fiilen authoritative** ama bu **belgelenmemiş bir karar** — [I]. Borsa'nınki boş ve kullanılmıyor.

**Yaşam döngüsü:** generation → quality_control → storage → publish_status → export → web → user
- generation: WORKING (96 üretildi)
- quality_control: **UNKNOWN** (quality_guard hiç koştu mu kanıt yok — 88 draft bunun kanıtı)
- storage: WORKING (Finsense DB)
- export: **MANUAL** (Finsense→Borsa, `export_lessons.py` ayrı repo)
- web: WORKING (academy_lessons.json okunuyor)

---

## E. SCHEDULER FORENSICS

**Akademi scheduler:** `academy/scheduler.py` var, `api/main.py:225` başlatıyor, apscheduler+pytz kurulu [V].
**Ama "Started" logu hiçbir yerde gözlemlenmedi** — son çalıştırma kanıtı yok.

**Sınıflandırma: REGISTERED (kod var, başlatılıyor) — ama RUNNING/SUCCESSFULLY EXECUTING kanıtlanmadı → ❓ UNKNOWN.**

APScheduler `BackgroundScheduler` ana process'e bağlı; API restart'ta ölür. İzlenmiyor.

---

## F. ATTENTION MAP RE-CLASSIFICATION

| Seviye | Durum | Kanıt |
|---|---|---|
| VALIDATED — DESCRIPTIVE RESEARCH | ✅ | 40.834 satır, lift 1,7–3,3×, 5 ay, matched-control |
| VALIDATED — DIRECTION | ❌ | Yön yok (8 yol kapandı) |
| VALIDATED — OOS | ❌ | Locked OOS NOT_OPENED |
| VALIDATED — PRODUCTION | ❌ | Feature flag'a hiç ulaşmadı; export alanları kısmi |
| VALIDATED — ECONOMIC | ❌ | Maliyet modeli yok |

**Doğru sınıflandırma:** DESCRIPTIVE RESEARCH seviyesinde. Production'a terfi etmesi için shadow koşu şart. Önceki audit bunu doğru sınıflandırdı.

---

## G. CLAIM AUDIT — önceki audit'in ana iddiaları

| İddia | Durum | Güven |
|---|---|---|
| API 128 endpoint | VERIFIED | HIGH (openapi 200) |
| Web çalışıyor | VERIFIED | HIGH (127.0.0.1 200; localhost timeout ayrı konu) |
| Günlük tarama çalışıyor | VERIFIED | HIGH (2026-09-07 export) |
| Dağıtım zinciri çalışıyor | VERIFIED | HIGH (gate PASS + commit ff9658a) |
| Flag'ler skoru etkiliyor | **VERIFIED** | HIGH (meta-audit ölçtü: %83,5 satır) |
| Flag'ler doğrulanmamış | VERIFIED | HIGH (matched-control yok) |
| Catalyst cache regresyonu gerçek | VERIFIED | HIGH (1.801→8) |
| 8 yön yaklaşımı başarısız | VERIFIED | HIGH (2 batarya artifact) |
| Attention map research-validated | VERIFIED | HIGH (ama production değil) |
| Akademi scheduler çalışıyor | UNKNOWN | — (kanıt yok) |
| Çift DB | VERIFIED | HIGH (96 vs 0) |
| Redis onarımı doğrulandı | DOCUMENTED | MEDIUM (önceki oturum, bu oturumda doğrulanmadı) |

---

## H. PRODUCTION VS RESEARCH

| Bileşen | Research | Shadow | Production | Economically Validated |
|---|---|---|---|---|
| Score engine | — | — | 🟢 LIVE | ❌ (flag faktörleri doğrulanmadı) |
| Attention map | 🟢 | ❌ | ❌ | ❌ |
| Catalyst | 🟡 (regresyon) | — | ❌ (flag açık ama veri boş) | ❌ |
| Fade | 🟠 (discovery) | — | ❌ | ❌ |
| TimesFM | ❌ | — | ❌ | ❌ |
| Locked OOS | — | — | ❌ NOT_OPENED | — |

---

## I. META-CONTRADICTION AUDIT

### 🔴 CRITICAL — Feature flag çelişkisi (büyütüldü)
- Claim A: "flag'ler default OFF / validate-first" (decision-log)
- Claim B: ".env'de 9 flag =1, score_engine kullanıyor, %83,5 satır etkileniyor" (.env + score_engine + meta-ölçüm)
- **Yüksek kanıt:** B (çalışan sistem)
- **Çözüm:** kod ve doküman uzlaştırılmalı — flag'leri kapat VEYA ablation kanıtı üret. Read-only; değiştirilmedi.

### 🟡 MEDIUM — Çift academy DB (Finsense 96 vs Borsa 0)
### 🟡 MEDIUM — localhost vs 127.0.0.1 (web)
### 🟢 LOW — Catalyst cache çift-yazıcı (iki process yazıyor)

---

## J. KEEP / CHANGE / FREEZE / KILL / TEST

| Bileşen | Karar | Kanıt |
|---|---|---|
| Yayın zinciri | KEEP | Doğrulanmış |
| Scanner/evaluate | KEEP | Sözleşme tutarlı |
| Yön tahmini | KILL | 8 yol, kanıt yeterli |
| entry_ok | KILL | Adverse selection |
| High-RVOL | KILL | Reddedildi |
| TP/SL grid | KILL | 3.120 konfigürasyonda kanıt yok |
| Rejim katmanı | KILL | OOS'ta öldü |
| Attention map | TEST | Shadow koşu gerek |
| Fade | TEST | 3 koşul |
| TimesFM | TEST | EOD-only backtest önce |
| **Feature flag'ler** | **CHANGE** | **Açık ama doğrulanmamış, %83,5 etki** |
| Catalyst cache | CHANGE | Çift-yazıcı + regresyon |
| FinSense döngüsü | CHANGE | Scheduler + export + çift DB |
| Akademi scheduler | TEST | Çalıştığını kanıtla |
| Locked OOS | FREEZE | Kapılar açılmadı |

---

## K. NEXT 5 ACTIONS (yalnızca 5)

1. **Feature flag kararı:** 9 açık flag'i kapat VEYA component-ablation kanıtı üret (skor %83,5 satırda sapıyor). — **EN YÜKSEK ÖNCELİK**
2. **Catalyst cache çift-yazıcıyı tek-yazıcıya indir** + regresyon kök nedenini logla.
3. **Akademi scheduler'ın çalıştığını kanıtla** (health endpoint'e ekle veya ilk çalıştırmada log doğrula).
4. **Çift academy DB kararı:** Finsense'yi authoritative ilan et VEYA birleştir — belgelensin.
5. **88 draft dersi quality_guard'dan geçir** (toplu denetim — hiç koşulmadı).

---

## FINAL VERDICT

**Önceki audit güvenilir mi?** Büyük ölçüde evet (47/60) — ama feature flag iddiası **doğruydu ve yetersizdi**: "açık ama doğrulanmamış" dedi, skor etkisini ölçmedi. Meta-audit ölçtü: **%83,5 satırda skor sapıyor.** Bu, önceki audit'in en önemli bulgusunu doğruladı ve büyüttü.

**Şu an güvenilebilecekler:** yayın zinciri, tarama, auth, API, attention map (research), negatif bilgi tabanı.
**Şu an güvenilemeyecekler:** canlı skorun flag-etkili hali (doğrulanmamış), akademi scheduler, catalyst cache, FinSense döngüsü.

**Tek en önemli sonraki doğrulama:** Feature flag kararı — canlı skorun bütünlüğü.

---

## Governance

- Salt-okunur; hiçbir kod/config/veri/flag/DB değiştirilmedi.
- Locked OOS NOT_OPENED, erişilmedi.
- Çelişkiler gizlenmedi. Önceki audit'in kendisi denetlendi ve düzeltildi.
