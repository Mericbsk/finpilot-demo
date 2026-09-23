# Negatif Cache — Tasarım Spesifikasyonu

**Tarih:** 2026-09-22 · **Seviye:** B (production scanner) · **Durum:** ONAY BEKLİYOR — kod yazılmadı

---

## 1. Problem

Ölçülmüş (2026-09-22, üretim 200 sembol):

| Timeframe | Hiçbir sağlayıcının vermediği sembol |
|---|---|
| 15m | 51 |
| 1h | 30 |
| 1d | 8 |
| **Toplam** | **89 slot** |

Sistem **her taramada** bu 89 slot için istek yapıyor, ~1.31 sn/slot ödüyor ve *"veri yok"* cevabını yeniden keşfediyor.

**~117 sn/tarama, tamamen boşa** (89 × 1.31, ESTIMATED).

Bu bir sağlayıcı sorunu değil — EODHD'ye geçsek de o 89 slot yine boş döner. Dolayısıyla **sağlayıcı kararından bağımsız** ve onunla birlikte değil, ondan **önce** çözülmeli.

---

## 2. Temel kural — bu tasarımın can damarı

> **Yalnızca KESİN "veri yok" sonuçları cache'lenir. Geçici hatalar ASLA cache'lenmez.**

Bu ayrım yapılmazsa cache, var olan veriyi görünmez kılar — ki bu yavaşlıktan çok daha kötü bir arızadır.

### Cache'lenebilir (DEFINITIVE)

Sağlayıcı **başarılı yanıt verdi** ama veri yetersiz:

- İstek HTTP 200 döndü, gövde ayrıştırıldı, bar sayısı `MIN_HISTORY_BARS[interval]` altında
- Toplu indirmede genel yanıt **dolu** geldi ama o sembol sonuç kümesinde **yok** (ör. `yf.download` MultiIndex'inde ticker yok) → o sağlayıcıda o sembol için veri yok demektir

### ASLA cache'lenmez (TRANSIENT)

- Timeout (bağlantı veya okuma)
- Rate-limit (429) veya kota aşımı (402/403)
- **HTTP 404** — aşağıdaki gerekçeyle
- Herhangi bir HTTP 5xx
- Bağlantı/DNS/TLS hatası
- Exception fırlatan her yol
- **Toplu çağrının tamamının boş/başarısız dönmesi** → hiçbir sembol için sonuç çıkarılamaz
- Sağlayıcı devre dışı (bayrakla kapatılmış)

**Belirsizse cache'leme.** Varsayılan davranış her zaman "tekrar sor" tarafında olmalı.

### HTTP 404 — neden TRANSIENT sayılıyor (2026-09-22 eklendi)

404 ilk bakışta "kesin" görünür: EODHD bilinmeyen sembol için 404 döner. Ama **kota tükenmesi, konfigürasyon hatası veya endpoint değişikliği de 404 üretebilir.**

Gözlenen olay (2026-09-22): aynı gün, aynı 200 sembolle yapılan ilk ölçüm EODHD'de 148/200 ve 166/200 kapsam verdi; saatler sonraki koşu **toplu 404** döndürdü. Sağlayıcı davranışı kararlı değil ve 404'ün nedeni ayırt edilemedi.

Eğer 404 "kesin" sayılsaydı, o ikinci koşu **tüm evreni "verisi yok" diye cache'lerdi.** Tek bir kota olayı, kalıcı ve sessiz bir veri kaybına dönüşürdü.

**Kural:** 404 yalnızca başka bir sağlayıcı **aynı sembol/timeframe için başarılı yanıt verdiyse** ve o yanıt da yetersizse kesin sayılabilir. Tek başına asla.

### KOŞUL 2 (kilitlendi) — "toplu yanıt dolu" kesin tanımı

Negatif kayıt yazılabilmesi için **üçü birden** sağlanmalı:

1. Sağlayıcı çağrısı **exception fırlatmadan** döndü
2. Yanıt nesnesi **boş değil** (yf: `raw` DataFrame dolu; Alpaca: `BarSet.df` dolu)
3. **Ayrıştırma exception'sız tamamlandı**

Bu üçü sağlanırsa, yanıt yapısında **bulunmayan** sembol için "o sağlayıcıda veri yok" **kesin** sayılır. Yanıt tamamen boşsa → hiçbir sembol hakkında çıkarım yok → **sıfır yazma**.

#### Değerlendirilip REDDEDİLEN alternatif: kapsama oranı eşiği

"İstenen sembollerin %50'sinden azı döndüyse yanıtı şüpheli say" kuralı düşünüldü ve **reddedildi**:

Repair yolunda `_bulk_yf_download` yalnızca **Alpaca'nın kaçırdığı** sembollerle çağrılıyor — yani zaten verisi olmama ihtimali yüksek bir küme. Orada düşük dönüş oranı **normaldir, arıza değil**. Oran eşiği koymak özelliğin ana kullanım senaryosunu bozardı.

Yerine: oran **gözlem alanı olarak loglanır** (`negcache_write_ratio`), karar mekanizması yapılmaz. Patolojik görünürse sonra kural eklenir — önce gözle, sonra kısıtla.

Kısmi/bozulmuş yanıt riski için asıl koruma **canary metriğidir** (Bölüm 4 + 7): tahmin etmeye çalışmak yerine ampirik olarak yakalar.

---

## 3. Anahtar ve kapsam

```
key = (provider, symbol, timeframe)
```

**Sağlayıcı-başına olması şart.** Alpaca'nın vermediğini EODHD verebilir (ölçüldü: EODHD 15m'de 58, 1h'te 63 ek sembol). Global bir cache, EODHD'yi haksız yere atlardı.

---

## 4. TTL ve tazeleme

| Kural | Değer | Gerekçe |
|---|---|---|
| Birincil geçerlilik | **İşlem günü** | Bugün 15m barı olmayan sembol yarın olabilir (yeni listelenen, düşük hacimli gün) |
| Mutlak üst sınır | **24 saat** | Seans hesabı hatalı olsa bile sonsuza kadar tutmasın |
| Canary yeniden-deneme | **%5 rastgele** | TTL içinde bile küçük bir örneklem yeniden sorulur — veri belirmişse erken yakalanır |

Canary maddesi ucuz sigorta: 89 slot'un ~4'ü her taramada yine sorulur (~5 sn), karşılığında "cache gerçeği yansıtıyor mu" sorusu sürekli test edilmiş olur.

### KOŞUL 1 (kilitlendi) — canary seçimi enjekte edilebilir olmalı

Seçim **modül seviyesinde gizli `random` çağrısı olmayacak.** Seçici bir bağımlılık olarak geçirilir:

```
_should_canary(key, *, selector=None) -> bool
    selector None ise modül varsayılanı kullanılır
    testler deterministik bir selector enjekte eder
```

Gerekçe: gizli RNG, testleri nondeterministik yapar ve "bazen geçen" test bu programda en pahalı hata türüdür — bugün ölü koda dönüşmüş `_note_alpaca_total_failure()` tam da testin yanlış şeyi ölçmesinden kaçmıştı.

Ek: üretimde kullanılan tohum (seed) başlangıçta **loglanır**, böylece bir olay sonrası canary deseni yeniden üretilebilir.

---

## 5. Saklama

**Süreç-içi (in-memory), başlangıç için yeterli.**

Taramalar aynı uzun-ömürlü uvicorn sürecine gelen ayrı HTTP istekleri — yani cache taramalar **arasında yaşıyor**. Asıl fayda buradan geliyor.

Disk kalıcılığı (restart sonrası) **ilk sürümde YOK**: bayat negatif kayıtların diskte birikmesi, kazanılan süreden daha büyük bir risk. Ölçüm faydayı doğrularsa sonra eklenebilir.

---

## 6. Gözlemlenebilirlik — zorunlu

Timing kaydına eklenecek alanlar:

| Alan | Anlamı |
|---|---|
| `negcache_size` | Cache'teki toplam kayıt |
| `negcache_hits` | Bu taramada atlanan slot sayısı |
| `negcache_writes` | Bu taramada eklenen yeni kayıt |
| `negcache_canary_recheck` | Canary ile yeniden sorulan slot |
| `negcache_canary_revived` | Canary'de **veri bulunan** slot ← kritik |

**`negcache_canary_revived` sıfırdan belirgin biçimde büyükse cache aşırı-agresif demektir** ve TTL/kural gözden geçirilmeli. Bu alan olmadan sessiz veri kaybını fark edemeyiz.

---

## 7. Güvenlik valfi

```
FINPILOT_DISABLE_NEGCACHE=1   → cache tamamen devre dışı
```

- Varsayılan: cache **açık** (`"0"`)
- Yalnızca `os.environ`'dan okunur
- Kod değişikliği olmadan geri dönüş imkânı

> Not: Bu haftanın dersi — env değişikliği `restart` ile değil `--force-recreate` ile geçiyor. Acil kapatma gerekirse bu maliyeti hesaba kat.

---

## 8. Beklenen etki (ESTIMATED — ölçüm değil)

| | Şimdi | Negatif cache sonrası |
|---|---|---|
| `prefetch.repair` | 274.6 sn | ~158 sn |
| `total_s` | 336.6 sn | **~220 sn** |

Varsayım: 89 slot × ~1.31 sn/slot doğrusal ölçekleniyor. Repair'in bulk+per-symbol karışımı nedeniyle sapabilir.

**Bu sayı doğrulanmadan EODHD kararı verilmeyecek** — cache sonrası EODHD'nin marjinal katkısı çok daha temiz ölçülür.

---

## 9. Doğrulama planı

Uygulama sonrası, **aynı üretim 200 sembolüyle**:

1. 5 koşu (ilki soğuk, atılır — cache boş başlar)
2. Karşılaştırılacak: `prefetch.repair`, `yf_fallback`, `total_s`, ve yeni `negcache_*` alanları
3. **Çıktı eşdeğerliği zorunlu**: `result_symbols` ve skor dağılımı değişmemeli

> Cache doğru çalışıyorsa hiçbir sembol kaybolmaz — zaten alınamayan veri atlanıyor. `result_symbols` düşerse tasarım hatalıdır ve geri alınır.

### KOŞUL 3 (kilitlendi) — kill kriteri SAYISAL

"Anlamlı çıkarsa" yeterli değil. Kesin eşikler:

```
revived_rate = negcache_canary_revived / negcache_canary_recheck
```

| Koşul | Eylem |
|---|---|
| `canary_recheck < 50` (kümülatif) | **Karar verme** — örneklem yetersiz |
| `revived_rate > 0.02` | TTL **yarıya indirilir**, uyarı verilir |
| `revived_rate > 0.05` | Cache **devre dışı** (`FINPILOT_DISABLE_NEGCACHE=1`), tasarım gözden geçirilir |
| Veri-bütünlüğü metriği düşerse (aşağıda) | **Derhal devre dışı**, örneklem beklenmez |

### KOŞUL 4 (kilitlendi) — `result_symbols` YANLIŞ METRİK, baseline yeniden tanımlandı

İlk taslakta kill kriteri "`result_symbols` düşerse" idi. **Bu hatalıdır.**

Negatif cache bir sembolün 15m verisini atladığında, o sembol **yine değerlendirilir ve yine sonuç satırı üretir** (`_unavailable_result()` zaten bu deseni kullanıyor). Satır sayısı **değişmez**. Cache tamamen yanlış olsa bile `result_symbols` 200'de kalır → sessiz veri kaybını **tespit edemez**.

#### Doğru metrik: gün içi veriye bağlı bileşenlerin kapsamı

Negcache yanlış atlarsa, o sembolde gün içi bar olmadığı için şunlar hesaplanamaz:

- `momentum_ratio` → 15m + 4h gerektirir
- `alignment_ratio` → 1h + 4h + 1d gerektirir

**Birincil kill metriği:** taramada bu bileşenleri **hesaplanabilmiş sembol sayısı**.

### ŞEMA TEYİDİ SONUCU (2026-09-22) — KAPI TEMİZ GEÇİLMEDİ

`alignment_ratio` ve `momentum_ratio` sonuç sözlüğünde **mevcut** (`scanner/evaluate.py:651-652, 791-793`).

**Ama doğrudan kill metriği olarak kullanılamazlar.** Üretildikleri yerde:

```python
alignment_ratio = float(alignment_ratio or 0.0)   # evaluate.py:474
momentum_ratio  = float(momentum_ratio or 0.0)    # evaluate.py:477
```

Veri yokken **`0.0`'a zorlanıyorlar** → "hesaplanamadı" ile "hesaplandı, sıfır çıktı" çıktıda ayırt edilemiyor. `check_timeframe_alignment` meşru olarak 0.0 döndürebilir (hiçbir timeframe hizalı değilse), dolayısıyla `> 0` sayımı da iki durumu karıştırır.

#### Karar: prefetch seviyesinde yeni sayaç (Seçenek C)

**`intraday_coverage`** — prefetch tamamlandığında 15m ve 1h için `MIN_HISTORY_BARS` eşiğini geçen sembol sayısı. Timing kaydına yazılır.

| Neden | |
|---|---|
| Doğrudan ölçer | Coercion'dan **önce**, gerçek büyüklüğü |
| Saf gözlem | `alpaca_miss` / `yf_bulk_*` ile aynı desen; skorlamaya **dokunmuyor** |
| Dar yarıçap | Sinyal kodu, ağırlıklar, çıktı şeması değişmiyor |

Değerlendirilen alternatifler:
- **A — `alignment_ratio > 0` sayımı:** ek kod gerektirmez, ama **vekil**. "Gerçek sıfır" popülasyonu sabit ofset olduğundan işe yarar, fakat gürültülü. Yedek plan olarak korunur.
- **B — sonuç şemasına "veri yok" işareti:** skorlama çıktısına dokunur, sinyale komşu. **Reddedildi.**

> `intraday_coverage` küçük bir kod eklemesidir ve **uygulama onayının kapsamındadır** — ayrı onay değil, ama kapsamda olduğu burada yazılı.

#### Baseline ve tolerans

| Öğe | Tanım |
|---|---|
| **Baseline penceresi** | Cache **açılmadan önce** aynı 200 sembolle 5 koşu (ilki soğuk, atılır) |
| **Karşılaştırma penceresi** | Cache açıldıktan sonraki ilk 5 koşu (ilki soğuk, atılır) |
| **Tolerans** | **Baseline'ın kendi min değeri.** Karşılaştırma penceresinde herhangi bir koşu bunun altına düşerse → ihlal |

Tolerans için keyfi yüzde **kullanılmaz**. Baseline'ın kendi koşu-arası değişkenliği toleransı tanımlar: 5 koşu 200/200/200/200/200 verdiyse 199 bile sinyaldir; 197-200 bandı verdiyse tolerans o banttır.

Bu, eşiği veriye tanımlatır — tahmin etmeye değil.

#### Yine de kaydedilecek (gözlem, karar değil)

`result_symbols` **loglanmaya devam eder** — beklenen davranış "değişmemesi"dir. Değişirse bu, negcache'ten bağımsız **başka** bir sorunun işaretidir ve ayrıca incelenmelidir.

Minimum 50 kümülatif canary gözlemi şart: tarama başına ~4 canary olduğundan bu ~13 tarama demek. Öncesinde oran gürültüdür.

> **Eşikler teknik değil ÜRÜN kararıdır.** %2, "TTL içinde cache'lenmiş slotların %2'sinde aslında veri varmış" demek — yani ~2 sembolün gün içi verisi sessizce atlanmış. Bunun kabul edilebilir olup olmadığı **hız ile veri bütünlüğü arasında bir takas** ve Meriç'in kararıdır. Buradaki değerler öneri; onay aşamasında teyit edilmeli.

---

## 10. Kapsam dışı

- Sağlayıcı zinciri değişikliği (EODHD) → ayrı karar, bu ölçümden **sonra**
- `_bulk_yf_download` timeout'u (#29) → ayrı dayanıklılık işi
- Alpaca A/B (Faz 3R) → **ertelendi, iptal edilmedi**; Alpaca'nın EODHD'ye özgün katkısı 15m=1, 1h=4 olduğu için öncelik düştü, ama karar kapatılmadı

---

## 11. Onay

Bu spec Level B'dir. Kod yazılmadan önce onay gerekir.

### Onay gerektiren iki AYRI şey

| # | Ne | Neden ayrı |
|---|---|---|
| 1 | **Uygulama izni** | Level B kod değişikliği |
| 2 | **Kill eşikleri (%2 / %5)** | Teknik gerçek değil **ürün politikası** — hız ile veri bütünlüğü arasında takas. Bu sayılar Claude'un önerisi, onaylanmış politika **değil**. |

İkincisi birincisiyle birlikte varsayılmayacak. Eşikler teyit edilmeden cache açılırsa, ihlal durumunda ne yapılacağı tanımsız kalır.

### Şema teyidi ✅ YAPILDI (2026-09-22)

Sonuç: alanlar var ama coercion nedeniyle kullanılamaz → **`intraday_coverage` sayacı** kill metriği olarak seçildi (Bölüm 9). Uygulama artık bloke değil.

### Sıra

| # | Adım | Durum |
|---|---|---|
| 1 | Şema teyidi | ✅ yapıldı — metrik `intraday_coverage` olarak yeniden seçildi |
| 2 | **`intraday_coverage` sayacını ekle** (yalnızca gözlem, cache YOK) | ⏳ |
| 3 | **Baseline penceresi**: cache KAPALIYKEN 5 koşu → metriğin min değeri kaydedilir | ⏳ |
| 4 | Negatif cache uygulaması + deterministik testler | ⏳ |
| 5 | **Karşılaştırma penceresi**: 5 koşu | ⏳ |
| 6 | Karar | ⏳ |

> **Adım 2, adım 3'ten önce gelmek zorunda.** Sayaç yoksa baseline ölçülemez.
>
> **Adım 3 atlanamaz.** Baseline olmadan kill kriteri uygulanamaz — neyin "düşüş" olduğu tanımsız kalır.
>
> Adım 2 ve 4 **ayrı commit/ayrı doğrulama** olmalı: sayaç önce tek başına devreye girip baseline üretmeli, cache sonra. Birlikte yapılırsa "ölçüm aleti mi değişti, davranış mı" ayırt edilemez — bu haftanın Faz 1 dersi.
