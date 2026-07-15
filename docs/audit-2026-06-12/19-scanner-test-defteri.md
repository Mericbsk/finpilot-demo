# Scanner Değişiklikleri — Tam Test Defteri (bugüne kadar)

**Tarih:** 2026-07-15 · **Amaç:** Scanner'ı değiştirmek/yeni modele geçmek için bugüne kadar yapılan TÜM testler, kriterleri ve sonuçları — tek dürüst kayıt.

> Sistem-tasarımı/ölçüm kaydıdır, yatırım tavsiyesi değildir.

---

## 0. ÖNCE KRİTİK AYRIM: iki farklı "test" var

| Tür | Ne kanıtlar | Ne KANITLAMAZ |
|---|---|---|
| **A. Kod doğruluğu (birim testi)** | Fonksiyon doğru hesaplıyor, çökmüyor, kapalıyken davranışı bozmuyor | Para kazandırdığını **kanıtlamaz** |
| **B. Edge / kârlılık (backtest)** | Sinyalin maliyet-sonrası pozitif beklentisi var mı | — |

**Bugüne kadar A'dan çok yaptık (hepsi geçti); B'den yalnızca BİR bağımsız ölçüm yaptık — ve NEGATİF çıktı.** Kalan "iyi" sonuçlar önceki geliştiricinin kod-yorumlarındaki backtest iddiaları — bizim bağımsız doğrulamadığımız ve taze veriyle çelişen.

---

## 1. KOD DOĞRULUĞU TESTLERİ (bizim, bu çalışmada) — hepsi GEÇTİ

| Test dosyası | Kaç test | Neyi doğruluyor | Sonuç |
|---|---|---|---|
| `test_early_detection.py` | 22 | contraction/rvol feature'ları + WATCH→CONFIRM merdiveni + triple-barrier etiketleme doğru; **entry_ok'u değiştirmiyor** | ✅ 22/22 |
| `test_edge_report.py` | ~12 | Edge Report + factor_ablation + ablate_all doğru sayıyor | ✅ |
| `test_scanner_fixes.py` | 7 | vol_regime_from_df formülü birebir eşleşiyor; legacy import'lar gerçekten ölü; slippage gerçek API'yle çözülüyor | ✅ |
| `test_sentiment.py` | 11 | EODHD sentiment normalizasyon/parse/cache/gate doğru | ✅ |
| **TOPLAM** | **51** | **Kod doğru + additive (canlı davranış değişmez)** | **✅ 51/51** |

**Kriter:** deterministik, ağsız, flag kapalıyken skor birebir aynı. **Sonuç:** hepsi geçti. **Ama:** bu, edge kanıtı DEĞİL — sadece kodun doğru çalıştığı.

---

## 2. EDGE / KÂRLILIK ÖLÇÜMLERİ

### 2A. BİZİM bağımsız ölçümümüz (2026-07-15) — tek gerçek edge testi

**factor_ablation_report.py** · son 2 hafta · n=249 sinyal · TP %10 / SL %5 / 10 gün · triple-barrier.

**Kriter:** bir faktör açmaya değer sayılır ancak: `separates=True` (yüksek bucket hem beklenti hem hit-rate'te daha iyi) **+** her bucket ≥~30 örnek **+** maliyet-sonrası (%0.55) pozitif **+** 2-3 hafta tutarlı.

| Ölçüm | Sonuç |
|---|---|
| **Baseline (tüm sinyaller)** | n=249, hit-rate **%6**, beklenti **−%1.10** (NEGATİF) |
| Tier: CONFIRM (canlı entry_ok) | −%1.44, **%57 stop** — en kötü grup |
| Tier: WATCH | −%0.73, **%91 hiç hareket etmemiş** |
| Tier: SETUP | −%5.00 (n=4, gürültü) |
| composite_score / catalyst / sentiment / conviction | **n_hi=0** — eşiği geçen sinyal yok, ölçülemedi |
| squeeze_factor | n_hi=1 (gürültü) |
| contraction_factor | hi −%0.73 vs lo −%1.21 (daha az kötü) ama **helps=hayır** |
| rvol_acceleration | hi −%2.85 (**daha kötü**) |
| **news_sentiment** (n=164) | hi −%1.61 vs lo −%0.12 → **TERS korelasyon** (yüksek sentiment = daha kötü) |
| lottery / overnight (fade) | zayıf, eşik altı |

**Sonuç: HİÇBİR faktör kriteri geçmedi. Baseline negatif. news_sentiment ters yönlü.** Bu ölçüm "yeni modele geç" demiyor — "hiçbirini canlıya alma, önce bariyerleri düzelt + örneklem büyüt" diyor.

**Bu ölçümün kendi zayıflıkları (çift yönlü uyarı):** n küçük (249, 2 hafta = tek rejim); bariyerler muhtemelen yanlış-ölçekli (TP %10 10-günde çok uzak → %62 time-out → yapısal düşük hit-rate); giriş=scan-kapanış + yfinance forward yaklaşımı gürültü katıyor; SPY-göreli bakılmadı (ne kadarı beta?). Yani "edge kesin yok" da denemez — "bu kurulumda kanıtlanamadı" denir.

### 2B. ÖNCEDEN VAR OLAN denetimler (biz doğrulamadık — kod/rapor kaydı)

| Test | Tarih | Kriter | Sonuç | Güvenilirlik |
|---|---|---|---|---|
| **Profit Core audit** | 2026-05-23 | decile_lift>1 & p<0.05 | **decile_lift 0.728, p=0.995 → EDGE YOK** (rastgeleden kötü) | Sistemin kendi audit'i; 2A ile TUTARLI (negatif) |
| **Component ablation** | 2026-05 (6e09509) | bileşenlerin edge katkısı | **"score & R/R zararlı, regime nötr"** | Sistemin kendi bulgusu |
| **Barrier audit** | 2026-06-12 (n=4066) | rejim×skor-bandı win-rate | Bear-orta (30-55) wr %42.7 PF 2.18 → ×1.3 boost; **yüksek skor (>62) wr %25-29 → ×0.5-0.75 baskı** | Regime-gate'in temeli; "yüksek skor daha kötü" 2A'daki CONFIRM sonucuyla TUTARLI |
| **Alpha-v2 backtest** | 2026-06 (kod yorumu, n=6410) | >=%10 bucket'ta decile lift | gap>3% lift 1.74; RVOL lift 1.24→1.50; squeeze short>=20% ×2.57; 52w-high fade 0.68 | **Geliştirici iddiası — biz doğrulamadık; 2A taze veriyle ÇELİŞİYOR** |
| **Conviction tier lab** | 2026-06 (kod yorumu, n=6410) | faktör-hizalı bucket hit-rate | short>=15 & gap>=3 → >=%5 %73, >=%10 %69 | **Geliştirici iddiası — doğrulanmadı; 2A'da conviction n_hi=0 (ölçülemedi)** |

---

## 3. NET ÖZET — bugüne kadar ne kanıtlandı?

1. **Kod doğru çalışıyor** (51/51 birim testi). Ama bu edge değil.
2. **Bağımsız tek edge ölçümümüz (2 hafta, n=249) NEGATİF:** baseline −%1.10, hiçbir faktör ayrışmadı, en "güvenilir" sinyaller (CONFIRM) en kötü, news_sentiment ters.
3. **Sistemin kendi eski audit'i de EDGE YOK diyordu** (decile_lift 0.728) — yani iki bağımsız ölçüm (Mayıs Profit Core + Temmuz ablation) aynı yönde: **kanıtlanmış edge yok.**
4. **"İyi" görünen tüm rakamlar** (alpha-v2 lift 1.7, conviction %73) **önceki geliştiricinin doğrulanmamış kod-yorumu iddiaları** ve taze veriyle çelişiyor.
5. **Barrier audit'in "yüksek skor daha kötü" bulgusu**, taze ablation'daki "CONFIRM en kötü" sonucuyla örtüşüyor — bu tutarlılık, ölçümün gerçek bir şeyi gösterdiğine işaret (skor ile ileri getiri arasında pozitif ilişki yok, hatta ters).

**Karar için tek cümle:** Bugüne kadarki testler "yeni modele geç" için **yeterli kanıt üretmedi** — aksine iki bağımsız edge ölçümü (Mayıs + Temmuz) "edge yok/negatif" diyor. Kod hazır ve testli; eksik olan **kanıtlanmış kârlılık.**

---

## 4. SIRADAKİ DOĞRU TESTLER (edge'i adil ölçmek için)

1. **Bariyer düzeltmesi:** ATR-ölçekli TP/SL veya grid (örn. TP %5/SL %3; ve per-signal ATR katları) → mevcut %10/%5 testi negatife eğimli.
2. **Benchmark-göreli:** her sinyalin getirisinden aynı dönem SPY/IWM getirisini çıkar → beta mı, sinyal mi ayır.
3. **Örneklem büyüt:** haftalık biriktir; 2 hafta = tek rejim, karar için yetersiz.
4. **composite_score n_hi=0 araştır:** skala/eşik doğru mu? median-split kullan.
5. **news_sentiment ters etkisini** daha fazla veriyle sına → tutarsa **fade** olarak kullan.
6. Ancak bir sürüm **maliyet-sonrası pozitif + yeterli n + 2-3 hafta tutarlı** çıkarsa → gölge-mod → canlı/Telegram.
