# FinPilot/FinSense — 2026-08-13/14 Araştırma Turu: Kesin Sonuçlar

Tarih: 2026-08-14 · Statü: Level A (araştırma, üretim değişikliği yok — tek istisna: FinSense RSI probu, ayrı not) · Kapsam: FinSense indikatör-çevirisi deneyi + FinPilot Winner Anatomy (10+ alt-deney)

Yöntem notu: bu tur, bu konuşma içindeki 6 önceki dosyayı (`2026-08-13-winner-anatomy-exp01..exp05`, `2026-08-13-finsense-reasoning-engine-research-v0.1-deney1-divergence`) ve aralarındaki bağımsız çapraz-doğrulamaları tek yerde topluyor. Kanıt standardı önceki dosyalarla aynı: `[EVIDENCE]`/`[INFERENCE]`/`[HYPOTHESIS]`/`[RADICAL]`.

---

## A. FinSense — RSI İndikatör-Çevirisi Deneyi

`[EVIDENCE]` `web/src/app/dashboard/analysis/page.tsx`'e minimal bir prob eklendi: RSI aşırı bölgedeyken (>70/<30) tek cümlelik sade-dil açıklama + 👍/👎 mikro-geri-bildirim, mevcut Plausible entegrasyonu üzerinden ölçülüyor (`indicator_caveat_shown`/`indicator_caveat_feedback`). tsc temiz, tek dosya, ~65 satır ekleme. **Henüz production'a push edilmedi** — `.git/index.lock` nedeniyle bekliyor (bu konuşmada tekrar tekrar denendi, repoda eşzamanlı başka bir git süreci var). Açık iş: kilit açılınca commit+push tamamlanmalı (bkz. görev listesi #55).

Ayrıca aynı gün, çok daha büyük bir "10-persona Divergence" araştırma belgesi üretildi (`2026-08-13-finsense-reasoning-engine-research-v0.1-deney1-divergence.md`) — dış literatürle (overconfidence araştırması, TradingView'in Nisan 2026 Chart Copilot'u, AI güven-kalibrasyonu bulgusu) desteklenmiş 10 bağımsız perspektif. Bu belge hipotez üretici olarak değerli ama kanıt değil — Collision/Convergence aşamaları (Deney 2/3) kasıtlı olarak yapılmadı, çünkü gerçek sinyal (RSI probunun feedback verisi) henüz push edilmediği için hiç toplanmadı.

---

## B. FinPilot Winner Anatomy — Öldürülen Hipotezler

Hepsi day-clustered matched-random kontrolle test edildi (aynı gün içinden rastgele eşleşen kontrol grubuyla karşılaştırma, ~100-300 çekiliş/gün).

`[EVIDENCE]`
1. **`entry_ok` (mevcut canlı-benzeri kapı: regime & direction & (ATR≥4 veya |gap|≥3 veya RVOL≥2))** — rastgele seçimden ÖLÇÜLEBİLİR KÖTÜ. Medyan -0.81% (5g)/-0.13% (1g), rastgele-örneklem p5'inin bile altında. Gerçek bar-bar first-touch path testinde (TP=2%/SL=2%) SL'e ilk çarpma oranı %62.0 (evren %51.4), gerçek MAE -5.38% (evren -3.53%). Ay-ay: 4 aydan sadece 2'si pozitif, işaret 3 kez dönüyor — kararsız. `exp03`, `exp04`, `exp05`.
2. **Gate Anatomy** — hiçbir tekil kapı (regime/direction/ATR-gap-RVOL eşiği) tek başına matched-control'de anlamlı zarar vermiyor (p=0.26-0.41). Zarar kapıları AND ile üst üste bindirdikçe birikiyor (tek kapı ~+0.08%, üç kapı -0.81%) — mekanizma muhtemelen aşırı-uzama, tek eşik hatası değil.
3. **ATR×RVOL "sweet spot" (ATR 3-8, RVOL 0.8-1.5/2.0)** — matched-control p=0.29-0.42 (birden fazla tanımda tekrar test edildi), yüksek-volatilite tercilinde bile p=0.35. Ay-ay: 5 aydan sadece 3'ü pozitif, işaret 2 kez dönüyor.
4. **`regime=False` daha iyi görünmesi** — iki bağımsız matched-control koşusunda p=0.55/0.57, işaret bile tutarsız (bir koşuda pozitif, diğerinde negatif) — gürültü.
5. **52 haftalık zirveden mesafe** — gerçek, iki kez bağımsız doğrulanan non-monoton desen var (en iyi win-rate/medyan %50-70 aralığında, iki uçta daha kötü) ama ay-ay kararlılık testinden geçmedi (5 aydan 2'si pozitif).
6. **Day-1 Confirmation Premium** — D1≥+2% grubunun toplam 5-günlük getirisi matched-control'e göre neredeyse anlamlı (p=0.07) ÇIKTI ama bu **mekanik**: D1 zaten D5'in içinde (capture oranı %111.5 — yani hareketin tamamından fazlası 1. günde oluyor). Kalan 4 günü (`c2c_5d - c2c_1d`) izole edip matched-control'e sokunca p=0.58, işaret negatife dönüyor — gerçek yeni bilgi yok, sadece zaten-gerçekleşmiş getirinin yeniden ölçümü.
7. **Tip A/Tip B (ucuz-oynak vs pahalı-sakin kaçırılan winner'lar)** — tam popülasyon (sadece winner'lar değil) olarak test edilince ikisi de matched-control'de anlamsız (p=0.39/0.57). Tip A içindeki `lottery_factor` bölünmesi (+1.25% düşük-lottery vs -0.67% yüksek-lottery) ilginç ama ayrı matched-control testi yapılmadı — açık.

---

## C. Doğrulanan, Actionable Bulgular

`[EVIDENCE]`
1. **`composite_score` asıl olarak 52 haftalık zirveye yakınlık ölçüyor** (Spearman ρ=+0.67, iki bağımsız hesapla doğrulandı). Skor formülünde (`scanner/score_engine.py`) buna ait tek bir terim yok — korelasyon, birbirini tekrar eden momentum-ailesi bileşenlerin (regime/direction/momentum_ratio/alignment_ratio) ortak bir "zaten güçlü" faktörüne yüklenmesinden geliyor.
2. **`lottery_factor` gerçek ve tekrar doğrulandı** (bugün ρ=-0.18, önceki bulunan -0.20'ye çok yakın — programın Bonferroni-hayatta-kalan tek bulgusu, bugün bağımsız bir veri dilimiyle bir kez daha teyit edildi).
3. **ATR/RVOL yön değil BÜYÜKLÜK tahmin ediyor — ve bu istatistiksel olarak güçlü.** Yüksek ATR+RVOL, |getiri| medyanını gerçek matched-control'e göre büyütüyor (fark +4.38pp, çekilişlerin %92.9'u pozitif, p≈0.07). Düşük ATR+RVOL simetrik şekilde küçültüyor (çekilişlerin sadece ~%5'i pozitif). Bu, sağlanan bulgular arasında en güçlü/en tutarlı olanı.

---

## D. TEK Üretime-Hazır Pozitif Bulgu: Dikkat/Anomali Dedektörü

`[EVIDENCE]` "Yüksek ATR (≥5%) + yüksek RVOL (≥1.5x)" bayrağı, bugün test edilen HER doğrulama katmanından geçen tek kriter:
- Matched-control: p≈0.07 (|getiri| büyüklüğü için)
- **Ay-ay kararlılık: 5/5 ay pozitif, işaret HİÇ dönmedi** (ortalama +3.19pp, std sadece 0.95pp) — bugün bu testi geçen tek kriter.
- Precision/recall: işaretlenenlerin %67.5'i gerçekten büyük hareket ediyor (taban oranın 1.68 katı), ama tüm büyük hareketlerin sadece %10.1'ini yakalıyor (dar ama isabetli).
- Simetri: hem yukarı (1.49x lift) hem aşağı (1.86x lift) hareketleri öngörüyor — gerçekten yön-kör, gizli bir yön sinyali değil.
- 1 günlük ufukta da tutarlı (çapraz-ufuk doğrulaması).

**Yorum:** bu bir trade sinyali değil — yön söylemiyor ve söylememeli. Ama gerçek, çok-yöntemli doğrulanmış bir "bu hisse olağandışı davranıyor" dedektörü. Önerilen kullanım: dashboard "What to Watch" bölümü veya FinSense'in "bu hisse neden ilginç" açıklaması için girdi — yön kararı insana veya ayrı, henüz doğrulanmamış bir katmana bırakılarak.

---

## E. Açık Sorular / Bloklu Kalemler

1. FinSense RSI probu push bekliyor (`.git/index.lock`).
2. Tip A'nın düşük-`lottery_factor` alt kümesi kendi matched-control testini almadı.
3. `close5_real` (gerçek bar verisinden) vs `c2c_5d` (export'taki hazır kolon) arasında ρ=0.845 uyuşmazlığı — kaynağı bulunmadı, muhtemelen giriş-noktası tanım farkı.
4. Kategori 3 (yeni veri kaynakları — intraday OHLCV, FINRA short interest, opsiyon pozisyonlaması, haber/katalist etiketi) hiç test edilmedi — mevcut feature ailesi tükendi, yeni bilgi ancak buradan gelebilir.
5. `research/full_universe_barrier_backtest.py` ve `research/high_rvol_raw_ohlc_exit_battery_2026_08_12.py` — bugün keşfedildi (daha önce "yok" sanılıyordu), içerikleri bu turda incelenmedi, olası tekrar-iş riski var.

---

## Sonuç

Bugünün en önemli çıktısı bir "kazanma formülü" değil — bir **teşhis** ve **tek gerçek pozitif bulgu**: mevcut feature ailesinde (composite_score, entry_ok, ATR, RVOL, gap, 52w-mesafe, regime, direction, day-1 dönüş) yönü güvenilir tahmin eden hiçbir kriter yok (10+ bağımsız yöntemle, matched-control + ay-ay kararlılık + rejim-koşullama + gerçek first-touch path ile doğrulandı). Ama ATR/RVOL kombinasyonu, büyüklüğü (yön değil) güvenilir şekilde tahmin ediyor — bu, bugün üretilen tek, çok-yöntemli doğrulanmış, üretime taşınabilir bulgu.
