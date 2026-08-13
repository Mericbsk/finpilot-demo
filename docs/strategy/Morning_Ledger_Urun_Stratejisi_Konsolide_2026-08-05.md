# Morning Ledger × Open Classroom — Konsolide Ürün Stratejisi
Durum: **VİZYON — DONDURULDU (rafa kalkar)** · 2026-08-05 · Layer: 01-product/strategy · Eskalasyon: Level B (öneri)
Girdi: Çok turlu beyin fırtınası thread'i. Bu belge onu tek kanonik metne indirir + kanıtla çerçeveler.
Kural: Bu belge kod, public içerik, Grade sözleşmesi veya yayın davranışı **değiştirmez**. Onaya sunulur.

---

## 0. Meta-uyarı (önce bunu oku)

Bu güçlü bir vizyon — ama CTO-DD'nin kuralı net: **"Vizyonu belge olarak dondur, günlük kararları
'bu lansmanı ilerletiyor mu?' filtresinden geçir."** Bu belgenin kendisi bir iş programı DEĞİL;
kapsam kilidini (PARKING_LOT) bozmamalı. **Bu haftanın tek aksiyonu değişmiyor:** lansman yürütme
planı (4 madde) + demo feedback'ini **3 doğrulama sorusuna** bağlamak. Trust Engine / Market Memory /
çok-boyutlu Grade / community = **PMF sonrası, ayrı Level B kararları.** Aşağısı ne zaman-ne, ve
bugün neyi dürüstçe söyleyebileceğimizin haritasıdır.

---

## 1. Kategori kararı (thread'in yakınsadığı yer)

Üç aday arasından:
- ❌ **AI Investment Signal Platform** — kalabalık, regülasyon riski yüksek, edge kanıtı yok.
- ⚠️ **Financial Intelligence Briefing** — Bloomberg/FT/Morningstar dolu; sırf haber = farksız.
- ✅ **Market Reasoning Platform** — "piyasayı takip et" değil, **"piyasayı okumayı öğren"**; açık
  karneyle. Rakip az, compliance-uyumlu, moat'ı kopyalaması zor.

**Çekirdek ayrım (en değerli kristalizasyon):** FinPilot bir **bilgi** ürünü değil, **muhakeme
(reasoning)** ürünüdür. Bilgi ürünü "NVIDIA yükseldi" der; muhakeme ürünü "neden bekleniyordu, beklenti
neydi, alternatif açıklamalar, hangi varsayım yanlış çıkabilirdi" diye *düşündürür*. Dışa dönük kategori
adı: **Daily Market Reasoning System** ("Piyasayı takip etme; okumayı öğren").

**Kanonik cümle:**
> FinPilot, piyasayı gerçek olaylar üzerinden **okumayı öğreten**, araştırma varsayımlarını açıklayan
> ve geçmiş sonuçlarını **saklamayan** günlük bir piyasa-akıl-yürütme platformudur.

Katmanlar (tek ürün, beş yüz): **Morning Ledger** (ritüel) · **Open Classroom** (öğrenme) ·
**Honest Ledger** (güven) · **Explainable AI** (açıklama) · Learning Journal (ileride kişiselleştirme).

---

## 2. Kanıt ayrımı — EN ÖNEMLİ BÖLÜM

Bu üründe iddia, kanıtın önüne geçerse güven ölür. Her fikir üç kovadan birine:

### ✅ BUGÜN dürüstçe söylenebilir (kanıtlı)
| İddia | Dayanak |
|---|---|
| Compliance-first dil (BUY/SELL/hedef-fiyat yok, Grade dili) | Kod + governance (gerçek varlık) |
| Açık **overall karne**: beklenti +%0.40/işlem, ~%30 isabet, **3.36x asimetri** (kazanan +4.28% / kaybeden −1.27%) | signals_archive bariyer, 5216 işlem (bu oturum doğrulandı) |
| Açıklamalı, kaynaklı araştırma yaklaşımı | rationale motoru + atıf zorunluluğu |
| Olay-bazlı eğitim fikri (haber → kavram → örnek) | FinSense/academy altyapısı |

### ⚠️ ÖLÇÜM gerektiren (hipotez — kanıtlanmadı)
Kullanıcı alışkanlığı · öğrenme etkisi · retention · "her sabah geri dönüş" · güven üstünlüğü ·
"5 dk'da piyasayı anlıyorum" vaadi. → **5-10 kullanıcı / 5 gün testiyle ölçülecek** (bkz. §7).

### ⛔ PARK — veri sözleşmesi/olgunluk/kapsam gerektirir (bugün SÖYLENEMEZ)
| Fikir | Neden park |
|---|---|
| "Grade A geçmişi: 523 gözlem, %65 doğruluk" | Grade→sonuç **veri sözleşmesi yok** (bkz. §4); by_grade şu an kırılgan resolver + çok az örnek (A=1,B=17,C=41) |
| Market Memory "benzer 43 olay" | Olay taksonomisi/benzerlik sistemi yok → kelime benzerliği olur, güveni bozar |
| Çok-boyutlu Grade (Evidence/Confidence/Risk/Learning Value) | Önce iç ölçüm; UI'yı 5 metrikle boğma |
| Community, AI chat, Learning levels/"Level 7 Investor", TLRI formülü, risk-appetite skoru | PMF öncesi over-engineering; kanıtsız ağırlıklar |
| "Dünyanın en iyisi / en şeffaf / accuracy / edge" dili | Üstünlük iddiası kanıtlanmadı |

---

## 3. Ürün omurgası (MVP — thread'in küçülttüğü hâli)

Tek kusursuz sabah sayısı. İçerik akışı değil, **ritüel**:
```
1. MARKET   — Bugün ne oldu? (≤3 gelişme: ne/neden/hangi veri/hangi belirsizlik)
2. MEANING  — Bugün anlaman gereken tek fikir (1 cümle)
3. LESSON   — Olaydan doğan tek kavram (1 dk + gerçek örnek + bugüne bağlantı + 1 soru)
4. RESEARCH — ≤3 Grade araştırma kaydı (neden listede / hangi faktör / hangi risk / hangi açık soru)
5. LEDGER   — Açık karne (overall barrier: beklenti+asimetri+örneklem+olgunluk+metodoloji linki)
6. REFLECT  — Tek soru: "Bugünkü en önemli fikir neydi?" (buton değil, kısa cevap = değerli veri)
```
İlk MVP'de YOK: portföy, alarm, community, açık-uçlu AI chat, büyük dashboard, gamification, gelişmiş Market Memory.

---

## 4. Trust Engine'in kilit taşı — Grade→Sonuç Veri Sözleşmesi (post-launch, Level B)

Tüm "güven motoru" vizyonu tek mühendislik ön koşuluna bağlı. Bugün `overall` sağlam ama `by_grade`
kırılgan. Grade-bazlı bir geçmiş yayınlamak için ŞU sözleşme kurulmadan hiçbir Grade-accuracy sayısı
gösterilemez:
- Grade **kayıt anında değişmez (immutable)** + değişiklik audit'i.
- Grade ↔ sonuç **açık join**; her kayıt bir kez sayılır.
- Giriş / stop / hedef / **çözüm ufku sabit** (tek deterministik resolver — roadmap P0.2, yfinance değil).
- Açık / olgun / olgunlaşmamış kayıt **ayrı**; olgunlaşmamış dışlanır.
- Küçük örneklem otomatik "olgunlaşıyor" etiketi.

Bu kurulana kadar dürüst ifade: **"Açık bariyer karnesi + Grade karnesi henüz oluşuyor."**

---

## 5. Dil ve isim düzeltmeleri (compliance + ton)
- "Prediction Cemetery" → **"What We Got Wrong / Tutunmayan Varsayımlar"** (sansasyon değil, ders).
- "tahmin / accuracy / doğru tahmin" → **"araştırma kaydı / varsayımın durumu"**.
- "AI Teacher/mentor" → **Sokratik açıklama-mentoru** (karar vermez, soru sorar; ilk sürüm chat değil,
  ders altında sınırlı aksiyonlar: "basitleştir / örnek ver / kontrol sorusu sor").
- Yasak: "dünyanın en iyisi", "edge", "kazandırır", "benchmark-üstü", garanti dili, kişisel tavsiye.

---

## 6. Rakip konumu (kısa) ve gerçek moat
Bloomberg/Reuters (haber otoritesi), Morningstar (araştırma), Seeking Alpha (görüş), TradingView/Koyfin
(grafik/veri) — hepsi güçlü ama **açık karne + olay-bazlı öğrenme + açıklanabilir araştırma** kesişiminde
zayıf. FinPilot'un moat'ı **algoritma değil**: yıllarca tutarlı biçimde (a) her gün yayınlamak, (b)
başarısızlıkları saklamamak, (c) çözüm kurallarını değiştirmemek, (d) feedback'le müfredatı geliştirmek.
Tek cümle: **moat = güvenilir bir finansal düşünme arşivi** (kopyalaması teknik değil, disiplin olarak zor).

---

## 7. Asıl doğrulama ölçütü + guardrail (ölçülebilir)
**Ana metrik:** 5-günlük kohortta, ürünü **doğru tarif ederek** en az **3 sabah geri dönen** kullanıcı oranı.
**İkincil:** ilk 10 sn'de doğru anlama · ≥1 gerekçe okuma · ders tamamlama · karne görme · D1/D3/D5 dönüş.
**Guardrail (kritik):** kullanıcıların **ürünü "al-sat sinyali" diye tarif etme oranı** — yüksekse dil/yüzey yanlış.
**Uzun-vade (asıl vaadi ölçen): Reasoning Improvement Rate (RIR)** — aynı tip senaryoyu 30 gün arayla
sor; kullanıcı risk faktörünü görüyor, beklenti↔gerçekleşen ayırıyor, alternatif açıklama üretiyor mu?
Yatırım *sonucunu* değil, **muhakeme kalitesini** ölçer. (İlk sürümde tek composite skora sıkıştırma —
boyutları ayrı tut.)

---

## 8. Faz sırası
- **ŞİMDİ (bu hafta, lansman cephesiyle aynı):** günlük Ledger formatını sabitle · `overall` karneyi dürüst
  göster · günlük dersi gerçek olayla bağla · **feedback'i 3 doğrulama sorusuna bağla** · 5-10 kullanıcı / 5 gün.
- **SONRA (PMF sinyali sonrası):** "What We Got Wrong" sabit format · Grade→sonuç veri sözleşmesi (§4) ·
  ders tekrarları / learning record · Sokratik açıklama aksiyonları.
- **DAHA SONRA:** Market Memory (taksonomili, kaynaklı, küçük başla) · kişiselleştirme · community · premium.

---

## 9. Kapanış — dürüst hüküm
Vizyon güçlü ve büyük ölçüde katılıyorum: FinPilot'un savaş alanı algoritma değil, **güvenilir finansal
düşünme alışkanlığı.** Ama bugün kanıtlı olan yalnızca: açıklama yaklaşımı, overall karne, compliance dili,
eğitim fikri. Kanıtlanmamış olan: alışkanlık, öğrenme etkisi, retention, güven üstünlüğü, Grade performansı.
Bu yüzden **sıradaki aşama teknoloji/özellik değil, doğrulama.** Bu belge dondurulur; tek somut dilim
lansman planı + 3 soruluk feedback + küçük kohorttur.

_İlgili: `docs/ops/Lansman_Yurutme_Plani_2026-08-05.md`, `distribution/karne.py`, `docs/2026-07-31-genel-yol-haritasi`, `PARKING_LOT.md`, CTO-DD._
