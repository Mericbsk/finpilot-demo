# Insan Onayli AI Yayini - Manuel Degisiklik Listesi

Status: PROPOSAL ONLY - etkin talimat veya ikinci bir kural otoritesi degildir.
Prepared: 2026-10-12
Layer: Governance / AI execution authority (Layer 5), Risk & Compliance onceligi korunur.
Level: C - yetki degisikligini insan uygular; bu listeyi hazirlama Level A'dir.
Owner: Meric for adoption/application; GitHub Copilot for proposal preparation.

## Kaynak ve Kapsam

- Tek yetki otoritesi [05-escalation.md](../../_instructions/05-escalation.md) olarak kalir.
- Benimsenecek istisna metni [v1.1 onerisi](ai-publication-v1.1.proposal.patch) icindeki
  `Insan onayli dagitim yayini istisnasi` bolumudur. Burada tekrar kopyalanmaz.
- Oneri yamasi mevcut haliyle Git uygulanabilirlik kontrolunu gecmedi; `git apply`
  ile uygulanmamalidir. Bu liste insanin dosya bazinda uygulamasi icindir.
- Kapsam varsayimi: web/Telegram dagitim icerigi ve onayli uretilmis web ciktisina
  bagli mevcut otomatik CI/Vercel deploy'u dahildir. Genel kod/altyapi deploy'u
  dahil degildir. Insan bu siniri incelemeden istisna etkinlestirilmez.
- [_instructions/00-core.md](../../_instructions/00-core.md) ve
  [YONERGE.md](../../YONERGE.md) degistirilmez; Risk & Compliance kapilari korunur.

## Uc Dosyada Yapilacak Degisiklik

1. [05-escalation.md](../../_instructions/05-escalation.md): v1.0'dan v1.1'e
   versiyonla; onceki surumu ve changelog'u belirt. Level C paragrafini ve onerideki
   dar istisna bolumunu insan tarafindan benimsenen metinle guncelle. `ACTIVE` ve
   `Last Updated` bilgileri gercek uygulama/aktivasyon tarihini gostermeli;
   9 Ekim taslak tarihi bugunku aktivasyon kaniti degildir. Istisna, insan
   aktivasyon kaydi yokken kullanilamaz. Diger Level C islemleri insan uygulamasinda kalir.
2. [copilot-instructions.md](../../.github/copilot-instructions.md): versiyon ve
   changelog ekle. Level C maddesindeki mutlak AI yayin yasagini, yalniz etkin ve
   insan tarafindan aktive edilmis `05-escalation.md` istisnasina referans verecek
   bicimde degistir. Istisna metnini burada cogaltma; diger Level C yasaklari kalir.
3. [INDEX.md](../INDEX.md): yalniz manifestteki `id: escalation` kaydini guncelle.
   `authority_path` ayni kalir. Otorite gercekten aktive edilince `status: active`
   ve insan aktivasyon kanitina isaret eden not eklenir. Diger `draft` kayitlarini
   veya otorite hiyerarsisini degistirme.

## Insan Aktivasyon Kaydi

[decision-log.md](decision-log.md) icinde ayri bir aktivasyon kaydi zorunludur.
Kayit: tarih, baslik, layer, Level C, benimsenen kapsam, once/sonra, uygulayan insan,
uc dosyanin benimsenen surum/hash'leri, etki ve gercek uygulama kanitini icermelidir.
Insan uygulamasi tamamlanmadikca durum `pending` kalir. AI bu listeyi veya eski
yayin onayini aktivasyon kaniti sayamaz; insan adina uygulanmis kaydi uyduramaz.

## Aktivasyon Sonrasi Kontrol

- Uc dosya ve insan aktivasyon kaydi ayni istisna/surum uzerinde uzlasmali.
- Gercek aktivasyondan sonra talimatlar yeni bir ajan oturumunda yeniden okunmali.
- Her yayin icin paket/hash, tarih, hedef dal/proje/kanal ve yuzey onayi ayri
  dogrulanmali. 9 Ekim paketinin onayi 12 Ekim'de yeni yayin izni degildir.
- Git hedefi ve mevcut smoke/teslim kontrolleri
  [YONERGE.md](../../YONERGE.md) uzerinden dogrulanmali.
- Bu liste yayin, commit, push, deploy, secret erisimi veya sifre sifirlama yapmaz.
