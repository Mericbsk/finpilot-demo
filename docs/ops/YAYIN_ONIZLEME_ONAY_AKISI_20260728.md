# FinPilot — Yayın Önizleme ve Sohbet Onayı Akışı

**Tarih:** 2026-07-28
**Katman:** 02-engineering / 06-releases
**Durum:** preview tooling uygulandı; canlı yayın onayı ayrı bir insan kararıdır

## Amaç

Tam tarama bittikten sonra Telegram ve web içeriği önce burada incelenir. Açık insan onayı gelmeden Telegram API'sine, yayın kuyruğuna, `web/public` dosyasına veya Vercel deploy hook'una dokunulmaz.

## Aşama 1 — Yan etkisiz önizleme

```powershell
py -3 scripts/preview_publish.py
```

İnceleme için dosyaya da yazılabilir:

```powershell
py -3 scripts/preview_publish.py --output data/distribution/preview_YYYY-MM-DD.md
```

Web'de yayınlanacak İngilizce public görünümün tarayıcı önizlemesini de üretmek için:

```powershell
py -3 scripts/preview_publish.py --web-output data/distribution/web_preview_YYYY-MM-DD.html
```

Üretilen HTML yalnızca yerel inceleme dosyasıdır; `web/public/demo_snapshot.json` dosyasını ve deploy zincirini değiştirmez.

Preview şu kontrolleri yapar:

- güncel scan export var mı;
- full-scan contract ve pre-publish gate geçiyor mu;
- Türkçe ve İngilizce snapshot kimlikleri aynı mı;
- snapshot şeması geçerli mi;
- Telegram free brief metni;
- web public görünümü ve aday listesi;
- web public görünümünün tarayıcıdaki kart düzeni;
- warning alanları.

Preview şu işlemleri yapmaz:

- `broadcast_queue` içine kayıt eklemez;
- admin Telegram bildirimi göndermez;
- Telegram kanalına mesaj göndermez;
- `snapshot_latest.json` veya `web/public/demo_snapshot.json` güncellemez;
- `FINPILOT_WEB_PUBLISH_CMD` veya Vercel deploy hook çalıştırmaz.

## Aşama 2 — Sohbet içi onay

Asistan preview içeriğini burada özetler ve özellikle şu maddeleri gösterir:

- tarih, scan ID ve snapshot ID;
- aday sayısı, ticker, grade ve olasılık bandı;
- Telegram metninin tamamı veya ilgili bölümü;
- web public aday görünümü;
- gate/warning durumu;
- karne veri kaynağı ve fallback durumu.

Yayın yalnızca insanın açık `YAYINLA` onayından sonra başlatılabilir. `BEKLET` veya `RED` yanıtında hiçbir dış yayın yapılmaz.

## Aşama 3 — Yayın

Onaydan sonra manuel yayın komutu çalıştırılır:

```powershell
py -3 scripts/publish_now.py --yes
```

Bu aşama gerçek Telegram gönderimi ve web deploy işlemidir. Sonuçta `sent`, `failed`, `blocked` ve `web_pushed` alanları kontrol edilir. `web_pushed=true` değilse işlem başarılı kabul edilmez.

## Operasyon notları

- `FINPILOT_ENABLE_DISTRIBUTION=0` scheduler otomatik yayınını kapalı tutar; manuel `publish_now.py` kendi process'i içinde dağıtımı geçici açar.
- Preview çalıştırmak için dağıtım bayrağının açık olması gerekmez.
- Preview gate geçmiyorsa `--force` ile yayın yapılmaz; önce export sorunu çözülür.
- Telegram bot tokenı, kanal kimliği ve deploy hook URL'si preview çıktısına yazılmaz.
- Bu akış canlı yayın kontrolü olduğundan strateji veya risk kurallarını değiştirmez.
