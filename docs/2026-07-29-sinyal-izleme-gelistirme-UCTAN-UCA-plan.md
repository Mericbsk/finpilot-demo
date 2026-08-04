# Sinyal İzleme Geliştirme — Uçtan Uca Plan

Sürüm: 1.0 · Durum: DRAFT (plan; öneriler Level B pending) · Tarih: 2026-07-29
Kaynak: `docs/2026-07-29-sinyal-takip-kavrayis-denetimi.md` (Ö1–Ö5)
Amaç: Mevcut sinyal mantığına **dokunmadan**, izleme merceğini 5 eksende zenginleştirmek
(kontrol grubu · dağılım · göreli/benchmark · horizon · risk-ayarlı · segment/rejim).
Araç: `shadow_scorecard.py` (var) + gölge defteri (`scan_shadow.jsonl`, 29.808 satır, 261 seçilen / 29.547 kontrol).

---

## 0. Tek Evrensel Engel (önce bu)

Beş önerinin de önündeki tek blokaj: **`price_cache` bayat** — semboller 30 Haz / 14 Tem'de bitiyor,
sinyaller 8–29 Tem. Benchmark ETF'leri (SPY, QQQ, XLK/XLF/XLE/XLV/XLY, IWM) cache'te **var** ama onlar
da 30 Haz'da bitiyor. Cache güncellenmeden hiçbir faz gerçek sonuç üretemez (skorlanabilir = 0).

**FAZ 0 — Veri temeli (ön koşul, Level A):**
- Sinyal + kontrol sembolleri + benchmark ETF'leri için `price_cache`'i **bugüne kadar** güncelle
  (EODHD ücretli anahtar, local çalıştır — sandbox'ta ağ yok).
- **Kabul:** eligible + benchmark sembollerinin ≥%90'ı sinyal günü + 5 işlem günü ileri bar taşıyor
  (`shadow_scorecard.py` "pending" sayısı ≈ yalnız son 5 günün sinyalleri).
- Süreklilik: günlük tarama sonrası cache refresh adımını zorunlu kıl (Faz 4'e bağlanır).

---

## 1. FAZ 1 — Kontrol grubu + dağılım + risk-ayarlı + horizon (Ö1/Ö3/Ö4) · Level A

**Neden Level A:** `shadow_scorecard.py` izole bir analiz aracı; üretim sinyal/karne mantığına dokunmaz.

**Kod eklemeleri (`shadow_scorecard.py`):**
1. **Model-bağımsız ölçümler** (kontrol grubu exit_profile taşımaz): `forward_return(bars, entry_idx, horizon)`
   ve mevcut MFE — seçilen ve reddedilen için aynı şekilde hesapla. Böylece elmayla elma kıyası.
2. **Kontrol grubu skorlama** (`--control`): `selection_eligible=False` satırlarını da (symbol, gün) ile
   skorla; reject_reason'a göre katmanla (signal_not_eligible, momentum_score_gate, liquidity_gate,
   direction_gate, regime_gate…). Dev örneklem (29.547) alt-örneklenebilir (perf için).
3. **Dağılım** (`summarize`'a ekle): ortalamaya ek p10 / medyan / p90 (getiri ve MFE için) — birkaç
   büyük kazananın şişirdiği ortalamayı ifşa eder.
4. **Risk-ayarlı** kolon: getiri/ATR ve `profit_factor` (zaten var) + Sharpe-benzeri (ort/σ).
5. **Horizon süpürme** (`--horizon-sweep 1,3,5,10,20`): her horizon için ayrı özet → olgunlaşma zamanı.

**Çıktı:** `shadow_scorecard.md`'ye iki yeni blok — (a) **Seçilen vs Kontrol** dağılım kıyası
(p10/medyan/p90, tp_rate, getiri/ATR), (b) horizon×metrik matrisi.

**Kabul kriterleri:**
- Seçilen ve kontrol grubu için p10/medyan/p90 + getiri/ATR raporlanıyor.
- Kontrol grubu reject_reason bazında kırılıyor.
- 1/3/5/10/20 gün ayrı ayrı raporlanıyor.
- Birim testi: sentetik veriyle kontrol kolu + percentile + horizon doğrulandı (mevcut test desenini genişlet).

**Beklenen kazanım:** "Sinyalin gerçek edge'i var mı, yoksa piyasa mı?" sorusuna ilk somut kanıt
(seçilen dağılımı kontrol grubundan anlamlı ayrışıyor mu?).

---

## 2. FAZ 2 — Göreli / benchmark (excess return) (Ö2) · Level A

**Kod eklemeleri:**
- `load_benchmark(symbol="SPY")` — SPY (ve istenirse sektör ETF) barlarını yükle.
- Her sinyal için aynı [entry_idx, entry_idx+horizon] penceresinde benchmark getirisini hesapla;
  `excess_ret = signal_ret − benchmark_ret`. Sektör eşlemesi varsa sektör-göreli de ekle (`--benchmark sector`).
- `summarize`'a `avg_excess`, `excess_win_rate` (excess>0 oranı), excess p10/medyan/p90.

**Kabul kriterleri:**
- Her skorlanan sinyalde `spy_excess` (ve mümkünse `sector_excess`) var.
- Özet: boğa düzeltmesi sonrası (excess) tp_rate/getiri, ham ile yan yana.

**Beklenen kazanım:** Boğa piyasasında şişen mutlak isabeti düzeltir; **gerçek alfa** görünür.
(Bu proje boyunca tekrarlanan "piyasa yönü ↔ edge karışımı" riskini doğrudan ölçer.)

---

## 3. FAZ 3 — Segment + rejim kırılımı (Ö5) · Level A (rejim: veri bekler)

**Kod eklemeleri:**
- **Segment** (`--by-segment`): gölge defterindeki `dollar_adv` (likidite kovaları) + `data_quality_tier`
  + sektör etiketi (symbol→sektör eşlemesi; ETF/statik tablo). Her segment için ayrı özet.
- **Rejim** (`--regime`): SPY trend (örn. 50g EMA üstü/altı) + gerçekleşmiş volatilite (SPY 20g σ; VIX
  cache'te yoksa proxy) ile her sinyal gününü etiketle; rejim başına ayrı özet.

**Kabul kriterleri:**
- Karne ADV kovası / tier / sektör bazında kırılıyor; zayıf segment görünür.
- Rejim etiketi üretiliyor; en az 2 rejimde ayrı özet (yeterli gün birikince).

**Beklenen kazanım:** Genel ortalamanın gizlediği zayıf segmentleri/rejim kırılganlığını açar.
**Uyarı:** Eldeki veri ~15 gün ve **tek rejim (boğa)** → rejim kırılımı ancak daha uzun tarihle güvenilir.

---

## 4. FAZ 4 — Operasyonelleştirme + yüzeye taşıma · Level B (onay şart)

**4a. Günlük otomasyon (Level A):** tarama + cache refresh sonrası `shadow_scorecard.py`'yi otomatik
koştur (scheduled task); çıktı `shadow_scorecard.md` + CSV güncellensin. Yeni skor kartı hazır olunca
Telegram admin'e kısa özet ping (mevcut `notify_admin` altyapısı).

**4b. Karne/web'e taşıma (Level B):** doğrulanmış merceklerden (excess return, dağılım, kontrol-grubu
kıyası) seçilenleri **canlı karneye** (`/watchlist/performance` çıktısına ek alanlar) ve web Ledger
karne bileşenine ekle. Bu, üretim yüzeyini değiştirir → **Meriç onayı**, YONERGE §12 (yasak dil) kontrolü,
`/methodology` "past performance" uyarısı gözden geçirilir.

**Kabul kriterleri:**
- 4a: Her işlem günü, cache güncel + skor kartı otomatik üretiliyor; admin ping düşüyor.
- 4b: Karne/web yalnız **doğrulanmış** (kontrol grubundan anlamlı ayrışan) mercekleri gösteriyor; ham
  ortalama tek başına sunulmuyor.

---

## 5. Sıra ve bağımlılıklar

```
FAZ 0 (cache refresh)  ─┬─▶ FAZ 1 (kontrol+dağılım+risk+horizon)  ─┐
                        ├─▶ FAZ 2 (benchmark/excess)              ─┤─▶ FAZ 4a (otomasyon)
                        └─▶ FAZ 3 (segment; rejim=veri bekler)    ─┘        │
                                                                            └─▶ FAZ 4b (karne/web) [Level B onay]
```
- Faz 0 tüm fazların ön koşulu.
- Faz 1–3 paralel ilerleyebilir (hepsi aynı skor kartına eklenir), hepsi Level A (offline analiz).
- Faz 4b tek Level B kapısı — üretim yüzeyi.

---

## 6. Doğrulama ve istatistik disiplini (çapraz kesen)

- Her yeni hesap fonksiyonu için sentetik-veri birim testi (mevcut test desenini genişlet: TP/SL/TIME,
  excess, percentile, kontrol kolu).
- **Küçük örneklem uyarısı:** n<30 segmentlerde farklar gürültü olabilir; bootstrap güven aralığı ekle,
  eşik altını "yetersiz veri" işaretle.
- **Tek rejim uyarısı:** tüm bulgular boğa dönemi; rejim/forward doğrulaması olmadan "daha iyi" denmez.
- Kanıt olmadan hiçbir mercek "üstün" ilan edilmez (denetim kuralı).

---

## 7. Governance
- Faz 1–3 + 4a: **Level A** (izole analiz aracı + otomasyon; üretim sinyal/skor mantığı değişmez).
- Faz 4b: **Level B** — üretim karne/web yüzeyi; Meriç onayı + compliance kontrolü.
- Ö1–Ö5 önerileri `docs/governance/decision-log.md`'ye **pending** eklenir; Faz 4b uygulanınca
  Layer=Product/Engineering + Level=B olarak işlenir.

---

## 8. Kapsam dışı / riskler
- **Cache güncelliği** her şeyi kilitliyor (Faz 0). Sandbox'ta ağ yok → local EODLD çalıştırması şart.
- **Rejim testi** eldeki ~15 günle güvenilmez; ay/çeyrek ölçekli tarih gerekir.
- **Sektör eşlemesi** için symbol→sektör tablosu yok; ETF/statik kaynak eklenmeli.
- **Nedensellik (3.5)** bu planda yok; sinyal-öncesi pencere verisi sistemli toplanmıyor (ayrı iş).
- **VIX** cache'te olmayabilir; rejim vol proxy'si SPY gerçekleşmiş σ ile kurulur.
