# B2-0 — Flag User-Facing Impact & Flag-Configuration Provenance Gate — SONUÇ RAPORU

**Tarih:** 2026-09-23 · **Level:** A (read-only) · **Production impact:** NONE
**Prereg:** `reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md` (LOCKED v2, SHA-256 `fe4ceab1…2133c0`)
**Flag trace (Q4 öncesi):** `data/backtest_out/b2_0_flag_scope_trace_2026-09-23.json` (SHA-256 `838ab9de…ee63b7`)
**Runner:** `research/b2_0_flag_user_facing_impact_2026_09_23.py`
**Sonuç JSON:** `data/backtest_out/b2_0_flag_user_facing_impact_2026-09-23.json`. İki ardışık çalıştırma byte-identical çıktı üretti (determinism).

---

## TOPLAM VERDICT: `INCOMPLETE`

**Tanım (§9, öncelik 5):** Yeniden kurulabilen hiçbir flag kullanıcıya dönük etki göstermedi, ama en az bir kapsam-içi flag `NOT_RECONSTRUCTIBLE`.

- "Etki yok" iddia EDİLMEZ.
- Sonraki adım (§9 eşleme): kapsamlı bir provenance çözüm adımı. B2-full ve B4 sırası Meriç kararıdır.

**Sınır:** Bu sonuç yalnızca counterfactual flag çıkarımı altındaki davranışsal farkı ölçer. Predictive, ekonomik, fayda, zarar ya da yetki kanıtı değildir. Hiçbir flag'in açılması veya kapatılması gerektiği anlamına gelmez.

---

## Soru bazında sonuçlar

| Soru | Sonuç | Özet |
|---|---|---|
| Q0 Integrity | **PASS** | 19 manifest SHA + prereg + trace = 21/21 `SHA_MATCH`. DB kopyası manifestle eşleşiyor. §2 olgularının 7/7'si yeniden üretildi. CONFLICT yok |
| Q1 Yayın (bağlam) | **DORMANT** | Son `sent` kaydı `daily_free` 2026-09-09. Son başarılı Telegram teslimi 2026-09-09T11:42:18Z (toplam 72 ok). Web public snapshot tarihi 2026-09-09 |
| Q2 Flag-config provenance | **CONFIG_HASH_MATCH_BY_ENUMERATION** | Tek fark: `DISTRIBUTION` (yerel=0, snapshot=1). Ayrıntı aşağıda |
| Q3A Snapshot fidelity | **PASS** | 5/5 kontrol: candidate_hash, snapshot_id, sıralı O1, O2, O3. Repo fonksiyonları kullanılmadan bağımsız yazılmış bir implementasyon da O1 ve hash'i birebir tutturdu |
| Q3B Reconstructibility | 7 PASS / 2 FAIL | CONVICTION_TIERS ve ALPHA_V2 = FAIL |
| Q4 Leave-one-out | 7 flag `NO_OBSERVED_USER_FACING_IMPACT` | 2 flag `NOT_RECONSTRUCTIBLE` |

---

### Q2 — Ayrıntı

09-09 snapshot damgası `a5e0d8b7c9d5@ff9658a`. Kilitli 18 anahtar × {0,1} uzayında (2^18 aday) tek bir konfigürasyonla eşleşti: yerel `.env` extract'ının aynısı, tek farkla `FINPILOT_ENABLE_DISTRIBUTION=1`.

- Aynı sonuç 08-03, 08-11, 08-14, 08-24 ve 08-27 snapshot'larında da geçerli (her biri kendi commit'iyle).
- 07-29 ve 07-30 = `NO_MATCH`. O tarihlerde anahtar kümesi farklıymış; kilitli uzay genişletilmedi.
- Bağımsız hesap ile repo fonksiyonu (kontrollü env, kontrollü git) her snapshot'ta aynı hash'i verdi.

**Yorum sınırı (§7, zorunlu):**
> A hash match establishes a FINPILOT_ENABLE* configuration consistent with the snapshot stamp under the locked hash function and candidate value space. It does not independently prove the physical/runtime origin of the snapshot, the state of non-FINPILOT_ENABLE* configuration, or the absence of uncommitted code changes.

**Üretim yeri (2d):** `UNKNOWN`. Mevcut kanıt bu repo'nun `data/` dizinine yazan bir ortamla tutarlı: snapshot üretimi, DB yazımı ve snapshot commit'i ~2 dakika içinde gerçekleşmiş. Ama bu, runtime host'unu kanıtlamaz.

**Ek betimsel kanıt (verdict girdisi değil):** Export'taki satır bazlı `score_feature_flags` alanı, 1508 satırda 4 skor flag'inin (squeeze, edgar, lottery, overnight) `true` olduğunu gösteriyor.

---

### Q3B — Ayrıntı

| Flag | Q3B | Gerekçe |
|---|---|---|
| SQUEEZE_FACTOR, LOTTERY_FADE, OVERNIGHT_GAP, EDGAR_CATALYST, FRED_MACRO | PASS | Tam konfigürasyonla recommendation_score (tol 0,01) ve composite_score (tam eşitlik) 1508/1508 satırda yeniden üretildi. FRED çarpanı 1,0 varsayıldı (ağ çağrısı yok); precondition geçtiği için bu varsayım saklı değerlerle tutarlı |
| EXECUTION_POLICY | PASS | `execution_feasible` / `selection_eligible` ana-yol satırlarında 0 uyumsuzluk |
| PORTFOLIO_ADV_LIMIT | PASS | `position_cap_reject_reason` ana-yol satırlarında 0 uyumsuzluk (bkz. implementation correction) |
| **CONVICTION_TIERS** | **FAIL** | `atr_pct_daily` export'ta saklanmıyor. 1794 satır tekil olarak yeniden üretildi. 7 satırın tier'ı ATR'ye bağlı: MU, AMD, QCOM, SMCI, SMMT, IBRX, BE. Hepsi yayınlanan listede ve hepsi saklı değerle *tutarlı*, ama kilitli katı kural tekil yeniden üretim istiyor |
| **ALPHA_V2** | **FAIL** | Squeeze ağırlıkları (`features.py:151`) ve stop/TP çarpanları (`risk_engine.py:204`) ham short/float ve ATR-bar girdilerine ihtiyaç duyuyor. Bunlar export'ta yok |

---

### Q4 — Leave-one-out (C_full ile C_full − {f})

| Flag | Sınıf | O1 | O2 üyelik/sıra | O3 | public değişen satır |
|---|---|---|---|---|---|
| EXECUTION_POLICY | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| PORTFOLIO_ADV_LIMIT | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| SQUEEZE_FACTOR | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| LOTTERY_FADE | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| OVERNIGHT_GAP | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| EDGAR_CATALYST | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| FRED_MACRO | NO_OBSERVED | 10/10 | değişmedi | 10/10 | 0 |
| CONVICTION_TIERS | NOT_RECONSTRUCTIBLE | — | — | — | — |
| ALPHA_V2 | NOT_RECONSTRUCTIBLE | — | — | — | — |

- ROW_ORDER_INTEGRITY tüm karşılaştırmalarda korundu.
- N sınırında tuple-eşit grup yok: O2 ve O3 için grup boyutu 1; O1'de truncation yok, çünkü L=10 < 50.
- **All-OFF (ikincil, betimsel):** Sadece yeniden kurulabilen 7 flag kapatılabildi; CONVICTION_TIERS ve ALPHA_V2 hesaplanamadı. Bu alt kümede: NO_OBSERVED, O1 10/10.

**Counterfactual'ların boş olmadığının kontrolü (bağımsız hesap):** Flag kapatıldığında composite_score değişen satır sayısı:
- SQUEEZE: 1232/1508
- LOTTERY: 1503/1508
- OVERNIGHT: 843/1508
- EDGAR ve FRED: 0 (catalyst_factor=0, çarpan=1,0)

PORTFOLIO_ADV_LIMIT kapalıyken 1252 ana-yol satırının `adv_position_cap` reddi kalkıyor, ama bunların hiçbiri graded değil. EXECUTION_POLICY bu gün hiçbir satırın uygunluğunu değiştirmiyor. Yani müdahaleler gerçek değişiklikler üretiyor; bu değişiklikler kullanıcıya dönük nesnelere ulaşmıyor.

---

## Verdict dışı gözlemler (karar girdisi olarak Meriç'e; sınıflandırmayı değiştirmez)

1. **10 Eylül flag-impact raporu kullanıcıya dönük sıralamayı ölçmemiş.** O rapor 1.792 sembolde rank değişimi saydı, ama bunu composite sıralama üzerinde yaptı. Yayınlanan sıralamanın 4. anahtarı ise `ranking_score = legacy_quality_score` (`LEGACY_COMPOSITE_RANKING=0`, `evaluate.py:722`). `legacy_quality_score` lottery/overnight faktörlerini flag'den bağımsız kullanıyor (`score_engine.py:193-222`). Fiyatı olan ana-yol satırlarında `ranking_score` hiçbir zaman boş değil, bu yüzden composite'e fallback yok. Sonuç: LOTTERY_FADE, OVERNIGHT_GAP ve SQUEEZE (ALPHA_V2 açıkken) composite'i değiştiriyor ama yayınlanan listeyi değiştirmiyor. B2'yi başlatan "flag'ler kullanıcı sıralamasını oynatıyor" endişesi, bu üç flag için 09-09 snapshot'ında gözlenmedi.
2. **Graded listenin kapısı CONVICTION_TIERS.** Export'ta `tier` alanı yok (0/1801), bu yüzden grade yalnızca `conviction_tier`'dan geliyor. Flag kapalıyken kod her satıra `('', 0.0)` döndürüyor (`features.py:221`). Kod yolu, graded listenin boş kalacağını ima ediyor. Bu bir verdict DEĞİL: kilitli Q3B ön koşulu 7 satırda sağlanamadı. Ama kullanıcıya gösterilen listenin varlığını belirleyen flag'in bu olduğu kod düzeyinde açık.
3. **ALPHA_V2 da liste üyeliğine dokunuyor.** Squeeze ağırlıkları `conviction`'daki `short_strong` koşulunu, `legacy_quality_score`'u ve `v2_score`'u besliyor. Etkisi ölçülemedi.
4. **Kodda okuyucusu olmayan açık flag'ler.** EARLY_TIER, FUNDAMENTALS ve NEWS `.env`'de ON, ama `ff9658a`'da hiçbir kod bunları okumuyor. B2-full envanterine not edildi.
5. **Yayın durumu.** Yayın 09-09'dan beri DORMANT. Yerel `DISTRIBUTION=0`, snapshot anında ise 1'di. DISTRIBUTION 09-09 sonrası kapatılmış görünüyor. Bu, Q2 eşleşmesiyle ve DB mtime'ıyla tutarlı; tek başına bir kanıt değil.
6. **PROVENANCE_GAP.** `broadcast_queue` config_sha saklamıyor → B4 borcu. Ayrıca `atr_pct_daily` ve ham squeeze girdileri (short/float) export'ta saklanmıyor. İki NOT_RECONSTRUCTIBLE sonucunun doğrudan nedeni bu. B4 persistence spec'ine girdi olarak önerilir.

---

## Implementation correction (belgeli, gizlenmedi)

- **İlk çalıştırma:** PORTFOLIO_ADV_LIMIT'in Q3B ön koşulu 293 satırda uyumsuz çıktı ve flag FAIL oldu. Sebep bir uygulama hatasıydı: `position_cap()` formülü, bu fonksiyondan hiç geçmeyen hata-şablonu satırlarına da uygulanmıştı (`_unavailable_result`, `evaluate.py:69-107`; `scan_status` var, `score_input` yok, entry_ok=False, tier yok, fiyat yok).
- **Düzeltme:** Execution flag'lerinin ön koşul ve dönüşümleri ana-yol satırlarıyla sınırlandı. Şablon satırları sabit tutuldu; composite flag'lerde zaten böyle yapılıyordu. Ayrıca şablon kümesinin `score_input`'u olmayan satırlarla birebir aynı olduğu (293) ve hiçbirinin nesnelere giremeyeceği doğrulandı.
- **Sonuç ve kural:** PORTFOLIO_ADV_LIMIT FAIL → PASS, sınıfı NO_OBSERVED. Kilitli kural değişmedi. Düzeltme, sonuca göre değil kod provenance'ına göre belirlendi, ama ilk sonuç görüldükten sonra yapıldı. Bu yüzden burada ve decision-log'da açıkça kayıtlı.
- **Toplam verdict'e etkisi:** Yok. Düzeltme olmasaydı da verdict INCOMPLETE olurdu.

---

## Sınırlamalar

- Q4 tek güne (09-09) dayanıyor. PORTFOLIO_ADV_LIMIT ve EXECUTION_POLICY için "etki yok" sonucu güne özgü: 1252 ret var ama o gün hiçbiri graded değil.
- Sandbox CPython 3.10 ile çalıştı. `datetime.UTC = timezone.utc` alias'ı eklendi; hesaplamaya etkisi yok ve Q3A PASS bunu destekliyor.
- **Bağımsızlık sınırı:** Prereg'i, trace'i ve runner'ı aynı ajan yazdı. Bağımsız bir yeniden doğrulama (B1'deki gibi, farklı implementasyonla) önerilir.
- F, kod trace'inin doğruluğuna bağlı.

## Karar noktaları (Meriç — öneri, onay değil)

1. **Prereg v3 amendment:** Girdiden bağımsız OFF-durumları için (CONVICTION_TIERS) daha zayıf ama açık bir ön koşul tanımlanabilir. Bu yapılırsa sonuç büyük olasılıkla CONVICTION_TIERS = USER_FACING_IMPACT olur. Bu yeni bir kilit ve yeni bir koşum gerektirir.
2. **B2-full kapsamı:** Mevcut kanıtla B2-full'un odağı composite flag'leri değil CONVICTION_TIERS ve ALPHA_V2 olmalı. Kullanıcıya dönük listeyi fiilen belirleyen flag'ler bunlar.
3. **B4 spec girdisi:** `atr_pct_daily`, ham short/float girdileri ve `broadcast_queue.config_sha` persist edilirse gelecekteki counterfactual'lar yeniden kurulabilir olur.
4. **Distribution'ın yeniden açılması:** Yayın DORMANT. Yeniden açmadan önce CONVICTION_TIERS ve ALPHA_V2 için yetki kararının verilmesi önerilir.
