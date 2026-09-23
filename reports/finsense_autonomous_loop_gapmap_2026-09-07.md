# FinSense Otonom Döngü — Tam Harita ve Kopukluk Analizi

Tarih: 2026-09-07
Level: A (araştırma; hiçbir kod/config değiştirilmedi)
Tetikleyici: Kullanıcı — "sadece ders üretimi değil; üret → denetle → düzelt → yayınla → web'e koy → sürekli çalış. Altyapıyı kurdum ama çalıştırmıyorum her zaman. Ayrıca hedef doğrultusunda kod yazacak, otomatik denetleyecek, düzenleyecek."
Önceki: `reports/finsense_content_readiness_2026-09-07.md`

---

## 1. İstenen tam otonom döngü

```
[1. ÜRET]      content_generator → ders üret (LLM + pedagoji şablonu)
[2. DENETLE]   quality_guard → 7 boyutlu kalite denetimi → APPROVED/REVISION/REJECTED
[3. DÜZELT]    content_updater → REVISION gelen dersi geri bildirimle güncelle
[4. YAYINLA]   status="published" → SQLite'e yaz
[5. WEB'E KOY] export_lessons → academy_lessons.json → publish_web.py → git push → Vercel
[6. SÜREKLİ]   scheduler → günlük 02:00, haftalık Pazartesi 07:00, çeyreklik
```

## 2. Halka-halka mevcudiyet

| Halka | Dosya | Durum | Not |
|---|---|---|---|
| 1. ÜRET | `academy/agents/content_generator.py` | ✅ VAR | LLM + pedagoji şablonu + JSON parse + quiz/flashcard |
| 2. DENETLE | `academy/agents/quality_guard.py` | ✅ VAR | 7 boyutlu denetim, APPROVED/REVISION/REJECTED |
| 3. DÜZELT | `academy/agents/content_updater.py` | ✅ VAR | Geri bildirimle ders güncelleme |
| 4. YAYINLA | `academy/models.py` (LessonRepository) | ✅ VAR | SQLite persist, status="published" |
| 5. WEB'E KOY | **`Finsense/academy/export_lessons.py`** | ⚠️ **AYRI REPO** | `python -m academy.export_lessons --json --status published --out ../Borsa/web/public/academy_lessons.json` — **Borsa reposunda değil, Finsense reposunda.** Ardından `scripts/publish_web.py` (Borsa) git push yapar. |
| 6. SÜREKLİ | `academy/scheduler.py` | ✅ VAR | APScheduler, günlük 02:00 ET, haftalık Paz 07:00, çeyreklik |

## 3. Gerçek kopukluk noktaları (neden çalışmıyor)

### Level A doğrulama sonuçları (2026-09-07, doğrulandı)

| Kontrol | Sonuç |
|---|---|
| LLM provider | ✅ OllamaProvider, model=qwen2.5:7b, localhost:11434 — ama Ollama'nın çalışıp çalışmadığı test edilmedi |
| APScheduler | ✅ apscheduler 3.10.4 + pytz kurulu, modül importable |
| Borsa academy.db | ❌ **0 ders — bomboş** (`data/academy.db`) |
| Finsense academy.db | ✅ **96 ders: 8 published, 88 draft** (`C:\Users\meric\Finsense\data\academy.db`) |

**Kritik keşif:** İki ayrı academy sistemi var. Finsense kendi DB'sinde 96 ders üretmiş (%92'si draft'ta takılı), Borsa'nınki boş. Web'in okuduğu `academy_lessons.json` Finsense'nin export'undan geliyor. Yani **içerik üretimi aslında çalışmış** — ama (a) draft'lar publish'e geçmiyor, (b) Borsa tarafı kendi DB'sini kullanmıyor, (c) export manuel.

### Kopukluk A — Scheduler başlatılıyor ama doğrulanmıyor
- `api/main.py:225-231` akademi scheduler'ını `ACADEMY_AUTOSTART_SCHEDULER=1` (varsayılan açık) ile başlatıyor.
- Ama **`start_academy_scheduler()`'ın başarısını yalnızca log'a yazıyor** — `_svc_registry.register("academy_scheduler", healthy=academy_started)` var ama bu kaydın gerçekten "healthy" olup olmadığını hiç doğrulamadık.
- APScheduler `BackgroundScheduler` kullanıyor — ana process (uvicorn) ayakta kaldığı sürece çalışır. Ama API restart edilirse scheduler da ölür ve yeniden başlar; bu doğru davranış ama **izlenmiyor**.
- **Kanıt boşluğu:** Akademi scheduler'ının hiç çalıştığına dair log kaydı görmedik. `logger.info("[AcademyScheduler] Started...")` mesajını hiçbir yerde gözlemlemedik.

### Kopukluk B — Export köprüsü ayrı repo'da + çift DB sorunu
- `academy_lessons.json`'u üreten komut **Finsense reposunda** (`C:\Users\meric\Finsense\academy\export_lessons.py`), Borsa reposunda değil.
- Web sayfası ([web/src/app/academy/page.tsx:6-8](web/src/app/academy/page.tsx#L6)) bu dosyayı bekliyor ama üretimi başka bir repo'nun sorumluluğunda.
- **Çift DB:** Finsense'nin `data/academy.db`'sinde 96 ders var; Borsa'nın `data/academy.db`'si boş. İki sistem aynı şema, ayrı veri. Hangi DB "gerçek" belli değil.
- **Draft birikimi:** 96 dersin 88'i draft — quality_guard ya hiç çalışmadı ya da REVISION/REJECTED verip kimse düzeltmedi.
- **Bu, iki repo arasındaki manuel bir köprü** — otomatik değil. Akademi ajanı ders üretse bile, export komutunu kimse çalıştırmazsa web'e ulaşmaz.

### Kopukluk C — Quality Guard darboğazı (draft mezarlığı)
- 88 ders draft'ta bekliyor. Quality Guard ya hiç çalıştırılmadı ya da REVISION verdi ve content_updater düzeltmedi.
- `run_daily` → `quality_guard.review_pending_lessons()` çağırıyor — ama scheduler hiç kanıtlanmadı (Kopukluk A).
- **Kanıt boşluğu:** Hiçbir quality_guard denetim logu görmedik.
- LLM provider var (Ollama qwen2.5:7b) ama Ollama'nın çalışıp çalışmadığı doğrulanmadı — provider yoksa mock mode'a düşer.

### Kopukluk D — "Kod yazma ve otomatik denetleme" isteği ayrı bir eksen
Kullanıcının "verdiğimiz hedef doğrultusunda kodları yazacak, otomatik denetleyecek, düzenlemeleri yapacak" isteği akademi içeriğinden ayrı bir şey: **FinPilot'un kendi kodunu geliştiren bir ajan.** Bu:
- Hedef → plan → kod yaz → test çalıştır → hata varsa düzelt → tekrar dene
- Bu bir **self-improving development loop** — akademi döngüsünden farklı
- Mevcut 23 ajan (`agents/`) bunu kısmen yapıyor (coder, tester, reviewer) ama **hedef-odaklı otonom geliştirme** için ayrı bir orkestrasyon gerekir

## 4. Ne eksik — tek liste

| # | Eksik | Etki | Düzeltme | Level |
|---|---|---|---|---|
| 1 | Akademi scheduler sağlık kanıtı yok | Çalışıp çalışmadığını bilmiyoruz | Health endpoint'ine academy_scheduler durumunu ekle + ilk çalıştırmada log doğrula | A |
| 2 | Export köprüsü manuel | Ders üretilse bile web'e ulaşmıyor | `academy/scheduler.py`'ye export adımı ekle (ders yayınlandıktan sonra `export_lessons --json` çağır) — ama bu Finsense reposuna bağımlılık yaratır; alternatif: export mantığını Borsa'ya taşı | B |
| 3 | LLM provider doğrulanmamış | Ders üretimi mock'da kalabilir | `ACADEMY_LLM_BACKEND` env + provider sağlık kontrolü + mock'da ne ürettiğini belgele | A |
| 4 | publish_web entegrasyonu yok | Export sonrası git push manuel | `run_daily`'ye `_push_academy_to_web()` adımı ekle (mevcut `_push_snapshot_to_web()` desenini izle) | B |
| 5 | Self-improving code loop ayrı eksen | "Kod yaz + denetle + düzelt" akademi değil | Ayrı tasarım: hedef → plan → kod → test → düzelt döngüsü. Mevcut agents/ altyapısını kullanır ama ayrı orchestrator gerekir | B (ayrı proje) |

## 5. Önerilen minimum canlıya-alma sırası (güncel — doğrulanmış bulgularla)

```
Adım 1 (Level A): Ollama'nın çalıştığını doğrula
  → curl http://localhost:11434/api/tags — qwen2.5:7b yüklü mü?
  → Çalışmıyorsa: ollama serve + ollama pull qwen2.5:7b

Adım 2 (Level A): Çift DB sorununu çöz
  → Hangi DB gerçek? Finsense'ninki (96 ders) mi, Borsa'nınki (0 ders) mi?
  → Karar: tek DB'ye birleştir veya Finsense'yi tek otorite kabul et

Adım 3 (Level A): Quality Guard darboğazını aç
  → 88 draft dersi toplu denetle: quality_guard.review_pending_lessons()
  → APPROVED olanları publish et, REVISION olanları content_updater'a gönder

Adım 4 (Level B): Export + publish köprüsünü otomatikleştir
  → Ders APPROVED olduğunda otomatik export_lessons + publish_web
  → publish_web.py zaten academy_lessons.json'u biliyor (FILES listesinde)

Adım 5 (Level B): İlk toplu üretim
  → 69 modül - 8 mevcut published = 61 kalan
  → 5 job/gün = 13 gün, veya tek seferde batch

Adım 6 (Level B, ayrı proje): Self-improving code loop
  → Hedef → plan → kod → test → düzelt döngüsü için ayrı orchestrator tasarımı
```

## Governance

- Hiçbir production/içerik/kod değiştirilmedi.
- Kopukluk A ve C Level A (doğrulama), Kopukluk B ve D Level B (yeni bağlantı/tasarım).
- "Self-improving code loop" (Kopukluk D) akademi döngüsünden ayrı bir eksen — karıştırılmamalı.
