# FinPilot Araştırma Yol Haritası v2

Sürüm: 2.0 · Tarih: 2026-07-31 · Level A (araştırma yönetişimi) · Sahibi: Research
Geçersiz kılar: "daha fazla TP/SL kombinasyonu arama" eksenli v1 yaklaşımı.

---

## VİZYON

> FinPilot araştırmasının amacı **daha fazla TP/SL kombinasyonu denemek değildir.**
> Amaç: **istatistiksel olarak doğrulanmış, production ortamında tekrarlanabilir, en yüksek
> beklenen-değerli (expected value) işlemleri DOĞRU SIRAYLA seçebilen bir karar sistemi** geliştirmek.
> TP/SL optimizasyonu bu karar sistemini destekleyen **ikincil** bir katmandır.

Kanıt bu vizyonu destekliyor: bugüne dek yapılan aramalar, yeni TP/SL kombinasyonlarının tek başına
doğrulanmış avantaj üretmediğini; asıl potansiyelin **işlem seçimi (ranking), giriş kalitesi, rejim
uyumu ve portföy davranışı** tarafında OLABİLECEĞİNİ gösteriyor. (Bu hâlâ test edilecek bir hipotez.)

---

## ⚖️ TEMEL İLKE — "Her şey edge_recheck dürüst-metrikten geçer"

Hiçbir faktör, skor, kural, veri kaynağı veya kombinasyon; **`edge_recheck.py` dürüst metriğinden
(gerçekleşen kapanış-kapanış c2c5 / cost'lu c2c5_net / triple-barrier tb_ret) VE zaman-bölünmüş
IS/OOS testinden geçmeden** "edge" veya "iyileştirme" sayılmaz.

**Yasaklar:** (1) `resolved_pct_t5` (MFE-yanlı, best-case) sonuç metriği olarak kullanılamaz — kanıtlandı
ki sahte edge üretir. (2) Ortalama getiri uç-değer içerir → **medyan + cap'li ortalama** kullan.
(3) Yalnız IS'te iyi olan konfig kabul edilmez. (4) Sinyal sayısı artışı başarı değildir.

---

## ÖNCELİK TABLOSU (v2) + DURUM

| Öncelik | Araştırma Alanı | Neden önce | Durum (2026-07-31) |
|---|---|---|---|
| ⭐⭐⭐⭐⭐ | **Veri Bütünlüğü & Validation** | Validation bozuksa her sonuç şüpheli | 🟡 Kısmen: `resolved_pct_t5` MFE-bozuk (P0), Mart-2026 dilimi artefakt (−99), canlı karne yfinance-kırılgan → **formalize et** |
| ⭐⭐⭐⭐⭐ | **Production Ranking / Entry Quality** | Getiriyi en çok hangi işlemlerin seçildiği belirler | 🟡 Cevap-negatif: **entry_ok expectancy −0.11 (baseline +0.39'un ALTINDA)**; skorlar IC~0 → iş "yeni edge" değil, "neden"i attribute etmek |
| ⭐⭐⭐⭐⭐ | **Expectancy + MAE/MFE** | Sorun giriş mi çıkış mı ayırır | 🟢 Yapıldı: MFE +3.7 / MAE −8.3 (asimetri); triple-barrier negatif; expectancy tablosu çıktı |
| ⭐⭐⭐⭐ | **Portfolio Simulation** | İşlem başarısı ≠ portföy başarısı | 🔴 Açık: dürüst-metrikle henüz yok |
| ⭐⭐⭐⭐ | **Market Regime Conditioning** | Strateji rejime göre değişir | 🟡 Kısmen: bull/bear IC ikisi de ~0 (SPY 50-SMA); daha derin kırılım açık |
| ⭐⭐⭐ | **Dynamic Exit** | Ancak giriş kalitesi doğrulanınca anlamlı | 🔴 Açık, düşük öncelik |
| ⭐⭐ | **Yeni TP/SL Grid** | En düşük; tek başına yetersiz kanıtlandı | ⚪ Bilinçli ertelendi |

### Eklenen iki alan (v1'de vurgulanmayan)
| | Alan | Durum |
|---|---|---|
| ➕ | **Feature Attribution** — her bileşenin katkısı | 🟢 Yapıldı: tüm skor/faktör dürüst-IC ~0; composite getiri-negatif faktörlere (lottery/overnight) yükleniyor |
| ➕ | **Probability Calibration** — skor → P(kazanç) eğrisi | 🔴 Açık: IC~0 iken düz çıkması beklenir ama görsel/istatistik teyit değerli |

---

## ŞU ANA KADAR SABİTLENEN BULGULAR (roadmap'i kapılayan)

1. **Dürüst metrikte doğrulanmış tradeable alfa YOK** — composite IC −0.03, finpilot +0.03, ATR ~0/negatif; 2-faktör (74) ve 4000-konfig ağırlık araması IS/OOS'ta başarısız.
2. **`resolved_pct_t5` P0-bozuk** (MFE-yanlı) — eski "edge" iddiaları bununla yeniden temellenmeli.
3. **Scanner entry_ok değer yok ediyor** — expectancy −0.11 < baseline +0.39.
4. **~~Tek lead~~ ELENDİ (2026-07-31):** `finpilot_score` üst-%10'un +1.09 expectancy'si **dönem/coverage artefaktı** çıktı. Coverage-matched: alt-küme baseline'ı zaten +0.96 → finpilot katkısı yalnız **+0.13**. IS/OOS: her ikisinde de baseline'ın ALTINDA (Δ −0.60 / −0.67), IC işaret değiştiriyor (+0.086 → −0.032). → **Doğrulanmış tradeable edge kalmadı; ranking/entry tam cevap-negatif.**

---

## SONRAKİ ADIMLAR (öncelik sırası)

1. ~~finpilot lead doğrulaması~~ ✅ **YAPILDI → ELENDİ** (2026-07-31; artefakt). Ranking/entry'de araştırılacak lead kalmadı.
2. **[P0] Veri bütünlüğü formalizasyonu** — Mart-2026 artefaktını temizle; `resolved_pct_t5`'i üretimde `edge_recheck` motoruyla değiştir (Level B taslak); validation kapsamını (kaç sinyal çözülüyor, boşluklar) raporla.
3. **[P1] Portfolio simulation (dürüst)** — top-N seçim, pozisyon boyutu, eşzamanlı-pozisyon korelasyonu, drawdown; işlem→portföy dönüşümü.
4. **[P1] Probability calibration** — skor decile → gerçek kazanç olasılığı eğrisi (dürüst c2c5_net).
5. **[P1] Yeni-veri fizibilitesi** — teknik faktörler tükendi; YENİ bilgi sınıflarını `edge_recheck`'ten geçir.
   - 🟢 **Opsiyon-faktörü pilotu HATTI KURULDU** (2026-07-31): `data/eodhd_client.py::options_eod` + `options_factor_pilot.py` (put/call OI/hacim, ATM IV, IV skew, OI; IS/OOS IC). Ağsız test edildi. **LOCAL-RUN bekliyor:** `--probe` (plan/şema teyit) → `--build` → `--analyze`. Ön koşul: EODHD UnicornBay opsiyon eklentisi plan kapsamı.
   - 🔴 Sentiment/short% (elde var, ilk turda flat) granüler yeniden test; Finnhub vb. (bkz. `docs/2026-07-31-dis-kaynaklar-repo-veri-degerlendirme.md`).
6. **[P2] Regime derin kırılım · Dynamic exit** — giriş kalitesi bir sinyal bulununca.

---

## GOVERNANCE
- Tüm bu araştırma **Level A** (analiz; üretim skoru/scanner/entry-exit/risk/canlı yüzey değişmez).
- `resolved_pct_t5` üretim metrik-düzeltmesi, entry-gate değişikliği, canlı skor değişikliği = **Level B** (Meriç onayı + decision-log).
- Referans motor: `edge_recheck.py`. Ana rapor: `docs/2026-07-31-FinPilot-Research-skorun-anlami-RAPOR.md`. Karar: `docs/governance/decision-log.md` (2026-07-31 Level A girdisi).

---

## KAPSAM DIŞI / AÇIK SORULAR
- Bear testi elimizdeki SPY dilimiyle yapıldı (Mart–Nis 2025 düzeltme) ama gerçek uzun bear (2022 gibi) verisi yok → local EODHD çekimi gerekebilir.
- ML skor yeniden-kurulumu: n/rejim yeterli + yeni-veri faktörü bulunana kadar ertelendi (mevcut faktörlerde bilgi yok).
- Intraday giriş kuralları (VWAP/ORB) intraday veri bekliyor.
