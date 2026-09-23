# C1 — Level B Implementation Gate: Guard Decision Layer

**Tarih:** 2026-09-14 · **Gate:** Level B Implementation · **Kapsam:** YALNIZCA `quality_guard.py` karar katmanı
**Freeze edilen kontrat:** `reports/c1_guard_contract_specification_2026_09_14.md` (B5-kalibreli)
**Kesinlikle dokunulmadı:** DB schema/data, 120 lesson, test card, generator/R3, updater/R1, scheduler, LLM scoring kriterleri, lesson content, publish/export, bulk.

> **Governance kuralı (Meriç):** Bu gate'in PASS'i Guard'ın "doğru" olduğunu kanıtlamaz — yalnızca freeze edilen kontratın kodda **doğru uygulandığını** kanıtlar.

---

## Değişiklik (yalnızca decision layer)

`Finsense/academy/agents/quality_guard.py`:

1. **`_lesson_format(lesson)`** (yeni, :224) — lesson format'ını `module` alanından ("… · card") güvenilir türetir; legacy'de id-suffix fallback; bilinmeyen → `guide` (muhafazakar tam-ders kuralı).
2. **`_FORMAT_MIN_WORDS`** (:101) — `{guide:200, coded:200, compare:200}` (initial, **empirically optimal DEĞİL**); card/checklist eşiksiz (B5: card median=63w).
3. **`_heuristic_checks`** (:240) — 200-kelime tabanı artık yalnızca tam-ders formatlarında. `few_takeaways` TBD/non-blocking kaldı.
4. **Decision merge** (:160-171) — LLM APPROVED artık gerekli-formattaki gating issue'ları **yutamaz** (`APPROVED → REVISION_NEEDED` demote). `3+ issue → REJECTED` değişmedi. `no_source_when_rag` (CRITICAL) gating set'inde.

**Guard invariants değişmedi:** `MIN_APPROVE_SCORE=7.5`, `MIN_DIMENSION_SCORE=5.0` (line 91-92), 7-boyut LLM scoring, heuristic kural metinleri. AST OK.

---

## Gate çıkış kriterleri

### L1 — Static/code verification: **PASS**
AST parse OK; invariants (7.5/5.0) intact; merge markers (`_lesson_format`, `_FORMAT_MIN_WORDS`, `_GATING_PREFIXES`, demote kuralı) mevcut. Kontrat ↔ kod eşleşiyor.

### L2 — Read-only historical replay: **PASS**
Yeni format-aware heuristic, 120 derse DB yazmadan uygulandı (word-count bazlı):
```
card       short=0/24   (eşik yok — doğru)
checklist  short=0/23   (eşik yok — doğru)
coded      short=8/23   ← format floor doğru çalışıyor
compare    short=8/23   ← doğru
guide      short=9/28   ← doğru
```
B5 tahminiyle birebir. Card/checklist false-positive'leri kaldırıldı; tam-ders floor korundu.

### L3 — Regression check: **PASS (tek kasıtlı değişiklik)**
10 published ders, OLD vs NEW heuristic issue-count:
- 9/10 **SAME** (değişiklik yok)
- 1/10 **CHANGED**: test card 2→1 (`short_content` format-aware kaldırıldı — **kasıtlı contract değişikliği**, beklenen)
Kontrat dışı değişiklik yok.

### L4 — Single E2E: **PASS**
Test card (`-card`, 89 kelime, 1 takeaway) yeni Guard altında, **persistence disabled**:
```
ÖNCEKI (anomali):  2 heuristic issue + LLM 8.25 → APPROVED
YENİ:              gating issue (takeaway hariç — TBD) değerlendirildi
                   → REVISION_NEEDED (avg 7.71)
DB:                DEĞİŞMEDI (published, 1.0 — read-only save no-op)
```
C1-GUARD-001 anomali davranışı düzeltildi (LLM APPROVED artık gating issue'yu yutmuyor) — **üstelik DB'ye yazmadan.**

### L5 — Gate decision

```
LEVEL B IMPLEMENTATION GATE = PASS
```
Freeze edilen kontrat kodda doğru uygulandı. **Bu PASS, Guard'ın kaliteyi iyileştirdiğini kanıtlamaz** (o iddia sonraki replay/E2E'nin konusu).

---

## C1-GUARD-001 durumu

`OPEN / IMPLEMENTATION_PENDING` → **`OPEN / IMPLEMENTED_AWAITING_VALIDATION`**
(Contract uygulandı; "Guard gerçekten kaliteyi iyileştiriyor mu" sorusu hâlâ açık — ayrı validation.)

## Sonraki adım (kilitli sıra)

```
Contract freeze → Implementation Gate (ŞU AN, PASS) → Guard replay (DB'ye yazan, onaylı)
→ E2E → R3 generator optimization
```
**R3 hâlâ HOLD** — generator, Guard'ın eski kusurlu davranışına göre optimize EDİLMEDİ.

## Notlar / sınırlar
- Finsense bir git repo DEĞİL → değişiklikler git-diff ile izlenemiyor (yedek/geri-alma için dosya kopyası önerilir).
- Test card published kalıyor (LEAVE AS-IS, anomaly-flagged) — bu gate ona dokunmadı.
- `few_takeaways` TBD — blocking değil; ayrı kanıt/kalibrasyon gerekir.

## Governance
- Level B; yalnızca Guard decision layer değişti. DB/lesson/generator/updater/scheduler/LLM-criteria/publish/bulk değişmedi.
- Hiçbir production rollout yapılmadı; sonraki Guard replay (DB yazan) ayrı onay gerektirir.
