"""Build the ten original FinPilot educational manuscripts.

The generated manuscripts are drafts. They are intentionally based on original
explanations, fictional examples, and review questions rather than copied
source-book text.
"""

from __future__ import annotations

from pathlib import Path

OUTPUT_DIR = Path("reports/content_series")

OPENERS = (
    "The first step in learning a concept is separating it from an impressive result.",
    "Market language can create too much certainty in a single word; this page opens that word up.",
    "We treat this subject as a testable research question rather than as a chart signal.",
    "Fictional examples are used to make assumptions visible, not to imply a real-world outcome.",
    "A useful financial explanation carries a definition, a boundary, and a control question.",
)

APPLICATIONS = (
    "Define the concept in one sentence. Rewrite it after adding a data source, "
    "a timestamp, and a comparison measure.",
    "Create three worksheet rows where the concept appears strong, weak, and "
    "uncertain. Compare the rows by information quality, not by outcome.",
    "Choose a fictional company or market day. Put the observation time, prior "
    "information, and later-known information in separate columns.",
    "Write the sentence a reader might use to misinterpret the concept. Rewrite "
    "it to state the evidence and the missing information more carefully.",
    "Design a condition where the concept is not useful. A good teaching example "
    "shows the boundary as well as the apparent success.",
)

QUESTIONS = (
    "Which data and comparison measure would you require before using this concept?",
    "What is the simplest fictional example that could falsify this explanation?",
    "Why might the same observation be interpreted differently in another market regime?",
    "Which sentence on this page is too certain, and how would you soften it?",
    "Which two concepts might a reader confuse here?",
)

ENGLISH_METADATA = {
    "01-finansal-okuryazarlik-atlasi": (
        "Financial Literacy Learning Atlas",
        "Beginning market students",
        "Learn market language before interpreting charts, scores, or headlines.",
    ),
    "02-piyasa-mekanigi": (
        "Market Mechanics: How Prices Move",
        "Readers learning orders, liquidity, and market structure",
        "Read price movement through orders, liquidity, volume, and volatility.",
    ),
    "03-durust-backtest": (
        "The Honest Backtest Workbook",
        "Analysts, developers, and quantitative researchers",
        "Audit what a backtest actually measures before optimizing it.",
    ),
    "04-strateji-efsaneleri-ve-kanit": (
        "Strategy Myths and Evidence",
        "Readers evaluating online trading claims",
        "Separate a persuasive market story from testable evidence.",
    ),
    "05-skor-olasilik-kalibrasyon": (
        "Score, Probability, and Calibration Lab",
        "Users of scanners, rankings, models, and AI outputs",
        "Test what a score describes and when a probability is meaningful.",
    ),
    "06-risk-drawdown-boyutlandirma": (
        "Risk, Drawdown, and Position Sizing",
        "Readers who want to understand exposure beyond an entry idea",
        "Understand loss size, volatility, correlation, and recovery mathematics.",
    ),
    "07-execution-gercegi": (
        "Execution Reality: From Spread to Slippage",
        "Readers examining the gap between backtests and live prices",
        "Turn a theoretical signal into an explicit, measurable fill assumption.",
    ),
    "08-disiplinli-yatirimci": (
        "The Disciplined Investor: Behaviour and Decision Design",
        "Self-directed learners building process consistency",
        "Build a decision and review system that makes impulsive errors visible.",
    ),
    "09-veri-okuryazarligi": (
        "Data Literacy and Source Quality",
        "Analysts, developers, and advanced students working with market data",
        "Assess whether data is timely, complete, comparable, and fit for a claim.",
    ),
    "10-ai-drl-arastirma-rehberi": (
        "AI and DRL in Markets: A Realistic Research Guide",
        "Technical readers and developers",
        "Understand the research value and limits of PPO, DQN, SAC, adaptive alpha, and explainability.",
    ),
}


PRODUCTS = [
    {
        "slug": "01-finansal-okuryazarlik-atlasi",
        "title": "Finansal Okuryazarlık Öğrenme Atlası",
        "audience": "Başlangıç seviyesindeki yatırım piyasası öğrencileri",
        "promise": "Piyasa dilini grafik, skor veya başlık yorumlamadan önce öğrenmek.",
        "sections": [
            (
                "Piyasanın Temel Dili",
                [
                    "Para, sahiplik ve fiyat",
                    "Getiri ile risk",
                    "Varlık sınıfları",
                    "Zaman ufku",
                    "Tanılayıcı mini sınav",
                ],
            ),
            (
                "Fiyat ve İşlem Akışı",
                [
                    "Fiyatın neyi söylediği",
                    "Hacim ve katılım",
                    "Likidite ve spread",
                    "Float ve piyasa değeri",
                    "Bir işlem gününün haritası",
                ],
            ),
            (
                "Olasılık ve Kanıt",
                ["Olasılık sözcükleri", "Baz oran", "Kalibrasyon", "Lift", "Belirsizlik günlüğü"],
            ),
            ("Grafik Kavramları", ["Momentum", "Gap", "Kırılım", "Yalancı kırılım", "Rejim"]),
            (
                "Olay ve Şirket Riski",
                [
                    "Katalizör",
                    "Bilanço sonrası sürüklenme",
                    "Hisse ihracı",
                    "İşlem durdurma",
                    "Haber ile sonuç arasındaki fark",
                ],
            ),
            (
                "Volatilite ve Sermaye",
                [
                    "ATR",
                    "Risk/ödül",
                    "Drawdown",
                    "Pozisyon boyutlandırma",
                    "Kayıptan toparlanma matematiği",
                ],
            ),
            (
                "Davranış ve Süreç",
                ["FOMO", "Aşırı işlem", "Dikkat bütçesi", "Karar günlüğü", "Süreç sonucu ayırmak"],
            ),
            (
                "Uygulama Atlası",
                ["Fiyat kartı", "Risk kartı", "Kanıt kartı", "Kurgusal vaka 1", "Kurgusal vaka 2"],
            ),
        ],
    },
    {
        "slug": "02-piyasa-mekanigi",
        "title": "Piyasa Mekaniği: Fiyat Nasıl Hareket Eder?",
        "audience": "Grafik okuyan fakat emir ve likidite yapısını yeni öğrenenler",
        "promise": "Fiyat hareketini emir, likidite, hacim ve volatilite ilişkisiyle okumak.",
        "sections": [
            (
                "Bir Günün Anatomisi",
                ["Açılış öncesi", "İlk fiyat", "Teklif ve talep", "Kapanış", "Gün sonu incelemesi"],
            ),
            (
                "Emir Defteri",
                ["Bid ve ask", "Spread", "Piyasa emri", "Limit emri", "Kuyruk önceliği"],
            ),
            (
                "Likidite ve Etki",
                [
                    "Likidite nedir",
                    "Float",
                    "Piyasa etkisi",
                    "Hacim kapasitesi",
                    "İnce piyasa vakası",
                ],
            ),
            (
                "Hacim ve Katılım",
                ["Hacim", "RVOL", "Hacim sıçraması", "Gürültü ve katılım", "Hacim kontrol listesi"],
            ),
            (
                "Gap ve Halt",
                [
                    "Gap anatomisi",
                    "Haber boşluğu",
                    "İşlem durdurma",
                    "Yeniden açılış",
                    "Eksik fiyat riski",
                ],
            ),
            (
                "Aralık ve Volatilite",
                [
                    "ATR",
                    "Range contraction",
                    "Genişleme",
                    "Volatilite rejimi",
                    "Kurgusal volatilite laboratuvarı",
                ],
            ),
            (
                "Sıkışma ve Seyreltme",
                [
                    "Short interest",
                    "Squeeze mekanizması",
                    "Katalizör",
                    "Offering ve dilution",
                    "Rakip açıklamalar",
                ],
            ),
            (
                "Mekanik Laboratuvarı",
                [
                    "Emir dizisi çizmek",
                    "Dört kurgusal emir defteri",
                    "Fiyat yolu",
                    "Mekanik hata günlüğü",
                    "Özet test",
                ],
            ),
        ],
    },
    {
        "slug": "03-durust-backtest",
        "title": "Dürüst Backtest Çalışma Kitabı",
        "audience": "Analistler, geliştiriciler ve nicel araştırma yapanlar",
        "promise": "Bir backtest'i optimize etmeden önce gerçekten neyi ölçtüğünü denetlemek.",
        "sections": [
            (
                "Araştırma İddiası",
                ["Soru yazmak", "Popülasyon", "Horizon", "Sonuç etiketi", "İddia kartı"],
            ),
            (
                "Etiket Semantiği",
                ["MFE", "MAE", "Close-to-close", "Barrier sonucu", "Etiket sözleşmesi"],
            ),
            (
                "Veri Soyu",
                ["Feature lineage", "Leakage", "Restatement", "Survivorship", "Timestamp denetimi"],
            ),
            (
                "Etkin Örneklem",
                [
                    "Satır sayısı",
                    "Gün kümeleri",
                    "Sembol tekrarları",
                    "Block bootstrap",
                    "Belirsizlik raporu",
                ],
            ),
            (
                "Null ve Karşılaştırma",
                ["Baz oran", "Benchmark", "Null preflight", "Counterfactual", "Finding verdict"],
            ),
            (
                "Çoklu Deney",
                [
                    "Deney bütçesi",
                    "Preregistration",
                    "Araştırmacı serbestlik derecesi",
                    "FDR fikri",
                    "Registry sayfası",
                ],
            ),
            ("Execution Katmanı", ["Spread", "Drift", "Half-life", "Replay", "Maliyet sözleşmesi"]),
            (
                "Dört Kapı Uygulaması",
                [
                    "Veri kapısı",
                    "Ölçüm kapısı",
                    "Execution kapısı",
                    "Sinyal kapısı",
                    "Tam audit vakası",
                ],
            ),
        ],
    },
    {
        "slug": "04-strateji-efsaneleri-ve-kanit",
        "title": "Strateji Efsaneleri ve Kanıt",
        "audience": "Çevrim içi trading iddialarını değerlendiren okuyucular",
        "promise": "İkna edici bir piyasa hikâyesi ile sınanabilir kanıtı ayırmak.",
        "sections": [
            (
                "Kanıtın Anatomisi",
                ["İddia ve mekanizma", "Benchmark", "Tekrar", "Belirsizlik", "Kanıt seviyesi"],
            ),
            (
                "Momentum ve Trend",
                [
                    "Orta vadeli momentum",
                    "Time-series momentum",
                    "Trend kırılması",
                    "Rejim etkisi",
                    "Test kartı",
                ],
            ),
            (
                "Faktör Aileleri",
                ["Value", "Size", "Profitability", "Investment", "Uygulama farkları"],
            ),
            (
                "İndikatör İddiaları",
                ["RSI", "MACD", "Pattern isimleri", "Fibonacci", "Data-snooping kontrolü"],
            ),
            (
                "Breakout ve Reversal",
                [
                    "Kırılım iddiası",
                    "Reversal iddiası",
                    "Yalancı kırılım",
                    "Seçim yanlılığı",
                    "Maliyet sonrası test",
                ],
            ),
            (
                "Olay Stratejileri",
                ["Bilanço", "Catalyst", "Earnings drift", "Squeeze", "Event selection"],
            ),
            (
                "Dayanıklılık Soruları",
                ["Crowding", "Regime değişimi", "Gecikme", "Out-of-sample", "Replication"],
            ),
            (
                "30 İddia Kartı",
                [
                    "İddia kartı formatı",
                    "Kurgusal iddia 1",
                    "Kurgusal iddia 2",
                    "Değerlendirme rubriği",
                    "Cevap anahtarı",
                ],
            ),
        ],
    },
    {
        "slug": "05-skor-olasilik-kalibrasyon",
        "title": "Skor, Olasılık ve Kalibrasyon Laboratuvarı",
        "audience": "Scanner, ranking, model ve AI çıktısı kullananlar",
        "promise": "Skorun neyi tarif ettiğini ve olasılığın ne zaman anlamlı olduğunu test etmek.",
        "sections": [
            ("Beş Kavram", ["Skor", "Rank", "Grade", "Olasılık", "Forecast ayrımı"]),
            (
                "Composite Score",
                ["Boyutlar", "Ağırlıklar", "Eksik feature", "Yorumlanabilirlik", "Toy score"],
            ),
            (
                "Ayna Testi",
                [
                    "Geçmiş korelasyonu",
                    "İleri korelasyon",
                    "Mirror örneği",
                    "Tersine çevirme sınırı",
                    "Raporlama",
                ],
            ),
            (
                "Kalibrasyon",
                [
                    "Probability bucket",
                    "Reliability diagram",
                    "Brier score",
                    "Base-rate skill",
                    "Kurgusal tablo",
                ],
            ),
            (
                "Ranking Denetimi",
                ["Decile", "Tie", "Monotonicity", "Adverse selection", "Counterfactual ranking"],
            ),
            (
                "Benchmark",
                ["Random", "Market", "Sector", "Simple baseline", "Karşılaştırma tablosu"],
            ),
            (
                "Drift ve Recalibration",
                ["Rejim drift", "Feature crowding", "Score decay", "Recalibration", "İzleme planı"],
            ),
            (
                "Score Audit",
                ["Audit worksheet", "Toy dataset", "Verdict", "Limitations", "Yayın şablonu"],
            ),
        ],
    },
    {
        "slug": "06-risk-drawdown-boyutlandirma",
        "title": "Risk, Drawdown ve Pozisyon Boyutlandırma",
        "audience": "Giriş fikrine fazla odaklanıp maruziyeti az düşünenler",
        "promise": "Kayıp büyüklüğü, volatilite, korelasyon ve toparlanma matematiğini anlamak.",
        "sections": [
            (
                "Riskin Anatomisi",
                ["Kayıp", "Belirsizlik", "Exposure", "Risk bütçesi", "Risk sözlüğü"],
            ),
            (
                "Drawdown Matematiği",
                [
                    "Tepe ve dip",
                    "%10 kayıp",
                    "%50 kayıp",
                    "Toparlanma asimetrisi",
                    "Senaryo tablosu",
                ],
            ),
            (
                "Volatilite",
                [
                    "ATR",
                    "Volatility scaling",
                    "Büyük hareket",
                    "Volatilite riski",
                    "Kurgusal hesap",
                ],
            ),
            (
                "Boyutlandırma",
                [
                    "Sabit boyut",
                    "Risk bütçeli boyut",
                    "Farklı bütçeler",
                    "Varsayım kontrolü",
                    "Boyutlandırma formu",
                ],
            ),
            (
                "Yoğunlaşma",
                [
                    "Korelasyon",
                    "Sektör maruziyeti",
                    "Gizli ortak risk",
                    "Çeşitlendirme sınırı",
                    "Portföy haritası",
                ],
            ),
            (
                "Kayıp Sınırları",
                ["Stop sınırı", "Gap", "Halt", "Fill belirsizliği", "Sınırların sınırı"],
            ),
            (
                "Seriler ve Psikoloji",
                [
                    "Kayıp serisi",
                    "Risk toleransı",
                    "Senaryo",
                    "Karar yorgunluğu",
                    "İnceleme takvimi",
                ],
            ),
            (
                "Kişisel Çalışma Kitabı",
                ["Risk profili", "Journal", "Review rubric", "Kurgusal portföy", "Kapanış testi"],
            ),
        ],
    },
    {
        "slug": "07-execution-gercegi",
        "title": "Execution Gerçeği: Spread'den Slippage'a",
        "audience": "Backtest sonucu ile gerçek piyasa fiyatı arasındaki farkı inceleyenler",
        "promise": "Teorik sinyali ölçülebilir ve açık bir fill varsayımına çevirmek.",
        "sections": [
            (
                "Sinyal ve Fill",
                ["Chart event", "Fill fiyatı", "Gecikme", "Entry drift", "Signal contract"],
            ),
            (
                "Spread ve Ücret",
                ["Bid-ask", "Midpoint", "Emir türleri", "Komisyon", "Round-trip maliyet"],
            ),
            (
                "Slippage",
                ["Slippage tanımı", "Latency", "Adverse selection", "Gap risk", "Drift ölçümü"],
            ),
            (
                "Impact ve Capacity",
                ["ADV", "Participation", "Impact", "Capacity", "Kurgusal hacim"],
            ),
            (
                "Intraday Yol",
                ["OHLC sınırı", "Fill ordering", "Path dependence", "Look-ahead", "Replay dizisi"],
            ),
            ("Half-life", ["Sinyal ömrü", "Decay", "Delayed decision", "Ölçüm", "Kurgusal seri"]),
            (
                "Execution Replay",
                ["Tick dizisi", "Bar dizisi", "Üç fill varsayımı", "Duyarlılık", "Replay kaydı"],
            ),
            (
                "Cost Audit",
                [
                    "Cost model",
                    "Sensitivity",
                    "Worst case",
                    "Evidence status",
                    "Execution checklist",
                ],
            ),
        ],
    },
    {
        "slug": "08-disiplinli-yatirimci",
        "title": "Disiplinli Yatırımcı: Davranış ve Karar Tasarımı",
        "audience": "Süreç tutarlılığı geliştirmek isteyen kendi kendine öğrenenler",
        "promise": "Dürtüsel hataları görünür kılan bir karar ve inceleme sistemi kurmak.",
        "sections": [
            (
                "Duygu ve Dikkat",
                ["FOMO", "Regret", "Loss aversion", "Attention", "Canlı piyasa baskısı"],
            ),
            (
                "Aktivite Tuzakları",
                [
                    "Overtrading",
                    "Novelty seeking",
                    "Revenge decision",
                    "Activity bias",
                    "Maliyet günlüğü",
                ],
            ),
            (
                "Ön Taahhüt",
                [
                    "Soru yazmak",
                    "Kanıt kriteri",
                    "Disconfirming evidence",
                    "Bekleme kuralı",
                    "Ön taahhüt formu",
                ],
            ),
            (
                "Kontrol Listeleri",
                ["Before review", "During review", "After review", "Cooling-off", "Decision log"],
            ),
            (
                "Süreç ve Sonuç",
                [
                    "İyi süreç",
                    "Şanslı sonuç",
                    "Kötü süreç",
                    "Sonuç yanlılığı",
                    "Vaka karşılaştırması",
                ],
            ),
            (
                "Hata Taksonomisi",
                ["Etiket hatası", "Ölçüm hatası", "Dikkat hatası", "İcra hatası", "Hata kodları"],
            ),
            (
                "Medya ve Uyarılar",
                ["Haber akışı", "Sosyal kanıt", "Bildirimler", "Attention budget", "Dijital düzen"],
            ),
            ("30 Günlük Journal", ["Gün 1", "Hafta 1", "Hafta 2", "Hafta 3", "Final review"]),
        ],
    },
    {
        "slug": "09-veri-okuryazarligi",
        "title": "Veri Okuryazarlığı ve Kaynak Kalitesi",
        "audience": "Piyasa verisiyle çalışan analistler, geliştiriciler ve ileri öğrenciler",
        "promise": "Bir verinin zamanında, eksiksiz, karşılaştırılabilir ve iddiaya uygun olup olmadığını değerlendirmek.",
        "sections": [
            (
                "Veri ve Kanıt",
                ["Alan anlamı", "Timestamp", "Observation", "Claim fit", "Veri sözleşmesi"],
            ),
            ("Veri Aileleri", ["OHLCV", "Fundamentals", "Filings", "Options", "Sentiment"]),
            (
                "Zaman ve Revizyon",
                ["Frequency", "Latency", "Revision", "Restatement", "Point-in-time"],
            ),
            (
                "Eksik ve Bozuk Veri",
                ["Missingness", "Duplicate", "Survivorship", "Corporate action", "Symbol change"],
            ),
            (
                "Feature Lineage",
                ["Origin", "Transform", "Timestamp lineage", "Owner", "Lineage card"],
            ),
            (
                "Kaynak Karşılaştırması",
                ["Coverage", "Cost", "Reliability", "Dependency", "Vendor matrix"],
            ),
            (
                "Kalite Deneyleri",
                [
                    "Kurgusal bozuk set",
                    "Missingness testi",
                    "Duplicate testi",
                    "Revision testi",
                    "Quality verdict",
                ],
            ),
            (
                "Source Register",
                [
                    "Kaynak formu",
                    "Quality scorecard",
                    "Pre-analysis contract",
                    "Review date",
                    "Kapanış testi",
                ],
            ),
        ],
    },
    {
        "slug": "10-ai-drl-arastirma-rehberi",
        "title": "Piyasalarda AI ve DRL: Gerçekçi Araştırma Rehberi",
        "audience": "Teknik meraklı okuyucular ve geliştiriciler",
        "promise": "PPO, DQN, SAC, adaptive alpha ve explainability yaklaşımlarının araştırmaya katkısını ve sınırlarını görmek.",
        "sections": [
            (
                "Piyasalar Neden Zor",
                ["Non-stationarity", "Noise", "Feedback", "Costs", "Environment contract"],
            ),
            (
                "Öğrenme Yaklaşımları",
                ["Supervised", "Reinforcement", "Decision support", "Baseline", "Model choice"],
            ),
            ("PPO, DQN, SAC", ["Policy", "Value", "PPO", "DQN", "SAC"]),
            ("Environment Design", ["State", "Action", "Reward", "Transaction cost", "Episode"]),
            ("Doğrulama", ["Walk-forward", "Leakage", "Regime drift", "Out-of-sample", "Replay"]),
            (
                "Paper Telemetry",
                ["Event log", "Monitoring", "Failure containment", "Shadow run", "Review"],
            ),
            (
                "Explainability",
                [
                    "Feature attribution",
                    "Counterfactual",
                    "Uncertainty",
                    "Human review",
                    "Explanation limits",
                ],
            ),
            (
                "Toy Agent Lab",
                [
                    "Kurgusal ajan",
                    "Basit baseline",
                    "Failure test",
                    "Research checklist",
                    "Model is not edge",
                ],
            ),
        ],
    },
]


def page_body(product: dict[str, object], section: str, topic: str, page: int) -> str:
    title = str(product["title"])
    audience = str(product["audience"])
    variant = (page - 1) % len(OPENERS)
    opener = OPENERS[variant]
    application = APPLICATIONS[variant]
    question = QUESTIONS[variant]
    observed = 42 + page * 3
    comparison = observed - (page % 4) * 5
    sample_size = 18 + page
    return f"""## Page {page} — Concept {page}

{opener} This page connects the selected concept to the broader learning
question in {title}. The purpose is not to direct one outcome, but to help the
reader distinguish when a concept can be used and when caution is required.
Examples are fictional and do not represent a real asset, person, or outcome.

### Core idea

The selected concept is an observation tool in this module. An observation tool
is not, by itself, a cause, proof, or assurance. The reader should define it in
their own words, then identify what data could support or challenge it. This is
important for {audience.lower()} because a simple term can change meaning across
time horizons and market conditions.

### Worked fictional case

In a fictional review, the concept was observed in **{observed}** records while
the comparison group contained **{comparison}** records. The researcher had
**{sample_size}** independent day clusters, but the raw row count was larger
because several observations came from the same day. More rows do not
automatically mean more independent evidence.

| Check | Fictional observation | Required interpretation |
| --- | ---: | --- |
| Observed records | {observed} | A description, not a result claim |
| Comparison records | {comparison} | A reference group to inspect |
| Independent day clusters | {sample_size} | A more useful uncertainty check |
| Missing assumption | Timing and selection | A limitation to resolve |

### Failure mode

The common error is to treat the first visible relationship as a stable rule.
That shortcut hides selection, timing, costs, and the possibility that the
comparison group was chosen after seeing the result. A stronger review records
what was known at decision time and what was learned only afterward.

### Practice application

{application} For each row, record the time, data source, expected comparison,
and limitation. Explain why the three rows should not be turned into one success
story.

### Control question

{question} Which sentence would you refuse to make before completing the missing measurement?

### Page note

This content is educational material and is not investment advice. Source ideas
are processed through original explanations; no source text, figure, or table
is reproduced directly.
"""


def build_product(product: dict[str, object]) -> str:
    title, audience, promise = ENGLISH_METADATA[str(product["slug"])]
    lines = [
        f"# {title}",
        "",
        "Version: 0.1 draft · 2026-08-10",
        "Status: Original educational manuscript · pending editorial and rights review",
        "",
        f"**Audience:** {audience}",
        f"**Learning promise:** {promise}",
        "",
        "> This workbook is educational material, not investment advice. It does",
        "> not promise returns, a validated edge, or a live signal. All examples",
        "> are fictional unless explicitly labelled as a FinPilot research case.",
        "",
        "## How to use this workbook",
        "",
        "Read one page, answer its control question, and record the assumption you",
        "would need to verify. A completed page is not proof of a market result; it",
        "is evidence that the reader can state the concept and its limitation.",
        "",
    ]
    page = 1
    for module_number, (section, topics) in enumerate(product["sections"], start=1):  # type: ignore[index]
        lines.extend([f"# Module {module_number}", ""])
        for topic in topics:
            lines.append(
                page_body(
                    {**product, "title": title, "audience": audience},
                    str(module_number),
                    topic,
                    page,
                )
            )
            page += 1
    lines.extend(
        [
            "## Sources and rights",
            "",
            "This draft uses original educational explanations and FinPilot-owned",
            "working material. External sources will not be cited until title, author,",
            "URL, licence, edition, and permission are verified in the source register.",
            "",
            "## Pre-publication checklist",
            "",
            "- [ ] Forty content pages are present.",
            "- [ ] Every page has an original explanation, application, and control question.",
            "- [ ] Rights status and source records have been reviewed.",
            "- [ ] Advice, guarantees, and unsupported edge language have been removed.",
            "- [ ] English terminology has been reviewed for consistency.",
            "- [ ] Human editorial and publishing approval has been obtained.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for product in PRODUCTS:
        path = OUTPUT_DIR / f"{product['slug']}.md"
        path.write_text(build_product(product), encoding="utf-8")
        print(f"built {path}")


if __name__ == "__main__":
    main()
