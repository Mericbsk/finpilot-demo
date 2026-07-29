# FinPilot — TEK-DOKUNUŞLA YAYIN: FAZ 2 ÇÖZÜM RAPORU
Layer: 02-engineering + 05-governance · 2026-07-29 · (Faz 1 tamamlandıktan sonra)

## 2.1 — Önceliklendirme kovaları
**KOVA A — Doğrulanmış & Sağlam (dokunma, izle):** `publish_web.py` git-push kodu · `maybe_trigger_draft` gating (jobs.py:555) · `expire_stale→notify_admin` (broadcast.py:164) · decision-log kararları · snapshot git-tracked yapısı · DB `journal_mode=delete`.

**KOVA B — Düşük risk (bir test çalıştır + logla):**
- B1: `harden_db.py` çalıştırma çıktısını üret (DELETE zaten görünüyor; teyit için `python scripts\harden_db.py` bir kez koş, çıktıyı sakla).
- B2: git push→Vercel deploy testi (aşağıda C1 ile birlikte).
- B3: Telegram teslim testi (bir test brifi; C5 tam turunun parçası).

**KOVA C — Yüksek risk (kapanmadan Faz 3 YOK):** C1-C5 aşağıda.

## 2.2 — KOVA C maddeleri

### C1 — Web-deploy kancası devrede değil
- **SORUN:** `.env`'de `FINPILOT_WEB_PUBLISH_CMD` YOK → `_push_snapshot_to_web` `publish_web.py`'yi çağırmıyor; web güncellenmez.
- **RİSK:** Yayınladığını sanırsın ama finpilot.at eski kalır → "web yayını" fiilen çalışmaz.
- **ÇÖZÜM ADIMLARI:** `.env`'e ekle:
  `FINPILOT_WEB_PUBLISH_CMD=python scripts/publish_web.py`
  `FINPILOT_REQUIRE_VERCEL_DEPLOY=0`  (push zaten deploy tetikler)
  Git push kimliğini (PAT/SSH) kur; `python scripts\publish_web.py` bir kez elle koş.
- **DOĞRULAMA TESTİ:** `publish_web.py` çıktısı "pushed → Vercel deploy tetiklendi" + Vercel dashboard'da yeni deploy + finpilot.at/demo'da güncel tarih (cache temizlenmiş).
- **SORUMLU:** İnsan (env + git kimlik) · **SEVİYE:** B (uygulama)

### C2 — Bot-süpervizör dosyaları eksikti (DÜZELTİLDİ)
- **SORUN:** `scripts/run_bot.py` + `scripts/start_bot.bat` repo'da YOKTU; `telegram_bot_runner.py` kökte.
- **RİSK:** Bot çalışmaz → `/start`/`/feedback` toplanmaz → kitle/feedback darboğazı sürer.
- **ÇÖZÜM (uygulandı):** `scripts/run_bot.py` + `scripts/start_bot.bat` yeniden oluşturuldu; bot = **kök** `telegram_bot_runner.py`, `PYTHONPATH=kök` ile `telegram_config` çözülür.
- **DOĞRULAMA TESTİ:** `python scripts\run_bot.py` → "süpervizör başladı" + Telegram'dan `/start` → `tg_users` artar (`SELECT count(*) FROM tg_users`). PC restart → `start_bot.bat` (shell:startup) → bot otomatik ayağa kalktı mı.
- **SORUMLU:** AI (dosya) + İnsan (startup kısayolu + gözlem) · **SEVİYE:** B

### C3 — Kalıcı waitlist aynası ayarsız
- **SORUN:** `.env`'de `WAITLIST_WEBHOOK_URL` YOK → kayıtlar yalnız ephemeral Render diskinde.
- **RİSK:** Render redeploy → toplanan e-postalar SİLİNİR (geri dönüşsüz).
- **ÇÖZÜM ADIMLARI:** Google Apps Script web app (Sheet'e appendRow) kur → URL'i `WAITLIST_WEBHOOK_URL`'e ekle; ayrıca `FINPILOT_ADMIN_KEY=<gizli>` (waitlist/list için).
- **DOĞRULAMA TESTİ:** test kaydı yap → Sheet'te göründü mü; Render redeploy sonrası Sheet hâlâ dolu mu.
- **SORUMLU:** İnsan · **SEVİYE:** C (veri kaybı)

### C4 — SMTP rotasyonu doğrulanamadı
- **SORUN:** Sızan SMTP şifresinin rotate edildiği kanıtlanamadı (yerel `.env`'de yok; Render'da olabilir).
- **RİSK:** Eski şifre aktifse hesap/e-posta ele geçirme.
- **ÇÖZÜM ADIMLARI:** Sağlayıcıdan yeni şifre üret + eskisini İPTAL et; yalnız env'de sakla (yerel + Render); git geçmişinde arama (`git log -S`).
- **DOĞRULAMA TESTİ:** yeni şifreyle test e-postası gider; eskiyle gönderim BAŞARISIZ.
- **SORUMLU:** İnsan · **SEVİYE:** C (güvenlik, P0)

### C5 — Uçtan-uca tam tur hiç doğrulanmadı
- **SORUN:** Kabul kriteri (scan→publish→Telegram→web→arşiv→yedek→streak) fiilen çalıştırılmadı.
- **RİSK:** "Hazır" sanılan hat ilk gerçek günde kırılabilir.
- **ÇÖZÜM:** 2.3'teki 8-adım turu senin makinende koş, her adımı kanıtla.
- **DOĞRULAMA TESTİ:** 2.3 (aşağı) · **SORUMLU:** İnsan (AI yorumlar) · **SEVİYE:** B

## 2.3 — Uçtan-uca TAM TUR test planı (senin makinende, her adım kanıtlı)
1. Elle scan → `data/distribution/scan_export_latest.json` **mtime** bugünkü mü?
2. `python scripts\publish_now.py` → prepublish gate GEÇTİ mi (çıktı) / hata mı?
3. Taslak gösterildi → Enter → gönderim tetiklendi mi (çıktı)?
4. Telegram kanalında brif GÖRÜNDÜ mü (mesaj ID / ekran görüntüsü)?
5. `publish_web.py` push etti mi (`git log -1` yeni commit)?
6. finpilot.at/demo GÜNCEL mi (cache temizlenmiş; `demo_snapshot.json` bugünkü tarih)?
7. Arşiv + yedek YAZILDI mı (`backups/<bugün>/` + signals_archive büyüdü mü)?
8. `publish_streak()` önce/sonra ARTTI mı?
> Herhangi biri başarısız → o adıma özel yeni KOVA C maddesi.

---
_Faz 3 (telefondan onay / DISTRIBUTION=1 genişletme) yalnızca C1-C5 kapanıp 2.3 turu başarılı olunca AÇILIR. Bu oturumda uygulanan: run_bot.py + start_bot.bat (C2). Gerisi senin aksiyonun._
