# FinPilot — Teknik Due Diligence & CTO Değerlendirmesi
### Bağımsız, övgüsüz teknik inceleme · 2026-08-02

**Kanıt tabanı ve güven düzeyi (dürüstlük notu).**
- ✅ Yüksek güven (doğrulandı): FinSense reposu (satır düzeyi denetim+düzeltme bu oturumda), FinPilot yapısı/dizinleri, git geçmişi (277 commit, 2025-12 → 2026-07), ürün/vizyon/governance dokümanları, ajan/dağıtım/execution envanteri, compliance ilkesi.
- ⚠️ Orta/düşük güven (çıkarım — kod satır düzeyinde okunmadı): scanner iç mantığı, api router'ları, web bileşenleri, execution motoru, DRL, gerçek test kapsamı, DB/altyapı seçimleri.
- Düşük güvenli bölümlerde puan **(geçici)** işaretlidir; sonda doğrulama listesi var.

**Genel özet (peşinen, sert):** Tek kişilik bir operasyon için mimari olgunluk ve governance disiplini **olağanüstü**; compliance-first kimlik gerçek bir varlık. Ama proje **kapsam olarak boğuluyor**: ~90 kök script, ~110 doküman, 23 ajan, iki repo, bitmemiş lansman (2/10). En büyük teknik borç kodda değil, **odakta**. Ağırlıklı genel puan: **6.1/10** (çekirdek güçlü, dağınıklık ve traction eksikliği düşürüyor).

---

## 1. Vision — 7/10
- **Mevcut:** İki-sistem netleşti — (A) özel/yerel otonom trading+karar beyni (kendin için), (B) dünyaya açık compliance-first finansal okuryazarlık + kendini geliştiren ajan platformu.
- **Güçlü:** Tutarlı; mevcut varlıklara oturuyor; özel/kamu ayrımı regülasyon riskini büyük ölçüde kaldırıyor. Trend uyumu yüksek (agentic AI + finansal okuryazarlık boşluğu).
- **Zayıf:** Tek kişiye göre çok büyük; "5 yılda tüm dünya" ile bugünkü kaynak arasında uçurum. Vizyon günlük enerjiyi lansmandan çekiyor.
- **Risk:** Kapsam genişlemesi (scope creep) — projenin ana hastalığı.
- **Öncelik:** Yüksek (yön), ama uygulama olarak DÜŞÜK öncelik: kuzey yıldızı yazılıp rafa kalkmalı.
- **Öneri:** Vizyonu belge olarak dondur; günlük kararları "bu lansmanı ilerletiyor mu?" filtresinden geçir.

## 2. Product — 6/10
- **Mevcut:** "Morning Ledger × Open Classroom" — her gün hem haber hem ders; karne (dürüst geçmiş performans) + eğitim; compliance-first (BUY/SELL yok, Grade dili).
- **Güçlü:** Gerçek problem (finansal okuryazarlık + güvenilir, abartısız içerik boşluğu). Farklılaştırıcı = **dürüst karne + eğitim + AI**; incumbent'ların kolay kopyalayamayacağı güven zemini. İlk kullanıcı = sen (doğru).
- **Zayıf:** "Neden bunu kullansın?" henüz kanıtlanmadı (0 gerçek kullanıcı/geri bildirim). Değer önerisi eğitim mi sinyal mi — hâlâ biraz bulanık.
- **Risk:** Çözüm arayan bir problem yerine, problem arayan bir çözüm olma riski.
- **Öncelik:** Yüksek — lansman = ilk gerçek kullanıcı testi.
- **Öneri:** Tek net vaatte netleş: "her sabah, dürüst karneli, öğreten bir bülten." Onu kanıtla.

## 3. Software Architecture — 5/10
- **Mevcut:** Domain'e göre modüler monolit (scanner, agents, core, distribution, execution, api, web). FastAPI + Next.js. Governance/otorite katmanı var.
- **Güçlü:** Domain ayrımı temiz; monolit bu aşama için DOĞRU seçim (microservice DEĞİL). Offline fabrika ↔ online servis ayrımı sağlam.
- **Zayıf:** **Kökte ~90 dağınık script** = mimarinin kanseri; net modül sınırları var ama etrafı çöple çevrili. İki repo (FinPilot/FinSense) arası sınır köprüyle muğlak.
- **Risk:** Yeni gelen (ya da 3 ay sonraki sen) nereden başlayacağını bulamaz.
- **Öncelik:** Orta-yüksek (lansman sonrası).
- **Öneri:** DDD/microservice GEREKMEZ. Gereken: kök scriptleri `experiments/` altına arşivle, `src/` disiplinine geç. Monolit'te kal.

## 4. Code Quality — (geçici) 5/10
- **Mevcut:** 66 test dosyası var; governance disiplini yüksek. Ama FinSense'te gerçek buglar buldum (bayat-dict, JSON parse, ölü kod ~52KB); kökte tekrarlı deney scriptleri.
- **Güçlü:** Test kültürü var; decision-log ile değişiklik izlenebilirliği iyi.
- **Zayıf (çıkarım):** Teknik borç yüksek görünüyor (ölü kod, kopya scriptler, "yourusername" placeholder'lı CI badge → CI muhtemelen gerçek değil). SOLID/Clean Arch uyumu doğrulanmadı.
- **Risk:** Bakım maliyeti sessizce artıyor.
- **Öncelik:** Orta.
- **Öneri:** ⚑ Kesin puan için scanner/api/execution'ı okumam gerek. Şimdilik: ölü kodu sil, CI'yı gerçekten çalışır yap, kök scriptleri arşivle.

## 5. AI Architecture — 6/10
- **Mevcut:** Takılabilir LLM (yerel/bulut/mock), RAG (FinSense), çok-ajan, MCP başlangıcı, hibrit niyet. DRL ayrı bir dünya (45 dosya).
- **Güçlü:** Sağlayıcı soyutlaması + yerel/bulut hibrit + RAG + atıf zorunluluğu — bu aşama için gerçekten iyi tasarım. Format-agnostik parser, keep-alive gibi doğru mühendislik kararları (FinSense'te doğruladım).
- **Zayıf:** **Memory / planning / reflection / evaluation zayıf.** FinSense'te eval döngüsü boştu (bu oturumda telemetri+revizyonu ekledim ama hâlâ ilkel). LLM-jüri "örnek puanı tekrarlıyor"du. Agent collaboration çoğunlukla sıralı, gerçek müzakere değil.
- **Risk:** "Kendi kendini geliştiren" iddiası, eval/ölçüm ayağı olmadan slogan kalır.
- **Öncelik:** Yüksek (B sistemi için).
- **Öneri:** Önce **eval harness** (objektif ölçüm) — kendini geliştirme onsuz mümkün değil.

## 6. Agent System — 5/10
- **Mevcut:** FinPilot'ta **23 ajan** (ceo, bull/bear_researcher, risk, analysis, backtest, strategy_optimizer, market/social_intelligence, advisory, alert, alpha_tracker, data_quality, feedback, performance_monitor, report, scanner, shortlist_enricher, combo_testing, ...). FinSense'te 6 ajan + orchestrator.
- **Güçlü:** Orchestrator + registry deseni tutarlı; roller tanımlı.
- **Zayıf:** **Bu aşama için çok fazla ajan.** ceo, social_intelligence, bull/bear_researcher gibi ajanlar PMF öncesi over-engineering kokuyor. Her ajan bakım + prompt + test yükü. Görev çakışması riski yüksek.
- **Risk:** Ajan çoğalması = kontrol edilemeyen karmaşıklık (senin bunaltının teknik yüzü).
- **Öncelik:** Orta-yüksek.
- **Öneri:** ⚠️ **Ajan sayısını kes.** Lansman için gereken çekirdek 4-5 ajan (scan → analiz → risk → rationale → publish). Gerisini "park". Ajan eklemek çözüm değil, çoğu zaman problem.

## 7. Scalability — (geçici) 4/10 (kamu) / 8/10 (özel)
- **Mevcut:** Tek makine + tek Next.js/FastAPI + SQLite/Postgres karışık.
- **10-100 kullanıcı:** sorunsuz. **1.000:** DB/bağlantı havuzu, LLM eşzamanlılık, canlı veri maliyeti zorlar. **10.000+:** mevcut mimari kırılır (tek servis, yerel LLM serving ölçeklenmez).
- **Kırılma noktası:** Kamu tarafı ~1.000 eşzamanlı aktif kullanıcıda; özel (tek kullanıcı) sistem hiç kırılmaz.
- **Risk:** "Tüm dünya" hedefiyle mevcut serving mimarisi arasında uçurum.
- **Öncelik:** DÜŞÜK şimdilik (10.000 kullanıcı problemi bugünkü problem değil).
- **Öneri:** Ölçeği erken çözme (premature). Kamu büyüyünce bulut serving + stateless API + managed DB. Yerel LLM = fabrika, bulut = serving.

## 8. Performance — (geçici) 5/10
- **Mevcut:** price_cache, Redis activity feed, yfinance fallback telemetrisi, scan hız optimizasyonu (2x). Darboğazlar: canlı veri çekimi, LLM üretim süresi (FinSense'te CPU'da timeout gördüm), vektör arama (FinSense'te SQLite kosinüs — O(n), ölçeklenmez).
- **Güçlü:** Cache + fallback + telemetri bilinci var.
- **Zayıf:** Kuyruk/streaming/background-job mimarisi olgun değil; vektör arama naif.
- **Öncelik:** Orta (lansman sonrası).
- **Öneri:** ⚑ Doğrulama gerek. Vektör arama ölçekte gerçek vektör DB'ye (pgvector/Qdrant) taşınmalı.

## 9. Security — (geçici) 4/10
- **Mevcut:** FinPilot'ta `auth/` var; governance'ta secrets disiplini (08-security). Ama FinSense API'sinde auth yoktu (kısmen ekledim). Prompt injection / RAG güvenliği sertleştirilmemiş.
- **Güçlü:** Secrets'ı dosyaya yazmama kültürü; `.finpilot` redaksiyon kuralları (bu oturum).
- **Zayıf:** LLM saldırı yüzeyi (prompt injection, RAG zehirleme) ele alınmamış; para-bitişik sistemde yetki modeli kritik. Authn/authz olgunluğu doğrulanmadı.
- **Risk:** Para + LLM = yüksek saldırı değeri.
- **Öncelik:** Yüksek (özellikle A sistemi gerçek paraya dokununca).
- **Öneri:** Prompt injection savunması, RAG kaynak güveni (trust_tier — dokümanda var), execution'da imzalı+onaylı komut zinciri.

## 10. DevOps — (geçici) 4/10
- **Mevcut:** Docker, docker-compose, render.yaml, alembic migrations, backup+bütünlük job'u, arşiv alarmı. `monitoring/` ve `reports/` dizinleri boş (py yok).
- **Güçlü:** Konteynerizasyon + migration + backup var; operasyon ritüeli dokümante.
- **Zayıf:** **Gerçek CI/CD şüpheli** (README badge placeholder); observability zayıf (metric/trace yok); rollback/DR prosedürü belirsiz.
- **Risk:** Tek kişi + zayıf observability = sessiz üretim arızası.
- **Öncelik:** Orta.
- **Öneri:** Gerçek CI (test+lint her push), basit observability (yapılandırılmış log + sağlık ucu), yazılı rollback.

## 11. Data Layer — (geçici) 5/10
- **Mevcut:** SQLite (FinSense) + muhtemel Postgres (alembic/migrations) + Redis (activity feed) + price_cache (dosya) + financial data (yfinance/Alpaca/EODHD/FRED). Dedike vektör DB YOK (FinSense'te SQLite-kosinüs).
- **Güçlü:** Katmanlar var; migration disiplini (alembic) iyi.
- **Zayıf:** Vektör DB yok; time-series için özel çözüm yok; SQLite ile Postgres karışımı tutarsız; veri sahipliği/yaşam döngüsü net değil.
- **Öncelik:** Orta.
- **Öneri:** Tek kanonik OLTP (Postgres) + pgvector (RAG) + Redis (cache/queue). SQLite yalnız yerel fabrika/tek-kullanıcı için kalsın.

## 12. FinTech — 8/10 (projenin en güçlü alanı)
- **Mevcut:** Compliance-first (BUY/SELL/hedef-fiyat yasak, Grade dili, her ekranda disclaimer), `audit_log` (append-only), karne/outcome tracking, `prepublish_gate` (yayın kalite kapısı), paper trading planı (Alpaca Labs), live trading insan kapısında.
- **Güçlü:** Bu, projenin **en olgun ve en savunulabilir** yanı. Explainability (rationale motoru), denetlenebilirlik ve dürüst outcome zinciri gerçek bir hendek. Regülasyonu ciddiye alan nadir bir tek-kişi projesi.
- **Zayıf:** Paper→live geçiş kriterleri henüz kanıtlanmadı; risk engine derinliği doğrulanmadı.
- **Risk:** Otonom işlem gerçek paraya erken geçerse hızlı kayıp. (Not: kendi paran için özel kullanım regülasyon dışı olabilir ama vergi/beyan sürer — hukuki teyit şart; ben avukat/danışman değilim.)
- **Öncelik:** Yüksek (A sistemi için).
- **Öneri:** Paper modda uzun karne → insan-onaylı live. Bunu ASLA erken otomatikleştirme.

## 13. User Experience — 6/10
- **Mevcut:** Morning Ledger tasarımı (gazete metaforu, serif, Grade mührü); landing + /demo canlı; dashboard V2 donuk.
- **Güçlü:** Güçlü, ayırt edici tasarım dili; metafor tutarlı.
- **Zayıf:** Onboarding/öğrenme eğrisi kanıtlanmadı; mobil test bekliyor; "ilk 5 dakika" deneyimi belirsiz.
- **Öncelik:** Orta-yüksek (lansman için).
- **Öneri:** İlk-kullanım akışını 3 gerçek insanla test et (checklist'te zaten var).

## 14. Business — 4/10
- **Mevcut:** Premium sayfa + free-to-paid funnel + GTM dokümanları var; gelir modeli tasarlanmış ama kanıtlanmamış (0 ödeyen).
- **Güçlü:** Düşük işletim maliyeti (yerel LLM), düşünülmüş funnel.
- **Zayıf:** Traction yok; fiyatlandırma/ödeme mekaniği test edilmemiş; birim ekonomi belirsiz.
- **Risk:** Ürün teknik olarak sağlam ama ticari olarak doğrulanmamış.
- **Öncelik:** Yüksek (lansmanın amacı bu).
- **Öneri:** Önce 10 beta + 15 geri bildirim (checklist), sonra ödeme.

## 15. Competition — 5/10
- **Mevcut/Rakipler:** Trade Republic/eToro (broker+sosyal), Finary/finansal takip, finansal okuryazarlık uygulamaları, pro tarafta Bloomberg/TradingView. AI tarafında finchat botları.
- **Avantaj:** Compliance-first eğitim + dürüst karne + AI ajan org kombinasyonu niş ama savunulabilir.
- **Zayıf:** Kalabalık pazar; dağıtım gücü yok; marka yok.
- **Öneri:** Yatay yarışma; dikey niş (dürüst karneli, öğreten, tavsiyesiz) tut. Benchmark: karne şeffaflığında kimse senin kadar ileri değil — orada lider ol.

## 16. Technical Debt — 4/10 (ciddi ve büyüyen)
- **Bugün çözülmezse büyüyecekler:** (1) kök ~90 script → arşivlenmezse her ay büyür; (2) ~110 doküman → bayatlayıp çelişki üretir; (3) 23 ajan → bakım borcu; (4) iki repo sınırı; (5) SQLite/Postgres karışımı; (6) ölü kod; (7) gerçek CI yokluğu.
- **Öncelik:** Yüksek (ama lansman sonrası tek blok halinde).
- **Öneri:** Lansman sonrası 1 haftalık "büyük temizlik": arşivle, sil, tek DB'ye geç, CI kur.

## 17. Future Readiness — 7/10
- **Mevcut:** Yerel+bulut hibrit, açık modeller (qwen/llama), agentic desen, MCP.
- **Güçlü:** 2028-2030 trendlerine (ucuzlayan yerel modeller, edge AI, agentic) iyi konumlu. Yerel-öncelik maliyet avantajı büyüyecek.
- **Zayıf:** Model bağımlılık soyutlaması var ama eval/gözlemlenebilirlik zayıf; hızlı model değişimine hazır değil.
- **Öneri:** Sağlayıcı soyutlamasını koru; eval harness ekle → model yükseltmelerini güvenle yut.

## 18. Startup Perspective
- **Yatırımcı:** "Tek kişi için etkileyici mühendislik ve compliance olgunluğu; ama traction yok, kapsam çok geniş, henüz yatırılabilir değil. Odaklan, 100 gerçek kullanıcı getir, sonra konuşalım."
- **CTO:** "Governance ve compliance harika; ama 23 ajan + 90 script = bakım bombası. Kes, sadeleştir, lansmanı bitir."
- **Senior Backend:** "Monolit doğru; DB'yi tekleştir, CI kur, kök scriptleri temizle."
- **Senior Frontend:** "Tasarım dili güçlü; onboarding ve mobil eksik."
- **AI Researcher:** "RAG+hibrit iyi; ama memory/reflection/eval ilkel — 'self-improving' henüz slogan."
- **FinTech CEO:** "Karne + compliance = gerçek hendek. Bunu ürünün merkezine koy, gerisini kes."

## 19. Roadmap (teknik)
- **30 gün:** Lansmanı bitir (10 günlük brif serisi). Ajanları çekirdek 4-5'e indir. Gerçek CI + ölü kod temizliği (küçük). Başka HİÇBİR yeni sistem yok.
- **90 gün:** İlk 10-25 kullanıcı + geri bildirim. Büyük temizlik (kök scriptler → experiments/, tek DB, tek repo disiplini). Eval harness v1.
- **6 ay:** Kişiselleştirme (öğrenen profil) + karne şeffaflık ürünü. Özel trading beyni PAPER modda uzun koşu + karne. Basit observability.
- **1 yıl:** Bulut serving (kamu ölçek), pgvector, çok-dil (EN kanonik). Premium doğrulama. A sistemi insan-onaylı sınırlı live (kendi paran).
- **3 yıl:** Kişiselleştirilmiş ajan platformu (B), regülasyon danışmanlığıyla danışmanlık katmanı, çok-ülke. Ekip.

## 20. Final CTO Report

**A. En güçlü 10 özellik:** 1) Compliance-first kimlik (Grade dili). 2) Karne/dürüst outcome zinciri. 3) Governance katmanı (AGENTS/decision-log/authority map) — tek kişi için olağanüstü. 4) Takılabilir LLM (yerel/bulut/mock). 5) RAG + atıf zorunluluğu. 6) Offline fabrika ↔ online servis ayrımı. 7) Morning Ledger tasarım dili. 8) Alpaca Labs (iç doğrulama, kullanıcıya kapalı). 9) `.finpilot` ortak-beyin/HITL (bu oturum). 10) Yerel-öncelik maliyet konumu.

**B. En kritik 10 risk:** 1) Kapsam genişlemesi (ana hastalık). 2) Lansman 2/10, enerji dış halkalara akıyor. 3) 23 ajan bakım bombası. 4) ~90 kök script + ~110 doküman borcu. 5) Eval/observability zayıf → "self-improving" slogan riski. 6) Otonom trading erken live → para kaybı. 7) Güvenlik (prompt injection/RAG/authz) olgun değil. 8) Gerçek CI yok. 9) Traction/ticari doğrulama yok. 10) Tek kişi = bus factor 1.

**C. En büyük fırsatlar:** Dürüst-karneli, tavsiyesiz, öğreten finansal okuryazarlık — kimsenin liderlik etmediği niş. Yerel-AI maliyet avantajı. Agentic dalganın erken oyuncusu.

**D. En büyük tehditler:** Kendi kapsamında boğulmak (dış tehditten önce). Incumbent'ların AI+eğitim eklemesi. Regülasyon (kamu danışmanlığa kayarsa). Tükenmişlik (tek kişi, çok cephe).

**E. Hemen yapılması gerekenler:** Lansmanı bitir. Ajanları kes. Yeni sistem AÇMA. Ölü kodu sil. Kuzey yıldızını yazıp rafa kaldır.

**F. Yapılmaması gerekenler:** ⛔ Şimdi web Control Center kurma. ⛔ Yeni ajan ekleme. ⛔ Otonom gerçek-para trading'i erken açma. ⛔ Kamuya tavsiye/danışmanlık sunma (regülasyon). ⛔ Mikroservise geçme. ⛔ Yeni kök script yazma. ⛔ FinSense'i lansmandan önce büyütme (kendi park kuralın).

**G. Ben CTO olsaydım ilk 6 ayda:** Ay 1: lansmanı bitir + ajanları sadeleştir + CI. Ay 2-3: 25 kullanıcı + geri bildirim + büyük temizlik + tek DB. Ay 4-6: kişiselleştirme + karne şeffaflık ürünü + eval harness + özel trading beyni paper karne. Tek kural: aynı anda tek cephe.

**H. Bu şirkete yatırım yapar mıydım?** Bugünkü haliyle **hayır** — traction ve odak yok, kapsam çok geniş, tek kişi. AMA: 90 günde 25 gerçek kullanıcı + dürüst karne + odaklanmış tek ürün gösterirse **evet, erken tohum** — çünkü compliance/karne hendeği ve mühendislik kalitesi nadir. Yatırım tezi ürün değil, **disiplin kanıtı**.

**I. Neye benziyor?** Genetiği: erken **Bloomberg** (dürüst veri/karne otoritesi) × **Duolingo** (öğreten, alışkanlık) × **QuantConnect/Numerai** (karne/backtest kültürü) × agentic bir **Palantir Foundry** iç-motoru. Ama bugünkü olgunluğu: tutkulu, aşırı-mühendislik yapan bir **solo founder MVP'si**.

**J. Gerçek potansiyel:** Yüksek ama koşullu. Dürüst-karneli finansal okuryazarlıkta Avrupa'da niş lider olabilir (gerçekçi 3-5 yıl hedefi). "Tüm dünya + kişisel danışman" ise ancak ekip+sermaye+regülasyon+odak dörtlüsü gelirse. Potansiyeli sınırlayan şey teknoloji değil, **odak ve tek-kişi kapasitesi**. Tek cümle: **çekirdek dünya standartında, çevre dağınık — kazanmak için küçülmek gerekiyor.**

---
_Puan doğrulama için okumam gerekenler (⚑): scanner/score_engine, api routers, execution/gateway+worker, web bileşenleri, gerçek test kapsamı, DB/altyapı (Postgres/Redis/pgvector) konfigürasyonu. Bunlar okununca §4,7,8,9,10,11 puanları kesinleşir._
