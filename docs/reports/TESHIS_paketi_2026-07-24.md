# TEŞHİS PAKETİ RAPORU — 1.1 / 1.2 / 3.1 / 3.3
**Tarih:** 2026-07-24 · **Tür:** Salt-okunur teşhis (hiçbir dosya değiştirilmedi) · **Plan:** UcaUca_Uygulama_Plani Bölüm 1 ve 3'ün ön-audit'i

---

## 1.1 — Arşiv neden 2026-05-22'de durdu? ✅ KÖK NEDEN BULUNDU

**Zincir haritası (kod kanıtlı):**
```
POST /watchlist/archive (api/routers/watchlist.py) → data/signal_archive/<tarih>.json
→ scripts/migrate_signal_archive_to_sqlite.py → signals_archive tablosu
→ core/scheduler.py::_run_resolve_open_signals_job (Pzt 03:00, haftalık) → resolved_* kolonları
```
**Kök neden:** Zincirin HER halkası "sürekli çalışan API + scheduler" mimarisine bağlı. Temmuz pivotuyla (manuel yayın, API kapalı) üç halka birden durdu. `data/signal_archive/` son dosyalar: 2026-05-22 + tek başıboş 2026-06-01 (52 dosya). Kaza değil — mimari emeklilikte unutulan bağımlılık.

**İyİ SÜRPRİZ 1:** `watchlist_signals` tablosu BUGÜNE KADAR CANLI (12 May → 24 Tem, 999 kayıt; bugün 25 yeni). Yaşam döngüsü de işliyor: resolved_loss 620, resolved_win 48, watching 260. Yani günlük sinyal kaydı VE sonuç takibi hâlâ yaşıyor — sadece signals_archive'a kopyalanmıyor.

**İyİ SÜRPRİZ 2:** signals_archive'ın 5719 kaydının **5594'ü zaten çözümlenmiş** (resolved_win 1571 · resolved_loss 3789 · expired 234). Açık sadece ~125 satır. "Tarihi çözümleme" işi (plan 1.4) sanılandan ÇOK küçük.
*(Not: ham isabet %29.3 — barrier etiketiyle %30.0. Karne dürüstlüğü tartışmasında bu sayı masada olmalı; A/B/C kırılımı ve dönem filtresi işin rengini değiştirebilir, Bölüm 1'de hesaplanacak.)*

## 1.2 — Karne neden boş? ✅ KÖK NEDEN BULUNDU (ve fix kolay)

`distribution/jobs.py::_fetch_karne()` karneyi **yerel API'den** çekiyor:
`http://localhost:8000/api/v1/watchlist/performance?days=5`
Sabah yayınında API **kapalı** → `urlopen` düşer → `karne=None` → snapshot'a "karne unavailable" + `by_grade:{}`. Veri var (watchlist sonuçları), köprü HTTP'ye bağımlı olduğu için kopuk.

**Önerilen fix (Bölüm 1):** `_fetch_karne`'ye API-yoksa **doğrudan DB'den hesapla** fallback'i (watchlist_signals: conviction_tier × status_lifecycle). HTTP bağımlılığı biter; API açıkken davranış değişmez. + `days=5` penceresi kararı (5 gün çok dar — kapıda konuşulacak).
`resolve_open_signals.py` sağlam görünüyor (dual-label, dry-run'lı, yfinance). Haftalık job'u manuel akışta ölü — resolver publish_now zincirine hafif adım olarak eklenmeli (plan 1.3/1.7 ile örtüşür).

## 3.1 — Bütünlük kapısı VAR MI? ⚠️ VAR AMA BİR KRİTİK DELİK

Mevcut ve sağlam: `read_json_object` (boş/çok-JSON/obje kontrolü, gürültülü hata) ✓ · bayat-tarih kapısı (job_draft, admin DM'li) ✓ · `validate_scan_export`→`full_scan_problems` (universe/tamlık) ✓ · atomic write (tmp+replace) ✓ · E6 bakım job'u (DB integrity+budama — uykuda; Bölüm 0 yedeği fiilen yerini aldı) ✓

**KIRIK OLAN — NUL kontrolü çalışmıyor (P0, tek satır):**
`snapshot_builder.py:440` → `if b"\\x00" in raw:` — kaynakta çift ters bölü. Gerçek NUL baytını değil, düz metin `\x00` dizisini arıyor. Geçmişteki NUL-bozulmalarının kapıdan sessizce geçmesinin muhtemel açıklaması bu. Fix: `b"\\x00"` → `b"\x00"` (tek karakter değişikliği + sabotaj testi).

## 3.3 — eligible=2 seçicilik analizi → ❗ DAHA BÜYÜK BİR BULGUYA DÖNÜŞTÜ

Analiz sırasında çelişki çıktı: bugünkü `scan_export_latest.json`'da 1801 satırın **TAMAMI** selection_eligible=False, tier/conviction boş, conviction_prob=0, data_quality %100 partial/missing — simülasyonda aday sayısı **0**. Ama yayınlanan snapshot'ta RIOT (B) + DVN (C) var ve scan_id'ler "aynı".

**Çözüm — üç katmanlı bulgu:**
1. **scan_id koşuyu değil, sembol listesini kimliklendiriyor** (`scan.py:739` — sorted sembollerin sha256'sı). Aynı 1801 sembolle koşan HER tarama aynı scan_id'yi üretir. Snapshot↔export eşleşmesi yanıltıcı.
2. **Bugün birden fazla tam tarama koştu** (5 partial + ≥2 tam; dosya saatleri 13:53–15:01). Snapshot 14:59'da grade'li bir export'tan üretildi; **15:01'deki son koşu** (enrichment'ı boş/kırık) eşit boyutta olduğu için `latest` VE tarihli dosyanın üzerine yazdı. "Son yazan kazanır" — yayında kullanılan zenginleştirilmiş export **kayboldu**.
3. **Sonuç:** (a) seçicilik hunisi şu an ölçülemez — yayın anındaki export korunmuyor; (b) daha tehlikelisi: kalitesi bozuk bir koşu yayından ÖNCE gelirse gün 0 adayla, sessizce yayınlanır. `existing_is_larger` koruması yalnız KÜÇÜLMEYİ engelliyor, eşit-boy bozuk koşuyu engellemiyor.

**Önerilen fix (Bölüm 3):** ① yayın anında kullanılan export'un dokunulmaz kopyası (`scan_export_<tarih>_published.json` — publish_now içinde) ② `latest` üzerine yazmadan önce **zenginlik kapısı** (ör. tier'lı satır ≥1 VEYA conviction_prob>0 satır sayısı eşiği; değilse partial gibi kenara yaz) ③ scan_id'ye koşu-özgü bileşen (timestamp) ④ seçicilik hunisi raporu, korunmuş published kopya üzerinden.

---

## KAPILARA ETKİSİ

**Bölüm 1 küçülüyor ve netleşiyor:** 1.1 teşhis ✓, 1.2 teşhis ✓ (plandan düşülür). 1.3 "arşive yazma" = watchlist→archive köprüsünü publish zincirine almak. 1.4 "tarihi çözümleme" = yalnız ~125 açık satır + mevcut 5594 çözümden by_grade üretimi. 1.5-1.7 aynı. Efor 2-3 günden ~1.5 güne iner.
**Bölüm 3 büyüyor:** 3.1'e NUL-fix (tek satır, P0) ve 3.3'e "published kopya + zenginlik kapısı + koşu-id" eklenir. eligible=2 sorusunun cevabı ancak korunmuş kopyayla verilebilir.
**Bugün için operasyonel not:** Yarın sabahki tarama `latest`'i taze tarihle yazacağı için bayat-kapı sorun çıkarmaz; ama yarınki koşu da "boş enrichment" üretirse brif 0 aday çıkar. Yarın publish öncesi snapshot'taki aday sayısına bak — 0 ise dur, bana yaz.

_Sonraki adım: Bölüm 0 kapısının kalan 2 maddesi (pytest tabanı + OneDrive/AV) → kapı onayı → Bölüm 1 onarımları bu teşhisle başlar._
