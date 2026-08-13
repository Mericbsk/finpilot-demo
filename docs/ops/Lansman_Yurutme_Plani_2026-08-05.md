# Lansman Yürütme Planı — Bu Haftanın Tek Cephesi
Durum: AKTİF · 2026-08-05 · Cephe: **LANSMAN** · Eskalasyon: adım-bazlı (aşağıda)
Kapsam: 4 madde — (1) yayın boru hattını sağlamlaştır, (2) ilk dolu karneli yayın, (3) gerçek-kullanıcı
daveti öncesi 3-cihaz mobil test, (4) her işlem günü brifi 10 güne taşı. Başka cepheye dokunulmaz.

---

## 0. Çerçeve (planı belirleyen dürüst gerçek)

- **Değer vaadi = dürüst karneli, öğreten sabah bülteni** — "sinyallerimiz kazandırır" DEĞİL. Edge
  ölçülen pencerede kanıtlanmadı; o yüzden seri **yalnız bu çerçevede** meşru: karne kaçıranları da gösterir.
- **Karne başlığı = beklenti + asimetri, kazanç oranı DEĞİL.** İki resolver var: watchlist_signals'ın
  naif/kırılgan resolver'ı **%7 kazanç (51/668)** gösteriyor — bu bir **ARTEFAKT** (yol haritası P0.2
  bunu değiştirecek), performans değil. Sağlam **bariyer** yöntemi (signals_archive, 5216 işlem):
  **~%30 isabet · kazanan ort +%4.28 / kaybeden ort −%1.27 = 3.36x asimetri · beklenti +%0.40/işlem** —
  düşük-kazanç-oranlı, pozitif-skew momentum profili (normal ve matematiksel sağlam). Kırmızı çizgi:
  ne "felaket" diye abart, ne "kazandırır" diye; **benchmark-üstü edge kanıtlanmadı** — şeffaf söyle.
  (%7'yi yayınlamak dürüstlük değil, yanıltma olur.)
- **Bağımlılık:** (1) diğer üçünün ön koşulu. (2) kredibilite kilidi. (3) gerçek-kullanıcı davetinin kapısı.
  (4) 1+2'nin güvenilir tekrarının sonucu.

---

## MADDE 1 — Yayın boru hattını sağlamlaştır (ön koşul)

**Tanım (DoD):** Her işlem günü, tek komutla, kopmadan: `scan → export → job_draft → prepublish_gate →
onay → job_publish → Telegram + web push + archive + backup`. Çift-bot yok, sessiz düşme yok.

**Ön koşullar:** `.env`'de `TELEGRAM_BOT_TOKEN/CHAT_ID` dolu; `FINPILOT_WEB_PUBLISH_CMD=python scripts/publish_web.py`,
`FINPILOT_REQUIRE_VERCEL_DEPLOY=0` (tek tanım); git push kimliği kurulu.

**Adımlar:**
1. **Çift-bot kontrolü (kritik — 409 Conflict serisi kırar).** Tek `run_bot.py`/`telegram_bot_runner.py`
   süreci olmalı:
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ? { $_.CommandLine -match 'run_bot|telegram_bot_runner' } | Select ProcessId,CommandLine | fl
   ```
   Fazlaysa kapat; startup'ta tek kayıt bırak.
2. **Kuru prova (dry-run) — canlıya göndermeden zinciri gör:**
   ```powershell
   python scripts\publish_now.py
   ```
   → "PRE-PUBLISH GATE" hatası YOK, taslak gösterildi mi? (Ctrl+C ile iptal.)
3. **Web push testi:** `python scripts\publish_web.py` → "pushed → Vercel" ya da "değişiklik yok".
4. **Yedek + arşiv:** yayın sonrası `backups\<bugün>` oluştu mu; `signals_archive` sayısı arttı mı.

**Doğrulama (kabul testi — 8/8):** `Senin_Yapacaklarin_Yonerge` ADIM 7'deki uçtan-uca turu bir kez
tam geç (scan→publish→onay→Telegram→git log→canlı web→arşiv+yedek→streak). 8/8 ✓ = hat canlı.

**Riskler:** çift-bot (mesaj düşer) · web push kimlik hatası · gate'in taslağı boş/karne'siz döndürmesi.
**Seviye:** B (env/publish) · **Kim:** Meriç (panel/komut) + ben (kod/doğrulama).

---

## MADDE 2 — İlk dolu karneli yayın (kredibilite kilidi)

**Tanım (DoD):** Yayınlanan brifin karne bölümü **gerçek, dolu ve dürüst**: başlıkta bariyer-tabanlı
**beklenti + asimetri (win/loss büyüklük) + bağlamlı isabet**, olgunluk notu, metodoloji linki. Ham
"win/loss sayısı" başlık DEĞİL. Boş/placeholder karne YOK.

**Ön koşullar (kanıt):** Karne'nin `overall` bloğu zaten **sağlam bariyer verisini** okuyor
(`karne.py::_overall_from_archive`: +%0.40 beklenti, 3.36x asimetri — kod yorumu bile "the real,
positive track record" diyor). AMA `by_grade` bloğu **watchlist_signals'ın kırılgan resolver'ını**
okuyor (%7 artefakt + A/B/C çok az örnek: A=1, B=17, C=41). İlk dolu karne için: ya **(a) overall'ı
başlığa al, by_grade'i "olgunlaşıyor / az örnek" diye işaretle** (ilk yayın için yeterli), ya da
**(b) by_grade'i sağlam bariyer resolüsyonuna taşı** (yol haritası P0.2 — Level B).

**Adımlar:**
1. **Karne'yi hesapla ve GÖZDEN GEÇİR (yayınlamadan):** `distribution/karne.py::compute_karne_db`
   çıktısını al; kontrol et:
   - by_grade (A/B/C) + overall (tam-arşiv beklentisi) + tracked_total dolu mu?
   - Olgunluk kapısı çalışıyor mu (taze sinyaller "olgunlaşıyor" olarak, hüküm dışı)?
2. **Dürüst çerçeve metnini yaz (compliance-safe):**
   - "Bu, seçtiğimiz sinyallerin **şeffaf karnesidir — kaçıranlar dâhil.**"
   - Başlık: **beklenti +%0.40/işlem · ~%30 isabet · 3.36x asimetri** (kazanan büyük, kaybeden küçük);
     "düşük isabet ama pozitif skew — bu bilinçli bir profil" diye **açıkla**.
   - **Edge/kazanç iddiası YOK · benchmark-üstü performans iddiası YOK**; "eğitim amaçlı, tavsiye değil" mührü.
3. **prepublish_gate'ten geçir:** karne alanları dolu değilse gate yayını durdurmalı (degraded-run koruması).
4. **Yayınla ve doğrula:** Telegram + web snapshot'ta karne göründü mü; sayılar hesapla eşleşiyor mu.

**Doğrulama:** Yayınlanan karne = `compute_karne_db` çıktısı (birebir); "kaçıranlar" görünür; hiçbir
yerde edge ima yok (lint/gözle).
**Riskler:** ⚠️ **Kırılgan resolver'ın %7'sini yayınlamak = yanıltma** (dürüstlük değil). Bariyer-tabanlı
beklenti+asimetriyi başlığa al. · Kazanç oranını TEK metrik yapma (asimetrik ödeme). · Benchmark-üstü
edge iddiası YOK. · by_grade az örnekli → kesin hüküm verme, işaretle.
**Seviye:** B (public karne içeriği) · **Kim:** ben (hesap+metin taslağı) + Meriç (onay+yayın).

---

## MADDE 3 — 3-cihaz mobil test (gerçek-kullanıcı davetinin kapısı)

**Tanım (DoD):** Landing + /demo, **3 farklı gerçek cihazda** (iOS Safari, Android Chrome, +1 küçük ekran)
kırılmadan açılıyor; karne + CTA + disclaimer okunur; waitlist formu çalışıyor.

**Adımlar:**
1. Canlı landing'i 3 cihazda **Ctrl+F5/temiz** aç: düzen, font (serif), Grade mührü, karne bölümü, CTA.
2. **İlk-5-dakika akışı:** ziyaretçi ne görüyor → ne anlıyor → nereye tıklıyor? (checklist'teki onboarding.)
3. Waitlist formu: e-posta gir → 201 + admin bildirimi (Telegram) düştü mü?
4. Kırıkları not al → düzelt → tekrar test (yeşile kadar).

**Doğrulama:** 3/3 cihaz temiz; waitlist uçtan uca çalışıyor; disclaimer her ekranda.
**Riskler:** mobilde newsroom-mockup/donuk bölüm görünmesi (kredibilite) · form/SMTP kopukluğu.
**Seviye:** A/B · **Kim:** Meriç (cihazlar) + ben (kod düzeltme).

---

## MADDE 4 — Brif serisini 10 işlem gününe taşı (koşan sonuç)

**Tanım (DoD):** `publish_streak()` **10** döndürene kadar, **her işlem günü** dürüst-karneli brif;
seri kırılmadı.

**Adımlar (günlük ritüel — 10 dk):**
1. Scan çalıştı mı → `scan_export_latest.json` tarihi bugün mü?
2. `python scripts\publish_now.py` → taslak (karne dolu) → onay.
3. Telegram + web güncel mi (Ctrl+F5); streak arttı mı:
   ```powershell
   python -c "from distribution.broadcast import publish_streak;print('streak',publish_streak())"
   ```
4. Kopma olursa: o günü not, kök nedeni çöz (genelde §1 hattı), ertesi gün devam.

**Doğrulama:** Her gün streak +1; 10'da DoD. Piyasa kapalı günler seriyi kırmaz (işlem günü sayacı).
**Riskler:** hafta sonu/tatil karışıklığı (sayaç işlem-günü olmalı) · tek gün kaçırma → seri sıfırlama algısı.
**Seviye:** A (rutin) · **Kim:** Meriç (günlük onay) — hedef: sonra tek-dokunuş/otomasyon.

---

## Sıra ve "gerçek kullanıcı daveti" kapısı

```
GÜN 1     MADDE 1  hattı sağlamlaştır + 8/8 uçtan-uca tur           (ön koşul)
GÜN 1-2   MADDE 2  ilk dolu karne: hesapla → dürüst çerçeve → yayınla (kredibilite)
GÜN 2-3   MADDE 3  3-cihaz mobil test + waitlist doğrula            (davet kapısı)
GÜN 1-10  MADDE 4  her işlem günü brif → streak 10                  (koşan sonuç)
```

**⛔ GERÇEK KULLANICI DAVETİ KAPISI (hepsi ✓ olmadan davet yok):**
- [ ] §1 hat 8/8 canlı (seri kırılmaz)
- [ ] §2 ilk dolu, dürüst karne yayınlandı (edge iddiası yok)
- [ ] §3 3-cihaz mobil temiz + waitlist çalışıyor
- [ ] **Yasal sayfalar (Impressum/Datenschutz)** — Avusturya'da public site için **zorunlu** (Level C, avukat).
      Telegram serisi için bloke değil; **web daveti için pazarlık dışı.**
- [ ] SMTP şifresi rotate (sızmış) — waitlist e-posta bildirimi için de gerekli.

---

## Kapsam kilidi (feature-freeze)
Bu hafta yalnız yukarıdaki 4 madde + davet kapısı. Yeni fikir gelirse → "bu, bu 4 maddenin hangisini
ilerletiyor?" yazılamıyorsa `PARKING_LOT.md`. Edge ölçümü (P0.1) arka planda **pasif** birikir; evren
büyütme / donanım / ağır web — edge kanıtına kadar park.

_İlgili: `docs/2026-07-31-genel-yol-haritasi`, `docs/ops/FinPilot_Senin_Yapacaklarin_Yonerge`, `distribution/karne.py`, `scripts/publish_now.py`, `LAUNCH_CHECKLIST.md`._
