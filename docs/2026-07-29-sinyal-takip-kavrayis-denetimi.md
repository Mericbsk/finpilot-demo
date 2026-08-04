# Sinyal Takip Mantığı — Kavrayış ve Perspektif Denetimi

Sürüm: 1.0 · Level A (kavrayış/analiz) · Tarih: 2026-07-29
Layer: 01-product (sinyal/scanner) + 03-research (kanıt) · Bulgular = Level B öneri (pending)
Zihniyet: önce ANLA, sonra SORGULA — savunma/eleştiri değil, keşif.
Kanıt: `scanner/evaluate.py`, `api/routers/watchlist.py` (`_evaluate_signal_sync`, `_group_signals_by`, `/watchlist/performance`), `api/routers/scan.py` (`_auto_add_watchlist`, `_persist_shadow_ledger`), `scanner/{labeling,backtest_metrics}.py`, `data/shadow/scan_shadow.jsonl`.

---

## ADIM 1 — MEVCUT SİNYAL TAKİP MANTIĞI (açıklayıcı, yargısız)

### 1. Sinyal nedir, nasıl doğar?
Tek bir "%X hareket etti" eşiği **değil**; çok-kriterli bir kapı. `evaluate.py:469`'da bir hisse ancak `score == 3` (RSI/MACD/momentum çekirdek sinyali) **ve** likidite uygun (`:492`) **ve** piyasa "safe" (`:538`) **ve** kazanç-öncesi blackout değil (`:553`) ise `entry_ok=True` sayılıyor. Yani sinyal, hareketin kendisini değil, hareket **öncesi kurulumu** (momentum göstergeleri + volatilite/gap/hacim özellikleri) yakalamaya çalışan bir dedektör. Üstüne sıralama katmanı biniyor: `legacy_quality` (varsayılan) veya `v2` skoru, ve konviksiyon tier'ı (A/B/C). Özet: sinyal = birden çok kriterin bileşimi, tek eşik değil.

### 2. Hangi zaman çerçevesinde izleniyor?
İki katman var:
- **Takip/ömür:** sinyal watchlist'e ekleniyor (`_auto_add_watchlist`), **21 takvim günü** sonra force-expire (`watchlist.py:191-195`, `_EVALUATE_EXPIRY_DAYS`).
- **Sonuç penceresi:** `/watchlist/performance?days=N` — outcome N **işlem günü** içinde ölçülüyor. Endpoint **varsayılanı 1 gün** (`days=Query(default=1, ge=1, le=30)`), ama dağıtım karnesi çağrısı `days=5` kullanıyor (`distribution/jobs.py _fetch_karne`). Takip, sinyalin eklendiği günden (`added_at`) başlıyor; barlar sırayla yürünüyor. Pencere **sabit** (parametrik), hisseye göre değişmiyor.

### 3. "Başarı" hangi kritere göre?
Üçlü bariyer, mutlak fiyat seviyeleriyle (`_evaluate_signal_sync:869-915`): giriş = kayıtlı `entry_price`; `take_profit`/`stop_loss` sinyal anında (ATR-türevli) belirlenmiş **mutlak fiyatlar**. Barlar yürünürken **ilk değen kazanır**: high ≥ TP → `TP_HIT` (başarı), low ≤ SL → `STOP_HIT` (başarısızlık); ikisi de olmazsa `OPEN` (son kapanışla gerçekleşmemiş PnL). `tp_rate = TP / n`. Yani başarı = **hedefe ulaşmak** (pozitif getiri değil, belirli fiyata değmek); başarısızlık = **stop'a değmek** (sadece "hedefe ulaşmadı" değil). Ölçüm **mutlak** — endekse/sektöre/volatiliteye göre normalize **edilmiyor**.

### 4. Sinyal sonrası ne izleniyor?
Sonuç için **yalnızca fiyat** (OHLC vs TP/SL). Gölge defteri (`_persist_shadow_ledger` → `scan_shadow.jsonl`) sinyal **anında** zengin bağlam kaydediyor (veri kalitesi tier'ı, execution feasibility, dollar_adv, legacy/v2 skorları, exit profilleri) — ama bunlar sinyal-anı özellikleri; sonuç takibinde hacim/haber/sektör hareketi **izlenmiyor**.

### 5. Karne/istatistik nasıl hesaplanıyor, kaç örnek?
Canlı karne, **o an watchlist'te izlenen sinyalleri** yfinance'ten çekip (`_evaluate_signal_sync`) tier/konviksiyon bazında grupluyor (`_group_signals_by` → `tp_rate`, `avg_pnl`). Yani "geçmiş sinyallerin ortalaması" (canlı takip), geniş tarihsel taramanın değil. **Örneklem = o an izlenen sinyal sayısı** (+ `signal_archive/`, ki bellek notuna göre 2026-05-22'de donmuş). Ayrı bir **araştırma** hattı da var (`scanner/labeling.py`, `backtest_metrics.py`, `full_universe_enriched.csv`'deki `resolved_pct_t5`) — bu tarihsel/backtest tarafı; canlı karneyle **aynı motor değil**. Not: sonuç çekimi **yfinance** kullanıyor (Alpaca/EODHD değil).

---

## ADIM 2 — MEVCUT AÇI (hangi mercekten bakılıyor)

- **BAKIŞ AÇISI:** Mutlak fiyat hareketi · sabit/kısa pencere (1–5 gün) · tek-yön (long-ağırlıklı) · üçlü-bariyer (ATR-türevli mutlak TP/SL) isabeti.
- **TEMEL VARSAYIM:** RSI/MACD kapısı + volatilite/gap/hacim profilini sağlayan hisseler, sinyal sonrası kısa pencerede ATR-türevli hedefe ulaşır; geçmiş benzerler gelecek benzerlere kılavuzdur.
- **NEYİ ÖLÇÜYOR:** Sinyal-sonrası kısa vadeli mutlak fiyatın önceden tanımlı TP'ye değip değmediği (barrier isabet oranı) ve ortalama PnL.
- **NEYİ ÖLÇMÜYOR:** Piyasa-göreli edge (index/sektör normalizasyonu yok) · getiri **dağılımı** (yalnız ortalama + tp_rate) · nedensellik (hareketi önden mi yakalıyor, sonradan mı) · risk-ayarlı tekil-sinyal büyüklüğü · segment kırılımının derinliği · piyasa rejimi ayrımı · kontrol grubu (sinyal-almayanlarla kıyas).

Bu, "yanlış mı bakıyoruz" sorusundan önce "şu an TAM OLARAK neye bakıyoruz" sorusunun kesin cevabıdır.

---

## ADIM 3 — ALTERNATİF MERCEKLER (tamamlayıcı; mevcut açıyı değiştirmeden)

**3.1 Mutlak vs. Göreceli.** Şu an TP isabeti mutlak. Piyasa genel yükselirken çoğu hisse hedefe değebilir → gerçek *edge* ile *piyasa yönü* karışır. Ek mercek: getiriyi SPY/sektöre göre normalize et ("endeksten %X iyi"). *Test edilebilir mi:* index/sektör bar verisi gerekir (elde kısmen var; benchmark serisi eklenmeli).
**3.2 Zaman penceresi çeşitliliği.** Sabit 1/5 gün yerine olgunlaşma **dağılımı** (1/3/5/10/20 gün): sinyal erken mi zirve yapıyor, geç mi olgunlaşıyor? *Test:* gölge defteri + `shadow_scorecard.py` horizon taramasıyla doğrudan yapılabilir (price_cache güncelken).
**3.3 Risk-ayarlı.** Ham getiri yerine getiri/volatilite: "büyük ama riskli" ile "küçük ama tutarlı" ayrışır. *Test:* MFE/ATR ve getiri/ATR gölge skor kartında zaten hesaplanabiliyor.
**3.4 Dağılım (nokta tahmini yerine).** "%X'i %Y hareket etti" tek ortalama; birkaç büyük kazanan ortalamayı şişirebilir. Ek: tam dağılım (en kötü %10 / medyan / en iyi %10). *Test:* `shadow_scored.csv`'den percentile'lar; hemen yapılabilir.
**3.5 Nedensellik.** Sinyal hareketi **önceden** mi yakalıyor yoksa **başladıktan sonra** mı? *Test:* sinyal-anı fiyat/hacmi ile sinyal-öncesi N gün kıyası (gölge defterinde sinyal-anı var; öncesi için price_cache penceresi gerekir).
**3.6 Popülasyon/segment.** Genel ortalama, zayıf segmenti güçlü segmentin arkasında gizleyebilir (küçük/büyük şirket, hacim, sektör). *Test:* gölge defterinde `dollar_adv`, tier var; sektör etiketi eklenmeli.
**3.7 Ters/kontrol grubu.** Sinyal-almayan (kontrol) hisselerle kıyas yapılıyor **mu?** Şu an hayır. Sinyal rastgeleden/piyasa ortalamasından gerçekten iyi mi? *Test:* gölge defteri reddedilenleri de kaydediyor → kontrol grubu **elimizde**, skor kartına eklenebilir.
**3.8 Rejim.** Kriterler yüksek/düşük volatilite, trend/sideways rejimlerde ayrı test ediliyor **mu?** Şu an tek genel ortalama. *Test:* SPY/VIX rejim etiketi + gölge defteri kesişimi; daha çok gün/ay gerekir.

*(Hiçbiri için "daha iyi olur" iddia edilmiyor — her biri "şunu ortaya çıkarabilir, test edilmeye değer" merceği.)*

---

## ADIM 4 — "Baktığımız açı yanlış mı?" (yapılandırılmış)

Mevcut açı **yanlış değil, ama eksik** — bir kriteri değiştirmeye değil, ek mercek eklemeye ihtiyaç var.

| Mevcut Açı | Ne Yakalıyor | Ne Kaçırıyor | Alternatif eklenirse | Öncelik |
|---|---|---|---|---|
| Mutlak TP isabeti | Hedefe değme oranı | Piyasa yönü ↔ edge karışımı | Göreli (index/sektör) normalizasyon (3.1) | **Yüksek** |
| Tek ortalama/tp_rate | Merkezi eğilim | Dağılım kuyrukları, şişiren birkaç kazanan | Percentile dağılımı (3.4) | **Yüksek** |
| Kontrol grubu yok | — | Sinyal rastgeleden iyi mi? | Reddedilenlerle kıyas (3.7) | **Yüksek** (veri elde) |
| Sabit 1–5 gün | Kısa vadeli sonuç | Olgunlaşma zamanlaması | Horizon dağılımı (3.2) | Orta |
| Ham getiri | Hareket büyüklüğü | Risk-ayarlı kalite | Getiri/ATR (3.3) | Orta |
| Tek genel ortalama | Kaba başarı | Segment/rejim saklı | Segment + rejim kırılımı (3.6/3.8) | Orta |
| Yalnız fiyat izleme | Sonuç | Nedensellik (önden mi?) | Sinyal-öncesi kıyas (3.5) | Düşük-Orta |

---

## ADIM 5 — İZLEME YÖNTEMİ ÖNERİLERİ (Level B, pending)

**Ö1 — Kontrol grubu + dağılım skor kartı.** Gölge defterindeki **reddedilen** sinyalleri kontrol grubu olarak skorla; seçilenlerin tp_rate/getiri dağılımını (p10/medyan/p90) kontrol grubuyla kıyasla.
*Gerekçe:* 3.7 + 3.4. *Uygulanabilirlik:* **hemen** — veri (reddedilenler + exit profilleri) gölge defterinde var; `shadow_scorecard.py`'ye kontrol kolu + percentile eklenir; tek engel price_cache tazeliği. *Kazanım:* "sinyalin gerçek edge'i var mı, yoksa piyasa mı" sorusuna ilk kanıt.

**Ö2 — Göreli (benchmark) sonuç.** Her sinyalin getirisini aynı penceredeki SPY/sektör getirisinden çıkararak "excess return" ekle.
*Gerekçe:* 3.1. *Uygulanabilirlik:* SPY/sektör bar serisi gerekir (küçük ek veri). *Kazanım:* boğa piyasasında şişen isabeti düzeltir; gerçek alfa görünür.

**Ö3 — Horizon dağılımı.** Karne/skor kartını 1/3/5/10/20 günde ayrı raporla.
*Gerekçe:* 3.2. *Uygulanabilirlik:* **hemen** (`shadow_scorecard.py --horizon`). *Kazanım:* sinyalin ne zaman olgunlaştığı → daha doğru exit penceresi.

**Ö4 — Risk-ayarlı kolon.** tp_rate yanına getiri/ATR ve profit factor.
*Gerekçe:* 3.3. *Uygulanabilirlik:* **hemen** (skor kartı zaten MFE/ATR biliyor). *Kazanım:* "büyük-riskli" vs "küçük-tutarlı" ayrımı.

**Ö5 — Segment + rejim kırılımı.** Karneyi ADV/tier/sektör ve SPY-VIX rejimine göre ayrı raporla.
*Gerekçe:* 3.6 + 3.8. *Uygulanabilirlik:* segment hemen (ADV/tier var, sektör etiketi eklenir); rejim için daha çok gün. *Kazanım:* saklı zayıf segmentleri ortaya çıkarır.

Bu öneriler doğrudan uygulanmaz; `docs/governance/decision-log.md`'ye **pending** eklenip mevcut sinyal mantığına dokunmadan önce onaya sunulur.

---

## KAPSAM DIŞI (bu analizin veri nedeniyle test edemedikleri)
- **Kontrol grubu/dağılım/horizon/risk-ayarlı (Ö1/Ö3/Ö4):** mantık elde ama `price_cache` bayat (30 Haz/14 Tem'de bitiyor) → olgun sonuç yok; canlı skor için cache güncellenmeli.
- **Göreli benchmark (Ö2):** SPY/sektör bar serisi henüz entegre değil.
- **Rejim (3.8):** eldeki gölge verisi ~15 Tem sonrası ve tek rejim (boğa) → çapraz-rejim testi için daha uzun tarih gerekir.
- **Nedensellik (3.5):** sinyal-öncesi pencere verisi sistemli toplanmıyor.
- **Canlı karne örneklem büyüklüğü:** watchlist/archive'a bağlı; archive donmuş olabilir (doğrulanmalı) → mevcut karne ince/boş olabilir.
