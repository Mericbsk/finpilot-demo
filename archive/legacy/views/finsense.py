import json
import os
import random

import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Veri Yükleme
# ──────────────────────────────────────────────────────────────────────────────


def load_dictionary():
    """v2 şemasını destekler; yoksa v1'e (dictionary.json) geri döner."""
    for fname in ["dictionary_v2.json", "dictionary.json"]:
        path = os.path.join("data", fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                return json.load(f)
    return []


# ──────────────────────────────────────────────────────────────────────────────
# Dil Yardımcısı
# ──────────────────────────────────────────────────────────────────────────────

LANG_LABELS = {"tr": "🇹🇷 Türkçe", "en": "🇬🇧 English", "de": "🇩🇪 Deutsch"}


def _term_display(entry: dict, lang: str = "tr") -> tuple:
    """(ad, tanım, örnek) → seçilen dile göre."""
    if lang == "en":
        name = entry.get("term_en") or entry.get("term", "")
        defn = entry.get("definition_en") or entry.get("definition", "")
        ex = entry.get("example_en") or entry.get("example", "")
    elif lang == "de":
        name = entry.get("term_de") or entry.get("term_en") or entry.get("term", "")
        defn = (
            entry.get("definition_de") or entry.get("definition_en") or entry.get("definition", "")
        )
        ex = entry.get("example", "")
    else:
        name = entry.get("term", "")
        defn = entry.get("definition", "")
        ex = entry.get("example", "")
    return name, defn, ex


# ──────────────────────────────────────────────────────────────────────────────
# Strateji Veritabanı
# ──────────────────────────────────────────────────────────────────────────────

STRATEGY_DATA = {
    "Momentum Yatırımı": {
        "aciklama": "Yükselenin yükselmeye, düşenin düşmeye devam edeceği varsayımına dayanır.",
        "nasil_calisir": "Son 3-6-12 ayda en çok kazandıran hisseler alınır.",
        "finpilot_yorumu": "FinPilot tarama motoru, momentumu yüksek hisseleri tespit etmek için RSI ve Hareketli Ortalamalar kullanır.",
    },
    "Mean Reversion (Ortalamaya Dönüş)": {
        "aciklama": "Fiyatların aşırı saptıktan sonra eninde sonunda ortalamasına döneceği prensibidir.",
        "nasil_calisir": "Aşırı düşmüş (ucuzlamış) hisseler alınır, aşırı yükselmişler satılır.",
        "finpilot_yorumu": "FinPilot'un Z-Skoru analizi, fiyatın ortalamadan ne kadar saptığını ölçerek bu stratejiyi uygular.",
    },
    "Trend Takibi": {
        "aciklama": "Mevcut piyasa trendinin yönünde işlem yapmaktır.",
        "nasil_calisir": "Fiyat 200 günlük ortalamanın üzerindeyse alım, altındaysa satım/nakit pozisyonu korunur.",
        "finpilot_yorumu": "FinPilot 'Rejim Tespiti' modülü ile piyasanın trendini (Boğa/Ayı) otomatik belirler.",
    },
}

LEVEL_COLOR = {
    "Başlangıç": "🟢",
    "Orta": "🟡",
    "İleri": "🟠",
    "Uzman": "🔴",
}

LEVEL_ORDER = {"Başlangıç": 1, "Orta": 2, "İleri": 3, "Uzman": 4}


# ──────────────────────────────────────────────────────────────────────────────
# Bileşik Faiz Hesaplayıcı
# ──────────────────────────────────────────────────────────────────────────────


def render_compound_interest_calculator():
    st.markdown("### 🧮 Bileşik Faiz Hesaplayıcı")
    st.caption("Küçük tasarrufların zamanla nasıl büyüdüğünü görün.")

    col1, col2 = st.columns(2)
    with col1:
        initial_investment = st.number_input("Başlangıç Yatırımı (TL)", value=10000, step=1000)
        monthly_contribution = st.number_input("Aylık Ek Katkı (TL)", value=1000, step=100)
    with col2:
        interest_rate = st.number_input("Yıllık Beklenen Getiri (%)", value=25.0, step=1.0)
        years = st.slider("Yatırım Süresi (Yıl)", 1, 30, 10)

    months = years * 12
    monthly_rate = interest_rate / 100 / 12

    future_value = initial_investment * (1 + monthly_rate) ** months
    if monthly_rate > 0:
        future_value += monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)

    total_invested = initial_investment + (monthly_contribution * months)
    total_interest = future_value - total_invested

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Yatırılan", f"₺{total_invested:,.0f}")
    c2.metric("Kazanılan Getiri", f"₺{total_interest:,.0f}")
    c3.metric(
        "Gelecekteki Değer",
        f"₺{future_value:,.0f}",
        delta=f"%{((future_value / total_invested) - 1) * 100:.1f}",
    )

    data, balance, invested = [], initial_investment, initial_investment
    for m in range(1, months + 1):
        balance = balance * (1 + monthly_rate) + monthly_contribution
        invested += monthly_contribution
        if m % 12 == 0:
            data.append({"Yıl": m // 12, "Toplam Değer": balance, "Yatırılan Ana Para": invested})

    df_calc = pd.DataFrame(data)
    st.area_chart(
        df_calc.set_index("Yıl")[["Yatırılan Ana Para", "Toplam Değer"]],
        color=["#94a3b8", "#00e6e6"],
    )


# ──────────────────────────────────────────────────────────────────────────────
# Quiz Modülü (v2: dil desteği + zorluk filtresi)
# ──────────────────────────────────────────────────────────────────────────────


def render_quiz_module(terms, lang="tr"):
    st.markdown("### 🧠 Finansal Bilgi Yarışması")
    st.caption("Sözlükteki terimlerle bilginizi test edin.")

    qs_key = f"quiz_state_{lang}"
    if qs_key not in st.session_state:
        st.session_state[qs_key] = {
            "current_question": None,
            "score": 0,
            "total": 0,
            "answered": False,
            "feedback": "",
        }
    qs = st.session_state[qs_key]

    # Zorluk filtresi
    diff_filter = st.select_slider(
        "Zorluk",
        options=["Başlangıç", "Orta", "İleri", "Uzman"],
        value=("Başlangıç", "Uzman"),
        key=f"quiz_diff_{lang}",
    )
    min_lv = LEVEL_ORDER.get(diff_filter[0], 1)
    max_lv = LEVEL_ORDER.get(diff_filter[1], 4)
    eligible = [t for t in terms if min_lv <= LEVEL_ORDER.get(t.get("level", "Orta"), 2) <= max_lv]

    def next_question():
        if len(eligible) < 4:
            return
        correct = random.choice(eligible)
        distractors = random.sample(
            [
                t
                for t in eligible
                if t.get("slug", t["term"]) != correct.get("slug", correct["term"])
            ],
            3,
        )
        opts = [correct] + distractors
        random.shuffle(opts)
        qs["current_question"] = {"term": correct, "options": opts}
        qs["answered"] = False
        qs["feedback"] = ""

    if qs["current_question"] is None:
        next_question()

    q = qs["current_question"]
    if not q or len(eligible) < 4:
        st.warning("Bu zorluk seviyesinde yeterli terim yok. Lütfen filtreyi genişletin.")
        return

    correct_term = q["term"]
    _, defn, _ = _term_display(correct_term, lang)

    with st.container():
        st.markdown("#### 📖 Soru:")
        st.info(f'*"{defn}"*')
        st.caption("Bu tanım hangi terime aittir?")

    cols = st.columns(2)
    for i, opt in enumerate(q["options"]):
        opt_name, _, _ = _term_display(opt, lang)
        btn_key = f"opt_{lang}_{i}_{opt.get('slug', opt['term'])}"
        if cols[i % 2].button(
            opt_name.split("(")[0].strip(),
            key=btn_key,
            use_container_width=True,
            disabled=qs["answered"],
        ):
            qs["answered"] = True
            qs["total"] += 1
            correct_name, _, _ = _term_display(correct_term, lang)
            if opt.get("slug", opt["term"]) == correct_term.get("slug", correct_term["term"]):
                qs["score"] += 1
                qs["feedback"] = "✅ Doğru! Harika gidiyorsun."
            else:
                qs["feedback"] = f"❌ Yanlış. Doğru cevap: **{correct_name}**"
            st.rerun()

    if qs["answered"]:
        if "✅" in qs["feedback"]:
            st.success(qs["feedback"])
        else:
            st.error(qs["feedback"])
        if st.button("Sonraki Soru ➡️", type="primary", key=f"next_{lang}"):
            next_question()
            st.rerun()

    st.markdown("---")
    pct = int(qs["score"] / qs["total"] * 100) if qs["total"] else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Doğru", qs["score"])
    c2.metric("Toplam", qs["total"])
    c3.metric("Başarı", f"%{pct}")


# ──────────────────────────────────────────────────────────────────────────────
# Sözlük Kartı (v2: formül, etiket, zorluk, ilişkili terimler)
# ──────────────────────────────────────────────────────────────────────────────


def _render_term_card(term: dict, lang: str):
    name, defn, ex = _term_display(term, lang)
    lv = term.get("level", "Orta")
    icon = LEVEL_COLOR.get(lv, "⚪")
    diff = term.get("difficulty_score", "")
    tags = term.get("tags", [])
    formula = term.get("formula", "")
    related = term.get("related", [])
    synonyms = term.get("synonyms", [])

    with st.container():
        # Başlık satırı
        col_name, col_badge = st.columns([4, 1])
        with col_name:
            st.markdown(f"**{name}**")
            if lang != "tr" and term.get("term"):
                st.caption(f"🇹🇷 {term['term']}")
        with col_badge:
            st.markdown(f"{icon} `{lv}`")
            if diff:
                st.caption(f"⚡ {diff}/10")

        # Tanım
        st.markdown(defn)

        # Örnek
        if ex:
            st.caption(f"💡 *{ex}*")

        # Formül
        if formula:
            st.latex(formula)

        # Etiketler
        if tags:
            st.markdown(" ".join(f"`{t}`" for t in tags))

        # İlişkili terimler
        if related:
            st.markdown("🔗 " + " · ".join(f"*{r}*" for r in related[:5]))

        # Eş anlamlılar
        if synonyms:
            st.caption("≈ " + ", ".join(synonyms))

        st.markdown("---")


# ──────────────────────────────────────────────────────────────────────────────
# Ana Sayfa
# ──────────────────────────────────────────────────────────────────────────────


def render_finsense_page():
    st.markdown("## 🎓 FinSense: Finansal Okuryazarlık Akademisi")
    st.markdown("Finansal terimleri öğrenin, stratejileri çözün ve geleceğinizi hesaplayın.")

    tab_dict, tab_quiz, tab_strat, tab_calc = st.tabs(
        ["📚 İnteraktif Sözlük", "🧠 Quiz Modu", "🧩 Strateji Çözücü", "🧮 Hesaplayıcılar"]
    )

    terms = load_dictionary()

    # ── TAB 1: SÖZLÜK ─────────────────────────────────────────────────────────
    with tab_dict:
        if not terms:
            st.error(
                "Sözlük verisi bulunamadı. Lütfen 'data/dictionary_v2.json' dosyasını kontrol edin."
            )
        else:
            # Üst kontroller
            ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([3, 1, 1, 1])
            with ctrl1:
                search_query = st.text_input(
                    "🔍 Sözlükte Ara",
                    placeholder="Terim, tanım veya etiket ara...",
                    key="dict_search",
                ).lower()
            with ctrl2:
                all_levels = sorted(
                    {t.get("level", "Orta") for t in terms}, key=lambda x: LEVEL_ORDER.get(x, 0)
                )
                selected_levels = st.multiselect(
                    "Seviye", all_levels, default=all_levels, key="dict_levels"
                )
            with ctrl3:
                lang = st.selectbox(
                    "Dil", ["tr", "en", "de"], format_func=lambda x: LANG_LABELS[x], key="dict_lang"
                )
            with ctrl4:
                all_cats = sorted({t.get("category", "Genel") for t in terms})
                cat_filter = st.selectbox("Kategori", ["Tümü"] + all_cats, key="dict_cat")

            st.caption(f"📖 Toplam **{len(terms)}** terim · 🇹🇷 TR · 🇬🇧 EN · 🇩🇪 DE")
            st.divider()

            # Filtrele
            filtered = []
            for t in terms:
                if t.get("level", "Orta") not in selected_levels:
                    continue
                if cat_filter != "Tümü" and t.get("category") != cat_filter:
                    continue
                name, defn, _ = _term_display(t, lang)
                tags_str = " ".join(t.get("tags", []))
                if search_query and not any(
                    search_query in s.lower()
                    for s in [name, defn, t.get("term", ""), t.get("term_en", ""), tags_str]
                ):
                    continue
                filtered.append(t)

            if not filtered:
                st.info("Arama kriterlerine uygun terim bulunamadı.")
            else:
                # Kategori grupları
                cats_present = sorted({t.get("category", "Genel") for t in filtered})
                for category in cats_present:
                    cat_terms = [t for t in filtered if t.get("category") == category]
                    if not cat_terms:
                        continue
                    expanded = cat_filter != "Tümü" or len(cats_present) == 1
                    with st.expander(f"📌 {category} ({len(cat_terms)})", expanded=expanded):
                        cols = st.columns(2)
                        for i, term in enumerate(cat_terms):
                            with cols[i % 2]:
                                _render_term_card(term, lang)

    # ── TAB 2: QUIZ MODU ──────────────────────────────────────────────────────
    with tab_quiz:
        if not terms:
            st.warning("Quiz için yeterli veri yok.")
        else:
            quiz_lang = st.selectbox(
                "Quiz Dili",
                ["tr", "en", "de"],
                format_func=lambda x: LANG_LABELS[x],
                key="quiz_lang_select",
            )
            render_quiz_module(terms, lang=quiz_lang)

    # ── TAB 3: STRATEJİ ÇÖZÜCÜ ───────────────────────────────────────────────
    with tab_strat:
        st.markdown("### Algoritmalar Nasıl Düşünür?")
        st.caption("FinPilot'un arkasındaki mantığı ve popüler borsa stratejilerini anlayın.")

        for strat, info in STRATEGY_DATA.items():
            with st.container():
                st.markdown(f"#### ⚡ {strat}")
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown(f"**Nedir?** {info['aciklama']}")
                    st.markdown(f"**Nasıl Çalışır?** {info['nasil_calisir']}")
                with c2:
                    st.info(f"🤖 **FinPilot:** {info['finpilot_yorumu']}")
                st.divider()

    # ── TAB 4: HESAPLAYICI ────────────────────────────────────────────────────
    with tab_calc:
        render_compound_interest_calculator()

    # Alt bilgi
    st.markdown("---")
    st.caption(
        "ℹ️ Bu içerikler uluslararası finansal okuryazarlık standartlarına (OECD/INFE) uygun olarak hazırlanmıştır."
    )
    st.caption(
        "⚠️ **Yasal Uyarı:** FinPilot yalnızca eğitim ve bilgi amaçlıdır; yatırım tavsiyesi niteliği taşımaz. "
        "Yatırım kararlarınız tamamen size aittir. Geçmiş performans gelecekteki sonuçların garantisi değildir."
    )
