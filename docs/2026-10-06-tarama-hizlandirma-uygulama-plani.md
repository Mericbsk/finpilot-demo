# Tarama Hızlandırma — Uçtan Uca Uygulama Planı v3.4

**Tarih:** 2026-10-06 · **Sürüm:** v3.4 · **Durum:** Blok 0A/kapalı bayrakla 0B izole kod kontrolleri PASS; 0A canlı gözlemi ve canlı geçiş kapıları AÇIK; diğer bloklar ONAY BEKLİYOR · **Önceki:** v3.3; `docs/2026-09-21-tarama-hizlandirma-plani.md` (v2), `docs/2026-09-23-neden-yavas-ve-cozum-uzayi.md`

**Değişiklik kaydı (v3.4):** Meriç'in “gereknlerı yap” talebiyle belirtilen teknik engeller giderildi. Gölgelenen iki yardımcı tanım kaldırıldı; eski baseline beklentileri mevcut kodun karakterizasyonuna çevrildi ve pozitif kontroller eklendi. Geniş scanner kapısı 172 passed / 0 failed; canlı gözlem, restart, aktivasyon ve yayın yapılmadı. Aşağıdaki v3.2/v3.3 koşu kayıtları tarihseldir; güncel teknik durum v3.4 kaydındadır. Ürün/risk kuralı veya mevcut canlı kapılar değişmez.

**Değişiklik kaydı (v3.3):** Meriç'in “evet yapalım” onayı, 0B kod hazırlığını 0A canlı gözleminden önce yapmaya izin verir. Bu yalnız geliştirme sırasını değiştirir: `FINPILOT_SCAN_COORDINATOR=0` varsayılanıyla hazırlanır; restart, canlı ölçüm, geniş test kapısı veya 1-2 günlük 0A gözlemi atlanmaz. Risk ve yayın kuralları değişmez.

**Değişiklik kaydı (v3.2):** Meriç'in 2026-10-06 onayıyla §1'deki kopya-batch kanıtı iddiası geri çekildi. Blok 0A kod ve test uygulaması onaylandı; restart, canlı ölçüm ve diğer blokların aktivasyonu bu onaya dahil değil.

Bu plan, 21 Eylül'den beri bilinen ama uygulanmamış düzeltmeleri ve 6 Ekim'de bulunan eşzamanlılık sorununu tek bir uygulanabilir sıraya koyar.

---

## 1. Neredeyiz

| | |
|---|---|
| Darboğaz | `prefetch.repair` — sürenin %81.6 (medyanların oranı) / %86.5 (koşu-başına medyan) |
| 200-sembol medyan, tüm geçmiş | 307 sn (n=328) |
| 200-sembol medyan, 23 Eylül'den beri | **415 sn** (n=23) |
| Tam evren (~1.812 sembol, ~9 batch) | ~50-65 dk |
| 23 Eylül'den beri uygulanan düzeltme | **Yok** |

### 6 Ekim'de bulunan: yenileme → yetim tarama → eşzamanlılık

Tarayıcı yenilendiğinde sunucudaki tarama **durmuyor**. `run_in_executor` thread'i iptal edilemez; `asyncio.wait_for` yalnızca beklemeyi bırakır, işi değil. Yarım kalan batch 400-500 sn arka planda koşmaya devam eder. Kullanıcı yeniden başlatınca iki tarama aynı anda koşar.

Gözlem (`scan_timing.jsonl`, 6 Ekim): farklı zamanlarda başlayıp 1-2 sn arayla biten kayıtlar eşzamanlı çalışma ile tutarlı. 376/377'nin aynı sayaçları süreç-global ölçümler olduğu için aynı batch'in iki kez tarandığını kanıtlamaz. Meriç'in yenileme anlatımı kopya istek olasılığını destekler; batch ve çağıran kimliği bu kayıttan belirlenemez.

Sonuçları:
- **Hız:** sunucu 16 eşzamanlı taramaya izin veriyor (`scan.py`, `_executor = ThreadPoolExecutor(max_workers=16)`); her biri ~40 thread açıyor; hepsi aynı GIL'i ve yfinance hız sınırını paylaşıyor
- **Ölçüm:** sayaçlar süreç-global; her tarama başlarken sıfırlıyor (`scan.py:341`) → eşzamanlı taramalar birbirinin sayaçlarını siliyor (kayıt 379: 563 sn, tüm sayaçlar sıfır)

---

## 2. Değişmez kurallar (bu oturumun dersleri)

1. **Alet → ortam → ölçüm → değişiklik → doğrulama.** Sırası pazarlığa kapalı.
2. **Ölçüm aleti ile davranış değişikliği aynı adımda olmaz.** Ayrı commit, ayrı doğrulama.
3. **Kod yazmadan önce dosyanın güncel hali okunur.** Araç "dosya diskte değişti" derse yazma durur. (Bu repoda iki ajan çalışıyor; üç çakışma yaşandı.)
4. **Plandan sapılırsa sapma aynı anda bu belgeye yazılır.**
5. **Her değişiklik bayrakla geri alınabilir.**
6. **Her sayı etiketlidir:** MEASURED / ESTIMATED / UNKNOWN. Tahmin sonuç sayılmaz.
7. **Sinyal ve skor formülü bu planın yetkisi dışında.** Huni hariç (aday kümesini etkilediği için ayrı ürün onayı ister, Blok 2).

---

## 3. Doğrulama protokolü (her blokta aynen tekrarlanır)

### 3.1 Kod kontrolleri

| Kontrol | Komut | Nerede |
|---|---|---|
| Sözdizimi | `python -m py_compile <dosyalar>` | konteyner |
| Odak testler | `pytest tests/test_scanner_performance.py -q` | konteyner |
| Geniş testler | `pytest tests/ -q -k "scan or data_fetcher or evaluate"` | konteyner |
| Diff temizliği | `git diff --check` + `git diff --stat` | host |
| Çakışma kontrolü | değiştirilen her dosyada `grep` ile çift tanım yok | host |

> Claude'un sandbox'ı Python 3.10; repo 3.11 istiyor (`datetime.UTC`). **Testler konteynerde koşulur** (`docker compose exec -T api pytest ...`). Claude kodu ve testi yazar, sonuçları okuyup değerlendirir.

### 3.2 Yükleme

| Değişiklik türü | Gereken |
|---|---|
| Kod (`scanner/`, `api/` bind mount) | `docker compose restart api` |
| `.env` değişikliği | `docker compose up -d --no-deps --force-recreate api` |

Service adı **`api`**. `finpilot_api` container adıdır; `restart finpilot_api` sessizce etkisiz kalır.

### 3.3 Ölçüm koşusu

- **Yol:** API üzerinden (web arayüzü tarama düğmesi). Taze `docker exec` süreci **kullanılmaz** — kıyaslanamaz.
- **Sıra:** tek tek. Ölçüm sırasında **yenileme yok, ikinci sekme yok**.
- **Evren:** aynı ilk 200 sembol (ilk batch) — ya da tam evren taraması yapılıp ilk batch'in kaydı kullanılır.
- **Sayı:** 6 koşu, ilki soğuk, atılır → 5 koşu analiz edilir.
- **Pencere:** aynı seans (piyasa açık ya da kapalı, karışık değil).
- **Raporlanan:** `total_s` medyan ve p95/medyan · `prefetch.repair` · `yf_fallback` · `yf_bulk_symbols` · `intraday_coverage` (min ve yayılım) · `result_symbols` · bloğa özel alanlar.

### 3.4 Çıktı eşdeğerliği

Her blok sonrası shortlist üyeliği ve skor dağılımı bir önceki baseline ile karşılaştırılır. Blok 0 ve 1 için beklenen: **aynı** (sağlayıcı gürültüsü hariç). Fark çıkarsa blok geri alınır ve incelenir.

### 3.5 Kayıt

Her blok sonunda `docs/governance/decision-log.md`'ye: ne değişti, testler, ölçüm, sapmalar.

---

## 4. Bloklar

### BLOK 0 — Eşzamanlılık ve ölçüm hijyeni (v3.1: iki alt bloğa bölündü)

> **v3.1 revizyonu (2026-10-06, bağımsız inceleme sonrası).** v3'teki Blok 0 tasarımında üç hata vardı:
> 1. **Kilit HTTP isteğine bağlıydı.** Timeout'ta `async with` çıkar, kilit bırakılır — ama `run_in_executor` thread'i durdurulamadığı için çalışmaya devam eder. Yani eşzamanlılık kilide rağmen geri gelir. (Yapay testle doğrulandı.)
> 2. **"Fazlası bekler" sınırsızdı.** Web proxy 620 sn bekliyor (`web/src/app/py-api/[...path]/route.ts`). ~400 sn kuyruk + ~400 sn koşu bunu aşar → istemci timeout.
> 3. **Kilit yalnızca `/scan` route'undaydı.** `agents/scanner_agent.py:36` `evaluate_symbols_parallel`'ı doğrudan çağırıyor; kilidin dışında kalır ve aynı global sayaçları kirletir.
>
> Ayrıca: 6 Ekim'deki 376/377'nin birebir aynı sayaçları **"aynı batch iki kez"in kanıtı değil** — sayaçlar süreç-global olduğu için aynı anda biten iki tarama aynı değerleri okur. Kopya istek ihtimali Meriç'in yenileme anlatımıyla tutarlı ama kayıttan kanıtlanamıyor.

#### BLOK 0A — Ölçüm hijyeni (salt gözlem, davranış değişmez)

**Seviye:** B (yalnızca kayıt alanı) · **Bağımlılık:** yok

| Adım | İş |
|---|---|
| 0A.1 | **İş/istek kimliği:** `job_id` (bir tarama işi) ve `request_id` (bir HTTP isteği) ayrı. Kayda `caller` (`api_scan` / `scanner_agent` / `script`) |
| 0A.2 | **Başarısız sonuçlar da kaydedilsin.** Şu an kayıt yalnızca başarılı yanıt yolunda yazılıyor; timeout, hata ve istemcinin koptuğu durumlar görünmüyor. Kayda `outcome` alanı: `ok` / `timeout` / `error` / `client_gone` |
| 0A.3 | **Gerçek çalışan iş sayısı:** `active_jobs_at_start`, `active_jobs_at_end`. Sayaç güvenilirliği bundan türetilir: 1'den büyükse `counters_unreliable=true` |
| 0A.4 | Tüm giriş noktaları (`/scan` route ve `ScannerAgent`) aynı kayıt yardımcısını kullanır |

**Neden ayrı:** önce eşzamanlılığın gerçekten ne sıklıkta olduğunu ve kimden geldiğini **ölçeriz**, sonra davranışı değiştiririz. Ölçüm aleti ve davranış değişikliği aynı adımda olmaz (kural 2).

**Doğrulama:** normal kullanımda 1-2 gün kayıt topla. Soru: kaç kayıtta `active_jobs_at_start > 1`, `caller` dağılımı ne, kaç `client_gone` var?

**v3.2 uygulama kaydı (2026-10-06):** 0A kodu ve odak testleri tamamlandı; servis restartı ve 1-2 günlük canlı kayıt kampanyası **YAPILMADI**. Geniş test kapısı aşağıdaki iki mevcut-beklenti hatası nedeniyle henüz yeşil değil; 0A -> 0B geçişi kapanmış sayılmaz.

- Ortak yardımcı: `core/scan_observability.py`. Evaluator dekoratörü tüm doğrudan çağrıları da gözler; API ve `ScannerAgent` çağıran bağlamını verir, bağlamsız doğrudan çağrı `script` olarak kaydedilir.
- `FINPILOT_SCAN_OBSERVABILITY=0` yeni gözlem kayıtlarını kapatır; eski başarılı API timing kaydı korunur. Varsayılan `1`; ortam dosyası bu görevde değiştirilmedi.
- JSONL `event` ayrımı: `job_started`, `job_finished`, `request_finished`, `request_disconnected`, `caller_finished`. Gerçek iş sayımı evaluator içine girişte başlar ve thread gerçekten çıktığında biter. Timeout/kopma yalnız bekleyenin sonucudur; thread'in daha sonra bitişi aynı `job_id` ile ayrıca yazılır.
- `active_jobs_at_end`, çıkmakta olan işi **dahil** sayar; `active_jobs_at_event` kayıt anındaki kalan işleri sayar. Aradaki geçici çakışma `peak_active_jobs` ile korunur. Sayaç reseti ve yeni işe geçiş de önceki timing snapshot'ını ihtiyatlı biçimde güvenilmez işaretler.
- Sayım **süreç içidir** (`process_id`, `active_jobs_scope=process`); çoklu worker/süreç toplamı değildir. `client_gone`, API'nin gözleyebildiği bağlantı kopması veya handler iptalidir; proxy arkasındaki tarayıcı kopmasının iletildiği varsayılmaz.
- Analizde API latency için yalnız `event=request_finished` ve `outcome=ok` kayıtları kullanılır; timeout/hatalarda `request_s` vardır, geçmişteki `total_s` anlamı değiştirilmez. İş sayısı için yalnız `job_finished` ve benzersiz `(process_id, job_id)` kullanılır. Başlangıç/istek kayıtları ek tarama sayılmaz.
- MEASURED: izole Python 3.11.15 container'da odak suite **32 passed**, altı dosyalık scanner/contract suite **88 passed**. Tam `tests/ -k "scan or data_fetcher or evaluate"` koşusu **135 passed / 4 failed**; shortlist fixture eksikliği giderilince ilgili iki tarihsel test geçti. Kalan iki `tests/scanner_rollout/test_runtime_baseline.py` testi gözlem kapalı kontrolünde de başarısız: score-2/alignment ve min-signal-score beklentileri. Sinyal kuralı veya bu testlerin beklentileri değiştirilmedi.
- İzolasyon: mevcut image, ağ kapalı, kod/fixture salt-okunur, DB/data/cache/log geçici; gerçek `.env`, sırlar, restart, live scan ve yayın yok. Genel planın 3.1 kapısındaki canlı container yerine ayrı container seçildi; canlı state'i test importlarından koruma sapması burada kaydedildi.

#### BLOK 0B — İş koordinasyonu (davranış değişikliği)

**Seviye:** B · **Geliştirme bağımlılığı (v3.3):** 0A kodu ve izole testler; canlı veri beklenmeden kapalı bayrakla geliştirme onaylı. **Canlı aktivasyon bağımlılığı:** 0A verisi, geniş test kapısı ve ayrı insan yayın kararı. 0A -> 0B canlı geçişi henüz kapanmadı.

Koordinasyon route'ta değil, **tarayıcı katmanında** olur — `evaluate_symbols_parallel`'ı çağıran her yol tek bir koordinatörden geçer.

| Adım | İş | Neden |
|---|---|---|
| 0B.1 | **Slot işe ait, isteğe değil.** Slot thread'in içinde alınır, `finally` ile iş gerçekten bittiğinde bırakılır. `FINPILOT_SCAN_MAX_CONCURRENT`, varsayılan 1 | Timeout veya kopma slotu bırakmaz, eşzamanlılık geri gelmez |
| 0B.2 | **Kopya iş birleştirme.** İş anahtarı: normalize edilmiş sembol kümesi + tüm etkili parametreler (kelly, aktif bayraklar) + yetki kapsamı. Aynı anahtarla gelen istek çalışan işe bağlanır. Bir iş → birden çok `request_id`. **Kalıcılaştırma (shortlist, shadow ledger, watchlist, distribution export) iş başına bir kez** | Yenileme senaryosu: yeni istek yetim işe bağlanır. Kopyalar ölçüm istatistiğini şişirmez |
| 0B.3 | **İşbirlikçi iptal.** Bir işe bağlı **tüm** istekler gittiyse (timeout/kopma) işe iptal bayrağı konur. İş, faz sınırlarında (prefetch sonrası; değerlendirme döngüsünde her N sembolde) bayrağı kontrol eder ve erken çıkar | Farklı batch'in yetimi de boşa koşmaz. Bir bekleyenin iptali diğer bekleyenleri etkilemez |
| 0B.4 | **Sınırlı kuyruk ve süre bütçesi.** Kuyruk kapasitesi ve azami bekleme (ör. 120 sn). Bekleme + tahmini koşu proxy bütçesini (620 sn) aşacaksa istek beklemez, açık bir "meşgul, tekrar dene" yanıtı alır. Frontend bunu mevcut başarısız-batch akışıyla gösterir | 620 sn'lik proxy timeout'una sessizce çarpmamak |

**Hazırlık güvenliği / geri alma:** `FINPILOT_SCAN_COORDINATOR=0` (varsayılan) koordinatörü tamamen atlar; mevcut 0A davranışı korunur. Yalnız izole testlerde `1` ile açılır. Canlı açılış bu geliştirme onayına dahil değildir. Koordinatör açıkken `FINPILOT_SCAN_MAX_CONCURRENT=16` + `FINPILOT_SCAN_DEDUPE=0` + `FINPILOT_SCAN_COOP_CANCEL=0` davranış kontrollerini gevşetir; tam geri alma için koordinatör bayrağı kapatılır.

**v3.3 kod hazırlığı (2026-10-06):** İzole 0B kodu hazır; canlı aktivasyon **YAPILMADI**. Bu kayıt geniş kapıyı veya 0A gözlemini tamamlanmış saymaz.

- Ortak koordinatör `core/scan_coordinator.py`; API, agent ve doğrudan evaluator aynı süreç-içi havuzu kullanır. API işi evaluator + zenginleştirme + mevcut dört kalıcılaştırma adımını kapsar; slot bu işin thread'i gerçekten bitene kadar tutulur. İç evaluator çağrısı mevcut işi yeniden kuyruğa sokmaz. Çoklu worker/servis veya koordinatör dışındaki sağlayıcı trafiği için global serileştirme iddiası yoktur.
- API dedupe anahtarı operasyon, normalize sembol kümesi, **ham sembol sırası/çokluğu**, Kelly, mevcut scanner/DRL ayarları, piyasa/strateji durumu, sır içermeyen `FINPILOT_` bayrakları ve `(sub, role, type)` yetki kapsamını içerir. Ham girdi de korunur: farklı sunumların evren sayımı/çıktı sırası bakımından eşdeğer olduğu varsayılıp birleştirilmez. Callback kimliği doğrudan evaluator anahtarına dahildir. Agent'ta kullanıcı yetki kapsamı bulunmadığından çağrıları birleştirilmez; yine aynı slot sınırına uyar.
- Yalnız **halen çalışan/kuyruktaki** işler birleşir; bitmiş sonuç cache'i veya TTL yoktur. Her bekleyen bağımsız sonuç kopyası alır. Son bekleyen gidince iptal beklemeye alınır; aynı anahtar faz sınırından önce yeniden bağlanırsa iptal kaldırılır. Faz sınırında iptal kesinleşmiş işe yeniden bağlanılmaz.
- İptal prefetch sonrası, sembol değerlendirme girişleri/dönüşleri ve kalıcılaştırma grubu öncesinde kontrol edilir. Çalışan sağlayıcı I/O'su/thread zorla kesilmez; başlamış kalıcılaştırma grubunun ortasında abort yapılmaz. API timeout/kopma yalnız o bekleyeni ayırır. Agent/script'in senkron beklemesi 600 sn'de ayrılır; dış scheduler'ın daha erken beklemeyi bırakması ayrıca gözlenmiş sayılmaz.
- Teknik varsayılanlar: `FINPILOT_SCAN_MAX_CONCURRENT=1`, `FINPILOT_SCAN_QUEUE_CAPACITY=1`, `FINPILOT_SCAN_QUEUE_WAIT_S=120`, `FINPILOT_SCAN_ESTIMATED_JOB_S=480`, dedupe/cooperative cancel `1`. 480 sn **ESTIMATED** ilk admission tahminidir, ölçülmüş koşu süresi değildir. Bekleme + tahmin en fazla API'nin 600 sn bütçesine alınır; 620 sn proxy için 20 sn pay bırakılır. Kuyruk kapasitesi/süre aşımı `503` + `Retry-After: 5`; istek deadline'ı `504`. Bayrak/config değişikliği bu görevde canlı ortama uygulanmadı.
- Kayıtlarda `coordinator_version=1`, `queue_wait_s` ve `job_skipped` eklenir. Skipped işler gerçek tarama sayılmaz. Koordineli API `job_s` tüm pipeline'ı, doğrudan evaluator işi yalnız evaluator'ı kapsar; 0A'nın evaluator süresiyle tek seride karşılaştırılmaz. `request_s` kuyruk dahil istemci gecikmesidir; timing/counter analizi için benzersiz `(process_id, job_id)` ve sürüm/event filtreleri gerekir. Global sayaç güvenilirliği bütün sağlayıcı çağrılarının izole olduğu kanıtı değildir.
- **MEASURED:** Son kodla odak suite **59 passed**; son geniş `tests/ -k "scan or data_fetcher or evaluate"` koşusu **164 passed / 2 failed / 867 deselected**. Aynı iki `tests/scanner_rollout/test_runtime_baseline.py` beklentisi başarısız; geniş kapı **NOT PASS**. Altı Python dosyası Python 3.11 derleme, Ruff lint ve editör tanıları temiz. `evaluate_symbol`, dört kalıcılaştırma yardımcısı ve evaluator imzası HEAD'e karşı AST kontrolünde aynı. Sinyal/risk/sağlayıcı kuralları ve başarısız test beklentileri değiştirilmedi.
- Çakışma kontrolü: evaluator'da mevcut `_feature_contract` **3 tanım**, HEAD'de de **3 tanım**. Yeni çift tanım eklenmedi; ancak §3.1'in sıfır çift tanım koşulu **PASS değil**. Kapsam dışı mevcut yardımcı temizliği yapılmadı; bu bulgu iki test hatasından ayrı kaydedilir.
- Test ortamı mevcut image, ağ kapalı, kod/fixture salt-okunur, DB/data/cache/log/bytecode geçici; gerçek `.env` veya sırlar okunmadı. Geniş collection için `scripts/` salt-okunur eklendi; bu bilimsel araştırma tekrar koşusu değildir. Restart/deploy/canlı ölçüm, commit, hız kazancı ve bölüm kapatma **YOK**. 0A canlı gözlemi ve insan yayın kararı hâlâ bekliyor.

**v3.4 teknik kapı düzeltmesi (2026-10-06):** Belirtilen iki teknik engel giderildi; bu yalnız izole kod doğrulamasıdır, canlı geçiş veya ürün kuralı onayı değildir.

- `_feature_contract` artık tek tanımdır. Python'ın önceden kullandığı son tanım ile `evaluate_symbol` gövdesi HEAD'e karşı AST olarak birebir aynı; kaldırılanlar gölgelenen tanımlardır. Sinyal, skor, risk, sağlayıcı ve kalıcılaştırma kuralları değiştirilmedi.
- Baseline uyuşmazlığı açıkça bildirildi: eski testler score-2 kabul bekliyordu, mevcut otorite `scanner/evaluate.py` farklı davranıyor. Testler bu kodu karakterize eder; yeni eşik veya politika koymaz. Score-2 reddi ve score-3 kabulü alignment 0.65/0.66/1.0 ve mevcut `min_signal_score` ayarlarıyla birlikte doğrulanır. Git blame, ilgili sabit kapının `f8bb21a0` (2026-05-19) içinde bulunduğunu gösterir; bu oturumda eklenmedi. Formal geçmiş onay izi hedefli karar kaydı aramasında bulunmadı; test geçişi bu izi ikame etmez.
- **MEASURED:** Değişiklik sonrası contract/performance suite **64 passed**; baseline suite **10 passed**; son geniş `pytest tests/ -q -k "scan or data_fetcher or evaluate" -p no:cacheprovider` **172 passed / 0 failed / 867 deselected**, 129.44 sn. Odak koşuları geniş koşunun alt kümeleridir; sayıları toplanmaz. Bu seçim bütün depo testlerini veya üretim koşullarını sertifikalandırmaz.
- **MEASURED:** Yedi Python dosyası Python 3.11 derleme, Ruff lint ve editör tanılarından geçti; scoped diff whitespace kontrolü temiz. Scanner slice'ın mevcut teknik kapısı **PASS**. Test bağımlılık uyarıları ve altı pytest uyarısı raporlandı; dependency/marker temizliği kapsam dışı tutuldu.
- Aynı mevcut image ile ağsız, salt-okunur kod/fixture ve geçici durum kullanıldı. İlk geniş komutta PowerShell argüman aktarımı pytest başlamadan başarısız oldu; standart girdiyle aynı kontrol tekrarlandı ve yukarıdaki sonuç alındı. Gerçek `.env`, sırlar, servis state'i ve donmuş araştırma çıktıları değiştirilmedi.
- **Canlı durum:** restart, 1-2 günlük 0A kampanyası, API ölçüm koşuları ve aktivasyon **NOT RUN**. Canlı bayraklar/dağıtılmış sürüm/gözlem kapsamı **UNKNOWN**; test varsayılanı canlı durum kanıtı değildir. Karışık worktree'deki diğer değişiklikler korunur; temiz ve izlenebilir yayın adayına dönüştürüldüğü iddia edilmez. Bu nedenle canlı geçiş **NO-GO** kalır; mevcut insan/yayın ve Risk & Compliance kapıları aynen geçerlidir. Hız kazancı veya bölüm kapanışı ilan edilmedi.

**Testler (yapay iş ile, gerçek tarama gerekmez):**
- Timeout'ta slot, çalışan iş bitene kadar **bırakılmaz**
- İkinci iş, ilki bitmeden **başlamaz**
- Aynı anahtar → tek iş, iki yanıt, kalıcılaştırma **bir kez**
- Farklı anahtar → birleştirilmez
- Bir bekleyenin iptali işi durdurmaz; **son** bekleyen gidince iş faz sınırında durur
- İş hata verirse tüm bekleyenler hatayı alır, takılmaz
- `ScannerAgent` çağrısı koordinatörden geçer
- Kuyruk dolu / bütçe aşılır → "meşgul" yanıtı

**Doğrulama:**
1. Yenileme senaryosu bilerek tekrarlanır. Beklenen: aynı batch için `request_id` iki, `job_id` bir; farklı batch'in yetimi `outcome=client_gone` ile erken biter; `active_jobs_at_start` hiç 1'i aşmaz
2. Protokol 3.3 ile koşular → **Blok 1'in baseline'ı**

> **Ölçüm gücü:** 5 sıcak koşu pilot kanıttır, güvenilir p95 değildir. p95 iddiası için daha fazla koşu ya da birkaç günlük kayıt gerekir. Anlam eşdeğerliği (aynı girdi → aynı çıktı) sabit girdi anlık görüntüsüyle, canlı performans API koşularıyla — **ayrı ayrı** — ölçülür.

**Beklenen (ESTIMATED):** eşzamanlılık kalkınca 200-sembol medyan ~418 → ~307-336 sn.

---

### BLOK 1 — Hazır düzeltmeler (üçü ayrı commit)

**Seviye:** B · **Bağımlılık:** Blok 0 doğrulaması (baseline)

| Adım | İş | Bayrak | Kaynak |
|---|---|---|---|
| 1.1 | **yfinance toplu çağrıya timeout** (#29) | `FINPILOT_YF_BULK_TIMEOUT_S`, varsayılan 30 | Benchmark'ta askıda kalma gözlendi |
| 1.2 | **Extract `groupby`** (#31): sembol başına `get_level_values` + `in` yerine tek geçiş | yok (semantik eşdeğer) | n^1.39 ölçüldü |
| 1.3 | **Negatif cache** (#30) | `FINPILOT_DISABLE_NEGCACHE=1` kapatır | `docs/2026-09-22-negatif-cache-tasarimi.md` |

**1.2 notu:** batch'ler 200 sembol olduğu sürece kazanç küçük (~2.9 sn). Ucuz ve risksiz olduğu için burada; asıl değeri Blok 2'de tüm evren tek çağrıda işlenirse ortaya çıkar.

> **v3.1 hedef netleştirmesi.** İncelemede "`get_level_values(0)` zaten döngü dışında" denmişti; bu **`_bulk_yf_download`** için doğru (satır ~994). Ölçtüğümüz yavaş döngü **`_prefetch_alpaca_bulk`**'ta ve orada `get_level_values(0)` **hâlâ sembol döngüsünün içinde** (satır ~886: `lvl0 = full_df.index.get_level_values(0)` → `sym in lvl0` → `full_df.loc[sym]`). Hedef bu fonksiyon. Düzeltme hem üyelik testini hem `.loc` dilimlemesini kapsar (tek geçiş `groupby(level=0)`). Eşdeğerlik testi sabit sentetik girdiyle yapılır.

**1.3 kuralları (spec'ten, kilitli):**
- Yalnızca **kesin** "veri yok" cache'lenir: HTTP 200 + ayrıştırma tamam + yanıt dolu + o sembol için bar yetersiz/yok
- **Asla:** timeout, 429, 402/403, **404**, 5xx, bağlantı hatası, exception, tamamen boş toplu yanıt
- Anahtar `(sağlayıcı, sembol, zaman dilimi)`; TTL işlem günü, üst sınır 24 saat
- Canary %5, **enjekte edilebilir seçici** (testlerde deterministik), tohum loglanır
- Kayıt alanları: `negcache_size`, `negcache_hits`, `negcache_writes`, `negcache_canary_recheck`, `negcache_canary_revived`, `negcache_write_ratio`

~~**Neden güvenli:** `evaluate.py:379` gün içi verisi yetersiz sembolleri zaten `unavailable` döndürüyor. Negatif cache sonuç kümesini değiştirmez, sadece aynı sonuca daha hızlı varır.~~

> **v3.1 düzeltmesi — bu iddia fazla kesindi.** Satır 379, eşdeğerliği yalnızca **cache'e yazıldığı anda** gösteriyor. TTL boyunca değil:
> - Saat 10:00'da yetersiz olan bir sembolün verisi 14:00'te yeterli hale gelebilir. Cache onu 14:00'te de atlarsa sonuç kümesi cache'siz duruma göre **değişir**.
> - Dolu bir toplu yanıtta eksik görünen sembol her zaman kalıcı "veri yok" değildir; kısmi yanıtlar sembol-başına hataları gizleyebilir.
>
> Canary bu riski **izler**, eşdeğerliği **kanıtlamaz**.

**1.3 için aktivasyon öncesi ön koşullar (v3.1):**

| Ön koşul | Nasıl |
|---|---|
| **Gün içi canlanma oranı** ölçülsün | Aynı 200 sembolde, sabah yetersiz olanların kaçı öğleden sonra yeterli? Bu oran TTL'i belirler. (Eskiden opsiyonel olan görev #34 artık **ön koşul**) |
| **Teyitli yazma** | Toplu yanıtta eksik sembol, tek gözlemle değil, **ardışık iki** başarılı yanıtta eksikse cache'lenir |
| **Seans sınırı** | TTL işlem gününü değil, **seans fazını** (açılış öncesi / seans / kapanış sonrası) aşamaz |
| **Testler** | canlanan kayıt silinir · seans geçişinde cache temizlenir · tek eksik gözlem yazılmaz · kısmi yanıt yazılmaz |

Bunlar sağlanmadan 1.3 **açılmaz** (kod yazılabilir, bayrak kapalı kalır).

**Testler:**
- 1.1: yavaş `yf.download` mock'u timeout'a düşer, tarama devam eder
- 1.2: eski ve yeni extraction sentetik MultiIndex üzerinde **birebir aynı** DataFrame'leri üretir
- 1.3: kesin "yok" yazılır · 404/429/timeout/boş toplu yanıt yazılmaz · TTL dolunca tekrar sorulur · canary deterministik selector ile tetiklenir · bayrak kapatınca cache tamamen devre dışı

**Doğrulama:** her alt adım sonrası odak testler; üçü bitince protokol 3.3 ile 5 koşu, Blok 0 baseline'ı ile karşılaştırma.

**Kill kriterleri (1.3):**

| Koşul | Eylem |
|---|---|
| `intraday_coverage` herhangi bir koşuda baseline min'in altında | Derhal kapat, incele |
| Shortlist üyeliği baseline'dan sağlayıcı gürültüsünün ötesinde farklı | Derhal kapat |
| Kümülatif canary ≥ 50 ve `revived_rate > 0.02` | TTL yarıya, uyar |
| `revived_rate > 0.05` | Kapat |

> %2 / %5 eşikleri **ürün politikası** — Meriç onayı gerekir. Onaylanmadan 1.3 açılmaz.

**Beklenen (ESTIMATED):** repair ~117 sn azalır → 200-sembol ~220 sn.

---

### BLOK 2 — Huni (iki aşamalı tarama)

**Seviye:** B + **ürün kararı** · **Bağımlılık:** Blok 1 doğrulaması

Aşama 1 tüm batch'e yalnızca `1d` verisiyle skor; aşama 2 yalnızca ilk %K adaya gün içi veri çeker.

| Adım | İş |
|---|---|
| 2.0 | **Recall testini doğru veriyle tekrarla.** Eylül testi `filter_score`'u dışarıda bırakmıştı (dataset'te yoktu). Canlı tarama çıktısında (`data/shortlists/*.csv`) tüm bileşenler var → günlük-only skor `filter_score` dahil hesaplanır, gerçek recall ölçülür. Offline, üretime dokunmaz. |
| 2.1 | **Tasarım kararı:** aşama 1 batch-içi mi (her 200'lük batch kendi %K'sını seçer) yoksa evren-geneli mi (önce tüm evren 1d, sonra global %K)? Batch-içi basit; evren-geneli daha doğru ama akışı değiştirir. 2.0 sonucuna göre seçilir. |
| 2.2 | **Gölge mod.** Huni hesaplanır ama çıktıyı değiştirmez; her taramada "huni olsaydı hangi adaylar kalırdı" ve örtüşme kayda yazılır. `FINPILOT_SCAN_FUNNEL=shadow` |
| 2.3 | **Gölge ölçüm:** en az 2 işlem günü, recall ve kaçan aday sayısı izlenir |
| 2.4 | **Aktivasyon** — yalnızca Meriç onayıyla. `FINPILOT_SCAN_FUNNEL=on`, `FINPILOT_SCAN_FUNNEL_PCT=<2.0'dan>` |

**Neden ürün kararı:** aşama 1'de elenen sembol aşama 2'ye hiç girmez. Eylül ölçümünde %40 genişlikte 50 adaydan 1'i kaçıyordu. Kabul edilebilir kayıp oranı teknik değil, ürün kararı.

**Beklenen (ESTIMATED):** ~220 → ~125 sn.

---

### BLOK 3 — EODHD onarım yolunda

**Seviye:** B · **Bağımlılık:** Blok 2 aktif (kota ancak huniyle yetiyor)

Kod 14 Eylül'de yazıldı: `FINPILOT_ENABLE_EODHD_BARS`, `scripts/verify_eodhd_bars.py`.

| Adım | İş |
|---|---|
| 3.1 | `verify_eodhd_bars.py` konteynerde koşulur (plan, şekil, hız) |
| 3.2 | **Kota koruması:** kayda `eodhd_calls` ve tahmini kredi; günlük sayaç belirli eşiği (ör. 8.000) aşınca EODHD atlanır, yfinance'e düşer |
| 3.3 | Bayrak açılır, protokol 3.3 ile 5 koşu |

**Kota:** 10.000/gün, intraday ~5 kredi/çağrı. Huni + negatif cache ile ~240 kredi/tarama → ~41 tarama/gün. Huni olmadan ~5 tarama/gün — **kullanılamaz**.

**Açık risk:** 22 Eylül'de bir koşu toplu 404 döndü, nedeni bilinmiyor. 3.1 bunu da sınamalı.

**Beklenen (ESTIMATED):** ~125 → ~72 sn.

---

### BLOK 4 — Arka planda veri deposu (kapsam dışı, yalnızca tasarım)

Tarama sağlayıcıyı beklemeden yerel snapshot'tan okur; arka plan yenileyici depoyu doldurur. En büyük kazanç (~%85, ESTIMATED), en büyük iş: yeni gün içi veri katmanı, tazelik sözleşmesi, gölge doğrulama. **Bu planın uygulama kapsamında değil.** Blok 0-3 bittikten sonra ayrı tasarım belgesi ve ayrı onayla.

---

## 5. Toplam beklenti (hepsi ESTIMATED)

| Sonrası | 200-sembol batch | Tam evren (~9 batch) |
|---|---|---|
| Şimdi (eşzamanlılıkla) | ~415 sn | ~50-65 dk |
| Blok 0 | ~307-336 sn | ~45-50 dk |
| Blok 1 | ~220 sn | ~33 dk |
| Blok 2 | ~125 sn | ~19 dk |
| Blok 3 | ~72 sn | ~11 dk |

Her satır, o blok ölçülene kadar tahmindir. Ölçüm gelince bu tablo gerçek sayılarla güncellenir.

---

## 6. Kapılar ve sahiplik

| Kapı | Ne gerekir | Kim |
|---|---|---|
| Planın onayı | Bu belge | Meriç |
| Blok 0 → 1 | Blok 0 testleri yeşil + yenileme senaryosu + 5 koşu baseline | Meriç (restart+ölçüm), Claude (değerlendirme) |
| 1.3'ün açılması | %2/%5 kill eşiklerinin ürün onayı | Meriç |
| Blok 1 → 2 | Blok 1 ölçümü + çıktı eşdeğerliği | Meriç + Claude |
| Huni aktivasyonu (2.4) | Gölge ölçüm + kabul edilebilir kayıp oranı | **Meriç (ürün kararı)** |
| Blok 3 | 3.1 doğrulaması + kota koruması | Meriç + Claude |

---

## 7. Bu planın yapmadıkları

- Sinyal/skor formülünü değiştirmez (`momentum_ratio`, `alignment_ratio` dahil)
- Gün içi zaman dilimlerini kaldırmaz — giriş fiyatı, ATR, spread ve uygunluk kapısı 15m'den geliyor (`evaluate.py:379, 419, 420`)
- Flag kararlarını (DEFERRED) değiştirmez
- Blok 4'ü uygulamaz
