# FinPilot Morning Trade Report — 2026-05-13 (Çarşamba)

**Görev:** `finpilot-morning-trade` (zamanlanmış otomasyon, 09:35 ET sonrası)
**Çalışma dizini:** `/sessions/cool-peaceful-franklin/mnt/Borsa`
**Mod:** PAPER trading (Alpaca paper) — `broker/__init__.py` `paper=True`
**Sonuç:** **0 emir gönderildi.** Pipeline tarama aşamasında veri çekemediği için erken sonlandı. Bu, 2026-05-08'den beri 4. ardışık iş günü görülen aynı altyapı hatası.

---

## Özet

| Metrik | Değer |
|---|---|
| Alpaca'ya gönderilen emir | **0** |
| Üretilen ham sinyal | 0 (veri çekilemediğinden değerlendirme yapılamadı) |
| Strateji B'den geçen sinyal | 0 |
| Taranan sembol | 0/27 fetched, 27/27 attempted |
| Gap nedeniyle reddedilen sinyal | 0 (bu aşamaya gelinemedi) |
| Risk limiti nedeniyle bloklanan sinyal | 0 (bu aşamaya gelinemedi) |
| Açık pozisyon (Alpaca) | sorgulanamadı — REST API sandbox'tan erişilemiyor (proxy 403) |
| Günlük P&L | n/a (Alpaca'ya erişim yok) |
| `.env` içinde Alpaca anahtarları var mı? | **Evet** (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`, `ALPACA_PAPER`) |
| Process env'de var mı? | **Hayır** — anahtarlar process env'e otomatik enjekte edilmiyor; bu nedenle `has_keys = False` → kontrol mantığı dry-run rotasına düştü |
| Dry-run kullanıldı mı? | **Evet** — process env boş olduğu için |
| Çalıştırılan komut | `python3 scripts/auto_scan_trade.py --once --dry-run` |
| `logs/auto_trade/summary_2026-05-13.json` üretildi mi? | **Manuel yazıldı** — script 0 ham sinyalde erken `return` ettiği için summary'yi kendi yazmadı (kod yolu: `auto_scan_trade.py:716-718`) |
| `logs/slippage_tracker.json` güncellendi mi? | **Hayır** — dosya hâlâ mevcut değil; dolu emir hiç olmadığı için oluşturulmadı |

---

## Karşılaşılan Sorunlar

### 1) `yfinance` modülü scheduled-task sandbox'ında yok ve pip kurulamıyor

Tarama sırasında 27 sembolün her zaman dilimi için aynı hata zinciri tekrar etti:

```
ERROR | scanner.data_fetcher | yfinance beklenmeyen hata (ModuleNotFoundError):
  DDOG 1d 400d - No module named 'yfinance'
... (27 sembol × 4 zaman dilimi)
INFO  | scanner.evaluate     | evaluate_symbols_parallel complete: 0/27 results
INFO  | auto_scan_trade      | Scan complete: 0 results
INFO  | auto_scan_trade      | BUY signals: 0
INFO  | auto_scan_trade      | Bugün BUY sinyali bulunamadı.
```

Çözmek için denenenler:

1. **`pip install yfinance --break-system-packages`** — sandbox'tan PyPI'ya proxy ile çıkış engellendi:
   ```
   ProxyError('Cannot connect to proxy.', OSError('Tunnel connection failed: 403 Forbidden'))
   ```
2. **Proje `.venv` Python'u** — `.venv/bin/python` symlink'i `/usr/local/bin/python` adresine işaret ediyor; sandbox runtime'ında o yol yok. `.venv` Python 3.11 ile kurulmuş, sandbox 3.10 çalıştırıyor.
3. **`.venv/lib/python3.11/site-packages` doğrudan sys.path'e ekleme** — numpy `.so` dosyaları cpython-3.11 ABI için derlenmiş, 3.10'da `ImportError: No module named 'numpy._core._multiarray_umath'` hatası verdi.

### 2) Alpaca paper-api da sandbox'tan erişilemiyor

Doğrudan REST ile hesap/pozisyon sorgusu denendi:

```
HTTPSConnectionPool(host='paper-api.alpaca.markets', port=443):
  ProxyError('Tunnel connection failed: 403 Forbidden')
```

Yani **anahtarlar olsaydı bile** sandbox'tan emir yerleştirilemezdi.

### 3) Process env'de Alpaca anahtarları yok (görev kontrolü dry-run'a düşüyor)

`.env` dosyası diskte mevcut ama scheduled-task sandbox'ı onu shell'e enjekte etmiyor. Görev tanımındaki ön koşul kontrolü:

```python
has_keys = bool(os.environ.get("ALPACA_API_KEY")) and bool(os.environ.get("ALPACA_SECRET_KEY"))
```

bu yüzden `False` döndü ve dry-run yoluna girildi. (Manuel `set -a; source .env` yapsak bile §2'deki proxy engelinden dolayı yine emir gönderilemezdi.)

---

## Çalışan / İncelenen Kod Yolları

| Aşama | Durum | Not |
|---|---|---|
| Process env kontrolü | ⚠️ False döndü | `.env` dosyası mevcut ama otomatik yüklenmedi |
| `scripts/auto_scan_trade.py --once --dry-run` | ⚠️ Çalıştı ama veri yok | Script kendisi bozuk değil |
| `scanner.data_fetcher` (yfinance backend) | ❌ ModuleNotFoundError | Aynı hata 4 gündür |
| `apply_strategy_b()` | ⏭️ Çalıştırılmadı | 0 ham sinyalle erken `return` |
| `place_alpaca_orders()` | ⏭️ Çalıştırılmadı | dry-run + 0 sinyal |
| Risk guard (`risk_YYYY-MM-DD.json`) | ⏭️ Bugün üretilmedi | Son kayıt `risk_2026-05-06.json` (5 pozisyon) |
| `logs/slippage_tracker.json` | ❌ Hâlâ yok | Dolu emir olmadığı için bugüne kadar üretilmedi |

---

## Risk Durumu (en güncel state)

`logs/auto_trade/risk_2026-05-06.json` (sonuncu mevcut snapshot, 7 iş günü öncesinden):

- Açık pozisyon (cache): **5** (AAPL, MSFT, GOOGL, NVDA, TSLA)
- Sektör dağılımı: Tech 3, Semicon 1, Auto 1
- Başlangıç portföyü: 100,000.00 USD
- Max pozisyon limiti (5): **dolmuş** — bu durumda yeni sinyaller zaten risk guard tarafından bloklanırdı

Sandbox dışından Alpaca'ya bağlanılamadığı için bu pozisyonların **hâlâ açık olup olmadığı doğrulanamadı**. Cache stale olabilir (TP/SL'lerle kapanmış olabilir).

---

## Tekrarlayan Failure (Pattern)

Bu görev **4 ardışık iş günü** aynı kök nedenle başarısız oldu:

| Tarih | Run sayısı | Sebep | Çözüldü mü? |
|---|---|---|---|
| 2026-05-08 | 1 | yfinance yok | ❌ |
| 2026-05-11 | 1 | yfinance yok | ❌ |
| 2026-05-12 | 2 (14:53, 17:48) | yfinance yok | ❌ |
| 2026-05-13 | 1 | yfinance yok + Alpaca API da unreachable | ❌ |

Görev kullanıcı müdahalesi olmadan bu hatayı çözemeyecek. **Yapılması gerekenler kullanıcı tarafında**:

1. Scheduled-task sandbox'a kalıcı `yfinance` (+pandas+numpy 3.10-uyumlu) ya da bir Polygon/Alpaca-data fallback fetcher eklenmesi.
2. `.env` dosyasının sandbox shell'ine otomatik yüklenmesi (örn. wrapper script `set -a; source .env; set +a; python ...`).
3. Sandbox'tan `paper-api.alpaca.markets`'in beyaz listeye alınması (proxy 403 düşmesin).
4. Alternatif: `auto_scan_trade.py` 0 ham sinyalde de summary JSON yazsın (kullanıcı failure'ı erkenden görsün).

Bu maddeler tamamlanmadan sabah otomatik emir görevi anlamlı bir çıktı üretemez.

---

## Komut Çıktısı (özet)

```
$ python3 scripts/auto_scan_trade.py --once --dry-run
...
2026-05-13 13:52:28,725 | INFO | scanner.evaluate    | evaluate_symbols_parallel complete: 0/27 results
2026-05-13 13:52:28,730 | INFO | auto_scan_trade     | Scan complete: 0 results
2026-05-13 13:52:28,733 | INFO | auto_scan_trade     | BUY signals: 0
2026-05-13 13:52:28,735 | INFO | auto_scan_trade     | Bugün BUY sinyali bulunamadı.
```

(Üst kısımda 27 sembol × 4 zaman dilimi için `ModuleNotFoundError: No module named 'yfinance'` bloğu.)

---

## Başarı Kriterleri Kontrolü

- ❌ En az 1 emir gönderildi — **Hayır**, ancak açıklama yapıldı (yfinance yok, sandbox proxy Alpaca'yı da engelliyor).
- ⏭️ Risk guard düzgün çalıştı — **Çalıştırılmadı** (önceki aşamada durdu).
- ✅ Log dosyası güncellendi — Bu rapor + manuel `summary_2026-05-13.json` yazıldı.

---

## Çıktılar

- `Borsa/logs/auto_trade/summary_2026-05-13.json` — bugünün scan summary'si (manuel yazıldı)
- `Borsa/FINPILOT_MORNING_TRADE_REPORT_2026-05-13.md` — bu rapor
