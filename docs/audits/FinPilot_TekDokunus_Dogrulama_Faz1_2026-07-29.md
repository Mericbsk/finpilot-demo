# FinPilot — TEK-DOKUNUŞLA YAYIN: FAZ 1 DOĞRULAMA RAPORU
Layer: 05-governance · Escalation: karma · 2026-07-29
Kaynaklar: FinPilot_OnTarama_TelegramWeb_Yayin_2026-07-28 · FinPilot_TekDokunusla_Yayin_Plani_2026-07-28
Kural: yalnız KANIT gösterilen "Doğrulandı"dır. Canlı sistem (git push→Vercel, Telegram teslim, Windows başlangıç) sandbox'tan test EDİLEMEZ → "Test Edilmedi".

## ÖZET SAYIM
- **Doğrulandı (kod kanıtıyla): 6**
- **Doğrulandı = EKSİK (kanıtlı olarak yapılmamış/ayarsız): 5** ← en kritik
- **Kısmen doğrulandı: 1**
- **Test Edilmedi (ortam erişimi yok): 8**
> ⚠️ Plan "AKTİF" diyordu ama fiilen **web-deploy hattı ve bot-yaşatma altyapısı devrede DEĞİL** (aşağıda kanıtlı).

## 1.1 — Ön-tarama iddiaları
| # | İddia | Yöntem | Sonuç + Kanıt |
|---|---|---|---|
| 1 | Otomasyon kancaları koda bağlı ama kapalı | kod okuma | **Doğrulandı** — `maybe_trigger_draft_after_scan` (jobs.py:542) `distribution_enabled()`'a bağlı (jobs.py:555) |
| 2 | Web-deploy tuzağı git-push ile kapatıldı | dosya+env | **KISMEN/EKSİK** — `publish_web.py` VAR ve git add/commit/push yapıyor (satır 33/40/44), AMA `.env`'de **FINPILOT_WEB_PUBLISH_CMD YOK** → kanca devrede DEĞİL. Gerçek push→Vercel testi **yapılmadı**. |
| 3 | "expired" alarmı bir kanala bağlı | kod | **Doğrulandı (kod)** — `expire_stale` (broadcast.py:146) `notify_admin` (Telegram DM) çağırıyor (satır 164-166). Gerçek expired senaryosunda teslim **test edilmedi**. |
| 4 | Kanal `@Finpilot_Breif` kararı log'da | grep | **Doğrulandı** — decision-log'da kanal+web-deploy kararları var (3 eşleşme). Not: lansman yaklaşınca yeniden gözden geçirilmeli. |
| 5 | SMTP sızıntısı rotate edilmedi | env | **Test Edilmedi** — yerel `.env`'de `SMTP_PASSWORD` YOK (Render'da olabilir); rotasyon durumu sandbox'tan **doğrulanamaz**. Kanıt yokluğu = riskli kabul. |
| 6 | Ephemeral Render — webhook aynası aktive edilmeli | env | **Doğrulandı = EKSİK** — `.env`'de `WAITLIST_WEBHOOK_URL` YOK → kalıcı ayna **aktif değil**; veri-kaybı riski AÇIK. |
| 7 | Tek-PC bağımlılığı | gözlem | **Test Edilmedi** — PC-kapalı kesinti testi yapılmadı; teorik risk. |

## 1.2 — Plan iddiaları (KRİTİK — "yapıldı" ≠ doğrulandı)
| # | İddia | Yöntem | Sonuç + Kanıt |
|---|---|---|---|
| 1 | Vercel push'ta otomatik deploy | dosya+dış | **Doğrulandı (yapı)** — remote=github.com/Mericbsk/finpilot-demo; `demo_snapshot.json`+`academy_lessons.json` git'te izleniyor + geçmişte commit'li. **Ama** push'un Vercel deploy'u GERÇEKTEN tetiklediği (dashboard) **test edilmedi**. |
| 2 | Git push kimliği test edildi | çalıştırma | **Test Edilmedi** — plan zaten "kalan: git push kimliğini test et" diyor. Yapılmadı. |
| 3 | `harden_db.py` çalıştırıldı (WAL→DELETE) | DB PRAGMA | **Kısmen Doğrulandı** — 3 DB de ŞU AN `journal_mode=delete` (önceden WAL idi). harden_db çalışmış YA DA store.py devrede olabilir; script çıktısı gözlenmedi. |
| 4 | Bot yaşatıldı: run_bot.py + start_bot.bat startup'ta | dosya+gözlem | **DOĞRULANAMADI — DOSYALAR YOK** — `scripts/run_bot.py` ve `scripts/start_bot.bat` MEVCUT DEĞİL (yalnız eski `__pycache__/run_bot.pyc` kaldı). `telegram_bot_runner.py` **kökte** (scripts/'te değil). Yani bot-süpervizör altyapısı **repo'da yok**; startup kısayolu doğrulanamaz. |
| 5 | Kabul kriteri: tam tur + streak artışı | uçtan uca | **Test Edilmedi** — tam tur çalıştırılmadı → kabul kriteri KARŞILANMADI. |
| 6 | Env'ler dolu (TOKEN/CHAT/ADMIN/EODHD...) | .env | **Karışık** — DOLU: DISTRIBUTION, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_CHANNEL_ID, EODHD_API_KEY, REQUIRE_VERCEL_DEPLOY. **YOK/BOŞ:** WEB_PUBLISH_CMD, VERCEL_DEPLOY_HOOK_URL, WAITLIST_WEBHOOK_URL, FINPILOT_ADMIN_KEY, FINPILOT_ACADEMY_WEB_JSON, SMTP_PASSWORD. |

## 1.3 — Kapsanmayan (ortam kısıtı)
Sandbox repo aynasıdır; şunlar **test edilemedi**: gerçek git push→Vercel deploy; Telegram'a gerçek teslim; canlı finpilot.at güncellemesi; Render redeploy sonrası waitlist kaybı/webhook; Windows startup kısayolu; PC-kapalı bot davranışı; SMTP rotasyonu; harden_db çalıştırma çıktısı; tam uçtan-uca tur. Bunların hepsi **senin makinende** gözlemlenmeli.

## Faz 1 kararı
Plan kâğıtta hazır ama **fiilen devrede DEĞİL**: (a) web-deploy kancası ayarsız, (b) bot-süpervizör dosyaları repo'da yok, (c) kalıcı waitlist aynası + admin key + akademi export ayarsız, (d) hiçbir uçtan-uca tur doğrulanmadı. **Faz 2'ye geçilir; Faz 3 (telefondan onay/genişletme) bunlar kapanmadan AÇILMAZ.**
