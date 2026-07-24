# FinPilot — Çalışma Yönergesi (Operations Charter)

> Amaç: tekrar eden kırılmaları **net sınırlar** ve **tanımlı görevlerle** en aza indirmek.
> ROL: Bu doküman OPERASYONUN tek otoritesidir (nasıl çalışırız). AI çalışma kuralları `_instructions/00-core.md`'de, güncel durum `LAUNCH_CHECKLIST.md`'de, kararlar `docs/governance/decision-log.md`'dedir (bkz. `docs/INDEX.md` otorite haritası). Her Pazartesi birlikte gözden geçirilir.
> Sürüm: 1.1 · Son güncelleme: 2026-07-24 (rol netleştirme — ReAudit R1)

---

## 0. Beş Temel İlke (ezberlenmeli)

1. **Üretim davranışı bir SÖZLEŞMEDİR** — korunmadan değiştirilmez.
2. **Runtime veri git'e girmez.**
3. **Üretilen artifact elle düzenlenmez.**
4. **Tek tarama → tek snapshot → tüm yüzeyler** (web + Telegram aynı kaynaktan).
5. **Sır asla paylaşılmaz / commit edilmez.**

---

## 1. Dosya Sınıfları ve Kuralları

| Sınıf | Örnek | Kural |
|------|-------|-------|
| **Üretim kodu** | `scanner/`, `distribution/`, `api/`, `llm/`, `web/src/` | Git'te; dalda değişir; test şart |
| **Runtime veri** | `data/*.json`, `data/shadow/`, `data/distribution/*.json`, `*.db` | `.gitignore` — **ASLA commit** |
| **Üretilen artifact** | `web/public/demo_snapshot.json`, `snapshot_latest.json` | Yalnız pipeline üretir — **elle DOKUNMA** |
| **Config / sır** | `.env` | Git'te **YOK**; yedeği şifre yöneticisinde |
| **Araştırma** | `research/`, `reports/`, backtest | Ayrı; deploy'a girmez |
| **Geçici artık** | `.fuse_hidden*`, `__pycache__`, `*.pyc` | Repodan temizlenir |

---

## 2. Scanner ↔ Distribution Sözleşmesi (HARD CONTRACT)

`evaluate_symbol()` her satırda şu alanları **üretmek zorundadır** (dağıtım katmanı bunlara bağımlı):

```
selection_eligible · execution_feasible · execution_confidence · data_quality
execution_reject_reason · reject_reason
legacy_quality_score · ranking_score · ranking_method · v2_score · strategy_scores
conviction_tier · conviction_prob
position_cap_notional · position_cap_applied · position_cap_reject_reason
```

Kurallar:
- `legacy_quality` = **production ranking**. V2 = **yalnız shadow**. `selected_by_legacy_quality / _v2 / _both` açıkça yazılır.
- Bu alanları **kaldırmak / yeniden adlandırmak = KIRICI değişiklik.** Ancak `contract test` + `snapshot test` birlikte güncellenerek yapılır.
- **Yazma-anında şema doğrulaması:** alan eksikse export **başarısız olmalı** (sessizce bozuk üretmemeli).
- Sözleşmeye dokunan her PR açıklamasında "contract impact" bölümü olur.

---

## 3. Git Disiplini

- Runtime veri `.gitignore`'da; commit'e girmez.
- **Tek konu = tek commit**; kod ile veri asla aynı commit'te değil.
- Değişiklik **dalda** yapılır; `main` korunur; **deploy yalnız `main`'den**.
- Deploy öncesi `git status` **temiz** olmalı — staged/unstaged/yeni dosya karışıklığıyla deploy edilmez ("kod yeni, web eski" bundan doğar).
- `.fuse_hidden*`, cache, `*.pyc` commit'ten önce temizlenir.

---

## 4. Tarama / Export Kuralları

- **Tam tarama** (`universe=1812`) ile **küçük test taraması** AYRI dosyalara yazılır.
- Küçük tarama tam export'u **ASLA ezmez.** Guard: `universe` **+** `scan_id` **+** benzersiz sembol sayısı.
- Dosya adları ayrık:
  ```
  scan_export_<date>_full.json
  scan_export_<date>_partial_<scan_id>.json
  ```
- `scan_export_latest.json` yalnız **tam-evren** tarama tarafından güncellenir.

---

## 5. Snapshot Tek-Kaynak Kuralı

- Web **ve** Telegram **aynı `build_snapshot()` koşusundan** beslenir (aynı `snapshot_id`).
- Artifact **elle düzenlenmez.** Bozulursa: `git checkout <artifact>` → temiz tam tarama → `publish` ile yeniden üretilir.
- **Toleranslı JSON okuyucu bütünlük-kapılı olmalı:** `date == bugün` **ve** `universe == beklenen` **ve** tek-JSON-nesnesi değilse → **hata ver + admin'e yüksek sesle uyar** (bayat/yanlış veriyi sessizce yayınlama).

---

## 6. Deploy Disiplini

**Vercel (web):**
- Project root = **`web/`** (asıl düzeltme budur). Tek standart deploy komutu.
- Büyük klasörler ignore: `.venv*`, `__pycache__`, `data/`, `research/`, `reports/`, `scripts/`, `api/`. (`demo_snapshot.json` **dahil kalır**.)
- Deploy sonrası otomatik smoke: `GET /demo_snapshot.json` → `date == bugün`, `universe == 1812`, `candidate > 0`.

**Render (API):**
- Guard + SMTP kodu **commit'li** olmalı; env panelde doğrulanır.
- Deploy sonrası test signup → mailin `finpilot@finpilot.at` inbox'ına ulaştığı doğrulanır.

---

## 7. Telegram Yayın Kuralları

- Günde **tek** pending `daily_free` taslağı; eski pending **expire** edilir.
- **Admin onay hedefi** (`7139868446`) ≠ **yayın kanalı** (`@handle`) — ayrı config, karıştırılmaz.
- Onay yalnız **aynı `snapshot_id`**'ye ait taslağı yayınlar.
- Delivery log her gönderimde: `queue_id · channel · telegram_message_id · snapshot_id · timestamp`.

---

## 8. Sırlar (Secrets)

- `.env` git'te **yok**; ekran görüntüsü/mesajda **paylaşılmaz**.
- Sır açığa çıktıysa **DERHAL rotate** (örn. `SMTP_PASSWORD`).
- Prod sırları Render/Vercel env panelinden yönetilir; local `.env` yedeği şifre yöneticisinde.

---

## 9. Değişiklik Protokolü (her değişiklikte)

**Öncesi:** `git status` temiz → dal aç → yedek al (E6 backup job'u).
**Sırasında:** sözleşme alanlarına dokunma; dokunduysan `contract test`'i güncelle. Runtime/artifact dosyalarına dokunma.
**Sonrası (kabul kapısı):**
1. `py_compile` + testler yeşil
2. Tam tarama smoke → export **sözleşmeli** mi (`selection_eligible` vb. var mı)
3. snapshot / web / Telegram **aynı adaylar** mı
4. Deploy smoke (`/demo_snapshot.json` doğru mu)

---

## 10. Roller (net sınırlar)

| Kim | Sorumluluk |
|-----|-----------|
| **Meriç** | Hesaplar · env/secrets · deploy onayı · günlük `ONAYLA` · OneDrive/AV/donanım · şifre rotasyonu |
| **Claude (kod)** | Üretim kodu — **sözleşmeyi KORUYARAK** · test ekleyerek · runtime/artifact'e dokunmadan |
| **Ortak** | Haftalık kapı denetimi · yönerge güncellemesi |

> **Claude için özel sınır (bugün acı çekerek öğrendik):** sandbox dosya-mount'u büyük dosyaları okurken/yazarken **bozabiliyor.** Bu yüzden Claude büyük/kritik dosyaları doğrudan düzenlemez; **tam snippet + git komutu verir**, Meriç kendi makinesinde uygular ve `git diff` ile doğrular.

---

## 11. Günlük Sağlık Kontrolü (2 dk)

- [ ] export `date == bugün`, `universe == 1812`
- [ ] snapshot / web / Telegram **aynı adaylar**
- [ ] Telegram'da pending taslak var mı → `ONAYLA`
- [ ] waitlist count arttı mı / mail geldi mi

---

## 12. Kırmızı Çizgiler (ASLA)

1. Regresyonlu/doğrulanmamış scanner ile **üretim taraması** koşma.
2. Üretilen artifact'i **elle düzenleme.**
3. Runtime veriyi **commit etme.**
4. Sözleşme alanını **sessizce kaldırma.**
5. Sırrı **paylaşma / commit etme.**
6. **Yarım/karışık commit** ile deploy.
7. Küçük taramayla full export'u **ezme.**

---

_Bu yönerge yaşayan bir belgedir. Yeni bir kırılma yaşandığında: kök nedeni bul → buraya tek satır kural ekle → bir daha yaşanmasın._
