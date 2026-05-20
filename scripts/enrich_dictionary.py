"""Sprint 2: Add simple_explanation, why_important, common_mistake to 50 key terms."""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "web" / "public" / "dictionary.json"

ENRICHMENTS = {
    # ── TEKNIK ANALİZ ──────────────────────────────────────────────────────────
    "relative-strength-index": {
        "simple_explanation": "RSI, bir hissenin son dönemde ne kadar hızlı yükselip düştüğünü 0-100 arası bir sayıyla gösterir. 70 üzeri 'çok pahalı olabilir', 30 altı 'çok ucuz olabilir' sinyali verir.",
        "why_important": "En yaygın kullanılan teknik göstergelerden biridir. FinPilot scanner'ı RSI'yi momentum ve aşırı alım/satım tespitinde kullanır.",
        "common_mistake": "RSI 70'i geçti diye hemen satmak. Güçlü trendlerde RSI uzun süre 70 üzerinde kalabilir; tek başına bir giriş/çıkış sinyali değildir.",
        "finpilot_usage": ["scanner", "analysis"],
    },
    "goreceli-guc-endeksi": {
        "simple_explanation": "RSI, bir hissenin son dönemde ne kadar hızlı yükselip düştüğünü 0-100 arası bir sayıyla gösterir. 70 üzeri 'çok pahalı olabilir', 30 altı 'çok ucuz olabilir' sinyali verir.",
        "why_important": "En yaygın kullanılan teknik göstergelerden biridir. FinPilot scanner'ı RSI'yi momentum ve aşırı alım/satım tespitinde kullanır.",
        "common_mistake": "RSI 70'i geçti diye hemen satmak. Güçlü trendlerde RSI uzun süre 70 üzerinde kalabilir; tek başına bir giriş/çıkış sinyali değildir.",
        "finpilot_usage": ["scanner", "analysis"],
    },
    "moving-average-convergence-divergence": {
        "simple_explanation": "MACD, iki hareketli ortalamanın birbirinden ne kadar uzaklaştığını gösterir. Sinyal çizgisini yukarı keserse 'al', aşağı keserse 'sat' sinyali olarak yorumlanır.",
        "why_important": "Trend yönünü ve momentumu aynı anda gösterir. FinPilot'ta MACD kesişimleri strateji sinyallerinde kullanılır.",
        "common_mistake": "MACD histogramının renk değiştirmesini kesin sinyal saymak. Yan trend piyasalarda MACD çok fazla yanlış sinyal üretir.",
        "finpilot_usage": ["analysis", "scanner"],
    },
    "macd": {
        "simple_explanation": "MACD, iki hareketli ortalamanın birbirinden ne kadar uzaklaştığını gösterir. Sinyal çizgisini yukarı keserse 'al', aşağı keserse 'sat' sinyali olarak yorumlanır.",
        "why_important": "Trend yönünü ve momentumu aynı anda gösterir. FinPilot'ta MACD kesişimleri strateji sinyallerinde kullanılır.",
        "common_mistake": "MACD histogramının renk değiştirmesini kesin sinyal saymak. Yan trend piyasalarda MACD çok fazla yanlış sinyal üretir.",
        "finpilot_usage": ["analysis", "scanner"],
    },
    "bollinger-bands": {
        "simple_explanation": "Fiyatın etrafına çizilen iki bant — fiyat genellikle bu bantların içinde kalır. Fiyat üst banda yaklaşırsa 'pahalı', alt banda yaklaşırsa 'ucuz' yorumu yapılabilir.",
        "why_important": "Volatilite genişlediğinde bantlar açılır, daralır. FinPilot, Z-Score ile birlikte ortalamaya dönüş fırsatlarını belirler.",
        "common_mistake": "Fiyat üst bantı kırmayı her zaman 'sat' sinyali saymak. Güçlü trendlerde fiyat uzun süre bantın dışında kalabilir.",
        "finpilot_usage": ["analysis"],
    },
    "bollinger-bantlari": {
        "simple_explanation": "Fiyatın etrafına çizilen iki bant — fiyat genellikle bu bantların içinde kalır. Fiyat üst banda yaklaşırsa 'pahalı', alt banda yaklaşırsa 'ucuz' yorumu yapılabilir.",
        "why_important": "Volatilite genişlediğinde bantlar açılır, daralır. FinPilot, Z-Score ile birlikte ortalamaya dönüş fırsatlarını belirler.",
        "common_mistake": "Fiyat üst bantı kırmayı her zaman 'sat' sinyali saymak. Güçlü trendlerde fiyat uzun süre bantın dışında kalabilir.",
        "finpilot_usage": ["analysis"],
    },
    "moving-average": {
        "simple_explanation": "Son N kapanış fiyatının ortalaması. Fiyatın üstünde olmak yükselen trend, altında olmak düşen trend işareti sayılır.",
        "why_important": "Tüm stratejilerin temelinde yer alır. SMA200 üzerindeki hisseler FinPilot'un trend filtrelerini geçer.",
        "common_mistake": "Tek bir MA değerine güvenmek. 50-200 MA kombinasyonu çok daha güvenilir sinyal üretir.",
        "finpilot_usage": ["scanner", "analysis"],
    },
    "support": {
        "simple_explanation": "Fiyatın defalarca düşüp geri döndüğü fiyat seviyesi — bir taban gibi düşünün. Bu seviyede alıcılar satıcıları geçer.",
        "why_important": "Alım noktası ve stop-loss belirlemede kritik. FinPilot'un destek/direnç hesaplamaları bu seviyeleri otomatik tespit eder.",
        "common_mistake": "Eski destek kırıldıktan sonra hâlâ geçerli olduğunu düşünmek. Kırılan destek genellikle dirence dönüşür.",
    },
    "resistance": {
        "simple_explanation": "Fiyatın defalarca yükselip geri döndüğü tavan seviyesi. Bu noktada satıcılar alıcıları geçer ve fiyat düşer.",
        "why_important": "Kar alma noktası ve risk yönetimi için kullanılır. Kırılan direnç genellikle yeni destek olur.",
        "common_mistake": "Direnç kırılımını beklemeden işlem açmak. Direnç bölgesinde yaşanan 'sahte kırılımlar' stop-loss'u tetikleyebilir.",
    },
    "trend": {
        "simple_explanation": "Fiyatın genel hareket yönü — yukarı, aşağı veya yatay. 'Trende karşı gitme' yatırımın temel kurallarından biridir.",
        "why_important": "Trend doğru tespit edilmezse en iyi sinyal bile zarara yol açabilir. FinPilot Regime Detection modülü trendi otomatik belirler.",
        "common_mistake": "Kısa vadeli dalgalanmayı trend zannetmek. Trend teyidi için en az 2-3 düşük tepe/yüksek taban görmek gerekir.",
        "finpilot_usage": ["analysis"],
    },
    "volume": {
        "simple_explanation": "Bir günde el değiştiren hisse sayısı. Yüksek hacimle gelen fiyat hareketi daha güvenilir; düşük hacimle gelen hareket kandırıcı olabilir.",
        "why_important": "Hacim 'teyit' göstergesidir. FinPilot scanner'ı anormal hacim artışlarını otomatik işaretler.",
        "common_mistake": "Habersiz hacim artışını atlayıp sadece fiyata bakmak. Hacim artışı kurumsal hareketin öncü sinyalidir.",
        "finpilot_usage": ["scanner"],
    },
    "candlestick": {
        "simple_explanation": "Her mum, o gün/saat/dakikada fiyatın nerede açılıp kapandığını ve en yüksek/düşük noktaları gösterir. Rengi yeşil/beyazsa kapanış açılışın üstünde, kırmızı/siyahsa altında.",
        "why_important": "Teknik analizin temel görsel aracı. Formasyonlar (doji, çekiç) olası dönüş noktalarını gösterir.",
        "common_mistake": "Tek bir mumu bağımsız yorumlamak. Mumlar önceki bağlama göre anlam kazanır; aynı formasyon farklı yerlerde farklı şeyler ifade eder.",
    },
    "z-score": {
        "simple_explanation": "Bir değerin ortalamasından kaç standart sapma uzakta olduğunu gösterir. Hisse için: Z-Score +2'nin üstündeyse 'aşırı pahalı', -2'nin altındaysa 'aşırı ucuz' yorumu yapılabilir.",
        "why_important": "FinPilot'un ortalamaya dönüş stratejisinin çekirdeği. Hem fiyat hem de göstergeler için normalize edilmiş sinyal üretir.",
        "common_mistake": "Z-Score'un her zaman ortalamaya döneceğini düşünmek. Yapısal değişimlerde (yeni gelir modeli, sektör değişimi) Z-Score sıfırlanır.",
        "finpilot_usage": ["scanner", "analysis"],
    },
    "fibonacci-retracement": {
        "simple_explanation": "Büyük bir fiyat hareketinin ardından fiyatın nerede durup geri gelebileceğini tahmin etmeye yarayan %23.6, %38.2, %61.8 gibi seviyeler.",
        "why_important": "Çok sayıda trader bu seviyelere baktığı için self-fulfilling özellik kazanır. Destek/direnç tespitinde yaygın kullanılır.",
        "common_mistake": "Her seviyenin kesinlikle tutacağını beklemek. Fibonacci seviyeleri olasılık bölgeleridir, garanti değildir.",
    },
    "golden-cross": {
        "simple_explanation": "50 günlük hareketli ortalama, 200 günlük hareketli ortalamanın üstüne çıktığında oluşur. Güçlü yükseliş trendi habercisi sayılır.",
        "why_important": "Kurumsal yatırımcıların da takip ettiği uzun vadeli al sinyali. Death Cross'un (ters kesişim) tam tersidir.",
        "common_mistake": "Golden Cross oluştuktan çok sonra al emri vermek. Sinyal genellikle büyük hareketin ortasında gelir ve geç girenler tepede kalabilir.",
    },
    # ── TEMEL ANALİZ ────────────────────────────────────────────────────────────
    "p-e-ratio": {
        "simple_explanation": "Hissenin piyasa fiyatını yıllık kâra bölerek 'bu kâr için kaç yıl bekliyorum?' sorusunu yanıtlar. F/K 10 ise 10 yılda paranızı geri alırsınız.",
        "why_important": "En temel değerleme metriğidir. FinPilot Analysis sekmesinde sektör ortalamasıyla karşılaştırmalı gösterilir.",
        "common_mistake": "Yüksek F/K = pahalı demek değildir. Büyüme şirketleri yüksek F/K'ya rağmen iyi yatırım olabilir; sektör ortalamasıyla karşılaştırın.",
        "finpilot_usage": ["analysis"],
    },
    "market-cap": {
        "simple_explanation": "Şirketin toplam borsa değeri: hisse fiyatı × toplam hisse sayısı. 'Bu şirket piyasada ne kadar ediyor?' sorusunun cevabıdır.",
        "why_important": "Şirket büyüklüğünü ölçer ve yatırım kategorisini belirler (mikro/küçük/orta/büyük cap). Risk profilinizi etkiler.",
        "common_mistake": "Piyasa değerini gerçek değer zannetmek. Şirket 10 milyar TL piyasa değerinde olabilir ama 15 milyar TL borcu da olabilir.",
    },
    "dividend-yield": {
        "simple_explanation": "Yatırdığınız paranın yüzde kaçını yılda temettü olarak geri aldığınızı gösterir. Temettü 5 TL, hisse fiyatı 100 TL ise temettü verimi %5.",
        "why_important": "Pasif gelir hedefleyenler için kritik. Ancak çok yüksek temettü verimi bazen şirketin sorunlu olduğuna işaret edebilir.",
        "common_mistake": "Sadece yüksek temettü verimine bakarak hisse seçmek. Sürdürülebilir temettü için şirketin nakit akışı ve kâr büyümesine de bakmak gerekir.",
    },
    "hisse-basina-kar": {
        "simple_explanation": "Şirketin net kârını hisse sayısına bölünce çıkan değer. Şirket hisse başına ne kadar kazanıyor? sorusunun cevabı.",
        "why_important": "F/K oranının paydasıdır; büyüme beklentileri bu metrikle ölçülür. Çeyrekten çeyreğe EPS büyümesi hisse fiyatını doğrudan etkiler.",
        "common_mistake": "Mutlak EPS değerine bakmak yerine büyüme oranını görmezden gelmek. EPS büyümesi yönü ve hızı fiyatı yönlendirir.",
        "finpilot_usage": ["analysis"],
    },
    "ozkaynak-karliligi": {
        "simple_explanation": "Şirketin hissedarların parasını ne kadar verimli kullandığını gösterir. ROE %20 ise her 100 TL özkaynak için 20 TL kâr üretiyor.",
        "why_important": "Uzun vadeli değer yatırımının temel ölçütü. Warren Buffett yüksek ve istikrarlı ROE'li şirketleri arar.",
        "common_mistake": "Çok yüksek ROE'nin her zaman iyi olduğunu düşünmek. Aşırı kaldıraçla şişirilmiş ROE yanıltıcıdır; borç/özkaynak oranıyla birlikte değerlendirin.",
        "finpilot_usage": ["analysis"],
    },
    "dcf": {
        "simple_explanation": "Şirketin gelecekte yaratacağı nakit akışlarını bugüne indirgeyerek adil fiyatını hesaplar. 'Bugün ödediğim para, gelecekteki getiriyi hak ediyor mu?' sorusunu yanıtlar.",
        "why_important": "Temel analizin en güçlü değerleme yöntemi. Ancak çok sayıda varsayıma dayandığı için sonuç değişkendir.",
        "common_mistake": "Büyüme oranını fazla iyimser seçmek. %1 büyüme farkı bile hesaplanan değeri %20-30 değiştirebilir.",
    },
    "ipo": {
        "simple_explanation": "Bir şirketin ilk kez borsa'da halka hisse satışı. Bundan önce şirket özel sahiplikte; IPO sonrası herkes hisse alabilir.",
        "why_important": "Erken giriş fırsatı sunabilir ama risk de yüksektir; şirketin geçmiş borsa verisi yoktur.",
        "common_mistake": "Her IPO'ya heyecanla girip 'ilk günde fiyat kesin yükselir' diye düşünmek. Tarihsel veri: IPO'ların %40'ı ilk yılını altında tamamlar.",
    },
    "ev-ebitda": {
        "simple_explanation": "Şirketin tüm borçlarıyla satın alınma maliyetini yıllık işletme kârına böler. 'Bu şirket kaç yılda kendini amorti eder?' sorusunun cevabı.",
        "why_important": "F/K'nın aksine sermaye yapısından bağımsız karşılaştırma sağlar. Kaldıraçlı sektörlerde (gayrimenkul, telekom) daha güvenilir.",
        "common_mistake": "Sektörden bağımsız değerlendirmek. EV/EBITDA 8x teknoloji şirketi için pahalı iken, altyapı şirketi için ucuz sayılabilir.",
    },
    # ── İLERİ DÜZEY KAVRAMLAR ───────────────────────────────────────────────────
    "sharpe-ratio": {
        "simple_explanation": "Aldığınız risk başına ne kadar getiri elde ettiğinizi gösterir. Sharpe 1.0 iyi, 2.0 çok iyi, 0'ın altı ise risksiz mevduattan daha kötü performans demektir.",
        "why_important": "Portföy performansını doğru ölçmenin temel yolu. Ham getiriyi değil, riski de hesaba katan tek metrik budur.",
        "common_mistake": "Yüksek getiri = iyi strateji zannetmek. %50 getiri elde eden ama %60 kayıp riski olan strateji, %15 getirili ama %5 kayıplı stratejiden çok daha kötüdür.",
        "finpilot_usage": ["analysis", "backtest"],
    },
    "beta": {
        "simple_explanation": "Hissenin piyasa (endeks) hareketlerine ne kadar duyarlı olduğunu gösterir. Beta 1.5 = endeks %10 düşünce hisse %15 düşer. Beta 0.5 = yarı kadar etkilenir.",
        "why_important": "Portföy riskini ölçmede temel araç. Yüksek beta = yüksek risk ve potansiyel getiri; düşük beta = daha savunmacı.",
        "common_mistake": "Betanın sabit olduğunu düşünmek. Beta piyasa koşullarına göre değişir; kriz dönemlerinde çoğu hissenin betası yükselir.",
    },
    "alpha": {
        "simple_explanation": "Portföyünüzün piyasa getirisini ne kadar aştığını gösterir. Alfa +5 = endeksten %5 daha iyi performans. Alfa 0 = sadece piyasa getirisi.",
        "why_important": "Yatırım kararlarınızın gerçekten değer yaratıp yaratmadığını ölçer. Uzun vadede pozitif alfa üretmek zorlu ama mümkündür.",
        "common_mistake": "Kısa vadeli alfa'yı kalıcı beceri sanmak. 1-2 yıllık pozitif alfa şans eseri de olabilir; anlamlı alfa için en az 5 yıllık veri gerekir.",
    },
    "dalgalanma": {
        "simple_explanation": "Fiyatın ne kadar oynak olduğunun ölçüsü. Yüksek volatilite = büyük ani hareketler. Düşük volatilite = sakin, istikrarlı seyir.",
        "why_important": "Risk yönetiminin temelini oluşturur. FinPilot, volatiliteye göre pozisyon büyüklüğünü otomatik ayarlar.",
        "common_mistake": "Volatiliteyi sadece 'kötü' görmek. Trader'lar için volatilite fırsattır; uzun vadeli yatırımcılar için ise risk.",
        "finpilot_usage": ["analysis", "scanner"],
    },
    "dusus-derinligi": {
        "simple_explanation": "Bir yatırımın zirve noktasından en derin çukura kadar düşüşünün yüzdesi. %50 drawdown: 100'den 50'ye düşmek anlamına gelir. Geri dönmek için %100 kazanmak gerekir!",
        "why_important": "Stratejinin en kötü dönemde sizi ne kadar 'sancıtacağını' gösterir. Uzun vadede kalmayı zorlaştıracak drawdown'ı önceden bilmek şarttır.",
        "common_mistake": "Sadece ortalama getiriye bakıp drawdown'ı görmezden gelmek. %40 drawdown yaşayan çoğu insan panikleyip tam dibinde satar.",
        "finpilot_usage": ["backtest"],
    },
    "leverage": {
        "simple_explanation": "Kendi paranızdan daha büyük pozisyon açmak için borç kullanmak. 5x kaldıraç = 100 TL ile 500 TL'lik işlem açmak. Kar da zarar da 5 katına çıkar.",
        "why_important": "Doğru kullanımda getiriyi artırır; yanlış kullanımda tüm sermayeyi sıfırlayabilir.",
        "common_mistake": "Yeni başlayanlara en tehlikeli araç. 5x kaldıraçla piyasa sadece %20 aleyhe giderse tüm paranız biter.",
    },
    "korunma": {
        "simple_explanation": "Portföyünüzü ters yönde bir pozisyonla sigortalamak. Hisse aldıysanız opsiyonla veya short satışla kayıp riskini sınırlarsınız.",
        "why_important": "Büyük kayıpları sınırlamanın en etkili yolu. Volatil dönemlerde portföy değerini korur.",
        "common_mistake": "Hedge maliyetini (sigorta primine benzer) hesaba katmamak. Sürekli hedge, uzun vadede getiriyi önemli ölçüde aşındırır.",
    },
    "liquidity": {
        "simple_explanation": "Bir varlığı hızla nakit paraya çevirme kolaylığı. Yüksek likidite = istediğiniz an alıp satabilirsiniz. Düşük likidite = satmak zor, kayıpla satmak zorunda kalabilirsiniz.",
        "why_important": "Kriz anında en kritik faktör olur. FinPilot scanner'ı düşük hacimli/likiditesiz hisseleri filtreler.",
        "common_mistake": "İyi piyasada likiditesiz varlık almak. Kriz gelince herkes satmak ister ama alıcı olmaz; fiyat çöker.",
        "finpilot_usage": ["scanner"],
    },
    # ── PİYASA İŞLEYİŞİ ────────────────────────────────────────────────────────
    "bull-market": {
        "simple_explanation": "Piyasanın genel olarak yükseldiği dönem. Genellikle dipten %20 veya daha fazla yükseliş olarak tanımlanır. Boğa yukarı saldırır, bu yüzden 'boğa piyasası' denir.",
        "why_important": "Strateji seçimini doğrudan etkiler. Boğa piyasasında çoğu hisse yükselir; doğru hisseyi seçmek görece kolaydır.",
        "common_mistake": "Boğa piyasasının sonu gelmeyeceğini düşünmek. Tüm boğa piyasaları er ya da geç sona erer; çıkış stratejisi şart.",
    },
    "bear-market": {
        "simple_explanation": "Piyasanın zirveye göre %20+ düştüğü dönem. Ayı saldırırken pençesini aşağı doğru vurur — bu yüzden 'ayı piyasası' denir.",
        "why_important": "Portföy dayanıklılığını test eder. Defansif hisseler, tahvil ve nakit önem kazanır.",
        "common_mistake": "Her düşüşü ayı piyasası saymak. Düzeltme (%10-20 düşüş) ile ayı piyasası (%20+ düşüş) farklı şeylerdir.",
    },
    "short-selling": {
        "simple_explanation": "Sahip olmadığınız hisseyi ödünç alıp satmak, sonra daha düşük fiyattan geri alıp kâr etmek. Fiyat düşerse kazanırsınız.",
        "why_important": "Piyasanın düşeceğini düşündüğünüzde veya hedge olarak kullanılır. Teorik kayıp sınırsızdır (fiyat sonsuza çıkabilir).",
        "common_mistake": "Short squeeze riskini küçümsemek. Fiyat beklenmedik şekilde yükselirse zarar hızla büyür; mutlaka stop-loss kullanın.",
    },
    "zarar-kes": {
        "simple_explanation": "Kayıplarınızı sınırlamak için önceden belirlediğiniz çıkış fiyatı. Hisseniz 10 TL'ye aldıysanız ve 9 TL'de stop koyduysanız, %10'dan fazla kaybetmezsiniz.",
        "why_important": "Profesyonel trader'ların en kritik kuralı. Küçük kayıpları kabul edip büyük kayıpları önler.",
        "common_mistake": "Stop-loss koymamak veya çok geniş koymak. 'Geri döner' diye umarken pozisyon %30-50 kaybedilebilir.",
        "finpilot_usage": ["analysis"],
    },
    "limit-order": {
        "simple_explanation": "İstediğiniz fiyatı belirtip işlemin ancak o fiyatta gerçekleşmesini sağlayan emir türü. 'Ancak 50 TL'den al' dersiniz; fiyat 50'ye gelene kadar işlem açılmaz.",
        "why_important": "Slippage'ı önler; belirlediğinizden kötü fiyatta alım/satım yapmaz.",
        "common_mistake": "Limit emir koyup piyasayı takip etmemek. Hızlı hareketlerde emir gerçekleşmeyebilir; fırsatı kaçırabilirsiniz.",
    },
    "margin-call": {
        "simple_explanation": "Kaldıraçlı pozisyonunuz büyük zarar edince broker'ın 'daha teminat yatır veya pozisyonu kapatıyorum' uyarısı. Acil bir borç talep çağrısıdır.",
        "why_important": "Kaldıraçlı yatırımın en tehlikeli anı. Margin call geldiğinde zaten zarardasınız ve ek para yatırmazsanız pozisyon zorunlu kapatılır.",
        "common_mistake": "Margin call geldiğinde daha fazla para yatırarak 'ortalamalamak'. Bu genellikle daha büyük kayba yol açar.",
    },
    # ── MAKROEKONOMİ ────────────────────────────────────────────────────────────
    "cpi": {
        "simple_explanation": "Bir sepet tüketici ürününün fiyatlarındaki değişimi ölçür. Enflasyonun ana göstergesidir. 'Geçen yıla göre alışveriş ne kadar pahalılaştı?'",
        "why_important": "Merkez bankası faiz kararlarını doğrudan etkiler. Yüksek CPI → faiz artışı → borsa baskısı. FinPilot makro takibinde kullanılır.",
        "common_mistake": "CPI'ın kendi harcamalarınızı yansıttığını düşünmek. CPI ortalama bir sepete dayanır; sizin sepetiniz farklı olabilir.",
        "finpilot_usage": ["analysis"],
    },
    "gdp-growth": {
        "simple_explanation": "Ülkenin ekonomik büyüme hızı. %3 GSYİH büyümesi = bir önceki yıla göre ekonomi %3 büyümüş. Negatif büyüme = daralma/kriz.",
        "why_important": "Şirket kârlarının ve hisse senedi piyasasının uzun vadeli yönünü belirler. Büyüyen ekonomi şirket gelirlerini artırır.",
        "common_mistake": "GSYİH büyümesi = borsa yükselişi zannetmek. Piyasalar geleceği fiyatlar; sürpriz büyüme önemli, beklenen büyüme değil.",
    },
    "recession": {
        "simple_explanation": "Ekonominin art arda iki çeyrekte küçüldüğü dönem. İşsizlik artar, tüketim azalır, şirket kârları düşer.",
        "why_important": "Resesyon dönemlerinde hisseler genellikle %30-50 değer kaybeder. Savunmacı yatırım stratejisi kritik hale gelir.",
        "common_mistake": "Resmi açıklanmadan önce pozisyon almaya çalışmak. Resesyon açıklandığında piyasalar genellikle aylarca önce tepki vermiştir.",
    },
    "monetary-policy": {
        "simple_explanation": "Merkez bankasının faiz oranlarını ve para arzını yöneterek ekonomiyi düzenleme politikası. Faizi artırır (enflasyona karşı) veya düşürür (büyümeyi destekler).",
        "why_important": "Tüm varlık fiyatlarını etkiler. Faiz artışı tahvil getirisini artırır, hisseleri caydırır; faiz indirimi tam tersi.",
        "common_mistake": "Fed/TCMB toplantısına gün sayıp hızlı karar almak. Piyasalar beklentileri önceden fiyatlar; açıklamada 'beklenmedik' bir şey olmadıkça reaksiyon sınırlı kalır.",
    },
    "yield-curve": {
        "simple_explanation": "Devlet tahvillerinin faizlerini vadeye göre grafik üzerinde gösterir. Normalde uzun vadeli tahvil daha yüksek faiz verir. Ters çevrilince (kısa vadeli yüksek) resesyon uyarısıdır.",
        "why_important": "Tarihsel olarak ters getiri eğrisi, 6-18 ay içinde resesyonu 8/8 öngördü. En güvenilir makro göstergelerden biri.",
        "common_mistake": "Ters eğrinin hemen resesyon anlamına geldiğini düşünmek. Sinyal ile resesyon arasında 1-2 yıl olabilir.",
    },
    "quantitative-easing": {
        "simple_explanation": "Merkez bankasının tahvil alarak piyasaya para basması. Faizleri sıfıra yaklaştırdıktan sonra ekonomiyi uyarmak için kullanılan özel araç.",
        "why_important": "2008 ve 2020 krizlerinde hisselerin geri toplanmasında büyük rol oynadı. 'Fed'e karşı gitme' kuralının temelinde QE yatar.",
        "common_mistake": "QE'nin sonsuz süreceğini düşünmek. QE'nin sona ermesi (taper) piyasalarda büyük satış dalgası tetikleyebilir.",
    },
    # ── RİSK YÖNETİMİ ──────────────────────────────────────────────────────────
    "var": {
        "simple_explanation": "Belirli bir güven aralığında, belirli bir sürede kaybedebileceğiniz maksimum tutarı tahmin eder. '%95 güvenle 1 günde en fazla 10,000 TL kaybederim' gibi.",
        "why_important": "Bankalar ve kurumsal yatırımcılar günlük risk limitlerini VaR ile belirler. FinPilot portföy risk hesaplamasında kullanılır.",
        "common_mistake": "VaR'ın sınırını abartmak. VaR 'olası' kaybı gösterir, 'maksimum' kaybı değil. Kara kuğu olaylarında VaR çok aşılabilir.",
    },
    "max-drawdown": {
        "simple_explanation": "Bir stratejinin ya da portföyün tarihinde gördüğü en büyük zirve-dip kaybı yüzdesi. Strateji ne kadar 'acı verebilir'in ölçüsü.",
        "why_important": "Gerçekçi risk beklentisi oluşturmanın en iyi yolu. FinPilot backtest raporlarında her strateji için gösterilir.",
        "common_mistake": "Geçmiş max drawdown'ın tekrarlanmayacağını düşünmek. Tarihsel max drawdown gelecekteki en kötü senaryonun alt sınırıdır, üst sınırı değil.",
        "finpilot_usage": ["backtest", "analysis"],
    },
    "standard-deviation": {
        "simple_explanation": "Getirilerinizin ortalamadan ne kadar saptığını gösterir. Standart sapma yüksek = büyük dalgalanmalar, tahmin etmesi zor. Düşük = istikrarlı, öngörülebilir.",
        "why_important": "Volatilite ölçüsünün matematiksel temelidir. Sharpe oranı ve VaR hesaplamalarının bel kemiği.",
        "common_mistake": "Getiri dağılımının normal (çan eğrisi) şeklinde olduğunu varsaymak. Finansal getiriler aşırı olayları (kuyruk riskini) daha sık yaşar.",
    },
    "black-swan": {
        "simple_explanation": "Önceden tahmin edilemeyen, nadiren olan ama gerçekleşince büyük etki yaratan olaylar. 2008 krizi, COVID-19, ani iflas gibi.",
        "why_important": "Hiçbir model bunu öngöremez; bu yüzden portföyde 'kara kuğu koruması' (nakit, altın, opsiyonlar) bulundurmak akıllıca.",
        "common_mistake": "'Bu sefer farklı' ya da 'bu kadar nadirdir ki olmuyor' demek. Her on yılda en az bir kara kuğu olayı gerçekleşiyor.",
    },
    "systematic-risk": {
        "simple_explanation": "Tüm piyasayı etkileyen ve çeşitlendirmeyle önlenemeyen risk. Savaş, kriz, faiz artışı gibi. Ne kadar çok hisse alırsanız alın bu riski yok edemezsiniz.",
        "why_important": "Çeşitlendirmenin sınırlarını anlamak için temel kavram. Bu risk beta ile ölçülür.",
        "common_mistake": "Çok sayıda hisse alarak her türlü riski önleyebileceğini sanmak. Sistematik risk herkesi vurur.",
    },
    # ── PORTFÖY TEORİSİ ─────────────────────────────────────────────────────────
    "asset-allocation": {
        "simple_explanation": "Paranızı farklı varlık türlerine (hisse, tahvil, altın, nakit) dağıtmak. 'Bütün yumurtaları aynı sepete koyma' ilkesinin uygulaması.",
        "why_important": "Araştırmalar, uzun vadede portföy performansının %90'ının varlık dağılımı kararından geldiğini gösteriyor.",
        "common_mistake": "Varlık dağılımını kurmak ama hiç değiştirmemek. Piyasalar değiştikçe dağılım bozulur; yeniden dengeleme şart.",
    },
    "rebalancing": {
        "simple_explanation": "Portföyünüzü başlangıçta belirlediğiniz hedef dağılıma geri getirmek. Yükselen varlıktan biraz sat, düşenden biraz al.",
        "why_important": "Otomatik olarak 'düşükten al, yüksekten sat' uygular. Uzun vadede %1-2 ekstra yıllık getiri sağlayabilir.",
        "common_mistake": "Çok sık yeniden dengeleme yapmak. Her ay rebalancing yapmak işlem maliyetini artırır; yılda 1-2 kez yeterlidir.",
    },
    "modern-portfolio-theory": {
        "simple_explanation": "Birbiriyle ilişkisiz varlıkları bir araya getirerek aynı getiriyi daha düşük riskle elde etmeyi hedefleyen teori. Çeşitlendirmenin matematiksel temeli.",
        "why_important": "Markowitz tarafından 1952'de geliştirilen Nobel ödüllü teori. Tüm modern portföy yönetiminin temelini oluşturur.",
        "common_mistake": "Teorinin pratikte mükemmel çalışacağını beklemek. Kriz dönemlerinde korelasyonlar 1'e yaklaşır ve çeşitlendirme faydasını yitirir.",
    },
    "capm": {
        "simple_explanation": "Bir hissenin beklenen getirisinin 'risksiz faiz + hissenin piyasa riskine (beta) göre ek getiri' olması gerektiğini söyleyen model.",
        "why_important": "Hisse değerlemesinde iskonto oranını belirlemek için kullanılır. DCF modellerinin arka planında CAPM yatar.",
        "common_mistake": "CAPM'in tek-faktör modeli olduğunu unutmak. Gerçek piyasada boyut, momentum, değer gibi başka faktörler de getiriyi etkiler (Fama-French).",
    },
    "risk-free-rate": {
        "simple_explanation": "Teorik olarak sıfır riskli yatırımın getirisi. Pratikte kısa vadeli devlet tahvil faizi kullanılır. Tüm yatırım kararlarının karşılaştırma noktası.",
        "why_important": "Sharpe oranı ve CAPM'in temel bileşenidir. 'Bu yatırım risk almaya değer mi?' sorusunun referans noktası.",
        "common_mistake": "Enflasyonu hesaba katmamak. Risksiz faiz %40 ama enflasyon %50 ise gerçek risksiz getiri negatiftir.",
    },
    # ── TEMEL FİNANS KAVRAMLARI ─────────────────────────────────────────────────
    "dividend": {
        "simple_explanation": "Şirketin kârından hissedarlara ödediği nakit pay. Örneğin hisse başına 2 TL temettü verirse, 100 hisseniz varsa 200 TL nakit alırsınız.",
        "why_important": "Pasif gelir ve uzun vadeli yatırımın temel unsuru. Temettü yeniden yatırımı (bileşik etki) ile sermaye önemli ölçüde büyür.",
        "common_mistake": "Temettü ödeyen şirketin her zaman iyi yatırım olduğunu düşünmek. Şirket büyümek için yatırım yerine temettü dağıtıyorsa büyüme fırsatı kaçıyor olabilir.",
    },
    "etf": {
        "simple_explanation": "Pek çok hisseyi veya tahvili bir arada tutan ve borsada hisse gibi alınıp satılan yatırım aracı. BIST100'e yatırım yapmak istiyorsanız tek bir ETF alabilirsiniz.",
        "why_important": "Düşük maliyet ve anında çeşitlendirme sağlar. Dünyada en hızlı büyüyen yatırım aracıdır.",
        "common_mistake": "ETF = tamamen güvenli zannetmek. ETF de piyasa düşünce düşer; sadece tek hisse riskinden korur.",
    },
}


def main():
    data = json.loads(SRC.read_text(encoding="utf-8"))
    updated = 0
    for entry in data:
        slug = entry.get("slug", "")
        if slug in ENRICHMENTS:
            for key, val in ENRICHMENTS[slug].items():
                entry[key] = val
            updated += 1
    SRC.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated {updated} entries in {SRC}")


if __name__ == "__main__":
    main()
