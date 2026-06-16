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
            status="published",
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
