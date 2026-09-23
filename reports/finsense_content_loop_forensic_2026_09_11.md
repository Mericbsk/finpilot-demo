# C1 — FinSense Content Loop: Read-Only End-to-End Forensic Audit

**Tarih:** 2026-09-11 · **Level:** A (salt-okunur; hiçbir kod/config/DB/içerik değiştirilmedi, yeni içerik üretilmedi, scheduler başlatılmadı)
**Yöntem:** kod + config + DB (read-only `mode=ro`) + agent_logs + artifact incelemesi. Runtime proof > code existence.

---

## C1 EXECUTIVE VERDICT

```
STATUS:              BROKEN-LOOP (operational, not architectural)
FIRST_BROKEN_POINT:  REVISION_NEEDED → (updater → recheck → publish) "convergence" aşaması
ROOT_CAUSE:          Quality bar mevcut içerik kalıbının üzerinde + auto-revise convergence
                     üretemiyor; 100 ders draft'ta takılı, export yalnızca "published"ı alıyor
                     (publish olmadığı için web'de 1 ders).
CONFIDENCE:          HIGH (DB + 2712 agent_logs + timestamp kanıtıyla)
```

**Önceki varsayım düzeltmesi:** "Scheduler hiç çalışmıyor / içerik üretilmiyor" **YANLIŞTI.** Kanıt: quality_guard **2.679 kez** koşmuş (en son **bugün 2026-09-11 12:47**). Loop **çalışıyor** — ama **yayın üretmiyor.**

**Boyut analizi (§11b):** 100 draft'ın **%48'i "içerik çok kısa" (<200 kelime)**, %45'i heuristiği geçip LLM-skorunda takılıyor (avg 5–7,5; APPROVED için 7,5 gerekli). Updater **52 gündür pasif** (son 2026-07-21), 8 ders üzerinde koşmuş, v1.1 üretse de persist edilen dersler v1.0 kalıyor. **Kök neden: üretim kalıbı (kısa içerik) + updater pasifliği — Guard kalibrasyonu değil.**

---

## 1. Architecture Map

**İki ayrı codebase + iki ayrı DB (kritik bulgu):**

| Component | Borsa | Finsense |
|---|---|---|
| `academy/` paketi | ✅ VAR (`C:\Users\meric\Borsa\academy\`) | ✅ VAR (`C:\Users\meric\Finsense\academy\`) |
| academy.db | **0 ders (BOŞ)** | **109 ders (100 draft / 9 published)** |
| agent_logs | 0 | **2.712** |
| content_jobs | 0 | 86 (17 done / 12 failed / 56 pending / 1 running) |
| corpus_chunks | — | 28 |

Borsa `api/main.py:224` `from academy.scheduler import start_academy_scheduler` → **`C:\Users\meric\Borsa\academy\scheduler.py`'ye** resolve oluyor (Borsa'nın kendi kopyası) — ve **Borsa'nın boş DB'sine** yazıyor. Finsense'deki asıl içerik (109 ders) Finsense process'inden.

## 2. Six-Link Status

| Link | Status | Evidence |
|---|---|---|
| Generate | 🟢 PROVEN | content_generator 15 log; 109 ders üretilmiş |
| Quality Guard | 🟢 PROVEN | 2.679 log; ama **%92 REVISION_NEEDED / %7 REJECTED / %0,4 APPROVED** |
| Update (revise) | 🟡 PARTIAL | `_maybe_revise` kodu tam (orchestrator:236), updater 8 kez koşmuş ama v1.0'a dönüyor (aşağı) |
| Publish DB | 🔴 FAIL | 100 ders draft'ta kalıyor; yalnızca 9 published |
| Web Export | 🔴 FAIL | `academy_lessons.json` count=1, status_filter=published, generated 2026-07-21 (eski) |
| Scheduler | 🟢 PROVEN-RUNNING | agent_logs bugün aktif (2026-09-11 12:47); ama publish üretmiyor |

## 3. 109-Lesson Forensics (Finsense DB)

- Toplam: **109** (100 draft, 9 published) — *not: önceki raporlar "96/88" diyordu; sistem o zamandan beri üretmeye devam etmiş.*
- Tüm draft'lar version=**1.0** (hiçbiri v1.1'e terfi etmemiş — updater yeni versiyon üretse de persist edilen ders v1.0 kalıyor).
- 100 draft'tan **97'si** `updated_at > created_at` (tekrar dokunulmuş — guard yeniden koşmuş) ama hâlâ draft.

## 4. Draft Root-Cause Matrix (100 draft)

| Root Cause | Count | Evidence |
|---|---|---|
| Guard REVISION_NEEDED verdi, auto-revise converge edemedi | ~çoğu | 2.472 REVISION_NEEDED kararı |
| Guard REJECTED | bir kısmı | 197 REJECTED |
| APPROVED ama publish olmamış | ~0 | yalnızca 11 APPROVED toplam |
| Hiç guard görmemiş | az | pending jobs 56 |
| **Toplam** | 100 draft | ✓ |

**Baskın kök neden:** REVISION_NEEDED (2.472) — guard dersleri geçirmiyor ve auto-revise döngüsü APPROVED'a converge edemiyor.

## 5. Quality Guard Trace (kanıtlı)

- **Caller:** `orchestrator.run_daily()` → `quality_guard.review_pending_lessons()` (orchestrator.py:77). PROVEN.
- **Kararlar:** REVISION_NEEDED %92 (2.472) · REJECTED %7 (197) · APPROVED %0,4 (11). Örnek avg skorlar 5,3–7,5.
- **Persist:** karar `agent_logs.output_summary`'ye yazılıyor; ama `lessons.status` "draft"ta kalıyor (APPROVED olmadıkça publish yok).
- **APPROVED → published:** var (orchestrator:84-87) ama neredeyse hiç tetiklenmiyor (11 APPROVED).
- **REVISION → updater → recheck:** `_maybe_revise` (orchestrator:236) zinciri **kodda tam** — `updater.update_lesson` → `quality_guard.review_lesson`. Ama sonuç: ders hâlâ v1.0 draft.

**Bulgu:** Zincir kırık değil — **convergence yok.** Guard sürekli REVISION diyor; updater'ın düzeltmesi guard'ı APPROVED'a ikna edemiyor.

## 6. Scheduler Trace (kanıtlı)

| Aşama | Durum | Evidence |
|---|---|---|
| Config (ACADEMY_AUTOSTART_SCHEDULER) | PROVEN | api/main.py:224, default "1" |
| scheduler.start() / job registration | PROVEN | Finsense process agent_logs üretiyor |
| job trigger → execution | PROVEN | quality_guard 2.679 kez, bugün dahil |
| execution log → DB change | PROVEN | agent_logs + draft updated_at bugün |

`SCHEDULER_STATUS = PROVEN_RUNNING` — ama **publish üretmiyor** (Guard konvergence sorunu).

## 7. Two-Database Analysis

- **Borsa academy.db:** 0 ders — Borsa'nın kendi `academy/` paketi boş DB'ye yazıyor. **Kullanılmıyor.**
- **Finsense academy.db:** 109 ders + 2.712 log + corpus — **gerçek içerik burada.**

**Source-of-truth:** `FINSENSE_DB` (kanıtlı). Borsa'nınki **orphaned duplicate** (aynı şema, 0 veri). **DUPLICATED_SOURCE_OF_TRUTH riski VAR** — iki `academy/` paketi + iki DB; Borsa'nın kopyası hiçbir şey üretmiyor ama varlığı karışıklık yaratıyor.

## 8. Export/Web Pipeline

```
Finsense DB (9 published)
  → export_lessons.py --status published
  → academy_lessons.json (count=1, 2026-07-21)   ← ESKİ, 1 published olduğu tarihten
  → Borsa web/public → publish_web.py → git → Vercel
```
- `EXPORT EXISTS ≠ EXPORT AUTOMATIC`: export komutu var ama **manuel**; 2026-07-21'den beri çalıştırılmamış (o tarihte 1 published vardı).
- `PUBLISH SCRIPT EXISTS ≠ PIPELINE RUNS`: publish_web var ama export güncel olmadığı için web'de **1 ders** görünüyor.

## 9. First Broken Point

```
GENERATED        ✓ (109 ders)
QUALITY_CHECK    ✓ (2.679 guard run)
APPROVED         ✗ ← İLK KIRIK: guard neredeyse hiç APPROVED vermiyor
PUBLISHED        ✗ (buna bağlı)
EXPORTED         ✗ (publish olmadığı için 1 ders)
WEB              ✗ (buna bağlı)
```

**İlk kırılan nokta: APPROVED transition** — Guard'ın kalite barı mevcut content kalıbının ürettiği çıktının üzerinde; auto-revise bu farkı kapatamıyor.

## 10. Root Cause Classification

| Sınıf | Severity | Evidence | First broken |
|---|---|---|---|
| B — QUALITY FAILURE (bar/çıktı uyumsuzluğu) | **CRITICAL** | %92 REVISION, %0,4 APPROVED | APPROVED transition |
| F — DATA ARCHITECTURE FAILURE (çift DB/paket) | HIGH | Borsa DB=0, Finsense=109 | source-of-truth karışıklığı |
| G — EXPORT FAILURE (manuel + eski) | MEDIUM | json count=1, 2026-07-21 | export tetiklenmiyor |
| E — SCHEDULER FAILURE | **YOK (refuted)** | scheduler PROVEN-RUNNING | — |
| A — GENERATION FAILURE | YOK (refuted) | 109 ders üretilmiş | — |

## 11. Minimal Repair Plan (önce bunlar)

1. **(A) Guard kalibrasyon kanıtı:** 2.472 REVISION'ın *hangi 7-boyut kriterinde* takıldığını say (avg skorlar 5-7 arası → hangi boyut düşük?). Bu Level A, read-only.
2. **(A) Auto-revise convergence ölçümü:** `_maybe_revise` sonrası guard'ın yeniden APPROVED oranını ölç (şu an ~0 görünüyor). Neden converge etmediğini belirle (updater çıktısı v1.0'da mı kalıyor?).
3. **(A) Tek source-of-truth kararı:** Borsa `academy/`+DB orphaned → Finsense'i tek otorite ilan et (veya Borsa'yı). Bu bir karar, kod değil.

## 11b. Guard Boyut + Convergence Ölçümü (2026-09-11, read-only kanıt — DOLDU)

**Guard karar mantığı (quality_guard.py:48-50, 91-92):** `APPROVED = avg≥7,5 VE hiçbir boyut <5 değil`. `REVISION_NEEDED = avg 5-7,5 VEYA tek boyut <5`. `REJECTED = avg<5 VEYA 2+ boyut <5`. Ayrıca **heuristic_checks** (144): herhangi bir `issue` varsa → otomatik REVISION_NEEDED (LLM skoru ne olursa olsun).

**100 draft'ın heuristic kriter analizi (read-only ölçüm):**

| Heuristic kriter (quality_guard._heuristic_checks) | Takılan draft | Oran |
|---|---|---|
| `short_content` (içerik < 200 kelime) | **48** | **%48** |
| `few_takeaways` (kilit çıkarım < 2) | 10 | %10 |
| `no_real_example` (gerçek örnek yok) | 10 | %10 |
| `quiz<1` veya `flashcard<2` | 8 | %8 |
| **Hiçbiri (heuristic PASS)** | **45** | **%45** |

**İki baskın bulgu:**
1. **%48'i `short_content`** — en büyük tek kriter. İçerik kalıbı 200 kelimenin altında üretiyor. Bu bir **template/üretim** sorunu, Guard kalibrasyonu değil (bar makul; içerik kısa).
2. **%45'i heuristic'i GEÇİYOR** — ama yine de draft. Demek ki bunlar **LLM-skor tarafında** REVISION alıyor (avg 5-7,5 bandında, APPROVED için 7,5 gerekli). Bu **kalibrasyon + içerik derinliği** kesişimi.

**Auto-revise convergence (kanıt):**
- `content_updater` **sadece 8 distinct ders** üzerinde koşmuş, en son **2026-07-21** (52 gün önce).
- Updater v1.1 üretiyor ama **persist edilen dersler v1.0 kalıyor** (100/100 draft version=1.0).
- Toplam **11 APPROVED** (2.679 guard run'ında) → auto-revise **convergence ≈ %0,4**.

**Kök neden (convergence):** İki katmanlı —
(a) **Updater pasif:** 52 gündür hiç koşmamış; `_maybe_revise` tetiklenmiyor veya REVISION dersleri updater'a ulaşmıyor (56 job pending'de bekliyor, `run_daily` işlemiyor olabilir).
(b) **Convergence yok:** updater koşsa bile çıktı v1.0'a geri dönüyor / guard yeniden REVISION veriyor. İçerik kalıbı kısa olduğu için tek düzeltme 200-kelime barını aşamıyor.

**Net:** Sorun Guard'da değil — **üretim kalıbında (kısa içerik %48) + updater'ın pasif/etkisizliğinde.** Bu "barı gevşet" değil, "kalıbı zenginleştir + updater'ı çalışır kıl" sonucunu destekler.

## 12. Architectural Improvement (sonra, minimal repair'dan SONRA)

- Export+publish'i orchestrator publish adımına bağla (Level B).
- 88→100 draft backlog'unu Guard kalibrasyonu sonrası toplu işle.

## 13. Verification Plan

- Repair sonrası: bir draft ders Guard'dan APPROVED alıp published → export → web'de görünene kadar izlenebilir olmalı (end-to-end proof).

## 14. What Must NOT Be Changed Yet

- Guard'ın 7-boyut kriterlerini **gevşetme** (bu kaliteyi düşürür — Level B/C karar, önce kanıt).
- Borsa/Finsense DB'lerini birleştirme (Level B).
- Yeni framework/queue/DB/refactor YOK.

## 15. C1 — GO / BLOCKED / NO-GO

```
GO
```
Root cause yeterince kanıtlandı (scheduler çalışıyor; sorun Guard konvergence'ında). Minimal repair açık (Guard kalibrasyon kanıtı + auto-revise convergence ölçümü + source-of-truth kararı). Doğrulama yöntemi açık (end-to-end draft→published→web).

**Bir sonraki adım (Level A, read-only):** Guard'ın hangi kalite boyutunda takıldığını ve auto-revise'in neden converge etmediğini ölçmek. İsterseniz onu yapayım.
