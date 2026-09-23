# MASTER PROJECT REALITY & CONTINUITY AUDIT — FinPilot × FinSense

**Tarih:** 2026-09-08 · **Prompt:** `docs/MASTER_PROJECT_REALITY_AUDIT_PROMPT.md` v1.0
**Level:** A (salt-okunur denetim; hiçbir kod/config/veri değiştirilmedi)
**Yöntem:** FAZ 1 (Discovery) + FAZ 2 (Evaluation) — gerçeklik hiyerarşisi: çalışan kod → veri → test → doküman

---

## PART A — EXECUTIVE SUMMARY

FinPilot, **çalışan bir araştırma + dağıtım sistemidir**: 128-endpoint FastAPI (canlı), Next.js web (canlı, 127.0.0.1:3001), 23 ajan, 61 araştırma scripti, 90 rapor. Günlük tam-evren tarama (1.812 sembol → 1.801 satır) çalışıyor ve yayın zinciri (export → gate → snapshot → Telegram → web → git) doğrulanmış durumda.

**En kritik bulgu:** `.env`'de **tüm feature flag'ler açık** (catalyst, squeeze, lottery, overnight, FRED, fundamentals, news, alpha_v2) — ama decision-log bunları "default OFF / validate before enable" olarak belgeliyor. Bu bir **kod↔doküman çelişkisi (CRITICAL)**: canlı skor motoru, doğrulanmamış faktörleri (henüz kanıtlanmamış catalyst/lottery/squeeze etkileri) aktif olarak kullanıyor olabilir.

**İkinci kritik bulgu:** FinSense akademi döngüsü (üret→denetle→düzelt→yayınla→web→sürekli) **kodu var ama döngü kapalı değil** — 96 ders üretilmiş (8 yayında, 88 draft'ta takılı), Borsa'nın academy.db'si boş, export köprüsü ayrı repo'da ve manuel.

---

## PART B — CURRENT PROJECT REALITY

### 🟢 ÇALIŞAN (runtime'da doğrulandı)
- **API:** 128 endpoint, `/docs` + `/openapi.json` 200 OK (localhost:8001). Auth, scan, watchlist, academy, execution, loop, research, trade router'ları kayıtlı.
- **Web:** 127.0.0.1:3001 200 OK (localhost:3001 timeout — DNS/IPv6 ayrımı; `127.0.0.1` çalışıyor).
- **Tarama:** 2026-09-07 export: universe=1812, result_count=1801, scan_complete=True, 0 kopya, prepublish gate PASS.
- **Dağıtım zinciri:** export → prepublish_gate → snapshot → Telegram queue → web artifact → git push (son başarılı web commit ff9658a, 2026-09-03).
- **Ollama:** çalışıyor, qwen2.5:7b + 16 model yüklü (akademi LLM provider'ı hazır).
- **SEC EDGAR:** canlı erişim doğrulandı (10.412 ticker map, gerçek filing'ler).

### 🔵 DOĞRULANMIŞ (test/kanıtla)
- Redis AOF onarımı (2026-08-27, veri kaybı yok)
- Prepublish gate (38 odak testi geçti)
- Admin auth reset + login doğrulaması
- c2c_5d etiket bütünlüğü teşhisi (EOD ρ=0,9829 vs intraday 0,9173 — kök neden: gün-içi scan_ts karışıklığı)

### 🔴 BAŞARISIZ / NEGATİF (kanıtlı, kayıtlı)
- Yön tahmini: **8 bağımsız yaklaşım başarısız** (regime, breadth, sektör, tier, intraday path...)
- entry_ok: winner'ların %97,5'ini kaçırıyor; adverse selection
- High-RVOL: pozitif selector olarak reddedildi
- Statik skor ↔ ileri getiri: ρ=0,013–0,019; Brier skill negatif
- 3.120 TP/SL konfigürasyonunda küresel kanıt yok

### 🟡 KISMEN / KOPUK
- **FinSense döngüsü:** 6 ajan + orchestrator + scheduler var ama döngü kapalı değil (scheduler kanıtı yok, çift DB, export manuel)
- **Catalyst cache:** 1.801/548 dolu → 8/0'a geriledi (2026-09-07, üzerine yazıldı — regresyon)

### ❓ BİLİNMEYEN
- Akademi scheduler'ının gerçekten çalışıp çalışmadığı (log kanıtı yok)
- `localhost` vs `127.0.0.1` web erişim ayrımının kök nedeni

---

## PART C — FINPILOT SYSTEM MAP

```
yfinance/EODHD/SEC-EDGAR ──→ scanner/evaluate.py ──→ score_engine.py (flag'ler)
        │                          │                        │
   price_cache (2.046 OHLCV)  features.py              [FLAG'LER AÇIK — bakınız Part J]
        │                          │                        │
        └──────→ scan_export_*.json ──→ snapshot_builder ──→ prepublish_gate
                                                     │
                              ┌──────────────────────┼──────────────────┐
                          Telegram                 web/public         API /scan/*
                          queue                 demo_snapshot.json
```

**Gerçek bağlantılar (kod-doğrulanmış):**
- `scanner/evaluate.py` → 136 alanlık satır → `data/distribution/scan_export_<date>.json`
- `distribution/snapshot_builder.py` → `data/distribution/snapshot_latest.json` + `web/public/demo_snapshot.json`
- `distribution/prepublish_gate.py` → `check_export_health()` → publish kararı
- `distribution/jobs.py` → `job_draft()` → Telegram queue → `scripts/publish_web.py` → git push

---

## PART D — FINSENSE SYSTEM MAP

```
academy/domains.py (12 domain, 69 modül)
        │
academy/agents/ (6 ajan: generator, quality_guard, gap_detector, updater, analytics, personalization)
        │
academy/orchestrator.py (run_daily/weekly/quarterly)
        │
academy/scheduler.py (APScheduler — günlük 02:00, haftalık Paz 07:00)
        │
        ├─→ Finsense/data/academy.db (96 ders: 8 published, 88 draft)  [AYRI DB]
        ├─→ Borsa/data/academy.db (0 ders — BOŞ)                        [BOŞ]
        │
Finsense/academy/export_lessons.py ──→ Borsa/web/public/academy_lessons.json  [MANUEL KÖPRÜ]
        │
scripts/publish_web.py ──→ git push ──→ Vercel
```

**Kopukluklar:** (1) scheduler çalıştığı kanıtlanmadı; (2) çift DB — hangisi "gerçek" belirsiz; (3) export manuel ve ayrı repo'da; (4) 88 ders draft'ta takılı (quality_guard denetlenmemiş).

---

## PART E — MODULE & DEPENDENCY INVENTORY (özet)

| Modül | Rol | Durum | Kanıt |
|---|---|---|---|
| scanner/evaluate.py | 136-alan satır üretimi | 🟢 WORKING | 2026-09-07 export |
| scanner/score_engine.py | composite skor | 🟠 UNVALIDATED | flag'ler açık ama faktörler doğrulanmadı |
| distribution/* | yayın zinciri | 🟢 VALIDATED | gate PASS, web commit ff9658a |
| api/main.py | 128-endpoint API | 🟢 WORKING | openapi 200 OK |
| academy/orchestrator.py | ders döngüsü | 🟡 PARTIAL | var ama tetiklenmiyor |
| academy/scheduler.py | zamanlanmış çalıştırma | ❓ UNKNOWN | hiç "Started" logu görülmedi |
| agents/ (23) | çok-ajanlı analiz | 🟠 UNVALIDATED | registry var, canlı koordinasyon ölçülmedi |
| auth/ | kullanıcı/session | 🟢 VALIDATED | admin reset + login doğrulandı |
| drl/ (45 dosya) | DRL araştırma | 🔵 FROZEN | araştırma, production değil |

---

## PART F — COMPLETED / WORKING / FROZEN / PARTIAL AUDIT

| Kategori | İçerik |
|---|---|
| 🟢 WORKING | API, web, tarama, yayın zinciri, auth, Ollama, EDGAR erişimi |
| 🟢 VALIDATED | Redis onarımı, prepublish gate, admin auth, c2c_5d teşhisi |
| 🔵 FROZEN | DRL (araştırma), locked OOS (açılmadı), yön tahmini (8 yol kapandı) |
| 🟡 PARTIAL | FinSense döngüsü, catalyst cache (geriledi), attention map (kod var, production'a ulaşmadı) |
| 🔴 FAILED | entry_ok, High-RVOL selector, statik skor, TP/SL konfigürasyonları |
| ⚪ PLANNED | Attention map production geçişi (feature flag), fade confirmatory, TimesFM backtest |
| ❓ UNKNOWN | Akademi scheduler çalışıyor mu, localhost/127.0.0.1 ayrımı |

---

## PART G — RESEARCH & EXPERIMENT LEDGER (özet, 90 rapor)

| Deney | n | Sonuç | Statü |
|---|---|---|---|
| Attention map | 40.834 | Betimleyici çerçeve kanıtlandı (hareket, yön değil); lift 1,7–3,3×, 5 ay | 🟢 VALIDATED (research) |
| Direction-context battery | 40.834 | Rejim/breadth/sektör yönü koşullamıyor | 🔴 FAILED |
| Experiment #1 (Rejim×Tier×eşik) | 40.834 | Tier rejimden baskın; High tier her rejimde negatif | 🔴 FAILED |
| Winner anatomy | 40.834 | entry_ok %97,5 winner kaçırıyor | 🔴 FAILED (mevcut seçim) |
| Fade (opening-range) | 698 | %59,9 brüt win ama %1 maliyette negatif | 🟠 DISCOVERY SIGNAL (koşullu) |
| c2c_5d integrity | 3.000 eşleşmiş | EOD ρ=0,98, intraday 0,92 — kök neden bulundu | 🟢 VALIDATED (teşhis) |
| Catalyst pipeline | 1.801 | %100 kapsam, 548 nonzero — AMA cache geriledi | 🟡 PARTIAL (regresyon) |

---

## PART H — FAILURE / NEGATIVE KNOWLEDGE LEDGER

| Denendi | Beklenti | Sonuç | Tekrar? |
|---|---|---|---|
| Statik skor → yön | Skor yüksek = getiri yüksek | ρ≈0, Brier negatif | ❌ KILL (8 yol kapandı) |
| entry_ok filtresi | Daha iyi seçim | Adverse selection, %97,5 winner kaçırma | ❌ KILL |
| High-RVOL selector | Yüksek RVOL = fırsat | Reddedildi (artefakt) | ❌ KILL |
| 3.120 TP/SL grid | Optimal çıkış bulunur | Küresel kanıt yok | ❌ KILL |
| Opening-range fade | Gün içi devam | %39,7 devam; fade %59,9 ama maliyette negatif | 🔄 TEST (koşullu — maliyet+OOS) |
| Rejim katmanı | Rejim yönü koşullar | OOS'ta öldü | ❌ KILL |

---

## PART I — DATA & NUMBER INTEGRITY AUDIT

| Sayı | Kaynak | Dataset | Tanım | Durum |
|---|---|---|---|---|
| 5.216 | signals_archive | barrier-captured | Ana karne | 🟢 [V] |
| +%0,40 | signals_archive | historical mean | Barrier-based expectancy | 🟢 [V] |
| 46.581 | full_universe_barrier_results.json | ayrı grid | MFE çalışması | 🟢 [V] (ayrı) |
| 111 | full_universe_enriched.csv | resolved_pct_t5 | ≥%100 MFE gözlemleri | 🟢 [V] (ayrı, kuyruk temizli) |

**Çelişki yok** — dört rakam ayrı dataset'te, spec bunu kilitledi.

**Veri bütünlüğü olayları (kayıtlı):**
- Catalyst cache regresyonu (1.801/548 → 8/0, 2026-09-07) — **kök neden: hangi işlem ezdi, bilinmiyor**
- 148 sembolde büyük jump flag (adjusted-close audit) — kurumsal-aksiyon bekçisi önerildi
- c2c_5d intraday karışıklığı — EOD-only filtre önerildi, backfill üretildi

---

## PART J — CONTRADICTION REPORT

### 🔴 CRITICAL — Feature flag'ler vs decision-log

`.env`'de **9 flag açık** (catalyst, squeeze, lottery, overnight, FRED, fundamentals, news, alpha_v2, shadow_scorecard). Decision-log bunları tekrar tekrar "default OFF / validate with component_ablation before enabling" olarak belgeliyor. **score_engine.py bu faktörleri aktif kullanıyor** — ama hiçbiri matched-control ile doğrulanmadı.

**Etki:** Canlı skor motoru, kanıtlanmamış faktörlerin etkisini taşıyor olabilir. Bu, "çalışan sistem ≠ doküman" çelişkisinin en yüksek riskli örneği.

**Kanıt:** `.env` (okundu) vs decision-log girdileri (2026-08-12/14) + score_engine.py:155-180 (flag-kapılı faktörler).

### 🟡 MEDIUM — Çift academy DB

Finsense'de 96 ders, Borsa'da 0. Hangi DB "gerçek" belirsiz. Export köprüsü Finsense'den Borsa'ya manuel.

### 🟡 MEDIUM — localhost vs 127.0.0.1

Web `127.0.0.1:3001`'de 200 OK, `localhost:3001` timeout. DNS/IPv6 ayrımı; kullanıcı etkisi düşük ama tutarsız.

### 🟢 LOW — c2c_5d ρ=0,845 → 0,98

Eski ölçüm 0,845'ti; yeni EOD-only ölçüm 0,9829. Çelişki çözüldü (intraday karışıklığı) — artık çelişki değil, kapalı.

---

## PART K — DECISION HISTORY (önemli kararlar)

| Karar | Tarih | Neden | Hâlâ geçerli? |
|---|---|---|---|
| Tahmin → Attention map pivot | 2026-08-14 | Yön 8 yoldan kapandı | ✅ Evet (Level B, onay bekliyor) |
| Locked OOS NOT_OPENED | sürekli | Veri/execution kapıları açılmadı | ✅ Evet |
| c2c_5d EOD-only filtre | 2026-09-03 | İntraday karışıklığı kök neden | ✅ Evet (Level B fix uygulandı) |
| Catalyst pipeline onarımı | 2026-09-03 | catalyst_factor=0.0 kök neden | ⚠️ Kısmen (cache geriledi) |
| Fade = CONFIRMATORY_CANDIDATE | 2026-09-03 | %59,9 brüt ama maliyette negatif | ✅ Evet (3 koşul) |

---

## PART L — CURRENT vs TARGET STATE

| Alan | Bugün | Hedef | Eksik |
|---|---|---|---|
| Sinyal | Çalışan tarama + yayın | Attention map production | Feature flag + schema v3 + shadow |
| Doğrulama | Araştırma kanıtları | Locked OOS | P1/P2 kapıları |
| FinSense | 8 yayında ders | 69 modül canlı | Scheduler + export köprüsü + toplu üretim |
| Veri | yfinance+EODHD+EDGAR | tick/L2/execution truth | Seviye 2-3 veri katmanları |
| Otonomi | İnsan-kapılı | Kademeli otonomi | GO/NO-GO kanıtı |

---

## PART M — KEEP / CHANGE / FREEZE / KILL / TEST

| Parça | Karar | Neden |
|---|---|---|
| Yayın zinciri | **KEEP** | Doğrulanmış, çalışıyor |
| Scanner/evaluate | **KEEP** | 136-alan sözleşme tutarlı |
| Yön tahmini | **KILL** | 8 yol kapandı; tekrar deneme |
| entry_ok | **KILL** | Adverse selection kanıtlı |
| Attention map | **TEST** | Araştırma kanıtlı; production'a shadow koşu gerek |
| Fade | **TEST** | 3 koşul: geniş cache + maliyet + pre-registered OOS |
| TimesFM | **TEST** | Önce EOD-only backtest |
| FinSense döngüsü | **CHANGE** | Scheduler + export köprüsü + çift DB çözümü |
| Catalyst flag | **CHANGE** | Cache geriledi; yeniden doldur + flag ayrı Level B |
| Feature flag'ler (genel) | **CHANGE** | Açık ama doğrulanmamış — component ablation şart |
| Akademi scheduler | **TEST** | Çalıştığını kanıtla (log/health) |

---

## PART N — CRITICAL UNKNOWNS

1. Akademi scheduler gerçekten çalışıyor mu? (hiç log kanıtı yok)
2. Catalyst cache'i hangi işlem ezdi? (regresyon kök nedeni)
3. localhost vs 127.0.0.1 ayrımının kök nedeni
4. Feature flag'ler açıkken canlı skor ne kadar sapıyor? (ölçülmedi)
5. 88 draft dersin kalite dağılımı (quality_guard hiç koşmadı)

---

## PART O — PRIORITY ANALYSIS

| İş | Etki | Kanıt | Bağımlılık | Risk azaltma | Öncelik |
|---|---|---|---|---|---|
| Feature flag çelişkisini çöz | Yüksek | Var | Canlı skor bütünlüğü | Yüksek | **1** |
| FinSense scheduler'ı doğrula + bağla | Yüksek | Var (kod) | 69 modül üretimi | Orta | **2** |
| Catalyst cache yeniden doldur | Orta | Var | EDGAR hattı | Orta | **3** |
| Attention map shadow koşu | Yüksek | Güçlü | Production geçiş | Yüksek | **4** |
| Fade confirmatory | Orta | Koşullu | Yeni veri | Orta | **5** |

---

## PART P — ANTI-ROADMAP (şimdi YAPMAYACAĞIZ)

1. **Yön tahminini tekrar deneme** — 8 yol kapandı
2. **Yeni TP/SL grid taraması** — 3.120 konfigürasyonda kanıt yok
3. **entry_ok'ı gevşetme** — adverse selection kanıtlı
4. **Canlı sermaye artırma** — locked OOS açılmadı
5. **Feature flag'leri doğrulamadan açık bırakma** — component ablation şart
6. **Yeni ajan ekleme** — 23 ajan var, koordinasyon ölçülmedi

---

## PART Q — MASTER WORK PLAN

### NEXT (hemen, ≤7 madde)
1. **Feature flag çelişkisini çöz:** `.env`'deki 9 açık flag'i decision-log'la uzlaştır — ya kapat ya component-ablation kanıtı üret
2. **FinSense scheduler kanıtı:** akademi scheduler'ının çalıştığını log/health ile doğrula
3. **Catalyst cache yeniden doldur** + regresyon kök nedenini bul
4. **Çift academy DB kararı:** hangisi gerçek — Finsense mi Borsa mı?
5. **88 draft dersi quality_guard'dan geçir** (toplu denetim)

### NEXT PHASE
6. Attention map shadow koşu (feature flag arkasında, production'a yazmadan)
7. Export köprüsünü otomatikleştir (ders APPROVED → export → publish_web)

### LATER
8. Fade confirmatory (yeni veri + maliyet + OOS)
9. TimesFM EOD-only backtest
10. Self-improving code loop (ayrı proje)

---

## PART R — GO / NO-GO GATES

| Kapı | Gerekli kanıt | GO koşulu | NO-GO koşulu |
|---|---|---|---|
| Attention map → production | Shadow vs live karşılaştırma | Shadow çıktısı canlıyla tutarlı + matched-control | Tutarsızlık veya negatif kontrol |
| Canlı sermaye | Pozitif net expectancy + OOS + drawdown + rejim istikrarı + paper/live tutarlılık | Hepsi geçti | Herhangi biri başarısız → ek sermaye yok |
| Fade → kural | Geniş cache + maliyet modeli + pre-registered OOS | Yeni dönemde pozitif gün >%55 + maliyetli mean >0 | Pozitif gün <%55 veya maliyetli mean ≤0 |

---

## PART S — ONE-PAGE PROJECT STATE

```
FINPILOT / FINSENSE — PROJECT STATE
Tarih: 2026-09-08

BUGÜN: Çalışan araştırma+dağıtım sistemi; 128-endpoint API, web, günlük tarama, yayın zinciri.

ÇALIŞAN ÇEKİRDEK: scanner → export → gate → snapshot → Telegram → web → git. Auth. Ollama. EDGAR.

DOĞRULANANLAR: Redis onarım, prepublish gate, admin auth, c2c_5d teşhisi, attention map (research).

DONDURULANLAR: DRL, locked OOS, yön tahmini (8 yol kapandı).

BAŞARISIZLAR: entry_ok, High-RVOL, statik skor, 3.120 TP/SL grid.

KRİTİK BİLİNMEYENLER: akademi scheduler çalışıyor mu; catalyst cache'i ne ezdi; flag'ler açıkken skor sapması.

EN ÖNEMLİ 5 BULGU:
1. Tüm 9 feature flag açık ama hiçbiri doğrulanmadı (CRITICAL çelişki)
2. Yön tahmini 8 bağımsız yoldan kapandı — attention map tek canlı çerçeve
3. MFE %4,83 vs captured +%0,37 — çıkış mimarisi en büyük fırsat
4. FinSense: 96 ders var ama 88'i draft'ta takılı; döngü kapalı değil
5. Çift academy DB — Finsense 96 ders, Borsa 0

EN ÖNEMLİ 5 RİSK:
1. Doğrulanmamış faktörler canlı skoru etkiliyor olabilir
2. Catalyst cache regresyonu (veri kaybı)
3. Akademi scheduler kanıtlanmamış
4. Locked OOS açılmadan canlı sermaye yok
5. 88 draft dersin kalitesi bilinmiyor

ŞİMDİ YAPILACAK 5 İŞ:
1. Feature flag çelişkisini çöz (kapat veya ablation kanıtı)
2. FinSense scheduler'ı doğrula
3. Catalyst cache yeniden doldur + kök neden
4. Çift DB kararı
5. 88 draft'ı quality_guard'dan geçir

ŞİMDİ YAPILMAYACAKLAR:
1. Yön tahminini tekrar deneme
2. Yeni TP/SL grid taraması
3. Canlı sermaye artırma

SONRAKİ GO/NO-GO: Attention map shadow koşu sonucu.
```

---

## PART T — FINAL VERDICT

1. **FinPilot bugün gerçekte nedir?** Çalışan, ölçülmüş, yayın yapan bir piyasa araştırma ve dağıtım sistemi — henüz kanıtlanmış bir trading şirketi değil.
2. **FinSense bugün gerçekte nedir?** 96 ders üretmiş ama %92'si draft'ta takılı, döngüsü kapalı olmayan bir içerik altyapısı.
3. **En değerli çalışan çekirdek?** Yayın zinciri (export→gate→snapshot→Telegram→web→git) — doğrulanmış, tekrarlanabilir, denetlenebilir.
4. **En güçlü doğrulanmış bulgu?** Attention map: olağandışı hisseler ölçülebilir biçimde daha büyük hareket ediyor (yön değil, büyüklük).
5. **En önemli başarısızlık?** Yön tahmini — 8 bağımsız yoldan kapandı; bu bilgi kaybedilmemeli.
6. **En büyük bilinmeyen?** Akademi scheduler çalışıyor mu + feature flag'ler açıkken canlı skor ne kadar sapıyor.
7. **En büyük teknik risk?** Feature flag çelişkisi — doğrulanmamış faktörler canlı skoru etkiliyor olabilir.
8. **En büyük araştırma riski?** Quasi-OOS — deney ailesi aynı dataset'i paylaşıyor; locked OOS hiç açılmadı.
9. **En büyük ürün riski?** FinSense döngüsü kapalı değil — 88 ders draft'ta, web'e tek ders ulaştı.
10. **Hangi iş diğerlerinin önünü açar?** Feature flag çelişkisini çözmek — canlı skorun bütünlüğü her şeyin temeli.
11. **Hangi işler yapılmamalı?** Yön tahmini tekrar, TP/SL grid, canlı sermaye artırma, yeni ajan ekleme.
12. **Sonraki seviyeye geçmek için kritik kanıt?** Attention map'in shadow koşuda canlıyla tutarlı çıkması + locked OOS kapılarının açılması.

---

## Governance

- Bu denetim salt-okunur; hiçbir kod/config/veri/flag değiştirilmedi.
- Locked OOS NOT_OPENED.
- Tüm bulgular gerçeklik hiyerarşisine dayanır: çalışan kod/sistem önce, sonra veri, sonra test, sonra doküman.
- Çelişkiler gizlenmedi — Part J'de sınıflandırıldı.
