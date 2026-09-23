# FinSense — Guard Contract Specification (C1-GUARD-001 Resolution)

**Tarih:** 2026-09-14 · **Durum:** C1-GUARD-001 STATUS=OPEN / SUBSTATUS=**IMPLEMENTATION_PENDING** — B5 GO (Meriç). Contract FREEZE; Guard kodu HENÜZ değiştirilmez (ayrı Level B Implementation Gate)
**Karar:** **C — iki katmanlı kalite politikası.** B5 replay sonrası REVISE-LIGHT uygulandı. Mevcut kod davranışı "doğru" ilan EDİLMEDİ.
**Kapsam:** Bu bir **specification** dokümanıdır (contract freeze). Guard/DB/120-draft'ta değişiklik YOK. Uygulama ayrı Level B gate'tir.

> Temel prensip (Meriç): **"Heuristic = structural/format gate; LLM = content-quality gate. İkisi birbirinin yerine geçmez."** Severity (ne kadar ciddi) ile gate behavior (APPROVED'ı engeller mi) **ayrı eksenlerdir**. Ve **"200 makul" ≠ "200 empirically optimal"** — B5 format-ayrımını destekler ama 200'ün optimum olduğunu kanıtlamaz.

---

## B0 — Lesson Taxonomy (koddan doğrulandı)

`agent_logs`/`lessons.id` suffix + `lesson_components.type`'tan türetildi. **Not:** `Lesson` modelinde ayrı bir `lesson_type` alanı YOK — tür `id` suffix'inden çıkarılıyor (bu bir **contract gap**; aşağıya bak).

| Tür (suffix) | Sayı | Doğası | Önerilen minimum profil |
|---|---:|---|---|
| `guide` | 24 | Kapsamlı açıklayıcı ders | derinlik + takeaway + örnek + quiz |
| `coded` | 23 | Uygulamalı/hesaplamalı ders | mekanizma + hesap + örnek + quiz |
| `compare` | 23 | Karşılaştırma | iki taraf + takeaway + örnek |
| `card` | 24 | Kısa özet kart | **daha kısa metin kabul edilebilir** + takeaway |
| `checklist` | 22 | Kontrol listesi | yapı (madde listesi) + örnek |
| `dersi` / diğer | 4 | Legacy/seed | genel ders |
| (component) `quiz` | 137 | Değerlendirme sorusu | kavram-anlama ölçer, ezber değil |
| (component) `flashcard` | 250 | Hafıza kartı | kısa, net, birbirinin kopyası değil |
| (component) `source` | 290 | RAG atfı | doğruluk izi |

**Contract gap:** `lesson_type` persisted alan olarak yok. Tür'ü id-suffix'inden çıkarmak kırılgan. **Öneri (uygulama gate'inde):** Guard'a format-aware karar verebilmesi için lesson type'ı belirleyen güvenilir bir yol gerekir (id-suffix parse veya yeni alan — bu bir schema kararı, ayrı onay).

## B1 — Heuristic Classification (SEVERITY + GATE POLICY — ayrı)

Mevcut `_heuristic_checks` (quality_guard.py:204-215) 5 kontrol. **İki ayrı kavram:** severity (problemin ciddiyeti) ≠ gate behavior (APPROVED'ı engeller mi). "Soft ama blocking" çelişkisini önler.

| Heuristic | Anlam | Severity | Gate (APPROVED'ı engeller mi) | Gerekçe |
|---|---|---|---|---|
| `short_content` (<200 kelime) | yapısal derinlik | SOFT | **FORMAT_DEPENDENT** | card/checklist'te kısa olmak normal olabilir; full-lesson'da daha ağır |
| `few_takeaways` (<2) | öğrenme çıktısı eksik | **TBD (PROVISIONAL)** | **TBD** | ≥2 takeaway'in her türde zorunlu olduğu kanıtlanmadı; card/checklist'te gerekmeyebilir |
| `quiz<1` | değerlendirme eksik | SOFT | FORMAT_DEPENDENT | bazı türlerde (card) quiz şart olmayabilir |
| `flashcard<2` | tekrar aracı eksik | SOFT | FORMAT_DEPENDENT | destekleyici, bloklayıcı değil |
| `no_real_example` | uygulanabilirlik eksik | SOFT | FORMAT_DEPENDENT | her ders somut örnek gerektirmez (kavramsal konular) |
| `no_source_when_rag` | kaynak atfı eksik | **CRITICAL** | **HARD_BLOCK** | RAG doluyken kaynaksız ders doğruluk riski (finansal içerikte kırmızı çizgiye yakın) |

**Not:** TBD = henüz kanıt yok; B5 exact replay karar verecek. Severity/gate'ler **ürün/kalite politikası önerisidir** — Meriç onayı gerekir.

## B2 — Format-Aware Thresholds (CONTRACT FREEZE — B5 replay ile kalibre)

**İki eksen ayrımı korunur:** severity (ciddiyet) ≠ gate behavior (blocking). Ve **`initial contract threshold` ≠ `empirically optimal`** — 200 B5'le format-ayrımı destekli ama optimum kanıtlanmadı.

| Tür | min_words | min takeaways | quiz / flashcard | real_example |
|---|---|---|---|---|
| guide | **200** (initial) | TBD | format-aware | önerilen |
| coded | **200** (initial) | TBD | format-aware | **önemli** |
| compare | **200** (initial) | TBD | format-aware | önerilen |
| card | **yok** | TBD | opsiyonel | opsiyonel |
| checklist | **yok** (madde-yapısı kontrolü) | TBD | opsiyonel | opsiyonel |
| dersi / legacy | **TBD** | TBD | TBD | TBD — **legacy/undefined policy** |

**B5 kanıtı:** card 22/24 <200 kelime (median 63) → evrensel 200 kuralı card'da anlamsız; guide/coded/compare'de <200 azınlık (7-8/24) → 200 initial makul. `few_takeaways` TBD kalır (B5 kanıtı yetersiz).

## B3 — LLM Quality Contract (KORUNUYOR — değişiklik yok)

```
APPROVED  := avg >= 7.5  AND  hiçbir boyut < 5
REVISION  := avg 5-7.5  OR  tek boyut < 5
REJECTED  := avg < 5     OR  2+ boyut < 5
```
Bu katman **değiştirilmez.** LLM gerçek kaliteyi ölçer (doğruluk, pedagoji, derinlik, örnek, açıklık, uygulanabilirlik, kavram bütünlüğü).

## B4 — Decision Matrix (PROPOSED nihai kontrat)

| Structural (heuristic) | LLM | → Final |
|---|---|---|
| PASS (hiç issue yok) | APPROVED | **APPROVED** |
| PASS | REVISION | REVISION |
| PASS | REJECTED | REJECTED |
| SOFT issue, gate=FORMAT_DEPENDENT (format bu türde gerektiriyorsa) | APPROVED | **REVISION** ← soft issue APPROVED'ı engeller (gerekli formatta) |
| SOFT issue | REVISION/REJECTED | aynı |
| HARD/CRITICAL issue (gate=HARD_BLOCK, ör. no_source_when_rag) | herhangi | **REJECTED** (CRITICAL) / **REVISION** (HARD) |
| LLM yok | — | 0 issue → APPROVED; ≥1 issue → REVISION (fallback, mevcut) |

**Önceki davranışla tek fark (kritik):** LLM APPROVED artık gerekli formattaki heuristic issue'ları **geçemez** (eski kod 0-2 issue'yu yutuyordu). Ama **severity + format-aware** — kör "any issue → revision" DEĞİL, ve `few_takeaways` gibi TBD maddeler replay'e kadar blocking DEĞİL.

## B5 — Replay: iki AYRI çalışma (karıştırma)

### B5-A — Exact Replay (yalnızca bugün girdileri yeniden hesaplanabilen)
Yalnızca: heuristic inputs bugün mevcut + lesson content mevcut + lesson type belirlenebilir. → gerçek decision-matrix replay.

### B5-B — Historical Outcome Audit (geçmiş loglardan yalnızca gözlenebilen)
`agent_logs` issue-count saklamıyor → heuristic sebep ATANAMAZ. Yalnızca `decision × LLM avg × lesson` üzerinden tutarsızlık ölçülür (örn. APPROVED@<7.5, REJECTED@≥7.5). **Exact replay ≠ historical outcome audit.**

**Lesson-level vs run-level ayrımı (kritik):** 118 **lessons** ≠ 2.679+ **guard_runs** (bir ders 30 kez review edilmiş olabilir). Replay'de `unique_lessons`, `guard_runs`, `unique_lesson_versions` ayrı raporlanır — aksi halde tekrar review'lar bağımsız örnek gibi görünür.

Bu replay **kontratı kalibre eder** (B2 eşikleri + B1 TBD'ler) ve **uygulama öncesi etkiyi ölçer** (kaç mevcut published geri düşerdi). Guard koduna DOKUNMAZ.

---

## Durum kilidi (Meriç kararına uygun)

```
C1-GUARD-001
  ├── STATUS: OPEN → PROPOSED-CONTRACT (bu spec)
  ├── Guard code: IMMUTABLE
  ├── DB: IMMUTABLE
  ├── 108 drafts: IMMUTABLE
  ├── Test artifact (…-card): LEAVE AS-IS (published, anomaly-flagged)
  ├── R1 updater: CAN PROCEED (Guard kontratından bağımsız — operasyonel)
  ├── Guard contract definition: BU DOSYA (sıradaki)
  ├── R3 generator: HOLD
  ├── R4 E2E: HOLD
  └── Bulk processing: BLOCKED
```

## Sonraki adım (Meriç B5 GO — Contract Revision tamam, Implementation Pending)

Sıra (kilitli): **B5 evidence → Contract freeze (bu dosya) → Level B Implementation Gate → Guard implementation → Guard replay → E2E → R3 generator optimization.**

Implementation Gate giriş kriterleri (Meriç): (1) bu spec güncellendi ✓; (2) B2 placeholder'ları format-aware değerlerle dolduruldu ✓; (3) few_takeaways TBD ✓; (4) dersi/legacy = undefined policy ✓; (5) severity≠gate ayrımı eklendi ✓; (6) Guard kodu henüz değişmedi ✓; (7) ayrı Level B Implementation Gate açılacak; (8) implementation **yalnızca Guard decision layer**'ını değiştirir — DB/lesson/generator/scheduler/updater'a DOKUNULMAZ; (9) önce tek kontrollü test → replay → rollout.

**R3 generator AÇILMAZ** — generator, Guard'ın mevcut kusurlu davranışına göre optimize EDİLMEZ; önce Guard doğru kontrata getirilir.

## Governance
- Read-only spec; Guard/DB/draft değiştirilmedi. Test dersi LEAVE AS-IS.
- Bu dosya C1-GUARD-001'i **kapatmaz** — kontratı **önerir**. Kapatma, Meriç onayı + B5 replay + ayrı implementation gate'i gerektirir.
- `%48 short_content = generator failure` yorumu **bu spec tamamlanana kadar PROVISIONAL** (format-aware olmadan kanıtlanamaz).
