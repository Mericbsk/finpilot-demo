# Decision Context Battery

## Karar özeti

Bu çalışma Level A, research-only bir deneydir. Amaç, `finpilot_score` tek başına gelecekteki getiriyi tahmin ediyor mu sorusunu; olay/state tanımı, geçmiş benzer vakaların dağılımı, kanıt kalitesi ve abstention sorularına ayırmaktır. Scanner, skor, ranking, entry/exit, risk, portföy, yayın, broker ve canlı davranış değiştirilmemiştir. Locked OOS açılmamıştır.

Ana sonuç: descriptive state özetleri üretilebildi; ancak 25-nearest-case tahmini satır bazında train-only sabit medyan base-rate'i geçmedi. 1 günlük MAE `%6,168`'den `%6,253`'e, 5 günlük MAE `%12,390`'dan `%12,693`'e kötüleşti. Date-block median 5 günlük hata ise `%4,386`'dan `%4,356`'ya yalnızca yaklaşık `0,031 pp` iyileşti. Bu, benzer-vaka yaklaşımının doğrulanmış tahmin gücü olduğunu göstermiyor; ilk hipotezin ana kısmı exploratory validation'da desteklenmedi.

Abstention heuristiği validation satırlarının `%25,0`'ını ayırdı. Aktif grubun 5 günlük medyanı `%-0,094`, abstain grubunun medyanı `%-3,161` oldu. Bu ayrım gelecekte “hangi koşullarda kanıt zayıf veya olumsuz?” sorusu için incelenebilir bir araştırma adayıdır; tek başına işlem, yön veya seçim kuralı değildir.

## Veri ve protokol

- Kaynak: `data/backtest_out/full_universe_enriched.csv`
- Kaynak tarih aralığı: `2025-09-11` – `2026-08-05`
- Ham satır: `100.496`
- `(symbol, scan_date)` canonical dedup sonrası: `43.323`
- Outcome eksikleri atıldıktan sonra kronolojik train/validation: `21.869` / `21.454` satır
- Tarih bölmesi: `57` train tarihi ve `25` validation tarihi
- Feature'lar: `gap_pct`, `rvol`, `atr_pct_real`, `dist_52w_high`, `finpilot_score`
- Outcome'lar: `c2c_1d`, `c2c_5d`
- Eşikler: yalnızca train'den q10/q25/q75/q90 quantile'ları
- Benzer-vaka modeli: train feature'larının median/IQR standardizasyonu ve `k=25` en yakın tarihsel satırın outcome medyanı
- Base-rate: yalnızca train outcome medyanı
- Benchmark/sector: mevcut exportta kullanılabilir bir benchmark veya sektör kontrolü yoktur
- Execution: gözlenen spread, ADV ve işlem maliyeti yoktur; tradeability iddiası yapılmamıştır

## State özeti

Batarya train-only eşiklerle şu descriptive state'leri sınıflandırır:

- `ordinary`
- `gap_down`
- `gap_up`
- `high_activity` (yüksek ATR ve RVOL)
- `extended_up` (52-week high'a yakınlık ve pozitif gap)

Gap state'leri yüksek aktivite veya extension ile çakıştığında önceliklidir. State tablolarının tam satır, tarih, medyan ve pozitif oran çıktısı artifact'in `state_summary` alanındadır. Bu state'ler keşifsel betimlemelerdir; sınıflara dayalı bir giriş/çıkış kuralı tanımlanmamıştır.

## Similar-case validation

| Ölçüm | Train base-rate | 25 similar-case |
|---|---:|---:|
| `c2c_1d` satır MAE | `%6,1676` | `%6,2531` |
| `c2c_5d` satır MAE | `%12,3902` | `%12,6930` |
| `c2c_5d` date-block median hata | `%4,3864` | `%4,3558` |

Satır bazındaki ana benchmark iki horizonda da daha iyi performans verdi. Date-block sonucu küçük farkla benzer-vaka lehine olsa da bu fark ekonomik, istikrarlı veya bağımsız doğrulanmış değildir. Ayrıca export satırları aynı scan günlerinde kümelendiği için bağımsız gözlem sayısı satır sayısından düşüktür; bu rapor ayrıca yeni bir confidence interval veya confirmatory p-değeri iddiası üretmiyor.

## Evidence ve abstention

Evidence skoru, benzer vakaların 5 günlük dispersion'ı ile pozitif oranının `0,5`'ten uzaklığını birleştiren araştırma heuristiğidir. En düşük quartile abstain olarak işaretlenmiştir.

- Abstain oranı: `%25,0023`
- Aktif satır: `16.090`
- Aktif grup `c2c_5d` medyanı: `%-0,09395`
- Abstain grup `c2c_5d` medyanı: `%-3,16054`

Bu sonuç, “abstain grubu daha sorunlu olabilir mi?” sorusunu destekleyen descriptive bir ayrışmadır. Ancak evidence skoru validation outcome'ları görmeden train benzer-vaka dispersion/pozitif oranından türetilmiş olsa da quartile seçimi yine aynı validation dağılımında yapılmıştır; bu nedenle bağımsız eşik, cost, kapasite, turnover ve canlı uygulama testi yoktur.

## Hipotez kararı

1. **Event/state sorusu:** Uygulanabilir. State'ler tanımlanabildi ve state-specific dağılımlar üretildi; yönsel veya ekonomik edge iddiası yok.
2. **Similar-case sorusu:** Ana haliyle desteklenmedi. Satır MAE base-rate'ten kötü; date-block farkı çok küçüktür.
3. **Evidence quality sorusu:** Abstention heuristiği riskli validation satırlarını ayırıyor olabilir; sonuç exploratory candidate olarak tutulur.
4. **Score replacement:** Bu batarya score'un yerine yeni bir production score önermiyor.

## Sınırlar ve sonraki kapılar

- Intraday path, news attribution, benchmark/sector relative strength ve observed execution maliyeti bu bataryada yoktur.
- PIT lineage, immutable cache snapshot ve locked OOS kapıları açılmamıştır.
- Bu exportta görülen fiyat bütünlüğü ve effective-sample sorunları sonucu confirmatory kanıt seviyesine taşımaz.
- Human interviews/user-truth protokolleri (`PR1/PR7/PR2`) bu kodla tamamlanamaz.
- Herhangi bir event/state/abstention kuralı ancak bağımsız locked OOS, observed execution, kapasite ve Level B insan onayı sonrasında ayrıca değerlendirilebilir.

## İzlenebilirlik

- Runner: `research/decision_context_battery_2026_08_12.py`
- Artifact: `data/backtest_out/decision_context_battery_2026-08-12.json`
- Focused tests: `tests/test_decision_context_battery_2026_08_12.py`
- Regression validation: `35 passed` focused research tests
- Gate refresh: `data/backtest_out/gated_research_program_2026-08-12.json` (`220` planned tests; P1/P2/P9 blocked, locked OOS not opened)
- Run date: `2026-08-12`
