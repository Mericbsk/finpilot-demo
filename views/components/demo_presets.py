"""
FinPilot Demo Stock Presets - Expanded Edition
===============================================

100+ unique stocks organized into thematic categories for the demo page.
Supports multi-language (EN/DE/TR).

Usage:
    from views.components.demo_presets import DEMO_CATEGORIES, get_demo_stocks
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DemoCategory:
    """Demo category with multi-language support."""

    key: str
    icon: str
    names: dict[str, str]  # {lang: name}
    descriptions: dict[str, str]  # {lang: description}
    symbols: list[str]


# ============================================
# 📊 DEMO CATEGORIES - 100+ Unique Stocks
# ============================================

DEMO_CATEGORIES: dict[str, DemoCategory] = {
    # ----------------------------------------
    # 🖥️ TECHNOLOGY
    # ----------------------------------------
    "magnificent_7": DemoCategory(
        key="magnificent_7",
        icon="👑",
        names={"en": "Magnificent 7", "de": "Glorreiche 7", "tr": "Muhteşem 7"},
        descriptions={
            "en": "The top 7 tech giants driving the market",
            "de": "Die 7 größten Tech-Giganten",
            "tr": "Piyasayı yönlendiren 7 teknoloji devi",
        },
        symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    ),
    "ai_revolution": DemoCategory(
        key="ai_revolution",
        icon="🤖",
        names={"en": "AI Revolution", "de": "KI-Revolution", "tr": "Yapay Zeka Devrimi"},
        descriptions={
            "en": "Companies leading the artificial intelligence wave",
            "de": "Unternehmen an der Spitze der KI-Welle",
            "tr": "Yapay zeka dalgasına öncülük eden şirketler",
        },
        symbols=["NVDA", "AMD", "PLTR", "AI", "PATH", "SNOW", "MDB", "DDOG", "CRWD", "PANW"],
    ),
    "semiconductors": DemoCategory(
        key="semiconductors",
        icon="💾",
        names={
            "en": "Semiconductor Stars",
            "de": "Halbleiter-Stars",
            "tr": "Yarı İletken Yıldızları",
        },
        descriptions={
            "en": "Chip makers powering the digital world",
            "de": "Chiphersteller der digitalen Welt",
            "tr": "Dijital dünyaya güç veren çip üreticileri",
        },
        symbols=[
            "NVDA",
            "AMD",
            "INTC",
            "AVGO",
            "QCOM",
            "TXN",
            "MU",
            "AMAT",
            "LRCX",
            "KLAC",
            "ARM",
            "MRVL",
        ],
    ),
    "cloud_computing": DemoCategory(
        key="cloud_computing",
        icon="☁️",
        names={"en": "Cloud Computing", "de": "Cloud Computing", "tr": "Bulut Bilişim"},
        descriptions={
            "en": "Cloud infrastructure and SaaS leaders",
            "de": "Cloud-Infrastruktur und SaaS-Führer",
            "tr": "Bulut altyapı ve SaaS liderleri",
        },
        symbols=["CRM", "NOW", "SNOW", "DDOG", "NET", "ZS", "OKTA", "WDAY", "TEAM", "HUBS"],
    ),
    "cybersecurity": DemoCategory(
        key="cybersecurity",
        icon="🔐",
        names={"en": "Cybersecurity", "de": "Cybersicherheit", "tr": "Siber Güvenlik"},
        descriptions={
            "en": "Protecting the digital frontier",
            "de": "Schutz der digitalen Grenze",
            "tr": "Dijital sınırları koruyan şirketler",
        },
        symbols=["CRWD", "PANW", "ZS", "FTNT", "S", "OKTA", "CYBR", "VRNS", "TENB", "RPD"],
    ),
    # ----------------------------------------
    # 💊 HEALTHCARE & BIOTECH
    # ----------------------------------------
    "biotech_giants": DemoCategory(
        key="biotech_giants",
        icon="🧬",
        names={"en": "Biotech Giants", "de": "Biotech-Riesen", "tr": "Biyotek Devleri"},
        descriptions={
            "en": "Large-cap biotechnology leaders",
            "de": "Große Biotechnologie-Unternehmen",
            "tr": "Büyük biyoteknoloji şirketleri",
        },
        symbols=["AMGN", "GILD", "VRTX", "REGN", "BIIB", "MRNA", "BNTX", "ILMN", "ALNY", "SGEN"],
    ),
    "pharma_leaders": DemoCategory(
        key="pharma_leaders",
        icon="💊",
        names={"en": "Pharma Leaders", "de": "Pharma-Führer", "tr": "İlaç Liderleri"},
        descriptions={
            "en": "Major pharmaceutical companies",
            "de": "Große Pharmaunternehmen",
            "tr": "Büyük ilaç şirketleri",
        },
        symbols=["JNJ", "PFE", "MRK", "ABBV", "LLY", "BMY", "AZN", "NVS", "GSK", "SNY"],
    ),
    "healthcare_tech": DemoCategory(
        key="healthcare_tech",
        icon="🏥",
        names={"en": "Healthcare Tech", "de": "Gesundheitstechnologie", "tr": "Sağlık Teknolojisi"},
        descriptions={
            "en": "Digital health and medical technology",
            "de": "Digitale Gesundheit und Medizintechnik",
            "tr": "Dijital sağlık ve tıbbi teknoloji",
        },
        symbols=["VEEV", "DOCS", "TDOC", "HIMS", "OSCR", "PGNY", "SDGR", "TALK", "AMWL", "ONEM"],
    ),
    # ----------------------------------------
    # 🏦 FINANCE
    # ----------------------------------------
    "big_banks": DemoCategory(
        key="big_banks",
        icon="🏦",
        names={"en": "Big Banks", "de": "Großbanken", "tr": "Büyük Bankalar"},
        descriptions={
            "en": "America's largest financial institutions",
            "de": "Amerikas größte Finanzinstitute",
            "tr": "Amerika'nın en büyük finans kuruluşları",
        },
        symbols=["JPM", "BAC", "WFC", "C", "GS", "MS", "USB", "PNC", "TFC", "SCHW"],
    ),
    "fintech_disruptors": DemoCategory(
        key="fintech_disruptors",
        icon="💳",
        names={"en": "Fintech Disruptors", "de": "Fintech-Disruptoren", "tr": "Fintek Yıkıcıları"},
        descriptions={
            "en": "Financial technology innovators",
            "de": "Finanztechnologie-Innovatoren",
            "tr": "Finansal teknoloji yenilikçileri",
        },
        symbols=["V", "MA", "PYPL", "SQ", "COIN", "HOOD", "SOFI", "AFRM", "UPST", "BILL"],
    ),
    "insurance": DemoCategory(
        key="insurance",
        icon="🛡️",
        names={"en": "Insurance Leaders", "de": "Versicherungsführer", "tr": "Sigorta Liderleri"},
        descriptions={
            "en": "Major insurance companies",
            "de": "Große Versicherungsunternehmen",
            "tr": "Büyük sigorta şirketleri",
        },
        symbols=["BRK.B", "PGR", "ALL", "TRV", "MET", "PRU", "AIG", "AFL", "HIG", "LMND"],
    ),
    # ----------------------------------------
    # ⚡ ENERGY
    # ----------------------------------------
    "oil_gas": DemoCategory(
        key="oil_gas",
        icon="🛢️",
        names={"en": "Oil & Gas", "de": "Öl & Gas", "tr": "Petrol & Gaz"},
        descriptions={
            "en": "Traditional energy giants",
            "de": "Traditionelle Energieriesen",
            "tr": "Geleneksel enerji devleri",
        },
        symbols=["XOM", "CVX", "COP", "EOG", "SLB", "OXY", "PSX", "VLO", "MPC", "DVN"],
    ),
    "clean_energy": DemoCategory(
        key="clean_energy",
        icon="🌱",
        names={"en": "Clean Energy", "de": "Saubere Energie", "tr": "Temiz Enerji"},
        descriptions={
            "en": "Renewable energy and sustainability",
            "de": "Erneuerbare Energien und Nachhaltigkeit",
            "tr": "Yenilenebilir enerji ve sürdürülebilirlik",
        },
        symbols=["ENPH", "SEDG", "FSLR", "RUN", "PLUG", "BE", "NEE", "AES", "CHPT", "BLNK"],
    ),
    # ----------------------------------------
    # 🚗 MOBILITY
    # ----------------------------------------
    "ev_revolution": DemoCategory(
        key="ev_revolution",
        icon="🚗",
        names={"en": "EV Revolution", "de": "EV-Revolution", "tr": "Elektrikli Araç Devrimi"},
        descriptions={
            "en": "Electric vehicle makers and suppliers",
            "de": "Elektrofahrzeughersteller und Zulieferer",
            "tr": "Elektrikli araç üreticileri ve tedarikçiler",
        },
        symbols=["TSLA", "RIVN", "LCID", "NIO", "LI", "XPEV", "FSR", "CHPT", "QS", "GOEV"],
    ),
    "auto_legacy": DemoCategory(
        key="auto_legacy",
        icon="🚙",
        names={"en": "Legacy Auto", "de": "Traditionelle Autos", "tr": "Geleneksel Otomotiv"},
        descriptions={
            "en": "Traditional automakers going electric",
            "de": "Traditionelle Autohersteller werden elektrisch",
            "tr": "Elektriğe geçen geleneksel otomobil üreticileri",
        },
        symbols=["GM", "F", "TM", "HMC", "STLA", "VWAGY", "BMWYY", "MBGAF", "RACE", "TTM"],
    ),
    # ----------------------------------------
    # 🚀 THEMATIC
    # ----------------------------------------
    "space_defense": DemoCategory(
        key="space_defense",
        icon="🚀",
        names={"en": "Space & Defense", "de": "Raumfahrt & Verteidigung", "tr": "Uzay & Savunma"},
        descriptions={
            "en": "Aerospace and defense contractors",
            "de": "Luft- und Raumfahrt sowie Verteidigung",
            "tr": "Havacılık ve savunma müteahhitleri",
        },
        symbols=["LMT", "RTX", "NOC", "GD", "BA", "LHX", "RKLB", "SPCE", "ASTS", "LUNR"],
    ),
    "crypto_blockchain": DemoCategory(
        key="crypto_blockchain",
        icon="₿",
        names={
            "en": "Crypto & Blockchain",
            "de": "Krypto & Blockchain",
            "tr": "Kripto & Blockchain",
        },
        descriptions={
            "en": "Cryptocurrency and blockchain companies",
            "de": "Kryptowährung und Blockchain-Unternehmen",
            "tr": "Kripto para ve blockchain şirketleri",
        },
        symbols=["COIN", "MARA", "RIOT", "CLSK", "MSTR", "SQ", "PYPL", "HOOD", "HUT", "BITF"],
    ),
    "gaming_metaverse": DemoCategory(
        key="gaming_metaverse",
        icon="🎮",
        names={"en": "Gaming & Metaverse", "de": "Gaming & Metaverse", "tr": "Oyun & Metaverse"},
        descriptions={
            "en": "Video games and virtual worlds",
            "de": "Videospiele und virtuelle Welten",
            "tr": "Video oyunları ve sanal dünyalar",
        },
        symbols=["NVDA", "AMD", "RBLX", "U", "EA", "ATVI", "TTWO", "NTDOY", "SONY", "SE"],
    ),
    "social_media": DemoCategory(
        key="social_media",
        icon="📱",
        names={"en": "Social Media", "de": "Soziale Medien", "tr": "Sosyal Medya"},
        descriptions={
            "en": "Social networking platforms",
            "de": "Soziale Netzwerkplattformen",
            "tr": "Sosyal ağ platformları",
        },
        symbols=["META", "SNAP", "PINS", "TWTR", "RDDT", "MTCH", "BMBL", "ZG", "YELP", "ANGI"],
    ),
    # ----------------------------------------
    # 🛒 CONSUMER
    # ----------------------------------------
    "ecommerce": DemoCategory(
        key="ecommerce",
        icon="🛒",
        names={"en": "E-Commerce", "de": "E-Commerce", "tr": "E-Ticaret"},
        descriptions={
            "en": "Online retail and marketplaces",
            "de": "Online-Einzelhandel und Marktplätze",
            "tr": "Çevrimiçi perakende ve pazar yerleri",
        },
        symbols=["AMZN", "SHOP", "EBAY", "ETSY", "W", "CHWY", "WISH", "OSTK", "BIGC", "VTEX"],
    ),
    "streaming": DemoCategory(
        key="streaming",
        icon="📺",
        names={
            "en": "Streaming & Entertainment",
            "de": "Streaming & Unterhaltung",
            "tr": "Yayın & Eğlence",
        },
        descriptions={
            "en": "Video streaming and entertainment",
            "de": "Video-Streaming und Unterhaltung",
            "tr": "Video yayını ve eğlence",
        },
        symbols=["NFLX", "DIS", "WBD", "PARA", "CMCSA", "SPOT", "ROKU", "FUBO", "SONO", "COUR"],
    ),
    "food_beverage": DemoCategory(
        key="food_beverage",
        icon="🍔",
        names={"en": "Food & Beverage", "de": "Essen & Getränke", "tr": "Yiyecek & İçecek"},
        descriptions={
            "en": "Food, restaurants and beverages",
            "de": "Lebensmittel, Restaurants und Getränke",
            "tr": "Gıda, restoran ve içecekler",
        },
        symbols=["MCD", "SBUX", "YUM", "DPZ", "CMG", "DASH", "UBER", "KO", "PEP", "MNST"],
    ),
    "retail_giants": DemoCategory(
        key="retail_giants",
        icon="🏬",
        names={"en": "Retail Giants", "de": "Einzelhandelsriesen", "tr": "Perakende Devleri"},
        descriptions={
            "en": "Major retail and department stores",
            "de": "Große Einzelhandels- und Kaufhäuser",
            "tr": "Büyük perakende ve mağazalar",
        },
        symbols=["WMT", "COST", "TGT", "HD", "LOW", "ORLY", "AZO", "AAP", "BBY", "DG"],
    ),
    "luxury_fashion": DemoCategory(
        key="luxury_fashion",
        icon="👗",
        names={"en": "Luxury & Fashion", "de": "Luxus & Mode", "tr": "Lüks & Moda"},
        descriptions={
            "en": "Luxury brands and fashion retailers",
            "de": "Luxusmarken und Modehändler",
            "tr": "Lüks markalar ve moda perakendecileri",
        },
        symbols=["NKE", "LULU", "DECK", "CROX", "SKX", "VFC", "PVH", "RL", "TPR", "CPRI"],
    ),
    # ----------------------------------------
    # 📈 STRATEGIES
    # ----------------------------------------
    "dividend_kings": DemoCategory(
        key="dividend_kings",
        icon="💰",
        names={"en": "Dividend Kings", "de": "Dividenden-Könige", "tr": "Temettü Kralları"},
        descriptions={
            "en": "High-yield dividend stocks (4%+)",
            "de": "Hochverzinsliche Dividendenaktien (4%+)",
            "tr": "Yüksek temettü veren hisseler (%4+)",
        },
        symbols=["T", "VZ", "MO", "PM", "IBM", "XOM", "CVX", "ABBV", "KO", "JNJ"],
    ),
    "growth_rockets": DemoCategory(
        key="growth_rockets",
        icon="🚀",
        names={"en": "Growth Rockets", "de": "Wachstumsraketen", "tr": "Büyüme Roketleri"},
        descriptions={
            "en": "High-growth momentum stocks",
            "de": "Wachstumsstarke Momentum-Aktien",
            "tr": "Yüksek büyüme momentum hisseleri",
        },
        symbols=["NVDA", "TSLA", "AMD", "CRWD", "DDOG", "NET", "SNOW", "MDB", "ZS", "PANW"],
    ),
    "value_plays": DemoCategory(
        key="value_plays",
        icon="💎",
        names={"en": "Value Plays", "de": "Wertspiele", "tr": "Değer Oyuncuları"},
        descriptions={
            "en": "Undervalued quality companies",
            "de": "Unterbewertete Qualitätsunternehmen",
            "tr": "Düşük değerlemeli kaliteli şirketler",
        },
        symbols=["BRK.B", "JPM", "BAC", "CVX", "XOM", "VZ", "INTC", "GM", "F", "C"],
    ),
    "small_cap_gems": DemoCategory(
        key="small_cap_gems",
        icon="💠",
        names={
            "en": "Small Cap Gems",
            "de": "Small-Cap-Perlen",
            "tr": "Küçük Sermaye Mücevherleri",
        },
        descriptions={
            "en": "High-potential small companies",
            "de": "Kleine Unternehmen mit hohem Potenzial",
            "tr": "Yüksek potansiyelli küçük şirketler",
        },
        symbols=["SOFI", "UPST", "AFRM", "DAVE", "INOD", "BBAI", "SOUN", "AIP", "RKLB", "LUNR"],
    ),
    # ----------------------------------------
    # 🌍 REGIONAL
    # ----------------------------------------
    "china_tech": DemoCategory(
        key="china_tech",
        icon="🇨🇳",
        names={"en": "China Tech ADRs", "de": "China Tech ADRs", "tr": "Çin Teknoloji ADR'leri"},
        descriptions={
            "en": "Chinese technology companies (ADR)",
            "de": "Chinesische Technologieunternehmen (ADR)",
            "tr": "Çin teknoloji şirketleri (ADR)",
        },
        symbols=["BABA", "JD", "PDD", "BIDU", "NIO", "LI", "XPEV", "BILI", "TME", "NTES"],
    ),
    "europe_leaders": DemoCategory(
        key="europe_leaders",
        icon="🇪🇺",
        names={"en": "European Leaders", "de": "Europäische Marktführer", "tr": "Avrupa Liderleri"},
        descriptions={
            "en": "Top European companies (ADR)",
            "de": "Top-europäische Unternehmen (ADR)",
            "tr": "En iyi Avrupa şirketleri (ADR)",
        },
        symbols=["AZN", "NVO", "SAP", "ASML", "TM", "UL", "DEO", "BTI", "RIO", "BP"],
    ),
    # ----------------------------------------
    # 🏭 INDUSTRIALS
    # ----------------------------------------
    "industrial_titans": DemoCategory(
        key="industrial_titans",
        icon="🏭",
        names={"en": "Industrial Titans", "de": "Industrielle Titanen", "tr": "Sanayi Titanları"},
        descriptions={
            "en": "Manufacturing and industrial leaders",
            "de": "Fertigungs- und Industrieführer",
            "tr": "Üretim ve sanayi liderleri",
        },
        symbols=["HON", "UNP", "UPS", "CAT", "DE", "MMM", "GE", "EMR", "ITW", "ETN"],
    ),
    "travel_leisure": DemoCategory(
        key="travel_leisure",
        icon="✈️",
        names={"en": "Travel & Leisure", "de": "Reisen & Freizeit", "tr": "Seyahat & Eğlence"},
        descriptions={
            "en": "Airlines, hotels and leisure",
            "de": "Fluggesellschaften, Hotels und Freizeit",
            "tr": "Havayolları, oteller ve eğlence",
        },
        symbols=["DAL", "UAL", "AAL", "LUV", "MAR", "HLT", "BKNG", "ABNB", "EXPE", "RCL"],
    ),
}


# ============================================
# 🛠️ HELPER FUNCTIONS
# ============================================


def get_demo_stocks(category_key: str) -> list[str]:
    """Get stocks for a specific category."""
    if category_key in DEMO_CATEGORIES:
        return DEMO_CATEGORIES[category_key].symbols
    return []


def get_category_name(category_key: str, lang: str = "en") -> str:
    """Get localized category name."""
    if category_key in DEMO_CATEGORIES:
        return DEMO_CATEGORIES[category_key].names.get(
            lang, DEMO_CATEGORIES[category_key].names["en"]
        )
    return category_key


def get_category_description(category_key: str, lang: str = "en") -> str:
    """Get localized category description."""
    if category_key in DEMO_CATEGORIES:
        return DEMO_CATEGORIES[category_key].descriptions.get(
            lang, DEMO_CATEGORIES[category_key].descriptions["en"]
        )
    return ""


def get_all_demo_symbols() -> list[str]:
    """Get all unique symbols from all categories."""
    all_symbols = set()
    for cat in DEMO_CATEGORIES.values():
        all_symbols.update(cat.symbols)
    return sorted(list(all_symbols))


def get_category_count() -> int:
    """Get total number of categories."""
    return len(DEMO_CATEGORIES)


def get_unique_stock_count() -> int:
    """Get total number of unique stocks."""
    return len(get_all_demo_symbols())


def get_categories_by_group(lang: str = "en") -> dict[str, list[DemoCategory]]:
    """Group categories by theme for display."""
    groups = {
        "Technology": [
            "magnificent_7",
            "ai_revolution",
            "semiconductors",
            "cloud_computing",
            "cybersecurity",
        ],
        "Healthcare": ["biotech_giants", "pharma_leaders", "healthcare_tech"],
        "Finance": ["big_banks", "fintech_disruptors", "insurance"],
        "Energy": ["oil_gas", "clean_energy"],
        "Mobility": ["ev_revolution", "auto_legacy"],
        "Thematic": ["space_defense", "crypto_blockchain", "gaming_metaverse", "social_media"],
        "Consumer": ["ecommerce", "streaming", "food_beverage", "retail_giants", "luxury_fashion"],
        "Strategy": ["dividend_kings", "growth_rockets", "value_plays", "small_cap_gems"],
        "Regional": ["china_tech", "europe_leaders"],
        "Industrial": ["industrial_titans", "travel_leisure"],
    }

    # Translate group names
    group_names_i18n = {
        "en": {
            "Technology": "Technology",
            "Healthcare": "Healthcare",
            "Finance": "Finance",
            "Energy": "Energy",
            "Mobility": "Mobility",
            "Thematic": "Thematic",
            "Consumer": "Consumer",
            "Strategy": "Strategy",
            "Regional": "Regional",
            "Industrial": "Industrial",
        },
        "de": {
            "Technology": "Technologie",
            "Healthcare": "Gesundheit",
            "Finance": "Finanzen",
            "Energy": "Energie",
            "Mobility": "Mobilität",
            "Thematic": "Thematisch",
            "Consumer": "Konsum",
            "Strategy": "Strategie",
            "Regional": "Regional",
            "Industrial": "Industrie",
        },
        "tr": {
            "Technology": "Teknoloji",
            "Healthcare": "Sağlık",
            "Finance": "Finans",
            "Energy": "Enerji",
            "Mobility": "Mobilite",
            "Thematic": "Tematik",
            "Consumer": "Tüketici",
            "Strategy": "Strateji",
            "Regional": "Bölgesel",
            "Industrial": "Endüstriyel",
        },
    }

    result = {}
    for group_name, category_keys in groups.items():
        localized_name = group_names_i18n.get(lang, group_names_i18n["en"]).get(
            group_name, group_name
        )
        result[localized_name] = [DEMO_CATEGORIES[k] for k in category_keys if k in DEMO_CATEGORIES]

    return result


# Statistics at import time
DEMO_STATS = {
    "total_categories": get_category_count(),
    "unique_stocks": get_unique_stock_count(),
    "avg_per_category": get_unique_stock_count() // get_category_count()
    if get_category_count() > 0
    else 0,
}
