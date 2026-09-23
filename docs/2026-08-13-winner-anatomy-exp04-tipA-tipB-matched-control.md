# Winner Anatomy — Tip A / Tip B Tam Popülasyon Matched-Control Testi

Tarih: 2026-08-13 · Statü: Level A · Veri: `full_universe_enriched.csv`, aynı temizlik (dedupe symbol+scan_ts, |c2c_5d|≤100, price≥$1), n=61.297

**Kritik metodolojik fark:** önceki turda Tip A/Tip B'nin sadece *winner* alt kümesine bakılmıştı (hayatta-kalma önyargılı). Burada her ikisinin **tam popülasyonu** (kazanan+kaybeden hepsi) matched-control'e karşı test edildi, ayrıca `lottery_factor`'e göre ikiye bölündü.

## Sonuçlar

| Popülasyon | n (%evren) | medyan | ortalama | win≥5% | loss<0% | büyük-kayıp<-10% | matched-control diff | p (≈) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **entry_ok=True (mevcut kapı)** | 1.877 (3.1%) | **-0.814%** | -0.809% | 19.1% | 55.8% | **14.3%** | -1.013pp | 0.61 |
| Tip A (regime=F, ATR/gap/RVOL geçiyor) | 3.399 (5.6%) | -0.080% | +0.167% | 26.8% | 50.2% | 13.6% | -0.665pp | 0.57 |
| Tip B (sakin, ATR/gap/RVOL geçmiyor) | 13.691 (22.3%) | **+0.357%** | +0.508% | 11.8% | 43.7% | **1.4%** | +0.442pp | 0.39 |

## lottery_factor'e göre bölünme (en çarpıcı sonuç)

| Popülasyon | düşük-lottery yarı (medyan) | yüksek-lottery yarı (medyan) |
|---|---:|---:|
| entry_ok=True | **-2.536%** (n=244) | -4.125% (n=240) |
| Tip A | **+1.246%** (n=976) | -0.666% (n=976) |
| Tip B | +0.563% (n=3.794) | +0.329% (n=3.793) |

## Okuma

1. **Mevcut `entry_ok` kapısı, üç popülasyonun en kötüsü.** Sadece "yardımcı olmuyor" değil — medyan, ortalama, en büyük kayıp oranı ve **her iki lottery_factor yarısında da negatif**. `lottery_factor` düşük olan (yani "güvenli" sayılması gereken) yarısı bile -2.5% medyan taşıyor. Bu, mevcut gate mantığının aktif olarak kötü bir alt küme seçtiğine dair en güçlü kanıt şimdiye kadar.

2. **Tip A, tam popülasyon olarak kanıtlanmadı ve gerçek kuyruk riski taşıyor** (%13.6 büyük-kayıp, entry_ok'a yakın). Matched control anlamsız (p=0.57, işaret bile negatif). **Ama içindeki lottery_factor bölünmesi çarpıcı:** düşük-lottery yarı +1.25% medyan, yüksek-lottery yarı -0.67%. Yani Tip A'nın "opportunity" hikayesi muhtemelen doğru ama sadece **düşük-lottery alt kümesinde** — bunu ayrı test etmeden Tip A'yı bütün olarak kovalamak, tam olarak `lottery_factor`'ün cezalandırmak için var olduğu tuzağa düşmek olur.

3. **Tip B, en güvenli ve en büyük popülasyon.** Koşulsuz bile pozitif medyan (+0.357%), en düşük büyük-kayıp oranı (%1.4 — diğerlerinin onda biri), matched control en azından yön olarak pozitif (p=0.39, hâlâ anlamlı değil ama üçünün en iyisi) ve evrenin %22'si kadar büyük bir örneklem — istatistiksel güç açısından en çok üzerinde çalışılabilecek grup bu.

## Sonuç ve öneri

Hiçbir popülasyon henüz üretim-kalitesinde anlamlı değil (üçünün de p>0.05). Ama üç popülasyon arasında net bir sıralama var: **entry_ok (kötü) < Tip A bütün-olarak (belirsiz, riskli) < Tip A∩düşük-lottery (umut verici ama test edilmedi) ≈ Tip B (en güvenli, en büyük).**

Önerilen sıradaki adımlar (öncelik sırasıyla): (a) Tip A ∩ düşük-lottery_factor alt kümesini kendi matched-control testine sok — bu şu an en çarpıcı ama doğrulanmamış hücre. (b) Tip B'yi neden düşük-riskli olduğunu anlamak için derinleştir (muhtemelen "kaliteli/istikrarlı" isimler — 5 günlük ufuk yerine daha uzun ufukta test edilmeye değer). (c) `entry_ok` kapısını mevcut haliyle production'da kullanmaya devam etmenin gerekçesi kalmadı — ayrı bir governance kararı gerektirir, bu belge onu önermiyor, sadece kanıtı kaydediyor.
