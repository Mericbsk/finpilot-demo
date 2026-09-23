# C1-GUARD-001 — Guard Decision-Surface Forensic (READ-ONLY)

**ID:** C1-GUARD-001 · **Tarih:** 2026-09-14 · **Severity:** HIGH · **Type:** Quality-control contract inconsistency
**Status:** OPEN / UNRESOLVED · **Mutation:** NONE (hiçbir Guard/DB/draft değişmedi; test dersi LEAVE AS-IS)
**Tetikleyici:** B-REPAIR-3 tek-ders E2E'si beklenmedik APPROVED üretti → PHASE B = DIAGNOSTIC HOLD (Meriç kararı)

---

## 1. Observed (kanıt)

```
lesson = financial-analysis-likidite-oranlar-card
content_words = 89   (heuristic: <200 → issue)
takeaways   = 1      (heuristic: <2  → issue)
heuristic_issues = 2
LLM_avg = 8.25
decision = APPROVED  → status = published
```

## 2. Documented contract (quality_guard.py docstring, :48-50)

```
- Ortalama >= 7.5 ve herhangi bir boyut < 5 yoksa: APPROVED
- Ortalama 5-7.5 veya tek bir boyut < 5: REVISION_NEEDED
- Ortalama < 5 veya 2+ boyut < 5: REJECTED
```

**Not:** Bu dokümantasyon LLM-skor boyutlarını tanımlıyor; **heuristic_issues ile LLM kararının nasıl birleştiği dokümante edilmemiş.**

## 3. Actual implementation (quality_guard.py:124-151)

```
issues = heuristic_checks(...)            # 0..N
if RAG dolu ve source yok: issues += 1
llm_result = _llm_review(...)

if llm_result:                            # LLM çalıştıysa
    decision = llm_result["decision"]     # heuristic issues IGNORE edilir
else:                                     # LLM yoksa fallback
    decision = APPROVED if len(issues)==0 else REVISION_NEEDED
if len(issues) >= 3:                      # tek heuristic override
    decision = REJECTED
```

**Gerçek davranış:** LLM varken **0-2 heuristic issue tamamen yok sayılıyor** (LLM kararı geçerli). Yalnızca **3+ issue → REJECTED** override'ı var. LLM yokken: 0 issue → APPROVED, ≥1 issue → REVISION.

## 4. Decision-surface (code-derived)

| Heuristic issues | LLM var mı | LLM kararı | → Gerçek karar |
|---|---|---|---|
| 0 | Evet | APPROVED | APPROVED |
| 0 | Evet | REVISION | REVISION |
| 1-2 | Evet | APPROVED | **APPROVED** ← (heuristic ignore) |
| 1-2 | Evet | REVISION | REVISION |
| **3+** | Evet | *herhangi* | **REJECTED** (override) |
| 0 | Hayır | — | APPROVED (fallback) |
| ≥1 | Hayır | — | REVISION (fallback) |

## 5. All-time distribution (2.679+ guard run, agent_logs)

`agent_logs` issue count saklamıyor → heuristic-sayımı geçmişe dönük reconstruct **edilemez** (UNKNOWN). Ama decision × avg bandı ölçülebilir:

| Karar | avg≥7.5 | 5≤avg<7.5 | avg<5 |
|---|---:|---:|---:|
| APPROVED | 9 | **4** ⚠️ | 0 |
| REJECTED | **16** ⚠️ | 181 | 28 |
| REVISION_NEEDED | 406 | 2.376 | 89 |

**Anomali kanıtı:** `APPROVED & 5≤avg<7.5` (4 vaka) ve `REJECTED & avg≥7.5` (16 vaka) dokümante contract'la **çelişiyor** — bu, heuristic override'ın (3+ → REJECTED) ve/veya LLM-belirsizliğinin geçmişte de sapmalara yol açtığını gösteriyor. (Kesin neden — heuristic mi LLM mi — log'da issue olmadığı için UNKNOWN.)

## 6. Üç olasılık (hangisi — HENÜZ KARAR YOK)

- **A — Documentation yanlış:** Gerçek kontrat "1-2 issue → LLM'e bırak, 3+ → reject" ise Guard doğru çalışıyor.
- **B — Code yanlış:** Kontrat "any issue → revision" ise implementation hatalı (heuristic 1-2'yi yutuyor).
- **C — İki katmanlı politika belgelenmemiş:** "heuristic = soft gate, LLM = hard gate" tasarımı olabilir ama yazılı değil.

**UNKNOWN (log sınırı):** agent_logs issue-count içermediği için geçmiş 4 APPROVED/16 REJECTED sapmasının kök nedeni reconstruct edilemiyor.

## 7. Test artifact kaydı (mutasyon yok)

```
lesson: financial-analysis-likidite-oranlar-card
E2E_TEST_ARTIFACT = true
GUARD_ANOMALY = true
NORMAL_PRODUCTION_SAMPLE = false
status: published (LEAVE AS-IS — ikinci mutasyon yapılmadı)
```
Bu ders normal production başarısı sayılmıyor. Geri alma (published→draft) kararı Meriç'e ait — şu an yapılmadı.

## 8. Neden R3/R4 durdu

Guard'ın gerçekten hangi koşulda APPROVED verdiği bilinmeden generator'ı optimize etmek **yanlış hedefe optimizasyon** olur. `C1-GUARD-001` kapanmadan:
- Guard'a dokunulmayacak
- R3 generator değişikliği HOLD
- 108 draft'a toplu işlem YOK

## 9. Sonraki adım (Meriç kararı gerekir)

`C1-GUARD-001`'i kapatmak için kontrat netleşmeli:
- Eğer (A)/(C) ise → kontratı **belgele** (kod doğru, doc yanlış).
- Eğer (B) ise → bu bir **Guard değişikliği** olur (Level B/C, ayrı onay) — "any issue → revision" yapmak. **Bu turda yapılmadı.**

**Beklenen karar:** Guard'ın *olması gereken* kontratı hangisi? (Bu bir ürün/kalite-politikası kararı, teknik değil.)

## Governance
- Read-only. Guard/DB/draft değiştirilmedi. Test dersi LEAVE AS-IS (published, anomaly-flagged).
- Phase B = DIAGNOSTIC HOLD. R3/R4 durdu.
- Bu bulgu E2E testinin değerini kanıtlıyor: 108 dersi toplu işlemden ÖNCE yakalandı.
