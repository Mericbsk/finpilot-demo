# FinPilot Scanner — Net Değişim Planı

**Tarih:** 2026-07-15
**Dayanak:** Bugünkü ~30 test + P0 execution replay + peer-review. Nihai karar: yön volatilite-odaklı ve doğru; ama production ağırlık switch'i forward-P&L kanıtına bağlı. Bu plan "neyi, hangi sırayla, hangi dosyada, geri alınabilir mi" sorularını netleştirir.

---

## 0. İlke (neden böyle)

- **En iyi backtest skoru ≠ karar.** Karar metriği = maliyet-sonrası execution P&L + zaman istikrarı + veri kalitesi.
- **Precision ≠ realized P&L.** Volatil isim bulmak (V2 güçlü) ile o hareketi kârlı trade etmek ayrı problem.
- **Değişiklikler geri alınabilir (env-gate).** Production sert switch YOK; shadow'da kanıt topla.

---

## 1. DEĞİŞTİRMEYECEKLER (bilinçli — overfit'ten kaçınmak için)

| Yapılmayacak | Neden |
|---|---|
| Production skor ağırlıklarını sert değiştirmek | Validation negatif, küçük-n, eksik data-contract |
| Yeni threshold sweep aramak | Çoklu-test bias; en iyi kombolar (%81) zaten reddedildi |
| V2'yi production hard-filter yapmak | Forward-P&L kanıtı yok |
| `first_signal_only` | 0/3 rolling pozitif — reddedildi |
| Sektör / persistence / haber-akışı filtresi | Test edildi, katkı yok / look-ahead |
| `gap>=3`'ü zorunlu hard gate yapmak | Örneklemi aşırı küçültüyor; gap etkileşim (gap×RVOL) olarak kullanılmalı |
| Eksik veriyi (spread/short) sıfır varsaymak | Backtest'in yalanı tam burada |

---

## 2. HEMEN YAPILACAKLAR (kesin, güvenli, geri alınabilir)

| # | Değişiklik | Dosya / config | Durum |
|---|---|---|---|
| 2.1 | Kırık legacy composite'i RANKING'den çıkar (silme, guard flag) | `.env`: `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=false` | yeni flag |
| 2.2 | Üç skoru da HESAPLAMAYA devam et (legacy_composite / legacy_quality / v2) — telemetry'de tut | `score_engine.py` + `telemetry.py` | kuruldu, koru |
| 2.3 | Her sinyale `reject_reason[]` + `score_component_breakdown` | `evaluate.py` (P0) | kuruldu |
| 2.4 | Her sinyale `execution_confidence` (Tier 0/1/2) + `data_quality_tier` | `evaluate.py` | eklenecek |
| 2.5 | Parity testi: legacy composite kapalıyken risk engine / sizing / exit / telemetry değişmemeli | `tests/` | eklenecek |
| 2.6 | Conviction prob'ları gerçeğe çek (A=0.73, B=0.59, C=0.52) | `features.py` `_CONV_PROB` | eklenecek |

Not: ALPHA_V2 skor + sıkı kapı + tier + scan_summary zaten `FINPILOT_ENABLE_ALPHA_V2` arkasında ve env-gate'te. Bunlar korunur; production kararı yine shadow'a bağlı.

---

## 3. SCANNER AKIŞINDA YAPISAL DEĞİŞİKLİK (iki aşamalı mimari)

Yeni karar akışı (tek skorla "al" YOK):

```
1. Data quality gate      → eksik veri = düşük kalite/reject (sıfır değil)
2. Execution feasibility  → spread/ADV varsa zorunlu; yoksa execution_confidence=low
3. Regime policy          → seçicilik seviyesi belirler (al/alma DEĞİL)
4. Ranking                → legacy_quality VE v2 paralel hesaplanır
5. Top-N + portföy limiti → pozisyon ≤ %0.5 dollar_ADV_20d
6. Kilitli exit           → shadow config'te SABİT (TP/SL değişmez)
7. Paper/shadow logging   → reddedilenler DAHİL (selection bias önle)
```

Uygulama: mevcut `evaluate_symbol()` → çıktı sözleşmesine data/execution katmanı + üç skor + tier eklenir; seçim/tavan `scan_summary` / alert katmanında kalır.

---

## 4. SHADOW'DA YARIŞTIRILACAKLAR (3 strateji ID, paralel)

Aynı sinyal günleri, aynı maliyetler, aynı KİLİTLİ exit ile:

| Strateji ID | Tanım | Rol |
|---|---|---|
| `legacy_quality` | onarılmış volatilite formülü | baseline şampiyon |
| `v2` | 4×short+3×ATR+3×gap+2×RVOL−1.5×ext | ana aday |
| `v2_atr4_rvol2` | v2 top-10% + ATR≥4 + RVOL≥2 | yüksek-tavan/yüksek-varyans, düşük-güven |

Her sinyal için loglanacak: symbol, date, legacy_quality_score/rank/selected, v2_score/rank/selected, selected_by_both/legacy_only/v2_only, exit_profile, entry_quote, spread, ADV, actual_fill, slippage, commission, exit_reason, net_pnl, execution_confidence.

Nihai soru: "V2 çalışıyor mu?" DEĞİL → **"Aynı koşulda legacy_quality mi V2 mi daha iyi net P&L?"**

---

## 5. EXIT KARARI (production'a almadan ÖNCE kesinleştir)

Aynı source + canonical universe + score cut + selected rows + slippage + commission + horizon; **sadece TP/SL değişecek:**

| Exit | Amaç |
|---|---|
| TP 5× / SL 1× | mevcut en iyi aday (+%2.05) |
| TP 5× / SL 1.5× | önceki birleşik runner baseline (−%0.005) |
| TP 3× / SL 1× | erken realize alternatifi |
| TP 5× / SL 2× | geniş stop duyarlılığı |

Kural: araştırmada exit seçilebilir; **shadow'da exit SABİT.** `5×/1×` ile `5×/1.5x` aynı replay'de kesinleşmeden V2 exit'i production'a aktarılmaz. (Sonraki tur: rejim × exit — sıkı stop sakin rejimde, geniş volatilde mi.)

---

## 6. VERİ KADEMELİ EKLENECEK (execution_confidence yükseltir)

| Tier | Alanlar | Etki |
|---|---|---|
| **Tier 0 (şimdi başlar)** | price, ATR, RVOL, gap, short_value, dist52, ADV-proxy, feature_ts, entry_drift | ranking/sinyal-sayısı/fiyat-yolu/teorik-execution ölçülür |
| **Tier 1 (kısmi)** | ADV var; spread/short-freshness yok | analizde tut, `execution_confidence=low` |
| **Tier 2 (production)** | bid/ask, quote_ts, spread_bps, short_interest_ts, corporate_action | gerçek production adayı |

Eksik veri → sıfır DEĞİL, düşük-kalite/reject. Shadow tüm sistemi bekletmeden Tier 0 ile bugün başlar.

---

## 7. PRODUCTION'A GEÇİŞ KOŞULU (hepsi birlikte)

Bir strateji production'a ancak şu koşulda geçer:

**İstatistiksel:** ≥3 bağımsız rolling OOS penceresi · ≥2 farklı volatilite rejimi · pencere başına yeterli n · bootstrap/Wilson alt sınır pozitif · tek döneme bağımlı değil.
**Finansal:** net expectancy pozitif · PF > 1.2 · spread/impact stresi altında PF > 1 · max drawdown kabul edilebilir · exit profiliyle tutarlı · time-exit oranı kontrol.
**Operasyonel:** spread coverage yüksek · short timestamp coverage yüksek · feature age eksiksiz · entry drift düşük · corporate action biliniyor · signal-to-fill ölçülüyor.

Mevcut veride hiçbir V2 adayı bu koşulu sağlamıyor → shadow şart.

---

## 8. UYGULAMA SIRASI (net)

1. **Hemen:** kırık composite ranking'i kapat (guard flag); üç skoru telemetry'de tut; execution_confidence + data_tier alanları; conviction prob düzelt; parity testi.
2. **Exit'i kesinleştir:** 5×/1× vs 5×/1.5× aynı seçili satırlarda; shadow'a tek sabit exit yaz.
3. **Shadow başlat:** legacy_quality / v2 / v2_atr4_rvol2 → 3 paralel strateji ID; reddedilenler dahil logla.
4. **Veri kademeli:** önce ADV/feature-age/entry-drift → sonra bid/ask/spread → en son historical-short-ts/corporate-action.
5. **Karar:** Bölüm 7 koşulunu sağlayan strateji production'a; sağlamayan shadow'da kalır. Rollback her an mümkün (flag).

**Tek cümle:** Yeni ağırlık arama; volatilite-odaklı + quality-gated + execution-first + iki-stratejili shadow mimarisini kur, exit'i doğrula-ve-kilitle, V2'yi legacy_quality'ye karşı gerçek forward-P&L'de kazanana kadar production'a alma.
