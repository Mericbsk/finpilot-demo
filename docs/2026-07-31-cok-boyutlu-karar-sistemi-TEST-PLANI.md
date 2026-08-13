# Çok-Boyutlu Karar Sistemi — Kapsamlı Test Planı

Sürüm: 1.0 · Tarih: 2026-07-31 · Level A (araştırma/tasarım) · İlke: her şey `edge_recheck` dürüst-metrik + IS/OOS
Bağlam: Sistem tek sembol için çok fazla örtüşen "karar dili" üretiyor (entry_ok, legacy_quality,
composite_score, conviction_tier, conviction_prob, Grade A/B/C, position_cap). Öneri: tek nihai skor yerine
**birkaç bağımsız boyut** göster → "neden öne çıktı" görünür olsun.

---

## 0. ÖN BULGU (illüstrasyon — planı temellendirir)

- **Redundancy KANITLI:** `composite_score` ↔ `finpilot_score` rank-korelasyon **0.98** → aynı boyut. ATR ortogonal (−0.23).
  → "çok fazla karar dili" eleştirisi ampirik doğru; bu diller ~2-3 bağımsız eksene iniyor.
- **Kalibrasyon YOK:** composite decile → P(kazanç) [51.6…45.5] düz/azalan (kalibre skor monoton artmalı).
- **Risk boyutu GEÇERLİ:** ATR ↔ gerçekleşen MAE IC **−0.514**, decile monoton (−1.1→−9.8).
- **Ana tez:** Boyutların **doğruluk-statüsü FARKLI.** Getiri boyutu = kanıtsız (edge yok); risk boyutu = güçlü/geçerli;
  conviction = yanlış kalibre; tradability = yapısal geçerli. **Her boyut KENDİ ground-truth'una karşı test edilmeli.**

---

## 1. ÖNERİLEN 4 BOYUT (her biri farklı ground-truth)

| Boyut | Ne söyler | Ground-truth (neye karşı test edilir) | Mevcut statü (ön bulgu) |
|---|---|---|---|
| **D1 — Setup / Yön** | "neden tetiklendi" (momentum/vol kurulumu) | Gelecek getiri (honest c2c5_net) | ❌ Edge yok (kanıtlı) |
| **D2 — Güven / Conviction** | "lehte hareket olasılığı" | İleri hit-rate / kalibrasyon eğrisi | ⚠ Yanlış kalibre (düz) |
| **D3 — Risk** | "ne kadar oynak/downside" | Gerçekleşen MAE / drawdown | ✅ Geçerli (IC −0.51) |
| **D4 — İşlem-yapılabilirlik** | "gerçekte alınabilir mi" | Gerçekleşen spread/slippage/fill | ⚠ Yapısal geçerli (ölçülmeli) |

**Kritik ilke:** D3/D4 geçerli olması D1'in (getiri edge'i) geçerli olduğunu İMA ETMEZ. Kullanıcıya "yüksek risk"
güvenilir söylenebilir; "yükselecek" söylenemez. Bu ayrım hem dürüstlük hem compliance (Grade etiketi) için zorunlu.

---

## 2. KAPSAMLI TEST SÜİTİ

### T1 — Ortogonallik / Redundancy (boyutlar gerçekten bağımsız mı?)
- **Hipotez:** 4 boyut bağımsız bilgi taşır.
- **Yöntem:** tüm boyutlar + alt-göstergeler (entry_ok, legacy_quality, composite, conviction_prob, Grade, ADV) arası
  rank-korelasyon matrisi; PCA ile "etkili boyut sayısı" (kümülatif varyans %90); VIF.
- **Geçme:** çift-yönlü |kor|<0.5 ve PCA ≥4 anlamlı bileşen. **Kalma:** |kor|>0.7 çiftleri BİRLEŞTİR.
- **Ön bulgu:** composite↔finpilot 0.98 → **KALDI**, ikisi tek boyuta indirgenmeli.

### T2 — Construct validity (her boyut iddia ettiğini mi ölçüyor?)
- Her boyutu **amaçladığı girdilere** regres et: D1↔momentum/vol; D2↔geçmiş hit-rate; D3↔ATR/realized-vol; D4↔ADV/spread.
- **Geçme:** boyut, kendi girdi ailesiyle güçlü (|IC|>0.5), diğer ailelerle zayıf ilişkili.

### T3 — Predictive validity — KENDİ ground-truth'una karşı (honest, IS/OOS)
- **D1 → getiri:** rank-IC vs c2c5_net (IS/OOS). *Beklenti: ~0 (kanıtlı).*
- **D2 → hit-rate:** decile → P(c2c5_net>0) monotonluk + kalibrasyon (T5).
- **D3 → MAE:** rank-IC vs mae5 + decile monotonluk. *Beklenti: güçlü (−0.51).*
- **D4 → fill:** gerçekleşen spread/slippage (execution verisi gerekir; yoksa ADV→gerçekçi-fill proxy).
- **Geçme:** her boyut kendi ground-truth'unda IS+OOS tutarlı; getiri boyutu geçemezse "getiri-yordayıcı DEĞİL" etiketi.

### T4 — Incremental information (boyut diğerlerinin ÜSTÜNE ne katıyor?)
- Çok-değişkenli (standardize β) + leave-one-out IC; her boyut çıkarıldığında bilgi kaybı.
- **Geçme:** her tutulan boyut marjinal katkı sağlar; sağlamayan (finpilot gibi) elenir.

### T5 — Kalibrasyon (conviction_prob / Grade dürüst mü?)
- Reliability diagram (tahmin edilen P vs gerçekleşen), **Brier skoru**, **ECE** (expected calibration error), honest metrik.
- Grade A/B/C ve conviction A/B/C için ileri hit-rate: A>B>C monoton mu?
- **Geçme:** ECE düşük + tier'lar monoton. **Ön bulgu:** düz → **yeniden kalibrasyon** ya da "uncalibrated" dürüst etiketi.

### T6 — Kararlılık / persistence (aynı sembol, günden güne)
- Aynı (symbol) için ardışık günlerde boyut/etiket değişim (flip) oranı; ATR ve conviction'ın otokorelasyonu.
- **Geçme:** boyutlar makul kararlı (gürültü değil); Grade günlük zıplamıyor.

### T7 — Public etiket bütünlüğü + compliance
- Grade A/B/C ↔ 4 boyut ↔ honest outcome tutarlılığı; **YONERGE §12** (al/sat/hedef dili yok), "past performance" uyarısı.
- Grade'in "yükselir" ima etmediği; yalnız setup/risk/likidite karışımını yansıttığı doğrulanır.
- **Geçme:** etiket dili compliance-uyumlu; getiri-vaadi yok.

### T8 — Rejim koşullandırma (her boyutun geçerliliği rejime bağlı mı?)
- T3'ü bull/bear (SPY 50-SMA) ayrı koş. D3(risk) her rejimde geçerli mi? D1 rejimde işaret değiştiriyor mu?
- **Geçme:** boyutun geçerlilik-statüsü rejim-etiketli raporlanır (evrensel demeden).

### T9 — Karar-değeri (4 boyut, 1 skordan iyi mi?)
- **Nicel proxy:** boyut-tabanlı alt-kümeler (ör. düşük-risk ∩ yüksek-likidite) honest outcome/risk-ayarlıda baseline'ı geçiyor mu?
- **Davranışsal:** kullanıcı 4-boyutu 1-skordan daha doğru/hızlı yorumluyor mu (küçük A/B; kapsam: yapısal + anlaşılırlık, gerçek dönüşüm analitiği yoksa ölçülemez).
- **Geçme:** ya bir boyut-kombinasyonu ölçülebilir fayda sağlar, ya da şeffaflık/anlaşılırlık kanıtlanır.

---

## 3. ÖNCELİK + BEKLENTİ

| Test | Öncelik | Şimdi yapılabilir? | Beklenti (ön bulgu) |
|---|--:|---|---|
| T1 Ortogonallik | ⭐⭐⭐⭐⭐ | ✅ (elde) | composite/finpilot birleşecek |
| T3 Predictive (kendi GT) | ⭐⭐⭐⭐⭐ | ✅ (edge_recheck) | D1 boş, D3 güçlü |
| T5 Kalibrasyon | ⭐⭐⭐⭐⭐ | ✅ (honest) | miskalibre → recalibrate |
| T4 Incremental | ⭐⭐⭐⭐ | ✅ | finpilot elenir |
| T8 Rejim | ⭐⭐⭐⭐ | ✅ (bull/bear var) | D3 her rejim geçerli |
| T2 Construct | ⭐⭐⭐ | kısmen | — |
| T6 Persistence | ⭐⭐⭐ | ✅ (ledger günleri) | — |
| T7 Compliance | ⭐⭐⭐⭐ | ✅ (metin) | dil kontrolü |
| T4/D4 fill · T9 davranışsal | ⭐⭐ | execution/analitik gerekir | ölçülemez (kapsam dışı) |

---

## 4. SONUÇ ÇERÇEVESİ (bu testler ne verecek)
Muhtemel dürüst sonuç: **"getiri" boyutu (D1/conviction) yordayıcı değil ve conviction miskalibre → ya recalibrate
ya 'uncalibrated' göster; RİSK (D3) ve İŞLEM-YAPILABİLİRLİK (D4) boyutları geçerli ve kullanıcıya güvenle
gösterilebilir; composite/finpilot birleştirilmeli (redundant)."** Yani ürün, alfa vaat etmeden **dürüst, çok-boyutlu
bir karar-destek yüzeyi** olarak sağlamlaşır — bu da aws impact/eğitim hattıyla tutarlı.

## 5. GOVERNANCE
- Tüm testler Level A (analiz). Boyut/etiket üretim değişikliği (Grade tanımı, conviction recalibration) = Level B.
- Her predictive iddia `edge_recheck` dürüst-metrik + IS/OOS'tan geçer; getiri ile risk/tradability truth-status'ı ASLA karıştırılmaz.
