# FinPilot Yayın — P0 Adım Adım Uygulama Planı

_Amaç: günlük brief yayın zincirini (scanner → snapshot → web demo + Telegram) güvenli ve manuel-kontrollü hale getirmek. Sıra önem sırasıdır: 1 → 4._

Doğrulanan giriş noktaları (kod):
- `distribution/jobs.py`: `distribution_status()`, `job_draft()`, `job_publish()`, `push_snapshot_manual(path)`, `_push_snapshot_to_web()`
- `distribution/snapshot_builder.py`: `build_snapshot(...)`
- `distribution/scan_contract.py`: sözleşme doğrulaması
- Bayrak: `FINPILOT_ENABLE_DISTRIBUTION` (varsayılan `0` = kapalı)

---

## P0-1 · SMTP şifre rotasyonu (GÜVENLİK — önce bu)

**Neden:** Şifre bir ekran görüntüsünde sızdı; git geçmişine veya loglara girmiş olabilir. Rotasyon yapılmadan hiçbir şey yayınlanmamalı.

**Adımlar**
1. E-posta sağlayıcı panelinden (SMTP hesabı) yeni bir uygulama şifresi/parola üret. Eski şifreyi **iptal et**.
2. Yeni şifreyi **yalnızca** ortam değişkeni olarak sakla — koda/`.env`'in commit'lenen kısmına YAZMA. Render'da: Dashboard → Service → Environment → `SMTP_PASSWORD` (ve gerekiyorsa `SMTP_USER`, `SMTP_HOST`, `SMTP_PORT`).
3. Yerelde test için `.env` kullanıyorsan `.env`'in `.gitignore`'da olduğunu doğrula (bkz. P0-4 ek adım).
4. Sızan şifre git geçmişinde mi? Kontrol et:
   ```powershell
   git log -p -S "<sızan_şifrenin_bir_parçası>" -- . | Select-String "SMTP"
   ```
   Geçmişte varsa: şifre zaten iptal edildiği için acil değil, ama ileride `git filter-repo` ile temizlemeyi not et.

**Doğrulama:** yeni şifreyle bir test e-postası gönder (waitlist onay akışı veya küçük bir SMTP smoke-test scripti). Eski şifreyle gönderim **başarısız** olmalı.

**Geri alma:** yok — eski şifre kalıcı iptal.

---

## P0-2 · Scanner sözleşmesini (contract) sağlam commit'ten geri al

**Neden:** Dağıtımın beklediği alanlar (ör. `selection_eligible`, `conviction_prob`, `ranking_method`) bir regresyonla kırıldı; bu yüzden `job_draft()` taslak üretemiyor / snapshot eksik çıkıyor.

**Adımlar**
1. Sözleşmeyi tanımlayan/tüketen dosyaların geçmişini çıkar:
   ```powershell
   git log --oneline -- distribution/scan_contract.py distribution/snapshot_builder.py core/pipeline.py
   ```
2. Regresyondan **önceki** son sağlam commit'i bul (alan adlarının bütün olduğu). İçerik farkını gör:
   ```powershell
   git show <iyi_commit>:distribution/scan_contract.py > $env:TEMP\good_contract.py
   code --diff distribution/scan_contract.py $env:TEMP\good_contract.py
   ```
3. Kırılan alanları geri getir. Tercih sırası:
   - Sadece o dosya bozulduysa: `git checkout <iyi_commit> -- distribution/scan_contract.py`
   - Birden çok dosyaya yayıldıysa: ilgili dosyaları tek tek `git checkout <iyi_commit> -- <dosya>` ile al, sonra sonraki iyi değişiklikleri elle yeniden uygula.
4. Sözleşmeyi **kilitleyen bir test ekle** (regresyonun tekrarını önler): `tests/test_scan_contract.py` — üretilen bir scan kaydında tüm zorunlu alanların varlığını ve tipini assert et.

**Doğrulama**
```powershell
python -c "from distribution import scan_contract; print('contract import OK')"
pytest tests/test_scan_contract.py -q
python -m distribution.jobs   # ya da distribution_status() çağrısı; sözleşme hatası kalmamalı
```

**Geri alma:** değişiklikleri ayrı bir dalda yap (`git switch -c fix/scan-contract`); sorun çıkarsa `git switch main` ile dön.

---

## P0-3 · demo_snapshot.json'u yeniden üret → web demoyu düzelt

**Neden:** `web/public/demo_snapshot.json` bozuk (ayrıştırılamıyor); `/demo` sayfası kırık/eski veri gösteriyor. P0-2 bittikten sonra yapılmalı (sağlam sözleşme = sağlam snapshot).

**Adımlar**
1. En güncel scan çıktısının mevcut olduğundan emin ol (`data/scan_export_latest.json` ya da senin scan komutunun ürettiği dosya). Yoksa önce bir tarama çalıştır.
2. Snapshot'ı yeniden üret:
   ```powershell
   python -c "from distribution.snapshot_builder import build_snapshot; print(build_snapshot())"
   ```
   Bu, güncel `demo_snapshot.json`'u (veya builder'ın çıktısını) oluşturur.
3. Snapshot'ı web'e it:
   ```powershell
   python -c "from distribution.jobs import push_snapshot_manual; print(push_snapshot_manual('data/demo_snapshot.json'))"
   ```
   (Doğru kaynak yolunu adım-2 çıktısına göre ver.)
4. JSON'u yerelde doğrula:
   ```powershell
   python -c "import json;d=json.load(open('web/public/demo_snapshot.json'));print('OK', d.get('date'), len(d.get('candidates',[])))"
   ```
5. Web'i çalıştırıp `/demo` sayfasını gör: `cd web; npm run dev` → http://localhost:3000/demo

**Doğrulama:** adım-4 hata vermeden `OK <tarih> <aday sayısı>` basmalı; `/demo` gerçek adayları göstermeli (uyarı bandı/`sample:true` olmamalı).

**Geri alma:** eski dosyayı commit'lemeden önce `git checkout -- web/public/demo_snapshot.json` ile geri al.

---

## P0-4 · Manuel yayın akışını devreye al (cron yerine kontrollü)

**Neden:** Kırılgan zamanlanmış yayını (draft→publish) manuel, onaylı bir akışla değiştir. Dağıtım varsayılan kapalı (`FINPILOT_ENABLE_DISTRIBUTION=0`); niyet manuel tetikleme.

**Adımlar**
1. Dağıtımı otomatik zamanlamada **kapalı tut** (Render env): `FINPILOT_ENABLE_DISTRIBUTION=0`. Böylece scheduler cron'ları ateşlemez; yayın sadece senin elinle olur.
2. Durum gör:
   ```powershell
   python -c "from distribution.jobs import distribution_status; import json; print(json.dumps(distribution_status(), ensure_ascii=False, indent=2))"
   ```
3. **Taslak üret** (snapshot + brief render + lint):
   ```powershell
   python -c "from distribution.jobs import job_draft; import json; print(json.dumps(job_draft(), ensure_ascii=False, indent=2))"
   ```
   Lint hatası varsa çıktıda görünür — yayın YASAK ifadeleri (al/sat, hedef fiyat vb.) burada yakalanır.
4. Taslağı **gözden geçir/onayla** (kodun onay mekanizması neyse: DB'de status alanı ya da onay fonksiyonu). Onaysız yayın olmamalı.
5. **Yayınla** (onaylı taslağı Telegram + web'e it):
   ```powershell
   python -c "from distribution.jobs import job_publish; import json; print(json.dumps(job_publish(), ensure_ascii=False, indent=2))"
   ```
6. Telegram ön koşulları: bot token env'de (`TELEGRAM_BOT_TOKEN`), kanal handle'ı doğru (ör. `@Finpilot_Breif` yazımını teyit et), bot runner çalışıyor. Token'ı ASLA commit'leme.

**Ek — runtime verisini git'ten çıkar (P0-4 ile birlikte):**
`.gitignore`'a ekle: `data/*.json`, `*.db`, `.env`, `web/public/demo_snapshot.json` (eğer runtime üretiliyorsa). Böylece bozuk/anlık veriler repoyu kirletmez.

**Doğrulama:** `job_draft()` temiz (lint 0 ihlal) → onay → `job_publish()` başarılı; Telegram kanalında ve `/demo`'da aynı içerik görünür.

**Geri alma:** `FINPILOT_ENABLE_DISTRIBUTION=0` zaten güvenli varsayılan; yanlış yayında Telegram mesajını elle sil, `demo_snapshot.json`'u önceki commit'e döndür.

---

## Kanal 2 — FinSense akademi yayını (altyapı hazır)
Ayrı ve akıyor. Kalan: ilk üretim turunu doğrula (`python run.py status`), sonra `python -m academy.export_lessons --json --status published --out ..\Borsa\web\public\academy_lessons.json` ile `/academy` demosunu tazele. Detay: akademi bölümünde konuşuldu.

## Önerilen sıra (özet)
1. **P0-1** SMTP rotasyonu (yayından önce, güvenlik).
2. **P0-2** Scanner sözleşmesini geri al + test ekle.
3. **P0-3** demo_snapshot yeniden üret → web demo düzelir.
4. **P0-4** Manuel yayın akışı (`job_draft` → onay → `job_publish`) + `.gitignore`.

_Not: Bu plan doğrulanmış fonksiyon/dosya adlarına dayanır; kesin commit hash'i, SMTP sağlayıcı adımları ve onay mekanizmasının tam şekli senin makinende teyit edilmelidir._
