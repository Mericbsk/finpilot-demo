# FinPilot Scanner Research Battery v2

**Tarih:** 2026-08-11
**Katman:** Research / Engineering
**Seviye:** Level A, research-only
**Durum:** Tamamlandı; üretim promosyonu yok

## 1. Kapsam ve veri kimliği

Bu rapor, kullanıcının talep ettiği ek scanner deneylerini mevcut üretim davranışına dokunmadan çalıştırır. Üretim scanner'ı, `score`, `ranking`, `entry_ok`, TP/SL, exit, portfolio, publication, broker, risk ve live davranış değiştirilmemiştir.

Kaynak veri:

- CSV: `data/backtest_out/full_universe_enriched.csv`
- CSV SHA-256: `e3b183552c7c38755528d133327a0c0601fe0cfff49ba58b9e360d17716ed3d3`
- Canonical satır: 48,727
- Sembol: 1,968 canonical export; cache auditinde 2,047 JSON sembol
- Dönem: 2025-09-11..2026-07-09
- Fiyat cache: `data/price_cache/*.json`, günlük OHLCV
- Tam 5 günlük ileri path: 43,293
- Tam 5 günlük path ve entry drift <=5%: 41,433
- Tam 5 günlük path ve entry drift <=1%: 30,088

Ana yorum cohortu **full 5-day path + entry drift <=1%** olan 30,088 satırdır. `any_forward_path` sonuçları ayrıca tutuldu; cache/price mismatch kaynaklı aşırı uçların ana yorumu bozmasına izin verilmedi. Entry drift temizliği corporate action sorununu çözmez; yalnızca scan fiyatı ile cache giriş kapanışı arasındaki kısa vadeli uyumsuzluğu sınırlar.

Tam artifact: `data/backtest_out/scanner_battery_v2_2026-08-11.json`
Runner: `research/scanner_battery_v2.py`

## 2. Deney sırası

1. Path ve data-integrity ayrımı: herhangi bir ileri path, tam 5 günlük path, entry drift <=5% ve <=1%.
2. Maliyet senaryosu: 0, 5, 10, 15, 25, 40, 55, 75, 100 ve 150 bps.
3. Payoff ve tail: üst %1 ve üst %5 çıkarıldığında mean/median, trimmed mean ve katkı.
4. Tek değişkenli score/feature sıralama tanısı.
5. Signal frequency ve günlük signal sayısı-quality ilişkisi.
6. Aynı gün yakın özellikli eligible/rejected matched selection.
7. Veto bileşenleri.
8. Mevcut `vol_regime`/`regime` alanı içinde score quintile etkileşimi; gerçek makro rejim ayrı tutuldu.
9. Kısa horizon, next-open proxy ve günlük bar pullback proxy.
10. Flat-bps execution stress.
11. Survivorship, corporate action, score version, benchmark ve observed execution veri kapıları.

Bu listedeki 1-11 deneyleri artifact içinde ayrı sonuç olarak saklanmıştır. Meta-multiple-testing için önceki full battery'nin FDR/CPCV/PBO/White/Hansen sonuçları da bu raporla birlikte değerlendirilmiştir; yeni v2 hücreleri bağımsız confirmatory OOS olarak yorumlanmamıştır.

## 3. Temel bulgular

### 3.1 Entry ve maliyet duyarlılığı

Ana cohort, 5 günlük `fwd_5d_pct` sonuçlarını kullanır:

| Grup | n | 0 bps mean | 0 bps median | 55 bps mean | 55 bps median | 100 bps mean | 100 bps median |
|---|---:|---:|---:|---:|---:|---:|---:|
| All | 30,088 | 1.4026% | 0.0555% | 0.8526% | -0.4945% | 0.4026% | -0.9445% |
| `entry_ok=True` | 795 | -0.3451% | -0.4851% | -0.8951% | -1.0351% | -1.3451% | -1.4851% |
| `entry_ok=False` | 29,293 | 1.4500% | 0.0670% | 0.9000% | -0.4830% | 0.4500% | -0.9330% |

Bu, mevcut `entry_ok` cohortunun aynı veri ve aynı forward label altında rejected cohorttan daha iyi olmadığını gösterir. Bu bir production rule change önerisi değildir; ürün katmanı kararı ayrıca Level B/C sürecine tabidir.

### 3.2 Payoff ve tail davranışı

Ana cohortta all grubunun 5 günlük ham ortalaması 1.4026% iken:

- Üst %1 çıkarılınca mean **-0.3741%**, median 0.0000%, trimmed mean -0.2021%.
- Üst %5 çıkarılınca mean **-1.1040%**, median -0.1718%, trimmed mean -0.6573%.
- Ham maksimum kazanç 5,491.94%, maksimum kayıp -97.01%.
- Ham all ortalamasının üst %1 katkısı %126.41 seviyesinde.

Eligible cohort zaten hamda negatiftir: mean -0.3451%, median -0.4851%. Üst %1 çıkarılınca mean -0.8227%; üst %5 çıkarılınca -1.8266% olur. Bu nedenle görünen pozitif all mean, tipik işlem davranışı veya istikrarlı edge olarak yorumlanamaz.

### 3.3 Score ve feature tanısı

Bu bölüm gerçek çok değişkenli ablation değildir. Her feature tek başına forward sonuçla Spearman ilişkisi ve üst quintile özetidir; production score formülünün nedensel katkısı olarak yorumlanmamalıdır.

| Feature | Spearman | Üst quintile mean | Üst quintile median | Üst quintile trimmed mean |
|---|---:|---:|---:|---:|
| `finpilot_score` | 0.0191 | 0.6319% | 0.2066% | 0.2644% |
| `composite_score` | -0.0067 | 0.3035% | -0.0201% | -0.1004% |
| `dist_52w_high` | 0.0540 | 0.4091% | 0.1182% | 0.0967% |
| `gap_pct` | -0.0279 | 2.2234% | -0.5962% | -0.7117% |
| `rvol` | 0.0687 | 2.3547% | 0.1586% | 0.2021% |
| `atr_pct_real` | -0.1211 | 4.5467% | -2.3644% | -2.0394% |
| `squeeze_factor` | -0.0351 | -0.8749% | -0.4608% | -1.0730% |
| `lottery_factor` | -0.1909 | 2.0284% | -2.5265% | -2.6715% |
| `overnight_gap_factor` | -0.1088 | -0.2597% | -1.8714% | -2.4203% |
| `catalyst_factor` | unavailable | -0.5308% | -0.0396% | -0.4191% |

Özellikle `atr_pct_real`, `lottery_factor` ve `gap_pct` üst quintile mean'leri uç kazançlara duyarlıdır; median ve trimmed mean aynı desteği vermemektedir.

### 3.4 Signal frequency

Drift-temiz cohortta 80 scan günü vardır. Eligible count için 46 gün kalite medianı mevcut olduğundan, günlük sayı-quality Spearman korelasyonu **-0.1551**'dir. Bu zayıf ve açıklayıcı olmayan ilişki, daha fazla signal üretmenin daha iyi kalite verdiğini desteklemiyor.

Günlük count özeti yalnızca sayı dağılımıdır; forward outcome ile karıştırılmamalıdır. Bazı günlerde eligible signal bulunmadığı için kalite medianı yoktur; korelasyon yalnızca eşleşmiş count-quality günleriyle hesaplanmıştır.

### 3.5 Matched eligible/rejected

Aynı gün, `composite_score`, `atr_pct_real`, `gap_pct`, `rvol` ve `dist_52w_high` yakınlığıyla 594 eligible/rejected çifti kuruldu.

- Eligible eksi matched rejected mean farkı: **-1.4640 puan**
- Median fark: **-0.9981 puan**
- Trimmed mean: **-1.3871 puan**
- Positive difference rate: **44.78%**
- Profit factor: 0.6738

Bu eşleştirme aynı gün nearest-neighbor tanısıdır; replacement, residual confounding ve çoklu eşleşme sınırlılıkları vardır. Nedensel etki veya bağımsız validation olarak kabul edilmemelidir.

### 3.6 Veto decomposition

Veto hücreleri tek tek predicate tanısıdır; birleşik policy optimizasyonu değildir. Ana cohort 5 günlük sonuçlarında:

| Veto | Flagged n / mean | Not flagged n / mean |
|---|---:|---:|
| High volatility (`ATR >= 8`) | 4,390 / 6.8045% | 25,698 / 0.4798% |
| Gap risk (`gap >= 5`) | 444 / -0.2182% | 29,644 / 1.4269% |
| Near 52-week high (`>= .95`) | 5,100 / 0.4451% | 24,988 / 1.5980% |
| Low RVOL (`<1`) | 20,657 / 1.1651% | 9,431 / 1.9227% |
| Weak trend predicate | 16,825 / 2.4161% | 13,263 / 0.1169% |

Flagged meanler tail etkisine açıktır; örneğin weak-trend flagged grubunda üst uç katkısı %113.26'dır. Bu tablo tek başına bir veto kaldırma/ekleme gerekçesi değildir.

### 3.7 Horizon, next-open ve pullback

Ana cohortta:

| Horizon | n | Mean | Median | Trimmed mean | Positive rate |
|---|---:|---:|---:|---:|---:|
| 1 gün | 30,088 | 0.1286% | -0.0321% | -0.0979% | 48.40% |
| 2 gün | 30,088 | 0.1826% | -0.0398% | -0.1668% | 48.58% |
| 3 gün | 30,088 | 0.4273% | 0.0000% | -0.0934% | 49.91% |
| 5 gün | 30,088 | 1.4026% | 0.0555% | -0.0698% | 50.45% |
| 10 gün | 25,682 | 3.1654% | 0.2010% | 0.1523% | 51.53% |

Next-open proxy: n=30,088, mean 0.1089%, median -0.0231%, trimmed mean -0.0899%. 0.25 ATR pullback proxy: n=19,087, mean -0.1705%, median -0.0546%, trimmed mean -0.1245%.

Bunlar günlük bar proxy'leridir. Intraday bar olmadığı için pullback'ın önce gerçekleşip gerçekleşmediği, order'ın dolduğu veya stop/target sırasının nasıl oluştuğu doğrulanamaz.

### 3.8 Rejim ve execution stress

`vol_regime`/`regime` alanı ile score quintile hücreleri hesaplandı; bunlar gerçek makro rejim değildir. VIX, SPY/benchmark, sektör sınıflaması ve beta-neutral alanları yoktur. Bu nedenle VIX/SPY/sector beta-neutral testinin durumu **BLOCKED**'dır.

Execution stress sonuçları 10k, 50k ve 100k notional için aynı kalır; çünkü exportta dollar ADV, spread, slippage, impact ve fill alanları yoktur. 0-100 bps flat scenario meanleri all cohortta 1.4026% -> 0.4026% arasında lineer azalır; bu gözlenmiş execution sonucu değildir. Observed spread/slippage/impact için gerçek fill veya mikro yapı verisi gereklidir ve test **BLOCKED**'dır.

## 4. Multiple testing ve güven sınırı

Bu v2 deneyleri önceki araştırma battery'siyle birlikte okunmalıdır. Önceki fixed-target battery 3,120 konfigürasyon içeriyordu; FDR 1,012, CPCV/PBO 0.6, White Reality Check p=0.7413 ve Hansen SPA p=0.7761 raporlandı. Bu sonuçlar araştırmacı serbestlik derecesinin yüksek olduğunu ve tekil pozitif hücrelerin confirmatory kanıt sayılamayacağını gösterir.

V2, 53 JSON artifact'ini meta-audit envanterine dahil etti; ancak yeni bağımsız locked OOS açılmadı. Locked OOS sonucu bu raporda yoktur ve sonuçlar promotion evidence değildir.

## 5. Veri kapıları ve bloklu deneyler

Tamamlanamayan veya geçerli biçimde yorumlanamayan sorular:

- Point-in-time listing/delisting universe yok: survivorship test **BLOCKED**.
- Corporate-action feed veya provider açıklaması yok: flagged jumps sınıflandırması **BLOCKED**.
- Adjusted close kapsamı raw close değerlerinin yaklaşık %9.85'i: adjusted/raw güvenilir karşılaştırma **BLOCKED**.
- Historical score version/epoch alanı yok: score version replay **BLOCKED**.
- VIX/SPY/sector benchmark alanı yok: macro regime ve beta-neutral test **BLOCKED**.
- Observed spread, slippage, impact, dollar ADV ve fill log yok: execution/capacity test **BLOCKED**.
- Intraday bars yok: pullback ordering ve intraday fill **BLOCKED**.
- Bağımsız insan red-team değerlendirme harness'ı yok: adversarial human test **BLOCKED**; mevcut predicate diagnostics bunun yerine geçmez.

## 6. Sonuç ve karar sınırı

Bu v2 bataryası, mevcut veriyle çalıştırılabilecek ek deneyleri tamamladı. En dayanıklı mesajlar şunlardır:

1. `entry_ok` cohortu rejected cohorttan ayrışmıyor; matched tanıda fark negatif.
2. 5 günlük all mean, üst uç çıkarıldığında negatife dönüyor; tipik sonuç medyan/trimmed mean ile pozitif değil.
3. Kısa horizonlarda medyan ve trimmed mean negatif; 10 günlük küçük pozitif trimmed mean haftalık %5-10 hedefini desteklemiyor.
4. Flat bps senaryosu gözlenmiş execution kanıtı değildir.
5. Survivorship, corporate actions, score epochs, true regime ve capacity için veri eklenmeden daha ileri sonuç iddia edilemez.

Bu veriler, düzenli haftalık toplam **%5-10 kazanç** beklentisini desteklemiyor. Ayrıca hiçbir bulgu production scanner, score, `entry_ok`, ranking, TP/SL, exit veya portfolio kuralının otomatik değiştirilmesini haklı çıkarmıyor. Herhangi bir canlı kural değişikliği ayrı bir Level B/C ürün/risk kararıdır.

## 7. Kanıt ve yeniden üretim

```text
python -m pytest -q tests/test_scanner_battery_v2.py
python -m research.scanner_battery_v2 --csv data/backtest_out/full_universe_enriched.csv --cache data/price_cache --artifacts data/backtest_out --out data/backtest_out/scanner_battery_v2_2026-08-11.json
```

Focused test sonucu: **6 passed**, bir mevcut `datetime.utcnow()` deprecation warning'i.

Araştırma kodu ve testleri:

- `research/scanner_battery_v2.py`
- `tests/test_scanner_battery_v2.py`
- `data/backtest_out/scanner_battery_v2_2026-08-11.json`

Bu rapor araştırma bulgusudur; yayın, yatırım tavsiyesi, canlı işlem onayı veya üretim kuralı değildir.
