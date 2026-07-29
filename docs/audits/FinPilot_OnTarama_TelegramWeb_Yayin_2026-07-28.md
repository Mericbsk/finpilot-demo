# FinPilot — ÖN-TARAMA: Telegram + Web Yayınına Başlamadan Önce
Durum: AKTİF · 2026-07-28 · Tür: keşif taraması (findings → detaylı plan sonra)

## 1. Mevcut yayın zinciri (kanıt: distribution/jobs.py)
`scan → job_draft (snapshot + brief + lint) → ONAY → job_publish → [Telegram send_to_channel] + [_push_snapshot_to_web]`
- Mod: **MANUEL** (`FINPILOT_ENABLE_DISTRIBUTION=0`); yayın `scripts/publish_now.py` ile.
- **Web push mekaniği hazır:** EN snapshot → `web/public/demo_snapshot.json` (premium alanları temizlenmiş demo_view) + iki opsiyonel kanca:
  - `FINPILOT_WEB_PUBLISH_CMD` (shell: repo'ya kopyala / R2'ye rclone)
  - `FINPILOT_VERCEL_DEPLOY_HOOK_URL` (POST → Vercel redeploy)
  - İkisi de yoksa + `FINPILOT_REQUIRE_VERCEL_DEPLOY=1` → **hata verir** (güvenli varsayılan).
- **Otomasyon kancaları KODDA VAR ama kapalı:** `maybe_trigger_draft_after_scan` (scan sonrası taslağı otomatik kuyruğa alır — DISTRIBUTION=1 + universe≥100 + işlem günü + gün-içi tekrar yok şartlarıyla).

## 2. Manuel ⟷ Otomatikleştirilebilir haritası
| Adım | Şu an | Otomatikleştirilebilir mi | Öneri |
|---|---|---|---|
| Tam-evren tarama | Manuel/scheduler | Evet (12:00 Viyana penceresi) | **Otomatikleştir** |
| Taslak üretimi (snapshot+brief+lint) | Manuel (publish_now) | Evet (`maybe_trigger_draft_after_scan`) | **Otomatikleştir** (scan sonrası taslak Telegram'a düşsün) |
| **ONAY** (kalite kapısı) | Manuel (ONAYLA / --yes) | Teknik olarak evet (auto-approve) | **İNSANDA KALSIN** — finansal brif; güvenlik kapısı |
| Telegram teslim | job_publish otomatik | — | Onaydan sonra otomatik |
| Web güncelleme | job_publish + deploy hook | Evet (`VERCEL_DEPLOY_HOOK_URL`) | **Otomatikleştir** (tuzağa dikkat ↓) |
| Akademi→web export | env-kapılı (bu oturumda) | Evet | Aktive et |
| Bot uptime | run_bot.py + auto-start | Evet (bu oturumda) | Aktive et |

## 3. 🚧 Başlamadan DİKKAT — tuzaklar/riskler
1. **WEB DEPLOY TUZAĞI (en kritik):** `demo_snapshot.json`'u yerel `web/public`'e yazmak, Vercel'de CANLI olması demek DEĞİL. Vercel commit'lenen repo'yu build eder. Ya `WEB_PUBLISH_CMD` ile snapshot'ı **git commit+push** et (push zaten Vercel'i tetikler), ya da statik bir store'a (R2/S3) yazıp oradan servis et. Yalnız deploy-hook + push'lanmamış yerel dosya = "web güncellenmedi" kafası. **Başlamadan bu akışı netleştir.**
2. **Onay kapısı = seri katili:** yayın onaya kilitli; bot çalışmıyor/onay unutulursa "expired" (seri kırılır). Alarm eklendi ama **bot canlı olmalı** + günlük ritüel şart.
3. **Kanal adı `@Finpilot_Breif`** ("Brief" yazım hatası) — düzelt/karara bağla.
4. **SMTP sızıntısı** rotate edilmedi (güvenlik — waitlist maili + genel).
5. **Ephemeral Render:** waitlist/veri redeploy'da silinebilir (webhook aynası mitige eder — aktive et).
6. **Compliance:** her taslak lint'ten geçmeli (tavsiye-dili yok) — job_draft'ta otomatik; ama kanal biyografisi/pinned mesaj da uyumlu olmalı.
7. **Tek-PC:** PC yoksa yayın yok; auto-approve güvenliği bozar, o yüzden çözüm "her sabah PC + bot canlı."

## 4. Ne daha iyi/daha otomatik yapılabilir (insan kapısını KORUYARAK)
**Hedef mimari: "tek-dokunuşla yayın"** —
`otomatik scan (12:00 Viyana) → otomatik taslak → Telegram'a düşer → sen ONAYLA'ya bas → Telegram + web otomatik güncellenir + arşiv + yedek.`
Yani sadece **onay** insanda; gerisi otomatik. Bu, kalite güvenliğini kaybetmeden manuel yükü ~1 dakikaya indirir.

## 5. Nereye odaklanmalıyız / hangi planla başlayalım
**Öncelik sırası (önerilen):**
1. **Web deploy akışını doğru kur** (tuzak #1) — snapshot'ın Vercel'e ULAŞMA yolu (git push mü, R2 mı) + `VERCEL_DEPLOY_HOOK_URL`. Bu olmadan "web yayını" çalışmaz.
2. **Bot'u yaşat + kanal adı kararı** — Telegram tarafının ön-koşulu.
3. **Scan→taslak otomasyonu** — `maybe_trigger_draft_after_scan`'i aç (yalnız taslak; onay hâlâ insan).
4. **Kesintisiz teslim ritüeli** — her işlem günü ONAYLA + expired alarmı izle.
5. **Env'ler:** `VERCEL_DEPLOY_HOOK_URL`, `WEB_PUBLISH_CMD`, `WAITLIST_WEBHOOK_URL`, `EODHD_API_KEY`, SMTP rotasyonu.

## 6. Detaylı plan için karara bağlanacak sorular (sonraki adım)
- Web snapshot Vercel'e **nasıl** ulaşacak: (a) git commit+push otomasyonu mu, (b) R2/S3 static mı?
- Scan **tam otomatik mi** (scheduler açık) yoksa "her sabah elle scan + oto-taslak" mı?
- Onay: sadece Telegram ONAYLA mı, yoksa publish_now --yes ritüeli mi?
- Kanal adı: `@Finpilot_Breif` düzeltilsin mi (yeni kanal = takipçi sıfırlanır) yoksa kalsın mı?

---
_Durum: AKTİF · Keşif taraması. Bu bulgulara göre "tek-dokunuşla yayın" detaylı uygulama planı bir sonraki adımda kurulacak._
