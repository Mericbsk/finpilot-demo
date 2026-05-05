# Legacy Streamlit Karar Planı

**Tarih:** 16 Nisan 2026
**Karar seviyesi:** Mimari / Teslimat / Bakım
**Varsayılan sahip:** Platform + Product

## Karar

Legacy Streamlit yüzeyi (`streamlit_app.py`, `views/`, root `Dockerfile`, compose içindeki `finpilot` servisi) artık **birincil ürün yüzeyi değildir**. Kısa vadeli karar, bu yüzeyi tamamen silmek değil; **maintenance-only secondary surface** olarak sınırlamaktır.

## Neden Bu Karar Alındı

1. Modern kullanıcı yüzeyi artık Next.js + FastAPI üzerinden çalışıyor.
2. Legacy Streamlit varlığı README, Docker, CI ve health sözleşmelerinde drift yaratıyor.
3. Scanner/export gibi bazı eski işlevler hâlâ legacy kod yoluna dokunuyor; bu yüzden tek adımda silmek riskli.

## Hedef Durum

- Primary runtime: `bash start.sh` ile `web:3001` + `api:8000`
- Legacy Streamlit: yalnızca internal/demo/back-compat amaçlı, varsayılan deploy zincirinin dışında
- CI: modern stack’i gate eder, legacy smoke ise ayrı ve non-blocking olur ya da tamamen kaldırılır

## Karar Matrisi

| Alan | Mevcut Durum | Karar | Hedef Tarih |
|------|--------------|-------|-------------|
| `streamlit_app.py` | Legacy entrypoint | Maintenance-only | Hemen |
| `views/` | Büyük legacy UI ve export yüzeyi | Kademeli migration | 2-6 hafta |
| Root `Dockerfile` | Streamlit production image | Primary pipeline’dan çıkar | 1-2 hafta |
| `docker-compose.yml` `finpilot` servisi | Legacy surface’i ayağa kaldırıyor | Optional profile / secondary service | 1-2 hafta |
| `scanner` ve `telegram_bot` servis bağı | `finpilot` servisine bağlı | API/worker tabanlı bağımsızlaştır | 2-4 hafta |
| View smoke testleri | Legacy import zincirine bağlı | Migration tamamlanana kadar koru | Geçiş süresince |

## 3 Aşamalı Plan

### Aşama 1: Resmi Statü

- README ve audit dokümanlarında Streamlit yüzeyi “secondary / legacy” olarak işaretlenir.
- CI blocking pipeline modern stack üzerinden tanımlanır.
- Root Dockerfile için deprecation notu düşülür.

### Aşama 2: Bağımlılık Çözme

- `scanner` ve `telegram_bot` servisleri `finpilot` yerine `api` veya bağımsız worker akışına bağlanır.
- Export ve profile/settings gibi hala `views/` altında değeri olan parçalar liste halinde çıkarılır.
- Hangi legacy ekranın modern web karşılığı olduğu migration matrix ile eşleştirilir.

### Aşama 3: Emeklilik veya İzolasyon

- Karar A: Streamlit tamamen devreden çıkar.
- Karar B: Internal admin/debug tool olarak ayrı profile altında tutulur.
- Her iki durumda da primary deploy, smoke ve health zincirinden çıkarılır.

## Exit Kriterleri

1. Root Dockerfile primary build zincirinde kullanılmıyor.
2. Compose içindeki legacy servis default olarak başlamıyor.
3. Scanner ve telegram bağımlılıkları legacy UI’dan kopmuş.
4. README, CI ve deploy rehberi modern stack ile tutarlı.
5. Legacy’ye özel kalan testler ya ayrı profile taşınmış ya da kaldırılmış.

## Riskler

- Export/Excel fonksiyonları modern web’de tam karşılık bulmamış olabilir.
- Bazı debug veya ops akışları sessizce Streamlit yüzeyine bağımlı olabilir.
- Erken kaldırma, bakım kolaylığı kazancı sağlarken operasyonel sürpriz üretebilir.

## Önerilen Uygulama Sırası

1. Status ve doküman kararı sabitle.
2. Compose ve CI’dan blocking legacy bağımlılıklarını çıkar.
3. Migration matrix üret.
4. Son olarak emeklilik ya da izolasyon kararını uygula.

## Tekrarlama Notu

- **Ne nedir:** Bu dosya legacy Streamlit yüzeyinin nasıl yönetileceğini tanımlar.
- **Nasıl çalışır:** yüzey birincil ürün olmaktan çıkarılır, sonra bağımlılıklar kademeli çözülür.
- **Nasıl test edilir:** compose profilleri, legacy smoke ve modern runtime contract ayrı ayrı doğrulanır.
- **Bir sonraki değerlendirme için not:** scanner ve telegram bağımlılıkları çözülmeden legacy yüzey tamamen kapatılmamalıdır.
