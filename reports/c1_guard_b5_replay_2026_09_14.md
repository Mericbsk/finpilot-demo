# C1 — B5 Guard Contract Replay (READ-ONLY)

**Tarih:** 2026-09-14 · **Girdi:** Guard Contract Specification (C, Meriç-onaylı revize) · **Mutation:** NONE
**İki ayrı analiz:** B5-A Exact Replay (lesson-level, bugün yeniden hesaplanabilir) + B5-B Historical Outcome Audit (run-level, agent_logs). **Lesson ≠ run ayrımı korundu.**

---

## Veri kapsamı

- `unique_lessons` = **120** · `guard_runs` = **3.168** · unique lesson-review hedefi = **126** (bazı dersler çok kez review edilmiş — ayrı sayıldı)
- `corpus_chunks` (RAG) = 28 (dolu)
- Türler (id-suffix): guide 24 · card 24 · coded 23 · compare 23 · checklist 22 · dersi 3 · la 1

## B5-A — Exact Replay: tür-bazlı heuristic başarısızlık

| Tür | n | short(<200k) | few_take | no_quiz | few_flash | no_ex | no_source |
|---|---:|---:|---:|---:|---:|---:|---:|
| guide | 24 | 7 | 1 | 1 | 2 | 1 | 0 |
| **card** | 24 | **22** | 4 | 0 | 0 | 0 | 0 |
| coded | 23 | 8 | 4 | 4 | 4 | 5 | 0 |
| compare | 23 | 8 | 1 | 1 | 1 | 4 | 0 |
| checklist | 22 | 7 | 1 | 2 | 2 | 1 | 0 |
| dersi | 3 | 2 | 1 | 0 | 0 | 0 | 0 |

**Q1 (kaç card <200 kelime):** 22/24 (%92). **Median card = 63 kelime.**
**Q2 (short card'lar gerçekten kalite-problemli mi):** pedagogy_score çoğunluğu 8,0 — kısa olmalarına rağmen yüksek skor. → **card için <200 kelime "kalite problemi" değil, format gereği.** 200-kelime evrensel kuralı card'da anlamsız.
**Q3 (200 kelime guide/coded/compare için anlamlı mı):** guide'da 7/24, coded'da 8/23, compare'de 8/23 <200 kelime — bu türlerde kısa olmak azınlık ve anlamlı bir sinyal olabilir.
**Q7 (no_source CRITICAL ayrılabilir mi):** **0/120** derste no_source (RAG doluyken hepsi source taşıyor) → CRITICAL gate şu an hiç tetiklenmiyor; ayrım teorik olarak temiz ama pratikte tetiklenmiyor.

## B5-B — Historical Outcome Audit (run-level, issue-count UNKNOWN)

`agent_logs` issue-count saklamıyor → heuristic sebep geçmişe **atanamaz** (UNKNOWN). Yalnızca decision × LLM avg:

| Karar | avg≥7.5 | 5–7.5 | <5 |
|---|---:|---:|---:|
| APPROVED | 9 | **4** ⚠️ | 0 |
| REJECTED | **16** ⚠️ | 184 | 29 |
| REVISION_NEEDED | 418 | 2.417 | 91 |

**Tutarsızlık:** 4× APPROVED@5-7.5 ve 16× REJECTED@≥7.5 — mevcut heuristic-override'ın (3+→REJECTED) ve LLM-üzerinden-heuristic-yutmanın geçmişte de sapma ürettiğini gösteriyor. **Exact kök neden UNKNOWN** (issue-count loglanmıyor).

## 10 Published ders — yeni kontrat altında (Q8: kaçı geri düşer)

| Tür | words | takeaways | quiz | flash | Mevcut-heuristic durumu |
|---|---:|---:|---:|---:|---|
| la | 202 | 3 | 1 | 2 | PASS |
| dersi | 164 | 3 | 1 | 2 | short(<200) |
| dersi | 172 | 3 | 1 | 2 | short(<200) |
| dersi | 313 | 1 | 1 | 2 | few_takeaways |
| **card** | **89** | **1** | 2 | 4 | short + few_takeaways ← test dersi |
| checklist | 214 | 3 | 2 | 2 | PASS |
| compare | 353 | 3 | 2 | 2 | PASS |
| coded | 479 | 3 | 1 | 2 | PASS |
| coded | 231 | 3 | 1 | 2 | PASS |
| coded | 231 | 2 | 1 | 2 | PASS |
| checklist | 342 | 3 | 1 | 2 | PASS |

**Q8 cevabı:** Format-aware kontrat altında, published'lerin çoğu PASS kalır. Test dersi (`-card`, 89 kelime/1 takeaway) yalnızca **eğer card için min-words/min-takeaway zorunlu kılınırsa** geri düşer — ama B5-A card'ların doğal olarak kısa olduğunu gösterdi (median 63). → **Card için kısa olmak geri-düşürme nedeni olmamalı.**

## B5 Karar Soruları — cevaplar

- **Q1:** 22/24 card <200 kelime (median 63).
- **Q2:** Hayır — kısa card'lar yüksek pedagogy_score (8,0) taşıyor; format gereği kısa.
- **Q3:** guide/coded/compare'de <200 kelime azınlık → anlamlı sinyal olabilir.
- **Q4 (few_takeaways):** card 4, coded 4, dersi 1, guide/compare/checklist 1 — az ama türden bağımsız değil; **TBD olarak kalmalı** (Meriç kararı doğruydu).
- **Q5 (quiz/flashcard):** eksiklik coded'da en yüksek (4/23) — hesaplamalı derste quiz eksikliği anlamlı; card'da 0 eksik.
- **Q6 (real_example):** coded 5, compare 4 — uygulamalı türlerde örnek eksikliği daha anlamlı.
- **Q7:** 0 tetiklenme — CRITICAL gate teorik temiz, pratikte aktif değil.
- **Q8:** Çoğu published PASS kalır; yalnızca card/dersi formatları format-aware olmadan haksız geri-düşerdi.

## B5 Sonucu → **REVISE (hafif) → GO eğilimli**

Önerilen C kontratı mevcut içerikle **büyük ölçüde tutarlı** (çoğu published PASS kalır) VE card/format false-positive'lerini doğru yakalıyor. Ama:

- **`few_takeaways` TBD olarak kalmalı** (kanıt yetersiz) ✓ zaten revize edildi
- **Format-aware `min_words` şart** — evrensel 200 kelime card'da anlamsız (median 63). Eşik **tür bazlı** olmalı: card → kelime eşiği yok; guide/coded/compare → ~200 makul; checklist → madde-yapısı kontrolü.

**Bu B5, implementation'a GO eğilimli ama önce:** (1) format-aware eşikleri bu bulgularla doldur (B2'yi artık placeholder olmaktan çıkar, replay-veriyle), (2) Meriç onayı, (3) ayrı implementation gate.

## Governance
- Read-only. Guard/DB/120-draft değiştirilmedi. Test dersi LEAVE AS-IS.
- C1-GUARD-001 STATUS: OPEN / CONTRACT_PROPOSED → replay REVISE-eğilimli-GO. Implementation henüz YOK.
- Lesson-level (120) ≠ run-level (3.168) ayrı tutuldu. Exact replay ≠ historical outcome audit ayrı tutuldu.
