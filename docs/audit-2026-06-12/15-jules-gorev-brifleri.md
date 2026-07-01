# Jules Görev Brifleri — İlk 5 Görev (kopyala-yapıştır hazır girdiler)

**Tarih:** 2026-06-12 · **Bağlam:** `14-jules-test-stratejisi.md`. Aşağıdaki 5 brif, asenkron kodlama ajanına (Google Jules vb.) doğrudan verilebilecek **girdilerdir.** Hepsi Aşama-1: deterministik, izole, hızlı doğrulanır, finansal karar mantığına dokunmaz.

---

## TÜM GÖREVLER İÇİN ORTAK KURALLAR (her brife dahil et)

```
GLOBAL GUARDRAILS (FinPilot):
- Bu bir test/kalite görevidir. Strateji, skor veya risk MANTIĞINI DEĞİŞTİRME.
- Dokunma (salt-okunur): scanner/score_engine.py, scanner/evaluate.py karar
  bloğu, scanner/risk_engine.py, scanner/labeling.py parametreleri, drl/ reward.
  Bu dosyalara yalnızca TEST yazabilirsin; içlerindeki mantığı değiştiremezsin.
- Testler DETERMİNİSTİK olmalı: hiçbir test gerçek ağ/yfinance/Alpaca/SEC
  çağrısı yapmamalı — dış veriyi mock'la veya sabit fixture kullan.
- Bir testi geçirmek için üretim kodunun davranışını DEĞİŞTİRME; test mevcut
  davranışı doğrulamalı (bug fix görevleri hariç, onlar da dar kapsamlı).
- Çıktı: tek odaklı, küçük bir PR. 1000+ satırlık dosyalara dokunuyorsan
  dosyayı KISALTMA — tam dosya bütünlüğünü koru; diff'i minimal tut.
- Her PR şu gate'lerden geçmeli: `python -m py_compile <değişen .py>` +
  ilgili pytest yeşil + `ruff check` temiz. Geçmiyorsa PR açma.
- Belirsizlik varsa varsayım yapma; PR açıklamasında soruyu belirt.
```

---

## GÖREV 1 — yfinance'e bağlı 2 kırık testi mock'la (P0, en güvenli başlangıç)

```
BAŞLIK: tests/test_new_endpoints.py içindeki fiyat testlerini mock'la

BAĞLAM: tests/PRE_EXISTING_FAILURES.md'ye göre şu 2 test, yfinance'in canlı
veri şekli değiştiği için kırık (ağa bağımlı, flaky):
  - TestFetchPriceSync::test_returns_expected_keys   (assert 1.0 == 150.0)
  - TestFetchPriceSync::test_rounds_price_to_four_decimals (assert 1.0 == 123.4568)

GÖREV:
1. Bu iki testte yfinance çağrısını mock'la (monkeypatch / unittest.mock) —
   sabit, deterministik bir fiyat DataFrame'i döndür.
2. Test artık ağ olmadan, her ortamda aynı sonucu vermeli.
3. Üretim kodunu (fiyat çeken fonksiyonu) DEĞİŞTİRME — yalnız testi düzelt.
   Eğer fonksiyon test edilebilir değilse (mock'lanamıyorsa), bunu PR
   açıklamasında belirt; kodu yeniden yazma.

DOSYALAR: tests/test_new_endpoints.py (+ gerekiyorsa tests/conftest.py'ye
  paylaşılan bir yfinance-mock fixture'ı).

KABUL KRİTERİ:
  - `python -m pytest tests/test_new_endpoints.py -q` ağsız ortamda yeşil.
  - Hiçbir gerçek yfinance çağrısı yok (mock'lu).
  - PRE_EXISTING_FAILURES.md'den bu 2 satır kaldırılabilir hale geldi.

RİSK: Düşük. ORTAK KURALLAR geçerli.
```

---

## GÖREV 2 — Flaky prometheus testini sabitle (P0)

```
BAŞLIK: tests/test_prometheus.py::test_server_port_in_use flaky'sini gider

BAĞLAM: Bu test Windows'ta port-yeniden-kullanım semantiği yüzünden flaky
("DID NOT RAISE OSError"). PRE_EXISTING_FAILURES.md'de bilinen-fail.

GÖREV:
1. Testi deterministik yap: ya port çakışmasını mock'la/simüle et, ya da
   platforma göre koşullu skip uygula (Windows'ta skip + net gerekçe).
2. Tercih: gerçek port bağlamak yerine, "port kullanımda" durumunu mock'la
   ki test platform-bağımsız ve hızlı olsun.
3. Üretim prometheus kodunu değiştirme; yalnız testi düzelt.

DOSYALAR: tests/test_prometheus.py

KABUL KRİTERİ:
  - Test Linux ve Windows'ta deterministik (flaky değil).
  - Gerçek socket bağımlılığı yok veya güvenli şekilde izole.
  - `python -m pytest tests/test_prometheus.py -q` yeşil.

RİSK: Düşük. ORTAK KURALLAR geçerli.
```

---

## GÖREV 3 — CI'ı temizle + coverage gate'ini dürüst yap (P0)

```
BAŞLIK: .github/workflows/ci.yml — silinmiş 'views'i kaldır, 'academy'yi ekle

BAĞLAM: CI zaten `--cov-fail-under=70` ile coverage ölçüyor AMA:
  - artık silinmiş olan `views` modülünü ve `tests/test_views_integration.py`
    ignore'unu hâlâ referans alıyor (ölü).
  - YENİ `academy/` modülü --cov listesinde YOK → coverage gate academy'yi
    göremiyor (academy'nin 0 testi var, bkz. Görev 4).
  - 4 bilinen-fail (PRE_EXISTING_FAILURES.md) gate'i kirletiyor; Görev 1-2
    bunların 3'ünü çözüyor, auth fail'i ayrı (Görev kapsamı dışı, insan işi).

GÖREV:
1. ci.yml test adımından `--cov=views` ve `--ignore=tests/test_views_integration.py`
   referanslarını kaldır (modül artık yok).
2. `--cov=academy` ekle.
3. Coverage adımının güncel test takımıyla yeşil kaldığını doğrula (Görev 1-2
   merge edildikten sonra). Auth fail'i hâlâ kırıyorsa, onu ÇÖZME — PR
   açıklamasında "auth regresyonu ayrı, insan onayı bekliyor" diye belirt ve
   gate'in yeşil kalması için yalnızca o tek testi geçici `xfail` işaretle
   (gerekçeli, PRE_EXISTING_FAILURES.md'ye atıfla).
4. CI'ın academy testlerini de çalıştırdığını doğrula (testpaths zaten "tests").

DOSYALAR: .github/workflows/ci.yml (+ gerekiyorsa Makefile test-cov hedefi:
  --cov=core --cov=auth --cov=api --cov=academy ile hizala).

KABUL KRİTERİ:
  - ci.yml `views` referansı içermiyor; `academy` --cov'da.
  - CI test adımı yeşil (Görev 1-2 sonrası).
  - Coverage raporu academy'yi içeriyor.

RİSK: Düşük-orta (CI yapılandırması). ORTAK KURALLAR geçerli.
```

---

## GÖREV 4 — Academy'ye taban birim testleri (P0, 0→kapsam)

```
BAŞLIK: academy/ için deterministik taban test seti yaz (şu an 0 test)

BAĞLAM: academy/ modülünün HİÇ testi yok. Saf, deterministik kısımlar var:
  - academy/models.py — Lesson/Job/User repository'leri + init_db (SQLite).
  - academy/domains.py — 12 domain tanımı.
  - academy/agents/*.py — saf yardımcı mantık (LLM çağrısı OLMAYAN kısımlar).

GÖREV:
1. In-memory SQLite (veya tmp_path fixture) ile academy/models.py
   repository'lerinin CRUD davranışını test et (oluştur/oku/güncelle/listele).
2. academy/domains.py'nin 12 domaini doğru tanımladığını + yardımcı
   erişimcileri test et.
3. agents/ içindeki LLM-BAĞIMSIZ saf fonksiyonları test et. LLM çağıran
   kısımları mock'la — gerçek model çağrısı YOK.
4. init_db'nin idempotent olduğunu (iki kez çağrılabildiğini) doğrula.

DOSYALAR: tests/test_academy_models.py (yeni), tests/test_academy_domains.py
  (yeni). Gerekiyorsa conftest'e in-memory academy DB fixture'ı.

KABUL KRİTERİ:
  - `python -m pytest tests/test_academy_*.py -q` yeşil, ağsız, deterministik.
  - models.py repository'leri ve domains.py anlamlı kapsama sahip.
  - LLM/ağ çağrısı içeren hiçbir test yok (hepsi mock'lu).

RİSK: Düşük. ORTAK KURALLAR geçerli. (academy mantığını değiştirme — yalnız test.)
```

---

## GÖREV 5 — Veri pipeline'ı için schema/null guard testleri (P0-P1)

```
BAŞLIK: data_fetcher çıktısı + API payload için null/NaN/boş-veri testleri

BAĞLAM: FinPilot'un en sık kırılan yüzeyi eksik/bozuk veri (2 bilinen fail
yfinance shape değişiminden). scanner/data_fetcher.py OHLCV döndürür;
boş DataFrame, NaN, eksik kolon, tek-satır gibi kenar durumlarında pipeline'ın
çökmemesi gerekir.

GÖREV:
1. Sabit, sentetik DataFrame'lerle (gerçek ağ YOK) data_fetcher çıktısını
   tüketen fonksiyonların kenar durumlarını test et:
     - boş DataFrame, tek satır, eksik kolon (Volume yok vb.), NaN içeren satır,
       sıralanmamış / yinelenen index.
2. Beklenen davranış: çökme yok; ya güvenli boş sonuç ya da net hata.
   MEVCUT davranışı doğrula — düzeltme gerekiyorsa AYRI bir bug-fix PR'ında,
   dar kapsamlı ve guardrail'lerle (data_fetcher'ı yeniden yazma).
3. API payload doğrulaması: ilgili router'ların eksik/bozuk girdide 4xx
   döndürdüğünü (500 patlamadığını) test et — yalnız test, mantık değişikliği yok.

DOSYALAR: tests/test_data_pipeline_guards.py (yeni). Mevcut tests/test_data_fetcher.py
  varsa onu genişlet.

KABUL KRİTERİ:
  - `python -m pytest tests/test_data_pipeline_guards.py -q` yeşil, ağsız.
  - Boş/NaN/eksik-kolon/yinelenen-index senaryoları kapsanıyor.
  - Bir gerçek kırılma bulunursa: ayrı, dar bug-fix PR'ı + bu testle kanıt.

RİSK: Orta (gerçek bir bug ortaya çıkabilir → ayrı PR + insan review).
ORTAK KURALLAR geçerli.
```

---

## KULLANIM SIRASI VE NOTLAR

Sıra: **1 → 2 → 3 → 4 → 5.** Görev 1-2 bilinen-fail'leri çözer; Görev 3 gate'i dürüstleştirir (1-2 merge sonrası); 4-5 yeni kapsam ekler. Her görevi **ayrı PR** olarak ver; merge etmeden diff'i incele + CI yeşilini bekle.

**Kapsam dışı bırakılanlar (bilinçli):** auth regresyonu (`test_compute_surface_requires_auth`) — güvenlik fix'i, Jules taslak açabilir ama **insan onayı zorunlu**, bu 5 görüş paketine dahil değil. Skor/risk/strateji mantığı, canlı execution, geniş refactor — tamamen kapalı.

**Başarı ölçümü (paket sonrası):** 4 bilinen-fail → 1 (yalnız auth, insan kuyruğunda), academy 0 → taban kapsam, CI gate dürüst (views yok, academy var), pipeline guard'ları mevcut, sıfır yeni regresyon.
