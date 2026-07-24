# BÖLÜM 0 RAPORU — Zemin Güvencesi
**Tarih:** 2026-07-24 · **Plan:** FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md · **Durum: ✅ KAPI KAPANDI (2026-07-24)**

## Kapı kapanış kaydı
- 0.3: Borsa klasörü OneDrive kapsamında DEĞİL (doğrulandı) + Windows Defender dışlaması `data\` için eklendi ✓
- 0.4 pytest tabanı: **707 geçti · 12 kırmızı · 6 atlanmış** (377 sn). Bilinen kırmızılar: test_squeeze_factor (2), scanner_rollout/test_runtime_baseline (2) + 8 diğer. Kural: bu 12'lik taban SABİT — sonraki bölümlerde yeni kırmızı = regresyon. Tam listeyi hızlı almak için (yeniden koşmadan): `python -m pytest --lf --collect-only -q`
- 0.5: commit + push tamamlandı ✓
- Sonraki bölüm: BÖLÜM 1 (teşhis raporuyla küçültülmüş kapsam — bkz. TESHIS_paketi_2026-07-24.md)

## Yapılanlar ve kanıtlar

**0.1 Tam yedek — TAMAM ✓**
`backups/2026-07-24/` içinde: finpilot.db (7.3 MB), distribution.db, academy.db, finsense_academy.db + snapshot_latest / snapshot_en_latest / scan_export_latest / demo_snapshot JSON'ları.
Restore provası: yedek DB'ler açıldı, üçünde de `PRAGMA integrity_check = ok`, tablo sayıları doğru (23/9/10), signals_archive=5719 kayıt yedekte doğrulandı. Snapshot JSON yedekten okundu (date=2026-07-24).

**0.2 Tekrarlayan yedek — TAMAM ✓ (Windows smoke testi kapıda)**
- Yeni dosya: `scripts/daily_backup.py` — sqlite backup API + dosya-kopyalama fallback'i; her kopya sonrası yerel temp üzerinde integrity_check (WAL kurtarması güvenli); 14 günden eski yedekleri budar; `FINPILOT_BACKUP_EXTERNAL_DIR` tanımlıysa pazartesileri OneDrive-dışı klasöre haftalık ayna kopya.
- `scripts/publish_now.py` değişikliği (küçük, yayın başarısını bozamaz):
  ```python
  print("Publication completed: ...")
  try:
      from scripts.daily_backup import run_backup
      run_backup()
  except Exception as exc:
      print(f"WARNING: daily backup failed: {exc}", file=sys.stderr)
  return 0
  ```
- Test: `python3 scripts/daily_backup.py` → `backup ok → backups/2026-07-24 | files: 6`; her iki dosya `py_compile` temiz.
- `.env.example`'a `FINPILOT_BACKUP_EXTERNAL_DIR` eklendi.
- Geliştirme sırasında yakalanan 3 hata (sandbox dosya sistemi): backup API disk I/O → fallback eklendi · unlink engeli → üzerine-yazma · mode=ro WAL kurtaramama → temp-kopya doğrulama. Üçü de script'i Windows'ta da daha dayanıklı yapan düzeltmeler.

**0.4 Test tabanı — KISMEN (sandbox sınırı belgelendi)**
Sandbox'ta 351 test toplandı; 27 toplama hatasının 22'si `datetime.UTC` (repo Python ≥3.11 istiyor, sandbox 3.10), kalanı eksik bağımlılık. **Tam süit yalnızca senin makinede koşabilir** (aşağıda).

**0.5 Git — KISMEN**
Son commit: `adb3b59 2026-07-24 15:01 "Enrich public daily scan snapshot metrics"` (bugün — repo canlı). İzlenen dosyalarda bekleyen değişiklik görünmüyor (0.2'nin iki dosyası hariç). Sandbox git commit YAZAMIYOR (.git nesne yazımı silme korumasına takılıyor) → commit+push sende.

## KAPI İÇİN SENİN 3 ADIMIN (Windows, ~20 dk)

1. **0.3 OneDrive/AV dışlaması (kök neden önlemi):**
   - OneDrive ayarları → Senkronizasyon → `Borsa\data` ve `Borsa\backups` klasörlerini senkron DIŞI bırak (ya da "Always keep on this device" + çakışma korumasını kapat).
   - Windows Güvenliği → Virüs koruması → Dışlamalar → `C:\Users\meric\Borsa\data` klasörünü ekle.
   - Kanıt: ekran görüntüsü ya da "yaptım" onayı.
2. **0.4 Test tabanı:**
   ```powershell
   cd C:\Users\meric\Borsa
   .\.venv\Scripts\python -m pytest -q --tb=no 2>&1 | Select-Object -Last 5
   ```
   Son satırları buraya yapıştır (kaç geçti/kaç kırmızı — kırmızılar ŞİMDİ düzeltilmez, sadece taban kaydı).
3. **0.5 Commit+push:**
   ```powershell
   git add scripts/daily_backup.py scripts/publish_now.py .env.example
   git commit -m "Add verified daily backup step to manual publish flow (Bolum 0)"
   git push
   ```
   İlk publish_now koşusunda çıktının sonunda `backup ok → backups\<tarih>` satırını gör — 0.2'nin Windows smoke testi budur.

## Kapı kriteri
Yedek ✓ (kanıtlı) · restore ✓ (kanıtlı) · tekrarlayan yedek ✓ (kod+test; Windows smoke bekliyor) · dışlama kuralı ⏳ · pytest taban ⏳ · commit/push ⏳.
**Üç ⏳ kapanınca Bölüm 0 kapısı onaylanır → Bölüm 1 (Karne) başlar.**
