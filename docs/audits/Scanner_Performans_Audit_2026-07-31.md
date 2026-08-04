# FinPilot Scanner — Derin Analiz, Performans Profili ve Güvenli Hızlandırma
Durum: TASLAK · 2026-07-31 · Sürüm 1.0
Layer: 02-engineering + 01-product + 03-research + 05-governance
Eskalasyon: Faz 0–3 = **Level A** (gözlem/ölçüm). Faz 4+ önerileri = **Level B** (insan onayı).
İlke: Önce ölç, sonra anla, sonra değiştir. Kanıtsız iddia yok — kanıt yoksa "test edilmedi" yazıldı.

---

## 1. Yönetici Özeti

**Scanner ne ölçüyor?** Her sembol için 3 gerçek zaman-dilimi (15m/1h/1d; 4h 1h'ten türetiliyor)
OHLCV çeker; üzerine teknik kurulum ölçer — rejim (fiyat>EMA200), yön, momentum, trend gücü,
hacim spike'ı, zaman-dilimi hizası, volatilite rejimi — ve bunları **0–100 composite score**'a
toplar; ardından uygunluk (entry_ok/selection_eligible) ve tier (A/B/C) belirler. Bir dizi ek
faktör (squeeze, SEC katalizör, lottery-fade, overnight-gap, FinBERT sentiment, FRED makro) **kod
olarak var ama varsayılan KAPALI** (`score_engine.py`).

**En büyük 3 doğrulanmış darboğaz:**
1. **yfinance per-sembol yedeği (GÜVEN: YÜKSEK).** `eval_s` toplam süreyi tamamen domine ediyor,
   `enrich_s ≈ 0.0s`. `eval_s`, o batch'te yfinance'e düşen sembol sayısıyla (`yf_fallback`) birebir
   ölçekleniyor. Kanıt (scan_export timing dict'leri):

   | Tarih | Batch | yf_fallback | eval_s |
   |---|---:|---:|---:|
   | 2026-07-30 | 200 | 12 | **83.6** |
   | 2026-07-30 | 200 | 75 | 113.6 |
   | 2026-07-31 | 200 | 37 | 158.9 |
   | 2026-07-30 | 200 | 123 | 250.3 |
   | 2026-07-30 | 200 | 144 | 338.7 |
   | 2026-07-31 | 200 | 57 | **504.0** (aykırı — muhtemel retry döngüsü) |

2. **Tam-evren koşusu tarayıcıda 200'lük batch'lere bölünüp SIRAYLA çalışıyor (GÜVEN: ORTA).**
   Evren 1812 ≈ 9 batch. Batch'ler 84–504s olduğundan tam tur kabaca **15–60+ dk** ve çok
   değişken. Ama tam-tur duvar-saati **hiçbir yerde toplu loglanmıyor** (1812'lik export'larda
   `timing={}`). Bu bir **ölçüm boşluğu**.

3. **Veri hijyeni: sahte semboller (GÜVEN: YÜKSEK).** api.log'da `SCORE`, `FILTER`, `INVALID`,
   `ALIGN` gibi geçersiz "semboller" yfinance'te 404 alıyor (178 yfinance hata satırı). Bunlar boşa
   yavaş yedek çağrısı harcıyor.

**En yüksek faydalı 3 optimizasyon (hepsi Level B, golden-test şartlı):**
- **P0 — Ölçümü tamamla:** tam-evren duvar-saati + aşama kırılımı + Alpaca-ıskalama sebebi. (Düzeltemeyeceğimizi ölçemeyiz.)
- **P1 — Kademeli huni:** önce ucuz 1d verisiyle likidite/fiyat/aktiflik ön-filtresi → pahalı 15m/1h **sadece hayatta kalanlara**. (1801 taranıp yalnız **7 eligible** çıkıyor — huni çok dar.)
- **P1 — Alpaca-ıskalama kök nedeni + evren hijyeni:** neden 200'de 144 sembol yetersiz Alpaca geçmişi alıyor? Geçersiz sembolleri evrenden ele.

**Hızlandırmanın güvenlik sınırları:** Hiçbir değişiklik composite score, eligible aday listesi veya
top-N sıralamasını **golden dataset'te aynı** tutmadan canlıya alınamaz. Skoru/adayı değiştiren her
şey salt-performans değil, **Level B ürün/strateji değişikliğidir** ve ayrı backtest ister. Geniş
evren / paralellik / cache testleri Telegram+web canlı yayınını tetiklememelidir.

---

## 2. Scanner Mantık Haritası (Faz 1)

### 2.1 Uçtan uca akış (gerçek fonksiyonlarla)
```
Sembol evreni (≤500/istek; tarayıcı 200'lük batch)
→ POST /api/v1/scan  (api/routers/scan.py:run_scan)
→ scanner.evaluate_symbols_parallel
   → _prefetch_alpaca_bulk (data_fetcher.py:638) — TÜM semboller için
     timeframe başına TEK Alpaca HTTP çağrısı  [O(timeframe), ~20× hızlı]
   → yetersiz geçmişi olan semboller (_has_sufficient_history=False)
     → fetch_multi_timeframe (per-sembol yfinance, max 4 worker)  ← YAVAŞ YOL
   → per-sembol: indikatörler + features + compute_recommendation_score
     (score_engine.py) + filtreler + eligibility/tier
→ _enrich_results (explanation/reason/finpilot_score)  [~0.0s]
→ _persist_shortlist (CSV) + _persist_shadow_ledger (jsonl, RED dahil)
   + _auto_add_watchlist (BUY→watchlist) + _persist_distribution_export
     (scan_export_latest.json + tarihli; atomic tmp+replace; timing dict)
→ /scan/summarize (tüm batch birleşince) → LLM ≤10 seçim → Telegram
→ snapshot → job_draft → insan onayı → Telegram+web+archive/backup
```

### 2.2 Zaman-dilimi & maliyet modeli
- `DEFAULT_TIMEFRAMES = [("15m",10g), ("1h",15g), ("1d",300g)]`; 4h, 1h'ten resample (ağ yok).
- **Hızlı yol (Alpaca toplu):** 200 sembol için ~3 HTTP çağrısı (dilim başına bir).
- **Yavaş yol (yfinance):** sembol başına ≤3 çağrı, yalnız 4 worker paralel. `MIN_HISTORY_BARS`
  (15m:15, 1h:10, 1d:50) karşılanmazsa o sembol bu yola düşer.
- **Alpaca anahtarları .env'de DOLU** → yedek, eksik kimlik değil; **kapsama** kaynaklı (Alpaca'nın
  intraday/15m geçmişi birçok küçük-cap için yetersiz). *Kesin sebep henüz test edilmedi — bkz. P0.*

### 2.3 Kriter envanteri (score_engine.py — hepsi saf CPU/pandas, ağ yok)
| Kriter | Ağırlık | Score'u etkiliyor mu? | Not |
|---|---|---|---|
| regime (fiyat>EMA200) | +2.0 | Evet | |
| direction | +2.0 | Evet | |
| raw score (RSI/MACD/hacim onayı) | ×0.5 (maks 1.5) | Evet | Faz 5'te ×1.0→×0.5 düşürülmüş |
| filter_score (vol_spike+price_mom+trend) | ×1.5 (maks 4.5) | Evet | En temiz onay |
| alignment_ratio | ×2.0 | Evet | |
| momentum_ratio | ×{2.5/2.0/1.5} vol-rejime | Evet | Düşük-vol'e daha çok güven |
| volume_spike / price_momentum / trend_strength | +0.5 her | Evet | |
| **sentiment (FinBERT)** | ±0.5 | **Hayır (varsayılan kapalı)** | Ayrı FinBERT raporu |
| squeeze / catalyst / lottery / overnight / FRED | değişken | **Hayır (env-gated OFF)** | component_ablation ile doğrulanacak |
- Composite tavan **16.5**, 0–100'e normalize. Rejim×score-band kapısı pozisyon çarpanı veriyor
  (ampirik, 2026-06-12 bariyer audit'i).
- **Bulgu:** Skorlama maliyeti önemsiz (`enrich_s≈0`). Optimizasyon skor tarafında değil, **veri
  çekiminde** aranmalı.

---

## 3. Performans Baseline (Faz 0/2 — kanıt: scan_export timing)

| Baseline Alanı | Değer | Kanıt | Güven |
|---|---|---|---|
| Evren büyüklüğü | 1812 (varsayılan; `FINPILOT_FULL_UNIVERSE_SIZE` .env'de yok, kodda hardcoded) | scan.py | Yüksek |
| Batch büyüklüğü | 200 (tarayıcı) | scan/summarize docstring | Yüksek |
| 200-batch eval süresi | 84–504s (medyan ~200s civarı) | 8 gerçek batch timing | Yüksek |
| enrich süresi | ~0.00–0.03s | timing dict | Yüksek |
| yf_fallback / 200 | 12–144 (%6–72) | timing dict | Yüksek |
| Tam-evren duvar-saati | **bilinmiyor** (toplu loglanmıyor) | 1812 export'ta timing={} | — |
| Başarısız/geçersiz sembol | ≥ birkaç (SCORE/FILTER/INVALID/404) | api.log | Orta |
| API retry / rate-limit sayısı | **test edilmedi** (yfinance logu CRITICAL'e susturulmuş; Alpaca retry WARNING) | — | — |
| Eligible aday (1812'den) | **7** eligible, 4 graded A/B/C | scan_export_latest | Yüksek |
| Yayın penceresine uyum | **test edilmedi** (tam-tur saati yok) | — | — |

---

## 4. Darboğaz / Kök Neden Analizi (Faz 3)

| Hipotez | Kanıt | Sonuç | Etki | Güven |
|---|---|---|---|---|
| **H1 Seri/yavaş API** | eval_s↔yf_fallback korelasyonu; yfinance yalnız 4 worker | **Doğrulandı** — asıl darboğaz yfinance yedeği | Yüksek | Yüksek |
| **H2 Mükerrer çekim** | Cache in-memory + market-aware TTL; batch'ler ayrık sembol → tam-tur içinde cache faydası düşük | Kısmen: tek-tur içinde cache yardım etmiyor (her sembol 1 kez); yalnız re-scan'de | Orta | Orta |
| **H3 Pahalı indikatör** | enrich_s≈0; skor saf CPU | **Çürütüldü** — hesap darboğaz değil | Düşük | Yüksek |
| **H4 Retry/timeout döngüsü** | 504s aykırı batch (yf=57 ama en yavaş) | **Muhtemel, test edilmeli** — loglar susturulmuş, kanıt yetersiz | Orta | Düşük |
| **H5 Geçersiz/eksik sembol** | SCORE/FILTER/INVALID 404; 178 yfinance hata | **Doğrulandı** — evren hijyeni sorunu var, boşa yedek çağrısı | Orta | Yüksek |
| **H6 DB/dosya yazma** | Atomic tmp+replace export; enrich_s≈0 içinde yazma da var | **Çürütüldü (bu ölçekte)** — yazma darboğaz değil | Düşük | Orta |
| **H7 Ortam/sürüm kayması** | git/py/config hash scan başına kaydedilmiyor | **Test edilmedi** — izlenebilirlik eksik (P0 öneri) | ? | — |

**Kök neden özeti:** Yavaşlık *hesaplama* değil, **veri-çekimi I/O**'sudur; kaynağı Alpaca toplu
çekimin birçok (özellikle küçük-cap) sembol için yetersiz intraday geçmiş döndürüp bunları **4-worker
sınırlı, per-sembol yfinance** yoluna itmesidir. Süre, o batch'teki fallback sembol sayısıyla
belirleniyor. 504s aykırısı muhtemelen retry/backoff'la şişiyor ama kanıtlanmadı.

---

## 5. Optimizasyon Backlog'u (Faz 4 — hepsi Level B, golden-test şartlı)

### P0 — Önce (ölçüm & güvenlik ağı; düşük risk)
- **P0.1 Tam-evren telemetrisi:** `/scan/summarize`'a toplu duvar-saati + batch başına
  eval/yf_fallback + Alpaca-ıskalama sebebi (hangi timeframe/hangi sembol yetersiz) yaz. Fayda:
  darboğazı tam ölçekte görünür kılar. Risk: yok (salt gözlem, Level A).
- **P0.2 Golden dataset harness:** sabit tarih + sabit sembol + dondurulmuş ham OHLCV snapshot →
  mevcut çıktı "golden baseline". Her optimizasyon sonrası score/eligible/top-N **birebir**
  karşılaştırılır. Bu olmadan hiçbir P1/P2 canlıya alınamaz.

### P1 — Yüksek değer (darboğazı doğrudan azaltır)
- **P1.1 Kademeli huni (en yüksek değer):** Sıra — (1) ucuz 1d verisiyle likidite/fiyat/aktiflik
  ön-filtresi → (2) pahalı 15m/1h **yalnız hayatta kalanlara**. Gerekçe: 1801 sembol taranıp yalnız
  7 eligible; çoğu sembol için intraday çekmek boşa. **Risk/şart:** ön-filtre nadir fırsatları
  elerse top-N değişir → golden testte **birebir aynı top-N** kanıtlanmadan alınmaz (Level B).
- **P1.2 Alpaca-ıskalama kök nedeni:** neden bu kadar çok sembol yetersiz? Plan tier'ı mı, 15m
  geçmiş limiti mi, sembol kapsaması mı? Sonuca göre: intraday gereksinimini gözden geçir (ama bu
  sinyali değiştirir → Level B/regresyon) veya Alpaca planını yükselt.
- **P1.3 Evren hijyeni:** delisted/geçersiz/sahte sembolleri (SCORE/FILTER/INVALID) evrenden ele;
  "Alpaca-desteklemiyor" setini günlük cache'le, boşuna yfinance denemesini atla. Risk: yanlış eleme
  değerli sembol kaybettirmesin → eleme listesi loglanır/gözden geçirilir.

### P2 — Sonra
- **P2.1 Kalıcı çapraz-tur cache (Redis):** yavaş değişen 1d barları tur-ötesi cache; core.cache
  zaten var. Risk: bayat veri → cache key'e tarih/config-sürümü, net invalidation.
- **P2.2 Kontrollü fallback paralelliği:** yfinance worker 4→8, ama **global rate limiter + backoff**
  ile. Risk: yfinance rate-limit/ban → en hızlı değil, en güvenilir seviye seçilir (1/2/4/8 testi).
- **P2.3 Retry telemetrisi (H4 kapatmak için):** Alpaca/yfinance retry/backoff sayaçlarını export'a
  yaz; 504s aykırısının retry mi olduğunu kanıtla.

---

## 6. Regresyon Güvenliği (Faz 5)

**Golden karşılaştırma zorunlu kontrol listesi** (her optimizasyon sonrası, aynı dondurulmuş veriyle):

| Kontrol | Beklenti |
|---|---|
| Taranan sembol sayısı | Aynı |
| Başarısız sembol listesi | Aynı veya açıklanmış |
| Her indikatör/kriter | Aynı |
| composite_score | Aynı (tolerans yok) |
| Eligible adaylar | Aynı |
| Top-N sıralaması | Aynı |
| Snapshot şeması + Telegram/web alanları | Aynı |

Score/aday/top-N değişirse → salt-performans DEĞİL; Level B ürün/strateji değişikliği; ayrı backtest.
**Uçtan uca dry-run:** `scan → export → snapshot → job_draft → lint → dry-run publish` (Telegram/web'e
GERÇEK gönderim YOK).

---

## 7. Kademeli Geçiş Planı (Faz 6)
1. **Aşama 0 — Baseline sabitle:** mevcut commit/tag + config + universe sürümü + golden output; tek
   komutla geri dönüş doğrulanır.
2. **Aşama 1 — İzole benchmark:** yalnız golden dataset; sonuç eşitliği + süre farkı.
3. **Aşama 2 — Shadow scan:** eski scanner canlı üretir; yeni scanner aynı gün **dry-run**; süre/hata/
   aday farkı karşılaştırılır; **yayın yok**.
4. **Aşama 3 — Kontrollü canlı:** insan onayı sonrası sınırlı süre; eski sürüm geri-dönüş hazır.
5. **Aşama 4 — Stabilizasyon:** hedefler tutarsa "stable" tag.
Her aşama için: başarı/başarısızlık kriteri, geri-alma komutu, sorumlu, decision-log kaydı, onay seviyesi.

---

## 8. Operasyonel İzleme (Faz 7)
| Metrik | Neden | Uyarı eşiği |
|---|---|---|
| Tam-tur süresi (P0.1 sonrası) | Regresyon | Baseline P95 üstü |
| yf_fallback oranı | Alpaca kapsama bozulması | Tarihsel bant dışı |
| Taranan sembol sayısı | Evren kayması | Beklenen aralık dışı |
| Eligible aday sayısı | Score/veri anomali | Tarihsel bant dışı (ör. 0 veya aşırı) |
| Snapshot timestamp | Bayat yayın | Güncel değil |
| Alpaca/yfinance hata oranı | Sağlayıcı | Eşik üstü |
| git/config/universe hash | İzlenebilirlik | Eksik/mismatch |
Alarm → Telegram admin (mevcut `notify_admin`), log. Otomatik rollback yok — önce uyarı + insan.

---

## 9. Kapsam Dışı / Açık Sorular (kanıt eksikleri — dürüstçe)
- **Tam-evren duvar-saati ölçülmedi** (toplu loglanmıyor) — P0.1 kapatır.
- **Retry/rate-limit sayıları test edilmedi** (yfinance logu susturulmuş) — H4 açık.
- **Alpaca-ıskalama kesin sebebi test edilmedi** (plan mı, kapsam mı, 15m limiti mi) — P1.2.
- **CPU/RAM/lock profili alınmadı** (canlı kontrollü scan gerekli; burada üretilmedi).
- **Ortam/sürüm kayması izlenmiyor** (H7) — scan başına hash kaydı önerisi.
- Bu rapor **hiçbir kodu değiştirmedi** (Level A). Uygulama, P0 → golden → P1 sırasıyla ve her adım
  kendi onay seviyesinden geçerek yapılır.

---
_Zorunlu kural hatırlatması: Profilleme olmadan "şu yüzden yavaş" denmedi; kanıtsız kriter iddiası
yok; hız için hiçbir veri-kalitesi/retry/lint/compliance kontrolü kaldırılması ÖNERİLMEDİ; her
optimizasyon golden baseline'dan geçmeden canlıya alınmaz._
