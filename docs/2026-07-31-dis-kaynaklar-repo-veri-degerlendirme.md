# Dış Kaynaklar — Repo / Veri / Backtest Değerlendirmesi (bize ne yarar?)

Sürüm: 1.0 · Tarih: 2026-07-31 · Level A (araştırma) · Kaynak: web araması (GitHub/HF/API)
Süzgeç: Bugünkü bulgu — **mevcut günlük-bar teknik faktör setinde doğrulanmış tradeable alfa yok** (IC≈0,
IS/OOS-tutarsız). O yüzden değerlendirme şu kritere göre: *(a) yeni BİLGİ/faktör mü getiriyor, (b) dürüst
backtest altyapısını mı güçlendiriyor.* **Uyarı:** halka açık repo'lar genelde gerçek edge içermez (içerse
kapalı olurdu); değer **altyapı + veri erişimi**nde, hazır alfada değil.

---

## A) Backtest / Faktör ALTYAPISI (elle yaptığımızı sanayileştirir)

| Araç | Ne yapar | Bize faydası |
|---|---|---|
| **Qlib** (Microsoft) | AI-odaklı kantitatif platform; point-in-time DataServer, LSTM/LightGBM/Transformer hazır, Alpha158/360 dahili | ML faktör araştırması + kesitsel hisse seçimi için **akademik-seviye pipeline**. Bizim ad-hoc scriptleri yerine koyar. |
| **VectorBT** | Numba+NumPy vektörize; binlerce konfigi saniyede sweep | Bizim 4000-konfig aramalarımızı **saniyeler**e indirir; honest-metrik grid için ideal |
| **Zipline-reloaded** | Pipeline API, point-in-time doğruluk | Look-ahead/survivorship'e dikkatli günlük-frekans faktör backtest |
| **backtesting.py** | Basit, hızlı tek-strateji | Hızlı prototip |

**Öneri:** VectorBT'yi honest-metrik faktör-sweep için, Qlib'i ML faktör pipeline'ı için değerlendir.

## B) FAKTÖR KÜTÜPHANELERİ (yeni GİRDİ adayları — mevcut setimizin ötesi)

| Kaynak | İçerik | Not |
|---|---|---|
| **Alpha101** (WorldQuant) | 101 formülsel alfa (fiyat-hacim) | `yli188/WorldQuant_alpha101_code`; ama **hâlâ günlük fiyat-hacim** → bizimkiyle aynı bilgi sınıfı, ~0 IC riski yüksek |
| **Alpha158 / Alpha360** (Qlib) | 158/360 teknik faktör (MA/RSI çok-pencere) | ML modellerinin standart girdisi; test etmeye değer ama yine teknik |
| **KunQuant** | Alpha101/158'i hızlı derleyip hesaplayan motor | Hesaplama hızlandırıcı |
| **ML for Trading** (Stefan Jansen) | Alpha faktör kütüphanesi + reprodüksiyon | Rigorous referans/metodoloji |

**Dürüst beklenti:** Alpha101/158 de günlük fiyat-hacim türevi → muhtemelen bizimkiyle aynı (~0) sonucu verir.
Yine de **ucuz test**: hesapla, `edge_recheck.py` dürüst metriğiyle IS/OOS'tan geçir. Survivor varsa gerçek.

## C) YENİ VERİ (asıl kaldıraç — YENİ bilgi, recombination değil)

| Kaynak | Ne verir (yeni bilgi) | Erişim |
|---|---|---|
| **Finnhub** (free) | reddit/twitter **social sentiment**, haber, fundamentals, bazı alt-data | ücretsiz tier |
| **Alpha Vantage** | haber-sentiment, fundamentals, ekonomik | ücretsiz ama 25 istek/gün (çok kısıtlı) |
| **CBOE / opsiyon** | **opsiyon akışı + Greeks + 0DTE** — crowd/positioning sinyali | bazıları ücretsiz |
| **FINRA short volume** | piyasa-geneli **short hacmi** | ücretsiz (muhtemelen zaten kullanıyoruz) |
| **SEC EDGAR** | filing/insider akışı | ücretsiz |
| **Alpaca options** | opsiyon verisi (Greeks/flow) — elimizdeki broker | Alpaca planına bağlı |
| **HuggingFace** | finansal **veri setleri + modeller** (FinBERT vb.) | ücretsiz |

**Öncelik:** teknik faktörler tükendiği için asıl fırsat burada — **positioning/sentiment/opsiyon-akışı/short-borrow**
gibi *yeni bilgi sınıfları*. Bunlar günlük-bar teknikle korele değil → gerçek yeni sinyal potansiyeli.

## D) Alpaca ekosistemi (altyapı, alfa değil)

`alpacahq/notebooks` (cross-sectional momentum bot, historical-data, backtest rehberleri), community libs
(algo-trader, backtrader entegrasyonu). Wiring/örnek için faydalı; hazır edge beklenmez.

---

## ÖNCELİKLENDİRİLMİŞ PLAN (test-first, honest-metrik)

1. **P1 — Yeni veri pilotu (asıl kaldıraç):** Finnhub free (social sentiment + fundamentals) ve Alpaca opsiyon
   verisini (Greeks/flow) birer faktör olarak çek → `edge_recheck.py` dürüst metriğiyle IS/OOS test et.
   *Kazanım: gerçekten yeni bilgi sınıfı; edge çıkarsa gerçek.*
2. **P1 — Alpha101/158 ucuz test:** KunQuant/qlib ile hesapla, aynı honest pipeline'dan geçir. *Düşük maliyet,
   kesin öğrenme (muhtemelen ~0 ama netleşir).*
3. **P2 — Altyapı:** VectorBT'yi honest-sweep motoru yap (elle scriptleri emekliye ayır); Qlib'i ML faktör
   pipeline adayı olarak değerlendir.
4. **Referans:** Stefan Jansen ML4T (metodoloji/reprodüksiyon).

**Kritik ilke:** hiçbir dış faktör/veri, `edge_recheck.py` dürüst-metrik + IS/OOS testinden geçmeden "edge" sayılmaz.
Repo indirmek edge indirmek değildir.

---

## Sources
- [Qlib vs Backtrader vs VectorBT karşılaştırma](https://dev.to/linou518/backtrader-vs-vnpy-vs-qlib-a-deep-comparison-of-python-quant-backtesting-frameworks-2026-3gjl) · [VectorBT (github)](https://github.com/polakowo/vectorbt)
- [Alpha101 (WorldQuant, 101 Formulaic Alphas)](https://www.researchgate.net/publication/289587760_101_Formulaic_Alphas) · [Qlib Alpha158 handler](https://github.com/microsoft/qlib) · [KunQuant](https://github.com/Menooker/KunQuant) · [ML for Trading alpha library](https://stefan-jansen.github.io/machine-learning-for-trading/24_alpha_factor_library/)
- [Alpaca notebooks (github)](https://github.com/alpacahq/notebooks) · [alpaca-markets GitHub topic](https://github.com/topics/alpaca-markets)
- [Finnhub (social sentiment/alt-data)](https://finnhub.io/) · [Alpha Vantage](https://www.alphavantage.co/) · [En iyi finans API'leri 2026](https://apiscout.dev/guides/best-stock-market-financial-apis-2026)
