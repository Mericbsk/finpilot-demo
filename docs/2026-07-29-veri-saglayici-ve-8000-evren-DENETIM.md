# Veri Sağlayıcı Kullanımı (EODHD + Alpaca) ve 1.800 → 8.000 Evren Denetimi

Sürüm: 1.0 · Faz 1–2 = Level A (koddan kanıt) · Tarih: 2026-07-29
Kural: kod/config/log kanıtı olmayan hiçbir şey "kullanılıyor" denmez. Ölçülemeyenler "ölçülmedi (local gerekir)".
Not: sandbox'ta ağ yok → API limiti/gecikme/maliyet/8.000-tarama süresi buradan ölçülemez.

---

## 1. YÖNETİCİ ÖZETİ

**EODHD — fiilen kullanılan (canlı yol, env-gated):**
- Fundamentals skoru — `scanner/features.py:543` (`compute_fundamental_score`), `data/eodhd_client.py::fundamental_signals`, 24s cache. **AÇIK** (`.env: FINPILOT_ENABLE_FUNDAMENTALS=1`). Composite score'u etkiler.
- Haber katalizör — `features.py:644` (`compute_news_catalyst`), EODHD news + polarity. **AÇIK** (`.env: FINPILOT_ENABLE_NEWS=1`). Score'u etkiler.
- News-sentiment faktörü — `evaluate.py:518-534`, `scanner/sentiment.py`. **KAPALI** (`FINPILOT_ENABLE_SENTIMENT` .env'de yok → default `0`). Kod var, skoru şu an etkilemiyor.
- EOD tarihsel bar + fundamentals — yalnız **offline** script'lerde (`fetch_and_retest.py`, `fetch_full_universe_and_retest.py`, `eodhd_check.py`); canlı günlük taramanın bar kaynağı **değil**.
- Delisted / exchange-symbol-list / splits-dividends — kodda **kullanılmıyor** (yalnız potansiyel).

**Alpaca — fiilen kullanılan:**
- Canlı fiyat (latest trade/bar) — `api/routers/prices.py` (`StockHistoricalDataClient`, batch ~30/300ms), **yfinance fallback**. `.env: ALPACA_API_KEY` = paper anahtar (PK…).
- Emir yürütme — `broker/` (paper-api.alpaca.markets), paper trading.
- Tarihsel bar (offline) — `data.alpaca.markets/v2/stocks/bars`, `feed=iex`.
- `/v2/assets` (evren listesi) — kodda **kullanılmıyor**; evren kaynağı bu değil.

**yfinance — fiilen kullanılan (kritik, çünkü "sağlayıcımız" sanılan yerlerde o var):**
- `prices.py` fallback · **squeeze fundamentals** (`features.py:118-146`: shortPercentOfFloat, floatShares — canlı squeeze EODHD değil **yfinance**) · **karne sonuç çözümleme** (`watchlist.py::_evaluate_signal_sync` yfinance).

**Evren kaynağı:** statik `web/public/stock_presets.json` (~1.812 sembol), `distribution/jobs.py::_load_universe`. Dinamik değil; Alpaca/EODHD asset listesinden gelmiyor.

**En büyük 3 fayda (8.000):** (1) daha geniş fırsat/sektör kapsaması, (2) survivorship-free backtest için daha büyük örneklem (EODHD delisted ile), (3) segment/rejim kırılımı için istatistik.
**En büyük 3 risk:** (1) **ölçüm altyapısı henüz kanıtlı edge vermiyor** (aşağıda P0), (2) tarama süresi + API kota/maliyet 8.000'de ölçülmedi/kırılabilir, (3) likidite/gürültü — daha çok aday, daha düşük kalite.

**ANA ÖNERİ (kanıta dayalı):** **Evreni şimdi büyütme.** Önce ölçüm/edge kanıtını düzelt. Gerekçe Bölüm 4 + 7.

---

## 2. SAĞLAYICI ENVANTERİ (kanıtlı)

| Sağlayıcı | Kod / Fonksiyon | Veri | Amaç | Zorunlu? | Fallback | Durum |
|---|---|---|---|---|---|---|
| EODHD | `features.py:543` / `eodhd_client.fundamental_signals` | Fundamentals, analist konsensüs | Fundamental skor | Hayır (gate) | skor no-op | **AÇIK** (FUNDAMENTALS=1) |
| EODHD | `features.py:644` / `compute_news_catalyst` | News + polarity | Katalizör skoru | Hayır (gate) | no-op | **AÇIK** (NEWS=1) |
| EODHD | `evaluate.py:518` / `sentiment.py` | News-sentiment | Sentiment faktörü | Hayır (gate) | None → nötr | **KAPALI** (SENTIMENT yok) |
| EODHD | offline `fetch_*` | EOD bars, fundamentals | Backtest/retest | Hayır | Alpaca | offline |
| Alpaca | `prices.py::_fetch_batch_alpaca` | Latest trade/bar | Canlı fiyat | Hayır | **yfinance** | **AÇIK** |
| Alpaca | `broker/` | Trading | Paper emir | Hayır | — | paper |
| yfinance | `features.py:133` | short%/float | Squeeze faktörü | — | no-op | **AÇIK** |
| yfinance | `watchlist.py:851` | OHLCV | Karne outcome | — | — | **AÇIK** |
| statik | `stock_presets.json` | ~1.812 sembol | Evren | Evet | — | **AÇIK** |

---

## 3. VERİ SOY AĞACI (canlı)

```
Evren: stock_presets.json (~1.812, statik)
  → Canlı fiyat: Alpaca latest trade  →(hata)→ yfinance
  → Günlük bar/indikatör: günlük cache (data/daily_cache_h) [canlı bar sağlayıcısı tam doğrulanmadı — açık soru]
  → Squeeze: yfinance short%/float
  → Fundamentals+News: EODHD (24s cache, gate AÇIK)  →(hata)→ skor no-op (nötr)
  → composite/legacy_quality/v2 score → entry_ok → snapshot
  → job_draft → Telegram + web (distribution)
  → shadow ledger (scan_shadow.jsonl) — reddedilenler dahil
  → outcome: karne = yfinance (_evaluate_signal_sync) + shadow_scorecard.py (yeni)
```
Hata davranışı: EODHD/Alpaca başarısız → **sembolü atlamaz, nötr/fallback ile devam** (skor no-op) — scan durmuyor. Kanıt: gate'lerin try/except no-op deseni + prices.py yfinance fallback.

---

## 4. BASELINE + P0 BULGU (ölçülen / ölçülemeyen)

**Ölçülebilen (bu oturumda):**
- Evren ~1.812 (stock_presets). Gölge defteri 8–29 Tem: **29.808 değerlendirme, 261 eligible, 29.547 reddedilen.**
- price_cache tam ve taze (2.039 sembol, 07-29'a kadar).
- İlk gerçek forward sonuç (87 sinyal, 5g): medyan **−4.67%**, SPY excess −4.07, **IWM excess −4.33** (küçük-cap'e göre de negatif), pozitif %21.
- Kontrol testi: seçilen medyan −4.67 vs reddedilen −0.69; pozitif %21 vs %45 → **bu pencerede seçim edge üretmedi (negatif).**

**P0 — ÖLÇÜM ALTYAPISI (evren büyütmeden önce düzeltilmeli):**
- Canlı karne **yfinance'e** bağlı (kırılgan); bellek notu "resolver dead, signals_archive 2026-05-22'de donmuş" — güncelde doğrulanmalı.
- Shadow-scorecard outcome çözümlemesi **yeni** kuruldu; tek kısa pencere, tek rejim (boğa/yumuşak).
- **Sonuç:** edge henüz kanıtlı değil (aksine bu pencerede negatif). Master prompt kuralı gereği: ölçüm bozuk/eksikken evren büyütmek = daha çok gürültü. **Evren genişletme, ölçüm+edge kanıtından SONRA.**

**Ölçülemeyen (local/canlı gerekir):** gerçek scan süresi, sembol başına süre, EODHD/Alpaca çağrı sayısı ve rate-limit/retry, CPU/RAM, job_draft süresi, 8.000'de API kota/maliyet. → "bilinmiyor / doğrulanmadı".

---

## 5. 1.800 → 8.000 KAZANIM/KAYIP (kanıt + boşluk)

**Kapasite (ölçülmedi, ama mimari sinyaller):**
- Canlı fiyat Alpaca latest-trade batch 30/~300ms → 8.000 ≈ 267 batch (~90s+ yalnız quote); yfinance'e düşen her sembol 3–8s → fallback oranı yüksekse süre **orantısız** patlar.
- Alpaca paper/free veri feed'i **IEX** (hacmin ~%2.5'i) → 8.000'de likidite/ADV **güvenilmez**; SIP ücretli gerekir.
- EODHD fundamentals+news **sembol başına** (24s cache) → 8.000 ilk-dolum kota/maliyet ölçülmedi; plan günlük kotası doğrulanmalı.

**Kalite (kanıt):** mevcut 1.812'de bile seçim bu pencerede edge vermedi → 8.000 muhtemelen **daha çok aday, daha düşük kalite** riski taşır; likidite filtresi olmadan small/micro-cap gürültüsü + gap/manipülasyon riski artar.

**Fayda (potansiyel, test edilmeli):** EODHD delisted ile survivorship-free daha büyük backtest örneklemi; yeni sektör/segment kapsaması. Ama "artımsal edge" **shadow-mode ile ölçülmeden** kabul edilmez.

---

## 6. SHADOW-MODE + KATMANLI EVREN (öneri tasarımı)

**Shadow-mode:** S1(3–4k)/S2(5–6k)/S3(~8k) ayrı config + ayrı snapshot/log/namespace, **Telegram/web'e ASLA gönderilmez**, S0(1.812) ile aynı gün yan yana. Her koşuda: config sürümü, sağlayıcı çağrı sayısı, süre, hata/retry, checksum. Min. test: birden çok rejim (trend/yüksek-vol/düşük-vol), tek gün/tek boğa yeterli değil.

**Katmanlı evren (1.800/8.000 ikilisine alternatif):**
- Tier 1 (production): yüksek likidite/veri, Telegram+web adayları.
- Tier 2 (extended research): orta likidite, taranır+izlenir, doğrudan yayın adayı değil (daha yüksek eşik).
- Tier 3 (discovery): geniş kapsam, düşük öncelik, yayına bağlı değil.
- Excluded: OTC, aşırı düşük fiyat/hacim, uygun olmayan enstrüman.
- Tier geçişi objektif kritere bağlanır (ADV, veri tamlığı, spread, kanıtlı edge).

---

## 7. ÖNERİ (yalnız kanıtın desteklediği)

**Seçilen: "Önce veri/sonuç-çözümleme altyapısını düzelt, evren genişlemesini ertele."**
Gerekçe: (a) tek ölçülebilir pencerede seçim edge vermedi (benchmark'a dayanıklı negatif), (b) karne yfinance'e bağlı/kırılgan, (c) 8.000 kapasite/kota/maliyet ölçülmedi. Bu üçü çözülmeden büyütme = ölçülemeyen, muhtemelen negatif edge'i ölçeklemek.

**Sıra:**
1. **Level A:** karne/outcome çözümlemeyi sağlamlaştır (yfinance yerine EODHD EOD ile deterministik; günlük shadow-scorecard'ı otomatikleştir) + çoklu-benchmark (SPY/IWM/sektör) varsayılan.
2. **Level A:** çok-pencere/çok-rejim edge kanıtı biriktir (kontrol grubu likidite-eşleştirilmiş).
3. **Level B:** edge kanıtlanırsa **kontrollü** S1 (3–4k) shadow-mode; kabul/geri-alma kriterleriyle.
4. **Level B:** faydası kanıtlanan segmentler için **katmanlı** model (8.000 tek sıçrama DEĞİL).
Mevcut 1.812 config sürümlü, tek komutla geri dönülebilir kalır.

---

## 8. KAPSAM DIŞI / AÇIK SORULAR
- Canlı günlük **bar** sağlayıcısı (indikatörler için) tam doğrulanmadı — `data/daily_cache_h` mı, Alpaca bars mı? (açık soru)
- EODHD plan günlük **API kotası** ve 8.000 ilk-dolum maliyeti — bilinmiyor (local/panel gerekir).
- Alpaca **secret** anahtarı ve veri planı (IEX/SIP) — .env'de yalnız key doğrulandı; feed teyidi gerekir.
- Gerçek scan süresi / rate-limit / retry telemetrisi — log erişimi/local koşu gerekir.
- Karne archive'ın (signals_archive) güncel durumu (donmuş mu?) — doğrulanmalı.
- **Güvenlik notu:** `.env` içinde canlı ALPACA + EODHD anahtarları düz metin — bu denetimde değerleri kaydedilmedi; rotate + secret yönetimi ayrı iş (Level B/C).
