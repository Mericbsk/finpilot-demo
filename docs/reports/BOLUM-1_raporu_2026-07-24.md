# BÖLÜM 1 RAPORU — Karne Zincirinin Diriltilmesi
**Tarih:** 2026-07-24 · **Plan:** UcaUca_Uygulama_Plani Bölüm 1 (TESHIS_paketi ile küçültülmüş kapsam) · **Durum: KAPI ONAYI BEKLİYOR**

## Yapılanlar ve kanıtlar

**1.5 → Karne artık API'siz çalışıyor ✓**
- Yeni dosya `distribution/karne.py`: karneyi doğrudan `finpilot.db`'den hesaplar (watchlist_signals: conviction_tier × status_lifecycle; CONFIRM→B/TRIGGER→C eşlemesi snapshot_builder ile birebir). Sadece KAPALI sonuçlar sayılır (resolved_win/loss) — açık sinyal asla gözlem sayılmaz. Pencere: `FINPILOT_KARNE_WINDOW_DAYS` (varsayılan 5).
- `distribution/jobs.py::_fetch_karne`: API erişilemezse veya boş dönerse DB fallback devreye girer. API açıkken davranış DEĞİŞMEDİ.
- Gerçek DB testi: `days=5 → B:{n:9, hit_rate:0.0}, C:{n:3, hit_rate:0.0}` · `days=30 → B:{n:36, hit_rate:0.028}, C:{n:23, hit_rate:0.0}`.
- Web şekil uyumu doğrulandı: LedgerStrip/ledgerSnapshot.ts tam bu şemayı bekliyor (`by_grade{n,hit_rate}` + `window`).

**1.3 + 1.7 → Arşiv köprüsü + süreklilik alarmı ✓**
- Yeni dosya `distribution/archive_bridge.py`: her başarılı publish sonrası günün public adayları `signals_archive`'a yazılır (deterministik id = sha256(sembol|tarih) → idempotent; `resolved_status='new'`). Satırlar watchlist_signals'tan zenginleştirilir (entry/SL/TP/score/tier — resolver'ın beklediği alanlar; watchlist satırı yoksa snapshot metrics fallback'i).
- `check_archive_continuity()`: arşiv 2+ işlem günü (hafta sonu toleranslı) büyümezse publish çıktısında YÜKSEK SESLE uyarı + admin Telegram DM. İki ay fark edilmeyen sessiz-ölüm sınıfı kapandı.
- `scripts/publish_now.py` zinciri artık: yayın → arşiv köprüsü → süreklilik kontrolü → günlük yedek.
- Kanıt (DB kopyasında uçtan uca): RIOT `entry:23.88 sl:21.74 tp:31.0 tier:B score:66.03`, DVN `entry:45.29 sl:43.96 tp:49.73 tier:C` yazıldı; 2. koşu `archived:0 skipped:2` (idempotent ✓); bayat DB'de alarm metni üretildi, güncel DB'de sustu ✓.

**Testler ✓**
Yeni `tests/test_karne_chain.py` — 12 test (karne matematiği, pencere, CONFIRM eşlemesi, idempotenlik, zenginleştirme, fallback, alarm): sandbox'ta **12/12 yeşil**. 5 değişen/yeni dosya py_compile temiz. Bölüm-0 tabanına yeni kırmızı beklenmiyor (yeni testler bağımsız, stdlib-only).

## ⚠️ KAPIDA KONUŞULACAK GERÇEK — dürüst karne acımasız çıkacak
Son 30 günün kapalı sonuçları: **B: 1 isabet/36 · C: 0/23**. Yarın karne dolduğunda web bunu gösterecek. Bu, ürünün "dürüst karne" vaadinin ta kendisi — ama Masthead'deki "%68 backtested win rate" ifadesiyle yan yana ağır çelişki üretir (backtest ≠ canlı, ama okuyucu bunu bilmez). Ayrıca dünkü loss-ağırlıklı dağılım seçicilik sorunuyla (Bölüm 3.3) bağlantılı olabilir: eleme hunisi zayıf adayları geçiriyor olabilir. Karar senin — seçenekler aşağıda.

## KAPI İÇİN SENİN ADIMLARIN

1. ~~**Resolver koşusu (1.4)**~~ ✅ TAMAMLANDI (2026-07-24 17:09): 93 satır çözümlendi (t5=91, barrier=93, unresolvable=0). DB doğrulaması: 'new' sınıfı SIFIRLANDI; win 1571→1602, loss 3789→3850. Kalan 32 açık satır Mart tarihli, verisi çekilemeyen (muhtemelen delist) semboller — arşivin %0.6'sı, kabul edilebilir artık; ısrar ederse 'unresolvable' işaretlenir.
2. **Yarın sabah uçtan uca kanıt:** normal ritüel (tarama → `python scripts\publish_now.py --yes`). Çıktıda sırasıyla şunları GÖR: `archive: {'archived': N, ...}` · alarm YOK · `backup ok` · snapshot'ta `by_grade` DOLU (ve web /demo'da LedgerStrip gerçek veri). Yayın ÖNCESİ aday sayısı 0 ise DUR (teşhis raporundaki enrichment riski).
3. ~~**Karar A — karne penceresi**~~ ✅ KARAR: **30 gün**. Uygulandı: `.env` + `.env.example`'a `FINPILOT_KARNE_WINDOW_DAYS=30` eklendi (2026-07-24).
4. ~~**Karar B — Masthead istatistiği**~~ ✅ KARAR: **Süreç istatistiği.** Masthead'de oran yerine şeffaflık sayısı ("5.700+ pick publicly tracked since Sep 2025" formunda); grade bazlı isabet oranları yalnız LedgerStrip'te, pencere etiketiyle. Not: Masthead kodu zaten "karne doluysa canlı, değilse etiketli backtest" mantığında — değişiklik: canlı ağırlıklı oran yerine süreç sayısı basılacak. **Uygulama: Bölüm 4.1'e eklendi.** Ek bulgu: Hero/HeroGrid.tsx (BUY/SELL mock'lu) landing'de import edilmiyor — ölü kod; dashboard/backtest sayfasında rastgele üretilmiş sahte winRate var (satır 37) — ikisi de Bölüm 4 temizlik listesine.
5. **Commit+push:** `git add distribution/karne.py distribution/archive_bridge.py distribution/jobs.py scripts/publish_now.py tests/test_karne_chain.py` → commit → push. İstersen önce `python -m pytest tests/test_karne_chain.py -q` (12 passed görmelisin).

## Kapı kriteri
Kod+testler ✓ (kanıtlı) · resolver koşusu ⏳ · yarın sabah uçtan uca kanıt ⏳ · Karar A/B ⏳ · commit ⏳ → hepsi kapanınca **Bölüm 2** (yayın disiplini + süre ölçümü; expired alarmı teşhisle hazır).
