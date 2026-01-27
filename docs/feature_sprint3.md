# Sprint 3 – Feature Dönüşümü Mimari Özeti

Bu sprint, alternatif veri setlerinden türetilen ham Parquet dosyalarını DRL ajanının kullanılabilir özelliğine dönüştüren modülleri kazandırır.

## 🎯 Hedefler

- Haber ve on-chain verileri için üstel ağırlıklı sentiment, momentum ve gecikme (lag) özellikleri oluşturmak.
- Farklı frekanstaki veri kaynaklarını ortak zaman ekseninde hizalayabilmek.
- Fonksiyonel testlerle edge-case (NaN, boş frame, negatif değer) dayanıklılığını garanti etmek.

## 🧱 Modüller

| Modül | Ana Fonksiyonlar | Açıklama |
| --- | --- | --- |
| `drl/feature_generators.py` | `calculate_weighted_sentiment`, `calculate_momentum`, `create_lag_features`, `assemble_feature_frame` | Üstel ağırlıklı sentiment, % değişim tabanlı momentum ve gecikme kolonları üretir. Haber hacmi (`news_volume`) gibi ağırlıklar opsiyonel olarak kullanılarak yakın zamandaki haberlerin etkisi artırılır. |
| `drl/alignment_helpers.py` | `resample_frame`, `forward_fill`, `align_frames` | Günlük/saatlik/haftalık veri setlerini resample ederek tek frekansa taşır, forward-fill ve interpolasyon stratejileri ile boşlukları doldurur. |

## 🧪 Testler

- `tests/test_feature_generators.py`
  - EWM hesapları elle hesaplanan referansla karşılaştırılır.
  - Momentum yüzdeleri (`pct_change`) ve lag fonksiyonları belirli örneklerle doğrulanır.
  - Feature frame montajının (`assemble_feature_frame`) seri ve DataFrame kombinasyonlarında çalıştığı test edilir.
- `tests/test_alignment_helpers.py`
  - Resample toplamlarının doğru hesaplandığı, forward-fill limitlerinin uygulandığı ve hizalama fonksiyonunun prefiksli kolonlarla birleşimi doğrulanır.

## 🔄 Akış

1. Prefect ETL (`drl.etl.flows`) temizlenmiş haber ve on-chain verisini Parquet partitionlarına yazar.
2. `alignment_helpers.align_frames` ile haber/on-chain veri setleri günlük frekansa getirilir, forward-fill uygulanır.
3. `feature_generators.calculate_weighted_sentiment` yakın zamandaki sentimenti daha yüksek ağırlıkla hesaplarken, `calculate_momentum` zincir aktivitesindeki yön değişimini yakalar.
4. `create_lag_features` ile 1/3/7 günlük gecikmeler eklenir; `assemble_feature_frame` tüm özellikleri tek DataFrame’de toplar.
5. Ortaya çıkan DataFrame, `FeaturePipeline` tarafından ölçeklendirilip DRL ajanına aktarılır.

## 📌 Bir Sonraki Adımlar

- Feature setini Feature Store sözleşmesiyle (schema versioning, artefact metadata) kayıt altına almak.
- Prefect flow’larına feature jenerasyonunu entegre edip MLflow/W&B artefact’larıyla bağlamak.
- Feature önem (SHAP) ve drift (Evidently) metriklerini observability katmanına taşımak.
