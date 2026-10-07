# Tarama Neden Yavaş — ve Çözüm Uzayının Tamamı

**Tarih:** 2026-09-23 · **Sürüm:** v2 (bağımsız incelemeyle düzeltildi) · **Tip:** Kavramsal · **Durum:** tartışma için, karar değil

> **v2 notu.** v1'deki beş iddia bağımsız bir incelemede sorgulandı; kod okumasıyla doğrulandı ve düzeltildi. En önemlisi: v1 "gün içi veriyi yalnızca iki doğrulanmamış feature için çekiyoruz" diyordu — **bu yanlıştı** (Bölüm 7). Değişiklikler her bölümde işaretli.

---

## 1. Tek cümlelik teşhis

> **Her taramada, gün içinde değişmeyen bir gerçeği, eşzamanlı olarak, kritik yolun ortasında yeniden keşfediyoruz.**

O gerçek: *hangi sembolün hangi zaman diliminde verisi var.*

Bu bilgi **tek bir işlem günü içinde** kararlı görünüyor — aynı koşuların eksik sayıları tekrarlanıyor (15m: 109, 1h: 93, 1d: 8). Ama her taramada sıfırdan soruyoruz ve cevabın büyük kısmı "yok" çıkıyor.

> ⚠️ **v2 düzeltmesi:** v1 "aynı semboller her gün boş dönüyor" diyordu. **Bu kanıtlanmadı.** Tekrarlanan şey *sayılar*; sayı ≠ sembol kimliği. Günler arası kimlik kararlılığı ayrı ölçülmeli (Bölüm 8). Gün-içi kararlılık ise pratikte yeterli: negatif cache için günlük TTL bunu varsayar, daha fazlasını değil.

---

## 2. Nedensel zincir

Ölçülmüş adımlar:

1. Tarama her sembol için **4 zaman dilimi** istiyor: 15m, 1h, 1d (+ 1h'ten türetilen 4h)
2. Birincil sağlayıcı (Alpaca/IEX) yalnızca `1d`'de güvenilir — **192/200**. Gün içinde yarısını kaçırıyor: 15m **91/200**, 1h **107/200**
3. Eksik veri, istek anında **onarım yolunu** tetikliyor
4. Onarım yfinance'e gidiyor — eşit kapsam için **~15× yavaş** (40 sembollük benchmark)
5. Onarımın kovaladığı 210 slot'un **89'u Alpaca ∪ EODHD birleşiminde yok**

### Sürenin ne kadarı onarımda — istatistik açıkça

| Ölçü | Değer |
|---|---|
| Medyanların oranı (`median(repair) / median(total)` = 274.6 / 336.64) | **%81.6** |
| Koşu-başına oranların medyanı | **%86.5** |
| Koşu-başına aralık | %78.6 – %90.6 |

Kaynak: 2026-09-22 kampanyası, 5 koşu (ilk soğuk koşu hariç), `scan_timing.jsonl`.

> ⚠️ **v2 düzeltmesi:** v1 yalnızca %81.6 verdi ve hangi istatistik olduğunu söylemedi. İkisi farklı sayılar; %81.6 muhafazakâr olanı.

> ⚠️ **v2 düzeltmesi:** v1 "89 slot hiçbir sağlayıcıda yok" diyordu. Birleşim ölçümü `--skip-yfinance` ile yapıldı — yani **yfinance kapsamı bu kümeye dahil değil**. Doğru ifade: "Alpaca ∪ EODHD birleşiminde yok." yfinance'in bu 89'un bir kısmını doldurup doldurmadığı ölçülmedi.

### Kök neden bir bileşen değil, bir varsayım

Mimari, "veri eksik" durumunu **istisna** sayıyor ve istek anında onarmaya çalışıyor. Oysa bu evrende veri eksikliği **istisna değil, kural** — ve en azından bir gün içinde **kararlı** bir kural.

### Ve sistem o sembolleri zaten eliyor

`scanner/evaluate.py:379`:

```python
if len(df_15m) < 15 or len(df_1h) < 10 or len(df_4h) < 15 or len(df_1d) < 50:
    return _unavailable_result(symbol, "insufficient_history")
```

Gün içi verisi yetersiz semboller **zaten** sonuca girmiyor. Yani onarım yolu, çoğu durumda, sistemin nasılsa vereceği "bu sembol yok" kararına **274 saniye harcayarak** varıyor.

---

## 3. Çözüm sınıfları

### A. Daha az iş yap

| Yöntem | Kazanç (ESTIMATED) | Maliyet |
|---|---|---|
| **Negatif cache** — var olmayanı sorma | ~117 sn | **Yok** — satır 379 o sembolleri zaten eliyor |
| **Huni** — yalnızca adaylara gün içi veri | ~165 sn | Aday kümesi değişebilir → **veri sözleşmesi kararı** |

> ⚠️ **v2 düzeltmesi:** v1 bu tabloda "Zaman dilimi azalt — ~275 sn" satırı içeriyordu. **Kaldırıldı** — gün içi veri yalnızca iki feature'ı değil, giriş fiyatını, ATR'yi, spread'i ve uygunluk kapısını besliyor (Bölüm 7). "Zaman dilimi azaltmak" bir performans seçeneği değil, sistemin çekirdeğini değiştirmek.

**Negatif cache listedeki en güvenli değişiklik.** Satır 379 sayesinde sonuç kümesini değiştirmez: atlanan her sembol zaten `unavailable` dönecekti.

**Huni ise salt performans değil.** Aşama-1'de elenen bir sembol aşama-2'ye hiç girmez; tam veriyle skorlansaydı seçilecek olanlardan bazıları kaçabilir (%40 genişlikte ölçülen: 50'den 1). Bu bir **ürün/veri sözleşmesi** kararı, Level B.

### B. Aynı işi daha hızlı yap

| Yöntem | Kazanç (ESTIMATED) | Maliyet |
|---|---|---|
| **EODHD** onarım yolunda | ~130 sn | Kota 10.000/gün; kararlılık belirsiz (bir ölçüm 404 döndü) |
| **Extract `groupby`** | 2.9 → ~0 sn (1.900'de ~66 → ~0) | Yok — semantik eşdeğer |
| **İndikatör hızlandır** | ~15 sn | Orta — vektörleştirme |
| **Daha çok worker** | ~0 | GIL'e takılı; 32 worker ~4× veriyor |

**Paralellik tükendi.** Daha fazla worker eklemek ölçülmüş olarak işe yaramıyor.

### C. İşi kritik yoldan çıkar ⭐

Tarama veri **çekmez**, önceden doldurulmuş bir depodan **okur**. Arka plan yenileyici depoyu periyodik olarak günceller.

```
ŞİMDİ:   tarama → sağlayıcı → bekle → onar → bekle → skorla
ÖNERİ:   [arka plan: sağlayıcı → depo]
         tarama → depo → skorla
```

Tarama süresi sağlayıcı gecikmesinden **kopar**. Geriye CPU kalır: ~45 sn, huniyle ~28 sn.

> ⚠️ **v2 düzeltmesi:** v1 "bu desen repoda zaten var: `price_cache/`" diyordu. **Fazla iyimserdi.**
> - `price_cache/` **günlük araştırma verisi**; tarama 15m ve 1h istiyor.
> - Tarayıcıdaki 5 dakikalık TTL cache'i yalnızca **tekil `fetch()`** yolunda. Alpaca ve toplu-yfinance prefetch yolları onu **kullanmıyor**.
>
> Yani C için **yeni bir gün içi veri katmanı** gerekiyor: 15m/1h barlarını tutan, yenileme sıklığı ve tazelik sözleşmesi olan, eksik/bayat veriyi açıkça işaretleyen bir katman. Büyük iş.

**C'nin gerektirdiği sözleşme:**
- Tarama tek, tutarlı bir yerel **snapshot** okur
- Cache miss'te sağlayıcıya **senkron düşmez**
- Bayat veya eksik veri **açıkça işaretlenir** (`data_quality` alanında)
- Önce **gölge yolda**: eski yol ile cache'li yol yan yana, skor/sıra/`data_quality`/kapsam eşdeğerliği ölçülür — **sonra** gecikme

**Bedeli tazelik.** 5 dakikada bir yenilenen 15m barı mevcut kullanım için muhtemelen yeterli; gerçek gün içi trading için değil.

### D. Kısmi veriyi kabul et

Eksiği onarmak yerine elindekiyle skorla.

> ⚠️ **v2 düzeltmesi:** v1 bunu "bugün de fiilen bu oluyor" diye sundu. **Tam doğru değil.** Satır 379 gün içi verisi yetersiz sembolü `unavailable` döndürüyor — kısmi skorla devam etmiyor. D'yi uygulamak, **şu an elenen sembolleri sonuca sokmak** demek. Bu, giriş fiyatı ve ATR'nin 15m'den geldiği düşünülürse (Bölüm 7) ciddi bir davranış değişikliği. **Yüksek risk, ürün kararı.**

### E. Mimariyi değiştir — akış

Sürekli durum tut; tarama anlık bir hesaba dönüşür. `archive/core_legacy/websocket_feeds.py` duruyor.

> ⚠️ **v2 düzeltmesi:** v1 "gerçek gün içi canlı sistem için tek yol bu" diyordu. **Fazla kesin.** 15 dakikalık barlar için periyodik yenileme (C) yeterli olabilir. E, saniye-altı tazelik gerekiyorsa gerekli.

### F. Sözleşmeyi değiştir

- **Asenkron tarama:** istek hemen döner, sonuçlar geldikçe dolar
- **Kademeli sonuç:** önce günlük-skorlu liste, gün içi veri geldikçe güncellenir

> ⚠️ **v2 düzeltmesi:** v1 F'in kazancını "%0 gerçek" olarak verdi. **Yanlış çerçeve.** F işlem süresini değil **yanıt süresini** iyileştirir — ve kullanıcı açısından bu gerçek bir kazanç.

---

## 4. Sınıflar nasıl birleşir

```
F (algı)        ── asenkron/kademeli sonuç
E (mimari)      ── akış  ────────────┐
C (zamanlama)   ── arka plan depo ───┤→ tarama ≈ CPU
A (az iş)       ── negcache + huni ──┤
B (hızlı iş)    ── EODHD, groupby ───┘
```

**A + C birlikte güçlü bir hedef mimari.**

> ⚠️ **v2 düzeltmesi:** v1 "C yapılırsa EODHD gereksizleşir" diyordu. **Yanlış.** C sağlayıcı *gecikmesini* kritik yoldan çıkarır; sağlayıcı *kapsamını* çözmez. Arka plan yenileyici de bir sağlayıcıdan beslenir — ve orada EODHD, Alpaca'nın kaçırdığı 121 slot'u doldurabilir. C, EODHD'yi **kritik yoldan** çıkarır, **mimariden** değil.

---

## 5. Karşılaştırma

| Sınıf | Kazanç (ESTIMATED) | Risk | Efor | Geri alma | Seviye |
|---|---|---|---|---|---|
| **A** negatif cache | ~%35 | **Çok düşük** (satır 379) | Küçük | Bayrak | B |
| **A** huni | ~%50 | Orta — aday kümesi | Orta | Bayrak | B (veri sözleşmesi) |
| **B** extract | ~%1 (1.900'de ~%15) | Yok | Çok küçük | Trivial | B |
| **B** EODHD | ~%40 | Orta — kota, kararlılık | Orta | Bayrak | B |
| **C** arka plan depo | ~%85 | Orta — tazelik | **Büyük** | Zor | B → C (canlı) |
| **D** kısmi veri | ~%80 | **Yüksek** — elenen semboller sonuca girer | Küçük | Bayrak | Ürün kararı |
| **E** akış | ~%95 | Yüksek | Çok büyük | Çok zor | Ayrı ürün |
| **F** asenkron | Yanıt süresi ↓ | Düşük | Orta | Orta | B |

Tüm kazançlar **ESTIMATED** — uygulanıp ölçülene kadar performans sonucu sayılmaz.

---

## 6. Görüş

**Kısa vade:** **Negatif cache, huniden ayrı.** Satır 379 sayesinde sonuç kümesini değiştirmediği için tek başına en güvenli adım. Spec hazır, onaylı.

**Huni ayrı bir Level B değerlendirmesi olmalı** — aday kümesini etkiliyor.

**Orta vade:** C'yi hedef mimari olarak tasarla. Gölge yolla başla: skor/sıra/kapsam eşdeğerliği kanıtlanmadan gecikme kazancı konuşulmasın.

**EODHD** C'nin arka plan yenileyicisinde kapsam sağlayıcı olarak rol alabilir — kota orada daha rahat yönetilir çünkü tarama sıklığından bağımsız.

---

## 7. v1'in yanlış olduğu en önemli nokta

v1 bu bölümde şunu söylüyordu:

> ~~"Gün içi barları **sadece** `momentum_ratio` ve `alignment_ratio` için çekiyoruz... Cevap hayırsa performans sorunu ortadan kalkıyor."~~

**Bu yanlıştı.** Kod okuması (`scanner/evaluate.py`):

| Satır | 15m verisinden gelen | Rolü |
|---|---|---|
| 379 | Asgari geçmiş kapısı (`len(df_15m) < 15`) | **Uygunluk** — yoksa sembol `unavailable` |
| 419 | `last_price = df_15m["Close"].iloc[-1]` | **Giriş fiyatı** |
| 420 | `atr_val = df_15m["atr"].iloc[-1]` | **Risk boyutlandırma** |
| 148, 239, 310 | `spread_bps` | **Uygulanabilirlik** |
| 475 | `momentum_ratio` | Skor bileşeni |
| 706 | `df_15m.index[-1]` | **Sinyal zaman damgası** |

Gün içi veri, sistemin **giriş fiyatlandırmasının, risk hesabının, uygulanabilirlik kontrolünün ve uygunluk kapısının** temeli. "İki feature'ı at" demek bunların hepsini yeniden tasarlamak demek.

Bu iddia birkaç tur boyunca tekrarlandı ve bağımsız incelemede yakalandı.

**Hâlâ geçerli olan soru:** `momentum_ratio` ve `alignment_ratio`'nun skora katkısı doğrulanmadı. Ama bu **sinyal** sorusu — performans sorusu değil. Onları çıkarmak gün içi veri ihtiyacını ortadan kaldırmaz.

---

## 8. Açık ölçümler

| Soru | Neden önemli | Nasıl |
|---|---|---|
| Eksik sembollerin **kimliği** günler arası kararlı mı? | Negatif cache TTL'inin ne kadar uzun olabileceği | Aynı 200 sembolle farklı günlerde kapsam **kümelerini** karşılaştır |
| yfinance, Alpaca ∪ EODHD'nin kaçırdığı 89'un kaçını dolduruyor? | "Hiçbir sağlayıcıda yok" ifadesinin kesinliği | Benchmark'ı yfinance dahil, sembol × zaman dilimi × sağlayıcı düzeyinde koş |
| Huninin gerçek recall'u, `filter_score` dahil edilince? | Huni genişliği | Offline, filter_score'u günlük bardan hesaplayıp testi tekrarla |

İlki negatif cache'i **bloke etmez** — günlük TTL, gün-içi kararlılığı varsayar, fazlasını değil. Uzun TTL'e geçmek için gerekir.
