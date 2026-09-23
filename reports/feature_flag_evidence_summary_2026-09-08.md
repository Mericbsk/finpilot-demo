# Feature Flag Kanıt Özeti — 9 Açık Flag

Tarih: 2026-09-08
Level: A (salt-okunur — hiçbir flag/kod/config değiştirilmedi)
Tetikleyici: `reports/master_project_reality_audit_2026-09-08.md` PART J CRITICAL bulgusu + Araştırma Portföyü Kurulu #1 önceliği
Yöntem: Her flag için (a) kod-seviyesi varsayılan değeri (b) `.env`'deki fiili değeri (c) bu 2 yıllık araştırma programında veya repo genelinde bulunan doğrudan kanıt.

**Ortak bulgu:** Grep edilen 9 flag'in **hepsinin kod-seviyesi varsayılanı `"0"` (kapalı)**. `.env`'de hepsi `1`. Yani mevcut durum "kasıtlı açık" değil, koddaki güvenli varsayılanın manuel olarak ezilmiş hali — bu, denetim raporunun "muhtemelen kasıtsız drift" yorumunu destekliyor.

---

## Tablo

| Flag | Kod varsayılanı | `.env` | Score'u nasıl etkiliyor | Bu programda kanıt | Değerlendirme |
|---|---|---|---|---|---|
| `FINPILOT_ENABLE_LOTTERY_FADE` | 0 | **1** | `lottery_factor`, composite'te ağırlık -2.0, legacy_quality'de -1.5 | **TEK doğrulanmış sinyal.** `score_component_decomposition.py`: rho=-0.204, t=-6.60, **Bonferroni'de hayatta kalan tek bileşen** (eşik \|t\|>4.56). Negatif yönlü (riskten kaçınma sinyali), skor formülünde zaten doğru yönde (çıkarılıyor) kullanılıyor. | **Açık kalması kanıtla destekleniyor.** |
| `FINPILOT_ENABLE_SQUEEZE_FACTOR` | 0 | **1** | `squeeze_factor`, composite +1.5, legacy_quality +0.5 | Test edildi, **güvenilmez**: n_gün=23 (ince), null-baseline şüpheli şekilde sıfır değil (+0.0338) — ne pozitif ne negatif kesin sonuç yok. | **Kanıt yetersiz** — açık/kapalı kararı veri kalitesine bağlı, şu an ne destekleniyor ne çürütülüyor. |
| `FINPILOT_ENABLE_OVERNIGHT_GAP` | 0 | **1** | `overnight_gap_factor`, composite formülünde kullanılıyor | Test edildi, **ölü**: CI sıfırı içeriyor (`score_component_decomposition.py`), hem lottery/gap re-weight testinde hem decomposition'da tutarlı. | **Kanıt kapalı tutmayı destekliyor** — hiçbir turda pozitif sonuç çıkmadı. |
| `FINPILOT_ENABLE_EDGAR_CATALYST` | 0 | **1** | `catalyst_factor`, legacy_quality'de dolaylı (lottery-relief kolu) | Test edildi, **veri yetersiz** (n_gün<8, decomposition'da). Ayrıca bugün (2026-09-03/07 civarı) teşhis edildi: cache pratikte boş/bayat (bu oturumda da doğrulandı — 8 sembol/0 nonzero, ya da benim doldurduğum 1.199/0 nonzero, ikisi de tazelik açısından anlamsız). | **Açık olması riskli değil ama FAYDASIZ** — şu an skor'a gerçek bilgi eklemiyor, sadece gürültü/0.0 ekliyor. Cache tazelenmeden açık kalmasının pratik zararı yok ama yararı da yok. |
| `FINPILOT_ENABLE_FRED_MACRO` | 0 | **1** (gerçek API key `.env`'de mevcut) | Makro rejim girdisi, composite'e katkı (score_engine.py:89) | **Bu programda hiç test edilmedi** — `full_universe_enriched.csv`'de bu bileşene ait bir kolon yok, decomposition/red-team envanterinde geçmiyor. | **UNKNOWN** — ne kanıt var ne karşı-kanıt. |
| `FINPILOT_ENABLE_FUNDAMENTALS` | 0 | **1** | `compute_fundamental_score` (features.py:543), composite'i etkiliyor, EODHD 24s cache | **Bu programda hiç test edilmedi.** | **UNKNOWN.** |
| `FINPILOT_ENABLE_NEWS` | 0 | **1** | `compute_news_catalyst` (features.py:644), EODHD news+polarity, score'u etkiliyor | Muhtemelen CSV'deki `sentiment` kolonuyla ilişkili/aynı aile — `score_component_decomposition.py`'de `sentiment` "yetersiz veri (n_gün<8)" olarak işaretli, ama bu flag ile birebir aynı üretim yolu olduğu bu oturumda doğrulanmadı (kod-seviyesinde ayrıca teyit gerekir). | **BELİRSİZ/UNKNOWN** — muhtemel ilişkili zayıf kanıt var ama teyitsiz. |
| `FINPILOT_ENABLE_ALPHA_V2` | 0 | **1** | Squeeze ağırlığını 0.5/0.5→0.7/0.3 değiştiriyor (risk_engine.py:204, features.py:172) — yapısal bir re-weighting, tek faktör değil | **Bu programda hiç matched-control ile test edilmedi.** Ayrıca decision-log'da (2026-07-XX) bu flag'in test paketine sızıp sonuçları bozduğu belgeli — yani en azından bir kez zaten operasyonel karışıklığa neden olmuş. | **UNKNOWN + geçmişte sorun çıkarmış** — dikkatli değerlendirilmeli. |
| `FINPILOT_ENABLE_SHADOW_SCORECARD` | 0 | **1** | **Skor formülünü etkilemiyor** — `distribution/jobs.py:615` altında izole bir ölçüm/rapor işi (model-bağımsız ileri getiri, MFE, bootstrap CI üretir) | Kendi testleri var (`tests/test_shadow_scorecard.py`, 3 passed), amacı zaten "measure without affecting". | **Farklı kategori — risksiz.** Skoru değiştirmiyor, yalnızca ölçüm üretiyor. Açık kalması sorun değil. |

---

## Sadeleştirilmiş özet

- **Açık kalması kanıtla desteklenen:** `LOTTERY_FADE` (tek gerçek sinyal), `SHADOW_SCORECARD` (zaten skoru etkilemiyor, salt ölçüm).
- **Kanıtla çürütülmüş, kapatılması savunulabilir:** `OVERNIGHT_GAP` (ölü sinyal, hiçbir turda pozitif çıkmadı).
- **Zararsız ama faydasız (kapansa da açık kalsa da fark etmez, ÇÜNKÜ veri bayat):** `EDGAR_CATALYST` — asıl sorun flag değil, cache'in taze tutulamaması (ağ erişimi bu ortamda yok, bu oturumda ayrıca belgelendi).
- **Kanıt yetersiz, veri kalitesi sorunlu:** `SQUEEZE_FACTOR` — ne açık ne kapalı için güçlü gerekçe var.
- **Tamamen test edilmemiş (gerçek UNKNOWN):** `FRED_MACRO`, `FUNDAMENTALS`, `NEWS`, `ALPHA_V2` — bu dördü hakkında bu programın hiçbir yerinde matched-control/rank-korelasyon testi yok. `ALPHA_V2` ayrıca geçmişte test paketine sızıp karışıklık yaratmış olması nedeniyle ekstra dikkat gerektiriyor.

## Not — flag'lerin kendisi mi, "kanıt yok" mu asıl sorun?

Denetim raporunun "kritik çelişki" çerçevelemesi doğru ama biraz kabaca genelliyor: 9 flag'in hepsi aynı risk seviyesinde değil. `LOTTERY_FADE` ve `SHADOW_SCORECARD` açık kalmalı zaten kanıtlı/zararsız. Asıl açık risk 4 tamamen test edilmemiş flag (`FRED_MACRO`, `FUNDAMENTALS`, `NEWS`, `ALPHA_V2`) ve kısmen `SQUEEZE_FACTOR` — bunlar composite skoru etkiliyor ama hiçbiri bu 2 yıllık programın hiçbir turunda matched-control ile sınanmadı.

## Hiçbir şeye dokunulmadı

Bu rapor tamamen salt-okunur derleme — `.env`, `score_engine.py`, hiçbir dosya değiştirilmedi. Karar Meriç'e ait.
