# Frontend Web Özeti

## Teknik Tanım

Next.js 16 App Router tabanlı ana kullanıcı yüzeyidir. Dashboard, scanner, AI Lab, history, portfolio ve settings akışlarını içerir. `/py-api/*` ile FastAPI backend’e, `/api/quotes` ile doğrudan Yahoo Finance’a bağlanır.

## Durum

**Kısmen çalışıyor.** `http://localhost:3001` canlı döndü ve `npm run build` başarılı oldu. Varsayılan `npm test` worker timeout verdi; `npx vitest run --pool=threads` ile 12 test geçti.

## Öne Çıkan Fonksiyonlar

- `web/src/app/dashboard/page.tsx`
- `web/src/app/api/quotes/route.ts`
- `web/src/app/error.tsx`
- `web/next.config.ts`

## Ana Bulgular

- Güçlü güvenlik header seti mevcut.
- Rewrite mimarisi net, ancak backend auth eksikliği frontend’i dolaylı olarak etkiliyor.
- Test kapsamı dar ve default test komutu stabil değil.
- `web/README.md` hâlâ template metni.

## Güvenlik / Uyumluluk

- Header hardening iyi seviyede.
- Error boundary mevcut.
- Backend route koruması eksik olduğu için kullanıcı verisi akışlarında zincir tamamlanmıyor.

## Performans / Ölçek

- `/api/quotes` batch + 30sn cache olumlu.
- Loglarda quote route latency varyansı yüksek.
- RUM, Web Vitals ve frontend telemetry görünmüyor.

## Puan

| Kriter | Puan |
|--------|------|
| Stabilite | 7 |
| Güvenlik | 7 |
| Performans | 7 |
| Test | 5 |
| Bakım | 5 |
| Teknik Borç | 6 |
| **Toplam** | **6.4 / 10 — B** |

## İlk 3 Aksiyon

1. `npm test` komutunu stabil hale getir.
2. Dashboard ve scanner için contract smoke testleri ekle.
3. `web/README.md` dosyasını güncel ürün akışına göre yaz.

## Tekrarlama Notu

- **Ne nedir:** Kullanıcının gördüğü modern ürün yüzeyidir.
- **Nasıl çalışır:** quote çağrıları frontend route’una, uygulama çağrıları backend rewrite katmanına gider.
- **Nasıl test edilir:** build, vitest, dashboard smoke ve quote contract birlikte çalıştırılır.
- **Bir sonraki değerlendirme için not:** frontend telemetry ve E2E kapsamı eklenmelidir.
