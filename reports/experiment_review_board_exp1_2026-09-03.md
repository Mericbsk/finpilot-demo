# EXPERIMENT REVIEW BOARD — Experiment #1: Regime × Attention Tier × Forward Direction (+ Opening-Range Fade)

Tarih: 2026-09-03
İnceleme: Master Prompt v3.0, 8 rol
Deney: `research/direction_threshold_matrix_2026_09_03.py` → `data/backtest_out/direction_threshold_matrix_2026-09-03.json`
Rapor: `reports/direction_threshold_matrix_2026-09-03.md`

---

## DENEY KİMLİĞİ

| Alan | Değer |
|---|---|
| Experiment ID | direction_threshold_matrix_2026_09_03 |
| Tarih | 2026-09-03 |
| Dataset | `full_universe_enriched.csv` + `data/intraday_cache` (880 dosya) |
| Dataset hash | SHA-256 `e3b183552c7c38755528d133327a0c0601fe0cfff49ba58b9e360d17716ed3d3` (FACT) |
| Kod commit | Çalışma ağacı (commit yok — dirty worktree) |
| Config | Pre-registered docstring; eşikler sabit (rejim ±0.2%, tier 25/50, band ±3/±5) |
| Model/checkpoint | Yok (istatistiksel test, model yok) |
| Seed | 20260903 (sabit RNG, matched-control) — FACT |
| Discovery/OOS | Kronolojik 70/30, kesim 2026-06-26 (discovery n=21.925, OOS n=18.909) |
| Test dönemi | 2025-09-11 → 2026-08-05 (81 tekil gün) |
| Universe | Tam evren, dedup symbol-day, price≥$1, \|c2c_5d\|≤100% → 40.834 satır |
| Outcome | `c2c_5d` (close-to-close 5g ileri getiri) |
| Score | Ağırlıklı 6-flag attention skoru (25/25/15/15/10/10) |
| Execution varsayımı | **YOK** — spread/slippage/komisyon modellenmedi |
| Önceki varyant sayısı | **HIGH** — aynı dataset üzerinde 40+ önceki deney var (master_audit_battery, winner_anatomy, day1_confirmation, high_rvol serisi, attention_score_validation, direction_context_battery...). Attention formülünün kendisi bu dataset'te keşfedildi. |

---

## DENEYİN TEK CÜMLELİK HÜKMÜ

> **Ana hipotez (rejim × tier etkileşimi yön üretir) çürütüldü; fade bulgusu %1 maliyet stresinde negatife dönen, kendi üzerinde keşfedildiği veriyle test edilmiş bir DISCOVERY SIGNAL'dir — deney amacına ulaştı ama ürettiği olumlu sinyal production kanıtı değildir.**

---

## ROL 1 — KANTİTATİF ARAŞTIRMACI

**1A. Performans:** Portföy metriği yok (Sharpe/Sortino/Calmar hesaplanamaz — strateji backtest'i değil, koşullu dağılım analizi). **UNKNOWN** olarak değil, **kapsam dışı** olarak işaretlenir; bu deney zaten getiri stratejisi önermedi.

**1B. Raw N ≠ Effective N:**
- Raw N: 40.834 (H1/H2), 698 (H3/H4).
- Etkin N: **81 tekil gün** (H1); H3'te yalnızca **59 tekil gün / 210 sembol**. Aynı gün içindeki gap gözlemleri korele → etkin N ≈ gün sayısı mertebesinde. H1 High-tier OOS hücreleri n=130–1490 görünse de ~23 güne kümelenmiş. **Effective N = LOW-MEDIUM (FACT: gün kümeleri sayıldı).**

**1C. Outlier robustness (H3 fade):**
- Mean %0.91 / median %0.51 — mean≈2×median, sağ kuyruk çekiyor.
- En iyi %1 çıkar: mean %0.66 (hâlâ pozitif). En iyi %5 çıkar: mean **%0.20** (kırılgan). En kötü %1 çıkar: mean %1.15.
- En iyi 3 işlem aynı değeri taşıyor (+24.47 ×3) — aynı sembol-gün kümesi veya veri tekrarı şüphesi (UNKNOWN, doğrulanmadı).
- **OUTLIER DEPENDENCY = HIGH** (top %5 kaldırılınca edge'in %78'i kayboluyor).

**1D. Dağılım (H3):** skew +0.30, kurtosis 8.16 — kalın kuyruklu. En kötü işlem -%33.75 (tek günde fade'in 37 katı medyan kayıp). Pozitif/negatif asimetri: win rate %59.9 ama ortalama kayıp büyüklüğü ortalama kazançtan büyük (worst-5 |-13…-34| vs best-5 +24…+31; kuyruk asimetrik).

**1E. İstatistiksel anlam:** H3 win rate %59.9 (n=698) nominal binom se ~%1.9 altında anlamlı görünür — ama 59 gün kümelenmesiyle etkin se çok daha büyük; gün-bazlı kümelendiğinde **pozitif gün oranı yalnızca %54.2 (59 günün 32'si)** — bu oran istatistiksel olarak %50'den ayırt edilemez (binom p≈0.60). **EVIDENCE: gün seviyesinde anlamsız.**

**1F. Outcome definition audit:** `c2c_5d` = close-to-close 5g ileri getiri — kod zincirinden doğrulandı. ANCAK repo kayıtlarında `c2c_5d` ile gerçek `close5_real` (price_cache'ten) korelasyonu ρ=0.845 (beklenen ~1.0) ve kök neden bulunamamış (docs/2026-08-15 açık iş). **OUTCOME DEFINITION STATUS: PARTIALLY VERIFIED** — etiket tanımı doğru ama etiketin veri hattı bütünlüğü doğrulanmamış. H3 outcome'u (30dk→kapanış) ham barlardan hesaplandı, timestamp'ler UTC varsayımıyla — **PARTIALLY VERIFIED** (DST/saat dilimi hatası dışlanamadı).

---

## ROL 2 — OVERFITTING / DATA LEAKAGE DETECTIVE

**2A. Veri ayrımı:** 70/30 kronolojik split var. ANCAK: **OOS pencere tertemiz değil.** Attention formülü, tier eşikleri (25/50) ve rejim kavramının kendisi daha önce bu dataset'in tamamı üzerinde keşfedildi (2026-08-12/14 deneyleri). Yani "OOS" yalnızca bu bataryanın parametrelerine karşı OOS; **deney ailesine karşı OOS değil.** **QUASI-OOS — EVIDENCE.**

**2B. Look-ahead:** Rejim = günün evren medyan gap_pct'si; tarama anında (19:45) hesaplanabilir — leakage yok (FACT). `c2c_5d` ileri getiri — etiket olarak kullanımı meşru. Ancak H3'te gap günü seçimi gün açılışı bilgisiyle yapılıyor ve giriş 30. dakikada — zamanlama tutarlı (FACT).

**2C. Survivorship:** Universe, geçmiş shortlist export'larından toplandı; delisted/iflas sembollerin dahil edilip edilmediği **UNKNOWN**. 1.926 sembollük sector_map ile 40.834 satırın evreni arasında sistematik dışlama kontrol edilmedi. **SURVIVORSHIP RISK = UNKNOWN.**

**2D. Matched-random control:** H1/H2'de same-date matched control mevcut (100 draw, sabit seed) — **FACT**. Ancak kontrol yalnızca tarih üzerinden eşleşiyor; fiyat/likidite/sektör eşleştirmesi yok. High tier matched-control tüm rejimlerde negatif (share_positive 0.02–0.33) → **attention seçimine özgü pozitif etki yok** (EVIDENCE).

**2E. Walk-forward:** Yok — tek kronolojik split. **NOT DONE.**

**2F. Regime robustness:** Deneyin kendisi rejim testiydi: discovery'deki strong-down rebound deseni OOS'ta öldü → **rejim tutarlılığı YOK (EVIDENCE).**

**2G. Multiple testing:** Aynı dataset'te 40+ önceki deney; fade hipotezi **aynı intraday cache üzerinde** keşfedilip aynı cache'te test edildi (39.7% devam oranından türetilip 59.9% fade win rate ölçüldü — aynı 698 gözlemin ters yüzü). **SELECTION / CHERRY-PICK RISK = HIGH (FACT — hipotez ve test aynı veri).**

---

## ROL 3 — RİSK YÖNETİCİSİ

- H3 fade: tek işlemde -%33.75 gözlendi; fade stratejisi gap günlerinde counter-trend pozisyon alır — gap'in devam ettiği günlerde kayıplar hızlı büyür.
- Konsantrasyon: 59 gün × günde ortalama ~12 pozisyon; aynı gün pozisyonları yüksek korelasyonlu → tek kötü gün portföyü vurur.
- Maliyet stresi: +%0.1 → mean %0.81 (win %57.4); +%0.25 → %0.66 (%56.0); +%0.5 → **%0.41 (%50.3)**; +%1.0 → **-%0.09 (%44.8)**. Gap hisselerinde gerçekçi round-trip maliyet %0.5–1+ → **ekonomik edge maliyet altında kayboluyor (EVIDENCE).**
- Volatilite şoku, halts, likidite: modellenmedi — UNKNOWN.
- **Risk kararı: HIGH** (maliyet kırılganlığı + kalın sol kuyruk + gün korelasyonu).

---

## ROL 4 — SYSTEM / DATA / ML ENGINEER

- **4A Data pipeline:** Dedup + price≥$1 + |c2c_5d|≤100 temizliği var. Ancak: (a) `c2c_5d`↔`close5_real` ρ=0.845 anomalisi çözülmemiş; (b) intraday cache'de hacim yok, 15dk bar, UTC varsayımı; (c) en iyi 3 fade işleminin aynı getiriyi taşıması veri tekrarı olasılığı (doğrulanmadı — UNKNOWN); (d) `catalyst_factor` sabit 0.0 — şema var ama veri yok (FACT, veri hattı açığı).
- **4B Traceability:** Attention skoru kodda `research/direction_threshold_matrix_2026_09_03.py` içinde açık tanımlı; canlı scanner'daki skorla aynı DEĞİL (canlıda alanlar farklı — daha önce belgelenmiş GAP). Deney sonuçları canlı sisteme genellenemez (FACT).
- **4C Reproducibility:** Dataset hash (SHA-256) alındı, seed sabit, script+artifact mevcut. Eksik: kod commit'i (dirty worktree), dependency versiyonları. **REPRODUCIBILITY = MEDIUM.**
- **4D Execution realism:** Yok. Spread/slippage/fill/halts modellenmedi. H3 için bu eksiklik sonucu tek başına geçersiz kılabilecek düzeyde (maliyet stresi bunu gösterdi).

---

## ROL 5 — ADVERSARIAL / RED TEAM

- **Attack 1 (outlier):** Top %5 çıkınca fade mean %0.91→%0.20. **SONUÇ KISMEN BAĞLI.**
- **Attack 2 (matched control):** H1 High tier tüm rejimlerde kontrolün altında — pozitif etki iddiası çöktü. Ana hipotez için zaten ölümcül.
- **Attack 3 (threshold):** Fade gap eşiği ±3% civarında oynatılmadı — UNKNOWN. Rejim eşiği ±0.2% keyfiyeti test edilmedi — UNKNOWN.
- **Attack 4 (zaman):** H1 deseni OOS'ta öldü. Fade'in zaman tutarlılığı 59 günlük gün-ortalamalarında %54.2 — zayıf.
- **Attack 5 (evren):** Tek evren. UNKNOWN.
- **Attack 6 (maliyet):** %1 maliyette fade negatif. **EDGE KIRILGAN.**
- **Attack 7 (rejim):** Test edildi — rejim yön üretmiyor.
- **Attack 8 (veri kalitesi):** c2c_5d bütünlük anomalisi çözülmeden H1/H2 sonuçları gölge altında.
- **Attack 9/10 (baseline):** Fade, "gap günlerinde her zaman short/long" basit kuralıyla veya coin-flip maliyetli baseline ile karşılaştırılmadı — UNKNOWN.

> **Bu deneyin çökmesi için en güçlü karşı-örnek:** "Fade sinyali, keşfedildiği 698 gözlemin ters çevrilmiş hali; gün-kümeli anlamsız ve %1 maliyette negatif." — Bu üçü birlikte fade'i production kanıtı olmaktan çıkarır.

---

## ROL 6 — ÜRÜN / FINPILOT KURUCUSU

- En değerli çıktı **negatif sonuç**: "rejim ekleyince yön çıkar" beklentisi 8. bağımsız yoldan kapandı. Bu, Attention Map'in betimleyici ürün konumunu (vaat: "olağandışı, yön bilinmiyor") şirketin tek dürüst anlatısı olarak pekiştiriyor — grant/investor anlatısında "we tested direction 8 ways and killed it ourselves" güvenilirlik varlığıdır.
- `catalyst_factor`=0.0 keşfi, event-veri hattını somut bir milestone haline getiriyor.
- Fade, kâr vaadi olarak değil; FinSense akademi içeriği ("gap sonrası ilk hareket genelde terslenir — %60 brüt") olarak düşük riskli kullanıcı değeri üretebilir — **ama ancak CONFIRMATORY sonrası.**

---

## ROL 7 — DRL / RL UZMANI

- RL bileşeni yok; 7A–7E kapsam dışı. Not: fade gibi kırılgan bir sinyal RL reward'una girerse, agent'ın %0.91 brüt edge'i öğrenip maliyet gerçeğinde sistematik kaybetmesi tipik bir reward-hacking senaryosu olur — RL entegrasyonundan önce maliyet modeli şart (HYPOTHESIS → tasarım kuralı).

---

## ÇATIŞAN GÖRÜŞLER

> **Quant:** Fade %59.9 win rate, +%0.91 mean — nominal binom altında anlamlı.
> **Red Team:** Gün-kümeli pozitif gün oranı %54.2 (p≈0.60), top %5 çıkınca mean %0.20, %1 maliyette negatif, hipotez test verisinde keşfedildi.
> **Çatışma:** Nominal örneklem istatistiği vs kümelenme + maliyet + multiple-testing.

> **Founder:** "Gap-down Watch daha az negatif" replike oldu — kullanıcıya bağlam olarak sunulabilir.
> **Leakage Detective:** Gap skorun girdisi; gap-down ↔ düşük skor mekanik korelasyon. Matched control geçilemedi.
> **Çatışma:** Gözlem gerçek ama nedensel/bağımsız değil — ürün dili olarak bile riskli.

---

## KANIT LEDGER

| Bulgu | Kanıt | Güven | Tür | Kritik Eksik |
|---|---|---|---|---|
| Rejim×Tier yön üretmiyor | H1 matrisi + OOS replikasyonu + matched control | High | EVIDENCE | — |
| High tier her rejimde negatif | 9/9 hücre + matched control 0.02–0.33 | High | EVIDENCE | c2c_5d bütünlüğü |
| Fade brüt %59.9 win / +%0.91 | 698 gözlem, sabit seed | Med | EVIDENCE (brüt) | Maliyet, OOS |
| Fade %1 maliyette negatif | Maliyet stres tablosu | High | EVIDENCE | Gerçek spread verisi |
| Fade gün-kümeli anlamsız | 59 gün, %54.2 pozitif gün | Med | EVIDENCE | Daha uzun cache |
| c2c_5d etiket bütünlüğü şüpheli | ρ=0.845 açık işi | Med | FACT (anomali) | Kök neden analizi |
| catalyst_factor sabit 0.0 | 48.188 satır | High | FACT | Event veri hattı |
| OOS penceresi quasi-OOS | Deney geçmişi kaydı | High | FACT | Locked OOS hiç açılmadı |
| Fade hipotez-test aynı veri | Batarya geçmişi | High | FACT | Bağımsız cache dönemi |

---

## DENETİM SKORU

| Boyut | Skor | Gerekçe |
|---|---|---|
| Evidence Quality | **MEDIUM** | Negatif ana sonuç sağlam; olumlu yan bulgular kırılgan |
| Experiment Integrity | **MEDIUM** | Pre-registration + split var; ama hipotez-test aynı veri (H3), quasi-OOS |
| Statistical Reliability | **LOW-MEDIUM** | Kümelenme sonrası etkin N küçük; H3 gün seviyesinde anlamsız |
| Economic Reliability | **LOW** | Maliyet stresi fade'i öldürüyor; H1 zaten negatif |
| Production Readiness | **NO** | Execution modeli yok, etiket bütünlüğü açık |

---

## DENEY STATÜSÜ

- **H1 (Rejim×Tier):** 🔴 **FAIL** — ana hipotez desteklenmedi (bu, planlı ve değerli bir negatif sonuçtur).
- **H3 (fade):** 🟠 **DISCOVERY SIGNAL** — pattern var, doğrulanmamış, maliyet-kırılgan.

## ANA KARAR

- **H1 → STOP.** Rejim katmanı yolu kapatılmalı. Koşul: hiçbir — 8 bağımsız başarısızlık yeterli.
- **H3 → CONFIRMATORY_CANDIDATE (koşullu).** Neden: tek canlı örüntü; ancak onayı şu üçüne bağlı: (a) intraday cache genişletme (≥3 ay, hacim dahil) — Level B veri işi; (b) gerçekçi spread/maliyet modeli; (c) yeni veri üzerinde pre-registered tek atış (eski 698 gözlem artık keşif olarak mühürlü). Bu üçü olmadan fade hakkında hiçbir olumlu cümle ürün yüzeyine çıkamaz.
- **catalyst_factor → DATA_REPAIR.** Event etiketi hattı kurulmadan H2 sınıfı sorular cevaplanamaz — Level B.
- **c2c_5d bütünlüğü → DATA_REPAIR.** ρ=0.845 anomalisi H1/H2'nin zeminini etkiliyor — Level A araştırma, öncelikli.

## LEVEL

**A (Discovery).** B'ye çıkış kapıları: bağımsız veri + maliyet modeli + tek-atış pre-registration. C/D/E gündemde değil.

## KILL CRITERIA (fade için)

1. Genişletilmiş cache'te (yeni dönem) gün-bazlı pozitif gün oranı <%55 veya maliyetli mean ≤0 → fade yolu kalıcı kapanır.
2. Basit baseline (her gap günü sabit yön) fade'den ayırt edilemezse → kapanır.
3. %0.5 maliyette net win rate <%52 çıkarsa → ekonomik olarak ölü, kapanır.

## LEVEL B/C ONAY ŞARTLARI

- B: yeni dönem intraday veri + maliyet modeli + pre-registered tek atış + gün-kümeli bootstrap.
- C (paper): B geçildikten sonra canlı gözlem, spread gerçek ölçümü, slippage logu. Meriç onayı zorunlu (Level C insan onayıdır).

## SON SORU

**Bu deney tam olarak hangi iddiayı destekliyor?**
"FinPilot'un attention çerçevesi yön bilgisi üretmez; rejim, sektör ve gün-içi yol katmanları da bunu değiştirmiyor. Ürünün doğru vaadi betimleyici dikkat haritasıdır."

**Hangi iddiayı desteklemiyor?**
"Gap fade tradeable'dır", "strong-down günlerde attention hisseleri rebound yapar", "event türü yönü ayırt eder", "High tier herhangi bir rejimde pozitif getiri verir."

**Hangi kritik bilinmeyen çözülmeden sonuç production evidence olamaz?**
c2c_5d etiket bütünlüğü (ρ=0.845 anomalisi) ve fade'in maliyet-sonrası, bağımsız-dönem varlığı. İlki tüm H1/H2 zeminini, ikincisi tek olumlu sinyalin tamamını belirliyor.

---

_Governance: Level A araştırma; production değişikliği yok; locked OOS NOT_OPENED. Kurul kararı decision-log'a işlendi._
