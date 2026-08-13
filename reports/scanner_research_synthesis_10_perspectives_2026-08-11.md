# FinPilot Scanner Research Synthesis
## Önceki raporlar + v2 eklemesi + 10 bakış açılı red-team incelemesi

**Tarih:** 2026-08-11
**Katman:** Research / Engineering
**Seviye:** Level A, research-only analiz
**Durum:** Üretim promosyonu yok; canlı kural değişikliği yok

## 1. Bu rapor neyi birleştiriyor?

Bu belge şu araştırma kayıtlarını birlikte okur:

- `reports/research_battery_consolidated_2026-08-11.md`
- `reports/research_battery_full_2026-08-11.md`
- `reports/scanner_research_complete_inventory_2026-08-11.md`
- `reports/strategic_lab_experiments_2026-08-10.md`
- `reports/ten_perspectives_lab_2026-08-10.md`
- `reports/mirror_analysis_2026-08-10.md`
- `reports/scanner_research_battery_v2_2026-08-11.md`

V2 artifact’i: `data/backtest_out/scanner_battery_v2_2026-08-11.json`
Ana export SHA-256: `e3b183552c7c38755528d133327a0c0601fe0cfff49ba58b9e360d17716ed3d3`
Dönem: 2025-09-11..2026-07-09

Bu bir production validation raporu değildir. Locked OOS açılmamış, shadow/paper/live emir yürütülmemiş, broker veya yayın davranışı değiştirilmemiştir.

## 2. Kısa cevap: ne bulduk?

Bütün raporların ortak sonucu şudur:

1. **Veri ve etiket kalitesi, sinyal tartışmasından önce geliyor.** 2,047 cache sembolünün 485’inde en az %50 close sıçraması var; flagged sembollerde en büyük sıçramanın medyanı %173.57513. Corporate action, ticker değişimi ve provider davranışı ayrıştırılmadı.
2. **Score ileriye dönük güvenilir predictor olarak doğrulanmadı.** Strategic Lab’de geçmiş 5 günlük hareketle ilişki `rho=0.376`, ileri 5 günlük hareketle `rho=0.013`; v2 `finpilot_score` ileri ilişkiyi `rho=0.0191` olarak ölçtü. Ten Perspectives score’un base-rate predictor’dan daha iyi olmadığını buldu: Brier skill `-0.019` ve `-0.030`.
3. **Score saf bir “mirror” değil; extension ağırlıklı, yavaş ve gürültülü bir composite.** `dist_52w_high` ile score ilişkisi `rho=0.667`, `past_5d_pct` ile `rho=0.376`; ancak extension’ı tersine çevirmek de çalışmıyor.
4. **`entry_ok` değer eklemiyor, bazı kontrollerde adverse selection yapıyor.** V2’nin tam 5 günlük, drift ≤1% cohortunda eligible 5 günlük mean/median `-0.3451%/-0.4851%`; rejected mean/median `1.4500%/0.0670%`. Aynı gün yakın özellikli 594 eşleşmede eligible eksi rejected farkı ortalama `-1.4640` puan.
5. **Pozitif görünen ham ortalamalar uç değerlere bağlı.** V2 ana cohortunda 5 günlük all mean `1.4026%`; üst %1 çıkarılınca `-0.3741%`, üst %5 çıkarılınca `-1.1040%`.
6. **TP/SL/exit matrisi geniş tarandı ama global kanıt oluşmadı.** 3,120 fixed-target konfigürasyonunda CPCV/PBO `0.6`, White Reality Check `p=0.7413`, Hansen SPA `p=0.7761`; locked OOS açılmadı.
7. **Kısa vadede tipik sonuç pozitif değil.** V2 drift-temiz cohortta 1/2/3/5 günlük trimmed mean sırasıyla `-0.0979%/-0.1668%/-0.0934%/-0.0698%`; 10 günlük trimmed mean `+0.1523%` ile küçüktür ve haftalık %5-10 beklentisini taşımaz.
8. **Portfolio/sizing, selection’dan daha anlamlı bir araştırma yönü gibi görünüyor; ama bu edge değildir.** ATR-parity sizing max drawdown’ı `-15.9%` ile equal-weight `-24.3%` değerinden düşük gösterdi; execution ve veri kapıları açık olmadığı için production sizing sonucu değildir.
9. **Gerçek execution, kapasite, survivorship, corporate-action, score-version ve makro rejim testleri yapılamadı.** Bunlar eksik veri nedeniyle `BLOCKED`.
10. **Dürüst ürün konumu:** FinPilot’ın mevcut kanıtı “garantili kazanç” veya “haftalık %5-10” değil; veri, ölçüm, path ve risk belirsizliğini görünür kılan bir günlük piyasa reasoning/measurement yüzeyi olabilir. Bu ürün konumu da ayrı bir Level B ürün kararıdır; burada onaylanmış değişiklik yapılmadı.

## 3. Son v2 eklemesi neyi değiştirdi?

### 3.1 Ana sonuç değişmedi, ölçüm daha sıkı hale geldi

Önceki bataryalar zaten score, selection, TP/SL, null ve reality-check katmanlarında olumlu production kanıtı bulmamıştı. V2 bu sonucu değiştirmedi; daha kontrollü cohortlarla aşağıdaki şekilde güçlendirdi:

| Konu | Önceki raporlarda | V2 ile güncel çerçeve |
|---|---|---|
| Path | Loader ve horizonlara göre farklı resolved sayıları | Any path `48,727`; full 5d `43,293`; drift ≤1% `30,088` ayrı tutuldu |
| `entry_ok` | Eligible mean/median negatif; eski runlarda `-1.4361%/-3.3977%` net scenario sonucu | Aynı 5 günlük close-to-close zeminde eligible `-0.3451%/-0.4851%`; rejected daha iyi |
| Tail | Raw meanlerin outlier/cap etkisi taşıdığı biliniyordu | Üst %1 çıkarılınca all 5d mean `-0.3741%`; üst %5 çıkarılınca `-1.1040%` |
| Cost | 55 bps senaryoları negatif/medyan zayıf | Eligible median 0 bps’te bile `-0.4851%`; 55 bps’te `-1.0351%` |
| Timing | Next-open maliyeti günlük ölçekte ana sorun değildi | V2 next-open mean `0.1089%`, median `-0.0231%`, trimmed `-0.0899%` |
| Rejim | Bazı iç rejim hücreleri pozitif ama küçük/tutarsız | VIX/SPY/sector gerçek rejim testi `BLOCKED`; mevcut `vol_regime` makro rejim sayılmadı |
| Execution | Spread/slippage/impact yok | 10k/50k/100k sonuçları aynı; flat-bps yalnızca scenario |
| Data integrity | Drift ≤1% önceki lab’da medyanı `+0.52%` hareket ettirmişti | Aynı pozitif bulgu full 5d `fwd_5d_pct` ile tekrarlanmadı; güncel ana cohort median `+0.0555%` |

### 3.2 Açık revizyon: drift sonucu neden değişti?

Strategic Lab raporu drift ≤1% alt kümesinde `+0.52%` medyan bildirdi. V2’de aynı etiketi otomatik olarak “doğrulandı” saymadık; farklı loader/horizon/path ve outcome semantiklerini ayırdık. V2:

- canonical symbol-day satırlarını yeniden yükledi;
- tam 5 günlük cache path istedi;
- scan fiyatı ile cache entry close drift’ini ölçtü;
- `fwd_5d_pct` değerini doğrudan scan fiyatından ileri kapanışa hesapladı;
- ana yorumu drift ≤1% cohortuna sabitledi.

Sonuç: all cohort median `+0.0555%`, eligible median `-0.4851%`. Bu, eski raporun yanlış olduğu kesin kanıtı değildir; iki ölçümün aynı population/label/loader olmadığını gösterir. Ancak güncel karar için daha sıkı ve yeniden üretilebilir V2 tanımı esas alınmalıdır. Eski `+0.52%` değerini production edge olarak taşımıyoruz.

## 4. On farklı bakış açısıyla kapsamlı inceleme

### Bakış 1: Veri bütünlüğü ve fiyat gerçekliği

**Soru:** Ölçtüğümüz fiyat serisi ekonomik olarak güvenilir mi?

**Kanıt:** 2,047 cache sembolünün 485’inde en az %50 close jump; flagged largest jump medyanı %173.57513. Adjusted-close kapsamı yaklaşık %9.85. Immutable eski cache snapshot’ı olmadığı için restatement karşılaştırması yapılamıyor.

**Yorum:** Bu sıçramalar split, reverse split, ticker değişimi, delist, provider veya gerçek hareket olabilir; sınıflandırma yok. Bu nedenle bazı yüksek forward getiriler “sinyal buldu” değil, veri/provider açıklığı olabilir.

**Karar etkisi:** En yüksek öncelik veri onarımıdır. Confirmatory H1/H2/H3, locked OOS ve production promotion bu kapı kapanmadan HOLD.

**Açık test:** Her bar için provider kaynağı, adjustment status, corporate-action event, ticker lineage ve immutable snapshot eklenmesi.

### Bakış 2: Etiket, path ve ölçüm semantiği

**Soru:** Mean, median, MFE, triple-barrier ve close-to-close aynı şeyi mi ölçüyor?

**Kanıt:** `resolved_pct_t5` MFE/favorable-movement benzeri bir ölçüdür; `c2c_5d` gerçek endpoint close-to-close’dur. Strategic Lab’de bunların korelasyonu `0.86`, ancak median absolute fark `3.6pp`. Fixed-target sonuçlarında target cap/time exit mekanik olarak pozitif mean üretebilir.

**Yorum:** “Hedefe dokundu”, “MFE oluştu” ve “pozitif P&L ile kapandı” aynı iddia değildir. Günlük OHLC aynı bardaki ordering’i de kesin çözemez; stop-first varsayımı muhafazakâr bir varsayımdır, gözlenen fill değildir.

**Karar etkisi:** Endpoint ve path sonuçları ayrı raporlanmalı; hiçbir MFE/target metriği doğrudan haftalık getiri iddiasına çevrilmemeli.

**Açık test:** Intraday bars, observed order/fill, timestamp-aligned labels ve pre-registered endpoint definition.

### Bakış 3: Score semantiği ve feature leakage

**Soru:** Score geleceği mi ölçüyor, geçmişi mi kodluyor, yoksa yalnızca gürültü mü?

**Kanıt:** Score/past 5d `rho=0.376`; score/forward 5d `rho=0.013` ve v2 `finpilot_score` `rho=0.0191`. `dist_52w_high` score ile `rho=0.667`; `past_5d_pct` `rho=0.376`. `catalyst_factor` constant zero. Lineage forward kolonlarını (`resolved_pct_t5`, `c2c_1d`, `c2c_5d`, `mae_t5`) feature olarak yasaklıyor.

**Yorum:** En dürüst tanım “geçmiş extension’a eğimli, yavaş hareket eden, zayıf faktörler ve gürültü içeren composite”tir. Saf mirror değildir; tersine çevirmek de çözüm değildir. Score version/epoch yokluğu tarihsel replay’i ayrıca bloklar.

**Karar etkisi:** Score ağırlık tuning’i frozen kalmalı. `catalyst_factor` contract audit adayıdır; production contract değişikliği Level B’dir.

**Açık test:** Versioned score inputs, feature timestamps, temporal replay ve forward target rebuild.

### Bakış 4: `entry_ok`, ranking ve selection kalitesi

**Soru:** Scanner’ın seçtiği satırlar seçilmeyenlerden daha iyi mi?

**Kanıt:** V2 drift ≤1% cohortunda eligible n=795, 5d mean/median `-0.3451%/-0.4851%`; rejected n=29,293, `1.4500%/0.0670%`. Matched same-day nearest-neighbor farkı eligible lehine `-1.4640` puan. Önceki çalışmalar random rejected karşılaştırmasında median `-2.01pp`, top score bandında eligible median `-0.20%` vs rejected `+1.08%` buldu.

**Yorum:** Sorun yalnızca tek bir veto eşiği değildir. Score bandı içinde selection adverse görünüyor; `entry_ok` bir edge olarak doğrulanmadı.

**Karar etkisi:** `entry_ok` kaldırma, tersine çevirme veya yeni veto ekleme kararı otomatik alınamaz. Bunlar Level B/C ürün/risk kararıdır.

**Açık test:** Yeni forward target, pre-registration, time-blocked locked OOS ve independent human approval.

### Bakış 5: Tail, outlier ve multiple-testing

**Soru:** Görünen kazanç tipik mi, yoksa az sayıdaki olağanüstü satır mı taşıyor?

**Kanıt:** V2 all 5d mean `1.4026%`; üst %1 çıkarılınca `-0.3741%`, üst %5 çıkarılınca `-1.1040%`. Max win `5,491.94%`, max loss `-97.01%`; üst %1 katkısı `%126.41`. Fixed-target matrix 3,120 konfigürasyon; FDR 1,012, CPCV/PBO 0.6, White p `0.7413`, Hansen p `0.7761`.

**Yorum:** FDR discovery sayısı production-worthy discovery sayısı değildir. High target/long horizon seçilmiş hücreler ve MFE/cap mekanikleri researcher degrees of freedom yaratır.

**Karar etkisi:** Mean tek başına raporlanmamalı; median, trimmed mean, tail contribution, block bootstrap ve null sonuçları birlikte verilmelidir. Haftalık %5-10 iddiası reddedilir.

**Açık test:** Locked OOS, pre-registered single protocol, nested selection ve immutable experiment registry.

### Bakış 6: Timing, half-life ve execution gerçekliği

**Soru:** Edge varsa zaman içinde ve gerçek fill koşulunda yakalanabilir mi?

**Kanıt:** Önceki timing çalışmasında signal-close raw mean `6.8838%`, median `0%`, trimmed mean `-0.0290%`; top %5 toplamın `%108`ini taşıdı. Next-open mean `0.1130%`, trimmed `-0.0014%`. V2 1/2/3/5 günlük trimmed meanler negatif; pullback proxy trimmed `-0.1245%`.

**Yorum:** Günlük timing ana problemi tek başına açıklamıyor; asıl problem tipik endpoint sonucunun zayıflığı ve execution gözleminin olmaması. Intraday ordering, fill ve spread/impact bilinmiyor.

**Karar etkisi:** Flat 55 bps veya 100 bps senaryosu gözlenmiş maliyet değildir. Capacity/impact iddiası kurulamaz.

**Açık test:** Intraday OHLCV/trade bars, bid-ask, order log, fill log, ADV-conditioned impact.

### Bakış 7: Rejim, benchmark ve piyasa bağımlılığı

**Soru:** Sonuç piyasanın, volatilitenin veya sektörün hareketini mi tekrar ediyor?

**Kanıt:** Ten Perspectives’te SPY’ye göre eligible median relative return `-1.22pp`, block CI `[-2.11,-0.23]`; IWM `-0.86pp`, CI sıfırı kapsıyor. Bu basit subtraction’dır, beta-neutral değildir. V2 mevcut `vol_regime` hücrelerini raporladı ama VIX/SPY/sector alanları yok.

**Yorum:** Score’un “rejimde çalışıyor” iddiası için gerçek benchmark, sector membership ve beta exposure gerekir. Küçük extreme clusters veri artifact’i olabilir.

**Karar etkisi:** Regime-specific production kuralı veya benchmark-relative başarı iddiası desteklenmiyor.

**Açık test:** Point-in-time SPY/IWM/VIX/sector data, rolling beta, beta-neutral residual return, pre-registered regime definitions.

### Bakış 8: Portfolio, sizing, correlation ve capacity

**Soru:** Tekil seçim zayıfsa portföy inşası riski anlamlı biçimde azaltıyor mu?

**Kanıt:** ATR-parity max drawdown `-15.9%`, equal-weight `-24.3%`, en iyi günlük Sharpe `0.267`; score-weighted sizing median günü daha iyi görünse de drawdown `-20.2%`. Candidate correlation median yaklaşık `0.19`; correlation-cluster selection median improvement `0.0`. Historical usable dollar ADV snapshot’ı ile outcomes join edilmedi; observed spread rate `%0`.

**Yorum:** Sizing ve risk mekanikleri seçim edge’i değildir. Daha iyi drawdown, daha iyi alpha anlamına gelmez. Capacity sonucu notional senaryosu olmaktan öteye geçemiyor.

**Karar etkisi:** ATR-parity üretime alınamaz; yalnızca pre-registered portfolio hypothesis olarak tutulabilir.

**Açık test:** PIT ADV, spread/impact, position constraints, turnover, borrow/short constraints, fill-aware portfolio backtest.

### Bakış 9: Survivorship, corporate actions ve point-in-time bias

**Soru:** Evren geçmişte gerçekten o gün erişilebilir olan şirketleri mi içeriyor?

**Kanıt:** Point-in-time listing/delisting universe yok; historical sector membership yok; score version/epoch yok; corporate-action açıklama feed’i yok. Cache’te büyük jump’lar var. Locked OOS açılmadı.

**Yorum:** Survivorship-free universe olmadan “full universe” ifadesi yalnızca mevcut export kapsamını anlatır; tarihsel ekonomik evreni kanıtlamaz. Score’un gelecekteki bilgiyle restate edilip edilmediği de tam kapanmış değil.

**Karar etkisi:** Bu kapılar kapanmadan confirmatory test sonucu promotion evidence sayılamaz.

**Açık test:** PIT security master, delisting return, ticker lineage, action-adjusted bars, immutable cache snapshots, publication/score timestamp.

### Bakış 10: Adversarial red-team, kullanıcı değeri ve ürün dürüstlüğü

**Soru:** Bulgular en sert karşı okumada ve gerçek kullanıcı bağlamında ayakta kalıyor mu?

**Kanıt:** Mirror analizi “score’u ters çevir” tezini de reddetti: follow score `rho=0.013`, fade extension `rho=-0.008`. Null-feature p95 `|rho|=0.011`; detectable olan her feature ekonomik olarak useful değil. Gerçek kullanıcı PR/B testleri ve LLM/adversarial harness çalıştırılmadı.

**Yorum:** En büyük risk, zayıf predictive evidence’ı güven veren bir sinyal arayüzü gibi sunmaktır. Mevcut kanıt “günlük piyasa reasoning, ölçüm belirsizliği ve karşı-tez görünürlüğü” çerçevesini destekler; “kazanç motoru” çerçevesini desteklemez.

**Karar etkisi:** Kullanıcı yüzeyi, yasaklı işlem dili ve performance claims açısından ayrı compliance/product incelemesi gerektirir. Bu rapor positioning’i onaylamaz; yalnızca kanıt sınırını gösterir.

**Açık test:** 10-15 gerçek kullanıcıyla PR1-PR7/B1-B7, outcome-blind review, calibration score, no-signal day, AI-free baseline ve grounded-rationale audit.

## 5. Sonuçların hiyerarşisi

### En güçlü negatif/koruyucu bulgular

- `entry_ok` için birden fazla bağımsız counter-evidence hattı var: random matched comparison, matched eligible/rejected, benchmark-relative, calibration ve null controls.
- Score forward correlationı bütün horizonlarda sıfıra yakın; score’un backward extension’a eğimli olduğu açıklanıyor.
- Tail çıkarımı ve robust statistics, ham pozitif meanlerin tipik sonucu yansıtmadığını gösteriyor.
- Fiyat cache integrity, survivorship ve observed execution kapıları açık değil.
- Weekly 5-10% expectation için hiçbir confirmatory kanıt yok.

### İlginç ama henüz bulgu olmayan hipotezler

- Gap-down reversal / gap-up failure.
- RVOL inversion.
- Path-aware MFE capture ve adverse-excursion avoidance.
- ATR-parity sizing.

Bu dört yön yeni production kuralı değildir. Her biri veri onarımı, ön-kayıt, tek hedef, locked OOS ve insan onayı gerektirir.

### Artık savunulamayacak kısa yollar

- Ham mean’i tipik getiri gibi sunmak.
- MFE veya target-touch’u gerçekleşmiş kapanış P&L’i gibi sunmak.
- `entry_ok` ile rejected satırlar arasındaki farkı başarı varsaymak.
- Score’u tersine çevirerek çözüm bulunduğunu iddia etmek.
- Flat bps senaryosunu observed execution kabul etmek.
- Current export’i survivorship-free veya corporate-action-clean tarihsel evren diye adlandırmak.
- 3,120 grid içindeki en iyi hücreyi bağımsız doğrulama gibi sunmak.

## 6. Değişen karar ve sonraki sıra

### Güncel karar

**Araştırma kararı:** Feasible diagnostics tamamlandı; sonuçlar production edge göstermiyor.
**Ürün kararı:** `entry_ok`, score, ranking, TP/SL, exit, portfolio veya yayın dili değiştirilmiyor.
**Risk kararı:** Haftalık %5-10 kazanç varsayımı kabul edilmiyor.
**Governance:** Bu belge Level A research synthesis’tir; Level B/C karar yerine geçmez.

### Önerilen araştırma sırası

1. Immutable cache snapshot ve provider/action provenance.
2. PIT universe, delisting, ticker lineage ve historical sector/benchmark data.
3. Score input/version/timestamp contract ve leakage-free forward target.
4. Intraday OHLCV, spread, slippage, fill ve ADV join.
5. Tek bir pre-registered confirmatory hypothesis: gap, RVOL, path veya sizing; hepsi birden değil.
6. Human-approved locked OOS.
7. Ancak kapılar geçerse ürün/production kararının Level B/C değerlendirmesi.

Bu sıra bir production roadmap veya onaylanmış ürün kararı değildir; mevcut araştırma bulgularından türetilmiş Level A öneri sırasıdır.

## 7. Kanıt sınırı

Bu raporda kullanılan sayılar FinPilot’ın kendi research-only backtest ve diagnostic artifact’lerinden gelir. Akademik veya üçüncü taraf GitHub kanıtı bu senteze karıştırılmamıştır. Tüm sayılar ilgili tarihli artifact ve raporlarla izlenebilir; farklı loader/path/label tanımları aynı cohortmuş gibi birleştirilmemiştir.

Üretim davranışı değişmedi. Bu belge yatırım tavsiyesi, canlı işlem onayı, yayın onayı veya düzenli kazanç garantisi değildir.
