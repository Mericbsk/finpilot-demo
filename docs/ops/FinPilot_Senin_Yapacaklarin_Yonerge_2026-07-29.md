# FinPilot — SENİN YAPACAKLARIN (Adım Adım Yönerge)
Durum: AKTİF · 2026-07-29 · Hedef: Tek-dokunuşla yayın hattını GERÇEKTEN devreye almak (Faz 2 / KOVA C).
Her adım: **NE YAP · NASIL (tam komut) · BEKLENEN (çalıştı mı) · TAKILIRSAN.**
Sıra önemlidir — yukarıdan aşağı git.

---

## ADIM 0 — Hazırlık (her seferinde)
**NE YAP:** PowerShell'i aç ve proje klasörüne git.
**NASIL:**
1. Başlat → "PowerShell" yaz → Enter.
2. Şu komutu yapıştır:
   ```powershell
   cd C:\Users\meric\Borsa
   ```
**BEKLENEN:** Satır başı `PS C:\Users\meric\Borsa>` oldu.
**TAKILIRSAN:** Klasör farklıysa doğru yolu yaz.

---

## ADIM 1 — .env'e web-yayın kancasını ekle (C1)
**NE YAP:** `.env` dosyasına 3 satır ekle (bunlar gizli değil).
**NASIL:**
1. Aç:
   ```powershell
   notepad .env
   ```
2. ⚠️ **ÖNCE ÇELİŞKİYİ ÇÖZ:** `.env`'de `FINPILOT_REQUIRE_VERCEL_DEPLOY` İKİ KEZ tanımlıysa (hem =1 hem =0), **=1 olanı SİL** — tek `=0` kalsın. (Çift tanım belirsiz/tehlikeli.) Neden 0: git-push deploy'u tetikler, ayrı hook yok; =1 olursa publish "başarısız" sayar.
3. Dosyanın sonuna şu satırları ekle (yoksa):
   ```
   FINPILOT_WEB_PUBLISH_CMD=python scripts/publish_web.py
   FINPILOT_REQUIRE_VERCEL_DEPLOY=0
   FINPILOT_ACADEMY_WEB_JSON=C:\Users\meric\Borsa\web\public\academy_lessons.json
   ```
   (REQUIRE_VERCEL_DEPLOY zaten varsa yeni satır ekleme; mevcut tek satırı 0 yap.)
4. Kaydet (Ctrl+S), kapat.
**BEKLENEN:** Dosyada bu satırlar var. Kontrol:
   ```powershell
   findstr WEB_PUBLISH_CMD .env
   ```
   → satırı gösterirse tamam.
**TAKILIRSAN:** `.env` yoksa `.env.example`'ı kopyala: `copy .env.example .env`.

---

## ADIM 2 — Git kimliğini kur ve web-push'u ELLE test et (C1 kanıtı)
**NE YAP:** `publish_web.py` git push yapacak; git'in senin adına push edebildiğini doğrula.
**NASIL:**
1. Git kullanıcı bilgisi (bir kez):
   ```powershell
   git config user.name "Meriç Başak"
   git config user.email "mericbsk@gmail.com"
   ```
2. Elle bir test push (küçük bir değişiklikle):
   ```powershell
   python scripts\publish_web.py
   ```
**BEKLENEN:**
- "publish_web: pushed → Vercel deploy tetiklendi ..." **ya da** "değişiklik yok — commit atlanıyor" (snapshot değişmediyse normal).
- Push başarısızsa "PUSH HATASI (kimlik/ağ?)" görürsün → kimlik sorunu.
**TAKILIRSAN (push hatası):**
- GitHub kimliği gerekiyor. En kolay: **GitHub Desktop** kur ve bir kez giriş yap, ya da bir **Personal Access Token (PAT)** oluştur (GitHub → Settings → Developer settings → Tokens) ve `git push` ilk sorduğunda kullanıcı adı + token (şifre yerine) gir.
- Doğru dalda mısın: `git branch` → `main` olmalı.

---

## ADIM 3 — Veritabanı sertleştirme (bir kez) (B1)
**NE YAP:** WAL→DELETE bozulma çaresini uygula — AMA önce gerekli mi kontrol et.
**ÖNCE KONTROL (çalıştırmadan):**
```powershell
python -c "import sqlite3;[print(f, sqlite3.connect('data/'+f).execute('PRAGMA journal_mode').fetchone()[0]) for f in ['finpilot.db','distribution.db','academy.db']]"
```
- Üçü de **`delete`** ise → `harden_db.py` GEREKSİZ, **bu adımı ATLA**.
- Biri **`wal`** ise → devam et (aşağı).
**NASIL (yalnız wal varsa):** Bot/worker DB'yi açık tutar; **önce onları durdur** (Adım 4'teki bot dahil), sonra:
```powershell
python scripts\harden_db.py
```
sonra bot'u yeniden başlat.
**BEKLENEN:** Her DB için `{'db': ..., 'before': ..., 'after': 'delete', 'integrity': 'ok'}` satırları.
**TAKILIRSAN:** "malformed" görürsen o DB bozuk → `backups\` klasöründen geri yükle, tekrar dene.
**EK (makine ayarı):** `data\` klasörünü OneDrive senk-dışı bırak + antivirüs istisnası (`*.db`, `-wal`, `-shm`).

---

## ADIM 4 — Botu başlat ve PC açılışına ekle (C2)
**NE YAP:** Public bot (/start, /feedback) sürekli çalışsın — AMA çift bot olmasın.
**⚠️ ÖNCE ÇİFT-BOT KONTROLÜ (kritik):** Aynı token'la 2 poller → Telegram 409 Conflict → mesajlar düşer. Kaç bot süreci var:
```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'run_bot|telegram_bot_runner' } | Select-Object ProcessId,CommandLine | Format-List
```
- **Tek** `run_bot.py`/`telegram_bot_runner.py` süreci olmalı. Fazlaysa fazlalıkları kapat (`Stop-Process -Id <pid>`).
- Startup'a eklemeden önce **başka otomatik-başlatma** (Görev Zamanlayıcı / önceki startup kaydı) var mı bak — varsa İKİSİNİ birden koyma.
**NASIL:**
1. Botun konuşması için `.env`'de `TELEGRAM_BOT_TOKEN` ve `TELEGRAM_CHAT_ID` **dolu olmalı** (kontrol: `findstr TELEGRAM_BOT_TOKEN .env`).
2. Zaten çalışmıyorsa başlat:
   ```powershell
   python scripts\run_bot.py
   ```
3. **Otomatik başlatma (tek poller garantisiyle):** Win+R → `shell:startup` → Enter → `C:\Users\meric\Borsa\scripts\start_bot.bat` **kısayolunu** buraya koy. Başka bir otomatik-başlatma varsa onu kaldır.
**BEKLENEN:**
- Konsolda "süpervizör başladı → telegram_bot_runner.py".
- Telegram'da bota `/start` yaz → botun cevap verdiğini gör.
- Kayıt oldu mu:
   ```powershell
   python -c "import sqlite3;print('users',sqlite3.connect('data/distribution.db').execute('SELECT count(*) FROM tg_users').fetchone()[0])"
   ```
**TAKILIRSAN:** "ModuleNotFoundError: telegram_config" → botu **kök klasörden** çalıştırdığından emin ol (run_bot.py bunu otomatik yapar); `telegram_config.py` `C:\Users\meric\Borsa` kökünde mi kontrol et.

---

## ADIM 5 — Waitlist kalıcı ayna (Google Sheet) + admin anahtarı (C3)
**NE YAP:** Kayıtların Render silinse bile kaybolmaması için Google Sheet'e aynalı yaz.
**NASIL:**
1. Yeni bir Google Sheet aç.
2. Üst menü → **Extensions → Apps Script**.
3. Açılan editöre şunu yapıştır (varsa mevcut kodu sil):
   ```javascript
   function doPost(e) {
     const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
     const d = JSON.parse(e.postData.contents);
     sheet.appendRow([d.signed_up_at, d.email, d.source, d.utm]);
     return ContentService.createTextOutput("ok");
   }
   ```
4. **Deploy → New deployment → "Web app"** seç → "Who has access: **Anyone**" → **Deploy** → verdiği **URL'i kopyala**.
5. `.env`'e ekle (notepad .env):
   ```
   WAITLIST_WEBHOOK_URL=<kopyaladığın-url>
   FINPILOT_ADMIN_KEY=<kendi-seçtiğin-gizli-bir-değer>
   ```
   (Bu iki değeri **Render**'ın environment ayarlarına da ekle — canlı site için.)
**BEKLENEN:** Sitene bir test e-postası kaydettiğinde Google Sheet'e satır düşer.
**KANITLA:** Bir kayıt yap → Sheet'te göründü mü; Render'ı redeploy et → Sheet hâlâ dolu mu.
**Kayıtları görmek için:**
   ```powershell
   curl -H "X-Admin-Key: <FINPILOT_ADMIN_KEY-değerin>" http://localhost:8001/api/v1/waitlist/list
   ```

---

## ADIM 6 — SMTP şifresini rotate et (C4 — güvenlik, önemli)
**NE YAP:** Sızmış SMTP şifresini iptal edip yenisini kur.
**NASIL:**
1. E-posta sağlayıcının panelinden **yeni bir uygulama şifresi** üret; **eskisini iptal et**.
2. Yeni şifreyi **yalnız** env'e koy: yerel `.env`'de `SMTP_PASSWORD=<yeni>` + **Render** environment'ına da.
3. Şifreyi koda/commit'e ASLA yazma.
**BEKLENEN:** Yeni şifreyle test e-postası gider; eski şifreyle gönderim başarısız.
**TAKILIRSAN:** Sağlayıcı bilinmiyorsa `.env`'de `SMTP_HOST` satırına bak (hangi sunucu).

---

## ADIM 7 — UÇTAN-UCA TAM TUR (C5 — kabul kriteri)
**NE YAP:** Gerçek bir günü baştan sona çalıştır, her adımı kanıtla.
**NASIL & KANIT (her adımı işaretle):**
1. **Scan çalıştır** (senin tarama komutun) → kontrol:
   ```powershell
   dir data\distribution\scan_export_latest.json
   ```
   → Tarih/saat **bugün** mü? ☐
2. **Yayın:**
   ```powershell
   python scripts\publish_now.py
   ```
   → "PRE-PUBLISH GATE" hatası YOK, taslak gösterildi mi? ☐
3. **Onay:** taslağı oku → **Enter**'a bas (Ctrl+C = iptal). ☐
4. **Telegram:** kanalda brif göründü mü? (ekran görüntüsü al) ☐
5. **Web push:**
   ```powershell
   git log -1 --oneline
   ```
   → En üstte "chore(web): daily snapshot ..." commit'i var mı? ☐
6. **Canlı web:** finpilot.at/demo'yu **Ctrl+F5** ile aç → tarih bugünkü mü? ☐
7. **Arşiv+yedek:**
   ```powershell
   dir backups\%date%  ; python -c "import sqlite3;print(sqlite3.connect('data/finpilot.db').execute('SELECT count(*) FROM signals_archive').fetchone()[0])"
   ```
   → Bugünün yedek klasörü var + arşiv sayısı arttı mı? ☐
8. **Seri:**
   ```powershell
   python -c "from distribution.broadcast import publish_streak;print('streak',publish_streak())"
   ```
   → Değer arttı mı? ☐
**8/8 ✓ ise:** hat CANLI, kabul kriteri karşılandı. Bir adım ✗ ise: o adımı not al, birlikte çözelim.

---

## Özet kontrol listesi
- ☐ ADIM 1: .env web kancası
- ☐ ADIM 2: git push testi
- ☐ ADIM 3: harden_db + OneDrive/AV
- ☐ ADIM 4: bot çalışıyor + startup
- ☐ ADIM 5: waitlist Sheet + admin key
- ☐ ADIM 6: SMTP rotasyonu
- ☐ ADIM 7: 8/8 tam tur

_Bittiğinde: KOVA C kapanır, hat gerçekten canlı olur ve ancak o zaman Faz 3 (telefondan onay) değerlendirilir._
