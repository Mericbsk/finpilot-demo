# ADDENDUM — FLAG IMPACT AUDIT (2026-09-10): ölçülen sıralama katmanının açıklaması

**Tarih:** 2026-09-23 · **Tip:** Dokümantasyon düzeltmesi (Level A) · **Production impact:** NONE
**İlgili rapor (DEĞİŞTİRİLMEDİ):**
- `reports/flag_impact/flag_impact_report.md` — SHA-256 `f3ffddd4f6161f4338874dcb4502e4332242100abda822ba4d8ec65e7d7be292`
- `reports/flag_impact/flag_impact_summary.json` — SHA-256 `40493bbe0ed6b21499400677da10833a96da8cc21004f6680c34f9cec77944d2`

Orijinal rapor byte-identical bırakıldı. Bu addendum onun sonuçlarını geçersiz kılmaz. Yalnızca hangi nesneyi ölçtüğünü netleştirir.

---

## Ne ölçüldü

Rapor, 2026-09-09 export'u üzerinde (run_id `20260909T111531`, commit `a242b06`) 5 skor flag'inin etkisini ölçtü. Bu export, 09-09'da yayınlanan snapshot'ın kaynağı olan export'la aynı run'dır. Ölçüm şu nesneler üzerinde yapıldı:
- `recommendation_score`
- bu skordan türetilen **composite sıralama** (raporun §Reproducibility bölümünde "rank method (composite desc)")

"1.792 sembolde rank değişti" gibi `RANK_EFFECT` sınıflandırmaları **bu composite katmana** aittir. Bu açıdan ölçümler doğrudur.

## Neyi ölçmedi

Kullanıcıya gösterilen liste (`distribution/snapshot_builder.py`) composite sıralamayla oluşturulmaz. Liste şu adımlarla kurulur:

1. `_public_candidate` filtresi uygulanır: grade, selection_eligible, execution_feasible, position_cap_reject_reason.
2. Satırlar `_sort_key` ile sıralanır: `(grade, execution_confidence, −conviction_prob, −ranking_score …)`.
3. `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` olduğu için `ranking_score = legacy_quality_score` (`scanner/evaluate.py:722-724`). 09-09 export'unda 1801 satırın 1801'inde `ranking_method = legacy_quality`.
4. `legacy_quality_score` (`scanner/score_engine.py:193-222`) lottery ve overnight faktörlerini flag'e bakmadan kullanır. `squeeze_factor` ise ALPHA_V2 açıkken SQUEEZE flag'inden bağımsız hesaplanır (`scanner/features.py:361`).

Bu yüzden raporun `RANK_EFFECT` bulguları kullanıcıya dönük sıralamanın kanıtı olarak **kullanılmamalıdır.**

## B2-0 bulgusu (bağlam)

B2-0 bu flag'lerin yayınlanan liste üzerindeki etkisini ayrıca ölçtü (`reports/b2_0_flag_user_facing_impact_report_2026-09-23.md`).

- 09-09 yayın snapshot'ında SQUEEZE_FACTOR, LOTTERY_FADE, OVERNIGHT_GAP, EDGAR_CATALYST ve FRED_MACRO için sınıf `NO_OBSERVED_USER_FACING_IMPACT`. Graded liste 10/10, ücretsiz katman değişmedi, web context 10/10.
- Aynı flag'ler kapatıldığında composite_score değişiyor: SQUEEZE 1232, LOTTERY 1503, OVERNIGHT 843 satırda (toplam 1508). Yani iki bulgu birbiriyle tutarlı; farklı katmanları ölçüyorlar.
- B2-0'ın toplam verdict'i `INCOMPLETE`. CONVICTION_TIERS ve ALPHA_V2 yeniden kurulamadı. Bu nedenle "flag'lerin kullanıcıya etkisi yoktur" genellemesi yapılamaz.

**Durum:** B2-0'ın bağımsız doğrulaması henüz tamamlanmadı. Bu addendum'un B2-0'a dayanan kısmı o doğrulamaya tabidir. Composite ile publication katmanının farklı olduğu tespiti ise doğrudan koda ve export'a dayanır.

## Kullanım kuralı
- **"Composite rank değişimi"**, yayınlanan listenin değiştiği anlamına gelmez.
- **Kullanıcıya dönük etki** iddiası için yalnızca snapshot inşa yolu (`_public_candidate` + `_sort_key`) üzerinde yapılmış bir ölçüm kullanılır.
