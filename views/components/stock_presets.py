"""
FinPilot Hazır Hisse Senedi Setleri
===================================

Kullanıcıların tek tıkla tarayabileceği hazır kategori listeleri.

Usage:
    from views.components.stock_presets import STOCK_PRESETS, render_preset_selector

    selected = render_preset_selector()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import streamlit as st


@dataclass
class StockPreset:
    """Hazır hisse senedi seti."""

    name: str
    icon: str
    description: str
    symbols: list[str]
    category: str


# ============================================
# 📊 HAZIR KATEGORİLER
# ============================================

STOCK_PRESETS: dict[str, StockPreset] = {
    # ----------------------------------------
    # 🖥️ TEKNOLOJİ
    # ----------------------------------------
    "tech_giants": StockPreset(
        name="Teknoloji Devleri",
        icon="🖥️",
        description="FAANG+ ve büyük teknoloji şirketleri",
        category="Sektör",
        symbols=[
            "AAPL",
            "MSFT",
            "GOOGL",
            "GOOG",
            "META",
            "AMZN",
            "NVDA",
            "TSLA",
            "ADBE",
            "CRM",
            "ORCL",
            "INTC",
            "AMD",
            "AVGO",
            "QCOM",
            "TXN",
            "MU",
            "AMAT",
            "LRCX",
            "KLAC",
            "SNPS",
            "CDNS",
            "MRVL",
            "ADI",
            "NXPI",
            "MCHP",
            "ON",
            "SWKS",
            "QRVO",
            "MPWR",
        ],
    ),
    "semiconductors": StockPreset(
        name="Yarı İletkenler",
        icon="💾",
        description="Çip üreticileri ve yarı iletken şirketleri",
        category="Sektör",
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
            "MRVL",
            "ADI",
            "NXPI",
            "MCHP",
            "ON",
            "SWKS",
            "QRVO",
            "MPWR",
            "ALGM",
            "ACLS",
            "AMKR",
            "CAMT",
            "AOSL",
            "ACMR",
            "AEHR",
            "ARM",
            "CRUS",
            "DIOD",
            "FORM",
            "MKSI",
        ],
    ),
    "cloud_saas": StockPreset(
        name="Bulut & SaaS",
        icon="☁️",
        description="Bulut altyapı ve yazılım hizmetleri",
        category="Sektör",
        symbols=[
            "CRM",
            "NOW",
            "SNOW",
            "DDOG",
            "NET",
            "ZS",
            "CRWD",
            "OKTA",
            "PANW",
            "FTNT",
            "WDAY",
            "SPLK",
            "MDB",
            "TEAM",
            "HUBS",
            "VEEV",
            "BILL",
            "DOCN",
            "CFLT",
            "ESTC",
            "GTLB",
            "PATH",
            "FROG",
            "SUMO",
            "NEWR",
            "ALKT",
            "APPF",
            "AGYS",
            "ACIW",
            "ALRM",
        ],
    ),
    # ----------------------------------------
    # 💊 SAĞLIK & BİYOTEK
    # ----------------------------------------
    "biotech_large": StockPreset(
        name="Büyük Biyotek",
        icon="🧬",
        description="Büyük biyoteknoloji şirketleri",
        category="Sektör",
        symbols=[
            "AMGN",
            "GILD",
            "VRTX",
            "REGN",
            "BIIB",
            "MRNA",
            "BNTX",
            "ILMN",
            "SGEN",
            "ALNY",
            "BMRN",
            "INCY",
            "EXEL",
            "JAZZ",
            "UTHR",
            "NBIX",
            "SRPT",
            "ALKS",
            "PTCT",
            "BLUE",
            "RARE",
            "FOLD",
            "HALO",
            "IONS",
            "ARCT",
            "CRSP",
            "EDIT",
            "NTLA",
            "BEAM",
            "VERV",
        ],
    ),
    "biotech_emerging": StockPreset(
        name="Yükselen Biyotek",
        icon="🔬",
        description="Gelişmekte olan biyotek şirketleri",
        category="Sektör",
        symbols=[
            "ABVX",
            "ACAD",
            "ACLX",
            "ADMA",
            "AGIO",
            "AKRO",
            "APGE",
            "AQST",
            "ARDX",
            "AXSM",
            "ETNB",
            "IRON",
            "KYMR",
            "LGND",
            "ANIP",
            "AUPH",
            "ALVO",
            "ACET",
            "ACIU",
            "ACTU",
            "ALT",
            "ARCT",
            "ARTV",
            "ATAI",
            "ATXS",
            "BCYC",
            "BDRX",
            "BRNS",
            "ACHV",
            "ABOS",
        ],
    ),
    "healthcare_services": StockPreset(
        name="Sağlık Hizmetleri",
        icon="🏥",
        description="Sağlık hizmet sağlayıcıları",
        category="Sektör",
        symbols=[
            "UNH",
            "CVS",
            "CI",
            "HUM",
            "CNC",
            "MOH",
            "ANTM",
            "HCA",
            "THC",
            "UHS",
            "ACHC",
            "ADUS",
            "ALHC",
            "AMEH",
            "CHE",
            "ENSG",
            "HIMS",
            "OSCR",
            "PGNY",
            "PRVA",
            "SDGR",
            "TALK",
            "TDOC",
            "VCYT",
            "VEEV",
            "DOCS",
            "ONEM",
            "AMWL",
            "LVGO",
            "ACCD",
        ],
    ),
    # ----------------------------------------
    # 🏦 FİNANS
    # ----------------------------------------
    "finance_banks": StockPreset(
        name="Bankalar",
        icon="🏦",
        description="Büyük ve bölgesel bankalar",
        category="Sektör",
        symbols=[
            "JPM",
            "BAC",
            "WFC",
            "C",
            "GS",
            "MS",
            "USB",
            "PNC",
            "TFC",
            "SCHW",
            "BK",
            "STT",
            "NTRS",
            "CFG",
            "KEY",
            "RF",
            "HBAN",
            "FITB",
            "MTB",
            "ZION",
            "CMA",
            "ALLY",
            "BOKF",
            "BANR",
            "BUSE",
            "ALRS",
            "FFIN",
            "IBKR",
            "LPLA",
            "MKTX",
        ],
    ),
    "finance_fintech": StockPreset(
        name="Fintek",
        icon="💳",
        description="Finansal teknoloji şirketleri",
        category="Sektör",
        symbols=[
            "V",
            "MA",
            "PYPL",
            "SQ",
            "COIN",
            "HOOD",
            "SOFI",
            "AFRM",
            "UPST",
            "BILL",
            "TOST",
            "FOUR",
            "DLO",
            "PAYO",
            "STNE",
            "PAGS",
            "NU",
            "DAVE",
            "CMPO",
            "GCMG",
            "BULL",
            "BETR",
            "CLOV",
            "LMND",
            "ROOT",
            "OPEN",
            "OPFI",
            "UPWK",
            "EQIX",
            "VNET",
        ],
    ),
    "insurance": StockPreset(
        name="Sigorta",
        icon="🛡️",
        description="Sigorta şirketleri",
        category="Sektör",
        symbols=[
            "BRK.B",
            "PGR",
            "ALL",
            "TRV",
            "MET",
            "PRU",
            "AIG",
            "AFL",
            "HIG",
            "LNC",
            "ACGL",
            "ACT",
            "BHF",
            "BWIN",
            "AMSF",
            "ACIC",
            "ERIE",
            "SIGI",
            "KNSL",
            "PLMR",
            "ROOT",
            "LMND",
            "HIPO",
            "EVER",
            "RYAN",
            "BRO",
            "GSHD",
            "WLTW",
            "MMC",
            "AON",
        ],
    ),
    # ----------------------------------------
    # ⚡ ENERJİ
    # ----------------------------------------
    "energy_oil": StockPreset(
        name="Petrol & Gaz",
        icon="🛢️",
        description="Petrol ve doğal gaz şirketleri",
        category="Sektör",
        symbols=[
            "XOM",
            "CVX",
            "COP",
            "EOG",
            "SLB",
            "OXY",
            "PSX",
            "VLO",
            "MPC",
            "PXD",
            "DVN",
            "FANG",
            "HES",
            "APA",
            "HAL",
            "BKR",
            "OVV",
            "CTRA",
            "MRO",
            "CLR",
            "RRC",
            "EQT",
            "AR",
            "SWN",
            "MTDR",
            "CHRD",
            "GPOR",
            "CNX",
            "NOG",
            "SM",
        ],
    ),
    "energy_renewable": StockPreset(
        name="Yenilenebilir Enerji",
        icon="🌱",
        description="Temiz enerji ve yenilenebilir kaynaklar",
        category="Sektör",
        symbols=[
            "ENPH",
            "SEDG",
            "FSLR",
            "RUN",
            "NOVA",
            "ARRY",
            "SHLS",
            "MAXN",
            "JKS",
            "CSIQ",
            "DQ",
            "SPWR",
            "BE",
            "PLUG",
            "BLDP",
            "FCEL",
            "NEE",
            "AES",
            "BEP",
            "CWEN",
            "HASI",
            "AMTX",
            "CLNE",
            "GEVO",
            "PTRA",
            "CHPT",
            "EVGO",
            "BLNK",
            "DCFC",
            "DRIV",
        ],
    ),
    # ----------------------------------------
    # 🚀 TEMATİK
    # ----------------------------------------
    "ai_leaders": StockPreset(
        name="Yapay Zeka Liderleri",
        icon="🤖",
        description="AI ve makine öğrenmesi odaklı şirketler",
        category="Tematik",
        symbols=[
            "NVDA",
            "MSFT",
            "GOOGL",
            "META",
            "AMD",
            "AVGO",
            "MRVL",
            "ARM",
            "PLTR",
            "AI",
            "PATH",
            "SNOW",
            "MDB",
            "DDOG",
            "CRWD",
            "PANW",
            "ZS",
            "S",
            "ESTC",
            "CFLT",
            "GTLB",
            "FROG",
            "DOCN",
            "INOD",
            "BBAI",
            "SOUN",
            "PRCT",
            "KARO",
            "GFAI",
            "AISP",
        ],
    ),
    "ev_mobility": StockPreset(
        name="Elektrikli Araç & Mobilite",
        icon="🚗",
        description="EV üreticileri ve şarj altyapısı",
        category="Tematik",
        symbols=[
            "TSLA",
            "RIVN",
            "LCID",
            "NIO",
            "LI",
            "XPEV",
            "FSR",
            "PSNY",
            "GOEV",
            "WKHS",
            "RIDE",
            "NKLA",
            "HYLN",
            "REE",
            "ARVL",
            "FFIE",
            "CHPT",
            "EVGO",
            "BLNK",
            "DCFC",
            "VLNC",
            "PTRA",
            "EOSE",
            "QS",
            "SLDP",
            "MVST",
            "FREYR",
            "ENVX",
            "AEHR",
            "LEA",
        ],
    ),
    "space_defense": StockPreset(
        name="Uzay & Savunma",
        icon="🚀",
        description="Uzay teknolojisi ve savunma sanayi",
        category="Tematik",
        symbols=[
            "LMT",
            "RTX",
            "NOC",
            "GD",
            "BA",
            "LHX",
            "TXT",
            "HII",
            "RKLB",
            "LUNR",
            "ASTS",
            "SPCE",
            "BKSY",
            "PL",
            "SATL",
            "ASTR",
            "RDW",
            "MNTS",
            "VORB",
            "GILT",
            "KTOS",
            "MRCY",
            "MAXR",
            "SATS",
            "VSAT",
            "IRDM",
            "GRMN",
            "FLY",
            "AIRO",
            "ACFN",
        ],
    ),
    "crypto_blockchain": StockPreset(
        name="Kripto & Blockchain",
        icon="₿",
        description="Kripto para ve blockchain şirketleri",
        category="Tematik",
        symbols=[
            "COIN",
            "MARA",
            "RIOT",
            "CLSK",
            "BITF",
            "HUT",
            "HIVE",
            "BTBT",
            "MSTR",
            "SQ",
            "PYPL",
            "HOOD",
            "SI",
            "SBNY",
            "ARBK",
            "IREN",
            "BTDR",
            "CIFR",
            "CORZ",
            "GREE",
            "WULF",
            "CANG",
            "XNET",
            "BTCS",
            "BNGO",
            "NVAX",
            "OCGN",
            "SAVA",
            "ANTA",
            "CMPO",
        ],
    ),
    # ----------------------------------------
    # 📈 STRATEJİ
    # ----------------------------------------
    "high_dividend": StockPreset(
        name="Yüksek Temettü",
        icon="💰",
        description="Yüksek temettü veren şirketler (%4+)",
        category="Strateji",
        symbols=[
            "T",
            "VZ",
            "MO",
            "PM",
            "IBM",
            "XOM",
            "CVX",
            "ABBV",
            "KO",
            "PEP",
            "JNJ",
            "PG",
            "MMM",
            "CAT",
            "DE",
            "EMR",
            "SWK",
            "GPC",
            "SYY",
            "ADM",
            "NUE",
            "AGNC",
            "NLY",
            "ARCC",
            "MAIN",
            "HTGC",
            "PSEC",
            "ORCC",
            "GBDC",
            "TPVG",
        ],
    ),
    "growth_momentum": StockPreset(
        name="Büyüme & Momentum",
        icon="📈",
        description="Yüksek büyüme gösteren şirketler",
        category="Strateji",
        symbols=[
            "NVDA",
            "TSLA",
            "AMD",
            "AVGO",
            "CRWD",
            "DDOG",
            "NET",
            "SNOW",
            "MDB",
            "ZS",
            "PANW",
            "FTNT",
            "ABNB",
            "DASH",
            "UBER",
            "LYFT",
            "RBLX",
            "COIN",
            "HOOD",
            "SOFI",
            "AFRM",
            "UPST",
            "DAVE",
            "INOD",
            "CAMT",
            "ACMR",
            "AEHR",
            "FLY",
            "ASTS",
            "AUR",
        ],
    ),
    "value_picks": StockPreset(
        name="Değer Hisseleri",
        icon="💎",
        description="Düşük değerleme ile işlem gören kaliteli şirketler",
        category="Strateji",
        symbols=[
            "BRK.B",
            "JPM",
            "BAC",
            "WFC",
            "C",
            "GS",
            "CVX",
            "XOM",
            "VZ",
            "T",
            "IBM",
            "INTC",
            "GM",
            "F",
            "AAL",
            "UAL",
            "DAL",
            "LUV",
            "CAR",
            "ACHC",
            "ACT",
            "BHF",
            "BOKF",
            "BANR",
            "ASO",
            "CAKE",
            "DRI",
            "SBUX",
            "MCD",
            "YUM",
        ],
    ),
    "small_cap_growth": StockPreset(
        name="Küçük Cap Büyüme",
        icon="🌱",
        description="Yüksek potansiyelli küçük şirketler",
        category="Strateji",
        symbols=[
            "SOFI",
            "UPST",
            "AFRM",
            "DAVE",
            "INOD",
            "AISP",
            "BBAI",
            "SOUN",
            "AIP",
            "AIRO",
            "ALNT",
            "AMPL",
            "ANGI",
            "ARQ",
            "ACTU",
            "ARTV",
            "ATAI",
            "ATXS",
            "ARCT",
            "AQST",
            "ADVM",
            "ABEO",
            "ABVC",
            "ACFN",
            "ADAM",
            "ADV",
            "AEBI",
            "AEHR",
            "AFYA",
            "ALGT",
        ],
    ),
    # ----------------------------------------
    # 🌍 BÖLGESEL
    # ----------------------------------------
    "uk_europe": StockPreset(
        name="İngiltere & Avrupa",
        icon="🇬🇧",
        description="Avrupa merkezli şirketler (ADR)",
        category="Bölgesel",
        symbols=[
            "AZN",
            "ARM",
            "BNTX",
            "ABVX",
            "CRSP",
            "ARQQ",
            "ATAI",
            "BCYC",
            "BRNS",
            "AUTL",
            "ARBK",
            "BGL",
            "CAPT",
            "ADAP",
            "AKTX",
            "BDRX",
            "AAPG",
            "ALVO",
            "ACIU",
            "AEBI",
            "AFYA",
            "GRAB",
            "SE",
            "BABA",
            "JD",
            "PDD",
            "BIDU",
            "NIO",
            "LI",
            "XPEV",
        ],
    ),
    "china_adr": StockPreset(
        name="Çin ADR",
        icon="🇨🇳",
        description="Çin merkezli şirketler (ADR)",
        category="Bölgesel",
        symbols=[
            "BABA",
            "JD",
            "PDD",
            "BIDU",
            "NIO",
            "LI",
            "XPEV",
            "BILI",
            "IQ",
            "TME",
            "WB",
            "NTES",
            "EDU",
            "TAL",
            "GOTU",
            "YQ",
            "HUYA",
            "DOYU",
            "ZH",
            "BZUN",
            "YUMC",
            "QFIN",
            "LX",
            "TIGR",
            "FUTU",
            "AAPG",
            "GDS",
            "VNET",
            "KC",
            "ATHM",
        ],
    ),
    # ----------------------------------------
    # 🏭 ENDÜSTRİYEL
    # ----------------------------------------
    "industrials": StockPreset(
        name="Sanayi",
        icon="🏭",
        description="Sanayi ve üretim şirketleri",
        category="Sektör",
        symbols=[
            "HON",
            "UNP",
            "UPS",
            "CAT",
            "DE",
            "MMM",
            "GE",
            "RTX",
            "LMT",
            "BA",
            "EMR",
            "ITW",
            "ETN",
            "PH",
            "ROK",
            "AME",
            "AAON",
            "AEIS",
            "ALNT",
            "ANDE",
            "BCPC",
            "BRKR",
            "ACDC",
            "ARQ",
            "AMTX",
            "AUR",
            "FLY",
            "AIRO",
            "ACU",
            "ACNT",
        ],
    ),
    "consumer_retail": StockPreset(
        name="Tüketici & Perakende",
        icon="🛒",
        description="Perakende ve tüketici şirketleri",
        category="Sektör",
        symbols=[
            "AMZN",
            "WMT",
            "COST",
            "TGT",
            "HD",
            "LOW",
            "BKNG",
            "ABNB",
            "EXPE",
            "MAR",
            "HLT",
            "SBUX",
            "MCD",
            "YUM",
            "DPZ",
            "CMG",
            "DRI",
            "CAKE",
            "ASO",
            "ORLY",
            "AZO",
            "AAP",
            "ULTA",
            "LULU",
            "NKE",
            "DECK",
            "CROX",
            "SKX",
            "BOOT",
            "FRPT",
        ],
    ),
    # ----------------------------------------
    # 🧬 BİYOTEK & İLAÇ (CSV Import)
    # ----------------------------------------
    "pharma_pipeline": StockPreset(
        name="İlaç & Biyoteknoloji Pipeline",
        icon="💊",
        description="Klinik aşamadaki ilaç ve biyotek şirketleri",
        category="Sektör",
        symbols=[
            "ABCL",
            "ABUS",
            "ACRS",
            "ACRV",
            "AARD",
            "AGEN",
            "ALT",
            "AMRX",
            "AUPH",
            "AVBP",
            "AVDL",
            "AXSM",
            "ETNB",
            "IRON",
            "KYMR",
            "LGND",
            "MIRM",
            "MRUS",
            "NAMS",
            "OCUL",
            "FOLD",
            "ADPT",
            "AURA",
            "APGE",
            "AKRO",
            "AGIO",
            "ANIP",
            "ALKS",
            "ADMA",
            "ABP",
        ],
    ),
    "medical_devices": StockPreset(
        name="Tıbbi Cihaz & Sağlık Hizmetleri",
        icon="🏥",
        description="Tıbbi cihaz, diagnostik ve sağlık hizmetleri",
        category="Sektör",
        symbols=[
            "ALGN",
            "ATRC",
            "LMAT",
            "LNTH",
            "ACHC",
            "ALHC",
            "ADUS",
            "ACHV",
            "BRKR",
            "BIIB",
            "AMGN",
            "ACAD",
            "ACLX",
            "ABVX",
            "CRSP",
            "ABSI",
            "ABEO",
            "ABOS",
            "ACB",
            "ACET",
            "ACIU",
            "ACTU",
            "ARDX",
            "ARCT",
            "AQST",
            "ADVM",
            "ARTV",
            "ATXS",
            "ATAI",
            "ABVC",
        ],
    ),
    # ----------------------------------------
    # 💻 YAZILIM & TEKNOLOJİ (CSV Import)
    # ----------------------------------------
    "enterprise_software": StockPreset(
        name="Kurumsal Yazılım",
        icon="🏢",
        description="SaaS, kurumsal çözümler ve altyapı yazılımları",
        category="Sektör",
        symbols=[
            "ADBE",
            "ADSK",
            "BSY",
            "BL",
            "APPF",
            "FIVN",
            "ACIW",
            "ALKT",
            "ALRM",
            "AGYS",
            "INOD",
            "AEYE",
            "AISP",
            "ADAM",
            "AUR",
            "AKAM",
            "AIOT",
            "ADP",
            "ACMR",
            "ACLS",
            "AEIS",
            "CAMT",
            "GDS",
            "AMBA",
            "ALAB",
            "ADI",
            "ALGM",
            "AMKR",
            "AIP",
            "AAON",
        ],
    ),
    # ----------------------------------------
    # 🏦 FİNANS & SİGORTA (CSV Import)
    # ----------------------------------------
    "finance_diversified": StockPreset(
        name="Çeşitlendirilmiş Finans",
        icon="🏦",
        description="Bankalar, sigortacılar ve finans hizmetleri",
        category="Sektör",
        symbols=[
            "AFRM",
            "DAVE",
            "BULL",
            "CMPO",
            "GCMG",
            "ACGL",
            "ACT",
            "NMIH",
            "BHF",
            "BWIN",
            "BOKF",
            "BANR",
            "BUSE",
            "AFBI",
            "AAME",
            "AIFU",
            "ANTA",
            "AGNC",
            "ACR",
            "ACRE",
            "AEI",
            "AFCG",
            "AIRE",
            "ACTG",
            "ALVO",
            "ABAT",
            "AMSC",
            "ACDC",
            "APA",
            "AEP",
        ],
    ),
    # ----------------------------------------
    # 🚀 TRENDİNG & MOMENTUM (CSV Import)
    # ----------------------------------------
    "trending_momentum": StockPreset(
        name="Trending & Yüksek Hacim",
        icon="📈",
        description="Yüksek işlem hacimli ve momentum gösteren hisseler",
        category="Strateji",
        symbols=[
            "AAPL",
            "ABNB",
            "AAL",
            "ASTS",
            "AFRM",
            "AUR",
            "BULL",
            "ALAB",
            "CRSP",
            "DAVE",
            "FLY",
            "ACMR",
            "ADMA",
            "AMKR",
            "BRKR",
            "ASO",
            "CAKE",
            "FRPT",
            "INOD",
            "KYMR",
            "LGND",
            "AXSM",
            "BIIB",
            "AMGN",
            "ADBE",
            "ADSK",
            "BSY",
            "BL",
            "APPF",
            "FIVN",
        ],
    ),
    # ----------------------------------------
    # 🌍 ULUSLARARASI (CSV Import)
    # ----------------------------------------
    "international_mix": StockPreset(
        name="Uluslararası Karışım",
        icon="🌐",
        description="ABD dışı ve çok uluslu şirketler",
        category="Bölgesel",
        symbols=[
            "AAPG",
            "ABVX",
            "ACIU",
            "ALVO",
            "CRSP",
            "MRUS",
            "NAMS",
            "ATAI",
            "GDS",
            "CAMT",
            "ARCT",
            "ACGL",
            "AUPH",
            "ABCL",
            "ABUS",
            "ACB",
            "AVDL",
            "AFRI",
            "ANTA",
            "AIFU",
            "AACG",
            "BATRA",
            "BATRK",
            "ALGN",
            "ABNB",
            "AMGN",
            "BIIB",
            "AMBA",
            "LMAT",
            "MIRM",
        ],
    ),
    # ============================================
    # 🌐 FINPILOT SEKTÖR TARAMA SETLERİ
    # (Sektör bazlı optimize edilmiş NASDAQ listeler)
    # ============================================
    "fp_technology": StockPreset(
        name="FP: Teknoloji",
        icon="💻",
        description="Yazılım, yarıiletken, bulut, SaaS — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "TXN", "KLAC", "ADI", "SHOP", "QCOM", "PDD", "APP", "ARM",
            "PANW", "ADBE", "INTU", "CRWD", "WDC", "SNDK", "STX", "SNPS",
            "CDNS", "DASH", "NTES", "MRVL", "FTNT", "NXPI", "MPWR", "FER",
            "ADSK", "BIDU", "CRWV", "MCHP", "DDOG", "ERIC", "MSTR", "MCHPP",
            "WDAY", "ROP", "CTSH", "STRF", "STRC", "MDB", "ON", "ZM",
            "FSLR", "GFS", "ZS", "FLEX", "NBIS", "STRK", "CRDO", "STRD",
            "ALAB", "NTAP", "TEAM", "VRSN", "SMCI", "PTC", "MTSI", "SSNC",
            "CHKP", "CDW", "TSEM", "NVMI", "GEN", "LSCC", "IREN", "LOGI",
            "OKTA", "BILI", "AEIS", "TTD", "AMKR", "JKHY", "TTMI", "RMBS",
            "CFLT", "NTNX", "SITM", "TEM", "BSY", "AUR", "GDS", "SWKS",
            "DOCU", "MANH", "SANM", "SMTC", "SAIL", "PEGA", "QRVO", "MBLY",
            "BZ", "VICR", "DOX", "MTCH", "NICE", "FORM", "CRUS", "ALGM",
            "CAMT", "SLAB", "DBX", "VIAV",
        ],
    ),
    "fp_health_care": StockPreset(
        name="FP: Sağlık",
        icon="🏥",
        description="İlaç, biyoteknoloji, medikal cihaz — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "GILD", "ISRG", "VRTX", "SNY", "REGN", "MDLN", "ARGX", "IDXX",
            "ALNY", "ONC", "GEHC", "INSM", "NTRA", "BIIB", "DXCM", "BNTX",
            "RPRX", "BTSGU", "UTHR", "INCY", "RVMD", "EXAS", "MRNA", "ROIV",
            "GMAB", "VTRS", "ILMN", "PODD", "HOLX", "COO", "RGC", "ASND",
            "ALGN", "IONS", "BBIO", "GH", "NBIX", "MEDP", "BMRN", "ENSG",
            "SMMT", "EXEL", "RNA", "JAZZ", "ABVX", "MDGL", "MASI", "HSIC",
            "AXSM", "TECH", "ARWR", "IBRX", "PRAX", "HALO", "CYTK", "PCVX",
            "ICLR", "KRYS", "RGEN", "BTSG", "NUVL", "KYMR", "BLTE", "RYTM",
            "GRFS", "COGT", "PTCT", "OPCH", "CAI", "RDNT", "IMVT", "MIRM",
            "ALKS", "PTGX", "CRSP", "SHC", "LNTH", "SRRK", "MMSI", "IRTC",
            "CELC", "TGTX", "APGE", "CGON", "GPCR", "TMDX", "AMRX", "CRNX",
            "FOLD", "INDV", "ALHC", "NAMS", "TERN", "ACAD", "BLLN", "ICUI",
            "ERAS", "ADMA", "LIVN", "ACLX",
        ],
    ),
    "fp_finance": StockPreset(
        name="FP: Finans",
        icon="🏦",
        description="Bankacılık, sigorta, yatırım, fintech — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "CME", "HOOD", "HBANL", "HBANM", "NDAQ", "COIN", "HBANZ", "HBAN",
            "HBANP", "ACGL", "FITB", "IBKR", "WTW", "TW", "NTRS", "LPLA",
            "CINF", "FCNCA", "SOFI", "FUTU", "PFG", "TROW", "CG", "FITBM",
            "FITBI", "AFRM", "BPYPP", "BPYPM", "TPG", "EWBC", "FITBP", "BPYPO",
            "SLMBP", "VLYPN", "BPYPN", "VLYPP", "VLYPO", "ARCC", "FITBO", "ERIE",
            "XP", "WTFC", "SEIC", "ONB", "ONBPO", "BPOP", "ONBPP", "UMBF",
            "COLB", "ZION", "GLXY", "BOKF", "APLD", "GGAL", "CHYM", "ACGLO",
            "CBSH", "VLY", "FRHC", "FSV", "SNEX", "MKTX", "ACGLN", "CGABL",
            "MORN", "FIGR", "UBSI", "ACT", "HLNE", "STEP", "HWC", "RIOT",
            "HUT", "CIFR", "CIGI", "OZK", "CORZ", "CORZZ", "CACC", "SIGI",
            "VCTR", "FFIN", "OPEN", "TCBI", "SLM", "EBC", "BGC", "IBOC",
            "OXLCP", "OXLCN", "OXLCZ", "TFSL", "OXLCL", "INDB", "OXLCO", "INTR",
            "FULT", "BANF", "FIBK", "NTRSO",
        ],
    ),
    "fp_industrials": StockPreset(
        name="FP: Sanayi",
        icon="🏭",
        description="Makine, havacılık, inşaat, lojistik — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "HON", "ADP", "CTAS", "CSX", "ELVR", "TER", "BRKRP", "ODFL",
            "PYPL", "RKLB", "AXON", "ESLT", "PAYX", "SYM", "FTAI", "STLD",
            "VRSK", "FOXA", "RGLD", "FWONK", "CHRW", "FOX", "JBHT", "FWONA",
            "ENTG", "LI", "RIVN", "NXT", "MKSI", "KTOS", "NDSN", "TRMB",
            "LECO", "STRL", "AVAV", "ZBRA", "SOLS", "PSKY", "SAIA", "DRS",
            "IESC", "CGNX", "AAON", "MIDD", "VFS", "ROAD", "NXST", "SSRM",
            "MWH", "BRKR", "BCPC", "LSTR", "CENX", "ITRI", "MYRG", "VSNT",
            "WSC", "MEOH", "HSAI", "LUNR", "WDFC", "FLY", "USLM", "LCID",
            "POWWP", "CECO", "FTAIM", "ATRO", "HUBG", "FTAIN", "TXG", "ARCB",
            "DXPE", "NN", "ANDE", "WERN", "KALU", "NWL", "PSIX", "IOSP",
            "PCTTU", "PCT", "ROCK", "TRS", "COHU", "XPEL", "ASTE", "PSNY",
            "PLPC", "EYPT", "CDNL", "AEBI", "ALNT", "GLDD", "MRTN", "OUST",
            "TSAT", "AEHR", "SBGI", "GPRE", "NNAVW", "RR", "HTLD", "EH",
            "FWRD", "SWIM", "STKL", "LOT", "TRNS", "NWPX", "KRNT", "TATT",
            "MBUU", "ASPI", "CTKB", "CMCO", "SWBI", "ASTL", "MLAB", "KRT",
            "PACB", "FEIM", "LWLG", "GEVO", "ULH", "LAB", "PKOH", "MCFT",
            "OFLX", "FWDI", "VFSWW", "ADUR", "NAUT", "CHSCP", "CUB", "SSP",
            "FSTR", "CHSCO", "CHSCL", "CHSCN", "CHSCM", "NKLR", "AIRO", "TAYD",
            "PPIH", "NIU", "QTRX", "IONR", "RAIL", "PAMT", "PESI", "TWIN",
            "POWW", "MASS", "ESOA", "AZ", "SND", "PSNYW", "QSI", "CBUS",
            "AIRJ", "GDC", "ALTO", "DPRO", "FLX", "BOOM", "SMID", "RPID",
            "ATLX", "BNC", "ACNT", "ATLN", "CODA", "ARQ", "BAER", "FRD",
            "LBGJ", "SHIM", "KEQU", "GEOS", "SEER", "FORR", "LGO", "HURC",
            "CRGO", "CDXS", "LNZA", "ZJK", "VMAR", "AMTX", "WRAP", "FFAI",
            "KNDI", "NTIC", "HOVR", "NNBR", "HLP", "SFWL", "MIND", "FEAM",
            "SYPR", "ZTEK", "LOOP", "SLGB", "XCH", "YIBO", "PCTTW", "VGAS",
            "DSWL", "CSTE", "DCX", "OCC", "MOB", "LOTWW", "SORA", "SEV",
            "PSIG", "AQMS", "FTEK", "PRPO", "AIRJW", "GGR", "PPSI", "AIIO",
            "SAFX", "TPCS", "BIOX", "WPRT", "SDST", "APWC", "QSIAW", "CLIR",
            "EKSO", "BAERW", "DAIO", "HBIO", "NCEW", "PRZO", "KITT", "ORGN",
            "ZKIN", "ASTLW", "MOBBW", "TRSG", "REE", "TOMZ", "HUDI", "HOVRW",
            "ELSE", "GTEC", "RVSN", "ENGS", "CRGOW", "ELOG", "ARTW", "SNES",
            "PETZ", "BNGO", "FGI", "CENN", "WETO", "SKYQ", "GURE", "ETS",
            "INHD", "WKHS", "YHGJ", "JYD", "HXHX", "INLF", "MNTS", "AIIOW",
            "VEEE", "CNEY", "SKK", "FCUV", "EVGN", "GLXG", "DXST", "FFAIW",
            "ASTC", "AEHL", "HIHO", "FLYE", "GWAV", "AIOS", "CDTG", "SGLY",
            "NITO", "GVH", "OUSTZ", "SDSTW", "KITTW", "MTEN", "AREB", "RETO",
            "NVVE", "TANH", "BNRG", "VGASW", "ORGNW", "DTCK", "AREBW", "LNZAW",
            "GGROW", "FGIWW", "RVSNW", "NVVEW", "MNTSW",
        ],
    ),
    "fp_consumer_discretionary": StockPreset(
        name="FP: Tüketici İhtiyari",
        icon="🛍️",
        description="Turizm, eğlence, perakende, restoran — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "BKNG", "SBUX", "MAR", "ORLY", "ABNB", "WBD", "PCAR", "ROST",
            "BKR", "FAST", "EA", "JD", "TRI", "TTWO", "UAL", "KMB",
            "CPRT", "RYAAY", "SATS", "ULTA", "ASTS", "TSCO", "DLTR", "EXPE",
            "CASY", "LULU", "HTHT", "WMG", "NWS", "HAS", "NWSA", "DPZ",
            "FIVE", "WYNN", "TXRH", "DKNG", "TTEK", "LLYVK", "AAL", "LLYVA",
            "LKQ", "POOL", "FCFS", "EQPT", "GSAT", "WFRD", "WING", "SIRI",
            "RRR", "OLLI", "CHDN", "OMAB", "MMYT", "URBN", "DOO", "LGN",
            "RUSHA", "MAT", "ATAT", "VSEC", "GNTX", "RUSHB", "REYN", "CROX",
            "GLNG", "PSMT", "IEP", "CVCO", "PATK", "CZR", "FELE", "SKYW",
            "FTDR", "DORM", "ASO", "GTX", "EXPO", "COLM", "CAR", "IPAR",
            "CAKE", "HWKN", "VRRM", "BATRA", "PLBL", "SBLK", "SHOO", "CHEF",
            "DRVN", "MGRC", "BATRK", "TRMD", "NSIT", "MLCO", "GT", "VC",
            "CENT", "MCW", "OSW", "HURN",
        ],
    ),
    "fp_energy": StockPreset(
        name="FP: Enerji",
        icon="🛢️",
        description="Petrol, gaz, yenilenebilir enerji — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "FANG", "EXE", "WWD", "VNOM", "PAA", "APA", "LFUS", "POWL",
            "CHRD", "PAGP", "ARLP", "PTEN", "MGEE", "PLUG", "NESR", "CLMT",
            "DMLP", "METC", "ACDC", "APC", "METCB", "HNRG", "FIP", "HPK",
            "BLDP", "FCEL", "PNRG", "AREC", "NUAI", "ANNA", "EPSN", "KGEI",
            "MMLP", "TUSK", "NCSM", "NUAIW", "DWSN", "USEG", "KLXE", "UFG",
            "RCON", "PTLE", "NWGL", "DLXY", "CIIT", "ANNAW", "BANL", "ATON",
            "MARPS", "HTOO",
        ],
    ),
    "fp_consumer_staples": StockPreset(
        name="FP: Temel Tüketim",
        icon="🛒",
        description="Gıda, içecek, ev bakım, tarım — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "MNST", "MDLZ", "CCEP", "KDP", "KHC", "CELH", "COKE", "PPC",
            "SFD", "CPB", "SFM", "MZTI", "CALM", "FRPT", "FIZZ", "COCO",
            "SONO", "IMKTA", "JJSF", "SMPL", "VITL", "AVO", "GO", "JBSS",
            "SENEA", "SENEB", "ARKO", "MAMA", "VLGEA", "MGPI", "DNUT", "WEST",
            "AGCC", "OTLY", "LWAY", "BYND", "WEYS", "AFRI", "LMNR", "TWG",
            "GNSS", "CHSN", "HAIN", "ABVE", "YI", "BRID", "PETS", "BOF",
            "UEIC", "BRFH", "KOSS", "BRLS", "MGN", "RYM", "FARM", "RDGT",
            "PFAI", "RMCF", "AFRIW", "WYHG", "YHC", "EPSM", "ABVEW", "JVA",
            "FAMI", "COOT", "WVVIP", "WVVI", "SEED", "RIME", "AGRZ", "MSS",
            "IPST", "TULP", "JXG", "SOWG", "NCRA", "AQB", "RKDA", "IBG",
            "IMTE", "STKH", "EDBL", "ORIS", "BRLSW", "COOTW", "EDBLW",
        ],
    ),
    "fp_real_estate": StockPreset(
        name="FP: Gayrimenkul",
        icon="🏠",
        description="REIT, emlak yönetimi, geliştirme — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "MELI", "EQIX", "EBAY", "TCOM", "FISV", "AGNCN", "AGNCO", "AGNCL",
            "AGNCP", "AGNCM", "SBAC", "CSGP", "GRAB", "REG", "HST", "LAMR",
            "AKAM", "GLPI", "AGNC", "Z", "ZG", "CART", "LINE", "HQY",
            "FRMI", "LYFT", "SBRA", "PECO", "LAUR", "EXLS", "LOPE", "DHCNL",
            "DHCNI", "REGCP", "REGCO", "DLO", "RELY", "XMTR", "ADAMI", "ADAMM",
            "ADAML", "PRDO", "ADAMN", "UNIT", "DRH", "PAYO", "STRA", "ADAMZ",
            "DHC", "FLYW", "AFYA", "GOODN", "RDWR", "LQDT", "GOODO", "LINC",
            "APEI", "LANDO", "AHG", "LANDP", "NUTX", "UXIN", "UDMY", "GRABW",
            "QNST", "GOOD", "CASS", "NHPAP", "NHPBP", "IMXI", "PRTH", "GRVY",
            "LAND", "ILPT", "SOHOO", "SOHOB", "SVC", "SOHON", "RMNI", "RPAY",
            "REFI", "CNDT", "STRS", "HERE", "ADV", "SEVN", "CURR", "OPRX",
            "KRKR", "SUNS", "RGP", "MAYS", "STHO", "YOUL", "WHLRL", "INTG",
            "MNY", "SELF", "LOAN", "HGBL", "NAMI", "AACG", "SCOR", "WHLRD",
            "YQ", "TDTH", "CREG", "TC", "EPOW", "GYRO", "SGRP", "SWVL",
            "EDTK", "MDRR", "GSUN", "OLB", "SQFTP", "FTFT", "MIMI", "BTCT",
            "MKZR", "WAFU", "TGL", "CJMB", "BOXL", "ZCMD", "GV", "SOPA",
            "WHLRP", "XHLD", "QH", "EEIQ", "LXEH", "SQFT", "BAOS", "WAI",
            "GIPR", "KIDZ", "JZ", "CMCT", "MNYWW", "VSA", "WHLR", "UK",
            "JDZG", "KIDZW", "GIPRW", "SWVLW", "SQFTW",
        ],
    ),
    "fp_telecommunications": StockPreset(
        name="FP: Telekomünikasyon",
        icon="📡",
        description="İletişim altyapısı, uydu, fiber — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "CMCSA", "LITE", "VOD", "CHTR", "FFIV", "ROKU", "TIGO", "LBRDK",
            "LBRDA", "LBTYB", "LBTYA", "VEON", "LBTYK", "LBRDP", "KYIV", "IRDM",
            "HTO", "DGII", "EXTR", "NSSC", "LILAK", "LILA", "GLIBA", "GLIBK",
            "ZD", "KYIVW", "MATW", "SHEN", "ATEX", "AIOT", "ATNI", "ALLT",
            "AMCX", "TTGT", "SPOK", "LTRX", "TBCH", "HUHU", "INSG", "CXDO",
            "SIDU", "SILC", "REKR", "SNT", "AMPG", "BWEN", "KSCP", "FOXX",
            "CHAI", "BOSC", "UTSI", "WLDSW", "INTZ", "MTEK", "NXPL", "WLDS",
            "MYSE", "AMPGZ", "HUBC", "NXPLW", "MTEKW", "ASNS", "FOXXW", "HUBCW",
        ],
    ),
    "fp_utilities": StockPreset(
        name="FP: Enerji & Altyapı",
        icon="⚡",
        description="Elektrik, doğalgaz, su, nükleer — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "CEG", "AEP", "EXC", "XEL", "EVRG", "LNT", "TLN", "ENLT",
            "CWST", "NWE", "OTTR", "RNW", "CDZIP", "NEXT", "NNE", "MSEX",
            "ADTN", "NTGR", "CWCO", "CLNE", "YORW", "CLFD", "CDZI", "OPAL",
            "NFE", "ARTNA", "PCYO", "GWRS", "MNTK", "WAVE", "RGCO", "AUDC",
            "VIASP", "ESGL", "SLNG", "FKWL", "FIEE", "VVPR", "QRHC", "SUUN",
            "CLRO", "SONM", "SUNE", "ESGLW", "RNWWW",
        ],
    ),
    "fp_miscellaneous": StockPreset(
        name="FP: Çeşitli",
        icon="📦",
        description="Konglomera, çoklu sektör şirketleri — NASDAQ sektör tarama",
        category="FinPilot Sektör",
        symbols=[
            "IDCC", "NOVT", "RUN", "QS", "EOSE", "FLNC", "NOVTU", "ENVX",
            "CTLP", "MVST", "SLDP", "APPS", "ACTG", "BYRN", "NEOV", "JYNT",
            "NVX", "ULBI", "CBAT", "SLDPW", "ELBM", "VHC", "ZEO", "RMCO",
            "NEOVW", "REFR", "FLUX", "STI", "DFLI", "AMOD", "LASE", "CAPT",
            "XELB", "MVSTW", "GAUZ", "TURB", "XPON", "ELPW", "POLA", "RMCOW",
            "ZEOWW", "AMODW", "CAPTW", "DFLIW",
        ],
    ),
}


# ============================================
# 🎨 UI COMPONENTS
# ============================================


def render_preset_selector() -> list[str] | None:
    """
    Hazır kategori seçici widget.

    Returns:
        Seçilen kategorinin sembolleri veya None
    """
    st.markdown("### 📊 Hazır Tarama Setleri")
    st.caption("Tek tıkla hazır kategorileri tarayın")

    # Kategorilere göre grupla
    categories = {}
    for key, preset in STOCK_PRESETS.items():
        if preset.category not in categories:
            categories[preset.category] = []
        categories[preset.category].append((key, preset))

    # Her kategori için expander
    selected_preset = None

    for category_name, presets in categories.items():
        with st.expander(f"📁 {category_name}", expanded=False):
            cols = st.columns(3)
            for idx, (key, preset) in enumerate(presets):
                with cols[idx % 3]:
                    if st.button(
                        f"{preset.icon} {preset.name}",
                        key=f"preset_{key}",
                        help=f"{preset.description}\n({len(preset.symbols)} hisse)",
                        use_container_width=True,
                    ):
                        selected_preset = key

    if selected_preset:
        preset = STOCK_PRESETS[selected_preset]
        st.success(f"✅ {preset.icon} **{preset.name}** seçildi ({len(preset.symbols)} hisse)")
        return preset.symbols

    return None


def render_preset_cards() -> list[str] | None:
    """
    Kart görünümünde preset seçici.

    Returns:
        Seçilen kategorinin sembolleri veya None
    """
    st.markdown("### 🎯 Popüler Tarama Setleri")

    # En popüler 6 kategoriyi göster
    popular_keys = [
        "tech_giants",
        "ai_leaders",
        "biotech_large",
        "semiconductors",
        "ev_mobility",
        "growth_momentum",
    ]

    cols = st.columns(3)
    selected_preset = None

    for idx, key in enumerate(popular_keys):
        preset = STOCK_PRESETS[key]
        with cols[idx % 3]:
            with st.container():
                st.markdown(
                    f"""
                <div style='background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(15,23,42,0.95));
                            border-radius: 12px; padding: 16px; margin-bottom: 12px;
                            border: 1px solid rgba(255,255,255,0.1);'>
                    <div style='font-size: 2rem; margin-bottom: 8px;'>{preset.icon}</div>
                    <div style='font-weight: 600; color: #f8fafc; margin-bottom: 4px;'>{preset.name}</div>
                    <div style='font-size: 0.85rem; color: #94a3b8; margin-bottom: 8px;'>{preset.description}</div>
                    <div style='font-size: 0.75rem; color: #64748b;'>{len(preset.symbols)} hisse</div>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                if st.button("Tara", key=f"card_{key}", use_container_width=True):
                    selected_preset = key

    # Tüm kategorileri göster butonu
    st.markdown("---")

    if st.checkbox("🔍 Tüm kategorileri göster", key="show_all_presets"):
        result = render_preset_selector()
        if result:
            return result

    if selected_preset:
        preset = STOCK_PRESETS[selected_preset]
        return preset.symbols

    return None


def render_quick_preset_buttons() -> list[str] | None:
    """
    Hızlı erişim butonları - sidebar için.

    Returns:
        Seçilen kategorinin sembolleri veya None
    """
    st.sidebar.markdown("### ⚡ Hızlı Tarama")

    quick_presets = [
        ("tech_giants", "🖥️ Teknoloji"),
        ("ai_leaders", "🤖 AI"),
        ("semiconductors", "💾 Çipler"),
        ("biotech_large", "🧬 Biyotek"),
        ("growth_momentum", "📈 Büyüme"),
    ]

    for key, label in quick_presets:
        if st.sidebar.button(label, key=f"quick_{key}", use_container_width=True):
            preset = STOCK_PRESETS[key]
            st.sidebar.success(f"✅ {len(preset.symbols)} hisse yüklendi")
            return preset.symbols

    return None


def get_preset_symbols(preset_key: str) -> list[str]:
    """Belirtilen preset'in sembollerini döndür."""
    if preset_key in STOCK_PRESETS:
        return STOCK_PRESETS[preset_key].symbols
    return []


def list_all_presets() -> dict[str, str]:
    """Tüm presetlerin listesi (key: name)."""
    return {key: f"{p.icon} {p.name}" for key, p in STOCK_PRESETS.items()}


def get_finpilot_sector_symbols() -> list[str]:
    """Tüm FinPilot sektör sembollerini birleştirilmiş liste olarak döndür."""
    seen: set[str] = set()
    result: list[str] = []
    for key, preset in STOCK_PRESETS.items():
        if key.startswith("fp_"):
            for s in preset.symbols:
                if s not in seen:
                    seen.add(s)
                    result.append(s)
    return result


def load_sectors_from_index() -> dict[str, dict]:
    """data/tickers/sectors/sector_index.json dosyasından dinamik sektör yükle."""
    import json
    import os

    index_path = os.path.join(os.getcwd(), "data", "tickers", "sectors", "sector_index.json")
    if not os.path.exists(index_path):
        return {}

    try:
        with open(index_path) as f:
            return json.load(f)
    except Exception:
        return {}


# ============================================
# 📊 İSTATİSTİKLER
# ============================================


def get_preset_stats() -> dict[str, Any]:
    """Preset istatistikleri."""
    total_presets = len(STOCK_PRESETS)
    total_symbols = sum(len(p.symbols) for p in STOCK_PRESETS.values())
    unique_symbols = len(set(s for p in STOCK_PRESETS.values() for s in p.symbols))

    categories = {}
    for p in STOCK_PRESETS.values():
        categories[p.category] = categories.get(p.category, 0) + 1

    return {
        "total_presets": total_presets,
        "total_symbols": total_symbols,
        "unique_symbols": unique_symbols,
        "categories": categories,
    }
