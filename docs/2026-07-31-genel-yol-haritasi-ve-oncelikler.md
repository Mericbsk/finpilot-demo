# FinPilot — Genel Yol Haritası ve Öncelikler (bugünkü master prompt'ların sentezi)

Sürüm: 1.0 · Tarih: 2026-07-31 · Durum: Level A sentez (kararlar Level B/C ayrı onay)
Kapsam: Bugün çalıştırılan tüm master prompt'ların (sinyal QA, dağıtım zinciri, governance
haritası, web yüzü, waitlist/feedback, sinyal-izleme, aws hibe, EODHD/Alpaca + evren) açık
işlerini tek öncelik sırasına koyar. Her madde: **ne**, **ne kazandırır**, **ne değiştirir**,
**seviye**, **bağımlılık**, **durum**.

---

## 0. STRATEJİK ÇERÇEVE — her şeyi belirleyen tek bulgu

Bugün ölçebildiğimiz **tek pencerede** (15–30 Tem), scanner'ın seçtiği sinyaller **pozitif edge
üretmedi** — hem piyasaya (SPY/IWM/QQQ hepsine göre negatif) hem reddedilen kontrol grubuna göre
daha kötü, ve bu **benchmark'a dayanıklı**. Tek pencere hüküm değil, ama şunu dayatıyor:

> **Gerçek edge kanıtlanana kadar, aşağı-akış her büyük yatırım (evren büyütme, ağır web yatırımı,
> aws'de performans iddiası, canlıya alma) ERTELENİR.** Önce ölçüm + çok-pencere kanıtı.

Bu yüzden yol haritası "ölç → kanıtla → sonra büyüt" mantığında sıralanmıştır.

---

## ✅ BUGÜN TAMAMLANANLAR (zemin)
- Gölge skor kartı: kontrol grubu + dağılım (p10/med/p90) + risk-ayarlı + horizon süpürme + **çoklu benchmark (SPY/IWM/QQQ)**. Bug fix (olgunluk eşiği).
- **Günlük otomasyon:** `daily_shadow_update.py` + scan-sonrası hook (env `FINPILOT_ENABLE_SHADOW_SCORECARD=1`, şimdi AÇIK) → her tarama pencereyi `scorecard_history.jsonl`'a biriktiriyor.
- Waitlist + demo feedback → Telegram admin bildirimi (Level B, onaylı, decision-log'da).
- Dağıtım endpoint'i (`/api/v1/distribution/snapshot`) kodda mevcut; `.env.local` routing düzeltildi; `price_cache` bugüne taze.
- Analiz/plan belgeleri: dağıtım zinciri, governance haritası, web yüzü denetimi, sinyal-takip kavrayışı, sinyal-izleme planı, EODHD/Alpaca + 8.000 evren denetimi.

---

## P0 — ÖLÇÜM VE EDGE KANITI (her şeyin kapısı)

**P0.1 — Çok-pencere/çok-rejim edge kanıtı biriktir**
- **Ne:** Otomasyon artık her tarama bir satır yazıyor; birkaç hafta çalıştır, farklı rejimleri (trend/yüksek-vol/düşük-vol) kapsa.
- **Ne kazandırır:** "Tek kötü pencere miydi, yoksa gerçekten edge yok mu?" sorusunu cevaplar. Tüm stratejik kararların (büyütme, canlı, aws iddiası) dayanağı.
- **Ne değiştirir:** Henüz bir şey değiştirmez — kanıt üretir. Kanıt pozitifse büyümenin önü açılır; negatifse sinyal mantığı elden geçirilir.
- **Seviye:** A · **Bağımlılık:** yok (otomasyon hazır) · **Durum:** çalışıyor, zaman gerekiyor.

**P0.2 — Canlı karne'yi deterministik EOD'ye taşı (yfinance → EODHD/price_cache)**
- **Ne:** `watchlist.py::_evaluate_signal_sync` şu an yfinance ile sonuç çözüyor (kırılgan, non-deterministik). Gölge skor kartının deterministik EOD motoruyla değiştir.
- **Ne kazandırır:** Tekrarlanabilir, güvenilir karne; "resolver dead / archive donmuş" riskini kapatır. aws ve kullanıcıya gösterilecek karne rakamları güvenilir olur.
- **Ne değiştirir:** Üretim karne API'sinin veri kaynağı — **Level B** (onay + decision-log).
- **Seviye:** B · **Bağımlılık:** P0.1 tooling (hazır) · **Durum:** açık.

**P0.3 — Temiz kontrol: likidite-eşleştirilmiş + red-nedeni kırılımı**
- **Ne:** Kontrol grubunu ADV kovasına göre eşleştir, `direction_gate` reddlerini ayır; illikit-stale fiyat artefaktını ele.
- **Ne kazandırır:** "Seçilen < kontrol" bulgusunun gerçek mi yoksa kontrol-kompozisyonu artefaktı mı olduğunu netleştirir.
- **Seviye:** A · **Bağımlılık:** P0.1 · **Durum:** kısmen (red-nedeni kırılımı scorecard'da var; likidite-eşleştirme eklenmeli).

---

## P0/P1 — DAĞITIM ZİNCİRİ GÜVENİLİRLİĞİ (edge kullanıcıya ulaşsın)

**P1.1 — Web'i tek kaynağa bağla (Render snapshot → tek doğruluk)**
- **Ne:** Landing + `/demo`'yu canlı `/api/v1/distribution/snapshot`'tan okut (statik dosya fallback); Vercel env (`NEXT_PUBLIC_SNAPSHOT_URL`, `BACKEND_URL`). Kuyruğu `snapshot_id`'ye bağla.
- **Ne kazandırır:** "Render 20 Tem, web 17 Tem" ayrışması biter; tek tarama → tek snapshot → tüm yüzeyler. Telegram+web tutarlılığı.
- **Ne değiştirir:** Web veri yolu + kuyruk şeması — **Level B**. Render deploy + Vercel env gerektirir (senin panel işin).
- **Seviye:** B · **Bağımlılık:** endpoint canlı (deploy) · **Durum:** endpoint kodda var, deploy + web bağlama açık.

**P1.2 — Render deploy + env doğrulama**
- **Ne:** Güncel commit'i deploy et; `/agent/scheduler`'da `distribution` alanını, `TELEGRAM_*`/`ALPACA_*`/`FINPILOT_FULL_UNIVERSE_SIZE=1812`/yeni `FINPILOT_ENABLE_SHADOW_SCORECARD` env'lerini doğrula.
- **Ne kazandırır:** Kod ile canlı runtime'ın aynı olması; sessiz "eski image" kopukluğunun sonu.
- **Seviye:** B (panel) · **Durum:** açık.

---

## P1 — WEB YÜZÜ KREDİBİLİTE + FİNSENSE (güven + aws hikayesi)

**P1.3 — Newsroom mockup'ını landing'den kaldır/gerçek veriye bağla**
- **Ne:** `Newsroom` (+TheWire/EditorialBoard/FactCheckingDesk) landing'de "illustrative" veriyle CANLI; etiketi kullanıcıya görünmüyor.
- **Ne kazandırır:** "Gerçek veri diyen sayfada sahte bölüm" çelişkisi biter → güven. En ucuz yüksek-etki.
- **Ne değiştirir:** Public landing — **Level B**.
- **Seviye:** B · **Durum:** açık (P0 web denetiminden).

**P1.4 — FinSense'i kamuya aç**
- **Ne:** Giriş-gerektirmeyen public FinSense (sözlük/eğitim), yasak-dil filtresiyle.
- **Ne kazandırır:** İki yönlü: (a) kullanıcıya erişilebilir eğitim (SEO/dağıtım), (b) **aws Innovative Solutions "Eğitim/impact" hikayesinin merkezi**. Positioning'i somutlaştırır.
- **Ne değiştirir:** Yeni public yüzey + compliance — **Level B**.
- **Seviye:** B · **Bağımlılık:** aws stratejisiyle koşut · **Durum:** açık.

**P1.5 — Premium funnel + CTA**
- **Ne:** Stripe env'ini Vercel'de doğrula/doldur; landing→demo→premium net yol + tek birincil CTA (Telegram brief).
- **Ne kazandırır:** Ziyaretçi → kayıt/ödeme dönüşümü; şu an kopuk huni.
- **Seviye:** A/B · **Durum:** açık (Stripe linkleri yerelde boş).

---

## P1 — aws HİBE (zaman-hassas: bilgi saati 19 Ağu)

**P2.1 — Konumlandırmayı Impact/Innovative Solutions'a çevir**
- **Ne:** "Deep Tech" hedefini bırak; başvuruyu **toplumsal problem (finansal okuryazarlık/erişim) + ölçülebilir etki** üzerine kur; FinSense merkez.
- **Ne kazandırır:** aws'nin resmi yönlendirmesine uyum → uygunluk; ~€89–100k hibe şansı.
- **Ne değiştirir:** Positioning dokümanı + başvuru anlatısı (kod değil).
- **Seviye:** A (analiz) → başvuru Level C (insan) · **Bağımlılık:** P1.4 (FinSense public = impact kanıtı), P0.2 (dürüst karne — abartma yok) · **Durum:** araştırma yapıldı, doküman açık.

**P2.2 — Kabul oranı kaldıraçları:** Avusturya üniversite/araştırma ortaklığı (LOI), impact inkübatörü/danışman, compliance firewall belgesi, gender bonus, traction kanıtı (waitlist/feedback — hazır). Karar gereken: **Avusturya lokasyonu** (uygunluk ön koşulu).

---

## P2 — GOVERNANCE HİJYENİ

**P3.1 — Otorite-haritası göçü (hayalet klasörler)**
- **Ne:** `.github/copilot-instructions.md` + `*.instructions.md` olmayan `00-strategy…06-releases`'e bakıyor; `AGENTS.md → docs/INDEX.md` dinamik modeline göçür + lint guard.
- **Ne kazandırır:** AI ajanları (Claude/Copilot/Cursor) tutarlı boot; hayalet referans/çelişki biter; repo yeniden düzenlense talimat kırılmaz.
- **Seviye:** B/C · **Durum:** plan hazır (`docs/2026-07-29-otorite-haritasi-gocu-plani.md`).

**P3.2 — Bugünkü Level B değişikliklerini decision-log'a işle** (scan/jobs hook, shadow env). Küçük ama governance gereği.

---

## P3 — ERTELENEN: EVREN BÜYÜTME (1.800 → 8.000)

- **Ne:** Daha geniş ABD evreni (katmanlı Tier 1/2/3 modeli önerilir, tek sıçrama değil).
- **Ne kazandırır (potansiyel):** Daha geniş fırsat/segment; survivorship-free daha büyük backtest (EODHD delisted).
- **Neden ERTELENDİ:** Ölçülen pencerede edge yok; ölçüm bozukken evren büyütmek = **daha çok gürültü, daha yüksek maliyet/kırılganlık.** Ayrıca 8.000'de API kota/süre/maliyet ölçülmedi; Alpaca free veri (IEX %2.5 hacim) likidite için güvenilmez.
- **Kapı:** P0.1 çok-pencere edge kanıtı POZİTİF olursa → kontrollü S1 (3–4k) shadow-mode → kanıtlı segmentler için katmanlı model.
- **Seviye:** B/C · **Durum:** bilinçli ertelendi (`docs/2026-07-29-veri-saglayici-ve-8000-evren-DENETIM.md`).

---

## ÖNERİLEN SIRA (önümüzdeki 2–4 hafta)

```
1. [P0.1] Otomasyonu çalıştır, pencere biriktir (pasif, zaman)         ← başladı
2. [P0.2] Canlı karne → deterministik EOD (Level B)                    ← ölçümü sağlamlaştırır
3. [P1.2] Render deploy + env doğrula (panel)                          ← runtime senkronu
4. [P1.1] Web'i Render snapshot'a bağla + snapshot_id (Level B)        ← dağıtım tek-kaynak
5. [P1.3] Newsroom mockup temizliği (Level B)                          ← kredibilite
6. [P1.4] FinSense public (Level B)  +  [P2.1] aws positioning         ← impact hikayesi (koşut)
7. [P1.5] Premium funnel                                               ← dönüşüm
8. [P3.1/P3.2] Governance göçü + decision-log                          ← hijyen
9. [P3] Evren büyütme — YALNIZ P0.1 edge pozitifse                     ← kapılı
```

**Tek cümlelik özet:** Önce **ölç ve kanıtla** (P0), paralelde **dağıtımı güvenilir + web'i kredibl** yap (P1) ve **aws'yi impact üstüne kur** (P1); **evren büyütmeyi edge kanıtına kadar beklet** (P3).

---

## AÇIK KARARLAR (senden)
- Avusturya lokasyonu: aws uygunluğu için — durumun?
- P0.2 (karne EOD göçü) ve P1.1 (web tek-kaynak) Level B — onaylıyor musun?
- Evren büyütme kapısı: P0.1 edge eşiğini ne kabul edelim (ör. çok-pencere medyan IWM-excess > 0)?
