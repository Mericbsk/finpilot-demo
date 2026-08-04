# Evren Genişletme — Araştırma Metni: Hangi Hisseleri Dahil Edelim?

Sürüm: 1.0 · Tarih: 2026-07-31 · Level A (araştırma/analiz; canlıya dokunmaz)
Kapsam: 1.800 → ~8.000 kararı için (a) mevcut evrenin gerçeği, (b) dahil/hariç kriterleri,
(c) katmanlı evren tanımı, (d) backtest tasarımı ve local koşum planı.
Not: gerçek 8.000-backtest verisi **local EODHD çekimi** gerektirir (sandbox'ta ağ yok).

---

## 1. MEVCUT 1.812 EVRENİN GERÇEĞİ (ölçüldü, 400 örneklem)

| Boyut | Bulgu |
|---|---|
| Sembol sayısı | 1.812 (statik `web/public/stock_presets.json`) |
| Fiyat medyanı | $16.63 |
| Fiyat <$5 oranı | **~%31** (penny/sub-$5 kuyruğu) |
| ADV medyanı | $6.75M |
| **ADV < $1M oranı** | **~%32** (pratikte işlem yapılamaz likidite) |
| ADV ≥ $100M | ~%27 |
| Veri eksik | ~%0.5 |

**Ana çıkarım:** Mevcut evren zaten **~üçte-bir illikit/penny kuyruk** taşıyor. Bugünkü "seçim
edge üretmedi" bulgusunun bir kısmı bu olabilir — illikit isimlerde sinyal gürültülü, spread/slippage
sonrası gerçekçi değil. Yani **naif büyütme yanlış soru**; doğru soru: *kaliteyi bozmadan kapsamı
nasıl artırırız (ve mevcut kuyruğu temizler miyiz)?* Master prompt ilkesi ("en büyük değil en doğru
evren") burada ampirik olarak destekleniyor.

---

## 2. EVREN KAYNAKLARI (nereden 8.000?)

| Kaynak | Kapsam | Kullanım |
|---|---|---|
| **EODHD** exchange-symbol-list (`.US`) | ~26.000 aktif + on binlerce delisted | Araştırma/backtest evreni + **survivorship-free** (delisted dahil) |
| **Alpaca** `/v2/assets` (`tradable=true`) | İşlem-yapılabilir ABD equity | **Canlı** evren (gerçekten işlem açılabilecekler) |

Öneri: **araştırma/backtest** evreni EODHD'den (delisted dahil, survivorship için); **canlı tarama**
evreni Alpaca tradable ∩ kalite filtreleri. İkisi aynı olmak zorunda değil (katmanlı model).

---

## 3. DAHİL / HARİÇ KRİTERLERİ (objektif eşikler)

**Dahil (hepsi sağlanmalı):**
- Borsa: NYSE, Nasdaq, NYSE American (AMEX). **OTC hariç.**
- Enstrüman: adi hisse (common stock). **Hariç:** ETF, leveraged/inverse ETF, ETN, warrant, right, unit, preferred, SPAC (pre-deal). *(ADR ayrı değerlendirilir — likidite yüksekse dahil.)*
- Fiyat: **≥ $3** (penny/sub-$3 hariç — manipülasyon/gap riski, gerçekçi olmayan sinyal).
- Likidite: **20-gün ortalama dolar hacmi ≥ $1M** (Tier'a göre yükselir, aşağıda).
- Veri: son 60 günde OHLCV tamlığı; eksikse Tier düşürülür veya elenir.

**Hariç:** OTC, ADV < $1M, fiyat < $3, uygun olmayan enstrüman, aşırı veri boşluğu.

**Delisted:** yalnız **backtest/araştırma** evrenine (survivorship-bias düzeltmesi); canlıya girmez.

---

## 4. KATMANLI EVREN (öneri — "1.800 mü 8.000 mi" ikilisine alternatif)

| Katman | Objektif eşik | Rol |
|---|---|---|
| **Tier 1 — Production** | Fiyat ≥ $5 · ADV ≥ $10M · veri tam · spread düşük | Günlük tarama + Telegram/web adayları |
| **Tier 2 — Extended research** | Fiyat ≥ $3 · ADV $1M–$10M · veri yeterli | Taranır + izlenir; doğrudan yayın adayı DEĞİL (daha yüksek eşik) |
| **Tier 3 — Discovery** | Fiyat ≥ $3 · ADV $0.5M–$1M · geniş | Yalnız araştırma/keşif; yayın zincirine bağlı değil |
| **Excluded** | OTC · fiyat < $3 · ADV < $0.5M · uygun olmayan enstrüman | Hiç taranmaz |

**Tier geçişi:** bir sembol Tier 2 → Tier 1'e yalnız N-gün ADV/spread/veri eşiğini **ve** shadow'da
kanıtlı kaliteyi sağlarsa geçer. Böylece Tier 1 kalitesi düşmeden kapsam artar.

**Neden katmanlı:** 8.000'in fırsatını (Tier 2/3'te keşif) alırken riskini (Tier 1 yayın kalitesi)
sınırlar. Tek dev liste = kalite/hız/maliyet riski.

---

## 5. BACKTEST TASARIMI (ne değişir? — hipotezleri ölç)

**Senaryolar (hepsi AYNI sinyal mantığı, tarih, giriş/çıkış, maliyet modeli):**
- **S0** — mevcut 1.812 (baseline).
- **S0-temiz** — mevcut evren ama Tier 1 filtresi (ADV≥$10M, fiyat≥$5) → *illikit kuyruğu atınca edge düzeliyor mu?* **En önemli test.**
- **S1** — +likit ekleme (~3–4k, ADV≥$10M).
- **S2** — +mid/small-cap (~5–6k, ADV≥$1M).
- **S3** — ~8.000 geniş (yalnız araştırma).

**Ölçülecek metrikler (her senaryo):** taranan sembol, eligible oranı, başarı/tp oranı, **medyan +
p10/p90 getiri**, **maliyet-sonrası net getiri** (komisyon+spread+slippage), **kontrol grubuna göre
excess** (SPY/IWM/QQQ), maksimum drawdown, sektör/market-cap/likidite segmenti, veri hata oranı,
tarama süresi, API çağrı/kota.

**Zorunlu kalite kontrolleri:** survivorship (EODHD delisted ile), look-ahead, delisting/ticker-change,
corporate action, likidite gerçekçiliği (spread/slippage), out-of-sample/walk-forward, aynı-anda-açılan
korelasyon, overfitting.

**Birincil karar metriği:** sinyal sayısı DEĞİL → **maliyet-sonrası, likidite-gerçekçi, kontrol-karşılaştırmalı
edge.** (Bugünkü bulgu: mevcut evrende bu negatifti.)

---

## 6. "NE DEĞİŞİR?" — TEST EDİLECEK HİPOTEZLER

1. **H1 (kalite):** Tier 1 filtresi (S0-temiz) mevcut evrenin edge'ini **düzeltir** — çünkü illikit
   kuyruk gürültü/negatif katıyor. *Beklenti: en yüksek olasılıklı kazanım burada.*
2. **H2 (kapsam):** Geniş evren (S1–S3) **yeni, mevcut evrende olmayan** yüksek-kaliteli adaylar
   getirir — ama bunlar mevcut adaylarla yüksek korelasyonlu mu, gerçekten yeni mi?
3. **H3 (artımsal edge):** Yeni eklenen segmentin sonucu baseline'dan **anlamlı** iyi mi, yoksa
   sadece daha çok-düşük-kaliteli aday mı?
4. **H4 (maliyet/kapasite):** 8.000'de tarama süresi + API kota + maliyet yayın penceresini/planı
   aşıyor mu? (lineer mi, retry/rate-limit ile orantısız mı?)

---

## 7. LOCAL KOŞUM PLANI (senin makinende)

Repo'da hazır: `fetch_full_universe_and_retest.py` (`--provider eodhd`) + `shadow_scorecard.py`.
Öneri sıra (kota-dostu):
```
1. Evren listesini çek: EODHD exchange-symbol-list (US) → filtrele (Bölüm 3 kriterleri) → tier'la.
2. Küçük örnek (500 sembol) fetch → sembol başına süre + kota tüketimi + hata oranını ÖLÇ (Faz 4 kapasite).
3. S0-temiz backtest'i ÖNCE koş (mevcut evren + Tier 1 filtresi) → H1'i test et (en ucuz, en kritik).
4. Fizibilite OK ise S1/S2 fetch + backtest → H2/H3.
5. Sonuçları shadow_scorecard + kontrol grubu + çoklu-benchmark ile değerlendir.
```

---

## 8. KARAR EŞİKLERİ + GOVERNANCE
- **Karar metriği:** bir senaryo ancak **kontrol grubuna ve IWM'e göre pozitif, maliyet-sonrası** edge
  gösterirse "iyi" sayılır. Sinyal sayısı artışı başarı değildir.
- **Level:** araştırma/backtest = **A** (dry-run, canlıya dokunmaz). Canlı tarama evrenini değiştirmek
  = **B** (insan onayı). Canlı işlem/risk = **C**.
- **Geri dönüş:** mevcut 1.812 `stock_presets.json` sürümlü, tek komutla geri alınabilir kalır.
- **Shadow-mode:** genişletilmiş evren yalnız dry-run; Telegram/web'e ASLA otomatik gitmez.

---

## 9. İLK SOMUT ADIM
**S0-temiz testi** (H1): mevcut evrene Tier 1 filtresi uygulanmış hâlde backtest — hiç veri çekmeden,
elimizdeki price_cache ile yapılabilir. "İllikit kuyruğu atınca edge düzeliyor mu?" sorusuna **bugün**
cevap verir ve tüm genişletme kararının yönünü belirler. Bunu ben şimdi koşabilirim.

**Açık kararlar:** (1) fiyat/ADV eşikleri (öneri: Tier1 $5/$10M) sana uygun mu? (2) EODHD plan günlük
API kotası nedir (tam-evren fetch fizibilitesi buna bağlı)?
