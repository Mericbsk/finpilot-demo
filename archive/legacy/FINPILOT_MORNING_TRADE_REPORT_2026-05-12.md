# FinPilot Morning Trade Report — 2026-05-12 (Salı)

**Görev:** `finpilot-morning-trade` (zamanlanmış otomasyon, 09:35 ET sonrası)
**Çalışma dizini:** `/sessions/gifted-beautiful-feynman/mnt/Borsa`
**Mod:** PAPER trading (Alpaca paper) — `broker/__init__.py` `paper=True`
**Sonuç:** **0 emir gönderildi** — pipeline tarama aşamasında veri çekemediği için erken sonlandı (2026-05-11 ile aynı hata zinciri).

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
| Açık pozisyon (Alpaca) | sorgulanmadı (pipeline veriden önce durdu) |
| Günlük P&L | n/a |
| Alpaca anahtarları mevcut mu? | **Evet** — `.env` içinde `ALPACA_API_KEY` ve `ALPACA_SECRET_KEY` var |
| Dry-run kullanıldı mı? | Hayır — anahtarlar mevcut olduğu için gerçek paper modu denendi |
| Çalıştırılan komut | `python scripts/auto_scan_trade.py --once --skip-gap` |
| `logs/auto_trade/summary_2026-05-12.json` üretildi mi? | **Manuel yazıldı** — script 0 ham sinyalde erken `return` ettiği için summary'i kendi yazmadı (kod yolu: `auto_scan_trade.py:716-718`) |
| `logs/slippage_tracker.json` güncellendi mi? | **Hayır** — dosya hâlâ mevcut değil; dolu emir olmadığı için hiç oluşturulmadı |

---

## Karşılaşılan Sorun

### `yfinance` modülü scheduled-task sandbox'ında yok ve pip kurulamıyor

Tarama sırasında 27 sembolün her zaman dilimi için aynı hata zinciri tekrar etti:

```
ERROR | scanner.data_fetcher | yfinance beklenmeyen hata (ModuleNotFoundError):
  DDOG 1d 400d - No module named 'yfinance'
... (27 sembol × 4 zaman dilimi = ~108 hata)
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

Sonuç: Tarama 0 ham sinyalle bitti, Strateji B / gap kontrolü / risk guard aşamalarına hiç girilmedi.

Bu, **2026-05-11 raporundaki ile aynı kök neden**. Dün yazılan note hâlâ geçerli:

> "Re-run from full environment (not scheduled-task sandbox) for valid scan results."

---

## Çalışan / İncelenen Kod Yolları

| Aşama | Durum | Not |
|---|---|---|
| `.env` yükleme | ✅ | `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` set edildi |
| `scripts/auto_scan_trade.py --once --skip-gap` | ⚠️ Çalıştı ama veri yok | Script bozuk değil (dünkü truncation sorunu giderilmiş) |
| `scanner.data_fetcher` (yfinance backend) | ❌ | ModuleNotFoundError |
| `apply_strategy_b()` | ⏭️ Çalıştırılmadı | 0 ham sinyalle erken `return` |
| `place_alpaca_orders()` | ⏭️ Çalıştırılmadı | aynı şekilde |
| Risk guard (`logs/auto_trade/risk_YYYY-MM-DD.json`) | ⏭️ | Bugünün dosyası oluşmadı; son kayıt `risk_2026-05-06.json` (5 pozisyon Tech/Semicon/Auto) |

---

## Risk Durumu (mevcut state'ten)

`logs/auto_trade/risk_2026-05-06.json` (en güncel risk snapshot'ı):

- Açık pozisyon (state cache): 5 (AAPL, MSFT, GOOGL, NVDA, TSLA)
- Sektör dağılımı: Tech 3, Semicon 1, Auto 1
- Başlangıç portföyü: $100 000
- 2026-05-07 → 2026-05-12 arası yeni risk snapshot'ı yok (ya hiç emir girilmedi ya da bu pencerede de pipeline çalışmadı).

> Bu state cache; gerçek Alpaca paper pozisyonlarıyla **bire bir aynı olmayabilir**. Doğru hesap durumu için Alpaca paper dashboard kullanılmalı: <https://paper.alpaca.markets>.

---

## Slippage Tracker

| Dosya | Durum |
|---|---|
| `logs/slippage_tracker.json` | Hâlâ yok. Pipeline emir doldurma aşamasına ulaşmadığı için yazılması beklenmiyordu. |

Bu davranış doğrudur — emir fill olmadan slippage hesabı yapılmaz.

---

## Sonraki Adımlar (önerilen)

1. **Sandbox'a `yfinance` ekleme yolu açın.** İki seçenek:
   - Proxy allowlist'ine PyPI ekleyin (`pypi.org`, `files.pythonhosted.org`).
   - Veya gerekli paketleri (`yfinance`, `requests`, `pandas`, `numpy` vb.) önceden mounted bir wheelhouse dizininde tutun ve `pip install --no-index --find-links=…` ile kurulum yapın.
2. **`scanner.data_fetcher`'a offline-friendly fallback.** Veri kaynağı opsiyonu olarak Alpaca historical bars (zaten Alpaca anahtarları mevcut) eklenirse, yfinance erişimi yokken Alpaca'dan tarama yapılabilir; bu, sandbox tarafından bloklanan dış ağ erişimini de azaltır.
3. **Erken-return durumunda da summary üret.** `scripts/auto_scan_trade.py:716-718` 0 ham sinyalde `return` ediyor ve `_save_summary` çağrılmıyor. Bunu da summary üretecek şekilde değiştirmek, gözleme açısından (bugün manuel yazmak zorunda kalındığı gibi durumlar) faydalı olur.
4. **Risk snapshot tazeleme.** Eğer paper hesaba elle pozisyon girildiyse `risk_*.json` cache'i artık güncel değil; bir sonraki başarılı run veya manuel `RiskGuard.refresh_from_broker()` yardımcı olabilir.

---

## Raporlanan Çıktı Dosyaları

- `logs/auto_trade/summary_2026-05-12.json` — manuel olarak üretildi (script tarafından üretilmeyen "no signals" durumu için bilgi tutuluyor)
- `FINPILOT_MORNING_TRADE_REPORT_2026-05-12.md` — bu rapor
