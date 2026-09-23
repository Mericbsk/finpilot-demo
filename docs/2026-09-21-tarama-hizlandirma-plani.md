# Tarama Hızlandırma Planı

**Tarih:** 2026-09-21 · **Sürüm:** v2 (konsolide) · **Durum:** Faz 0 ✅ · Faz 1 ⛔ geçersiz · Faz 2R ⏳ sırada

> **v2 notu:** Belge gün içinde parça parça düzenlendiğinden kendi içinde tutarsızlaşmıştı (bayat satır numaraları, çürütülmüş hipotezler açık listede, iki ayrı "Faz 4", var olmayan fazlara atıf). Bugün `_note_yf_fetch` çift sayımı **tam olarak bu yüzden** oluştu: paralel süreç bayat talimata uydu. Bu sürüm o borcu kapatır. **Belge bayatsa tehlikelidir.**

---

## 1. Neyi kesin biliyoruz

| # | Bulgu | Durum | Kanıt |
|---|---|---|---|
| K1 | `yf_fallback` sayacı toplu indirme yolunu saymıyordu (`_note_yf_fetch()` yalnızca sembol-başına yolda) | ✅ **Faz 0'da düzeltildi** — artık `yf_bulk_requests`/`yf_bulk_symbols` ayrı sayıyor | Kod; şimdi `data_fetcher.py:383` (sembol-başına) + `:871` (toplu) |
| K2 | `yf_fallback=0` "yfinance kullanılmadı" demek DEĞİL | ✅ **üretim verisiyle kanıtlandı**: 5 koşuda `yf_fallback=0` iken `yf_bulk_symbols=600` | Timing log |
| K3 | Süreyi belirleyen sembol sayısı değil | KESİN | Satır 182: 138 sembol düştü → 38 sn; satır 16: daha az düştü → 336 sn |
| K4 | Kalıcılaştırma `total_s`'nin dışında | KESİN (ölçüm penceresi hatası) | `scan.py`, `_t_scoring_done` konumu |
| K5 | Aşama zamanlaması kodda var, 12 noktada çağrılıyor | ✅ **açıldı** — 321 kaydın 6'sında `stage_timing` dolu (931 event/koşu) | `performance.py` + log |
| K6 | `scanner/` paketi `price_cache`/`intraday_cache`'i hiç okumuyor | KESİN | Grep: sıfır referans |
| K7 | `price_cache` ~2 ay bayat (AAPL 2026-07-22), yenileme görevi zamanlanmamış | KESİN | Dosya + scheduler grep |
| K8 | `eodhd_client.bulk_eod()` yazılmış, hiçbir yerden çağrılmıyor | KESİN | Grep |
| K9 | `api/main.py:16-26` elle yazılmış `.env` yükleyici içeriyor; `os.environ`'a **süreç başladıktan sonra** yazıyor | KESİN | Kod |
| K10 | Yükleyici `if _key not in os.environ` kullanıyor → **kabuktan verilen değişkenler `.env`'i ezer** | KESİN | Kod |
| K11 | İki ayrı konteyner tanımı var; devcontainer `Dockerfile`'ı kullanmıyor | KESİN | `devcontainer.json:4` vs `Dockerfile:18,43` |

---

## 2. Ölçülmüş sonuçlar (Faz 1 — ⛔ geçersiz temel, ama bazı bulgular geçerli)

Faz 1, üretim dışı bir ortamda koştuğu için **temel olarak kullanılamaz** (bkz. Bölüm 4). Yine de iki hipotez kesin olarak kapandı:

| Hipotez | Sonuç |
|---|---|
| **H1** — Kalıcılaştırma anlamlı pay tutar | ❌ **ÇÜRÜTÜLDÜ.** `persist_s` medyan 0.16 sn / 70.82 sn = **%0.23** |
| **H2** — `yf_fallback` toplu yolu gizliyordu | ✅ **DOĞRULANDI** (K2) |
| **H3** — 300 günlük 1d geçmişini her taramada çekmek anlamlı | ⏳ **AÇIK** — timeframe bazlı kırılım henüz ayrıştırılmadı |
| **H4** — EODHD intraday daha hızlı ve az oynak | ⏳ **AÇIK** — Faz 4R'ye ertelendi |

Alpaca'sız ortamda ölçülen dağılım (yalnızca o rejim için geçerli): `prefetch.bulk_yfinance` ~%81.7, değerlendirme ~%18 (iyi paralelleşmiş, ~11×), kalıcılaştırma %0.2.

---

## 3. Kapsam dışı (bu planın yetkisi değil)

- `alignment_ratio` / `momentum_ratio` kaldırmak → **sinyal kararı**
- Feature flag açma/kapatma → DEFERRED, baseline çözülene kadar
- Canlı gün-içi akış mimarisi → ayrı iş
- `.env` yükleme davranışını değiştirmek → 18 flag'i aynı anda etkiler, ayrı karar

---

## 4. Planın mantığı

> **Bozuk aletle iyileştirme ölçülemez. Yanlış ortamda ölçüm karşılaştırılamaz.**

İki ders, ikisi de pahalıya öğrenildi:

1. **14 Eylül:** "yfinance fallback THE darboğaz" dedim — bozuk sayaca güvendim. Geri çekildi.
2. **21 Eylül:** Faz 1 ölçümü üretim dışı ortamda alındı — fark edilmeseydi yanlış şeyi optimize edecektik.

Sıralama bu yüzden pazarlığa kapalı: **alet → ortam → ölçüm → değişiklik → doğrulama.**

---

## FAZ 0 — Aleti düzelt ✅ TAMAMLANDI (2026-09-21)

**Sahip:** Claude · **Seviye:** B · **Sinyale etkisi:** yok

| Adım | İş | Durum |
|---|---|---|
| 0.1 | Toplu yfinance görünürlüğü — `_note_yf_bulk()` + `yf_bulk_requests`/`yf_bulk_symbols` **ayrı** sayaçlar | ✅ |
| 0.2 | `alpaca_total_failure: bool` | ✅ (ölü kod hatası düzeltildi, regresyon testi eklendi) |
| 0.3 | `persist_s` timer | ✅ |

**Tasarım kuralı (bağlayıcı):** Mevcut alanların anlamı **değiştirilmez**. 321 geçmiş kayıtla karşılaştırılabilirlik korunur. Yeni ölçüm = yeni alan.

> **Çakışma kaydı:** 0.1 bu belgede önce "`_bulk_yf_download()` içine `_note_yf_fetch()` ekle" yazıyordu. Yanlıştı — yukarıdaki kuralı ihlal ediyordu. Claude ayrı sayaç yaptı ama belgeyi güncellemedi; paralel süreç bayat talimata uyup çift sayım oluşturdu. Testler yakaladı. **Ders: plandan sapılacaksa sapma ANINDA belgeye yazılır.**

**Doğrulama:** `pytest tests/test_scanner_performance.py` → 8/8 ✅

---

## FAZ 1 — Temel ölçüm ⛔ GEÇERSİZ (tekrarlanacak)

Koşuldu (5 koşu, 931 event/koşu) ama **üretim ortamında değil**. Kanıtlar:

- Ölçüm kabuğunda `alpaca` paketi yok (oysa `requirements.txt:72`'de beyan edilmiş)
- Her koşuda `No module named 'routers'` → `api.main` altında çözülen bir import orada çözülmüyor
- Aynı günün kampanya öncesi koşularında (06:50–07:19) `alpaca_miss` **dolu** → üretimde Alpaca çalışıyordu

**Sonuç: %81.7 rakamı yalnızca Alpaca'sız ortam için geçerli.** Faz 2R sonrası doğru ortamda tekrarlanacak.

### Yorumlanmayacak sinyal

| Rejim | Medyan | n |
|---|---|---|
| Alpaca var (06:50–07:19) | ~409 sn | 5 |
| Alpaca yok (kampanya) | ~71 sn | 5 |

~5.8× fark var **ama Alpaca etkisi olarak okunmayacak.** İki kol `.env` yüklemesi, `alpaca` paketi **ve** giriş noktası bakımından ayrı — büyük olasılıkla **ortam artefaktı**. Faz 3R bunu tek ortamda ayrıştıracak.

---

## FAZ 2R — Üretim ortamını tespit et ⏳ SIRADA (KAPI)

**Sahip:** Meriç · **Seviye:** A · **Ön koşul:** yok

Bu cevaplanmadan **hiçbir ölçüm karşılaştırılabilir değil.**

### Kod okumasıyla tespit edilenler

| Bulgu | Kaynak |
|---|---|
| Üretim Docker devcontainer içinde, `/workspaces/Borsa` | `devcontainer.json`, `finpilot.bat:75` |
| `requirements.txt` → `/opt/venv` (`alpaca-py==0.43.2` dahil) | `devcontainer.json:33` |
| VS Code yorumlayıcısı `/opt/venv/bin/python` | `devcontainer.json:22` |
| **İki başlatıcı da çıplak `python3`** kullanıyor | `start.sh:51,83` · `finpilot.bat:75` |
| devcontainer'da `remoteEnv`/`containerEnv`/`env_file` yok | `devcontainer.json` |

**İki konteyner tanımı karıştırılmamalı:** `Dockerfile` `ENV PATH="/opt/venv/bin:$PATH"` garantisi verir (satır 18, 43) — **ama devcontainer o Dockerfile'ı kullanmıyor**, `"image"` ile hazır imaj çekiyor. Ve `finpilot.bat` açıkça devcontainer'ı hedefliyor.

**Kritik belirsizlik:** devcontainer'da `python3` neye çözülüyor?
- VS Code terminali (venv oto-aktif) → `/opt/venv/bin/python3` → alpaca **var**
- `docker exec -d bash -c` → varsayılan PATH → `/usr/local/bin/python3` → alpaca **yok**

İki başlatıcı iki farklı yorumlayıcıya düşüyor olabilir. 5.8× farkın en olası açıklaması bu.

### 2R.1 — Süreç kimliği (dışarıdan)

```bash
docker ps --format "{{.ID}} {{.Names}}"

docker exec <ID> bash -lc '
  PID=$(pgrep -f "uvicorn api.main" | head -1)
  echo "PID=$PID"
  echo "EXE=$(readlink -f /proc/$PID/exe)"
  echo "CWD=$(readlink -f /proc/$PID/cwd)"
  echo "CMD=$(tr "\0" " " < /proc/$PID/cmdline)"
  tr "\0" "\n" < /proc/$PID/environ \
    | grep -E "^(ALPACA_API_KEY|FINPILOT_ENABLE_)" \
    | sed -E "s/=.*/=<present>/"
'
```

Gizli değer yazdırılmaz. `/proc/<pid>/environ` **çalışan sürecin** ortamıdır, `docker exec` ile açılan yeni kabuğunki değil — dünkü yanılgı buradaydı.

### 2R.2 — Paket (aynı yorumlayıcıda)

```bash
docker exec <ID> bash -lc '
  EXE=$(readlink -f /proc/$(pgrep -f "uvicorn api.main" | head -1)/exe)
  echo "EXE=$EXE"
  "$EXE" -c "import sys; print(sys.executable)"
  "$EXE" -c "import alpaca; print(\"alpaca\", alpaca.__version__)" || echo "alpaca YOK"
'
```

### 2R.3 — Canlı `os.environ` (içeriden) — YENİ KOD GEREKMİYOR

⚠️ **`/proc` tek başına yetmez, yanlış negatif verir.** K9: `api/main.py` `.env`'i süreç başladıktan **sonra** `os.environ`'a yazıyor; `/proc/<pid>/environ` bunu göstermez. `ALPACA_API_KEY=<present>` çıkmaması "anahtar yok" demek **değil**.

Faz 0'da kurduğumuz `alpaca_total_failure` alanı `data_fetcher.py:744`'teki ilk guard'dan (`if not os.environ.get("ALPACA_API_KEY")`) türüyor — yani **çalışan sürecin canlı `os.environ`'ını** okuyor.

**Gerçek API üzerinden tek bir tarama koş**, yeni timing kaydına bak:

| `alpaca_total_failure` | Anlamı |
|---|---|
| `false` | Anahtar `os.environ`'da **vardı** → `.env` sürece ulaşmış ✅ |
| `true` | Belirsiz: anahtar yok **ya da** `alpaca` import'u patladı |

**Belirsizliği `logs/api.log` çözer:** import patlarsa dıştaki `except` `"Alpaca bulk prefetch error: %s"` yazar; anahtar yoksa satır 745 **sessizce** döner. Log'un sessizliği de veridir.

**Bu tek tarama görev #25'i de kapatır:** `.env` yükleyicisi tek döngü — `ALPACA_API_KEY` için çalıştıysa 18 `FINPILOT_ENABLE_*` için de çalışmıştır. `false` sonucu "flag'ler fiilen kapalı" hipotezini çürütür. API'de flags endpoint'i yok, yazmaya da gerek yok.

### 2R.4 — Tetikleyici

Üretimde tarama nasıl başlıyor: scheduler mı, `/scan` endpoint mi, script mi? Hangi kolun ölçüldüğünü bu belirler.

### Çıkış kriteri

> Tarama şu konteyner içindeki şu PID tarafından, şu executable ile, şu import ortamında ve şu tetikleyici üzerinden çalışıyor; `.env` değerleri process environment'a aktarılmıştır / aktarılmamıştır.

> **Çıkarım sınırı (Meriç):** `alpaca_miss`'in dolu olması, Alpaca yolunun **o koşuda devreye girdiğini** kanıtlar — "üretim ortamı kesin buydu"yu **değil**. Log bir davranışı kanıtlar, bir ortamı kanıtlamaz.

---

## FAZ 3R — Kontrollü Alpaca A/B (tek ortamda)

**Sahip:** Meriç (koşum) + Claude (analiz) · **Seviye:** A · **Ön koşul:** Faz 2R

Faz 2R'de tespit edilen **tek** ortamda, **aynı** 200 sembolle: Kol A (Alpaca aktif) 5 koşu, Kol B (devre dışı) 5 koşu.

**Serpiştirilmiş: A-B-A-B-A-B-A-B-A-B.** Ardışık blok değil — 10× varyans zamana bağlı olabilir; serpiştirme piyasa saati, ağ ve cache kaymasını iki kola eşit dağıtır.

### Bayrak kısıtları (Meriç, bağlayıcı)

`FINPILOT_DISABLE_ALPACA` **Faz 2R tamamlanmadan yazılmayacak.** Yanlış giriş noktasına veya yanlış yorumlayıcıya eklenirse deney yine karşılaştırılamaz olur.

1. Varsayılan davranış korunur — Alpaca açık (`"0"`)
2. Yalnızca `os.environ` üzerinden okunur
3. `.env` içine **eklenmez**
4. Süreç başlatılırken açıkça verilir *(K10 sayesinde ek koda gerek yok — kabuk `.env`'i ezer)*
5. Alpaca devre dışıyken sonuç metadata'sına **deney kolu yazılır**
6. Süre yanında **çıktı eşdeğerliği ve sağlayıcı kapsamı** kaydedilir

Kimlik bilgisiyle oynanmaz; `.env`'den anahtar silmek gibi geri alması riskli yol kullanılmaz.

### Ölçülecek iki şey — ikisi de zorunlu

1. **Süre:** medyan + p95/medyan oranı (asıl hedef **varyans daralması**)
2. **Çıktı eşdeğerliği:** sembol sayısı, skor dağılımı, shortlist üyeliği

İkincisi pazarlığa kapalı. Alpaca ve yfinance farklı barlar verebilir → farklı skorlar. Çıktılar maddi olarak farklıysa **"Alpaca'yı kapat" bir hız kararı değil, veri kararıdır** ve bu planın yetkisi dışındadır.

### Dallanma

- B hızlı **ve** çıktı eşdeğer → Alpaca yolu gerçek darboğaz; kalıcı bypass tartışılır
- B hızlı **ama** çıktı farklı → veri kalitesi kararı, ayrı iş
- Fark yok → 5.8× ortam artefaktıydı; Faz 1 doğru ortamda tekrarlanır

---

## FAZ 4R — Günlük bar israfı (koşullu)

**Sahip:** Claude · **Seviye:** B · **Kapı:** Faz 1'in **doğru ortamda** tekrarı, 1d çekiminin anlamlı pay tuttuğunu göstermeli. Göstermezse yapılmaz — H3 böylece çürür.

Her tarama her sembol için 300 günlük geçmişi yeniden indiriyor; geçmiş günlük barlar değişmez. İki seçenek:

- **(a)** `bulk_eod()` bağla — tek çağrıda tüm US borsası, kod hazır
- **(b)** `price_cache`'i canlandır — yerel disk okuma

⚠️ (b) için: yenileme görevi kurulmadan canlı yola bağlamak, **2 aylık bayat veriyle tarama** demektir. Yavaşlıktan çok daha kötü bir hata.

---

## FAZ 5R — EODHD (askıda)

**Ön koşul:** Faz 3R sonucu. Gerekçe: Alpaca bypass'ı tek başına yeterse, EODHD'nin ne kattığını önce bilmeliyiz. `scripts/verify_eodhd_bars.py` hazır, koşulmayı bekliyor.

---

## FAZ 6R — İki aşamalı huni (mimari)

**Ön koşul:** Faz 3R + 5R. 1.900 sembolde önce ucuz `1d` eleme → ilk ~150 aday → yalnızca onlara gün içi veri. Tam evrende "dakikalar" seviyesine inmenin tek yolu; EODHD intraday sembol başına bir çağrı olduğu için kota açısından da zorunlu.

---

## Sahiplik

| Faz | Claude | Meriç |
|---|---|---|
| 0 ✅ | kod | gözden geçirme |
| 1 ⛔ | — | (tekrarlanacak) |
| 2R ⏳ | — | 4 kontrol |
| 3R | analiz + bayrak kodu | koşum |
| 4R / 5R / 6R | kod | onay |

**Kısıt:** Claude'un Linux çalışma alanı 8 Eylül Windows güncellemesinden beri erişilemez. Kod yazılabiliyor, **çalıştırılamıyor**. Her doğrulama adımı Meriç'te.

---

## Beklenen sonuç

| Rejim | 200 sembol | Etiket |
|---|---|---|
| Tarihsel (karışık) | medyan ~300 sn | LOGGED |
| Alpaca var (09-21 sabah) | ~409 sn | LOGGED, n=5 |
| Alpaca yok (kampanya) | ~71 sn | MEASURED, n=5, **üretim dışı** |
| Faz 3R sonrası | ? | ölçülecek |

**Tam evren için ekstrapolasyon YOK.** Temiz bir temel gelene kadar bu satır boş kalır.

---

## Governance

Hiçbir faz otomatik uygulanmaz. Kod değişiklikleri (Faz 0, 3R bayrağı, 4R, 5R, 6R) yazılmadan önce onaylanır. `.env` değişiklikleri **Meriç tarafından** yapılır.

Mevcut sınıflandırmalar (flag DEFERRED, fade CONFIRMATORY_CANDIDATE, attention map VALIDATED-DESCRIPTIVE, catalyst UNVALIDATED) bu planla **değişmez**.

**Kapatılan borçlar:** 2026-09-14 "yfinance birincil darboğaz" iddiası geri çekildi ✅ · ".env hiç yüklenmiyor" teşhisi geri çekildi ✅ (K9/K10).

**Açık yan bulgular (bu planın dışında, kendi görevleri var):**
- Auto-watchlist `No module named 'routers'` ile her koşuda sessizce başarısız (görev #24)
- Feature flag'lerin fiili durumu — Faz 2R.3 ile kapanacak (görev #25)
