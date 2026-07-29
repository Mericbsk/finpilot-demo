# FinPilot — UÇTAN UCA UYGULAMA PLANI (Bölüm-Kapılı)
**Tarih:** 2026-07-24 · **Sürüm:** 1.0 (İNCELEME BEKLİYOR) · **Kaynak:** FinPilot_OnTarama_GenelSaglik_2026-07-24.md
**İlke:** Her bölüm kendi içinde uçtan uca çalışır + test edilir + raporlanır + kontrol edilir → ancak o zaman sıradaki bölüme geçilir. Kapı geçilmeden yeni iş açmak YASAK.

---

## ÇALIŞMA KURALLARI (tüm bölümler için geçerli)

1. **Kapı ritüeli:** Bölüm bitince `docs/reports/BOLUM-X_raporu_<tarih>.md` yazılır → Meriç kontrol eder → kapı onayı rapora işlenir → sonraki bölüm açılır.
2. **Tek değişiklik kuralı:** Aynı anda tek bölüm, bölüm içinde adım adım. Üretim-kritik dosyalarda YONERGE kuralı: Claude snippet verir, Meriç uygular (yeni/izole dosyalar hariç).
3. **Kanıt zorunlu:** "Çalışıyor" demek yetmez — komut çıktısı, dosya tarihi, DB sorgusu veya test sonucu rapora yapıştırılır.
4. **Kırılma sigortası:** Her bölüm başında `backups/<tarih>/` yedeği alınır; her değişiklik ayrı git branch'inde; bozulursa geri dönüş adımı bölümde yazılıdır.
5. **Günlük yayın ASLA durmaz:** Plan çalışırken sabah ritüeli (tarama → publish_now) her işlem günü koşmaya devam eder. Seri sayacı her bölüm raporuna işlenir.

**Bölüm sırası ve mantığı:** Önce zemin (yedek/test tabanı), sonra ürünün kalbi (karne), sonra süreklilik (yayın disiplini), sonra sigortalar (bütünlük+contract), sonra vitrin (web/dil), sonra kayıt düzeni (doküman/sözlük), en son lansman provası. P3 kalemleri plana girmez, backlog'da bekler.

---

## BÖLÜM 0 — ZEMİN GÜVENCESİ (yarım gün + 1 saat/gün ritüel)
_Amaç: sonraki bölümlerde yapılacak her işin güvenli zeminde yapılması. Hiçbir onarım, bozulabilir zeminde başlamaz._

**Giriş kriteri:** yok (başlangıç bölümü).

| # | İş | Sahip | Efor |
|---|---|---|---|
| 0.1 | Tam yedek: finpilot.db + distribution.db + academy.db (her iki repo) + data/distribution/*.json → `backups/2026-07-XX/` | M (C komutları verir) | 15 dk |
| 0.2 | Yedeği TEKRARLAYAN hale getir: `publish_now.py` sonuna günlük yedek adımı ekle (yayın günü = yedek günü) + haftalık kopyanın OneDrive DIŞI bir konuma alınması | C snippet + M | 1 saat |
| 0.3 | DB bozulma kök nedeni: OneDrive/AV'nin `data/` klasörünü senkronlamasını/taramasını dışlama kuralı (iki repo'da iki bozulma yaşandı — ortak payda bu olabilir) | M | 30 dk |
| 0.4 | Test tabanı: `pytest -q` tam süit koşusu → kaç test var, kaçı yeşil? Kırmızılar listelenir (düzeltilmez — sadece kayıt). Bu, sonraki bölümlerin "regresyon yok" kanıt tabanıdır | M koşar, C yorumlar | 30 dk |
| 0.5 | Git durumu: commit edilmemiş değişiklikler temizlenir/commit'lenir, GitHub'a push (son push eskiyse) | M | 30 dk |

**Test:** yedekten örnek restore provası (1 dosya geri aç, doğrula) · pytest çıktısı kayıtlı.
**Çıkış kapısı:** yedek klasörü dolu + restore kanıtlı + dışlama kuralı ekran görüntüsü + pytest taban raporu → `BOLUM-0_raporu.md`.
**Kırılma riski:** yok (salt-okunur + kopyalama işleri).

---

## BÖLÜM 1 — KARNE ZİNCİRİNİN DİRİLTİLMESİ (2-3 gün) ★ ürünün kalbi
_Amaç: signals_archive'a yazım yeniden başlar + 5719 tarihi kayıt çözümlenir + by_grade dolu + web LedgerStrip gerçek veri gösterir. DoD#5'in önü açılır._

**Giriş kriteri:** Bölüm 0 kapısı onaylı.

| # | İş | Sahip | Efor |
|---|---|---|---|
| 1.1 | **Teşhis A:** günlük scan neden arşive yazmıyor? `signals_archive`'a yazan kodu bul (git blame/geçmiş), hangi tarihte/commit'te durduğunu tespit et. Bilinçli mi kaza mı — rapora yaz | C | 2 saat |
| 1.2 | **Teşhis B:** `scripts/resolve_open_signals.py` ne bekliyor, neden koşmuyor? Bağımlılıkları (fiyat verisi kaynağı, tablo şemaları) doğrula | C | 2 saat |
| 1.3 | Arşiv yazımını yeniden bağla: bugünkü scan'in eligible adayları her gün `signals_archive`'a yazılsın (snapshot zincirinin içinde, ayrı cron değil) | C snippet + M | ½ gün |
| 1.4 | **Tarihi çözümleme (tek seferlik):** 5719 kayıt üzerinde resolver koşusu — Eyl 2025–May 2026 sinyalleri fiyat verisiyle çözümlenir → `resolved_status` dolar. Önce 50 kayıtlık pilot, sonra tamamı | C + M | 1 gün |
| 1.5 | `by_grade` üretimi: çözümlenmiş kayıtlardan grade bazlı isabet tablosu → snapshot'ın `karne` alanına akar; `warnings`'ten "karne unavailable" düşer | C | ½ gün |
| 1.6 | Web doğrulaması: LedgerStrip gerçek by_grade gösteriyor; Masthead %68 iddiası gerçek karneye bağlanır ya da kaldırılır (karne ne diyorsa o) | C snippet + M | 2 saat |
| 1.7 | Süreklilik sigortası: arşiv 2 işlem günü büyümezse admin'e Telegram DM (sessiz ölüm sınıfı bir daha yaşanmasın) | C | 2 saat |

**Test:** ertesi sabah yayından sonra `select max(ts) from signals_archive` = bugün · by_grade dolu snapshot + web'de görünür · pilot 50 kaydın çözümü elle 5 örnekle çapraz kontrol (fiyat verisi doğru mu?) · pytest regresyon yok.
**Çıkış kapısı:** 2 ardışık gün arşiv büyüdü + by_grade webde + çapraz kontrol raporu → `BOLUM-1_raporu.md`.
**Kırılma riski:** tarihi çözümleme yanlış fiyat verisiyle YANLIŞ karne üretebilir — pilot + çapraz kontrol bu yüzden zorunlu. Şüpheli kayıt çözümsüz bırakılır, uydurulmaz.

---

## BÖLÜM 2 — YAYIN DİSİPLİNİ VE ÖLÇÜM (1 gün)
_Amaç: "expired" sınıfı kapanır, süreler ölçülür, 10 günlük seri sayacı resmen işler._

**Giriş kriteri:** Bölüm 1 kapısı onaylı (karne artık zincirin parçası — disiplin ölçümü tam zinciri kapsamalı).

| # | İş | Sahip | Efor |
|---|---|---|---|
| 2.1 | Expired alarmı: broadcast penceresi kaçarsa admin'e anında DM ("bugün yayınlanmadı!") — sessiz expired yasak | C | 2 saat |
| 2.2 | Süre logu: zincirin her adımı (scan başla/bit, snapshot, publish, web push) süresiyle loglanır → `data/distribution/timing_log.jsonl` | C | 2 saat |
| 2.3 | Seri sayacı: publish_now sonunda "ardışık yayın günü: N" hesaplanır, snapshot'a + admin DM'ine yazılır | C | 1 saat |
| 2.4 | 14:04→14:59 boşluğunun teşhisi: timing log ilk gün ne diyorsa — insan beklemesiyse ritüele not, hesaplamaysa optimizasyon kararı | O | 30 dk |
| 2.5 | Sabah ritüeli dokümante: YONERGE'ye "günlük 2-adım: tarama → publish_now --yes, hedef ≤15 dk" bloğu + hedef saat kararı (piyasa öncesi mi, öğlen mi — NET karar) | O | 1 saat |

**Test:** 1 gün kasıtlı yayın atlama provası → alarm DM geldi mi? · timing_log 2 gün dolu · seri sayacı doğru artıyor.
**Çıkış kapısı:** alarm kanıtı + 2 günlük timing verisi + ritüel YONERGE'de → `BOLUM-2_raporu.md`.
**Kırılma riski:** düşük — hepsi ekleme, mevcut akışı değiştirmiyor.

---

## BÖLÜM 3 — BÜTÜNLÜK VE SÖZLEŞME SİGORTALARI (1-2 gün)
_Amaç: sessiz bozulma ve sessiz regresyon sınıfları kalıcı kapanır. 07-14 krizi bir daha yaşanamaz hale gelir._

**Giriş kriteri:** Bölüm 2 kapısı onaylı.

| # | İş | Sahip | Efor |
|---|---|---|---|
| 3.1 | Bütünlük-kapılı okuyucu/yazıcı VAR/YOK tespiti (kodda ara); yoksa yaz: her JSON yazımında geri-okuma doğrulaması (date==bugün, universe==beklenen, tek-JSON, NUL taraması) — aykırıysa YÜKSEK SESLE hata + admin DM | C | ½ gün |
| 3.2 | Contract-test: `tests/test_scan_contract.py` — zorunlu alanlar (grade, prob_band, conviction, selection_eligible, company…) varlık+tip assert'i; publish_now başında otomatik koşar, kırmızıysa yayın DURUR | C | ½ gün |
| 3.3 | `eligible=2` seçicilik analizi: filtre zinciri 1801→2'yi hangi adımlarda indiriyor? Adım adım sayım raporu. Kasıtsa dokümante, hata varsa düzelt (ayrı karar — kapıda konuşulur) | C | ½ gün |
| 3.4 | `company` boş alanı doldur (sözleşmenin bilinen eksiği) | C | 1 saat |
| 3.5 | Boş DB tabloları kararı: signals/scan_results/buy_signals/execution_* — resmen emekli mi? Karar + şema notu (silme YOK, sadece karar kaydı) | O | 30 dk |

**Test:** kasıtlı bozuk JSON ile prova → kapı yakalıyor mu? · contract-test'e kasıtlı alan silme → yayın duruyor mu? · pytest tam süit yeşil (Bölüm 0 tabanına göre yeni kırmızı yok).
**Çıkış kapısı:** iki sabotaj provası kanıtlı + seçicilik raporu → `BOLUM-3_raporu.md`.
**Kırılma riski:** kapı fazla sıkı olursa sağlam yayını da durdurabilir — ilk 2 gün "uyar ama durdurma" modunda çalışır, sonra sertleşir.

---

## BÖLÜM 3-EK — SCANNER STABİLİTE BULGULARI (2026-07-29 forensic analiz)
_Amaç: Bölüm 3 kapısı 07-24'te onaylandıktan SONRA aynı hat (`distribution/*`, yayın zinciri) 07-27/07-28'de yine iki kez "harden/repair" commit'i aldı. 07-29 kök-neden incelemesi somut, kanıtlı yeni boşluklar buldu — bu ek, Bölüm 3'ü yeniden açmadan onları kayda geçirir. Kaynak: bu oturumdaki forensic analiz (git log, requirements.txt, render.yaml/.env, ci.yml, tests/ incelemesi)._

**Giriş kriteri:** yok — Bölüm 3 zaten kapanmıştı, bu bulgular sonradan keşfedildi; iş doğrudan uygulanabilir (çoğu Level A, izole).

| # | İş | Seviye | Durum | Kanıt |
|---|---|---|---|---|
| 3E.1 | `tests/test_ranking_guard.py` collection hatası düzeltildi: `scanner.evaluate._execution_contract` 07-15'te (`2c60744`) `scanner.execution_policy.execution_contract`'a taşınmış ama test import'u güncellenmemiş — **14 gündür tüm pytest koleksiyonu patlıyor** (tek bir bozuk import tüm süiti collection aşamasında durduruyor). Import + assertion yeni dönüş şekline göre düzeltildi. | Level A | **Uygulandı** | `python -m pytest tests/` artık collect ediyor (önce: `ImportError: cannot import name '_execution_contract'`) |
| 3E.2 | `tests/test_scanner_contract.py`: fixture (`data/distribution/scan_export_latest.json`) yoksa test artık sessizce `skipTest` değil, açıkça `fail` veriyor — "regresyon testi var ama koşulsuz değil" boşluğu kapandı | Level A | **Uygulandı** | Dosya diff'i, bu konuşma |
| 3E.3 | CI coverage kapsamı genişletildi: `--cov=distribution` eklendi (`ci.yml`) — tam olarak tekrar kırılan modül daha önce kapsam dışıydı | Level A | **Uygulandı** | `ci.yml` diff'i |
| 3E.4 | `requirements.txt`: `yfinance>=1.4.1` → `==1.4.1` sabitlendi (bilinen kırılgan veri-kaynağı bağımlılığı, repo hafızasında zaten sorunlu olduğu doğrulanmış); yinelenen çakışan `duckduckgo-search>=6.0.0` satırı silindi (`==8.1.1` tek kaynak kaldı) | Level A | **Uygulandı** | `requirements.txt` diff'i |
| 3E.5 | Doğrulama: yukarıdaki 4 değişiklikten sonra `pytest tests/ --cov=...` tam koşusu — collection hatasız + `--cov-fail-under=70` ile gerçek sonuç | Level A | **Uygulandı — Doğrulandı:** collection artık 0 hata (önce: 1 collection error, tüm süit durmuştu). Sonuç: **734 passed, 15 failed, 6 skipped, 380.81s**. Coverage: **43.47%** (`--cov-fail-under=70` **FAIL**). | pytest tam çıktısı, bu oturum |
| 3E.6 | `stable-2026-07-29` git tag'i: bu düzeltmelerin üzerine, "bilinen çalışan durum" işaretleyici | Level A (öneri) | Onay bekliyor (push/tag paylaşılan repo'yu etkiler) — **not:** 15 test kırmızı olduğu için "stable" etiketi şu an yanıltıcı olur, 3E.11 triyaj edilmeden atılmamalı | — |
| 3E.11 | **YENİ BULGU:** collection düzeldikten sonra ortaya çıkan 15 test hatası — hiçbiri bu oturumda değiştirilen 4 dosyayla ilgili değil (ör. `test_evaluate.py`, `test_catalyst.py`, `test_squeeze_factor.py`, `test_full_universe_robustness.py`, `test_new_endpoints.py`, `test_content_layer.py`, `test_api_runtime.py`, `test_prometheus.py`, `scanner_rollout/test_runtime_baseline.py`). **Doğrulandı:** bunlar 07-15'ten beri collection hatası nedeniyle görünmez olan, muhtemelen önceden var olan regresyonlar/drift'ler (ör. `compute_recommendation_score` beklenenden farklı skor üretiyor, `dedup_symbol_day()` bir `policy` kwarg'ı kabul etmiyor, glossary lint bir "garanti" kelimesi yakalıyor). **Olası, test edilmeli:** her biri ayrı kök-neden gerektirir (kod mu bozuk, test mi güncel değil) — bu oturumun kapsamı dışında, tek tek incelenmeden düzeltilmedi. | Level B | **Triyaj bekliyor — onay bekliyor** | pytest tam çıktısı `FAILURES` bölümü, bu oturum |
| 3E.12 | **YENİ BULGU:** `--cov-fail-under=70` eşiği 2026-03-30'da (`a9f65923`) 30'dan 70'e çıkarılmış. **Doğrulandı (hesaplandı):** `distribution/` modülü kendi içinde ~63% kapsanıyor — genel ortalamayı düşüren o değil, `drl/` altında binlerce satır %0 kapsanan modül (`data_loader.py` 274/274, `ensemble_router.py` 324/324, `inference.py` 307/307, `specialists.py` 161/161 vb.) — yani 3E.3'teki `--cov=distribution` eklemesi bu FAIL'e neden OLMADI (distribution dahil/hariç fark ~%42→%43, iyileşme yönünde). **Olası, test edilmeli:** eşik gerçek CI ortamında (GitHub Actions, Ubuntu) hiç geçmemiş mi yoksa yakın zamanda mı bozulmuş — bu ortamdan GitHub Actions çalışma geçmişine erişilemedi, doğrulanamadı. | Level B/C (politika kararı) | **Karar bekliyor** — eşiği düşürmek/`drl` hariç tutmak/gerçek test yazmak seçenekleri var, hiçbiri uygulanmadı | pytest coverage tablosu, git log `ci.yml`, bu oturum |
| 3E.7 | Tek otorite env kaynağı: `render.yaml`'daki env listesi `.env.example`'daki 9 `FINPILOT_ENABLE_*`/`FRED_*`/`SEC_EDGAR_*` bayrağından yalnız 1'ini (`FINPILOT_ENABLE_DISTRIBUTION`) içeriyor — production'da geri kalanlar kod varsayılanına düşüyor. Öneri: render.yaml'ı `.env.example`'dan üreten küçük bir script YA DA en azından iki dosyayı karşılaştıran bir CI kontrolü | Level B | **Onay bekliyor** | `render.yaml` vs `.env.example` karşılaştırması, bu konuşma |
| 3E.8 | Dry-run zorunluluğu: `scripts/preview_publish.py` (07-28'de eklendi) resmi tek yol hâline getirilsin — `publish_now.py --yes` doğrudan çağrısı fiilen kısıtlansın/uyarı versin | Level B | Kısmen başlamış (07-28), resmi karar **onay bekliyor** | `docs/ops/YAYIN_ONIZLEME_ONAY_AKISI_20260728.md`, decision-log 07-28 kaydı |
| 3E.9 | Erken uyarı sistemi: scan süresi/sonuç sayısı geçmiş ortalamanın dışına çıkarsa otomatik Telegram/log uyarısı (tasarım + eşik tanımı gerekiyor, telemetry.py üzerinde ölçülmedi) | Level B | **Öneri, tasarım yapılmadı** | — |
| 3E.10 | Manuel `docker exec -i` kanalı için runbook notu (SQLite kilit riski) — kod değişikliği değil, disiplin notu; zaten repo hafızasında var | Level B (düşük öncelik) | Bilgi zaten mevcut, sadece runbook'a taşınacak | `/memories/repo/docker-deploy.md` |

**Test:** `python -m pytest tests/ --ignore=tests/test_views_integration.py --cov=scanner --cov=drl --cov=core --cov=auth --cov=api --cov=broker --cov=llm --cov=views --cov=distribution --cov-fail-under=70` collection hatasız tamamlanmalı ve gerçek coverage yüzdesi rapora yazılmalı.
**Çalıştırıldı (2026-07-29):** collection temiz (0 hata) ✓ — ama `--cov-fail-under=70` **FAIL** (gerçek: 43.47%) ve 15 test kırmızı (3E.11). İkisi de bu oturumun 4 Level A değişikliğinden **kaynaklanmıyor** (bkz. 3E.11/3E.12 kanıt), ama Bölüm 3-Ek'in "temiz koşu" hedefi teknik olarak karşılanmadı — kısmi başarı olarak işaretlendi.
**Çıkış kapısı:** pytest tam-süit çıktısı (kırmızı sayısı, coverage %) ✓ alındı + 3E.7-3E.9 **ve** yeni bulgular 3E.11-3E.12 için Meriç kararı (onay/red/erteleme/triyaj sırası) → bu tabloya işlenecek. Bölüm bu haliyle **kısmen kapalı**: Level A teknik iş bitti ve doğrulandı, ama doğrulama sonucu yeni Level B/C kararlar gerektiriyor.
**Kırılma riski:** düşük — test dosyası ve CI/requirements değişiklikleri izole; üretim kodu (`scanner/`, `distribution/`) davranışı değişmedi, sadece test/CI/bağımlılık katmanı düzeltildi. 15 test hatası ve coverage açığı bu oturumda **oluşturulmadı**, sadece **görünür hale geldi**.

---

## BÖLÜM 4 — WEB VE DİL BÜTÜNLÜĞÜ (1-2 gün)
_Amaç: vitrin tek sesli, iki dilli tutarlı, görünür hatasız._

**Giriş kriteri:** Bölüm 3 kapısı onaylı (sağlam veri olmadan vitrin cilalanmaz).

| # | İş | Sahip | Efor |
|---|---|---|---|
| 4.1 | EN kararı: web dil anahtarı EN'de `snapshot_en_latest.json`'ı tüketir YA DA EN anahtarı gizlenir. Yarım dil yok. (Öneri: EN tüketimi — dosya zaten her gün üretiliyor) | O karar, C uygular | ½ gün |
| 4.2 | "İts" `_cap(lang)` yaması + `prob_band:"—"` web fallback metni | C snippet + M | 1 saat |
| 4.3 | FactCheckingDesk içerik kontrolü (ön-taramada grep temizdi ama görsel doğrulama yapılmadı) + tüm ledger bileşenlerinde son compliance turu | O | 1 saat |
| 4.4 | DE anahtarı kararı: gizle (içerik yok) | C | 30 dk |
| 4.5 | Mobil 3-cihaz testi (DoD#3'ün açık ucu) + Lighthouse koşusu (performans tabanı) | M | 2 saat |
| 4.6 | Vercel'e deploy + canlı doğrulama: finpilot.at'ta bugünün snapshot'ı, iki dilde | M | 1 saat |

**Test:** canlı sitede TR/EN geçişi doğru rationale gösteriyor · mobilde 3 cihaz ekran görüntüsü · lint/compliance turu temiz.
**Çıkış kapısı:** canlı URL kanıtları + Lighthouse skoru → `BOLUM-4_raporu.md`.
**Kırılma riski:** deploy hatası — önceki Vercel deployment'a tek tıkla rollback mümkün, risk düşük.

---

## BÖLÜM 5 — DOKÜMAN VE SÖZLÜK GERÇEKLEMESİ (1 gün)
_Amaç: kayıtlar kodla aynı gerçeği anlatır; bir sonraki oturum yanlış dokümana bakmaz._

**Giriş kriteri:** Bölüm 4 kapısı onaylı.

| # | İş | Sahip | Efor |
|---|---|---|---|
| 5.1 | LAUNCH_CHECKLIST gerçekleme: DoD#4 ✓, M7 düzelt (flag=0), retroaktif Hafta-1 kapı notu, seri sayacı bağlantısı, takvimi bugüne çek | O | 1 saat |
| 5.2 | docs/ reorg tamamla: `docs/ops/` + `docs/archive/2026-07/` kur, kök .md'leri taşı (ReAudit Bölüm 7 şeması), her dokümana `Durum:` başlığı | M (C liste verir) | 2 saat |
| 5.3 | PARKING_LOT güncelle: delinen maddeler (akademi export, Ledger tasarımı) gerçeğe göre yeniden yazılır | O | 30 dk |
| 5.4 | Sözlük tek-kaynak kararı: `glossary.py` üretici, `dictionary.json` + terms.ts türev — üretim script'i tek komut. Temmuz terimleri eklenir (prob_band, conviction, edition, karne/by_grade, Grade A/B/C) | C | ½ gün |
| 5.5 | `docs/INDEX.md`: "hangi soru → hangi doküman" tablosu güncellenir + bu planın ve raporlarının kaydı | C | 30 dk |

**Test:** dictionary.json yeniden üretilir, web GlossaryTooltip yeni terimleri gösterir · kökte kalan .md sayısı ≤5 · INDEX'ten 3 rastgele soruya doğru doküman bulunuyor.
**Çıkış kapısı:** dosya ağacı çıktısı + sözlük diff'i → `BOLUM-5_raporu.md`.
**Kırılma riski:** taşınan dokümanlara kırık referans — taşıma listesi raporda tutulur.

---

## BÖLÜM 6 — LANSMAN PROVASI VE KULLANICI HAZIRLIĞI (1 hafta, paralel: günlük yayın serisi işler)
_Amaç: DoD'nin insan/kullanıcı tarafı. Sistem artık teknik olarak tam — şimdi kanıt ve seyirci birikir._

**Giriş kriteri:** Bölüm 5 kapısı onaylı + seri sayacı ≥3.

| # | İş | Sahip | Efor |
|---|---|---|---|
| 6.1 | Kırmızı-gün tatbikatı (DoD#10): kasıtlı arıza senaryosu (veri yok/lint kırmızı/PC geç açıldı) → prosedür işletilir, süre tutulur | O | 2 saat |
| 6.2 | Premium mekaniği uçtan uca test modunda (DoD#9): test kartıyla ödeme → premium kanal daveti → iptal akışı | O | ½ gün |
| 6.3 | bot_runner rol kararı uygulanır: yalnız public komutlar (/start /today) ya da kapat | C | 2 saat |
| 6.4 | Brif kalite turu (DoD#6): 3 dış okuyucuya son 5 brif → geri bildirim formu | M | 2 gün (bekleme) |
| 6.5 | Takipçi büyütme başlangıcı (DoD#7): kanal tanıtımı — GTM planındaki ilk adımlar (bu plan kapsamında sadece BAŞLATILIR) | M | sürekli |
| 6.6 | Feedback döngüsü: tg_feedback/demo_feedback'in çalıştığı 1 gerçek kayıtla kanıtlanır | O | 1 saat |

**Test:** tatbikat tutanağı · premium test dekontu/log · dış okuyucu formları.
**Çıkış kapısı:** DoD tablosunun güncel durumu (kaç/10) + kalan maddelerin tarihli sahipleri → `BOLUM-6_raporu.md` = **LANSMAN HAZIRLIK RAPORU**.

---

## KAPSAM DIŞI (backlog — plana bilinçli alınmadı)
Monitoring kur/iptal kararı · Alpaca oto-execution (sahip+tarih atanana kadar park) · FinSense ders hızlandırma · agents "karşı görüş" satırı · tarihi track-record'un aws paketi · Tauri/alert sistemi (PARKING_LOT). Bunlar Bölüm 6 kapısından sonra önceliklenir.

---

## ZAMAN ÖZETİ

| Bölüm | Süre | Kümülatif |
|---|---|---|
| 0 — Zemin | ½ gün | 0.5 g |
| 1 — Karne ★ | 2-3 gün | ~3.5 g |
| 2 — Yayın disiplini | 1 gün | ~4.5 g |
| 3 — Sigortalar | 1-2 gün | ~6 g |
| 4 — Web/dil | 1-2 gün | ~7.5 g |
| 5 — Doküman/sözlük | 1 gün | ~8.5 g |
| 6 — Lansman provası | 1 hafta (çoğu bekleme/paralel) | ~2.5-3 hafta |

Gerçekçi hedef: **Bölüm 0-5 iki haftada** (işlem günü aksatmadan), Bölüm 6 üçüncü haftada. 10 günlük kesintisiz yayın serisi Bölüm 2'den itibaren işlemeye başlar → seri ve teknik iş aynı anda olgunlaşır.

---
_Durum: İNCELEME BEKLİYOR · Onay sonrası Bölüm 0 başlar. Değişiklik önerileri bu dosyaya işlenir, ayrı plan dosyası AÇILMAZ._
