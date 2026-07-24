# BÖLÜM 3 RAPORU — Bütünlük ve Sözleşme Sigortaları
**Tarih:** 2026-07-24 · **Plan:** UcaUca_Uygulama_Plani Bölüm 3 (TESHIS_paketi bulgularıyla genişletilmiş) · **Durum: KAPI ONAYI BEKLİYOR**
**Not:** Bölüm 2, Meriç kararıyla yarın sabahki yayına bağlandı (kanıtları o koşudan çıkacak); sıra bilinçli olarak 0→1→3 gitti.

## Yapılanlar ve kanıtlar

**3.1 → NUL kontrolü ONARILDI ✓ (teşhisin P0'ı)**
`snapshot_builder.py:440`: `b"\\x00"` → `b"\x00"` (literal metin araması → gerçek NUL baytı araması). Sabotaj testleri eklendi: NUL'lu dosya artık `ValueError` fırlatıyor, temiz dosya geçiyor (`tests/test_prepublish_gate.py`, Python 3.11 gerektirir — Windows süitinde koşacak).

**3.2 → Pre-publish kapısı KURULDU ✓**
Yeni `distribution/prepublish_gate.py`: yayından ÖNCE export'un yayınlanabilirliğini kanıtlamasını ister — bayat tarih, boş results, eksik sözleşme alanları (test_scanner_contract ile aynı küme), scan_complete=False ve **"bozuk koşu" tespiti** (0 grade'li + 0 eligible satır = zenginleştirme hiç çalışmamış). `publish_now` başında koşar; sorun varsa yayın DURUR (bilinçli geçiş: `--force`).
**Canlı doğrulama:** kapı, bugünkü gerçek bozuk export'u yakaladı → *"zenginleştirme boş görünüyor: 1801 satırda 0 grade'li ve 0 eligible satır"*. Yarın sabah tarama sağlıklıysa sessizce geçer; değilse seni durduracak — tam istenen davranış.

**3.3 → "Son yazan kazanır" sınıfı KAPANDI ✓**
- **Kanıt kopyası:** her başarılı yayında `scan_export_<tarih>_published.json` (varsa dokunulmaz) — bugün kaybolan kanıt bir daha kaybolamaz.
- **Bozuk-koşu koruması** (`api/routers/scan.py`): eşit boyutlu ama 0-zenginlikli koşu, dolu bir export'un üzerine YAZAMAZ — `scan_export_<tarih>_degraded_<saat>.json`'a yönlendirilir, `latest` korunur, log'a warning düşer.
- **run_id:** export'a koşu-özgü kimlik eklendi (scan_id sembol-kümesini, run_id koşuyu kimliklendirir — ikisi artık karışamaz).
- **Huni raporlayıcı:** yeni `scripts/funnel_report.py` — published kopya üzerinde aşama aşama eleme sayımı. İlk koşusu (bozuk export üzerinde) teşhisi doğruladı: `1801 → 1240 (dq) → 521 (direction) → 425 (edge) → 0 (GRADE aşamasında sıfırlanıyor)`. Gerçek seçicilik analizi yarın published kopyayla yapılacak.

**3.4 → company alanı DOLDURULDU ✓**
`snapshot_builder`'a `_company_from_db` eklendi: export'ta isim yoksa `symbols` tablosundan (13.852 kayıt) okur, borsa şablon eklerini kırpar ("... Common Stock"), önbellekli, hata durumunda sessizce boş — snapshot üretimini asla kıramaz. Test eklendi (RIOT → "Riot Platforms, Inc.").

**Testler:** sandbox'ta **20 passed, 3 skipped** (skip'ler 3.11 gerektiren testler — Windows'ta koşacak). Değişen 5 dosya py_compile temiz. Bölüm-0 tabanına yeni kırmızı yok.

## KAPI İÇİN SENİN ADIMLARIN

1. **Windows test doğrulaması:**
   ```powershell
   cd C:\Users\meric\Borsa
   python -m pytest tests/test_prepublish_gate.py tests/test_karne_chain.py -q
   ```
   Beklenen: **23 passed** (skip'siz). Sonra tam süit isteğe bağlı: taban 12 kırmızının üstüne yeni kırmızı OLMAMALI.
2. **Karar C — boş çekirdek tablolar (3.5):** `signals`, `scan_results`, `buy_signals` (+ `execution_intents/events/controls`) aylardır boş; üretim JSON-export üzerinden akıyor. Önerim: **resmen "emekli" ilan et** (şema kalır, silinmez; docs/INDEX'e not düşülür; Alpaca işi canlanırsa execution_* geri açılır). Alternatif: scan zincirini DB'ye de yazacak şekilde genişletmek — bugün için gereksiz iş.
3. **Commit+push (Bölüm 1+3 birlikte):**
   ```powershell
   git add distribution/karne.py distribution/archive_bridge.py distribution/prepublish_gate.py distribution/jobs.py distribution/snapshot_builder.py api/routers/scan.py scripts/publish_now.py scripts/daily_backup.py scripts/funnel_report.py tests/test_karne_chain.py tests/test_prepublish_gate.py .env.example
   git commit -m "Bolum 1+3: karne DB fallback, arsiv koprusu, pre-publish gate, NUL fix, degraded-run korumasi"
   git push
   ```

## YARIN SABAH — tek ritüel, üç bölümün kanıtı birden
Normal akış: tarama → `python scripts\publish_now.py --yes`. Çıktıda sırayla göreceklerin:
`PRE-PUBLISH GATE` sessiz (sorun yoksa) → draft/publish → `archive: {'archived': N}` → alarm yok → `published copy: ...` → `backup ok` → snapshot'ta `by_grade` DOLU (30g pencere). Sonra `python scripts\funnel_report.py` ile ilk gerçek seçicilik hunisini çıkar — çıktısını yapıştır, **eligible=2 sorusuna** birlikte cevap veririz.
Kapı, gate DURDURURSA da başarılıdır: o gün bozuk koşuyu yakalamış demektir — çıktıyı yapıştır, birlikte bakarız.

## Kapı kriteri
Kod+testler ✓ (kanıtlı) · Windows 23-test doğrulaması ⏳ · Karar C ⏳ · commit+push ⏳ · yarın sabah uçtan uca kanıt ⏳ → kapanınca **Bölüm 2** resmen işlenir (expired alarmı + süre logu + seri sayacı) ve ardından Bölüm 4 (web/dil + Karar B uygulaması).
