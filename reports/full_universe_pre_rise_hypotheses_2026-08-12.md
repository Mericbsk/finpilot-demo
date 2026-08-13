# Full-Universe Pre-Rise Hypothesis Battery

## Karar özeti

Bu çalışma araştırma amaçlıdır; scanner, skor, entry/exit, risk, yayın veya
canlı davranış değiştirilmemiştir. İncelenen ana hipotez şudur:

> Günlük close-location, 5 günlük trend tutarlılığı ve SPY relative strength
> birlikte güçlü; ancak günlük range aşırı genişlememişse, aynı tarihli
> benzer kontrollerden daha iyi kısa vadeli sonuç verebilir.

Sonuç: Hipotez full-universe veride zayıf ve kararsız destek buldu. 1 günlük
validation matched-control farkı negatif, 5 günlük fark pozitif olsa da iki
validation kolunun da 55 bps maliyet varsayımı sonrası medyanı negatiftir.
Bu sonuç üretim kuralı veya doğrulanmış alpha değildir.

## Veri ve protokol

- Kaynak: `data/backtest_out/full_universe_enriched.csv`
- Kaynak kapsamı: 100.496 satır, 1.970 sembol, 85 scan tarihi.
- Günlük cache: 2.047 sembol; daily proxy feature üretilebilen 100.492 satır,
  1.969 sembol ve 85 tarih.
- Pre-scan kuralı: feature hesaplamasında yalnızca `date < scan_date` günlük
  barlar kullanıldı.
- Train/validation ayrımı: kronolojik %70/%30 tarih bölmesi; eşikler yalnızca
  train bölümünden öğrenildi.
- Maliyet senaryosu: `0,55%`; gözlenen işlem maliyeti değildir.
- Kontrol: aynı tarih içinde standardize dört feature mesafesine göre en yakın
  kombinasyon-dışı gözlem; randomized control değildir.
- Tekil katkı kontrolü: her feature ayrı seçici olarak test edildi; kontrol,
  aynı tarihte diğer üç feature üzerinde standardize olarak en yakın gözlemdir.
- Belirsizlik: eşleştirilmiş farkların 2.000 tekrar bootstrap medyan aralığı ve
  sıfır-medyan sign-permutation null testi; p-değeri raporlaması için
  `(aşırı null sayısı + 1) / (2.000 + 1)` düzeltmesi kullanıldı.

Bu çalışma intraday path çalışmasının full-universe eşdeğeri değildir. Intraday
sonuçları ayrı çalışmada yalnızca 237 satır ve 16 tarih ile raporlanmıştır:
`reports/pre_rise_path_battery_2026-08-11.md`.

## Sabit kombinasyon

Eşikler train quantile’larından alındı ve validation’a taşındı:

`daily_close_location >= q70 AND daily_trend_consistency_5d >= q70 AND daily_relative_strength_5d_spy >= q70 AND daily_range_expansion_ratio <= q80`

ATR ve export’taki RVOL bu kombinasyona directional alpha olarak eklenmedi;
önceki bulgular doğrultusunda risk/bağlam değişkeni olarak tutuldu.

## Sonuçlar

### 1 günlük `c2c_1d`

- Train: kombinasyon `n=4.193`, medyan `%0,104`; baseline medyan `%0,079`.
- Validation: kombinasyon `n=4.384`, medyan `%-0,121`; baseline medyan
  `%-0,150`; median lift `+0,028 pp`.
- Validation maliyet sonrası kombinasyon medyanı `%-0,671`.
- Aynı tarih matched-control: `8.170` çift, medyan fark `-0,048 pp`, pozitif
  fark oranı `%49,3`; bootstrap %95 CI `[-0,138; +0,046] pp`, permutation
  p=`0,309`.

### 5 günlük `c2c_5d`

- Train: kombinasyon `n=3.498`, medyan `%0,578`; baseline medyan `%0,543`.
- Validation: kombinasyon `n=5.012`, medyan `%-0,299`; baseline medyan
  `%-0,357`; median lift `+0,059 pp`.
- Validation maliyet sonrası kombinasyon medyanı `%-0,849`.
- Aynı tarih matched-control: `7.227` çift, medyan fark `+0,194 pp`, pozitif
  fark oranı `%51,1`; bootstrap %95 CI `[0,000; +0,301] pp`, permutation
  p=`0,056`.

5 günlük matched-control sonucu olumlu yönde olsa da güven aralığı sıfıra
değiyor, permutation sonucu %5 eşiğini geçmiyor, ekonomik büyüklük küçük,
validation medyanı maliyet sonrası negatif ve kontrol randomized değildir.

## Tekil feature matched-control katkısı

Her feature ayrı seçildi ve diğer üç feature üzerinde aynı tarihli en yakın
kontrolle eşleştirildi. Bu, feature’ın kombinasyona bağımsız katkısı için
descriptive bir testtir; feature’ların tümü aynı evrenden eşiklenmiştir ve
multiple-testing düzeltmesi yapılmamıştır.

5 günlük sonuçlar:

- Close-location: `-0,142 pp`, bootstrap CI `[-0,264; +0,006]`, p=`0,040`.
- Trend consistency: `-0,219 pp`, bootstrap CI `[-0,314; -0,138]`, p=`<0,001`.
- SPY relative strength: `-0,128 pp`, bootstrap CI `[-0,271; -0,010]`, p=`0,024`.
- Range expansion kontrolü: `+0,379 pp`, bootstrap CI `[+0,302; +0,464]`,
  p=`<0,001`.

1 günlük sonuçlar:

- Close-location: `+0,055 pp`, bootstrap CI `[+0,013; +0,104]`, p=`0,006`.
- Trend consistency: `-0,176 pp`, bootstrap CI `[-0,221; -0,130]`, p=`<0,001`.
- SPY relative strength: `-0,048 pp`, bootstrap CI `[-0,103; +0,011]`, p=`0,083`.
- Range expansion kontrolü: `+0,071 pp`, bootstrap CI `[+0,033; +0,103]`,
  p=`<0,001`.

Bu sonuçlar, 5 günlük kombinasyondaki küçük olumlu farkın close-location,
trend veya SPY relative strength tarafından taşınmadığını; mevcut protokolde
range kontrolünün baskın göründüğünü gösteriyor. Ancak bu tekil sonuçlar da
aynı veri üzerinde çoklu exploratory testlerdir; p-değerleri doğrulayıcı kanıt
veya üretim gerekçesi değildir.

## Kapılar ve yorum

- Intraday volume, spread ve VWAP: mevcut veriyle bloklu.
- Timestamped news/event attribution: bloklu.
- Immutable point-in-time önceki cache snapshot’ı: bloklu.
- Locked OOS: açılmadı.
- Üretim promosyonu: yapılmadı.

Araştırma sonucu, “kazananların gerçekleşmiş anatomy’si” ile “scan anında
öngörü sağlayan feature” ayrımını destekliyor. ATR/RVOL’un gerçekleşmiş
kazananlarda yüksek görünmesi, tek başına yönsel alpha kanıtı değildir. Bu
bataryada bulunan günlük proxy kombinasyonu henüz bağımsız locked OOS, gerçek
execution cost, path/MAE-MFE ve kapasite kapılarını geçmemiştir.

## İzlenebilirlik

- Runner: `research/full_universe_pre_rise_hypotheses_2026_08_12.py`
- Artifact: `data/backtest_out/full_universe_pre_rise_hypotheses_2026-08-12.json`
- Focused test: `tests/test_full_universe_pre_rise_hypotheses_2026_08_12.py`
- Inference: her horizon için kombinasyon ve dört tekil feature matched-control
  farkları artifact içinde `inference` alanında bulunur.
- Run tarihi: 2026-08-12; source export ve daily cache kapsamı yukarıda
  belirtilmiştir.
