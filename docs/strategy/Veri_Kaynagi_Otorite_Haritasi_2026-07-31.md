# Veri Kaynağı Otorite Haritası — Karar Belgesi
Durum: TASLAK (karar bekliyor) · 2026-07-31 · Layer: 02-engineering + 05-governance
Eskalasyon: Analiz **Level A**. Fiyat-otoritesini değiştiren her uygulama **Level B** (golden testli, insan onaylı); planı/maliyeti değiştiren adım **Level C**.
Amaç: "Kaynaklar çok ve karışık" hissini kanıta indirgeyip, her veri tipi için **tek otorite + açık yedek** kuralı koymak.

---

## 1. Sonuç (önce cevap)

Sorun "çok kaynak" değil — sorun **tek bir yerde yoğunlaşıyor: fiyat/OHLCV yolu.** Orada iki
kaynak üst üste biniyor (Alpaca-IEX birincil + yfinance yedek) ve paralı, yetenekli EODHD bu yola
**hiç bağlı değil**. Diğer tüm kaynaklar ya zaten tek-otorite (EODHD: fundamentals/earnings/sentiment)
ya da **varsayılan kapalı opsiyon** (EDGAR, FRED, FinBERT, sosyal) — yani bugün runtime sorunu değil.

**En kritik teknik gerçek:** Tarayıcı **15m** timeframe'i zorunlu tutuyor ve **hiçbir sağlayıcı 15m'i
temiz vermiyor** — Alpaca-IEX küçük-cap'lerde ince, **EODHD 15m'i hiç sunmuyor** (yalnız 1m/5m/1h),
yfinance 15m veriyor ama yavaş+rate-limit+59 gün limiti. Yani asıl karar noktası kaynak değil,
**"15m gerçekten gerekli mi?"** sorusudur.

---

## 2. Mevcut durum — kanıtlı harita

| Veri tipi | Kaynak(lar) | Rol | Aktif mi? | Kod kanıtı | Not / semantik risk |
|---|---|---|---|---|---|
| **Günlük OHLCV (1d)** | Alpaca-IEX → yfinance | birincil→yedek | ✅ | `data_fetcher._prefetch_alpaca_bulk` (feed="iex") | 1d iyi kapsanıyor |
| **Intraday OHLCV (15m/1h)** | Alpaca-IEX → yf.download → per-sembol yfinance | 3 katman | ✅ | `_repair_partial_alpaca_result` | **Asıl darboğaz**; IEX intraday ince |
| **Fiyat semantiği** | Alpaca vs yfinance | — | ⚠️ | iki kaynak | adjusted-close/timezone/split farkı → sessiz skor kayması |
| **Fundamentals** | EODHD | otorite | ✅ | `features.py:581 fundamental_signals` | tek kaynak — temiz |
| **Earnings takvimi** | EODHD | otorite | ✅ | `eodhd_client.earnings_calendar` | tek kaynak |
| **Haber sentiment** | EODHD sentiments | otorite | ⚠️ env-gated | `scanner/sentiment.py` | `FINPILOT_ENABLE_SENTIMENT` kapalı |
| **FinBERT sentiment** | HF/ProsusAI | alternatif | ❌ uykuda | `llm/finbert_provider.py` | ayrı FinBERT raporu |
| **Katalizör** | SEC EDGAR | opsiyon | ❌ OFF | `scanner/catalyst.py` | validasyon bekliyor |
| **Makro rejim** | FRED | opsiyon | ❌ OFF | `core/macro_regime` | validasyon bekliyor |
| **Sosyal** | Reddit/HN/Polymarket | opsiyon | ❌ (DRL parked) | `agents/social_intelligence_agent` | FinBERT'e besliyor |
| **İşlem (trade)** | Alpaca broker | otorite | ✅ | `broker/` | veri değil, emir |
| **Polygon** | — | legacy | ❌ archive | `archive/…/polygon_live.py` | kullanılmıyor |

**Okuma:** Tek gerçek çakışma fiyat yolunda. "Karışıklık" hissinin %80'i buradan; gerisi kapalı opsiyon
(zararsız ama "kurulu görünüp kapalı" hijyen borcu).

---

## 3. EODHD ne sunuyor? (resmi doküman — kanıt)

- Intraday interval'leri: **1m, 5m, 1h** — **15m YOK**, 4h YOK. (bizim client'ta da intraday yok)
- Intraday endpoint'i **per-sembol** (`/api/intraday/{ticker}`), **bulk değil**; çağrı başına ~5 kredi.
- **Günlük EOD bulk**: `eod-bulk-last-day/US` → **tüm US tek çağrıda** (client'ta `bulk_eod` mevcut).
- Intraday veri gecikmeli, kapanıştan ~2-3 saat sonra kesinleşir → **canlı intraday tarama için uygun değil**, günlük/gün-sonu tarama için uygun.
- Plan: EOD = ~$20/ay; **EOD+Intraday Extended = ~$30/ay**. Intraday ayrı tier.

**Açık soru (tek):** Bizim mevcut anahtar Extended (intraday) içeriyor mu? → `scripts/probe_eodhd.py`
bunu **anahtarı basmadan** test eder.

---

## 4. Hedef otorite haritası (öneri)

Kural: **her veri tipi için TEK otorite; yedek yalnız açık, semantiği-eşleşmiş ve loglu.**

| Veri tipi | Otorite (öneri) | Yedek | Kural |
|---|---|---|---|
| Günlük OHLCV (1d) | **EODHD `bulk_eod`** (tüm US tek çağrı) | Alpaca | Tek çağrı = yüzlerce yfinance çağrısını siler |
| Intraday 1h | Alpaca-IEX **veya** EODHD 1h (probe'a göre) | — | Tek otorite seç, karıştırma |
| Intraday 15m | **KARAR GEREKLİ** (§5) | — | 15m→5m/1h değişimi = Level B |
| Fundamentals/earnings | EODHD | — | zaten otorite, dokunma |
| Sentiment | EODHD **veya** FinBERT (tek) | — | FinBERT raporundaki kapıdan |
| Katalizör/makro/sosyal | opsiyon (OFF) | — | aç → doğrula → ya kalıcı ya sil |

---

## 5. Kritik karar: 15m gerekli mi? (üç yol)

15m her sağlayıcıda sorunlu olduğu için asıl kaldıraç bu:

- **Yol A — 15m'i koru, kademeli huni uygula (P1.1).** Ucuz günlük (EODHD bulk) ön-filtre → 15m/1h
  yalnız hayatta kalan ~yüzlerce sembole. Fallback'i kökten azaltır, **sinyali değiştirmez** (eğer
  ön-filtre hiçbir eligible'ı elemezse). Golden testte birebir aynı top-N şartı. **En düşük riskli.**
- **Yol B — 15m'i 5m'e taşı (EODHD intraday).** Tüm intraday'i EODHD'ye konsolide et. Ama 15m≠5m →
  hizalama/momentum indikatörleri değişir → **sinyal semantiği değişir = Level B + backtest.** Ayrıca
  intraday per-sembol (bulk değil) → günlük tarama için yavaş olabilir.
- **Yol C — 15m'i tamamen bırak (1h+1d yeter mi?).** En büyük sadeleşme (yfinance'i tamamen bırakıp
  EODHD+Alpaca'ya inmek mümkün olur), ama **en büyük sinyal değişikliği** → zorunlu backtest, Level B.

**Öneri sırası:** Önce **Yol A** (davranışı değiştirmeden hızlan + kaynak sadeleştir); Yol B/C ancak
ayrı bir araştırma+backtest ile, ve yalnız ölçülen fayda gerçekse.

---

## 6. Ne yapmalıyız? (adım adım, kapılı)

1. **Probe (senin makinende, 1 dk):** `python scripts/probe_eodhd.py` → planımız intraday içeriyor mu +
   bulk_eod gerçekten tek çağrıda tüm US'i veriyor mu, **kanıtla**. (Bu, §5 kararını netleştirir.)
2. **Telemetri (P0.1):** `golden_scan.py capture` + `scan_timing_report.py` → gerçek 15m/1h/1d miss
   dağılımı (hangi timeframe fallback'i sürüklüyor).
3. **Yol A / P1.1'i default-KAPALI yaz:** EODHD `bulk_eod` günlük ön-filtre + intraday-yalnız-finalist;
   bayrakla aç/kapat.
4. **Golden doğrula:** `golden_scan.py compare` → top-N/eligible **birebir aynı** olmalı. Aynıysa "salt
   performans"; farklıysa Level B'ye çıkar.
5. **Semantik yedek kuralı:** yfinance yedeği kalırsa, adjusted-close/timezone/split'in Alpaca/EODHD ile
   eşleştiğini golden'da kanıtla; eşleşmiyorsa yedeği o veri tipi için kapat.

---

## 7. Ne sonuç elde ederiz? (dürüst beklenti)

| Adım | Kanıtlanacak sonuç | Güven |
|---|---|---|
| Probe | Planın intraday/bulk kapsamı **kesin** bilinir (bugün "test edilmedi") | — |
| Bulk_eod günlük otorite | Günlük veri için yüzlerce yfinance çağrısı → **1 çağrı**; günlük fallback biter | Yüksek (doküman + client hazır) |
| Kademeli huni (Yol A) | Intraday çağrısı ~1801 yerine ~hayatta kalan sembole → **büyük hız**, sinyal aynı | Orta-Yüksek (golden ile kanıtlanacak) |
| Semantik tek-otorite | Aynı sembol her koşuda aynı skor → **tekrarlanabilirlik + backtest güveni** | Yüksek |
| 15m kararı (B/C) | Sadeleşme büyük **ama** sinyal değişir → yalnız backtest olumluysa | Düşük (ölçülmeden söz verilmez) |

**Net:** Yol A + bulk_eod günlük otorite = düşük riskle hem **hız** hem **kaynak sadeleşmesi** hem
**tekrarlanabilirlik**; hepsi golden testle "sinyali bozmadan" kanıtlanır. Yol B/C daha büyük sadeleşme
vaat eder ama sinyal-değişikliği olduğundan ayrı backtest ve onay ister — bu belgede **karar verilmez,
seçenek olarak konur.**

---

## 8. Açık sorular / test edilmedi
- EODHD planımızın intraday kapsamı — probe ile kapanır (§6.1).
- `bulk_eod`'un adjusted vs raw close semantiği Alpaca/yfinance ile eşleşiyor mu — golden'da test.
- 15m→5m/1h/kaldır kararının sinyal etkisi — ayrı backtest (Level B).
- Bu belge kod değiştirmez; uygulama §6 sırasıyla, her adım kendi kapısından geçer.

_İlgili: `docs/audits/Scanner_Performans_Audit_2026-07-31.md` (P1.1 kaynağı), FinBERT raporları (sentiment otoritesi kararı)._
