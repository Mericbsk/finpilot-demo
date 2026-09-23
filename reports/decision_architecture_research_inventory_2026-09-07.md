# Karar Mekanizması Araştırma Envanteri — "Bugüne kadar ne yaptık?"

Tarih: 2026-09-07
Level: A (envanter; hiçbir kod değiştirilmedi)
Tetikleyici: Kullanıcı — "problemimiz karar mekanizması galiba. Bununla ilgili hangi çalışmaları yaptık bugüne kadar?"
Kaynak: `docs/governance/decision-log.md` + `reports/` + `research/`

---

## Karar mimarisi 5 katmandan oluşur — her birini ayrı test ettik

```
[1. SİNYAL SEÇİMİ]   hangi hisse → entry_ok / selector
[2. REJİM]           piyasa hangi durumda → regime flag
[3. POZİSYON]        ne kadar → sizing (dyn_kelly, position_pct)
[4. ÇIKIŞ]           ne zaman çık → TP/SL, barrier, exit timing
[5. ÖĞRENME]         sonuçtan öğren → weight update, calibration
```

Her katmanda ne yaptığımızı ve ne bulduğumuzu aşağıda listeliyorum.

---

## KATMAN 1 — Sinyal seçimi (hangi hisse)

| Çalışma | Tarih | Bulgu | Kaynak |
|---|---|---|---|
| `entry_ok` kapı analizi | 2026-08-13 | Regime kapısı winner'ların **%50,7'sini** öldürüyor; kapıları gevşetmek genel sonucu iyileştirmiyor — sorun seçim kriterinin kendisi | `winner_anatomy_thought_experiment_2026-08-14.md` §8-11 |
| Winner anatomy (düşünce deneyi) | 2026-08-14 | `entry_ok` +5% winner'ların **%97,5'ini kaçırıyor**; kaçırılan winner'lar daha düşük skorlu, daha ucuz, zirveden uzak | `winner_anatomy_thought_experiment_2026-08-14.md` |
| High-RVOL tüm evren | 2026-08-12 | High-RVOL pozitif selector **reddedildi** — rejected/extreme outcome artefaktı | decision-log |
| Attention map pivot | 2026-08-14 | "Hangi hisse yükselecek?" → "hangi hisse olağandışı?" çerçevesi kanıtlandı (hareket büyüklüğü, yön değil) | `attention_map_research_2026-08-14.md` |
| Day-1 confirmation matrix | 2026-08-14 | "T+1'e bekle, teyit al" işe yaramıyor — ilk gün hareketin %106,7'sini yakalıyor | `day1_confirmation_matrix_2026-08-14.md` |
| Master deney denetimi | 2026-08-12 | Tahmin çerçevesi 6 bağımsız yoldan kapandı → **PIVOT** kararı | `master_audit_application_2026-08-12.md` |

**Özet:** Seçim katmanı en çok test edilen katman. Sonuç: **statik skor + kapı yaklaşımı çalışmıyor** — entry_ok değer eksiltiyor, winner'ları kaçırıyor. Attention map (betimleyici) tek canlı alternatif.

---

## KATMAN 2 — Rejim (piyasa hangi durumda)

| Çalışma | Tarih | Bulgu | Kaynak |
|---|---|---|---|
| Rejim günleri (F1) | 2026-08-14 | `entry_ok` yalnızca strong-up günlerde pozitif (+2,69%) — piyasa bağımlı | `comprehensive_final_research_2026-08-14.md` |
| Rejim × direction hücresi | 2026-08-14 | `regime=False × direction=False` en yüksek winner rate (%22,4) ve tek pozitif medyan (+0,19%) | `winner_anatomy_thought_experiment_2026-08-14.md` |
| Direction-context battery | 2026-09-03 | Rejim + breadth + sektör yoğunlaşması yönü koşullamıyor — discovery'de görülen desen OOS'ta öldü | `direction_context_battery_2026-09-03.md` |
| Experiment #1 (Rejim × Tier × eşik) | 2026-09-03 | Rejim eklenince yön bilgisi çıkmıyor; High tier her rejimde negatif; **tier rejimden baskın** | `direction_threshold_matrix_2026-09-03.md` |

**Özet:** Rejim tek başına yön üretmiyor. Rejim × attention kesişimi de üretmiyor. Rejim bir "bağlam" — yön değil.

---

## KATMAN 3 — Pozisyon boyutlandırma (ne kadar)

| Çalışma | Tarih | Bulgu | Kaynak |
|---|---|---|---|
| Equal-weight vs ATR-parity | 2026-08-12 | Eligible ATR-parity medyan günlük -%0,313, max drawdown **-%51,70** | decision-log (uçtan uca tamamlama) |
| Sizing diagnostic | 2026-08-12 | High-RVOL eligible $10K → **$9.160** (negatif) | decision-log |

**Özet:** Sizing en az test edilen katman. Mevcut dyn_kelly/position_pct alanları var ama hiçbir matched-control ile doğrulanmadı. **Açık boşluk.**

---

## KATMAN 4 — Çıkış (ne zaman çık)

| Çalışma | Tarih | Bulgu | Kaynak |
|---|---|---|---|
| High-RVOL first-touch TP bataryası | 2026-08-12 | Fixed TP ve ATR TP ailelerinde eligible 5g maliyet-sonrası **negatif** | `high_rvol_first_touch_tp_battery_2026-08-12.md` |
| High-RVOL raw-OHLC exit gate | 2026-08-12 | "Day 5 çık" / "Day 8 çık" desteklenmedi; raw-bar control lift negatif | `high_rvol_raw_ohlc_exit_gate_2026-08-12.md` |
| 1-10 günlük horizon proxy | 2026-08-12 | Ne 5. gün ne 8. gün çıkışı desteklenmedi; exit logic Level B olarak donduruldu | `high_rvol_horizon_battery_2026-08-12.md` |
| Day-1→Day-5 monoton ilişki | 2026-08-14 | D1<-3% → D5 med -%5,4; D1>5% → D5 med +%6,7 — ama ilk gün %106,7'sini yakalıyor | `day1_confirmation_matrix_2026-08-14.md` |

**Özet:** **En çok çalışılan ama en az çözülen katman.** Hiçbir sabit çıkış kuralı (TP%, ATR, gün) desteklenmedi. MFE %4,83 vs captured +%0,37 farkı burada yaşıyor — çıkış mimarisi bırakılan potansiyelin ana kaynağı.

---

## KATMAN 5 — Öğrenme / kalibrasyon

| Çalışma | Tarih | Bulgu | Kaynak |
|---|---|---|---|
| Score calibration (Brier) | 2026-08-11 | Brier skill **-0,019/-0,030** — rastgeleden kötü | `scanner_research_synthesis_10_perspectives_2026-08-11.md` |
| Zaman-içi kararlılık (F3) | 2026-08-14 | Hiçbir feature aydan aya tutarlı değil (ATR 2025-09: +0,21 → 2026-07: -0,28) | `comprehensive_final_research_2026-08-14.md` |

**Özet:** Skor kalibre değil ve özellikler zamanla kayıyor. Öğrenme döngüsü henüz kurulmadı — bu Slide 9'daki "Learning" halkasının karşılığı ama henüz ürünleşmedi.

---

## Büyük resim — karar mimarisi envanteri

| Katman | Test sayısı | Sonuç | Durum |
|---|---|---|---|
| 1. Sinyal seçimi | 6+ batarya | entry_ok değer eksiltiyor; attention map tek canlı alternatif | **Kapandı (negatif)** → pivot attention |
| 2. Rejim | 4+ batarya | Yön üretmiyor; bağlam olarak zayıf | **Kapandı (negatif)** |
| 3. Sizing | 2 test | En az test edilen; ATR-parity negatif | **Açık boşluk** |
| 4. Çıkış | 4+ batarya | Hiçbir sabit kural desteklenmedi; MFE gap burada | **Kapandı (negatif)** → en büyük fırsat |
| 5. Öğrenme | 2 test | Kalibrasyon yok; kayma var | **Açık boşluk** |

## Deck ile bağlantı

Bu envanter, sunumun Slide 5 (What Doesn't Work) ve Slide 6 (Better Decision Architecture) arasındaki köprüyü besliyor:

- **Slide 5**'teki her negatif bulgu bir katmana işaret ediyor
- **Slide 6**'daki "better decision architecture" = bu 5 katmanın yeniden tasarımı
- **Slide 4**'teki MFE gap (%4,83 vs +%0,37) = Katman 4'ün (çıkış) ölçülmüş maliyeti

**En büyük açık araştırma fırsatı:** Çıkış katmanı (Katman 4). Sinyal üretimi ölçüldü, seçim test edildi, ama "tepeyi görüp yakalayamama" sorunu çıkışta. Bu, deck'in ana araştırma vaadiyle örtüşüyor.

## Governance

- Hiçbir production/scanner/score/entry-exit/publish davranışı değiştirilmedi.
- Bu bir envanter — yeni deney yok, mevcut çalışmaların yapılandırılması.
- Locked OOS NOT_OPENED.
