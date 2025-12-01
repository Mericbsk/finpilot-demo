# FinPilot: Proje Durum Analizi ve Stratejik Yol Haritası
**Tarih:** 28 Kasım 2025  
**Durum:** Beta Aşaması (MVP+)

---

## 1. Yönetici Özeti (Executive Summary)
**Vizyon:** Bireysel yatırımcılar için kurumsal kalitede, Yapay Zeka destekli ve anlaşılır bir finansal analiz terminali oluşturmak. "Bloomberg Terminali'nin herkes için olan versiyonu."

**Mevcut Durum:** 
- Streamlit tabanlı çalışan bir MVP (Minimum Viable Product) var.
- Kullanıcılar hisse tarayabiliyor, teknik analiz yapabiliyor ve AI destekli raporlar alabiliyor.
- Web sitesi (Landing Page) ve Beta kayıt sistemi aktif.

**Temel Farklılaşma (USP):** 
- **FinPilot Edge:** Sadece teknik veri değil, piyasadan "ayrışma" puanı sunması.
- **Hibrit Analiz:** Klasik indikatörleri (RSI, MACD) modern AI yorumlarıyla (Gemini/LLM) birleştirmesi.

---

## 2. Teknoloji Yığını (Tech Stack) & Altyapı

| Katman | Teknoloji | Durum | Değerlendirme |
| :--- | :--- | :--- | :--- |
| **Frontend** | Streamlit (Python) | 🟢 Aktif | Hızlı prototipleme için mükemmel, ancak yüksek trafikte ölçeklenme sorunu yaşatabilir. |
| **Backend** | Python (Pandas, NumPy) | 🟢 Aktif | Veri bilimi için endüstri standardı. Güçlü ve esnek. |
| **Veri Kaynağı** | yfinance (Yahoo) | 🟡 Riskli | Ücretsiz ve geniş kapsamlı ama 15dk gecikmeli ve stabilite garantisi yok. |
| **Yapay Zeka** | Google Gemini + DuckDuckGo | 🟢 Güçlü | Güncel haber tarama ve yorumlama yeteneği çok yüksek. |
| **Web (Landing)** | HTML5, CSS3, JS, PHP | 🟢 Tamam | Hafif, hızlı ve SEO dostu. Email servisi kendi sunucumuzda. |
| **Analiz Motoru** | TA-Lib, Custom Algo | 🟢 İyi | Teknik indikatörler ve rejim tespiti başarılı çalışıyor. |

---

## 3. Ticaret Stratejisi ve Algoritmalar

### Mevcut Strateji: "Akıllı Trend Takipçisi"
Sistem şu an **Momentum** ve **Trend** odaklı çalışıyor.
1.  **Filtreleme:** Hacim artışı ve hareketli ortalama (EMA) üzerinde olan hisseleri seçiyor.
2.  **Rejim Tespiti:** Piyasanın "Yükseliş", "Düşüş" veya "Yatay" olduğunu algılayıp stratejiyi ona göre değiştiriyor.
3.  **Risk Yönetimi (ATR):** 
    - Stop Loss: `2 x ATR` (Gürültüden kaçınmak için geniş).
    - Take Profit: `4 x ATR` (Risk/Ödül Oranı ~2).

### Tespit Edilen Eksiklikler & Fırsatlar
- **R/R Oranı:** Mevcut 2:1 oranı güvenli ama "zengin edici" değil. Bunu 3:1 veya 4:1 seviyesine çekecek "Sniper Modu" (Dar Stop, Uzun Hedef) eklenmeli.
- **Çoklu Zaman Dilimi:** Şu an ağırlıklı olarak Günlük/4 Saatlik bakıyor. "Multi-timeframe analysis" (Örn: Haftalıkta trend, 15dk'da giriş) eklenmeli.

---

## 4. SWOT Analizi (Güçlü/Zayıf Yönler)

### 💪 Güçlü Yönler (Strengths)
- **UX/UI:** Yeni "Hibrit Görünüm" ve interaktif tablolar rakiplerden (TradingView vb.) daha temiz ve odaklı.
- **AI Entegrasyonu:** Haberleri ve teknik veriyi birleştirip "insan gibi" konuşabilen raporlama sistemi.
- **Maliyet:** Şu anki altyapı maliyeti (Hosting + API) çok düşük.

### ⚠️ Zayıf Yönler (Weaknesses)
- **Veri Kalitesi:** `yfinance` profesyonel kullanım için yetersiz kalabilir.
- **Kullanıcı Yönetimi:** Henüz bir "Üyelik/Login" sistemi yok. Herkes aynı paneli görüyor.
- **Mobil Deneyim:** Streamlit mobilde çalışsa da "Native App" hissi vermiyor.

### 🚀 Fırsatlar (Opportunities)
- **SaaS Modeli:** Aylık abonelik ile "Premium Veri" ve "Sınırsız AI Analizi" satılabilir.
- **Sosyal Trading:** Kullanıcıların başarılı sinyalleri paylaşabileceği bir yapı.
- **Broker Entegrasyonu:** "Al" butonuna basınca doğrudan aracı kurumdan işlem yapabilme.

### 🌪️ Tehditler (Threats)
- **API Maliyetleri:** Kullanıcı sayısı artarsa LLM (Gemini/OpenAI) maliyetleri artabilir.
- **Yasal Düzenlemeler:** "Yatırım Tavsiyesi" (SPK/SEC) kurallarına dikkat edilmeli. (Uyarı metinleri mevcut ama hukuki altyapı güçlendirilmeli).

---

## 5. Gelecek Yol Haritası (Roadmap)

### Faz 1: Stabilizasyon (1-2 Ay)
- [ ] **Veri Sağlayıcı:** Polygon.io veya FMP gibi profesyonel bir API'ye geçiş.
- [ ] **Login Sistemi:** Firebase veya Supabase ile kullanıcı girişi ve favori listesi kaydetme.
- [ ] **Strateji Güncellemesi:** Tartıştığımız R/R 3:1 oranlı "Kademeli Kar Al" sisteminin koda dökülmesi.

### Faz 2: Ticarileşme (3-6 Ay)
- [ ] **Ödeme Sistemi:** Stripe/Iyzico entegrasyonu.
- [ ] **Bildirim Sistemi:** Telegram botunun panel ile tam entegre çalışması (Sinyal gelince cebe bildirim).
- [ ] **Backtest Motoru:** Kullanıcıların kendi stratejilerini geçmiş veride test edebilmesi.

### Faz 3: Ölçeklenme (6+ Ay)
- [ ] **Teknoloji Göçü:** Streamlit'ten React/Next.js (Frontend) + FastAPI (Backend) yapısına geçiş.
- [ ] **Mobil Uygulama:** iOS ve Android için native uygulama.

---

## 6. Sonuç ve Öneri
FinPilot, bir "Hobi Projesi" olmaktan çıkıp ticari bir ürüne dönüşme potansiyeline sahip. En kritik adım, **Veri Güvenilirliğini** sağlamak ve **Kullanıcıyı İçeri Almak (Login)** olacaktır.

**Önerilen İlk Aksiyon:** Strateji algoritmasını güncelleyip (R/R artırımı), profesyonel veri sağlayıcısı maliyetlerini araştırmaya başlamak.
