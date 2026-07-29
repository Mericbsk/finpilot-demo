# FinPilot — "TEK-DOKUNUŞLA YAYIN" Detaylı Plan (Telegram + Web)
Durum: AKTİF · 2026-07-28 · Kaynak: Telegram/Web ön-taraması + kullanıcı kararları

## Kararlar (kilit)
- **Web deploy:** git commit+push (Vercel monorepo `finpilot-demo` push'ta otomatik deploy; snapshot zaten git'te izleniyor). Ek servis yok.
- **Scan tetik:** her sabah ELLE scan → taslak otomatik hazır → insan onayı.
- **Kanal:** `@Finpilot_Breif` şimdilik kalır (SSoT'a not; lansmana kadar dokunma).

## Hedef akış
`elle scan → publish_now (taslak+lint) → SEN onayla (Enter) → Telegram + web (git push→Vercel) + arşiv + yedek — otomatik.`
Sadece **onay** insanda; gerisi tek komutta otomatik.

---

## 1. Kurulum (bir kez) — env değişkenleri (.env / Render)
```
FINPILOT_ENABLE_DISTRIBUTION=0          # cron kapalı; yayın publish_now ile (güvenli)
FINPILOT_WEB_PUBLISH_CMD=python scripts/publish_web.py   # snapshot'ı git ile push et
FINPILOT_REQUIRE_VERCEL_DEPLOY=0        # push zaten Vercel'i tetikler; ayrı hook gerekmez
TELEGRAM_BOT_TOKEN=...                  # dolu olmalı
TELEGRAM_CHAT_ID=...                    # admin/kanal
TELEGRAM_CHANNEL_ID=@Finpilot_Breif     # yayın kanalı
WAITLIST_WEBHOOK_URL=...                # kalıcı waitlist aynası (Google Sheet vb.)
FINPILOT_ADMIN_KEY=...                  # /waitlist/list için
EODHD_API_KEY=...                       # social sentiment sinyali (yoksa nötr)
FINPILOT_ACADEMY_WEB_JSON=C:\Users\meric\Borsa\web\public\academy_lessons.json  # FinSense export hedefi
```
**Git kimlik:** `publish_web.py` push için git kimliği (PAT/SSH) kurulu olmalı. Bir kez `git push` elle test et.

## 2. Bir kez yapılacaklar
- `python scripts\harden_db.py` (WAL→DELETE, bozulma çaresi)
- Bot'u yaşat: `python scripts\run_bot.py` + `start_bot.bat`'i shell:startup'a koy (/start, /feedback için)
- SMTP şifresini rotate et (güvenlik kırmızısı)
- `publish_web.py`'yi elle bir kez dene: `python scripts\publish_web.py` (git push çalışıyor mu)

## 3. Günlük ritüel (her işlem günü, ~2 dk)
1. **PC aç** (≤ sabah penceresi).
2. **Tam-evren tarama çalıştır** (mevcut scan komutun) → `scan_export_latest.json` tazelenir.
3. **`python scripts\publish_now.py`** →
   - prepublish gate (bütünlük + lint + "0 eligible" koruması)
   - taslağı gösterir → **Enter = ONAYLA** (Ctrl+C = iptal)
   - job_publish: Telegram kanalına gönderir + `_push_snapshot_to_web` → `publish_web.py` git push → **Vercel deploy** + arşiv köprüsü + günlük yedek.
4. **Doğrula:** kanalda brif göründü mü · birkaç dk sonra finpilot.at/demo güncel mi (`demo_snapshot.json` bugünün tarihi).
5. **İzle:** "expired" alarmı gelmedi mi · `publish_streak()` arttı mı.

## 4. Otomatikleşen kısımlar (insan kapısını koruyarak)
| Parça | Nasıl |
|---|---|
| Taslak üretimi + lint | publish_now içinde otomatik |
| Telegram teslim | onaydan sonra otomatik |
| Web güncelleme + deploy | `publish_web.py` git push → Vercel otomatik |
| Akademi→web | FinSense worker `FINPILOT_ACADEMY_WEB_JSON` ile yazar; publish_web push'lar |
| Arşiv + yedek | publish_now sonunda otomatik |
| /start, /feedback toplama | run_bot.py (süpervizörlü) |

## 5. Kabul kriteri (bu hat "canlı" sayılır)
✅ Bir günlük tam tur: scan → publish_now → onay → Telegram brifi + finpilot.at güncel + arşiv yazıldı + yedek alındı, hata yok. `publish_streak` artıyor.

## 6. Sonraya (opsiyonel yükseltme) — "telefondan onay"
Şu an onay PC'de (publish_now Enter). Tamamen uzaktan (telefondan ONAYLA) için: `FINPILOT_ENABLE_DISTRIBUTION=1` + bot'un admin ONAYLA→job_publish handler'ını bağlamak gerekir. Bu, cron auto-publish etkilerini de açar → dikkatli test ister. **Lansman sonrası** değerlendir; şimdilik PC-onay yeterli ve güvenli.

## 7. Tuzak hatırlatmaları
- Web güncellenmiyorsa: `publish_web.py` push etti mi (`logs`/çıktı), Vercel deploy tetiklendi mi, doğru branch mı?
- Onay unutulursa "expired" → seri kırılır; alarm gelir, aynı gün müdahale.
- Git working tree: publish_web SADECE 2 json'u stage'ler; başka değişikliklerin commit'e karışmaz.
- Render ephemeral: waitlist webhook aynası aktif olmalı (redeploy'da kayıp olmasın).

---
_Durum: AKTİF · publish_web.py bu oturumda eklendi. Kalan: env'leri ayarla + git push kimliğini test et + günlük ritüele başla._
