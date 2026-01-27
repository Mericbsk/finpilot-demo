# -*- coding: utf-8 -*-
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
from typing import Any, Dict, List, Optional

import streamlit as st


@dataclass
class StockPreset:
    """Hazır hisse senedi seti."""

    name: str
    icon: str
    description: str
    symbols: List[str]
    category: str


# ============================================
# 📊 HAZIR KATEGORİLER
# ============================================

STOCK_PRESETS: Dict[str, StockPreset] = {
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
}


# ============================================
# 🎨 UI COMPONENTS
# ============================================


def render_preset_selector() -> Optional[List[str]]:
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


def render_preset_cards() -> Optional[List[str]]:
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


def render_quick_preset_buttons() -> Optional[List[str]]:
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


def get_preset_symbols(preset_key: str) -> List[str]:
    """Belirtilen preset'in sembollerini döndür."""
    if preset_key in STOCK_PRESETS:
        return STOCK_PRESETS[preset_key].symbols
    return []


def list_all_presets() -> Dict[str, str]:
    """Tüm presetlerin listesi (key: name)."""
    return {key: f"{p.icon} {p.name}" for key, p in STOCK_PRESETS.items()}


# ============================================
# 📊 İSTATİSTİKLER
# ============================================


def get_preset_stats() -> Dict[str, Any]:
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
