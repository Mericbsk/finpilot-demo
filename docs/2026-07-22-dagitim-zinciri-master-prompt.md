# MASTER PROMPT — FinPilot Dağıtım Zinciri Uçtan-Uca Onarımı (Telegram + Web)

> Bu prompt'u sıfırdan başlayan bir agent'a ver. Amaç: "tarama tamamlandı →
> Telegram yayını → web güncellemesi" zincirini tekrar güvenilir hale getirmek.
> Tahmin etme; her adımı **kanıtla**. Tek doğruluk kaynağı ortak bir `snapshot_id`'dir:
> bir tarama; export, snapshot, kuyruk, Telegram mesajı ve web'de **aynı** snapshot_id
> ile görünmüyorsa zincir "başarılı" sayılmaz.

---

## 0. Rol ve Çalışma Kuralları

Sen bir üretim-güvenilirliği mühendisisin. Kurallar:

1. **Varsayma, doğrula.** Her iddiayı bir komut çıktısı, dosya içeriği veya HTTP
   cevabıyla kanıtla. "Deploy edildi", "çalışıyor" gibi ifadeleri kanıtsız kullanma.
2. **Dört zinciri ayrı denetle:** (A) tarama kaydı, (B) backend runtime,
   (C) Telegram yayını, (D) Vercel/web yayını. Her biri için: kanıt → kök neden →
   kullanıcı müdahalesi (dashboard/secret) → agent'ın düzeltebileceği kod.
3. **İki ortam var, karıştırma:** Local (VS Code/Docker) ve Render (prod). Bir dosyayı
   hangi ortamın yazdığını/okuduğunu her zaman belirt.
4. **Sandbox mount büyük/yeni dosyaları bozuk okuyabilir** (geçerli JSON + sonda
   null-byte dolgusu). Bir dosyanın baş baytları (date/universe) güvenilir; parse
   hatası görürsen bunun mount artefaktı mı yoksa gerçek disk bozulması mı olduğunu
   `wc -c` + null sayımı + `tail -c` ile ayırt et, kullanıcının pytest'i geçiyorsa
   diski otorite kabul et.
5. **Secret'ları asla yazdırma/log'lama.** Sadece anahtar adının var/yok olduğunu kontrol et.
6. **Trade/para hareketi yapma.** Sadece yayın/veri zincirini onar.

---

## 1. Sistem Mimarisi (hedef akış)

```
VS Code / tarayıcı dashboard
    │  (tüm /py-api/* çağrıları same-origin proxy'den → API_HOST)
    ▼
/scan  (batch batch, her batch _persist_shadow + partial)
    ▼
/scan/summarize   ← TAM evren handoff (scan_complete + universe≥1812)
    │  ├─ _persist_distribution_export(full)   → scan_export_latest.json (snapshot_id üretir)
    │  └─ _trigger_distribution_draft()
    ▼
job_draft()  → build_snapshot → snapshot_latest.json + snapshot_en_latest.json
    │           → broadcast.queue_draft (snapshot_id/date/universe/candidate_hash TAŞIR)
    │           → notify_admin("ONAYLA <id>")
    ▼
Admin: "ONAYLA <id>"  (Telegram)
    ▼
job_publish()
    ├─ send_to_channel(text)  → Telegram message_id + tg_delivery_log
    └─ snapshot yayınla       → /api/v1/distribution/snapshot (web BURADAN okur)
    ▼
Web (Vercel): statik demo_snapshot.json DEĞİL, Render snapshot endpoint'ini okur
    → date/universe/candidate_hash doğrulanır
```

**İlgili dosyalar (referans):**
- `web/src/app/py-api/[...path]/route.ts` — runtime proxy; `API_HOST` set değilse Render'a düşer.
- `web/src/lib/api.ts` — `NEXT_PUBLIC_API_URL` SET ise `/api/v1/*` proxy'yi atlar, doğrudan (cross-origin) gider.
- `web/.env.local` — local dev backend hedefi.
- `api/main.py` (CORS ~335-350, router kayıtları ~356-380) — `distribution` router BURAYA eklenecek.
- `api/routers/scan.py` — `/scan` (~366), `/scan/summarize` (~385, guard 403-406, persist+draft 418-420), `_persist_distribution_export` partial-guard (~718-759).
- `distribution/jobs.py` — `job_draft` (116), `job_publish` (194), `_push_snapshot_to_web` (228), `maybe_trigger_draft_after_scan` (391).
- `distribution/store.py` — `broadcast_queue` şeması + `queue_draft/decide/get_approved_unsent/mark_sent`.
- `web/src/lib/ledgerSnapshot.ts` — landing zaten `${API_HOST}/api/v1/distribution/snapshot` çekiyor (endpoint YOK).
- `web/src/app/demo/page.tsx:338` — demo statik `/demo_snapshot.json` çekiyor.

---

## 2. Şu Ana Kadar Doğrulanmış Kök Nedenler (başlangıç kanıtı)

1. **Routing local'i sessizce prod'a yönlendirdi.** `next.config.ts` rewrite'ı kaldırılıp
   `route.ts` runtime proxy'sine geçildi; proxy `API_HOST` set değilse Render'a düşer.
   `web/.env.local`'de ayrıca `NEXT_PUBLIC_API_URL=...:8001` vardı → `/scan/summarize`
   handoff'u proxy'yi atlayıp **cross-origin** gidiyordu → CORS whitelist localhost'u
   içermezse handoff sessizce ölüyordu. (Düzeltildi: `NEXT_PUBLIC_API_URL` kaldırıldı,
   `API_HOST=http://localhost:8001` — Docker host portu. Bare uvicorn ise 8000 yapılmalı.)
2. **Tam tarama "latest" olarak yazılmıyor.** `scan_export_latest.json` = **universe 12**
   (bugün). Kodda partial-guard var (12<1812 → `_partial_` dosyasına gider) → yani ya
   çalışan backend guard'sız ESKİ kod, ya da summarize handoff hiç tamamlanmıyor.
3. **Render eski image çalıştırıyor.** Canlı `/api/v1/agent/scheduler` `distribution`
   alanını DÖNMÜYOR (eski `running/cycle_count/last_status` formatı). `/ready` timestamp'i
   de bayat. `redis: degraded` (in-memory fallback).
4. **Web Render'a bağlı değil.** `_push_snapshot_to_web` yalnızca Render container'ının
   `web/public/demo_snapshot.json`'ına yazar → Vercel deployment'ını değiştirmez. Ayrıca
   web'in okumak istediği `/api/v1/distribution/snapshot` endpoint'i **hiç yok** (router
   `main.py`'de kayıtlı değil) → landing statik/bayat dosyaya düşüyor. Canlı web = 2026-07-17.
5. **Kuyruk snapshot'a bağlı değil.** `queue_draft` kaydı `snapshot_id/hash` taşımıyor →
   "ONAYLA <id>" hangi snapshot'ı yayınladığını garanti etmiyor.
6. **`.env` durumu:** `FINPILOT_ENABLE_DISTRIBUTION=1` ✓, TELEGRAM anahtarları ✓,
   `FINPILOT_FULL_UNIVERSE_SIZE` YOK (default 1812), `CORS_ORIGINS` YOK (local'de localhost izinli).

---

## 3. GÖREVLER (zincir zincir; her görevin kabul kriteri var)

### A. Tarama kaydı zinciri — tam evren "latest" olarak persist olsun

A1. Çalışan backend'in portunu ve güncelliğini kanıtla:
```
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/ready
curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/ready
curl -s http://localhost:<PORT>/api/v1/agent/scheduler   # "distribution" alanı OLMALI
```
- `distribution` alanı yoksa → **eski kod çalışıyor**; güncel commit'i ayağa kaldır (Docker rebuild / uvicorn reload). Bu düzelmeden ilerleme.

A2. `web/.env.local`'i çalışan porta göre kesinleştir (`API_HOST`), `NEXT_PUBLIC_API_URL`
   set OLMADIĞINI doğrula. `next dev`'i tamamen kapat-aç (env cache).

A3. `.env`'e ekle: `FINPILOT_FULL_UNIVERSE_SIZE=1812` (guard'ın beklenen boyutu açık olsun),
   gerekiyorsa `FINPILOT_AUTOSTART_SCHEDULER=1`.

A4. Frontend tam-evren handoff'u: `scanner/page.tsx` taramayı, `/scan/summarize` **200**
   dönmeden "başarılı" göstermemeli. Handoff `422 "Aggregate scan incomplete"` dönerse
   frontend'in gönderdiği `universe`/`results` sayısını logla ve tam seti gönder.

**Kabul kriteri A:** Tam tarama sonrası
```
data/distribution/scan_export_latest.json → date=bugün, universe≈1812, results≥1631
```
ve DevTools'ta `/scan/summarize` = 200. Kısmi (`_partial_*.json`) dosyalar latest'i EZMEMELİ.

---

### B. Backend runtime — Render güncel kodu çalıştırsın (kullanıcı müdahalesi + kod)

B1. **Kullanıcı (Render dashboard):** `finpilot-api` için güncel commit'i **Manual Deploy**.
   Build log'da commit hash'i doğrula. Runtime log'da: scheduler started, distribution
   enabled, telegram bot started.

B2. **Kullanıcı (Render env):** doğrula/ekle —
```
FINPILOT_ENABLE_DISTRIBUTION=1
FINPILOT_AUTOSTART_SCHEDULER=1
FINPILOT_FULL_UNIVERSE_SIZE=1812
TELEGRAM_BOT_TOKEN=<geçerli>
TELEGRAM_CHANNEL_ID=@Finpilot_Breif
TELEGRAM_ADMIN_ID=<id>
CORS_ORIGINS=<vercel domain>,https://www.<domain>   # web origin'i MUTLAKA içersin
# Quote sağlayıcı NET olsun: Alpaca kullanılacaksa ALPACA_API_KEY/SECRET ekle,
# EODHD kullanılacaksa quote kodu EODHD'yi gerçekten çağırmalı (yalnız key yetmez).
```

B3. **Kullanıcı (güvenlik):** Bu oturumlarda gerçek görünümlü token/secret'lar geçti.
   Telegram bot token'ını ve varsa Alpaca key'lerini **rotate et**, Render secret'larını
   yeniden kaydet, `.env`/log'larda secret sızmadığını kontrol et.

B4. Redis: prod'da ya gerçek Redis bağla ya da Redis bağımlılığını açıkça persistent
   store'a taşı; `/ready` "degraded" kalmamalı ya da etkisi net raporlanmalı.

**Kabul kriteri B:** Canlı `https://<render>/api/v1/agent/scheduler` →
`"distribution": {"enabled": true, ...}`; `/ready` bugünün timestamp'i.

---

### C. Telegram yayını — onay snapshot'a bağlansın

C1. `distribution/store.py`: `broadcast_queue`'ya sütun ekle —
   `snapshot_id, snapshot_date, snapshot_universe, candidate_hash`.
   `queue_draft` bunları yazsın; `job_draft` snapshot üretirken `snapshot_id` (örn.
   `sha256(date + universe + sorted(candidate_tickers))[:12]`) hesaplayıp hem snapshot
   dosyasına hem kuyruk kaydına koysun.

C2. `job_publish` gönderim öncesi guard:
```
snapshot_date == bugün
snapshot_universe >= FINPILOT_FULL_UNIVERSE_SIZE
queue.snapshot_id == mevcut snapshot_latest.snapshot_id
```
Biri tutmazsa gönderme; kaydı `blocked/stale` yap, admin'e sebep DM'i at.

C3. Gönderim sonrası: Telegram `message_id` ve `tg_delivery_log` kaydı olmadan
   `mark_sent(success)` ÇAĞIRMA. `message_id` boşsa `failed`.

**Kabul kriteri C:** "ONAYLA <id>" sonrası kanalda mesaj görünür; kuyruk kaydı `sent`,
`message_id` dolu, ve o kaydın `snapshot_id`'si o günkü `snapshot_latest` ile aynı.

---

### D. Vercel/web yayını — web canlı Render snapshot'ını okusun

D1. **API'ye okuma endpoint'i ekle** — yeni dosya `api/routers/distribution.py`:
```python
from __future__ import annotations
import json
from fastapi import APIRouter, Response
from distribution.schema import demo_view
from distribution.snapshot_builder import EXPORT_DIR

router = APIRouter(prefix="/distribution", tags=["distribution"])

@router.get("/snapshot")
def public_snapshot():
    src = EXPORT_DIR / "snapshot_en_latest.json"
    if not src.exists():
        src = EXPORT_DIR / "snapshot_latest.json"
    if not src.exists():
        return Response('{"error":"no snapshot"}', status_code=404,
                        media_type="application/json")
    snap = json.loads(src.read_text(encoding="utf-8"))
    public = demo_view(snap, max_candidates=len(snap.get("candidates", [])))
    return Response(json.dumps(public, ensure_ascii=False),
                    media_type="application/json",
                    headers={"Cache-Control": "public, max-age=60",
                             "Access-Control-Allow-Origin": "*"})
```
`api/main.py`: `from api.routers import distribution` + `app.include_router(distribution.router, prefix="/api/v1")`.
Bu, `_push_snapshot_to_web` ile **aynı kaynak + aynı demo_view**'i kullanır → web ve
Telegram tek gerçekten beslenir.

D2. Web'i endpoint'e bağla:
- `web/src/lib/ledgerSnapshot.ts` zaten `${API_HOST||BACKEND_URL}/api/v1/distribution/snapshot`
  çekiyor — endpoint canlı olunca çalışır; statik dosyayı fallback bırak.
- `web/src/app/demo/page.tsx:338`: `fetch(process.env.NEXT_PUBLIC_SNAPSHOT_URL ?? "/demo_snapshot.json", {cache:"no-store"})`.
- **Vercel env:** `NEXT_PUBLIC_SNAPSHOT_URL=https://<render>/api/v1/distribution/snapshot`,
  `BACKEND_URL=https://<render>` (server-side landing için).

D3. `_push_snapshot_to_web` "başarılı" (`web_pushed=true`) yalnızca uzak yayın (endpoint
   güncel snapshot_id'yi döndürüyor ya da Vercel Deploy Hook 200) doğrulanırsa dönsün.

**Kabul kriteri D:** `curl https://<render>/api/v1/distribution/snapshot` → bugünün
`date` + `snapshot_id`; canlı web aynı tarihi/adayları gösteriyor (Vercel rebuild beklemeden).

---

## 4. Uçtan-Uca Doğrulama (tek snapshot_id ile)

Bir tam tarama çalıştır, sonra şu beşinin **aynı snapshot_id/date/universe** taşıdığını kanıtla:

```
1. scan_export_latest.json   → date=bugün, universe≈1812, snapshot_id=X
2. snapshot_latest.json       → snapshot_id=X
3. broadcast_queue (sent)     → snapshot_id=X, message_id dolu
4. Telegram kanal mesajı      → o günün adayları
5. /api/v1/distribution/snapshot ve canlı web → date=bugün, snapshot_id=X
```

Beşi eşleşmiyorsa zincir GÜVENİLİR DEĞİL — hangi halkada koptuğunu (yukarıdaki A/B/C/D
kabul kriterlerinden) tespit et ve orada dur, raporla.

---

## 5. Kalıcı Guardrail'ler (regresyon önleme)

- `/scan/summarize` başarısızsa frontend taramayı "başarılı" göstermez.
- `_persist_distribution_export` beklenen evren altında latest'i EZMEZ (partial'a yazar).
- `job_draft` yalnızca dosya tarihine değil; `universe≥beklenen` ve `snapshot_id` üretimine bakar.
- `job_publish` snapshot_id eşleşmesi + `message_id` olmadan `sent` demez.
- Web statik dosyaya bağımlı değil; canlı endpoint'i okur (fallback statik).
- `/api/v1/agent/scheduler` teşhis alanları döndürür: `running_commit`, `distribution`,
  `current_snapshot_id`, `last_scan_universe`, `last_publish_status`, `last_tg_message_id`.
- CI/smoke: deploy sonrası `/api/v1/distribution/snapshot` 200 + `distribution.enabled=true` kontrolü.

---

## 6. İlk Aksiyon Sırası (bugünkü veri için)

```
1. [A1] Backend portu + güncelliği (scheduler.distribution alanı) — kanıtla.
2. [B1/B2] Gerekliyse Render'a güncel commit deploy + env doğrula.
3. [A2/A3] .env.local (API_HOST, NEXT_PUBLIC_API_URL yok) + .env FULL_UNIVERSE_SIZE=1812; next dev restart.
4. [A4] TAM taramayı çalıştır; /scan/summarize=200 bekle.
5. [Kabul A] scan_export_latest → universe≈1812 doğrula.
6. [D1] distribution/snapshot endpoint'ini ekle + main.py'ye kaydet + deploy.
7. [C1-C3] Kuyruğu snapshot_id'ye bağla; "ONAYLA <id>" ile yayınla; message_id doğrula.
8. [D2] Web'i endpoint'e bağla (Vercel env); canlı web tarihini doğrula.
9. [Bölüm 4] Beş halkanın snapshot_id eşleşmesini kanıtla.
```

**Kural:** yalnız "scanner'ı tekrar çalıştır / Render restart / ONAYLA gönder / Vercel
redeploy" TEK BAŞINA çözüm değildir. Dört zincir birden yeşil olmadan ve tek snapshot_id
beş halkada eşleşmeden zincir tamamlanmış sayılmaz.
