import json
import os
import random

import pandas as pd
import streamlit as st

# Finansal Okuryazarlık Sözlüğü Veri Seti
# JSON dosyasından yüklenir


def load_dictionary():
    file_path = os.path.join("data", "dictionary.json")
    try:
        with open(file_path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def _term_display(term_entry: dict, lang: str = "tr") -> tuple:
    """Return (display_name, definition, example) respecting language preference."""
    if lang == "en":
        name = term_entry.get("term_en", term_entry["term"])
        defn = term_entry.get("definition_en", term_entry["definition"])
    else:
        name = term_entry["term"]
        defn = term_entry["definition"]
    return name, defn, term_entry.get("example", "")


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

    # Hesaplama
    months = years * 12
    monthly_rate = interest_rate / 100 / 12

    future_value = initial_investment * (1 + monthly_rate) ** months
    future_value += monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)

    total_invested = initial_investment + (monthly_contribution * months)
    total_interest = future_value - total_invested

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Yatırılan", f"₺{total_invested:,.0f}")
    c2.metric("Kazanılan Faiz/Getiri", f"₺{total_interest:,.0f}", delta_color="normal")
    c3.metric(
        "Gelecekteki Değer",
        f"₺{future_value:,.0f}",
        delta=f"%{((future_value / total_invested) - 1) * 100:.1f}",
    )

    # Grafik
    data = []
    balance = initial_investment
    invested = initial_investment
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


def render_quiz_module(terms):
    st.markdown("### 🧠 Finansal Bilgi Yarışması")
    st.caption("Sözlükteki terimlerle bilginizi test edin.")

    if "quiz_state" not in st.session_state:
        st.session_state.quiz_state = {
            "current_question": None,
            "score": 0,
            "total": 0,
            "answered": False,
            "feedback": "",
        }

    def next_question():
        if not terms:
            return

        correct_term = random.choice(terms)
        distractors = random.sample([t for t in terms if t["term"] != correct_term["term"]], 3)
        options = [correct_term] + distractors
        random.shuffle(options)

        st.session_state.quiz_state["current_question"] = {"term": correct_term, "options": options}
        st.session_state.quiz_state["answered"] = False
        st.session_state.quiz_state["feedback"] = ""

    if st.session_state.quiz_state["current_question"] is None:
        next_question()

    q = st.session_state.quiz_state["current_question"]

    if q:
        with st.container():
            st.markdown("#### Soru:")
            st.info(f'"{q["term"]["definition"]}"')
            st.caption("Bu tanım hangi terime aittir?")

        cols = st.columns(2)
        for i, opt in enumerate(q["options"]):
            btn_key = f"opt_{i}_{opt['term']}"
            if cols[i % 2].button(
                opt["term"].split("(")[0].strip(),
                key=btn_key,
                use_container_width=True,
                disabled=st.session_state.quiz_state["answered"],
            ):
                st.session_state.quiz_state["answered"] = True
                st.session_state.quiz_state["total"] += 1
                if opt["term"] == q["term"]["term"]:
                    st.session_state.quiz_state["score"] += 1
                    st.session_state.quiz_state["feedback"] = "✅ Doğru! Harika gidiyorsun."
                else:
                    st.session_state.quiz_state["feedback"] = (
                        f"❌ Yanlış. Doğru cevap: **{q['term']['term']}**"
                    )
                st.rerun()

        if st.session_state.quiz_state["answered"]:
            if "✅" in st.session_state.quiz_state["feedback"]:
                st.success(st.session_state.quiz_state["feedback"])
            else:
                st.error(st.session_state.quiz_state["feedback"])

            if st.button("Sonraki Soru ➡️", type="primary"):
                next_question()
                st.rerun()

        st.markdown("---")
        st.metric(
            "Skor",
            f"{st.session_state.quiz_state['score']} / {st.session_state.quiz_state['total']}",
        )


def render_finsense_page():
    """
    FinSense Eğitim Modülü arayüzünü çizer.
    """
    st.markdown("## 🎓 FinSense: Finansal Okuryazarlık Akademisi")
    st.markdown("Finansal terimleri öğrenin, stratejileri çözün ve geleceğinizi hesaplayın.")

    tab_dict, tab_quiz, tab_strat, tab_calc = st.tabs(
        ["📚 İnteraktif Sözlük", "🧠 Quiz Modu", "🧩 Strateji Çözücü", "🧮 Hesaplayıcılar"]
    )

    terms = load_dictionary()

    # --- TAB 1: SÖZLÜK ---
    with tab_dict:
        if not terms:
            st.error(
                "Sözlük verisi bulunamadı. Lütfen 'data/dictionary.json' dosyasını kontrol edin."
            )
        else:
            # Filtreleme Alanı
            col_search, col_filter = st.columns([2, 1])
            with col_search:
                search_query = st.text_input(
                    "🔍 Sözlükte Ara", placeholder="Örn: Enflasyon, Hisse, Risk..."
                ).lower()
            with col_filter:
                all_levels = sorted({t["level"] for t in terms})
                selected_levels = st.multiselect("Seviye Filtrele", all_levels, default=all_levels)

            # Kategorilere Göre Grupla
            categories = sorted({t["category"] for t in terms})

            for category in categories:
                # Kategoriye ait terimleri filtrele
                category_terms = [
                    t
                    for t in terms
                    if t["category"] == category
                    and t["level"] in selected_levels
                    and (
                        search_query in t["term"].lower() or search_query in t["definition"].lower()
                    )
                ]

                if category_terms:
                    with st.expander(f"📌 {category} ({len(category_terms)})", expanded=True):
                        cols = st.columns(2)
                        for i, term in enumerate(category_terms):
                            with cols[i % 2]:
                                st.markdown(f"**{term['term']}** · `{term['level']}`")
                                st.markdown(f"{term['definition']}")
                                st.caption(f"💡 Örnek: {term['example']}")
                                # E2: Related terms
                                related = term.get("related", [])
                                if related:
                                    st.markdown("🔗 " + " · ".join(f"*{r}*" for r in related))
                                st.markdown("---")

    # --- TAB 2: QUIZ MODU ---
    with tab_quiz:
        if terms:
            render_quiz_module(terms)
        else:
            st.warning("Quiz için yeterli veri yok.")

    # --- TAB 3: STRATEJİ ÇÖZÜCÜ ---
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

    # --- TAB 4: HESAPLAYICI ---
    with tab_calc:
        render_compound_interest_calculator()

    # Alt Bilgi — yasal uyarı (R7)
    st.markdown("---")
    st.caption(
        "ℹ️ Bu içerikler uluslararası finansal okuryazarlık standartlarına (OECD/INFE) uygun olarak hazırlanmıştır."
    )
    st.caption(
        "⚠️ **Yasal Uyarı:** FinPilot yalnızca eğitim ve bilgi amaçlıdır; yatırım tavsiyesi niteliği taşımaz. "
        "Yatırım kararlarınız tamamen size aittir. Geçmiş performans gelecekteki sonuçların garantisi değildir."
    )
