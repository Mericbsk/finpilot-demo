# FINPILOT — TARAMA HATTI PERFORMANS DENETİMİ
## MASTER AUDIT PROMPT v1.0

**Tarih:** 2026-09-21
**Çalışma tipi:** READ-ONLY / ÖLÇÜM-ÖNCELİKLİ / FORENSIC
**Governance:** Level A. Üretim kodu, `.env`, flag, cache, scheduler, DB değişikliği YOK.
**Amaç:** Tarama süresinin NEREYE gittiğini tahminle değil ölçümle belirlemek ve darboğazları etki sırasına dizmek.

---

# 0. TEMEL PRENSİP

Bu bir optimizasyon çalışması **değildir**. Bu bir **ölçüm** çalışmasıdır.

> Hiçbir satır kod hızlandırılmadan önce, o satırın toplam süredeki payı ÖLÇÜLMÜŞ olmalıdır.

Bu programda daha önce iki kez, ölçülmeden yapılan "iyileştirme" tahmini yanlış çıktı (composite reverse-ranking artefaktı; "felaket-alt-kümesi" mean-artefaktı). Performans tarafında aynı hatayı yapmamak için kural:

**ÖLÇÜLMEMİŞ DARBOĞAZ = DARBOĞAZ DEĞİL, HİPOTEZ.**

---

# 1. ZATEN BİLİNEN (yeniden türetme, SABİT bağlam olarak al)

2026-09-14 teşhisinde ölçülmüş ve doğrulanmıştır:

| Bulgu | Kanıt |
|---|---|
| 200 sembol, `yf_fallback=0` → **50-64 sn** | `data/distribution/scan_timing.jsonl`, 84 gerçek tarama |
| 200 sembol, `yf_fallback≈150` → **420-534 sn** | aynı kaynak |
| Fallback başına ek maliyet ≈ **2.5 sn/sembol** | yukarıdaki iki satırın farkı |
| `alpaca_miss` her satırda aynı desen: 15m/1h'te onlarca, **1d'de ~0** | aynı kaynak |
| Kök neden: `feed="iex"` **koda gömülü** (`scanner/data_fetcher.py:740`) | kod okuması |
| 15m/1h yalnızca `momentum_ratio` + `alignment_ratio` için gerekli | `scanner/evaluate.py` |
| `enrich_s` ≈ 0.0 — **skorlama darboğaz DEĞİL** | timing log, tüm satırlar |
| EODHD bar katmanı eklendi, **bayrak kapalı, doğrulanmadı** | decision-log 2026-09-14 |

Bunları yeniden ölçmeye gerek yok. Denetim bunların **ÜSTÜNE** çıkmalıdır.

---

# 2. DENETİMİN CEVAPLAMASI GEREKEN ANA SORU

> **Tam evren taramasının duvar-saati süresi, aşama aşama nereye gidiyor; her aşamanın toplam içindeki YÜZDE payı nedir; ve hangi aşamalar ölçülemiyor?**

Alt sorular:

1. Ölçülen `total_s` gerçekten taramanın tamamını kapsıyor mu, yoksa bir kısmı ölçüm penceresinin **dışında** mı kalıyor?
2. Her aşamanın payı yüzde kaç? (Amdahl: %5'lik bir aşamayı sıfırlamak en fazla %5 kazandırır.)
3. Süre **ağ bekleme**, **CPU hesap**, **disk I/O**, yoksa **kilit/serileşme** mi?
4. Aynı girdiyle tekrarlanan taramalar arasındaki 10× varyansın kaynağı ne?
5. Soğuk cache ile sıcak cache arasındaki fark ne?
6. Paralellik gerçekten paralel mi, yoksa bir yerde serileşiyor mu?
7. Hangi aşamalar hiç enstrümante edilmemiş?

---

# 3. ÖLÇÜM ETİKETLEME (ZORUNLU)

Her sayı için kaynak etiketi:

```
MEASURED   — bu denetimde doğrudan ölçüldü (timer/log/profil çıktısı)
LOGGED     — mevcut scan_timing.jsonl'den okundu (geçmiş ölçüm)
DERIVED    — ölçülen iki sayıdan aritmetikle türetildi (formülü yazılacak)
ESTIMATED  — ekstrapolasyon; varsayımı AÇIKÇA yazılacak
UNKNOWN    — ölçülemedi; tahmin YAZILMAYACAK
```

Etiketsiz hiçbir sayı rapora girmez. "Muhtemelen", "büyük ihtimalle", "genelde" gibi ifadeler sayı yerine geçmez.

---

# 4. PART 0 — FİZİBİLİTE KAPISI (atlanamaz)

Ölçüme başlamadan önce, ortamın neyi ölçebildiği tespit edilip tabloya yazılır:

| Yetenek | Gerekli | Mevcut mu | Yoksa sonucu |
|---|---|---|---|
| Ağ erişimi (Alpaca/EODHD/yfinance) | Canlı tarama ölçümü | ? | Canlı ölçüm YAPILAMAZ → yalnız log analizi |
| Python çalıştırma | Profil/timer | ? | Hiçbir yeni ölçüm yapılamaz |
| `cProfile` / `time.perf_counter` | CPU profili | ? | CPU/ağ ayrımı yapılamaz |
| `psutil` veya eşdeğeri | CPU/RAM izleme | ? | Kaynak darboğazı UNKNOWN kalır |
| Disk yazma (`data/`) | Log toplama | ? | Sonuç kalıcılaştırılamaz |

**Kapı kuralı:** Bir yetenek yoksa, ona dayanan tüm bulgular `UNKNOWN` olarak işaretlenir. Eksik yetenek "yaklaşık" değerle doldurulmaz.

> Not: Bu ortamda ağ erişimi ve Linux çalışma alanı geçmişte birden çok kez kullanılamaz durumdaydı. Kapıyı her koşuda YENİDEN kontrol et; önceki turun sonucunu varsayma.

---

# 5. BİRİNCİ ADIM — ZATEN VAR OLAN ENSTRÜMANTASYONU AÇ

**Kritik bulgu (2026-09-21):** `scanner/performance.py` içinde tam bir aşama-zamanlama sistemi **zaten yazılmış** ve 12 noktada çağrılıyor. Ancak `FINPILOT_SCAN_STAGE_TIMING` varsayılan `"0"` ve **mevcut 84 tarama kaydının hiçbirinde `stage_timing` alanı dolu değil.**

> Yani: ölçüm aleti kurulmuş, hiç açılmamış.

Denetimin ilk eylemi yeni kod yazmak değil, **bu bayrağı açıp bir tarama koşmaktır.**

Mevcut timer noktaları (kod-doğrulanmış):

| Aşama adı | Dosya:satır | path etiketi |
|---|---|---|
| `prefetch.alpaca` | `data_fetcher.py:1129` | alpaca |
| `prefetch.repair` | `data_fetcher.py:1132` | alpaca_repair |
| `prefetch.bulk_yfinance` | `data_fetcher.py:1155` | bulk_yfinance |
| `prefetch.resample_4h` | `data_fetcher.py:1167` | derived |
| `prefetch.symbol_yfinance` | `data_fetcher.py:1204` | symbol_yfinance |
| `fetch.request` | `data_fetcher.py:813, 988` | bulk_yfinance, **eodhd** |
| `fetch.parse` | `data_fetcher.py:838` | bulk_yfinance |
| `retry.attempt` / `retry.backoff` | `data_fetcher.py:190, 205` | alpaca |
| `rate_limit.wait` | `data_fetcher.py:321` | yfinance |
| `indicator.compute` | `indicators.py:133` | pandas |
| `evaluation.symbol` | `evaluate.py:930` | prefetched |

---

# 6. BİLİNEN ENSTRÜMANTASYON BOŞLUKLARI (denetimin doğrulaması gereken)

Kod okumasıyla tespit edilen, **ölçüm penceresinin dışında kalan** aşamalar:

### 6.1 KRİTİK — Kalıcılaştırma fazı hiç ölçülmüyor

`api/routers/scan.py` içinde sıra şu:

```
_t_scoring_done = time.perf_counter()     # <-- ÖLÇÜM BURADA BİTİYOR
_timing = {... "total_s": _t_scoring_done - _t_start ...}
_append_scan_timing_log(...)
_persist_shortlist(out)                   # <-- ÖLÇÜLMÜYOR
_persist_shadow_ledger(out, ...)          # <-- ÖLÇÜLMÜYOR
_auto_add_watchlist(out, ...)             # <-- ÖLÇÜLMÜYOR
_persist_distribution_export(out, ...)    # <-- ÖLÇÜLMÜYOR
```

→ **Raporlanan `total_s`, taramanın gerçek duvar-saati süresi DEĞİL.** Dört kalıcılaştırma çağrısı tamamen ölçüm dışında. Denetim bunların payını ölçmelidir. Bu pay büyükse, şimdiye kadarki tüm "tarama süresi" konuşması eksik bir sayı üzerinden yapılmış demektir.

### 6.2 Ölçülmeyen diğer noktalar (doğrulanacak)

- Evren listesi yükleme (`distribution/jobs.py::_load_universe`, `stock_presets.json`)
- `_repair_partial_alpaca_result` içindeki **timeframe döngüsü** (yalnız dış sarmalayıcı ölçülüyor)
- EODHD **sembol başına** çağrı (`_eodhd_one`) — yalnız toplu sarmalayıcı ölçülüyor
- Evaluate fazının ThreadPoolExecutor'ı bir bütün olarak (yalnız sembol başına ölçülüyor)
- `_enrich_results` içindeki DRL cache yükleme
- Batch'ler arası boşluk (API çağrıları arası duvar-saati)

---

# 7. AŞAMA-BAZLI DENETİM PROTOKOLÜ

Her aşama için şu tablo doldurulur:

```
AŞAMA            : <ad>
ÖLÇÜM KAYNAĞI    : MEASURED / LOGGED / DERIVED / ESTIMATED / UNKNOWN
SÜRE (medyan)    : <sn>
SÜRE (p95)       : <sn>
TOPLAMDAKİ PAY   : <%>
DARBOĞAZ TİPİ    : ağ-bekleme / CPU / disk-I/O / kilit-serileşme / UNKNOWN
SEMBOL BAŞINA MI : evet (doğrusal büyür) / hayır (sabit maliyet)
TEORİK TAVAN     : bu aşama SIFIRLANSA toplam kazanç = <%>
```

**Son satır zorunludur.** Amdahl disiplini: bir aşamanın payı %8 ise, o aşamayı mükemmel hale getirmek bile %8'den fazla kazandıramaz. Bu satır yazılmadan hiçbir optimizasyon önerilemez.

---

# 8. VARYANS SORUŞTURMASI (zorunlu — atlanamaz)

Mevcut logda aynı sembol sayısıyla **10× varyans** var (50 sn ↔ 534 sn). Bu, tek bir ölçümün hiçbir şey kanıtlamadığı anlamına gelir.

Zorunlu kurallar:

1. **Tek koşu = kanıt değil.** Her konfigürasyon en az **5 kez** koşulur; medyan + p95 raporlanır, ortalama değil.
2. Koşular arasında **cache durumu** kaydedilir: soğuk / sıcak / bilinmiyor.
3. **Piyasa saati** kaydedilir. `data_fetcher.py:116` içinde `_market_aware_ttl()` var — cache TTL'i piyasa saatine göre değişiyor, dolayısıyla aynı kod farklı saatte farklı davranır.
4. Varyansın kaynağı ayrıştırılmalı: `yf_fallback` sayısı mı, ağ dalgalanması mı, cache durumu mu, rate-limit kuyruğu mu?
5. Varyans açıklanamıyorsa **UNKNOWN** yazılır — "muhtemelen ağ" yazılmaz.

---

# 9. SERİLEŞME SORUŞTURMASI

Kodda iç içe iki ThreadPool var (`prefetch` max_workers=10, `evaluate` max_workers=min(32,...)) **ve** bir token-bucket rate limiter (`rate_limit.wait`, path=yfinance).

Sorulacaklar:

1. `rate_limit.wait` toplamda kaç saniye bekliyor? (Bu **saf serileşme**dir — paralellik ekleyerek çözülemez.)
2. Worker sayısını artırmak gerçekten hızlandırıyor mu, yoksa rate limiter aynı duvara mı dayanıyor?
3. GIL nedeniyle `indicator.compute` (pandas) fazı paralelde gerçekten hızlanıyor mu?
4. Alpaca `retry.backoff` toplamı ne kadar? Üstel geri çekilme sessizce dakikalar yiyor olabilir.

**Not:** `rate_limit.wait` ve `retry.backoff` toplamları, "paralelleştirerek hızlandıralım" önerisinin geçerli olup olmadığını belirler. Bu iki sayı ölçülmeden paralellik önerisi yapılamaz.

---

# 10. ÖLÇEKLEME MODELİ

Tam evren (~1.900 sembol) için ekstrapolasyon **formülü yazılarak** yapılır:

```
toplam_süre ≈ sabit_maliyet
            + (sembol_sayısı × sembol_başına_maliyet)
            + (fallback_sembol_sayısı × fallback_başına_ek_maliyet)
```

Her terim ayrı ölçülür. Ekstrapolasyon `ESTIMATED` etiketlidir ve varsayımları açık yazılır (örn. "fallback oranı 200-sembol batch'lerdeki gözlenen orana eşit varsayıldı").

**Doğrusal olmayan etkiler ayrıca aranır:** batch boyutu büyüdükçe sembol başına maliyet artıyor mu (bellek, cache tahliyesi, API sayfalama)? `_limit = max(10_000, len(symbols) * 250)` gibi boyuta bağlı parametreler var — bunların etkisi ölçülmeli.

---

# 11. KARAR AĞACI

```
Durum A: Kalıcılaştırma fazı toplamın >%15'i
  → BULGU: ölçüm penceresi hatalı; "tarama süresi" tanımı düzeltilmeli
  → Bu, veri çekme optimizasyonundan ÖNCE gelir

Durum B: prefetch.repair / symbol_yfinance toplamın >%50'si
  → BULGU: 2026-09-14 teşhisi DOĞRULANDI, veri kaynağı birincil darboğaz
  → EODHD/huni/cache yolları geçerli

Durum C: rate_limit.wait + retry.backoff toplamın >%25'i
  → BULGU: darboğaz serileşme, paralellik ÇÖZMEZ
  → Sağlayıcı/kota kararı gerekir

Durum D: indicator.compute + evaluation.symbol toplamın >%30'u
  → BULGU: darboğaz CPU; veri kaynağı değiştirmek işe yaramaz
  → 2026-09-14 teşhisi EKSİK demektir

Durum E: Hiçbir aşama >%25 ve süre yine yüksek
  → BULGU: darboğaz dağıtık; tek nokta düzeltmesi yetmez
  → Mimari değişiklik konuşulur

Durum F: Ölçüm yapılamadı (fizibilite kapısı kapalı)
  → PRIMARY STATUS = NOT MEASURED
  → Hiçbir darboğaz iddiası yapılmaz. Tahmin edilmez.
```

---

# 12. KESİNLİKLE YAPILMAYACAKLAR

- Ölçmeden optimizasyon önerme
- Üretim kodu değiştirme (denetim salt-okunur)
- `.env` değiştirme — **istisna yok**; `FINPILOT_SCAN_STAGE_TIMING` dahil, bayrak açma işlemi **kullanıcı tarafından** yapılır, ajan tarafından değil
- Flag açma/kapatma
- Cache/DB/scheduler dokunma
- Tek koşuyu kanıt sayma
- Ortalamayı medyan yerine kullanma
- "Şu satır yavaş olmalı" tipi kod-okuma sezgisini ölçüm yerine koyma
- Skor formülünü/sinyali değiştirmeyi bu denetim kapsamında önerme (ayrı iş, ayrı karar)
- Mevcut governance kararlarını (flag DEFERRED, fade CONFIRMATORY_CANDIDATE, attention map VALIDATED-DESCRIPTIVE, catalyst UNVALIDATED) bu denetimle değiştirme

---

# 13. ZORUNLU ÇIKTILAR

| Dosya | İçerik |
|---|---|
| `research/scan_performance_audit_<YYYY_MM_DD>.py` | Log analizi + (mümkünse) canlı ölçüm scripti |
| `reports/scan_performance_audit_<YYYY-MM-DD>.md` | Ana rapor (Bölüm 14 formatı) |
| `reports/scan_stage_breakdown_<YYYY-MM-DD>.csv` | aşama × medyan × p95 × pay% × tip × teorik tavan |
| `reports/scan_variance_analysis_<YYYY-MM-DD>.csv` | koşu × konfigürasyon × cache durumu × süre × fallback sayısı |
| `reports/scan_instrumentation_gaps_<YYYY-MM-DD>.csv` | ölçülmeyen aşamalar + neden + nasıl ölçülür |

---

# 14. RAPOR FORMATI

1. Executive Summary (≤ 12 satır)
2. Fizibilite Kapısı sonucu (Bölüm 4 tablosu)
3. Enstrümantasyon durumu — neyin açık/kapalı olduğu
4. Ölçüm penceresi doğrulaması — `total_s` gerçekten neyi kapsıyor
5. Aşama kırılımı (yüzde paylarla, Amdahl tavanlarıyla)
6. Darboğaz tipi ayrımı (ağ / CPU / disk / serileşme)
7. Varyans analizi
8. Serileşme analizi (`rate_limit.wait`, `retry.backoff`)
9. Ölçekleme modeli + formül + varsayımlar
10. Enstrümantasyon boşlukları
11. Karar ağacı sonucu (Bölüm 11'den hangi durum)
12. Darboğazlar — ETKİ SIRASINA göre, her biri teorik tavanıyla
13. **WHAT WE MEASURED** — yalnız ölçülenler
14. **WHAT WE COULD NOT MEASURE** — ve nedeni
15. **WHAT THE MEASUREMENT CONTRADICTS** — önceki varsayımlardan çürüyenler
16. Önerilen sonraki adım — TEK tane, ölçüme dayalı, teorik tavanı yazılı
17. PROPOSED GOVERNANCE ACTION (varsa; uygulanmaz, yalnız önerilir)

---

# 15. BAŞARI KRİTERİ

Denetim ancak şu cümle **ölçülmüş sayılarla** tamamlanabildiğinde başarılıdır:

> "Tam evren taramasının süresi şu aşamalara şu yüzdelerle dağılıyor: ___. En büyük tekil darboğaz ___ ve payı %___. Bu aşama tamamen sıfırlansa toplam kazanç en fazla %___ olur. Ölçemediğimiz kısım ___ ve bu toplam süreyi en fazla %___ etkileyebilir."

Bu cümle doldurulamıyorsa denetim **başarısızdır** ve sonucu şudur:

> **PRIMARY STATUS = NOT MEASURED.** Tahmin yok.

---

# 16. GOVERNANCE

Denetim sonunda otomatik hiçbir değişiklik yapılmaz. Gerekli görülen her eylem şu başlık altında **önerilir**:

```
PROPOSED PERFORMANCE ACTION
  Ne          : <değişiklik>
  Gerekçe     : <ölçülmüş sayı + etiketi>
  Teorik tavan: <%>
  Risk        : <sinyali/veriyi etkiler mi>
  Seviye      : A / B / C
```

Sinyali veya skoru etkileyen hiçbir öneri bu denetimden çıkamaz — performans ile sinyal ayrı karar hatlarıdır. `alignment_ratio`/`momentum_ratio`'yu kaldırmak bir **performans** eylemi gibi görünür ama bir **sinyal** kararıdır ve bu denetimin yetkisi dışındadır.

---

# 17. SON İLKE

### Ölçüm > sezgi
### Medyan > ortalama
### Tekrarlanan koşu > tek koşu
### Yüzde pay > mutlak saniye
### Amdahl tavanı > "bu hızlanır" iddiası
### "Ölçemedik" > uydurulmuş sayı

**Hızlı olduğunu sandığın şeyi değil, ölçtüğün şeyi hızlandır.**

---

# END OF MASTER PROMPT
