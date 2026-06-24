# FinPilot — Yerel LLM + Canlı Veri + Haber + Sohbet Tabanlı Karar Asistanı

**Tarih:** 2026-06-12 · **Kaynaklar:** `llm/` (router, base, groq/claude/gemini provider), `agents/`, `core/scheduler.py`, mevcut audit raporları (09-agent, 10-scanner) + master prompt.

> **Uyarı:** Karar-destek sistemi tasarımıdır, yatırım tavsiyesi değildir. LLM geleceği bilmez; aşağıdaki mimari kararın *kalitesini ve açıklanabilirliğini* artırmayı hedefler, kâr garantisi vermez.

---

## 1. YÖNETİCİ ÖZETİ

**Mantıklı mı? Evet — ve düşünülenden çok daha yakın.** FinPilot'un "LLM beyni" zaten açık-ağırlıklı bir model: `llm/groq_provider.py` bugün **Groq üzerinde llama-3.3-70b** çalıştırıyor. Yani soru "açık model işe yarar mı?" değil (yarıyor, üretimde), soru **"nerede koşsun?"** — bulutta mı, yerelde mi. Mevcut `LLMProvider` soyut sınıfı (generate/stream/health) sayesinde yerel bir sağlayıcı (Ollama/llama.cpp) **temiz bir drop-in**: router'a tek provider eklenir, gerisi (failover, cache, headroom token sıkıştırma, langfuse izleme) bedavaya gelir.

**Asıl darboğaz LLM değil, etrafındaki üç eksik katman:**
1. **RAG / vektör hafıza YOK** — repoda hiçbir embedding/vektör DB yok. "Geçen ay benzeri ne yaptı?" sorusunun cevabı bugün üretilemez.
2. **Streaming context katmanı YOK** — scheduler polling-tabanlı (saatlik cron), event-bus/materialized-view yok. "Canlı veriyi izleyip kritik anda konuş" için olay omurgası gerekiyor (bu, `09-agent` raporundaki `signal_events` tablosuyla aynı ihtiyaç).
3. **Agent'lar kopuk** — sosyal/araştırma agent'ları üretim akışına bağlı değil (`09-agent-mimari-analizi.md`). Sohbet asistanı bu agent'ları "tool" olarak çağıracaksa önce onların yaşaması gerekir.

**Doğru kuruluş:** Eğitme — **bağla.** Base model (yerel) + FinPilot system prompt + canlı-veri araçları (tool calling) + RAG/memory + (mevcut) agent katmanı. Fine-tuning piyasa gibi sürekli değişen ortamda yanlış: ağırlıklar dünkü dünyayı dondurur.

**En doğru ilk ürün:** Trade ETMEYEN, **açıklayan ve seçici uyaran** yerel asistan: "bu hisse neden listede / neden WAIT / bu haber hangi watchlist'i etkiler". Execution'dan uzak, insan-döngüde, structured-output zorunlu.

**Tek cümle:** Model hazır; eksik olan onu besleyecek hafıza, olay omurgası ve "sus-konuş" disiplini — sırayla bunlar kurulmalı, fine-tuning değil.

---

## 2. YEREL LLM ENTEGRASYONU MANTIKLI MI? (Bölüm 1 cevapları)

1. **Mantıklı mı?** Evet. Mevcut Groq/llama-3.3-70b bağımlılığı zaten açık model; yerele almak gizlilik + sürekli maliyet + API-bağımsızlık kazandırır. Ama yerel ≠ ücretsiz (donanım + bakım).
2. **Sohbet edilebilir mi?** Evet — router `generate`/`stream` zaten var; eksik olan sohbet-orkestrasyonu + araç bağlama.
3. **Canlı veri/haber/scanner/short/options/earnings ile çalışabilir mi?** Kısmen bugün, tam olarak streaming-context + tool katmanı kurulunca. LLM bu verileri *doğrudan* okumamalı; özetlenmiş/materialized bir katmandan **araçlarla** çekmeli (Bölüm 5).
4. **Eğitmek mi, bağlamak mı?** Bağlamak (RAG + tool + memory). (Bölüm 4.)
5. **Yerelde mümkün mü?** Evet, donanıma bağlı (Bölüm 5).
6. **Sohbet-tabanlı seçici uyarı kurulabilir mi?** Evet — olay-tetiklemeli + "sessiz kalma" disiplini ile (Bölüm 6).
7. **En doğru kullanım?** Hepsi, ama sırayla: önce **scanner-açıklayıcı + alert chat**, sonra research copilot/memory, en son risk/karar katmanı.

---

## 3. NE KAZANDIRIR / NE KAZANDIRMAZ

**Kazandırır:** Açıklanabilirlik (her sinyale "neden" — scanner reason alanını zenginleştirir); hız (tek ekrandan "bugün ne değişti"); bağlam birleştirme (fiyat+haber+scanner+geçmiş tek cevapta); seçici dikkat (gürültüden anlamlı uyarıyı ayırma); gizlilik (yerelde kullanıcı notları/trade geçmişi dışarı çıkmaz); kurumsal hafıza (RAG ile geçmiş vakalar).

**Kazandırmaz:** Alpha (LLM geleceği bilmez; `10-scanner` raporundaki edge sorununu çözmez — kötü veriyi sadece güzel anlatır). Doğruluk garantisi (halüsinasyon riski). Frontier-seviye reasoning (yerel 70B < bulut frontier). Veri kalitesi (yoksa LLM uyduramaz, uydurursa tehlikeli).

**Kritik çerçeve:** LLM **karar-kalitesi çarpanı**, alpha kaynağı değil. Edge scanner/veride; LLM o edge'i anlaşılır, hızlı ve güvenli kılar.

---

## 4. EĞİTMEK Mİ, BAĞLAMAK MI? (net karar: BAĞLA)

**Fine-tuning neden yanlış (bu durumda):** (1) Piyasa sürekli değişir; ağırlıklar eğitim-anının dünyasını dondurur, dün doğru bugün yanlış. (2) Pahalı + yavaş döngü; her yeni veri için yeniden eğitim. (3) Halüsinasyonu azaltmaz, "kendinden emin yanlış" üretir. (4) FinPilot'un asıl ihtiyacı *güncel veriye erişim*, *parametrik bilgi* değil.

**Bilgi türü → doğru yöntem:**
| Bilgi | Yöntem |
|---|---|
| Finansal kavramlar (RSI, PEAD nedir) | Base model zaten biliyor — hiçbir şey gerekmez |
| FinPilot iç mantığı (skor nasıl çalışır) | **System prompt** + RAG (iç doküman) |
| Geçmiş trade sonuçları / vakalar | **RAG / vektör DB** (signals_archive, outcomes) |
| Canlı fiyat/haber/intraday | **Tool calling** (anlık çekim) — asla eğitim |
| Tekrarlayan format/ton | Birkaç-örnek (few-shot) system prompt'ta |

**"Modeli eğitmek" vs "sistemi eğitmek":** Model sabit kalır; **sistem** öğrenir — yeni vakalar vektör DB'ye düşer, outcome'lar geri beslenir, kalibrasyon güncellenir. Öğrenme ağırlıklarda değil, *retrieval + memory + kalibrasyon* katmanında.

**Doğru yığın:** Base model (yerel inference) → FinPilot system prompt → canlı-veri araçları → memory/RAG → (mevcut) agent katmanı. (İleride niş bir görev için — örn. Türkçe finansal ton — küçük LoRA düşünülebilir, ama P2+ ve opsiyonel.)

---

## 5. YEREL ÇALIŞMA FİZİBİLİTESİ (romantikleştirmeden)

**Avantaj:** gizlilik (notlar/trade geçmişi dışarı çıkmaz), API-bağımsızlık, sürekli-açık agent için sabit maliyet, düşük iç-ağ latency. **Dezavantaj (dürüst):** donanım ön-maliyeti, küçük modelin reasoning sınırı, uzun-context limiti, model/güvenlik bakımı, frontier kalitesine her zaman ulaşamama.

**Donanım senaryoları (gerçekçi):**
| Donanım | Çalışan model | Kullanım | Not |
|---|---|---|---|
| 16GB VRAM (RTX 4060Ti/4070) | 7-8B (Llama-3.1-8B, Qwen2.5-7B) Q4 | Triage, haber özeti, sınıflandırma | Sohbet zayıf, reasoning sınırlı |
| 24GB VRAM (RTX 3090/4090) | 14-32B (Qwen2.5-32B) Q4 | Sohbet + yapılandırılmış reasoning | **Tatlı nokta** — tek-kullanıcı için yeterli |
| 48GB+ (2×3090 / A6000) | 70B (Llama-3.3-70B) Q4 | Bugünkü Groq kalitesi yerelde | Pahalı; tek kullanıcıya overkill |
| Apple Silicon (M3/M4 Max 64-128GB) | 32-70B (MLX/llama.cpp) | Sessiz, düşük güç | Throughput GPU'dan düşük ama tek-kullanıcıda yeter |

**Gecikme:** Sohbet-açıklama için 2-10 sn kabul edilebilir (gerçek-zaman trade değil). Triage/sınıflandırma <1 sn (küçük model). Uyarı üretimi olay-tetiklemeli, gecikme kritik değil.

**Çok-model mimarisi (önerilen):** Tek dev model yerine görev-bazlı: küçük-hızlı (triage/alert sınıflandırma) + orta (sohbet/açıklama) + opsiyonel vision (chart/PDF/filing okuma). Router zaten çok-provider'ı destekliyor.

**Altyapı:** **Ollama** (en basit başlangıç, OpenAI-uyumlu API, `localhost:11434`) → ölçekte **vLLM** (yüksek throughput, batch). `llm/base.py`'ye `OllamaProvider(LLMProvider)` eklemek ~yarım günlük iş; FastAPI katmanı (`api/`) zaten var.

---

## 6. CANLI VERİ + HABER + CHAT MİMARİSİ (Bölüm 5 cevapları)

1. **LLM canlı veriyi doğrudan okumamalı.** Önce **streaming-context katmanı** (materialized views + event tablosu); LLM oradan **araçla** çeker. Sebep: ham tick LLM context'ini boğar, maliyeti patlatır, odağı dağıtır.
2. **Neden event-bus/materialized-view:** Hesaplama bir kez yapılır (RVOL, rejim, gap), N sorgu aynı özeti okur; LLM her seferinde yeniden hesaplamaz. FinPilot'ta bu katman **henüz yok** — `09-agent` raporundaki `signal_events` tablosu tam bu omurganın çekirdeği.
3. **Her tikte değil, olay-tetiklemeli.** LLM pahalı; her fiyat tikinde çalıştırmak hem maliyet hem gürültü. Eşik aşımında (kırılım, gap, haber, rejim değişimi) tetiklenir.
4. **"Sessiz kalma" mantığı:** İyi asistan az konuşur. Olay → eşik kontrolü → "bu gerçekten anlamlı mı?" (önem skoru) → ancak geçerse LLM çağrılır + bildirim. Her şeye konuşan model güveni öldürür (alert fatigue).
5. **Sohbet etkileşimleri** ("bugün neden sessizsin", "hangi hisseler kritik eşikte", "bu BUY'ı açıkla", "neden artık WAIT") — hepsi tool-calling ile mümkün: asistan ilgili aracı çağırır, sonucu açıklar, **kullandığı veriyi gösterir** (özel kural).

**Mimari (mevcut + eklenecek):**
```
[Veri: Alpaca/yf, EDGAR, scanner çıktısı, watchlist, outcomes]  ← VAR
        ▼
[Streaming-context: signal_events + materialized views + alert-candidates]  ← EKSİK (P1)
        ▼
[Memory/RAG: vektör DB — geçmiş vakalar, trade outcome, şirket dosyaları, iç dokümanlar]  ← EKSİK (P1)
        ▼
[Yerel LLM: sohbet modeli + triage modeli (+vision ops.)]  ← Provider eklenecek (P0)
        ▼
[Tool katmanı: quote(), explain_signal(), get_news(), compare_historical(), get_regime(), check_alerts()]  ← EKSİK (P0/P1)
        ▼
[Agent katmanı: triage / news / risk / chat-orchestrator]  ← KISMEN VAR ama kopuk (09 raporu)
        ▼
[UX: chat penceresi, alert center, "neden bu uyarı?" paneli]  ← web/ genişletilir
```

---

## 7. ALARM / UYARI MOTORU (seçici, açıklanabilir)

**Türler:** PRICE (kırılım, hızlı düşüş, gap, halt, vol patlaması) · NEWS (earnings, SEC filing, FDA/M&A, analist revizyonu, dilution/shelf — `catalyst.py` zaten S-1 tespit ediyor) · STRUCTURED (scanner skoru yükseldi, meta-label güveni değişti, rejim setup'ı bozdu, squeeze aktive, akış+fiyat+haber hizalandı) · EXPLAINABLE (her alarm: neden önemli + hangi veri tetikledi + tarihsel benzeri + ne yapmalı [watch/review/no-trade/manuel]).

**Eşik & gürültü azaltma:** Eşikler outcome verisinden kalibre edilir (sabit değil); **iki-aşamalı:** önce ucuz kural-tabanlı filtre (LLM'siz) olay-adayı üretir, sonra yalnız geçenler için LLM açıklama yazar. Bu, hem maliyeti hem false-alert'i düşürür. Aynı sinyal tekrar tetiklenirse bastır (dedup).

**Kanal yönlendirme:** Kritik + aksiyon-gerektiren → Telegram/push (bot zaten var). Orta → app/chat. Düşük/bilgi → yalnız dashboard. **"No alert" bilinçli karar:** sistem "bugün anlamlı bir şey yok" diyebilmeli — sessizlik de bir çıktı.

---

## 8. SOHBET DENEYİMİ ÖRNEKLERİ (her cevap kullandığı veriyi gösterir)

- **Scanner açıklama:** "NVDA neden ilk sırada?" → `explain_signal()` çağırır → "Composite 71: çok-zaman-dilimi hizalı (15m/4h/1d EMA+), momentum z-score 2.1, hacim 3.2×. Risk: EMA20'den %18 uzak (orta overextension). [Kaynak: scan #4412, 14:30]"
- **Piyasa durumu:** "Bugün hangi rejimdeyiz?" → `get_regime_state()` → "Bull (SPY>EMA200), vol normal. Momentum setup'ları destekleniyor ama yüksek-skor baskı bandı aktif (>58 ×0.75)."
- **Şirket odaklı:** "NVDA'da son 48 saatte ne değişti?" → `get_news()` + `compare_historical()` → haber+fiyat+geçmiş earnings reaksiyonu birleşik özet.
- **Karar öncesi:** "Şu an alım mantıklı mı?" → tarafsız boğa/ayı senaryosu + "neden güvenmemelisin" (overextension, edge-decay etiketi) + "neden WAIT" gerekçesi. **Asla "al" emri vermez.**
- **İç sistem:** "Geçen ay en çok hata yaptığımız setup?" → RAG outcomes sorgusu → "Bear rejimde yüksek-skor sinyaller: 12 BUY, 4 kazanç. Ortak özellik: düşük likidite + gap-up." (Bu, sistemin kendi `signal_events`/outcomes'ından öğrenmesi.)

---

## 9. RİSKLER VE GUARDRAILS (dürüst sınırlar)

LLM geleceği bilmez; canlı veriyi okuması doğru trade anlamına gelmez; haberi yanlış yorumlayabilir; halüsinasyon riski var; gereksiz konuşabilir; çok bağlamda odak kaybeder; frontier'dan zayıf reasoning verir; **kötü veriyi güzel anlatır** (en sinsi risk).

**Guardrails:**
- **Structured output zorunlu:** açıklama serbest metin olabilir ama her iddia bir veri-alanına (signal_id, fiyat, haber kaynağı, timestamp) bağlı; "kaynaksız iddia" filtrelenir.
- **Tool-grounding:** LLM sayı uydurmaz — fiyat/skor/haber yalnız araç çıktısından; model "bilmiyorum/veri yok" diyebilmeli (proxy-uydurma yasak).
- **İnsan onayı:** her aksiyon-ima eden çıktıda. LLM **execution'a hiç bağlanmaz** — en fazla "watch/review" önerir.
- **Disclaimer:** her karar-destek çıktısında (`08-90-gun` ve regülatör perspektifi P8 ile tutarlı).
- **Maliyet/gürültü guardrail:** olay-tetiklemeli + iki-aşamalı filtre + dedup.

---

## 10. BEN OLSAM NE YAPARDIM

**P0 — İlk kuracağım:** Yerelde çalışan **"scanner açıklayıcı + seçici alert chat"** — trade etmeyen, açıklayan ve uyaran. `OllamaProvider`'ı router'a ekle, 3-4 read-only tool (`explain_signal`, `quote`, `get_regime`, `check_alerts`), structured output + disclaimer, web/'e chat penceresi. Mevcut scanner reason alanını LLM ile zenginleştir.

**P1 — Sonraki katman:** RAG/vektör DB (signals_archive + outcomes + iç dokümanlar) → "geçmiş vaka" sohbeti; streaming-context (`signal_events` + materialized views); seçici/sessiz alarm motoru (iki-aşamalı, kalibre eşik); haber+filings RAG.

**P2 — İleri:** Multi-agent orchestration (önce `09-agent` orphan sorununu çöz), vision (chart/PDF/filing okuma), cross-market reasoning, otomatik post-mortem/self-learning loop (Academy A8 simülatörüyle ortak altyapı).

**Neyi YAPMAZDIM:** LLM'i doğrudan execution'a bağlamak; canlı veriyi her tikte reasoning'e sokmak; explainability olmadan action üretmek; fine-tuning ile "kahin model" kovalamak; RAG/streaming katmanı kurmadan "her şeyi bilen asistan" vaat etmek.

---

## 11. AŞAMALI YOL HARİTASI

### P0 — Yerel açıklayıcı + chat iskeleti (1-2 hafta)
1. `OllamaProvider(LLMProvider)` → router'a ekle (failover/cache/headroom bedava gelir). Donanım: 24GB VRAM veya M-serisi öneri.
2. 3-4 read-only tool: `explain_signal(id)`, `quote(ticker)`, `get_regime_state()`, `check_alerts()`.
3. Structured output sözleşmesi + zorunlu disclaimer + tool-grounding guardrail.
4. `web/`'e chat penceresi + scanner kartında "neden?" açıklaması (LLM, reason alanını genişletir).

### P1 — Hafıza + olay omurgası + seçici alarm (3-5 hafta)
5. `signal_events` tablosu + materialized views (streaming-context; `09-agent` ile ortak).
6. Vektör DB (yerel: Chroma/Qdrant) — signals_archive, outcomes, iç dokümanlar → "geçmiş vaka" RAG.
7. İki-aşamalı seçici alarm motoru: kural-filtresi → LLM açıklama → kanal yönlendirme + dedup + "no alert" durumu.
8. Haber/filings RAG (`catalyst.py` cache'i + news feed).

### P2 — Çok-agent + vision + self-learning (5-10 hafta+)
9. Chat-orchestrator + triage/news/risk agent'ları tool olarak bağla (önce orphan sorunu — `09-agent`).
10. Vision model (chart/PDF/filing okuma) — opsiyonel, donanıma bağlı.
11. Otomatik post-mortem döngüsü: kapanan her sinyal → LLM "ne öğrendik" notu → vektör DB → kalibrasyon. (Academy simülatörü A8 ile ortak altyapı.)

**Bağımlılık notu:** P1'in streaming-context'i ve P2'nin agent-bağlama'sı, `09-agent-mimari-analizi.md`'deki `signal_events` omurgası ve orphan-agent düzeltmeleriyle **aynı işi** paylaşıyor — bu raporlar tek bir altyapı yatırımına işaret ediyor, ayrı ayrı değil.

**Tek cümle:** Model zaten elimizde (Groq'taki llama yerele taşınır); yapılacak iş onu besleyecek hafızayı (RAG), olay omurgasını (signal_events) ve "sus-konuş" disiplinini kurmak — fine-tuning değil, bağlama, açıklanabilirlik ve seçicilik.
