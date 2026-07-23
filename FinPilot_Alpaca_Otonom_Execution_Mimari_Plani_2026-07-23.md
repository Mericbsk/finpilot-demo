# FinPilot — ALPACA PAPER TRADING OTONOM EXECUTION SİSTEMİ
## Mimari Keşif ve İnşa Planı
**Tarih:** 2026-07-23 · **Sürüm:** 1.0 · **Tür:** Mimari plan (kod değil)
**Kapsam sınıfı:** LABS / iç doğrulama motoru — kullanıcı yüzeyine ASLA çıkmaz.

> **Kapsam ve uyum notu (dünkü Re-Audit ile bağ):** Bu sistem konumlandırma kararına göre
> **Labs** işidir; BUY/SELL/stop/TP dili yalnız iç katmanda yaşar, dış yüzey Grade dilinde kalır
> (lint sınırı değişmez). Stratejik değeri büyük: paper fill'ler **karne/doğruluk zincirine dürüst
> outcome verisi** üretir — DoD#5'in (gerçek karne) en sağlam kanıt kaynağı olabilir. Karar bloğu
> (audit R-kuralı): *Uygulama sahibi: C+M · İnşa başlangıcı: Re-Audit P0 listesi kapandıktan sonra ·
> Kanıt: bu plandaki Faz-0 dry-run logu.*

---

## 1. YÖNETİCİ ÖZETİ

İyi haber: sistemin **yarısı zaten yazılmış.** `broker/AlpacaBroker` (Sprint 21) paper ortama emir
gönderebiliyor (market/limit + BRACKET stop/TP), pozisyon/hesap okuyabiliyor ve `AlpacaOrderRepository`
+ `BuySignalRepository` ile audit izi tutuyor. `api/routers/prices.py` Alpaca'dan latest-trade/bar
çekiyor (30 sembol ~300 ms). Scanner export'u **136 alanlık** zengin bir sözleşme üretiyor ve execution
için gereken hemen her şey içinde hazır: `entry_ok`, `execution_feasible/confidence`, `stop_loss`,
`take_profit`, `risk_reward`, `dyn_shares/dyn_notional` (kelly+regime+vol-norm), `position_cap_*`,
`earnings_blackout`, `spread_bps`, `liquidity_ok`, `conviction_tier/prob`, `exit_profiles`.

Eksik olan **orta katman**: (1) sinyali canlı fiyatla doğrulayıp emre çeviren **karar motoru**,
(2) emir yaşam döngüsünü dinleyen **TradingStream** tüketicisi (order update'ler), (3) açık pozisyonları
izleyip **otonom çıkış** veren döngü, (4) Alpaca-hesabı ↔ FinPilot-state **mutabakat** (reconciliation)
mekanizması, (5) **kill switch**. WebSocket market-data denemesi geçmişte yapılmış ve `archive/core_legacy`'ye
kaldırılmış — v1 için market-data tarafında streaming'e gerek YOK (gerekçe Bölüm 7).

Önerilen mimari: **hibrit** — emir/hesap olayları için Alpaca **TradingStream (WebSocket)**, fiyat
kontrolü için **REST polling (30-60 sn)**; tek long-running süpervizör process; SQLite (WAL, ayrı
`data/execution.db`) üzerinde event-sourced state machine; dosya+DM tabanlı kill switch. İnşa 4 fazda,
ilk faz tamamen **dry-run**.

---

## 2. MEVCUT SİSTEM ENVANTERİ (içerden bakış — koddan doğrulandı)

### 2.1 Scanner çıktısı
- **Format:** JSON export — `data/distribution/scan_export_<date>.json` (+`_partial_<id>`), satır başına 136 alan; `scan_id` mevcut. DB'ye değil dosyaya yazılır; olay değil **batch** üretimidir.
- **Sıklık:** Günde 1 tam tarama (şu an manuel tetik; 200'lük batch'ler halinde partial'lar). Gün içi yeniden tarama YOK → sinyaller "sabah adayları"dır.
- **Karar içeriği:** Sinyal bir **aday**dır, emir değildir. Ama iç alanlar yön ve seviyeleri taşır: `direction`, `stop_loss`, `take_profit`, `stop_loss_percent`, `risk_reward`. "Al kararı"nı execution sistemi verecek — scanner'ın işi değil (doğru ayrım, korunmalı).

### 2.2 Veri sözlüğü — execution'ın tüketeceği çekirdek alt küme
| Alan | Tip | Rol | Not |
|---|---|---|---|
| `symbol`, `timestamp`, `scan_id` | str | kimlik | idempotency anahtarının parçası |
| `conviction_tier` (A/B/C), `conviction_prob` | str/float | aksiyon eşiği + öncelik | kalibre olasılık |
| `selection_eligible`, `entry_ok`, `execution_feasible` | bool | üçlü ön-kapı | biri false → aday elenir |
| `execution_confidence`, `execution_reject_reason` | float/str | kapı gerekçesi | loglanır |
| `price`, `entry_drift_pct` | float | referans fiyat + kayma toleransı | canlı fiyatla karşılaştırılır |
| `stop_loss`, `take_profit`, `risk_reward` | float | bracket seviyeleri | broker BRACKET'e doğrudan gider |
| `dyn_shares`, `dyn_notional`, `dyn_position_pct`, `dyn_risk_pct` | float | pozisyon boyutu | kelly+regime+vol-norm — HAZIR, yeniden hesaplanmaz |
| `position_cap_notional`, `position_cap_applied`, `dyn_portfolio_ok` | float/bool | üst sınırlar | risk gate'te ikinci kontrol |
| `spread_bps`, `dollar_adv`, `liquidity_ok` | float/bool | mikroyapı kapısı | spread tavanı Bölüm 4'te |
| `earnings_blackout`, `earnings_proximity`, `market_status` | bool/str | takvim kapısı | blackout → işlem yok |
| `atr_pct`, `vol_regime`, `regime`, `regime_gate_mult` | — | bağlam | time-exit ve boyut ölçeği |
| `exit_profiles`, `ev_per_trade`, `net_expected_return` | — | çıkış/beklenti | haftalık kıyas raporunda |

### 2.3 Var olan yapı taşları
| Bileşen | Durum | Execution'daki rolü |
|---|---|---|
| `broker/AlpacaBroker` | ✅ çalışır (SDK: alpaca-py) | emir gönderme/iptal, pozisyon/hesap okuma, BRACKET |
| `AlpacaOrderRepository`, `BuySignalRepository` | ✅ | audit izi temeli — genişletilecek |
| `api/routers/trade.py` | ✅ manuel | acil manuel müdahale yüzeyi olarak kalır |
| `api/routers/prices.py` (Alpaca REST latest trade/bar) | ✅ | fiyat polling kaynağı (30 sembol ~300 ms) |
| `paper_trading.py` PaperTradingEngine | ⚠️ içsel simülatör, 5 sabit sembol | Alpaca'lı sistemle KARIŞTIRILMAZ; dry-run kıyas aracı olarak kalabilir |
| `core/scheduler` (APScheduler + watchdog) | ✅ | market-saati job'ları buradan |
| `archive/core_legacy/websocket_feeds.py` | 🗄️ ölü | ders: market-data streaming v1'de denenmeyecek |
| `tests/test_broker.py` | ✅ | genişletilecek |
| distribution onay/queue deseni | ✅ | state-machine + admin-DM desenleri kopyalanır |

### 2.4 Sinyalden emre akış (hedef akışın metinsel hali)
```
scan_export (sabah) ─► SignalIngest: eligible+entry_ok+feasible+tier∈{A,B} süz, conviction_prob'a göre sırala
  ─► Decision Engine: canlı fiyat al → drift ≤ eşik? spread ≤ tavan? piyasa açık mı?
    ─► Risk Gate: pozisyon sayısı < N? günlük risk bütçesi? sembol cooldown'da değil mi? nakit yeter mi?
      ─► OrderManager: BRACKET buy (limit) → client_order_id=idempotency anahtarı
        ─► TradingStream: fill/partial/reject/cancel olayları → state güncelle
          ─► PositionMonitor: stop/TP broker'da; time-exit (5. gün) + acil çıkış bizde
            ─► Close → outcome kaydı → karne zincirine dürüst veri
```

### 2.5 Eksik / belirsiz noktalar (inşadan önce cevap ister)
1. `direction` alanı short üretir mi? (v1 kararı: **yalnız long**; short'lar reddedilip loglanır.)
2. `dyn_notional` hangi hesap büyüklüğüne göre kalibre? Paper hesap equity'siyle **yeniden ölçekleme katsayısı** gerekli mi?
3. Gün içi ikinci tarama yapılmadığına göre "gün ortası yeni sinyal" senaryosu v1'de yok — kabul mü? (Öneri: evet, v1 sabah-batch.)
4. `exit_profiles` alanının şeması (tek profil mi, çoklu mu?) — time-exit gününü buradan mı okuyacağız, sabit 5 gün mü?
5. `take_profit` her satırda dolu mu, yoksa bazı adaylarda boş mu? (Boşsa bracket yalnız stop bacağıyla kurulur.)
6. PaperTradingEngine'in tarihsel sonuçları backtest kıyası için taban olarak kullanılacak mı?

---

## 3. ALPACA ENTEGRASYON GEREKSİNİMLERİ

### A. Kimlik & ortam
- Env: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` (mevcut adlar korunur) + **yeni** `FINPILOT_TRADING_MODE=paper` (zorunlu).
- **Paper/live sistemsel garantisi (üç kilit):** (1) `TradingClient(..., paper=True)` sabit kodlu; (2) başlangıçta `client.get_account()` → hesap numarası "P" önekli değilse ve base URL `paper-api.alpaca.markets` içermiyorsa **süreç başlamaz**; (3) `FINPILOT_TRADING_MODE != "paper"` ise başlamaz. Live modu v1 kod tabanında **yoktur** — bayrakla bile açılamaz.
- Anahtar rotasyonu: YONERGE §8'e tabi; anahtarlar yalnız `.env`/panel, log'a asla yazılmaz (maskeleme util'i).

### B. Veri katmanı (market data)
- İzlenecek evren küçük: günlük aday ≤10 + açık pozisyon ≤10 → **≤20 sembol**.
- **REST yeterli:** `StockHistoricalDataClient.get_stock_latest_trade/bar` (mevcut kod) 30-60 sn'de bir; 20 sembol tek istekte. IEX feed'in (ücretsiz plan) gecikmesi bu strateji ufku (5 güne kadar tutma, sabah girişi) için fazlasıyla kabul edilebilir.
- Market-data WebSocket v1'de YOK (arşivdeki başarısız deneme + gereksiz karmaşıklık). v2'de girişi saniye hassasiyetine indirmek istenirse eklenir.
- Reconnect stratejisi REST için basit: exponential backoff (1→2→4→…→60 sn), 5 ardışık hata → `DATA_STALL` eventi → yeni giriş yasağı (mevcut pozisyon izlemesi son bilinen stop'larla broker'da güvende).

### C. Emir katmanı
- **Giriş:** LIMIT buy (limit = `min(scan_price*(1+drift_eşiği), canlı ask yaklaşığı)`) + `OrderClass.BRACKET` (stop = `stop_loss`, TP = `take_profit`). TIF: **DAY** (dolmayan giriş ertesi güne taşınmaz — sabah sinyali bayatlar).
- **Kısmi dolum:** pozisyon state'i `filled_qty` üzerinden yürür; gün sonunda kısmi kalan giriş emri iptal edilir, dolan kısım normal pozisyon muamelesi görür (bracket bacakları Alpaca'da otomatik qty günceller).
- **Red/hata retry:** parametrik hatalarda (fiyat bandı, qty) **retry yok** — `ORDER_REJECTED` + neden logu; ağ/5xx hatalarında idempotent client_order_id ile 3 deneme (backoff). Aynı sembolde günde 2 red → sembol o gün devre dışı.
- **İdempotency:** `client_order_id = "fp-" + sha1(scan_id|symbol|side|YYYY-MM-DD)[:20]` + DB'de UNIQUE. Süreç yeniden başlasa bile mükerrer emir imkânsız.
- Rate limit: Alpaca ~200 istek/dk; bizim tepe yükümüz <20/dk → sorun değil; yine de token-bucket sarmalayıcı (P2).

### D. Hesap/pozisyon katmanı
- **TradingStream (WebSocket)** — tek gerçek zamanlı bağlantı: `trade_updates` (new, fill, partial_fill, canceled, rejected, expired). Kopunca: backoff'lu reconnect + kopukluk penceresi için REST `get_orders(status=all)` **replay** senkronu.
- **Mutabakat (reconciliation):** her 5 dk + her başlangıçta: Alpaca positions/orders ↔ `execution.db` karşılaştır. Fark → `STATE_DRIFT` eventi: Alpaca **her zaman kazanır** (broker = ground truth), yerel state düzeltilir, admin'e DM.

---

## 4. MİMARİ KATMANLAR

| # | Katman | Bileşen (yeni `execution/` paketi) | Girdi → Çıktı | Hata iletimi |
|---|---|---|---|---|
| 1 | Data Ingestion | `signal_ingest.py` · `price_feed.py` | scan_export + REST fiyat → normalize `Signal`/`Tick` | bozuk export → bütünlük kapısı (Re-Audit P0-5 ile ortak kod) → `SYSTEM_ERROR` |
| 2 | Decision Engine | `decision.py` | Signal+Tick → `EntryIntent` / `SIGNAL_REJECTED(reason)` | kural ihlali sessiz değil, nedenli event |
| 3 | Risk Gate | `risk_gate.py` | EntryIntent → onaylı/`RISK_LIMIT_BREACHED` | limit aşımı → intent düşer + sayaç |
| 4 | Order Mgmt | `order_manager.py` (AlpacaBroker'ı sarar) | Intent → `ORDER_SUBMITTED` → stream olayları | reject/timeout → retry politikası |
| 5 | Position & State | `state_store.py` (execution.db) · `position_monitor.py` · `reconciler.py` | fill'ler → pozisyon; koşullar → `EXIT_*` | drift → Alpaca kazanır + DM |
| 6 | Monitoring & Audit | `events.py` (append-only event log) · `daily_report.py` | tüm eventler → DB + günlük özet DM | log yazılamıyorsa sistem DURUR (auditsiz otonomi yok) |
| 7 | Safety | `kill_switch.py` · `guards.py` | tetikler → `KILL_SWITCH_TRIGGERED` → yeni emir yasağı (+ ops. flatten) | insan onayıyla reset |

Katmanlar arası tek veri biçimi: **event** (Bölüm 5'teki şema). Karar motoru broker'ı bilmez; order manager kural bilmez — test edilebilirlik bundan çıkar.

---

## 5. EVENT AKIŞ TASARIMI

Tam zincir (mutlu yol + sapmalar):
```
SCANNER_SIGNAL_RECEIVED (ingest; scan satırı)
 ├─► SIGNAL_REJECTED {reason: not_eligible|tier_C|blackout|illiquid|short_not_supported}  [terminal]
 └─► SIGNAL_VALIDATED (decision'a aday listesi, öncelik=conviction_prob desc)
       └─(polling döngüsü)─► MARKET_DATA_UPDATE {sym, last, spread_est, ts}
             ├─► SIGNAL_EXPIRED {reason: drift>eşik|gün_sonu}                            [terminal]
             └─► ENTRY_CONDITION_MET {sym, ref_price, live_price}
                   └─► (Risk Gate) ─► RISK_LIMIT_BREACHED {which_limit}  → intent düşer
                   └─► ORDER_SUBMITTED {client_order_id, qty, limit, bracket{stop,tp}}
                         ├─► ORDER_REJECTED {alpaca_reason} → (retry? sembol cooldown?)
                         ├─► ORDER_CANCELED {by: eod_sweep|manual}
                         ├─► ORDER_PARTIAL_FILL {filled_qty} ─┐
                         └─► ORDER_FILLED {avg_price} ────────┴─► POSITION_OPENED
                                └─(monitor: stream + 60sn poll + günlük EOD kontrol)
                                      ├─► EXIT_CONDITION_MET {type: stop_hit|tp_hit}   (broker bracket'i tetikler,
                                      │      biz stream'den öğreniriz → doğrudan POSITION_CLOSED)
                                      ├─► EXIT_CONDITION_MET {type: time_exit_day5} ─► ORDER_SUBMITTED(sell, market, DAY)
                                      └─► KILL_SWITCH_TRIGGERED ─► (ops.) tüm pozisyonlar market-close
                                            └─► POSITION_CLOSED {pnl, hold_days, exit_type}
                                                  └─► outcome kaydı → karne/doğruluk zinciri
Paralel bekçiler:
  RECONCILE_TICK (5 dk) ─► STATE_DRIFT {diff} ─► yerel düzeltme + ADMIN_DM
  SYSTEM_ERROR / RECONNECT_NEEDED ─► backoff; 5 ardışık ─► DATA_STALL ─► yeni giriş yasağı
```
Her event: `{event_id, ts_utc, type, symbol?, payload_json, actor(layer), correlation_id(=client_order_id|scan_id)}` — üreten katman yazar, dinleyenler DB'den değil süreç-içi kuyruktan alır; DB append-only kopyadır.

---

## 6. SELF-MANAGEMENT MEKANİZMALARI

| Mekanizma | Tetik | Aksiyon | Log | İnsan? |
|---|---|---|---|---|
| Sürekli izleme | süpervizör loop, piyasa açıkken | ingest→decision→monitor döngüsü | heartbeat/5 dk | hayır |
| Oto-reconnect | stream kopması / REST hatası | backoff + replay senkron | RECONNECT_NEEDED | 15 dk'yı aşarsa DM |
| Otonom karar | yeni doğrulanmış sinyal | kapılar geçildiyse emir — onay beklemez | tam karar zinciri | hayır (tasarım gereği) |
| Otonom çıkış | stop/TP (broker) · 5. gün EOD (biz) | bracket / market-sell | EXIT_* | hayır |
| Self-heal state | reconciliation farkı | Alpaca'yı kabul et, yereli düzelt | STATE_DRIFT | DM (bilgi) |
| Sembol karantina | aynı sembolde 2 red/gün veya 3 red/hafta | 1 gün / 1 hafta devre dışı | SYMBOL_QUARANTINED | hayır |
| Günlük sınırlar | >15 emir/gün · yeni-pozisyon riski > günlük bütçe | yeni giriş yasağı (çıkışlar serbest) | RISK_LIMIT_BREACHED | DM |
| Anomali freni | 10 dk'da >5 hata · equity günde >%3 düşüş | **oto kill switch** (yeni emir yok; pozisyonlar bracket'li kalır) | KILL_SWITCH_TRIGGERED | reset elle |

---

## 7. ÇALIŞMA MODU VE ZAMANLAMA KARARI

- **Long-running tek süreç** (`python -m execution.supervisor`), piyasa saatlerinde aktif; APScheduler değil kendi loop'u + `market_calendar` (mevcut util). Sebep: dakikalar içinde tepki + stream dinleme periyodik job'a sığmaz.
- **Hibrit karar: TradingStream=WebSocket (emir olayları) + fiyat=REST polling.** Gerekçe: ≤20 sembol, giriş kararı sabah-batch, tutma 5 güne kadar → saniyelik fiyat verisinin karara katkısı sıfıra yakın; buna karşılık emir fill'ini geç öğrenmek state'i bozar → stream oraya.
- Aralıklar: giriş penceresinde (açılış+15 dk → 12:00 NY) fiyat 30 sn; öğleden sonra 60 sn; pozisyon yoksa 5 dk.
- **Pre/after-hours: işlem YOK** (TIF=DAY zaten garanti eder); gap'ler sabah değerlendirilir.
- Hafta sonu/tatil: süreç uyur (`market_calendar`); Pazartesi sabahı state'i reconcile ederek uyanır.
- Scanner senkronu: manuel yayın akışıyla uyumlu — `publish_now.py` sonrası (veya export mtime değişince) ingest tetiklenir; execution scanner'ı BEKLEMEZ, yoksa o gün işlem yapmaz (dürüst boş gün).

## 8. TEST VE DOĞRULAMA PLANI (paper ortamında)

| # | Test | Başarı kriteri | Metrik | Başarısızlıkta |
|---|---|---|---|---|
| 1 | Dry-run (1 hafta) | 0 gerçek emir; karar logları eksiksiz; "gönderilecekti" kayıtları eldeki fiyatlarla tutarlı | karar sayısı, reject dağılımı | kural eşiklerini revize, tekrar |
| 2 | Tekli sinyal E2E | 1 sembol: sinyal→fill→(stop|tp|day5)→closed; state=Alpaca | zincir tamlığı, latency | kırılan katmana birim test ekle |
| 3 | Eşzamanlılık | 5+ sinyal aynı sabah: öncelik sırası doğru, limit N aşılmıyor, çifte emir yok | pozisyon sayısı, idempotency ihlali=0 | kuyruk/kilit düzelt |
| 4 | Kesinti | stream 10 dk kes: replay sonrası state farkı=0 | drift sayısı | replay mantığı düzelt |
| 5 | Hatalı emir | zorla reject (geçersiz qty): karantina çalışıyor, retry fırtınası yok | red→emir oranı | guard düzelt |
| 6 | Risk limiti | limit N'e dayat: N+1. giriş bloklanıyor, event doğru | breach eventi | gate düzelt |
| 7 | Stabilite (2 hafta) | kesintisiz; bellek düz; her gün heartbeat + günlük özet DM | uptime, hata/gün | süpervizör restart politikası |
| 8 | Paper vs backtest | 4 hafta sonunda: hit-rate & ortalama getiri, backtest bandının ±1 std içinde; slippage ölçülür | hit, PF, exp., slippage bps | sapma analizi → eşik/boyut revizyonu |

Sıra: 1→2→3→5→6→4→7→8. 1-6 geçmeden 7 başlamaz; 7 geçmeden "otonom" etiketi kullanılmaz.

## 9. LOG / VERİ ŞEMASI (`data/execution.db`, WAL — audit + performans analizi tabanı)

```
exec_events    (event_id PK, ts_utc, type, symbol, correlation_id, actor, payload_json)   -- append-only
exec_signals   (scan_id, symbol, date, tier, prob, ref_price, stop, tp, dyn_shares,
                gates_json, status[validated|rejected|expired|acted], reject_reason)
exec_orders    (client_order_id PK UNIQUE, alpaca_order_id, symbol, side, qty, limit_px,
                bracket_json, status, submitted_ts, filled_qty, avg_fill_px, closed_ts, raw_json)
exec_positions (position_id PK, symbol, entry_order_id FK, qty, avg_entry, stop, tp,
                opened_ts, exit_type[stop|tp|time|kill|manual], exit_px, closed_ts,
                pnl_usd, pnl_pct, hold_days, scan_id)      -- karne beslemesi buradan
exec_daily     (date PK, signals, validated, orders, fills, rejects, open_pos_eod,
                realized_pnl, equity_eod, max_intraday_dd, kill_events, notes)
exec_quarantine(symbol, reason, since_ts, until_ts)
```
Kurallar: her tablo yalnız kendi katmanınca yazılır · `payload/raw_json` ham Alpaca cevabını saklar (uyuşmazlık analizi) · haftalık job `exec_positions` → backtest beklentisi kıyas raporu (mevcut `weekly_paper_trading_report.py` bu şemaya taşınır) · `exec_positions.scan_id` karne zincirine köprüdür.

## 10. RİSK VE GÜVENLİK KONTROL LİSTESİ (net cevaplar)

- **Anahtarlar:** `.env` + panel; YONERGE §8; log maskesi; repo'da asla. ✔
- **Canlı hesap riski:** üç kilit (Bölüm 3A) + live kodu v1'de yok → yanlışlıkla canlıya bağlanmak **kod düzeyinde imkânsız**. ✔
- **Çökme anında pozisyonlar:** bracket stop/TP **broker tarafında** yaşar → süreç ölse de koruma durur; restart'ta reconciliation state'i geri kurar. ✔
- **Mükerrer emir:** deterministik client_order_id + DB UNIQUE + Alpaca'nın aynı-id reddi → çift katman idempotency. ✔
- **Rate limit:** tepe <20 istek/dk « 200 limit; token-bucket yine de eklenir (P2). ✔
- **Kill switch kim/nasıl:** (1) `data/KILL` dosyası (Meriç, tek dokunuş), (2) admin-DM komutu `DURDUR` (bot runner'daki admin-gate deseni), (3) oto-tetikler (Bölüm 6). Reset yalnız elle. ✔

## 11. İNŞA SIRASI (P0→P3) — Re-Audit P0 listesi kapandıktan sonra başlar

| Faz | İş | Efor | Çıkış kriteri |
|---|---|---|---|
| **P0 — İskelet + Dry-run** | `execution/` paketi: ingest + decision + risk gate + event log + süpervizör (emir YOK, "would_submit" logu) + paper-guard üç kilit + kill switch dosyası | 2-3 gün | Test 1 (1 hafta dry-run) temiz |
| **P1 — Gerçek paper emir** | order_manager (BRACKET) + TradingStream tüketicisi + reconciler + idempotency + EOD sweep | 2-3 gün | Test 2-6 geçti |
| **P2 — Dayanıklılık** | karantina, günlük limitler, oto-kill, token-bucket, heartbeat + günlük özet DM, restart politikası | 1-2 gün | Test 7 (2 hafta) geçti |
| **P3 — Analitik köprü** | haftalık paper-vs-backtest raporu + `exec_positions`→karne beslemesi + dashboard Labs paneli (read-only) | 1-2 gün | Test 8 raporu üretiliyor |

**Sertlik kuralları uyum beyanı:** mimari önce (bu doküman) · paper/live sistemsel ayrım (üç kilit) · her karar event'li ve açıklanabilir (append-only) · kill switch P0'da, "hazır" tanımının parçası · kesinti senaryosu tasarlandı (Test 4) · risk kontrolü emirden ÖNCE (Katman 3, Katman 4'ün önünde) · paper-vs-backtest farkı haftalık izlenir (Test 8) · hedef "çalışıyor" değil, "güvenli ve tutarlı çalışıyor".
