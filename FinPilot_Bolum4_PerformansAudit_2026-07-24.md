# FinPilot — BÖLÜM 4 DERİN AUDIT: Performans / Hız Darboğazı
**Tarih:** 2026-07-24 · **Tür:** Canlı kanıt (kod + log + export) · **Kaynak:** ön-tarama Bölüm 4

> **Özet:** Rapor "performans his ile yönetiliyor, tek veri dosya saatleri" demişti. Doğru — **uçtan uca boru hattı ölçülmüyor.** Ama iki önemli düzeltme: (1) tarama-içi eval/enrich **zaten ölçülüyor** (sadece yüzeye çıkmıyor); (2) **14:04→14:59 "55 dk boşluğu" bir darboğaz değil — manuel onay beklemesi** (kanıt: loglarda tekrar eden "web snapshot held: draft awaiting approval").

---

## 1. Ölçülen gerçekler (kod + log kanıtı)

### Enstrümantasyon — KISMİ VAR, YÜZEYE ÇIKMIYOR
- `api/routers/scan.py:358` **tarama-içi timing logluyor:** `scan timing: symbols=N eval=Xs enrich=Ys total=Zs` (perf_counter, satır 327/353/357).
- **Ama:** (a) mevcut `api.log`'da **0** böyle satır → günlük tarama ya bu süreçte loglanmıyor ya da yakalanmıyor; (b) süre **export'a yazılmıyor** — export yalnızca `generated_at`/`run_id`/`scan_id` taşıyor, **`scan_duration` yok** → geçmiş per-run süre sorgulanamıyor; (c) **snapshot build, publish, web push için hiç timing yok.**
- **Sonuç:** uçtan uca boru hattı süresi ölçülmüyor; "his ile yönetim" iddiası uçtan uca hâlâ geçerli.

### 14:04→14:59 "boşluk" — MANUEL BEKLEME, compute değil 🟢
`distribution.jobs` logu **tekrar tekrar**: `web snapshot held: 1 draft(s) still await approval` (16:50, 16:55, 18:32, 19:54). Publish **manuel onaya kapılı** (`publish_now` → onay → `job_publish`). Yani tarama bitişi (14:04) ile snapshot (14:59) arası **insan beklemesi** — gizli bir hesaplama darboğazı değil. Raporun en büyük açık sorusu **kapandı.**

### Tarama compute — paralelize, ~11 dk / 1801 sembol 🟢
- `api/routers/scan.py:41` **`ThreadPoolExecutor(max_workers=16)`**; `data_fetcher` alt-çekimde 4–8 thread.
- Veri yolu **Alpaca (toplu, hızlı) → yfinance (per-symbol fallback, yavaş)**. ~11 dk/1801 ≈ 0.37 sn/sembol efektif — kabul edilebilir; yavaşlık varsa yfinance fallback'e düşen sembol sayısından gelir (ölçülmüyor).

### Snapshot → web + Telegram — hızlı 🟢
Rapor ~1–2 dk (14:59→15:01). Enstrümantasyon yok ama darboğaz değil.

### Web yükü — ölçülmedi, düşük risk 🟢
Ledger statik JSON okuyor (`demo_snapshot.json` ~5 KB). Sandbox'ta Lighthouse yok; yapı gereği hafif. Lansman öncesi tek Lighthouse taraması yeterli.

---

## 2. Darboğaz haritası (güncel)

| Adım | Gerçek süre | Ölçüm durumu | Verdict |
|---|---|---|---|
| Tam evren taraması (1801) | ~11 dk (mtime) | eval/enrich loglanıyor ama yüzeyde yok | 🟢 kabul edilebilir; per-run süre kaydı eksik |
| Tarama → snapshot | ~55 dk | **manuel onay beklemesi** (kanıtlı) | 🟢 darboğaz DEĞİL — insan gecikmesi |
| Snapshot → web/TG | ~1–2 dk | ölçülmüyor | 🟢 hızlı |
| yfinance fallback payı | ? | **ölçülmüyor** | 🟡 kör nokta — kaç sembol fallback'e düşüyor bilinmiyor |
| Web yükleme | ? | ölçülmedi | 🟢 statik, hafif; Lighthouse baseline yeterli |

**Asıl bulgu:** Compute darboğazı YOK. Gerçek eksik = **ölçüm/görünürlük** (uçtan uca timing) ve **manuel gecikmenin açıkça ayrılması**.

---

## 3. Çalışma planı (kanıta dayalı, öncelikli)

**P0 — Uçtan uca boru hattı timing'i (ucuz, en yüksek değer):**
1. Export'a `scan_duration_s` + zaten hesaplanan `eval_s`/`enrich_s` alanlarını **yaz** (scan.py timing'i export'a taşı — hâlihazırda perf_counter var).
2. `job_draft`/`build_snapshot`/`job_publish`/`_push_snapshot_to_web` her birine başlangıç/bitiş süre logu ekle; snapshot'a `timing:{scan,snapshot,publish,web}` bloğu koy.
3. **Manuel gecikmeyi ayır:** `scan_finished_at` vs `publish_triggered_at` kaydet → "gap" resmen insan beklemesi olarak görünür, gizem biter.

**P1 — Kör noktayı ölç:**
4. yfinance fallback sayacı: bir taramada kaç sembol Alpaca'dan gelmeyip yfinance'e düştü → logla. Yüksekse Alpaca kapsamını genişlet (compute + 404 gürültüsü birlikte düşer).

**P2 — Baseline'lar:**
5. Web'de tek seferlik Lighthouse (lansman öncesi mobil/masaüstü skor).
6. "Sabah ≤15 dk" hedefi: manuel onay dahil mi hariç mi netleştir; timing bloğu bunu ölçülebilir yapar.

**Yapılmayacak (bilinçli):** compute optimizasyonu — ölçüm göstermeden erken. Tarama zaten paralelize ve ~11 dk kabul edilebilir; darboğaz kanıtı yok.

---
_Durum: AKTİF · Compute darboğazı yok; iş, ölçüm görünürlüğü (P0 timing) + fallback ölçümü (P1). "55 dk boşluk" manuel onay olarak çözüldü._
