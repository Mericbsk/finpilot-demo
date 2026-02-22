"""
FinPilot Research
=================
Gemini/Groq API ile araştırma ve haber analizi.
"""

from textwrap import dedent

import logging

import streamlit as st
import yfinance as yf

# Optional imports
try:
    import google.generativeai as genai
    from duckduckgo_search import DDGS
    from groq import Groq
except ImportError:
    genai = None
    DDGS = None
    Groq = None


def get_yfinance_news(symbol: str, max_results: int = 5) -> list:
    """yfinance'dan haber çeker (fallback için)."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        results = []
        for item in news[:max_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "body": item.get("summary", item.get("title", "")),
                    "url": item.get("link", ""),
                    "date": item.get("providerPublishTime", ""),
                    "source": item.get("publisher", "Yahoo Finance"),
                }
            )
        return results
    except Exception as e:
        print(f"yfinance news error for {symbol}: {e}")
        return []


# Standart TTL: 300 saniye (tüm modüllerle uyumlu)
RESEARCH_CACHE_TTL = 300


@st.cache_data(ttl=RESEARCH_CACHE_TTL, show_spinner="🔍 Araştırma yapılıyor...")
def get_gemini_research(symbol: str, language: str = "tr") -> str:
    """
    Fetches research data using DuckDuckGo for news and Gemini/Groq for analysis.
    Requires GOOGLE_API_KEY or GROQ_API_KEY in st.secrets (environment variables deprecated).
    """
    if not genai or not DDGS:
        return "⚠️ Gerekli kütüphaneler (google-generativeai, duckduckgo-search) yüklü değil."

    # API key only from secrets (secure mode)
    api_key = None
    try:
        api_key = st.secrets.get("GOOGLE_API_KEY")
    except Exception:
        pass  # secrets not configured

    if not api_key:
        return (
            "⚠️ Google API anahtarı bulunamadı.\n\n"
            "**Güvenli Yapılandırma:**\n"
            "1. `.streamlit/secrets.toml` dosyası oluşturun\n"
            '2. `GOOGLE_API_KEY = "your-key-here"` ekleyin\n\n'
            "Not: Güvenlik nedeniyle environment variable desteği kaldırıldı."
        )

    try:
        # 1. DuckDuckGo ile Haber Arama (Çok Dilli: EN + DE + TR)
        results = []
        with DDGS() as ddgs:

            def safe_search(
                query: str,
                region: str = "wt-wt",
                timelimit: str | None = "w",
                max_results: int = 3,
            ) -> list:
                """Hata korumalı ve fallback mekanizmalı arama fonksiyonu"""
                try:
                    # 1. Deneme: İstenen zaman aralığında (örn: son 1 hafta)
                    res = list(
                        ddgs.news(
                            query,
                            region=region,
                            safesearch="off",
                            timelimit=timelimit,
                            max_results=max_results,
                        )
                    )
                    if res:
                        return res

                    # 2. Deneme (Fallback): Eğer sonuç yoksa zaman kısıtını kaldır
                    if timelimit:
                        return list(
                            ddgs.news(
                                query,
                                region=region,
                                safesearch="off",
                                timelimit=None,
                                max_results=max_results,
                            )
                        )
                except Exception as e:
                    print(f"DDG Arama Hatası ({query}): {e}")
                    return []
                return []

            # İngilizce Arama (Genel Finans)
            results.extend(
                safe_search(
                    f"{symbol} stock news finance", region="wt-wt", timelimit="w", max_results=5
                )
            )

            # Yasal ve Regülasyon (SEC, Davalar - Öncelik Son 1 Ay)
            results.extend(
                safe_search(
                    f"{symbol} sec filings lawsuit regulation",
                    region="wt-wt",
                    timelimit="m",
                    max_results=3,
                )
            )

            # Almanca Arama
            results.extend(
                safe_search(
                    f"{symbol} aktie finanzen", region="de-de", timelimit="w", max_results=2
                )
            )

            # Türkçe Arama
            results.extend(
                safe_search(
                    f"{symbol} hisse haber borsa", region="tr-tr", timelimit="w", max_results=3
                )
            )

            # Ek fallback: Şirket ismiyle arama (sembol yetersiz kalırsa)
            if len(results) < 3:
                # Yaygın şirket isimlerini dene
                company_names = {
                    "VRTX": "Vertex Pharmaceuticals",
                    "AMGN": "Amgen",
                    "GILD": "Gilead Sciences",
                    "REGN": "Regeneron",
                    "MRNA": "Moderna",
                    "BIIB": "Biogen",
                    "ILMN": "Illumina",
                }
                company_name = company_names.get(symbol)
                if company_name:
                    results.extend(
                        safe_search(
                            f"{company_name} news stock",
                            region="wt-wt",
                            timelimit="m",
                            max_results=5,
                        )
                    )

        # Son fallback: yfinance'dan haber çek
        if not results:
            yf_news = get_yfinance_news(symbol, max_results=5)
            if yf_news:
                results = yf_news

        if not results:
            return f"⚠️ {symbol} için kaynaklarda erişilebilir haber bulunamadı. (Bağlantı sorunu veya veri eksikliği olabilir)"

        # Tekrarlanan haberleri temizle (URL'ye göre)
        seen_urls: set[str] = set()
        unique_results = []
        for r in results:
            if r.get("url") not in seen_urls:
                unique_results.append(r)
                seen_urls.add(r.get("url"))

        # İlk 12 haberi al
        news_context = "\n\n".join(
            [
                f"Tarih: {r.get('date', 'Belirsiz')}\nBaşlık: {r['title']}\nKaynak: {r['source']}\nÖzet: {r['body']}"
                for r in unique_results[:12]
            ]
        )

        prompts = {
            "tr": f"""
            Sen uzman bir borsa ve hukuk analistisin. Aşağıdaki **güncel** haberleri (İngilizce, Almanca, Türkçe) kullanarak {symbol} hissesi için kapsamlı bir yatırımcı raporu hazırla.

            Özellikle **yasal gelişmeler, regülasyonlar, davalar ve resmi bildirimlere (SEC/KAP)** dikkat et. Haberlerin tarihlerini göz önünde bulundur ve eski haberleri ele.

            Haberler:
            {news_context}

            İstenen Format:
            1. **Piyasa Algısı:** (Olumlu/Olumsuz/Nötr - Nedenleriyle)
            2. **Yasal ve Regülatif Gelişmeler:** (Varsa davalar, cezalar, onaylar, başvurular)
            3. **Öne Çıkan Finansal Gelişmeler:** (Maddeler halinde)
            4. **Riskler ve Fırsatlar:**
            5. **Sonuç Yorumu:** (Yatırımcı ne yapmalı?)
            """,
            "en": f"""
            You are an expert stock market and legal analyst. Create a comprehensive investor report for {symbol} using the **recent** news below.

            Pay special attention to **legal developments, regulations, lawsuits, and official filings (SEC/KAP)**. Consider the dates of the news and filter out outdated information.

            News:
            {news_context}

            Required Format:
            1. **Market Sentiment:** (Bullish/Bearish/Neutral - With reasons)
            2. **Legal & Regulatory Developments:** (Lawsuits, fines, approvals, filings if any)
            3. **Key Financial Developments:** (Bullet points)
            4. **Risks & Opportunities:**
            5. **Conclusion:** (Actionable advice)
            """,
            "de": f"""
            Sie sind ein erfahrener Börsen- und Rechtsanalyst. Erstellen Sie einen umfassenden Investorenbericht für {symbol} unter Verwendung der folgenden **aktuellen** Nachrichten.

            Achten Sie besonders auf **rechtliche Entwicklungen, Vorschriften, Klagen und offizielle Meldungen**. Berücksichtigen Sie die Daten der Nachrichten.

            Nachrichten:
            {news_context}

            Gewünschtes Format:
            1. **Marktstimmung:** (Positiv/Negativ/Neutral)
            2. **Rechtliche & Regulatorische Entwicklungen:**
            3. **Wichtige Finanzentwicklungen:**
            4. **Risiken & Chancen:**
            5. **Fazit:**
            """,
        }

        prompt = prompts.get(language, prompts["tr"])

        # ------------------------------------------------------------------
        # V2 MİMARİSİ: GROQ CLOUD ENTEGRASYONU (HIZLI & LİMİTSİZ)
        # ------------------------------------------------------------------
        if Groq:
            try:
                # API key only from secrets (secure mode)
                GROQ_API_KEY = None
                try:
                    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
                except Exception:
                    logging.getLogger(__name__).debug("st.secrets unavailable", exc_info=True)

                if not GROQ_API_KEY:
                    return _generate_offline_report(
                        symbol,
                        unique_results,
                        language,
                        reason="GROQ_API_KEY st.secrets'de tanımlanmamış",
                    )

                client = Groq(api_key=GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Updated: llama3-70b-8192 deprecated
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a senior financial analyst. Answer in Markdown.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                    max_tokens=2048,
                    top_p=1,
                    stream=False,
                    stop=None,
                )
                return completion.choices[0].message.content or ""
            except Exception as groq_error:
                return _generate_offline_report(
                    symbol,
                    unique_results,
                    language,
                    reason=f"Groq API Hatası: {str(groq_error)}",
                )
        else:
            return _generate_offline_report(
                symbol, unique_results, language, reason="Groq Kütüphanesi Yüklü Değil"
            )

    except Exception as e:
        error_msg = str(e)

        if Groq and "groq" in error_msg.lower():
            return f"⚠️ Groq Bağlantı Hatası: {error_msg}. (Offline moduna geçildi)"

        if "429" in error_msg or "ResourceExhausted" in error_msg:
            return _generate_offline_report(symbol, [], language, reason="API Kotası Doldu")

        return _generate_offline_report(symbol, [], language, reason=f"Hata: {error_msg}")


def _generate_offline_report(
    symbol: str, news_items: list, language: str, reason: str | None = None
) -> str:
    """Gemini API limitine takılınca çalışan basit yedek raporlayıcı."""

    headers = {
        "tr": ["Piyasa Algısı", "Son Haber Özeti", "Riskler & Fırsatlar"],
        "en": ["Market Sentiment", "Recent News Summary", "Risks & Opportunities"],
        "de": ["Marktstimmung", "Zusammenfassung aktueller Nachrichten", "Risiken & Chancen"],
    }
    h = headers.get(language, headers["tr"])

    positive_keywords = [
        "surge",
        "jump",
        "high",
        "profit",
        "growth",
        "yükseldi",
        "rekor",
        "kar",
        "büyüme",
        "buy",
        "al",
        "olumlu",
    ]
    negative_keywords = [
        "drop",
        "fall",
        "loss",
        "crash",
        "düşüş",
        "zarar",
        "kriz",
        "sat",
        "sell",
        "olumsuz",
        "lawsuit",
        "dava",
    ]

    combined_text = " ".join([n["title"].lower() + " " + n["body"].lower() for n in news_items])
    pos_count = sum(1 for k in positive_keywords if k in combined_text)
    neg_count = sum(1 for k in negative_keywords if k in combined_text)

    if pos_count > neg_count:
        sentiment = "🟢 Pozitif / Bullish" if language == "tr" else "🟢 Positive / Bullish"
    elif neg_count > pos_count:
        sentiment = "🔴 Negatif / Bearish" if language == "tr" else "🔴 Negative / Bearish"
    else:
        sentiment = "⚪ Nötr / Neutral" if language == "tr" else "⚪ Neutral"

    reason_text = f" ({reason})" if reason else ""

    report = f"""
    ### ⚠️ AI Limit Modu (Offline & Fallback)
    *Yapay Zeka bağlantısı sağlanamadığı için (Groq/Gemini), bu rapor haberlerin otomatik özetlenmesiyle oluşturulmuştur.*
    *{reason_text if reason else ""}*

    #### 1. {h[0]}
    **{sentiment}**
    (Pozitif Anahtar Kelimeler: {pos_count}, Negatif: {neg_count})

    #### 2. {h[1]}
    """

    for item in news_items[:8]:
        report += f"- **{item['date']}**: {item['title']} ({item['source']})\n"

    report += f"""
    #### 3. {h[2]}
    - **Fırsat:** Haber akışına göre kısa vadeli volatilite değerlendirilebilir.
    - **Risk:** Otomatik analiz şu an devre dışı olduğu için manuel inceleme önerilir.
    """

    return dedent(report)
