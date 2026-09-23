# Direction Signal Source Scouting — "Hangi ek veri yön taşıyabilir?" (PRE-REGISTERED)

**Tarih:** 2026-09-18 · **Level:** A (read-only araştırma planı; hiçbir deney/veri/kod değiştirilmedi)
**Tetikleyici:** Meriç — "hangi ek veri/sinyal yön taşıyabilir araştırmasını aç"
**Bağlam:** Direction prediction 8+ yolla başarısız; Detection (attention) yön taşımıyor. Bu çalışma **yön taşıyabilecek YENİ sinyal kaynaklarını** değerlendirir.

> **Dürüst çerçeve:** Bu FinPilot'ın en çok başarısız olduğu alan. **"Hiçbiri yön taşımıyor" geçerli ve olası bir sonuçtur.** Negatif sonuç = değerli bilgi (başka kaynak aramaya gerek kalmaz). Cherry-pick yapmamak için her aday **önceden** sınıflandırılır.

---

## 1. Mevcut alt-veri envanteri (kanıtla, bugün)

| Kaynak | İçerik | Kapsam | Tarih aralığı | Point-in-time uygun mu |
|---|---|---|---|---|
| `edgar_cache/` | SEC filings (4, 8-K, 10-Q, S-1...) | 1.127 dosya | 1994→2026-07 | ✅ Evet (tarihli) |
| `finra_cache/` | Short interest (bi-weekly) | 1.216 sembol | 2017→2026-06 | ✅ Evet (tarihli) |
| `news_cache/` | Haber skoru/zamanı | 1.216 sembol | 2025-08→2026-07 | ✅ Evet (tarihli) |
| `fundamentals_cache.json` | float_shares, short_pct | 1.116 sembol | snapshot | ⚠️ Kısmen (snapshot, zaman serisi değil) |
| `macro_regime.json` | regime/vix/spread | global | snapshot | ⚠️ Zayıf (4 key) |
| `sector_cache.json` | sektör eşlemesi | 144 | statik | — (yön değil, gruplama) |
| `catalyst_cache.json` | catalyst factor | **8** | — | 🔴 REGRESE (dual-writer) |

## 2. Aday sinyaller (literatür + mevcut veri eşlemesi)

Her aday: akademik dayanak + mevcut veri + neden yön taşıyabilir + risk.

| # | Sinyal | Literatür dayanağı | Veri | Yön hipotezi | Ana risk |
|---|---|---|---|---|---|
| S1 | **Short-interest değişimi (ΔSI)** | Short interest ↑ → negatif beklenti (Desai et al.); ama aşırı SI squeeze yapabilir | finra_cache (bi-weekly seri) | SI artışı → düşüş / aşırı SI → squeeze | bi-weekly gecikme; coverage bias |
| S2 | **Insider buying (Form 4)** | İçeriden alım → pozitif sinyal (Jaffe; Lakonishok) | edgar_cache (Form 4) | insider alım → yükseliş | Form 4 parse gerekir (şu an [form,date] tuple; alım/satım ayrımı yok) |
| S3 | **8-K material events** | Event-driven momentum (PEAD) | edgar_cache (8-K) | olumlu 8-K → drift | event tonu/yönü sınıflandırma gerekir |
| S4 | **News sentiment skoru** | Haber tonu → kısa-vadeli drift (Tetlock) | news_cache (tarih+skor) | pozitif haber → yükseliş | skorun ne ölçtüğü belirsiz (0.99 sabit?) |
| S5 | **Float / short_pct seviyesi** | Düşük float + yüksek short → squeeze potansiyeli | fundamentals_cache | yüksek short_pct + düşük float → yukarı kırılma | snapshot (point-in-time değil) |

## 3. Neden bunlar önceki 8+ başarısızlıktan farklı?

Önceki başarısızlıklar **fiyat/teknik** sinyallerdi (regime, breadth, sektör, tier, momentum, intraday path). Bunlar **olay/taban** sinyalleri (insider davranışı, short-selling, kurumsal olaylar, haber tonu) — fiyatın **nedenini** ölçer, fiyatın kendisini değil. Literatürde en güçlü cross-sectional yön kanıtları bu kategoride.

**Ama:** Bu da başarısız olabilir. Özellikle:
- Bi-weekly/snapshot veri gecikmesi sinyali öldürebilir
- Coverage bias (yalnızca belirli semboller)
- Attention map'in bulduğu gibi, "hareket var ama yön yok" burada da çıkabilir

## 4. Pre-registered test tasarımı (her aday için aynı disiplin)

Her aday, mevcut B3/B4 disiplinine uygun olarak:
1. **Point-in-time doğruluk:** Sinyal tarihi < outcome tarihi (leakage yok). Snapshot kaynaklar (S5) bu yüzden zayıf.
2. **Primary metric:** Spearman(signal, c2c_1d) — önceden sabit. Secondary: quintile monotonicity.
3. **Random/matched control:** aynı gün, aynı universe.
4. **Walk-forward:** tek bölünme değil.
5. **Negatif sonuç politikası:** "yön taşımıyor" geçerli cevap.
6. **Çoklu test düzeltmesi:** 5 aday × metrik → Bonferroni/FDR notu.

## 5. Öncelik sırası (uygulanabilirlik × literatür gücü)

| Öncelik | Aday | Neden |
|---|---|---|
| **1** | S2 Insider buying (Form 4) | En güçlü literatür + EDGAR'da var + point-in-time temiz. AMA: alım/satım ayrımı için Form 4 detay parse gerekir (şu an yok) — **data work gerekli** |
| **2** | S1 ΔSI (short interest değişimi) | Seri var, point-in-time temiz, test en kolay |
| **3** | S4 News sentiment | Veri var ama skorun ne ölçtüğü belirsiz (0,99 sabit görünüyor — doğrulama gerekir) |
| **4** | S3 8-K events | EDGAR'da var ama ton/yön sınıflandırması gerekir |
| **5** | S5 float/short_pct | snapshot — point-in-time zayıf, en son |

## 6. En büyük önkoşul (bloker)

**S2 (insider) için EDGAR Form 4'te alım/satım ayrımı yok** — şu an `[form_type, date]` tuple. Yön sinyali için "insider ALIYOR mu SATIYOR mu" gerekir. Bu bir **data-extraction işi** (Form 4 transaction code parse) — read-only değil, ayrı Level B data work.

**S1 (ΔSI) bu yüzden en temiz başlangıç** — seri zaten var, parse gerekmez.

## 7. Önerilen ilk adım (Meriç onayıyla)

**S1 — Short-interest değişimi (ΔSI) yön testi** (en düşük maliyetli, point-in-time temiz):
- Sinyal: SI'nın son iki bi-weekly okuma arasındaki değişimi
- Hipotez H0: ΔSI ile c2c_1d arasında yön ilişkisi yok
- H1 (iki yönlü): SI artışı → düşüş (klasik) VEYA aşırı SI → squeeze
- Pre-registered, random control, walk-forward, negatif-sonuç kabul

Bu, "ek veri yön taşır mı" sorusunun **en ucuz ve en temiz** ilk ölçümü. Sonuç negatifse diğer adaylara geçeriz; pozitifse matched-control + OOS'a derinleşiriz.

## Governance
- Read-only plan; hiçbir deney/veri/kod/production değiştirilmedi.
- Bu bir **araştırma önerisi** (Level A). S1 testi pre-registered olur; sonucu önceden bilmiyoruz.
- Negatif sonuç = geçerli ve değerli (başka kaynak aramayı durdurur veya yeniler).
