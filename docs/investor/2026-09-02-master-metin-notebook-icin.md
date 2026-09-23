# FinPilot — Otonom Trading Yatırım Sunumu — Master Metin

_Bu doküman bir slayt üretim aracına ("notebook uygulaması") ham girdi olarak hazırlanmıştır. Her rakam, repo'daki gerçek veritabanı/backtest dosyalarından doğrulanmıştır (bkz. "Kaynak" notları). Uydurma/varsayımsal hiçbir sayı yoktur — tahmini olan her yer açıkça "senaryo" veya "illüstratif" olarak işaretlenmiştir._

**Genel üslup kuralı (slayt üreten araç için):** Hiçbir yerde kesinlik iddiası yok. "Kanıtlandı" değil "gözlemlendi/ölçüldü". "Garanti" değil "hedef/senaryo". Geçmiş performans, gelecekteki sonucun göstergesi değildir notu, trading içerikli her slaytta zımnen geçerli sayılmalı.

---

## SLIDE 1 — Kapak

**FinPilot**
*Building the AI Trading Engine of the Future*

Alt not: Viyana merkezli, tek kurucu, finansal zeka şirketi. Meriç Başak · 2026.

---

## SLIDE 2 — The Future of Trading

**Anlatı:** Finansal piyasalar giderek daha algoritmik hale geliyor. Bir sonraki aşama yalnızca otomatik emir vermek değil — piyasayı algılayan → rejimi anlayan → strateji seçen → riski hesaplayan → işlemi gerçekleştiren → sonucundan öğrenen bir sistem.

**Görsel:** Market Data → AI Reasoning → Strategy Selection → Risk Engine → Execution → Learning (akış diyagramı)

**Why Now — 3 trend:**
1. **AI** — reasoning, ajanlar ve otonom iş akışları artık mümkün.
2. **Markets** — piyasalar daha hızlı, daha veri yoğun, daha algoritmik.
3. **Infrastructure** — büyük hedge fonların sahip olduğu veri+compute altyapısının önemli bir kısmı artık küçük ekiplerin erişimine giriyor.

**Solo founder çerçevesi (dikkatli kullanılmalı):**
- Kaynak: Carta 2025 Solo Founders Report — tek-kurucu şirket oranı 2019'da %23,7'den 2025 ilk yarısında %36,3'e çıktı.
- Mesaj **"tek kişilik unicorn" değil**, şu çerçeve kullanılmalı: *"Solo founder ≠ solo company. Lean by design, not alone by necessity."* AI araçları (Claude, MCP, otomasyon) sayesinde bir kurucu çok daha fazla işi tek başına yapabiliyor — ama kritik noktalarda (hukuk, finans, uyum, domain uzmanlığı) dış uzmanlardan destek alınıyor. Bu, "neden tek başına?" sorusunu baştan cevaplar.

**Kaynak:** fi.co "The One-Person Unicorn" (2026), Carta 2025 Solo Founders Report.

---

## SLIDE 3 — We Already Have a Research Base

**Anlatı çerçevesi (kritik):** FinPilot henüz kanıtlanmış bir trading şirketi değil. Ama 5.216 tarihsel sinyal üzerinde ölçülmüş, üç katmanlı olarak sunulması gereken bir bulgu var.

**Başlık:** *"5,216 Historical Signals: A Measured Signal Hypothesis"*

**What we have (doğrulanmış, n=5.216, DB sorgusuyla taze teyit edildi):**
- Hit rate: **%30,16**
- Ortalama (mean) getiri: **+%0,40**
- Medyan getiri: **-%0,64** (ortanca işlem hafif zararda — bunu gizlemeyin, dürüstlük sinyali)
- Ortalama kazanç: **+%4,28**
- Ortalama kayıp: **-%1,27**
- Kazanç/kayıp asimetrisi: **3,36×**

**What it means:** Tarihsel simülasyon, test edilen metodoloji altında potansiyel olarak pozitif bir beklenti (expectancy) olduğunu gösteriyor.

**What it does NOT mean:**
- Bu, gerçekleşmiş yatırım getirisi değildir.
- Gerçek para ile işlem yapılmamıştır.
- Bağımsız olarak henüz doğrulanmamıştır (canlı veri, gerçek execution maliyeti, out-of-sample testi bekliyor).

**Kaynak:** `data/finpilot.db`, tablo `signals_archive`, alan `resolved_pct_barrier` (2026-09-02 tarihinde canlı sorgulandı).

---

## SLIDE 4 — What Did We Actually Discover?

**Gerçek getiri dağılımı (barrier-captured, yani sistemin gerçekten yakaladığı sonuçlar — n=5.216):**

| Aralık | Sayı | Oran |
|---|---:|---:|
| <-%10 | 5 | %0,10 |
| -%10 – -%5 | 48 | %0,92 |
| -%5 – %0 | 3.590 | %68,83 |
| %0 – %2 | 446 | %8,55 |
| %2 – %5 | 699 | %13,40 |
| %5 – %10 | 329 | %6,31 |
| %10 – %20 | 79 | %1,51 |
| ≥%20 | 20 | %0,38 |

Maksimum gözlem: **%49,29**. Hiçbir kayıt %50'yi geçmiyor — sistemin risk-yönetimli çıkış kuralları (barrier/TP-SL) zaten bunu yapısal olarak engelliyor. **Bu slaytta "≥%100 yakaladık" gibi bir iddia KULLANILMAMALI** — geçmiş denetimde bu iddianın veri artefaktı (aynı milisaniyeye kayıtlı 19 penny-stock sinyali, %11.990'a varan imkânsız değerler) olduğu tespit edildi ve temizlendi.

**Ayrı ve açıkça etiketlenmiş ek bulgu — "bıraktığımız potansiyel":**
Farklı bir araştırma dosyasında (`full_universe_barrier_results.json`, n=46.581, farklı konfigürasyon grid'i — **n=5.216 karnesiyle KARIŞTIRILMAMALI**): ortalama MFE (Maximum Favorable Excursion — piyasanın lehimize gittiği en uzak nokta) **%4,83**, ama yakalanan ortalama sadece **+%0,37**. Yorum: piyasa bizim lehimize ortalama %4,83 hareket ediyor ama mevcut çıkış mantığımız bunun çok küçük bir kısmını yakalıyor — bu, gerçek ve dürüst bir araştırma fırsatı (bkz. Slide 5-6).

**Kaynak:** `data/finpilot.db` canlı sorgu (2026-09-02) + `data/backtest_out/full_universe_barrier_results.json`.

---

## SLIDE 5 — What Doesn't Work?

**En titiz araştırmadan (11 Ağustos 2026 sentez raporu, 48.727 çözümlenmiş path, CPCV/PBO/White Reality Check/Hansen SPA null-testleri ile desteklenmiş):**

- Skor, ileriye dönük getiriyle neredeyse ilişkisiz: rho = 0,013–0,019 (5 günlük ileri hareketle).
- Brier skill negatif: **-0,019 / -0,030** — yani skor, rastgele tahminden bile kötü performans gösteriyor bazı testlerde.
- `entry_ok` seçim filtresi değer katmıyor, hatta bazı kohortlarda ELENENLER SEÇİLENLERDEN daha iyi (eligible: -%0,35/-%0,49 vs rejected: +%1,45/+%0,07 — adverse selection).
- Ham ortalamalar uç değerlere aşırı bağımlı: üst %1 çıkarılınca ortalama +%1,40'tan -%0,37'ye düşüyor.
- 3.120 TP/SL konfigürasyonunda küresel bir kanıt oluşmadı; locked out-of-sample test hiç açılmadı.

**Mesaj:** *"Yüksek skor otomatik olarak daha iyi getiri üretmiyor. Daha uzun tutma süresi otomatik olarak daha iyi değil. Tek bir evrensel strateji tüm piyasa rejimlerine uymuyor."*

**Ne öğrendik:** Giriş kalitesi + volatilite + rejim + çıkış zamanlaması önemli — bunlar rejim-duyarlı (regime-aware) bir strateji seçim mimarisine işaret ediyor.

**Kaynak:** `reports/scanner_research_synthesis_10_perspectives_2026-08-11.md`.

---

## SLIDE 6 — The Next Problem

**Mesaj (kavramsal, ek veri gerekmiyor):**
> "We don't need another indicator. We need a better decision engine."

Slide 4'teki MFE-vs-yakalanan farkı (%4,83 vs +%0,37) ve Slide 5'teki bulgular birlikte gösteriyor ki: sorun sinyal keşfi değil, sinyal kalitesi ve çıkış/karar mimarisi.

---

## SLIDE 7 — Where Funding Goes

**Bütçe bandı:** ~€30.000-40.000 (örnek dağılım €35K üzerinden gösterilir, kesin tutar fon büyüklüğüne göre ölçeklenir)

| Bileşen | Seçenek | Yaklaşık Maliyet | Not |
|---|---|---|---|
| Geliştirme donanımı (lokal) | NVIDIA DGX Spark (GB10, 128GB) veya dengi — **Research & AI Compute Infrastructure** olarak çerçevelenir | ~€6.000 (tek seferlik) | Backtesting, walk-forward, model eğitimi, simülasyon — sürekli çalışmaz |
| Eğitim/compute (bulut) | RunPod/Lambda Labs — A100-H100 saatlik kiralama | ~€2.000/yıl (≈1000 saat) | Her zaman-açık execution altyapısı için değil; esnek burst kapasite |
| Canlı piyasa verisi | Polygon.io/Massive (referans) — nihai sağlayıcı karşılaştırmalı seçilecek | ~€2.200/yıl (~€199/ay) | "Professional real-time market data infrastructure" olarak çerçevelenir, tek vendor'a şimdiden kilitlenilmez |
| Execution/izleme altyapısı (bulut) | Küçük, güvenilir VPS + izleme/uyarı sistemi | Düşük maliyetli | 7/24 çalışma için GPU değil, kesintisizlik (uptime) gerekir — yerel PC tek hata noktası olmamalı |

**Kilit mesaj (slaytta birebir kullanılmalı):**
> "We are not buying data to manufacture profits. We are buying data to determine whether our existing signal hypothesis survives real market conditions."

**Kaynak:** Polygon.io, Databento, RunPod, Lambda Labs, NVIDIA fiyatlandırma sayfaları (2026).

---

## SLIDE 8 — Data We Need

**Bugünkü stack (repo koduyla doğrulandı):**
- **yfinance** — ücretsiz, gecikmeli, lisanssız fiyat verisi
- **EODHD** — temel veri/analist konsensüsü/haber, `FINPILOT_ENABLE_FUNDAMENTALS` bayrağı arkasında (her zaman aktif değil)

**Hedef veri ve ne sağlayacağı:**

| Veri | Ne sağlayacak? |
|---|---|
| Tick/intraday data | Entry/exit precision |
| Level 2/market depth | Execution quality |
| Volume/liquidity | Slippage estimation |
| Corporate actions | Doğru geçmiş test (bölünme/temettü düzeltmesi) |
| Fundamentals | Şirket kalite filtresi |
| News | Olay tespiti |
| Analyst data | Konsensüs değişimleri |
| Volatility data | Dinamik risk |
| Market regime data | Strateji seçimi |

**Kaynak:** `scanner/features.py`, `.env` konfigürasyonu (repo grep ile doğrulandı).

---

## SLIDE 9 — From Signal to Autonomous Trading

**Görsel (pipeline):** Data → Regime → Strategy → Meta-Ranker → Risk → Execution → Learning

Kavramsal, ek veri gerekmiyor — sunumun en önemli tek görseli olabilir.

---

## SLIDE 10 — 12-Month Roadmap

**Ay 0-3 — Altyapı + Araştırma:** Veri, donanım, backtesting, execution engine kurulumu; paralelde hibe/destek başvuruları ilerler.

**Ay 3-6 — Doğrulama:** Walk-forward, out-of-sample, işlem maliyeti + slippage dahil test, paper trading.

**Ay 6 — OBJEKTİF GO/NO-GO KAPISI.** Sistem ancak şu kriterleri sağlarsa canlı sermayeye geçer:
- Pozitif net expectancy (maliyet sonrası)
- Kabul edilebilir maksimum drawdown
- Out-of-sample doğrulama geçildi
- Piyasa rejimleri arasında istikrar
- Paper-trading tutarlılığı

Kriterler sağlanmazsa → **canlı sermaye artırılmaz.** Bu, "parayı aldık hemen borsaya basacağız" demediğimizin kanıtı.

**Ay 6-9 — Gözetimli canlı işlem:** Küçük sermaye, insan onayı, gerçek execution verisi toplanır.

**Ay 9-12 — Kademeli otonomi:** *"Toward autonomy — not blind autonomy."*

---

## SLIDE 11 — The Bigger Vision (FinSense — Ayrı Track)

**Çerçeveleme (önemli):** Bu, trading finansmanından **bağımsız, paralel bir hat** olarak sunulmalı — yatırımcı "trading botuna para verdim, neden eğitim uygulaması yapıyorsunuz?" diye sormasın. Ortak teknoloji: AI reasoning + financial intelligence. Ama iki ayrı ürün/yol haritası.

**FinPilot Trading Intelligence** — near-term validation/cash-flow motoru (Slide 3-10)
**FinSense** — long-term scalable consumer AI ürünü

**FinSense büyüme senaryosu (illüstratif, tahmin değil):**

| Aşama | Varsayım |
|---|---|
| Yıl 1 | Pilot + erken benimseyenler |
| Yıl 2 | Ürün-pazar uyumu + büyüme |
| Yıl 3 (senaryo) | 40.000-50.000 ödeyen kullanıcı hedefi |

Matematik: 50.000 × €12/ay × 12 = **€7,2M yıllık gelir potansiyeli (illüstratif senaryo)**

**Zorunlu uyarı (slaytta mutlaka yer almalı):** Tüketici abonelik uygulamalarında medyan fiyat ~€13/ay, yıl-1 elde tutma oranı genelde **%30'un altında**, ve büyüme çok eşitsiz dağılıyor (üst çeyrek yılda %80 büyürken alt çeyrek %33 küçülüyor — RevenueCat 2026 verisi). *"This is a scenario, not a forecast."*

**Kaynak:** RevenueCat "State of Subscription Apps 2026", B2B/B2C eğitim SaaS pazar verisi.

---

## SLIDE 12 — The Opportunity (Kapanış)

> "We are not trying to build another stock screener. We are building an AI system that can observe markets, reason about opportunities, manage risk, execute decisions and learn from outcomes."

**FinPilot**
*From financial data to autonomous financial intelligence.*

Kapanış cümlesi (ton belirleyici): *"Başarılı olursak: doğrulanmış, küçük ölçekli bir gelir kalemi kazanırız. Olmazsa: disiplinli şekilde denemiş, öğrenmiş ve sermayeyi korumuş oluruz. Her adım, açık raporlamayla ilerler."*

---

## EK NOT — Slayt üreten araca talimat

1. Hiçbir slaytta yukarıda verilmeyen bir sayı/istatistik EKLEMEYİN. Eksik veri varsa boş bırakın veya "TBD" yazın, uydurmayın.
2. "Garanti", "kesin", "kanıtlanmış edge" gibi ifadelerden kaçının — "hipotez", "senaryo", "gözlemlendi", "test ediliyor" dilini koruyun.
3. Slide 4 ve Slide 11'deki uyarı/dipnot cümlelerini SİLMEYİN — bunlar slaytın gövdesi kadar önemli.
4. Haftalık/aylık sabit getiri yüzdesi (örn. "%5/hafta") gibi bir hedef HİÇBİR YERDE kullanılmamalı.
