# FinPilot — Alternatif Vizyonlar & Otomatik Gelir Mimarisi

**Tarih:** 2026-06-11
**Kapsam:** "Sıfırdan çekseydin" soruları + 10 alternatif iş modeli vizyonu + 5-katmanlı gelir mimarisi + "neden kimse yapmadı" + 90-günlük plan
**Bağlam zorunluluğu:** Bu strateji, [WIN_RATE_ANALIZI.md](../audits/2026-06-11/WIN_RATE_ANALIZI.md) bulgusuyla sınırlıdır — **çekirdek sinyal edge'i henüz kanıtlanmadı.** Tüm vizyonlar bu gerçekle uyumlu olmalı.

---

## 1. "Sıfırdan Çekseydin" — 7 Temel Soru

1. **Asıl satılan ne?** Sinyal mi, güven mi, eğitim mi, zaman tasarrufu mu? → Edge kanıtlanmadığına göre bugün satılabilir olan **eğitim + tarama verimliliği + disiplin**, sinyal değil.
2. **Kim acı çekiyor?** DACH/TR'deki yeni-orta seviye bireysel yatırımcı: bilgi kirliliği, duygusal işlem, araç dağınıklığı.
3. **Neden şimdi?** LLM maliyeti düştü; bireysel yatırım DACH'ta büyüyor; Türkçe/Almanca kaliteli finans eğitimi az.
4. **En küçük kanıtlanabilir değer ne?** "Bu hafta neye bakmalıyım?" + "bu ne demek?" — tarama + bağlamsal eğitim.
5. **Hangi varlık savunulabilir?** Veri değil (yfinance herkeste); **Türkçe/Almanca eğitim içeriği + kişiselleştirme + topluluk**.
6. **Edge olmadan dürüst gelir nereden?** Eğitim aboneliği, araç/verimlilik aboneliği, topluluk — performans vaadi olmadan.
7. **Başarısızlık senaryosu ne?** Edge hiç kanıtlanmazsa → "sinyal" ürününü tamamen bırak, eğitim+araç platformuna pivot et.

---

## 2. 10 Alternatif Vizyon

| # | Vizyon | Çekirdek değer | Gelir | Edge gerekir mi? | Risk |
|---|--------|----------------|-------|------------------|------|
| V1 | **Sinyal SaaS (mevcut)** | Kârlı tarama sinyalleri | €29/ay Pro | ✅ Evet (yok!) | 🔴 Yüksek — edge yok |
| V2 | **Finans Akademisi** | Kişiselleştirilmiş TR/DE eğitim | €9–19/ay | ❌ Hayır | 🟢 Düşük |
| V3 | **Tarama Verimlilik Aracı** | "Bu hafta neye bak" + filtre/watchlist | €15/ay | ❌ Hayır | 🟢 Düşük |
| V4 | **Disiplin/Davranış Koçu** | Aşırı-güven biası uyarısı, jurnal | €12/ay | ⚠️ Kısmi | 🟡 Orta |
| V5 | **Topluluk + İçerik** | Discord/Telegram + premium içerik | €5–10/ay + sponsor | ❌ Hayır | 🟢 Düşük |
| V6 | **B2B White-Label Eğitim** | Banka/broker'a TR/DE finans eğitimi API | Lisans/yıllık | ❌ Hayır | 🟡 Orta (satış) |
| V7 | **Backtest/Araştırma Platformu** | Strateji test altyapısı (kendi edge'ini bul) | €39/ay pro | ❌ Hayır | 🟡 Orta |
| V8 | **Portföy Sağlık Tarayıcı** | Konsantrasyon/risk uyarısı (tavsiye değil) | €12/ay | ❌ Hayır | 🟢 Düşük |
| V9 | **AI Finans Asistanı (chat)** | "Bu hisse ne yapıyor?" RAG chat | €19/ay | ❌ Hayır | 🟡 Orta (LLM maliyet) |
| V10 | **Veri/API Altyapı** | Temiz sembol+market_cap+sinyal API | Kullanım başı | ❌ Hayır | 🟡 Orta |

### Önerilen birleşim (köprü stratejisi)
> **V2 + V3 + V4** çekirdek (edge gerektirmez, bugün satılabilir) → **V1**'i "deneysel/beta, edge kanıtlanırsa premium" olarak arkada tut. Edge kanıtlanırsa V1 ana ürüne döner; kanıtlanmazsa V2/V3/V4 zaten ayakta.

---

## 3. Otomatik Gelir Mimarisi (5 Katman)

| Katman | İçerik | Otomasyon | Marj |
|--------|--------|-----------|------|
| **L1 — Freemium giriş** | Sınırlı tarama + 3 ücretsiz ders | Self-serve kayıt | — (akış) |
| **L2 — Eğitim aboneliği** | Tam Academy + kişiselleştirme (V2) | Academy ajanları içerik üretir (Groq) | Çok yüksek |
| **L3 — Araç aboneliği** | Sınırsız tarama, watchlist, alert (V3/V8) | Scanner + Telegram otomatik | Yüksek |
| **L4 — Topluluk/içerik** | Premium Discord, canlı içerik (V5) | İçerik takvimi + moderasyon | Orta |
| **L5 — B2B/API** | White-label eğitim, veri API (V6/V10) | API + lisans | Yüksek (düşük hacim) |

**Otomatik döngü:** L1 (ücretsiz) → davranış verisi → Academy kişiselleştirme → L2/L3 upsell → topluluk (L4) retention → B2B (L5) ile içerik amortismanı.

> **Marj motoru:** Academy içeriği bir kez LLM ile üretilip QA'dan geçince **sıfır marjinal maliyetle** tüm kullanıcılara sunulur. Asıl maliyet üretim anında; tüketim neredeyse bedava.

---

## 4. "Neden Kimse Yapmadı?" Analizi

| Engel | Açıklama | FinPilot avantajı |
|-------|----------|-------------------|
| **Dil** | Kaliteli TR/DE finans eğitimi az; İngilizce hakim | Türkçe içerik + DACH odağı |
| **Edge yanılgısı** | Herkes "kazandıran sinyal" peşinde, çoğu başarısız | FinPilot dürüst pivot yapabilir (eğitim+araç) |
| **Birleşim zorluğu** | Eğitim + tarama + topluluk ayrı ürünler | Tek platformda entegre (Academy köprüleri) |
| **Otomasyon maliyeti** | İnsan içerik üretimi pahalı | Self-evolving Academy ajanları (Groq) |
| **Regülasyon korkusu** | Yatırım tavsiyesi riski | Eğitim çerçevesi = düşük regülasyon yükü |

**Özet:** Kimse yapmadı çünkü çoğu oyuncu "sinyal satıcısı" olmaya çalışıp edge'e takıldı. Eğitim+araç+topluluk birleşimi daha az seksi ama daha savunulabilir ve otomatize edilebilir.

---

## 5. 90 Günlük Plan

### Gün 0–30 — Dürüst Konumlandırma + Çekirdek Pivot
- [ ] Pazarlama/funding dilini düzelt (edge iddiası kaldır, "eğitim+araç+beta sinyal")
- [ ] Ters-decile skor sorununu araştır (P0 teknik — SISTEM_AUDIT E.2)
- [ ] V2/V3 paketleme: ücretsiz + €9 eğitim + €15 araç planları tanımla
- [ ] Academy çift kopya birleştirme + event log (ACADEMY tasarım #1–2)

### Gün 31–60 — Self-Serve Akış + Kişiselleştirme
- [ ] L1→L2/L3 upsell akışı (Stripe/abonelik)
- [ ] Academy köprü 1+2 (arama logu + sinyal pattern) canlı
- [ ] Telegram topluluk (L4) + premium kanal
- [ ] "İçerik etkisi" metriği prototipi

### Gün 61–90 — Ölçüm + İlk Gelir + Karar
- [ ] İlk ödeyen kullanıcılar (hedef: ölçülebilir conversion)
- [ ] Edge araştırması sonucu: skor düzeldi mi? → V1 beta kararı
- [ ] B2B/white-label (V6) ilk konuşmalar
- [ ] 90-gün retrospektif: pivot kalıcı mı, V1 geri mi geliyor?

**Başarı kriteri (90. gün):** Edge'e bağımlı olmayan, ölçülebilir ilk gelir + dürüst konumlandırma + Academy'nin ürün-içi entegrasyonu çalışır durumda.

---

## 6. Sonuç

FinPilot'un en büyük riski, **kanıtlanmamış bir edge üzerine kurulu "sinyal SaaS" anlatısı**. En büyük fırsatı, zaten sahip olduğu **olgun eğitim altyapısı (Academy) + tarama aracı + DACH/TR dil avantajı**. Önerilen yol: edge'i beta/araştırma olarak arkada tutup, **eğitim + araç + topluluk** üçlüsüyle bugün dürüst gelir üretmek. Edge kanıtlanırsa premium katman olarak geri döner; kanıtlanmazsa şirket yine ayakta kalır.

---
*FinPilot Strateji — 2026-06-11 — Tek doğruluk kaynağı: WIN_RATE_ANALIZI.md*
