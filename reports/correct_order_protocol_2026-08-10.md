# Veri → Ölçüm → Execution → Sinyal — Uygulama Protokolü

Date: 2026-08-10
Level: B (research-process change; human approval required)
Layer: Research / governance
Status: **proposal** — Level B, Meriç onayı bekliyor

## Amaç

"Veri → ölçüm → execution → sinyal" sırasını bir ilke olmaktan çıkarıp
**çalışan bir kapı zincirine** çevirmek. Her katman bir kapıdır; üst katmana
ancak alt katman kapandığında geçilir. Bu, iki yıllık "edge" anlatısının tek
bir etiket hatasıyla çökmesinin (MFE ≠ getiri) tekrarlanmasını engeller.

## Temel mekanizma: dört kapı

Her araştırma hipotezi, sinyal katmanına ulaşmadan önce üç kapıyı geçmek
zorundadır. Bir kapı açıksa, üst katmandaki hiçbir sonuç "bulgu" sayılmaz —
yalnızca "keşif sinyali" olarak işaretlenir ve pre-registration'a gider.

```
VERI kapisi ──→ OLCUM kapisi ──→ EXECUTION kapisi ──→ SINYAL (confirmatory)
   │                │                   │                    │
   │ aciksa:        │ aciksa:           │ aciksa:            │ ancak burada
   │ hicbir olcum   │ hicbir execution  │ hicbir sinyal      │ "bulgu"
   │ anlamli degil  │ iddiasi anlamli   │ iddiasi anlamli    │ sayilir
   │                │ degil             │ degil              │
```

---

## KAPI 1 — VERI (data integrity)

**Kapanma kriterleri (hepsi şart):**

| # | Kriter | Mevcut durum | Kapanma eylemi |
|---|---|---|---|
| 1.1 | Etiket semantiği doğrulanmış | ✅ **KAPANDI (tanım)** / ⚠️ **ilk analizler keşif-sinyali** (2026-08-10) | `resolved_pct_t5`=MFE belgelendi; `c2c_5d`/`mae_t5` export'ta. NOT: bu etiketle üretilen ilk iki headline-sayı (-2.39%/+0.06%; matched +0.50/-0.61) gün-kümeli+dedup+matched-random testten (Kapı 2.1/2.3) GEÇMEDİ — t~-0.86 ve t~-0.01, ikisi de anlamsız. Yön (eligible zayıf) P1/Mirror-L4/P0-P3 ile tutarlı ama bu iki sayı kendi başına "bulgu" değil, protokolün kendi tanımıyla "keşif sinyali"dir. Kanıt: `docs/governance/decision-log.md` [2026-08-10] "KONTROL TURU" ve "KONTROL TURU #2". |
| 1.2 | Fiyat sürekliliği | ❌ AÇIK | 148 işaretli sembolün adjusted OHLC onarımı; EODHD adjusted OHLC sağlamıyor → alternatif kaynak veya manuel corporate-action tablosu |
| 1.3 | Feature timestamp/age lineage | ❌ AÇIK | Her feature için "hangi anda biliniyordu" alanı export'a eklenir |
| 1.4 | Restatement dedektörü | ❌ AÇIK | Aynı tarihli barın zaman içindeki değişimini izleyen aylık audit |
| 1.5 | Benchmark adjustment standardı | ❌ AÇIK | Aday ve benchmark (SPY/IWM) aynı adjustment standardında |

**Kapı 1 açıkken:** Hiçbir ölçüm sonucu "bulgu" sayılmaz. Yalnızca keşif.

**Bu hafta yapılabilir (ajan):** 1.3 (feature lineage şeması tasarımı) ve 1.4
(restatement dedektörü pilotu, 100 sembol). 1.2 ve 1.5 veri kaynağı kararı
gerektirir (Level B).

---

## KAPI 2 — ÖLÇÜM (measurement)

**Kapanma kriterleri:**

| # | Kriter | Mevcut durum | Kapanma eylemi |
|---|---|---|---|
| 2.1 | Etkin örneklem raporu | ✅ ÖLÇÜLDÜ (S1) | Her raporda zorunlu alan yap |
| 2.2 | Deney bütçesi defteri | ❌ AÇIK | Toplam koşulan konfigürasyon sayısı + harcanan "şans bütçesi" public; `research/experiment_registry.py` genişletilir |
| 2.3 | Null-relative preflight | ❌ AÇIK | Her yeni bulguya zorunlu matched-null kontrolü (label/signal/time-shift); `research/negative_control.py` zorunlu gate yap |
| 2.4 | Replayable telemetry | ❌ AÇIK (Level B pending) | P0 score replay'i kapatacak export onayı |
| 2.5 | Tarih-blok bootstrap CI | ✅ KISMEN | Her raporda zorunlu alan yap (bataryalarda var, ana hatta yok) |

**Kapı 2 açıkken:** Hiçbir execution iddiası anlamlı değil.

**Bu hafta yapılabilir (ajan):** 2.2 (registry'ye bütçe muhasebesi) ve 2.3
(negative_control'ü preflight gate'e bağlama). 2.4 Level B onayı bekliyor.

---

## KAPI 3 — EXECUTION (tradeability)

**Kapanma kriterleri:**

| # | Kriter | Mevcut durum | Kapanma eylemi |
|---|---|---|---|
| 3.1 | Spread/ADV verisi | ❌ YOK | Günde 3 kez bid/ask snapshot toplama başlat (30 gün biriktir) |
| 3.2 | Signal half-life | ❌ YOK | Sinyalin predictive gücü kaç saat/gün sürüyor — entry-delay sweep (E1 altyapısı hazır) |
| 3.3 | İntraday path | ❌ YOK | İntraday OHLCV kaynağı (Level B veri kararı) |
| 3.4 | Capacity join | ❌ AÇIK | Likidite snapshot'ını tarihsel outcome'lara join |

**Kapı 3 açıkken:** Hiçbir sinyal iddiası anlamlı değil.

**Bu hafta yapılabilir (ajan):** 3.2 (signal half-life, mevcut daily veriyle
kaba ama dürüst bir ilk ölçüm). 3.1 veri toplama altyapısı kurulumu gerektirir
(ajan kodu yazar, Meriç zamanlanmış görevi kurar). 3.3/3.4 veri kaynağı
kararı (Level B).

---

## KAPI 4 — SİNYAL (confirmatory)

**Açılma koşulu:** Kapı 1 + 2 + 3 kapalı.

**İlk confirmatory adaylar:** Pre-registered üç hipotez (gap-reversal,
rvol-inversion, ATR-parity) — temiz `c2c_5d` etiketiyle, **yeni veriyle**,
null-relative, etkin-örneklem-düzeltmeli.

**Ama önce:** kullanıcı-gerçeği kapısı (PR1/PR7) — çünkü bu hipotezlerin ürün
değeri, kullanıcının ne istediğine bağlı.

---

## Ne değişir? (before/after)

| Alan | Before (ters sıra) | After (doğru sıra) |
|---|---|---|
| Yeni hipotez | Hemen backtest'e girer | Önce Kapı 1–3 kontrolü; açık kapı varsa "keşif" etiketi |
| Bulgu raporu | "edge bulundu" | "keşif sinyali" (kapılar açık) vs "bulgu" (kapılar kapalı) |
| Etiket | MFE getiri sanılıyor | Her etiketin semantiği kaynak koddan doğrulanmış |
| Örneklem | satır sayısı | etkin örneklem (blok-bootstrap) |
| Null kontrolü | isteğe bağlı | zorunlu preflight |
| Execution | hiç ölçülmez | spread/half-life/capacity kapısı |
| Score tuning | sürekli | Kapı 1–3 kapalı olmadan dondurulmuş |

## Beklenen zorluklar (dürüst)

1. **Yavaşlık hissi:** Kapı 1–3'ü kapatmak haftalar alır; bu sürede "hiçbir
   şey üretmiyoruz" hissi olur. Ama iki yıllık hızlı üretimin çıktısı
   MFE-şişirilmiş bir anlatıydı — yavaş ve doğru, hızlı ve yanlışı yener.
2. **Kapı 1.2 (fiyat sürekliliği) veri kaynağı kararı gerektirir** — EODHD
   adjusted OHLC sağlamıyor; alternatif kaynak maliyet/kapsam trade-off'u
   (Level B).
3. **Kapı 3 (execution) veri toplama süresi gerektirir** — spread/ADV 30 gün
   biriktirme ister; bu sürede execution kapısı açık kalır ve sinyal
   katmanı kilitli kalır.
4. **Kullanıcı-gerçeği kapısı (PR1/PR7) paralelde yürümeli** — quant kapıları
   kapanırken kullanıcı gerçeği de netleşmeli; yoksa doğru sinyali yanlış
   ürüne inşa ederiz.

## 90 günlük yol haritası (doğru sırada)

- **Gün 1–14:** Kapı 1 kalan (1.3 lineage şeması, 1.4 restatement pilotu) +
  Kapı 2 (2.2 bütçe defteri, 2.3 null preflight) + PR1/PR7 başlat (Meriç).
- **Gün 15–30:** Kapı 3 başlat (3.1 spread/ADV toplama altyapısı, 3.2 signal
  half-life ilk ölçüm). PR1/PR7 sonuçları.
- **Gün 31–60:** Kapı 1.2/1.5 veri kaynağı kararı (Level B). Kapı 3 verisi
  birikiyor. Kullanıcı gerçeği netleşiyor.
- **Gün 61–90:** Kapılar kapandıysa → pre-registered üç hipotezin confirmatory
  koşusu (yeni veri, null-relative). Kapanmadıysa → hangi kapının neden
  kapanmadığının dürüst raporu.

## Governance

Bu protokol bir araştırma-süreci değişikliğidir (Level B). Onaylanırsa:
- Her yeni araştırma raporu hangi kapıların kapalı olduğunu beyan eder.
- Açık kapı varken üretilen sonuç "keşif sinyali" etiketi taşır, "bulgu" değil.
- Kapı kapanma kriterleri decision-log'a girer; değişiklik Level B.
- Hiçbir scanner, score, backtest kuralı veya public davranış bu protokolle
  değişmez — yalnızca araştırma süreci düzenlenir.
