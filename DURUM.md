# 🧭 DURUM — neredeyim, sırada ne var (tek harita)

_Kural: bu dosya kafamın dışındaki tek "neredeyim" haritasıdır. Her sabah nabız buraya bakar; her Pazartesi elle güncellenir. Tam bileşen envanteri: `docs/2026-08-02-ENVANTER-tum-bilesenler.md`._

---

## ⭐ Bu 6 haftanın TEK önceliği: LANSMAN
Kaynak: `LAUNCH_CHECKLIST.md` · Kritik metrik: **10 ardışık işlem günü kesintisiz brif** → şu an **7/10**
(11 Ağu doğrulama: `distribution.db` broadcast_queue'dan `publish_streak()` ile hesaplandı; 3-7 ve
10-11 Ağu ardışık `sent` — 8-9 Ağu haftasonu, seri kırılmadı; seri en son 31 Tem'de kırılmıştı).
Başka her şey bunun önüne geçemez. "Bunu yapmak lansmanı bugün ilerletiyor mu?" — hayırsa park.

### Bu haftanın tek işi (her Pazartesi doldur)
> **LANSMAN — brif serisini kırmadan büyüt ve iki açık şartı kapat.**
>
> Ürün vaadi edge kanıtı değil; dürüst karneli, öğreten sabah bültenidir. Edge
> kanıtlanmış gibi ima edilmez. Bu haftanın sırası:
> 1. Yayın boru hattını sağlamlaştır: tek-poller / `publish_now` akışını temiz,
>    güvenli ve her işlem gününde tekrarlanabilir tut.
> 2. Karne zincirini ilk kez gerçekten dolu yayınla; kaçırılanları da göster,
>    abartısız geçmiş olarak sun.
> 3. Gerçek kullanıcı davetinden önce landing'i üç mobil cihazda doğrula;
>    Impressum ve Datenschutz sayfalarını Level C hukuk kapısı olarak koru.
> 4. Her işlem günü brif yayınını sürdür ve seriyi ~2/10'dan 10 ardışık güne
>    taşı.

> Edge ölçümü arka planda pasif olarak birikmeye devam eder. Evren büyütme,
> donanım ve ağır web yatırımı edge kanıtına kadar parktadır.

---

## ✅ Aktif (yalnız lansman-kritik — LAUNCH_CHECKLIST'ten)
- Her işlem günü brif yayını → seriyi büyüt (hedef 10)
- Demo her gün taze snapshot (köprü onarıldı; "her gün" kanıtı seriyle)
- Karne dolu yayın (ilk dolu yayın bekleniyor)
- Mobil 3-cihaz landing testi
- İçerik "insan yazmış" kalitesi (variety raporu + 3 dış okuyucu)
- ≥25 kanal takipçisi + ≥10 beta kullanıcı · ≥15 feedback

## 🅿️ Park (6 hafta DOKUNMA — PARKING_LOT + bu oturum)
- **FinSense onarımları / içerik fabrikası** (Finsense repo) — bu oturumda çalıştı ama PARK
- **Buzz / Control Center + `/ops` + tasarım promptları** — bu oturumun ürünü, ama PARK (lansman-sonrası v2)
- `.finpilot/` ortak-beyin protokolü — kuruldu; kullanımı hafif tut, geliştirmesi park
- Ledger×Classroom kod uygulaması · ShortlistEnricher · DRL/alt-data araştırma
- Hibe dokümanları · Tauri masaüstü · kullanıcıya-özel alert
- Kökteki ~90 deney scripti — lansman sonrası arşivle

## 🚧 Bilinen takıntı/temizlik (lansman sonrası)
- Kök dağınıklığı: ~90 script + ~110 doküman → arşiv/park
- `execution/` + `broker/` (Level C, para-bitişik) — dokunma, insanda

---
_Not: yol planının tamamı (tüm sistemi düzenleme) lansmandan SONRA. Şimdi tek yol lansman._
