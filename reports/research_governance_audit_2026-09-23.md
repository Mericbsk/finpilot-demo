# RESEARCH GOVERNANCE MASTER AUDIT — 2026-09-23

**Controller:** Research Governance Master Controller v1 (one-shot, Level A, READ-ONLY)
**Scope:** end-to-end forensic/governance/provenance/readiness audit of the FinPilot research program.
**Method:** five independent audit threads (flag+lock/SHA, decision-log, overstatement, debt/provenance, production-impact), consolidated here.
**Determinism note:** this is a read-only audit; no experiment was rerun, no locked artifact modified, no production surface touched. `production_impact = NONE`.
**Subagent-error corrections applied by consolidator (documented, not hidden):**
- (a) The lock/SHA thread incorrectly reported RX-CAPTURE-1 as "locked but not executed" because it searched for `research_x_rx_capture_1_*` filenames; the actual artifacts are `research_x_capture_1_*` and exist, executed, verified (SHA `c6ab152157…`). Corrected below.
- (b) The production-impact thread presented the 9-flag ON state as a *new* critical finding. It is NOT new: it is the `CRITICAL CONTRADICTION` documented in `reports/meta_validation_audit_2026-09-08.md` (2026-09-08) and is a *known, open* governance debt (B2), not a newly discovered breach. Reclassified accordingly.

---

## A. EXECUTIVE SCIENTIFIC STATE (≤15 bullets)

1. Selection motoru forward predictive edge göstermiyor: geçmiş-5g ilişki ρ≈0.376, gelecek-5g ρ≈0.013 (association, nedensellik değil). Yön tahmini kapalı.
2. İlk bağımsız-doğrulanmış pozitif mekanik bulgu çıkışta: sabit-hedef +3%/+5%, selection sabitken maliyet-sonrası pozitif medyan capture (CAPTURE_SUPPORTED). Production onayı değil.
3. H4 FROZEN/CLOSED — compression gözlendi ama production ranking bozulması gösterilmedi; production resolution tarihsel olarak ölçülemez (provenance yok).
4. NS-1 NO_SCREEN_SUPPORTED — negatif eleme üretim filtresi için yeterli kanıt yok; NS-B3 PARTIAL; naive düşük-fiyat elemesi zararlı.
5. Program pre-production: locked OOS hiç açılmadı; hiçbir aday tam kanıt zincirini geçmedi.
6. Üç frozen/kapalı hat (H4, NS-1, RX-CAPTURE-1) bağımsız doğrulanmış ve kilitli; governance zinciri sağlam.
7. En büyük açık governance çelişkisi: 9+ flag canlıda ON ama predictive validation yok (belgeli, eski borç).
8. En kritik veri borçları: spread kapsama %0 (maliyet doğrulanamaz) ve production tuple provenance yok (ranking geçmişi denetlenemez).
9. Kullanıcı-yüzlü/yatırımcı materyali disiplinli — materyal overstatement bulunmadı.
10. 9+ kayıt-boşluğu (kayıt dışı tamamlanmış iş) sistematik bir governance boşluğu olarak duruyor.
11. V0 korelasyon çelişkisi (0.86/0.325/0.55) kök nedeniyle (MFE≠c2c) çözüldü ama henüz tek sayıya kilitlenmedi.
12. Level B kararları artık hazırlık durumuna göre ayrıştırılabilir: 3 hemen-hazır, 1 veri-bekleyen, 1 kanıt-bekleyen.
13. Hiçbir denetim kilitli sonucu değiştirmedi; hiçbir yeni deney başlatılmadı.
14. Hiçbir yetkisiz production değişikliği *yeni* bulunmadı (flag durumu önceden belgeli).
15. Program karar-hazır: her açık hattın tek-yasal-sonraki-adımı tanımlı.

## B. WHAT WE KNOW (yalnızca doğrudan destekli)

- Skor formülü doğru çalışıyor (B1: 8/8 exact reconstruction); tarihsel sorun persistence'dı.
- composite_score skor-uzayında sıkışık (90 unique/40k; tie ~%99.9975) — MEASURED_DESCRIPTIVE.
- Üretim sıralaması çok anahtarlı tuple; varsayılan kaynak flag=0 iken legacy_quality_score (kod seviyesi).
- Kilitli kohortta +3%/+5% sabit-hedef çıkış maliyet-sonrası pozitif medyan (bağımsız doğrulanmış).
- E0 hold-to-T+5 baseline maliyet-sonrası medyan-negatif (−0.718pp).
- 9 flag davranışsal aktif (skorun %83.5'ini etkiliyor); yalnızca LOTTERY_FADE tek Bonferroni-survivor.
- Yön tahmini 8+ bağımsız yoldan desteklenmedi; attention yön değil büyüklük taşıyor.
- ANS-1 attention-eleme medyan +2.62pp iyileştiriyor (risk-eleme değeri; al-sinyali değil).
- Ekonomik kapı FAIL: maliyet sonrası hiçbir grid/strateji pozitif kalmadı; ret yüzeyi %41.79 yanlış-red.

## C. WHAT WE DO NOT KNOW (gerçek bilinmeyenler)

- +3/+5% çıkışın gelecek OOS performansı ve yeni dönemlerde dayanıklılığı.
- Gerçek maliyet: spread/slippage/likidite/ADV/latency (spread kapsama %0).
- +5%'in late-period zayıflaması (1.556→0.117) kalıcı mı örneklem mi.
- Üretim ranking'inin gerçek tarihsel davranışı (tuple persist edilmiyor).
- Selection'ın gelecekteki predictive validity'si (locked OOS kapalı).
- Bileşenlerin nedensel katkısı; composite≈dist_52w_high nedensel mi.
- FRED_MACRO/FUNDAMENTALS/NEWS/ALPHA_V2'nin herhangi bir etkisi (hiç test edilmedi).

## D. CLOSED / FROZEN

```
H4A / H4B / H4C / H4D-def / H4D-measure   → CLOSED (H4 FROZEN)
RX-H2 score-direction                      → CLOSED / NOT_SUPPORTED
Direction prediction battery               → CLOSED / NOT_SUPPORTED
S1 Short Interest                          → CLOSED / REJECTED
High-RVOL line                             → CLOSED / REJECTED (tail-driven)
TP/SL grid                                 → CLOSED / ZERO ROBUST CONFIGS
Reverse-ranking / extension-cap            → CLOSED / artefakt
Ranking-score backtest                     → CLOSED / worse than composite
V2 path-aware locked-OOS                   → CLOSED / NO EDGE (n=62)
NS-1                                       → CLOSED / NO_SCREEN_SUPPORTED / VERIFICATION_PASS
RX-CAPTURE-1 (experiment)                  → CLOSED / VERIFICATION_PASS
```

## E. ACTIVE RESEARCH LINES (gerçekten açık olanlar)

Yok. Tüm araştırma hatları kapalı veya frozen. Açık olan tek şey **Level B kararları** (araştırma değil).

## F. LEVEL B READINESS MATRIX

| Karar | Kategori | Kanıt hazır? | Veri hazır? | Governance hazır? | Engel |
|---|---|---|---|---|---|
| B1 Capture economic/robustness review | ACTIONS_READY | ✓ (SUPPORTED+verif) | ✗ (spread/slippage/OOS yok) | ✓ | gerçek maliyet + temporal robustness |
| B2 Flag governance reconciliation | INFRASTRUCTURE_GOVERNANCE | ✓ (belgeli çelişki) | ✓ | ✗ (yetki kaydı yok) | kayıt/yetki temizliği |
| B4 Future tuple persistence | INFRASTRUCTURE_GOVERNANCE | ✓ (H4D gap) | ✓ | ✓ | alan spec + Level B onay |
| B3 B2→B3 geçişi | WAITING_FOR_DATA | ✓ | ✗ (2 gün/8 sembol) | ✓ | diversity kriterleri dolmadı |
| B5 Negative-screen production | BLOCKED (kanıt yetersiz) | ✗ (NO_SCREEN_SUPPORTED) | ✗ (yeni dönem yok) | ✓ | yeni pre-reg + yeni periyot |

## G. PRODUCTION / GOVERNANCE CONFLICTS

1. **Flag çelişkisi (BİLİNEN, açık borç — yeni değil):** `.env` 9+ flag ON; kod default OFF; decision-log "validate before enable" diyor ama her flag için tek-tek canlı-onay kaydı yok. Sınıf: `GOVERNANCE_CONFLICT` (belgeli 2026-09-08). Düzeltme controller'da değil — B2 reconciliation.
2. **Kayıt-boşluğu (sistematik):** 9+ tamamlanmış iş (Strategic Lab, 10-Perspective, Mirror, PR1/PR7 kit, vb.) decision-log kaydı olmadan duruyor. Sınıf: `GOVERNANCE_CONFLICT` (tekrarlayan süreç zayıflığı, red-team tarafından 6. kez flag'lendi).
3. **Yetkisiz production değişikliği:** YENİ bulgu yok. Tüm araştırma kodu değişiklikleri gated/test-only; canlı skor/scanner/publish zinciri araştırma tarafından değiştirilmemiş.

## H. PROVENANCE / DATA DEBT (etkiye göre sıralı)

| Borç | Şiddet | Etkilediği | Hangi kararı bloke ediyor | Read-only çözülür mü? |
|---|---|---|---|---|
| Spread/slippage kapsama %0 | CRITICAL | tüm net-P&L iddiaları | B1 economic gate, production release | Hayır (broker verisi) |
| Production tuple provenance yok | CRITICAL | H4D resolution, grade-accuracy | B4, ranking denetimi | Hayır (kod + persist) |
| V0 korelasyon 3 değer | HIGH | E2/V0 confirmatory gate | E2 gate kapanışı | Kısmen (uzlaşma yazısı gerekir) |
| PIT sektör %8.31 | HIGH | sektör/rejim kapıları | sector-aware kararlar | Hayır (dış veri) |
| Corporate-action 485 sembol | HIGH | full-universe metrikleri | eligibility/ürün kapısı | Kısmen (EDGAR) |
| Multi-TF OHLCV (alignment/momentum) | HIGH | H4 reproducibility | tarihsel reconstruction | Hayır (backfill) |
| Export sürüm kontrolü yok | MEDIUM | tekrar üretilebilirlik | baseline lock | Kısmen (dokümante et) |
| Percentile tie tanımı | LOW | ranking spec | formalizasyon | Evet |
| Performans kartı n (5.206/5.216) | — | — | — | **ÇÖZÜLDİ** (kasıtlı ayrım, spec'te belgeli) |
| MFE (46.080/46.581) | — | — | — | **ÇÖZÜLDİ** (ayrı çalışmalar) |
| Dedup semantiği (NVDA) | — | — | — | **ÇÖZÜLDİ** (tutarlı implementasyon; not düşüldü) |
| Decision-log 08-12 boşlukları | MEDIUM | audit trail | yürütücü blok değil | Evet (backfill) |

## I. CLAIM OVERSTATEMENT AUDIT

**Sonuç: uyumlu — materyal overstatement bulunmadı.** Yatırımcı/yöntem materyali disiplinli: tüm tarihsel metrikler [V]erified+caveat; ileri-iddialar [C]onceptual/[S]cenario; MFE≠capture ayrımı korunmuş; negatif bulgular öne çıkarılmış ("What Doesn't Work"); kilitli OOS şeffaf; "production-ready / guaranteed / proven" dili yok. Tek isteğe-bağlı iyileştirme: Slide 6 "sometimes moves" yerine somut +4.83% vs +0.37% sayıları verilebilir (düzeltme değil, güçlendirme).

## J. DEPENDENCY GRAPH

```
B1 CAPTURE:  CAPTURE_SUPPORTED → [GERÇEK MALİYET/SLIPPAGE/LIQUIDITY yok] → Level B economic review
             └─ engel: spread %0 (veri borcu) → ekonomik kapı tam doğrulanamaz
B2 FLAGS:    belgeli çelişki → [yetki kaydı yok] → governance reconciliation
B3 B2→B3:    B2 birikim (2 gün/8 sembol) → [diversity dolmadı] → B3 BLOCKED_BY_DIVERSITY
B4 TUPLE:    H4D PROVENANCE_INSUFFICIENT → [persist edilmiyor] → persistence Level B (H4'ü açmaz)
B5 NEG-SCREEN: NS-1 NO_SCREEN_SUPPORTED → [yeni periyot+pre-reg yok] → BLOCKED
```

## K. DO-NOT-INFER (korunan yorumlar)

compression≠ranking failure · compression≠information loss · behavioral flag≠predictive · MFE≠realized profit · NS-B3 PARTIAL≠production filter · CAPTURE_SUPPORTED≠production approval · VERIFICATION_PASS≠strategy approval · historical underperformance≠no future value · provenance insufficiency≠low resolution · NOT_SUPPORTED≠DISPROVED · NO_SCREEN_SUPPORTED≠no screening information exists.

## L. REQUIRED DECISIONS (insan onayı gerektirenler)

| Karar | Neden var | Mevcut kanıt | Eksik kanıt | Tam karar | Onaylanırsa | Onaylansa bile yasak |
|---|---|---|---|---|---|---|
| B1 capture economic/robustness | tek doğrulanmış pozitif | SUPPORTED+verif | gerçek maliyet, OOS | review pre-reg açılsın mı | Level B economic review başlar | production deploy, yeni target arama |
| B2 flag reconciliation | governance çelişkisi | 9 flag ON, belgeli | flag bazlı yetki tablosu | reconciliation tablosu onaylansın mı | flag kaderi tabloya dökülür | otomatik enable/disable |
| B4 tuple persistence | H4D ölçemedi | alan listesi biliniyor | persist spec | persistence spec onaylansın mı | ileri-dönük provenance altyapısı | H4'ü açmak, tarihi yeniden yazmak |

(B3 ve B5 karar gerektirmez — veri/kanıt bekliyor.)

## M. RECOMMENDED NEXT GOVERNANCE STATE

```
READY:           B1 (economic review), B2 (flag reconciliation), B4 (persistence)
WAIT:            B3 (diversity)
BLOCKED:         B5 (negative-screen production)
CLOSED:          H4, NS-1, RX-CAPTURE-1, tüm yön/prediction hatları
```

## N. FINAL PROGRAM STATE

```
PROGRAM_STATE:
SELECTION_PREDICTIVE_EDGE = NOT_ESTABLISHED
DIRECTION_PREDICTION = CLOSED_NOT_SUPPORTED
H4 = FROZEN_CLOSED
NS1 = CLOSED_NO_SCREEN_SUPPORTED_VERIFIED
RX_CAPTURE = CLOSED_CAPTURE_SUPPORTED_VERIFIED
RX_CAPTURE_PRODUCTION = NOT_APPROVED
FLAGS = GOVERNANCE_RECONCILIATION_PENDING
B2_B3 = WAITING_FOR_DIVERSITY
PROVENANCE_PERSISTENCE = INFRASTRUCTURE_DECISION_PENDING
NEGATIVE_SCREEN_PRODUCTION = NOT_AUTHORIZED
LOCKED_OOS = NOT_OPENED
PRODUCTION_IMPACT = NONE
```

---

**Governance principle:** bu audit FinPilot'ı başarılı göstermek için değil, mevcut durumu denetlenebilir, tekrar üretilebilir, muhafazakâr ve karar-hazır hale getirmek için üretildi. Hiçbir production değişikliği bu audit'in önerisiyle otomatik gerçekleşmez; her Level B→C geçişi insan onayı gerektirir.
