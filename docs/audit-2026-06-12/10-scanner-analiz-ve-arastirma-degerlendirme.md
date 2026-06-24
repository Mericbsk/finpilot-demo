# FinPilot Scanner — Tam Analiz + İki Araştırma Dosyasının Değerlendirmesi ve Yol Haritası

**Tarih:** 2026-06-12 · **Kaynaklar:** `scanner/` kodu (signals, score_engine, evaluate, features, catalyst, risk_engine, position_sizer, config) + iki yüklenen araştırma dosyası (Doc1: "Pre-Event Momentum Research Framework", Doc2: "Untitled / FinPilot Architecture v2.0").

> **Uyarı:** Aşağıdaki her şey araştırma ve sistem-tasarımı değerlendirmesidir, yatırım tavsiyesi değildir. Bahsedilen hipotezlerin hiçbiri canlı veriyle doğrulanmış *edge* değildir; sistemin kendi iç denetimi (Profit Core, 2026-05-23) skorun pozitif edge üretmediğini buldu. Mikro/küçük-kap patlama ticareti yapısal olarak yüksek risklidir.

---

## 1. YÖNETİCİ ÖZETİ

**İki araştırma dosyası da aynı mimariyi anlatıyor:** son 2-3 günde patlayan veya patlamak üzere olan (özellikle mikro/küçük-kap) hisseleri, hareket *görünür olmadan önce* yakalamak. 8 sinyal kategorisi (hacim/fiyat hızlanması, katalizör, float/short, sektör rejimi, breakout yapısı, order-flow/mikroyapı, sosyal, tarihsel analog), 4 seviyeli kanıt hiyerarşisi, 0-100 fırsat skoru, 8 false-positive filtresi ve 12 adımlı otomatik pipeline. Doc1 daha akademik ve atıflı; Doc2 daha agresif, eşik-spesifik (Float<15M, RVOL>4, OFI>0.65) ve micro-cap odaklı.

**En önemli tespit — iki farklı oyun:** Mevcut scanner ile araştırma dosyaları **aynı şeyi hedeflemiyor.**
- **Mevcut scanner** = likit hisselerde *trend-devamı doğrulayıcısı*: çok-zaman-dilimli EMA hizalaması + momentum confluence + RSI/MACD/hacim teyidi. "Bu temiz bir yükseliş trendi mi?" sorusunu sorar → momentum *zaten oluştuktan sonra* yakalar.
- **Araştırma dosyaları** = mikro/küçük-kap *pre-event setup dedektörü*: "Bu patlama olmadan önce hangi birleşik sinyaller haber verdi?" → momentum *görünür olmadan önce* yakalamayı hedefler.

Bu, scanner master prompt'unun "WAIT/no-trade da bir karardır, geç girişi ayıkla" temasının ta kendisi. Mevcut sistem yapısal olarak "geç giren teyitçi"; araştırma "erken giren avcı" istiyor.

**İkinci en önemli tespit — sistem zaten yarısını içeriyor:** Scanner, araştırma dosyalarının önerdiği bileşenlerin çoğunu **kod düzeyinde zaten barındırıyor ama `env-gated KAPALI`:**
- `compute_squeeze_factor` (float + short% → 0-1 squeeze skoru) — `FINPILOT_ENABLE_SQUEEZE_FACTOR=0`
- `scanner/catalyst.py` (SEC EDGAR 8-K/Form4 bullish, S-1/424B dilution bearish, cache'li) — `FINPILOT_ENABLE_EDGAR_CATALYST=0`
- `compute_lottery_factor` (Bali-Cakıcı-Whitelaw MAX etkisi — aşırı uçucu/parabolik fade cezası) — `FINPILOT_ENABLE_LOTTERY_FADE=0`
- `compute_overnight_gap_factor` (gap-up reversal cezası) — `FINPILOT_ENABLE_OVERNIGHT_GAP=0`
- `compute_sector_rs` (sektör göreli güç), `compute_vol_regime`, FRED makro çarpanı, Yang-Zhang volatilite.

Yani araştırma dosyalarının "yeni fikir" sandığı şeylerin %60'ı **inşa edilmiş, açılmayı ve doğrulanmayı bekliyor.** Açılmama sebebi doğru: `component_ablation` marjinal lift'i doğrulamadan canlı skoru bozmamak (disiplinli karar).

**Üçüncü tespit — veri tavanı gerçek:** Araştırma dosyalarının en yüksek-güven sinyalleri (OFI, Level 2/3 order book, gerçek short interest/CTB/Ortex, OPRA opsiyon akışı) **FinPilot'un sahip olmadığı ve ucuza edinemeyeceği** veriyi gerektiriyor. FinPilot'ta yfinance + Alpaca (bar verisi, full L2 değil) + SEC EDGAR (var) + kısmi sosyal var. Dolayısıyla dosyalardaki "Seviye 1 doğrudan kanıt" diye sunulan OFI aslında FinPilot için "Seviye 4 proxy" (VWAP reclaim, up/down-tick bar hacmi). Bu farkı kabul etmeyen her plan kâğıt üstünde kalır.

**Sonuç stratejisi:** Araştırmayı **hedef mimari** olarak benimse, ama (a) mevcut trend-scanner'a cıvatalama — onun varsayımlarıyla çelişir; bunun yerine **ikinci bir scanner modu** ("Pre-Event / Explosive") ekle; (b) yalnız ulaşılabilir %60'ı dürüst proxy etiketiyle uygula; (c) her bileşeni canlıya almadan önce `outcomes_horizon` üzerinde geriye-test et. Önce ölç, sonra aç.

---

## 2. MEVCUT SCANNER MANTIĞININ ÇÖZÜMÜ (koddan)

**Akış (`evaluate.evaluate_symbol`):**
1. Günlük DD gate (>%3 → sinyal yok).
2. Çok-zaman-dilimli veri (15m / 4h / 1d), Alpaca bulk → yfinance fallback.
3. Sinyal bileşenleri: `signal_score_row` (Bollinger + RSI[30-70] + MACD histogram + hacim → 0-3 "score"), `check_volume_spike`, `analyze_price_momentum` (z-score, dinamik kuantil eşik), `check_trend_strength`, `check_timeframe_alignment` (15m/4h/1d EMA), `check_momentum_confluence`.
4. Composite skor (`compute_recommendation_score`, tavan 16.5): regime(2) + direction(2) + score×0.5 + filter_score×1.5 + alignment×2 + momentum_ratio×{2.5/2.0/1.5 vol-rejime göre} + volume_spike/price_momentum/trend_strength(0.5'er) + sentiment(±0.5) ± gated faktörler. → 0-100'e ölçeklenir.
5. `entry_ok` = score==3 (RSI/MACD/hacim kapısı) ∧ liquidity_ok ∧ market safe ∧ earnings blackout değil.
6. Rejim × skor-bandı gate (2026-06-12 barrier audit, n=4066): Bear Q2 (30-55) ×1.3 boost, Bear/Bull yüksek-skor (>58) ×0.5/×0.75 baskı.
7. Risk yönetimi (`calculate_risk_management`): ATR (veya Yang-Zhang) tabanlı stop/tp1/tp2/tp3, strateji etiketi (Sniper score≥70 / Normal / Defansif <50), R/R.
8. Kelly oranlı dinamik pozisyon boyutu, rejim-adaptif.
9. Maliyet-farkında net beklenen getiri + edge etiketi (negative / edge_decay / thin_edge / ok).

**Çıktı:** `entry_ok` (bool) + composite_score + R/R + stop/tp + reason metni ("Alınır: ... | R/R | SL/TP" veya "Bekleyin: Eksik Hacim,Momentum").

---

## 3. ŞU ANKİ TAKTİKLER VE ÖRTÜK VARSAYIMLAR

**Sinyal aileleri (gerçekte aktif):** Trend (EMA hizalama, çok-zaman-dilimi), momentum (z-score, confluence), MA uyumu, hacim spike, Bollinger/RSI/MACD teyidi. **Aktif DEĞİL (gated):** float/short squeeze, SEC katalizör, lottery fade, overnight gap, sektör RS. **Hiç yok:** order-flow/OFI, L2 derinlik, opsiyon akışı, DTW analog, sosyal (scanner'da; agents tarafında kısmi).

**Karar tipleri:** Aslında ikili — `entry_ok=True` (AL) veya değil (BEKLE). Gerçek bir **SELL/EXIT yok** (scanner long-only setup bulucu; çıkış paper-trading/risk tarafında). WAIT örtük ("eksik X"). FILTER/SUPPRESS var (liquidity, blackout, rejim gate ×0.5).

**Örtük varsayımlar:** (1) "Güçlü hizalı trend = iyi aday" — momentum continuation edge teorisi. (2) "Yüksek composite = daha iyi" — ama barrier audit bunu KISMEN çürüttü (yüksek skor bazı rejimlerde düşük win-rate → suppress eklendi; bu dürüst bir düzeltme). (3) Likidite tabanı ($2 fiyat, 300k hacim) → mikro-kap'ı dışlar. (4) Tek skor + tek eşik her hisseye uygulanır (setup-türü ayrımı yok).

**Scanner'ın "psikolojisi":** Temkinli-teyitçi. Trend kovalamaya meyilli ama rejim gate ve lottery/overnight (açılırsa) bunu dengeliyor. Reversal'ı setup olarak görmüyor (yalnız ceza olarak). **Yakaladığı tipik hisse:** likit, çok-zaman-diliminde hizalı, momentumu *zaten başlamış* orta/büyük-kap → araştırmanın "geç gelen işaret" dediği bölge.

---

## 4. STRATEJİ BAZLI ANALİZ — neler yanlış, neden

| Hata sınıfı | Mevcut durumda kanıt | Sonuç |
|---|---|---|
| **Strateji-seçim** | Tek composite skor trend + reversal + breakout'u körce karıştırıyor; setup-türü yok | Farklı edge'ler tek sayıda erir, hiçbiri net ölçülemez |
| **Rejim** | Rejim gate VAR (iyi) ama yalnız bull/bear × skor-bandı; trend-vs-mean-reversion rejimi (Hurst, jump model) yok | Mean-reversion rejiminde breakout sinyali baskılanmıyor |
| **Ölçüm** | Profit Core: decile_lift 0.728 (edge yok); composite estetik teknik-uyumu ölçüyor, edge değil | Ana skor istatistiksel olarak ileri getiriyi ayıramıyor |
| **Etiketleme** | `outcomes_horizon` (T+3/5/10) eklendi ama triple-barrier (TP/SL/time ayrı bariyer) tam değil; path-dependency kısmi | Sinyal kalitesi tek-ufuk getiriyle ölçülüyor, yol bağımlılığı eksik |
| **Aksiyon** | entry_ok ikili; gerçek SELL/EXIT yok, setup-spesifik çıkış yok | "Doğru hissede yanlış zamanda çıkış" riski scanner'da yönetilmiyor |
| **Veri katmanı** | OFI / L2 / gerçek short / opsiyon yok; squeeze yfinance proxy'siyle (stale, 2-haftada bir) | Araştırmanın en yüksek-güven sinyalleri ya yok ya zayıf proxy |

---

## 5. AL / SAT / BEKLE KARAR AĞACI (önerilen — setup-türü bazlı)

Araştırma dosyalarının istediği ve scanner master prompt'unun vurguladığı yapı: tek skor değil, **setup türü + rejim + confidence + aksiyon**.

```
GİRİŞ: aday (RVOL↑ veya gap veya squeeze flag)
  │
  ├─ Rejim filtresi (IWM>SMA20 & VIX<18? mean-reversion mi trend mi?)
  │     └─ uyumsuz → WAIT(regime) / size ×0.5
  ▼
  Setup sınıflandırma:
  ├─ BREAKOUT  : vol-contraction(≥14g) sonra range+volume expansion →
  │     AL şartı: temiz seviye kırılımı + RVOL>3 + (OFI proxy: VWAP reclaim)
  │     Stop: kırılım seviyesi altı / 1.5×ATR ; TP: ölçülü hareket / 3-5×ATR
  ├─ PULLBACK  : trend var + EMA20'ye geri çekiliş → AL: higher-low + hacim kuruması
  ├─ CATALYST  : 8-K/FDA/earnings beat (catalyst.py) → AL: haber + ilk-30dk hacim teyidi
  │     ⚠ dilution (S-1/ATM) tespitinde → SUPPRESS (catalyst.py bunu zaten -ye çeviriyor)
  ├─ SQUEEZE   : float<15M + short>%18 (proxy) → AL: squeeze başlamadan;
  │     ⚠ Volume/Float>3 → exhaustion → SUPPRESS
  ├─ REVERSAL  : aşırı düşüş + absorption → yalnız trend>SMA50 değilse dikkat (dead-cat filtresi)
  └─ hiçbiri / overextended (>%40 EMA20 üstü) → WAIT / SUPPRESS
  ▼
  Validation: meta-label confidence + likidite/spread + analog(DTW) win-rate
  ▼
  AKSİYON: BUY(setup, size, stop, tp, holding) | WAIT(eksik teyit) | SUPPRESS(false-pos)
           | (pozisyon varsa) REDUCE/EXIT(setup bozuldu / time-stop / hedef)
```

**WAIT'in değeri:** Master prompt'un altını çizdiği nokta — kötü sistem her zaman aksiyon üretir. Mevcut scanner `entry_ok=False`'ı pasif "bekle" olarak gösteriyor ama aktif WAIT alt-tipleri (breakout için izle / pullback bekle / teyit bekle / no-trade) yok. Bu, eklenmesi en ucuz ve en değerli katman.

---

## 6. HEDEF / STOP / BEKLEME MANTIĞI

**Mevcut (iyi temel):** ATR/Yang-Zhang ölçekli stop + tp1/tp2/tp3, strateji etiketine göre çarpanlar, R/R. Sabit yüzde KULLANMIYOR — bu doğru (araştırma da volatilite-ölçekli hedefi savunuyor).

**Eksik:** (1) Hedef *setup'a göre* değişmiyor — breakout'un hedefi (ölçülü hareket / range yüksekliği) ile squeeze'in hedefi (önceki tepe / float-bazlı dikey) farklı olmalı. (2) **Triple-Barrier** tam değil: TP/SL/zaman bariyeri ayrı ayrı tanımlanıp hangisinin önce vurduğu etiketlenmeli (López de Prado). `outcomes_horizon` bunun yarısı; tam triple-barrier etiketleme `evaluate`'e girmeli. (3) Holding period hedefle birlikte tasarlanmıyor — squeeze 1-2 gün, PEAD drift 5-10 gün, pullback 3-5 gün.

**"Hedef fiyat bazlı mı, olasılık bazlı mı, karar-kalitesi bazlı mı?" →** Üçü birlikte: fiyat bariyeri (ATR/seviye) *uygulama* için, olasılık (kalibre p_win) *boyutlandırma* için, karar-kalitesi (meta-label confidence + analog win-rate) *AL/WAIT kapısı* için. Scanner bugün yalnız fiyat-bariyeri + kısmi olasılık üretiyor; karar-kalitesi katmanı (meta-labeling) eksik.

---

## 7. İKİ ARAŞTIRMA DOSYASININ DEĞERLENDİRMESİ + GAP ANALİZİ

### 7.1 Doc1 vs Doc2 farkı
- **Doc1 (Pre-Event Momentum):** Akademik, atıflı (momentum burst, OFI HMM, PEAD, microstructure), proxy-katmanı dürüst tanımlı, "setup tespit et, koşmuş hareketi kovalama" vurgusu güçlü. Daha dengeli ve uygulanabilir.
- **Doc2 (Architecture v2.0):** Daha agresif, micro-cap squeeze odaklı, çok spesifik eşikler (Float<12M, OFI>0.68, DTW<0.10) ve yüksek güven yüzdeleri (%92-%99 filtre güveni). Bu kesin yüzdeler **kanıtlanmamış iddialardır** — Doc2'nin en zayıf yanı; eşikler makul başlangıç ama "güven %95" gibi rakamlar backtest'siz kullanılmamalı.
- **Ortak çekirdek (ikisinde de sağlam):** 8 kategori, kanıt hiyerarşisi, opportunity score = pozitif bileşenler − ceza, 8 false-positive filtresi, 12 adımlı pipeline. Bu iskelet doğru ve FinPilot'un mevcut `score_engine` (additive + penalty) yapısıyla uyumlu.

### 7.2 Bileşen bazında FinPilot gap'i

| Araştırma bileşeni | FinPilot durumu | Ulaşılabilirlik (mevcut veri) | Karar |
|---|---|---|---|
| RVOL / hacim hızlanması | Var (volume_spike, z-score momentum) | ✅ Tam (Alpaca/yf bar) | Aç + RVOL'u sürekli skora çevir |
| Range/vol contraction→expansion | Kısmi (ATR var, contraction skoru yok) | ✅ Tam | **Ekle** (ucuz, yüksek değer) |
| Gap analizi | Kısmi (overnight_gap_factor gated) | ✅ Tam | Aç |
| Katalizör (SEC 8-K/Form4/S-1) | **Var** (catalyst.py, cache'li) | ✅ Tam (EDGAR ücretsiz) | **Aç + ablation** |
| Float / short squeeze | **Var** (squeeze_factor) | ⚠️ Zayıf proxy (yfinance stale) | Aç ama "proxy" etiketle; Ortex'siz sınırlı |
| Sektör rejimi | **Var** (sector_rs) | ✅ Tam (ETF bar) | Aç |
| Order-flow / OFI / L2 | **Yok** | ❌ Veri yok (L2 lazım) | Proxy: VWAP reclaim + up/down-tick bar hacmi (Seviye-4 dürüst) |
| Opsiyon akışı / IV skew | Yok | ❌ OPRA lazım | Şimdilik kapsam dışı |
| Sosyal buzz | Agents'ta kısmi (Polymarket/HN/DDG) | ⚠️ Kısmi | Mevcut social agent'ı scanner'a bağla (önce orphan sorunu — bkz. 09 raporu) |
| Tarihsel analog (DTW) | Yok | ✅ Tam (yalnız OHLCV) | **Ekle** (dış veri gerektirmez, yüksek değer) |
| Triple-barrier etiketleme | Yarım (outcomes_horizon) | ✅ Tam | Tamamla |
| Meta-labeling | Yok | ✅ Tam (mevcut feature'lar) | Ekle (López de Prado) |
| False-positive cezaları | Kısmi (lottery, overnight gated; dilution catalyst içinde) | ✅ Çoğu ulaşılabilir | Cezalar paketini aç (liquidity/spread/dilution/pump/overextension) |

**Özet:** Araştırmanın ~%60'ı mevcut veriyle uygulanabilir (RVOL, contraction, gap, katalizör, sektör, DTW analog, triple-barrier, meta-label, ceza paketi); ~%25'i zayıf proxy ile (squeeze, OFI proxy, sosyal); ~%15'i mevcut veriyle imkânsız (gerçek L2/OFI, OPRA opsiyon, Ortex short). Dürüst plan bu üçünü ayırır.

---

## 8. BEN OLSAM NE YAPARDIM — 3 Katmanlı Scanner

**İlke:** Mevcut trend-scanner'ı SİLME (likit trend-devamı için çalışan, kalibre edilmiş bir araç). Yanına **ikinci mod** ekle ve ortak bir karar-katmanında birleştir. Master prompt'un istediği 3 katman:

**A. Discovery Layer (aday bulma) — iki ayrı tarayıcı:**
- *Trend mode* (mevcut): likit, çok-zaman-dilimi hizalı.
- *Pre-event mode* (yeni): RVOL hızlanması + range/vol contraction→expansion + gap + squeeze proxy + katalizör flag + sektör uyumu. Mikro/küçük-kap evrenine açık (ayrı likidite tabanı + spread/ADV ceza paketi şart).

**B. Validation Layer (edge doğrulama — ortak):**
- Rejim filtresi (trend vs mean-reversion; başlangıçta IWM/VIX + vol_regime, sonra Hurst/jump model).
- Meta-labeling: "bu setup geçmişte para kazandırdı mı?" → binary edge-confidence (mevcut feature'lardan eğitilir).
- Likidite/spread/slippage filtresi (slippage_tracker var).
- DTW analog: setup'ı geçmiş kazanan/kaybeden kümelerle eşle → tarihsel win-rate.
- OFI proxy (VWAP reclaim + tick-volume) — dürüst Seviye-4 etiketiyle.

**C. Decision Layer (aksiyon):**
- BUY yalnız doğrulanmış edge'de (meta-label + analog + rejim uyumu).
- Aktif WAIT alt-tipleri.
- Setup-spesifik stop/tp/holding + triple-barrier etiketleme.
- EXIT/REDUCE kuralları (setup bozulması, time-stop, hedef).
- Açıklanabilirlik bloğu: her sinyal "ana sürücü + ana risk + kanıt seviyesi" (araştırmanın çıktı matrisi — UI'da zaten reason alanı var, genişletilir).

**Tasarım ilkeleri (araştırma + master prompt ortak):** Tek skor değil setup+rejim+confidence; her sinyalin açıklanabilir gerekçesi; setup'a göre hedef/stop; false-positive azaltmak sinyal sayısından önemli; scanner karar hazırlar, yalnız bulmaz.

---

## 9. BİLİMSEL TEMEL (araştırma dosyalarının atıfladığı, FinPilot'a uygunluk)

| Yöntem | Katkı | FinPilot'ta nerede / risk |
|---|---|---|
| Short-term momentum vs mean-reversion | Rejime göre strateji seçimi | vol_regime var; turnover/Hurst ayrımı eklenmeli. Risk: rejimi yanlış sınıflama |
| Share turnover / likidite segmentasyonu | Düşük-turnover'da momentum, yüksekte reversal | config segment eşikleri var; turnover-bazlı ayrım eklenmeli |
| PEAD (earnings drift) | Katalizör sonrası 5-10g drift | catalyst.py + earnings_blackout var; drift exploit edilmiyor (blackout'ta dışlanıyor) |
| Triple-Barrier (López de Prado) | TP/SL/time ayrı etiket → doğru outcome | outcomes_horizon yarım; tamamla. Risk: bariyer parametre overfit |
| Meta-labeling | "Sinyal var" ile "trade et" ayrımı; false-pos azaltır | Yok — en yüksek getirili eklenti. Risk: az örnekle overfit |
| Sequential bootstrap / örtüşen etiket | Bağımsız örneklem | Backtest'te eksik; istatistiksel geçerlilik için gerekli |
| Fractional differentiation | Durağanlık + hafıza dengesi | Yok; feature kalitesi için opsiyonel |
| OFI / LOB mikroyapı | En erken kurumsal akış sinyali | **Veri yok**; yalnız proxy. Yanlış kullanımda en pahalı yanılgı |
| Rejim-switching / jump model | Rejim tespiti | Basit rejim var; jump model araştırma adayı |
| Hurst üssü | Trend mi mean-reversion mı | Yok; rejim katmanına aday |
| Volume Profile / POC / HVN-LVN | Seviye-bazlı hedef/stop | Yok; hedef mantığını iyileştirir (bar verisinden türetilebilir) |

**Genel risk:** Bu yöntemlerin çoğu *backtest'te parlayıp canlıda sönen* tekniklerdir (look-ahead, overfit, rejim kayması). Sistemin zaten edge bulamamış olması, "daha fazla feature" değil **daha sıkı doğrulama** gerektiğini söylüyor. Yeni her bileşen ablation + walk-forward + maliyet-sonrası net getiri kapısından geçmeli.

---

## 10. ÖNERİLEN YENİ SCANNER MİMARİSİ (girdi → setup → validation → aksiyon)

**Girdi katmanı:** Fiyat/hacim (1m/5m/15m/1d — var), turnover (türetilebilir), volatilite (Yang-Zhang var), haber/earnings (var), SEC katalizör (var), short/float (yfinance proxy), sektör ETF (var). *Yok:* OFI/L2, opsiyon, gerçek short → proxy veya kapsam dışı.

**Setup Engine:** breakout / pullback / catalyst / squeeze / reversal / no-trade-suppression — her biri ayrı tetik + geçersizlik kuralı.

**Validation Engine:** meta-label confidence + rejim filtresi + likidite/spread filtresi + DTW analog + confluence skoru + OFI-proxy.

**Action Engine:** BUY/WAIT/SELL/REDUCE/SUPPRESS + setup-spesifik hedef/stop/holding + risk-ayarlı boyut + açıklanabilirlik bloğu (ana sürücü, ana risk, kanıt seviyesi, tarihsel analog win-rate).

**Çıktı matrisi (araştırmadan, UI'a):** `| Ticker | Opportunity Score | Setup | Ana sürücü | Ana risk | Kanıt seviyesi | Aksiyon | Stop/TP/Holding |`

---

## 11. ÖNCELİKLENDİRİLMİŞ AKSİYON PLANI (P0 / P1 / P2)

### P0 — Ölç ve mevcut yatırımı aç (1-2 hafta, dış veri gerektirmez)
1. **Triple-barrier etiketlemeyi tamamla** (`evaluate` + `outcomes_horizon`): her sinyale TP/SL/time bariyerinden hangisinin önce vurduğu + path. Edge ölçümünün ön şartı — bu olmadan aşağıdakilerin hiçbiri doğrulanamaz.
2. **Haftalık otomatik Edge Report** (scheduler job): decile_lift, hit-rate, net-getiri; her gated faktör için açık/kapalı A/B. (Önceki raporların P0'ı ile aynı.)
3. **Gated faktörleri ablation ile teker teker aç:** catalyst (en sağlam — SEC ücretsiz, dilution-suppress dahil) → sector_rs → squeeze (proxy etiketiyle) → lottery/overnight. Geçen kalır, geçmeyen kapanır.
4. **Aktif WAIT alt-tipleri + açıklanabilirlik bloğunu** reason alanına ekle (ucuz, kullanıcı değeri yüksek).

### P1 — Yeni edge katmanları (2-4 hafta, mevcut veriyle)
5. **DTW tarihsel analog modülü** (yalnız OHLCV): setup'ı geçmiş kümelerle eşle, tarihsel win-rate üret. Dış veri yok, yüksek değer.
6. **Range/vol contraction→expansion skoru** + RVOL'u sürekli bileşene çevir (breakout setup'ın çekirdeği).
7. **Meta-labeling katmanı:** mevcut feature'lardan "trade-et/etme" binary edge-confidence; BUY kapısına ekle (false-positive'i en çok azaltacak tek adım).
8. **Pre-event mode (ikinci tarayıcı)** iskeleti + mikro-kap evreni + tam ceza paketi (low-liquidity/spread/dilution/pump/overextension). Trend mode'a dokunma.

### P2 — Derinlik ve proxy'ler (4-8 hafta+, doğrulama sonrası)
9. **OFI proxy** (VWAP reclaim + up/down-tick bar hacmi), Seviye-4 dürüst etiketiyle; gerçek L2 yok.
10. **Rejim katmanı derinleştir:** turnover-bazlı momentum/reversal ayrımı + Hurst/jump model araştırması.
11. **Sosyal sinyali scanner'a bağla** (önce orphan agent sorununu çöz — bkz. `09-agent-mimari-analizi.md`).
12. **Setup-spesifik hedef/stop + Volume Profile** seviyeleri.

**Veri yatırımı kararı (ayrı):** Gerçek OFI/L2 (Polygon full-depth), Ortex short, OPRA opsiyon → ancak P0-P1 ulaşılabilir %60 doğrulanmış pozitif edge gösterirse satın al. Önce mevcut veriyle edge kanıtla, sonra pahalı veriye para bağla.

**Tek cümlelik karar:** Araştırma dosyaları mükemmel bir *hedef harita*; FinPilot zaten yarısını inşa etmiş ama açmamış. Yapılacak iş yeni feature yığmak değil — mevcut gated bileşenleri **ölçüp doğrulayarak açmak**, triple-barrier + meta-label ile edge'i nihayet ölçülebilir kılmak, ve mikro-kap pre-event oyununu mevcut trend-scanner'ı bozmadan ayrı bir mod olarak eklemek.
