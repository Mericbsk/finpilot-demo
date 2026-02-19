import streamlit as st

from .utils import trigger_rerun


def render_finpilot_landing():
    hero_section = """
        <div class='layout-grid'>
            <div style='background: linear-gradient(100deg,#131b2b 55%,#1e2b40 100%); border-radius:24px; padding:50px 36px; margin-bottom:36px; box-shadow:0 24px 60px -32px rgba(8,47,73,0.65);'>
                <div style='display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:32px;'>
                    <div style='flex:2; min-width:290px;'>
                        <span style='font-size:3em; font-weight:800; color:#00e6e6; letter-spacing:0.02em;'>FinPilot</span><br>
                        <span style='font-size:1.6em; font-weight:500; color:#f8fafc;'>Yapay zekâ destekli alım-satım ve eğitim kokpitin.</span><br>
                        <span style='font-size:1.1em; color:rgba(186,228,236,0.92);'>Riskini yönet, fırsatları yakala, finansal okuryazarlığını geliştir.</span>
                        <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:18px; margin-top:28px;'>
                            <div style='background:rgba(30,41,59,0.65); border-radius:16px; padding:20px 22px;'>
                                <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                                    <span style='font-size:2rem;'>⚡</span>
                                    <div style='font-size:1.1rem; font-weight:600; color:#38bdf8;'>Anlık Tarama Motoru</div>
                                </div>
                                <ul style='list-style:disc; margin:0; padding-left:1.2rem; color:#cbd5f5; font-size:0.96rem; line-height:1.55;'>
                                    <li>500+ sembolü saniyeler içinde ML modelleriyle tarar.</li>
                                    <li>Likit segment ve momentum eşikleri otomatik kalibre edilir.</li>
                                    <li>Gürültüyü azaltan adaptif filtre sonucu net sinyaller sunar.</li>
                                </ul>
                            </div>
                            <div style='background:rgba(30,41,59,0.65); border-radius:16px; padding:20px 22px;'>
                                <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                                    <span style='font-size:2rem;'>🎓</span>
                                    <div style='font-size:1.1rem; font-weight:600; color:#a78bfa;'>FinSense Akademi</div>
                                </div>
                                <ul style='list-style:disc; margin:0; padding-left:1.2rem; color:#cbd5f5; font-size:0.96rem; line-height:1.55;'>
                                    <li>100+ terimlik kapsamlı finansal sözlük ve bilgi bankası.</li>
                                    <li>İnteraktif quiz modülü ile piyasa bilginizi test edin.</li>
                                    <li>Teknik, Temel ve Psikoloji kategorilerinde uzmanlaşın.</li>
                                </ul>
                            </div>
                            <div style='background:rgba(30,41,59,0.65); border-radius:16px; padding:20px 22px;'>
                                <div style='display:flex; align-items:center; gap:12px; margin-bottom:12px;'>
                                    <span style='font-size:2rem;'>📊</span>
                                    <div style='font-size:1.1rem; font-weight:600; color:#fbbf24;'>Şeffaf Analitik Kokpiti</div>
                                </div>
                                <ul style='list-style:disc; margin:0; padding-left:1.2rem; color:#cbd5f5; font-size:0.96rem; line-height:1.55;'>
                                    <li>Her sinyalin metrik ve veri kaynağı tek kartta görünür.</li>
                                    <li>Backtest ve canlı performans sonuçları aynı ekranda izlenir.</li>
                                    <li>Sentiment &amp; on-chain verileriyle fikirlerini hızla doğrularsın.</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    <div style='flex:1; min-width:260px; display:flex; flex-direction:column; align-items:center; justify-content:center;'>
                        <div style='background:rgba(30,41,59,0.4); padding:20px; border-radius:20px; border:1px solid rgba(255,255,255,0.1); text-align:center;'>
                            <h3 style='color:#fff; margin-bottom:10px;'>Hemen Başla</h3>
                            <p style='color:#cbd5f5; font-size:0.9em; margin-bottom:20px;'>Kayıt olmadan demo modunu deneyebilir veya tam sürüme geçebilirsiniz.</p>
                            <div style='font-size:3rem; margin-bottom:10px;'>🚀</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """

    features_section = """
        <div class='layout-grid'>
            <div style='display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:24px; margin-bottom:40px;'>
                <div class='feature-card' style='background:rgba(15,23,42,0.75); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(14,165,233,0.45);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>🧠</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#38bdf8;'>Akıllı Strateji Motoru</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#cbd5f5; font-size:0.98rem; line-height:1.6;'>
                        <li>Trend, momentum ve hacmi birlikte puanlayan ML/DRL orkestrasyonu.</li>
                        <li>Regime &amp; segment bazlı eşikler ile yanlış pozitifler azalır.</li>
                        <li>Her taramada yeni veriye göre skorlar anında yeniden kalibre edilir.</li>
                    </ul>
                </div>
                <div class='feature-card' style='background:rgba(23,32,48,0.78); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(34,197,94,0.45);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>🧭</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#4ade80;'>Risk &amp; Sermaye Kılavuzu</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#d1fae5; font-size:0.98rem; line-height:1.6;'>
                        <li>Kelly fraksiyonu, ATR ve volatilite ile uyumlu pozisyon boyutları.</li>
                        <li>Anlık risk/ödül hesaplarıyla stop &amp; hedefler aynı ekranda.</li>
                        <li>Portföy yoğunluğu ve korelasyon uyarılarıyla aşırı risk engellenir.</li>
                    </ul>
                </div>
                <div class='feature-card' style='background:rgba(24,31,48,0.78); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(251,191,36,0.4);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>🔍</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#fbbf24;'>Şeffaf Sonuç Raporu</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#fde68a; font-size:0.98rem; line-height:1.6;'>
                        <li>Her sinyal kartında kullanılan veri ve skor bileşenleri açıkça listelenir.</li>
                        <li>Backtest, canlı performans ve alternatif veriler tek kokpitte.</li>
                        <li>Paylaşılabilir rapor ve uyarılar ekip içinde aksiyona dönüşür.</li>
                    </ul>
                </div>
                <div class='feature-card' style='background:rgba(30,27,75,0.78); border-radius:18px; padding:26px 24px; box-shadow:0 22px 52px -32px rgba(167,139,250,0.4);'>
                    <div style='display:flex; align-items:center; gap:14px; margin-bottom:16px;'>
                        <span style='font-size:2.2rem;'>📚</span>
                        <h4 style='margin:0; font-size:1.2rem; color:#a78bfa;'>FinSense Akademi</h4>
                    </div>
                    <ul style='margin:0; padding-left:1.3rem; color:#e9d5ff; font-size:0.98rem; line-height:1.6;'>
                        <li>Finansal okuryazarlığınızı artıracak kapsamlı sözlük.</li>
                        <li>Bilgilerinizi test edebileceğiniz interaktif quiz modu.</li>
                        <li>Yatırımcı psikolojisi ve teknik analiz eğitimleri.</li>
                    </ul>
                </div>
            </div>
        </div>
        """

    checklist_html = """
        <div class='layout-grid'>
            <div class='action-checklist'>
                <h3>📋 Pilot'un Aksiyon Kontrol Listesi</h3>
                <p class='lead'>Analiz sonrası hangi adımları atacağını saniyeler içinde hatırla. FinSense bu panelde seninle birlikte.</p>
                <div class='checklist-grid'>
                    <div class='bucket'>
                        <h4><span>🛠️</span>Eylemsel Basitleştirme</h4>
                        <ul>
                            <li><span class='icon'>✅</span> Kural basit: Yeşil sinyalleri (AL) R/R oranına göre filtrele.</li>
                            <li><span class='icon'>⏱️</span> Stop-Loss ve Take-Profit seviyelerini belirle, beklemeye geç.</li>
                        </ul>
                    </div>
                    <div class='bucket'>
                        <h4><span>🛫</span>Uçuş Öncesi Kontrol</h4>
                        <ul>
                            <li><span class='icon'>🟢</span> Yeşil (AL) sinyalleri filtrele.</li>
                            <li><span class='icon'>🏆</span> Kazananları önce listele.</li>
                            <li><span class='icon'>📈</span> R/R &gt; 2.0 fırsatlara odaklan.</li>
                            <li><span class='icon'>📝</span> Stop-Loss ve Take-Profit seviyeni kaydet.</li>
                        </ul>
                    </div>
                    <div class='bucket'>
                        <h4><span>💡</span>Yardım &amp; İpuçları</h4>
                        <ul>
                            <li><span class='icon'>🛡️</span> R/R oranı kontrolü (PilotShield önerisi).</li>
                            <li><span class='icon'>🌙</span> Piyasalar kapalıyken stop-loss güncelleme hatırlatması.</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        """

    st.markdown(hero_section, unsafe_allow_html=True)
    st.markdown(features_section, unsafe_allow_html=True)
    st.markdown(checklist_html, unsafe_allow_html=True)

    action_cols = st.columns([1, 1, 1])
    with action_cols[1]:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🚀 Panele Geç", key="landing_enter_panel", use_container_width=True):
                st.session_state.has_seen_landing = True
                trigger_rerun()
        with c2:
            if st.button("🎯 Canlı Demo", key="landing_enter_demo", use_container_width=True):
                st.session_state.has_seen_landing = True
                st.session_state.current_page = "demo"
                trigger_rerun()

    st.caption(
        "🎉 Bu tanıtım ekranı sadece ilk oturumda gösterilir. Tekrar görmek için tarayıcı önbelleğini temizleyin."
    )
    st.caption(
        "⚠️ **Yasal Uyarı:** FinPilot yalnızca eğitim ve bilgi amaçlıdır; yatırım tavsiyesi niteliği taşımaz. "
        "Yatırım kararlarınız tamamen size aittir. Geçmiş performans gelecekteki sonuçların garantisi değildir."
    )
    st.stop()
