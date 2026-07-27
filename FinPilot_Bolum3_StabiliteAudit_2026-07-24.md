# FinPilot — BÖLÜM 3 DERİN AUDIT: Stabilite Bulguları ve Risk Haritası
**Tarih:** 2026-07-24 · **Tür:** Canlı kanıt (log + DB + dosya + kod) · **Kaynak:** ön-tarama Bölüm 3

> **Özet:** Raporun 3 stabilite riskinden ikisi (**yedek sürekliliği**, **karne sessiz-ölümü**) fiilen giderildi; **DB bozulması hâlâ en yüksek risk** (tekrarlayan, kök neden elimine edilmedi). İki yeni doğrulanmış risk: **veri-sağlayıcı tekilliği** ve **log gürültüsü**.

---

## 1. Doğrulanan bulgular (bugün, kanıtla)

### DB bozulması — TEKRARLAYAN (en yüksek risk) 🔴
Kanıt (`data/`):
- `finpilot.db.corrupt_20260715` (7.9 MB) — **15 Temmuz bozulma olayı**
- `finpilot_recovered_20260703.db` (0 B) + `signals_archive_recovered_20260703.csv` (557 KB) — **3 Temmuz kurtarma**
- → **en az iki bozulma** iki farklı tarihte. Tek seferlik değil.

Mekanizma (güçlü hipotez): `finpilot.db` ve `distribution.db` **WAL modunda** (`journal_mode=wal`); `-wal`/`-shm` sidecar dosyaları mevcut. WAL sidecar'ları ana `.db`'den ayrı zamanlarda buluta senkronlanırsa (OneDrive) ya da AV tarafından kilitlenirse, bir sonraki açılışta bozulma olur. Bu, iki olayın ortak paydası için en olası açıklama.

**Durum:** Kök neden **elimine edilmedi.** Yedek artık tekrarlayan (azaltıcı), ama önleme yok.

### Yayın penceresi disiplini — GEÇMİŞ KÖTÜ, ARTIK ALARMLI 🟡→✅
`broadcast_queue`: **5 sent / 11 expired / 3 rejected.** Son: #18-19 sent (23-24 Tem), #14-17 expired (20-22 Tem). 11 kayıp = sessiz-başarısızlık sınıfı gerçekti. **Artık `expire_stale` expired'de yüksek sesle admin'e haber veriyor + seriyi bildiriyor** (bu oturumda eklendi). Mevcut seri: 2.

### api.log gürültüsü — GERÇEK, CANLI 🟡
`logs/api.log` = 11.595 satır, **874 ERROR**. Son hatalar (bugün 19:57) **yfinance HTTP 404** — geçersiz/delisted ticker'lar. Test gürültüsü değil, canlı veri-sağlayıcı hataları. Gerçek hataları maskeliyor; log rotasyonu yok, `logs/` eski dosyalarla dolu (Mart–Mayıs).

### Veri sağlayıcı tekilliği — DOĞRULANDI 🟠
`yfinance` her katmanda sabit (agents, api routers, scanner). **Provider soyutlaması/fallback YOK** (`class *Provider` / `get_provider` / `DATA_PROVIDER` grep'i boş). yfinance rate-limit/blok/şema değişikliği = tüm tarama durur. Tek nokta arıza.

---

## 2. Rapordaki risklerin güncel durumu

| Risk (rapor) | Rapor seviyesi | Bugünkü durum |
|---|---|---|
| Karne arşiv yazıcısı sessiz ölmüş | Yüksek | ✅ **Giderildi** — `archive_bridge` yazıyor + süreklilik alarmı |
| Yedekleme sürekliliği (tek gün) | Yüksek | ✅ **Giderildi** — her publish'te `daily_backup` + off-site opsiyonu |
| Bütünlük-kapılı okuyucu yok | Orta-yüksek | ✅ **Var** — NUL kontrolü + `validate_scan_export` + `prepublish_gate` |
| Yayın penceresi disiplini | Orta | ✅ **Alarm eklendi** (expired→admin) |
| DB bozulma kök nedeni | Yüksek | 🔴 **Açık** — tekrarlayan, WAL+senk/AV; önleme yok |
| Tek-PC / tek-insan | Yüksek | 🔴 **Yapısal** — değişmedi; PC yoksa yayın yok |
| Dış bağımlılık tekilliği | Orta | 🟠 **Açık** — yfinance fallback'siz; tek bot; Vercel+Render |
| Monitoring yokluğu | Orta | ⚪ **Park edildi** (bilinçli) — gerçek uyarılar Telegram'da |
| api.log gürültüsü | Orta | 🟡 **Açık** — 874 hata, çoğu yfinance 404 |

---

## 3. Öncelikli aksiyonlar (canlı bulgulara göre)

**P0 — DB bozulma önleme (kök neden):**
1. `C:\Users\meric\Borsa\data\` OneDrive senkronu dışına alınmalı (klasörü OneDrive dışına taşı ya da "her zaman bu cihazda tut / senkronu durdur"). **Borsa OneDrive altında mı önce teyit et** — değilse suçlu AV gerçek-zamanlı tarama.
2. AV istisnası: `data\*.db`, `*.db-wal`, `*.db-shm`.
3. WAL disiplini: yayın/yazım sonrası `PRAGMA wal_checkpoint(TRUNCATE)` ya da kritik DB'lerde `journal_mode=DELETE` değerlendir (academy.db zaten DELETE, hiç bozulmadı — ipucu).
4. Off-site yedeği aç: `FINPILOT_BACKUP_EXTERNAL_DIR` + `FINPILOT_BACKUP_EXTERNAL_EVERY_RUN=1` (bu oturumda eklendi).
5. Bozulma artefaktlarını temizle: `finpilot.db.corrupt_20260715`, boş `finpilot_recovered_*.db`, eski sidecar'lar (karışıklık + risk).

**P1 — Veri sağlayıcı dayanıklılığı:**
6. yfinance çağrılarını tek bir provider modülü arkasına al; 404/rate-limit'i zarifçe yut (ERROR→WARNING) + ileride ikinci kaynak (ör. Stooq/Alpha Vantage) fallback'i için kanca.

**P1 — Log hijyeni:**
7. Beklenen yfinance 404'lerini ERROR'dan DEBUG/WARNING'e indir; `logs/`'a rotasyon (boyut/gün) ekle; eski logları arşivle.

**P2 — Yapısal tekillik:**
8. Tek-PC: publish penceresini kaçırınca zaten alarm var; ileride ikinci bir tetikleyici (telefon/başka cihaz) düşün. Tek bot/hosting: fallback tanımı (lansman sonrası).

---
_Durum: AKTİF · Canlı kanıta dayalı. Rapordaki 9 riskin 4'ü giderildi, 1 park; 4'ü açık (1 kritik: DB bozulma önleme)._
