# Infra / CI / Delivery Özeti

## Teknik Tanım

Build, start, Docker, compose ve CI işlerini yöneten teslimat katmanıdır.

## Durum

**Kısmen çalışıyor.** `start.sh` ile güncel stack ayağa kalkıyor. Buna rağmen CI, README, Docker ve compose hâlâ legacy Streamlit varsayımlarını taşıyor.

## Öne Çıkan Dosyalar

- `start.sh`
- `stop.sh`
- `.github/workflows/ci.yml`
- `docker-compose.yml`
- `Dockerfile`
- `api/Dockerfile`

## Ana Bulgular

- Temiz kurulum kırık.
- Tek source-of-truth runtime yok.
- CI ve Docker smoke testleri legacy mimariye dayanıyor.
- Lock file ve canary/rollback standardı görünmüyor.

## Güvenlik / Uyumluluk

- Secret scan job’ı olumlu.
- Default compose parolaları prod uyumlu değil.

## Performans / Ölçek

- Ayrı servisler düşünülmüş.
- Quota/cost/alerting/canary mekanizmaları yok.

## Puan

| Kriter | Puan |
|--------|------|
| Stabilite | 4 |
| Güvenlik | 5 |
| Performans | 5 |
| Test | 4 |
| Bakım | 4 |
| Teknik Borç | 4 |
| **Toplam** | **4.4 / 10 — C** |

## İlk 3 Aksiyon

1. Tek resmi runtime tanımını tüm delivery dosyalarına taşı.
2. Clean install + docker build + smoke test zincirini kur.
3. Canary ve rollback prosedürü ekle.

## Tekrarlama Notu

- **Ne nedir:** Build ve deploy zinciridir.
- **Nasıl çalışır:** start script, container’lar ve CI job’ları yayına çıkışı belirler.
- **Nasıl test edilir:** temiz kurulum, docker build, health probe ve smoke suite birlikte denenir.
- **Bir sonraki değerlendirme için not:** runtime sözleşmesi tekilleşmeden prod kararı verilmemelidir.
