"""
Finance Academy — Starter Content Seeder
==========================================
LLM'e ihtiyaç duymadan sistemi başlatmak için elle yazılmış
temel içerikler. Her domain için 1 başlangıç dersi.

Çalıştır:
  python -m academy.seed_content
"""

from __future__ import annotations

from datetime import datetime, timedelta

from academy.models import (
    Lesson,
    LessonComponent,
    LessonComponentRepository,
    LessonRepository,
    init_db,
)

SEED_LESSONS: list[dict] = [
    # ──────────────────────────────────────────────────────────────────
    # 1. TEMEL FİNANS
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "FF-001-para-nedir",
        "domain": "fundamental-finance",
        "domain_id": 1,
        "module": "Para ve Değeri",
        "title": "Para Nedir? Değeri Nereden Gelir?",
        "difficulty": "beginner",
        "estimated_minutes": 8,
        "content": """## Para Nedir?

Para, mal ve hizmetlerin değişimini kolaylaştıran bir araçtır. Ancak paranın kendisi doğaları itibariyle değersizdir — bir kağıt parçası veya dijital kayıt. Peki değeri nereden gelir?

### Paranın 3 Temel İşlevi

1. **Değişim aracı**: Alışveriş yaparken kullanırsın. Muz karşılığında gömlek takas etmek zorunda kalmazsın.
2. **Değer saklama aracı**: Bugün kazandığın parayı yarın harcayabilirsin. (Enflasyon bunu aşındırır ama...)
3. **Hesap birimi**: "Bu araba kaç lira?" diye sorabilirsin — ortak bir ölçek vardır.

### Paranın Değeri Güvene Dayanır

Modern para "fiat para"dır — yani devletin "bu geçerlidir" demesiyle değer taşır. Altın standardı 1971'de tamamen terk edildi. Bugün Türk Lirası veya Amerikan Doları'nın arkasında altın yok, **güven** var.

Bu güven zayıfladığında ne olur? Enflasyon hızlanır, para değer kaybeder.

### Gerçek Hayat Örneği

2021-2022 yıllarında Türk Lirası, bir yılda USD karşısında %44 değer kaybetti. Lira bazında 100.000 TL birikimin değeri, dolar bazında neredeyse yarıya indi. Tasarruflarını hangi para biriminde tuttuğun, zenginleşme veya fakirleşme arasındaki fark olabilir.

### Yatırımcı İçin Ne Anlam İfade Eder?

Paranın değeri sabit değildir. Yatırım yapmanın temel amacı: paranın satın alma gücünü korumak, tercihen artırmak. Nakit tutmak "güvenli" değil — enflasyona karşı her gün biraz kaybediyorsun.""",
        "key_takeaways": [
            "Para, değişim aracı, değer saklama ve hesap birimi işlevi görür",
            "Modern para güvene dayanır, arkasında fiziksel varlık yok",
            "Enflasyon paranın satın alma gücünü sürekli aşındırır",
            "Nakit tutmak 'güvenli' değil — yatırım yapmak bir zorunluluktur",
        ],
        "misconceptions": [
            "Yanlış: 'Bankada para tutmak en güvenli yoldur' — Enflasyona göre her yıl değer kaybedersin",
            "Yanlış: 'Para değerini korur' — Tarihsel olarak tüm paralar değer kaybetmiştir",
        ],
        "real_example": {"ticker": "TRY/USD", "context": "TL 2021-2022 arasında %44 değer kaybı"},
        "quizzes": [
            {
                "question": "Paranın 'değer saklama aracı' işlevi hangisini ifade eder?",
                "options": [
                    "A) Mal ve hizmet alışverişinde kullanılması",
                    "B) Bugün kazanılan değerin ileriye taşınabilmesi",
                    "C) Fiyat karşılaştırması yapılabilmesi",
                    "D) Devlet tarafından basılması",
                ],
                "correct": "B",
                "explanation": "Değer saklama, bugün kazandığın parayı ileriki bir tarihte harcayabilme özelliğidir. Enflasyon bu özelliği zayıflatır.",
            }
        ],
        "flashcards": [
            {
                "front": "Fiat Para nedir?",
                "back": "Fiziksel bir karşılığı (altın vb.) olmayan, devlet güvencesiyle değer taşıyan para.",
            },
            {
                "front": "Paranın 3 işlevi nedir?",
                "back": "1) Değişim aracı  2) Değer saklama  3) Hesap birimi",
            },
            {
                "front": "Enflasyon ne yapar?",
                "back": "Paranın satın alma gücünü azaltır — aynı para ile daha az mal/hizmet alabilirsin.",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 2. BORSA VE HİSSE SENETLERİ
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "SM-001-borsa-nasil-calisir",
        "domain": "stocks-market",
        "domain_id": 2,
        "module": "Borsa Nasıl Çalışır",
        "title": "Borsa Nasıl Çalışır? Hisse Senedi Nedir?",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "content": """## Borsa Nasıl Çalışır?

Borsa, şirket hisselerinin alınıp satıldığı organize bir piyasadır. New York Stock Exchange (NYSE) veya NASDAQ, günde milyonlarca işlemin gerçekleştiği bu piyasaların en büyükleridir.

### Hisse Senedi Nedir?

Bir şirketin küçük bir parçasına sahip olma belgesidir. Apple'ın 1 hissesini satın aldığında, Apple'ın küçücük de olsa bir ortağı olursun. Şirket büyüdükçe hissenin değeri artar; kötü giderse düşer.

### Alıcı ve Satıcı Eşleşmesi

Borsa bir "pazar yeri"dir. Biri satar, biri alır — borsa sadece bu eşleşmeyi organize eder:

- **Bid (teklif fiyatı)**: Alıcının ödemeye razı olduğu maksimum fiyat
- **Ask (satış fiyatı)**: Satıcının kabul edeceği minimum fiyat
- **Spread**: Bid ile Ask arasındaki fark — bu fark ne kadar küçükse piyasa o kadar "likit"

### Piyasa Saatleri

NYSE ve NASDAQ: **09:30 – 16:00 ET** (Doğu ABD saati)
İşlem öncesi/sonrası (pre/after market): 04:00 – 09:30 ve 16:00 – 20:00

### Piyasa Değeri (Market Cap)

Şirketin toplam değeri = Hisse fiyatı × Toplam hisse sayısı

Apple, 2024'te ~3 trilyon dolar piyasa değeriyle dünyanın en değerli şirketi. Bu rakam tüm Türkiye ekonomisinin büyüklüğünden fazla.""",
        "key_takeaways": [
            "Borsa, hisse senetlerinin alınıp satıldığı organize piyasadır",
            "Hisse senedi = bir şirkete ortak olma belgesi",
            "Bid/Ask spread piyasanın likiditesini gösterir",
            "Piyasa değeri = Hisse fiyatı × Toplam hisse sayısı",
        ],
        "misconceptions": [
            "Yanlış: 'Borsa kumar gibidir' — Borsa, şirketlere ortak olma platformudur; uzun vadede ekonomik büyümeyi yansıtır",
            "Yanlış: 'Hisse alınca şirkete borç verirsin' — Borç verme tahvil ile olur; hisse ortak olmaktır",
        ],
        "real_example": {
            "ticker": "AAPL",
            "context": "Apple 2024'te ~3 trilyon dolar piyasa değeri",
        },
        "quizzes": [
            {
                "question": "Apple'ın 10 hissesini satın aldığında ne olur?",
                "options": [
                    "A) Apple'a borç vermiş olursun",
                    "B) Apple'ın küçük bir ortağı olursun",
                    "C) Apple'dan temettü alma garantin olur",
                    "D) Apple'ın yönetimine katılma hakkı kazanırsın",
                ],
                "correct": "B",
                "explanation": "Hisse senedi sahipliği = şirkete ortak olmak. Temettü garantisi yoktur; yönetim hakkı çok küçük pay için anlamsızdır. Borç verme ise tahvil ile yapılır.",
            }
        ],
        "flashcards": [
            {"front": "Bid nedir?", "back": "Alıcının ödemek istediği maksimum fiyat."},
            {"front": "Ask nedir?", "back": "Satıcının kabul edeceği minimum fiyat."},
            {
                "front": "Piyasa değeri formülü?",
                "back": "Hisse fiyatı × Toplam dolaşımdaki hisse sayısı",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 3. TEKNİK ANALİZ
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "TA-001-grafik-tipleri",
        "domain": "technical-analysis",
        "domain_id": 3,
        "module": "Grafik Tipleri",
        "title": "Mum Grafikleri: Trader'ın En Güçlü Silahı",
        "difficulty": "beginner",
        "estimated_minutes": 12,
        "content": """## Mum Grafikleri (Candlestick Charts)

Japonya'dan 18. yüzyılda gelen bu grafik tipi, fiyat hareketini en zengin biçimde gösterir.

### Bir Mumun Anatomisi

Her mum 4 bilgiyi taşır: **Açılış, Kapanış, Yüksek, Düşük** (OHLC)

```
     │  ← Üst gölge (Wick/Shadow)
   ┌─┴─┐
   │   │  ← Gövde (Body)
   └─┬─┘    • Yeşil/Beyaz = Kapanış > Açılış (YUKARI)
     │  ← Alt gölge        • Kırmızı/Siyah = Kapanış < Açılış (AŞAĞI)
```

### Gölgeler Ne Anlatır?

- **Uzun üst gölge**: Yukarı denediler ama tutamadılar → satış baskısı
- **Uzun alt gölge**: Aşağı düştü ama toplandı → alış desteği
- **Küçük gövde**: Karar verilemiyor → tersine dönme potansiyeli

### Kritik Mum Formasyonları

| Formasyon | Anlam | Örnek |
|-----------|-------|-------|
| Hammer (Çekiç) | Düşüşten dönüş sinyali | Uzun alt gölge, küçük gövde |
| Shooting Star | Yükselişten dönüş sinyali | Uzun üst gölge, küçük gövde |
| Doji | Kararsızlık | Gövde neredeyse yok |
| Engulfing | Güçlü tersine dönüş | Önceki mumu tamamen yutan mum |

### Zaman Dilimleri

- **1 dakika**: Scalper'lar için
- **15 dakika**: Kısa vadeli swing
- **1 saat / 4 saat**: Orta vadeli
- **1 gün (Daily)**: Trend takibi

**FinPilot kullanırken**: Strateji B sinyalleri 15 dakika + 1 saat + 4 saat + günlük grafiklerin hizalamasına bakar.""",
        "key_takeaways": [
            "Her mum: Açılış, Kapanış, Yüksek, Düşük bilgisini içerir",
            "Yeşil mum = kapanış açılıştan yüksek (boğa); Kırmızı = düşük (ayı)",
            "Gölge uzunluğu o yönde deneme yapıldığını ama tutunulamadığını gösterir",
            "Mum formasyonları tek başına değil bağlam içinde anlam taşır",
        ],
        "misconceptions": [
            "Yanlış: 'Her yeşil mum alım sinyalidir' — Tek muma bakarak işlem yapılmaz",
            "Yanlış: 'Çekiç formasyonu her zaman yükseliş getirir' — Bağlam (trend, hacim) kritiktir",
        ],
        "real_example": {
            "ticker": "SPY",
            "context": "2022 ayı piyasasında her rallide shooting star formasyonu oluştu",
        },
        "quizzes": [
            {
                "question": "Bir mum grafiğinde uzun alt gölge ve küçük gövde ne anlama gelir?",
                "options": [
                    "A) Satış baskısı çok güçlü",
                    "B) Fiyat aşağı düştü ama alıcılar topladı — destek var",
                    "C) Piyasa yatay seyrediyor",
                    "D) İşlem hacmi düşük",
                ],
                "correct": "B",
                "explanation": "Uzun alt gölge: fiyat aşağı denedi ama alıcılar devreye girdi ve kapanış yukarı çekti. Bu genellikle destek seviyesini gösterir.",
            }
        ],
        "flashcards": [
            {
                "front": "OHLC nedir?",
                "back": "Open (Açılış), High (Yüksek), Low (Düşük), Close (Kapanış)",
            },
            {
                "front": "Doji mumu ne gösterir?",
                "back": "Alıcı ve satıcı güçlerinin eşit olduğu kararsızlık anı. Genellikle tersine dönüş habercisi.",
            },
            {
                "front": "Engulfing formasyonu nedir?",
                "back": "Bir mumun bir önceki mumu tamamen yutması. Güçlü tersine dönüş sinyali.",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 6. RİSK YÖNETİMİ
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "RM-001-risk-nedir",
        "domain": "risk-management",
        "domain_id": 6,
        "module": "Risk Nedir",
        "title": "Risk Yönetimi: Sermayeni Korumanın Bilimi",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "content": """## Risk Yönetimi Neden Kritik?

Piyasalarda başarıyı belirleyen en az kazanmak kadar önemli bir şey var: **kaybetmemek**.

### Drawdown Matematiği

%50 kaybedersen geri dönmek için %100 kazanman gerekir!

| Kayıp | Geri Dönüş İçin Gerekli Kazanç |
|-------|--------------------------------|
| %10   | %11                            |
| %25   | %33                            |
| %50   | %100                           |
| %75   | %300                           |

Bu tablo neden büyük kayıpları önlemenin küçük kazançlar toplamaktan çok daha önemli olduğunu gösteriyor.

### 2% Kuralı

En yaygın risk yönetimi kuralı: **Her işlemde hesabın maksimum %2'sini riske at.**

Örnek: 10.000 dolar hesabın varsa, tek işlemde 200 dolardan fazla kaybetme.

Neden 2%? 50 ard arda yanlış işlem yapmadan hesabını sıfırlayamazsın.

### Stop-Loss Nedir?

Belirlediğin kayıp limitine ulaşıldığında pozisyonunu otomatik kapatan emir türü.

Örnek: AAPL'yi 185 dolardan aldın. Stop-loss = 179 dolar (%3.2 kayıp). Fiyat 179'a düşerse — satış otomatik gerçekleşir. Ne kadar kaybedeceğini baştan biliyorsun.

### FinPilot'ta Risk Yönetimi

FinPilot'un tarama motoru her sinyal için ATR (Average True Range) bazlı dinamik stop-loss hesaplar. "Sniper" stratejisinde 1.5× ATR, "Defansif" stratejisinde 2.5× ATR kullanılır.""",
        "key_takeaways": [
            "%50 kaybedersen geri dönmek için %100 kazanman gerekir — asimetrik matematikten kaçış yok",
            "2% kuralı: tek işlemde hesabın en fazla %2'sini riske at",
            "Stop-loss koymak zayıflık değil, profesyonellik işaretidir",
            "Kazanmak kadar önemli: kaybetmemek",
        ],
        "misconceptions": [
            "Yanlış: 'Stop-loss koymak fırsatı kaçırmaktır' — Stop-loss seni oyunda tutar",
            "Yanlış: 'Büyük kayıplardan hızla çıkılır' — Matematiksel olarak imkansıza yakın",
        ],
        "real_example": {
            "ticker": "TSLA",
            "context": "TSLA 2022'de 70% düştü; geri dönmek için 233% kazanç gerekiyor",
        },
        "quizzes": [
            {
                "question": "10.000 dolarlık hesabından %50 kaybettin. Başlangıç değerine dönmek için ne kadar kazanman gerekir?",
                "options": ["A) %50", "B) %75", "C) %100", "D) %150"],
                "correct": "C",
                "explanation": "5.000 dolardan başlayarak 10.000 dolara ulaşmak için %100 kazanman gerekir. 5000 × 2 = 10.000.",
            }
        ],
        "flashcards": [
            {
                "front": "2% kuralı nedir?",
                "back": "Tek bir işlemde hesabınızın maksimum %2'sini riske atmak.",
            },
            {
                "front": "Drawdown nedir?",
                "back": "Portföyün tepe değerinden en düşük noktaya kadar olan yüzde düşüşü.",
            },
            {
                "front": "Stop-loss nedir?",
                "back": "Belirlenen kayıp seviyesine ulaşıldığında pozisyonu otomatik kapatan emir.",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 9. PSİKOLOJİ VE DAVRANIŞSAL FİNANS
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "BF-001-kayiptan-kacınma",
        "domain": "behavioral-finance",
        "domain_id": 9,
        "module": "Kayıptan Kaçınma (Loss Aversion)",
        "title": "Neden Kaybetmekten Kazanmaktan Daha Çok Korkarız?",
        "difficulty": "beginner",
        "estimated_minutes": 9,
        "content": """## Kayıptan Kaçınma Bias'ı

Daniel Kahneman ve Amos Tversky'nin Nobel ödüllü araştırması şunu ortaya koydu:

> **100 dolar kaybetmenin acısı, 100 dolar kazanmanın sevincinden yaklaşık 2 kat daha güçlüdür.**

Bu "kayıptan kaçınma" (loss aversion) denilen bilişsel bir önyargı — ve piyasalarda sürekli yanlış kararlar aldırır.

### Trader'lar Nasıl Etkilenir?

**Senaryo 1 — Kazanan pozisyon:**
AAPL 190'dan 200'e çıktı. "+%5 kârdayım, ama ya düşerse?" → Çok erken satış. Kazancı budanır.

**Senaryo 2 — Kaybeden pozisyon:**
AAPL 190'dan 175'e düştü. "Stop-loss koymadım, bekleyeyim geri döner." → Küçük kayıp büyük kayba dönüşür.

İki senaryo aynı psikolojinin ürünü: kayıptan daha çok korkuyoruz.

### Somut Sonuçlar

- Kazanan pozisyonlar **erken** satılır (küçük kâr yeterli hissedilir)
- Kaybeden pozisyonlar **çok geç** kapatılır (kayıp gerçekleşmeden yokmuş gibi davranılır)
- Sonuç: Ortalama kâr küçük, ortalama zarar büyük → sistem çalışmaz

### Çözüm: Kurala Dayalı Sistem

Duygusal kararları yok etmenin tek yolu: **önceden belirlenmiş kurallar.**

- Stop-loss: önceden belirle, dokunma
- Take-profit: hedefe ulaşınca al, "daha çıkar mı" diye bekleme
- FinPilot gibi araçlar: sinyali insan yargısından bağımsız üretir""",
        "key_takeaways": [
            "Kayıp acısı, eşit kazanç sevincinden ~2 kat daha güçlüdür",
            "Bu önyargı: kazananları erken, kaybedenleri geç satmaya iter",
            "Çözüm: kural bazlı sistem — stop-loss ve TP önceden belirlenir",
            "Kahraman trader değil, tutarlı sistemci ol",
        ],
        "misconceptions": [
            "Yanlış: 'Duygularımı kontrol edebilirim' — Araştırmalar gösteriyor ki stres altında kontrol zorlaşır",
            "Yanlış: 'Zararı bekleyince geri döner' — İstatistiksel olarak çoğunlukla daha da düşer",
        ],
        "real_example": {
            "ticker": "GME",
            "context": "2021 GameStop: Kayıptan kaçınanlar 483'den 40'a düşerken tuttu",
        },
        "quizzes": [
            {
                "question": "Kayıptan kaçınma bias'ına göre trader hangi hatayı yapar?",
                "options": [
                    "A) Kaybeden pozisyonları çok erken kapatır",
                    "B) Kazanan pozisyonları çok erken satar, kaybeden pozisyonları çok geç kapatır",
                    "C) Her zaman stop-loss koyar",
                    "D) Piyasaya hiç girmez",
                ],
                "correct": "B",
                "explanation": "Kayıptan kaçınma, kârlı pozisyonları erken kapatmaya (kâr güvende kalsın) ve zararlı pozisyonları geç kapatmaya (zarar gerçekleşmesin) iter.",
            }
        ],
        "flashcards": [
            {
                "front": "Loss Aversion nedir?",
                "back": "Eşit miktarda kayıp, kazanç ile kıyaslandığında yaklaşık 2 kat daha güçlü hissedilir. Kahneman & Tversky.",
            },
            {
                "front": "Disposition Effect nedir?",
                "back": "Kazanan hisseleri erken satıp, kaybeden hisseleri elde tutma eğilimi. Loss aversion'ın doğrudan sonucu.",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 4. TEMEL ANALİZ
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "FA-001-degerleme-yontemleri",
        "domain": "fundamental-analysis",
        "domain_id": 4,
        "module": "Değerleme Yöntemleri (P/E, DCF)",
        "title": "P/E Oranı: Bir Hisse Pahalı mı Ucuz mu?",
        "difficulty": "beginner",
        "estimated_minutes": 11,
        "content": """## P/E Oranı Nedir?

Fiyat/Kazanç oranı (Price/Earnings, P/E), bir hissenin fiyatının şirketin kârına
göre "kaç kat" olduğunu gösterir.

```
P/E = Hisse Fiyatı ÷ Hisse Başına Kâr (EPS)
```

Örnek: Hisse 100 dolar, EPS 5 dolar → P/E = 20. Yani yatırımcı, şirketin yıllık
kârının 20 katını ödüyor.

### P/E Tek Başına Ne Anlatır, Ne Anlatmaz?

P/E yüksekse iki farklı hikâye olabilir: piyasa şirketin hızlı büyüyeceğine
inanıyor (büyüme primi) YA DA hisse gerçekten pahalı fiyatlanmış. P/E düşükse
de iki hikâye olabilir: hisse ucuz kalmış bir fırsat YA DA şirketin gerçek bir
sorunu var ve piyasa bunu fiyatlıyor. P/E sayısı tek başına hangisi olduğunu
söylemez — bağlam gerekir.

### Karşılaştırma Olmadan P/E Anlamsızdır

| Şirket | P/E | Sektör Ortalaması |
|--------|-----|--------------------|
| Yazılım şirketi | 35 | 30 (normal) |
| Bankacılık şirketi | 35 | 10 (aşırı yüksek) |

Aynı P/E, farklı sektörlerde farklı anlam taşır. Büyüme sektörleri (yazılım,
teknoloji) yapısal olarak daha yüksek P/E ile işlem görür; olgun sektörler
(bankacılık, enerji) daha düşük P/E'yi normal karşılar.

### DCF (İndirgenmiş Nakit Akışı) — Kısaca

DCF, bir şirketin gelecekte üreteceği tahmini nakit akışlarını bugünkü değere
indirger. Mantık: "Bu şirket önümüzdeki 10 yılda ne kadar nakit üretecek, ve
bu nakit bugün ne kadar eder?"

DCF'in zayıf noktası: girdileri (büyüme oranı, iskonto oranı) tahminden
ibarettir. Küçük bir varsayım değişikliği, sonucu büyük ölçüde değiştirebilir
— bu yüzden DCF tek başına değil, diğer yöntemlerle birlikte kullanılır.

### FinPilot'ta Temel Analiz

FinPilot'un tarama motoru fiyat/hacim davranışına odaklanır; P/E veya DCF gibi
temel değerleme metriklerini sinyal üretiminde kullanmaz. Bu ayrım kasıtlıdır:
teknik tarama "şu an ne oluyor"yu, temel analiz "bu şirket gerçekte ne değer"i
yanıtlar — ikisi farklı sorulara cevap verir ve birbirinin yerine geçmez.""",
        "key_takeaways": [
            "P/E = Hisse Fiyatı ÷ Hisse Başına Kâr — 'kaç kat ödüyorsun' sorusuna cevap verir",
            "Yüksek/düşük P/E tek başına 'pahalı/ucuz' anlamına gelmez — sektör karşılaştırması şart",
            "DCF, gelecekteki nakit akışlarını bugüne indirger; varsayımlara aşırı duyarlıdır",
            "Temel analiz 'ne değer' sorusuna, teknik tarama 'şu an ne oluyor' sorusuna cevap verir",
        ],
        "misconceptions": [
            "Yanlış: 'Düşük P/E her zaman ucuz demektir' — Düşük P/E bazen gerçek bir sorunun fiyatlanmasıdır",
            "Yanlış: 'DCF kesin bir değer üretir' — DCF sonucu, girilen varsayımlar kadar güvenilirdir",
        ],
        "real_example": {
            "ticker": "NVDA",
            "context": "NVDA 2023-2024'te yüksek P/E ile işlem gördü; piyasa büyüme beklentisini fiyatlıyordu",
        },
        "quizzes": [
            {
                "question": "Bir yazılım şirketinin P/E'si 35, sektör ortalaması 30. Bir bankacılık şirketinin P/E'si de 35, sektör ortalaması 10. Bu ikisi hakkında ne söylenebilir?",
                "options": [
                    "A) İkisi de aynı derecede 'normal' fiyatlanmış",
                    "B) Yazılım şirketi sektörüne göre hafif yüksek, banka aşırı yüksek fiyatlanmış olabilir",
                    "C) İkisi de aşırı ucuz",
                    "D) P/E bu şirketler için karşılaştırılamaz",
                ],
                "correct": "B",
                "explanation": "P/E'nin anlamı sektöre göre değişir. Aynı P/E değeri, kendi sektör ortalamasına göre çok farklı bir sinyal taşıyabilir.",
            }
        ],
        "flashcards": [
            {"front": "P/E oranı formülü?", "back": "Hisse Fiyatı ÷ Hisse Başına Kâr (EPS)"},
            {
                "front": "DCF nedir?",
                "back": "Bir şirketin gelecekteki nakit akışlarını bugünkü değere indirgeyen değerleme yöntemi.",
            },
            {
                "front": "P/E'yi tek başına yorumlamak neden risklidir?",
                "back": "Sektör bağlamı olmadan yüksek/düşük P/E'nin 'büyüme primi' mi yoksa 'gerçek sorun' mu olduğu ayırt edilemez.",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 5. PORTFÖY YÖNETİMİ
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "PM-001-diversifikasyon",
        "domain": "portfolio-management",
        "domain_id": 5,
        "module": "Diversifikasyon Nedir",
        "title": "Diversifikasyon: Tüm Yumurtaları Aynı Sepete Koymamak",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "content": """## Diversifikasyon Neden İşe Yarar?

Diversifikasyon, farklı varlıklara yatırım yaparak tek bir varlığın kötü
performansının tüm portföyü batırmasını engellemektir. Matematiksel temeli:
farklı varlıklar aynı anda, aynı yönde hareket etmediği (düşük korelasyon)
sürece, portföyün toplam dalgalanması tek tek varlıkların ortalamasından
daha düşük olur.

### Basit Bir Örnek

10.000 doları tek bir hisseye koyarsan ve o şirket %40 düşerse, portföyün
%40 düşer. Aynı 10.000 doları birbiriyle düşük korelasyonlu 10 farklı
hisseye eşit dağıtırsan, bir hissenin %40 düşmesi portföyü sadece ~%4
etkiler (diğerleri sabit kalırsa).

### Diversifikasyon Neyi Çözer, Neyi Çözmez

Çözer: **şirkete özgü risk** (tek bir şirketin skandal, iflas, ürün
başarısızlığı yaşaması). Bir hisseye ne kadar çok para bağlarsan, o şirkete
özgü bir olay seni o kadar çok etkiler.

Çözmez: **piyasa riski** (sistematik risk). 2008 veya 2020'de neredeyse tüm
hisseler aynı anda düştü — çünkü kriz anlarında korelasyonlar birbirine
yaklaşır. Diversifikasyon dalgalanmayı azaltır ama piyasa çapında bir düşüşü
tamamen ortadan kaldırmaz.

### Ne Kadar Diversifikasyon Yeterli?

Akademik araştırmalar, rastgele seçilmiş ~20-30 hisseden oluşan bir
portföyün, şirkete-özgü riskin büyük kısmını ortadan kaldırdığını gösteriyor.
Bunun ötesinde eklenen her yeni hisse, azalan getiriler sağlar — 20 hisseden
100 hisseye çıkmak, riski önemli ölçüde daha fazla azaltmaz ama takip etmeyi
zorlaştırır.

### Diversifikasyon Sadece "Çok Hisse" Değildir

Gerçek diversifikasyon; farklı sektörler, farklı varlık sınıfları (hisse,
tahvil, emtia), farklı coğrafyalar arasında dağılımı içerir. 15 farklı
teknoloji hissesi tutmak, "diversifiye" hissettirir ama hepsi aynı sektör
şokuna (örn. faiz artışı, regülasyon) aynı anda maruz kalır — bu sahte
diversifikasyondur.

### FinPilot'ta Diversifikasyon

FinPilot'un günlük taraması, birden fazla sektörden aday üretebilir; ama
hangi adayların portföyde birlikte tutulacağına, hangi ağırlıkla, hangi
toplam risk bütçesiyle — bu tamamen kullanıcının kararıdır. Tarama motoru
bir portföy inşa etmez, adayları listeler.""",
        "key_takeaways": [
            "Diversifikasyon, düşük korelasyonlu varlıklar bir araya geldiğinde toplam dalgalanmayı azaltır",
            "Şirkete-özgü riski azaltır; piyasa çapında (sistematik) riski ortadan kaldırmaz",
            "~20-30 hisseden sonra ek çeşitlendirmenin getirisi hızla azalır",
            "Aynı sektörden çok sayıda hisse tutmak 'sahte diversifikasyon' olabilir",
        ],
        "misconceptions": [
            "Yanlış: 'Ne kadar çok hisse o kadar güvenli' — 20-30'dan sonra ek fayda azalır, takip zorlaşır",
            "Yanlış: 'Diversifikasyon her türlü kayıptan korur' — Kriz anlarında korelasyonlar birbirine yaklaşır, koruma azalır",
        ],
        "real_example": {
            "ticker": "SPY",
            "context": "Mart 2020: S&P 500'ün 500 hissesi neredeyse aynı anda düştü — diversifikasyon dalgalanmayı azalttı ama düşüşü önlemedi",
        },
        "quizzes": [
            {
                "question": "Bir yatırımcı 15 farklı teknoloji hissesi tutuyor ve bunu 'iyi diversifiye' olarak görüyor. Bu doğru mu?",
                "options": [
                    "A) Evet, 15 farklı şirket yeterlidir",
                    "B) Hayır, hepsi aynı sektör şokuna maruz kalabileceğinden bu sahte diversifikasyon olabilir",
                    "C) Evet, çünkü 20'den az hisse tutmak zaten önerilir",
                    "D) Hayır, çünkü tek hisseye yoğunlaşmak her zaman daha güvenlidir",
                ],
                "correct": "B",
                "explanation": "Diversifikasyon sadece hisse sayısıyla değil, sektör/varlık sınıfı çeşitliliğiyle ölçülür. Aynı sektördeki hisseler genelde birlikte hareket eder.",
            }
        ],
        "flashcards": [
            {
                "front": "Diversifikasyon hangi riski azaltır?",
                "back": "Şirkete-özgü riski. Piyasa çapında sistematik riski tam olarak ortadan kaldırmaz.",
            },
            {
                "front": "Kaç hisseden sonra diversifikasyonun ek faydası azalır?",
                "back": "Akademik araştırmalara göre yaklaşık 20-30 hisseden sonra.",
            },
            {
                "front": "Sahte diversifikasyon nedir?",
                "back": "Çok sayıda hisse tutmak ama hepsinin aynı sektöre/riske maruz kalması — sayı çok ama gerçek çeşitlilik az.",
            },
        ],
    },
    # ──────────────────────────────────────────────────────────────────
    # 7. MAKROEKONOMİK ANALİZ
    # ──────────────────────────────────────────────────────────────────
    {
        "id": "MA-001-faiz-kararlari",
        "domain": "macro-analysis",
        "domain_id": 7,
        "module": "Faiz Kararları ve Piyasalar",
        "title": "Fed Faiz Kararları Neden Tüm Piyasayı Hareket Ettirir?",
        "difficulty": "beginner",
        "estimated_minutes": 10,
        "content": """## Faiz Oranı Neyi Değiştirir?

Merkez bankası (ABD'de Fed) politika faizini belirler. Bu tek sayı, ekonomideki
hemen her varlığın fiyatlamasını dolaylı olarak etkiler — çünkü faiz, "paranın
zaman içindeki maliyeti"dir.

### Yüksek Faiz Neden Hisseleri Baskılar?

İki ana kanal vardır:

1. **İskonto etkisi**: Bir hissenin "gerçek değeri", gelecekteki kârların
   bugünkü değere indirgenmesiyle hesaplanır (bkz. DCF). Faiz yükselince
   iskonto oranı yükselir, gelecekteki kârların bugünkü değeri düşer.
2. **Alternatif maliyet**: Faiz yüksekken risksiz tahvil/mevduat getirisi
   cazipleşir. Yatırımcılar riskli hisselerden risksiz araçlara kayabilir.

### Faiz Artışına En Duyarlı Şirketler

Büyüme şirketleri (kârın büyük kısmı uzak gelecekte bekleniyor) faiz
artışından, olgun/değer şirketlerine (kâr şimdiki zamanda) göre daha çok
etkilenir — çünkü uzak gelecekteki nakit akışları, iskonto oranı artışından
orantısız şekilde daha çok değer kaybeder.

### Fed Toplantıları Neden "Event" Sayılır?

Fed, yaklaşık her 6 haftada bir (FOMC toplantıları) faiz kararını açıklar.
Piyasa genellikle kararı önceden fiyatlar (beklenti); asıl hareket, kararın
kendisinden çok **beklenenle gerçekleşen arasındaki fark** ile **Fed
Başkanı'nın basın toplantısındaki dil tonundan (şahin/güvercin)** gelir.

### Enflasyon ile Faiz İlişkisi

Fed'in iki ana görevi (mandate): fiyat istikrarı (düşük enflasyon) ve tam
istihdam. Enflasyon hedefin üzerindeyken Fed genelde faizi yükseltir
(talebi soğutmak için); ekonomi zayıflarken faizi düşürür (büyümeyi
desteklemek için). Bu ikisi arasındaki denge, her FOMC toplantısının
merkezindedir.

### FinPilot'ta Makro Bağlam

FinPilot'un günlük tarama motoru şirket-seviyesi fiyat/hacim davranışına
odaklanır; makro takvimi (FOMC tarihleri, enflasyon verisi çıkış günleri)
doğrudan sinyal üretimine dahil etmez. Bu, kullanıcının kendi başına takip
etmesi gereken ayrı bir bağlam katmanıdır — özellikle FOMC günlerinde piyasa
çapında oynaklık normalden yüksek olabilir.""",
        "key_takeaways": [
            "Faiz artışı, gelecekteki kârların bugünkü değerini düşürür (iskonto etkisi)",
            "Yüksek faiz, risksiz alternatiflerin (tahvil/mevduat) cazibesini artırır",
            "Büyüme şirketleri faiz artışına, olgun/değer şirketlerinden daha duyarlıdır",
            "Piyasa tepkisi genelde kararın kendisinden çok 'beklenenle fark'tan gelir",
        ],
        "misconceptions": [
            "Yanlış: 'Faiz artışı her zaman hisseleri düşürür' — Beklenenden az bir artış bazen ralliye yol açar",
            "Yanlış: 'Fed kararı önceden tamamen bilinemez, o yüzden önemsizdir' — Piyasa genelde büyük ölçüde fiyatlar; sürpriz kısmı hareket yaratır",
        ],
        "real_example": {
            "ticker": "QQQ",
            "context": "2022 faiz artış döngüsünde büyüme ağırlıklı QQQ, değer ağırlıklı endekslere göre daha sert düştü",
        },
        "quizzes": [
            {
                "question": "Fed faizi beklenenden az artırdığında piyasalar genelde nasıl tepki verir?",
                "options": [
                    "A) Her zaman düşer, çünkü faiz arttı",
                    "B) Genelde yükselebilir, çünkü gerçekleşen beklenenden 'daha az sıkı' oldu",
                    "C) Hiçbir etkisi olmaz",
                    "D) Sadece tahvil piyasasını etkiler, hisseleri etkilemez",
                ],
                "correct": "B",
                "explanation": "Piyasa fiyatlaması büyük ölçüde beklentiye dayanır. Gerçekleşen karar beklenenden 'gevşekse', bu genelde olumlu karşılanır — kararın mutlak yönünden bağımsız olarak.",
            }
        ],
        "flashcards": [
            {
                "front": "Faiz artışı hisse değerlemesini hangi kanalla düşürür?",
                "back": "İskonto etkisi: gelecekteki kârların bugünkü değeri, yükselen iskonto oranıyla düşer.",
            },
            {
                "front": "Faiz artışına daha duyarlı olan şirket tipi hangisi?",
                "back": "Büyüme şirketleri — kârın büyük kısmı uzak gelecekte beklendiği için iskonto etkisinden orantısız etkilenirler.",
            },
            {
                "front": "FOMC nedir?",
                "back": "Federal Open Market Committee — Fed'in faiz kararını aldığı, yaklaşık 6 haftada bir toplanan komite.",
            },
        ],
    },
]


def seed_all(overwrite: bool = False) -> dict[str, int]:
    """Insert all seed lessons into DB. Returns {'inserted': N, 'skipped': N}."""
    init_db()
    lesson_repo = LessonRepository()
    comp_repo = LessonComponentRepository()
    now = datetime.utcnow().isoformat()
    review_at = (datetime.utcnow() + timedelta(days=90)).isoformat()

    inserted = 0
    skipped = 0

    for data in SEED_LESSONS:
        existing = lesson_repo.get(data["id"])
        if existing and not overwrite:
            skipped += 1
            continue

        lesson = Lesson(
            id=data["id"],
            domain=data["domain"],
            domain_id=data["domain_id"],
            module=data["module"],
            title=data["title"],
            difficulty=data["difficulty"],
            estimated_minutes=data.get("estimated_minutes", 10),
            content=data["content"],
            key_takeaways=data.get("key_takeaways", []),
            misconceptions=data.get("misconceptions", []),
            real_example=data.get("real_example", {}),
            related_lessons=data.get("related_lessons", []),
            pedagogy_score=8.0,
            status="draft",
            created_at=now,
            updated_at=now,
            next_review_at=review_at,
        )
        lesson_repo.save(lesson)

        order = 0
        for quiz in data.get("quizzes", []):
            comp_repo.save(
                LessonComponent(lesson_id=lesson.id, type="quiz", content=quiz, order_idx=order)
            )
            order += 1

        for card in data.get("flashcards", []):
            comp_repo.save(
                LessonComponent(
                    lesson_id=lesson.id, type="flashcard", content=card, order_idx=order
                )
            )
            order += 1

        inserted += 1
        print(f"  ✅ {lesson.id}: {lesson.title}")

    return {"inserted": inserted, "skipped": skipped}


if __name__ == "__main__":
    print("\n🌱 Finance Academy — Başlangıç İçeriği Yükleniyor...\n")
    result = seed_all()
    print(
        f"\n✨ Tamamlandı: {result['inserted']} ders yüklendi, {result['skipped']} zaten vardı.\n"
    )
