# Bekleyen İkincil İşler — Kapsamlı Plan: FinSense Deney 2/3 ve close5_real/c2c_5d Uyuşmazlığı

Tarih: 2026-08-15 · Statü: Level A (plan; hiçbir kod/deney henüz başlamadı) · Kanıt standardı: `[EVIDENCE]`/`[INFERENCE]`/`[HYPOTHESIS]`/`[RADICAL]`

Bu belge, önceki turda "düşük öncelikli, bekleyen" diye işaretlenen iki ayrı iş akışını genişletiyor. İkisi de bağımsız — biri ürün araştırması (FinSense), biri veri-kalite hata avı (FinPilot). Ayrı bölümler halinde, ayrı fazlarla planlandı; birini yapmak diğerini beklemez.

---

## BÖLÜM A — FinSense Reasoning Engine: Deney 2 (Collision) ve Deney 3 (Convergence)

### A.0 Durum ve neden hâlâ duraklatılmış

`[EVIDENCE]` Deney 1 (Divergence) tamamlandı: `docs/2026-08-13-finsense-reasoning-engine-research-v0.1-deney1-divergence.md` — 10 bağımsız persona, dış literatürle desteklenmiş, sabit 10 soruya cevap verdi. Deney 2/3 kasıtlı olarak başlatılmadı çünkü gerekçe şuydu: gerçek sinyal (RSI caveat deneyinin geri bildirim verisi) henüz toplanmamıştı — spekülasyon üstüne spekülasyon inşa etmemek için.

`[EVIDENCE]` RSI caveat deneyi (`web/src/app/dashboard/analysis/page.tsx`, `indicator_caveat_shown`/`indicator_caveat_feedback` Plausible event'leri) o zamandan beri production'a girdi (commit `ecd1f61`, ~2026-08-13). Bugün 2026-08-15 — yaklaşık 2 gün geçti.

`[INFERENCE]` 2 günlük pencere, anlamlı bir geri bildirim hacmi için muhtemelen yetersiz — özellikle FinSense/dashboard'un mevcut trafik seviyesi bilinmeden bunu varsaymak riskli. Bu belgenin önerdiği **Faz 0 (Sinyal-Hacmi Kapısı)**, Deney 2'ye başlamadan önce bunu doğrulamayı zorunlu kılıyor — [[audit-before-speculating]] ve [[finsense-validate-before-expanding]] hafıza notlarındaki tekrarlayan kalıptan (doğrulamadan genişletme) kaçınmak için.

### A.1 Faz 0 — Sinyal-Hacmi Kapısı (ZORUNLU, Deney 2'den önce)

`[HYPOTHESIS]` Deney 2'nin (Collision) gerçek katma değer üretmesi için, en azından bazı persona iddialarını gerçek veriyle çürütecek/destekleyecek kadar geri bildirim birikmiş olmalı.

**Yapılacak:**
1. Plausible dashboard'undan (veya API'sinden) `indicator_caveat_shown` ve `indicator_caveat_feedback` event sayılarını çek — toplam gösterim, toplam feedback (yes/no oranı).
2. Eşik: **< 30 feedback** ise Deney 2 BAŞLAMAZ — bunun yerine sadece deneyin kendisini daha görünür hale getirme (örn. daha fazla sayfaya ekleme) tartışılır. **≥ 30 feedback** ise Deney 2'ye gerçek veri girdisi olarak dahil edilir.
3. Sonuç ne olursa olsun bir satırlık kayıt: "Faz 0: N gösterim, M feedback (X% olumlu) — Deney 2 [başladı/ertelendi]."

**Çıktı:** `docs/2026-08-15-finsense-deney2-faz0-sinyal-kapisi.md` (kısa, tek sayfa).

### A.2 Faz 1 — Deney 2: Collision (çapraz sorgulama)

Sadece Faz 0 geçerse başlar.

`[INFERENCE]` Deney 1'in 10 personası aynı 10 soruya bağımsız cevap verdi — birbirini görmeden. Collision'ın amacı: nerede gerçekten çelişiyorlar (yüzeysel kelime farkı değil), nerede biri diğerinin kör noktasını yakalıyor, ve gerçek RSI-deney verisi bu çelişkilerden hangisini çözüyor.

**Metodoloji:**
1. Deney 1'in 10×10 cevap matrisini (persona × soru) tara, her soru için persona'lar arası **gerçek anlaşmazlık** noktalarını çıkar (yüzeysel değil — örn. "A persona'sı X'i riskli buluyor, B persona'sı X'i fırsat buluyor" gibi doğrudan zıt pozisyonlar).
2. Her anlaşmazlık için: en güçlü karşı-argümanı seçilen personaya "karşı savunma" turu olarak sun (tek round, kısa) — bu, gerçek bir tartışma değil, yapılandırılmış bir stres testi.
3. Faz 0'da toplanan gerçek RSI-deney verisini (gösterim/feedback oranı, olumlu/olumsuz dağılımı) yeni kanıt olarak devreye sok — hangi personanın orijinal tahmini bu veriyle tutarlı, hangisi çürütülüyor, açıkça işaretle.
4. Format: önceki (10-08-10, 10-perspektif-red-team) belgelerle aynı ev-stili — `[EVIDENCE]`/`[EXTERNAL]`/`[INFERENCE]`/`[HYPOTHESIS]`/`[RADICAL]` etiketleri, üretim etkisi notu ("Etki: Üretim DEĞİŞMEDİ").

**Çıktı:** `docs/2026-08-XX-finsense-reasoning-engine-research-v0.1-deney2-collision.md`

### A.3 Faz 2 — Deney 3: Convergence (3-5 büyük hipotez)

Sadece Deney 2 tamamlanınca başlar.

`[INFERENCE]` Kullanıcının orijinal talebi ("10 Perspektif → Collision → 3-5 Büyük Hipotez") burada kapanıyor. Amaç: dağınık 10-persona + collision çıktısını, her biri **yanlışlanabilir** (falsifiable) 3-5 hipoteze indirgemek.

**Metodoloji:**
1. Deney 1+2'den, tekrar eden/en güçlü temaları 3-5 hipoteze indirge (örn. "Kullanıcılar RSI gibi indikatörleri sade-dil açıklamayla daha çok anlıyor" gibi somut, test edilebilir iddialar — spekülatif "büyük vizyon" cümleleri değil).
2. Her hipotez için ZORUNLU alanlar: (a) yanlışlama kriteri (hangi veri bunu çürütür), (b) önerilen sıradaki gerçek deney (RSI probu gibi küçük, ucuz, atılabilir — büyük build değil), (c) öncelik sıralaması (gerekçeli).
3. Açık, yazılı bir "YAPILMAYACAKLAR" listesi: hangi büyük-build fikirleri (10-persona'nın önerdiği "Reasoning Engine" tam ürünü gibi) bu turda kasıtlı olarak ERTELENDİ ve neden.

**Çıktı:** `docs/2026-08-XX-finsense-reasoning-engine-research-v0.1-deney3-convergence.md`

### A.4 Riskler / kırmızı çizgiler

`[EVIDENCE]` Bu oturumda 4+ kez tekrar eden kalıp ([[finsense-validate-before-expanding]]): büyük build önerisi → doğrulama olmadan genişleme → kullanıcı/ben fren yapıp küçültme. Bu plan, Faz 0 kapısı ve Deney 3'ün "yapılmayacaklar" listesi ile bu kalıbı yapısal olarak engellemeyi hedefliyor — sona kadar hiçbir kod/ürün taahhüdü yok, sadece daha iyi çerçevelenmiş hipotezler.

---

## BÖLÜM B — close5_real vs c2c_5d Korelasyon Uyuşmazlığı (ρ=0.845)

### B.0 Sorunun tanımı ve neden önemli

`[EVIDENCE]` `docs/2026-08-13-winner-anatomy-exp05-real-first-touch-path.md`'de bulundu: `data/price_cache/*.json`'daki gerçek barlardan hesaplanan `close5_real` (5 gün sonraki kapanış / giriş kapanışı) ile `full_universe_enriched.csv`'deki hazır `c2c_5d` kolonu arasındaki korelasyon **ρ=0.845** — aynı şeyi (aynı sembol, aynı 5-günlük pencere, close-to-close getiri) ölçmeleri beklenirdi, 1.0'a yakın olmalıydı. Kök neden bulunamadı, açık iş olarak bırakıldı.

`[INFERENCE]` Bu, sadece kozmetik bir tutarsızlık değil — exp05'teki first-touch-path backtest'in (entry_ok=True MAE -5.38%, SL-first %62 gibi) **mutlak büyüklüklerine** tam güvenilemeyeceği anlamına geliyor, çünkü hangi veri kaynağının doğru olduğu belirsiz. Yön/sıralama bulguları muhtemelen sağlam (iki kaynak da aynı yönde hareket ediyor, ρ=0.845 hâlâ güçlü bir pozitif korelasyon) ama kesin sayılar temkinli kullanılmalı.

### B.1 Bugün toplanan yeni kanıt — en güçlü aday hipotez netleşti

`[EVIDENCE]` Bu planı hazırlarken `data/price_cache/` üzerinde hızlı bir örneklem kontrolü yapıldı (200 rastgele dosya, ~9.598 bar): **`close` ve `adjusted_close` alanları barların %55'inde (5.323/9.598) birbirinden farklı**, bazı sembollerde (örn. `KIDZ`, 2024-09-03: close=0.0222 vs adjusted_close=11.12) fark ~500 kat — klasik ters-split ayarlaması imzası. `research/feature_lineage.py` (satır 53), `c2c_5d`'nin `"close"` alanından (adjusted_close DEĞİL) türetildiğini belgeliyor.

`[HYPOTHESIS], en yüksek öncelik]` exp05'teki `close5_real` hesaplaması muhtemelen `bars["Close"]` (ham, split-ayarlanmamış) kullandı — eğer `c2c_5d`'nin kaynağı farklı bir noktada (ayarlanmış fiyatla, ya da farklı bir sağlayıcıdan) hesaplandıysa, split-döneminde işlem gören semboller için iki kolon sistematik olarak ayrışır. Bu, ρ=0.845 gibi "yüksek ama 1.0 değil" bir korelasyonu çok iyi açıklar: çoğu sembol split yaşamaz (ρ yüksek), azınlık bir kısmı yaşar (korelasyonu 1.0'dan aşağı çeker).

### B.2 Test edilecek hipotezler (öncelik sırasıyla)

1. **`[HYPOTHESIS] Split/dividend-ayarlama farkı (en olası, B.1'de kanıt var).** `close5_real`'i `adjusted_close` ile yeniden hesapla, `c2c_5d` ile korelasyonun 1.0'a yaklaşıp yaklaşmadığına bak. Ucuz, hızlı, ilk yapılacak test.
2. **`[HYPOTHESIS] Giriş noktası tanım farkı.** `c2c_5d`'nin gerçek üretim script'ini bul (bugünkü grep taramaları başarısız oldu — `research/feature_lineage.py` sadece "close, forward, 5" diyor, tam formülü göstermiyor) ve giriş barının scan-close mı, ertesi-gün-open mı, farklı bir referans mı olduğunu doğrula.
3. **`[HYPOTHESIS] Tarih hizalama/timezone.** `scan_date` ile price_cache bar tarihleri arasında off-by-one türü kaymalar (özellikle gece/hafta sonu taramaları) olup olmadığını kontrol et.
4. **`[HYPOTHESIS] Aykırı-değer kirliliği.** Toplam korelasyonu değil, `(close5_real - c2c_5d)` farkının dağılımını çıkar — birkaç büyük aykırı mı (örn. split-etkilenen semboller) yoksa sistemik küçük bir kayma mı olduğunu ayır.
5. **`[HYPOTHESIS], düşük olası] Farklı veri sağlayıcısı.** `full_universe_enriched.csv`'nin `c2c_5d`'si EODHD'den farklı bir kaynaktan (örn. orijinal tarama-anı fiyat sağlayıcısından) gelmiş olabilir — kurumsal aksiyon (split/dividend) işleme farkı olabilir.

### B.3 Yöntem

1. `full_universe_enriched.csv`'den orta büyüklükte (~500-1000 satır) bir örneklem al, her satır için eşleşen price_cache dosyasını bul.
2. Üç paralel hesap üret: `c2c_5d` (mevcut kolon), `close5_real` (ham `close`), `adjusted_close5_real` (yeni, `adjusted_close` ile).
3. Üç kolon arası Spearman korelasyonlarını karşılaştır — hipotez 1 doğruysa `adjusted_close5_real` ↔ `c2c_5d` korelasyonu `close5_real` ↔ `c2c_5d`'den belirgin şekilde yüksek çıkmalı (ρ→~0.95+).
4. Hâlâ tam örtüşmüyorsa (adjusted ile bile <0.95), hipotez 2-3'e geç: giriş-noktası/tarih hizalamasını satır satır 20-30 örnek üzerinde elle doğrula.
5. Kalan fark için hipotez 4-5'i son çare olarak dene (üretim script kaynağını bulmak dahil).

**Çıktı:** `docs/2026-08-15-close5real-c2c5d-uyusmazlik-kok-neden.md` — hangi hipotez(ler) doğrulandı, hangi kolonun (varsa) daha güvenilir olduğuna dair net bir tavsiye, ve exp05'teki mutlak büyüklük iddialarının bu bulguyla ne kadar güncellenmesi gerektiği.

### B.4 Kapsam ve sınır

`[INFERENCE]` Bu bir veri-kalite hata avı — üretim scanner/ranking/entry mantığına dokunmuyor, `full_universe_enriched.csv` veya `price_cache`'e yazma yapmıyor (salt-okunur analiz). Level A. Sonuç, gelecekteki research script'lerinin hangi kolonu (`c2c_5d` mi `adjusted_close5_real` mi) tercih etmesi gerektiğine dair bir tavsiye üretecek — ayrı bir karar gerekmeden decision-log'a kaydedilebilir.

---

## Özet — Öncelik ve Bağımsızlık

| İş | Bağımlılık | Tahmini efor | Bloklanıyor mu? |
|---|---|---|---|
| A.0-A.1 (Faz 0 sinyal kapısı) | RSI deney verisine erişim (Plausible) | Küçük (~30dk) | Hayır, hemen başlanabilir |
| A.2 (Deney 2 Collision) | A.1'in sonucu (≥30 feedback) | Orta | Faz 0'a bağlı |
| A.3 (Deney 3 Convergence) | A.2 tamamlanmış olmalı | Orta | A.2'ye bağlı |
| B.1-B.3 (close5_real kök-neden) | Yok — bağımsız, hemen başlanabilir | Küçük-orta (~1-2 saat) | Hayır |

İki bölüm birbirinden bağımsız, paralel ilerletilebilir. B bölümü daha hızlı kapanabilir (mekanik veri analizi); A bölümü Faz 0'ın sonucuna göre hiç başlamayabilir de.
