"""
Finance Academy — Domain & Module Definitions
=============================================
12 domain, her birinin modülleri ve öncelik sırası.
"""

from __future__ import annotations

DOMAINS: list[dict] = [
    {
        "id": 1,
        "slug": "fundamental-finance",
        "name": "Temel Finans",
        "name_en": "Fundamental Finance",
        "emoji": "💵",
        "priority": 1,
        "description": "Para, enflasyon, faiz oranları, bütçe ve temel ekonomik kavramlar.",
        "modules": [
            "Para ve Değeri",
            "Enflasyon ve Satın Alma Gücü",
            "Faiz Oranları",
            "Bütçe ve Tasarruf",
            "Yatırımın Temelleri",
        ],
    },
    {
        "id": 2,
        "slug": "stocks-market",
        "name": "Borsa ve Hisse Senetleri",
        "name_en": "Stocks & Markets",
        "emoji": "📈",
        "priority": 1,
        "description": "Borsa nasıl çalışır, hisse senedi nedir, piyasa katılımcıları kimlerdir.",
        "modules": [
            "Borsa Nasıl Çalışır",
            "Hisse Senedi Türleri",
            "Endeksler ve Piyasa Göstergeleri",
            "IPO ve Halka Arz",
            "Piyasa Döngüleri",
        ],
    },
    {
        "id": 3,
        "slug": "technical-analysis",
        "name": "Teknik Analiz",
        "name_en": "Technical Analysis",
        "emoji": "📊",
        "priority": 1,
        "description": "Grafik okuma, indikatörler ve fiyat hareketi yorumlama.",
        "modules": [
            "Grafik Tipleri",
            "Destek ve Direnç",
            "Trend Analizi",
            "Hacim Analizi",
            "Osilatörler (RSI, MACD, Stochastic)",
            "Hareketli Ortalamalar",
            "Formasyonlar",
            "Fibonacci ve Elliott Dalgaları",
            "İleri Teknik Analiz",
        ],
    },
    {
        "id": 4,
        "slug": "fundamental-analysis",
        "name": "Temel Analiz",
        "name_en": "Fundamental Analysis",
        "emoji": "🔍",
        "priority": 2,
        "description": "Bilanço okuma, gelir tablosu, değerleme yöntemleri.",
        "modules": [
            "Finansal Tablolar 101",
            "Bilanço Analizi",
            "Gelir Tablosu",
            "Nakit Akışı Tablosu",
            "Değerleme Yöntemleri (P/E, DCF)",
            "Sektör Analizi",
        ],
    },
    {
        "id": 5,
        "slug": "portfolio-management",
        "name": "Portföy Yönetimi",
        "name_en": "Portfolio Management",
        "emoji": "🗂️",
        "priority": 2,
        "description": "Diversifikasyon, risk/getiri dengesi ve portföy oluşturma.",
        "modules": [
            "Diversifikasyon Nedir",
            "Modern Portföy Teorisi",
            "Varlık Dağılımı",
            "Yeniden Dengeleme",
            "Performans Ölçümü",
        ],
    },
    {
        "id": 6,
        "slug": "risk-management",
        "name": "Risk Yönetimi",
        "name_en": "Risk Management",
        "emoji": "🛡️",
        "priority": 1,
        "description": "Stop-loss, pozisyon boyutu, drawdown analizi ve sermaye koruma.",
        "modules": [
            "Risk Nedir",
            "Stop-Loss Stratejileri",
            "Pozisyon Boyutlandırma",
            "Risk/Ödül Oranı",
            "Drawdown ve Çekilme Analizi",
            "Kelly Kriteri",
        ],
    },
    {
        "id": 7,
        "slug": "macro-analysis",
        "name": "Makroekonomik Analiz",
        "name_en": "Macro Analysis",
        "emoji": "🌍",
        "priority": 2,
        "description": "Fed kararları, enflasyon, faiz politikası ve ekonomik döngüler.",
        "modules": [
            "Merkez Bankası ve Fed",
            "Enflasyon Türleri",
            "Faiz Kararları ve Piyasalar",
            "Ekonomik Göstergeler",
            "Para Politikası vs Maliye Politikası",
        ],
    },
    {
        "id": 8,
        "slug": "options-derivatives",
        "name": "Opsiyon ve Türevler",
        "name_en": "Options & Derivatives",
        "emoji": "⚙️",
        "priority": 3,
        "description": "Call/put opsiyonları, Yunanlılar (Greeks), hedge stratejileri.",
        "modules": [
            "Opsiyon Nedir",
            "Call ve Put",
            "The Greeks (Delta, Gamma, Theta, Vega)",
            "Temel Opsiyon Stratejileri",
            "Vadeli İşlemler",
            "Hedge Stratejileri",
        ],
    },
    {
        "id": 9,
        "slug": "behavioral-finance",
        "name": "Psikoloji ve Davranışsal Finans",
        "name_en": "Behavioral Finance",
        "emoji": "🧠",
        "priority": 2,
        "description": "Bilişsel önyargılar, duygusal kararlar ve trader psikolojisi.",
        "modules": [
            "Davranışsal Finans Nedir",
            "Kayıptan Kaçınma (Loss Aversion)",
            "Doğrulama Önyargısı (Confirmation Bias)",
            "Sürü Psikolojisi",
            "Trader Disiplini",
            "Duygusal Kontrol",
        ],
    },
    {
        "id": 10,
        "slug": "algo-trading-ai",
        "name": "Algoritmik Trading ve AI",
        "name_en": "Algo Trading & AI",
        "emoji": "🤖",
        "priority": 3,
        "description": "Backtest, DRL, strateji geliştirme ve AI destekli analiz.",
        "modules": [
            "Algoritmik Trading Nedir",
            "Backtest Temelleri",
            "Strateji Geliştirme Süreci",
            "Derin Pekiştirmeli Öğrenme (DRL)",
            "Walk-Forward Analizi",
            "Monte Carlo Simülasyonu",
        ],
    },
    {
        "id": 11,
        "slug": "etf-passive",
        "name": "ETF ve Pasif Yatırım",
        "name_en": "ETFs & Passive Investing",
        "emoji": "📦",
        "priority": 2,
        "description": "Index fonlar, sektör ETF'leri ve pasif yatırım stratejileri.",
        "modules": [
            "ETF Nedir",
            "Index Yatırımı",
            "Sektör ve Tema ETF'leri",
            "ETF vs Hisse Senedi",
            "Pasif vs Aktif Yatırım",
        ],
    },
    {
        "id": 12,
        "slug": "crypto-alternatives",
        "name": "Kripto ve Alternatif Varlıklar",
        "name_en": "Crypto & Alternatives",
        "emoji": "₿",
        "priority": 3,
        "description": "Bitcoin, blockchain, DeFi temelleri ve alternatif varlık sınıfları.",
        "modules": [
            "Blockchain ve Kripto Temelleri",
            "Bitcoin ve Ethereum",
            "DeFi (Merkeziyetsiz Finans)",
            "Kripto Risk Yönetimi",
            "Alternatif Varlık Sınıfları",
        ],
    },
]

DOMAIN_BY_SLUG: dict[str, dict] = {d["slug"]: d for d in DOMAINS}
DOMAIN_BY_ID: dict[int, dict] = {d["id"]: d for d in DOMAINS}


def get_domain(slug: str) -> dict | None:
    return DOMAIN_BY_SLUG.get(slug)


def priority_domains() -> list[dict]:
    """Return domains sorted by priority (1 = highest)."""
    return sorted(DOMAINS, key=lambda d: d["priority"])
