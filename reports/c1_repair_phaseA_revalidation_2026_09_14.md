# C1 Level B Repair — PHASE A: Current-State Revalidation

**Tarih:** 2026-09-14 · **Level:** B (Phase A = read-only; hiçbir değişiklik yapılmadı)
**Girdi:** C1 forensic (2026-09-11) + B master prompt (2026-09-14)
**Sonuç:** `B-REPAIR-0 = PASS` (mimari + bulgular bugünkü repo'da doğrulandı)

---

## A. Bugünkü durum (2026-09-14, doğrulandı)

- Finsense DB: **118 ders** (108 draft / 10 published) — sistem üretmeye devam ediyor (09-11'de 109'du)
- Guard **aktif**: bugün 56 run (son 2026-09-14 11:00), kararlar hâlâ REVISION_NEEDED ağırlıklı (avg 4,5–8,0)
- content_updater: **sadece 2026-06-26 ve 2026-07-21** aktif; o günden beri **sıfır**
- Tüm 118 ders **version=1.0** (hiç v1.1 persist edilmemiş)
- 56 pending job **tamamı content_generator** (0 tanesi content_updater)
- Ollama **çalışıyor** (200 OK, qwen2.5:7b + 16 model)

## B. COMPONENT MAP (doğrulanmış execution path)

```
scheduler.start_academy_scheduler()         [Finsense/academy/scheduler.py:22]
  → orch.run_daily  (CronTrigger 02:00 ET)  [scheduler.py:36]
      → orchestrator.run_daily()            [orchestrator.py:63]
          → gap_detector.run_daily_scan()
          → _process_pending_jobs(max_jobs=5)   [orchestrator.py:256]  (SADECE content_generator/content_updater job'ları)
          → quality_guard.review_pending_lessons()  [quality_guard.py:184 → SELECT id WHERE status='draft']
              → review_lesson (her draft)     [quality_guard.py:111 → status persist 152-161]
          → her REVISION_NEEDED → _maybe_revise   [orchestrator.py:80-83]
              → updater.update_lesson(lesson, notes)  [orchestrator.py:251 → content_updater.py:70]
                  → get_academy_provider() → llm None? return None : LLM → persist v1.1  [content_updater.py:71-122]
              → if updated: quality_guard.review_lesson(updated)  (RECHECK, revised üzerinde)  [orchestrator.py:253]
```

## C. P0/P1 kök neden (kod kanıtı)

### P0-1: Updater neden pasif? — Üç bileşik neden
1. **LLM bağımlılığı:** `update_lesson` LLM None → `return None` (sessiz skip). content_updater:71-78.
2. **En son 07-21:** o tarihten beri updater hiçbir log üretmedi. run_daily→_maybe_revise zinciri var ama updater hiç persist etmedi.
3. **Guard→draft döngüsü:** Guard `updated_at`'i her REVISION'da bump ediyor (quality_guard.py:160) ama status draft kalıyor → "revised ama draft" yanılsaması.

### P0-2: Version persistence — **KOD DOĞRU, kanıt YOK**
- `LessonRepository.save` (models.py:256-300) ON CONFLICT `version=excluded.version` yazar → **doğru**.
- **Ama** tüm 118 ders v1.0 ve updater-touched 8 ders `lessons`'ta **bulunamıyor** (id'ler eski seed formatından, mevcut DB'de yok). Yani v1.1'in persist edildiğine dair **mevcut DB'de kanıt yok**. `v1.0 → persist → v1.1` zinciri **kod-doğru ama runtime-doğrulanmamış**.

### P0-3: Recheck doğru
- `_maybe_revise` revise edilen `updated` lesson üzerinde `review_lesson` çağırıyor → recheck **doğru** (eski v1.0 değil).

### P1: Generator output contract — **LLM talimatı takip etmiyor**
- Şablon "~250-450 kelime" diyor (content_generator.py:66) ama **%48 <200 kelime** üretiliyor.
- Şablon quiz≥1/flashcard≥2/takeaways≥3 istiyor ama Guard'ın ≥2 takeaway / 200-kelime barını karşılamıyor.
- **Generator'da üretim-sonrası self-check / min-length enforcement YOK** — LLM çıktısı neyse o persist ediliyor.

## D. Guard invariants (DEĞİŞMEYECEK — doğrulandı)
`MIN_APPROVE_SCORE=7.5`, `MIN_DIMENSION_SCORE=5.0`, heuristic_checks (200 kelime, ≥2 takeaway, quiz≥1, flashcard≥2, real_example), 7-boyut scoring. **Hiçbiri değiştirilmeyecek.**

## E. Phase A verdict

```
B-REPAIR-0 = PASS
```
Mimari doğrulandı; bulgular bugünkü repo'da geçerli; kök nedenler kod-kanıtlı. Phase B'ye geçilebilir.

## F. Repair hedefleri (Phase B — onaylandı, şimdi uygulanıyor)

- **R1 (P0) Updater execution:** LLM-None sessiz skip'i loglanır/görünür kıl; updater'ın gerçekten koştuğundan emin ol. Yeni framework YOK.
- **R2 (P0) Version persist E2E kanıtı:** v1.0→v1.1'in DB'ye yazdığını tek derste kanıtla.
- **R3 (P1) Generator output contract:** Şablona **üretim-sonrası self-check** ekle (persist öncesi <200 kelime / <2 takeaway / quiz/flashcard eksikse düzelt/yeniden dene). Guard'a dokunma.
- **R4 (E2E):** Tek representative draft üzerinde draft→revise→persist(v1.1)→recheck→approve→publish→export.
