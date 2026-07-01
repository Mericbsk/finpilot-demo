# FinPilot — Google Jules / Asenkron Kodlama Ajanı için Test Stratejisi ve Kontrol Planı

**Tarih:** 2026-06-12 · **Kaynak:** FinPilot mevcut test durumu (`tests/PRE_EXISTING_FAILURES.md`, 67 test dosyası, CI), bu oturumda eklenen erken-yakalama katmanı (28 test) + audit raporları.

> **Uyarı:** Jules (veya benzeri asenkron ajan), bağımsız bir dalda çalışıp PR açan bir QA/kod-üretim aracıdır. Strateji beyni değildir; finansal karar mantığını ona icat ettirme. Aşağıdakiler yatırım tavsiyesi değil, mühendislik kalite planıdır.

---

## 1. YÖNETİCİ ÖZETİ

FinPilot, Jules için **olgun bir aday** — çünkü altyapı (pytest, ruff, mypy, pre-commit, 494 geçen test) hazır ama **ölçülebilir, deterministik test boşlukları** var: 4 bilinen test hatası (biri güvenlik), 2 kalıcı ignore'lu test takımı, **0 testli Academy modülü**, 21 router'ın ~13'ü yalnız happy-path smoke testli, ve Mayıs'tan beri **ölçülmemiş coverage**. Bunların hepsi Jules'ün en güçlü olduğu alan: tekrar eden hata, test açığı, regresyon riski.

**En değerli ilk kullanım** strateji icadı değil — **deterministik test boşluklarını kapatmak:** yfinance'e bağlı 2 kırık testi mock'la, flaky prometheus testini sabitle, Academy'ye taban test seti yaz, test-light router'ları tamamla, ignore'lu takımları çöz/emekli et, ve coverage ölçümünü CI'a geri getir.

**FinPilot'a özgü en kritik guardrail** (bu oturumda bizzat yaşandı): asenkron ajan **büyük dosyaları bozabilir.** Bu ortamın kabuk görünümü `data_fetcher.py` (1201 satır) ve `evaluate.py`'yi okurken kesti; dikkatsiz bir düzenleme bunları truncate edebilirdi. Bu yüzden her Jules PR'ında **tam-dosya bütünlük kontrolü + `py_compile`/import gate + git diff review** zorunlu olmalı. "Güzel görünen ama dosyayı bozan patch" gerçek bir risk.

**En önemli kural:** Jules'e testleri **davranışı** doğrulatmak için yazdır, **kârlılığı** değil. Bir testi geçirmek için skor formülünü "iyileştirmesine" asla izin verme — bu, edge ölçümünü (triple-barrier + Edge Report) sessizce bozar.

---

## 2. FİNPİLOT İÇİN EN SAĞLIKLI TEST TÜRLERİ

Mevcut duruma göre en yüksek getiri/maliyet oranına sahip olanlar (Bölüm 2 matrisinden FinPilot'a uyarlanmış):

**Çekirdek (P0) — deterministik, hızlı, yüksek etki:**
- **Birim testleri (saf fonksiyonlar):** scanner scoring (`score_engine`, `finpilot_score`), erken-yakalama (`features`, `watch_tier`, `labeling`, `edge_report` — bu oturumda 28 test ile başladı), risk hesapları (`risk_engine`). Ağ yok → deterministik → Jules için ideal.
- **Schema/null/edge-case testleri:** `data_fetcher` çıktısı, API payload doğrulama, NaN/boş DataFrame yayılımı. FinPilot'un en sık kırılan yeri burası (2 bilinen fail yfinance shape değişiminden).
- **Regresyon testleri:** `PRE_EXISTING_FAILURES.md`'deki bilinen vakalar + geçmişte bozulan watchlist/chart uçları (son haftalarda 3 fix commit'i).
- **Timestamp/zaman-dilimi hizalama:** haber-fiyat, market-closed/holiday — `earnings_blackout` ve çok-zaman-dilimi mantığı için.

**Orta (P1) — entegrasyon + tutarlılık:**
- Pipeline entegrasyonu (ingestion → scoring → alert), ama **dış veri mock'lanarak** (deterministik olması şart).
- Sıralama kararlılığı (aynı input → aynı skor → aynı sıralama).
- Snapshot testleri (kilit dashboard/özet çıktıları).

**İleri (P2) — yalnız insan onayıyla:**
- Backtest tutarlılığı / lookahead-leakage / walk-forward split — bunları Jules **doğrular** (test yazar), formül **değiştirmez**.
- Paper trading simülasyon guard'ları.

**FinPilot'a özel not:** Strateji-doğrulama testleri (lookahead, leakage, survivorship) çok değerli ama bunları "Jules yaz" derken dikkat — Jules testi yazabilir, ama testin *doğru bias'ı yakaladığını* insan doğrulamalı (yanlış-pozitif/negatif test, olmayan testten beterdir).

---

## 3. EN VERİMLİ JULES KULLANIM ALANLARI (FinPilot'ta somut)

| Alan | Neden FinPilot'ta verimli | Risk |
|---|---|---|
| **yfinance'e bağlı testleri mock'lama** | 2 bilinen fail bundan; deterministik hale getirir → CI yeşillenir | Düşük |
| **Academy'ye taban test seti** | 0 test → her test net kazanç; saf repository/model mantığı | Düşük |
| **Test-light router'ları tamamlama** | ~13 router happy-path smoke'lu; auth/scan/advisory dahil | Düşük-orta |
| **Flaky test sabitleme** | prometheus port testi Windows'ta flaky → izole, deterministik | Düşük |
| **Ignore'lu takımları çözme** | `test_signals.py` + `scanner_rollout/` ya düzelt ya resmî emekli et | Orta |
| **Coverage ölçümü + CI gate** | Mayıs'tan beri ölçülmüyor; Jules CI'a coverage adımı ekler | Düşük |
| **Schema/null guard'ları** | data_fetcher/API; FinPilot'un en kırılgan yüzeyi | Düşük-orta |
| **Snapshot testleri (refactor koruması)** | büyük dosyalar (watchlist 1019, scheduler 1247) parçalanırken | Orta |

---

## 4. KAÇINILMASI GEREKEN GÖREVLER (FinPilot'ta P2/yasak)

İlk aşamada Jules'e **verilmeyecek** işler, somut dosyalarla:
- **Skor ağırlıklarını değiştirme** — `score_engine.compute_recommendation_score` formülü, vol-rejim ağırlıkları, regime-gate çarpanları. Bunlar barrier-audit'le kalibre; "test geçsin" diye değiştirilemez.
- **Gated faktörleri "optimize etme"** — catalyst/squeeze/lottery/overnight ağırlıkları; bunlar ablation'la açılmalı, ajan sezgisiyle değil.
- **`evaluate.py` karar mantığı** — `entry_ok` kapısı, erken-tier eşikleri. (Jules buraya test yazabilir, mantığı değiştiremez.)
- **`risk_engine` core** — ATR/Yang-Zhang stop/TP çarpanları, Kelly, DD gate.
- **DRL reward / backtest etiketleme mantığı** — triple-barrier parametreleri dahil.
- **Canlı/paper trade execution** — emir üreten hiçbir kod.
- **Belirsiz görevler** — "performansı artır", "scanner'ı iyileştir", geniş kapsamlı refactor, veri-kalitesi doğrulanmadan backtest yeniden yazımı, hyperparameter search.

**Neden:** Jules geniş/belirsiz görevde "yanlış ama güzel görünen" patch üretir; finansal mantıkta bu, sessiz edge kaybı + yanlış kalibrasyon demektir.

---

## 5. AŞAMALI KULLANIM PLANI

**Aşama 1 — Güvenli giriş (1-2 hafta):** yfinance mock'lama (2 fail), flaky prometheus fix, Academy taban testleri, schema/null guard'ları. Hepsi deterministik, ölçülebilir, hızlı doğrulanır.

**Aşama 2 — Kalite artırma (2-4 hafta):** test-light router'ları tamamla, ignore'lu takımları çöz/emekli et, coverage ölçümü + CI gate, refactor koruması için snapshot testleri (önce watchlist.py/scheduler.py gibi tanrı-dosyalarına).

**Aşama 3 — Sistem genişletme (4-8 hafta):** pipeline entegrasyon testleri (mock'lu), alert açıklanabilirlik testleri, walk-forward split kontrolleri (Jules yazar, insan doğrular), erken-yakalama tier'larının gölge-mod ölçüm guard'ları.

**Aşama 4 — Kontrollü ileri kullanım:** core strateji/risk değişiklikleri **yalnız** insan onayı + zorunlu test paketi + çift review ile. Canlı sistem değişikliği için iki onay.

---

## 6. BAŞARI METRİKLERİ (FinPilot taban değerleriyle)

| Metrik | Bugünkü taban | Hedef |
|---|---|---|
| Bilinen test hatası | 4 (1'i güvenlik) | 0 |
| Ignore'lu test takımı | 2 (`test_signals`, `scanner_rollout`) | 0 (düzelt veya resmî emekli) |
| Academy test sayısı | 0 | ≥ taban kapsam (repository + model) |
| Test-light router | ~13/21 | ≤ 3 |
| Coverage ölçümü | yok (Mayıs'tan beri) | CI'da ölçülüyor + gate |
| Yeni regresyon (Jules sonrası) | — | 0 (CI compile+test gate) |
| İnsan müdahalesi | yüksek | azalır ama **diff review korunur** |

**Karar kuralı:** Bu metrikler iyileşmiyorsa Jules sadece "kod yazan araç" olarak kalır. Coverage artışı + bilinen-fail düşüşü + sıfır yeni regresyon = değer üreten asistan.

---

## 7. ÖNERİLEN İLK GÖREV LİSTESİ (sıra + kabul kriteri)

1. **yfinance mock'lama** → `test_new_endpoints.py`'deki 2 fail. Kabul: testler ağsız geçiyor, deterministik. *(P0, izole)*
2. **Flaky prometheus testi** → `test_prometheus.py::test_server_port_in_use`. Kabul: Windows dahil deterministik (skip veya SO_EXCLUSIVEADDRUSE). *(P0)*
3. **Coverage tabanı + CI adımı** → `pytest --cov` + CI'a rapor. Kabul: coverage % görünür, gate eşiği konuldu. *(P0)*
4. **Academy taban testleri** → `academy/models.py` repository CRUD + `domains.py`. Kabul: 0 → anlamlı kapsam, hepsi deterministik. *(P0)*
5. **Schema/null guard'ları** → `data_fetcher` çıktısı + API payload. Kabul: eksik/NaN/boş DataFrame'de çökme yok, test kanıtlıyor. *(P0-P1)*
6. **Test-light router tamamlama** → auth/scan/advisory/watchlist happy-path ötesi. Kabul: hata yolları + auth kontrolleri test ediliyor. *(P1)*
7. **`test_signals.py` + `scanner_rollout/`** → güncel sinyal kontratına göre düzelt veya `archive/`'a resmî emekli et. Kabul: ignore listesi boşaldı. *(P1)*
8. **Auth regresyonu için kanıt-testi** → `test_compute_surface_requires_auth`'u yeşile çevirecek **failing test + require_auth restorasyonu taslağı**. Kabul: Jules taslak açar, **insan review eder** (güvenlik). *(P1, insan onaylı)*

Hepsi deterministik, ölçülebilir, hızlı doğrulanır — sağlıklı başlangıç noktaları.

---

## 8. RİSKLER VE GUARDRAILS (FinPilot'a özel)

- **Büyük-dosya bozulması (bu oturumda yaşandı):** ajan `data_fetcher.py`/`evaluate.py`/`watchlist.py`/`scheduler.py` gibi 1000+ satırlık dosyaları kısaltabilir/bozabilir. **Guardrail:** her PR'da satır-sayısı/bütünlük kontrolü + `py_compile` + import smoke + git diff review. Asla kör merge yok.
- **Determinizm:** yfinance/ağ çağrıları flaky test üretir. **Guardrail:** Jules'ün yazdığı her test dış veriyi mock'lamalı; ağa çıkan test reddedilir.
- **Edge'i sessizce bozma:** test geçirmek için skor/risk mantığını değiştirmek. **Guardrail:** `score_engine`, `evaluate` karar bloğu, `risk_engine`, `labeling` parametreleri "salt-okunur" ilan; bu dosyalarda mantık değişikliği = otomatik insan review.
- **Yanlış-pozitif test:** bias-yakalama testi yanlış yazılırsa güven verir ama korumaz. **Guardrail:** strateji-doğrulama testleri insan tarafından bir "bilinen-kötü" vakayla sınanmalı (test gerçekten yakalıyor mu?).
- **Kapsam kayması:** "küçük fix" geniş refactor'a dönüşür. **Guardrail:** görev başına dosya/satır limiti; PR büyürse böl.
- **Güvenlik fix'leri:** auth gibi → Jules taslak, insan onay zorunlu (P1, otomatik merge değil).
- **CI tabanı:** CI Mart'tan beri bayat (academy'yi, coverage'ı kapsamıyor). **Önce CI'ı güncelle**, sonra Jules PR'larını ona dayandır — yoksa gate yok.

---

## 9. SON KARAR VE TAVSİYE

Jules FinPilot için **evet, ama dar ve test-ağırlıklı bir kapıdan.** En sağlıklı kullanım: deterministik test boşluklarını kapatmak (yfinance mock, Academy testleri, router tamamlama, coverage gate, flaky fix) ve regresyon koruması kurmak. Bu, mevcut 4 bilinen-fail + 2 ignore + 0-test-Academy + ölçülmeyen-coverage tablosunu hızla düzeltir ve her adımı ölçülebilir kılar.

**Asla** strateji beyni yapma: skor formülü, risk core, DRL reward, gated faktör ağırlıkları, canlı execution Jules'e kapalı (en fazla test yazar, mantık değiştirmez — insan review). Bu oturumdaki büyük-dosya bozulma olayı, en somut FinPilot guardrail'ini verdi: **her PR tam-dosya bütünlük + compile + diff review gate'inden geçmeli.**

**Tek cümle:** Jules'ü FinPilot'ta bir kalite-güvence mühendisi olarak konumla — önce kırık/eksik testleri deterministik biçimde kapattır, coverage'ı görünür yap, ve her değişikliği compile+diff gate'iyle koru; strateji ve riski insan onayına sakla.
