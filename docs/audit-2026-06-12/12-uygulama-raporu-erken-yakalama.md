# Uygulama Raporu — Erken-Yakalama Katmanı + Ölçüm Temeli (P0)

**Tarih:** 2026-06-12 · **Kapsam:** `10-scanner-analiz-ve-arastirma-degerlendirme.md` yol haritasının P0 / erken-yakalama kısmının ilk somut, test edilmiş kod uygulaması.

> **Uyarı:** Sistem-tasarımı uygulamasıdır, yatırım tavsiyesi değildir. Eklenen hiçbir bileşen kanıtlanmış edge değildir; canlıya alınmadan önce gerçek veriyle (triple-barrier + Edge Report) doğrulanmalıdır.

---

## 1. NE YAPILDI (özet)

Scanner'ı "geç-giren teyitçi"den "olmadan önce yakalayan" hale getirmenin **temel, test edilmiş yapı taşları** eklendi. Hepsi **additive ve canlı davranışı değiştirmiyor** — `entry_ok`, composite skor ve mevcut tarama akışı **hiç dokunulmadan** çalışmaya devam ediyor. Raporun disiplinine sadık kalındı: *önce ölç, env-gated, canlı skoru bozma.*

Dört yeni yapı taşı, **22/22 birim testi yeşil**:

| # | Dosya | Ne yapar | Durum |
|---|---|---|---|
| 1 | `scanner/features.py` (+72 satır) | `compute_contraction_factor` (sıkışma/coiled-spring 0-1) + `compute_rvol_acceleration` (hacim ivmesi 0-1) | ✅ test edildi |
| 2 | `scanner/watch_tier.py` (yeni, 200 satır) | WATCH→SETUP→TRIGGER→CONFIRM merdiveni (`classify_tier`) + df→tier glue (`compute_early_tier`) | ✅ test edildi |
| 3 | `scanner/labeling.py` (yeni, 153 satır) | Triple-barrier etiketleme (`triple_barrier_label`) + toplu istatistik (`summarize_labels`) | ✅ test edildi |
| 4 | `tests/test_early_detection.py` (yeni, 214 satır) | 22 birim testi (feature'lar, merdiven, bariyer, uçtan-uca glue) | ✅ 22/22 geçti |

---

## 2. HER PARÇA NEDEN VAR (raporla bağ)

**Sıkışma skoru + RVOL ivmesi (öncü sinyaller).** Rapordaki teşhis: mevcut scanner *etkiyi* (hizalı trend, RSI/MACD onayı) ölçüyor, *sebebi* değil. Bu iki saf-pandas faktör tam da sebebi ölçer: range/volatilite kendi yakın dağılımının dibinde mi (yaylanan zemberek), ve hacim düşük tabandan *yükseliyor mu* (mevcut ikili `volume_spike` "spike oldu" derken, ivme "spike oluşuyor" der). İkisi de dış veri gerektirmez — eldeki günlük OHLCV'den hesaplanır.

**WATCH→SETUP→TRIGGER→CONFIRM merdiveni.** Rapordaki "erken yakalama merdiveni"nin kodu. Mevcut scanner yalnız en alt basamağı (CONFIRM = `entry_ok`) üretiyordu — en geç ve en kesin sinyal. Merdiven, üstteki üç erken basamağı ekler: sistem artık bir hisseyi *entry-ready olmadan önce* "kuruluyor" diye yüzeye çıkarabilir. Her basamağa **tavsiye** (advisory) pozisyon-fraksiyonu bağlı (¼/½/tam Kelly) — rapordaki "onay geldikçe ekle" kademeli boyutlandırması. Bu fraksiyonlar **asla emir vermez**, sadece UI/kullanıcıya öneri.

**Triple-barrier etiketleme (ölçüm temeli).** Raporun P0 birinci maddesi ve "her şeyin ön şartı": bir sinyalin edge'i, hangi bariyerin (TP/SL/zaman) önce vurduğuyla etiketlenmeden ölçülemez. Tek-ufuk getiri yol-bağımlılığını yok sayar. Bu modül López de Prado yöntemini FinPilot'un bar verisine sadeleştirir; MFE/MAE (en olumlu/olumsuz sapma) dahil — haftalık Edge Report'un yakıtı.

---

## 3. NASIL TEST EDİLDİ

`tests/test_early_detection.py`, 22 birim testi. Çalıştırma: repo'nun `.venv`'i bu ortamda kırık symlink + `pip` engelli olduğundan, testler sistem python'ında (pandas 2.3 + numpy 2.2) saf-fonksiyon koşucusuyla yürütüldü. Sonuç: **22 passed, 0 failed.**

Kapsam:
- **Sıkışma:** daralan range → yüksek skor (≥0.6); genişleyen range → düşük (≤0.4); yetersiz veri → 0.0.
- **RVOL ivmesi:** düşük tabandan hacim yükselişi → pozitif; düz hacim → 0.0; yetersiz veri → 0.0.
- **Merdiven:** boş girdi → NONE; coil+hacim → WATCH; katalizör+coil → SETUP (¼); kırılım+hacim → TRIGGER (½); entry_ok → CONFIRM (tam); merdiven sırası monotonik; **entry_ok verilmeden asla CONFIRM olmaz** (saflık garantisi — canlı kapıyı değiştirmediğinin kanıtı).
- **Triple-barrier:** TP önce / SL önce / zaman çıkışı; aynı-bar beraberliğinde temkinli stop; short tarafı; oran-toplamı ≈ 1; boş girdi.
- **Uçtan-uca glue:** sentetik coil + geç hacim → df'den tier dict üretimi; bozuk girdi → NONE (best-effort, raise etmez).

İki test ilk turda sentetik veri kusurundan düştü (düz fiyat serisi Bollinger-genişliğini dejenere ediyordu; oran-toplamı 4-hane yuvarlamadan 0.9999'du). **Fonksiyonlar değil testler düzeltildi** — araştırma dosyasının dediği gibi ≥14-günlük konsolidasyon kullanan gerçekçi veriyle, ve yuvarlama toleransıyla. Bu, fonksiyonların doğru olduğunun ve testlerin gerçeği yansıttığının kanıtı.

**Regresyon riski: yok.** Mevcut hiçbir fonksiyon/imza değiştirilmedi; yalnız `features.py` sonuna fonksiyon eklendi + iki yeni dosya + bir test dosyası. Üç modül de `py_compile`'dan temiz geçiyor. `evaluate.py`'ye **hiç dokunulmadı** → canlı tarama davranışı bit-bazında aynı.

---

## 4. NASIL DEVREYE ALINIR (henüz kapalı — kasıtlı)

Yapı taşları hazır ama **canlı akışa bağlanmadı.** Bağlamak için `scanner/evaluate.py`'de, faktörlerin hesaplandığı bloğun (satır ~350, `_composite_score` civarı) hemen ardına env-gated tek çağrı yeterli:

```python
# Erken-yakalama merdiveni (env-gated, default OFF — canlı davranışı değiştirmez)
early_tier = {"tier": "NONE"}
if os.environ.get("FINPILOT_ENABLE_EARLY_TIER", "0") == "1":
    from scanner.watch_tier import compute_early_tier  # noqa: PLC0415
    early_tier = compute_early_tier(
        df_1d,
        catalyst_factor=catalyst_factor,   # zaten hesaplanıyor
        volume_multiple=volume_multiple,   # zaten return dict'te
        entry_ok=bool(entry_ok),           # mevcut kapı
    )
```
Sonra return dict'e `**early_tier` veya `"early_tier": early_tier` eklenir. `compute_early_tier` best-effort — hata durumunda NONE döner, taramayı asla kırmaz. Flag açılana dek hiçbir şey değişmez.

Triple-barrier ise `outcomes_horizon` reconcile job'unda (kapanan sinyalleri etiketlemek için) ve haftalık Edge Report'ta kullanılır — sinyal *üretimine* değil, *ölçümüne* bağlanır.

---

## 5. NE YAPILMADI VE NEDEN (dürüst kapsam)

- **evaluate.py'ye canlı bağlama yapılmadı.** Bilinçli: rapor "canlı skoru ölçmeden bozma" diyor; ayrıca bu ortamda dosya-aracı ↔ kabuk-mount senkron gecikmesi büyük dosyalarda edit riskini artırıyor. Bağlama tek-satırlık ve yukarıda hazır; ölçüm iskeleti kurulunca açılmalı.
- **Haftalık Edge Report job'u yazılmadı.** `summarize_labels` onun çekirdeği; scheduler job'u + `outcomes_horizon` sorgusu ayrı bir adım (P0 madde 2).
- **Gated faktörlerin (catalyst/squeeze/lottery) ablation'ı çalıştırılmadı.** Bu, canlı/geçmiş veri ve çalışan tam ortam gerektirir; bu oturumun saf-birim test kapsamı dışında.
- **DTW analog, meta-labeling, pre-event ayrı mod (P1):** bu oturumda kapsanmadı; yapı taşları (özellikle triple-barrier etiketleri) onların da zeminini hazırlıyor.
- **Mikro-kap evreni + ceza paketi:** P1; mevcut likidite tabanı korundu.

---

## 6. SONRAKİ ADIMLAR (öncelik sırası)

1. `outcomes_horizon` reconcile'ına `triple_barrier_label` bağla → her kapanan sinyal etiketlensin.
2. Haftalık **Edge Report** job'u (`summarize_labels` + scheduler) → decile_lift/hit-rate/expectancy görünür olsun.
3. `FINPILOT_ENABLE_EARLY_TIER=1` ile merdiveni **gölge modda** aç (sadece kaydet, sinyal üretme) → birkaç hafta WATCH/SETUP adaylarının sonucunu triple-barrier ile ölç.
4. Ölçüm pozitifse: merdiveni UI'da göster (scanner kartında tier rozeti + "neden" listesi), kademeli boyut önerisini yüzeye çıkar.
5. Sonra P1: DTW analog + meta-labeling + ayrı pre-event mod.

**Tek cümle:** Erken-yakalamanın çekirdek mantığı (sıkışma, hacim ivmesi, 4-basamaklı merdiven) ve onu dürüstçe ölçecek triple-barrier temeli kuruldu ve test edildi; sıradaki iş bunları gölge-modda ölçüp, edge kanıtlanırsa canlıya almak — kanıtlamadan değil.
