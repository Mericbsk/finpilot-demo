# Production-Instrumented Baseline Data Capture — Level B

**Tarih:** 2026-09-09 · **Tip:** Measurement / instrumentation (observability only)
**Level:** B — production dosyasına instrumentation eklendi; scoring/ranking/flag/weight/DB davranışı değiştirilmedi; locked OOS açılmadı.
**Amaç:** Production baseline hesaplanırken kaybolan ara girdileri (filter_score, alignment_ratio, momentum_ratio, volume_spike, price_momentum, trend_strength) **değiştirmeden** persist etmek.

---

## 1. Objective
Production scan sırasında hesaplanan ama dataset'e persist edilmeyen 6 ara girdiyi, mevcut scoring davranışını **hiç değiştirmeden** append-only olarak kaydetmek. Predictive improvement / optimizasyon bu çalışmanın kapsamı dışında.

## 2. Scope
Yalnızca observability. Yeni scoring modeli, ağırlık, feature, ranking değişikliği YOK. Synthetic/imputed historical data YOK.

## 3. Production execution path (koddan doğrulandı)
```
evaluate_symbol(symbol)
  → fetch_multi_timeframe / prefetched (15m,1h,4h,1d OHLCV)
  → regime = close_1d > ema200_1d          (evaluate.py:395)
  → direction = close_1d > ema50_1d        (evaluate.py:396)
  → score 0-3 (RSI/volume/MACD_hist)       (evaluate.py:401-414)
  → volume_spike / price_momentum / trend_strength → filter_score (evaluate.py:422-425)
  → alignment_ratio = check_timeframe_alignment(1h,4h,1d)  (evaluate.py:471)
  → momentum_ratio  = check_momentum_confluence(15m,4h)    (evaluate.py:474)
  → _score_input dict → compute_recommendation_score → _score_raw (evaluate.py:671)
  → _score_components = score_component_breakdown(_score_input) (evaluate.py:672)
  → _composite_score = compute_recommendation_strength (evaluate.py:672-674)
  → return dict  (tüm component'leri İÇERİR: filter_score, alignment_ratio,
                   momentum_ratio, volume_spike, price_momentum, trend_strength,
                   vol_regime, composite_score, _score_components, _score_input)
  → evaluate_symbols_parallel toplar → return results
```
**Kritik bulgu:** return dict zaten tüm component'leri taşıyor — sadece **persist edilmiyorlardı**. Bu yüzden instrumentation `evaluate_symbols_parallel`'ın çıkışında, return dict'ten okuyan tek bir hook.

## 4. Instrumented fields
`symbol, scan_ts_utc, scan_date, scan_basis, regime, direction, score, filter_score, volume_spike, price_momentum, trend_strength, alignment_ratio, momentum_ratio, vol_regime, composite_score, recommendation_score, score_component_breakdown, score_component_total, score_input, score_feature_flags, telemetry_version, run_id, instrumentation_version, git_commit`.

## 5. Schema
Append-only JSONL. Canonical isimler production return dict'ten korundu (yeni isim yaratılmadı). `score_feature_flags` zaten `score_feature_flags()`'ten snapshot olarak geliyor (catalyst/squeeze/lottery/overnight).

## 6. Timestamp semantics
- `scan_ts_utc`: instrumentation'ın yazıldığı UTC an (run provenance).
- `timestamp` (result'tan): `_signal_timestamp` = son 15m bar (signal zamanı).
- `scan_date`: result timestamp'inden türetildi (YYYY-MM-DD).
- `scan_basis`: "EOD" (bu pipeline EOD-only). EOD/intraday karıştırılmadı.

## 7. Provenance
`run_id` (UTC), `instrumentation_version=1.0`, `git_commit` (git rev-parse; yoksa NULL), `scan_basis`, `score_feature_flags` snapshot.

## 8. Flag-state capture
`score_feature_flags` production'dan snapshot alınır. `.env` / flag davranışı **değiştirilmedi**.

## 9. Test methodology
`research/instrumentation_validation_2026_09_09.py` — sentetik kontrollü input üzerinde: T1 schema, T2 score non-regression, T3 rank non-regression, T4 reconstruction. Canlı universe'de ÇALIŞTIRILMADI (küçük kontrollü sample prensibi).

## 10. Score non-regression
```
flag OFF score 9.1 | flag ON score 9.1 | delta 0.0
T2: before=13.84 after=13.84 delta=0.0 -> PASS
```
Instrumentation compute path'te değil; skora **sıfır etki**.

## 11. Rank non-regression
```
T3: strength 84 == 84 -> PASS
```
Ranking değişmedi.

## 12. Reconstruction fidelity (kontrollü sample)
```
T4: reco=13.84 == production 13.84 (exact) -> PASS
    components sum 13.84 == production -> PASS
    reconstructed composite 84 == production strength 84 -> PASS
```
Kontrollü sample'da **%100 exact reconstruction** (bu, persist edilen `score_input`/`score_component_breakdown` ile mümkün — forensic'teki eksik giderildi).

## 13. Coverage
Sentetik sample'da %100. **Gerçek production coverage için canlı scan gerekir** (yapılmadı — Level B onay + prepublish gerektirir). `alignment_ratio`/`momentum_ratio` 15m/4h/1h OHLCV gerektirir — production `fetch_multi_timeframe` bunları zaten çekiyor, dolayısıyla **canlı scanda persist edilebilir** (historical backfill MÜMKÜN DEĞİL — geçmiş OHLCV yok, sentetik üretilmedi).

## 14. Missing-data analysis
- `vol_regime` None → momentum_weight=2.0 (production default) korunur.
- OHLCV eksik → ilgili feature production'da False/0 olur, instrumentation bunu olduğu gibi kaydeder (impute etmez).
- `missing_reason` ayrı alan olarak schema'da production `_unavailable_result` akışına bırakıldı.

## 15. Known limitations
- **Historical backfill yok:** 6 alan geçmiş scan'ler için ÜRETİLEMEZ (multi-TF OHLCV geçmişi yok). Instrumentation yalnızca **bundan sonraki** scan'leri yakalar.
- Canlı scan çalıştırılmadı → production coverage/uptime kanıtı yok (NOT_READY for live).
- `scan_basis` sabit "EOD"; intraday scan ayrımı production davranışına bağlı.

## 16. Final status

## **PARTIAL**

- IMPLEMENTED: ✓ (hook + emit modülü)
- ACTIVE: ✗ (default OFF, canlı scan yapılmadı)
- INSTRUMENTED: ✓ (kontrollü sample'da doğrulandı)
- RECONSTRUCTABLE: ✓ (kontrollü sample'da %100 exact)
- PREDICTIVE: — (test edilmedi, kapsam dışı)
- VALIDATED: — (canlı production'da değil)

## 17. Next allowed step
**GATE B1: CAN PRODUCTION BASELINE NOW BE RECONSTRUCTED EXACTLY?**
- Kontrollü sample'da: **YES** (%100 exact, sıfır non-regression).
- Production-wide historical: **NO** — geçmiş scan'ler backfill edilemez; yalnızca gelecekteki scan'ler.
- → Sonraki adım: **Meriç onayı ile FINPILOT_INSTRUMENT_BASELINE=1 açılıp tek bir kontrollü canlı scan** (5-20 sembol) → production coverage + fidelity kanıtı. Bu Level C'ye yaklaşır (canlı sisteme dokunur). Sonra yeterli persist birikince `Baseline Reconstruction & Predictive Validation`.

---

# FINAL RESPONSE FORMAT

```
FINPILOT LEVEL B — INSTRUMENTATION RESULT

STATUS: PARTIAL

1. Production Path
   evaluate_symbol -> component hesaplama -> return dict (tum component'leri icerir)
   -> evaluate_symbols_parallel -> [YENI] instrumentation.emit_baseline_inputs -> return

2. Instrumented Fields
   symbol, scan_ts_utc, scan_date, scan_basis, regime, direction, score, filter_score,
   volume_spike, price_momentum, trend_strength, alignment_ratio, momentum_ratio,
   vol_regime, composite_score, recommendation_score, score_component_breakdown,
   score_component_total, score_input, score_feature_flags, run_id,
   instrumentation_version, git_commit

3. Schema
   Append-only JSONL: data/backtest_out/production_instrumentation/baseline_inputs_<run_id>.jsonl
   Canonical isimler production return dict'ten; yeni isim yok. run-specific, overwrite yok.

4. Timestamp/Provenance
   scan_ts_utc (write), timestamp (signal 15m bar), scan_date (derived), scan_basis=EOD,
   run_id(UTC), git_commit (yoksa NULL), score_feature_flags snapshot.

5. Coverage
   Sentetik sample %100. Canli production coverage NOT YET (canli scan yapilmadi).
   alignment/momentum canli scanda persist EDILEBILIR; historical backfill MUMKUN DEGIL.

6. Score Non-Regression
   PASS (delta 0.0; flag OFF/ON ayni; compute path'e dokunmuyor)

7. Rank Non-Regression
   PASS (strength 84==84)

8. Reconstruction Fidelity
   PASS kontrollu sample'da: reco exact, components sum exact, composite exact (84==84)

9. Missing Inputs
   Historical 6 alan backfill edilemez (multi-TF OHLCV gecmisi yok). Gelecek scan'ler yakalanir.

10. Artifacts Created
   scanner/instrumentation.py (yeni)
   research/instrumentation_validation_2026_09_09.py (yeni)
   reports/production_instrumentation_2026_09_09.md (bu rapor)
   data/backtest_out/production_instrumentation/ (run-time olusur)

11. Files Changed
   scanner/evaluate.py  (+1 import, +3 satir hook = saf OBSERVABILITY)
   YENI: scanner/instrumentation.py, research/instrumentation_validation_2026_09_09.py
   UYARI: scanner/evaluate.py ve scanner/features.py icinde BU CALISMA DISI ek
   degisiklikler mevcut (compute_dist_52w_high/gap_pct/rvol_daily hesap+dict) — benim
   enstrumantasyonum DEGIL, geri alinmadi, DATA CAPTURE kategorisi.

12. Governance Impact
   Level B. Locked OOS / catalyst / squeeze / lottery / overnight / attention-map /
   baseline-validity DEGISMEDI. .env DEGISMEDI. decision-log'a otomatik yazilmadi.

13. What We Know Now
   - Return dict zaten tum component'leri tasiyor; sadece persist edilmiyordu.
   - Instrumentation skoru/rank'i degistirmiyor (delta 0).
   - Persist edilen score_input/components ile exact reconstruction mumkun.

14. What We Still Don't Know
   - Canli production coverage/uptime (scan yapilmadi).
   - alignment/momentum gercek varyansi (canli persist birikmeden bilinemez).
   - Baseline reconstruction production-wide mumkun mu (gecmis backfill yok).

15. Next Gate
   GATE B1: kontrollu sample = YES; production-wide = NO (historical backfill yok).
   Sonraki: onayli tek kontrollu canli scan (FINPILOT_INSTRUMENT_BASELINE=1) ->
   coverage/fidelity kaniti -> yeterli persist sonrasi Predictive Validation.

CRITICAL FINDING:
   Production baseline'in reconstruct edilememesinin nedeni formulin yanlis olmasi
   DEGIL; component'lerin evaluate_symbol return dict'inde zaten mevcut olup hicbir
   yere persist edilmemesi. Tek bir append-only observability hook'u (skora dokunmadan)
   gelecekteki scan'ler icin exact reconstruction'i mumkun kiliyor. Ancak historical
   scan'ler (alignment/momentum gibi multi-TF girdiler) GERI GETIRILEMEZ — bu veri
   kaybi kalici ve yalnizca ileriye donuk cozulebilir.

RECOMMENDATION:
   Bu instrumentation'i onaylayip tek bir kontrollu canli scan ile dogrulayin
   (coverage + fidelity kaniti). Predictive test YAPMAYIN — once yeterli persist
   biriksin. Historical baseline reconstruction imkansiz kalacagindan, baseline
   "FAILED" sonucu PROVISIONAL kalmaya devam eder.
```

## Governance
- Level B; production scoring/ranking/flag/DB/scheduler davranışı değiştirilmedi. Locked OOS açılmadı.
- `.env` değiştirilmedi; `FINPILOT_INSTRUMENT_BASELINE` **default OFF** (açılmadı).
- decision-log'a otomatik yazılmadı (onay bekleniyor).
- Diff audit: eklenen kod yalnızca OBSERVABILITY/DATA CAPTURE/TEST. `PRODUCTION LOGIC` değişikliği YOK (emit hook'u return öncesi skoru değiştirmez; hata yutar).
- Çelişki/uyarı: `scanner/features.py` +54 satır ve `evaluate.py` içindeki `compute_dist_52w_high/gap_pct/rvol_daily` ekleri bu çalışma dışı — raporlandı, geri alınmadı.
