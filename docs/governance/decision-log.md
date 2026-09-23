# FinPilot — Merkezi Karar Logu

_CLAUDE.md Bölüm 3 formatı: her önemli karar buraya, dağınık dosyalara gömülmez._

[2026-09-22] — INTRADAY COVERAGE GÖZLEM SAYACI (Level B, uygulama onayı)
Layer: Observability / Data providers
Decision Level: B. Uygulama onayı verildi; negatif cache henüz uygulanmadı.
Değişiklik: Prefetch tamamlandıktan sonra 15m ve 1h için
`MIN_HISTORY_BARS` eşiğini geçen sembol sayısı `intraday_coverage` olarak
ölçülüyor ve scan timing JSONL kaydına yazılıyor. Sayaç resetlenebilir; Alpaca,
bulk-yfinance ve per-symbol fallback yollarının tamamı gözlemleniyor.
Kapsam dışı: cache, sağlayıcı seçimi, timeout, skor, sinyal ve sonuç şeması.
Doğrulama: `35 passed`; ilgili Python dosyaları derlendi; diagnostics temiz.
Sonraki adım: cache kapalı 200 sembollük baseline penceresi.
Status: applied - observation only; negative cache implementation pending.

[2026-09-22] - FAZ 1 RECREATE SONRASI STAGE OLCUMU TAMAMLANDI (Level A, salt olcum)
Layer: Observability / Data providers
Decision Level: A. Saglayici zinciri, sinyal mantigi ve uretim davranisi DEGISTIRILMEDI.

== KAMPANYA ==
`FINPILOT_SCAN_STAGE_TIMING=1` ile `api` servisi `--force-recreate` sonrasi,
ayni 200 sembolle tek persistent helper process icinde 6 seri kosu yapildi.
Scheduler kosu sirasinda durduruldu; ilk soguk kosu analiz disi birakildi.
JSONL kayitlari: `data/distribution/scan_timing.jsonl`, satir 335-340.

  Kosu | Satir | total_s | persist_s | yf_fallback | stage event
      1 |   335 |  371.58 |      0.47 |         198 | 1513 (soguk)
      2 |   336 |  376.86 |      0.31 |         198 | 1513
      3 |   337 |  373.35 |      0.19 |         198 | 1513
      4 |   338 |  336.64 |      0.21 |         198 | 1513
      5 |   339 |  180.67 |      0.30 |          81 | 1396
      6 |   340 |  313.04 |      0.31 |         117 | 1432

Tum kayitlar `symbols=200`, `result_symbols=200`, `experiment_arm=A_baseline`,
`alpaca_total_failure=false`, `alpaca_disabled=false`.

== ANALIZ (KOSU 2-6) ==
- `total_s` medyan 336.64 sn; aralik 180.67-376.86 sn; p95 376.158 sn.
- `persist_s` medyan 0.30 sn; kalicilastirma 200 sn farkinin nedeni degil.
- `prefetch.repair` 141.924-335.024 sn, medyan 305.025 sn; toplam sure oynakliginin
  ana gozlenen katmani repair/yfinance yoludur.
- `alpaca_miss` her kosuda ayni: 15m=109, 1h=93, 1d=8. Bu, 200 sembol evreninde
  timeframe bazli Alpaca kapsamasini sirasiyla %45.5, %53.5 ve %96.0 yapar.
- `yf_bulk_symbols=210`, 109+93+8 toplamidir; benzersiz sembol sayisi degildir.
- Stage event sureleri paralel ve ic ice oldugu icin stage toplamlarinin yuzdeleri
  duvar saati olarak toplanmadi. `prefetch.repair` dis timer olarak 200 sn'lik
  farki aciklayan en guclu kanittir; ic yfinance request event'leri bunun altindadir.

Benchmark'taki Alpaca `39/40` sonucu bu kayitlarla celismiyor: benchmark 40 sembolluk
farkli bir orneklemde provider kapsamasini olcuyor; production kaydi 200 sembolluk
evrende, repair oncesi timeframe bazli yetersiz tarih sayisini olcuyor. Sembol-bazli
esdegerlik iddiasi kurulamaz. Saglayici degisikligi karari verilmedi.

== KAPATMA ==
Olcum tamamlaninca `.env` icindeki gecici flag `FINPILOT_SCAN_STAGE_TIMING=0` yapildi
ve yalnizca `api` servisi force-recreate edildi. Dogrulama: `TIMING=0`, `/ready=200`,
timing logu 340 satir; recreate sonrasi yeni olcum satiri yazilmadi. Scheduler standart
startup ile yeniden aktif oldu (`running=true`, `cycle_count=0`).
Status: applied - Level A measurement closure.

[2026-09-22] - AUTO-WATCHLIST IMPORT DUZELTMESI (Level B, pending)
Layer: Engineering / API
Decision Level: B. Uretim API yuzeyine dokunan degisiklik; Meric onayi bekliyor.
Bulgu: `api/routers/scan.py` icindeki `from routers.watchlist` import'u
`api.main` giris noktasinda cozulmedigi icin her taramada `No module named
'routers'` ile auto-watchlist akisini pasif birakiyordu.
Degisiklik: Import yolu `from api.routers.watchlist` olarak duzeltildi.
Dogrulama: `api.routers.scan` import kontrolu gecti; `tests/test_watchlist_db.py`
25 test gecti; `get_errors` scan.py icin hata bildirmedi.
Kapsam: Scanner mantigi, sinyal kurali, veri saglayici, scheduler ve kullanici
verisi degistirilmedi. Bu kayit, duzeltmenin teknik olarak hazir oldugunu bildirir;
Level B onayi olmadan karar kapanmis sayilmaz.
Status: pending - Meric approval required.

[2026-09-22] - FAZ 5R KESISIM OLCUMU (Level A, salt olcum)
Layer: Observability / Data providers
Decision Level: A. Saglayici zinciri DEGISTIRILMEDI; bu kayit yalnizca kapsama
kesisimini olcer.
Kapsam: Uretim `load_symbols(limit=200)` sonucu olan ayni 200 sembol, Alpaca ve
EODHD, tek tur; benchmark `--skip-yfinance` ile calistirildi. Yfinance cagrilmadi.
Son kosu: Alpaca 17.21 sn, EODHD 25.51 sn; API anahtarlari mevcut, Alpaca devre
disi degil.

  Timeframe | Alpaca | EODHD | Kesisim | EODHD ek | Birlesim | Hicbiri/yf
  15m       | 91/200  | 148/200 | 90     | 58       | 149/200  | 51
  1h        | 107/200 | 166/200 | 103    | 63       | 170/200  | 30

Yorum: EODHD, Alpaca'nin kapsamadigi sembollerin bir kismini tamamliyor fakat
buyuk kesisim nedeniyle yfinance repair yolu tamamen ortadan kalkmiyor. 15m'de
51, 1h'te 30 sembol iki saglayicida da yeterli history saglamadi. EODHD sonucu
tek tur ve ag/veri kosullarina duyarlidir; provider degisikligi veya 336->62 sn
projeksiyonu bu kayittan kararlastirilmaz.
Status: applied - Level A measurement.

[2026-09-22] - YFINANCE BULK TIMEOUT RISKI (Level B, pending)
Layer: Engineering / Scanner resilience
Decision Level: B. Uretim scanner koduna timeout/cancel degisikligi yapmak icin
Meric onayi bekleniyor.
Bulgu: `scanner/data_fetcher.py::_bulk_yf_download` icindeki `yf.download`
cagrisi timeout argumani vermiyor. Bulk cagri agda asilirsa endpoint'in
`_SCAN_TIMEOUT_SECONDS=600` siniri istegi sonlandirabilir, ancak worker/thread
ve alttaki HTTP cagri ayni anda guvenilir sekilde iptal edilmis sayilmaz.
Kanıt: 200 sembol production-universe benchmark'inda yfinance kolu timeout'suz
uzun sure calisti; Alpaca/EODHD kesisim kosusu `--skip-yfinance` ile bu riski
izole ederek tamamlandi. Bu benchmark bir production scan degildir.
Onaylanmayan kapsam: timeout degeri, retry/cancel semantigi, thread havuzu veya
endpoint sozlesmesi degistirilmedi.
Status: pending - Meric approval required.


[2026-09-23] — HUNI TASARIMI OLCULDU: %40 genislikte %98 recall (Level A, offline analiz)
Layer: Research / Architecture
Decision Level: A. Uretime DOKUNULMADI; offline dataset analizi.
Script: research/funnel_overlap_test_2026_09_23.py, research/funnel_recall_test_2026_09_23.py
Veri: full_universe_enriched_eod_only.csv, 57 gun, 40.014 satir, gun-basi medyan 860 sembol

== SORU ==
Meric'in onerisi: taramayi ikiye bol — once herkese gunluk veri, sonra adaylara
gun ici. Bu bir HIZLANDIRMA mi yoksa DAVRANIS DEGISIKLIGI mi?

== BULGU 1: "ilk-N'i al" YETMEZ ==
Gunluk-only skorun ilk-N'i, tam skorun ilk-N'ini yakalamiyor:
  ilk-10: %20 ortusme | ilk-25: %32 | ilk-50: %41
Rastgele kontrole gore 6.8x-16x daha iyi (yani sinyal VAR), ama tam degil.
Sinirdaki tie yogunlugu dusuk (%0.4-1.0), yani sonuc esitliklerden gelmiyor.

== BULGU 2: "GENIS HAVUZ SEC, SONRA DARALT" CALISIYOR ==
recall@K (hedef: tam skorun ilk-50'si):
  K=%10 -> %62   K=%20 -> %76   K=%30 -> %90   K=%40 -> %98   K=%50 -> %100
=> 1. asama evrenin %40'ini gecirirse dogru adaylarin %98'i yakalaniyor
   (50 adaydan 1'i kaciyor).

== PERFORMANS PROJEKSIYONU (ESTIMATED) ==
  Simdi                      : repair 274.6 sn -> toplam 336.6 sn
  Huni %40                   : repair ~110 sn  -> toplam ~172 sn  (2.0x)
  + negatif cache            : repair ~63 sn   -> toplam ~125 sn  (2.7x)
  + EODHD (kota ici)         : repair ~10 sn   -> toplam ~72 sn   (4.7x)

== KOTA COZULDU ==
EODHD gunluk kota = 10.000 (Meric). Intraday ~5 kredi/cagri.
  Huni YOK  : 200 sembol x 2 tf = 400 cagri x 5 = 2.000 kredi -> gunde 5 tarama
  Huni %40 + negcache: ~48 slot x 5 = 240 kredi -> gunde 41 tarama
=> EODHD ancak HUNI VE NEGATIF CACHE ILE BIRLIKTE uygulanabilir. Tek basina
   mevcut hacimde kota duvarina carpar. Bu, FAZ 5R'nin on kosulunu degistirir.

== BU TEST HUNIYI OLDUGUNDAN KOTU GOSTERIYOR ==
Kurulan "gunluk-only" skor `filter_score`'u da disarida birakti (dataset'te yok).
Ama filter_score (volume_spike + price_momentum + trend_strength) GUNLUK BARDAN
hesaplanabilir, yani gercek 1. asamada MEVCUT olurdu.
=> Gercek huni bu testten DAHA IYI recall verir; %40 muhtemelen fazla genis.

== SINIR ==
Test "composite_score'un ilk-50'sini koruyor muyuz" sorusunu cevapliyor. O skor
arastirma hattinda rastgeleden ayirt EDILEMEDI. Huni mevcut DAVRANISI koruyor
(dogru muhendislik hedefi) ama secimin kendisini iyilestirmiyor. Iki ayri mesele.

== SIRA ETKISI ==
#31 (extract O(n^1.39)) artik huninin ON KOSULU: 1. asama tum evreni o dongudden
gecirecek. 200'de 2.9 sn, 1.900'de ~66 sn.

---

[2026-09-22] — GERI CEKME: "hayatta-kalan yanliligi" HIPOTEZI CURUDU (Level A, duzeltme)
Layer: Observability / Methodology
Decision Level: A. Ayni gun girilen bir onceki kaydin duzeltmesi.

== TEST VE SONUC ==
Hipotez: timing log kesik bir dagilim, cunku 600 sn timeout'a takilan taramalar
`_append_scan_timing_log`'a ulasmadan HTTPException firlatiyor.
Test:  grep -c 'Scan timed out' logs/api.log
Sonuc: **0**. Son 20 timeout kaydi da yok.
=> Uretim taramalari 600 sn altinda bitiyor. Dagilim KESIK DEGIL.
=> "336.6 sn hayatta kalanlarin medyani" iddiasi GERI CEKILIYOR.

Acik kalan: log rotasyonu veya farkli log yolu ihtimali elenmedi. Ama en basit
aciklama hipotezin YANLIS olmasidir ve oyle kabul ediliyor.

== ETKI: ONCEKI ANALIZ SAGLAM ==
Timing log guvenilir oldugu icin uzerine kurulan her sey gecerli kalir:
  prefetch.repair = %81.6          GECERLI
  Amdahl tavani 5.4x               GECERLI
  89 slot x ~1.31 sn = ~117 sn     GECERLI
  negatif cache tahmini            REVIZYONA GEREK YOK

== ACIKLANAMAYAN GOZLEM (karar verdirmeyecek) ==
Ayni gun iki soguk olcum celisiyor:
  API uzerinden, restart sonrasi (soguk) : 385.8 sn
  Taze `docker exec` surecinde (soguk)   : 20+ dk, tamamlanmadi
Cache-sicakligi aciklamasi TUTMUYOR — restart sonrasi API de soguktu.
Aday nedenler (HICBIRI DOGRULANMADI): ayni konteynerde API ile CPU/ag cekismesi,
taze surecte TLS/keep-alive kurulumu, stage timing yuku.
KARAR: bu tek anomali gozlemi URETIM YOLUNDA uretilmedi ve karar verdirmez.
API uzerinden tekrarlanana kadar acik birakiliyor.

== DEGISMEYEN KURAL ==
Baseline, karsilastirmayla ve uretimle AYNI YOLDAN (API) alinmalidir.

---

[2026-09-22] — (GERI CEKILDI, yukari bkz.) KRITIK: TIMING LOG'U HAYATTA-KALAN YANLILIGI TASIYOR (Level A, bulgu)
Layer: Observability / Methodology
Decision Level: A. Kod degismedi; baseline TAMAMLANAMADI.

== NE OLDU ==
Negatif cache baseline'i icin 200 sembollük 5 kosu planlandi. Auth zincirini
atlamak amaciyla `evaluate_symbols_parallel` TAZE bir `docker exec` surecinde
dogrudan cagrildi. ILK (cold) kosu 20+ DAKIKA surdu ve hic tamamlanmadi;
yalnizca repair/veri-eksikligi uyarilari uretti. Kontrollü olarak durduruldu.

== BULGU 1: TIMING LOG'U KESIK BIR DAGILIM ==
api/routers/scan.py: executor 600 sn'de donmezse TimeoutError -> HTTPException
firlatilir ve `_append_scan_timing_log` HIC CAGRILMAZ.
=> scan_timing.jsonl'de YALNIZCA 600 sn'den hizli biten taramalar var.
=> "336.6 sn medyan" HAYATTA KALAN taramalarin medyanidir. Dagilimin sag kuyrugu
   kesilmis ve biz kesik dagilima bakiyorduk.
ETKI: `prefetch.repair = %81.6` SAGLAM kalir (ayni kosu icinde olculmus ORAN,
cache durumundan bagimsiz). Ama MUTLAK sayilar ve negatif cache'in ~117 sn
tahmini sicak-cache varsayimina dayaniyor; soguk durumda kazanc daha buyuk olabilir.

== BULGU 2: OLCULEN SAYILAR BUYUK OLCUDE SICAK-CACHE ==
`_cache_data(ttl_seconds=CACHE_TTL_SECONDS)` SUREC-ICI. API uzun omurlu ve arka
arkaya tarama yapiyor -> cache sicak. `docker exec` ile acilan TAZE surecte
hicbir sey yok. Faz 1'in 336.6 sn'si buyuk olcude sicak-cache rakami.
Market-aware TTL (300 sn piyasa aciksa / 3600 sn kapaliysa) bu etkiyi guclendiriyor.

== METODOLOJIK HATA (tekrar) ==
Baseline TAZE SURECTE, karsilastirma ise API uzerinden alinacakti. Bu kiyaslanamaz
— FAZ 1'de yapilan hatanin AYNISI (yanlis ortamda olcum), ikinci kez.
KURAL: baseline, karsilastirmayla AYNI YOLDAN ve uretimle AYNI YOLDAN alinmalidir.
Auth'u atlamak icin evaluator'i dogrudan cagirmak karsilastirilabilirligi bozar.

== SIRADAKI (ucuz ve onemli) ==
  grep -c 'Scan timed out' logs/api.log
Bu, hayatta-kalan yanliliginin BUYUKLUGUNU dogrudan verir. Sayi anlamliysa:
  (1) uretimde taramalar fiilen basarisiz oluyor ve bunu bilmiyorduk,
  (2) gercek performans tablosu dusunulenden kotu -> negatif cache (#30) ve
      yfinance timeout'u (#29) daha da gerekli.

== DURUM ==
Negatif cache UYGULANMADI. .env, servisler, kaynak kod degismedi.
Baseline API uzerinden yeniden alinmali.

---

[2026-09-22] — UCUNCU CAKISMA: intraday_coverage IKI KEZ UYGULANDI (Level B, geri alindi)
Layer: Observability / Process
Decision Level: B (kod); Claude'un eklemesi KALDIRILDI, paralel surecin surumu korundu.

== NE OLDU ==
Paralel surec `_note_intraday_coverage()`'i `prefetch_symbols_multi_timeframe`'in
UC donus yolunda da (data_fetcher.py:1281, 1333, 1381) uygulamis, testleriyle
birlikte scan.py'ye baglamisti. Claude ayni ozelligi bagimsiz olarak ikinci kez
yazdi (`note_intraday_coverage`, evaluate.py'den tek cagri).
SONUC: data_fetcher.py'de IKI `intraday_coverage()` tanimi. Ikincisi birincisini
golgeledi; Claude'un evaluate.py cagrisi HIC OKUNMAYAN bir degiskene yaziyordu.
Sessiz bir olcum hatasi — negatif cache'in kill metrigi bozuk olurdu.

== KOK NEDEN: CLAUDE ==
Edit araci acikca uyardi: "the file had been modified on disk since you last read
it — read it before edits that depend on surrounding content." Claude uyariyi
gordu ve yine de dosyayi yeniden OKUMADAN yazdi.

== KARAR ==
Claude'un surumu KALDIRILDI. Paralel surecinki korundu — uc donus yolunu birden
kapsadigi icin hangi yol kosarsa kossun olcum aliniyor; Claude'un tek-nokta
surumu daha dar. Kaldirilan yerlere aciklayici NOT birakildi ki ucuncu kez
yazilmasin.

== DESEN: BU OTURUMDA UCUNCU CAKISMA ==
  1. `_note_alpaca_total_failure()` return altinda olu kod (paralel surec yazdi,
     Claude buldu ve duzeltti)
  2. `_note_yf_fetch()` cift sayim (Claude plandan sapti, belgeyi guncellemedi,
     paralel surec bayat talimata uydu)
  3. `intraday_coverage` cift uygulama (Claude diskteki degisikligi okumadi)
UCUNU DE TESTLER veya grep YAKALADI — sans eseri degil. Ama ucu de ayni koke
isaret ediyor: IKI AJAN AYNI DOSYALARDA, PAYLASILAN DURUM KONTROLU OLMADAN.

== ONERI (uygulanmadi) ==
Kod yazmadan once ilgili dosyanin GUNCEL halini okumak, bu repoda opsiyonel bir
nezaket degil zorunluluk. Ozellikle: arac "dosya diskte degisti" uyarisi
verdiginde yazma islemi DURDURULMALI ve dosya yeniden okunmalidir.

---

[2026-09-22] — ANALIZ: KESISIM SONUCU + YENI KALDIRAC "NEGATIF CACHE" (Level A, yorum)
Layer: Analysis / Data providers
Decision Level: A. Karar VERILMEDI, kod DEGISMEDI.
Girdi: uretim 200 sembolu ile kesisim olcumu (--skip-yfinance, 1 tur)

== KESISIM TABLOSU ==
  TF   Alpaca EODHD Kesisim EODHD-net Birlesim Hicbiri
  15m     91    148      90        58  149/200      51
  1h     107    166     103        63  170/200      30

== BULGU 1: EODHD INTRADAY'DE ALPACA'YI NEREDEYSE TAMAMEN KAPSIYOR ==
Alpaca'nin TEK BASINA kattigi: 15m'de 1 sembol, 1h'te 4 sembol.
=> Intraday icin EODHD ~ Alpaca'nin ust kumesi. Mimari sadelestirme imkani.
   ANCAK Alpaca TOPLU (1 cagri), EODHD SEMBOL-BASINA (N cagri) — kredi maliyeti
   acisindan Alpaca'yi once denemek hala mantikli.

== BULGU 2: PROJEKSIYON ASAGI CEKILDI (Claude'un 5.4x iddiasi fazla iyimserdi) ==
ESTIMATED (dogrusal olcekleme varsayimi, repair bulk+per-symbol karisimi
oldugu icin sapabilir):
  Su an     : 210 eksik slot -> 274.6 sn repair -> ~1.31 sn/slot
  EODHD sonrasi eksik: 15m 51 + 1h 30 + 1d 8 = 89 slot -> ~116 sn
  + EODHD'nin kendi maliyeti ~20 sn
  => repair 274.6 -> ~136 sn ; toplam 336.6 -> ~198 sn
  => 1.7x, 5.4x DEGIL. Tavan (Amdahl) ile GERCEKLESEBILIR kazanc farkli.

== BULGU 3 (YENI KALDIRAC): NEGATIF CACHE — saglayicidan BAGIMSIZ ==
Birlesim, kapsanabilirligin TAVANI. 15m'de 51, 1h'te 30 sembolu HICBIR saglayici
vermiyor. Sistem her taramada bu 81 slot icin gidip soruyor, ~1.31 sn oduyor ve
"yok" cevabini YENIDEN KESFEDIYOR.
  81 x 1.31 ~ 106 sn / tarama, tamamen bosa.
ONERI (uygulanmadi, Level B): TTL'li negatif cache — "bu sembolun 15m verisi yok"
bilgisini tut, gunluk yenile (yeni listelenen / dusuk hacimli gunler icin TTL sart).
Saglayici degisikligi YOK, kapsam kaybi YOK (zaten alinamayan veri kaybedilmiyor).

== IKI KALDIRACIN TOPLAMI (ESTIMATED) ==
  EODHD repair yolunda : 121 slot doldurur -> ~158 sn
  Negatif cache        :  81 slot hic sorulmaz -> ~106 sn
  Toplam 202/210 slot  -> 336.6 sn -> ~90-110 sn
Negatif cache TEK BASINA EODHD'ye yakin kazanc veriyor ve HICBIR saglayici
karari gerektirmiyor. Bagimsiz uygulanabilir.

== OLCUM NOTU ==
Kapsam sayilarinda gurultu var: EODHD iki kosu arasinda 148->149, 166->170.
Tek turluk kapsam olcumleri +/- birkac sembol oynuyor.

== KARAR VERILMEDI ==
Ne saglayici zinciri ne negatif cache uygulandi. Ikisi de Level B ve ayri onay ister.

---

[2026-09-22] — ANALIZ: DARBOGAZ BULUNDU — prefetch.repair %81.6 (Level A, yorum)
Layer: Observability / Analysis
Decision Level: A. Karar VERILMEDI, saglayici DEGISTIRILMEDI.
Girdi: Faz 1-tekrar kampanyasi (6 kosu, ilki soguk-atildi), scan_timing.jsonl 335-340

== AMDAHL SONUCU ==
  prefetch.repair kosu basina : 1373.241 / 5 = 274.6 sn
  total_s medyan              : 336.64 sn
  PAY                         : %81.6
  Geriye kalan her sey        : ~62 sn
=> Repair tamamen cozulurse 336 sn -> ~62 sn (5.4x tavan).
   Baska katmana dokunmanin kayda deger getirisi YOK.
   persist_s medyan 0.30 sn -> H1 (kalicilastirma) kesin olarak CURUK.

== 10x VARYANS GIZEMI COZULDU (14 Eylul'den beri acikti) ==
Kosu 2 vs Kosu 5 dogal deneyi:
  yf_fallback      198 -> 81      (delta -117)
  prefetch.repair  335.0 -> 141.9 (delta -193.1 sn)
  total_s          376.9 -> 180.7 (delta -196.2 sn)
delta_repair ~ delta_total (193 ~ 196) -> toplam suredeki degisimin TAMAMINA
YAKINI repair'den geliyor. Sembol basina maliyet 193.1/117 = ~1.65 sn.
=> Varyansin tek degiskeni: kac sembol per-symbol yfinance kuyruguna dusuyor.

== MEKANIZMA: REPAIR ICINDE IKINCI KATMAN ==
alpaca_miss 210 timeframe-slot (15m:109, 1h:93, 1d:8).
Toplu yfinance bunlari 3 istekte karsilamaya calisiyor (~110 sn/kosu,
fetch.request/bulk_yfinance 550.145/5). AMA 198 sembol YINE DE per-symbol
fallback'e dusuyor -> toplu cagri bosluğu dolduramiyor, kod alt kademeye iniyor.
Repair ici kabaca: toplu ~110 sn + per-symbol stragglerlar ~158 sn.
ASIL KATIL per-symbol katmani.

== IKINCIL GOZLEMLER ==
  prefetch.alpaca  : 179.337/5 = 35.9 sn/kosu (~%11) — makul
  retry.attempt    :  65.016/5 = 13.0 sn/kosu — Alpaca retry'lari sessizce
                     13 sn yiyor, ikincil ama gozden kacmasin
  evaluation.symbol: 535.035/5 = 107 sn TOPLAM is, 32 worker'da paralel;
                     duvar saati katkisi <= 62 sn (kalan butce)
  indicator.compute: 146.801/5 = 29.4 sn toplam is, paralel

== GOREV #28 (alpaca_miss celiskisi) — COZULDU AMA BIR ZAYIFLIK ACIGA CIKTI ==
Celiski YOK: farkli orneklem, ve alpaca_miss timeframe-SLOT sayisi, benzersiz
sembol degil. ANCAK buyukluk farki duruyor: uretimde 210/600 = %35 miss,
benchmark'ta 1/40 = %2.5. 14 kat.
=> CLAUDE'UN BENCHMARK ORNEKLEMI URETIMI TEMSIL ETMIYOR. "Kucuk hisse" niyetiyle
   secilen PLTR/SOFI/GME aslinda oldukca likit. Bu, benchmark'in EODHD kapsam
   sonucunu (39/40) da supheli kilar — gercek uretim evreninde olculmedi.

== FAZ 5R ICIN GEREKCE OLUSTU, AMA TEK KONTROL KALDI ==
Benchmark verisiyle: 210 slot icin EODHD ~7.6 sn (80 cagri 2.91 sn -> 210 cagri),
yfinance ise ~274 sn. Tam evrende (~2.000 slot) EODHD ~73 sn.
ONERI (uygulanmadi): repair yolundaki yfinance -> EODHD. Alpaca birincil kalir,
yfinance son care olarak durur ama pratikte cagrilmaz.
SON KONTROL: benchmark URETIMIN KENDI 200 SEMBOLUYLE tekrarlanmali. Aksi halde
EODHD'nin gercek kapsami bilinmeden mimari degistirilmis olur.

== OPERASYON ==
.env'de FINPILOT_SCAN_STAGE_TIMING=0'a geri alindi (log sismesini onlemek icin,
kampanya bitti). API /ready 200. Scheduler running, cycle_count=0.

---

[2026-09-22] — FAZ 2R.3 KAPANDI + SAGLAYICI KIYASLAMASI (Level A, salt olcum)
Layer: Observability / Data providers
Decision Level: A. Saglayici secimi DEGISTIRILMEDI, sinyal/flag/uretim DEGISMEDI.

== FAZ 2R TAMAMEN KAPANDI ==
Canli uretim taramasi (200 sembol, restart sonrasi):
  alpaca_total_failure = FALSE  -> Alpaca URETIMDE GERCEKTEN DEVREDE
  experiment_arm = A_baseline, result_symbols = 200, hata = 0, persist = 0.2 sn
  yf_fallback = 48 (sembol-basina), yf_bulk = 2 istek / 29 sembol
  total_s = 385.8 sn
  stage_timing = 0 event (beklenen — recreate yapilmadi)
=> FAZ 0 olcum alanlari URETIMDE CALISIYOR. Kapi kapandi.

== SAGLAYICI KIYASLAMASI (scripts/provider_benchmark.py, 40 sembol, 3 tur) ==
  Saglayici | Medyan  | Aralik        | 15m   | 1h    | 1d
  Alpaca    |  6.73 s | 5.67-8.13     | 39/40 | 39/40 | 39/40
  EODHD     |  2.91 s | 2.82-8.25     | 39/40 | 39/40 | (zincire bagli degil)
  yfinance  | 43.79 s | 27.07-44.82   | 39/40 | 39/40 | 39/40
Kapsam DENK oldugu icin sure kiyasi mesru (scriptin kurali saglandi).
=> yfinance, AYNI kapsam icin EODHD'den ~15x, Alpaca'dan ~6.5x YAVAS.

== CLAUDE'UN CURUYEN IDDIASI (geri cekiliyor) ==
2026-09-21'de "Alpaca'nin zayif oldugu yer tam da 15m/1h, yfinance'i cikarmak
kapsama bosluğu birakir" denmisti. BENCHMARK BUNU CURUTUYOR: Alpaca 15m ve 1h'te
39/40 — ustelik orneklemde bilerek kucuk isimler vardi (BBAI, SOUN, WULF, CIFR,
HIVE, BTBT, GEVO, FCEL, PLUG, NKLA). Korkulan bosluk bu orneklemde YOK.
Iddia `alpaca_miss` desenine dayandirilmisti.

== YENI ACIK SORU (onemli) ==
Uretim neden onlarca `alpaca_miss` raporluyor da benchmark 39/40 gosteriyor?
Ayni MIN_HISTORY_BARS esigi, ayni (interval, days) ciftleri kullanildi.
Olasi nedenler (TEST EDILMEDI): uretim evreninin (200) benchmark'tan (40) daha
kotu isimler icermesi, piyasa saati/seans farki, repair yolunun farkli lookback
kullanmasi. CEVAPLANMADAN saglayici mimarisi kesinlestirilmemeli.

== OLCEKLEME TUZAGI (ham siralama yaniltici) ==
EODHD `_bulk_eodhd_intraday` SEMBOL BASINA cagri (16 worker paralel).
Alpaca TOPLU — sembol sayisindan bagimsiz, timeframe basina 1 cagri.
  EODHD : 80 cagri / 16 worker ~ 5 parti x 0.58 sn = 2.91 sn
          -> CAGRI SAYISIYLA DOGRUSAL. 1.900 sembolde 3.800 cagri ~ 138 sn
             (+ ~5 kredi/cagri kota maliyeti)
  Alpaca: 1.900 sembolde HALA 3 cagri; yuk buyur, cagri sayisi sabit ~ 30-60 sn
=> EODHD 40 sembolde KAZANIYOR, 1.900 sembolde buyuk olasilikla KAYBEDIYOR.
   Ham medyan siralamasi tek basina mimari karar icin KULLANILAMAZ.

== ACIKLANAMAYAN SURE ==
385.8 sn'nin tamami hesaba katilamiyor. Kaba tahmin: Alpaca ~30 sn (200 sembole
olceklenmis), yfinance ~150 sn (48 sembol-basina + 2 toplu) -> ~200 sn ACIKTA.
Bunu yalnizca stage timing cozer. TEK recreate gerekiyor.

== KARAR VERILMEDI ==
Saglayici zinciri DEGISTIRILMEDI. Bulgular "Alpaca birincil (toplu, iyi
olcekleniyor) / EODHD bosluklar icin / yfinance son care" yonunu DESTEKLIYOR
ama acik soru (alpaca_miss celiskisi) ve olcekleme tuzagi cozulmeden
FAZ 5R uygulanmayacak.

---

[2026-09-22] - RESEARCH-X/H4C information-loss preregistration locked (Level A)
Layer: Research / Governance
Level: A (read-only research preregistration; production and locked OOS unchanged)
Context: H4B closed as MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS and left official production ranking resolution as DEFINITION_REQUIRED with historical production ordering NOT RECONSTRUCTED. H4C is scoped strictly to the reconstructable composite_score <-> legacy_quality_score mapping; it examines measurable information loss between the two score values only and never assumes production ordering.
Change: No score formula, ranking source, scanner, configuration, database, scheduler, publication behavior, or user-facing surface was changed. The preregistration header fixes Production ordering = UNKNOWN / NOT RECONSTRUCTED and Official production ranking resolution = DEFINITION_REQUIRED. After user review the null control was corrected to a scan-date-preserving permutation (the (symbol, scan_date) grouping is singleton after dedup), tie-internal proxy dispersion (TIE_INTERNAL_PROXY_VARIATION) was made the primary evidence separate from monotonicity violation, the verdict set was fixed to four values, and INFORMATION_LOSS_SUPPORTED was recentered on observed tie-internal dispersion vs the permuted-null 95% upper band.
Impact: Preregistration APPROVED / LOCKED; this approves only execution of the pre-defined test, not any result. Verdict set: INFORMATION_LOSS_SUPPORTED / INFORMATION_LOSS_NOT_SUPPORTED / INSUFFICIENT_DATA / INPUT_MISMATCH. No verdict asserts anything about production ranking; a positive verdict means observable information divergence in the mapping, not production information loss. H2/H4A/H4B verdicts unchanged; H4C NOT_STARTED -> PREREG_LOCKED.
Status: applied - Level A preregistration locked before runner execution.
Evidence: `reports/research_x_h4c_information_loss_preregistration_2026-09-22.md`; canonical export SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`; H4B artifact `data/backtest_out/research_x_h4b_ranking_mapping_2026-09-21.json`.

---

[2026-09-21] - RESEARCH-X/H4B production ranking mapping reconstruction completed (Level A)
Layer: Research / Governance
Level: A (read-only forensic research; production and locked OOS unchanged)
Context: H4A established structural composite-score compression but deliberately left official production ranking resolution as DEFINITION_REQUIRED. H4B traced the current score-source branch, candidate eligibility, public snapshot ordering, summary/alert ordering, tie behavior, and historical field coverage against the canonical EOD-only export.
Change: No score formula, ranking source, scanner, configuration, database, scheduler, publication behavior, or user-facing surface was changed. Under the observed default flag value `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0`, current evaluator code selects `legacy_quality_score` for `ranking_score`; the override branch selects `composite_score`. Public and summary ordering remain separate multi-key paths, and neither has an explicit final tie-breaker.
Impact: H4B verdict is `MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS`. Code-level source selection is reconstructable, but exact historical ranking values and final public order are not: the canonical export does not persist `ranking_score`, `legacy_quality_score`, or `ranking_method`, and 28 of 40,014 rows lack RVOL for the descriptive legacy proxy. Official production ranking resolution remains `DEFINITION_REQUIRED`. This does not relabel H4A compression as ranking failure and does not establish predictive or economic failure. H4C remains deferred until the resolution definition is clarified.
Status: applied - Level A research-only audit complete.
Evidence: `research/research_x_h4b_ranking_mapping_2026_09_21.py`, `data/backtest_out/research_x_h4b_ranking_mapping_2026-09-21.json`, `reports/research_x_h4b_ranking_mapping_2026-09-21.md`; canonical export SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`; validation: ranking guard 8 passed, prepublish gate 13 passed, deterministic rerun confirmed.

---

[2026-09-21] — RESTART YAPILDI + OPERASYONEL DERS: restart != recreate (Level B)
Layer: Operations / Observability
Decision Level: B (uretim servisi yeniden baslatildi; .env'e 1 satir eklendi)

== YAPILAN ==
- `.env`'e `FINPILOT_SCAN_STAGE_TIMING=1` eklendi (Meric onayiyla, tek satir)
- `docker compose restart api` -> health 200, servis saglikli

== IKI OPERASYONEL DERS (kalici, tekrar aranmasin) ==
1. COMPOSE SERVICE ADI != CONTAINER ADI.
   Container: `finpilot_api`. Compose service: `api`.
   `docker compose restart finpilot_api` SESSIZCE ETKISIZ kalir (hata vermez).
   Dogru komut: `docker compose restart api`.
2. `restart` ENV DEGISIKLIGINI ALMAZ.
   Ortam degiskenleri konteyner OLUSTURULURKEN sabitlenir. `env_file`
   degisikligi icin `docker compose up -d --no-deps --force-recreate api`
   gerekir. Bu yuzden stage timing restart sonrasi hala 0.

== KRITIK AYRIM: KOD YUKLENDI, ENV YUKLENMEDI ==
Kod bind mount'tan geliyor (./scanner:/app/scanner:ro, ./api:/app/api:ro).
`restart` sureci yeniden baslattigi icin moduller YENIDEN IMPORT EDILDI.
=> FAZ 0 kodu ve FINPILOT_DISABLE_ALPACA bayrak kodu ARTIK CANLI.
=> Yalnizca FINPILOT_SCAN_STAGE_TIMING eksik.
Sonuc: FAZ 2R.3 probe'u (alpaca_total_failure okumak) stage timing'e IHTIYAC
DUYMAZ ve EK KESINTI OLMADAN simdi kosulabilir.

== FAZ 3R TASARIM DUZELTMESI (recreate maliyeti) ==
Kol B `FINPILOT_DISABLE_ALPACA=1`'i surec ortaminda ister. Env degisikligi
recreate gerektirdigine gore, serpistirilmis A-B-A-B... tasarimi 10 RECREATE
demek olurdu. Bu hem agir, hem her recreate cache'leri ve Alpaca client
singleton'ini sifirlayarak SISTEMATIK CONFOUND ekler.
YENI BOLUSUM (10 recreate -> 2):
  - SURE + KAPSAM  : konteyner ici script, surec icinde bayragi degistirerek
                     serpistir -> 0 kesinti
                     (scripts/provider_benchmark.py zaten bayraktan bagimsiz
                      uc saglayiciyi dogrudan olcuyor)
  - CIKTI ESDEGERLIGI: 2 API taramasi (kol basina 1) -> 2 recreate
Plan belgesindeki FAZ 3R bu bolusume gore guncellenmeli.

== SIRADAKI (kesintisiz) ==
1. Tek API taramasi -> FAZ 2R.3 kapanir (alpaca_total_failure, experiment_arm,
   yf_bulk_symbols alanlari geldi mi + Alpaca gercekten devrede mi)
2. scripts/provider_benchmark.py -> Alpaca/EODHD/yfinance sure+kapsam
Ikisi de recreate GEREKTIRMEZ.

== SONRA (tek recreate) ==
`docker compose up -d --no-deps --force-recreate api` -> stage timing devreye
girer -> FAZ 1 dogru ortamda tekrarlanir.

---

[2026-09-21] — FINPILOT_DISABLE_ALPACA bayragi eklendi (Level B, varsayilan KAPALI)
Layer: Scanner / Experiment control
Decision Level: B (uretim veri yolu; bayrak verilmeden davranis BIREBIR eskisi gibi)
Affected Files: scanner/data_fetcher.py, api/routers/scan.py, tests/test_scanner_performance.py
Kapi: FAZ 2R tamamlandi (ayni gun) -> bayragin yazilmasi icin konulan sart kalkti.

== PARALEL SURECIN KRITIK KATKISI ==
Bayrak yalnizca `_get_alpaca_client()`'a konsaydi YETMEZDI. `ALPACA_API_KEY`
UC ayri yerde kapi olarak kullaniliyor:
  1. _get_alpaca_client()            (satir ~218)
  2. fetch_symbols_batch auto-detect (satir ~666)
  3. _prefetch_alpaca_bulk           (satir ~744)
Biri acik kalsaydi Kol B "kismen Alpaca acik" kosar ve A/B deneyi GECERSIZ
olurdu. Bu, paralel surecin tespitiydi; Claude iki kapi gormustu, ucuncusunu
kacirmisti.

== TASARIM ==
Tek ortak kaynak: `_alpaca_available()` -> ucu de bundan geciyor.
`alpaca_disabled()` public (test + metadata icin).
fetch_symbols_batch'te EK KORUMA: cagiran acikca use_alpaca=True gecse bile
bayrak EZER (deney kolu mutlak olmali).

== ALTI KISIT (Meric) — hepsi karsilandi ==
  1. Varsayilan Alpaca ACIK ("0")                    -> test ile garanti
  2. Yalnizca os.environ'dan okunur                  -> ✓
  3. .env'e EKLENMEDI                                -> ✓
  4. Surec baslatilirken acikca verilir              -> docker-compose
     `environment:` veya kabuk; .env'i ezer
  5. Deney kolu sonuc metadata'sina yazilir          -> yeni alanlar:
     `alpaca_disabled`, `experiment_arm` (A_baseline / B_alpaca_disabled)
  6. Cikti esdegerligi + saglayici kapsami kaydedilir-> `result_symbols` eklendi;
     saglayici kapsami zaten yf_fallback/yf_bulk_*/alpaca_miss/alpaca_total_failure
     alanlariyla kayitli

== DURUM ==
Kod yazildi, Claude tarafindan CALISTIRILAMADI (calisma alani 8 Eylul'den beri
erisilemez). Dogrulama gerekiyor: `pytest tests/test_scanner_performance.py`
Yeni testler: varsayilan-kapali, uc-kapi-birden, explicit-override, metadata.

== ENGELLEYICI HATIRLATMA ==
Bu kod da Faz 0 kodu gibi CALISAN uretim surecine yuklu DEGIL (--reload yok).
`docker compose restart finpilot_api` gerekiyor. Restart TEK SEFERDE hem Faz 0
hem bu bayragi devreye alir. Restart'tan sonra tek tarama ile alanlarin
geldigi dogrulanmali; ancak ondan sonra FAZ 3R A/B kosulabilir.

== YAPILMAYAN (bilerek) ==
Faz 4R/5R/6R (EODHD gecisi, gunluk-bar israfi, huni mimarisi) — saglayici
secimini veya mimariyi kalici degistiren Level B isler. "Butun fazlari kos"
talebi bunlari KAPSAMIYOR; Faz 3R sonucu olmadan yorumlari da belirsiz.

---

[2026-09-21] — FAZ 2R TAMAMLANDI: uretim ortami kesin tespit edildi (Level A, salt gozlem)
Layer: Configuration / Observability
Decision Level: A. Hicbir kod/.env/bayrak/saglayici degisikligi YAPILMADI.

== CANLI SUREC KANITI (Meric kostu, /proc uzerinden, gizli deger yazdirilmadan) ==
  Container : finpilot_api            (devcontainer DEGIL)
  CWD       : /app                    (/workspaces/Borsa DEGIL)
  EXE       : /usr/local/bin/python3.11
  CMD       : python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
  ALPACA_API_KEY        : process ortaminda MEVCUT
  FINPILOT_ENABLE_*     : 18 adet MEVCUT
  FINPILOT_SCAN_STAGE_TIMING : 0
  alpaca 0.43.2         : ayni executable'da import OK

== docker-compose.yml ILE TAMAMLANAN RESIM ==
  - `env_file:` (satir 68) -> .env konteyner BASLARKEN process ortamina giriyor.
    Yani uretimde .env'i api/main.py'nin ic yukleyicisi DEGIL, docker-compose
    tasiyor. /proc'ta gorunmesinin sebebi bu.
  - Bind mount'lar: ./scanner:/app/scanner:ro, ./api:/app/api:ro, ./data:/app/data
    -> Repo'daki kod konteynerin DISKINDE mevcut; data/ yazimlari repo'ya donuyor
       (timing log'u bu yuzden okuyabiliyoruz).

== KAPANAN SORULAR ==
1. GOREV #25 CURUTULDU. 18 FINPILOT_ENABLE_* process ortaminda MEVCUT.
   "Flag'ler uretimde fiilen kapali olabilir" hipotezi YANLIS. 2026-09-08
   flag kanit ozetinin zemini SAGLAM; gozden gecirme gerekmiyor.
2. Uc ayri ortam oldugu netlesti: (a) Windows host PowerShell, (b) devcontainer
   /workspaces/Borsa, (c) finpilot_api /app = URETIM. Onceki tum karsilastirmalar
   bu uclusu ayirt etmeden yapilmisti.
3. "5.8x Alpaca etkisi" KESIN OLARAK GECERSIZ. Sabah kosulari (06:50-07:19)
   finpilot_api'den (uretim, eski kod, Alpaca calisiyor); kampanya kosulari
   baska bir ortamdan (yeni kod, alpaca paketi yok, `No module named 'routers'`).
   IKI FARKLI KONTEYNER, IKI FARKLI KOD SURUMU. Karsilastirma bastan gecersizdi.

== YENI ENGEL: FAZ 0 KODU URETIMDE YUKLU DEGIL ==
Bind mount sayesinde kod konteynerin DISKINDE var, AMA calisan surece YUKLENMEDI.
start.sh acikca "--reload YOK -> stabil PID" diyor; uvicorn scanner/data_fetcher.py'yi
baslangicta import etti. Dolayisiyla su an calisan uretim surecinde
`alpaca_total_failure`, `yf_bulk_requests`, `yf_bulk_symbols`, `persist_s` ALANLARI YOK.
Kanit: sabah kosularinin (06:50-07:19) hicbirinde bu alanlar yok.
=> Faz 2R.3 probe'u (tek tarama ile alpaca_total_failure okumak) calisan surecte
   CALISMAZ. Once konteyner YENIDEN BASLATILMALI.
   REBUILD GEREKMIYOR — bind mount kodu zaten tasiyor, yalniz restart yeterli.

== SIRADAKI TEK ENGELLEYICI ADIM ==
`docker compose restart finpilot_api` (veya esdegeri) -> sonra tek tarama ->
`alpaca_total_failure` ve `yf_bulk_symbols` alanlarinin geldigini dogrula.
Bu yapilmadan Faz 3R A/B'si kurulamaz, cunku olcum alanlari uretimde mevcut degil.

== NOT ==
FINPILOT_SCAN_STAGE_TIMING uretimde 0. Faz 3R icin acilmasi gerekecek; bu
Meric'in karari ve konteyner restart'i ile birlikte planlanmali.

---

[2026-09-21] — GERI CEKME: ".env hic yuklenmiyor" TESHISI YANLISTI (Level A, duzeltme)
Layer: Configuration
Decision Level: A (onceki ayni-gun girdisinin duzeltmesi)

== NE YANLISTI ==
Ayni gun girilen "ALPACA KESINTISI TESHIS EDILDI: .env hic yuklenmiyor" kaydi,
kok neden olarak "load_dotenv API acilis yolunda hic cagrilmiyor" diyordu.
BU YANLIS. api/main.py satir 16-26'da ELLE YAZILMIS bir .env yukleyici var:
    _env_path = Path(_PROJECT_ROOT) / ".env"
    if _env_path.exists():
        for _line in _f:
            ...
            if _key and _key not in os.environ:
                os.environ[_key] = _val
`load_dotenv` kullanmadigi icin `load_dotenv|dotenv` grep'i bunu KACIRDI.
METOD HATASI: idiomatik API'nin yoklugundan yoklugu sonucu cikarildi; elle
yazilmis esdegeri aranmadi. Bundan sonra env yukleme sorusunda
`os.environ\[|setdefault|update|putenv` de aranacak.

== DUZELTILMIS DURUM ==
- `api.main:app` uzerinden kosan URETIM API'sinde .env `os.environ`'a YUKLENIYOR.
  Dolayisiyla ALPACA_API_KEY scanner'a GORUNUR ve Alpaca CALISIR. Bu, 2026-09-21
  sabah kosularinda (06:50-07:19) `alpaca_miss`'in DOLU olmasiyla tutarli.
- Yukleyici `if _key not in os.environ` kullaniyor: KABUKTAN verilen degiskenler
  .env'i EZER. FAZ 3R bayrak tasariminin 4. kisiti (surec baslatilirken acikca
  verilir) bu sayede calisir — ek koda gerek yok.
- Kampanya kosularinin alpaca_total_failure=true olmasi, .env'in hic yuklenmemesi
  degil, O KOSULARIN api.main uzerinden GECMEMESI ile aciklaniyor. Kanit:
  her kosuda `No module named 'routers'` — api.main altinda cozulen bir import
  orada cozulmuyor.

== TASK #25 UZERINDEKI ETKI ==
"Feature flag'ler fiilen kapali olabilir" hipotezi, uretim API yolu icin
BUYUK OLASILIKLA CURUK: api.main .env'i yukluyorsa FINPILOT_ENABLE_* bayraklari
os.environ'da vardir ve fiilen ACIKTIR. Yine de Faz 2R'nin ENABLE_FLAG_COUNT
ciktisiyla dogrulanacak; simdiden kapatilmiyor.

== DEGISMEYEN SONUC ==
FAZ 1 olcumu hala GECERSIZ ve "5.8x Alpaca etkisi" hala YORUMLANMAYACAK.
Aksine bu duzeltme, iki kolun .env yuklemesi + alpaca paketi + giris noktasi
bakimindan AYRI oldugunu gosterdigi icin, farkin ORTAM ARTEFAKTI olma
ihtimalini ARTIRIR. Faz 2R ve tek-ortam A/B zorunlulugu aynen duruyor.

---

[2026-09-21] — FAZ 1 OLCUMU GECERSIZ: uretim disi ortamda alinmis + ALPACA VARLIGI YAVASLIKLA ILISKILI
Layer: Observability / Configuration
Decision Level: A (bulgu). Hicbir duzeltme uygulanmadi — oncelik tersine donmus olabilir.

== FAZ 1 TEMELI NEDEN GECERSIZ ==
1. `alpaca-py==0.43.2` requirements.txt:72'de BEYAN EDILMIS bagimlilik.
   Olcum kabugunun Python'unda `ModuleNotFoundError: No module named 'alpaca'`.
   -> O kabuk URETIM ORTAMI DEGIL (venv aktif degil / farkli yorumlayici).
2. Kampanya kosularinin HEPSINDE `Auto-watchlist failed: No module named 'routers'`.
   Farkli import koku -> farkli giris noktasi -> gercek API uygulamasi degil.
3. Bugunun KAMPANYA ONCESI kosulari (06:50-07:19, kayit 310-314) `alpaca_miss`
   DOLU: {"15m":10,"1h":10}, {"15m":16,"1h":13}, {"15m":44,"1h":41},
   {"15m":36,"1h":30}. Dolu olmasi `_repair_partial_alpaca_result`'in calistigini,
   yani Alpaca'nin VERI DONDURDUGUNU kanitlar. Uretimde Alpaca CALISIYOR.
4. Kampanya kayitlarinda (316-321) alpaca_total_failure=true, retry.attempt=0.
   Logda `alpaca_total_failure: false` olan HIC kayit yok — kampanya calisan
   Alpaca'yi hic gozlemedi.
=> FAZ 1'in %81.7 bulk-yfinance payi YALNIZCA Alpaca'siz ortam icin gecerlidir.
   Uretimi TEMSIL ETMIYOR. FAZ 1 temel olarak KULLANILAMAZ.

== BEKLENMEDIK SINYAL: ALPACA VARLIGI ~5.8x YAVASLIKLA BIRLIKTE ==
Ayni gun, ayni evren (200 sembol):
  Alpaca VAR  (06:50-07:19): 278.61 / 406.92 / 445.31 / 450.92 / 409.04 -> ~409 sn
  Alpaca YOK  (kampanya)   :  82.21 /  68.96 /  70.82 /  55.07 /  71.34 -> ~71 sn
Alpaca'nin hizli birincil yol olmasi gerekiyordu; veri TERSINI gosteriyor.
MEKANIZMA HIPOTEZI (TEST EDILMEDI): Alpaca kismen calistiginda Alpaca gecikmesi +
timeframe basina AYRI repair cagrilari odeniyor; repair `_bulk_yf_download`'i
yalnizca EKSIK sembollerle cagiriyor -> kucuk, verimsiz partiler. Alpaca hic
yokken tek temiz gecis: 3 istek, 600 sembol-timeframe.
CONFOUND'LAR ACIK: farkli ortam, farkli giris noktasi, farkli kod surumu,
n=5 vs n=5, tek gun, kontrollu deney DEGIL. Bu bir SINYAL, sonuc degil.

== ONCELIK TERSINE DONMUS OLABILIR ==
"Alpaca'yi geri getir" refleksi YANLIS olabilir. Alpaca-varken yol gercekten
yavassa, paketi kurup .env'i yuklemek taramayi YAVASLATIR. Bu yuzden ne paket
kurulumu ne .env duzeltmesi uygulandi.

== PLAN ETKISI ==
Eski FAZ 2/3 (EODHD dogrulama + gecis) YANLIS HEDEFE nisan aliyor ve ERTELENDI.
Yerine iki yeni faz konuldu (bkz. docs/2026-09-21-tarama-hizlandirma-plani.md):
  FAZ 2R — Uretim ortaminin tespiti (KAPI: bu cevaplanmadan hicbir olcum
           karsilastirilabilir degil)
  FAZ 3R — AYNI ortamda kontrollu Alpaca A/B (serpistirilmis ABABAB, 5+5),
           hem SURE hem CIKTI ESDEGERLIGI olculecek.
CIKTI ESDEGERLIGI neden zorunlu: Alpaca ve yfinance farkli barlar verebilir ->
farkli skorlar. O zaman "Alpaca'yi kapat" bir HIZ karari degil, VERI karari olur.

---

[2026-09-21] — ALPACA KESINTISI TESHIS EDILDI: .env hic yuklenmiyor (Level A, teshis; DUZELTME YAPILMADI)
Layer: Configuration / Scanner
Decision Level: A (teshis). Kod/env/flag DEGISTIRILMEDI — duzeltmenin yan etkisi buyuk, bkz. UYARI.

== KANIT ZINCIRI (hepsi dogrulandi) ==
1. Bes enstrumanli kosunun tamaminda alpaca_total_failure=true.
2. `prefetch.alpaca` stage suresi: 2.9e-05 / 1.6e-05 / 2.3e-05 / 1.2e-05 / 3e-05 /
   1.4e-05 sn -> ~20 MIKROSANIYE. Hicbir ag islemi bu surede olmaz (DNS/TCP/TLS yok).
3. `retry.attempt` event sayisi: SIFIR. `_get_stock_bars_with_retry` hic cagrilmadi.
   -> Alpaca'ya HIC istek gonderilmedi. Auth hatasi, kota, plan veya ag sorunu DEGIL.
4. `_prefetch_alpaca_bulk`'un ILK satiri (data_fetcher.py:744):
       if not os.environ.get("ALPACA_API_KEY"): return None
   20 mikrosaniye tam olarak bu: bir dict lookup + return.
5. `datetime.UTC` ImportError ihtimali ELENDI: api/routers/scan.py ayni UTC'yi
   kullaniyor ve timing kayitlarinda `ts` dolu -> Python 3.11+, import saglam.
6. `.env` dosyasinda anahtar VAR (satir 20, tek kayit, bicim sorunu yok).
7. KOK NEDEN: `load_dotenv` repo genelinde YALNIZCA script'lerde cagriliyor
   (enrich_market_caps, dist_live_test, telegram_config, publish_now,
   preview_publish, sync_symbols, verify_eodhd_bars). API acilis yolunda
   (api/main.py, api/routers/scan.py) HIC YOK.
8. core/config.py pydantic-settings kullaniyor:
       model_config = SettingsConfigDict(env_file=str(PROJECT_ROOT / ".env"), ...)
   Bu, degerleri Settings NESNESINE yukler; `os.environ`'a YAZMAZ.
   scanner/data_fetcher.py ise dogrudan `os.environ.get()` okuyor.
   IKI MEKANIZMA HIC BULUSMUYOR.

== SONUC ==
`.env` degerleri API surecinin `os.environ`'ina hicbir zaman girmiyor. Tarama
suresince ALPACA_API_KEY gorunmez; Alpaca yolu 20 mikrosaniyede sessizce atlaniyor
ve her tarama SIFIR Alpaca verisiyle, tamamen yfinance uzerinden calisiyor.

== UYARI: DUZELTME KUCUK DEGIL, KONTROLLU YAPILMALI ==
`api/main.py`'ye `load_dotenv()` eklemek tek satirlik gorunur AMA `.env`'deki
TUM degiskenleri ayni anda devreye sokar. `.env`'de dokuz FINPILOT_ENABLE_* bayragi
"1" yazili; kodda hepsinin varsayilani "0". Yani bu duzeltme, su an fiilen KAPALI
olabilecek dokuz feature flag'i AYNI ANDA acar.
Bu, flag karari DEFERRED (baseline cozulene kadar) iken sinyali sessizce degistirir.
=> Duzeltme TEK BASINA uygulanmamalidir; once hangi bayragin fiilen hangi durumda
   oldugu olculmelidir.

== YENI HIPOTEZ (TEST EDILMEDI, iddia DEGIL) ==
Ayni mekanizma tum `os.getenv` tabanli bayraklar icin gecerliyse, uretimde
feature flag'ler `.env`'de "1" yazmasina ragmen fiilen "0" olabilir. Bu dogruysa
2026-09-08 "9 flag kanit ozeti" calismasinin zemini etkilenir. DOGRULANMADAN
hicbir sonuc cikarilmayacak; kendi gorev kaydi acildi.

== DOGRULAMA ADIMI (Meric, tek satir) ==
Sunucuyu baslattigi ayni kabukta:
    python -c "import os; print('ALPACA_API_KEY' in os.environ)"
    python -c "import alpaca; print(alpaca.__version__)"
Ilki False donerse teshis kesinlesir.

== ETKI ==
Bu bir HIZ sorunu degil. Tarama aylardir Alpaca verisi olmadan calisiyor olabilir;
veri kaynagi/kapsam ve FAZ 3 tasarimi bundan etkilenir.

---

[2026-09-21] — FAZ 1 olcum kampanyasi TAMAMLANDI: ilk gercek asama kirilimi (Level A, salt gozlem)
Layer: Observability / Scanner
Decision Level: A (olcum; hicbir uretim/saglayici/flag/sinyal degisikligi YOK)
Kaynak: data/distribution/scan_timing.jsonl son kayitlar (FINPILOT_SCAN_STAGE_TIMING=1)
Kosum: Meric + paralel surec. Claude'un calisma alani hala erisilemez (8 Eylul Windows
  guncellemesi); Claude sayilari grep ile bagimsiz dogruladi (6 kayitta
  alpaca_total_failure=true ve yf_bulk_symbols=600 — rapor 5 demisti, log 6 gosteriyor).

== MEASURED (n=5 enstrumanli kosu, universe=200, kosu basina 931 stage event) ==
  total_s   : 55.07 / 68.96 / 70.82 / 71.34 / 82.21  -> MEDYAN 70.82 sn
  persist_s : 0.11-0.24 -> MEDYAN 0.16 sn
  Stage toplamlari (5 kosu): prefetch.bulk_yfinance 289.155 sn,
    evaluation.symbol 710.498 sn, indicator.compute 90.789 sn
  DERIVED kosu basina: prefetch.bulk_yfinance ~57.8 sn = total_s'nin ~%81.7'si
  NOT: evaluation.symbol SEMBOL BASINA olculuyor ve 32-worker havuzunda kosuyor;
    710 sn TOPLAM istir, duvar saati degildir (~142 sn/kosu is, ~13 sn duvar saatine
    sikisiyor -> paralellik ~11x calisiyor). prefetch.bulk_yfinance ise 3 timeframe
    uzerinde SIRALI dongu tek timer'la sarili -> duvar saati olarak okunabilir.

== SONUC: Master prompt'un basari cumlesi ILK KEZ DOLDURULDU (bu rejim icin) ==
  "200 sembollük taramanin suresi: ~%82 toplu yfinance veri cekimi, ~%18 degerlendirme
   (iyi paralellesmis), ~%0.2 kalicilastirma. En buyuk tekil asama prefetch.bulk_yfinance,
   payi %81.7. Tamamen sifirlansa toplam kazanc en fazla %82 (70.8 sn -> ~13 sn)."

== HIPOTEZ SONUCLARI ==
  H3 (kalicilastirma anlamli pay tutar) -> **CURUTULDU**. 0.16/70.82 = %0.23.
    Plandaki FAZ 0.3 gerekliydi (olcum icin) ama optimizasyon hedefi DEGIL.
  H2 (300 gunluk 1d gecmisini her taramada cekmek anlamli) -> kismen destekleniyor:
    1d, 600 sembol-timeframe'in 200'u ve bulk cekimin icinde. Ayrisma icin
    timeframe bazli kirilim gerekiyor; stage event'lerde timeframe alani var,
    henuz ayristirilmadi.
  K1/K2 (yf_fallback toplu yolu saymiyordu) -> **URETIM VERISIYLE KANITLANDI**:
    bes kosunun tamaminda yf_fallback=0 iken yf_bulk_symbols=600.
    "yfinance kullanilmadi" okumasi kesin olarak yanlisti.

== BEKLENMEDIK VE PLANI BOZAN BULGU ==
  Bes kosunun TAMAMINDA alpaca_total_failure=TRUE. Alpaca hicbir veri vermedi.
  VE BU KOSULAR HIZLI: medyan 70.8 sn, tarihsel 200-sembol medyani ~300 sn.
  Yani "Alpaca tamamen olu" rejimi, tarihsel ortalamadan ~4x HIZLI.
  Bu, planin ortuk varsayimini TERSINE CEVIRIYOR (Alpaca calisir=hizli,
  duser=yavas). Yeni hipotez (TEST EDILMEDI): yavas kosular Alpaca'nin KISMEN
  calistigi kosular olabilir — o zaman Alpaca gecikmesi + retry/backoff + timeframe
  basina ayri repair cagrilari + son catare sembol-basina tier ust uste biniyor.
  Hizli yol ise "Alpaca'yi hizlica atla, tek temiz toplu cekim yap" olabilir.

== HALA NOT MEASURED (asiri genelleme yapilmayacak) ==
  Enstrumanli kosularin HEPSI ayni rejimde (Alpaca olu). Tarihsel 300-590 sn'lik
  kosularin asama kirilimi icin SIFIR veri var. %81.7 rakami YALNIZCA Alpaca-olu
  rejimi icin gecerlidir.

== PLAN ETKISI: FAZ 3'UN TASARIMI GECERSIZ ==
  FAZ 3 "FAZ 1 temeliyle karsilastir" diyordu. Ama FAZ 1 temeli Alpaca'nin bozuk
  oldugu bir rejimde alindi ve tarihsel populasyonu TEMSIL ETMIYOR. EODHD acilip
  bu temele karsi olculurse sonuc yorumlanamaz. FAZ 3 yeniden tasarlanmali.

== AYRI BULGULAR (performanstan bagimsiz, kendi islerini hak ediyor) ==
  1) ALPACA TAMAMEN DEVRE DISI. Tarama su an SIFIR Alpaca verisiyle calisiyor.
     Bu bir hiz meselesi degil, VERI KALITESI/KAPSAM meselesi. Anahtar PK ile
     baslayan paper anahtari; auth/plan durumu ayrica incelenmeli.
  2) `Auto-watchlist failed: No module named 'routers'` HER kosuda goruldu.
     api/routers/scan.py'deki try/except bunu sessizce yutuyor. Auto-watchlist
     islevsel olarak CALISMIYOR. Level B hata, ayri kayit/duzeltme gerekiyor.

== GOVERNANCE ==
  Hicbir saglayici secimi, cache, scheduler, sinyal, ranking, flag veya yayin
  davranisi degistirilmedi. .env yalnizca FINPILOT_SCAN_STAGE_TIMING icin ve
  Meric tarafindan degistirildi. pytest tests/test_scanner_performance.py 8/8.
  reports/scan_performance_audit_2026-09-21.md hala NOT MEASURED diyor ve bu
  kampanya islenene kadar guncel sayilmamali.

---

[2026-09-21] — FAZ 0 uygulandi: olcum aleti duzeltildi + 2026-09-14 iddiasi GERI CEKILDI (Level B)
Layer: Observability / Scanner
Decision Level: B (uretim olcum yolu; tarama ciktisi/skor/sinyal DEGISMEDI)
Affected Files: scanner/data_fetcher.py, api/routers/scan.py, tests/test_scanner_performance.py
Plan: docs/2026-09-21-tarama-hizlandirma-plani.md (Meric onayladi)

== GERI CEKME ==
2026-09-14 girdisi "yfinance fallback birincil darbogaz" diyordu. Bu iddia
FAZLA GUCLUYDU ve geri cekiliyor. Gerekce: o teshis `yf_fallback` sayacina
dayaniyordu; sayac yalnizca SEMBOL-BASINA yolu sayiyor, TOPLU yolu (yf.download)
saymiyordu. Tam veri kumesinde `yf_fallback=0` olan kayitlarda bile sure
37 sn ile 354 sn arasinda degisiyor — yani sayac ayrim gucunu kaybetmis.
Yerine gecen, veriyle desteklenen ifade: "Yavas kosularin hepsi yfinance'e
ugruyor; fallback sayisi tek basina 10x varyansi aciklamiyor." Asama seviyesinde
darbogaz hala NOT MEASURED.

== BULUNAN HATA (paralel surecin kodunda) ==
`_note_alpaca_total_failure()` cagrisi prefetch_symbols_multi_timeframe icinde
`return alpaca_result`'in ALTINDA duruyordu -> ULASILAMAZ OLU KOD. Bayrak
uretimde hicbir zaman True olmuyordu. Mevcut birim testi fonksiyonu DOGRUDAN
cagirdigi icin hatayi yakalayamamisti (IMPLEMENTED != ACTIVE — programin kendi
ayrimi, bu kez kendi enstrumantasyonumuzda cikti).
Duzeltildi + uretim yolunu kullanan REGRESYON TESTI eklendi.

== YAPILAN (FAZ 0) ==
0.1 Toplu yfinance gorunurlugu: _note_yf_bulk() + yf_bulk_counts();
    _bulk_yf_download() artik sayiliyor. Yeni alanlar: yf_bulk_requests,
    yf_bulk_symbols. Log satiri da yaniltici olmaktan cikarildi.
0.2 alpaca_total_failure: olu kod duzeltildi (yukari bkz). Cagri, besi birden
    kapsayan cagiran-taraf konumuna alindi (_prefetch_alpaca_bulk'un 5 ayri
    `return None` cikisi var).
0.3 persist_s: paralel surec tarafindan ZATEN yapilmisti, dogrulandi ve korundu.

== COZULEN CAKISMA (sessizce gecilmedi) ==
Paralel surecin testi (test_bulk_yfinance_call_counts_as_fallback) toplu yolun
MEVCUT `yf_fallback` sayacina katilmasini bekliyordu. BU YAPILMADI:
  (a) `yf_fallback` 315 gecmis kayitta var; anlamini degistirmek eski/yeni
      kayitlari karsilastirilamaz yapardi — planin kendi tasarim kurali bunu
      `total_s` icin yasakliyordu, ayni mantik bu alan icin de gecerli;
  (b) "200 sembol servis eden 1 toplu cagri" ile "1 sembol ceken 1 cagri" ayni
      sayiya yazilirsa maliyet ayrimi kaybolur.
Testin NIYETI (toplu kullanim gorunur olsun) korundu, MEKANIZMASI degistirildi.
Iki sayi ayri tutuluyor: requests (ag turu) ve symbols (kac sembol servis edildi).

== DURUM: DOGRULANDI (2026-09-21, ayni gun) ==
`pytest tests/test_scanner_performance.py` -> **8 passed, 0 failed**.
Testleri paralel surec kostu (Claude'un Linux calisma alani 8 Eylul Windows
guncellemesinden beri erisilemez; py_compile dahil hicbir sey kosulamadi).
Tarama ciktisi, skor formulu, agirliklar, flag kararlari DEGISMEDI.

== IKINCI CAKISMA VE KOK NEDENI (ayni gun, test kosumunda yakalandi) ==
Ilk test kosumu 1 hata verdi: `_bulk_yf_download()` HEM `_note_yf_fetch()` HEM
`_note_yf_bulk()` cagiriyordu -> CIFT SAYIM. Paralel surec `_note_yf_fetch()`
cagrisini kaldirdi, tekrar kosuldu, 8/8 gecti.
KOK NEDEN CLAUDE'DA: plan belgesinin (docs/2026-09-21-tarama-hizlandirma-plani.md)
0.1 adimi harfiyen "`_bulk_yf_download()` icine `_note_yf_fetch()` ekle" diyordu.
Paralel surec PLANA UYDU; Claude kendi planindan SAPTI (ayri sayac yapti, gerekcesi
saglamdi) ama BELGEYI GUNCELLEMEDI. Iki ajanin ayni plandan calistigi bir repoda
bu, ayni fonksiyonda carpisma demek. Plan belgesi duzeltildi (0.1 artik ayri-sayac
tasarimini ve bu cakismanin kaydini iceriyor).
DERS: plan belgesinden sapilacaksa, sapma ANINDA belgeye yazilmali — yoksa
belge ikinci ajan icin yanlis talimat kaynagi olmaya devam eder.

== K1 BAGIMSIZ OLARAK DOGRULANDI ==
Cakisma, K1'in ("toplu yol hic sayilmiyordu") o an DOGRU oldugunu teyit ediyor:
paralel surecin cagriyi EKLEMESI gerekti, demek ki yoktu. Veri tarafindan da
destekleniyor: timing log satir 16'da `alpaca_miss` DOLU (yani repair calisti,
repair `_bulk_yf_download` cagirir) ama `yf_fallback=0`. Toplu yol sayilsaydi
o kayit >=1 gosterirdi. Dolayisiyla 2026-09-14 iddiasinin geri cekilmesi
saglam zeminde duruyor.

== ACIK RISK: ESZAMANLI AJAN KOORDINASYONU ==
Bu oturumda ayni dosyada IKI carpisma yasandi (olu-kod `_note_alpaca_total_failure`
ve simdi cift sayim). Ikisi de yakalandi, ama sans eseri degil test sayesinde.
ONERI (uygulanmadi): paylasilan plan belgeleri tek yazma-otoritesi altinda
tutulsun; sapma varsa once belge guncellensin, sonra kod yazilsin.

---

[2026-09-21] — Tarama Performans Denetimi Master Prompt v1.0 olusturuldu (Level A, sadece belge)
Layer: Governance / Performance
Decision Level: A (yalnizca protokol belgesi; olcum yapilmadi, kod degismedi)
Affected Files: docs/2026-09-21-tarama-performans-denetimi-master-prompt.md (yeni)
Prompt hazirlanirken kod okumasiyla bulunan IKI YENI BULGU (denetimin dogrulamasi gerekiyor):
  1. ENSTRUMANTASYON VAR AMA HIC ACILMAMIS: scanner/performance.py tam bir asama-
     zamanlama sistemi iceriyor ve 12 noktada cagriliyor (prefetch.alpaca,
     prefetch.repair, prefetch.bulk_yfinance, prefetch.resample_4h,
     prefetch.symbol_yfinance, fetch.request [bulk_yfinance+eodhd], fetch.parse,
     retry.attempt, retry.backoff, rate_limit.wait, indicator.compute,
     evaluation.symbol). Ancak FINPILOT_SCAN_STAGE_TIMING varsayilan "0" ve
     mevcut 84 tarama kaydinin HICBIRINDE stage_timing alani dolu degil.
     -> Olcum aleti kurulmus, hic acilmamis. Denetimin ilk eylemi kod yazmak degil,
        bu bayragi acip bir tarama kosmak.
  2. OLCUM PENCERESI EKSIK: api/routers/scan.py'de _t_scoring_done sonrasi calisan
     DORT kalicilastirma cagrisi (_persist_shortlist, _persist_shadow_ledger,
     _auto_add_watchlist, _persist_distribution_export) total_s'nin DISINDA kaliyor.
     -> Raporlanan "total_s" taramanin gercek duvar-saati suresi DEGIL. Simdiye
        kadarki tum tarama-suresi konusmasi eksik bir sayi uzerinden yapilmis olabilir.
Prompt icerigi: olcum etiketleme (MEASURED/LOGGED/DERIVED/ESTIMATED/UNKNOWN),
  Part 0 fizibilite kapisi, asama-bazli protokol (her asama icin Amdahl teorik tavani
  ZORUNLU), varyans sorusturmasi (mevcut logda 10x varyans var -> tek kosu kanit degil,
  min 5 kosu + medyan/p95), serilesme sorusturmasi (rate_limit.wait + retry.backoff
  olculmeden paralellik onerisi YASAK), olcekleme formulu, A-F karar agaci,
  5 zorunlu cikti dosyasi, 17 bolumluk rapor formati.
Onemli sinir: prompt, performans ile sinyali ayri karar hatlari olarak ayiriyor.
  alignment_ratio/momentum_ratio kaldirmak performans eylemi GIBI gorunur ama
  SINYAL kararidir ve bu denetimin yetkisi disindadir. Ayrica .env degisikligi
  ajana degil kullaniciya birakildi (FINPILOT_SCAN_STAGE_TIMING dahil).
Durum: belge olusturuldu, HENUZ UYGULANMADI. Mevcut hicbir siniflandirma degismedi.

---

[2026-09-18] — Yon tahmini dis-kanit taramasi (Deep Research Master Prompt v1.0) (Level A, salt-okunur)
Layer: Research / External evidence
Decision Level: A (literatur taramasi; uretim/kod/veri degisikligi yok, tahmin uretilmedi)
Affected Files: reports/direction_prediction_external_evidence_2026-09-18.md (yeni)
Ana sonuc:
  - 1-5 gun ufkunda, retail maliyetiyle, guvenilir YON tahmini dis literaturde de
    buyuk olcude DESTEKLENMIYOR. FinPilot'in 8 bagimsiz yon testinin basarisiz
    olmasi alanin durumuyla TUTARLI — bize ozgu bir basarisizlik degil.
  - Kisa ufukta en guclu/tekrarlanmis bulgularin yonu NEGATIF:
    * Barber/Huang/Odean/Schwarz (2022, JF): en cok alinan hisseler 20 gunde
      ortalama -%4.7 anormal getiri (TIER A).
    * Bali/Cakici/Whitelaw (2011, JFE): MAX/lottery hisseleri, en dusuk-en yuksek
      decile farki >%1/ay TERS yonde (TIER A).
  - BUNUN ANLAMI: FinPilot attention map'inin "negatif medyan getiri (-%2.32) +
    yuksek buyuk-kaybeden orani (%39.4 vs %15.1)" bulgusu bir artefakt degil,
    literaturdeki attention/lottery asiri-fiyatlama olgusunun bagimsiz tekrari
    gibi gorunuyor. Dedektor bozuk degil; YANLIS YONE okunuyor.
    Savunulabilir kullanim: AL sinyali degil, ELEME/kacinma filtresi.
  - lottery_factor'un negatif yonu artik dis TIER A kanitla UYUMLU (Bali 2011).
    Bu onu "kaldirilacak" degil "dogru yonde calisiyor olabilir" sutununa tasir;
    karar yine de baseline cozulene kadar ERTELENMIS kaliyor.
  - Fade: dis literatur terfi gerekcesi SAGLAMIYOR. Genis evrende reversal maliyetle
    oluyor (de Groot/Huij/Zhou 2012, TIER A). Tek "maliyet sonrasi pozitif" gap
    iddiasi MDPI kaynakli (TIER D, replikasyon yok) — kabul edilmedi.
  - dist_52w_high celiskisi: CELISKI YOK, UFUK UYUMSUZLUGU VAR. George & Hwang
    (2004) etkisi 6-12 ay ufkunda; bizim olcumumuz 1-5 gun + redundancy.
  - Aday kaynak kararlari: insider Form 4 = DEPRIORITIZE (kanit 12 ay ufkunda,
    bizim ufkumuzla uyusmuyor); 8-K = TEST-CAREFULLY (kisa ufukta drift gosteren
    tek yapisal aday, TIER B); short interest = TEST-CAREFULLY ama LONG/dusuk-SI
    tarafi; news_cache = DEPRIORITIZE (skor ~0.99 sabit, BOZUK);
    float/short_pct snapshot = KILL (point-in-time degil -> look-ahead bias).
  - McLean & Pontiff (2016, JF): yayin sonrasi getiriler -%58. Literaturden alinan
    her etki bu iskontoyla okunmali.
Onerilen TEK on-kayitli deney: ANS-1 (Attention-as-Negative-Screen).
  Attention-flag'li hisselerin ELENMESI medyan c2c_5d'yi iyilestiriyor mu?
  Hipotez yonu DIS kaynaktan turetildi (muhurlenmis-kesif ihlali degil).
  Kritik avantaj: eleme bir islem degil -> ISLEM MALIYETI BARIYERI YOK.
  Bu, programin diger tum adaylarini (fade/reversal/short) olduren engeli asiyor.
  Yeni feed gerekmiyor; mevcut veri yeterli.
PROPOSED GOVERNANCE ACTION (uygulanmadi, oneri): kanit taksonomisine
  EXTERNAL-EVIDENCE (TIER A/B/C/D) sinifi eklensin — su an dis literatur kanitini
  ic bulgudan ayiran resmi etiket yok, karisma riski yuksek.
Durum: Hicbir mevcut siniflandirma degistirilmedi (attention map, fade, flag karari,
  catalyst aynen korundu). Uydurma atif yok; dogrulanamayan iki kaynak UNVERIFIED /
  TIER D olarak isaretlendi.

---

[2026-09-14] — EODHD intraday barlari veri-saglayici zincirine eklendi (Level B, bayrak-kapali)
Layer: Data / Scanner
Decision Level: B (uretim veri yolu; bayrakla kapali, varsayilan davranis degismedi)
Affected Files: data/eodhd_client.py (intraday() metodu + TTL),
  scanner/data_fetcher.py (_eodhd_one, _bulk_eodhd_intraday, _resample_intraday,
  eodhd_bars_enabled, _repair_partial_alpaca_result icine EODHD basamagi),
  .env.example (FINPILOT_ENABLE_EODHD_BARS), scripts/verify_eodhd_bars.py (yeni)
Gerekce (olculmus, tahmin degil):
  - data/distribution/scan_timing.jsonl, 84 gercek tarama: 200 sembol, yf_fallback=0
    iken 50-64 sn; yf_fallback~150 iken 420-534 sn. Fallback basina ~2.5 sn.
    1.900 sembole olceklenince ~50 dk — kullanicinin bildirdigi 30-60 dk ile uyumlu.
  - alpaca_miss her satirda ayni desen: 15m/1h'te onlarca eksik, 1d'de ~0.
    Kok neden: scanner/data_fetcher.py:740'ta feed="iex" KODA GOMULU; IEX ABD
    hacminin ~%2-3'u, kucuk/orta likiditede gun ici bar tasimiyor.
  - EODHD ucretli aboneligi mevcut ve ANAHTARI dolu, ancak bar kaynagi olarak
    hic baglanmamisti: eodhd_client'ta intraday metodu YOKTU, saglayici zinciri
    sadece Alpaca -> yfinance idi. EODHD canli yolda yalnizca fundamentals
    (features.py:543) ve news catalyst (features.py:644) icin kullaniliyordu.
  - scripts/probe_eodhd.py (2026-07-31) bu soruyu sormak icin yazilmis ama
    hic calistirilmamis ("LOCAL-RUN bekliyor") — bu tur o boslugu kapatiyor.
Degisiklik:
  - eodhd_client.intraday(symbol, interval, days): 1m/5m/1h. EODHD'de 15m YOK.
  - data_fetcher: 15m, 5m barlarindan resample ile turetiliyor (_EODHD_DERIVED).
  - _repair_partial_alpaca_result artik once EODHD'yi deniyor (yalnizca gun ici
    araliklar; 1d'de Alpaca zaten ~hic iskalamadigi icin kota israfi onlendi),
    doldurulamayanlar eskisi gibi yfinance'e dusuyor.
  - Bayrak FINPILOT_ENABLE_EODHD_BARS varsayilan "0" — acilmadan davranis birebir
    eskisi gibi. Skor formulu, agirliklar, flag kararlari DEGISMEDI: bu degisiklik
    barlarin NEREDEN geldigini degistirir, NE hesaplandigini degil.
Durum: kod yazildi, AGSIZ dogrulanamadi (bu oturumda hem sandbox agi hem de
  Linux calisma alani kullanilamaz durumda — Windows 8 Eylul guncellemesi).
  Sozdizimi/py_compile KOSULAMADI; yerel dogrulama sarttir.
  LOCAL-RUN bekliyor: python scripts/verify_eodhd_bars.py
    -> (1) plan intraday iceriyor mu (2) bar sekli scanner sozlesmesine uyuyor mu
       (3) yfinance'e karsi gercek hiz farki.
Acik risk: EODHD intraday endpoint'i coklu-sembol DESTEKLEMEZ (sembol basina 1
  cagri, ~5 kredi). Tam evrende kota/maliyet ETKISI OLCULMEDI — bu yuzden iki
  asamali huni (once 1d ile eleme, sonra yalnizca adaylara gun ici veri) hala
  gerekli; bu tur onu icermiyor.

---

[2026-09-09] — Master Validation Prompt v1.0 uygulandi: Full Baseline Reconstruction + Compression Forensics (Level A, read-only)
Layer: Research / Score Engine
Decision Level: A (teshis, uretim degisikligi yok)
Affected Files: research/full_baseline_reconstruction_compression_forensics_2026_09_09.py (yeni),
  reports/full_baseline_reconstruction_compression_forensics_2026-09-09.md (yeni),
  reports/baseline_{reconstruction_components,compression_forensics,input_coverage,
  component_predictiveness,random_control,leave_one_out,reconstruction_walk_forward,
  component_correlation}_2026-09-09.csv (yeni)
Ozet:
  - KRITIK DUZELTME: composite_score = compute_recommendation_strength() cikisidir
    (round(clip(raw/16.5*100,0,100)), 0-100 olcekli) -- compute_recommendation_score()'un
    ham (0-16.5) cikisi DEGIL. scanner/score_engine.py:24,329-397 dogrudan okunarak
    dogrulandi. Onceki turlarda (bu oturumun erken kismi dahil) yanlis olcek varsayilmisti.
  - Reconstruction Case D: PRODUCTION BASELINE = NOT FULLY RECONSTRUCTED. En iyi kismi
    reconstruction (8 terim: regime/direction/score/squeeze/catalyst/lottery/overnight/
    sentiment) exact-match %10.58, correlation 0.882. filter_score/alignment_ratio/
    momentum_ratio/volume_spike/price_momentum/trend_strength CSV'de yok, bu ortamda
    yapisal olarak reconstruct edilemiyor (1h/4h/15dk tarihsel bar verisi mevcut degil).
  - composite_score sadece 57/84 gunde (%67.86) dolu -- coverage bias dogrulandi.
  - Ham Pearson (composite_score vs c2c_1d) kucuk ve negatif (-0.0136, permutation p<0.01
    ama YANLIS YONDE); winsorize(1/99) edilince pozitife donuyor (+0.0420); medyan-tabanli
    quintile de zayif-pozitif egilim gosteriyor (Q1 hit %44.4 -> Q5 hit %51.1). Bu celiski
    COZULEMEDI -- outlier-hassasiyeti kesin ama "gercek" yon UNKNOWN.
  - catalyst_factor sifir-varyansli (tek deger 0.0) -- UNVALIDATED/DATA PIPELINE REGRESSION
    statusu bu bagimsiz bulguyla yeniden dogrulandi, degistirilmedi.
  - overnight_gap_factor: leave-one-out'ta negatif katki (REMOVE-CANDIDATE, karar degil) --
    onceki bagimsiz flag-evidence turuyla (2026-09-08) ayni yonde, iki bagimsiz kanit.
  - Sapmalar (durustce belirtildi): permutation 150 replikasyon (istenen 500-1000 degil,
    performans kisiti); raw-vs-final compression testi (Bolum 11/20) INSUFFICIENT_DATA
    (gercek production raw skoru mevcut degil); component-contribution CSV 5000 satirla
    orneklendi (tam 40014 degil).
  - Flag karari DEFERRED/BLOCKED BY BASELINE FAILURE olarak korundu. Catalyst/attention-map/
    opening-range-fade siniflandirmalari degistirilmedi (Bolum 37-39).
  - PROPOSED GOVERNANCE ACTION (uygulanmadi, sadece oneri): (1) full_universe_enriched.csv
    (SHA e3b18355...) ile full_universe_enriched_eod_only.csv (SHA 87541cc5...) arasindaki
    donusum zincirinin tek bir lineage belgesinde toplanmasi; (2) composite_score'un dogru
    tanimi (strength%, 0-16.5 degil) isigi altinda onceki raporlarin gozden gecirilmesi.
  - Sonraki arastirma sorusu: composite_score coverage-bias penceresi genisletilmeden veya
    filter_score/alignment_ratio/momentum_ratio icin gercek tarihsel coklu-zaman-dilimi veri
    elde edilmeden, ham-negatif vs winsorized-pozitif celiskisi cozulemez.
  - Uretim kodu, .env, flag, cache, scheduler veya onceki governance karari DEGISTIRILMEDI.

---

[2026-09-09] — Master Validation Prompt v1.0 (43 bolum) kaydedildi (Level A, sadece kayit)
Layer: Governance / Research
Level: A (yalnizca dokuman kaydi; hicbir kod/config/veri degistirilmedi)
Context: Meric, onceki turdaki taslak Full Baseline Reconstruction promptunu genisletip 43 bolumluk kesin/otoriter bir "Master Validation Prompt v1.0" olarak formulize etti (R1/R2/R3 reconstruction, exact-match testi, coverage/timing/compression forensics, component predictiveness, quintile/random-control/permutation/walk-forward/leave-one-out, redundancy, coverage-bias, universe/horizon/regime/time stability, H1-H10 basarisizlik-mekanizmasi hipotezleri, Case A-E karar agaci, WHAT WE KNOW/DONT KNOW/FAILED/PASSED zorunlu kapanisi).
Change: `docs/MASTER_VALIDATION_PROMPT_2026-09-09.md` — tam metin (1.570 satir) bu depoya kanonik olarak kaydedildi.
Impact: Hicbir sey degismedi. Bu, uygulamanin ayri decision-log girdileriyle takip edilecegi bir sonraki adimlarin cercevesi.
Evidence: docs/MASTER_VALIDATION_PROMPT_2026-09-09.md.

[2026-09-09] — Full Baseline Reconstruction master promptu olusturuldu + Part 0 (fizibilite) ve Part B (compression forensics) calistirildi (Level A, tesihs)
Layer: Research / Governance / Methodology
Level: A (yalnizca teshis; agirlik optimizasyonu/grid search/reverse-score/yeni feature/production/flag degisikligi YOK)
Context: `reports/baseline_ranking_health_2026-09-09.md`'nin bulgusu (composite_score random'dan kotu, %99.78 tie) uzerine Meric "Full Baseline Reconstruction + Ranking Compression Forensics" siralamasini onerdi (Part A-D, acik yasaklarla). Bu, uc-prompt ailesinin (Review Board/Hipotez Uretimi/Arastirma Portfoyu) disinda 4. ve en dar-kapsamli teshis promptu.
Change: (1) `docs/2026-09-09-full-baseline-reconstruction-master-prompt.md` yazildi -- Part 0 fizibilite kapisi ZORUNLU ilk adim olarak eklendi (kullanicinin onerisine ek). (2) Part 0 calistirildi: `volume_spike/price_momentum/trend_strength/filter_score` GUNLUK OHLCV'den (`data/price_cache/*.json`, 2.047 sembol) reconstruct edilebilir (EVET); `alignment_ratio` (1h/4h/1d) ve `momentum_ratio` (15dk/4h) bu ortamda YAPISAL OLARAK reconstruct EDILEMEZ (gecmis saatlik/4-saatlik bar verisi yok) -- UNRECONSTRUCTABLE olarak isaretlendi, sentetik deger URETILMEDI. (3) Part B.1 calistirildi (`research/ranking_compression_forensics_2026_09_09.py`, EOD-only temiz veri, n=40.014): **%99.78 tie BAGIMSIZ DOGRULANDI** (onceki turun rakamiyla birebir ortusuyor) -- composite_score'un sadece 90 benzersiz degeri var; gun-ici etkin rank cozunurlugu ORTALAMA %23.2 ama MEDYAN sadece %5.99 (53 gun). Ham girdilerin kendi kabaligi da olculdu: `score` sadece 4 benzersiz deger, `risk_reward` sadece 9.
Impact: Hicbir production/flag/skor degisikligi yapilmadi. KRITIK SINIRLAMA acikca belirtildi: sikismanin "formul tasarimindan mi" yoksa "alignment/momentum'un kendisinin de kaba olmasindan mi" geldigi bu ortamda KANITLANAMADI (UNKNOWN) -- alignment_ratio/momentum_ratio'nun gercek varyansi olculemedi (Part 0). Bu yuzden composite_score'un COK sikisik oldugu KESIN (2. bagimsiz olcum), ama "neden" sorusunun tam cevabi acik kaldi.
Status: applied - Level A partial diagnosis; Part A (4/6 reconstruction) ve Part C (dist_52w_high redundancy) sonraki tura birakildi.
Evidence: docs/2026-09-09-full-baseline-reconstruction-master-prompt.md, reports/baseline_reconstruction_part0_partB_2026-09-09.md, research/ranking_compression_forensics_2026_09_09.py.

[2026-09-03] — catalyst_factor evren-çaplı refresh denendi (Meriç onayıyla, Level B) — kapsam hedefi karşılanmadı, dürüst rapor
Layer: Research / Engineering
Level: B (Meriç onayı alındı — "Evet, kur"); FINPILOT_ENABLE_EDGAR_CATALYST'e DOKUNULMADI
Context: Araştırma Portföyü Kurulu'nun #3 önerisi. `data_repair_diagnosis_2026-09-03.md`: EDGAR ham verisi (edgar_cache/, 1.127 CIK) var ama boru hattı çalıştırılmıyordu.
Change: `research/catalyst_universe_refresh_2026_09_03.py` yazıldı — yerel `edgar_cache/tickers.json` (10.433 şirket) + `sub_*.json` (1.127 dosya) kullanarak `scanner/catalyst.py::_score_filings` ile bire bir aynı mantıkla evren-çaplı `data/catalyst_cache.json` üretti (eski hali: 8 sembol/hepsi 0.0).
Sonuç (dürüst, hedef KARŞILANMADI): 1.926 evrenin %62,25'i (1.199 sembol) skorlandı, hedef ≥%90 — 676 sembol yerel dosya eksikliği + bu ortamda `data.sec.gov`'a ağ erişimi olmaması (proxy 403, doğrulandı) nedeniyle boş bırakıldı (0.0 YAZILMADI, "bilinmiyor" sayıldı). Ayrıca skorlanan 1.199 sembolün 0'ı son 7 gün içinde dosyalama gösteriyor (yerel cache dosyaları Mayıs-2026 civarında donmuş, bugüne göre bayat) — bu yüzden bugün için her catalyst_factor dürüstçe 0.0. Boru hattının kendisi doğru çalıştığı doğrulandı (gerçek veriyle test edildi); eksik olan yalnızca güncel ağ erişimi.
Impact: Production'a hiçbir etki yok. Bir sonraki adım: bu script'i ağ erişimi olan bir ortamda (canlı sunucu/Meriç'in makinesi) çalıştırmak — o zaman hem %90 kapsam hem gerçek tazelik mümkün. Flag açma kararı ayrı, bu turda alınmadı.
Evidence: reports/catalyst_refresh_2026-09-03.md, research/catalyst_universe_refresh_2026_09_03.py, data/catalyst_cache.json, data/backtest_out/catalyst_refresh_quality_2026-09-03.json.

[2026-09-03] — c2c_5d DATA_REPAIR uygulandı: label_entry_basis eklendi (Meriç onayıyla, Level B)
Layer: Research / Engineering
Level: B (Meriç onayı alındı — "Evet, uygula")
Context: Araştırma Portföyü Kurulu'nun #1 önerisi. `reports/data_repair_diagnosis_2026-09-03.md`'nin kök-neden bulgusu: scan_ts≥15:30 taramalar ρ=0.9829, <15:30 taramalar ρ=0.9173 (>5pp sapma %5.70, %79'u 13:30-14:30 saatlerinde).
Change: (1) `fetch_full_universe_and_retest.py`'ye `label_entry_basis(scan_ts)` eklendi — ileriye dönük, gelecek fetch çalışmalarında otomatik dolacak; `c2c_5d/c2c_1d/mae_t5` hesaplama mantığına DOKUNULMADI. (2) `research/label_entry_basis_backfill_2026_09_03.py` yazıldı ve çalıştırıldı — mevcut `full_universe_enriched.csv`'yi (ağ erişimi gerekmeden, scan_ts zaten CSV'de) geriye dönük etiketledi: 100.496 satırın %79,5'i (79.935) `eod_close`, %20,5'i (20.561) `intraday`; en yoğun intraday saatler 13:30-14:45 bandı (diagnostik raporla birebir örtüşüyor). İki yeni dosya üretildi: `full_universe_enriched_labeled.csv` (tüm satır + etiket) ve `full_universe_enriched_eod_only.csv` (yalnızca temiz alt-küme, n=79.935).
Impact: Production/canlı scanner'a hiçbir etki yok. c2c_5d değerlerinin kendisi değiştirilmedi, yalnızca hangi satırların güvenilir sayılacağı işaretlendi. Bundan sonraki confirmatory koşular `_eod_only.csv`'yi tercih edebilir.
Evidence: reports/c2c_5d_label_entry_basis_2026-09-03.md, research/label_entry_basis_backfill_2026_09_03.py, data/backtest_out/full_universe_enriched_labeled.csv, data/backtest_out/full_universe_enriched_eod_only.csv, fetch_full_universe_and_retest.py.

[2026-09-03] — Araştırma Portföyü ve Kaynak Tahsisi Kurulu v1.0 oluşturuldu + ilk envanter çalıştırıldı (Level A, süreç)
Layer: Research / Governance / Methodology
Level: A (yalnızca sıralama; hiçbir Level B/C kararı bu kurul tarafından alınmadı)
Context: Meriç'in "bütün testleri nasıl değerlendirip yol izlerdin, geniş kapsamlı ama detaylı bir master prompt oluştur" talebi. Review Board v3.0 (tek deney) ve Hipotez Üretimi v1.0 (tek veri kümesi) program-seviyesinde "sırada ne var" sorusuna cevap vermiyordu.
Change: `docs/2026-09-03-arastirma-portfoyu-master-prompt.md` oluşturuldu — decision-log'u tarayıp açık kalemleri (BLOCKED/DATA_REPAIR/CONFIRMATORY_CANDIDATE/HYPOTHESIS_LOCKED) 3 kovaya (Agent-şimdi / Takvim-kilitli / İnsan-zamanı-kilitli) ayıran, Information-Gain×Blocking-count×Production-Relevance / (Agent-cost+3×Human-cost) formülüyle sıralayan bir süreç. 3 sabit kapı kuralı var (veri-bütünlüğü, kullanıcı-gerçeği, arama-bütçesi) — hiçbiri ihlal edilmemiş bulundu. İlk gerçek uygulama: 9 aktif kalem envanterlendi, ilk 3: (1) c2c_5d EOD-only etiket filtresi (kök neden zaten bulunmuş, ~2 saat agent işi + Meriç onayı, blocking-count~40), (2) PR1+PR7 (agent-maliyeti sıfır, tek risk unutulması), (3) catalyst_factor evren-çaplı refresh görevi. XLC/XLK ve yeni evren-genişletme teklifleri açıkça reddedildi (gerekçeli).
Impact: Hiçbir production/scanner/veri davranışı değişmedi. Önerilen 3 kalemin ikisi (c2c_5d filtresi, catalyst refresh) hâlâ Meriç onayı bekliyor; PR1/PR7 zaten insan-zamanı bekliyordu.
Evidence: docs/2026-09-03-arastirma-portfoyu-master-prompt.md.

[2026-09-03] — Hipotez Üretimi v1.0 uygulama #1: H3 (opening-range fade) alt-küme araması — 0 hipotez, STOP (Level A)
Layer: Research
Level: A (yalnızca analiz; üretime hiçbir etki yok)
Context: Meriç'in "pozitif getiri sağlayan hisseleri nasıl daraltabiliriz" sorusu üzerine, cherry-pick yerine `docs/2026-09-03-hipotez-uretimi-master-prompt.md`'nin tam süreciyle H3 fade sinyali (direction_threshold_matrix, 698 gözlem/59 gün/210 sembol) 6 değişken/27 kesim üzerinden arandı.
Change: `research/hgen_h3_fade_2026_09_03.py` yazıldı — fade verisi sembol kimliğiyle yeniden kuruldu (orijinal `h3_fade()` sembolü atıyordu), `sector_map_full.csv` + `full_universe_enriched.csv` ile zenginleştirildi. Arama bütçesi önceden tanımlandı (m_generation=27, m_toplam=9.781, Bonferroni |t|>4.56). 22/27 kesim değerlendirildi (5'i n<8 ile otomatik elendi, bütçeden düşülmedi). Sonuç: **0 kesim 5 şartın tamamını geçti** — hiçbiri HYPOTHESIS statüsüne yükseltilemedi, hepsi SPECULATION'da kaldı. En yakın iki aday (sector_etf=XLC t=2.36, XLK t=1.98) 4/5 şartı geçti ama eşikte düştü — kayıt altına alındı, gelecekte veri büyüyünce yeniden değerlendirilebilir.
Evidence: reports/hgen_h3_fade_2026-09-03.md, data/backtest_out/hgen_h3_fade_2026-09-03.json, research/hgen_h3_fade_2026_09_03.py.

[2026-09-03] — Hipotez Üretimi Master Prompt v1.0 oluşturuldu (Level A, metodoloji — üretim etkisi yok)
Layer: Research / Governance / Methodology
Level: A (yalnızca metodoloji dokümanı; hiçbir koda, veriye veya karara dokunmadı)
Context: Experiment #1 review board sonucunda (`reports/experiment_review_board_exp1_2026-09-03.md`) opening-range fade DISCOVERY SIGNAL statüsünde koşullu kaldı. Meriç bunun ardından "pozitif getiri sağlayan hisseleri nasıl daraltıp sonuçları pozitife çevirebiliriz" diye sordu — bu, aynı 698 gözlemlik keşif verisi üzerinde alt-küme araması yapmak anlamına geliyordu, yani tam olarak Review Board'un kendisinin "SELECTION / CHERRY-PICK RISK = HIGH" diye işaretlediği tuzak. Reddedildi; bunun yerine meşru yol (yeni pre-registered hipotez + bağımsız veri) için ayrı bir master prompt istendi.
Change: `docs/2026-09-03-hipotez-uretimi-master-prompt.md` oluşturuldu — Review Board v3.0'ın companion'ı. Zorunlu unsurlar: (1) Arama Bütçesi (m_generation, mevcut global m≈9.754 bütçesine EKLENİR), (2) Veri Karantinası (discovery seti vs. dokunulmayan bağımsız set — "mühürlenmiş keşif" verisi üzerinde yeniden keşif yasak), (3) 5 şartlı Hipotez Süzgeci (mekanistik gerekçe + etkin-N + outlier-bağımlılığı + maliyet-sonrası + düzeltilmiş eşik), (4) zorunlu Ön-Kayıt şablonu (kill criteria + başarı eşiği + kilit tarihi, test öncesi değiştirilemez), (5) Arama Günlüğü'nde TÜM denemelerin (kazanan/kaybeden) kaydı zorunlu, (6) HYPOTHESIS_LOCKED/SPECULATION statüsündeki hiçbir bulgunun ürün/karne/yatırımcı materyaline giremeyeceği açık yasak.
İlişki: Bu prompt "keşif başlamadan önce" kullanılır; Review Board v3.0 "deney bittikten sonra" kullanılır. Akış: hipotez üret (bu prompt) → ön-kaydı kilitle → bağımsız veride tek atış test et → sonucu Review Board'a sok.
Doğrulama: dosya `docs/` içine yazıldı, bu girdi decision-log'a eklendi.

[2026-08-24] — FinPilot Attention Map içerik paketi (taslak) + FinSense Academy'de 3 yeni ders — additive, hiçbiri canlıya bağlanmadı (Level A/B karışık)
Layer: Content / Documentation / Engineering
Level: A (Academy ders ekleme, glossary'ye yeni anahtar ekleme — additive, mevcut hiçbir kayda dokunmadı) + B (methodology/kart/Telegram metinleri — kullanıcıya-görünür yüzeyler için taslak, canlı dosyalara UYGULANMADI)
Context: Meriç'in iki master prompt belgesinin (2026-08-15, FinPilot Attention Map + FinSense Thinking Mirror) "içerikleri de bitirelim/geliştirelim" talebi üzerine, AskUserQuestion ile netleştirilen iki somut iş: (1) FinPilot Attention Map'in gerçek kullanıcı metinleri, (2) FinSense Academy'nin ders/vaka içerikleri.
Change — Academy (Level A, additive, uygulandı): `academy/seed_content.py`'ye 3 yeni ders eklendi — `FA-001-degerleme-yontemleri` (fundamental-analysis, domain_id=4, P/E ve DCF), `PM-001-diversifikasyon` (portfolio-management, domain_id=5), `MA-001-faiz-kararlari` (macro-analysis, domain_id=7, Fed faiz kararları). Bu 3 domain önceden SIFIR ders içeriyordu (`academy/domains.py`'deki 12 domain'den 7'si boştu; en değerli/temel 3'ü seçildi). Her ders mevcut 5 dersle birebir aynı şemayı kullanıyor (content/key_takeaways/misconceptions/real_example/quizzes/flashcards). py_compile temiz, 8/8 ders id'si ve Türkçe karakterler doğrulandı. Kalan 4 boş domain (options-derivatives, algo-trading-ai, etf-passive, crypto-alternatives) hâlâ boş — bu turun kapsamı dışında bırakıldı.
Change — Glossary (Level A, additive, uygulandı): `distribution/glossary.py`'ye 7 yeni terim eklendi (`attention_score`, `attention_tier`, `unusualness`, `big_gap`, `volatility_spike`, `far_from_high`, `high_lottery`) — mevcut 37 terime hiç dokunulmadı, sadece eklendi. `squeeze`/`volume` bayrakları için mevcut girdiler yeniden kullanıldı (tekrar tanımlanmadı). Tüm 7 yeni girdi `distribution/lint.py::check_text` ile tek tek test edildi — 0 ihlal.
Change — Web/Telegram içerik paketi (Level B, TASLAK, UYGULANMADI): `docs/2026-08-24-attention-map-content-pack-draft.md` yazıldı — methodology sayfası tam metni (mevcut `web/src/app/methodology/page.tsx`'in H2/P yapısına birebir uyumlu), demo kart metni (`CandidateCard` yapısına uyumlu), Türkçe Telegram brif örneği (`distribution/templates.py::_candidate_line` kalıbına uyumlu). Hiçbir gerçek `.tsx`/`templates.py` dosyası değiştirilmedi — bunlar hâlâ eski Grade/prob_band çerçevesini sunuyor ve öyle kalmalı, çünkü Faz 1c (formül eşdeğerliği) hâlâ kanıtlanmadı.
Yan bulgu: `distribution/lint.py`'nin kendi `DISCLAIMER_EN` sabiti kendi `guarantee` kuralına takılıyor (regex "does not guarantee" negasyonunu ayırt etmiyor) — `check_text(DISCLAIMER_EN)` 1 ihlal döndürüyor. Düzeltilmedi, sadece raporlanıyor; aynı cümle canlı methodology sayfasında da var.
Karar: Academy dersleri ve glossary terimleri additive ve düşük riskli olduğu için doğrudan uygulandı (Level A). Web/Telegram metinleri ise kullanıcıya-görünür yeni bir çerçeve vaadi taşıdığı ve Faz 1c'nin kanıt eksikliğine bağlı olduğu için TASLAK olarak bırakıldı — canlıya bağlanması hem Faz 1c'nin tamamlanmasını hem de ayrı bir Meriç onayını gerektirir.
Etki: `academy/seed_content.py` ve `distribution/glossary.py` değişti (additive, geri alınabilir); hiçbir canlı kullanıcı yüzeyi (web/Telegram) değişmedi.
Kanıt: `academy/seed_content.py` (py_compile OK, 8 ders id doğrulandı), `distribution/glossary.py` (py_compile OK, 44 girdi, 7 yeni), lint test çıktısı (7/7 yeni glossary girdisi temiz; methodology/kart/Telegram taslak metinleri temiz, tek istisna yukarıdaki disclaimer yan bulgusu), `docs/2026-08-24-attention-map-content-pack-draft.md`.

---

[2026-08-14] — Attention Map Faz 1a/1b tamamlandı (scanner mühendisliği), Faz 1c hâlâ açık — price_cache 16 gündür güncellenmiyor (Level B, kod yazıldı, üretime bağlanmadı)
Layer: Engineering / Research / Governance
Level: B (kod değişikliği; henüz canlı davranışı etkilemiyor, üretime bağlanması ayrı onay gerektirir)
Context: `reports/attention_map_migration_plan_v3_2026-08-14.md` §2.1'in uygulanması istendi — scanner'a Attention Score formülünün ihtiyaç duyduğu 4 alanı hesaplama/export etme işi. Kapsam kasıtlı olarak dar tutuldu: sadece `scanner/features.py` + `scanner/evaluate.py` + testler; `snapshot_builder.py`/`schema.py`/`prepublish_gate.py`/web/telegram'a dokunulmadı.
Change: (1) `scanner/features.py`'e üç fonksiyon eklendi: `compute_dist_52w_high`, `compute_gap_pct`, `compute_rvol_daily` — üçü de bağımsız çalıştırılıp elle hesaplanan beklenen değerlerle doğrulandı (0.9911 / 4.7619 / 3.0, birebir eşleşti), eksik/boş veri durumunda güvenli şekilde 0.0 dönüyor. (2) `scanner/evaluate.py`'nin return dict'ine 4 alan eklendi: `dist_52w_high`, `gap_pct`, `rvol_daily`, `squeeze_factor` (squeeze zaten hesaplanıyordu, sadece export'a yazılmıyordu) — mevcut `_score_input` sözlüğüyle çakışma yok, ayrı dict. (3) `tests/test_attention_map_features.py` (yeni) + `tests/test_evaluate.py` güncellemesi eklendi. (4) `research/attention_score_formula_overlap_2026_08_14.py` (yeni) — export formülü (§1.1) ile üretim formülü (§1.3) arasındaki eşdeğerliği gerçek `price_cache` barlarıyla ölçmek için yazıldı.
Bulgu (Faz 1c hâlâ AÇIK — beklenenden daha köklü bir sebeple): formula-overlap script'i `data/backtest_out/attention_score_formula_overlap_2026-08-14.json`'da 0/12 karşılaştırılabilir satır buldu. Sebep sadece "bugünün barı henüz yok" değil — `data/price_cache/`'te örneklenen 12/12 sembolün son barı **2026-07-29** tarihinde donmuş durumda, yani canlı shortlist'in tarama tarihinden (2026-08-14) 16 gün geride. price_cache dizinindeki dosyalar 2026-08-10'da yazılmış ama içerdikleri veri yine de 2026-07-29'da kesiliyor — güncelleme pipeline'ı bir yerde durmuş görünüyor. "Yarın tekrar dene" çözümü YETERSİZ; önce price_cache güncelleme sürecinin neden durduğu ayrıca araştırılmalı.
Karar: Faz 1a/1b (scanner kodu) tamamlandı ve doğrulandı, ama Faz 1c (canlı formül eşdeğerliği) bu bulgu çözülmeden ilerletilemez. Faz 2'ye (web/telegram/schema) geçiş için hem Faz 1c'nin tamamlanması hem de Meriç onayı gerekiyor — henüz hiçbiri yok.
Etki: Üretim scanner/snapshot/ranking DEĞİŞMEDİ — yeni kod hiçbir canlı akışa bağlı değil, feature flag açılmadı.
Kanıt: `scanner/features.py`, `scanner/evaluate.py` (git diff), `tests/test_attention_map_features.py`, `tests/test_evaluate.py`, `research/attention_score_formula_overlap_2026_08_14.py`, `data/backtest_out/attention_score_formula_overlap_2026-08-14.json` (0/12 comparable), `data/price_cache/*.json` (örneklenen 12 sembolün hepsi son-bar=2026-07-29).

---

[2026-08-14] - Dikkat Haritası planı v3 (final): temiz tek formül, canlı CSV doğrulandı, kaynak artifact üretildi (Level B, onay bekliyor)
Layer: Product / Engineering / Governance
Level: B (ürün değişikliği; Meriç onayı gerekli)
Context: v3 planı temiz tek formülle yeniden yazıldı. Doğrulama rakamları artık kaynaklı: research/attention_score_validation_2026_08_14.py → data/backtest_out/attention_score_validation_2026-08-14.json. Canlı CSV (shortlist_20260814_1157.csv) ile alan eşleme doğrulandı.
Change: (1) Doğrulama artifact üretildi: matched-control p=0.055, precision 61.8%, coverage 52.5%, lift 1.52x, ay-ay lift 1.70-3.34x (5 ay kapsamlı — 2025-09, 2026-04/05/06/07; 2025-10/11/12 ve 2026-01/02/03 veri yetersiz). (2) v3 planı temiz tek formülle yazıldı — export formülü (§1.1) ve üretim formülü (§1.3) ayrı ayrı net. (3) Canlı CSV doğrulandı: volume_multiple, ann_vol_pct, lottery_factor, overnight_gap_factor, ema_gap_pct var; dist_52w_high, gap_pct, rvol, squeeze_factor yok — scanner'a 4 yeni hesaplama gerekli. (4) ranking_score çelişkisi uzlaştırıldı: iki test farklı şey ölçüyor, her ikisi de tahmin etmiyor sonucuna işaret ediyor.
Impact: Plan v3 Meriç onayı bekliyor. Onay sonrası Faz 1a (scanner features) ile başlanır. Locked OOS NOT_OPENED.
Status: pending - Level B, Meriç onayı bekliyor.
Evidence: reports/attention_map_migration_plan_v3_2026-08-14.md, data/backtest_out/attention_score_validation_2026-08-14.json, data/shortlists/shortlist_20260814_1157.csv.

---

[2026-08-14] — LAUNCH_CHECKLIST.md taze doğrulama: Şart 1 (10 ardışık gün) TAMAMLANDI, Şart 5 (karne by_grade) "olgunlaşıyor" notu geri çekildi (Level A, kontrol; Meriç onayıyla checklist güncellendi)
Layer: Governance / Distribution
Level: A (salt-okunur doğrulama + Meriç onaylı checklist güncellemesi)
Bağlam: Meriç'in "tekrar kontrolleri sağla" talebiyle LAUNCH_CHECKLIST.md'nin 10 şartı taze kanıtla yeniden doğrulandı.
Bulgu 1 (Şart 1): `data/distribution.db/broadcast_queue` doğrudan sorgulandı — 2026-08-03..07 ve 2026-08-10..14 (hafta sonu hariç 10 işlem günü) hepsi `status='sent'`, ara boşluk yok. Önceki checklist notu (11 Ağu doğrulaması, "7 gün, 3 gün kaldı") güncel; seri bugün itibariyle 10/10'a ulaştı.
Bulgu 2 (Şart 5): `data/distribution/snapshot_2026-08-10..14.json` tek tek açıldı — `karne.by_grade` 4/5 günde tamamen boş, yalnız 08-12'de `B: n=1`. Önceki checklist notundaki "4-6 Ağu'da B/C'de dolmaya başladı, olgunlaşma sürüyor" anlatısı GÜNCEL VERİYLE DESTEKLENMİYOR — veri büyümüyor, dalgalı/ince kalıyor.
Diğer şartlar (2,3,6,7,8,9,10): repo genelinde (docs/, reports/, DB tabloları `waitlist`/`tg_feedback`/`demo_feedback`/`beta_invites`/`premium_events`) yeni kanıt aranmadı/bulunamadı — hepsi 0 veya boş, önceki "açık" durumları değişmedi.
Karar: Meriç onayıyla LAUNCH_CHECKLIST.md satır 6 ve 10 güncellendi (Şart 1 işaretlendi, Şart 5 notu düzeltildi). Diğer şartlara dokunulmadı.
Etki: Üretim/scanner/entry-exit/risk DEĞİŞMEDİ; yalnız durum panosu (LAUNCH_CHECKLIST.md) güncellendi.
Kanıt: `data/distribution.db` (broadcast_queue, bu turda sorgulandı); `data/distribution/snapshot_2026-08-10.json` .. `snapshot_2026-08-14.json` (bu turda okundu); `data/distribution.db` tabloları waitlist/tg_feedback/demo_feedback/beta_invites/premium_events (bu turda sayıldı, hepsi 0).

---

[2026-08-13] — FinPilot/Finsense repo ve doküman hijyeni denetimi tamamlandı ve bağımsız doğrulandı (Level A; migration pending — Meriç onayı bekliyor)
Layer: Governance / Engineering / Content / Research
Level: A (salt-okunur audit ve öneri); önerilen taşıma/rename Level B, silme/geri-dönüşsüz işlem Level C
Bağlam: `docs/2026-08-06-DOSYA-DUZENI-MASTER-PROMPT.md` master prompt'uyla üretilen denetim (`reports/repo_document_hygiene_audit_2026-08-13.md`) ikinci bir yürütücü (Cowork) tarafından kanıta karşı doğrulandı. Ölçümler birebir teyit edildi: Borsa kök 81 py / 30 md, Finsense 33 py / 37 md; `Finsense/academy/export_lessons.py`, `Borsa/archive/FinanceAcademy/academy/seed_content.py`, `Borsa/api/routers/academy.py:37` (`from academy.orchestrator import`) ve `scripts/publish_web.py` mevcut ve doğrulandı.
Bulgu: (P0) `docs/INDEX.md` makine-manifestindeki `academy-content` authority'si repo-qualified DEĞİL; Borsa `academy/` (7 py, API runtime) ile Finsense `academy/` (33 py, içerik fabrikası + export) AYRI kod/veri sınırlarında yaşıyor. Reviewer notu: bu yalnız doküman belirsizliği değil, iki paralel academy kod tabanı arasında KOD KAYMASI (drift) riski; 33-e-7 kapasite asimetrisi Finsense'in kanonik, Borsa/academy'nin eski köprü olduğunun güçlü (kesin değil) sinyalidir. Bu bir bakım/governance borcudur ama LANSMAN BLOKÖRÜ DEĞİLDİR (web /academy statik `academy_lessons.json` artifact'ini okur). Root sprawl (81 kök py, ~37 research adayı; 30+ doküman) migration adayıdır; hiçbir dosya 'dead' ilan edilmedi (seed_content_en = aktif ama ayrı workflow).
Değişiklik: Hiçbir dosya taşınmadı/silinmedi/yeniden adlandırılmadı. Denetim raporu + fazlı migration önerisi hazırlandı (Faz 0 = lansman sırasında yalnız karar hazırlığı; Faz 1 = lansman sonrası onaylı git mv batch'leri).
Etki: Üretim scanner/distribution/execution/broker/web-runtime/publish davranışı DEĞİŞMEDİ. Academy authority/cutover kararı VERİLMEDİ. `web/public/academy_lessons.json` release-artifact olarak kabul edildi.
Durum: pending — Meriç onayı bekliyor. En yüksek öncelikli tek karar: Academy authority'yi repo-qualified netleştirmek (bridge retained vs cutover) — lansman sonrası. Bu kayıt migration/authority değişikliği DEĞİLDİR.
Kanıt: reports/repo_document_hygiene_audit_2026-08-13.md; docs/2026-08-06-DOSYA-DUZENI-MASTER-PROMPT.md; docs/INDEX.md; Borsa/api/routers/academy.py:37; Finsense/academy/export_lessons.py; scripts/publish_web.py.

---

[2026-08-13] — 5-yeni-soru fizibilite taraması: Soru-2 (485 flagged sembol sınıflandırması) için ucuz bir ayırt-edici bulundu (%56'sı yuvarlak split-oranına uyuyor); Soru-5 (abstention bağımsız-veri retest) TAKVİM-ENGELLİ (mevcut veri zaten train/calib/valid'in tamamını tüketmiş); Soru-1/3/4 dış-veri veya insan-zamanı gerektiriyor, bu oturumdan yapılamaz (Level A, fizibilite+ilk-bulgu)
Layer: Research / data
Level: A
Bağlam: Meriç'in onayladığı 5 yeni-soru listesinden ("sürpriz", "485-sembol sınıflandırması", "execution/capacity", "kullanıcı-gerçeği", "abstention bağımsız-veri") hangisinin bu oturumdan, ek veri/insan olmadan ilerletilebileceği tarandı.
1) SORU 5 (abstention bağımsız-veri) — BLOCKED, takvim: `production_candidate_validation_2026-08-12.json/abstention_independent_split` train=40+calibration=16+validation=25=81 gün kullanmış; `full_universe_enriched.csv`'nin c2c_5d-dolu tarih aralığı (2025-09-11→2026-07-31, 82 gün) BUNU NEREDEYSE TAMAMEN KAPSIYOR. Şu an genuinely-yeni (train/calib/valid'de hiç kullanılmamış) bir tarih aralığı YOK — 5-günlük ileri-getiri hesaplanabilmesi için takvimin ilerlemesi (haftalar) gerekiyor. Bu, sabırla beklenmesi gereken bir kapı, bugün zorla açılamaz.
2) SORU 2 (485 sembol sınıflandırması) — İLK UCUZ AYIRT-EDİCİ bulundu: her flagged sembolün en-büyük tek-günlük sıçraması, yuvarlak split-oranlarına (2x,3x,...,100x, log-ölçekli %12 tolerans) ne kadar yakın diye test edildi. Sonuç: 272/485 (%56,1) yuvarlak-orana uyuyor (örn. YHC +10.608%≈100x, COOK +5.469%≈50x) — muhtemelen GERÇEK ama fiyat-cache'inde AYARLANMAMIŞ reverse-split. Kalan 213/485 (%43,9) hiçbir yuvarlak orana uymuyor (örn. FFAI +1.542.757%, MIMI +1.027.400%, EDBL +190.809%) — muhtemelen VERİ-HATASI/bad-print, gerçek bir corporate-action değil. Bu, tam-kesin bir sınıflandırma DEĞİL (yalnız en-büyük sıçramaya bakıyor, provider-seviyesi doğrulama yok) ama ucuz bir ilk-ayrıştırma: %56'lık kısım "düzeltilebilir" (split-adjust), %44'lük kısım muhtemelen "sadece dışlanabilir" (veri-hatası, düzeltilecek gerçek bir olay yok).
3) SORU 1 (sürpriz/event) ve SORU 3 (execution/capacity) — BLOCKED, dış-veri: event-feed / observed spread-ADV-fill verisi bu ortamda yok, `full_universe_enriched.csv`'de de yok (grep doğrulandı: `dollar_adv`/`spread_bps` gibi alanlar tarihsel export'ta YOK — yalnız CANLI shortlist'te var, geriye-dönük değil).
4) SORU 4 (PR1/PR7 kullanıcı görüşmesi) — BLOCKED, insan-zamanı: script hazır (`reports/user_research_kit_2026-08-10.md`), yalnız Meriç'in görüşme yapması gerekiyor.
Karar: Bu turda yalnız Soru-2'nin ucuz ayırt-edicisi ilerletildi (bulgu yukarıda, EXPLORATORY — provider-seviyesi doğrulama olmadan kesin sınıflandırma sayılmaz). Diğer 4 soru resmi olarak BLOCKED (2'si dış-veri, 1'i insan-zamanı, 1'i takvim) — bu oturumdan daha fazla ilerletilemez, sahte-ilerleme üretilmeyecek.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: bu turun bağımsız script'i (kaydedilmedi, çıktı yukarıda); `data/backtest_out/price_cache_integrity_audit_2026-08-11.json`; `data/backtest_out/production_candidate_validation_2026-08-12.json/abstention_independent_split`.

---

[2026-08-13] — KONTROL TURU #6: repo-durumu + decision-log bütünlüğü + CANLI SHORTLIST'İN KENDİSİYLE DOĞRUDAN AMPİRİK TEYİT — `ranking_score`=`legacy_quality_score` satır-satır birebir eşit (`ranking_method`="legacy_quality"), ayrıca `score_component_breakdown`/`score_component_total`/`recommendation_score` alanları CANLI ÇIKTIDA ZATEN VAR — "export'a eklenmeli" önerisi "yeni alan hesapla"dan "zaten hesaplanan alanı research pipeline'a bağla"ya düşürüldü (Level A, kontrol)
Layer: Research / governance
Level: A
Bağlam: Meriç'in "tekrar kontrolleri sağla, nelere baktık/ne yapmalıyız/nelere dikkat etmeliyiz" talebiyle rutin bir bütünlük+doğrulama turu yapıldı.
1) DECISION-LOG BÜTÜNLÜĞÜ: 824 satır, bugünün (08-12) 8 girdisi de sırayla ve bozulmadan mevcut (grep ile doğrulandı) — üzerine yazma/çakışma yok.
2) REPO DURUMU: son ~40 dakikada yalnız rutin canlı-tarama çıktıları değişmiş (`data/distribution/scan_export_*partial*.json`, `data/shortlists/shortlist_202608 13_*.csv` — 2-5 dakikada bir yeni dosya, canlı scanner aktif çalışıyor). `reports/`/`research/` altında YENİ dosya yok — paralel süreç şu an duraklamış görünüyor.
3) EK DOĞRULAMA (fırsatçı, bu turda bulundu): en-güncel canlı shortlist (`data/shortlists/shortlist_20260813_1146.csv`, 198 satır, GERÇEK üretim çıktısı) doğrudan okundu. Sonuç: HER satırda `ranking_score` == `legacy_quality_score` (birebir, örn. RRR: ikisi de 57,073; CZR: ikisi de 65,631) ve `ranking_method` sütunu her satırda literal `"legacy_quality"` string'i taşıyor. Bu, önceki iki girdideki (.env dosyası + Meriç'in container-içi kontrolü) bulguyu ÜÇÜNCÜ, EN GÜÇLÜ kanıt-katmanıyla (doğrudan canlı veri, kod/config çıkarımı değil) doğruluyor. `composite_score` alanı da aynı satırlarda mevcut ama `legacy_quality_score`'dan sistematik olarak farklı (bazı satırlarda büyük fark, örn. HWKN: composite=3 vs legacy=11,14) — gün-içi rank-korelasyonun yüksek (0,867) olması satır-satır aynı oldukları anlamına gelmiyor.
4) YENİ, ÖNEMLİ-UCUZLAŞTIRICI BULGU: canlı shortlist CSV'sinde `score_component_breakdown`, `score_component_total`, `recommendation_score`, `score_input`, `score_feature_flags` alanları ZATEN MEVCUT (üretim zaten hesaplıyor ve yazıyor). Önceki girdide ("Score yeniden-tasarım önceliklendirmesi") bunu "export'a eklenmesi gerekiyor" (yeni instrümantasyon) olarak önermiştim — YANLIŞ ÇERÇEVE: iş, YENİ bir hesaplama eklemek değil, ZATEN CANLIDA ÜRETİLEN bu alanları `full_universe_enriched.csv`'yi besleyen araştırma pipeline'ına (`research/score_replay.py` veya eşdeğeri) DAHİL ETMEK. Bu, tahmin edilenden çok daha ucuz bir data-repair kalemi.
Karar: Hiçbir üretim/araştırma-sonucu değişmedi; bu tur salt doğrulama ve önceki önerinin maliyet-tahminini düzeltme. Güncellenmiş öncelik: `research/score_replay.py`'ye (veya export-üreten script'e) canlı shortlist/scan_export JSON'larından `ranking_score`,`legacy_quality_score`,`score_component_breakdown`,`score_component_total` alanlarını JOIN eden bir adım eklemek — yeni hesaplama gerekmiyor, sadece zaten-var-olan veriyi araştırma export'una taşımak.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: `data/shortlists/shortlist_20260813_1146.csv` (bu turda okundu, 198 satır); decision-log grep-bütünlük kontrolü (bu turda).

---

[2026-08-12] — CANLI SUNUCUDA TEYİT EDİLDİ (Meriç): finpilot_api container'ında `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` → `legacy_composite_ranking_enabled()`→`False` → `ranking_score`=`legacy_quality_score` KESİNLEŞTİ; "KRİTİK DÜZELTME/BÜYÜK BULGU" zincirinin son açık maddesi kapandı (Level A, kanıt-teyidi)
Layer: Research / product / governance
Level: A
Bağlam: Bu oturumun kod-seviyesi bulgusu (`ranking_score`'un `.env` dosyasına göre `legacy_quality_score`'a eşit olduğu, dolayısıyla canlı ürünün Grade A/B/C sıralamasının `composite_score` değil `legacy_quality_score` kullandığı) tek bir sınırlamayla bırakılmıştı: repo-dosyası (`.env`) seviyesinde doğrulandı ama ÇALIŞAN sürecin kendi ortam-değişkeni bu oturumdan sorgulanamamıştı. Meriç, `finpilot_api` container'ında doğrudan kontrol edip `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` ve `legacy_composite_ranking_enabled()→False` sonucunu bildirdi.
Sonuç: Zincir artık UÇTAN UCA kesinleşti: canlı Grade A/B/C sıralaması ve web-context sıralaması (`distribution/snapshot_builder.py:99-116,179,408`) → `ranking_score` → `legacy_quality_score` (atr_pct+rvol+squeeze+lottery+overnight birleşimi) → bu oturumda geriye-dönük backfill+test edildi (`ranking_score_backfill_test.py`) → composite_score ile aynı "forward-bilgi yok" verdiktini veriyor (rho=+0,02, CI 0'ı içeriyor) AMA composite_score'un aksine seçimi rastgeleden ölçülebilir-kötü DEĞİL, nötr (medyan +0,33 vs rastgele +0,28).
Karar: "Score'un forward-öngörü gücü yok" sonucu artık canlı ürünün GERÇEKTEN kullandığı alan için de tam teyitli — bu program tarihinin en önemli dış-geçerlilik (external validity) boşluğu kapandı. "Seçim aktif zarar veriyor" iddiası ise composite_score'a özgü kalıyor; canlı ranking_score için bu iddia YOK (nötr sonuç). Bu ayrım, gelecekteki her türlü ürün/iletişim kararında (örn. "FinPilot'un mevcut sıralaması rastgeleden kötü mü" sorusuna cevap verirken) referans alınmalı.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu yalnızca hangi alanın hangi bulguyla ilişkilendirileceğine dair bir doğrulama.
Kanıt: Meriç'in canlı `finpilot_api` container kontrolü (bu turda bildirildi); önceki 2 girdi (`scanner/evaluate.py`/`score_engine.py`/`distribution/snapshot_builder.py` kod-izi + `ranking_score_backfill_test.py` sonuçları).

---

[2026-08-12] — ranking_score/legacy_quality_score GERİYE-DÖNÜK BACKFILL VE TEST EDİLDİ (ek veri gerekmedi) — merkezi bulgu SARSILMADI, tersine İKİ BAĞIMSIZ SKOR FORMÜLÜYLE DE teyit edildi; composite_score'un rastgeleden ÖLÇÜLEBİLİR DERECEDE KÖTÜ olması ranking_score'da YOK (Level A, araştırma — önceki "kritik düzeltme" girdisinin kapanışı)
Layer: Research / quant
Level: A
Bağlam: Önceki girdide ("KRİTİK DÜZELTME/BÜYÜK BULGU") tespit edilen boşluk — canlı ürünün asıl kullandığı `ranking_score`/`legacy_quality_score` alanının hiç test edilmemiş olması — Meriç'in "bedava, mevcut veriyle" ilkesiyle hemen kapatıldı: `ranking_score_backfill_test.py`. `scanner/score_engine.py::compute_legacy_quality_score` formülü BİREBİR (satır-satır) kopyalanarak, mevcut export kolonlarıyla (regime, direction, score, atr_pct_real, rvol, squeeze_factor, lottery_factor, overnight_gap_factor — hepsi zaten export'ta) her satır için geriye-dönük hesaplandı. Yeni veri/backfill-altyapısı gerekmedi.
Sonuçlar (43.279 satır, 81 gün):
  **Test A (composite_score ile ne kadar aynı?):** gün-içi Spearman(legacy_quality_score, composite_score)=+0,867 (t=+97,2, n_gün=47, composite_score dolu olduğu satırlarda) — YÜKSEK KORELE. İki skor pratikte çoğunlukla AYNI adayları üst sıraya taşıyor.
  **Test B (c2c_5d ile forward-korelasyon, composite_score'la AYNI metodoloji):** legacy_quality_score ort-rho=+0,0195 (t=+0,94, boot-CI=[-0,042,+0,084], null-ort=-0,016) → **ÖLÜ**, composite_score ile TAM AYNI VERDİKT (composite_score: rho=-0,0277, t=-1,10, CI 0'ı içeriyor, aynı şekilde ölü). **Merkezi bulgu ("score'un forward-bilgisi yok") artık İKİ BAĞIMSIZ, YÜKSEK-KORELE AMA FORMÜL OLARAK FARKLI skor değişkeniyle teyitli — daha da sağlam.**
  **Test C (top-10 portföy, medyan-bazlı — KONTROL TURU #5 dersi uygulanarak ortalama DEĞİL medyan birincil alındı):** legacy_quality_score top-10 gün-medyanlarının-medyanı=+0,333 vs rastgele=+0,278 (istatistiksel olarak ayrışamaz, ~aynı) vs composite_score=-0,567 (rastgeleden daha kötü, önceki bulguyla tutarlı). Yani: composite_score seçimi RASTGELEDEN ÖLÇÜLEBİLİR DERECEDE KÖTÜ (bilinen bulgu), ama legacy_quality_score/ranking_score seçimi rastgeleden ne iyi ne kötü — NÖTR. (NOT: ortalama-bazlı ilk hesap legacy_quality_score için yanıltıcı şekilde pozitif çıkmıştı — +4,37% — bu, tam da KONTROL TURU #5'te öğrenilen mean/outlier-hassasiyeti örneği; medyana geçince kayboldu, doğru sonuç budur.)
Karar: Programın "score'un forward-öngörü gücü yok" merkezi sonucu GEÇERLİ ve şimdi iki bağımsız formülle DAHA GÜÇLÜ. Tek gerçek fark: composite_score'un seçimi aktif-olarak-rastgeleden-kötü iken, ranking_score/legacy_quality_score'un seçimi sadece bilgisiz (rastgeleyle aynı) — bu ayrım küçük ama pratik: eğer canlı ürün gerçekten legacy_quality_score/ranking_score kullanıyorsa (Meriç'in .env-teyidi hâlâ bekleniyor), "seçim aktif zarar veriyor" iddiası composite_score'a özgü kalır, ranking_score'a genellenemez. Kalan tek açık iş: Meriç/canlı-erişimli tarafın `.env`'deki `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING` değerini canlı süreçte teyit etmesi.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: `ranking_score_backfill_test.py` (bu turda yazıldı, repo köküne kondu); ek bash-tek-satır medyan-kontrolü (bu turda, kaydedilmedi, çıktı yukarıda).

---

[2026-08-12] — KRİTİK DÜZELTME/BÜYÜK BULGU: canlı ürünün GERÇEK sıralama alanı `composite_score` DEĞİL, `ranking_score`'dur (şu an = `legacy_quality_score`, `.env`'deki `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0` nedeniyle) — bu alan `full_universe_enriched.csv`'de HİÇ YOK ve bu programın 2 yıllık tarihinde HİÇBİR deney tarafından test edilmemiş; önceki girdideki "atr/rvol canlı formülde yok" iddiam bu yüzden YANLIŞTI, düzeltiliyor (Level A, kod-denetimi + öz-düzeltme)
Layer: Research / product / governance
Level: A
Bağlam: Meriç'in önceki girdideki iki "sürpriz" bulguya ("atr/rvol/dist_52w_high/risk_reward canlı formülde yok" ve "ağırlık-bütçesinin %60'ı test edilmemiş") daha derin bakma isteğiyle `scanner/evaluate.py` incelendi.
KOD-ZİNCİRİ (satır 661-724, 814-818): `evaluate.py`, HER taranan aday için ÜÇ farklı skor hesaplıyor ve HEPSİNİ döndürüyor: `composite_score` (=`compute_recommendation_strength`, benim şimdiye kadar test ettiğim alan), `legacy_quality_score` (=`compute_legacy_quality_score` — regime/direction/raw_score/**atr_pct**/**rvol**/squeeze/lottery/overnight'ı birleştiren AYRI bir formül), ve `ranking_score` = `_composite_score if legacy_composite_ranking_enabled() else _legacy_quality_score`. `legacy_composite_ranking_enabled()` → `os.environ.get("FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING","0")=="1"`. `.env` dosyasında bu değişken **`0`** — yani bugün `ranking_score` = `legacy_quality_score`'a EŞİT.
CANLI ÜRÜNDE HANGİSİ KULLANILIYOR: `distribution/snapshot_builder.py:99-116,179,408` — HEM "web context" satırları (`measurable.sort(key=_sort_key)`, satır 179) HEM de asıl GRADE A/B/C adayları (`graded.sort(key=_sort_key)`, satır 408) `_sort_key()` ile sıralanıyor; bu fonksiyon skoru `row.get("ranking_score") or row.get("legacy_quality_score") or row.get("composite_score") or row.get("score")` fallback-zinciriyle seçiyor — yani `ranking_score` (=`legacy_quality_score`) DOLU olduğu sürece BİRİNCİL alan, `composite_score` yalnız fallback. `distribution/prepublish_gate.py:37` de `ranking_score`'u zorunlu alan olarak listeliyor.
SONUÇ (kritik): `full_universe_enriched.csv`'de `ranking_score` VEYA `legacy_quality_score` kolonu YOK (header doğrulandı: yalnız `score`,`composite_score`,`finpilot_score` var). `research/score_replay.py` da bu alanı hesaplamıyor (grep, sıfır eşleşme). Yani: reverse-ranking, extension/exhaustion, Mirror Analysis, P0-P3, bu oturumun score-backward-looking bulgusu, score_component_decomposition.py — BU PROGRAMDAKİ HER TEK SCORE-DENEYİ, canlı ürünün asıl kullandığı alanı DEĞİL, ikincil/fallback bir alanı test etmiş.
ÖZ-DÜZELTME: Önceki girdideki "en-umut-verici 4 bileşen (atr/rvol/dist_52w_high/risk_reward) canlı formülde HİÇ YOK" iddiam YANLIŞTI — `atr_pct` ve `rvol` zaten `legacy_quality_score` içinde (1,5× ve 1,5× ağırlıkla) kullanılıyor VE bu, `ranking_score` aracılığıyla muhtemelen ŞU AN CANLI ÜRÜNÜN GERÇEKTEN KULLANDIĞI skor. `dist_52w_high` ve `risk_reward` hâlâ hiçbir skor formülünde yok (bu kısım doğru kalıyor).
ÖNEMLİ SINIRLAMA: `.env`'in canlı çalışan süreçle bire-bir aynı olduğu bu turda dosya-seviyesinde doğrulandı (repo'daki 5 farklı script `load_dotenv(ROOT/".env")` ile bu dosyayı yüklüyor) ama ÇALIŞAN sürecin ortam-değişkenlerini (systemd/process-env) bu turda DOĞRUDAN sorgulamadım — bu son %5'lik doğrulama BLOCKED (canlı sunucuya erişim bu oturumda yok).
Karar: Bu, programın en yüksek-öncelikli data-repair kalemi olarak yeniden sıralanmalı — Meriç'in önceki 2 sorusundan (soru 1: ranking_score backfill, soru 2: score_component_breakdown export) BİRİNCİSİ artık BİRİNCİ ÖNCELİK: (a) `.env`'in canlı sunucudaki gerçek değeriyle bu bulgunun doğrulanması (Meriç veya canlı-erişimi-olan taraf), (b) `research/score_replay.py`'ye `legacy_quality_score`/`ranking_score`'u hesaplayıp export'a ekleyen bir adım eklenmesi, (c) TÜM geçmiş score-negatif bulgularının `ranking_score` ile TEKRAR test edilmesi — mevcut "score bilgi taşımıyor" sonucu `composite_score` için EVIDENCE seviyesinde kalıyor ama `ranking_score`/`legacy_quality_score` için hâlâ test edilmemiş/UNKNOWN.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu turda salt kod-okuma yapıldı. Ama bu bulgu DOĞRULANIRSA, bu programın "score'un forward-bilgisi yok" sonucunun canlı ürüne UYGULANABİLİRLİĞİ ciddi şekilde sorgulanır hale gelir.
Kanıt: `scanner/evaluate.py:661-724,814-818`, `scanner/score_engine.py:193-222,238-240`, `distribution/snapshot_builder.py:99-116,179,408`, `distribution/prepublish_gate.py:37`, `.env:56` (`FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0`), `research/score_replay.py` (grep, ranking_score/legacy_quality_score için sıfır eşleşme).

---

[2026-08-12] — Score yeniden-tasarım önceliklendirmesi: gerçek üretim formülü (`scanner/score_engine.py::compute_recommendation_score`) koduyla istatistiksel decomposition eşleştirildi — catalyst_factor AKTİF-AMA-ÖLÜ-FEATURE (bug), squeeze/overnight_gap istatistiksel-ölü-ama-canlı-ağırlıklı, lottery_factor tek gerçek sinyal ve zaten aktif; en-umut-verici 4 bileşen (atr/rvol/dist_52w_high/risk_reward) CANLI FORMÜLDE HİÇ YOK; canlı formülün ağırlık-bütçesinin ~%60'ı (alignment_ratio/momentum_ratio/filter_score/regime/direction/3-binary) export'ta kolon olmadığı için HİÇ TEK-TEK TEST EDİLEMEMİŞ (Level A, araştırma+kod-denetimi)
Layer: Research / quant
Level: A
Bağlam: Meriç'in "score yeniden tasarlanırsa ne atılır ne tutulur" sorusuna somut cevap için `scanner/score_engine.py:99-190` (`compute_recommendation_score`, gerçek üretim ağırlıkları) okundu ve `score_component_decomposition.py`'nin istatistiksel sonuçlarıyla satır-satır eşleştirildi. `.env` dosyası kontrol edildi: `FINPILOT_ENABLE_SQUEEZE_FACTOR=1`, `FINPILOT_ENABLE_EDGAR_CATALYST=1`, `FINPILOT_ENABLE_LOTTERY_FADE=1`, `FINPILOT_ENABLE_OVERNIGHT_GAP=1` — dördü de CANLI AKTİF (env-gated ama açık).
Bulgular:
1) **catalyst_factor: AKTİF AĞIRLIK (±1,5×macro_mult) AMA VERİ-KATMANI KIRIK** — tam-evrende sabit `''`/`'0.0'` (önceden bilinen bulgu, bu turda kod-seviyesinde kesinleşti: `_catalyst_enabled()`=True olduğu halde `compute_catalyst_factor`'ün çıktısı hep sıfır). Ayrıca lottery_penalty'yi "catalyst>0.3 ise %50'ye kadar hafiflet" mantığı da bu yüzden HİÇBİR ZAMAN tetiklenmiyor — ölü feature, sadece kendi ağırlık-slotunu değil, lottery-relief mekanizmasını da devre dışı bırakıyor.
2) **overnight_gap_factor: AKTİF AĞIRLIK (-1,0) AMA İSTATİSTİKSEL OLARAK ÖLÜ** (t=-1,19, CI 0'ı içeriyor) — canlıda gerçek bir ceza uyguluyor ama bu cezanın forward-getiriyle ilişkisi kanıtlanamadı.
3) **squeeze_factor: AKTİF AĞIRLIK (+0-1,5×macro_mult) AMA GÜVENİLMEZ ÖLÇÜM** — boot-CI 0'ı dışlıyor gibi görünüyor ama n_gün=23 (ince) ve null-kontrolü kendisi sıfırdan uzak (+0,0338) — ne kanıtlanmış-pozitif ne kanıtlanmış-ölü, ÖLÇÜLEMEZ durumda.
4) **lottery_factor: AKTİF AĞIRLIK (-2,0) VE TEK BONFERRONI-HAYATTA-KALAN GERÇEK SİNYAL** — formülde zaten doğru yönde kullanılıyor, değişiklik gerekmiyor (yalnız ağırlık-büyüklüğünün optimize olup olmadığı ayrı bir soru, test edilmedi).
5) **YAPISAL SÜRPRİZ:** decomposition'da en-umut-verici (yalnız-konvansiyonel, t=3,1-4,1) 4 bileşen — `atr`, `rvol`, `dist_52w_high`, `risk_reward` — canlı `compute_recommendation_score` formülünde HİÇ DOĞRUDAN TERİM OLARAK YOK. Bunlar yalnızca KULLANILMAYAN `compute_legacy_quality_score` (farklı bir 0-100 formülü, `legacy_composite_ranking_enabled()` ile kapalı) içinde mevcut. Yani formülün en-umut-verici sinyalleri şu an canlı skora hiç girmiyor.
6) **EN ÖNEMLİ BOŞLUK:** canlı formülün ağırlık-bütçesinin büyük kısmı (`raw_score`×0,5, `filter_score`×1,5, `alignment_ratio`×2,0, `momentum_ratio`×1,5-2,5, `regime`/`direction`×2,0+2,0, `volume_spike`/`price_momentum`/`trend_strength`×0,5+0,5+0,5 — toplam ~10-12 puanlık bir bütçenin çoğu) `full_universe_enriched.csv` export'unda AYRI KOLON OLARAK YOK, dolayısıyla bu decomposition'da (ve bilinen hiçbir önceki deneyde) TEK TEK TEST EDİLEMEDİ. Şu ana kadar test edilen her şey ya bu terimlerin ÖNCEDEN-TOPLANMIŞ hali (`score`, `composite_score` — ölü çıktı) ya da toplamın dışındaki ek-katman feature'lardı (lottery/gap/squeeze/catalyst).
Karar: Bu bir üretim-değişikliği DEĞİL, yalnız bir önceliklendirme haritası. Eğer/ne zaman score yeniden tasarlanırsa: (a) catalyst_factor'ün veri-katmanı onarılmalı veya ağırlık+relief-mantığı kaldırılmalı; (b) overnight_gap_factor ağırlığı test-sonuçlarıyla uyumlu şekilde küçültülmeli/kaldırılmalı; (c) squeeze_factor daha uzun bir pencerede yeniden ölçülmeli (şu an yetersiz-güç); (d) lottery_factor korunmalı; (e) EN YÜKSEK ÖNCELİK: `score_component_breakdown()`'ın (zaten kodda var, satır 253-302) her bir alanını (alignment_ratio, momentum_ratio, filter_score, regime, direction, volume_spike, price_momentum, trend_strength) araştırma export'una AYRI KOLON olarak eklemek — bu, formülün en büyük ağırlık-payını taşıyan ve HİÇ test edilmemiş kısmını nihayet ölçülebilir kılar. Bu, önceki tüm score-decomposition çalışmalarının neden eksik kaldığının kök-nedenidir.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu turda salt kod-okuma ve envanter eşleştirmesi yapıldı, hiçbir dosya/config/ağırlık değiştirilmedi.
Kanıt: `scanner/score_engine.py:29-73,99-190,253-302`, `.env:33-41` (bu turda okundu), `score_component_decomposition.py` çıktısı (önceki girdi).

---

[2026-08-12] — Soru 7 + Soru 10 (bedava, mevcut-veri): score 14 bileşene ayrıştırıldı, Bonferroni-eşiği (|t|>4,56) geriye uygulandı — lottery_factor TEK Bonferroni-hayatta-kalan; composite/finpilot_score'un HAM KENDİSİ bile konvansiyonel eşiği geçemiyor; 4 bileşen (atr/rvol/dist_52w_high/risk_reward) yalnız konvansiyonel |t|>2'de, EXPLORATORY (Level A, araştırma)
Layer: Research / quant
Level: A
Bağlam: Meriç'in "sadece bedava, mevcut veriyle hesaplanabilen kısımlarına (soru 7, soru 10) birkaç saat ayır" talebiyle, red-team raporunun Soru 7 (score bileşen-ayrıştırması) ve Soru 10'u (geriye-dönük global-FDR) birleştiren `score_component_decomposition.py` yazıldı ve çalıştırıldı. Ek veri gerekmedi — mevcut `full_universe_enriched.csv` (dedup, c2c_5d dolu 43.323 satır/82 gün) üzerinde `lottery_gap_reweight_test.py`'nin AYNI metodolojisi (gün-içi Fama-MacBeth rank-korelasyon + null-shuffle kontrol + blok-bootstrap CI) 14 numerik score-bileşenine tek-tek uygulandı.
Sonuçlar (Bonferroni eşiği |t|>4,56, m≈9.754):
  **Bonferroni-hayatta-kalan (tek):** lottery_factor (t=-6,60, boot-CI=[-0,286,-0,133], zaten bilinen bulgunun bu bağımsız-turda TEKRAR teyidi).
  **Sadece konvansiyonel |t|>2'de (Bonferroni'de DEĞİL, EXPLORATORY etiketiyle):** atr (t=+4,09), rvol (t=+3,76), dist_52w_high (t=+3,14), risk_reward (t=+3,50) — dördü de pozitif yönde (yüksek değer=daha iyi forward-getiri). squeeze_factor boot-CI'si 0'ı dışlıyor ama n_gün=23 (ince) ve null-kontrolü kendisi sıfırdan uzak (+0,0338) — GÜVENİLMEZ, ayrı not edildi.
  **Ölü (CI 0'ı içeriyor):** ham `score` (t=-1,91), `composite_score` (t=-1,08), `finpilot_score` (t=-0,88), `overnight_gap_factor` (t=-1,19, önceki bulgunun teyidi), `atr_pct_real`, `gap_pct`, `tier_score`.
  `catalyst_factor` ve `sentiment` yetersiz-veri (n_gün<8) — ölçülemedi.
ÖNEMLİ BULGU: composite_score/finpilot_score'un KENDİSİ (tüm bileşenlerin toplamı) bile konvansiyonel |t|>2 eşiğini geçemiyor — yani score'un içindeki hiçbir güçlü bileşen toplamda görünür kalmıyor, zayıf bileşenler (bazıları zıt yönlü: atr/rvol/dist_52w_high POZİTİF ama score'un kendisi negatif-eğilimli) birbirini götürüyor. Bu, "tek sayıda çok kavramı sahte birleştirme" teşhisini (red-team raporu §1-C) doğrudan destekliyor.
Karar: 4 EXPLORATORY adayın (atr/rvol/dist_52w_high/risk_reward) her biri kendi başına m≈9.754'lük evrende beklenen-şans-pozitifinin İÇİNDE — hiçbiri "bulgu" ilan edilmemeli, ancak bağımsız/yeni veriyle pre-registered test için aday olabilirler. lottery_factor'ün Bonferroni-hayatta-kalan tekliği bir kez daha teyit edildi.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ.
Kanıt: `score_component_decomposition.py` (bu turda yazıldı, repo köküne kondu, tam çıktı bu turda üretildi).

---

[2026-08-12] — BAĞIMSIZ RED-TEAM BİLİMSEL İNCELEME tamamlandı: `reports/red-team-scientific-review-2026-08-12.md` — 10-bölümlü zorunlu format, final decision ledger (çoğu başlık STOP/BLOCKED/DATA_REPAIR); ayrıca bugünkü (08-12) 10+ yeni script/rapor decision-log'a HİÇ girmemiş — 6. kayıt-boşluğu örneği, Meriç'e bildiriliyor (Level A, red-team/governance)
Layer: Research / governance
Level: A
Bağlam: Meriç, kapsamlı bir "Research Red Team + Scientific Review Board" promptu verdi — amaç yeni kural önermek değil, hangi eski sonuçların güvenilir/geçersiz/tekrar/veri-bağımlı olduğunu ve doğru problem tanımını ortaya çıkarmak. `docs/governance/decision-log.md` (734 satır, tam okundu) + paralel sürecin 08-12 tarihli 6 anahtar raporu (`master_audit_application`, `research_program_end_to_end`, `production_candidate_validation`, `high_rvol_deep_audit`, `correct_order_protocol`, `winner_anatomy`) tam okunup bu oturumun kendi rigor-tarihiyle (reverse-ranking, extension/exhaustion, concentration/ATR-parity, lottery_factor, global-FDR, felaket-alt-kümesi düzeltmesi) çapraz-doğrulandı.
Bulgular (rapor kendi içinde tam gerekçeli):
1) Score'un geçmişi-ölçme/geleceği-ölçmeme bulgusu artık 6+ bağımsız yoldan EVIDENCE seviyesinde, tartışmasız.
2) Concentration-limit/ATR-parity'nin "score'a özgü değil, generic portföy-matematiği" sonucu İKİ BAĞIMSIZ YÖNTEMLE (benim rigor_upgrade_concentration_atr.py'm VE paralel sürecin production_candidate_validation'ındaki 100-rastgele-kontrolü) ayrı ayrı doğrulandı — programın en sağlam çift-teyitli bulgusu.
3) "Eligible-rejected farkı kaç puan" sorusunun 5 farklı ölçümde 5 farklı, birbirine indirgenemeyen sayı verdiği (Ç3) tespit edildi — yön tutarlı, büyüklük şu an INSUFFICIENT_DATA.
4) `reports/high_rvol_deep_audit_2026-08-12.md` (paralel süreç) programın metodolojik olarak en iyi-yapılmış tekil artifact'i olarak öne çıkarıldı — kendi "pozitif" $10.000 bulgusunu 5 stres-testiyle (4-en-büyük-günü-çıkar, her-5.-günü-al, ±%50/±%20 winsorize) kendi eliyle çökertti.
5) YÖNETİŞİM: bugünkü (08-12) 10+ yeni script (`high_rvol_*` serisi, `production_candidate_validation`, `decision_context_battery`, `budget_return_battery`, `research_program_end_to_end`, `master_audit_battery`, `hypothesis_ladder_battery`) ve eşdeğer sayıda rapor decision-log'a HİÇ girmemiş (grep ile doğrulandı, bu raporun kendi 2 girdisi hariç sıfır 2026-08-12 eşleşmesi) — CLAUDE.md Bölüm 3'ün en az 6. kez tekrarlanan ihlali.
6) DOSYA-HİJYENİ: `reports/research_program_end_to_end_2026-08-12.md` içinde İngilizce ve Türkçe İKİ TAM RAPOR ayrı bir başlık/ayraç olmadan art arda eklenmiş (satır 135'te "...production approval.# FinPilot Research Program..." şeklinde kesintisiz birleşmiş) — muhtemelen iki ayrı yazma-turu üst-üste append edilmiş, veri kaybı yok ama okunabilirlik/izlenebilirlik sorunu.
Karar: Rapor Level A (araştırma/metodoloji), hiçbir üretim kuralı önermiyor. Final decision ledger'daki başlıkların çoğu STOP/BLOCKED/DATA_REPAIR; iki kalem CONFIRMATORY_CANDIDATE (abstention) / PRODUCT_MVP (PR1/PR7 + Reasoning-Platform testi) olarak işaretlendi. Meriç'e açıkça bildirilmesi gereken governance-bulgusu: Madde 5 (kayıt-boşluğu) ve Madde 6 (dosya-hijyeni) — ikisi de Level A sınırında ama tekrarlayan bir süreç-zayıflığına işaret ediyor.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Bu girdi yalnız bu raporun varlığını ve governance-bulgularını kayda geçiriyor.
Kanıt: `reports/red-team-scientific-review-2026-08-12.md` (tam rapor); bu turun grep sonuçları (`^\[2026-08-1[12]\]` deseni, decision-log.md üzerinde).

---

[2026-08-12] — KONTROL TURU #5 (kendi-kendini-denetim): dünkü "felaket alt-kümesi doğrulandı" iddiam (Madde 4) MEAN/OUTLIER ARTEFAKTIYDI — median-bazlı yeniden test tersini gösteriyor; `reports/master_audit_application_2026-08-12.md`'nin (paralel süreç) çelişen C15/N3 bulgusu doğrulandı ve D20/%86.9 sayısı bağımsız olarak yeniden üretildi (Level A, öz-düzeltme)
Layer: Research / governance
Level: A
Bağlam: Meriç "master_audit_application_2026-08-12.md — kontrolleri sağla" dedi. Bu rapor (paralel süreç, `research/master_audit_battery_2026_08_12.py` çalıştırarak üretilmiş) benim dünkü [2026-08-12] "4 AÇIK İPUCU" girdimdeki Madde-4 sonucuyla DOĞRUDAN ÇELİŞİYORDU: ben "felaket alt-kümesi doğrulandı" dedim (148 flagged sembolü çıkarınca eligible-rejected farkı anlamsızlaşıyor), rapor N3/C15'te "HAYIR, geniş-tabanlı, en büyük leave-one-out etkisi +0.33pp" diyor. Kendi iddiama uyguladığım aynı şüphecilik standardını uyguladım: yeniden hesapladım.

BULUNAN KÖK-NEDEN: Benim testim GÜN-KÜMELİ ORTALAMALARIN ORTALAMASI'nı kullanıyordu (block-bootstrap CI, mean-of-daily-means). Bu istatistik, tek bir aşırı-uç satıra (örn. EDBL +154.445%, INLF +9.146% — ikisi de flagged) karşı SON DERECE hassas, özellikle flagged-eligible alt-kümesi gibi ince örneklemlerde (n=28 satır/20 gün, günde ~1.4 satır). Rapor MEDYAN (day-clustered median + date-block bootstrap) kullanıyor — aşırı-uçlara karşı doğal olarak dirençli. Kendi verimle her iki istatistiği yan yana yeniden hesapladım:
  - Eski liste (148, 2026-08-07) ile: flagged-eligible gün-medyanlarının-medyanı=+0.108 (yaklaşık sıfır) AMA gün-ortalamalarının-ortalaması=-3.066 (çok negatif). non-flagged-eligible: medyan=-1.050 (negatif!) ama ortalama=+1.862 (pozitif!). **Ortalama ve medyan TERS YÖNDE.**
  - Ayrıca daha da önemlisi: `data/backtest_out/price_cache_integrity_audit_2026-08-11.json` diye YENİ, DAHA GENİŞ bir bütünlük-taraması var (485 flagged sembol, 2026-08-07'deki 148'in TAMAMINI kapsıyor + 337 yeni) — ben dünkü testimde BAYATLAMIŞ 148-listeyi kullanmışım. Yeni listeyle de aynı ters-yön deseni tekrarlanıyor: flagged(485)-eligible medyan=-0.235, non-flagged-eligible medyan=-1.179 (flagged DAHA AZ negatif, non-flagged DAHA NEGATİF — tam benim iddiamın tersi).
  - Tüm eligible (49 gün, filtresiz): pooled-medyan=-0.832, gün-medyanlarının-medyanı=-0.884 (ikisi de negatif, rapor'un overall_eligible_median=-0.834 ile eşleşiyor ✓) — ama gün-ortalamalarının-ortalaması=+1.839 (POZİTİF). rejected: medyan≈0/+0.30, ortalama=+5.80.
SONUÇ: eligible-vs-rejected medyan-bazlı fark GERÇEK VE NEGATİF (rapor ile ben aynı yönde-hemfikiriz), ama bunun "148/485 flagged sembolden geldiği" iddiam YANLIŞTI — flagged alt-kümesinin kendi medyanı sıfıra YAKIN, negatifliği non-flagged (temiz) kısım taşıyor. Benim dünkü mean-bazlı testim, ince örneklemde aşırı-uç bir-iki satırın ortalamayı sürüklemesiyle YANLIŞ YÖNDE bir sonuç üretmiş.

BAĞIMSIZ DOĞRULAMA (rapor'un başka iki iddiası): D20 (%86.9 örtüşme) kendi kodumla yeniden üretildi: |c2c_5d|>100 olan 183 satırdan 159'u (485-listede) flagged = %86.85 ≈ rapor'un %86.9'u — **FACT, teyit edildi**. E22 (null-kalibrasyon p95=0.50pp) basit rastgele-yarı-bölme simülasyonumla (farklı metodoloji, 1000 çekim, gün-bloksuz) p95=0.83pp verdi — aynı büyüklük-sınıfında, rapor kendi §7-madde-2'sinde bunun "basitleştirilmiş, tam matched-random değil" olduğunu zaten itiraf ediyor; çelişki yok.

Karar: Dünkü [2026-08-12] "4 AÇIK İPUCU" girdisinin Madde-4 sonucu ("felaket-alt-kümesi doğrulandı") GERİ ÇEKİLİYOR. Doğru sonuç `master_audit_application_2026-08-12.md`'nin N3/C15'i: eligible-kohortun negatifliği GENİŞ TABANLI, tek bir flagged-sembol alt-kümesine indirgenemez. Aksiyon önerisi de buna göre değişir: "148/485 sembolü filtrelemek yeterli düzeltmedir" iddiası YANLIŞ; scanner-çıkışı filtresi (madde 4'teki Level-B önerisi) veri-kalitesi için hâlâ makul ama eligible-negatifliğini ÇÖZMEYECEK. Ayrıca: bundan sonraki tüm alt-küme/felaket testlerinde MEDYAN (gün-kümeli, blok-bootstrap) birincil istatistik olsun, ORTALAMA yalnız ikincil/duyarlılık-kontrolü olarak raporlansın — ince örneklemde ortalama tek bir aşırı-uca karşı güvenilmez. `price_cache_integrity_audit_2026-08-11.json` (485 sembol) artık güncel referans; 2026-08-07/148-listesi BAYAT sayılmalı.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ. `finpilot-4-open-leads-2026-08-12.md` (memory) ve bu logdaki dünkü girdi bu turda düzeltiliyor; script'lerin kendisi (rigor_upgrade_concentration_atr.py, lottery_gap_reweight_test.py, catastrophe_subset_test.py) silinmedi/değiştirilmedi — sadece catastrophe_subset_test.py'nin YORUMU düzeltiliyor, Madde 1-3 (concentration/ATR-parity rigor'dan düşmesi, lottery_factor'ün hayatta kalması, global-FDR hesabı) bu düzeltmeden ETKİLENMİYOR ve geçerliliğini koruyor.
Kanıt: bu turda yazılan doğrulama script'i (yukarıdaki komutlar, bu oturumda); `reports/master_audit_application_2026-08-12.md` §1(N3,N6), §3(C15,D20,E22); `research/master_audit_battery_2026_08_12.py:137-174,244-255`; `data/backtest_out/master_audit_battery_2026-08-12.json` (C15_disaster_subset, D20_artifact_clusters); `data/backtest_out/price_cache_integrity_audit_2026-08-11.json` (485 flagged, eskisinin süperseti).

---

[2026-08-12] — 4 AÇIK İPUCU KOŞTURULDU: concentration/ATR-parity rigor'dan DÜŞTÜ, lottery_factor rigor'dan GEÇTİ (tek hayatta kalan), global-FDR hesaplandı, "eligible kaybediyor" bulgusu felaket-alt-kümesi (148 flagged sembol) çıkarılınca KAYBOLDU (Level A, araştırma)
Layer: Research / measurement
Level: A
Bağlam: Meriç'in kendi önerdiğim 4 açık-ipucu listesini ("1. pozitif bulgular hiç aynı süzgeçten geçmedi, 2. lottery/gap ipucu hiç takip edilmedi, 3. global multiple-testing hiç uygulanmadı, 4. felaket-alt-kümesi testi hiç koşulmadı") onaylayıp "bunlara odaklanalım ne yapmak lazım" talebiyle dördünü de fiilen çalıştırma isteği. Üç yeni script yazıldı ve çalıştırıldı: `rigor_upgrade_concentration_atr.py`, `lottery_gap_reweight_test.py`, `catastrophe_subset_test.py`.

MADDE 0 (script yazarken tesadüfen bulunan, önceden fark edilmemiş kusur): `edge_recheck.csv` DEDUP EDİLMEMİŞ — 53.754 satır ama sadece 27.323 essiz (symbol,scan_date) anahtarı (13.062 tekrarlı anahtar, çoğu intraday-tekrar-tarama). Dedup'siz top-10 günlerin %68'inde (38/56) AYNI SEMBOL 2 kez top-10'a giriyor → o sembolün getirisi günlük portföy-ortalamasında çift sayılıyor. `concentration_portfolio_test.py`/`atr_sizing_test.py`'nin ŞİMDİYE KADAR bildirdiği TÜM sayılar bu kusurla üretilmiş. Dedup, `full_universe_enriched.csv`'deki en-erken-scan_ts satırının composite_score'una eşleştirerek yapıldı (13.062 tekrarlı anahtarın %85'i / 11.142'si tam eşleşti; kalan %15 için min-composite_score deterministik fallback — belirtilmiş bir sınırlama).

MADDE 0.5 (Madde 1 ile Madde 4'ün kesişimi): |c2c5_net|>100 olan 124 satırın 93'ü (%75) 148 price-integrity-flagged sembolle çakışıyor (örn. EDBL +154.445%, INLF +9.146% — muhtemelen ayarlanmamış reverse-split/veri hatası, gerçek getiri değil). Bu satırlar filtrelenmeden çalışan matched-random kontrol (Madde 1) günlük ortalamayı +25%'e kadar şişiriyordu — kendisi bir felaket-alt-kümesi kontaminasyon örneği. Tüm Madde-1 testleri bu 148 sembol dışlanarak yeniden koşuldu.

MADDE 1 — Concentration-limit ve ATR-parity RIGOR'DAN DÜŞTÜ (reverse-ranking ve extension/exhaustion'a katılıyor): Dedup + felaket-alt-kümesi-filtresi + blok-bootstrap CI (blok=5 işlem günü, otokorelasyon için — c2c5_net 5-günlük İLERİ getiri, ardışık günler örtüşüyor) + matched-random kontrol sonrası:
  (a) Score-seçimli kısıtlı-kısıtsız fark: +0.26 (n_gün=51, naive-t=+0.88, boot-CI=[-0.26,+0.86] → 0'ı İÇERİYOR, anlamsız).
  (b) Rastgele-seçimli (matched-random) kısıtlı-kısıtsız fark: -0.02 (boot-CI=[-0.27,+0.18], anlamsız) — yani sektör-tavanı RASTGELE bir portföyde de aynı büyüklükte (aslında biraz negatif) fark yaratıyor.
  (c) İnteraksiyon testi (score_fark - rastgele_fark): +0.29, boot-CI=[-0.27,+1.01] → 0'ı içeriyor → **"kısıtlama score'a özgü değil, generic çeşitlendirme etkisi"** doğrulandı istatistiksel olarak.
  (d) ATR-ters-ağırlık vs eşit-ağırlık: hem kısıtlı hem kısıtsızda CI 0'ı içeriyor (anlamsız). Permütasyon-kontrolü (ATR değerleri o günün isimleri arasında karıştırılıp yeniden hesaplanan ağırlıklı getiri) ile gerçek-ATR arasındaki interaksiyon da anlamsız (boot-CI 0'ı içeriyor) → ATR'nin SPESİFİK bilgisi ayırt edilemiyor, ağırlık-dağılımı varyansından ayrışmıyor.
  SONUÇ: Big-Bet-1'in "concentration-kısıtı riski yarıya indirdi" ve "ATR-parity Sharpe/drawdown iyileştirdi" iddiaları — hiçbiri gün-kümeli+blok-bootstrap+matched-random süzgecinden GEÇMEDİ. `finpilot-big-bet-1-findings.md` HYPOTHESIS seviyesine düşürülmeli.

MADDE 2 — lottery_factor RIGOR'DAN GEÇTİ (programın TEK hayatta kalan pozitif bulgusu), overnight_gap_factor GEÇMEDİ: Kaynak-kod semantiği doğrulandı (`scanner/features.py`: lottery_factor "higher = more lottery-like = stronger FADE expectation"; overnight_gap_factor "reversal pressure" — ikisi de negatif-ağırlıklı kullanılacak şekilde tasarlanmış). Fama-MacBeth tarzı gün-içi rank-korelasyon (n=30 gün, 2026-06-15→07-31, full_universe_enriched.csv dedup):
  lottery_factor vs c2c_5d: ort-rho=-0.204, naive-t=-6.60, boot-CI=[-0.282,-0.136] → **0'ı İÇERMİYOR, ANLAMLI** (null/karıştırılmış-kontrol: rho≈+0.001, referans).
  overnight_gap_factor vs c2c_5d: ort-rho=-0.048, naive-t=-1.19, boot-CI=[-0.123,+0.014] → 0'ı içeriyor, ANLAMSIZ.
  Portföy testi (top-10, n=30 gün): composite_score ile seçim ort-c2c_5d=-1.58 (score AKTİF OLARAK ZARAR VERİYOR, rastgeleden bile kötü); composite - lottery - gap (z-skorlu alt_score) ile seçim ort-c2c_5d=+0.08; rastgele seçim ort-c2c_5d=+2.68. alt-orig farkı=+1.66 (boot-CI=[+0.81,+2.54] → ANLAMLI, lottery/gap cezası gerçek bir iyileştirme). AMA alt_score hâlâ rastgeleden anlamlı derecede KÖTÜ (alt-rand=-2.60, boot-CI=[-4.00,-1.41] → ANLAMLI). SONUÇ: lottery_factor gerçek, doğrulanmış, zayıf bir ileri-bilgi taşıyor ve onu kullanmak composite_score'un zararını KISMEN azaltıyor — ama composite_score'un diğer bileşenleri hâlâ o kadar zararlı ki düzeltilmiş score bile rastgele seçimin altında kalıyor.

MADDE 3 — Global multiple-testing/FDR (geriye-dönük, kaba hesap): m≈9.754 toplam test edilen konfigürasyon (2.520 barrier-grid + 3.120 fixed-target + 4.000 weight-search + 74 iki-faktör-kombo + ~40 bu-yaz). Düzeltmesiz alpha=0.05'te BEKLENEN şans-eseri "anlamlı" sonuç sayısı: ~488. Bonferroni-düzeltilmiş eşik: alpha=5.13e-6, karşılığı iki-yönlü |t|>4.56 (konvansiyonel |t|>2 eşiğinin ÇOK altında kalan bulgular güvenilmez demektir). Q4 null-feature noise-floor referansı (|rho|=0.011 @ p95, tek-test) m=9.754 test üzerinden EN AZ BİR kez aşılması pratikte kesindir (olasılık ≈1). SONUÇ: bu ölçekte, düzeltilmemiş "|t|>2" veya "p<0.05" ile flaglenen HER bulgu a-priori şüpheli sayılmalı; programın 2 yıllık tarihinde flaglenen düzinelerce "pozitif" bulgudan (reverse-ranking, extension/exhaustion, MFE-headline'lar, concentration-limit, ATR-parity) sadece BİRİNİN (lottery_factor, Madde 2) global-ölçekli süzgeçten geçmesi, ~488 beklenen şans-pozitifine karşı ÇOK düşük bir gerçek-bulgu oranıyla tutarlı.

MADDE 4 — "Felaket alt-kümesi" hipotezi DOĞRULANDI: eligible (entry_ok=True) kohortunun negatif bulgusu GENEL DEĞİL, küçük bir veri-bütünlüğü-sorunlu alt-kümeye aşırı-maruziyet. full_universe_enriched.csv dedup, c2c_5d + entry_ok dolu 43.323 satır/82 gün:
  Adım 1 (filtresiz): eligible-rejected = -3.40, boot-CI=[-8.11,-0.91] → 0'ı İÇERMİYOR, ANLAMLI (önceki "eligible kaybediyor" anlatısını gün-kümeli+blok-bootstrap ile teyit ediyor).
  Adım 2: eligible içinde flagged (148 sembolden, sadece 28 satır/1094 = %2,6) vs non-flagged — flagged-eligible ort=-3.07 ama n çok ince (20 gün, günde ~1.4 satır), kendi başına CI 0'ı içeriyor (yetersiz güç).
  Adım 3 (KARAR VERİCİ): 148 flagged sembol HEM eligible HEM rejected'ten çıkarılınca (eligible'ın %2,6'sı, rejected'in %6,3'ü) → eligible-rejected farkı +0.39, boot-CI=[-3.03,+2.30] → 0'ı İÇERİYOR, **ANLAMSIZLAŞTI**.
  Adım 5 (çift-temiz, +penny-stock<$5 de çıkarılmış — ama penny-stock eligible'da pratikte yok, n=1): eligible-rejected=+0.08, boot-CI=[-3.19,+1.89], anlamsız.
  SONUÇ: eligible kohortunun sadece %2,6'sı (fiyat-bütünlüğü bozuk 148 sembolden) TÜM istatistiksel anlamlılığı taşıyıyor. Bu, "seçim (entry_ok) değer eksiltiyor" sonucunu "seçim, veri-bütünlüğü bozuk küçük bir alt-kümeye aşırı-maruz kalıyor; bu alt-küme temizlenince score'un net etkisi rastgeleden İSTATİSTİKSEL OLARAK AYRIŞAMIYOR (ne pozitif ne kanıtlanmış-negatif)" sonucuna çeviriyor — daha ucuz, daha aksiyon-alınabilir bir düzeltme (scanner çıkışında 148 sembolü filtrele) ama AYNI ZAMANDA "score net-pozitif" iddiasını da desteklemiyor.

Karar: Dört madde de araştırma/ölçüm bulgusu (Level A, üretim değişikliği yok). Önerilen takip kararları (Meriç onayı gerekir, Level B): (i) 148 flagged sembolü scanner/backtest pipeline'ından kalıcı olarak filtrele (Madde 4); (ii) composite_score'a lottery_factor+overnight_gap_factor negatif-ağırlıklı düzeltme ekle (Madde 2) — ama bunun kendi başına score'u net-pozitif YAPMADIĞI açıkça belirtilerek; (iii) `finpilot-big-bet-1-findings.md`'deki concentration-limit/ATR-parity iddiaları HYPOTHESIS'e düşürülsün (Madde 1); (iv) gelecekte "|t|>2" tek başına "bulgu" ilan edilmesin, Madde-3'ün m-düzeltmesi (|t|>4.56 veya BH-FDR) referans alınsın.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ — bu turda sadece ölçüm/analiz yapıldı, hiçbir kod/config canlıya dokunmadı.
Kanıt: `rigor_upgrade_concentration_atr.py`, `lottery_gap_reweight_test.py`, `catastrophe_subset_test.py` (üçü de bu turda yazıldı, repo köküne kondu, tam çıktıları bu turda üretildi); `scanner/features.py:392-471` (lottery/gap semantiği); `data/backtest_out/price_cache_adjusted_integrity_audit_2026-08-07.json` (148 flagged sembol).

---

[2026-08-11] — KONTROL TURU #4: PARKING_LOT ihlali tespit edildi — "Ledger×Classroom" kod uygulaması (parkta, "lansman sonrası İLK iş" sözü) canlı landing'e (page.tsx) zaten girmiş; ayrıca 2026-08-11 çalışması decision-log'a hiç girmemiş (5. kayıt-boşluğu örneği) (Level A, kontrol)
Layer: Governance / product
Level: A
Bağlam: Meriç'in "tekrar kontrolleri sağla" talebiyle bağımsız bir denetim turu daha yapıldı — repo dosya-durumu (mtime taraması), decision-log bütünlüğü ve son 24-48 saatte üretilmiş-ama-kayıtsız iş tarandı.
Bulgular:
1) PARKING_LOT İHLALİ (yeni, önceden kayıtlı değildi): `PARKING_LOT.md` "Ledger×Classroom tasarımının kod uygulaması"nı "lansman sonrası İLK iş — söz" diyerek parkta tutuyor. `docs/strategy/Morning_Ledger_Urun_Stratejisi_Konsolide_2026-08-05.md` bunu "VİZYON — DONDURULDU" statüsünde dondurmuş ve kendi metninde "bu belge kod, public içerik... değiştirmez" diyor. Ama gerçek repo durumu tersini gösteriyor: `web/src/components/ledger/ClassroomPreview.tsx` (mtime 2026-08-11 14:29, yeni dosya) canlı landing'e (`web/src/app/page.tsx:9,69`) `<ClassroomPreview>` olarak eklenmiş ve render ediliyor; `DailyDouble.tsx` (mtime 2026-08-10 13:00) aynı sayfada "section.dailyDouble"/"section.classroom" başlıklarıyla canlı. `docs/strategy/FinSense_MVP_Gap_Audit_2026-08-11.md` bunu kendi metninde doğruluyor: "Bugün değiştirdiğim ClassroomPreview.tsx/DailyDouble.tsx... Bugünkü Calibration v0 (Borsa web, ClassroomPreview.tsx) bunun ilk, küçük, kalıcı-olmayan örneği." AGENTS.md tanımıyla bu Level B (web canlı yüzeyi) bir değişiklik — decision-log'da bunu onaylayan/kaydeden hiçbir girdi yok (tam-dosya grep: "ClassroomPreview", "DailyDouble" [tek eski/farklı-bağlamlı referans satır 506], "Calibration v0", "Thinking Mirror" için sıfır ilgili sonuç). Deploy/canlılık durumu bu turda doğrulanamadı (git komutu zaman aşımına uğradı, repo büyük) — ama kod repo'da ve sayfa ağacında mevcut ve derleniyor durumda.
2) YENİ KAYIT-BOŞLUĞU (5. örnek — DURUM.md'nin bilinen örüntüsünün devamı): `reports/research_battery_consolidated_2026-08-11.md`, `docs/strategy/FinSense_MVP_Gap_Audit_2026-08-11.md`, tüm `reports/content_series/` (10 bölümlük "10x40" içerik serisi + HTML + `source_rights_register_2026-08-10.md`), `reports/honest_quant_handbook_2026-08-10.md` + `_distribution_2026-08-10.md`, `reports/glossary_cards_product_spec_2026-08-10.md`, `reports/source_material_inventory_2026-08-10.md`, `reports/finpilot_source_book_product_map_2026-08-10.md` — hiçbiri decision-log'da yok (tam-dosya grep, sıfır eşleşme). `research_battery_consolidated_2026-08-11.md` kendi başlığında "Level A for isolated diagnostics" diyor — sınıflandırma muhtemelen doğru ama yine de kayıt zorunluluğu (CLAUDE.md Bölüm 3) uygulanmamış.
3) DOSYA-SIRALAMA BÜTÜNLÜĞÜ: `decision-log.md` (~654 satır) kronolojik değil — satır 1-183 (KONTROL TURU zinciri, hepsi 2026-08-10) dosyanın BAŞINA eklenmiş, satır 184-653 ise genelde append-sırasında (07-31→...→08-10) ilerliyor. Bu, önceki turlarda "kilitsiz eşzamanlı yazma riski" olarak işaretlenen bulgunun somut kanıtı — iki farklı yazma alışkanlığı (prepend vs append) aynı dosyada karışmış, ama veri kaybı/çakışma gözlenmedi.
4) DURUM.md / LAUNCH_CHECKLIST.md sayıları hâlâ 7 Ağustos'ta doğrulanmış hâliyle duruyor (seri 4/10, 3-6 Ağu) — 11 Ağustos'a kadar canlı DB'ye karşı yeniden doğrulanmamış; 4 günlük bir bayatlık, kritik değil ama not edilir.
Karar: Bulgular yalnız kayıt/rapor; bu turda kod/dosya değişikliği YAPILMADI (Level A sınırı korundu). Madde 1 (PARKING_LOT ihlali) Meriç'e açıkça bildirilmeli — governance-kritik bir çelişki (CLAUDE.md: "report conflicts immediately"; "Never... overwrite governance without approval"). Karar Meriç'e ait: (a) ClassroomPreview/DailyDouble landing'den geri alınsın mı yoksa retroaktif Level B onayı mı verilsin, (b) madde 2'deki kayıtsız işler toplu bir "kayıt-boşluğu kapatma" girdisiyle mi işlensin.
Etki: Üretim skoru/scanner/entry-exit/risk DEĞİŞMEDİ. Web canlı yüzeyi (landing) muhtemelen ETKİLENDİ (madde 1) — bu turda salt tespit, geri alma/onay işlemi yapılmadı.
Kanıt: `web/src/components/ledger/ClassroomPreview.tsx` (mtime 2026-08-11 14:29), `web/src/app/page.tsx:3-11,46-70`, `PARKING_LOT.md:4`, `docs/strategy/Morning_Ledger_Urun_Stratejisi_Konsolide_2026-08-05.md:1-9`, `docs/strategy/FinSense_MVP_Gap_Audit_2026-08-11.md:22,33`, tam-dosya grep sonuçları (bu turda).

---

[2026-08-11] — Yayın serisi canlı DB'ye karşı yeniden doğrulandı: kesintisiz, 4/10 → 7/10 büyümüş; DURUM.md/LAUNCH_CHECKLIST.md güncellendi (Level A, dokümantasyon)
Layer: Documentation / governance
Level: A
Bağlam: Meriç'in "yayın kesintisiz sürüyor kontrol et" talebiyle `distribution.broadcast.publish_streak()` canlı `data/distribution.db`'ye karşı çalıştırıldı (2026-08-07'deki doğrulamanın aynı yöntemle tekrarı).
Bulgular: `broadcast_queue` sorgusu (`kind LIKE 'daily%'`, `status='sent'`) ardışık şu tarihleri gösteriyor: 3, 4, 5, 6, 7, 10, 11 Ağustos (8-9 Ağu haftasonu, market_calendar tarafından atlanıyor — seriyi kırmıyor). `publish_streak()` **7** döndürdü. En son sent kayıt bugüne (2026-08-11) ait — günün brifi zaten yayınlanmış. Seri kırılmadı; 7 Ağu'daki önceki doğrulamadan (4/10) bu yana 3 gün daha kesintisiz eklenmiş.
Değişiklik: `DURUM.md` "⭐ Bu 6 haftanın TEK önceliği" bölümü 4/10 → 7/10 ve güncel tarih/kanıt notuyla güncellendi. `LAUNCH_CHECKLIST.md` madde 1 aynı sayı + "3 gün kaldı" notuyla güncellendi.
Etki: Yalnız iki durum dosyasındaki sayı/not metni değişti. Scanner/distribution/skor/risk/canlı yayın davranışı DEĞİŞMEDİ — salt dokümantasyon düzeltmesi (2026-08-07 girdisiyle aynı desen, Level A).
Kanıt: `python3 -c "from distribution.broadcast import publish_streak; print(publish_streak())"` → 7; `broadcast_queue` GROUP BY sorgusu (bu turda, sonuç yukarıda).

---

[2026-08-10] — KONTROL TURU #3 (kendi-kendini-denetim): önceki girdideki "dördüncü kez tekrarlandı" iddiam kesin değildi — grep ile satır-satır yeniden sayıldı; ayrıca decision-log/protocol-dosyası bütünliği ve repo eşzamanlılığı doğrulandı (Level A, öz-düzeltme)
Layer: Research / governance
Level: A
Bağlam: "Kontrolleri sağla" talebi ikinci kez geldiğinde, önceki kendi iddiamı da denetime tabi tuttum (aynı şüphecilik kuralı bana da uygulanmalı).
1) BÜTÜNLÜK: `docs/governance/decision-log.md` ve `reports/correct_order_protocol_2026-08-10.md` son yazdığım hâliyle sağlam, üzerine yazma/çakışma yok. Repo'da bu turda yeni değişiklik yok (mtime'lar önceki turdakiyle aynı) — paralel süreç şu an duraklamış görünüyor.
2) ÖZ-DÜZELTME — "dördüncü kez tekrarlandı" iddiam ABARTILIYDI: Her rapor dosyasının kendi metni `grep`lendi. Gerçek durum: (a) `evidence_matrix_v1_2026-08-07.md` decision-log'un "2026-08-06 tarihli" 4 farklı girdisine atıf yapıyor — decision-log'da [2026-08-06] TARİHLİ HİÇBİR GİRDİ YOK (doğrulandı) → GERÇEK, dosya-içi YANLIŞ ATIF (1. örnek, daha önce fark edilmemiş, Aug-07'den). (b) `correct_order_analysis_2026-08-10.md` "Export değişikliği Level B olarak uygulandı (decision-log)" diyor, o an decision-log'da yoktu → GERÇEK, dosya-içi YANLIŞ ATIF (2. örnek). (c) `correct_order_protocol_2026-08-10.md`'nin KENDİ METNİ "Kapı kapanma kriterleri decision-log'a girer" gibi İLERİYE-DÖNÜK KURAL cümleleri kullanıyor, "zaten girdi" diye bir iddia YOK — kullanıcının ilettiği trace-log'daki "Level B pending olarak decision-log'da" cümlesi bir SOHBET-ÖZETİ ifadesiydi, dosyanın kendi metninde değildi. (d) Strategic Lab / 10-Perspective / Mirror Analysis / Pre-registration / User-research-kit dosyaları decision-log'a HİÇ ATIFTA BULUNMUYOR — bunlar "yanlış iddia" değil, sade "kayıt-boşluğu" (girilmemiş ama girileceğini de iddia etmemiş).
Düzeltilmiş sayım: kanıtlanmış dosya-içi yanlış decision-log atfı = 2 (evidence_matrix_v1, correct_order_analysis), + 1 sohbet-seviyesi yanlış durum-iddiası (protokol için, dosyanın kendisinde değil) = toplam 3 doğrulanmış örnek, "4" değil. Kayıt-boşluğu (atıfsız-eksik) ayrı ve daha geniş bir kategori (Strategic Lab vb. + şimdi de evidence_matrix'in ATIF ETTİĞİ ama var olmayan 2026-08-06 girdileri).
Karar: Önceki "dördüncü kez" ifadesi düzeltildi — abartılıydı. Genel bulgu (bu araştırma hattında decision-log referanslarının güvenilmez olduğu, doğrulanmadan kullanılmaması gerektiği) DEĞİŞMEDİ, sadece kesin sayı düzeltildi. Bu, kendi iddialarıma da başkalarının iddialarına uyguladığım aynı doğrulama standardını uygulama örneği.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Onaylanan protokol ve 5-işlik liste geçerliliğini koruyor, bu girdi yalnız önceki girdideki bir sayısal/dilsel abartıyı düzeltiyor.
Kanıt: bu turun grep sonuçları (yukarıda alıntılandı).

---

[2026-08-10] — "Veri→Ölçüm→Execution→Sinyal" 4-kapı protokolü ONAYLANDI (Meriç, bu turda); Kapı 1.1 durumu düzeltildi; eşzamanlı-süreç koordinasyonu netleştirildi (Level B onay + Level A düzeltme)
Layer: Research / governance
Level: B (protokol onayı) + A (durum düzeltmesi + süreç netliği)
Bağlam: `reports/correct_order_protocol_2026-08-10.md` (dört kapı: Veri/Ölçüm/Execution/Sinyal, her biri somut kapanma kriterleriyle) Meriç tarafından bu turda ONAYLANDI. Onayla birlikte iki düzeltme yapıldı:
1) KAPI 1.1 DURUM DÜZELTMESİ: Protokol dosyasında 1.1 ("Etiket semantiği doğrulanmış") "✅ KAPANDI" olarak işaretlenmişti. Bu, ETİKET TANIMI için doğru (resolved_pct_t5=MFE kod-seviyesinde doğrulandı, c2c_5d/mae_t5 export'ta) ama bu etiketle üretilen İLK İKİ headline-sayı (-2.39%/+0.06% ve matched +0.50/-0.61) "KONTROL TURU"/"KONTROL TURU #2" girdilerinde gün-kümeli+dedup+matched-random testten GEÇMEDİ (t~-0.86, t~-0.01, ikisi de anlamsız). Protokolün kendi diliyle bu iki sayı "bulgu" değil "keşif sinyali"dir. 1.1'in durumu buna göre "KAPANDI (tanım) / keşif-sinyali (ilk analizler)" olarak düzeltildi (`correct_order_protocol_2026-08-10.md` içinde de düzeltildi).
2) EŞZAMANLI-SÜREÇ KOORDINASYONU: Bu repo üzerinde bu oturumla PARALEL çalışan başka bir süreç var (muhtemelen Meriç'in ayrı bir Claude Code oturumu) — son ~40 dakikada `fetch_full_universe_and_retest.py`, `full_universe_enriched.csv`, `correct_order_analysis_2026-08-10.md`, `correct_order_protocol_2026-08-10.md` bu süreç tarafından üretildi/değiştirildi. Aynı decision-log.md dosyasına her iki taraf da yazıyor — şu ana kadar çakışma olmadı (her tur öncesi dosya durumu kontrol edildi) ama kilitsiz eşzamanlı yazma riski gerçek. AYRICA: bu paralel sürecin ürettiği 4 rapordan (Strategic Lab, Mirror Analysis, correct_order_analysis, correct_order_protocol) HİÇBİRİ kendi iddia ettiği decision-log girdisini gerçekten yazmamıştı — bu turda dördüncü kez doğrulandı (grep, sıfır eşleşme). Bu artık tek-seferlik değil, o sürecin sistemik bir alışkanlığı: rapor içinde "decision-log'a girdi" cümlesi bir niyet/formalite olarak yazılıyor, gerçek yazma adımı atlanıyor.
Karar: Protokol onaylandı, bu haftalık 5 iş (1.3 lineage şeması, 1.4 restatement pilotu, 2.2 deney-bütçesi defteri, 2.3 null-preflight zorunlu-gate, 3.2 signal half-life) başlatılabilir. Koordinasyon için önerilen kural: hangi taraf decision-log'a yazacaksa, YAZMADAN ÖNCE dosyayı taze okusun (iki taraf da bunu yapıyor gibi görünüyor, şimdilik çakışma yok) VE "girdi" iddiasını yalnızca gerçekten yazdıktan sonra rapor metnine koysun (yazmadan önce değil) — bu, tekrarlayan "iddia edilen ama yok" örüntüsünü kapatır.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Sinyal katmanı (Kapı 4, pre-registered H1-H3) hâlâ kilitli — Kapı 1-3 kapanana ve kullanıcı-gerçeği (PR1/PR7) netleşene kadar.
Kanıt: `reports/correct_order_protocol_2026-08-10.md` (düzeltilmiş hâli), bu turun grep-doğrulaması.

---

[2026-08-10] — KONTROL TURU #2: "confound-kontrollü" eşleştirilmiş MFE-vs-c2c karşılaştırması (+0.50/-0.61) da gün-kümeli teste tabi tutulunca anlamsız çıktı — confound-kontrolü doğruydu, gün-kümeleme atlanmıştı (Level A, kontrol)
Layer: Research / governance
Level: A
Bağlam: Önceki "KONTROL TURU" girdisinin ardından, paralel süreç bir takip analiziyle export-büyümesi confound'unu kontrol etti: eski∩yeni export'un kesişimindeki AYNI 27.386 sembol-gününde, yalnız etiket değiştirilerek (MFE vs c2c_5d) eligible-rejected farkı hesaplandı — MFE ile +0.50 (seçim "kazanıyor"), c2c_5d ile -0.61 (seçim "kaybediyor"), işaret tam tersine dönüyor. Bu, veri-büyümesi confound'unu doğru şekilde kontrol ediyor (iyi metodolojik içgüdü) — AMA satır-bazlı (978 eligible satırı vs 33-42binlik rejected satırı, aynı-gün-korelasyonu hesaba katılmadan) medyan karşılaştırması, bu programın tekrarlayan uyarısına (S1, gün-kümeleme olmadan "anlamlı" illüzyon) yine tabi.
Bu turda AYNI eşleştirilmiş alt-kümede (proxy: scan_date≤2026-07-13, dedup'lu, gün-kümeli, matched-random-kontrollü) bağımsızca yeniden test edildi:
- MFE (resolved_pct_t5): eligible-rejected paired fark = **-0.060, t~-0.01 — ANLAMSIZ** (raporun "+0.50 kazanıyor" iddiası gün-kümelemede kaybolan bir satır-bazlı artefakt; gerçekte MFE'de neredeyse sıfır fark var).
- c2c_5d (dürüst): eligible-rejected paired fark = **-2.190, t~-0.86 — ANLAMSIZ** (yön negatif/tutarlı ama istatistiksel olarak sağlam değil; raporun "-0.61 kaybediyor, confound-suz kanıt" iddiası bu barı geçmiyor).
Karar: Confound-kontrolü (export-büyümesi ayrıştırması) doğru ve değerli bir adımdı, korunuyor. Ama "işaret tam tersine dönüyor, confound-suz temiz kanıt" çerçevesi ABARTILI — çünkü gün-kümeleme adımı (bu programın S1 bulgusunun bizzat kendisinin gerektirdiği) atlanmış. Genel yön (eligible zayıf) hâlâ P1/Mirror-L4/P0-P3 üçlüsüyle destekleniyor; bu spesifik eşleştirilmiş-karşılaştırma kendi başına "kanıtlanmış" sayılmamalı — programın üçüncü kez tekrarlayan örüntüsü (çarpıcı satır-bazlı sayı → gün-kümelemede erir).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. "correct_order_analysis" raporunun sonuç-cümlesi ("tek düzeltme iki-yıllık anlatıyı tersine çevirdi") bu iki ayrı kontrol turuyla da desteklenmiyor; doğru çerçeve "düzeltme yönü teyit ediyor ama kendi başına henüz istatistiksel olarak sağlam değil."
Kanıt: bu turun bağımsız kontrol scripti (kaydedilmedi, çıktı yukarıda satır satır).

---

[2026-08-10] — KONTROL TURU: export sessizce büyümüş (53.859→100.496 satır, 66→85 gün); "correct_order" raporunun -%2.39/+%0.06 iddiası bu oturumun kendi rigor-standardıyla (dedup+gün-kümeli+matched-random+outlier) ANLAMSIZ çıktı — henüz doğrulanmış sayılmaz (Level A, kontrol)
Layer: Research / governance
Level: A
Bağlam: Kullanıcı talebiyle ("kontrolleri sağla") önceki turun bulgusu ve genel repo durumu bağımsızca yeniden denetlendi.
1) REPO-DURUM KONTROLÜ: `full_universe_enriched.csv` bu oturum içinde sessizce büyümüş — 53.859→100.496 ham satır, 66→85 farklı scan_date, tarih aralığı 2025-09-11..2026-07-13'ten 2025-09-11..2026-08-05'e uzamış. composite_score kapsamı önceki turda bulunan 39 günden (2026-05-06→07-13) 58 güne (2026-04-27→08-05) genişlemiş — "composite_score sadece 39 gün" bulgusu artık GÜNCEL DEĞİL, sayı büyüdü ama nitel sonuç aynı kalıyor (composite_score hâlâ 85 günün tamamını kapsamıyor, en-eski ~58 gün hâlâ boş). Bu oturumdaki ESKİ export üzerinde hesaplanan tüm sayılar (reverse_ranking_closure.py, extension_cap_test.py, iki batarya) artık dosyanın GÜNCEL hâliyle bire-bir yeniden üretilemez — anlık görüntü değişti. decision-log/memory'deki eski sayılar geçerliliğini korur (o anki dosya durumunu doğru yansıtıyorlardı) ama "güncel dosya durumu" olarak okunmamalı.
2) BAĞIMSIZ DOĞRULAMA — "correct_order_analysis" raporunun -%2.39/+%0.06 iddiası: Bu sayı için hiçbir kayıtlı script/artifact bulunamadı (yalnız `fetch_full_universe_and_retest.py` ve onun testi var, ikisi de bu karşılaştırmayı yapmıyor) — az önceki "0.325" ile aynı türde izlenemeyen-sayı sorunu. Bu turda dedup (en-erken-scan_ts) + gün-kümeli + matched-random-kontrol + outlier-farkındalığıyla (bu oturumun standart rigor'u) bağımsızca yeniden hesaplandı, YENİ (büyümüş) export üzerinde:
   - Ham (outlier dahil): eligible medyan -1.523% (n_gün=49, n_obs=1094, ort +1.839 — ort/medyan arası büyük fark, outlier-etkisi), rejected medyan +2.223% (n_gün=82, n_obs=42.229). Paired gün-kümeli fark: eligible-rejected = -3.402, SE=2.063, t~-1.65 → **ANLAMSIZ**. eligible vs random-kontrol (2 seed) de anlamsız (t~-0.13, -0.67).
   - Outlier-kapsanmış (|c2c_5d|≤%100): eligible medyan -1.523% (değişmedi), rejected medyan +0.311% (düştü). Paired fark: **YÖN TERSİNE DÖNÜYOR** (+1.250, t~+0.62, hâlâ anlamsız).
   Sonuç: "correct_order" raporunun "sonuç hemen değişti, seçim kaybediyor" çerçevesi, bu oturumun kendi rigor-standardına (dedup/gün-kümeli/matched-random — reverse-ranking'i ve extension/exhaustion'ı kapatan AYNI standart) tabi tutulduğunda DOĞRULANMIYOR. Yön (eligible zayıf) hâlâ genel tabloyla (P1, Mirror L4, P0-P3) tutarlı ama BU SPESİFİK sayı/iddia kendi başına istatistiksel olarak sağlam değil ve outlier-hassas.
Karar: "-%2.39/+%0.06" rakamı decision-log'daki önceki girdide (VERİ KATMANI DÜZELTMESİ) AKTARILDIĞI HALİYLE bırakılıyor (o an rapor edilen şekliyle kayıt altında) ama bu girdiyle DOĞRULANMAMIŞ/anlamsız olarak işaretleniyor — gelecekte biri bu sayıyı "kanıtlanmış" diye kullanmasın.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Genel yön-bulgusu (eligible zayıf/rastgeleyi geçemiyor) hâlâ 3 diğer bağımsız kanıtla (P1, Mirror L4, P0-P3) destekleniyor; sadece bu tek sayı/iddia zayıflatıldı.
Kanıt: bu turun bağımsız kontrol scripti (kaydedilmedi, sonuç yukarıda satır satır); `data/backtest_out/full_universe_enriched.csv` (güncel mtime 2026-08-10 15:13).

---

[2026-08-10] — VERİ KATMANI DÜZELTMESİ: resolved_pct_t5'in MFE (getiri değil) olduğu kod-seviyesinde doğrulandı; export'a gerçek c2c_1d/c2c_5d/mae_t5 eklendi; dürüst etiketle eligible<rejected bulgusu ÇOK DAHA SERT çıktı (Level A/B karışık — export değişikliği + araştırma bulgusu)
Layer: Research / data
Level: A (bulgu) + B (export şeması değişikliği — aşağıda not)
Bağlam: Önceki turda V0/resolved_pct_t5 korelasyonunun üç ayrı ölçümde üç farklı sayı verdiği (0.86/0.325/0.55) tespit edilmiş, kök-neden araştırması başlatılmıştı. Kod-seviyesi denetim (`fetch_full_universe_and_retest.py:294`) kesin cevabı verdi: `resolved_pct_t5 = (max(highs[T+1..T+5]) - entry)/entry*100` — bu bir MAX-FAVORABLE-EXCURSION (MFE) hesabı, close-to-close GETİRİ değil. Üç farklı korelasyon sayısı bu yüzden "hata" değildi — üçü de MFE'yi (yapısal olarak c2c'den ≥ olan, farklı örneklemlerde farklı oranda ayrışan bir büyüklük) bir getiriyle kıyaslıyordu. Bu, 2026-07-31 kararındaki "resolved_pct_t5 MFE-bozuk" bulgusunun kod-seviyesinde tam teyidi (üçüncü bağımsız doğrulama).
NOT (süreç/eşzamanlılık): Bu düzeltme, bu oturumun kendi script'i tarafından değil, REPO ÜZERİNDE EŞZAMANLI ÇALIŞAN başka bir süreç tarafından yapıldı (`fetch_full_universe_and_retest.py`, `full_universe_enriched.csv`, `reports/correct_order_analysis_2026-08-10.md` hepsi bu turda, dakikalar içinde değişti — muhtemelen Meriç'in paralel bir Claude Code oturumu). Bu üçüncü kez tekrarlanan bir örüntü: `reports/correct_order_analysis_2026-08-10.md`'nin kendi "Governance boundary" bölümü "export değişikliği Level B olarak uygulandı (decision-log)" diyor, ama decision-log'da bu değişikliğe dair HİÇBİR girdi yoktu (grep ile doğrulandı) — Strategic Lab/10-Perspective/Mirror-Analysis/Pre-registration'da da aynı boşluk vardı.
Bulgular (yeni export'un c2c_5d alanıyla, dürüst getiri):
- score vs c2c_5d (gerçek getiri): ρ=0.011 — ileri bilgi yok (önceki R1'in ρ=0.013'üyle tutarlı, farklı örneklem/tarih ile bağımsız teyit).
- score vs mae_t5 (adverse-excursion): ρ=+0.095 — yüksek score, DAHA KÖTÜ adverse excursion ile ilişkili (ters yönde, kötüye işaret).
- **eligible c2c_5d medyanı: -%2.39 | rejected c2c_5d medyanı: +%0.06.** Pozitif-oran: eligible %35.4 vs rejected %50.4.
- Bu, MFE-etiketiyle GÖRÜNMEYEN bir bulgu — MFE "5 gün içinde bir noktada yukarı gitti mi" ölçer, gerçek 5-gün-sonu durumunu değil. Dürüst ölçümle, seçim katmanının zararı ÖNCEDEN SANILANDAN DAHA BÜYÜK.
- Bu sayı, bu oturumun kendi bulgularıyla (reverse_ranking_closure.py, Mirror Analysis L4: eligible -%0.20 vs not-eligible +%1.08 üst-quintile içinde) AYNI YÖNDE ama farklı büyüklükte — beklenen, çünkü farklı dedup/örneklem/pencere kullanıyorlar. Yön tutarlılığı (eligible her zaman kötü) şu an DÖRT bağımsız ölçümde var: P1 (battery-1, -2.01pp), Mirror L4 (-0.20% vs +1.08%), bu turun c2c_5d'si (-2.39% vs +0.06%), ve entry_ok'un kendi P0-P3 end-to-end testi (-0.6387%, 2026-08-07).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Araştırma-export şeması (`full_universe_enriched.csv`, yeni kolonlar c2c_1d/c2c_5d/mae_t5) değişti — bu dosya yalnız research/ tüketiyor, canlı sisteme bağlı değil, dolayısıyla bu oturumun sınıflandırma alışkanlığıyla Level A sayılır; ilgili rapor "Level B" demiş, bu tutarsızlık not edilmiştir, üretim etkisi olmadığından pratik sonucu değiştirmiyor.
Sıradaki somut adımlar (raporun kendi sıralaması, "veri→ölçüm→execution→sinyal"): (1) 148 işaretli sembolün fiyat-sürekliliği onarımı (AÇIK), (2) feature timestamp/age lineage (AÇIK), (3) restatement dedektörü (AÇIK), (4) deney-bütçesi defteri (AÇIK), (5) zorunlu null-preflight (KISMEN), (6) replayable telemetry/P0 score-replay (AÇIK, Level B bekliyor), (7) spread/ADV toplama (YOK), (8) signal half-life (YOK) — sinyal katmanına (pre-registered H1-H3) yalnız bunlardan sonra + kullanıcı-gerçeği kapısından (PR1/PR7) sonra geçilecek.
Kanıt: `fetch_full_universe_and_retest.py` (satır 294-320), `data/backtest_out/full_universe_enriched.csv` (yeni kolonlar), `reports/correct_order_analysis_2026-08-10.md`.

---

[2026-08-10] — BÜYÜK KAYIT-BOŞLUĞU: 2026-08-04..08-10 arası onlarca deney + formal evidence-gate matrisi (PASS/FAIL/NOT_OPENED) hiç decision-log'a girmemiş; ayrıca V0 (resolved_pct_t5↔cache korelasyonu) üç bağımsız ölçümde üç farklı sayı veriyor (Level A, kayıt+tutarsızlık-tespiti)
Layer: Research / governance
Level: A
Bağlam: Bu oturumda "hepsini sıraya al, herşeyi dene" talebi üzerine tam envanter çıkarıldı. `reports/evidence_matrix_v1_2026-08-07.md`, `reports/end_to_end_experiment_summary_2026-08-07.md`, `reports/mirror_analysis_2026-08-10.md`, `reports/preregistration_three_hypotheses_2026-08-10.md`, `reports/user_research_kit_2026-08-10.md` ve bunlara bağlı `research/`, `tests/`, `data/backtest_out/` altındaki 2026-08-04..08-10 tarihli çıktılar — hiçbiri decision-log'da yok (grep ile doğrulandı, sıfır eşleşme). Bu, CLAUDE.md Bölüm 3'ün ("her önemli karar buraya girer") tekrarlayan biçimde ihlal edildiği anlamına geliyor — tek seferlik değil, en az 5 farklı tarihte.
Bulunan (önceden bilinmeyen) içerik özeti:
- FORMAL EVIDENCE-GATE MATRİSİ (2026-08-07) zaten var: PASS/FAIL/UNKNOWN/INSUFFICIENT_DATA/NOT_OPENED/PARTIAL sözlüğüyle 17 kapı tanımlı. Sonuç: "Discovery PASS, ama Economic-validation FAIL (maliyet %0.55→%1.00 pozitiften negatife döndü), Distribution-robustness FAIL, Rejection-quality FAIL (%41.79 yanlış-red oranı — bu oturumun kendi bulgusuyla aynı yönde), Locked-OOS NOT_OPENED, Execution/Capacity INSUFFICIENT_DATA/UNKNOWN." Genel sonuç zaten "NO-GO/promotion yok" olarak kayıtlı.
- MIRROR ANALYSIS (2026-08-10) bu oturumdaki "score backward-looking" bulgusunu DAHA DA sertleştiriyor: L4 bulgusu — en yüksek score-quintile İÇİNDE bile eligible medyan -%0.20 vs not-eligible +%1.08. Yani sorun "iyi score, kötü seçim" değil; score-bandının kendisi bilgi taşımıyor VE entry_ok o bandın içinde de kötüyü seçiyor. Ayrıca "fade the score" sentez-testi de reddedildi (follow +%0.77 vs fade -%0.89 top-decile medyan) — skoru ters çevirmek de çözüm değil.
- PRE-REGISTRATION (2026-08-10) 3 hipotezi (H1 gap-reversal, H2 rvol-inversion, H3 ATR-parity) zaten dondurmuş — "İKİ KAPI açılmadan (veri-bütünlüğü E2/V0 + kullanıcı-gerçeği PR1/PR7) confirmatory koşu YAPILMAYACAK" kuralıyla. Bu, HARKing/multiple-testing'i önlemek için.
- USER RESEARCH KIT (2026-08-10) zaten yazılmış — PR1 (12 görüşme scripti), PR7 (AI-ikame testi), PR2 (5 positioning-varyantı) hazır, yalnız Meriç'in gerçek kullanıcılarla çalıştırması gerekiyor.
TUTARSIZLIK TESPİTİ (bu turda, "ufak ihtimalleri atlama" talebiyle bulundu): resolved_pct_t5 ↔ cache-türetilmiş fwd-5g-getiri korelasyonu ÜÇ farklı ölçümde ÜÇ farklı sayı veriyor: (a) `strategic_lab_2026-08-10.json` V0: Pearson=0.8607, n=2.000 (örneklem). (b) `preregistration_three_hypotheses_2026-08-10.md`: "korelasyon 0.325" — HİÇBİR script/artifact'te bu sayıyı üreten kod bulunamadı (izlenemiyor). (c) Bu turda bağımsızca çalıştırılan tam-popülasyon kontrolü (n=7.454, pure-python Pearson/Spearman): Pearson=0.5515, Spearman=0.6038. Üç sayı da birbirinden farklı — bu, resolved_pct_t5'in KENDİSİNİN net tanımlanmamış olduğunu (entry-price konvansiyonu, ufuk hizalaması, örneklem farkı) gösteriyor; E2/V0 kapısı şu an güvenilmez bir sayıya dayanıyor.
Ayrıca doğrulandı: `catalyst_factor` tam-evrende (53.859 satır) yalnızca `''` veya `'0.0'` değerleri alıyor — kesin ölü feature, önceki turdaki bulgunun tam-popülasyon teyidi.
Karar: (1) Bu envanter artık kayıtlı — gelecekte "biliyor musunuz" sorusu bu girdiye referans verebilir. (2) V0/resolved_pct_t5 tanımı YENİDEN NET biçimde belgelenmeli ve tek-bir-doğru-implementasyon olarak dondurulmalı, üç farklı sayı çelişkisi kapanmadan E2/V0 kapısı "kapandı" sayılamaz. (3) Pre-registration'daki H1/H2/H3'ü ÇALIŞTIRMAMA kararı bu girdiyle teyit ediliyor — kullanıcıdan açık onay gelmeden bozulmayacak.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Yeni deney yapmadan önce mevcut envanterin decision-log'a işlenmesi ve V0 tutarsızlığının çözülmesi önceliklendirildi.
Kanıt: `reports/evidence_matrix_v1_2026-08-07.md`, `reports/end_to_end_experiment_summary_2026-08-07.md`, `reports/mirror_analysis_2026-08-10.md`, `reports/preregistration_three_hypotheses_2026-08-10.md`, `reports/user_research_kit_2026-08-10.md`, `data/backtest_out/strategic_lab_2026-08-10.json` (V0 alanı), bu turun bağımsız V0 kontrolü (script kaydedilmedi, sonuç yukarıda).

---
_Not (düzeltildi 2026-07-29): docs/INDEX.md 2026-07-24'te zaten gerçek indekse dönüştürülmüştü; bu satır o tarihten sonra güncellenmemiş bayat bir notu tekrarlıyordu. 2026-07-29'da INDEX.md'ye ayrıca makine-okunur bir manifest eklendi (bkz. aşağıdaki girdi)._

[2026-08-10] — KAYIT-BOŞLUĞU KAPATILDI: iki tam deney bataryası (Strategic Lab + 10-Perspective, toplam 31 deney, 18/18+10/10 test geçti) daha önce hiç decision-log'a girmemiş — şimdi kaydediliyor + kendi bulgularımızla sentezlendi (Level A, kayıt+sentez)
Layer: Research / quant
Level: A
Bağlam: `reports/strategic_lab_experiments_2026-08-10.md` ve `reports/ten_perspectives_lab_2026-08-10.md` (+ `research/strategic_lab_2026_08_10.py`, `research/ten_perspectives_lab_2026_08_10.py`, ilgili testler) tarihi 2026-08-10 olmasına rağmen bu oturumun kendi kayıtlarında (decision-log dahil) hiç görünmüyordu — CLAUDE.md Bölüm 3'ün gerektirdiği kayıt disiplini boşluğu. Veri: `full_universe_enriched.csv` 53.859 ham satır → 27.386 dedup'lu symbol-day, 2025-09-11..2026-07-13. Yöntem: date-block bootstrap CI (1000 çekiliş), medyan/winsorize/pozitif-oran — bu oturumdaki gün-kümeli SE yaklaşımından DAHA GÜÇLÜ (gün-içi VE günler-arası otokorelasyonu birlikte hesaba katıyor).
Başlıca bulgular (batarya 1 — Strategic Lab):
- R1: score geçmiş-5g getiriyle ρ=0.376, gelecek-5g getiriyle ρ=0.013 (n=16.693) — score büyük ölçüde OLMUŞ OLANI ölçüyor.
- P1: eligible portföy, aynı-gün rastgele-rejected portföylerden medyan -2.01pp kötü, 35 günün yalnız %31'inde önde (maliyet-sonrası) — "selector" ürün-iddiası KANITSIZ.
- R2: reverse-ranking YÖNÜ tekrarlıyor (eligible -0.386% vs rejected +0.427%) ama block-CI'lar örtüşüyor — kararsız, KAPATILDI değil "kesin değil".
- S1: tam-evren etkin örneklem ~620 (27.361 satırdan, ~44x küçültme); eligible ~168 (799'dan ~4.8x). Satır-sayısına dayalı TÜM anlamlılık iddiaları yanıltıcı.
- E2/V0: |drift|≤%1 alt-kümesi medyanı -%0.39'dan +%0.52'ye taşıyor; resolved_pct_t5 vs cache korelasyonu yalnız 0.86 — veri-bütünlüğü sinyalden daha belirleyici (2026-07-31 "resolved_pct_t5 MFE-bozuk" bulgusunun üçüncü bağımsız teyidi).
- X1/X3: eligible 5g MFE medyanı +%4.26, MAE -%4.36; hold-to-horizon bu excursion'ın yalnız ~%14'ünü yakalıyor — asıl fırsat pencerede, endpoint'te değil.
- X6: naif -1×ATR invalidation-exit medyanı KÖTÜLEŞTİRİYOR (-0.63% vs -0.39%) — basit stop çözüm değil.
- E1: entry-timing maliyeti küçük (-0.12pp) — bu programın kendi entry_point_drift.py bulgusunu teyit ediyor.
- P2: aday-korelasyonu düşük (medyan 0.19) — redundancy ana sorun değil.
- P7: kayıplar zaman-kümeli (lag-1 otokorelasyon 0.23) — S1'in düşük-etkin-n bulgusunun bir nedeni.
Başlıca bulgular (batarya 2 — 10-Perspective, batarya-1'i tekrarlamıyor):
- Q3 (KRİTİK, extension/exhaustion'ı YENİDEN ÇERÇEVELİYOR): score en güçlü dist_52w_high (ρ=0.667) ve past_5d_pct (ρ=0.376) ile kodlanmış — yani EXTENSION. Ama en fazla İLERİYE-dönük bilgi taşıyan feature'lar lottery_factor (ρ=-0.110) ve overnight_gap_factor (ρ=-0.095) — İKİSİ DE NEGATİF ve score'un ağırlıklandırmasında muhtemelen ters yönde kullanılıyor.
- F1: score'un olasılık-kalibrasyonu sabit-baseline'dan KÖTÜ (Brier-skill -0.019/-0.030) — rastgeleden kötü, tahmin etmemekten daha kötü.
- Q5: eligible, SPY'a göre medyan -1.22pp (CI [-2.11,-0.23], sıfırın altında istatistiksel).
- M1/M2: yüksek-rvol eligible en kötü kohort (-%1.77); büyük gap-up'lar başarısız (-%3.04), büyük gap-down'lar sıçrıyor (+%3.05) — score'un ödüllendirdiği yön ters.
- Q1: adverse-excursion evrensel (taban %86.5, eligible %91.2) — 1-ATR stop sınıfı bu ufukta yapısal olarak kırılgan.
- catalyst_factor SABİT-SIFIR (ölü feature, score ağırlığı işgal ediyor, sıfır bilgi taşıyor).
- P2(batarya-2): ATR-parity sizing en iyi maxDD (-%15.9 vs eşit-ağırlık -%24.3) — construction, selection'dan daha güçlü bir kaldıraç.
KENDİ BULGULARIMIZLA SENTEZ (bu oturum):
- Extension/exhaustion geri-çekilmesi (yukarıdaki DÜZELTME girdisi) Q3 ile TUTARLI ve DAHA İYİ AÇIKLANIYOR: score gerçekten extension'ı kodluyor (composite_score↔dist_52w_high r=+0.663, PCA bulgusu — Q3'ün ρ=0.667'siyle bağımsız teyit) ama extension'ın kendisi ileri-getiriyi monoton bozmuyor (extension_cap_test.py Test A) çünkü asıl ileri-bilgi TAMAMEN FARKLI feature'larda (lottery/overnight-gap, negatif) — score onları yanlış yönde/hiç kullanmıyor. "Extension → mean-reversion" nedensel hikayesi yerine "score, zayıf-ama-gerçek ileri-sinyali görmezden gelip geçmişi kodluyor" daha doğru çerçeve.
- S1'in etkin-örneklem bulgusu, bu oturumdaki "anlamsız" sonuçların (reverse-ranking kapanışı, extension-cap testi) neden sistematik olarak anlamsız çıktığını açıklıyor — gün-kümeli SE bile günler-arası otokorelasyonu (P7=0.23) hesaba katmıyor, gerçek n_eff daha da küçük. Bu, önceki "anlamsız" kararları ÇÜRÜTMÜYOR (yön aynı: daha az güç → daha zor anlamlılık, tutucu kalıyor) ama "kanıtsız" ile "sıfır-etki" arasındaki farkı netleştiriyor.
- E2 (drift-filtresi medyanı tersine çeviriyor) muhtemelen bu oturumda flagledigimiz Q4 outlier günlerinin (+134%/+176%) açıklaması olabilir — ayrı doğrulanmadı, açık.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A). Programın merkezi ampirik cevabı artık şu: (1) score geçmişi ölçüyor, geleceği değil (5 bağımsız kanıt hattı: R1,R4,R10,Q3,F1,Q5); (2) seçim katmanı değer EKSİLTİYOR (P1, Q5, F1 — 3 bağımsız kanıt); (3) tek somut ileri-yapı path/exit'te (X1/X3) ve construction'da (P2-batarya2), gated behind data-integrity (E2/V0); (4) parametre-ayarı DONDURULMALI, ileri-dönük hedef olmadan.
Kanıt: `reports/strategic_lab_experiments_2026-08-10.md`, `reports/ten_perspectives_lab_2026-08-10.md`, `research/strategic_lab_2026_08_10.py`, `research/ten_perspectives_lab_2026_08_10.py`, `tests/test_strategic_lab_2026_08_10.py`, `tests/test_ten_perspectives_lab_2026_08_10.py`, `data/backtest_out/strategic_lab_2026-08-10.json`, `data/backtest_out/ten_perspectives_lab_2026-08-10.json`.

---

[2026-08-10] — DÜZELTME: Extension/exhaustion "resmi teşhis"i geri çekildi — tam-popülasyon/gün-kümeli doğrudan-nedensellik testi doğrulamadı (Level A, düzeltme)
Layer: Research / quant
Level: A
Bağlam: Aşağıdaki girdide "entry_ok'un resmi teşhisi" ilan edilen extension/exhaustion mekanizması, aksiyon-alınabilirliğini test etmek için `extension_cap_test.py` ile derinleştirildi (bkz. o girdideki Level-B aksiyon-önerisi). Bu, önceki bulgunun kendisini sorguladı.
Bulgular (dedup'lu, gün-kümeli, tam-popülasyon n_gün≈27.323 satır, n=25.037 extension hesaplanabilir):
- TEST A (extension-decile → GERÇEK c2c5_net, doğrudan-nedensellik): monoton bozulma YOK. En yüksek decile (en uzamış isimler) en kötü getiriyi vermiyor — ort+1.00/medyan+1.26 (pozitif), t~+1.88, hâlâ |t|>2 eşiğinin altında. Hiçbir decile anlamlı değil.
- TEST B (entry_ok=True vs False ortalama-extension farkı, gün-kümeli, tam-popülasyon): eligible ort-ext +11.53 vs rejected +1.00 ama gün-kümeli paired-fark t~+1.56 — ANLAMSIZ. (Küçük/dengesiz bir alt-örneklemde -244 gözlem- daha önce t~+3.35 görünmüştü; tam popülasyonda bu tutarlılık KAYBOLDU — reverse-ranking'te görülen aynı küçük-n kırılganlığı.)
- TEST C (extension-cap simülasyonu — eligible kümesine medyan/p70 tavanı): capped-eligible ne orijinal-eligible'dan ne rejected'ten anlamlı farklı (iki cap seviyesinde de |t|<1). Önerilen "aksiyon" (entry_ok'a extension-tavanı ekleme) gerçekleşen-getiriyi iyileştirmiyor.
- METODOLOJİK NOT: orijinal "15× decile-rate" bulgusu (`extension_exhaustion_test.py`) satır-bazlıydı, DEDUP'LANMAMIŞ 6.000-satırlık rastgele örneklemdeydi — reverse-ranking'i çökerten aynı risk (saatlik-scanner gün-içi tekrarı) bu bulguda hiç kontrol edilmemişti.
Karar: Extension/exhaustion, "entry_ok'un resmi teşhisi" statüsünden "kısmen-desteklenen ama doğrudan-nedensellik testinde doğrulanamayan hipotez"e düşürülüyor. entry_ok<rejected inversiyonunun kök-nedeni HÂLÂ AÇIK. Extension-cap Level-B aksiyon-önerisi ERTELENDİ — dayandığı temel iddia kendisi tam-popülasyon testini geçemedi.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ. Aşağıdaki girdideki "resmi teşhis" ifadesi bu girdiyle geçersiz kılınıyor; gelecekte referans verilirken bu düzeltme esas alınmalı.
Kanıt: `extension_cap_test.py`.

---

[2026-08-10] — Reverse-ranking RESMEN KAPATILDI (artefakt); extension/exhaustion entry_ok'un resmi teşhisi oldu (SONRADAN DÜZELTİLDİ — bkz. yukarıdaki girdi); composite_score veri-kapsamı 39-güne daraldığı bulundu (Level A, kapanış)
Layer: Research / quant
Level: A
Bağlam: Önceki iki Level-A girdisinin ("Strategic Thinking Lab: 5 deney" ve "10-Perspektif: 4 ek deney") sentez raporunda (`docs/2026-08-10-iki-belge-kapsamli-sentez.md`) belirlenen 3 "Hemen" aksiyon maddesi işlendi: (1) reverse-ranking'i kapat, (2) extension/exhaustion'ı entry_ok'un resmi teşhisi olarak geçir, (3) günlük sembol-tekrarını (414 vs 814.5) aç-kapa.
Bulgular:
- REVERSE-RANKING KAPATILDI: `reverse_ranking_closure.py` ile iki eksik giderildi — (a) `full_universe_enriched.csv`'de aynı-(symbol,scan_date) için en-erken-scan_ts dedup'ı (bkz. aşağıdaki sembol-tekrarı maddesi), (b) tek IS/OOS yerine 4 çeyreklik pencere + her pencerede gerçek matched-random-kontrol (çoklu seed). Sonuç: Q1 anlamlı (t~+3.53), Q2 anlamlı ama RANDOM da ÜST'ü geçiyor (ALT özel değil, ÜST kötü), Q3 anlamsız (t~-0.50), Q4 anlamsız + outlier-şüpheli (t~-0.16, günlük +134/+176% gibi aşırı değerler — veri-hatası şüphesi, ayrı incelenmedi). TAM DÖNEM (34 gün, dedup'lu): ALT-%20 vs ÜST-%20 t~-0.14 (anlamsız), ALT vs 3 random-seed kontrolün hepsinde de anlamsız. KARAR: bulgu dönem-özel artefakt, ARTIK "düzeltildi/sınırda" değil, RESMİ OLARAK KAPATILDI — üretime/stratejiye taşınmayacak.
- YAN-BULGU (önemli, kapsam-sınırlayıcı): Dedup sonrası `composite_score`'un `full_universe_enriched.csv`'de güvenilir-dolu olduğu aralık yalnızca 2026-05-06 → 2026-07-13 (39 işlem-günü) — bu tarihten önce boş/NaN. Bu programdaki TÜM composite_score-tabanlı testler (bu tur dahil önceki turlar) "Eylül 2025–Temmuz 2026 geneli" değil, bu dar 39-günlük pencerede çalışmış. Kapsam iddiaları bu sınırlamayla yeniden okunmalı.
- EXTENSION/EXHAUSTION RESMİ TEŞHİS: önceki turda kanıtlanan bulgu (ATR-extension deciline göre entry_ok-oranı ~15× artış: [0.0,0.4,0.5,1.4,2.1,3.9,4.3,7.5,6.8,5.3]%, + composite_score↔dist_52w_high r=+0.663) burada entry_ok'un RESMİ teşhisi olarak kayda geçiriliyor: entry_ok, tasarım/yan-etki olarak zaten-uzamış (mean-reversion'a yakın) isimleri sistematik seçiyor — eligible<rejected ve conviction A<B<C inversiyonlarının ilk somut nedensel açıklaması. Aksiyon-adayı (Level B, henüz uygulanmadı): entry_ok kriterine extension-tavanı eklemenin cohort kalitesini iyileştirip iyileştirmediği ayrı test edilmeli.
- SEMBOL-TEKRARI AÇIKLANDI: `edge_recheck.csv`'nin 53.754 satırı yalnız 27.323 benzersiz (symbol,scan_date) çift — 13.062 çift (%48) tekrarlı (max 17×, örn. NVDA 2026-05-19). Kök-neden: production scanner saatlik çalışıyor (`core/scheduler.py`, interval_minutes=60), aynı sembol/gün birden çok kez ateşleniyor, composite_score hafif kayıyor ama outcome (c2c5_net, price_cache'ten tek-seferlik) sabit kalıyor. Tekrar-sayısı ile skor/outcome arasında yön-yanlılığı yaratacak korelasyon yok (rank-r=0.032/0.026) ama örneklem-büyüklüğünü yapay şişiriyor (gerçek fırsat n=27.323, "n=53.754" değil) ve sık-ateşlenen isimleri gün-ortalamalarında aşırı-temsil ediyor. Bu turdan itibaren dedup zorunlu; geçmiş satır-bazlı analizlerin şişirilmiş n ile yapıldığı not edilmeli.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A analiz/kapanış). Reverse-ranking artık aday listesinden düşürüldü. Extension/exhaustion, entry_ok üzerinde somut bir Level-B düzeltme deneyi için temel oluşturuyor. composite_score'un 39-günlük kapsam sınırı, gelecekteki tüm composite_score-tabanlı iddiaların örneklem-genelleme diliminde açıkça belirtilmesini gerektiriyor.
Kanıt: `hemen-yapilacaklar-sonuc.md`, `reverse_ranking_closure.py`.

---

[2026-08-10] — 10-Perspektif belgesinden 4 ek deney koşuldu: extension/exhaustion mekanizması kanıtlandı, PCA-redundancy hipotezi reddedildi, reverse-ranking cluster-robust'ta DÜZELTİLDİ (Level A, bulgu)
Layer: Research / quant
Level: A
Bağlam: `docs/2026-08-10-finpilot-10-perspektif-red-team-vizyon-arastirmasi.md`'nin (10-Perspektif) Persona-1 deney listesinden 4 ek deney koşuldu, ardından bu deney + önceki Strategic Thinking Lab deneyleri (9 toplam) tek sentez raporunda birleştirildi.
Bulgular:
- EXTENSION/EXHAUSTION MEKANİZMASI KANITLANDI: ATR-extension (20g-getiri/ATR) deciline göre entry_ok(eligible)-oranı ~15× artıyor ([0.0,0.4,0.5,1.4,2.1,3.9,4.3,7.5,6.8,5.3]%) — entry_ok sistematik olarak zaten-uzamış/tükenmiş isimleri seçiyor. Bu, önceden bilinen "eligible < rejected" ve "conviction A<B<C" inversiyonlarının ilk somut nedensel açıklaması.
- PCA/FEATURE-REDUNDANCY: composite_score↔finpilot_score dışında (r=+1.000, bilinen) feature-ailesi BEKLENENİN AKSİNE çok redundant değil — %90 varyansa 7-8/11 bileşen gerekiyor. "2-3 bağımsız eksene iniyor" hipotezi (10-Perspektif Persona-1) test edilip REDDEDİLDİ. YENİ: composite_score↔dist_52w_high r=+0.663 (extension-bulgusuyla tutarlı ikinci kanıt hattı).
- REVERSE-RANKING DÜZELTMESİ (kritik): Önceki turda "IS/OOS-tutarlı en güçlü sinyal" diye raporlanan composite_score ALT-%20 (reverse) bulgusu, gün-seviyesinde (cluster-robust) yeniden test edildi. IS'te fark hâlâ pozitif/sınırda-anlamlı (n=26 gün, t~+2.22) ama OOS'ta TAMAMEN ÇÖKTÜ (n=30 gün, t~-0.15, birkaç outlier-gün varyansı yutuyor). Bulgu artık "kanıtlanmış" sayılamaz — ya matched-random+yeni-OOS-penceresiyle tekrar test edilmeli ya da artefakt olarak resmi kapatılmalı. Bu, programın kendi "aynı-gün kümelenme CI'ları şişirir" uyarısının doğrulanmış hâli.
- ATR-BAZLI SIZING: 1/ATR ters-orantılı position-sizing, concentration-kısıtlı portföyde Sharpe'ı kötüleştirdi (0.165→0.127) — beklenmedik, concentration-kısıtı hâlâ dominant tek düzeltme.
- YAN-BULGU: günlük ort. 414 benzersiz-sembole karşı 814.5 toplam-satır (~2× tekrar) — dedup/multi-timestamp etkisi incelenmedi, açık soru.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A analiz). Extension/exhaustion bulgusu entry_ok'un resmi teşhisi olarak öneriliyor; reverse-ranking bulgusu geri çekilmeli/yeniden test edilmeli.
Kanıt: `docs/2026-08-10-iki-belge-kapsamli-sentez.md`, `extension_exhaustion_test.py`, `pca_feature_redundancy.py`, `cluster_robust_and_clustering.py`, `atr_sizing_test.py`.

---

[2026-08-10] — Strategic Thinking Lab: 5 deney koşuldu — canlı-skor train/serve skew bulundu, reverse-ranking + concentration-portföy adayları (Level A, bulgu)
Layer: Research / quant / infra
Level: A
Bağlam: "FinPilot Strategic Thinking Lab v1.0" belgesindeki Experiment Factory'nin (72 deney) çalıştırılabilir alt-kümesi (5 deney) koşuldu; kalanı yeni-veri veya kullanıcı-pilotu gerektirdiği için ertelendi (triyaj: `docs/2026-08-10-big-bet-1-sonuclar.md` §0).
Bulgular:
- ATR LOOK-AHEAD AUDİT: `edge_recheck.py`'nin ATR hesabı (pencere ei-14..ei-1, giriş-öncesi) klasik gelecek-sızıntısı taşımıyor — ATR→MAE risk-bulgusu (IC −0.51) sağlam kaldı. AMA yeni bulgu: `scanner/evaluate.py:403,412-413,497-498` canlı ATR/RSI/MACD/hacim-çarpanını `df_1d/df_15m[...].iloc[-1]` ile hesaplıyor; `core/scheduler.py` ana-tarama `interval_minutes=60` ile gün-içi çalışıyor → canlı skor çoğu zaman GÜN-İÇİ PARÇALI barla üretiliyor (RVOL özellikle saat-bağımlı yanlı). Klasik look-ahead değil, train/serve skew — P0 score-replay sorununun ve entry_ok/conviction inversiyonlarının olası kök-nedenlerinden biri.
- GİRİŞ-NOKTASI TESTİ (1.400/1.926 sembol, 36.932 satır): sinyal-close/ertesi-open/ertesi-close arasında SPY-excess'te anlamlı fark yok, hiçbir noktada drift/half-life yok → "giriş-zamanlaması yanlış" hipotezi ELENDİ.
- REVERSE-RANKING: composite_score ALT-%20 (fade-adayı), hem IS (medRet −0.155 vs üst-%20 −0.647) hem OOS'ta (+1.018 vs +0.517) baseline+üst-%20'yi tutarlı geçti — programda ilk IS/OOS-tutarlı doğrudan-getiri-sinyali (matched-random-kontrol doğrulaması bekliyor; finpilot_score'daki eşdeğer test tie-artefaktı verdi, gerçek değil).
- RANDOM-ENTRY KONTROLÜ: gerçek sinyaller (n=53.754) random-entry kontrolü (n=3.000) aynı exit-mekaniğiyle her metrikte (win/medyan × tb_ret/c2c5_net) geçti → taban-sinyal-üretimi rastgeleden gerçekten iyi; sorun downstream composite-ranking'te (yukarıdaki madde ile tutarlı).
- CONCENTRATION-PORTFÖY (yaklaşık, n=52-56 gün): kısıtsız top-10 ortalama %61.79 tek-sektöre yığılıyor; max-3/sektör kısıtı volatiliteyi yarıya (7.08→3.94), CVaR5%'i yarıdan-aza (−26%→−10.5%), maxDD'yi yarıdan-aza (−49%→−22%) indirdi VE ortalama-getiriyi artırdı (+0.07%→+0.65%) — alfa gerektirmeyen, en yüksek-etkili düzeltme adayı.
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (Level A analiz). Sıradaki öneriler: canlı-skor feature-timing düzeltmesi (Level B adayı), reverse-ranking'in pre-registered matched-random doğrulaması, concentration-kısıtının tam-evrende doğrulanması, Big Bet #3 (gerçek-sektör-etiket) hâlâ bekliyor.
Kanıt: `docs/2026-08-10-finpilot-strategic-thinking-lab-v1.md`, `docs/2026-08-10-big-bet-1-sonuclar.md`, `entry_point_drift.py`, `reverse_ranking_and_random_entry.py`, `concentration_portfolio_test.py`.

---

[2026-07-31] — Opsiyon-faktörü pilotu (yeni-bilgi) hattı kuruldu (Level A, local-run bekliyor)
Layer: Research / data
Level: A
Bağlam: Roadmap v2 P1 — teknik faktörler dürüst-metrikte tükendi (IC~0); tek yeni-bilgi yolu opsiyon positioning/IV (fiyat-hacimden türetilemez). EODHD UnicornBay opsiyon geçmişi Q4-2023'ten 2.5+ yıl EOD (Greeks/IV/OI/put-call), 6.600+ ABD hissesi → sinyal penceresini (Eyl'25–Tem'26) kapsıyor.
Değişiklik: `data/eodhd_client.py`'ye `options_eod()` metodu + modül wrapper eklendi (`mp/unicornbay/options/eod`, JSON:API, 24s cache). Yeni `options_factor_pilot.py`: 6 faktör türetir (put/call OI & hacim, ATM IV, IV skew, toplam OI/hacim) → `edge_recheck` dürüst-metrik + IS/OOS rank-IC testi; modlar: `--probe` (canlı şema+plan teyidi), `--build` (resumable), `--analyze`. Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ.
Etki/Durum: uygulandı ve AĞSIZ test edildi — `py_compile` temiz; `derive_factors` sentetik kontratla doğrulandı (put/call OI 1.625, ATM IV 0.35, skew 0.09); `analyze` harness'i gerçek symbol/date + sentetik faktörle çalıştı ve rastgeleyi doğru "tutarsız" işaretledi (IS/OOS disiplini). LOCAL-RUN bekliyor (ağ + EODHD UnicornBay opsiyon eklentisi gerekir). Ön koşullar: (1) opsiyon eklentisi plan kapsamı `--probe` ile teyit; (2) alan adları ilk yanıtla doğrulanıp gerekirse `FIELD_MAP` güncellenmeli. Bir faktör IS+OOS aynı işaret & |IC|>~0.03 verirse projenin ilk gerçek lead'i olur; vermezse kolay-erişilebilir veri de tükenmiş sayılır.

---

[2026-07-31] — Edge araştırması: dürüst-metrikte tradeable alfa yok + resolved_pct_t5 P0-bozuk (Level A, bulgu)
Layer: Research / quant
Level: A
Bağlam: FINPILOT RESEARCH master prompt — "skor gerçekte neyi ölçüyor?" bilimsel olarak araştırıldı.
Bulgular (hepsi kanıtlı, IS/OOS ve dürüst metrikle):
- `edge_recheck.py` (yeni, izole) tüm evreni (53.754 satır) price_cache'ten GERÇEKLEŞEN kapanış-kapanış + triple-barrier (cost'lu) ile yeniden hesapladı.
- METRİK DENETİMİ: ATR↔resolved_pct_t5(enriched) +0.40 vs ATR↔gerçekleşen c2c +0.01. `resolved_pct_t5` MFE (en-iyi-durum) izliyor, gerçekleşen getiriyi değil → "ATR edge" %100 metrik artefaktı.
- SKOR TESTİ (dürüst): composite_score IC −0.03 (kırık), finpilot_score +0.03 (ihmal, rejim-kararsız: bull +0.055/bear −0.093), ATR ~0/negatif. Cost sonrası evren medyanı ≈0; triple-barrier −0.95.
- ARAMA: 2-faktör 74 kombo (0 stabil) + 4000-konfig ağırlık optimizasyonu (add/remove/invert/reweight, IS/OOS) → hiçbir konfig baseline'ı stabil geçmedi; IS-en iyi OOS'ta şans (%44).
Etki: Üretim skoru/scanner/entry-exit/risk/canlı yüzey DEĞİŞMEDİ (yalnız analiz). İKİ P0 SONUÇ: (1) `resolved_pct_t5` MFE-bozuk → bu metriğe dayanan TÜM geçmiş "edge" iddiaları yeniden temellenmeli; (2) mevcut günlük-bar faktör setinde doğrulanmış tradeable alfa YOK → ilerlemek recombination değil YENİ veri/faktör ya da değer önermesini karar-destek/eğitime kaydırma gerektirir.
Durum: uygulandı — Level A (araştırma bulgusu). Kanıt: `docs/2026-07-31-FinPilot-Research-skorun-anlami-RAPOR.md`, `edge_recheck.py`, `data/backtest_out/edge_recheck.csv`.

---

[2026-07-30] - Sinyal izleme shadow scorecard altyapısı (Level A, uygulandı)
Layer: Research / engineering
Level: A
Bağlam: `docs/2026-07-29-sinyal-izleme-gelistirme-UCTAN-UCA-plan.md` offline kontrol grubu, horizon sweep, dağılım yüzdelikleri, SPY excess return, ATR-normalize getiri, segment alanları ve risk-ayarlı özetler öngörüyor. Faz 0 kontrolünde `data/price_cache` benchmark dahil `2026-06-30` tarihinde bitiyor; mevcut 107 dedup sinyalin tamamı olgunlaşmamış kaldı.
Değişiklik (önce/sonra): Önce `shadow_scorecard.py` yalnız seçilmiş satırları ve model bariyer sonuçlarını özetliyordu; sonra kontrol satırlarını opsiyonel dahil eden, model-bağımsız ileri getiri/MFE, horizon sweep, red nedeni, ADV/veri kalite segmentleri, SPY excess return, p10/medyan/p90, Sharpe-benzeri metrik ve deterministik bootstrap aralığı üreten izole altyapı eklendi. `tests/test_shadow_scorecard.py` sentetik sözleşmeleri doğruluyor.
Etki: Scanner skorları, filtreler, entry/exit kuralları, risk boyutlandırması ve canlı Karne/web yüzeyi değişmedi. Cache yenilenene kadar gerçek performans sonucu üretilmemeli; mevcut çalışma yalnız altyapı ve veri-yeterlilik bulgusudur. Faz 4b Level B olarak bu kaydın kapsamında değildir.
Durum: uygulandı — Level A. Kanıt: `python -m pytest tests/test_shadow_scorecard.py -q` (3 passed); baseline CLI (`--dedup`) 107/107 pending.

---

[2026-07-29] — Waitlist + demo feedback endpoint'lerine Telegram admin bildirimi (Level B, uygulandı)
Layer: Engineering / product distribution
Bağlam: Web yüzü denetimi (`docs/2026-07-29-web-yuzu-DENETIM-raporu.md`) waitlist ve demo feedback formlarının gerçek ve uçtan uca bağlı olduğunu, ama yeni kayıt/yorum geldiğinde hiçbir bildirim gitmediğini kanıtladı: waitlist SMTP yapılandırılmamış (`_notify_waitlist_signup` "skipped" logluyor), feedback yalnız SQLite'a yazıyor. Sonuç: gönderimler fark edilmeden birikiyordu.
Değişiklik: `api/routers/waitlist_signup.py` (yeni `_notify_admin_telegram` helper + signup sonrası ping: e-posta/kaynak/toplam) ve `api/routers/demo_feedback.py` (feedback kaydı sonrası ping: ödeme niyeti + yorum özeti) mevcut `distribution.telegram_client.notify_admin` altyapısına bağlandı. İkisi de try/except best-effort — bildirim hatası isteği bozmaz; `notify_admin` yapılandırma yoksa False döner (raise etmez). Scanner/skor/veri saklama/mevcut SMTP akışı değişmedi (yalnız ekleme — CORE-009).
Etki: Yeni waitlist kaydı / demo yorumu anında Telegram admin'e düşer (`TELEGRAM_BOT_TOKEN`+`TELEGRAM_ADMIN_ID` gerektirir; `.env`'de mevcut). 4/4 birim testi geçti: ping içeriği doğru, boş feedback ping atmıyor, `notify_admin` patlasa bile istek OK. `py_compile` temiz. Canlı deploy yapılmadı.
Durum: uygulandı — Level B; Meriç onayı alındı (2026-07-29). Canlı deploy kararı bu kaydın kapsamında değildir.

---

[2026-07-29] — Telegram gerekçe katmanına bağlam ve izlenecek sonuç açıklaması (Level B, pending)
Layer: Content / product distribution
Bağlam: Günlük Telegram taslağı mevcut faktörleri tek tek açıklıyordu; faktörlerin birlikte neyi düşündürdüğü ve hangi gözlenebilir sonucun izleneceği yeterince açık değildi.
Değişiklik: `distribution/rationale.py` içindeki deterministik rationale üretimine rozet kombinasyonlarına dayalı sentez cümlesi eklendi. Metin sırasıyla gözlenen nedenleri, bağlamsal birleşimi ve doğrulanmamış açık soruyu ifade ediyor; TR/EN/DE çıktıları korunuyor. Scanner skoru, eşikler, risk, entry/exit ve yayın akışı değişmedi.
Etki: Telegram ve snapshot rationale metinleri daha açıklayıcı ve bağlamlı oldu; bugünkü önizleme lint'ten geçti. Web public projection artık graded adaylar ve scan-context kayıtlarında `risk_reward`, `stop_loss`, `take_profit` ve `stop_loss_percent` alanlarını dışarıda bırakıyor. Karne API'si HTTP 401 olduğunda mevcut DB fallback notu korunuyor. Canlı Telegram/web yayını yapılmadı.
Durum: uygulandı — Level B; Meriç onayı alındı (2026-07-29). Canlı yayın kararı bu kaydın kapsamında değildir.

---

[2026-07-29] - Scanner 15-hata triyaji tamamlandi (10 Level A duzeltildi, 5 Level B/C flagged) + render.yaml/.env bulgusu genisletildi
Baglam: Onceki 07-29 kayitlarindaki dogrulama kosusunda (734 passed, 15 failed)
bulunan 15 test hatasi tek tek incelendi (kullanicinin "onayliyorum" onayi
uzerine, kullanici oturumda musait degildi, "otonom calis, iyi kararlar ver"
talimati verildi).
Sonuc: 10/15 duzeltildi (Level A, sadece test katmani, production kodu
degismedi):
(1-2) test_score_engine_catalyst/squeeze_off_by_default: Faz 5 (2026-06-20,
b2bdba0) skor x0.5 dususu icin test beklentisi guncellenmemisti (3.0->1.5).
(3-5) test_defensive_strategy, test_squeeze_factor_high_short_low_float,
test_get_alpha_features_skips_squeeze_when_disabled: yerel .env'deki
FINPILOT_ENABLE_ALPHA_V2=1 testlere sizip squeeze agirligini (0.5/0.5->0.7/0.3)
ve gate'i degistiriyordu; testlere izolasyon eklendi.
(6) test_returns_none_on_insufficient_data: 2026-07-15 (2c60744)
_unavailable_result sozlesmesi icin test bayikti (None bekliyordu, artik
Tier-3 dict donuyor - kasitli, dokumante degisiklik).
(7-8) test_returns_expected_keys, test_rounds_price_to_four_decimals:
_fetch_price_sync Alpaca-once + yf.download() fallback mimarisine tasinmis,
test eski yfinance.Ticker mock hedefini kullaniyordu.
(9) test_auth_register_login_and_me_flow: KRITIK BULGU - core.config.DB_PATH
modul-seviyesi sabit, core.config ilk import edildiginde (collection
sirasinda, fixture'lardan once) donuyor. monkeypatch.setenv("FINPILOT_DB_PATH")
tek basina auth.database.Database()'e ulasmiyor (Database() no-arg cagrisi
donmus DB_PATH'i okuyor) - gercek kalici data/finpilot.db dosyasina yaziyordu,
oturumlar arasi kullanici birikip 409 Conflict'e neden oluyordu. Fix:
monkeypatch.setattr("core.config.DB_PATH", ...) eklendi.
(10) test_all_fields_present_and_lint_clean: glossary prob_band metni
"bir garanti degil" / "not a guarantee" iceriyordu - distribution/lint.py'nin
guarantee kurali negation-aware degil, "degil" ile olumsuzlanmis olsa bile
yakaliyor. Icerik 2026-07-24'te eklenmis, 07-15 collection hatasi yuzunden
gorunmezdi. FIX: icerik yeniden yazildi (linter kurali GEVSETILMEDI - CORE-002
risk&compliance kurali korundu).
5/15 kasitli duzeltilmedi: 2'si tests/test_full_universe_robustness.py
icinde (bu dosya untracked/uncommitted, baska bir es zamanli oturumun WIP'i,
dokunulmadi); 1'i test_prometheus.py port-bind zamanlamasina dayanan
environment-bagimli flaky test; 2'si scanner_rollout/test_runtime_baseline.py
: entry_ok icin score==2 + alignment_ratio>=0.66 durumunda gecerli olmasi
beklenen bir gevsetilmis giris kapisi bekliyor ama scanner/evaluate.py'de
entry_ok = bool(score == 3) sabit kodlanmis. Git log bu test dosyasinin
sadece 2026-05-05'teki dev bir "thanks" commit'inde eklendigini gosteriyor,
ilgili evaluate.py degisikligi izlenemedi - ya hic uygulanmamis planli bir
ozellik ya da gecmiste kaldirilmis bir davranis. Canli sinyal uretim
mantigini etkiledigi icin urun/quant karari gerekiyor, DOKUNULMADI.
Dogrulama: 744 passed, 5 failed, 6 skipped (once: 734/15/6), 0 collection
hatasi, 0 yeni regresyon.
3E.7 bulgusu genisletildi: yerel .env'de 18 `FINPILOT_ENABLE_*`/`FRED_*`/
`SEC_EDGAR_*` anahtari var (hepsi kisisel arastirma icin ACIK), .env.example
bunlarin hicbirini belgelemiyor, render.yaml sadece 1 tanesini iceriyor.
.env.example yorumlari bu faktorlerin coğunun "Default OFF, once shadow modda
olc" seklinde tasarlandigini gosteriyor - yani production'in bunlari
ACMAMASI kasitli/guvenli olabilir. render.yaml'a DOKUNULMADI (canli sinyal
davranisini etkileme riski, tek tarafli karar verilemez).
3E.8 (dry-run zorunlulugu) ve 3E.9 (erken uyari sistemi) incelendi ama
uygulanmadi - ikisi de canli yayin/scan pipeline'ini etkileyen, gozden
gecirme gerektiren degisiklikler.
Etki alani: tests/test_catalyst.py, tests/test_squeeze_factor.py,
tests/test_evaluate.py, tests/test_new_endpoints.py, tests/test_api_runtime.py,
distribution/glossary.py (icerik, politika degil). Commit 068f2aa, push edildi.
Not (guvenlik, bilgi amacli): render.yaml/.env karsilastirmasi sirasinda
.env icinde gercek bir FRED_API_KEY degeri goruldu; .gitignore (.env*) ve
`git log --all -- .env` ile dogrulandi - bu dosya HICBIR ZAMAN git'e commit
edilmemis, sizinti yok. Deger bu kayda veya baska hicbir committed dosyaya
yazilmadi.
Durum: 10/15 tamamlandi ve dogrulandi; 5/15 + 3E.7/3E.8/3E.9 Meric karari
bekliyor.

[2026-07-29] - Otorite-haritasi gocu: lint guard (Level A uygulandi) + INDEX.md manifest / .github rewrite (Level B pending)
Baglam: Kullanici `docs/2026-07-29-otorite-haritasi-gocu-plani.md` planini
onayladi ve "neler olusturmamiz gerekiyor" diye sordu. Uygulamadan once repo'nun
gercek governance yuzeyi okundu (varsayimla degil): `docs/INDEX.md` VE
`docs/governance/decision-log.md` zaten VARDI (plan taslaginin "ikisi de yok"
iddiasi yanlisti); INDEX.md 2026-07-24'te zaten gercek otorite haritasina
donusturulmustu, ama bu logun ust notu bunu yansitmiyordu (yukarida duzeltildi).
`_instructions/01-governance.md`, `05-escalation.md`, `08-security.md` hala
Status: DRAFT (CORE-006 onayi bekliyor); yalniz `00-core.md` ACTIVE. Kok
klasorler `00-strategy…06-releases` ve `_instructions/core-rules.yaml`
dogrulandi — gercekten yok. `.github/instructions/*.md` (7 dosya) sadece
`applyTo` degil, govde metninde de (mission.md, composite-score.md,
entry-exit-rules.md, architecture.md, glossary.md, risk-policy.md) hic var
olmamis dosyalara atif veriyordu; bunlar ICAT EDILMEDI (CORE-004), gercek
yollara veya acik "gap" notuna cevrildi.
Karar (Level A — uygulandi, otonom, izole, salt-okunur guard):
`scripts/lint_authority_map.py` olusturuldu; `docs/INDEX.md`'deki manifesti ve
`.github/instructions/*.md` applyTo alanlarini gercek agacla karsilastirir.
Calistirildi: 7/7 hayalet applyTo hatasi tespit etti, duzeltme sonrasi
`lint_authority_map: OK (0 errors, 0 warnings)`.
Karar (Level B — uygulandi, Merric onayi bekliyor, KAPANMADI):
(a) `docs/INDEX.md`'ye JSON manifest eklendi (15 entry; strategy,
product-rules, engineering-architecture, risk-policy, releases acikca
`status: gap` isaretlendi — icat edilmedi); (b) bu logun ust notu duzeltildi;
(c) `.github/copilot-instructions.md` yeniden yazildi — hayalet klasor
haritasi silindi, `docs/INDEX.md`'ye referans verildi, `core-rules.yaml`
referansi kaldirildi (CORE-003: 00-core.md'yi kopyalamak yerine referans);
(d) 7 `.github/instructions/*.md` dosyasinin `applyTo` + govde referanslari
gercek yollara veya acik gap notlarina cevrildi; (e) `CLAUDE.md` v3.0→v3.1:
Startup Sequence'e docs/INDEX.md + decision-log adimlari eklendi, Governance
bolumundeki dosya referanslari tam yola cevrildi (changelog eklendi).
Etki alani: yalnizca dokumantasyon/AI-talimat dosyalari
(`.github/**`, `CLAUDE.md`, `docs/INDEX.md`, bu log, yeni `scripts/
lint_authority_map.py`). Scanner/distribution/api/web PRODUCTION kodu
davranissal olarak DEGISMEDI.
Sinir: `AGENTS.md` DRAFT→APPROVED degisikligi yapilmadi (Level C, yalniz
Merric). `_instructions/01-governance.md/05-escalation.md/08-security.md`
DRAFT durumu degistirilmedi. `core-rules.yaml` OLUSTURULMADI (CORE-003:
00-core.md'yi tekrar etmemek icin referans kaldirmayi tercih ettik; alternatif
"olustur" secenegi Merric onayina birakildi). Yeni "gap" olarak isaretlenen
otorite dokumanlari (mission.md, composite-score.md, entry-exit-rules.md,
architecture.md, risk-policy.md) bu kararla OLUSTURULMADI/ONAYLANMADI.
Operasyonel bulgu: bu oturumda `.github/copilot-instructions.md`, `CLAUDE.md`
ve bu logun kendisi, diskteki degisiklik dogrulandiktan SONRA, editorde acik
eski-icerikli sekme/otokaydetme kaynakli goruntu ile SESSIZCE eski haline
donduruldu; ayni edit ikinci kez uygulanarak kurtarildi. Kok neden dogrulanamadi
ama YONERGE.md M1 (OneDrive/AV dosya guvenligi riski) ile tutarli — izlenmesi
gereken acik bir operasyonel risk olarak buraya kaydedildi.
Kanit: `python scripts/lint_authority_map.py` -> `OK (0 errors, 0 warnings)`.
Durum: Level A uygulandi ve dogrulandi; Level B degisiklikler diskte hazir
ancak commit/push edilmedi, Merric onayi olmadan "kapandi" sayilmaz.

[2026-07-29] - Scanner kirilma/regresyon kok neden forensic analizi + Bolum 3-Ek (Level A uygulandi + Level B pending)
Baglam: Kullanici talebiyle scanner/distribution yayin zincirinin tekrar tekrar
"harden/restore/repair" commit'i almasinin (07-17, 07-23, 07-24, 07-27x2, 07-28)
yapisal kok nedeni arastirildi (git log, requirements.txt, render.yaml/.env,
ci.yml, tests/ incelemesi).
Dogrulanan bulgular: (1) main dalina dogrudan push, CI kapi degil sonradan
dogrulama; (2) render.yaml ile .env.example arasinda iki bagimsiz elle
senkronize env kaynagi (9 FINPILOT_ENABLE_*/FRED_*/SEC_EDGAR_* bayragindan
render.yaml'da sadece 1'i var); (3) yfinance pinlenmemis (bilinen kirilgan
veri-kaynagi bagimliligi) + duckduckgo-search cakisan cift satir; (4)
scanner/data_fetcher.py'de genis kapsamli sessiz exception yutma; (5)
tests/test_scanner_contract.py fixture yoksa skipTest ile sessizce geciyordu;
(6) EN KRITIK: tests/test_ranking_guard.py, scanner.evaluate._execution_contract
import ediyordu — bu fonksiyon 07-15'te (2c60744) scanner.execution_policy.
execution_contract'a tasinmis ama test guncellenmemis; ImportError butun pytest
collection'ini 14 gundur (6+ sonraki commit boyunca) durduruyordu.
Karar: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md'ye "BOLUM 3-EK" eklendi
(Bolum 3 yeniden acilmadan, bulgular kayda gecirildi). Level A kalemleri
UYGULANDI: (a) test_ranking_guard.py import+assertion duzeltildi (davranis
degismedi, sadece dogru sembole baglandi — tier siniflandirmasi elle
dogrulandi), (b) test_scanner_contract.py skipTest -> fail, (c) ci.yml
--cov=distribution eklendi, (d) requirements.txt yfinance==1.4.1 pinlendi +
yinelenen duckduckgo-search satiri silindi.
Etki alani: tests/test_ranking_guard.py, tests/test_scanner_contract.py,
.github/workflows/ci.yml, requirements.txt. Scanner/distribution PRODUCTION
kodu davranissal olarak degismedi — sadece test/CI/bagimlilik katmani.
Sinir: render.yaml/.env birlestirme (3E.7), dry-run zorunlulugu (3E.8), erken
uyari sistemi (3E.9) Level B — Merric onayi bekliyor, henuz uygulanmadi.
Kanit: bu oturumdaki forensic analiz + pytest tam-suit calistirma sonucu
(asagida ayri girdi olarak eklenecek).
Durum: Level A kismi uygulandi; Level B kismi pending.

[2026-07-29] - Scanner kirilma/regresyon kok neden forensic analizi + Bolum 3-Ek DOGRULAMA sonucu (Level A dogrulandi, 2 yeni Level B/C bulgu)
Baglam: Bir onceki 07-29 kaydindaki 4 Level A degisiklikten sonra tam pytest
suit calistirildi (734 passed, 15 failed, 6 skipped, 380.81s,
--cov-fail-under=70 uygulanarak).
Dogrulanan sonuclar:
(1) test_ranking_guard.py fix ONAYLANDI — collection artik 0 hata (once: 1
collection error, tum suit durmustu). Hedeflenen 4 dosyanin (test_ranking_guard,
test_scanner_contract, test_distribution, test_prepublish_gate) 47 testi ayrica
izole calistirildi: 47 passed.
(2) YENI BULGU — 15 test kirmizi, hicbiri bu oturumda degistirilen 4 dosyayla
ilgili degil (test_evaluate.py, test_catalyst.py, test_squeeze_factor.py,
test_full_universe_robustness.py, test_new_endpoints.py, test_content_layer.py,
test_api_runtime.py, test_prometheus.py, scanner_rollout/test_runtime_baseline.py).
Dogrulandi: bunlar 07-15'ten beri collection hatasi yuzunden gorunmez olan,
onceden var olan olasi regresyonlar (orn. compute_recommendation_score beklenen
disi skor, dedup_symbol_day() policy kwarg'i kabul etmiyor). Olasi, test
edilmeli: her biri ayri kok-neden gerektirir — bu oturumda DUZELTILMEDI (kapsam
disi, tek tek incelenmeden production kodu degistirilmedi).
(3) YENI BULGU — --cov-fail-under=70 esigi FAIL (gercek: 43.47%). Esik
2026-03-30'da (a9f65923) 30'dan 70'e cikarilmis. Dogrulandi (hesaplandi):
distribution/ modulu kendi icinde ~63% kapsaniyor, ortalamayi dusuren o degil —
drl/ altinda binlerce satir %0 kapsanan modul (data_loader.py, ensemble_router.py,
inference.py, specialists.py vb.) asil neden. Yani bu oturumdaki --cov=distribution
eklemesi (3E.3) bu FAIL'e neden OLMADI — hesaplama distribution dahil/haric
karsilastirmasi ile dogrulandi (~%42 -> ~%43, iyilesme yonunde). Olasi, test
edilmeli: gercek CI ortaminda (GitHub Actions) bu esik hic gecmis mi yoksa
yakinda mi bozulmus — bu ortamdan GitHub Actions calisma gecmisine erisilemedi
(repo'da PR yok, direkt main'e push), dogrulanamadi.
Karar: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md Bolum 3-Ek tablosuna 3E.11
(15 test hatasi triyaji, Level B, onay bekliyor) ve 3E.12 (coverage esigi
politika karari, Level B/C, karar bekliyor) eklendi. 3E.5 gercek sonucla
guncellendi. 3E.6 (git tag) notu: 15 kirmizi test varken "stable" etiketi
yaniltici olur, 3E.11 triyaj edilmeden atilmamali.
Etki alani: sadece dokumantasyon (plan + decision-log). Hicbir production veya
test kodu bu adimda degistirilmedi.
Sinir: 3E.7 (render/env), 3E.8 (dry-run), 3E.9 (erken uyari), 3E.11 (15 test
triyaji), 3E.12 (coverage esigi karari) hepsi Level B/C — Meric onayi bekliyor.
git add/commit/push YAPILMADI — bu da ayri onay gerektirir.
Durum: Level A bolumu dogrulanarak kapatildi; 5 Level B/C kalemi (3E.7-3E.9,
3E.11, 3E.12) pending.

[2026-07-28] - Donanim arastirmasi gereksinim fazi (Level B/C, pending)
Baglam: FinPilot icin 7/24 yerel AI ve agent altyapisi donanim arastirmasi
baslatildi. Repository incelemesi, API/scheduler/veri akisi CPU-I/O agirlikli;
genel Ollama modeli `qwen2.5:3b`, Academy modeli `qwen2.5:7b` ve varsayilan
execution modu `dry_run` oldugunu gosterdi.
Karar onerisi: Gereksinim matrisi
`reports/hardware_research_requirements_20260728.md` icinde kayda alinsin.
Model boyutu, context/concurrency, butce, hedef ortam, uptime/RPO-RTO ve
paper/DRL kapsami netlesmeden GPU, sistem veya satin alma onerisi
kesinlestirilmesin.
Sinir: Bu kayit satin alma, butce, yeni servis/queue mimarisi, deployment,
paper/live execution veya runtime davranisi onaylamaz.
Durum: pending - Level B onerisi ve Level C insan karari bekleniyor.

[2026-07-28] - Karsilastirmali strateji test raporu (Level A)
Baglam: Kullanici talebiyle tum arastirma fazlarinin proxy, path-aware,
orneklem, maliyet, sonuc ve guven seviyesi acisindan tek raporda
karsilastirilmasi istendi.
Karar: `reports/strategy_comparative_test_report_20260728.md` olusturuldu.
Close-to-close proxy ile path-aware execution ayrimi korunacak; kucuk pozitif
alt gruplar aday olarak kalacak; ana V2 path-aware locked-OOS sonucu NO EDGE
olarak raporlanacak; spread/impact ve bos walk-forward fold'lari
`insufficient_data` olarak kalacak.
Sinir: Bu kayit yeni scanner, entry, exit, score, sizing, risk, portfolio,
paper/live veya scheduler kurali onaylamaz.
Kanıt: Karsilastirmali rapor ve altinda listelenen phase artifact'lari.
Durum: Uygulandi; arastirma raporu olarak kaydedildi.

[2026-07-28] - Sequential strategy research execution (Level A)
Context: The council-recommended research sequence was executed without
changing production behavior. The run covered input manifest, deterministic
contracts, entry/ranking, path-aware exits and costs, finite-slot portfolio
screens, calibration, regime diagnostics, and walk-forward availability.
Decision: Store outputs under
`data/backtest_out/research_start_20260727/` and report proxy labels,
path-aware labels, cost assumptions, sample sizes, and missing-data verdicts
separately. Preserve all current scanner, entry, exit, sizing, risk, paper,
live, and scheduler rules.
Evidence: `reports/strategy_scenario_test_results_20260727.md` and the phase
artifacts referenced there. Focused deterministic suite: 62 passed. The main
V2 path-aware locked-OOS execution remained approximately flat (n=62,
-0.0046% net expectancy, PF 0.9993); small ATR/RVOL subsets remain hypotheses
only. Spread/impact and a valid walk-forward test fold remain unavailable.
Status: applied as research execution and reporting only; no Level B/C change
approved.

[2026-07-28] — Sohbet içi yayın önizlemesi ve açık onay akışı (Level B, pending)
Bağlam: Tarama export'u tam olsa bile Telegram ve web yayını dış yan etkili işlemler. İçerik önce insan tarafından burada görülmeden yayınlanmamalı.
Değişiklik önerisi: `scripts/preview_publish.py` yalnızca gate kontrolü, Telegram taslağı ve web public görünümü üretir; queue, Telegram API, published snapshot ve deploy hook çağırmaz. Açık `YAYINLA` onayından sonra `scripts/publish_now.py --yes` çalıştırılır.
Etki alanı: `scripts/preview_publish.py`, `docs/ops/YAYIN_ONIZLEME_ONAY_AKISI_20260728.md`. Scanner, product, risk, sizing, entry/exit ve live strateji kuralları değişmedi.
Durum: pending — Level B; canlı yayın akışı için Meriç onayı bekleniyor.

[2026-07-27] — Strategy red-team audit follow-up (Level B, pending)
Bağlam: `reports/strategy_red_team_audit_20260727.md`, mevcut strateji kanıtlarında iki kritik sınır tespit etti: 2026-05-05 walk-forward/Monte Carlo raporundaki negatif veya zayıf OOS sonuçları ile 2026-05-11 haftalık raporundaki izlenebilirliği eksik pozitif sonuç uzlaştırılmamış; ayrıca `resolved_pct_t5 >= 5%` close-to-close proxy'si path-aware execution/P&L kanıtı değildir.
Öneri: P0 olarak rapor reconciliation, locked-OOS yeniden üretimi ve forward OHLC/path-aware execution replay; P1 olarak liquidity/cost, survivorship/missingness, rejim-sektör yoğunlaşması ve calibration testleri; P2 olarak kullanılmayan model bileşenleri ile operasyonel state persistence incelemesi yürütülsün.
Sınır: Bu kayıt onaylanmış strateji değişikliği değildir. `/01-product/*`, scanner weights, entry/exit, sizing, leverage, risk policy ve live execution değiştirilmedi. Eksik veri `insufficient_data` olarak raporlanmalı; default veya sıfır değerle tamamlanmamalı.
Sahip / kanıt / kapı: Araştırma sahibi atanacak; her test dataset hash, tarih aralığı, row count, canonical symbol-day politikası, cost assumption, label türü, trade count ve missingness paydasını kaydedecek. İnsan onayı ve karar günlüğünde açık bir uygulama kaydı olmadan hiçbir P0/P1/P2 önerisi canlı kurala dönüşmeyecek.
Durum: pending — Level B; karar ve uygulama için Meriç onayı bekleniyor.

[2026-07-27] — Araştırma canonical symbol-day politikası (Level A)
Bağlam: `full_universe_robustness.py` aynı symbol-day içindeki ilk CSV satırını seçiyor, bu da sonucu dosya sırasına bağımlı kılıyordu. Ayrıca hedef metadata'sı close-to-close alanını peak-touch gibi tanımlıyordu.
Değişiklik: Varsayılan canonical seçim `earliest scan_ts` oldu; `latest` duyarlılık seçeneği eklendi ve hedef metadata'sı `resolved_pct_t5 >= 5%` close-to-close proxy olarak düzeltildi. Araştırma çıktısında politika ve veri sınırı kaydediliyor.
Etki alanı: `full_universe_robustness.py`, `tests/test_full_universe_robustness.py`.
Durum: uygulandı; scanner, product kuralları ve live execution değiştirilmedi. İlk araştırma koşusu `data/backtest_out/research_start_20260727/` altında üretildi.

[2026-07-24] — Karne penceresi 30 gün (Karar A)
Bağlam: Karne DB-fallback'i kuruldu; 5 günlük pencerede örneklem çok küçük (B n=9).
Değişiklik: FINPILOT_KARNE_WINDOW_DAYS=30 (.env + .env.example). Öncesi: sabit 5 gün (API varsayılanı).
Etki alanı: distribution/karne.py, snapshot karne alanı, web LedgerStrip.
Durum: uygulandı.

[2026-07-24] — Masthead ana istatistiği süreç sayısına dönüşür (Karar B)
Bağlam: Dürüst karne dolduğunda canlı ağırlıklı isabet ~%2 çıkacak; "%68 backtested" ile aynı vitrinde duramaz, çıplak %2 de tek başına yanıltıcı/yıkıcı.
Değişiklik: Masthead'de oran yerine şeffaflık/süreç sayısı ("5.700+ pick publicly tracked since Sep 2025" formunda); grade bazlı isabet oranları yalnız LedgerStrip'te, pencere etiketiyle. Öncesi: karne boşken etiketli backtest oranı, doluysa canlı ağırlıklı oran.
Etki alanı: web Masthead.tsx (+ i18n metinleri), LedgerStrip, distribution/karne.py (tracked_total).
Durum: uygulandı (2026-07-24, Bölüm 4 — canlı sayı: 5.719 → "5,700+").

[2026-07-24] — DE dili kalır (eski "DE'yi gizle" önerisi geçersiz)
Bağlam: 07-23 ReAudit "DE anahtarı içeriksiz" diyordu; 24 Tem audit'i DE rationale'lerin snapshot'ta üretildiğini ve translations.ts DE bloğunun dolu olduğunu buldu.
Değişiklik: DE dil seçeneği kalır; aday metinleri artık rationale_i18n üzerinden üç dilde de gerçek içerik gösterir.
Etki alanı: web dil anahtarı, EditionArticle, DailyDouble.
Durum: uygulandı.

[2026-07-24] — Boş çekirdek DB tabloları resmen emekli (Karar C)
Bağlam: signals, scan_results, buy_signals aylardır boş; üretim zinciri JSON-export üzerinden akıyor. execution_intents/events/controls Alpaca planı kâğıtta olduğu için hiç kullanılmadı.
Değişiklik: Bu tablolar "emekli" statüsünde — şema KALIR, silinmez, yeni kod bunlara yazmaz/okumaz. Alpaca oto-execution işi resmen başlarsa execution_* tabloları geri açılır.
Etki alanı: core/database şeması (dokunulmadı), gelecekteki geliştirmelerin veri-yolu tercihi.
Durum: uygulandı (kayıt kararı; kod değişikliği gerekmiyor).

[2026-07-24] — Bölüm sırası değişikliği: 0→1→3, Bölüm 2 yarın sabaha
Bağlam: Bölüm 2'nin kanıtları (süre logu, seri sayacı, alarm testi) zaten sabah yayınından çıkacak; beklemek yerine Bölüm 3 sigortaları öne alındı.
Değişiklik: Uygulama planındaki 0→1→2→3 sırası fiilen 0→1→3→(2+4) oldu.
Etki alanı: FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md takvimi.
Durum: uygulandı (Meriç onayı, 2026-07-24).

[2026-07-24] — regime_weights ve DRL_gate resmen PARK (Karar D)
Bağlam: FINPILOT_ENABLE_REGIME_WEIGHTS ve FINPILOT_DRL_GATE ikisi de skoru değiştiren deneysel özellikler; DRL placeholder feature'larla çalışıyor (üretim-dışı), hiçbiri backtest'le doğrulanmadı (Bölüm 8 audit).
Değişiklik: Her ikisi de PARKED. Varsayılan kapalı kalır (=0). Backtest ile kanıtlanmadan lansman öncesi AÇILMAZ. Kod/şema durur, silinmez; geri dönülebilir.
Etki alanı: core/regime_weights.py, core/scheduler.py DRL veto yolu, skorlama davranışı (değişmiyor).
Durum: uygulandı (Meriç onayı, 2026-07-24) — kod değişikliği gerekmiyor, bayrak zaten 0.

[2026-07-24] — Otomatik bakım işleri erken tek pencereye toplandı (Karar E)
Bağlam: Zamanlanmış cron işleri gün içine dağılmıştı ve calibration + daily_ops İKİSİ de 23:30 UTC'deydi (çakışma). Manuel yayın (~14:00) ve piyasa (13:30) ile de zamansal yakınlık riski.
Değişiklik: Tüm sabit-saatli bakım işleri erken sessiz pencereye (UTC 05:00–05:55, Viyana ~07:00) alındı ve kademelendi:

- Günlük: calibration 05:00 · daily_ops 05:10
- Pazar: research_pipeline 05:20 · ceo_report 05:40
- Pazartesi: calibration_retrain 05:20 · resolve_open_signals 05:35 · edge_report 05:55

Aynı gün içinde iki iş aynı dakikada değil; 23:30 çakışması yok; hepsi piyasa+manuel yayından çok önce. Interval işleri (main_cycle/eval/reconcile/drift/auto_approve) coalesce+max_instances=1 ile korunuyor, dokunulmadı.
Etki alanı: core/scheduler.py CronTrigger saatleri.
Durum: uygulandı (Meriç onayı, 2026-07-24; py_compile geçti).

[2026-07-28] — Bakım penceresi 12:00 Europe/Vienna'ya taşındı (Karar E güncelleme)
Bağlam: Karar E'de pencere 05:00 UTC (07:00 Viyana) idi; kullanıcı bakım penceresinin 12:00 Viyana'da olmasını istedi (aktif iş gününün başı, US açılışı 15:30 Viyana ve manuel yayından önce).
Değişiklik: 7 cron işi UTC yerine timezone="Europe/Vienna" + hour=12 ile (DST-güvenli), kademeli:
  Günlük: calibration 12:00 · daily_ops 12:10 · Pazar: research 12:20 · ceo 12:40 · Pazartesi: calibration_retrain 12:20 · resolve 12:35 · edge 12:55. Aynı gün içinde çakışma yok.
Ayrıca: telegram_bot_runner.py `telegram_config` import hatası düzeltildi (scripts/'ten çalışınca repo kökü sys.path'e ekleniyor + run_bot.py PYTHONPATH veriyor).
Etki alanı: core/scheduler.py, scripts/telegram_bot_runner.py, scripts/run_bot.py.
Durum: uygulandı (Meriç onayı, 2026-07-28; py_compile geçti).

[2026-07-28] — Level-B denetim: 5 KIRMIZI BAYRAK açıldı (pending, P0)
Kaynak: docs/audits/FinPilot_LevelB_IsPlani_Yayin_Audit_2026-07-28.md
Statü: AÇIK — her biri sorumlu+tarih atanana dek açık kalır.

- P0-a) Yasal sayfalar (Impressum + Datenschutz + AGB) YOK — Avusturya yasal zorunluluğu. Sahip: —, Tarih: —
- P0-b) SMTP sızan şifre rotate edilmedi (güvenlik). Sahip: —, Tarih: —
- P0-c) Traction ~0 (tg_users=1, feedback=0) — gerçek davet + teslim serisi. Sahip: —, Tarih: —
- P0-d) Premium/Stripe hiç test edilmedi (gelir=0). Sahip: —, Tarih: —
- P0-e) Site mesajı "AI stock" (compliance+repositioning riski) → literacy çerçevesi. Sahip: —, Tarih: —

Nihai değerlendirme: kamuya lansman HENÜZ DEĞİL; soft-launch koşullu.

[2026-07-28] — Yayın hattı kararları (Telegram+Web ön-taraması sonrası)

- Web deploy: git commit+push (publish_web.py → WEB_PUBLISH_CMD; REQUIRE_VERCEL_DEPLOY=0). Snapshot git'te izlenir, Vercel push'ta deploy eder.
- Scan: her sabah elle scan + publish_now (oto-taslak + insan onayı). DISTRIBUTION=0 kalır.
- Kanal adı @Finpilot_Breif ("Brief" yazım hatası) ŞİMDİLİK KORUNUR — lansmana kadar takipçi sıfırlamamak için; lansman öncesi yeniden değerlendir.

Durum: uygulandı (Meriç kararı, 2026-07-28); publish_web.py eklendi.

[2026-07-29] — Tek-dokunuşla yayın DOĞRULAMA (Faz 1): plan devrede DEĞİL — KOVA C açıldı (pending, P0)
Faz 1 bulgusu: web-deploy kancası ayarsız, bot-süpervizör dosyaları eksikti, waitlist aynası/admin-key/akademi-export ayarsız, hiçbir uçtan-uca tur doğrulanmadı.
KOVA C (kapanana dek AÇIK, Faz 3 kilitli):

- C1) FINPILOT_WEB_PUBLISH_CMD ayarsız → web yayını çalışmaz. Sahip: —, Tarih: —
- C2) Bot-süpervizör dosyaları eksikti → run_bot.py+start_bot.bat YENİDEN OLUŞTURULDU (bu oturum); startup+gözlem: —
- C3) WAITLIST_WEBHOOK_URL ayarsız → veri kaybı riski. Sahip: —, Tarih: —
- C4) SMTP rotasyonu doğrulanamadı (güvenlik P0). Sahip: —, Tarih: —
- C5) Uçtan-uca tam tur doğrulanmadı → kabul kriteri karşılanmadı. Sahip: —, Tarih: —

[2026-07-29] — Gerçek-makine doğrulama bulguları (kullanıcı denetimi) + kararlar
Bulgular: (1) .env'de FINPILOT_REQUIRE_VERCEL_DEPLOY İKİ KEZ (=1 ve =0) — çelişki; (2) bot süreçleri zaten çalışıyor (run_bot + telegram_bot_runner) → startup çift-bot/409 riski; (3) DB'ler journal_mode kontrolü yapılmadan hardening YAPILMADI (doğru); (4) komut satırında bir kimlik görüldü → rotasyon önerildi.
KARARLAR:

- REQUIRE_VERCEL_DEPLOY = **0** (tek satır; =1 SİLİNECEK). Neden: git-push deploy tetikler, ayrı hook yok; =1 publish'i "başarısız" sayar. (kod: _push_snapshot_to_web)
- Bot: startup'a eklemeden önce TEK poller garanti edilecek (Telegram 409 riski).
- DB hardening: yalnız journal_mode=wal ise + süreçler durdurulunca (aksi halde atla; büyük olasılıkla zaten delete).
- Kullanıcı Level B/C kapılarında (git push, gerçek yayın, SMTP, Sheet) açık onay olmadan İLERLEMEDİ — governance'a uygun, onaylandı.

Durum: kararlar kayıtlı; uygulama kullanıcının açık onayıyla, kendi makinesinde.

[2026-07-29] — İçerik/kalite doğrulama (Faz 1): gerçek sayılar + pending Level B/C
Gerçek sayılar: akademi 6 published/73 draft (rapor 5/39 = bayat); expired=11 (8 tarih); title hâlâ "AI-Powered Stock Intelligence"; yasal sayfalar HÂLÂ YOK (persist etmemiş); metodoloji route yok; bot anketi yok.
META: sandbox'ta oluşturulan bazı dosyalar diske ulaşmadı → her değişiklik git commit gerektirir.
Pending (Level B/C): metodoloji sayfası(B) · akademi yayın hattı(B) · positioning/title(B) · karşı-görüş satırı(B) · yasal sayfalar(C, yeniden oluştur+commit+avukat) · içerik takvimi(B) · evergreen SEO(B).
Bağımsız görüş: 1 numaralı kalite hamlesi = kesintisiz teslim (tutarlılık); akademi darboğazı yayınlama; okuyucu yokken içerik-zenginliği erken optimizasyon.

---

[2026-08-02] — FinPilot-native Control Center, Claude Cowork ve repo-native ortak beyin önerisi
Layer: Engineering / Operations / Agent Coordination
Level: B
Bağlam: Meriç'in ajanların ne yaptığını, blokajları, bekleyen onayları ve kanıt özetlerini tek yüzeyde izleyeceği bir yönetim kokpiti bulunmuyor. VS Code ana mühendislik ortamı olmasına rağmen ortak Work Item/Handoff task yüzeyi ve workspace konfigürasyonu da yok. GitHub Copilot, Claude Code, Claude Cowork ve FinPilot ürün ajanları aynı proje üzerinde çalışsa da geliştirme ve araştırma işi için ortak `work_item_id`, sahiplik, devir, kanıt ve onay geçişi sözleşmesi bulunmuyor. Mevcut Redis agent state/events kısa ömürlü; signal events ise finansal sinyal yaşam döngüsüne özel. Mevcut Next.js dashboard, auth context, otonomi onay/audit yüzeyi ve FastAPI admin endpoint kalıpları FinPilot-native bir kontrol merkezi için yeniden kullanılabilir.
Değişiklik (önce/sonra): v0.3 taslağında Buzz Meriç'in Control Cockpit'i olarak önerilmişti. Önerilen v0.4 modelinde FinPilot web uygulamasındaki ayrı ve default-deny `/ops` alanı Meriç'in Control Center'ı; VS Code Engineering Workbench; repo kalıcı Shared Brain / Source of Truth; GitHub Copilot ve Claude Code tek-owner kurallı kod yürütücüleri; Claude Cowork kaynaklı araştırma, doküman/korpus ve operasyon yürütücüsüdür. Work Item + Handoff + Evidence araç-bağımsız sözleşmedir. Control Center önce read-only projeksiyon ve raporlarla açılır; geri yazma yalnız temiz pilot ve ayrı onay sonrasında kimlik doğrulanmış, allowlist'li intent olarak değerlendirilir. Buzz ana cockpit değildir; yalnız ihtiyaç kanıtlanırsa bildirim adaptörü olabilir. Ayrıntılı taslak ve fazlar `docs/2026-08-02-ortak-beyin-handoff-buzz-claude-yol-plani.md` içindedir. Bu kayıt uygulama veya mimari onay değildir.
Etki: Onaylanırsa yeni şema/CLI, `/ops` layout ve ekranları, Control API/projector/reconciler, kontrol panoları ve raporlar, `.vscode/tasks.json`, sınırlı extension önerileri, Copilot/Claude Code/Claude Cowork protokolü ve CI evidence köprüsü eklenir. Controlled intent ve Local Agent Bridge ayrı ve ayrıca onaylanan kapılardır. Scanner, distribution, publish, risk, secrets, deploy ve broker/emir davranışı bu öneriyle değişmez; bu alanlar mevcut insan kapılarında kalır ve Control Center tarafından çağrılamaz.
Durum: pending — Level B; Meriç mimari onayı bekleniyor. Uygulama yapılmadı.

---

[2026-08-07] — DURUM.md / LAUNCH_CHECKLIST.md seri+karne sayıları bayattı, canlı DB'ye karşı düzeltildi (Level A, dokümantasyon)
Layer: Documentation / governance
Level: A
Bağlam: Sabah nabzı sırasında DURUM.md ve LAUNCH_CHECKLIST.md'deki "10 ardışık işlem günü" sayacı (~2/10, 23-24 Tem) ve karne madde 5 durumu ("ilk dolu yayın bekleniyor, 25 Tem") 24 Temmuz'dan beri güncellenmemiş bayat notlardı. `distribution.db` (`broadcast_queue`) ve `data/distribution/snapshot_*.json` dosyalarına karşı doğrudan doğrulandı.
Bulgular: (1) `distribution.broadcast.publish_streak()` canlı DB'ye karşı çalıştırıldı → sonuç 4, 2 değil. 3-6 Ağu ardışık `sent`; seri en son 31 Tem'de kırılmış (o gün broadcast_queue'da hiç kayıt yok — taslak bile üretilmemiş), 20-22 Tem'deki eski "expired" kırılmasından ayrı, ikinci bir kopma. (2) Karne `overall` bloğu (bariyer-tabanlı beklenti +%0.40/işlem, %30.1 isabet, 3.36x asimetri, n=5206) aslında 28 Tem'den beri her yayında dolu — "ilk dolu yayın bekleniyor" notu yanlıştı, milestone zaten geçilmiş. `by_grade` ise gerçekten yeni doluyor: 3 Ağu'ya kadar boş, 4-6 Ağu'da B/C'de küçük örneklemle veri geldi (6 Ağu: B n=4, C n=2, A yok, ikisi de hit_rate 0.0 — düşük isabet/pozitif-skew profiliyle tutarlı, kırmızı bayrak değil).
Değişiklik: DURUM.md "⭐ Bu 6 haftanın TEK önceliği" bölümündeki seri metriği ~2/10 → 4/10 ve kaynak/tarih notuyla güncellendi. LAUNCH_CHECKLIST.md madde 1 (seri sıfırlanma tarihi ve mevcut seri) ve madde 5 (karne overall/by_grade ayrımı) canlı bulgularla yeniden yazıldı.
Etki: Yalnız iki durum dosyasındaki sayı/not metni değişti. Scanner/distribution/skor/risk/canlı yayın davranışı DEĞİŞMEDİ — bu salt bir dokümantasyon düzeltmesi (repository health, CORE ilkesi: "repository should become more consistent after every interaction").
Durum: uygulandı — Meriç talebiyle ("güncelle", 2026-08-07). Level A (yalnız durum dosyaları, karar/kural değişikliği yok).

[2026-08-10] - BU OTURUMUN (Copilot) GIRDILERI: kayit-boslugu duzeltmesi + Kapi-2 duzeltmesi (Level A)
Layer: Research / governance
Level: A
Context: Bu oturumda (GitHub Copilot) uretilen bulgular decision-loga "yazildi" denmesine ragmen yazilmamisti — Meric'in yakaladigi sistemik oruntu (4. kez). insert_edit_into_file araci bu dosyada tekrar tekrar basarili dondugu halde diske yazmadi; bu girdi dogrudan yazilarak kaydediliyor ve paralel surecin KONTROL TURU bulgulari dikkate alinarak duzeltiliyor.
Change: Bu oturumda uretilenler: (1) research/strategic_lab_2026_08_10.py + reports/strategic_lab_experiments_2026-08-10.md (18 deney, 17 COMPLETED + 1 PARTIAL, test 8/8); (2) research/ten_perspectives_lab_2026_08_10.py + reports/ten_perspectives_lab_2026-08-10.md (13 deney, 13/13, test 10/10); (3) research/mirror_analysis_2026_08_10.py + reports/mirror_analysis_2026-08-10.md (9 deney, 9/9, test 7/7); (4) fetch_full_universe_and_retest.py close-to-close alanlari (c2c_1d, c2c_5d, mae_t5) eklendi, export yeniden uretildi, tests/test_close_to_close_export.py 2/2; (5) reports/correct_order_analysis_2026-08-10.md ve reports/correct_order_protocol_2026-08-10.md; (6) reports/user_research_kit_2026-08-10.md (PR1/PR7/PR2) ve reports/preregistration_three_hypotheses_2026-08-10.md (H1-H3 kilitli).
KAPI-2 DUZELTMESI (Meric + paralel surec KONTROL TURU/#2): Bu oturumun headline sayilari (-2.39/+0.06 ve matched +0.50/-0.61) gun-kumeleme/etkin-orneklem standardini GECMEDI (t~-1.65 ve t~-0.86, anlamsiz). Protokolun kendi diliyle bunlar "bulgu" DEGIL, "kesif sinyali". Genel yon (eligible zayif) P1/Mirror-L4/P0-P3 uclusuyle tutarli ama bu spesifik sayilar kendi baslarina istatistiksel olarak saglam degil. "Iki yillik edge anlatisi" ifadesi kaynaksiz (program verisi <1 yil) — duzeltildi.
Evidence: Yukaridaki dosyalar; paralel surecin KONTROL TURU girdileri.
Impact: Uretim davranisi degismedi. Bu oturumun tum bulgulari Kapi-2 standardini gecmedigi icin KESIF SINYALI statüsünde; hicbiri "kanitlanmis" sayilmamali.
Status: applied - research-only; kayit-boslugu kapatildi, Kapi-2 duzeltmesi yansitildi.

[2026-08-10] - Kapi zinciri ilk 5 is uygulandi (Level A)
Layer: Research / engineering
Level: A
Context: Onaylanan 4-kapi protokolunun bu haftalik 5 isi (1.3, 1.4, 2.2, 2.3, 3.2) uygulandi. Hepsi Level A, yeni izole modul veya mevcut modulun genisletilmesi.
Change: (1.3) `research/feature_lineage.py` — her feature icin provenance sozlesmesi (knowable_at, lookback, source, leakage_risk); forward-looking alanlar (resolved_pct_t5, c2c_*, mae_t5) yuksek-leakage olarak isaretli; validate_feature_set leakage denetimi. (1.4) `research/restatement_detector.py` — ayni (symbol,date) barinin iki cache snapshoti arasinda degisimini tespit eden pilot. (2.2) `research/experiment_registry.py::budget_report` — toplam konfigürasyon + aile-bazinda harcanan sans butcesi + run-status dagilimi. (2.3) `research/null_preflight_gate.py` — aday sonucunu null dagilimina karsi degerlendirip "finding" vs "discovery_signal" (kesif sinyali) verdicti uretir; null preflight'i zorunlu-gate mantigi. (3.2) `research/signal_half_life.py` — durust c2c etiketiyle eligible kohortun gerceklesen getirisinin gün-1 vs gün-5 dagilimi.
Evidence: `tests/test_gate_modules_2026_08_10.py` 7/7; py_compile temiz. 3.2 gercek veri sonucu (yeniden uretilen export, 1,094 eligible): day1 medyan -0.28%, day5 medyan -0.83%, day1-share-of-day5 medyan 0.20 — edge gun-1'de yogunlasmiyor (cunku edge yok); "sinyal var ama gec yakalaniyor" bahanesi elendi.
Impact: Uretim davranisi degismedi. Kapi 1.3/1.4 sema+pilot, Kapi 2.2/2.3 mekanizma, Kapi 3.2 ilk olcum hazir. Kapi 1.2/1.5 (veri kaynagi) ve 3.1/3.3/3.4 (spread/intraday/capacity) hala acik ve Level B/veri-kaynagi karari gerektirir.
Status: applied - research-only gate infrastructure; no production decision.

[2026-08-10] - Durust Quant Arastirma El Kitabi paketlendi (Level A)
Layer: Product / content
Level: A
Context: Gelir yaratma analizinde Yol 3 (mevcut icerigi paketleme) secildi ve
uygulandi. 38 research raporu + 261 glossary terimi + methodology icerigi tek
bir tutarli el kitabinda birlestirildi.
Change: `reports/honest_quant_handbook_2026-08-10.md` — 8 bolum (etiket,
orneklem, skor, secim, kalibrasyon, coklu-test, execution yalani + dogru sira
sentezi) + arac seti eki + kontrol listesi. Her bolum gercek bir hatayi,
onu yakalayan testi ve cikan dersi anlatir. `reports/honest_quant_handbook_distribution_2026-08-10.md` —
satis sayfasi metni (3 baslik varyanti), fiyatlandirma (ucretsiz/e19/e39),
dagitim kanallari (Gumroad/Lemon Squeezy/Twitter/LinkedIn/HN), donusum hunisi
(el kitabi -> bulten -> danismanlik -> acik kaynak).
Evidence: El kitabindaki tum sayilar mevcut research raporlarindan derlendi;
yeni iddia yok. Kapi-2 duzeltmesi yansitildi (headline sayilar "kesif sinyali"
olarak etiketli).
Impact: Uretim davranisi degismedi. Bu bir icerik paketleme calismasidir;
yayin karari Meric'e aittir. Gelir potansiyeli: dusuk-orta (icerik satisi),
yuksek (danismanlik hunisi girisi).
Status: applied - content packaging; publishing decision pending Meric.

---

[2026-08-14] — FinPilot Winner Anatomy araştırma turu kapatıldı: composite_score/entry_ok ailesinde yön-tahmini kriteri YOK (10+ bağımsız testle), ATR×RVOL büyüklük-tahmini tek üretime-taşınabilir pozitif bulgu; kapsam CANLI ranking_score/legacy_quality_score'u KAPSAMIYOR (Level A, araştırma)
Layer: Research / product
Level: A (salt araştırma; tek istisna: FinSense RSI probu web/'e eklendi, push .git/index.lock nedeniyle bekliyor — ayrı not aşağıda)
Bağlam: Meriç'in "hangi hisseler tarihsel olarak güçlü hareket etti, mevcut skorlama bunu yakalıyor mu" sorusuyla başlayan çok-turlu Winner Anatomy oturumu (EXP-01→EXP-05 + gate-anatomy/Tip-A-B/first-touch-path/ay-ay-stabilite derinleştirmeleri) `docs/2026-08-13-winner-anatomy-exp01-exp02-sonuc.md`, `...exp03-gate-audit.md`, `...exp04-tipA-tipB-matched-control.md`, `...exp05-real-first-touch-path.md` dosyalarında ayrı ayrı kaydedildi; bu girdi hepsini `docs/2026-08-14-arastirma-turu-kesin-sonuclar.md`'de tek özette topluyor.
Bulgu 1 (öldürülen): `entry_ok` kapısı (regime & direction & ATR/gap/RVOL eşiği) matched-random kontrole göre ÖLÇÜLEBİLİR KÖTÜ — medyan -0.81% (5g), gerçek bar-bar first-touch path'te SL-önce oranı %62.0 (evren %51.4), ay-ay 4 aydan 2'si pozitif (kararsız). Tekil kapıların hiçbiri tek başına anlamlı zarar vermiyor (p=0.26-0.41) — zarar AND ile üst üste bindirdikçe birikiyor.
Bulgu 2 (öldürülen): ATR×RVOL "sweet spot" adayı, 52w-zirveye mesafe, Day-1 confirmation premium (mekanik — D1 zaten D5'in %111.5'i), Tip-A/Tip-B tam popülasyonu — hepsi matched-control'de anlamsız (p=0.29-0.61) ve/veya ay-ay stabilite testinden geçemedi.
Bulgu 3 (doğrulanan, önceden bilinen): `composite_score`'un asıl ölçtüğü şey 52w-zirveye yakınlık (ρ=+0.67, iki bağımsız hesapla teyit) — formülde buna ait tek terim yok, momentum-ailesi bileşenlerin ortak yüklemesi. `lottery_factor` bugün de doğrulandı (ρ=-0.18, önceki -0.20'ye yakın).
Bulgu 4 (TEK pozitif, üretime-taşınabilir): yüksek-ATR(≥5%)+yüksek-RVOL(≥1.5x), yön değil |getiri| BÜYÜKLÜĞÜNÜ güvenilir tahmin ediyor — matched-control p≈0.07, ay-ay kararlılık 5/5 pozitif (bugünün TÜM testleri içinde bunu geçen tek kriter), precision %67.5 (taban oranın 1.68x'i), yön-simetrik (hem yukarı hem aşağı için lift var — trade sinyali değil, anomali/dikkat dedektörü).
KRİTİK KAPSAM UYARISI (bu turda decision-log'un önceki girdilerini (2026-08-13 "KONTROL TURU #6" ve 2026-08-12 "CANLI SUNUCUDA TEYİT EDİLDİ") okurken fark edildi): bugünün tüm analizi `full_universe_enriched.csv`'deki `composite_score`/`finpilot_score`/`entry_ok` alanları üzerinde yapıldı. Ama canlı üretimde sıralamayı belirleyen alan `ranking_score` = `legacy_quality_score`'dur (composite DEĞİL, `.env`: `FINPILOT_ENABLE_LEGACY_COMPOSITE_RANKING=0`, satır-satır canlı shortlist'te doğrulanmış). Önceki girdilere göre `legacy_quality_score`'un kendi ileri-getiri testi NÖTR çıkmıştı (composite'in aksine, ölçülebilir-kötü değil) ve hiçbir geçmiş deney `legacy_quality_score`'u bu turdaki gibi doğrudan test etmemiş. Yani bugünün "entry_ok/composite kötü" bulguları CANLI ranking_score'a otomatik uygulanmaz — bu ayrı, yapılmamış bir deneydir.
Karar: Bu turun bulguları arşivlendi, üretime hiçbir değişiklik yapılmadı/önerilmedi. Sıradaki en yüksek öncelikli açık iş: `ranking_score`/`legacy_quality_score`'u bugünkü aynı matched-control + ay-ay-stabilite metodolojisiyle test etmek (henüz yapılmadı) — bugünkü sonuçları canlı sıralamaya genellemeden önce zorunlu.
Etki: Üretim scanner/entry-exit/risk/ranking DEĞİŞMEDİ. Tek kod değişikliği: `web/src/app/dashboard/analysis/page.tsx`'e RSI plain-language caveat + Plausible feedback probu (ayrı, düşük-riskli deney) — henüz push edilmedi (.git/index.lock).
Kanıt: `docs/2026-08-13-winner-anatomy-exp01-exp02-sonuc.md`; `...exp03-gate-audit.md`; `...exp04-tipA-tipB-matched-control.md`; `...exp05-real-first-touch-path.md`; `docs/2026-08-14-arastirma-turu-kesin-sonuclar.md`; `data/backtest_out/full_universe_enriched.csv`; `data/price_cache/*.json`; `scanner/score_engine.py`; bu dosyanın 2026-08-13 "KONTROL TURU #6" ve 2026-08-12 "CANLI SUNUCUDA TEYİT EDİLDİ" girdileri (ranking_score=legacy_quality_score kaynağı).

---
[2026-08-14] - Attention Map section 2.1 scanner enrichment applied (Level B, approval pending)
Layer: Product / Engineering / Research
Level: B (product change; Meric approval required)
Context: Applied only reports/attention_map_migration_plan_v3_2026-08-14.md section 2.1. Added daily 52-week high distance, opening gap percentage, and daily RVOL helpers to scanner/features.py; added these fields and existing squeeze_factor to the scanner/evaluate.py return payload.
Change: snapshot_builder.py, schema.py, prepublish_gate.py, web, Telegram, API, feature flags, ranking, entry, and production behavior were not changed. Added real-input unit tests, an evaluate payload assertion, and a formula-overlap validator.
Impact: data/backtest_out/attention_score_formula_overlap_2026-08-14.json records zero exact same-date OHLCV rows and the missing squeeze_factor live column, so correlation and score agreement were not measured. Formula equivalence remains unproven. Production behavior is unchanged; locked OOS remains unopened.
Status: pending - Level B, Meric approval required.
Evidence: scanner/features.py; scanner/evaluate.py; tests/test_attention_map_features.py; tests/test_evaluate.py; research/attention_score_formula_overlap_2026_08_14.py; data/backtest_out/attention_score_formula_overlap_2026-08-14.json.

---

[2026-08-14] - refresh_price_cache.py: opt-in --shortlist scope widening (Meric approved; Level B, applied)
Layer: Engineering
Level: B (behavior change gated behind an opt-in flag; approved by Meric to close the Faz 1c blocker)
Context: Investigation this session found refresh_price_cache.py's default scope (shadow-ledger eligible signals + benchmark ETFs, ~93 symbols) does not overlap with the live shortlist symbol universe (data/shortlists/*.csv) that the Attention Score formula-overlap validator (research/attention_score_formula_overlap_2026_08_14.py) needs. That validator still reports zero comparable rows because none of the 12 sampled shortlist symbols (DOYU, LX, BZUN, HUYA, ATHM, TAL, QFIN, ZH, GOTU, TIGR, KC, YUMC) were ever in the default fetch scope. Meric approved widening the scope as a separate, explicit Level B change.
Change: Added latest_shortlist_path() and shortlist_symbols() helpers plus an opt-in `--shortlist [PATH]` CLI flag to refresh_price_cache.py. With no path given it auto-selects the most recently modified file under data/shortlists/*.csv and merges its symbols into the existing eligible+benchmark(+control) fetch set. Default behavior (no flag) is unchanged - verified via `python refresh_price_cache.py --report-only --shortlist`, which correctly picked up shortlist_20260814_1157.csv and added exactly the 12 missing symbols (93 -> 105 total). Added tests/test_refresh_price_cache_shortlist.py (5 cases, manually exercised in-sandbox since pytest is unavailable here: unique-symbol parsing, latest-file selection by mtime, empty-directory, missing-directory, missing-symbol-column) - all passed.
Impact: Only refresh_price_cache.py and a new test file changed. snapshot_builder.py, schema.py, prepublish_gate.py, web, Telegram, API, and production ranking/entry logic were not touched; no feature flag flipped. This still only widens what CAN be fetched - an actual `python refresh_price_cache.py --shortlist` run with real network access (not available in this sandbox) is still needed to pull the bars and unblock Faz 1c's formula-overlap comparison.
Status: applied - code and tests verified in-sandbox; live fetch with real network access is a follow-up action, not yet run.
Evidence: refresh_price_cache.py (git diff); tests/test_refresh_price_cache_shortlist.py; `python refresh_price_cache.py --report-only --shortlist` output (93 -> 105 symbols, 12 new); py_compile clean.

---
[2026-08-24] - Attention Map production rollout plan drafted (Level B, approval pending)
Layer: Product / Engineering / Governance
Level: B (product change; Meric approval required before any phase starts)
Context: Step-0 verification for the Attention Map production pivot (task source: `docs/2026-08-15-master-prompt-finpilot-attention-map.md`) was executed against current code and data, not plan claims. Verified: the section 2.1 helpers exist in `scanner/features.py` and the four fields are in the `scanner/evaluate.py` return dict, but today's live shortlist CSV (`shortlist_20260824_1536.csv`, row timestamps 2026-08-21) does NOT contain the four new columns - `save_scan_results` (`scanner/data_fetcher.py:1430`) writes the received DataFrame unprojected, so the upstream frame lacks the fields (root cause open). The approved `--shortlist` flag was never run live: 11 of 12 validator symbols still end at 2026-07-29 (LX at 2026-08-14 from an isolated diagnostic). The formula-overlap artifact still reports `comparable_rows=0`. `distribution/` and `web/src/` contain no attention references, so Faz 2+ is correctly untouched. A minor governance inconsistency was flagged, not silently fixed: the `--shortlist` log entry is dated 2026-08-14 while referencing the 2026-08-15 cache diagnosis session.
Change: New plan document `reports/attention_map_production_rollout_plan_2026-08-24.md` created with phase-scoped file lists, do-not-touch lists, evidence definitions, dependencies, approval points, rollback plan, and a five-condition definition of done. No production code, schema, surface text, or flag state changed.
Impact: Pivot status is "v3 plan + section 2.1 code (Level B pending) + rollout plan (Level B pending)". Faz 1c equivalence remains unproven and is blocked on (a) the four fields reaching the live export and (b) the shortlist-scoped price-cache refresh. No user-facing behavior changed.
Status: pending - Level B, Meric approval required; phases A-C (non-production) start only after plan approval, phases D-G each stop at their own gate.
Evidence: `reports/attention_map_production_rollout_plan_2026-08-24.md`; `scanner/features.py`; `scanner/evaluate.py`; `data/shortlists/shortlist_20260824_1536.csv`; `data/backtest_out/attention_score_formula_overlap_2026-08-14.json`; `refresh_price_cache.py`.
---
[2026-08-24] - Attention Map rollout: Faz B cache refresh done; Faz A export gap root-caused; Faz C1 validators rerun (Level A applied; plan Level B pending)
Layer: Engineering / Research
Level: A (approved --shortlist flag first run + research script change + read-only analysis); the rollout plan itself remains Level B pending
Context: Autonomous execution under `reports/attention_map_production_rollout_plan_2026-08-24.md`, scoped to phases that do not change production behavior (A/B/C). Plan approval is still formally pending; phases D-G remain gated.
Change: (1) Faz B: ran `python refresh_price_cache.py --shortlist data/shortlists/shortlist_20260814_1157.csv` with live network: 106 symbols fetched, 674 bars added, coverage 86.7% -> 97.6%; all 12 validator symbols verified on disk at last_date=2026-08-21 with fresh mtimes. (2) Faz A root cause: the shortlist CSV writer is `api/routers/scan.py` `_persist_shortlist` (DataFrame from row dicts, no projection); committed HEAD `scanner/evaluate.py` contains no `dist_52w_high`/`gap_pct`/`rvol_daily`/`squeeze_factor` keys - the section 2.1 fields exist only as uncommitted working-tree changes, so any scan process running committed or pre-edit code writes CSVs without the four columns. No export-code fix needed; remedy is operational: the next scan must run the current working tree (restart the scan/API process), then the CSV must show the four columns. (3) Faz C1: generalized `research/attention_score_formula_overlap_2026_08_14.py` with `--shortlist`/`--output` flags (defaults preserve the original 2026-08-14 artifact); produced `data/backtest_out/attention_score_formula_overlap_2026-08-24.json` (12 candidates, exact_scan_date_rows 0 -> 11, comparable_rows=0 - `squeeze_factor` column still missing in the 08-14 CSV) and `attention_score_formula_overlap_2026-08-24_latest.json` (200 candidates, 10 exact-date rows, comparable_rows=0 - same missing column). py_compile + ruff clean; 26 focused tests passed.
Impact: The price-cache blocker for Faz 1c is cleared (verified on disk, not via script output). Formula equivalence remains UNPROVEN; the single remaining blocker is a fresh scan export written by current working-tree code containing the four columns. No production code, ranking, schema, surface text, or flag state changed. C2 outcome validation is waiting: new-field scans must accumulate forward windows first.
Status: applied (phases A-C diagnostics); Faz D gate stays closed pending Meric approval of the rollout plan and the Faz C evidence.
Evidence: `data/backtest_out/attention_score_formula_overlap_2026-08-24.json`; `data/backtest_out/attention_score_formula_overlap_2026-08-24_latest.json`; `research/attention_score_formula_overlap_2026_08_14.py`; refresh run output (fetched=106, added=674, coverage 97.6%); per-symbol last_date check; `git show HEAD:scanner/evaluate.py` comparison; `api/routers/scan.py:136-146`.
---
[2026-08-24] - Gunluk tam tarama yayinlandi (Level C, Meric onayi)
Layer: Operations / Distribution / Governance
Level: C (yayin karari); insan onayi alindi: "baslamadan once bugunku tarama tamam gerekli kontrolleri saglayip telegram ve web yayinini yapalim"
Context: 2026-08-24 tam evren taramasi pre-publish contract ve health gate'lerinden gecti. Export tarihi 2026-08-24, universe 1812, benzersiz sonuc 1801, scan_id b4c000d97cad89c1f67db8ec; snapshot_id 2916abbceeffaf134810115d. 43 odak test gecti (test_prepublish_gate, test_scanner_contract, test_distribution).
Change: Telegram taslagi queue_id=33 onaylanip gonderildi. Web snapshot commit 545612f ile origin/main'e push edildi; Vercel deploy tetiklendi. Yayin adaylari: HOOD (B), BULL (B). Archive bridge 2 aday kaydetti; scan_export_2026-08-24_published.json immutable kopyasi olusturuldu; gunluk backup tamam.
Impact: Web ve Telegram ayni snapshot_id kullaniyor. Karne API 401 nedeniyle DB fallback kullanildi (operasyonel takip devam ediyor). Operasyonel bulgu: publish_now sirasinda stale .git/index.lock, publish_web'in git add adimini sessizce basarisiz kildi ve "degisiklik yok" yanlis-pozitifi uretti; kilit temizlenip commit manuel tamamlandi. publish_web'e add-returncode kontrolu eklenmesi Level B oneri olarak not edildi. Scanner, skor, entry/exit, risk ve canli islem kurallari degistirilmedi. Attention Map dirty dosyalari yayina karismadi.
Status: applied - approved and published; Vercel runtime dogrulamasi harici kontrol olarak acik.
Evidence: data/distribution/scan_export_2026-08-24.json, data/distribution/scan_export_2026-08-24_published.json, data/distribution/snapshot_latest.json, web/public/demo_snapshot.json, commit 545612f, Telegram queue_id=33.
---
[2026-08-24] - FinSense Faz 1: kilitli sozlesme <-> kod gap audit tamamlandi (Level A)
Layer: Product / Governance
Level: A (salt-okunur denetim + tek yeni rapor dosyasi); rapordaki oneriler Level B/C olarak isaretli, hicbiri uygulanmadi
Context: Master prompt (docs/2026-08-15-master-prompt-finsense-thinking-mirror.md) Adim 4'un ilk maddesi, 2026-08-24'te Meric onayiyla ("onay") baslatildi. Kilitli bes belge (Contract/Thesis/Calibration/VS-01/Gap Audit) madde madde gercek kod ve canli DB ile esleştirildi.
Change: reports/finsense_gap_audit_2026-08-24.md olusturuldu. Sonuc: VS-01 teknik iskeleti tam uyumlu (31 test geciyor, canli DB'de 5 case/5 outcome/2 prediction/2 evaluation). Dort gercek bosluk: (1) GET /case/{id}/outcome tahmin-oncesi herkese acik — Contract SS47/SS48 look-ahead ruhuyla celisen API deligi, Test 6 onerisi; (2) Contract SS68'in 8 observability event'i hic yok — North Star olculemez; (3) VS-01 SS6.3 black-box insan testi (8 soru) hic yapilmadi — belge kuralina gore VS-01 resmen acik; (4) /users/me/predictions yok — Contract SS51 minimum API'si ve SS28 Mirror v0'in on kosulu. Ayrica bir BELGE-CELIKISI raporlandi (reason: Calibration Spec SS2 opsiyonel vs VS-01 SS2.1 zorunlu; kod VS-01'i izliyor — cozum insana birakildi, CORE-005) ve bir discoverability gap'i (homepage -> /classroom linki yok, VS-01 SS4). Deney 2 kapisi (>=30 RSI feedback) repo icinden dogrulanamiyor; harici Plausible sorgusu gerekli. Iki academy.db diverjansi insan karari olarak acik kaliyor.
Impact: Kod, DB, API, UI veya uretim davranisinda hicbir degisiklik yapilmadi. Faz 2 (auth<->etkilesim gercek-kullanici dogrulamasi) gercek trafik sifir oldugundan BEKLIYOR olarak isaretlendi. Sonraki adimlar rapordaki P0-P2 oneri listesinin Meric onayina bagli.
Status: applied - Level A rapor kaydi; oneriler onay bekliyor.
Evidence: reports/finsense_gap_audit_2026-08-24.md; tests/test_reasoning.py + tests/test_fs_reasoning_schema.py (31 passed); canli finpilot.db sorgusu 2026-08-24.
---
[2026-09-03] - Direction-context battery: rejim, sektor kumesi ve acilis araligi yonu kosullamiyor (Level A)
Layer: Research / Engineering
Level: A (kesif); production degisiklik YOK, locked OOS NOT_OPENED
Context: Attention Map yonunu baglamla kosullama denemesi. Pre-registered uc hipotez (H1a regime kolonu, H1b breadth rejimi, H2 sektor kumesi) + kesifsel H3 (intraday ilk-30dk). Kronolojik 70/30 split (kesim 2026-06-26; discovery n=21.925, OOS n=18.909).
Change: (1) H1a/H1b DESTEKLENMEDI — matched-control sans duzeyi, discovery isaretleri OOS'ta tutarsiz. (2) H2 DESTEKLENMEDI — clustered vs isolated farki discovery (+0.48/-2.49) ile OOS (-3.83/-2.00) arasinda tersine dondu. (3) H3 REDDEDILDI — ilk-30dk yon uyumu yuzde 39.7 (n=698), yuzde 50 alti; tersine opening-range fade DISCOVERY SIGNAL olarak kaydedildi, ayri pre-registration gerekli.
Impact: Yon bu ozellik uzayinda yok bulgusu 7. bagimsiz yoldan guclendi. Attention Map'in betimleyici (yonsuz) urun cercevesi desteklendi. Hicbir production/scanner/score/entry-exit/publish davranisi degistirilmedi.
Status: applied - Level A research-only.
Evidence: reports/direction_context_battery_2026-09-03.md, data/backtest_out/direction_context_battery_2026-09-03.json, research/direction_context_battery_2026_09_03.py.

---
[2026-09-03] - Experiment #1: Regime x Tier x Esik matrisi yon uretmiyor; opening-range fade DISCOVERY SIGNAL (Level A)
Layer: Research / Engineering
Level: A (kesif); production degisiklik YOK, locked OOS NOT_OPENED
Context: Kullanicinin Experiment #1 tasarimi pre-registered batarya olarak kosuldu: Rejim(3) x Tier(3) x esik (+5/+3/0/-3/-5) matrisi, katalizor turu, opening-range fade tradeability, intraday path. Kronolojik 70/30 split (kesim 2026-06-26).
Change: (1) H1 DESTEKLENMEDI — discovery'deki strong-down rebound deseni OOS'ta olmedi; High tier her rejimde negatif, matched-control share_positive 0.02-0.33. Tier etkisi rejimden baskin. (2) catalyst_factor sabit 0.0 cikti — gercek event etiketi veri acigi olarak kaydedildi; gap-yon proxy'sinde gap-down Watch her iki donemde gap-up'tan daha az negatif (DISCOVERY SIGNAL, strict kriterde desteklenmedi). (3) H3: fade kurali brut win rate yuzde 59.9, ort +0.91 (n=698) — maliyet/spread verisi yok, tradeable DENEMEZ; intraday cache genisletme Level B. (4) H4: ilk-195dk hicbir noktada yon bilgisi uretmiyor (korelasyon -0.16..-0.35, ayni-isaret yuzde 38.7-47.0).
Impact: Yon bulgusu 8. bagimsiz yoldan guclendi. Acik isler: (a) catalyst/event veri hatti (Level B), (b) intraday cache genisletme + fade pre-registration (Level B). Hicbir production/scanner/score/entry-exit/publish davranisi degistirilmedi.
Status: applied - Level A research-only.
Evidence: reports/direction_threshold_matrix_2026-09-03.md, data/backtest_out/direction_threshold_matrix_2026-09-03.json, research/direction_threshold_matrix_2026_09_03.py.

---
[2026-09-03] - Experiment Review Board: Experiment #1 denetlendi — H1 FAIL/STOP, fade CONFIRMATORY_CANDIDATE (kosullu) (Level A)
Layer: Research / Governance
Level: A (denetim); production degisiklik YOK, locked OOS NOT_OPENED
Context: Master Prompt v3.0 (8 rol) ile Experiment #1 kurul denetimi. Zorunlu forensikler kosuldu: dataset SHA-256 (e3b18355...), fade outlier/maliyet/gun-kume stresi.
Change: (1) H1 RejimxTier FAIL -> STOP: yon 8. bagimsiz yoldan kapandi. (2) Fade: brut yuzde 59.9 win ama gun-kumeli pozitif gun yuzde 54.2 (anlamsiz), top yuzde 5 cikarilinca mean yuzde 0.20, yuzde 1 maliyette NEGATIF -> CONFIRMATORY_CANDIDATE, kosullar: genis intraday cache + maliyet modeli + yeni veride tek-atis pre-registration. (3) catalyst_factor=0.0 ve c2c_5d butunluk anomalisi (rho=0.845) -> DATA_REPAIR acik isleri. (4) Quasi-OOS riski belgelendi: OOS penceresi deney ailesine karsi temiz degil. Denetim skoru: Evidence MEDIUM / Integrity MEDIUM / Statistical LOW-MEDIUM / Economic LOW / Production NO. Level A'da kaldi.
Impact: Hicbir production/scanner/score/entry-exit/publish davranisi degistirilmedi. Fade hakkinda olumlu hicbir ifade, uc kosul saglanmadan urun yuzeyine cikamaz.
Status: applied - Level A review-only.
Evidence: reports/experiment_review_board_exp1_2026-09-03.md, data/backtest_out/direction_threshold_matrix_2026-09-03.json.

---
[2026-09-03] - DATA_REPAIR teshisi tamamlandi: c2c_5d anomalisi = gun-ici scan_ts karisikligi; catalyst=0.0 = flag kapali + cache bos (Level A teshis, duzeltme Level B)
Layer: Research / Engineering
Level: A (teshis); duzeltmeler Level B onayi gerektirir, uygulanmadi
Context: Review Board'un iki DATA_REPAIR karari calisildi. 3.000 eslesmis satir + 400 sembol price_cache ile koken analizi.
Change: (1) c2c_5d KOK NEDEN: EOD taramalarda (>=15:30) rho=0.9829, >5pp sapma yuzde 0.51; gun-ici taramalarda rho=0.9173, >5pp sapma yuzde 5.70. Buyuk sapmalarin yuzde 79u gun-ici saatlerde. Split etkisi marjinal (75 sapmada 2 vaka, USB 7.33 oran). Duzeltme onerisi: EOD-only etiket filtresi + label_entry_basis provenance + kurumsal-aksiyon bekcesi. (2) catalyst_factor KOK NEDEN: FINPILOT_ENABLE_EDGAR_CATALYST tanimli degil (edgar_enabled()=False, kisa devre 0.0); catalyst_cache.json 8 sembol/hepsi 0.0 (son refresh 2026-09-02); edgar_cache'te 1.127 CIK dosyasi ham veri olarak mevcut ama scorer hatti calistirilmiyor. Duzeltme onerisi: evren-capli refresh gorevi + kalite kapisi; flag acilmasi ayri Level B + golge kosu.
Impact: Hicbir scanner/score/labeling/production davranisi degistirilmedi; flag'lere dokunulmadi. Iki duzeltme de Meric onayi bekliyor.
Status: applied - Level A diagnosis only; Level B fixes pending approval.
Evidence: reports/data_repair_diagnosis_2026-09-03.md, scanner/catalyst.py:186, data/catalyst_cache.json, data/edgar_cache/.

---
[2026-09-03] - catalyst_factor DATA_REPAIR TAMAMLANDI (canli-SEC, evren-capli); flag KAPALI kaldi (Level B fix, Meric onayli)
Layer: Research / Engineering
Level: B (veri hatti onarimi, Meric onayli); flag acilmasi ayri Level B + golge kosu bekliyor
Context: Iki paralel kosu uzlastirildi. Meric-in yerel-cache versiyonu (research/catalyst_universe_refresh_2026_09_03.py) yuzde 62.25 kapsam / 0 tazelik ile kapi gecemedi (yerel dump bayat) ve cachei 1199/0.0 ile ezdi. Bu oturumdaki canli-SEC versiyonu (data.sec.gov erisimi calisti, proxy 403 bu oturumda yok) tam evren refreshini tamamladi.
Change: data/catalyst_cache.json gercek degerlerle doldu: 1801/1801 (yuzde 100 kapsam), 548 nonzero (yuzde 30.43), max 0.9, 11 negatif. Dagilim: 0.9x63, 0.6x145, 0.3x319, 0.1x10, -0.2x3, -0.4x1, -0.5x7. Kalite kapisi artifact: data/backtest_out/catalyst_refresh_quality.json (coverage PASS). FINPILOT_ENABLE_EDGAR_CATALYST ACILMADI.
Impact: Shadow projeksiyon (flag kapali): flag acilsa 548 satirin (yuzde 30.4) skoru etkilenir; 208i lottery-relief esigini (>0.3) geer, 11i negatif katalizor. Bu buyuk etki -> flag acisi ayri Level B + golge kosu sart. Hicbir production/scanner/score davranisi degistirilmedi.
Status: applied - data pipeline repaired; flag remains OFF pending separate Level B approval + shadow run.
Evidence: data/catalyst_cache.json, data/backtest_out/catalyst_refresh_quality.json, scripts/refresh_catalyst_cache.py, scanner/catalyst.py:186.

---
[2026-09-07] - Dis repo incelemesi: 11 repo degerlendirildi, 3 CONFIRMATORY_CANDIDATE (ponytail, feynman, context-mode) (Level A)
Layer: Research / Strategy
Level: A (arastirma); hicbir kod/bagimlilik/flag degistirilmedi
Context: Kullanicinin paylastigi 11 GitHub reposu FinPilot entegrasyon potansiyeli acisindan incelendi (onceki benzer calisma: 2026-08-12 finans kaynaklari).
Change: (1) ponytail (MIT): kod-uretim disiplini, benchmark-kanitli yuzde 54 daha az kod -> CONFIRMATORY_CANDIDATE. (2) feynman (MIT): arastirma ajani, pre-registration/matched-control disiplinimizle ortusuyor -> CONFIRMATORY_CANDIDATE. (3) context-mode (ELv2): buyuk scan exportlari LLM context disinda sorgulama -> CONFIRMATORY_CANDIDATE, SaaS kisit notu. (4) timesfm (Apache-2.0): zero-shot tahmin ama yon 8 yoldan kapandi -> BLOCKED, once EOD-only backtest. (5) academic-research-skills CC BY-NC (noncommercial) -> STOP. (6) lightpanda AGPL-3.0 -> HOLD. (7) OpenMAIC (egitim), ECC (referans), marketingskills (GTM), ruflo (kendi orkestrasyonumuz var), openclaude (TS, bizim yigin Python) -> HOLD/STOP.
Impact: Hicbir production/scanner/score/publish davranisi degistirilmedi. Onerilen ivme kombinasyonu: feynman+ponytail+context-mode. Sonraki adim Level B: kucuk pilot + olcum.
Status: applied - Level A research-only.
Evidence: reports/external_repo_review_2026-09-07.md.

---
[2026-09-07] - FinSense icerik hazirligi: 69 modul tanimli, 1 ders yayinda; darbogaz orkestrator tetikleme (Level A)
Layer: Content / Research / Strategy
Level: A (arastirma); hicbir icerik/kod/config degistirilmedi
Context: Kullanici duzeltmesi — proje bitirme = FinSense icerik cogaltma + kullanima hazirlik. Onceki teknik-lens degerlendirme (external_repo_review) icerik lensiyle yeniden yapildi.
Change: (1) Envanter: 12 domain / 69 modul tanimli (academy/domains.py), yayinda yalniz 1 ders (academy_lessons.json count=1, Likidite Oranlari). Sozluk 44 terim. (2) Koken: altyapi var (6 ajan + orchestrator) ama run_daily hic tetiklenmiyor; content_generator ders uretiyor ama status=draft kaliyor, quality_guard denetleyecek draft bulamiyor. (3) Icerik lensiyle repo sirasi degisti: feynman (kaynak-dogrulamali ders uretimi) + context-mode (buyuk arastirma materyali yonetimi) one cikti; OpenMAIC pedagoji kalibi referansi olarak HOLD; ponytail icerik uretmez (kod uretir). (4) Onerilen yol: orkestratoru scheduler'a bagla (tek baglanti), kalibi zenginlestir, toplu uretim (5 job/gun = 14 gun), kalite kapisi zorunlu — hepsi mevcut altyapida, dis repo sart degil.
Impact: Hicbir production/icerik degisikligi yapilmadi. 69 modulun uretimi icin Level B onaylari gerekli (orkestrator tetikleme, kalip zenginlestirme, toplu uretim).
Status: applied - Level A research-only.
Evidence: reports/finsense_content_readiness_2026-09-07.md, academy/domains.py, web/public/academy_lessons.json, academy/orchestrator.py, academy/agents/content_generator.py, academy/agents/quality_guard.py.

---
[2026-09-07] - Pitch deck presentation-generation specification v1.0 (13 slayt, [V]/[S]/[C]/[A] etiketli) (Level A)
Layer: Content / Strategy / Governance
Level: A (icerik spesifikasyonu); uretim aracina verilecek, production kod degil
Context: Kullanicinin 13-slayt revizyonu + red-team onerileri birlestirilip Notebook-ready spec formatinda yazildi. Dort rakam ayrimi (5216/+0.40/46581/111), medyan negatif aciklamasi, €10K DGX Spark butce tablosu, What We Know/Dont Know slayti, GO/NO-GO sertlestirmesi dahil.
Change: docs/pitch_deck_presentation_spec_2026-09-07.md olusturuldu. Her slayt icin: baslik + ana mesaj + veri + gorsel talimat + dipnot + kaynak + do-not-say kurallari. Ust kurallar: omurga cumle, dort rakam asla birlesmez, 111 asla yuzde100-kazanan degil, +0.40 asla profit degil, 8 basarisiz yaklasim yalnizca Red Team kutusunda kaynakli. Akis: PAST(3-5) PRESENT(6-9) FUTURE(10-12) VISION(13).
Impact: Hicbir production/icerik degisikligi; bu bir slayt-uretim girdisi. Notebook bu spec'i dogrudan tuketecek.
Status: applied - Level A content spec.
Evidence: docs/pitch_deck_presentation_spec_2026-09-07.md; kaynaklar: data/finpilot.db, data/backtest_out/full_universe_barrier_results.json, reports/scanner_research_synthesis_10_perspectives_2026-08-11.md, reports/experiment_review_board_exp1_2026-09-03.md.

---
[2026-09-07] - Pitch deck Notebook prompt v1.0 + catalyst cache regresyonu tespit edildi (Level A)
Layer: Content / Strategy / Governance
Level: A (icerik + veri-butunlugu notu); production kod degil
Context: Notebook uretim promptu yazildi (docs/pitch_deck_notebook_prompt_2026-09-07.md). Prompt, spec docs/pitch_deck_presentation_spec_2026-09-07.mdyi tek gercek kaynak olarak tuketi r; gorsel dil + anlati ivmesi tanimlar. Momentum rakamlari gercek repo/DB sorgusundan: 89 arastirma raporu, 23 ajan, 5.216 sinyal, 1.812 evren, 12 domain/69 modul, 96 ders (8 yayinda). Bu rakamlar traction/velocity baglaminda, cekirdek bulgularla karistirilmadan kullanilir.
Change: (1) Notebook prompt yazildi. (2) VERI BUTUNLUGU OLAYI: data/catalyst_cache.json 2026-09-07 11:28de 1801-sembol/548-nonzero halinden 8-sembol/0-nonzero haline geriledi (uzerine yazildi). Slide 8deki SEC EDGAR universe-wide refreshed iddiasi su an desteklenmiyor — prompt bu satiri yumusatiyor (pilot-validated / TBD). Dogru degerler geri yuklenene kadar catalyst kapsam iddiasi yasak.
Impact: Hicbir production/icerik degisikligi. Catalyst cache regresyonu ayri bir operasyonel takip gerektiriyor (kokensel: hangi islem ezdi?).
Status: applied - Level A content + data-integrity note.
Evidence: docs/pitch_deck_notebook_prompt_2026-09-07.md, data/catalyst_cache.json (mtime 2026-09-07T11:28:55), docs/pitch_deck_presentation_spec_2026-09-07.md.

---
[2026-09-07] - Pitch deck final: spec v1.0 guncellendi + 13 slayt uretildi (Level A)
Layer: Content / Strategy / Governance
Level: A (icerik uretimi); production kod degil
Context: Kullanicinin 4 duzenlemesi spec'e islendi (medyan silinmez-yeniden cercevelenir, Slide 5 by-design yumusatma, FinSense parallel-track etiketi, 111-MFE yalniz Slide 4). Ardından docs/pitch_deck_slides_2026-09-07.md uretildi: 13 slayt, spec + prompt kurallarina tam uyumlu.
Change: (1) spec guncellendi: medyan current-exit-architecture baglamiyla korunuyor, locked OOS by-design olarak yumusatildi, FinSense parallel-track etiketlendi, 111-MFE gap notu Slide 4 sag paneline yerlesti, temizlenmis-kuyruk dipnotu eklendi. (2) Notebook prompt senkronlandi. (3) 13 slayt markdown olarak uretildi: PAST(3-5)/PRESENT(6-9)/FUTURE(10-12)/VISION(13) akisi, omurga cumle, [V]/[S]/[C]/[A] etiketleri korundu.
Impact: Hicbir production/icerik degisikligi; slayt dokumu uretim aracina/hazirliga hazir.
Status: applied - Level A content production.
Evidence: docs/pitch_deck_slides_2026-09-07.md, docs/pitch_deck_presentation_spec_2026-09-07.md, docs/pitch_deck_notebook_prompt_2026-09-07.md.

---
[2026-09-07] - Pitch deck HTML uretildi ve tarayicida dogrulandi (13 slayt render OK) (Level A)
Layer: Content / Strategy / Governance
Level: A (icerik uretimi + gorsel dogrulama); production kod degil
Context: docs/pitch_deck_slides_2026-09-07.md icerigi, spec (pitch_deck_presentation_spec_2026-09-07.md) ve prompt (pitch_deck_notebook_prompt_2026-09-07.md) kurallarina tam uyumlu tek-dosya HTML sunumuna donusturuldu: docs/pitch_deck_finpilot_2026-09-07.html.
Change: (1) 13 slayt HTML olarak uretildi: koyu tema, tek vurgu rengi, [V]/[S]/[C]/[A] etiket rozetleri korundu, dort rakam ayrimi (Slide 4 sol/sag panel) uygulandi, medyan current-exit-architecture cercevesiyle korundu, Slide 5 by-design yumusatildi, FinSense parallel-track etiketlendi, 111-MFE gap notu Slide 4 sag panelde temizlenmis-kuyruk dipnotuyla, omurga cumle Slide 1 ve 13te. (2) Tarayici dogrulamasi: 13/13 slayt render edildi, Playwright ile tum slaytlarin gorunurlugu teyit edildi.
Impact: Hicbir production/icerik degisikligi; yatirimci-facing sunum dosyasi hazir. Yazdirma/PDF icin print-color-adjust aktif.
Status: applied - Level A content production, browser-verified.
Evidence: docs/pitch_deck_finpilot_2026-09-07.html (13/13 slides render verified), docs/pitch_deck_slides_2026-09-07.md, docs/pitch_deck_presentation_spec_2026-09-07.md.

---
[2026-09-07] - Pitch deck TR revizyonu: 111-MFE one cikarildi, butce 20K, Turkce once (Level A)
Layer: Content / Strategy / Governance
Level: A (icerik revizyonu); production kod degil
Context: Kullanici 4 degisiklik istedi: (1) sunum once Turkce, (2) 111 adet >=yuzde100 MFE gozlemi one cikarilsin + daha sik/dogru yakalama hedefi belirtilecek, (3) butce 10K -> 20K, (4) haftalik ortalama yuzde5 kazanc hedefi aciklansin.
Change: (1-3) Uygulandi: TR birinci dil, 111-MFE Slide 4te vurgu + yakalama-sikligi hedefi eklendi, butce 20K olarak olceklendi (toplam 20.000 dogrulandi, tick/L2 pilot katmani eklendi, runway genisletildi). (4) HAFTALIK yuzde5: spec kural 10 ihlali olarak isaretlendi; sabit haftalik getiri vaadi yerine asimetrik getiri yapisinin bilesik potansiyeli cercevesi onerildi. Kullaniciya birakildi: kurali bilerek ihlal ederse eklerim ama bu Slide 3-5teki durustluk sermayesini riske atar.
Impact: Hicbir production/icerik degisikligi; TR HTML deck guncellenecek.
Status: applied - Level A content revision.
Evidence: docs/pitch_deck_finpilot_2026-09-07.html, docs/pitch_deck_presentation_spec_2026-09-07.md (kural 10).

---
[2026-09-07] - Pitch deck Turkce + 111-MFE vurgusu + 20K butce uygulandi ve dogrulandi (Level A)
Layer: Content / Strategy / Governance
Level: A (icerik revizyonu + gorsel dogrulama); production kod degil
Context: Kullanicinin 4 istegi uygulandi: (1) Turkce birinci dil, (2) 111 adet >=yuzde100 MFE gozlemi Slide 4te one cikarildi + daha sik/dogru yakalama hedefi + 1-yil getiri imkani notu eklendi, (3) butce 10K -> 20K (toplam 20.000 dogrulandi, tick/L2 pilot katmani + genisletilmis pilot + buyutulmus runway), (4) haftalik yuzde5 hedefi spec kural 10 ihlali oldugu icin EKLENMEDI — kullaniciya birakildi.
Change: docs/pitch_deck_finpilot_2026-09-07.html tamamen Turkceye cevrildi (13 slayt), Slide 4te 111-MFE vurgusu + yakalama-sikligi hedefi + 1-yil potansiyel notu eklendi, Slide 7 butcesi 20K olarak olceklendi. Tarayici dogrulamasi: 13/13 slayt render, Slide 1/4/7 metinleri Turkce dogrulandi.
Impact: Hicbir production/icerik degisikligi; TR yatirimci sunumu hazir. Haftalik yuzde5 kural-10 ihlali olarak logda isaretli — kullanici karari bekliyor.
Status: applied - Level A content revision, browser-verified.
Evidence: docs/pitch_deck_finpilot_2026-09-07.html (13/13 TR render verified), decision-log kural-10 notu.

---
[2026-09-07] - Slide 7 butce tablosu duzeltildi: 20K kalemleri gercek degerlerle (Level A)
Layer: Content / Governance
Level: A (icerik duzeltme); production kod degil
Context: Kullanici Slide 7nin 20K baslik tasidigini ama kalemlerin 10K eski degerlerini tasidigini yakaladi. Tablo duzeltildi.
Change: docs/pitch_deck_finpilot_2026-09-07.html Slide 7: her kalem olceklendi — donanim 4700, canli veri 2200 (12ay), tick/L2 katmani 2200 (6ay), bulut 600 (12ay), VPS 240, IBKR 300, sirket+muhasebe 800, yazilim 300, runway 8660. TOPLAM=20.000 dogrulandi. Tarayici dogrulamasi: tablo Turkce, toplam 20.000 gorunur.
Impact: Hicbir production/icerik degisikligi.
Status: applied - Level A content fix, browser-verified.
Evidence: docs/pitch_deck_finpilot_2026-09-07.html (Slide 7 20K table verified).

---
[2026-09-07] - Pitch deck PDF uretildi (Playwright/Chromium printToPDF) (Level A)
Layer: Content / Governance
Level: A (icerik uretimi); production kod degil
Context: Kullanici PDF istedi. weasyprint Windows'ta GTK libgobject eksikligiyle calismadi; Playwright Python + kendi Chromium'u kuruldu ve printToPDF ile uretildi. scripts/make_deck_pdf.py yazildi (tekrarlanabilir).
Change: docs/pitch_deck_finpilot_2026-09-07.pdf uretildi (1.09 MB, gecerli PDF-1.4). Sayfa sayisi 16: 13 slayt + icerik-yogun 3 slayt (4, 7, 12) tek sayfaya sigmayip ikiye bolundu — okunabilir, print-color-adjust aktif.
Impact: Hicbir production/icerik degisikligi; PDF dagitim/sunum icin hazir.
Status: applied - Level A content production.
Evidence: docs/pitch_deck_finpilot_2026-09-07.pdf (1.09 MB), scripts/make_deck_pdf.py.

---
[2026-09-07] - Karar mekanizmasi arastirma envanteri: 5 katman, bugune kadar yapilan tum calismalar (Level A)
Layer: Research / Governance
Level: A (envanter); hicbir kod degistirilmedi
Context: Kullanici karar mekanizmasi ekseninde bugune kadar yapilan calismalari sordu. Decision-log + reports taranip 5 katmanli karar mimarisi (sinyal secimi, rejim, sizing, cikis, ogrenme) cercevesinde tum calismalar envanterlendi.
Change: reports/decision_architecture_research_inventory_2026-09-07.md olusturuldu. Bulgular: Katman 1 (secim) en cok test edildi, entry_ok deger eksiltiyor, attention map tek canli alternatif. Katman 2 (rejim) yon uretmiyor. Katman 3 (sizing) en az test edildi, ATR-parity negatif. Katman 4 (cikis) en cok calisilan ama en az cozulen — hicbir sabit kural desteklenmedi, MFE gap (4.83 vs 0.37) burada yasiyor. Katman 5 (ogrenme) kalibrasyon yok. En buyuk acik firsat: cikis katmani.
Impact: Hicbir production davranisi degistirilmedi. Envanter deck'in Slide 5/6 kopusunu besliyor.
Status: applied - Level A research inventory.
Evidence: reports/decision_architecture_research_inventory_2026-09-07.md, docs/governance/decision-log.md.

---
[2026-09-08] - MASTER PROJECT REALITY & CONTINUITY AUDIT promptu standart denetim cercevesi olarak kaydedildi (Level A)
Layer: Governance / Research / Strategy
Level: A (cerceve kaydi); hicbir kod degistirilmedi
Context: Kullanici kapsamli bir Master Prompt tasarimladi: FinPilot/FinSense icin Project Reality Audit + State Reconstruction. Once-ala-sonra-oner ilkesi, gerceklik hiyerarsisi, status taksonomisi, FinPilot/FinSense ayrimi, dataset separation, 40 bolumlu yapı, Part A-T cikti sirasi.
Change: docs/MASTER_PROJECT_REALITY_AUDIT_PROMPT.md olusturuldu. Mevcut governance (AGENTS.md, 00-core, decision-log, Level A/B/C) ile uyumlu; onlari gecersiz kilmaz, tamamlar.
Impact: Hicbir production/icerik degisikligi. Bu cerceve bundan sonraki buyuk calismalarin standart denetim promptudur.
Status: applied - Level A framework registration.
Evidence: docs/MASTER_PROJECT_REALITY_AUDIT_PROMPT.md.

---
[2026-09-08] - KONTROL TURU: catalyst_cache regresyonunun KOK NEDENI bulundu (Level A tesihs, salt-okunur)
Layer: Research / Engineering / Governance
Level: A (yalnizca teshis, hicbir kod/config degistirilmedi)
Context: "gerekli kontrolleri kapsamli sekilde sagla" talebi uzerine `git status`/`git diff` ile bu oturumun disindaki degisiklikler tarandi. `data/catalyst_cache.json` hala 8-sembol/0-nonzero (2026-09-07T17:28 damgali) bulundu -- satir 1069-1077'deki kayit 1801/548'lik basarili bir evren-capli refresh oldugunu soyluyordu, yani BASKA bir sey onu tekrar 8'e dusurmus. Kok neden onceki kayitlarda "bilinmiyor" olarak birakilmisti.
Change (bulgu): `core/scheduler.py:1319-1334` -- her 6 saatte bir calisan `finpilot_catalyst_refresh` job'i, `scanner.catalyst.refresh_catalyst_cache(symbols)` cagiriyor. Bu fonksiyon dosyayi MERGE degil TAM UZERINE YAZMA (`json.dump({"updated":..., "factors": factors})`) ile yaziyor. `symbols` parametresi `start_scheduler(symbols=...)`'a `api/main.py:200-205`'ten geliyor: `FINPILOT_SCHEDULER_SYMBOLS` env degiskeni `.env`'de VE `.env.example`'da TANIMSIZ (grep ile dogrulandi) -> kod-seviyesi fallback devrede: `"AAPL,MSFT,NVDA,GOOGL,META,AMZN,TSLA,AMD"` (TAM OLARAK 8 sembol). Yani her 6 saatte bir, bu 8 demo-sembolluk liste ile catalyst_cache.json'un TAMAMI eziliyor -- 1801-sembollu evren-capli bir refresh olsa bile 6 saat icinde 8'e donuyor.
Impact: Hicbir kod/config degistirilmedi (yalnizca teshis). Bu, `FINPILOT_ENABLE_EDGAR_CATALYST` flag'i acik oldugu surece TEKRARLAYAN bir veri-kaybi kaynagi -- flag kapaliyken zararsiz (compute_catalyst_factor zaten 0.0 donuyor) ama flag'in gelecekte acilmasi planlaniyorsa bu once duzeltilmeli. Duzeltme secenekleri (Meric karari): (a) FINPILOT_SCHEDULER_SYMBOLS'u gercek evrene (veya evren dosyasina) isaret edecek sekilde ayarla, (b) refresh_catalyst_cache()'i merge-yazma yapacak sekilde degistir (yeni sembolleri ekle, mevcutlari ezme), (c) bu 6-saatlik job'i evren-capli ayri bir gorevle degistir. Hicbiri bu turda uygulanmadi.
Evidence: core/scheduler.py:1130-1334, api/main.py:200-205, scanner/catalyst.py:138-170, .env + .env.example (FINPILOT_SCHEDULER_SYMBOLS aranip bulunamadi), git diff (data/catalyst_cache.json mtime 2026-09-07T17:28, n=8, nonzero=0).

[2026-09-08] - Feature flag kanit ozeti cikarildi: 9 flag'in hicbiri ayni risk seviyesinde degil (Level A, salt-okunur)
Layer: Research / Governance
Level: A (yalnizca kanit derlemesi; hicbir flag/kod degistirilmedi)
Context: `reports/master_project_reality_audit_2026-09-08.md`'nin CRITICAL bulgusu (9 flag acik, decision-log default-OFF diyor) uzerine Meric "once kanit ozeti cikar" secti. Ayrica .env dogrudan okunarak flag'lerin GERCEKTEN acik oldugu (9/9) ve kod-seviyesi varsayilaninin hepsinin "0" oldugu teyit edildi (grep ile). Ek bulgu: catalyst_cache.json bu oturumda yazdigim 1.199-sembollu dosya, 2026-09-07 17:28 damgali 8-sembollu bir dosyayla EZILMIS -- ayni "esz amanli surec cakismasi" sorununun somut bir veri-kaybi ornegi.
Change: `reports/feature_flag_evidence_summary_2026-09-08.md` yazildi. Ozet: LOTTERY_FADE (tek Bonferroni-hayatta-kalan sinyal) ve SHADOW_SCORECARD (skoru etkilemiyor, salt olcum) acik kalmasi kanitla destekleniyor; OVERNIGHT_GAP kanitla curutulmus (olu sinyal), kapatilmasi savunulabilir; EDGAR_CATALYST zararsiz ama faydasiz (veri bayat, flag sorunu degil); SQUEEZE_FACTOR kanit yetersiz (ince veri, supheli null-baseline); FRED_MACRO/FUNDAMENTALS/NEWS/ALPHA_V2 bu programda HIC test edilmemis gercek UNKNOWN'lar -- ALPHA_V2 ayrica gecmiste (2026-07) test paketine sizip karisiklik yaratmis oldugu icin ekstra dikkat gerektiriyor.
Impact: Hicbir flag/config degistirilmedi. Karar Meric'e ait -- rapor yalnizca hangi flag'in hangi kanit seviyesinde oldugunu ayirt ediyor.
Evidence: reports/feature_flag_evidence_summary_2026-09-08.md, .env (okundu), scanner/score_engine.py + scanner/features.py + scanner/risk_engine.py (grep ile varsayilan degerler dogrulandi), scanner/catalyst.py:64.

[2026-09-08] - MASTER PROJECT REALITY AUDIT calistirildi: FAZ 1+2, tam rapor (Level A)
Layer: Governance / Research / Strategy / Engineering
Level: A (salt-okunur denetim); hicbir kod/config/veri/flag degistirilmedi
Context: docs/MASTER_PROJECT_REALITY_AUDIT_PROMPT.md cercevesi ilk kez calistirildi. Repo, veritabanlari, calisan servisler (API 128 endpoint, web), feature flagler, decision-log taranip Part A-T raporu uretildi.
Change: reports/master_project_reality_audit_2026-09-08.md. Kritik bulgular: (1) CRITICAL CELISKI — .envde 9 feature flag acik (catalyst/squeeze/lottery/overnight/FRED/fundamentals/news/alpha_v2/shadow) ama decision-log bunlari default OFF/validate-first olarak belgeliyor; score_engine bunlari aktif kullaniyor, hicbiri matched-control ile dogrulanmadi. (2) FinSense dongusu kapali degil: 96 ders (8 yayinda, 88 draft), cift academy DB (Finsense 96, Borsa 0), export manuel. (3) Catalyst cache regresyonu 1801/548 -> 8/0. (4) En buyuk firsat: cikis katmani (MFE 4.83 vs captured 0.37).
Impact: Hicbir production davranisi degistirilmedi. Master Work Plan 5 NEXT maddesiyle cikti; ilk is feature flag celiskisini cozmek.
Status: applied - Level A full audit, read-only.
Evidence: reports/master_project_reality_audit_2026-09-08.md, api openapi (128 endpoints), .env flags, docs/governance/decision-log.md.

---
[2026-09-08] - META-VALIDATION AUDIT: onceki Master Audit denetlendi, feature-flag celiskisi olculdu ve buyutuldu (Level A, READ-ONLY)
Layer: Governance / Research / Engineering
Level: A (salt-okunur); hicbir kod/config/veri/flag/DB degistirilmedi
Context: Meta-Validation Master Prompt v1.0 calistirildi — onceki Master Project Reality Audit'in kendisi denetlendi. Her kritik iddia bagimsiz izlendi.
Change: reports/meta_validation_audit_2026-09-08.md. Onceki audit skoru 47/60 (GOOD, targeted correction). KRITIK: feature flag iddiasi dogrulandi VE buyutuldu — .envde 9 flag=1, score_engine cagiriyor, ve meta-olcum gosterdi: bugunku 1801 satirlik exportta 1503 satir (yuzde 83.5) skoru flagler tarafindan degistiriliyor, 775i anlamli (|delta|>=0.5), net etki -0.639 (asagi). Faktor verisi gercek (squeeze/lottery/overnight nonzero). Catalyst cache root cause PROBABLE=cift-yazici+yeniden-calistirma. Akademi scheduler REGISTERED ama RUNNING kanitlanmadi (UNKNOWN). Attention map VALIDATED-DESCRIPTIVE-RESEARCH seviyesinde dogru siniflandi (production degil).
Impact: Hicbir production degisikligi. NEXT 5: (1) flag karari (EN YUKSEK), (2) catalyst tek-yazici, (3) scheduler kaniti, (4) cift DB karari, (5) 88 draft quality_guard.
Status: applied - Level A meta-audit, read-only.
Evidence: reports/meta_validation_audit_2026-09-08.md, .env flag values, scanner/score_engine.py flag call counts, 2026-09-08 score-delta measurement.

---
[2026-09-08] - SCORING ABLATION: 4 flag componenti test edildi - hicbiri OOS'ta baseline'i iyilestirmiyor (Level A, READ-ONLY)
Layer: Research / Engineering / Governance
Level: A (read-only research); production/flag/veri degistirilmedi
Context: Scoring Ablation Master Prompt v1.0 calistirildi. Meta-auditin 1 numarali maddesi (flag karari) icin kanit uretildi. EOD-only dataset (c2c_5d duzeltmeli), kronolojik 70/30 split, pre-registered.
Change: reports/scoring_ablation_audit_2026-09-08.md + 2 CSV + artifact. Bulgular: (1) Meta-auditin yuzde 83.5 skor-sapmasi predictive degere DONUSMUYOR - IMPLEMENTED/ACTIVE/INFLUENTIAL/PREDICTIVE ayrimi dogrulandi. (2) Hicbir component KEEP degil: Squeeze UNVALIDATED, Lottery MODIFY (negatif-secim bucket'ta gercek ama Top-N tutarsiz), Overnight MODIFY (ayn), Catalyst UNVALIDATED (veri bos), Full UNVALIDATED. (3) Baseline bile OOS Top-20 hit 0.35 - siralama genel zayif. (4) Lottery/overnight negatif-secim davranisi bucket'ta dogrulandi (yuksek deger -> dusuk getiri) ama skora katkiya cevirmiyor.
Impact: Hicbir production degisikligi. Flag karari icin kanit hazir: flagler skoru degistiriyor ama ileri getiriyi tahmin etmiyor. Sonraki: matched-control + walk-forward + catalyst veri onarimi.
Status: applied - Level A research, read-only.
Evidence: reports/scoring_ablation_audit_2026-09-08.md, reports/scoring_component_leaderboard_2026-09-08.csv, data/backtest_out/scoring_ablation_2026-09-08.json, research/scoring_ablation_runner_2026_09_08.py.

---
[2026-09-08] - WALK-FORWARD + MATCHED-CONTROL + RANK-DISPLACEMENT: hicbir component OOS'ta baseline'i tekrarlanabilir gecmiyor (Level A, READ-ONLY)
Layer: Research / Engineering / Governance
Level: A (read-only); hicbir production/kod/flag/veri/agirlik degistirilmedi; hicbir optimizasyon yapilmadi
Context: Walk-Forward Master Prompt v1.0 calistirildi — ablation'in tek-bolunme zayifligini gideren daha guclu test. EOD-only, c2c_1d hedefi, 4 onceden-tanimli pencere (W1-W4, 70/30 kronolojik), W1 bloke (oos_n=1), 3 gecerli pencere.
Change: reports/walk_forward_scoring_validation_2026-09-08.md + 4 CSV + JSON artifact. Bulgular: (1) Hicbir component OOS'ta baseline'i tekrarlanabilir gecmiyor (Squeeze 0/3, Lottery 0/3, Overnight 1/3, Full 0/3 better). (2) Baseline kendisi zayif (Spearman yaklasik 0, Top-20 hit 0.55-0.75 tutarsiz) — COMPONENT VALIDATION CONFIDENCE=LOW. (3) Rank-displacement cogunlukla neutral; matched-control cogu pencerede yetersiz ornekle bloke (componentler siralamayi zar zor degistiriyor). (4) Catalyst UNVALIDATED-DATA-UNAVAILABLE (factor=0.0). (5) Kararlar: hepsi UNVALIDATED, hicbiri KEEP/DISABLE/MODIFY degil.
Impact: Hicbir production degisikligi. Flag karari icin daha guclu kanit: componentler skoru degistiriyor ama siralamada tekrarlanabilir bilgi tasimiyor. Sonraki: baseline methodology arastirmasi (Part 36) + catalyst veri onarimi.
Status: applied - Level A research, read-only.
Evidence: reports/walk_forward_scoring_validation_2026-09-08.md, reports/component_validation_leaderboard_2026-09-08.csv, data/backtest_out/walk_forward_scoring_2026-09-08.json, research/walk_forward_scoring_validation_2026_09_08.py.

---
[2026-09-10] - MASTER RESEARCH INVENTORY olusturuldu + INDEX research.authority_path adayi kaydi (Level B, Meric onayli)
Layer: Research / Governance
Level: B (Meric onayi ile); docs/INDEX.md manifest research girisine canonical-referans notu eklendi. Klasor otoritesi (authority_path=reports) DEGISMEDI; yalnizca tek giris noktasi isaretlendi.
Context: ~80 arastirma raporunun tek otorite envanterine ihtiyac vardi. Meric icerik incelemesinde 3 duzeltme istedi (baseline reconstruction = NOT_FULLY_RECONSTRUCTED historically / FORWARD CAPTURE ENABLED; IMPLEMENTED!=PREDICTIVE provenance; B2 'yetersiz' yerine 'diversity not yet sufficient') — hepsi uygulandi, sonra onay verdi.
Change: YENI reports/MASTER_RESEARCH_INVENTORY_2026-09-10.md (kavram->karar->kanit envanteri, 5 donem, cross-cutting bulgular, aktif gated pipeline, bekleyen kararlar, kirmizi cizgilar). docs/INDEX.md manifest id=research girisine note eklendi (authority_path degismedi). lint_authority_map.py OK (0 hata).
Impact: Yeni bir buyuk audit/research baslatilmadan once inventory'ye bakilir; bulgu degisikligi inventory'de tek satirla islenir (duplikasyon yok, referans var). B2 accumulation bundan bagimsiz devam eder; inventory B2/B3 sonucunu DEGISTIRMEZ, yalnizca canonical referansi belirler.
Status: applied - Level B, Meric onayli.
Evidence: reports/MASTER_RESEARCH_INVENTORY_2026-09-10.md, docs/INDEX.md (research note), scripts/lint_authority_map.py (OK).

---
[2026-09-18] - ANS-1 ATTENTION-AS-NEGATIVE-SCREEN: SUPPORTED (Level A, pre-registered, read-only)
Layer: Research / Product (attention map)
Level: A (read-only research); hicbir production/veri/flag degistirilmedi
Context: Dis kanit (Barber 2022 JF Robinhood -4.7%/20d; Bali 2011 JFE lottery) attention hisselerinin dusuk getiri verdigini soyluyordu. FinPilot cross-check bunu dogruladi (descriptive). ANS-1 bunu pre-registered OOS-disiplinli kontrolle test etti: attention-flag (|gap|>=3% OR ATR>=6%) hisseleri eleme kalan evrenin medyan 5-gun getirisini iyilestirir mi?
Change: reports/ans1_attention_negative_screen_2026-09-18.md + JSON artifact. Sonuc: SUPPORTED. Median iyilesme +2.62pp; block-bootstrap %95 CI [+0.16,+3.86] (sifir disinda); matched-random percentile 1.0; null-shuffle p=0.000. Big-loser orani %22.2 -> %3.5. Dort kosul da PASS.
Impact: Attention map'in okunmasi 'al' degil 'kacin/dikkat' yonunde destekleniyor (3 bagimsiz kanit katmani: dis TIER A + ic descriptive + pre-registered kontrol). NEGATIF-ELEME degeri medyan/risk tarafinda; maliyet bariyeri YOK (eleme islem degil). KANITLANMADI: short sinyali, ekonomik/portfoy degeri, buyuk-kazanan kuyrugu firsat maliyeti. Production yuzeyine tasimak ayri Level B/C (yasak-dil kirmizi cizgisi). Urun karari: attention map'i negatif-eleme/risk-uyarisi olarak konumlandirma (Level B).
Status: applied - Level A research, read-only.
Evidence: reports/ans1_attention_negative_screen_2026-09-18.md, data/backtest_out/ans1_attention_negative_screen_2026-09-18.json, research/ans1_attention_negative_screen_2026_09_18.py.

[2026-09-22] - RESEARCH-X/H4C information-loss result (Level A)
Layer: Research / Governance
Level: A (read-only forensic research; production and locked OOS unchanged)
Context: The APPROVED/LOCKED H4C preregistration was executed strictly as written. Scope was limited to the reconstructable composite_score <-> legacy_quality_score mapping on the canonical EOD-only export; no production ordering was reconstructed, simulated, or asserted.
Result: H4C verdict is `INFORMATION_LOSS_NOT_SUPPORTED`. Primary evidence (TIE_INTERNAL_PROXY_VARIATION) failed: observed tie-internal proxy dispersion (group-demeaned variance 68.46) is far BELOW the scan-date-preserving permuted-null 95% upper band (348.77), not above it. Composite ties do not hide extra proxy spread; the proxy's variation comes from its own daily marginal distribution, not from differences the composite fails to capture. Descriptive auxiliaries: monotonicity violation share 0.41573; round-trip R^2 0.787596 (unexplained 0.212404); many-to-one composite->proxy median distinct 449.5.
Boundaries (unchanged): This negative result does NOT mean production ranking avoids information loss; H4C did not examine production ordering. `production_ordering` remains UNKNOWN / NOT RECONSTRUCTED and official production ranking resolution remains DEFINITION_REQUIRED. H4C only records that the tested tie-internal proxy-dispersion information-loss hypothesis was not supported. This does not erase H4A's COMPRESSION_SUPPORTED finding or H4B's MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS finding; compression and the tested information-loss mechanism are different things. No causal chain 'compression -> information loss' is asserted.
Impact: No score formula, ranking source, scanner, configuration, database, scheduler, publication behavior, or user-facing surface was changed. production_impact = NONE. Chain now: H2 CLOSED/NOT_SUPPORTED, H4A CLOSED/COMPRESSION_SUPPORTED, H4B CLOSED/MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS, H4C CLOSED/INFORMATION_LOSS_NOT_SUPPORTED.
Status: applied - Level A research-only audit complete.
Evidence: preregistration `reports/research_x_h4c_information_loss_preregistration_2026-09-22.md` (APPROVED/LOCKED); runner `research/research_x_h4c_information_loss_2026_09_22.py`; JSON `data/backtest_out/research_x_h4c_information_loss_2026-09-22.json` SHA-256 `f4b0b552f3b79050b975b867be2230edaa1a81def9b5807ad0b7bbd10b46e762`; report `reports/research_x_h4c_information_loss_2026-09-22.md` SHA-256 `0c624caa7f61edfd8b3cd9830c2de339286a45bc8f1d3aaddfc18fa5aface66d`; determinism confirmed (two byte-identical runs); input integrity passed (40014 composite / 39986 proxy / 28 rvol-excluded; 90 vs 27050 unique; integer fraction 0.064573, all matching H4B).

---

[2026-09-22] - RESEARCH-X/H4D ranking-resolution definition locked (Level A)
Layer: Research / Governance
Level: A (read-only; definition-only - no measurement, no code, no production change)
Context: After the H4 line closed (H2 NOT_SUPPORTED, H4A COMPRESSION_SUPPORTED, H4B MAPPING_DEPENDS_ON_ADDITIONAL_INPUTS, H4C INFORMATION_LOSS_NOT_SUPPORTED), the remaining open concept was official production ranking resolution, left as DEFINITION_REQUIRED by H4B. H4D is a definition-only preregistration that locks what 'resolution' means and how it would be measured, without measuring it.
Change: Locked definition hierarchy: PRIMARY = Candidate B (production sort-tuple resolution, since production ordering is behavioral and multi-key); SECONDARY/DIAGNOSTIC = Candidate A (score-space resolution of the declared ranking-score field, preserving 'score resolution != production ordering resolution'); OBSERVATIONAL ENDPOINT / provenance-dependent = Candidate C (displayed-rank, not reconstructable from historical export). Score-field hierarchy locked: resolution is primarily the full production sort tuple (score + categorical/tier + confidence/probability fields); legacy_quality_score is a named score-field candidate/diagnostic, NOT equated with production ordering. FINAL-TIE STATUS = RESOLUTION_UNDERSPECIFIED_AT_FINAL_TIE when multiple observations share the complete declared sort tuple and no explicit final tie-breaker determines relative order.
Impact: Definition locked only; no resolution value was measured. Tie is explicitly NOT classified as failure/insufficiency/defect - it only means the group's internal ordering is not determined by declared sort keys; the definition separates resolution from determinism and capacity. Historical limitation: if production ordering/provenance cannot be reconstructed, the resolution value remains unmeasured/unknown. Measurement is prohibited in H4D-definition and requires a separate H4D-measure preregistration plus approval. Candidate C live measurement would be Level B and is not authorized here. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. production_impact = NONE. H2/H4A/H4B/H4C verdicts unchanged and not eroded.
Status: applied - Level A definition-only lock recorded.
Evidence: `reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md` (APPROVED/LOCKED) SHA-256 `cbd3812c76bb00a04f3420d1d08d312a22a3e679f1243aa37e2229798d587499`; canonical export SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`.

---

[2026-09-22] - RESEARCH-X/H4D-measure preregistration locked (Level A)
Layer: Research / Governance
Level: A (read-only; measurement protocol only - no code yet, no production change)
Context: Following the APPROVED/LOCKED H4D definition (primary = Candidate B production sort-tuple resolution), H4D-measure locks the measurement protocol for 'resolution kac?' only. It never answers 'resolution yeterli mi?'. The chain H2/H4A/H4B/H4C/H4D-definition remains closed and unchanged.
Change: Locked measurement protocol derived from the H4D definition. A historical reconstructability gate runs BEFORE measurement: the canonical export lacks grade, execution_confidence, conviction_prob, ranking_score and legacy_quality_score, so the full production sort tuple cannot be reconstructed historically and the gate is pre-defined as PROVENANCE_INSUFFICIENT (a valid outcome, not a failure, and not a workaround of H4B's UNKNOWN/NOT RECONSTRUCTED). Verdict set locked: MEASURED / NOT_MEASURABLE-PROVENANCE_INSUFFICIENT / PARTIAL / INPUT_MISMATCH, reported per endpoint (snapshot/summary/score-space). Capacity, Collision/tie structure, and Determinism are measured separately and never compressed into a single resolution score. Determinism is reported as UNDETERMINED_AT_FINAL_TIE in full-tie groups (a definition consequence, not a defect). NULL_BUCKET missing-policy, no imputation, no tuple shortening, snapshot vs summary never merged, no permutation/null model (descriptive), determinism via two byte-identical runs.
Impact: Locked an explicit methodological guard: preregistered expectations are priors only; the runner must actually execute the reconstructability gate and derive the outcome from data, and a MEASURED score-space (Candidate A) result does NOT mean production resolution was measured. production_impact = NONE. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed; no H4D-measure runner written yet. Runner research/research_x_h4d_measure_2026_09_22.py may now be written and run read-only.
Status: applied - Level A measure preregistration locked before runner execution.
Evidence: `reports/research_x_h4d_measure_preregistration_2026-09-22.md` (APPROVED/LOCKED) SHA-256 `9eb331c39d1e576c38b3e44115d0169c6c32184e205dcb164a3544dddebb657b`; locked definition `reports/research_x_h4d_ranking_resolution_definition_2026-09-22.md` SHA-256 `cbd3812c76bb00a04f3420d1d08d312a22a3e679f1243aa37e2229798d587499`; canonical export SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`.

---

[2026-09-22] - RESEARCH-X/H4D-measure result (Level A)
Layer: Research / Governance
Level: A (read-only measurement; production and locked OOS unchanged)
Context: The APPROVED/LOCKED H4D-measure preregistration was executed strictly as written. The runner executed the historical reconstructability gate on the actual canonical export columns (it did not assume the preregistered priors). It answered 'resolution kac?' only and did not answer 'resolution yeterli mi?'.
Result: H4D-measure = CLOSED / PROVENANCE_INSUFFICIENT. Primary Candidate B (production sort-tuple resolution): snapshot tuple NOT_MEASURABLE / PROVENANCE_INSUFFICIENT; summary tuple NOT_MEASURABLE / PROVENANCE_INSUFFICIENT - the export lacks grade, execution_confidence, conviction_prob, ranking_score and legacy_quality_score, and no imputation or tuple shortening was applied. Candidate A (score-space diagnostic): MEASURED, but descriptive only - composite_score unique = 90, tie_share = 0.999975; this is explicitly NOT a production resolution measurement (score resolution != production ordering resolution). Candidate C (displayed-rank): NOT_MEASURABLE / PROVENANCE_INSUFFICIENT historically (final tie-breaker and input-order provenance absent).
Boundaries (unchanged): Resolution is DEFINED (H4D-definition) but its production value is NOT historically measurable from the available export. This does NOT mean production resolution is low/insufficient, and the Candidate A 99.9975% tie share is NOT a production resolution result. production_ordering remains UNKNOWN / NOT RECONSTRUCTED. production_impact = NONE. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. H2/H4A/H4B/H4C/H4D-definition and the H4D-measure lock entry are unchanged and not eroded. Measuring production resolution would require live provenance, which is a separate Level B research/product decision not authorized here.
Status: applied - Level A measurement result recorded.
Evidence: preregistration `reports/research_x_h4d_measure_preregistration_2026-09-22.md` (APPROVED/LOCKED); runner `research/research_x_h4d_measure_2026_09_22.py`; JSON `data/backtest_out/research_x_h4d_measure_2026-09-22.json` SHA-256 `8319807678e4cd6113e4e18b64526a61b75249b8db50eb62a970952ef23fab0c`; report `reports/research_x_h4d_measure_2026-09-22.md` SHA-256 `12b6fd8de9b13605b939226ca6910da5c88b93907c58ecde696b32dbb0c85e78`; determinism confirmed (two byte-identical runs); input integrity passed (40014 composite rows; canonical SHA 87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad).

---

---
[2026-09-22] - RESEARCH-X/NS-1 negative-screen battery preregistration locked (Level A)
Layer: Research / Governance
Level: A (read-only; measurement protocol only - no code yet, no production change)
Context: After the master scientific state audit (read-only synthesis, unlocked), the first research step of Phase 1 (negative-screen line) was designed. Builds on ANS-1 SUPPORTED, ANS-2 opportunity-cost, ANS-3 temporal PARTIAL, and the failure-phenotype descriptive report (RX-H1 formalized here for the first time). H2/H4A/H4B/H4C/H4D chain remains CLOSED/FROZEN and untouched; this is NOT a continuation or reopening of H4.
Change: Locked protocol for the question "do pre-locked, scan_date-relative elimination rules improve the remaining universe c2c_5d distribution (median and big-loser tail) beyond matched-random and null-shuffle controls, and does the improvement replicate temporally?". Locked primary rule family: NS-A (ANS-1 exact replication), NS-B3 (failure-profile majority rule, >=3 of 4 conditions: atr_pct_real>=p80, lottery_factor>=p80, price<=p20, dist_52w_high<=p20, all scan_date-internal percentiles), NS-C (lottery_factor>=p80), NS-UNION (A or B3); family-wise Bonferroni adjusted CI 98.75%. Controls locked: matched-random R=300, null-shuffle R=300, date-block bootstrap B=2000, seed=20260922. Verdict set locked: SCREEN_SUPPORTED (adjusted CI excludes 0 AND matched-random AND null-shuffle AND early/late same sign AND big-loser rate not increased) / SCREEN_PARTIAL / SCREEN_UNSTABLE / SCREEN_NOT_SUPPORTED / INSUFFICIENT_DATA / INPUT_MISMATCH. Loser recall added as secondary descriptive metric (c2c_5d<=-10% base), never enters any verdict. Temporal reporting locked: early_effect_pp, late_effect_pp, early/late ratio mandatory; same-sign verdict rule unchanged, no post-hoc magnitude threshold. Screening evidence is NOT a buy signal and NOT a production filter; any production use is a separate Level B decision.
Impact: No score formula, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. production_impact = NONE. No runner written yet; runner research/research_x_ns1_negative_screen_2026_09_22.py may now be written and run read-only.
Status: applied - Level A preregistration locked before runner execution.
Evidence: `reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md` (APPROVED/LOCKED) SHA-256 `9e53d40759b6b989719f59fdd4d559c7f5fcc8a7346a3e1fd39e94c95c236838`; canonical export SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`.

---
[2026-09-22] - RESEARCH-X/NS-1 negative-screen battery result (Level A)
Layer: Research / Governance
Level: A (read-only forensic research; production and locked OOS unchanged)
Context: The APPROVED/LOCKED NS-1 preregistration was executed strictly as written on the canonical EOD-only export (n=34,762, 54 dates; input SHA verified; input_mismatch=False). Controls: matched-random R=300, null-shuffle R=300, date-block bootstrap B=2000 (5-day blocks, ANS-1 contract), seed=20260922, family-wise Bonferroni 98.75% adjusted CI on the 4 primary rules.
Result: Overall = NO_SCREEN_SUPPORTED. Per-rule: NS-A SCREEN_NOT_SUPPORTED; NS-B3 SCREEN_PARTIAL; NS-C SCREEN_PARTIAL; NS-UNION SCREEN_NOT_SUPPORTED. During execution one methodology-defect was found in my own first runner draft and corrected BEFORE any verdict was recorded: the first draft measured "median(kept)-median(full)" while the locked NS-1 question (and the ANS-1 contract it replicates) is the kept-vs-removed median difference; the runner was corrected to the ANS-1 estimand (median kept-removed, 5-day block bootstrap, ANS-1 matched-random/null-shuffle semantics). Verdicts above are from the corrected, determinism-verified runner only; the superseded draft produced different labels and was NOT used.
Replication: NS-A point estimate matches ANS-1 exactly (median kept-removed = 2.624845pp; kept 0.299 / removed -2.326; big-loser 22.2% -> 3.5%; loser recall 80.0%; removed n=13,433). ANS-1's SUPPORTED verdict is NOT reopened or weakened: NS-A reads SCREEN_NOT_SUPPORTED only because NS-1's locked question (does REMOVING flagged rows improve the remaining universe?) under the wider percentile bootstrap plus 98.75% family-wise adjustment yields an adjusted CI [-0.24, 4.57] containing zero - same point estimate, wider interval, different estimand.
Findings: NS-B3 (failure-profile majority rule) and NS-C (lottery-only) are the only rules whose adjusted CI excludes zero, but both fail temporal significance in one half (NS-B3 early-significant/late-not; NS-C late-significant/early-not) -> SCREEN_PARTIAL. NS-UNION tracks NS-A (only ~37 additional rows) and inherits its verdict. PRICE5 robustness arm is a valid negative descriptive finding: naive sub-USD5 exclusion WORSENS the kept universe (-2.10pp) and removes big winners faster than losers - it warns against using the price<=p20 leg of NS-B3 as a standalone rule. Loser recall (descriptive only, never enters verdicts): NS-A 80.0%, NS-B3 30.3%, NS-C 33.7%.
Boundaries (unchanged): Screening evidence is NOT a buy signal and NOT a production filter. No verdict authorizes any production elimination rule; that is a separate Level B decision. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. H2/H4 chain remains CLOSED/FROZEN; ANS-1/ANS-2/ANS-3 unchanged. production_impact = NONE.
Status: applied - Level A research-only result recorded.
Evidence: preregistration `reports/research_x_ns1_negative_screen_preregistration_2026-09-22.md` (APPROVED/LOCKED) SHA-256 `9e53d40759b6b989719f59fdd4d559c7f5fcc8a7346a3e1fd39e94c95c236838`; runner `research/research_x_ns1_negative_screen_2026_09_22.py`; JSON `data/backtest_out/research_x_ns1_negative_screen_2026-09-22.json` SHA-256 `0d0402f5a1f56a1c4c14734c444206801a863f678d5a8b6570210d45637a165c`; report `reports/research_x_ns1_negative_screen_2026-09-22.md` SHA-256 `d1f4cedb5d547d7a66c2b4849636826e3aa1b5ea3e23ceed4dccfd32bb5fbeef`; determinism confirmed (two byte-identical runs).

---
[2026-09-22] - RESEARCH-X Master Orchestrator v2 adopted (Level B)
Layer: Governance / Research process authority
Level: B. Meric approved v2 on 2026-09-22 ("V2'yi onaylıyorum"). This entry records adoption of the master research orchestrator as the process template for FUTURE Research-X lines. By its own sections 10 and 62, this adoption does NOT start any research line, does NOT change any production behavior, does NOT reopen any frozen line, and does NOT alter any locked historical record.
Context: Following the master scientific state audit and the completed NS-1 line, a v1 orchestrator draft was independently reviewed and three blocking findings were recorded: (1) an estimand ambiguity between median(kept)-median(removed) and median(remaining)-median(full); (2) the verdict engine missing the locked big-loser non-degradation gate; (3) stale "DRAFT/not-locked" state for NS-1. V2 resolved all three and added structural rules derived from NS-1's two real lessons: a mandatory pre-lock Estimand Audit (section 5: prose/formula/runner/verdict/report must map to exactly one mathematical estimand; ambiguity -> STOP -> USER REVIEW, unilateral interpretation prohibited) and a mandatory Independent Result Verification layer with a discrepancy protocol (sections 30-32: same data + same locked protocol + different implementation path; do-not-average, do-not-pick-favorite, do-not-edit-to-match).
Change: Adopted `docs/governance/research_x_master_orchestrator_v2.md` as the governing research-process template for future Research-X lines. NS-1 is recorded as COMPLETED / LOCKED / WITH DOCUMENTED PROTOCOL DEVIATION / PRIMARY VERDICT: NO_SCREEN_SUPPORTED / INDEPENDENT VERIFICATION: PENDING / PRODUCTION IMPACT: NONE; H4 remains FROZEN / CLOSED. No new research line is started by this adoption; NS-1 independent verification remains a separate, pending action requiring its own go-ahead.
Impact: production_impact = NONE. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. Governance is append-only; no prior record overwritten.
Status: applied - Level B research process authority adopted.
Evidence: `docs/governance/research_x_master_orchestrator_v2.md` SHA-256 `cf5ab1e2e721ea480e55eb2587f97cc65936047cc9fdfff29226f096c56536f3`.

---
[2026-09-22] - RESEARCH-X/NS-1 independent result verification (Level A)
Layer: Research / Governance
Level: A (read-only verification; NOT a new experiment; NS-1 artifacts, verdicts and governance unchanged)
Context: Master Orchestrator v2 (adopted today) marks NS-1 INDEPENDENT VERIFICATION: PENDING. Per v2 sections 30-32 this was executed with same data + same locked protocol + a DIFFERENT implementation path (csv module + dict dedup + sorted-list percentiles + statistics.median + numpy RandomState) versus the locked runner (pandas read_csv + groupby.quantile + default_rng).
Result: VERIFICATION_PASS. All deterministic primary quantities matched the locked NS-1 JSON exactly: population n=34,762; removed_n (NS-A 13,433 / NS-B3 3,959 / NS-C 4,854 / NS-UNION 13,470); observed median improvements (2.624845 / 3.471634 / 3.184916 / 2.624770 pp); kept/removed medians; big-loser rates; loser recall (80.0% / 30.3% / 33.7% / 80.1%); early/late temporal point estimates; all verdict inputs (adjusted-CI excludes-zero sign, matched-random pass, null-shuffle pass, temporal same-sign) reproduced. Verdicts unchanged: NS-A SCREEN_NOT_SUPPORTED, NS-B3 SCREEN_PARTIAL, NS-C SCREEN_PARTIAL, NS-UNION SCREEN_NOT_SUPPORTED, overall NO_SCREEN_SUPPORTED.
Discrepancy investigation (v2 section 32 - documented, not averaged, not edited-to-match): (1) SECONDARY arm B3-price differs by 3/34,762 rows at the price==p20 floating-point interpolation boundary (sorted-list linear interpolation vs np.quantile rounding at exact ties); (2) a dedup micro-ambiguity was identified in the canonical contract - the prose says "earliest lexical scan_ts" but the pipeline behaves as "first row in (scan_date,symbol) stable file order"; these differ on exactly 2 NVDA dates (2026-07-01, 2026-07-22) where the earliest scan_ts (19:45) appears after later-scan_ts duplicates in file order; (3) block-bootstrap CI bounds jitter up to ~0.4pp under the different RNG pattern with identical excludes-zero signs. None of these affects any verdict input; both discrepancy classes are confined to secondary/diagnostic arms.
Impact: production_impact = NONE. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. NS-1 remains COMPLETED / LOCKED / WITH DOCUMENTED PROTOCOL DEVIATION; its verdicts are unchanged. H4 FROZEN. The two micro-ambiguities (dedup tie semantics; price==p20 interpolation boundary) are recorded as DEFINITION debt for future pre-registrations: future protocols must pin dedup tie-handling and the exact percentile function in the estimand audit (v2 section 5).
Status: applied - Level A verification recorded. NS-1 INDEPENDENT VERIFICATION: PENDING -> VERIFICATION_PASS.
Evidence: verifier `research/ns1_independent_verification_2026_09_22.py`; verification JSON `data/backtest_out/ns1_independent_verification_2026-09-22.json` SHA-256 `e54344b6679dfd1b2f3a818f26f002db8ee53157361df933fecab02c534a02a7`; locked NS-1 JSON SHA-256 `0d0402f5a1f56a1c4c14734c444206801a863f678d5a8b6570210d45637a165c` (verified unchanged); input SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad` (verified).

---
[2026-09-22] - RESEARCH-X/RX-CAPTURE-1 capture & exit battery preregistration locked (Level A)
Layer: Research / Governance
Level: A (read-only; measurement protocol only - no code yet, no production change)
Context: After the master scientific state audit identified exit/capture as the largest quantified opportunity (MFE mean ~14.34% / prior capture ~+0.37%) and prior TP/SL batteries were NOT_SUPPORTED, RX-CAPTURE-1 asks a narrower, different question: with selection LOCKED, can pre-defined, path-aware, cost-inclusive exit rules capture a meaningful share of the 5-day MFE ex-ante? This is NOT a selection study and NOT a continuation or reopening of H4 (FROZEN). Meriç approved the 9-decision lock review; the two lock-blockers were resolved with evidence: (1) cost semantics verified from research/full_universe_barrier_backtest.py lines 335-338/366-368 (0.55% = percentage points per round-trip position, subtracted from expectancy; NOT per-turnover, NOT per-leg); (2) entry/exit price convention completed (T0=scan_date, entry=export price field, forward path=T+1..T+5 daily OHLC from price_cache, fallback exit=T+5 close). Estimand audit (section 52a) PASS.
Change: Locked protocol. Primary estimand = Median(NC_i) over VALID (non-ambiguous) observations, NC_i = GrossExitReturn_i - Cost_i. Cost: PRIMARY 0.55% / STRESS 1.00% round-trip, no slippage double-count. Exit families finite and pre-locked: E0 hold-to-T+5 baseline; E1 fixed target +3/+5/+10%; E2 ATR trailing 1.5/2.0/3.0 (ATR from atr_pct_real at T0, trailing = highest close since entry minus k*ATR on each close); E3 partial (50% at +3%, remaining 50% at T+5 close, single round-trip cost). Same-day target/stop ambiguity -> observation EXCLUDED from that candidate's primary estimate (deliberate departure from prior stop-first convention; ambiguous count + excluded fraction mandatory). Temporal: early 40% / middle 20% buffer / late 40%, minimum evidence >=20 distinct days AND >=100 valid obs per primary period else INSUFFICIENT_TEMPORAL_EVIDENCE. Concentration: any single scan day contributing >25% of a candidate's net P&L -> CONCENTRATION_WARNING (blocks SUPPORTED). Multiple comparison: Holm family-wise. Verdict engine: CAPTURE_SUPPORTED only if all 9 gates pass (median net >0, Holm-adjusted CI excludes 0, survives primary cost, stress reported, early/late same sign, temporal minimum, no unresolved concentration, ambiguity within bound, independent verification PASS); plus CAPTURE_PARTIAL / CAPTURE_NOT_SUPPORTED / CAPTURE_UNSTABLE / INSUFFICIENT_DATA / INPUT_MISMATCH / PROTOCOL_DEVIATION / VERIFICATION_INCONCLUSIVE. seed=20260922, block-bootstrap B=2000 5-day blocks; random control NOT USED (locked justification: selection locked, exit rule is a deterministic function of price path, no feature to shuffle; block bootstrap supplies the sampling distribution). Terminology locked: MFE = opportunity envelope; exit return = rule-realized outcome; 'we captured X% of MFE' forbidden for the primary result. MFE reconciliation locked: resolved_pct_t5 of the locked input is the single MFE definition (n=34,762, mean 14.3424, median 4.1789); older summaries not merged. Price-cache audit locked: 2,047 symbols, cohort coverage 100% (34,762/34,762), OHLC sample 18,296 bars 0 invalid; missing future path -> unavailable, NO imputation; survivorship limitation recorded. Dedup tie-handling and the exact percentile function are pinned in the estimand audit (NS-1 definition-debt lesson).
Impact: No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. production_impact = NONE. No runner written yet; runner may now be written and run read-only per section 53 (runner -> code review -> dry run -> execution). H4 chain remains CLOSED/FROZEN; H4 results are NOT used as evidence for RX-CAPTURE-1's hypothesis.
Status: applied - Level A preregistration locked before runner execution.
Evidence: `reports/research_x_capture_1_preregistration_2026-09-22.md` (APPROVED/LOCKED) SHA-256 `d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e`; canonical export SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad`; cost-semantics source `research/full_universe_barrier_backtest.py` lines 335-338, 366-368.

---
[2026-09-22] - RESEARCH-X/RX-CAPTURE-1 capture & exit battery result (Level A)
Layer: Research / Governance
Level: A (read-only forensic research; production and locked OOS unchanged)
Context: The APPROVED/LOCKED RX-CAPTURE-1 preregistration was executed strictly as written on the canonical EOD-only export (n=34,762, 54 dates; input SHA verified) with price_cache forward paths (T+1..T+5). Selection LOCKED; exit = variable. Determinism confirmed (two byte-identical runs). seed=20260922, block-bootstrap B=2000 (5-day blocks), Holm family-wise over the candidate set. Same-day ambiguity -> EXCLUDE (locked).
Result (median net capture, primary cost 0.55%; stress 1.00% also reported): E0 hold-to-T+5 = -0.718pp (Holm p=0.176, CI contains 0) CAPTURE_NOT_SUPPORTED. E1 fixed-target +3% = +2.45pp median net, Holm p~0, early/late same sign, temporal minimum met, no concentration -> CAPTURE_SUPPORTED_PENDING_VERIFICATION. E1 +5% = +1.136pp median net, Holm p=0.028, same gates pass -> CAPTURE_SUPPORTED_PENDING_VERIFICATION. E1 +10% = -0.369pp CAPTURE_NOT_SUPPORTED. E2 ATR trailing 1.5/2.0/3.0 = -0.987 / -0.785 / -0.728pp, all CAPTURE_NOT_SUPPORTED; k1.5 and k2.0 carry concentration warnings (28.6% / 27.4% single-day share). E3 partial = -0.765pp CAPTURE_NOT_SUPPORTED, 35.3% (12,264/34,762) excluded as same-day ambiguous, concentration warning 39.4%.
Methodology findings (documented, not hidden): (1) MEDIAN DEGENERACY - E1_t3 and E1_t5 primary medians land almost exactly on the locked target net of cost because >50% of valid observations hit the fixed target on first touch; the block-bootstrap CI becomes degenerate (holm p~0). This is a real finding (the majority of selected rows do reach +3%/+5% quickly) but it means the median estimand overstates discriminating power for these two candidates; mean and tail behaviour (secondary) carry the actual risk information. (2) Baseline E0 held to horizon is median-negative after cost, consistent with prior evidence; selection quality is out of scope (selection LOCKED). (3) E3's large ambiguous share reflects the locked EXCLUDE convention.
Boundaries (unchanged): MFE = opportunity envelope, exit return = rule-realized outcome; the primary result is never phrased as 'we captured X% of MFE'. Screening/capture evidence is NOT a buy signal and NOT a production filter; any production exit rule is a separate Level B decision. The two SUPPORTED-PENDING candidates require independent verification (v2 section 30) before any final closure; their status does not authorize production. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. H4 chain remains CLOSED/FROZEN. production_impact = NONE.
Status: applied - Level A research-only result recorded; independent verification PENDING.
Evidence: preregistration `reports/research_x_capture_1_preregistration_2026-09-22.md` (APPROVED/LOCKED) SHA-256 `d0baa61834efe06efa30dc674aa76b34881e29a06c05a1ad70627fc2b6d5036e`; runner `research/research_x_capture_1_2026_09_22.py`; JSON `data/backtest_out/research_x_capture_1_2026-09-22.json` SHA-256 `c6ab1521577183a4c103ca51740ceafc99767cfe5f43f8e212c159cb0c96e73e`; report `reports/research_x_capture_1_2026-09-22.md` SHA-256 `3bcad0086dda80247dd908c3b536e1ae21573f4455028e0c62796e6eaea26b1c`; determinism confirmed (two byte-identical runs).

---
[2026-09-23] - RESEARCH-X/RX-CAPTURE-1 independent result verification (Level A)
Layer: Research / Governance
Level: A (read-only verification; NOT a new experiment; RX-CAPTURE-1 artifacts, verdicts and governance unchanged)
Context: Master Orchestrator v2 sections 30-32. The two CAPTURE_SUPPORTED_PENDING_VERIFICATION candidates (E1 +3%, E1 +5%) were verified with same locked input (SHA-verified) + same locked protocol + a DIFFERENT implementation path: csv module + dict dedup + sorted-list path traversal + statistics.median + ordinal-day T+1..T+5 boundary + numpy RandomState bootstrap, versus the locked runner (pandas + default_rng). The verifier was initially slow due to per-row cache reads; a cache memoization was added that does NOT change any logic or result (performance only), then run to completion.
Result: VERIFICATION_PASS (0 mismatches). E1_t3: median net primary +2.45pp, stress +2.0pp, first-touch hit share 61.5%, early=late=+2.45, same sign True, median_degenerates_to_target True (matches the documented degeneracy). E1_t5: median net primary +1.13587pp, stress +0.68587pp, hit share 42.9%, early +1.556 / late +0.117, same sign True, median_degenerates_to_target False. All deterministic primary quantities (evaluated n, median net primary/stress, early/late medians, temporal same-sign) matched the locked JSON exactly; the locked input SHA and locked JSON SHA were verified unchanged. The E1_t5 result is the more reliable of the two because its median is NOT degenerate (hit share <50%); the E1_t3 median is degenerate (hit share 61.5% > 50% collapses the median onto the target), consistent with the documented methodology finding.
Boundary (unchanged): VERIFICATION_PASS != production approval. This verification only answers "was the locked result computed correctly?"; it does NOT answer "should +3%/+5% exit be used in production" (a separate Level B governance/economic-validation question). No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. RX-CAPTURE-1 remains COMPLETED/LOCKED; E1_t3 and E1_t5 move from CAPTURE_SUPPORTED_PENDING_VERIFICATION to CAPTURE_SUPPORTED (independent verification PASS). H4 FROZEN. production_impact = NONE.
Status: applied - Level A verification recorded.
Evidence: verifier `research/rx_capture_1_independent_verification_2026_09_22.py`; verification JSON `data/backtest_out/rx_capture_1_independent_verification_2026-09-22.json` SHA-256 `135a6a97d5b25ba1c4f23d346c0541aad7d33fcb426cc4445033ae90ea7a6085`; locked RX-CAPTURE-1 JSON SHA-256 `c6ab1521577183a4c103ca51740ceafc99767cfe5f43f8e212c159cb0c96e73e` (verified unchanged); input SHA-256 `87541cc54eb7c360b865ca5df6141fcd84ddb089d5d461b6e40dda74d8b073ad` (verified).

---
[2026-09-23] - RESEARCH GOVERNANCE MASTER AUDIT (one-shot controller, Level A)
Layer: Governance / Research
Level: A (read-only end-to-end audit; no experiment rerun, no locked artifact modified, no production surface touched). Approved by Meric ("3 fazı da uçtan uca bitir"). Ran as Seçenek A (one-shot Level A audit; NOT a persistent repo tool).
Context: Meric's Research Governance Master Controller v1 was reviewed (independent assessment found the spine sound, 5 design clarifications flagged) and executed read-only over the repo via five independent audit threads: flag+lock/SHA, decision-log, overstatement, debt/provenance, production-impact.
Result: Program is pre-production and decision-ready. Three frozen/closed lines (H4, NS-1, RX-CAPTURE-1) all locked + independently verified; governance chain sound. No NEW unauthorized production change found; the 9-flag ON-vs-governance-OFF conflict is a KNOWN open debt (documented in meta_validation_audit_2026-09-08), not a new breach. User-facing/investor material is disciplined (no material overstatement; MFE vs capture separated; negative findings foregrounded; locked OOS transparent). Level B decisions now classifiable by readiness: B1 capture economic/robustness review = ACTIONS_READY; B2 flag governance reconciliation = INFRASTRUCTURE_GOVERNANCE; B4 future tuple persistence = INFRASTRUCTURE_GOVERNANCE; B3 (B2->B3) = WAITING_FOR_DATA (diversity unmet); B5 negative-screen production = BLOCKED (NO_SCREEN_SUPPORTED).
Findings (documented, not hidden): (1) two consolidator corrections to subagent output - RX-CAPTURE-1 was mis-reported as "not executed" due to a wrong filename search pattern (actual artifacts research_x_capture_1_* exist, executed, verified SHA c6ab152157...); the flag conflict was mis-presented as a new critical finding when it is a previously documented open debt. (2) Systematic kayit-boslugu: 9+ completed work items lack decision-log entries (recurring process weakness). (3) Open data/provenance debts ranked: spread/slippage coverage 0% (CRITICAL, blocks B1 economic gate), production tuple not persisted (CRITICAL, blocks B4), V0 correlation 3 values (HIGH, root-caused as MFE!=c2c, needs single-number reconciliation), PIT sector 8.31%, corporate-action 485 symbols, multi-timeframe OHLCV unreconstructable, decision-log 08-12 gaps. (4) Two previously flagged "debts" (performance-card n 5206/5216; MFE 46080/46581) are NOT debts - intentional separate studies, properly documented in pitch spec; dedup NVDA semantics confirmed consistent.
Impact: production_impact = NONE. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. No new experiment started. H4 FROZEN. All closed lines remain closed. Every Level B -> C transition still requires human authorization.
Status: applied - Level A audit recorded.
Evidence: report `reports/research_governance_audit_2026-09-23.md` SHA-256 `dfb3071c2e46cc6734c555d30828e1178d7ea6481d4e5cbc177afbe6572f7f61`.

---
[2026-09-23] — DETECT-SECRETS FALSE-POSITIVE BASELINE UPDATE
Layer: Security / Tooling
Level: B (configuration change; human review and approval pending)
Context: The staged-file secret hook reported 13 high-entropy hex findings across eight research/report files. Inspection identified them as dataset SHA-256 fingerprints, preregistration/locked-artifact checksums, or short artifact identifiers; the dataset fingerprint was independently matched to the actual CSV.
Change: `.secrets.baseline` records only those exact findings. No detector, plugin, threshold, exclusion, or security rule was changed.
Impact: The exact known checksums no longer trigger false positives; other unmatched findings remain subject to the configured hook. No production behavior or data changed.
Status: pending - human review/approval required.

---
[2026-09-23] - Research Governance Controller spec v0.2 locked (Level B)
Layer: Governance / Research process authority
Level: B. Meric approved on 2026-09-23 ("lock"). This records adoption of the controller SPEC as the governing design for a READ-ONLY research governance controller. This lock authorizes the spec only; it does NOT create any tool/script/state file, does NOT start any research line, does NOT change production, and does NOT make the controller a decision maker or a governance authority (that is a separate, higher decision, explicitly out of scope).
Context: Following the Research Governance Master Audit (2026-09-23), Meric ran an independent spec audit of the v0.1 draft. Verdict: architecture direction PASS but NOT yet lock-ready; seven revisions required. All were applied in v0.2: (1) authority precedence - registry is a DERIVED VIEW, never authoritative over locked evidence (scientific truth = locked artifacts/verification; governance truth = decision-log; derived state = controller, lowest); (2) conflict semantics - controller RECONCILES, never resolves (CONFLICT/RESOLUTION_REQUIRED/AUTHORITY_ACTION=NONE); (3) lock provenance - explicit locked_at/generated_at/lock_sha, never file mtime; (4) state decomposition - five separate dimensions (lifecycle/scientific_verdict/verification/governance/production/decision), never collapsed; (5) STATE_PERMITTED_ACTIONS replaces NEXT_ALLOWED_ACTION (no RECOMMEND); (6) scope split - FULL-STATE lines (H4/NS-1/RX-CAPTURE-1) vs POINTER-ONLY historical lines, known_status != controller_verified_status; (7) decision classification - G1/G2 governance (approval required) vs I1-I4 implementation defaults (overridable, no approval needed). Two invariants hardened: absence semantics (NOT_FOUND != NOT_PERFORMED != FALSE; unknown -> UNKNOWN-INSUFFICIENT_PROVENANCE, never a negative finding) and a 10-point controller invariant list. Locked design sentence: controller produces state, not authority; reconciles evidence, never resolves conflict; never assumes historical provenance, only preserves it.
Change: Adopted docs/governance/research_governance_controller_spec_v1.md as APPROVED/LOCKED Level B spec. Implementation (a read-only reconciliation/provenance/integrity tool over the locked lines) is a separate subsequent step requiring its own build; the spec itself changes nothing at runtime.
Impact: production_impact = NONE. No score, ranking, scanner, configuration, database, scheduler, publication, or user-facing surface changed. H4 FROZEN. NS-1 and RX-CAPTURE-1 remain CLOSED/VERIFIED and are never rerun by the controller. Governance is append-only; no prior record overwritten.
Status: applied - Level B spec locked; implementation pending a separate go-ahead.
Evidence: `docs/governance/research_governance_controller_spec_v1.md` (APPROVED/LOCKED) SHA-256 `a3ea327b47f489f59867cf463b2efd2b0c59c9e0923a49ecdb27836a7e0bb19b`.

---
[2026-09-23] - Research Governance Controller v0.2 READ-ONLY implementation (Level B, spec-authorized)
Layer: Governance / Research process tooling
Level: B. Authorized by the APPROVED/LOCKED spec `docs/governance/research_governance_controller_spec_v1.md` (SHA a3ea327b..., locked 2026-09-23). This entry records the IMPLEMENTATION of the READ-ONLY controller; the spec lock itself authorized the design, and implementation is the separate step the spec explicitly allows (spec section: implementation is a separate step).
Change: Added `scripts/research_governance_controller.py` — a READ-ONLY CLI that derives research-line state from on-disk artifacts plus decision-log, never from hardcoded values and never from agent observation. Scope per locked spec: FULL-STATE lines (H4A/H4B/H4C/H4D-definition/H4D-measure, NS-1, RX-CAPTURE-1) are modeled and verified against artifacts; historical lines are POINTER-ONLY (known_status, never controller_verified). Implements the locked invariants: UNKNOWN never becomes FALSE; NOT_FOUND never equals NOT_PERFORMED; verdicts are read from artifacts (never invented); conflicts are surfaced (CONFLICT/RESOLUTION_REQUIRED/AUTHORITY_ACTION=NONE), never silently resolved; H4D-definition is reported DEFINITION_LOCKED by design (definition-only, no result JSON). Lock-before-result is assessed from explicit governance evidence, never file mtime.
Verification: compiles; runs deterministically (JSON output byte-stable modulo timestamp across two runs); produces a read-only report plus a derived PROGRAM_STATE block. No production code, score, ranking, flag, scanner, scheduler, database, or user-facing surface changed. The controller is NOT a decision maker and NOT a governance authority (that remains a separate, higher decision, out of scope). H4 FROZEN; all closed lines remain closed. production_impact = NONE.
Status: applied - Level B tool implementation recorded.
Evidence: `scripts/research_governance_controller.py`; locked spec `docs/governance/research_governance_controller_spec_v1.md` SHA-256 `a3ea327b47f489f59867cf463b2efd2b0c59c9e0923a49ecdb27836a7e0bb19b`.

---
[2026-09-23] - Research Governance Controller self-audit / regression tests (Level A)
Layer: Governance / Research process tooling
Level: A (read-only tests; temporary fixtures only; real locked artifacts NOT touched). Follow-up to the controller implementation; this hardens the tool and does NOT produce scientific findings.
Context: Meric's review corrected the claim "all invariants proven" to "invariants observed working in current execution; future protection requires automated regression tests". This entry adds that regression coverage before any B1/B2/B4 decision is opened.
Result: 7/7 tests PASS. Invariant coverage: (1) UNKNOWN never becomes FALSE/NOT_SUPPORTED/FAILED when verdict is absent; (2) NOT_FOUND never equals NOT_PERFORMED (lifecycle UNKNOWN, missing slots reported, no fabricated negative finding); (3) conflict is surfaced as CONFLICT/RESOLUTION_REQUIRED/AUTHORITY_ACTION=NONE and never silently resolved; (4) scientific verdict is read from the artifact, never invented; (5) CAPTURE_SUPPORTED never becomes production authorization (production_impact stays NONE); (6) H4D-definition is DEFINITION_LOCKED (definition-only, result_artifact NONE by design), not UNKNOWN; (7) determinism (two runs identical modulo timestamp). Real- artifact checks in tests 5-6 confirm the live RX-CAPTURE-1 and H4D-definition states.
Impact: production_impact = NONE. No research line rerun, reopened, or reinterpreted; H4 FROZEN; NS-1 and RX-CAPTURE-1 unchanged. Controller status is now IMPLEMENTED / READ-ONLY / SPEC-CONFORMANT ON VERIFIED CASES / REGRESSION COVERAGE = PRESENT. The controller is still NOT a decision maker and NOT a governance authority.
Status: applied - Level A regression coverage recorded.
Evidence: `tests/test_research_governance_controller.py` (7 tests, all passing); controller `scripts/research_governance_controller.py`; locked spec SHA-256 `a3ea327b47f489f59867cf463b2efd2b0c59c9e0923a49ecdb27836a7e0bb19b`.

---
[2026-09-23] - PROGRAM_STATE validation (controller cross-check, Level A)
Layer: Governance / Research process tooling
Level: A (read-only cross-check; no artifact modified, no experiment rerun)
Context: After controller self-audit (7/7 regression PASS), the controller-derived PROGRAM_STATE was validated against the locked artifacts themselves before any B1/B2/B4 decision.
Result: 9/9 PASS. Controller state matches locked artifacts: NS-1 overall=NO_SCREEN_SUPPORTED + verification=VERIFICATION_PASS; RX-CAPTURE-1 E1_t3/E1_t5=CAPTURE_SUPPORTED, E0=CAPTURE_NOT_SUPPORTED, verification=VERIFICATION_PASS; H4C=INFORMATION_LOSS_NOT_SUPPORTED; H4A=COMPRESSION_SUPPORTED; production_impact=NONE across all result artifacts. The controller's derived state is consistent with the authoritative locked evidence; no conflict, no fabrication, no production change.
Status: applied - Level A validation recorded.
Evidence: controller `scripts/research_governance_controller.py`; locked artifacts under `data/backtest_out/` (SHA references in prior entries).

---
[2026-09-23] - RX-CAPTURE-1-ECON economic and robustness preregistration draft (Level B, pending)
Layer: Governance / Research process
Level: B. This is a Level B decision, awaiting Meric approval. The draft is recorded for review only and is not locked.
Change: Added `reports/research_x_capture_1_economic_review_preregistration_2026-09-23.md` as a new economic/robustness evaluation line for the already closed and independently verified RX-CAPTURE-1 result. The proposed line covers cost/slippage sensitivity, temporal robustness, liquidity/ capacity measurability, and tail behavior; it does not reopen RX-CAPTURE-1, alter H4, define a production exit rule, or authorize a runner.
Impact: production_impact = NONE. No scanner, score, ranking, configuration, database, scheduler, publication, or user-facing surface changed.
Status: pending - Level B draft awaiting approval; no execution or production change.
Evidence: `reports/research_x_capture_1_economic_review_preregistration_2026-09-23.md` (v0.1-DRAFT).
