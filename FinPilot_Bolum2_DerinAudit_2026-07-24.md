# FinPilot — BÖLÜM 2 DERİN AUDIT: Bileşen Envanteri ve Tarama Durumu
**Tarih:** 2026-07-24 · **Tür:** Canlı doğrulama (kod + DB + dosya) · **Kaynak:** ön-tarama raporu Bölüm 2

> **Başlık bulgu:** Ön-tarama raporu, bugünkü sertleştirme commit'lerinden (`cbc09fc`, 18:51) **önceki** durumu yakalamış. Canlı denetim, raporun "açık/eksik" saydığı birçok P0/P1 maddesinin **kodda fiilen KAPALI** olduğunu gösteriyor. Sistem sanılandan iyi durumda.

---

## Bileşen bileşen denetim

### 1. Scanner + sözleşme — ✅ İYİ (soru çözüldü)
- **Contract-test VAR:** `tests/test_scanner_contract.py` + `tests/test_score_contract.py`. (Rapor "var mı?" diyordu → evet.)
- **eligible=2 kasıtlı seçicilik, bug DEĞİL:** `snapshot_builder._public_candidate()` dört kapı uyguluyor — grade var + `selection_eligible` + `execution_feasible` + `position_cap_reject` yok. `eligible_candidate_count = len(graded)`. Yani 1801 satırdan yalnız 2'si bu dört kapıyı geçti = bilinçli yüksek-konviksiyon shortlist.
- **"999 watchlist vs 2 eligible" çelişkisi çözüldü:** farklı popülasyonlar. `watchlist_signals`=999 kümülatif izleme geçmişi; eligible=2 bugünkü yayınlanabilir shortlist.

### 2. Distribution (integrity gate / P0-5) — ✅ KAPALI (rapor "kanıt yok" diyordu)
- **NUL-byte bütünlük kontrolü KODDA:** `snapshot_builder.py:471` → `if b"\x00" in raw: raise ValueError("JSON contains NUL bytes")`.
- **`validate_scan_export()`** (satır 500) + **`prepublish_gate.check_export_health()`**: tarih bayatlığı, zorunlu sözleşme alanları (`selection_eligible/entry_ok/execution_feasible/data_quality_tier/ranking_method`), `scan_complete`, ve "0 grade'li + 0 eligible" bozuk-koşu sınıfı denetleniyor. Sessiz-bozulma sınıfı kodda kapatılmış.

### 3. publish_now akışı — ✅ İYİ (güçlü ritüel)
`scripts/publish_now.py` incelendi:
- Prepublish gate → `--force` olmadan yayını durduruyor.
- `job_draft` → onay (interaktif ya da `--yes`) → `job_publish`; `web_pushed` başarısı doğrulanıyor.
- **Değişmez published-export kopyası** (satır 99-104): "sonraki bozuk tarama yayınlanan export'u eziyordu → seçicilik hunisi ölçülemez oluyordu. Bir daha asla." → çözüldü.
- **Her yayında otomatik yedek:** `scripts/daily_backup.run_backup()` (satır 117) → `backups/` altında 2. klasörün (07-24) açıklaması. **E6 tekrarlayan artık evet.**
- **Arşiv köprüsü + süreklilik alarmı:** durunca `notify_admin` ile yüksek sesli uyarı.

### 4. Web / Ledger landing — 🟡 BÜYÜK ÖLÇÜDE HAZIR (bir surfacing boşluğu)
- Bileşenler mevcut: `Masthead.tsx`, `LedgerStrip.tsx`, `FactCheckingDesk.tsx`, `Newsroom.tsx`, `ledgerSnapshot.ts`.
- **Masthead `tracked_total` okuyor** (Karar B) → re-publish sonrası "5.719 pick takip edildi" görünecek.
- **LedgerStrip akıllı:** `by_grade` boşsa scorecard'ı gizliyor, doluysa gösteriyor (`hasScorecard` guard). Yani boş karne çirkin görünmüyor.
- **Boşluk:** benim eklediğim `overall` bloğu (5206 işlem, +0.40%/işlem) henüz render edilmiyor. **EN snapshot → web tüketimi doğrulanamadı** (grep'te web'in `snapshot_en`'i çektiğine dair kanıt yok; EN üretiliyor ama tüketim belirsiz).

### 5. Karne / resolver — ✅ ONARILDI (Bölüm 1)
`archive_bridge.py` yazıyor + süreklilik alarmı; `karne.py` olgunluk kapısı + beklenen getiri + `overall` track record (5/5 test). Grade kırılımı olgunlaşınca (~1 ay) dolar. Detay: Bölüm 1.

### 6. Execution / Alpaca — 💤 UYKUDA ama SAĞLAM VARLIK (ölü kod değil)
`execution/gateway.py` = "Safety-first scanner-to-paper-order gateway"; `ExecutionRejected` (execution sözleşmesi), paper modu, `reconciliation.py`, `repository.py`, `worker.py`. Yapı tam ve güvenli. `execution_intents/events=0` → kurulu ama koşmuyor (bilinçli erteleme). `alpaca_orders=10` eski.

### 7. DRL / agents / llm — 💤 UYKUDA (varlık, aws anlatısı için)
Zengin ama koşmuyor; loglar Mart–Mayıs. Lansman kritiği değil; "Labs" kanıtı olarak paketlenebilir (koda dokunmadan).

### 8. Academy (Borsa web tarafı) — 🟡 ÖRNEK VERİ
`web/public/academy_lessons.json` = 1.1 KB — hâlâ örnek dosya. FinSense worker 9 ders üretti (4 published); gerçek export basılmadı. `/academy` sayfası hazır, veri bekliyor.

### 9. FinSense repo — ✅ ÇALIŞIYOR
Worker bugün koştu (n=6); `academy.db` bütünlük ok; 9 ders (4 published/5 draft). Export köprüsü kuruldu (`--json`).

### 10. Monitoring — 💤 ÖLÜ KONFİG
`monitoring/`: `alerts.yml` + `prometheus.yml` + `grafana/`, hepsi **20 Mayıs**'tan, dokunulmamış. Manuel akışa bağlı değil. Karar: ya kur ya resmen iptal et.

### 11. Backups — ✅ TEKRARLAYAN (rapordan iyi)
`backups/` = **2 klasör** (07-23 + 07-24). `daily_backup.py` her publish'te koşuyor. Rapordaki "tek klasör/kırılgan" → düzeldi. Kalan: off-site/ikinci kopya (tek disk hâlâ risk).

### 12. Test altyapısı — 🟡 KAPSAM İYİ, YEŞİL Mİ BİLİNMİYOR
52 test dosyası; contract-test + karne-chain testleri dahil. Sandbox'ta koşturulamadı (`from datetime import UTC` Python 3.10'da patlıyor + pytest yok). **Senin 3.11+ makinende `pytest -q` ile tam süit doğrulanmalı.** (Not: `UTC` importu 3.10 uyumsuz — 3.11+ şart.)

### 13. Auth / kullanıcı — ⚪ MVP / BELİRSİZ
`data/auth.db` **boş** (hiç tablo yok) — rapordaki 4 users/47 sessions başka bir store'da ya da kayıt yok. Premium/Stripe (DoD#9) test edilmedi. Lansman kritiği değil ama pre-launch teyit gerek.

---

## Revize edilmiş öncelik (canlı bulgulara göre)

**Rapordan KAPANMIŞ (artık P0/P1 değil):** contract-test ✓, integrity gate/P0-5 ✓, karne zinciri ✓, tekrarlayan yedek ✓, eligible seçicilik kasıtlı ✓, published-export kopyası ✓, arşiv alarmı ✓.

**Gerçekten açık kalan:**
1. **P1 — Test süiti yeşil mi?** 3.11+ makinede `pytest` koş; `UTC` import uyumu teyit et.
2. **P1 — EN snapshot → web tüketimi:** üretiliyor ama web çekmiyor gibi; tam-dil ya da anahtarı gizle kararı.
3. **P2 — Karne surfacing:** `overall` bloğunu LedgerStrip/Masthead'e ekle (re-publish sonrası).
4. **P2 — Yayın serisi disiplini:** "expired" olunca yüksek sesli admin uyarısı (arşiv alarmı var, broadcast expired alarmı eksik) + seri sayacı checklist'e.
5. **P2 — DB bozulma kök nedeni:** OneDrive/AV + SQLite WAL etkileşimi; dışlama kuralı yazılmadı. Off-site yedek yok (tek disk).
6. **P2 — Academy gerçek export + monitoring kararı + auth/premium teyidi.**

**Genel:** Ön-tarama ~60/100 demişti; canlı denetim, sertleştirme commit'leri sayesinde **çekirdek yayın + kanıt altyapısının fiilen sağlam** olduğunu gösteriyor. Kalan darboğaz artık kod değil, **doğrulama disiplini** (test süiti, EN tüketimi, seri disiplini) ve **veri olgunlaşması** (grade'li karne için ~1 ay).

---
_Durum: AKTİF · Canlı kod/DB/dosya kanıtına dayalı. Sonraki adım kullanıcı kararına bırakıldı._
