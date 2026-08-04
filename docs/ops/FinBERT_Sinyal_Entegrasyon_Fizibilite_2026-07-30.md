# FinBERT → Sinyal Akışı Entegrasyon Fizibilitesi
Durum: TASLAK · 2026-07-30 · Eskalasyon: **A** (teknik analiz; kod değişikliği YOK, yalnız plan)
Kapsam: FinBERT (finansal NLP duygu-analizi) mevcut tarama/sinyal hattına nasıl, ne maliyetle bağlanır?
İlke: kanıt > varsayım. Aşağıdaki her iddia dosya:satır ile doğrulandı.

---

## 1. Sonuç (önce cevap)

**Boru tesisatının ~%80'i zaten yazılmış.** FinBERT sağlayıcısı, skorlayıcı kancası,
cache deseni ve scheduler refresh çengeli hazır. Ama **şu an her yerde uykuda** —
gerçek FinBERT bugüne kadar hiç çalışmadı; sistem sessizce keyword'e düşüyor.

Eksik olan tek şey büyük bir mimari değil, **iki küçük anahtar**:
1. FinBERT'i canlandıran bir sağlayıcı (en ucuz: `HF_API_TOKEN` — ağır bağımlılık yok), ve
2. Scanner için ham başlık kaynağı → `score_texts` → aynı cache formatı (küçük bir refresh fonksiyonu).

**Efor:** düşük (yarım–bir gün). **Risk:** düşük teknik, ama **fayda kanıtlanmadı** —
modülün kendi audit notu bunu doğrulama kapısına bağlıyor (§6). Önce ölç, sonra güven.

---

## 2. Bugün gerçekte ne var (kanıt)

| Parça | Dosya | Durum |
|---|---|---|
| FinBERT sağlayıcı (`score_texts` → 0..1) | `llm/finbert_provider.py:249` | ✅ tam yazılmış; 3 katman: yerel transformers → HF API → keyword |
| Skorlayıcı sentiment kancası (±0.5·ağırlık) | `scanner/score_engine.py:150` | ✅ hazır; yorumda bile "FinBERT sentiment" yazıyor |
| Scanner'ın sentiment faktörü okuması | `scanner/evaluate.py:530-534` | ✅ hazır; ama **EODHD** kaynağından, FinBERT'ten değil |
| EODHD sentiment cache (hot-path güvenli) | `scanner/sentiment.py` | ✅ hazır; env-gated, scheduler-refresh |
| Scheduler refresh çengeli | `core/scheduler.py:1342` | ✅ `refresh_sentiment_cache` çağrılıyor |
| FinBERT'in tek gerçek çağıranı | `agents/social_intelligence_agent.py:104,259` | ⚠️ var ama **DRL/agent hattı parked** (Karar D); girdisi Reddit/HN/Polymarket başlıkları |

### Kritik uyku bulguları (env + bağımlılık)
- `transformers` / `torch` → `requirements*.txt`'te **YOK**. Yerel FinBERT katmanı import'ta sessizce düşüyor.
- `HF_API_TOKEN` / `HUGGINGFACE_TOKEN` → `.env`'de **YOK**. HF API katmanı da kapalı.
- **Net sonuç:** `score_texts()` şu an **daima keyword fallback**'a düşüyor. Gerçek FinBERT hiç çalışmadı.
- `FINPILOT_ENABLE_SENTIMENT` → **YOK** → canlı taramada sentiment **tamamen kapalı** (skora hiç girmiyor).
- `EODHD_API_KEY` → **TANIMLI** (yani "açılırsa" scanner EODHD'nin hazır-skorunu kullanır, FinBERT'i değil).

---

## 3. Asıl karar: hangi hatta, hangi metinle?

FinBERT metin ister (fiyat değil). İki bağlanış noktası var:

**Seçenek A — Scanner sentiment faktörünü FinBERT ile beslemek (ÖNERİLEN).**
Bu, günlük sinyallerde ve karnede görünen faktör. Bugün ya kapalı ya da paralı EODHD'ye bağlı.
FinBERT'i buraya koymak = **ücretsiz başlık + kendi validated NLP** ile paralı EODHD bağımlılığını
değiştirir/tamamlar. Hem maliyet düşer hem aws Deep Tech anlatısı güçlenir ("açık, doğrulanmış
finansal NLP modelini kamu başlıklarına uyguluyoruz").

**Seçenek B — Agent hattı (zaten kodlu).** DRL/agent pipeline `score_texts`'i çağırıyor ama
hat parked (Karar D) ve girdisi finansal haber değil sosyal başlık. Sinyal kalitesine bugün
etkisi yok. **Şimdilik dokunma.**

---

## 4. Seçenek A için minimal iş (uçtan uca)

Simetri sayesinde downstream'in tamamı hazır; sadece "başlık → skor → cache" halkasını ekleriz.

1. **FinBERT'i canlandır (bir anahtar).** En ucuz yol: `HF_API_TOKEN=<ücretsiz-token>` `.env`'e
   ekle. Böylece `score_texts` HF Inference API katmanına geçer — **torch/transformers kurmadan**.
   (Alternatif: yerel `transformers`+`torch` — daha doğru, offline; ama ~400MB model + ağır
   bağımlılık, Render'da footprint. Hot-path'te değil, scheduler job'ında çalışacağı için gecikme
   tolere edilebilir ama bağımlılık yükü gerçek. **İlk turda HF API yeterli.**)
2. **Ham başlık kaynağı ekle (ücretsiz).** `yfinance` `Ticker.news` semboller için başlık verir.
   `scanner/sentiment.py` desenini birebir taklit eden küçük bir `refresh_finbert_sentiment_cache(symbols)`:
   her sembol → başlıkları çek → `finbert_provider.score_texts(titles)` → aynı `data/sentiment_cache.json`
   formatına yaz (0..1, 0.5=nötr). Hot-path'e **hiç** dokunma; sadece cache oku.
3. **Kaynak seçimi bayrağı.** `FINPILOT_SENTIMENT_SOURCE=finbert|eodhd` (varsayılan `eodhd`, geriye uyumlu).
   `finbert` seçiliyse scheduler EODHD refresh yerine FinBERT refresh çağırır. Downstream değişmez —
   `compute_sentiment_factor` yine aynı cache'i okur.
4. **Scheduler'a bağla.** `core/scheduler.py:1342` çengeli zaten var; sadece kaynağa göre hangi
   refresh'in çağrılacağını dallandır.
5. **Aç ve gözle.** `FINPILOT_ENABLE_SENTIMENT=1` + `FINPILOT_SENTIMENT_SOURCE=finbert`.

**Dokunulan dosya sayısı:** ~2 yeni fonksiyon + scheduler'da 1 dal. Skorlayıcı/evaluate/cache-okuma **hiç** değişmez.

---

## 5. Maliyet & bağımlılık

| Yol | Bağımlılık | Maliyet | Doğruluk |
|---|---|---|---|
| HF Inference API | yok (sadece `requests`, zaten var) | ücretsiz kota / düşük | tam FinBERT |
| Yerel transformers | `torch`+`transformers` (~ yüzlerce MB) | RAM/disk footprint | tam FinBERT, offline |
| Keyword (bugünkü) | yok | 0 | düşük — FinBERT değil |
| EODHD (mevcut) | `requests` | **paralı API** | EODHD'nin kendi skoru |

Başlık kaynağı `yfinance` zaten repo'da → **ek maliyet yok**. FinBERT'e geçmek paralı EODHD'yi
opsiyonel yapar (maliyet **düşürür**).

---

## 6. Riskler ve zorunlu doğrulama kapısı

- **Fayda kanıtlanmadı.** `scanner/sentiment.py` docstring'i açıkça uyarıyor: *"Prove it helps via
  the weekly Edge Report (bucket by sentiment) BEFORE trusting it in live decisions."* Sentiment
  ağırlığı küçük (±0.5·ağırlık); precision'ı artırıp artırmadığı **A/B ile ölçülmeli**. Bu bir
  fizibilite, garanti değil.
- **Başlık kalitesi/kapsama.** `yfinance` haberi ABD tickerlarında iyi, her sembolde değil. Eksik →
  0.5 nötr (skora etki yok) — güvenli ama seyrek.
- **HF API gecikme/kota.** Scheduler job'ında olduğu için hot-path'i etkilemez; yine de kota aşımında
  zincir keyword'e düşer (sessiz degradasyon — `active_provider()` ile loglanmalı).
- **"Kurulu görünüp sessiz bozuk" tuzağı.** Bugünkü durumun ta kendisi bu (FinBERT kodlu ama hep
  keyword). Açtıktan sonra `active_provider()` değerini logla/kanıtla — gerçekten `finbert-hf-api`
  mı, yoksa yine keyword mü?

**Kapı:** Aç → 2–4 hafta gölge modda çalıştır → haftalık Edge Report'ta sentiment'e göre bucket'la →
precision farkı anlamlıysa canlı skora ağırlık ver. Aksi halde kapat/ağırlığı 0'da tut.

---

## 7. Öneri

**Evet, yapılabilir ve ucuz — ama bu haftanın işi değil.** Gerçek darboğaz hâlâ traction + yasal +
lansman (KOVA C). FinBERT bir *özellik iyileştirmesi ve hibe anlatısı*, sinyal kalitesinin
kanıtlanmamış bir katkısı.

Sıralama önerisi:
1. **Şimdi değil:** KOVA C bitene kadar bekle.
2. **Ucuz ilk adım (hazır olunca):** `HF_API_TOKEN` ekle → FinBERT'i uyandır → `active_provider()`
   ile gerçekten çalıştığını kanıtla (kod değişikliği sıfır, sadece env).
3. **Sonra:** Seçenek A'nın `yfinance`+FinBERT refresh'ini yaz, gölge modda aç, Edge Report'la doğrula.
4. **Karar:** kanıt olumluysa canlı skora al; değilse dürüstçe kapat.

Grant değeri: "açık, doğrulanmış finansal NLP modelini (FinBERT) kamu başlıklarına uyguluyor ve
kendi Edge Report'umuzla doğrulamadan hiçbir sinyale sokmuyoruz" — animasyon kütüphanelerinden
çok daha güçlü bir güvenilir-AI hikâyesi.

---
_Not: Bu belge yalnız analiz/plandır (Eskalasyon A). Kod değişikliği yapılmadı. Uygulama onayında
Seçenek A adım adım koda dökülür._
