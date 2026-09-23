# FinPilot — Master Research Inventory

**Version:** 1.0 · **Date:** 2026-09-10 · **Owner:** research
**Status:** ACTIVE — tek referans otoritesi. Yeni bir audit/research başlatmadan önce buraya bakılır; bir bulgu mevcut bir sonucu değiştirirse burada güncellenir (duplikasyon değil, referans).
**Governance:** Level B (docs/INDEX.md manifest id `research` altında `authority_path` adayı). Level A logging'e dahil değil — Level B onayı sonrası decision-log'a işlenir.
**Kapsam:** `reports/` + `research/` altındaki tüm büyük audit/araştırma çıktıları. Her satır bir *canonical bulguya* işaret eder; detay için bağlantılı rapora gidin.

> **Kural (CORE-004/CORE-005):** Bu envanter *kavram → otorite dosya* eşlemesidir. İş kurallarını, formülleri veya metrikleri buraya KOPYALAMAYIN — kaynak rapora referans verin. Bu dosya ve gerçek ağaç çelişirse DUR ve bildir.

---

## 0. Nasıl okunur

Her giriş: `[Dönem] Konu — canonical rapor → KARAR/DURUM`.
Karar sözlüğü (mevcut repo konvansiyonu):
- `VALIDATED` / `VALIDATED-DESCRIPTIVE-RESEARCH` / `CONFIRMATORY_CANDIDATE` / `UNVALIDATED` / `SUSPECT` / `FAILED` / `KILL` / `NOT_FULLY_RECONSTRUCTED` / `PASS` / `BLOCKED` / `PROVISIONAL`.

---

## 1. Üst düzey sonuç matrisi (şu anki gerçek durum)

| Kavram | Durum | Canonical kanıt | Güven |
|---|---|---|---|
| Direction prediction (hangi yön) | **KILL** — 8+ bağımsız yöntem başarısız | `direction_context_battery_2026-09-03.md`, `direction_threshold_matrix_2026-09-03.md`, `experiment_review_board_exp1_2026-09-03.md` | Yüksek |
| Attention map (olağandışı davranış) | **VALIDATED-DESCRIPTIVE-RESEARCH** — lift 1.7–3.3×, 5 ay; direction/predictive DEĞİL | `attention_map_research_2026-08-14.md` | Orta (descriptive) |
| Opening-range fade | **CONFIRMATORY_CANDIDATE** — 59.9% gross ama day-clustered, %1 maliyette negatif; 3 koşul | `hgen_h3_fade_2026-09-03.md` | Düşük (cherry-pick riski) |
| 9 feature flag'leri | **UNVALIDATED / predictive DEĞİL** — skoru %83.5 değiştirir ama forward return'ü tahmin etmez | `meta_validation_audit_2026-09-08.md`, `scoring_ablation_audit_2026-09-08.md`, `walk_forward_scoring_validation_2026-09-08.md` | Yüksek (kanıt zinciri) |
| Baseline ranking (composite_score) | **FAILED (PROVISIONAL)** — random'dan kötü; ama reconstruction eksikti | `baseline_ranking_health_2026-09-09.md` | Orta (provisional) |
| Baseline reconstruction | **NOT_FULLY_RECONSTRUCTED historically; FORWARD CAPTURE ENABLED** — geçmiş imkânsız, ileriye dönük exact capture mümkün | `full_baseline_reconstruction_compression_forensics_2026-09-09.md` + `production_instrumentation_2026_09_09.md` | Yüksek |
| Instrumentation (GATE B1/B2) | **PASS** — exact forward capture, score/rank delta=0 | `gate_b1_live_instrumentation_2026_09_09.md`, `gate_b2_manual_2026_09_09.md` | Yüksek |
| Research-X score/outcome direction | **INVERTED PATTERN OBSERVED — descriptive; H2a NOT_SUPPORTED; H2b secondary directional result; H2c mixed/directionless; H2d DEFERRED** | `research_x_failure_phenotype_2026-09-21.md`, `research_x_h2_score_direction_preregistration_2026-09-21.md`, `research_x_h2_score_direction_2026-09-21.md` | Düşük (historical split-sample; score-direction signal established değil) |
| Catalyst factor | **UNVALIDATED — DATA-UNAVAILABLE** (cache regrese) | `catalyst_refresh_2026-09-03.md` + meta-validation | Düşük |
| c2c_5d label integrity | **SOLVED** — EOD-only + label_entry_basis | `c2c_5d_label_entry_basis_2026-09-03.md` | Yüksek |
| FinSense content loop | **BROKEN** — 96 ders, 88 taslak takılı, orchestrator tetiklenmiyor | `finsense_content_readiness_2026-09-07.md`, `finsense_autonomous_loop_gapmap_2026-09-07.md` | Yüksek |
| Locked OOS | **NOT_OPENED** | decision-log | — |

---

## 2. Dönem bazlı envanter

### Dönem 1 — Erken sprint & sistem gap (Mayıs–Temmuz 2026)
- `audit_2026.md` — genel sistem audit'i.
- `sprint8_gap.md` … `sprint16_gap.md` — sprint bazlı boşluk analizleri.
- `variety_report_2026-07-16.md` — çeşitlilik.
- `strategy_scenario_test_plan/results_20260727.md` — senaryo testleri.

### Dönem 2 — İlk araştırma programı dalgası (2026-08-04 → 08-10)
- `scanner-performance-research-2026-08-04.md`
- `fixed_target_full_universe_2026-08-04/05.md`
- `full_universe_candidate_gates_2026-08-04/05.md`
- `full_universe_statistical_validation_2026-08-04.md`
- `entry_quality_experiment_2026-08-06.md`
- `decision_quality_experiment_2026-08-06.md`
- `multitimeframe_profile_experiment_2026-08-06.md`
- `stability_concentration_capacity_2026-08-06.md`
- `research_program_execution_2026-08-06.md`
- `research_run_2026-08-07.md`, `research_test_plan_v2_2026-08-07.md`, `evidence_matrix_v1_2026-08-07.md`
- `research_reframing_end_to_end_2026-08-07.md`
- `correct_order_analysis/protocol_2026-08-10.md`
- `honest_quant_handbook_2026-08-10.md` + `_distribution_2026-08-10.md`
- `mirror_analysis_2026-08-10.md`
- `preregistration_three_hypotheses_2026-08-10.md`
- `strategic_lab_experiments_2026-08-10.md`
- `ten_perspectives_lab_2026-08-10.md`
- `user_research_kit_2026-08-10.md`

### Dönem 3 — Araştırma bataryaları, envanter, red-team (2026-08-11 → 08-14)
- `research_battery_consolidated_2026-08-11.md` / `research_battery_full_2026-08-11.md`
- `scanner_research_complete_inventory_2026-08-11.md`
- `scanner_research_battery_v2_2026-08-11.md`
- `gated_research_program_execution_2026-08-11.md`
- `pre_rise_path_battery_2026-08-11.md`
- `decision_context_battery_2026-08-12.md`
- `master_audit_application_2026-08-12.md`
- **`red-team-scientific-review-2026-08-12.md`** — adversarial bilimsel inceleme
- `ranking_score_backtest_2026-08-12.md`
- `external_finance_resources_review_2026-08-12.md`
- `winner_anatomy_2026-08-11.md`, `winner_anatomy_thought_experiment_2026-08-14.md`
- `production_candidate_validation_2026-08-12.md`
- `full_universe_pre_rise_hypotheses_2026-08-12.md`
- **high_rvol serisi:** `high_rvol_first_touch_tp_battery_`, `_full_universe_`, `_opportunity_battery_`, `_horizon_battery_`, `_deep_audit_`, `_raw_ohlc_exit_gate_2026-08-12.md`
- `budget_return_battery_2026-08-12.md`
- `data_readiness_audit_2026-08-11.md`
- `research_protocol_check_2026-08-04.md`
- `repo_document_hygiene_audit_2026-08-13.md`
- `comprehensive_final_research_2026-08-14.md`
- `day1_confirmation_matrix_2026-08-14.md`
- **attention_map doğuşu:** `attention_map_research_2026-08-14.md`, `attention_map_migration_plan_2026-08-14.md`, `attention_map_migration_plan_v3_2026-08-14.md`
- `attention_map_production_rollout_plan_2026-08-24.md`
- `finsense_gap_audit_2026-08-24.md`
- (içerik/ürün) `glossary_cards_product_spec_2026-08-10.md`, `finpilot_10x40_content_series_2026-08-10.md`, `finpilot_source_book_product_map_2026-08-10.md`, `source_material_inventory_2026-08-10.md`

### Dönem 4 — Direction failure + data repair + repo/content review (2026-09-03 → 09-07)
- `direction_context_battery_2026-09-03.md` — direction KILL (batarya 1)
- `direction_threshold_matrix_2026-09-03.md` — direction KILL (batarya 2)
- `experiment_review_board_exp1_2026-09-03.md` — H1 Regime×Tier FAIL/STOP (8. kapanış)
- `data_repair_diagnosis_2026-09-03.md` — c2c_5d + catalyst kök neden
- `c2c_5d_label_entry_basis_2026-09-03.md` — EOD-only düzeltme (Level B, onaylı)
- `catalyst_refresh_2026-09-03.md` — EDGAR cache dolumu (1801/548) — sonra regrese
- `hgen_h3_fade_2026-09-03.md` — fade CONFIRMATORY_CANDIDATE
- `external_repo_review_2026-09-07.md` — 11 repo (ponytail/feynman/context-mode CONFIRMATORY)
- `finsense_content_readiness_2026-09-07.md` — content ~%1.4, loop kırık
- `finsense_autonomous_loop_gapmap_2026-09-07.md`
- `decision_architecture_research_inventory_2026-09-07.md`

### Dönem 5 — Scoring gerçekliği zinciri (2026-09-08 → 09-09) — *en güncel ve en kritik*
1. `master_project_reality_audit_2026-09-08.md` — **9 flag ON/OFF çelişkisi** (#1 bulgu)
2. `feature_flag_evidence_summary_2026-09-08.md`
3. `meta_validation_audit_2026-09-08.md` — flag skoru %83.5 etkiliyor (IMPLEMENTED≠PREDICTIVE)
4. `scoring_ablation_audit_2026-09-08.md` — hiçbir component KEEP değil
5. `walk_forward_scoring_validation_2026-09-08.md` — 0/3 OOS; baseline zayıf
6. `baseline_ranking_health_2026-09-09.md` — baseline FAILED (random'dan kötü; PROVISIONAL)
7. `baseline_reconstruction_part0_partB_2026-09-09.md` — fizibilite + compression forensics
8. `full_baseline_reconstruction_compression_forensics_2026-09-09.md` — Case D: NOT_FULLY_RECONSTRUCTED
9. `production_instrumentation_2026_09_09.md` — Level B observability hook (6 kayıp input)
10. `gate_b1_live_instrumentation_2026_09_09.md` — **PASS** (8/8 exact)
11. `gate_b2_manual_2026_09_09.md` — **PASS-WITH-WARNINGS** (24 obs, integrity stabil)

---

## 3. Tekrarlanan yapısal bulgular (cross-cutting)

Bunlar birden çok raporda doğrulandı — tek noktadan referans:

1. **RANKING COMPRESSION** — `composite_score` 90 unique / 40k satır, %99.78 tie, gün-içi medyan çözünürlük ~%6. Kaynak: baseline health + forensics.
2. **COVERAGE BIAS** — composite yalnızca son ~57 günde tanımlı (null'lar 2025-09→2026-05-05). Kaynak: forensics.
3. **REDUNDANCY** — `composite ~ dist_52w_high` ≈ 0.64. Kaynak: baseline health + forensics.
4. **INVERTED RELATIONSHIP** — Q1 (düşük skor) > Q5 (yüksek skor) getiri. Kaynak: baseline health (kararsız, Ağu'da ters).
5. **PERSISTENCE GAP** — 6 ara girdi (filter_score, alignment_ratio, momentum_ratio, volume_spike, price_momentum, trend_strength) hiçbir dataset/DB'de persist edilmiyordu → instrumentation ile ileriye dönük çözüldü. Kaynak: forensics + B1/B2.
6. **Historical evidence: IMPLEMENTED ≠ ACTIVE ≠ INFLUENTIAL ≠ PREDICTIVE** *(baseline reconstruction provisional)* — flag'ler skoru değiştiriyor ama predictive değil; ancak bu sonuç baseline production state'i eksikken üretildi. Kaynak: meta-validation → ablation → walk-forward.

---

7. **RESEARCH-X/H4A clarification (2026-09-21)** — historical score-resolution evidence is descriptive only; global scale capacity, observed tie concentration, daily cross-sectional resolution, score provenance, and official production ranking mapping are separate questions. Official production ranking resolution remains **DEFINITION_REQUIRED**. Kaynak: `reports/research_x_h4a_resolution_compression_2026-09-21.md`.

## 4. Aktif gated pipeline (şu an buradayız)

```
[GATE B1 PASS] Instrumentation canlı path'te çalışıyor
    ↓
[GATE B2 ACCUMULATION CONTINUES]  ← ŞU AN — diversity not yet sufficient for B3
    ↓  (24 obs, tek gün, 8 sembol; keyfi 'yeterli' threshold'u YOK — §25/§37)
[GATE B3] Baseline Reconstruction & Validation  ← SPEC REGISTERED 2026-09-11 (BLOCKED_BY_B2)
    ↓   [research/b3_b4_baseline_validation_spec_2026_09_11.md — dondurulmuş metodoloji]
[GATE B4] Predictive Validation (baseline vs future outcomes, OOS)
    ↓  (gerekçeli ise)
Model / Ranking Research
```

---

## 5. Bekleyen kararlar (Level B/C — Meriç onayı gerekir)

| # | Karar | Kanıt durumu | Canonical kaynak |
|---|---|---|---|
| 1 | **Feature flag kararı** (9 flag ON ama predictive değil) | Kanıt zinciri tamam | meta-validation + ablation + walk-forward |
| 2 | **Catalyst cache onarımı** (single-writer) | Regresyon teşhisli (dual-writer) | meta-validation |
| 3 | **FinSense content loop** (orchestrator→scheduler) | Loop kırık, 88 taslak | finsense_content_readiness |
| 4 | **Opening-range fade confirmatory** (yeni veri, tek-shot) | 3 koşul tanımlı | hgen_h3_fade |
| 5 | **B2 → sürekli instrumentation** (`.env` veya scheduler) | B1/B2 PASS | gate_b2_manual |
| 6 | **Compression çözümü** (float skor / tie-breaking) | Hipotez — optimization sınırında | baseline health |

---

## 6. Bilinen kırmızı çizgiler / kısıtlar (değişmez)

- **Locked OOS: NOT_OPENED.** Herhangi bir OOS/production/publish = Level B/C.
- **Yasak dil** (al/sat/hedef fiyat) hiçbir yüzeye giremez (YONERGE §12).
- **Secrets** hiçbir dosyaya/rapora açık yazılmaz.
- **Karar decision-log'a yazılmadan "verilmiş" sayılmaz.**
- **Predictive conclusion** ancak repeatability + OOS + random control + effect size + stability birlikteyken.
- **Historical baseline reconstruction imkansız** (multi-TF OHLCV kayıp) — yalnızca ileriye dönük.

---

## 7. Bu envanterin bakımı

- Yeni bir büyük audit/research tamamlandığında buraya **tek satır** eklenir (canonical rapor referansı + karar).
- Bir bulgu öncekini geçersiz kılarsa, eski satır **üstü çizilmez** — yeni satırda "supersedes/updates" notuyla belirtilir (tarihçe korunur).
- Bu dosya `docs/INDEX.md` manifest id `research` için `authority_path` adayıdır — o değişiklik **Level B** ve ayrı onay gerektirir.

---

*Oluşturuldu: 2026-09-10 · research · Level B (INDEX manifest referansı için onay bekler). İçerik mevcut raporların konsolidasyonudur; yeni metrik/kanıt üretilmemiştir.*
