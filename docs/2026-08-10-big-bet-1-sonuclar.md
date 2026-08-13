# Strategic Thinking Lab — Deney Sonuçları (2026-08-10)

Statü: Level A (araştırma, üretim değişikliği yok). Kaynak: `2026-08-10-finpilot-strategic-thinking-lab-v1.md`'deki Experiment Factory'nin gerçekten çalıştırılabilir alt-kümesi.

## 0. TRİYAJ — 72 deneyin durumu

Belgedeki 72 deneyin **tamamını** koşmak mümkün değildi. Üç kova:

**(A) Bugün, mevcut veriyle koşuldu (5 deney — bu raporun konusu):** ATR look-ahead kod-audit'i · 3-giriş-noktası + bariyersiz drift-eğrisi · Reverse-ranking testi · Random-entry vs gerçek-sinyal testi · Concentration-kısıtlı portföy simülasyonu.

**(B) Yeni veri gerektiriyor, bugün koşulamadı (~28 deney):** intraday-path/MAE-MFE-erken-validasyon (dakika-bar gerektirir) · opsiyon/pozisyonlanma-faktörleri (erişim yok, önceden blocked) · gerçek execution/spread/fill (broker-veri gerektirir) · gerçek-sektör-etiketiyle tam-evren testi (EODHD fundamentals ağ-erişimi gerektirir — bu oturumda denenmedi, ayrı görev) · event-driven/earnings-alt-küme (haber-feed zaman-damgası gerektirir) · likidite-kovası/spread-testleri (spread-kaynak kapsamı zaten %0) · macro-rejim katmanı (yeni veri-seti) · vb.

**(C) Kod-deneyi değil, ürün/kullanıcı-pilotu gerektiriyor (~39 deney):** kullanıcı-motivasyon-anketi · Grade açık/kapalı A/B · kalibrasyon-eğrisi-gösterimi · top-10/renk-kodlama davranışsal-etkisi · case-based eğitim-modülü · market-memory-prototipi · segment-bazlı arayüz · B2B-görüşmeleri · vb. Bunlar gerçek kullanıcı-etkileşimi veya ürün-değişikliği gerektirir, bu oturumun (araştırma-only, Level A) kapsamı dışında.

Aşağıda (A) kovasının **beş** deneyinin tam sonuçları var — hepsi kod + mevcut veriyle (price_cache, edge_recheck.csv, sector_map_full.csv) üretildi, yeni harici veri gerekmedi.

---

## 1. ATR LOOK-AHEAD AUDİT (Big Bet #1a)

**Yöntem:** Production kodunda (`scanner/evaluate.py`) ve backtest kodunda (`edge_recheck.py`) ATR/RSI/MACD/RVOL'ün hangi veri-penceresini kullandığı satır-satır denetlendi.

**Bulgu — beklenmedik ama net:**
- `edge_recheck.py`'nin kendi ATR hesabı (`atr_pct`, satır 70-83) **klasik gelecek-sızıntısı taşımıyor**: pencere `ei-14..ei-1` (giriş barından önceki 14 gün), MAE/getiri-ölçüm-penceresiyle (giriş sonrası) hiç çakışmıyor. **ATR→MAE bulgusu (IC −0.51) bu açıdan sağlam.**
- Ama daha ciddi, önceden hiç belgelenmemiş bir sorun bulundu: **`scanner/evaluate.py:403,412-413,497-498`** — canlı taramada ATR, RSI, MACD, hacim-çarpanı hep `df_1d["..."].iloc[-1]` / `df_15m["..."].iloc[-1]` ile hesaplanıyor, yani **"bugünün" barının kendisi.** `core/scheduler.py`'de ana tarama işi **`interval_minutes=60`** ile saatlik/gün-içi çalışıyor. Bu, canlı sinyalin "bugün" verisinin çoğu zaman **tam kapanmamış, parçalı bir gün** olduğu anlamına geliyor — özellikle hacim-çarpanı (bugünün-hacmi / 10-günlük-ortalama) günün hangi saatinde ölçüldüğüne göre sistematik yanlı olur (öğlen ölçülen RVOL, kapanışa-yakın ölçülenden yapısal olarak düşük çıkar).
- **Sonuç:** Klasik "look-ahead" değil, daha isabetli adı **train/serve skew** — canlı skor parçalı-gün verisiyle, backtest'in ATR'si tam-gün verisiyle üretiliyor. Bu, P0'da zaten bilinen "score-replay INSUFFICIENT_DATA" bulgusunun kök-nedenlerinden biri olabilir ve entry_ok/conviction inversiyonlarına da katkıda bulunuyor olabilir (gün-içi erken-ateşlenen sinyaller sistematik-farklı özellik-profiline sahip olabilir).

**Karar:** ATR-MAE risk-bulgusu **çürümedi**, sağlam kaldı. Ama yeni ve önemli bir altyapı-bulgusu: **canlı skor-hesaplaması gün-içi parçalı-veri kullanıyor** — bu ayrı bir Level-B-adayı düzeltme (feature'ları yalnız önceki-günün-kapanışına-kadarki veriyle hesaplamak, ya da gün-içi-ilerleme-yüzdesine göre normalize etmek).

---

## 2. 3-GİRİŞ-NOKTASI + BARİYERSİZ DRİFT EĞRİSİ (Big Bet #1b)

**Yöntem:** 1.400/1.926 sembol (%73 evren), 36.932 satır. Üç giriş noktası (sinyal-close / ertesi-open / ertesi-close) için t+1..t+10 kümülatif getiri, ham + SPY-excess + sektör-excess (korelasyon-proxy).

**Bulgu:** **Üç giriş noktası arasında SPY-excess'te anlamlı fark YOK.** Hepsi düzyanız, sıfıra-yakın, t=1..10 boyunca −0.4/+0.1 bandında dalgalanıyor. Temiz bir "tepe-sonra-sönüş" (half-life) eğrisi hiçbirinde yok.

**Karar:** "Edge sinyal-kapanışında var ama açılışta kayboluyor" hipotezi **desteklenmiyor** — hiçbir giriş noktasında drift yok. Bu, "giriş-zamanlaması yanlış" açıklamasını **eler**; sorun daha temel (sinyalin kendisinde yön-bilgisi yok, ne zaman girersen gir).

**Yan-bulgu (dikkatli okunmalı):** Sektör-excess (yalnız %24-doğru proxy'yle) t=6'dan itibaren +0.3/+0.6 pozitif eğilim gösteriyor, üç giriş-noktasında da tutarlı. Gerçek-sektör-etiketle doğrulanmadan güvenilmez ama önceki 143-sembol sektör-trend bulgusuyla yönü aynı — ayrı deneyle (Big Bet #3) takip edilmeli.

---

## 3. REVERSE-RANKING TESTİ

**Yöntem:** composite_score ve finpilot_score, günlük-kesitte ALT-%20 (ters-sıralama/fade-adayı) vs ÜST-%20 (normal) vs baseline, IS/OOS (c2c5_net).

**Bulgu — programın en güçlü yeni sinyali:**

| composite_score | IS medRet | OOS medRet |
|---|--:|--:|
| baseline | −0.639 | +0.617 |
| ÜST-%20 (normal) | −0.647 | +0.517 |
| **ALT-%20 (reverse)** | **−0.155** | **+1.018** |

**ALT-%20, hem IS hem OOS'ta hem baseline'ı hem üst-%20'yi geçiyor — iki bağımsız dönemde tutarlı yön.** Bu, tüm programda IS/OOS-tutarlı ilk **doğrudan getiri-sinyali** olabilir (composite_score'a özgü; finpilot_score'da top/bottom-%20 IS'te aynı satırları seçti — düşük-kardinalite/tie-artefaktı, gerçek sinyal değil).

**Karar:** `EVIDENCE zayıf-orta` — matched-random kontrol ve cluster-robust CI ile (aynı-gün kümelenme riski var) doğrulanmadan "kanıtlanmış" sayılamaz, ama şu ana kadarki EN güçlü aday. Composite_score'u **tersine çevirip fade-adayı olarak** pre-registered, ayrı bir OOS-penceresinde tekrar test etmek mantıklı sıradaki adım.

---

## 4. RANDOM-ENTRY vs GERÇEK-SİNYAL (aynı exit-mekaniği)

**Yöntem:** Gerçek sinyaller (n=53.754) vs rastgele (symbol,date) kontrolü (n=3.000), **aynı** triple-barrier exit-mekaniğiyle (TP=2×ATR/SL=1×ATR/H=5).

| | tb_ret win% | tb_ret medRet | c2c5_net win% | c2c5_net medRet |
|---|--:|--:|--:|--:|
| Gerçek sinyaller | 44.3 | −0.952 | 49.8 | −0.025 |
| Random-entry kontrol | 39.7 | −1.538 | 45.0 | −0.500 |

**Bulgu:** Gerçek sinyaller, random-entry'yi hem win-rate'te hem medyanda **tutarlı biçimde geçiyor** (dört metrikte de).

**Karar:** Taban-sinyal-üretimi (RSI/hacim/MACD confluence — "bir şey oluyor" tespiti) rastgeleden **gerçekten daha iyi.** Sorun tabanda değil, **downstream ranking'te** (composite_score — bkz. §3, ters çalışıyor). Bu, "hiçbir yerde bilgi yok" hükmünü nüanslıyor: iki ayrı katman var, biri (taban-tespit) zayıf-ama-gerçek bilgi taşıyor, diğeri (composite-ranking) o bilgiyi **bozuyor.**

---

## 5. CONCENTRATION-KISITLI PORTFÖY (yaklaşık)

**Yöntem:** Günlük top-10 (composite_score), kısıtsız vs max-3/sektör kısıtlı, eşit-ağırlık günlük-getiri yaklaşıklaması. n=52-56 gün (küçük-n uyarısı geçerli).

| | günlük-ort | std | Sharpe~ | CVaR5% | maxDD | ort-en-yoğun-sektör-payı |
|---|--:|--:|--:|--:|--:|--:|
| Kısıtsız top-10 | +0.071% | 7.08 | 0.010 | −26.12% | −49.0% | **%61.79** |
| Kısıtlı (max 3/sektör) | +0.650% | 3.94 | 0.165 | −10.55% | −22.0% | %29.81 |

**Bulgu — çarpıcı:** Mevcut kısıtsız top-N seçimi, ortalama günün **%62'sini tek sektöre** yığıyor — hiç fiili çeşitlendirme yok. Yalnızca max-3/sektör kısıtı eklemek (yeni alfa yok, aynı composite_score sıralaması): volatiliteyi yarıya, CVaR-kuyruk-riskini yarıdan-aza, maksimum-drawdown'ı yarıdan-aza indiriyor **ve** ortalama-getiriyi de artırıyor.

**Karar:** `EVIDENCE` (küçük-n ile, n~52-56 gün) — Portfolio Opportunity Quality (POQ) hipotezinin ilk güçlü kanıtı. Alfa gerektirmeyen, düşük-maliyetli, yüksek-etkili bir düzeltme adayı — daha büyük örneklemle (tüm-evren, daha uzun pencere) doğrulanmalı ama yön çok net.

---

## 6. GÜNCELLENMİŞ BIG BET DURUMU

| Bahis | Önceki statü | Bu turdan sonra |
|---|---|---|
| #1 Foundational Integrity | Test-öncesi | **Kısmen tamamlandı.** ATR-bulgusu sağlam kaldı (çürümedi); giriş-zamanlaması hipotezi ELENDİ (drift yok, hiçbir noktada); YENİ bulgu: canlı-skor parçalı-gün-verisi kullanıyor (train/serve skew) — ayrı Level-B düzeltme-adayı. |
| #2 Risk/Kalibrasyon Pivotu | #1'e bağımlı | #1'in ATR-ayağı sağlam kaldığı için **ilerlemeye devam edilebilir.** |
| #3 Gerçek-Sektör Doğrulaması | Bağımsız, veri-bekliyor | Değişmedi — hâlâ gerçek-sektör-etiket-tedariği (EODHD fundamentals) gerekiyor. |
| **YENİ — Reverse-Ranking Composite** | Yoktu | **En güçlü yeni-aday.** Pre-registered doğrulama-testi öneriliyor. |
| **YENİ — Concentration-Constraint** | Yoktu | **Alfa-gerektirmeyen en yüksek-etkili düzeltme adayı.** Tam-evren doğrulaması öneriliyor. |

---

## 7. SIRADAKİ EN YÜKSEK-EV ADIMLAR

1. Canlı-skor'un feature-timing'ini düzelt (yalnız önceki-günün-kapanışına-kadarki veri) — Level B, altyapı.
2. Reverse-ranking'i matched-random-kontrol + cluster-robust CI ile pre-registered doğrula.
3. Concentration-kısıtını tam-evrende, daha uzun pencerede tekrar-doğrula.
4. Gerçek-sektör-etiketiyle Big Bet #3'ü tamamla (hâlâ bekliyor).
