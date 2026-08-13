# External Finance Resources Review

Tarih: 2026-08-12
Katman: Research
Seviye: Level A, research-only
Durum: Uygulandı; üretim değişikliği yok

## Kapsam ve karar sınırı

Bu rapor, kullanıcı tarafından paylaşılan 11 dış kaynağın FinPilot/FinSense
bağlamında teknik faydasını, lisans/provenance riskini ve en küçük güvenli
araştırma adımını değerlendirir. Bu bir üretim veri kabulü, model promosyonu,
scanner/score/entry-exit değişikliği veya ticari lisans görüşü değildir.

Dış kaynaklara ilişkin bulgular üçüncü taraf proje/dataset metadata'sına
hakkında yapılan incelemedir; FinPilot backtest sonucu değildir. Mevcut FinPilot
kararlarıyla uyumlu olarak tahmin/alpha çerçevesi dondurulmuş/pivot edilmiş,
P1 data reliability ve P2 label/execution kapıları BLOCKED, locked OOS ise
NOT_OPENED durumundadır. Bu rapor bu kapıları açmaz.

## Kısa karar özeti

| Kaynak | En iyi kullanım | Lisans/provenance durumu | Karar |
|---|---|---|---|
| Kronos | İzole OHLCV modelleme ve benchmark smoke test | MIT kod/model bildirimi; veri ve model ağırlığı şartları ayrıca doğrulanmalı | İzole araştırma/pilot |
| Cloudflare Computer | Agent sandbox, dosya/SQLite/MCP deneyleri | MIT; açıkça preview ve production dışı | İzole araştırma/pilot |
| DeepTutor | Finance Academy pedagojisi, evidence-linked memory ve agent loop tasarımı | Apache-2.0 | Hemen kullanılabilir, mimari referans |
| MatrAIx Persona 1M | Persona/survey UX araştırması, sentetik cohort deneyi | Kaynak lisansları devam eder; gerçek kayıtlardan türetim ve PII/provenance riski | Lisans/veri doğrulaması olmadan kullanılmayacak |
| Finance News API | Haber ingestion sözleşmesi için prototip | Space README Apache-2.0; gerçek haber kaynağı, endpoint ve güncellik doğrulanmadı | İzole araştırma/pilot |
| Finance-Instruct-500k | Offline finance-QA veri kalite örneklemesi | HF Apache-2.0 etiketi; karma kaynak zinciri ve gürültü riski | İzole araştırma/pilot |
| FinanceBench | Evidence-grounded finansal QA değerlendirmesi | CC-BY-NC-4.0 etiketi; ticari kullanım için açık engel/risk | Hemen kullanılabilir, yalnızca evaluation |
| Finance Alpaca | Küçük instruction prototipi ve evaluator deneyi | HF MIT etiketi; GPT-3.5/FiQA/Alpaca upstream hakları doğrulanmalı | İzole araştırma/pilot |
| Yahoo Finance Data | Schema/lineage ve corporate-action veri araştırması | ODC-BY etiketi; upstream şartları ve PIT uygunluğu doğrulanmalı | Lisans/veri doğrulaması olmadan kullanılmayacak |
| Ritual Finance Agent | Agent davranışı/veri formatı incelemesi | Metadata ve viewer doğrulanamadı | Lisans/veri doğrulaması olmadan kullanılmayacak |
| Stock Finance | Finansal tablo schema ve Çin piyasası araştırması | Kartta lisans/provenance yok; çok büyük dataset | Lisans/veri doğrulaması olmadan kullanılmayacak |

## Kaynak bazında değerlendirme

### 1. Kronos

Kaynak: https://github.com/shiyu-coder/Kronos

Kronos, OHLCV serilerini tokenizer ile temsil eden Transformer tabanlı bir
finansal zaman serisi modelidir. Repo ve model kartı MIT olarak sunuluyor;
512 bağlam ve Qlib üzerinden fine-tuning/deney akışı öne çıkıyor. Bu, FinPilot
araştırmasına modelleme tekniği ve reproducible smoke-test iskeleti katkısı
verebilir.

Kullanım sınırı: Kronos tahmin performansı FinPilot için kanıt değildir. Model
çıktısı scanner sinyali, score bileşeni veya canlı karar olarak kullanılmamalı.
Veri kaynağı, model ağırlığının lisans şartları, corporate-action işlemesi,
PIT zaman damgaları ve gerçek execution maliyeti ayrıca incelenmelidir.

Önerilen pilot: Küçük, quarantined ve yalnızca point-in-time olduğu doğrulanmış
OHLCV örneğinde tek bir horizon smoke test; baseline ve naive kontrol ile
karşılaştırma; sonuç yalnızca rapora yazılır.

### 2. Cloudflare Computer

Kaynak: https://github.com/cloudflare/computer

Computer; Durable Object SQLite dosya sistemi, container/isolate runtime'ları
ve MCP örnekleri içeren deneysel bir agent çalışma alanı yaklaşımıdır. MIT
lisansı belirtiliyor; proje kendi açıklamasında preview ve production dışı
olduğunu belirtiyor.

FinPilot katkısı, Finance Academy veya research sandbox için izole görev
çalıştırma, dosya/artifact yönetimi ve MCP tool ergonomisi olabilir. Kullanıcı
verisi, production execution, sır saklama veya kritik karar akışı için temel
alınmamalı. Buradaki değer ürün kodunu kopyalamak değil, sınırlandırılmış
araştırma çalışma alanı desenlerini incelemektir.

### 3. DeepTutor

Kaynak: https://github.com/HKUDS/DeepTutor

DeepTutor Apache-2.0 lisanslı, kişiselleştirilmiş tutoring workspace'i; ortak
agent loop, multi-engine RAG, inspectable memory, MCP ve skill yaklaşımı
sunuyor.

FinSense için en doğrudan katkı burada: kullanıcının düşünme kaydı, evidence
bağları, yanlış cevap sonrası geri bildirim ve ders akışının birbirinden
ayrılması; cevap üretimi yerine kanıt izlenebilirliğini merkeze alan bir
Finance Academy tasarım notu. Bu, yeni bir finans kuralı değil, mevcut
öğrenme yüzeyi için mimari referanstır. Tam uygulama ithal etmek yerine küçük
bir evidence/memory sözleşmesi incelenmeli.

### 4. MatrAIx Persona 1M

Kaynak: https://huggingface.co/datasets/MatrAIx2026/MatrAIx_Persona_1M

HF API/card açıklamasına göre 999.847 persona, 1.290 kategorik alan, yaklaşık
4.17 GB packed Parquet ve iki bileşen bulunuyor: 599.847 gerçek kayıtlardan
türetilmiş, 400.000 sentetik. Kaynaklar Wiki, Stack Overflow, Amazon, GSS,
PRISM ve survey olarak ayrılıyor. Packed 4-bit alanlar için `pyarrow` ve
ayrı codebook gerekiyor; eksik alanlar imputasyon olarak yorumlanmamalı.

Kartın önemli sınırlaması: veri temsilî örnek değildir; human-grounded,
verified demek değildir; model extraction hataları vardır; sentetik oranı
tasarım seçimidir ve “source licenses and terms continue to apply”. Bu
nedenlerle kullanıcı profili, risk profili, kişiselleştirilmiş finansal tavsiye
veya commercial training için uygun kabul edilemez.

Yalnızca açık lisans/provenance ve PII incelemesinden sonra sentetik UX cohort
simülasyonu düşünülebilir. Şimdilik kullanılmayacak.

### 5. Finance News API

Kaynak: https://huggingface.co/spaces/ayush2917/finance-news-api

Space çalışır durumda görünüyor; README metadata'sı Apache-2.0 ve Docker SDK
kullanıyor. Repo ağacında `app.py`, `database.py`, Dockerfile ve requirements
bulunuyor; ancak inceleme sırasında güvenilir bir API route sözleşmesi,
haber sağlayıcı, lisans zinciri, retention/freshness veya ticker coverage
kanıtlanamadı.

Potansiyel katkı, yalnızca ingestion adapter prototipi ve response-schema
karşılaştırmasıdır. Gerçek endpoint, kaynak haber lisansı, timestamp semantiği,
duplicate davranışı, rate limit ve haber metni yeniden dağıtım hakkı
kanıtlanmadan FinPilot verisine bağlanmamalı.

### 6. Finance-Instruct-500k

Kaynak: https://huggingface.co/datasets/Josephgflowers/Finance-Instruct-500k

Dataset kartı yaklaşık 518.185 satır, 580 MB ve `system/user/assistant`
alanlarını bildiriyor. Apache-2.0 etiketi ve çoklu kaynaklardan birleştirilmiş
instruction örnekleri bulunuyor.

FinPilot'a katkısı, domain QA örneklerinin offline kalite örneklemesi,
retrieval/evaluator prompt prototipi ve cevap biçimi karşılaştırması olabilir.
Ancak aggregate lisans etiketi upstream içerik haklarını tek başına çözmez;
duplicate, sentetik cevap, yanlış finans bilgisi, stale bilgi ve tavsiye dili
filtrelenmelidir. Fine-tuning veya kullanıcıya gösterilen içerik için önce
küçük örnek ve provenance audit yapılmalı.

### 7. FinanceBench

Kaynak: https://huggingface.co/datasets/PatronusAI/financebench

FinanceBench, evidence-linked finansal soru-cevap değerlendirme benchmark'ıdır;
kartta 150 örnek ve CC-BY-NC-4.0 lisans etiketi görülüyor.

En yüksek öncelikli kullanım, FinSense/Finance Academy cevaplarının kanıta
bağlanması, abstention ve citation kalitesinin ölçülmesi için evaluation-only
harness'tir. Eğitim verisi olarak içeri aktarmak veya ticari ürüne doğrudan
katmak lisans nedeniyle ayrıca insan/legal inceleme gerektirir. Bu benchmark
FinPilot performans sonucu değildir; yalnızca değerlendirme protokolü
referansıdır.

### 8. Finance Alpaca

Kaynak: https://huggingface.co/datasets/gbharti/finance-alpaca

Kart yaklaşık 68.912 satır ve 42.9 MB bildiriyor; Alpaca, FiQA ve GPT-3.5
üretilmiş instruction çiftlerinin karışımı olarak tanımlanıyor. HF etiketi MIT
olsa da upstream FiQA/Alpaca içeriklerinin hakları ve GPT-üretilmiş cevapların
kalitesi ayrıca doğrulanmalı.

Küçük örnekle prompt/evaluator ve format prototipi yapılabilir. Finansal
gerçeklik, tarihsel geçerlilik, citation eksikliği ve tavsiye dilini filtreleyen
bir audit olmadan training corpus veya public content kaynağı yapılamaz.

### 9. Yahoo Finance Data

Kaynak: https://huggingface.co/datasets/defeatbeta/yahoo-finance-data

Kart yaklaşık 4 GB ve fiyat, statements, filings, news, earnings calls,
splits/dividends ve treasury yields dahil çok sayıda Parquet tablo bildiriyor;
ODC-BY etiketi görülüyor.

En değerli olası katkı, veri şeması/lineage audit'i ve corporate-action/PIT
araştırmasıdır. Ancak Yahoo-derived veriyi canonical backtest kabul etmek
özellikle announcement timestamp, restatement, delisting, survivorship,
adjustment ve news reuse açısından kanıt gerektirir. ODC-BY etiketi tek başına
upstream içerik ve ticari yeniden dağıtım hakkını çözmez. P1 data gate geçilmeden
scanner veya locked OOS'a alınmayacak.

### 10. Ritual Finance Agent

Kaynak: https://huggingface.co/datasets/surojitpvt/ritual-finance-agent

İnceleme sırasında dataset card/viewer ve güvenilir schema/provenance bilgisi
çıkarılamadı; görünen metadata çok sınırlıydı. Bu nedenle içeriğin ne olduğu,
lisansı, upstream kaynakları ve kullanım hakkı hakkında sonuç çıkarılamaz.

Şimdilik kullanılmayacak. Raw README, repository history, files, schema,
license ve örnek satırlar bağımsız olarak doğrulanmadan herhangi bir import,
training veya benchmark yapılmamalı.

### 11. Stock Finance

Kaynak: https://huggingface.co/datasets/langwnwk/stock_finance

Kart; `balance_report`, `profit_report`, `cash_report`, `profit_quarter`,
`cash_quarter` Parquet dosyalarını ve çok sayıda Çin hisse senedi HDF5 serisini
listeliyor. HF kartında açık bir license/provenance alanı görünmüyor.

Schema karşılaştırması, rapor dönemi ile açıklanma tarihinin ayrıştırılması,
quarter/report duplication ve Çin piyasası veri coverage araştırması için
teknik olarak ilginç olabilir. Ancak lisans, upstream provider, revision,
corporate-action, report availability timestamp ve quality log doğrulanmadan
FinPilot'a alınmayacak. Özellikle report period'i announcement date yerine
kullanmak look-ahead riski yaratır.

## Önceliklendirilmiş araştırma programı

### A. Hemen yapılabilecek, düşük riskli

1. **FinanceBench evaluation harness:** 10-20 örnekle evidence retrieval,
   citation, abstention ve answer-grounding ölçüm iskeleti. Dataset'i training
   corpus olarak kullanmadan, lisans etiketini raporda görünür tutarak çalışır.
2. **DeepTutor-inspired Academy design note:** case -> evidence -> learner
   response -> feedback -> revision akışı ve inspectable memory alanları için
   ürün dışı mimari not. FinSense'in mevcut beş manuel vaka sınırını korur.

### B. İzole pilot

3. **Finance-Instruct-500k / Finance Alpaca sample audit:** rastgele küçük
   örnek, duplicate oranı, ticker/tarih varlığı, citation, tavsiye dili,
   sentetiklik ve upstream attribution tablosu.
4. **Kronos smoke test:** yalnızca quarantined OHLCV, naive baseline ve
   reproducible seed; sonuç production signal değildir.
5. **Finance News API contract probe:** public endpoint, sample response,
   source URL, publication timestamp, ticker mapping, rate limit ve retention
   davranışını kaydetme.
6. **Yahoo Finance Data schema/lineage audit:** yalnızca metadata/schema,
   announcement-vs-period date ve corporate-action alanlarını inceleme;
   canonical backtest'e veri eklememe.
7. **Cloudflare Computer sandbox review:** production dışı küçük agent task ve
   SQLite/MCP ergonomi deneyi; kişisel veya kritik veri kullanmama.

### C. Şimdilik kapalı

8. MatrAIx Persona 1M: source-license, PII ve data subject/provenance incelemesi
   olmadan kullanılmayacak.
9. Ritual Finance Agent: metadata/schema/lisans kanıtı yok.
10. Stock Finance: lisans ve PIT/report availability kanıtı yok.
11. FinanceBench'i commercial training veya public product content'e katmak:
    CC-BY-NC-4.0 nedeniyle legal/human review olmadan yapılmayacak.

## Sonuç ve açık kapılar

En yüksek pratik değer, yeni bir alpha modeli ithal etmekten değil, kanıt
bağlı cevap kalitesi ve veri bütünlüğü kapılarını güçlendirmekten geliyor.
FinanceBench evaluation-only, DeepTutor mimari referans ve küçük dataset
sample audit'i ilk sırada olmalı. Kronos, Yahoo ve haber API'si araştırma
laboratuvarında kalmalı; hiçbirinin çıktısı production score, ranking,
entry/exit, risk, publication veya live davranışa taşınmamalı.

Bu raporun açık bıraktığı doğrulamalar:

- Her dataset için upstream lisans zinciri ve ticari yeniden dağıtım şartları.
- Finance News API'nin gerçek endpoint, source provider, freshness ve response
  contract'ı.
- Persona 1M için source-level PII/legal basis ve derived-record kullanım
  hakkı.
- Yahoo/Stock Finance için point-in-time availability, restatement,
  corporate-action ve delisting lineage.
- Ritual Finance Agent'in gerçek schema, files ve lisans metadata'sı.

Bu rapordaki sonuçlar araştırma önerisidir; insan onayı olmadan ürün veya
production kararı olarak yorumlanmamalıdır.
