# FinBERT — Kanıta Dayalı Derin Araştırma + FinPilot Planı
Durum: TASLAK · 2026-07-30 · Eskalasyon: **A** (analiz; kod değişikliği yok)
Amaç: Pazarlama değil, **kanıt**. "FinBERT bize ne kadar kanıtlanmış gerçekle geliyor?" → sonra plan.
Kaynak notu: Aşağıdaki her iddia güven seviyesiyle etiketlendi. Referanslar §6'da.

---

## 0. Tek cümlelik sonuç

FinBERT **analist-raporu cümlelerinde kanıtlanmış iyi** (%86–97), ama **bizim asıl gireceğimiz
yer olan kısa haber başlıklarında zayıf ve yanlı** (pozitifleri çoğunlukla "nötr" sanıyor); ayrıca
haber-sentiment'in getiriyi öngörme gücü **en iyi ihtimalle küçük ve değişken**. Yani FinBERT gerçek
ve kullanışlı bir araç — ama **sinyal alfası değil**, bir *bağlam/eğitim özelliği + hibe anlatısı*
olarak konumlandırılmalı. Sinyale ağırlık vermek yalnızca kendi A/B'mizden geçerse.

---

## 1. FinBERT nedir — kanıtlanmış temel (GÜVEN: YÜKSEK)

- FinBERT = BERT'in finansal metinle *ileri-eğitilmiş* hâli (Reuters TRC2'den **4.9 milyar token**),
  sonra **Financial PhraseBank** (Malo ve ark. 2014) ile duygu sınıflandırmaya ince-ayarlı.
  Çıktı 3 sınıf: **positive / negative / neutral** + güven skoru. (Araci 2019)
- Bizim `llm/finbert_provider.py` bunu `ProsusAI/finbert` olarak çağırıyor — literatürdeki *orijinal*
  model. Yani doğru, tanınmış modeli kullanıyoruz.

**Kanıtlanmış doğruluk (Financial PhraseBank test):**
- Tam anlaşma alt-kümesi: **%97 doğruluk** (önceki SOTA'dan +6 puan).
- Tüm veri seti (belirsiz cümleler dâhil): **%86 doğruluk** (önceki SOTA'dan +15 puan).
- Karşılaştırdığı yöntemlerin (LSTM, ULMFit, LPS, HSC, FinSSLX) hepsini geçti.

⚠️ **Kritik uyarı:** Bu sayılar **analist raporu / kurumsal iletişim cümleleri** üzerinde. Bizim
girdimiz **kısa, gayrı-resmî haber başlıkları** — aynı dağılım DEĞİL (§3).

---

## 2. Haber-sentiment getiriyi öngörüyor mu? — asıl soru (GÜVEN: KARIŞIK/ORTA)

Bu, tüm değerin bağlı olduğu soru. Literatür **net değil**:

**Şüpheci taraf (güçlü):**
- 1.86 milyon başlık üzerine yapılan kapsamlı bir çalışma: sentiment skorları (firma-özel/genel diye
  ayrıştırılsa bile) **sağlam öngörü gücünden yoksun**. Sadece hafta-sonu/tatil sentiment'inde mütevazı
  sinyal var.
- Bazı veri setlerinde **basit lojistik regresyon FinBERT'e denk** çıkıyor — karmaşık embedding'ler
  her zaman kazandırmıyor.

**Olumlu taraf (mütevazı etki):**
- S&P 500 (2021–2024): haber başlığı sentiment'ini teknik çerçeveye eklemek kazanma oranını
  **~%5** artırdı.
- Bir çalışma: FinBERT özelliğini teknik-yalnız temele **eklemek** AUC'de **+%12.6**, simüle PnL'de
  **+%26.3** kazandırdı (istatistiksel anlamlı).
- Etki **kısa vadede** ve **belirsizlik dönemlerinde** daha belirgin; varlık-özel gecikmeler var
  (piyasa bazen tepkisel değil öngörücü).

**Dürüst özet:** Etki **var ama küçük, kısa-ömürlü ve değişken.** Garanti değil; büyük ölçekli
çalışmalar temkinli. Bizim özel hattımızda işe yarayıp yaramayacağı **ancak kendi backtest/Edge
Report'umuzla** bilinir. Kimse bize "kesin alfa" vaat edemez.

---

## 3. FinBERT'in sınırları — bizim kullanımımıza doğrudan çarpanlar (GÜVEN: YÜKSEK)

Bunlar bizim planımızı belirleyen en önemli gerçekler:

1. **Başlıklarda güçlü NÖTR önyargısı (en kritik).** Zero-shot FinBERT kısa başlıklarda
   pozitif/negatifleri sıklıkla "nötr" sanıyor: bir değerlendirmede **nötrlerde %82.7 doğru ama
   pozitiflerde yalnız %16.8**. Yani bizim ham `yfinance` başlıklarında faktör büyük ihtimalle
   çoğu zaman 0.5 (nötr = skora etki yok), ara sıra da pozitifi kaçırır. **%86–97 rakamı bize
   uygulanamaz.**
2. **Alan + zaman kayması (drift).** Farklı kaynak/dönem → sözcük dağarcığı ve öncelikler değişir;
   geçmiş doğruluk yeni veride geçersizleşebilir. Sürekli izleme şart.
3. **Sayılara ve bağlama duyarsız.** "%50 düşüş" gibi sayısal ifadeleri, negasyonu, ince bağlamı
   iyi yakalayamaz.
4. **Yalnız İngilizce + resmî finansal dil.** Sosyal medya argosu, ticker, meme → güvenilmez.
   (Bizim mevcut agent hattı Reddit/HN başlığı besliyor — bu FinBERT için kötü girdi.)

---

## 4. Daha iyi alternatif var mı? (GÜVEN: ORTA-YÜKSEK)

3-yönlü sınıflandırma doğrulukları (bir karşılaştırmadan):
- ChatGPT zero-shot: **%63.4**
- **FinBERT (bizim model): %71.2**
- FinGPT (LoRA ince-ayar): **%78.8**
- FinGPT (SFT+RLSP): **%82.1**

Çıkarımlar:
- **İnce-ayarlı FinBERT, zero-shot GPT-3.5/4'ü geçebiliyor** — yani ucuz, yerinde bir temel.
- **GPT-4o few-shot ≈ ince-ayarlı FinBERT** — ama API maliyeti + prompt işçiliği.
- **FinGPT (ince-ayarlı) en yüksek** — ama kurulum/işçilik ağır; DRL parked iken bize erken.
- Jenerik LLM'ler (Qwen dâhil) zero-shot'ta uzman modelin altında.

**Bizim için pratik sonuç:** Ham `ProsusAI/finbert` (bizde olan) = en ucuz ama en zayıf uç.
Daha iyisini istersek yol *ince-ayar* ya da *few-shot GPT* — ikisi de gerçek işçilik. İlk turda
ham FinBERT'i bir **temel** olarak kullan, faydayı ölç, sonra yükseltmeye karar ver.

---

## 5. FinPilot için kanıta dayalı PLAN

Prensip: FinBERT'i **abartma**. Kanıt diyor ki: başlıklarda zayıf + getiri-öngörüsü küçük/belirsiz.
Öyleyse onu güçlü olduğu ve riskin düşük olduğu yerde kullan.

### Konumlandırma kararı (en önemli)
FinBERT'i **sinyal skorunun alfa kaynağı olarak DEĞİL**, şu iki rolde konumlandır:
- **(A) Bağlam/eğitim özelliği:** kart/sayfada "son haber tonu: olumlu/nötr/olumsuz + kaynak linki"
  diye *gösterilen* bir bağlam. Yanlışsa maliyeti düşük (karar vermiyor, bilgi veriyor), doğruysa
  kullanıcıya değer. Bizim "eğitim + şeffaflık" konumlandırmamıza tam oturur.
- **(B) Hibe anlatısı:** "Açık, akademik olarak doğrulanmış finansal NLP modelini (FinBERT) kamu
  başlıklarına uyguluyor; kendi Edge Report doğrulamamızdan geçmeden hiçbir sinyale ağırlık
  vermiyoruz." aws Deep Tech için animasyondan çok daha güçlü, dürüst bir hikâye.

### Faz 0 — Sıfır-kod gerçeklik kontrolü (KOVA C'den sonra, yarım saat)
- `.env`'e `HF_API_TOKEN` ekle → `active_provider()` gerçekten `finbert-hf-api` mı, kanıtla.
  (Şu an sistem sessizce keyword'e düşüyor; önce FinBERT'in *koştuğunu* gör.)
- 20–30 örnek Türkçe/İngilizce başlıkta elle bak: nötr önyargısı bizde de var mı? **Kendi verimizde
  %16.8 sorununu doğrula/yala.** Bu tek test, gerisini yönlendirir.

### Faz 1 — Düşük-riskli gösterim özelliği (opsiyonel, Faz 0 iyi giderse)
- `yfinance` başlıkları → `score_texts` → sembol başına ton etiketi. Skora **0 ağırlık**; yalnız
  kart/sayfada bağlam olarak göster. Kullanıcı değeri + veri toplama, sinyal riski yok.

### Faz 2 — Sinyale ağırlık, YALNIZ kanıtla (gölge mod → Edge Report)
- Faktörü `sentiment_cache.json`'a yaz (mevcut desen), `FINPILOT_ENABLE_SENTIMENT=1` ama **gölge
  modda** (skora girer, log'lanır, karar değiştirmez) 4–8 hafta.
- Haftalık Edge Report'ta sentiment bucket'larına göre precision/PnL farkına bak.
  - Anlamlı + pozitifse → küçük ağırlıkla canlıya al.
  - Null/negatifse → **dürüstçe kapat**, ağırlık 0'da kalsın (ama gösterim özelliği kalabilir).

### Yapma listesi (kanıtın söylediği)
- ✗ FinBERT'i "doğruluk %97" diye pazarlama/deck'e yazma — o rakam bizim veримize ait değil.
- ✗ Sosyal medya (Reddit/meme) başlığını FinBERT'e besleyip ciddiye alma — en zayıf girdi.
- ✗ Ölçmeden sinyal skoruna ağırlık verme.
- ✗ FinGPT/ince-ayara şimdi girme — DRL parked, traction darboğazı dururken erken.

---

## 6. Referanslar (güven değerlendirmesiyle okundu)

- Araci, D. (2019), *FinBERT: Financial Sentiment Analysis with Pre-trained Language Models* — https://arxiv.org/pdf/1908.10063
- Prosus AI Tech Blog, *FinBERT: Financial Sentiment Analysis with BERT* — https://medium.com/prosus-ai-tech-blog/finbert-financial-sentiment-analysis-with-bert-b277a3607101
- ProsusAI/finBERT (model + README) — https://github.com/ProsusAI/finBERT
- *FinBERT is Wrong 83% of the Time on Positive Headlines* (başlık zayıflığı) — https://tommijohnsen.substack.com/p/finbert-is-wrong-83-of-the-time-on
- *Can News Predict the Market? Limits of Zero-Shot Financial NLP* — https://arxiv.org/pdf/2606.12210
- *News Sentiment and Stock Market Dynamics: A Machine Learning Investigation* — https://www.mdpi.com/1911-8074/18/8/412
- *Sentiment-driven prediction of financial returns: a Bayesian-enhanced FinBERT approach* — https://arxiv.org/pdf/2403.04427
- *Financial Sentiment Analysis on News and Reports Using LLMs and FinBERT* — https://arxiv.org/abs/2410.01987
- *Instruct-FinGPT* (FinGPT ince-ayar karşılaştırması) — https://arxiv.org/pdf/2306.12659
- *Reasoning or Overthinking: Evaluating LLMs on Financial Sentiment Analysis* (ACM AI in Finance) — https://dl.acm.org/doi/10.1145/3768292.3770341

---
_Not: Yalnız analiz (Eskalasyon A). Uygulama, §5 Faz 0'dan başlar ve her faz kendi kanıt kapısından geçer.
Tesisatın ne kadarının hazır olduğu için bkz. `FinBERT_Sinyal_Entegrasyon_Fizibilite_2026-07-30.md`._
