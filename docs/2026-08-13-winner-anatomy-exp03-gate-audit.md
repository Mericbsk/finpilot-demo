# Winner Anatomy — entry_ok Gate Audit (gerçek sayılar)

Tarih: 2026-08-13 · Statü: Level A · Veri: aynı temizlenmiş `full_universe_enriched.csv` (n=64.217, dedupe + outlier filtresi uygulanmış — bkz. önceki dosya)

## Önce bir düzeltme

Bu turda bana yapıştırılan analizde geçen rakamlar (8.102 toplam +5% winner, entry_ok'un yalnızca 204'ünü yakalaması/%97,5 kaçırma, missed grupta %29,3 vs entry_ok grubunda %25,1 winner oranı, `regime=False+direction=False`'ın "tek pozitif hücre" olması) **benim ürettiğim dosyada yok ve ben doğrulayamıyorum.** Aşağıda aynı soruları kendi temizlediğim veri üzerinde yeniden hesapladım. Bazı sayılar yönü tutuyor (missed winner'ların daha ucuz/düşük skorlu/52w'den uzak olması, score/dist_52w_high büyüklükleri şaşırtıcı derecede yakın çıktı), bazıları tutmuyor (toplam winner sayısı, caught/missed sayıları, oranlar) ve bir iddia (**"tek pozitif hücre"**) doğrudan yanlış çıktı — 4 hücrenin **hepsi** pozitif medyan getiri gösteriyor. Muhtemelen farklı bir temizlik/dedupe/tanım kullanılmış; hangisi olduğunu bilmiyorum, o yüzden kendi sayılarımı esas alıyorum.

## Test 1 — entry_ok=True/False dağılım şekli (istenen bimodalite testi)

| | n | std | p10 | p25 | p50 (medyan) | p75 | p90 | uç-pay (<0% veya ≥5%) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| entry_ok=True | 1.877 | 11.10 | -12.83 | -6.17 | **-0.81** | 3.52 | 10.42 | %74.9 |
| entry_ok=False | 62.340 | 11.03 | -9.63 | -3.90 | **+0.12** | 3.95 | 9.44 | %69.1 |

**Okuma:** varyans (std) neredeyse aynı ama şekil simetrik değil — entry_ok=True grubunun sol kuyruğu belirgin şekilde daha kalın (p10=-12.83 vs -9.63, p25=-6.17 vs -3.90) ve **medyanı negatif** (-0.81% vs control +0.12%). Yani entry_ok "her iki yönde de büyütür" hipotezim kısmen yanlış — asıl etkisi aşağı yönde daha güçlü. Bu, `finpilot-evidence-inventory-and-gaps`'teki "eligible cohort rejected'ten kötü" bulgusuna dağılım-seviyesinde bir açıklama katıyor.

## Test 2 — gerçek +5% winner yakalama oranı

- Toplam +5% winner (c2c_5d≥5): **13.176** (evrenin %20.5'i — pasted'deki 8.102 ile uyuşmuyor)
- entry_ok=True tarafından yakalanan: **358** (%2.7 — pasted'deki 204/%2.5'e yakın oran ama farklı mutlak sayı)
- Kaçırılan: **12.818** (%97.3 — pasted'deki %97.5'e çok yakın)
- P(+5% winner | entry_ok=True) = **%19.07**, P(+5% winner | entry_ok=False) = **%20.56** — yani entry_ok=True grubunda winner olma ihtimali, entry_ok=False'tan **düşük**. Pasted metindeki %25.1 vs %29.3 ile yön aynı ama büyüklük farklı.

## Test 3 — caught vs missed +5% winner profili

| | n | fiyat (medyan) | composite_score (medyan) | finpilot_score (medyan) | dist_52w_high (medyan) |
|---|---:|---:|---:|---:|---:|
| caught (entry_ok=True) | 358 | $43.38 | 62 | 55 | 0.896 |
| missed (entry_ok=False) | 12.818 | $33.23 | 25 | 28 | 0.690 |

Yön doğru (caught grup daha pahalı, daha yüksek skorlu, zirveye daha yakın) ve score/dist_52w_high büyüklükleri pasted metindekine (22 vs 62, 0.67 vs 0.89) hayret verici derecede yakın — fiyat farkı ($43 vs $33) ise pasted'deki ($62 vs $26) kadar büyük değil. Yani **temel teşhis doğru**: FinPilot'un `entry_ok` kapısı "zaten güçlü görünen/pahalı/zirveye yakın" hisseleri seçiyor, büyük hareketlerin çoğu bunun dışında oluyor.

## Test 4 — ATR × RVOL ortak winner oranı (yeni, en önemli bulgu)

Win rate (%5+ olasılığı):

| ATR \\ RVOL | düşük | orta | yüksek |
|---|---:|---:|---:|
| düşük | %9.7 | %12.1 | %12.5 |
| orta | %19.7 | %25.9 | %27.5 |
| yüksek | %20.4 | %27.4 | **%30.8** |

Medyan c2c_5d (%):

| ATR \\ RVOL | düşük | orta | yüksek |
|---|---:|---:|---:|
| düşük | +0.27 | +0.54 | +0.49 |
| orta | -0.03 | +0.84 | +0.87 |
| yüksek | **-2.98** | **-1.29** | **-1.07** |

**Bu en temiz ve en önemli sonuç.** Yüksek ATR × yüksek RVOL hücresi, +5% winner olma **olasılığını** en yükseğe çıkarıyor (%30.8) ama aynı hücrenin **medyan getirisi negatif** (-1.07%). Yani ATR/RVOL büyük hareket olasılığını artırıyor ama hangi yönde olacağını söylemiyor — dağılımın her iki ucunu da şişiriyor, ortalama/medyan değeri aşağı çekiyor çünkü kayıp tarafı kazanç tarafından daha kalabalık. Bu, pasted metnin "ATR = opportunity amplitude, return predictor değil" çıkarımını gerçek veriyle doğruluyor — üstelik varsayılan tahminden bile daha net bir şekilde (düşük-ATR hücrelerin hepsi pozitif medyan taşıyor, yüksek-ATR hücrelerinin hepsi negatif).

## Test 5 — regime × direction 2x2 (düzeltme)

Win rate: regime=F/dir=F → %22.9, regime=F/dir=T → %22.3, regime=T/dir=F → %17.5, regime=T/dir=T → %18.8.
Medyan c2c_5d: regime=F/dir=F → **+0.147**, regime=F/dir=T → +0.106, regime=T/dir=F → +0.124, regime=T/dir=T → **+0.080** (en düşük, ama pozitif).

**Pasted metnin "tek pozitif hücre" iddiası yanlış — dört hücrenin de medyanı pozitif.** Doğru olan gözlem: `regime=True + direction=True` (sistemin "en bullish" etiketlediği hücre) hem en düşük winner oranına hem en düşük medyan getiriye sahip — yani mevcut regime/direction etiketleme, en azından bu tanımla, kendi iddia ettiği yönde çalışmıyor. Ama bu "tersine çevirin" anlamına gelmiyor; her iki n de yeterince büyük (24k-28k) olduğu için gürültü değil, gerçek bir ters-korelasyon gibi duruyor — ayrı bir audit gerektirir.

## Genel değerlendirme

Pasted metnin **teşhisi** (skor/entry_ok zaten-güçlü-görüneni seçiyor, ATR yön değil genlik ölçüyor, "yükselecek" ile "trade edilebilir" farklı şeyler) gerçek verilerle destekleniyor. Ama **spesifik rakamları** doğrulayamadım ve biri (tek pozitif hücre) açıkça yanlış çıktı — bu belgedeki tüm sayılar benim kendi hesapladığım, kaynağı belirsiz ikinci bir sayı setiyle karıştırılmamalı.
