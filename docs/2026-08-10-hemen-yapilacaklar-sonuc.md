# "Hemen" Öncelikleri — Sonuç Raporu (2026-08-10, üçüncü tur)

Statü: Level A (araştırma, üretim değişikliği yok). Önceki sentez raporunun (`2026-08-10-iki-belge-kapsamli-sentez.md`) "Hemen" bölümündeki üç madde işlendi.

---

## 1. REVERSE-RANKING — RESMİ OLARAK KAPATILDI

**Yöntem:** Önceki turun iki eksiği giderildi: (a) `full_universe_enriched.csv`'de aynı-(symbol,scan_date) için **en-erken-scan_ts** satırı tutan gerçek dedup uygulandı (scanner saatlik ateşlendiği için %48 çift vardı — bkz. §3), (b) tek IS/OOS ayrımı yerine **4 çeyreklik pencere** + her pencerede **gerçek matched-random-kontrol** (birkaç seed) eklendi.

**Yan-bulgu (önemli):** Dedup sonrası composite_score'un güvenilir kapsamının yalnız **2026-05-06 → 2026-07-13 (39 işlem-günü)** olduğu ortaya çıktı — bu tarihten önceki satırlarda composite_score boş/NaN. Yani hem bu turdaki hem önceki turdaki tüm composite_score-tabanlı testler aslında "Eylül 2025 – Temmuz 2026 geneli" değil, bu **dar 39-günlük pencerede** çalışıyordu. Bu, kapsam iddialarının gözden geçirilmesini gerektiren ayrı bir not.

**Sonuç (gün-kümeli, dedup'lu):**

| Pencere | ALT-%20 vs ÜST-%20 | ALT-%20 vs RANDOM |
|---|---|---|
| Q1 (9 gün) | ✅ anlamlı (t~+3.53) | ✅ anlamlı |
| Q2 (9 gün) | ✅ anlamlı (t~+2.89) ama RANDOM da ÜST'ü geçiyor — ÜST kötü, ALT özel değil | karışık |
| Q3 (9 gün) | ✗ anlamsız (t~-0.50) | ✗ anlamsız |
| Q4 (12 gün) | ✗ anlamsız (t~-0.16), devasa outlier'lar (günlük +134/+176%, veri-hatası şüphesi) | ✗ anlamsız |
| **TAM DÖNEM (34 gün)** | **✗ anlamsız (t~-0.14)** | **✗ anlamsız (tüm seed'lerde)** |

**Karar: KAPATILDI.** Reverse-ranking, dört çeyrekten yalnız ikisinde (ve o ikisinden birinde de "ALT özel değil, ÜST kötü") görünüyor; tam-dönem toplamda hem ÜST'e hem rastgele-kontrole karşı anlamsız. Bu, **tutarlı bir sinyal değil, dönem-özel gürültü/artefakt.** Üretime, stratejiye veya "aday" listesine taşınmayacak. Programın "aynı-gün kümelenme + kısa-pencere yanıltır" uyarısının ikinci kez doğrulanmış hâli.

---

## 2. EXTENSION/EXHAUSTION — entry_ok'UN RESMİ TEŞHİSİ

**Bulgu (önceki turdan, burada resmileştiriliyor):** ATR-extension (20 günlük getiri/ATR) deciline göre `entry_ok`(eligible)-oranı **~15 kat** artıyor: [0.0, 0.4, 0.5, 1.4, 2.1, 3.9, 4.3, 7.5, 6.8, 5.3]%. Destekleyici ikinci kanıt: `composite_score ↔ dist_52w_high` r=+0.663.

**Resmi teşhis:** `entry_ok`, tasarım gereği ya da yan-etki olarak, **zaten fiyat-hareketini tamamlamış (uzamış) isimleri sistematik olarak seçiyor.** Bu, önceden bilinen iki inversiyonun (eligible < rejected; conviction A < B < C) ilk somut nedensel açıklaması: sistem "kaliteli" diye işaretlediği isimler aslında mean-reversion'a en yakın, tükenmiş kurulumlar.

**Aksiyon-önerisi (henüz uygulanmadı, Level B karar gerektirir):** `entry_ok` kriterlerine bir **extension-tavanı** (örn. "son-20g-getiri/ATR belirli bir eşiği aşarsa ele") eklemenin eligible-cohort kalitesini iyileştirip iyileştirmediği ayrı test edilebilir — bu, programın ilk **aksiyon alınabilir** düzeltme-adayı olabilir (concentration-kısıtından farklı olarak, doğrudan seçim-mantığına dokunuyor).

---

## 3. GÜNLÜK SEMBOL-TEKRARI — AÇIKLANDI

**Bulgu:** `edge_recheck.csv`'nin 53.754 satırı yalnız **27.323 benzersiz (symbol, scan_date) çift** temsil ediyor — 13.062 çift (%48) birden fazla satırlı (max 17 tekrar, örn. NVDA 2026-05-19).

**Sebep:** Production scanner saatlik çalışıyor (`core/scheduler.py`, `interval_minutes=60`); aynı sembol aynı gün birden çok kez ateşlenip her seferinde `full_universe_enriched.csv`'ye yeni satır ekliyor, `composite_score` gün içinde hafifçe kayıyor (örn. 53→54) ama outcome (c2c5_net) aynı kalıyor (price_cache'ten tek-seferlik hesap).

**Etki değerlendirmesi:** Tekrar-sayısı ile composite_score/outcome arasında güçlü korelasyon yok (rank-r=0.032/0.026) — yön-yanlılığı yaratmıyor. Ama **örneklem-büyüklüğünü yapay şişiriyor** (53.754 "sinyal" aslında 27.323 gerçek fırsat) ve gün-ortalaması hesaplarında **sık-ateşlenen isimleri aşırı-temsil ediyor.** Bu turda kullanılan dedup (§1) bu sorunu düzeltti; **geçmişteki tüm satır-bazlı analizlerin (bu programın önceki tüm turları dahil) bu şişirilmiş n ile yapıldığı** not edilmeli — mutlak "n=53.754" büyüklüğü referans alınan hiçbir yerde artık öyle okunmamalı.

---

## 4. GÜNCEL DURUM

| Bulgu | Önceki statü | Şimdi |
|---|---|---|
| Reverse-ranking composite_score | Şüpheli (bir önceki turda düzeltildi) | **Resmen KAPATILDI** — artefakt, terk edildi |
| Extension/exhaustion mekanizması | Kanıtlandı | **Resmi teşhis** — entry_ok'un aksiyon-alınabilir düzeltme adayı |
| composite_score veri-kapsamı | Bilinmiyordu | **YENİ**: güvenilir yalnız 39-gün (2026-05-06→07-13) |
| Satır-bazlı örneklem büyüklükleri | "n=53.754" olarak okunuyordu | **YENİ**: gerçek benzersiz-fırsat n=27.323, %48 şişirilmiş |
