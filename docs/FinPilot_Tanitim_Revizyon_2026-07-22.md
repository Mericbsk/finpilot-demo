# FinPilot Tanıtım Revizyonu v2 — Eskimiş İçerik Denetimi + Yeni Tanıtım
**22.07.2026 · Kaynaklar: NVIDIA deck (Mart 2026), Nihai Kontrol Özeti (15.07), Master Tasarım Ledger×Classroom (05.07), Uçtan Uca Ürün Planı (05.07), Morning Ledger Landing Planı (13.07)**

---

## 1. ZAYIF YANLAR: Eski Tanıtım vs Programın Bugünkü Hali

Program Mart'tan bu yana **kimlik değiştirdi**; tanıtım materyalleri bu dönüşümün gerisinde kaldı. Somut envanter:

| # | Eski materyaldeki ifade | Temmuz 2026 gerçeği | Yapılacak |
|---|---|---|---|
| 1 | "15 DRL agents generate buy/sell/hold signals" — ürünün kalbi | DRL **"Labs — experimental"** rafına kaldırıldı; üretim motoru volatilite-farkındalıklı **V2 faktör skoru** (short interest, gap, RVOL, ATR) | DRL'i "Ar-Ge hattı / gelecek katmanı" olarak anlat, çekirdek diye değil |
| 2 | "RSI · MACD · EMA · Bollinger" rozetleri | 15.07 nihai raporu: **RSI/MACD ve risk/ödül skoru değersiz çıktı**; legacy composite "KIRIK" (monotonluk 0.44) ve emekli ediliyor | Bu göstergeleri tanıtımdan tamamen çıkar — teknik jüri önünde ciddi kredibilite riski |
| 3 | "Real-time signals", "buy/sell alerts", stop/TP dili | Yeni ürün ilkesi: **kullanıcı yüzeyinde BUY/SELL, hedef fiyat, getiri vaadi YOK**; tek dil "Grade A/B/C + kalibre olasılık bandı + gerekçe" | Compliance-by-design'ı zayıflık değil, **satış argümanı** yap |
| 4 | "Sharpe 0.057 → hedef 0.5" | Ölçüm çerçevesi değişti: **açık karne** (hit = 5 günde ≥%5; grade bazında isabet), locked-OOS, triple-barrier gerçek P&L | Sharpe anlatısını at; kalibrasyon/karne metriklerini koy |
| 5 | "500+ stocks", Streamlit dashboard | **1.800+ ABD hissesi**, her sabah 07:45 Viyana; Next.js "Morning Ledger" public yüzey + "Reader's Desk" dashboard | Sayıları ve mimariyi güncelle |
| 6 | 56K LOC, 493 test, 195 modül | Sayılar eski; ayrıca vanity metrik | Tek satır "engineering maturity" + asıl kanıt: ~30 backtest'lik doğrulama bataryası, 5.000+ çözümlenmiş arşiv sinyali |
| 7 | Roadmap "Q2 2026 GPU acceleration", GB10 "purchasing" | Q2 geçti; ürün yönü Ledger×Classroom lansmanına döndü | Roadmap'i bugünden ileri yeniden kur |
| 8 | "BrokeAI landing page" | İsim terk edildi | Tüm kalıntıları temizle |
| 9 | Eğitim = "100+ terim, quiz, hesaplayıcı" | FinSense artık **12 alan, 2 öğrenme yolu, 120+ terim, gerçek vakalardan üretilen dersler, kalibrasyon antrenörü, kör-nokta haritası** | "Impact engine" konumlandırması (aşağıda) |
| 10 | ⚠️ "Open scorecard" iddiası | **Veri gerçeği:** signals_archive 22.05.2026'da donmuş, resolver çalışmıyor, karne boş | Tanıtımda açık karneyi vitrine koymadan önce **zinciri canlandır** — jüri/demo öncesi şart |

**Özet teşhis:** Eski tanıtım "AI sinyal üreticisi" anlatıyor; bugünkü ürün "kendini notlayan, öğreten, compliance-gömülü araştırma gazetesi + karar destek altyapısı". İkincisi hem daha savunulabilir hem de hibe programları için çok daha güçlü.

---

## 2. Yeni Konumlandırma Çerçevesi (sizin tanımınız üzerine)

1. **Çatı cümle:** Bireysel yatırımcı için *kurumsal seviye analitik ve karar destek altyapısı* — ileride hem **finansal eğitmen** hem **bireysel finansal danışman**.
2. **Deep-tech/Ar-Ge vurgusu:** Doğrulama disiplini (locked-OOS, triple-barrier execution replay, cluster-bootstrap, gerçekçi maliyet, shadow validation) + faktör araştırması + multi-agent DRL araştırma hattı. "Precision ≠ P&L" dersini öğrenmiş, kendi hatalarını yakalayan bir araştırma kültürü — jüriye anlatılacak asıl teknoloji hikâyesi bu.
3. **Regtech/compliance + güvenlik katmanı:** Tavsiye dili yok; config hash + zaman damgası + arşiv ile denetlenebilirlik; GDPR temeli; gizlilik-öncelikli yerel AI planı. MiFID uyum hazırlığı yol haritasında.
4. **FinSense = Impact Engine:** Otomatik içerik üreten (her günün gerçek verisi ders olur), kullanıcıyı sürekli eğiten (kalibrasyon antrenörü, kör-nokta haritası), zamanla kendi kendini geliştiren (arşiv büyüdükçe vaka kütüphanesi büyür) **etkileşimli finansal okuryazarlık laboratuvarı**. aws Innovative Solutions'ın "eğitim" etki alanına da doğrudan köprü.
5. **Vizyon bugüne bağlı:** "Şu anda MVP'deyiz, hedefimiz X" formülü (tanıtım metninin son paragrafı).

---

## 3. YENİ KISA TANITIM

### Türkçe

> **FinPilot — Bireysel Yatırımcı için Kurumsal Seviye Analitik ve Karar Destek Altyapısı**
>
> FinPilot, Viyana'da geliştirilen ve uzun vadede hem bir **finansal eğitmen** hem de **bireysel finansal danışman** olmak üzere tasarlanmış bir yapay zekâ platformudur.
>
> Bugünkü ürün, "The Morning Ledger": her sabah 07:45'te 1.800+ ABD hissesini tarayan, adayları kalibre edilmiş olasılık bantlarıyla **A/B/C araştırma notuna** dönüştüren ve her sonucu — ıskalamalar dahil — **açık karnede** yayımlayan bir motor. Skorlama, Ar-Ge disiplinimizin ürünüdür: volatilite-farkındalıklı faktör motoru (short interest, gap, RVOL, ATR), locked out-of-sample doğrulama, triple-barrier execution replay, gerçekçi maliyet modeli ve shadow-validation süreciyle test edilir. Multi-agent derin pekiştirmeli öğrenme (DRL) hattımız, bu doğrulama çıtasını geçecek modellerin geliştirildiği araştırma laboratuvarımızdır.
>
> **Regtech ve güvenlik mimariye gömülüdür:** kullanıcı yüzeyinde al/sat tavsiyesi, hedef fiyat veya getiri vaadi yoktur; sistem "not + olasılık + gerekçe" dilinde konuşur, her çıktı zaman damgası ve konfigürasyon kimliğiyle denetlenebilir, veri gizliliği yerel AI çıkarımıyla korunur.
>
> **FinSense, platformun impact motorudur:** gerçek, tarihli ve sonucu bilinmeden notlanmış binlerce arşiv vakasından otomatik ders üreten; kalibrasyon antrenörü ve kör-nokta haritasıyla kullanıcıyı sürekli eğiten; arşiv büyüdükçe kendi kendini geliştiren etkileşimli bir **finansal okuryazarlık laboratuvarı**.
>
> **Şu anda MVP aşamasındayız.** Hedefimiz, bu altyapıyı multi-agent DRL karar motorları, otomatize agent iş akışları, tam regtech/compliance katmanı ve çok pazarlı uluslararası kapsamla (ABD → AB → global) büyüterek; kullanıcısının risk profilini öğrenen, piyasayı onun adına izleyen, her kararı anlaşılır dille gerekçelendiren ve onu bu süreçte adım adım daha iyi bir yatırımcıya dönüştüren kişisel finansal danışmana ulaşmak.

### English (kısa)

> **FinPilot — Institutional-grade analytics and decision-support infrastructure for retail investors.** Built in Vienna, designed to become both a financial educator and a personal financial advisor. Today's MVP, "The Morning Ledger", scans 1,800+ US stocks every morning, converts candidates into calibrated A/B/C research grades, and publishes every outcome — misses included — on an open scorecard. The scoring engine is the product of rigorous R&D: a volatility-aware factor model validated with locked out-of-sample testing, triple-barrier execution replay, realistic cost modelling and shadow validation; our multi-agent DRL line is the research lab feeding it. Regtech is built in: no buy/sell advice, no price targets — only grades, probabilities and reasons, every output auditable and privacy-first. FinSense, our impact engine, is a self-improving financial literacy lab that turns each day's real, time-stamped cases into lessons and continuously trains the user's judgement. We are at MVP today; our goal is a personal financial advisor-and-educator spanning multi-agent decision engines, automated agent workflows, a full compliance layer and multi-market international coverage.

---

## 4. Tanıtım Öncesi Teknik Ön Koşul (kritik)
Açık karne bu anlatının bel kemiği; ancak **signals_archive 22.05'te donmuş ve resolver çalışmıyor** durumda. Jüri, demo veya yatırımcı görüşmesinden önce: resolver'ı canlandır → karneyi doldur → "A: %X / B: %Y" cümlelerini gerçek veriyle yaz. Aksi hâlde en güçlü iddia kanıtsız kalır.
