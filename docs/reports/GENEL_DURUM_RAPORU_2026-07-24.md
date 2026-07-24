# FinPilot Genel Durum ve Çıktı Raporu

**Tarih:** 2026-07-24
**Kapsam:** Bugüne kadar uygulanan Bölüm 0, 1, 3 ve 4 çalışmaları; mevcut çalışma ağacı; backend/web doğrulamaları.
**Sonuç:** Değiştirilen yayın ve web yüzeyinde yeni bir kırılma yok. Repository genelinde önceden bilinen 12 test kırmızısı devam ediyor. Commit öncesi Ruff ve web build sorunları bu denetimde düzeltildi.

## 1. Yönetici Özeti

FinPilot'un manuel yayın mimarisi güçlendirildi. API kapalıyken de karne üretilebiliyor; başarılı Telegram/web yayınından sonra adaylar arşivleniyor; yayın öncesi bozuk veya zenginleştirilmemiş taramalar durduruluyor; bozuk eşit-boyutlu export'lar iyi export'un üzerine yazamıyor; yayınlanan export'un dokunulmaz kanıt kopyası tutuluyor; günlük yedek yayın zincirine bağlanıyor.

Web tarafında ürünün günlük ledger görünümü ve aday gerekçeleri aktif dile bağlandı. Masthead'de bağlamsız win-rate yerine kamuya açık şekilde takip edilen pick sayısı kullanılıyor. Güncel public snapshot iki adayı ve additive metrics alanlarını taşıyor.

## 2. Doğrulama Sonucu

### Değiştirilen kritik yüzey

- Pre-publish, karne, arşiv, snapshot sözleşmesi, distribution ve approval testleri: **52 passed**.
- Değiştirilen Python modülleri: `py_compile` temiz.
- Ruff: **temiz**.
- Next.js production build: **başarılı**; TypeScript kontrolü ve 31 route üretimi tamamlandı.
- Yerel snapshot:
  - `snapshot_id`: `4467524635e31a6041d4f524`
  - `date`: `2026-07-24`
  - `universe`: `1812`
  - `scan_result_count`: `1801`
  - `eligible_candidate_count`: `2`
  - adaylar: `RIOT (B)`, `DVN (C)`
  - her iki adayda public `metrics` mevcut.

### Repository genel testi

Tam test sonucu: **730 passed, 12 failed, 6 skipped**.

12 hata, mevcut Bölüm 0 raporundaki başlangıç tabanıyla aynı sınıflardadır:

- `test_api_runtime`: kayıt akışında mevcut veri nedeniyle `409` beklentisi.
- `test_catalyst`: catalyst varsayılan/puan davranışı.
- `test_evaluate`: defensive risk ve yetersiz veri beklentileri.
- `test_new_endpoints`: fiyat senkronizasyonu testleri.
- `test_prometheus`: port kullanım edge case'i.
- `test_squeeze_factor`: squeeze varsayılanı ve feature çağrısı.
- `scanner_rollout/test_runtime_baseline`: alignment ve minimum sinyal skoru beklentileri.

Bu sonuç “tamamen kırılmasız” anlamına gelmez. Ancak yeni yayın zinciri, karne, snapshot ve prepublish değişiklikleri için odak testlerinde yeni regresyon bulunmamıştır. Tam süit kırmızıları şu an bu çalışmanın kapsamına ait yeni bir hata olarak sınıflandırılmamıştır; yeniden taban karşılaştırması gerekir.

## 3. Bölüm Bazlı Yapılanlar ve Beklenen Çıktılar

### Bölüm 0 — Zemin, yedek ve geri dönüş

**Yapılanlar**

- Kritik SQLite veritabanları ve snapshot/export JSON'ları günlük yedek akışına alındı.
- SQLite backup API, dosya kopyası fallback'i ve kopya üzerinde `integrity_check` eklendi.
- 14 günden eski yedeklerin budanması ve isteğe bağlı harici ayna kopyası tanımlandı.
- `publish_now.py` başarılı yayın sonrasında günlük backup çalıştırıyor.
- Commit öncesi backup script'inde Ruff B904 düzeltildi.

**Beklenen çıktı**

Başarılı yayın sonunda şu tür bir kayıt beklenir:

```text
backup ok -> backups\\2026-07-24 | files: 6
```

**Açık kapı**

Windows üzerinde gerçek yayın ritüeliyle backup smoke testi ve tam test tabanının insan tarafından kabulü raporlanmalıdır. OneDrive/Defender dışlama kararının kanıtı da operasyon kaydına eklenmelidir.

### Bölüm 1 — Karne ve arşiv zinciri

**Yapılanlar**

- API kapalı olduğunda `finpilot.db` içinden doğrudan karne fallback'i eklendi.
- Yalnızca `resolved_win` ve `resolved_loss` kayıtları karneye giriyor; açık sinyaller sayılmıyor.
- Karne penceresi 30 gün olarak kararlaştırıldı.
- `signals_archive` için idempotent archive bridge eklendi.
- Başarılı yayından sonra adaylar arşivleniyor.
- Arşiv sürekliliği bozulursa yüksek sesli uyarı ve admin bildirimi üretiliyor.
- Resolver koşusunda 93 satır işlendi; yeni kayıt sınıfı sıfırlandı, kalan 32 satır çözümlenemeyen eski kayıt olarak ayrıldı.

**Beklenen çıktı**

```text
archive: {'archived': N, 'skipped': N, 'date': 'YYYY-MM-DD'}
backup ok -> backups\\YYYY-MM-DD | files: 6
```

Snapshot içinde `karne.by_grade` dolu, `window` değeri `last 30d eval`, `tracked_total` ise kamuya açık takip sayısını taşır.

**Mevcut gerçek veri**

- `tracked_total`: yaklaşık `5,719`.
- Son 30 günlük örnek karne: B `n=36`, C `n=23`; düşük isabet oranları gizlenmiyor.

**Açık kapı**

Bir sonraki gerçek sabah yayınında archive, alarm yokluğu, backup ve dolu karne birlikte kanıtlanmalıdır.

### Bölüm 3 — Bütünlük ve pre-publish sigortaları

**Yapılanlar**

- Gerçek NUL byte kontrolü düzeltildi.
- Export tarihi, boş sonuç, eksik sözleşme alanı ve `scan_complete=False` kontrolleri pre-publish gate'e alındı.
- Sıfır grade ve sıfır eligible üreten bozuk enrichment koşusu yayın öncesinde durduruluyor.
- Bilinçli istisna için `--force` mevcut; normal akışta yayın durur.
- Export'a koşu-özgü `run_id` eklendi; `scan_id` artık koşu kimliğiyle karıştırılmıyor.
- Eşit boyutlu ama zenginleştirilmemiş export, mevcut zengin export'un üzerine yazamıyor; degraded dosyasına yönlendiriliyor.
- Başarılı yayın için `scan_export_<tarih>_published.json` kanıt kopyası tutuluyor.
- Published kopya üzerinden funnel raporu üretilebiliyor.
- Eksik company alanı symbols tablosundan güvenli fallback ile dolduruluyor.

**Beklenen çıktı**

Sağlıklı koşuda gate sessiz geçer. Bozuk koşuda örneğin şu mesajla yayın durur:

```text
PRE-PUBLISH GATE: zenginleştirme boş görünüyor: 1801 satırda 0 grade'li ve 0 eligible satır
Yayın DURDURULDU.
```

Başarılı koşuda ayrıca published export kopyası ve funnel aşamaları görülebilir.

**Açık kapı**

Bir sonraki sabah gerçek export üzerinde funnel raporu çalıştırılmalı; eligible=2 seçicilik sorusu yalnız korunmuş published kopya üzerinden değerlendirilmelidir. Boş çekirdek DB tablolarının emekli statüsü karar logunda kayıtlıdır, fakat dokümantasyon indeksi henüz tamamlanmamıştır.

### Bölüm 4 — Web, dil ve içerik dürüstlüğü

**Yapılanlar**

- Aday rationale metinleri `rationale_i18n` üzerinden TR/EN/DE aktif diline bağlandı.
- `EditionArticle` ve `DailyDouble` düz Türkçe fallback yerine aktif dile göre metin seçiyor.
- DE dili kaldırılmadı; mevcut içerik gerçek ve kullanılabilir olduğu için korundu.
- Masthead ana istatistiği win-rate yerine takip edilen pick sayısına dönüştürüldü.
- Grade isabet oranları yalnızca LedgerStrip'te pencere etiketiyle gösteriliyor.
- Kullanılmayan sahte BUY/SELL mock içeren `Hero.tsx` ve `HeroGrid.tsx` kaldırıldı.
- Masthead'de kalan eski `liveWinRate` referansı düzeltildi.

**Beklenen çıktı**

- Ana sayfada TR/EN/DE seçimi aday gerekçelerini gerçekten değiştirir.
- Masthead'de bağlamsız `%68` benzeri win-rate yerine `5,700+` kamuya açık takip sayısı görünür.
- `/demo` günlük snapshot'tan iki adayı, güvenli metrics alanlarını ve günlük ledger özetini gösterir.

**Açık kapı**

Yerel build temizdir. Ancak son Masthead düzeltmesinden sonra Vercel'e yeniden deploy ve üç dilde görsel/mobil kontrol yapılmalıdır. Önceki production deploy snapshot artifact'ı güncellemişti; bu son web düzeltmesi için yeni deploy ayrıca teyit edilmelidir.

## 4. Operasyonel ve Ürün Çıktısı

Yayın akışının beklenen sırası artık şöyledir:

```text
scan
  -> pre-publish gate
  -> approval / Telegram human approval
  -> Telegram delivery verification
  -> web snapshot publication
  -> archive bridge
  -> archive continuity check
  -> immutable published export copy
  -> daily backup
```

Bu zincirin ürün çıktısı:

- İnsan onayı olmadan Telegram/web yayını yapılmaz.
- V2 shadow-only ve `legacy_quality` üretim sıralaması korunur.
- Full-scan ve snapshot identity sözleşmeleri korunur.
- Günlük yayın yalnız güncel ve zenginleştirilmiş export kanıtlanırsa devam eder.
- Web günlük bölümü adayın fiyat, stop, hedef, R/R, conviction, execution/data quality, volume ve ranking bilgilerini taşıyabilir.
- Telegram başarılı teslim edilmeden web yayını tamamlanmış sayılmaz.

## 5. Commit ve Çalışma Ağacı Durumu

- Son remote commit: `adb3b59 Enrich public daily scan snapshot metrics`.
- Yeni rapor ve Bölüm 0/1/3/4 dosyalarının önemli kısmı staged durumda.
- Bazı dosyalar hem staged hem unstaged (`MM`) durumda; kullanıcı/otomasyon değişiklikleri ayrıştırılmadan toplu commit yapılmamalıdır.
- Runtime JSON, shadow scan, calibration dosyaları ve kişisel dokümanlar çalışma ağacında değişmiş veya untracked durumdadır; bunlar otomatik olarak commit'e alınmamalıdır.
- Bu rapor, denetim sonucu olarak ayrıca commit edilmek üzere oluşturulmuştur.

## 6. Nihai Değerlendirme

**Değiştirilen kritik akış:** çalışıyor ve odak doğrulamalarda temiz.
**Repository genel sağlığı:** baseline'da 12 test kırmızısı var; tam sıfır değil.
**Üretim riski:** bir sonraki gerçek sabah yayın ritüeli, canlı üç dil görsel kontrolü ve son Masthead deploy doğrulaması açık.
**Karar:** Bölüm 0/1/3/4 teknik uygulamaları büyük ölçüde tamamlandı; kapılar, gerçek operasyon kanıtları ve kontrollü commit ayrıştırması tamamlanmadan “tam kapanmış” ilan edilmemeli.
