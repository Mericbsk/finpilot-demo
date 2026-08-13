# Pre-Registration — Three Hypotheses (HOLD until gates open)

Date: 2026-08-10
Level: A (research pre-registration; execution is gated)
Layer: Research
Status: **pre-registered, NOT to be run** until the two gates below open

Bu doküman üç hipotezi **koşulmadan önce** dondurur. Amaç: sonuçları gördükten
sonra hipotez değiştirmeyi (HARKing) ve multiple-testing kaymasını engellemek.
Bu hipotezler Strategic/10-Perspectives bataryalarında **keşif sinyali** olarak
ortaya çıktı; burada confirmatory koşu için kayıt altına alınıyorlar.

## İki açılma kapısı (ikisi de şart)

1. **Veri bütünlüğü kapısı (E2/V0):** `resolved_pct_t5` etiket semantiği
   doğrulanmalı (2026-08-10 teşhisi: cache close-to-close ile korelasyon
   **0.325**, ufuklarla uyuşmuyor, temiz sembollerde bile 3.5pp medyan sapma).
   Etiket doğrulanmadan hiçbir confirmatory koşu anlamlı değil.
2. **Kullanıcı gerçeği kapısı (PR1/PR7):** Bu hipotezlerin ürün değeri,
   kullanıcının ne istediğine bağlı. Kullanıcı "işlem sinyali" değil "dikkat
   haritası" istiyorsa, bu hipotezlerin ürünleşme biçimi değişir.

---

## H1 — Gap-Reversal (keşif: M2)

**Keşif sinyali:** eligible kohortta gap_up ≥3% → 5g medyan **-3.04%**
(n=85, %29 pozitif); gap_down ≥3% → 5g medyan **+3.05%** (n=51, %67 pozitif).

**Hipotez (dondurulmuş):** Büyük gap-down'lar (≤ -3%) 5 günlük ufukta
mean-revert eder; büyük gap-up'lar (≥ +3%) mean-revert eder (ters yön).

**Neden şüpheli olmalıyız:** n=51/85 küçük; etkin örneklem gün-içi korelasyonla
daha da küçük; keşif aynı veri setinde yapıldı (selection bias); score'un
extension kodladığı (Q3) bilindiği için bu, "uzamış olanı seçme"nin bir
yansıması olabilir, bağımsız bir yapı değil.

**Confirmatory tasarım (dondurulmuş):**
- Veri: temiz adjusted OHLC (kapı 1 sonrası), **yeni** tarih aralığı veya
  locked holdout — keşif verisiyle aynı değil.
- Birincil metrik: gap_down≥3% kohortunun 5g medyan getirisi, aynı-gün
  eşleştirilmiş null (rastgele sembol-gün, aynı |gap| dağılımı) ile
  karşılaştırma.
- İstatistik: tarih-blok bootstrap CI; etkin örneklem raporu; tek birincil
  hipotez (multiple-testing bütçesi = 1).
- **Success:** null'dan anlamlı pozitif ayrışma, CI sıfırın üstünde.
- **Kill:** CI sıfırı kapsıyorsa veya yön tersine dönerse → hipotez ölür,
  bir daha aynı veriyle ısıtılmaz.

## H2 — rvol-Inversion (keşif: M1)

**Keşif sinyali:** eligible kohortta yüksek-rvol tercili en kötü (5g medyan
**-1.77%**, %38.7 pozitif) vs düşük-rvol (+0.68%, %54.3).

**Hipotez (dondurulmuş):** Seçilen adaylarda yüksek relative-volume, 5g
getiriyle **negatif** ilişkili (katılım-teyidi varsayımının tersi).

**Neden şüpheli olmalıyız:** eligible kohort zaten adversely selective (L4);
rvol-inversion, seçim katmanının bir artifact'i olabilir, genel bir piyasa
yapısı değil. Tüm evrende (sadece eligible'da değil) test edilmeli.

**Confirmatory tasarım (dondurulmuş):**
- Veri: temiz adjusted OHLC, tüm evren (eligible + rejected).
- Birincil metrik: rvol tercili × 5g getiri, tüm evrende, gap büyüklüğü ve
  dist_52w_high kontrol edilerek (rvol, extension'ın proxy'si olabilir).
- **Success:** kontroller sonrası negatif gradyan korunuyor.
- **Kill:** kontroller sonrası etki kaybolursa → rvol-inversion, extension'ın
  proxy'si olarak kaydedilir ve bağımsız hipotez olarak ölür.

## H3 — ATR-Parity Sizing (keşif: P2)

**Keşif sinyali:** eligible portföyde ATR-parity sizing max drawdown'ı
**-%24.3 → -%15.9** indirdi, en iyi günlük Sharpe (0.267).

**Hipotez (dondurulmuş):** ATR-parity (volatiliteye ters ağırlık) sizing,
eşit ağırlığa göre daha düşük drawdown ve daha yüksek risk-ayarlı getiri üretir.

**Neden şüpheli olmalıyız:** bu bir **konstrüksiyon ilkesi**, trading kuralı
değil; ve selection katmanı değer üretmiyorsa (P1), sizing'in iyileştirdiği
şey negatif-Değerli bir sepet olabilir. Sizing, kötü seleksiyonu kurtaramaz.

**Confirmatory tasarım (dondurulmuş):**
- Veri: temiz adjusted OHLC; hem eligible hem counterfactual (rastgele
  rejected) sepetlerde.
- Birincil metrik: max drawdown + günlük Sharpe, ATR-parity vs eşit ağırlık,
  **her iki sepet tipinde**.
- **Success:** ATR-parity her iki sepette de drawdown'ı anlamlı azaltıyor
  (yani etki seleksiyondan bağımsız bir konstrüksiyon etkisi).
- **Kill:** etki yalnızca eligible'da varsa veya counterfactual'da tersine
  dönerse → sizing etkisi seleksiyonla iç içe, bağımsız ilke olarak ölür.

---

## Neden şimdi koşmuyoruz?

Üçü de keşif verisiyle aynı sette doğdu; aynı veride "doğrulama",
double-dipping olur. Ve üçü de etiket/veri kapısının (E2/V0) arkasında —
çünkü V0 gösterdi ki `resolved_pct_t5`'in ne ölçtüğü doğrulanamıyor; bu
etiketle koşulan her confirmatory test, tanımsız bir hedefi test eder.

**Doğru sıra:** (1) veri bütünlüğü kapısı → (2) kullanıcı gerçeği →
(3) bu üç hipotezin pre-registered confirmatory koşusu, **yeni veriyle**.

## Governance
Bu doküman bir pre-registration'dır (Level A kayıt). Hipotezlerin koşulması
Level A research; koşudan çıkan herhangi bir kural/ürün değişikliği Level B/C
onayı gerektirir. Bu doküman değiştirilirse, değişiklik tarihi ve nedeni
decision-log'a girilir (pre-registration bütünlüğü).
