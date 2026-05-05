# Backend API Özeti

## Teknik Tanım

FastAPI tabanlı servis katmanıdır. Scanner, history, trade, user, models, inference ve LLM route’larını taşır. Frontend `/py-api/*` rewrite ile bu servise bağlanır.

## Durum

**Kısmen çalışıyor.** `http://localhost:8000/api/v1/health` başarılı döndü. `start.sh` ile canlı kalktı. Buna rağmen `/ready` ve `/metrics` canlı uygulamaya bağlanmamış durumda.

## Öne Çıkan Fonksiyonlar

- `api/main.py`
- `api/routers/scan.py`
- `api/routers/llm.py`
- `api/routers/user.py`
- `api/middleware/auth.py`

## Ana Bulgular

- `requirements.txt` API runtime paketlerini eksik taşıyor.
- OpenAPI ile gerçek runtime sözleşmesi uyuşmuyor.
- Auth middleware var ama route bazında uygulanmıyor.
- User settings rotaları public davranıyor.

## Güvenlik / Uyumluluk

- JWT altyapısı var ama enforcement eksik.
- CORS tanımlı.
- Prod audit trail ve readiness eksik.

## Performans / Ölçek

- Scan route’unda thread pool ve timeout var.
- Request telemetry ve queue/backpressure yok.

## Puan

| Kriter | Puan |
|--------|------|
| Stabilite | 6 |
| Güvenlik | 4 |
| Performans | 6 |
| Test | 6 |
| Bakım | 4 |
| Teknik Borç | 4 |
| **Toplam** | **5.2 / 10 — C** |

## İlk 3 Aksiyon

1. API bağımlılıklarını dependency manifest’e ekle.
2. Auth dependency enforcement’i route bazında etkinleştir.
3. `/ready` ve `/metrics` endpoint’lerini canlı uygulamaya bağla.

## Tekrarlama Notu

- **Ne nedir:** Python iş mantığı ve servis yüzeyidir.
- **Nasıl çalışır:** frontend istekleri rewrite ile router’lara gelir, router’lar scanner/auth/ML/LLM modüllerini çağırır.
- **Nasıl test edilir:** health, auth, settings, scan ve models contract testleri çalıştırılır.
- **Bir sonraki değerlendirme için not:** OpenAPI sadece canlı route’lardan yeniden üretilmelidir.
