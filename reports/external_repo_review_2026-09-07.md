# Dış Repo İncelemesi — FinPilot Entegrasyon Değerlendirmesi

Tarih: 2026-09-07
Level: A (araştırma; hiçbir kod/config değiştirilmedi)
Kapsam: 11 GitHub reposu, FinPilot'a (scanner + attention-map + araştırma disiplini + yayın zinciri) uygunluk
Önceki benzer çalışma: `reports/external_finance_resources_review_2026-08-12.md` (finans-ağırlıklı set; bu set ajan-altyapı ağırlıklı)

---

## Özet karar tablosu

| Repo | Ne? | FinPilot'a uygunluk | Otonom-tamamlama katkısı | Lisans | Karar |
|---|---|---|---|---|---|
| Gitlawb/openclaude | Açık-kaynak coding-agent CLI (Claude Code türevi, çok-sağlayıcılı) | Düşük-orta (bizim yığınımız Python, o TypeScript/Bun) | Düşük — bizim zaten çalışan ajan altyapımız var | Açık kaynak | **HOLD** |
| THU-MAIC/OpenMAIC | Çok-ajanlı interaktif sınıf platformu (AI öğretmen) | Çok düşük (eğitim domain'i, finans değil) | Yok | MIT (AGPL'den geçiş) | **STOP** |
| google-research/timesfm | Google zaman-serisi temel modeli (zero-shot tahmin) | **Yüksek potansiyel ama KANIT YOK** | Orta — ama yön tahmini 8 yoldan kapandı | Apache-2.0 | **BLOCKED (kanıt kapısı)** |
| affaan-m/ECC | "Everything Claude Code" — 47 ajan, 181 skill, harness optimizasyonu | Orta (metodoloji/skill disiplini) | Düşük — içerik kütüphanesi, motor değil | MIT | **HOLD (referans)** |
| DietrichGebert/ponytail | "Tembel kıdemli geliştirici" skill — minimal kod, YAGNI, stdlib-önce | **Yüksek (metodoloji uyumu)** | Orta — kod-üretim disiplinimizi güçlendirir | MIT | **CONFIRMATORY_CANDIDATE (metodoloji)** |
| advaitpaliwal/feynman | Açık-kaynak AI araştırma ajanı (paper rank, /autoresearch, /audit) | **Yüksek (araştırma disiplini)** | Orta — araştırma pipeline'ımızı yapılandırır | MIT | **CONFIRMATORY_CANDIDATE (araştırma)** |
| Imbad0202/academic-research-skills | Akademik araştırma skill seti (deep-research, reviewer) | Orta (araştırma rigoritesi) | Düşük — akademik yazım, bizim konumuz değil | **CC BY-NC 4.0 (NONCOMMERCIAL)** | **STOP (lisans)** |
| mksglu/context-mode | MCP eklentisi — ham veriyi LLM context'inden uzak tutar (FTS5 + sandbox) | **Yüksek (altyapı)** | Orta — büyük scan export'larımızı context'e sokmadan sorgulamamızı sağlar | **Elastic License 2.0** | **CONFIRMATORY_CANDIDATE (altyapı)** |
| coreyhaines31/marketingskills | Pazarlama skill kütüphanesi (CRO, SEO, copywriting) | Düşük-orta (GTM/landing için) | Düşük — ürün değil, pazarlama | MIT | **HOLD (GTM aşaması)** |
| lightpanda-io/browser | Zig ile yazılmış başsız tarayıcı (AI ajanları için, CDP server) | Orta (otomasyon/test) | Düşük — web scraping testimiz var | **AGPL-3.0** | **HOLD (lisans kısıtı)** |
| ruvnet/ruflo | Claude-Flow enterprise ajan orkestrasyonu (swarm, hive-mind, SPARC) | Düşük (bizim 23 ajanımız var, o ayrı ekosistem) | Düşük — kendi orkestrasyonumuz var | MIT | **HOLD** |

---

## Detaylı değerlendirme

### 1. Gitlawb/openclaude — HOLD
**Ne:** Claude Code kod tabanından türetilmiş, çok-sağlayıcılı (OpenAI/Gemini/DeepSeek/Ollama/200+ model) açık-kaynak coding-agent CLI. TypeScript/Bun, Node ≥22.
**FinPilot'a katkısı:** Bizim yığınımız Python (FastAPI + scanner) — bu bir TypeScript CLI'si. Doğrudan entegrasyon yok. Ancak **ajan-tanım mimarisi** (`AgentTool`, `loadAgentsDir`, built-in `Explore`/`Plan` ajanları, `whenToUse` + `disallowedTools` kalıbı) bizim `agents/` klasörümüzle aynı fikirde — referans olarak değerli.
**Otonom-tamamlama:** YOK — bizim çalışan scanner+distribution zincirimiz var; bu bir IDE/CLI aracı, ürün değil.

### 2. THU-MAIC/OpenMAIC — STOP
**Ne:** LLM-destekli çok-ajanlı interaktif sınıf (AI öğretmen, slayt/quiz/PBL üretimi). Tsinghua. Next.js, LangGraph orkestrasyonu.
**FinPilot'a katkısı:** Eğitim domain'i. FinSense Akademi'ye benzer ama bizim zaten `academy/` + `web/public/academy_lessons.json` hattımız var ve onaylı içerik üretiyoruz. Örtüşme yok.
**Otonom-tamamlama:** Yok.

### 3. google-research/timesfm — BLOCKED (kanıt kapısı)
**Ne:** Google'ın zero-shot zaman-serisi temel modeli. TimesFM 2.5 (200M param, ~1,5 GB RAM CPU), quantile tahminleri, Apache-2.0.
**FinPilot'a katkısı (potansiyel):** Fiyat serileri için zero-shot tahmin. **AMA:** yön tahmini bizde **8 bağımsız yoldan kapandı** (Review Board 2026-09-03). TimesFM'i scanner'a sokmadan önce `full_universe_enriched_eod_only.csv` üzerinde pre-registered matched-control testi şart. Bu yapılmadan entegrasyon yok.
**Otonom-tamamlama:** Orta — ama ancak kanıt üretirse. Şu an **kanıt yok, hipotez var.** Karar: **BLOCKED — önce `data/backtest_out/` üzerinde EOD-only backtest, sonra Level B.**

### 4. affaan-m/ECC — HOLD (referans)
**Ne:** "Everything Claude Code" — 47 ajan, 181 skill, Anthropic Hackathon kazananı. MIT. Harness optimizasyonu, `harness-optimizer`, `intent-driven-development`, skill'ler.
**FinPilot'a katkısı:** Kod entegrasyonu değil; **metodoloji referansı.** Bizim `_instructions/00-core.md` + `AGENTS.md` disiplinimizle aynı felsefede (minimal değişiklik, tek otorite, decision-log). `intent-driven-development` skill'i (Acceptance Brief şablonu) bizim Level B/C kapı raporlarımıza benziyor.
**Otonom-tamamlama:** Düşük — içerik kütüphanesi, motor değil.

### 5. DietrichGebert/ponytail — CONFIRMATORY_CANDIDATE (metodoloji)
**Ne:** "Tembel kıdemli geliştirici" — YAGNI, stdlib-önce, minimal-kod skill'i. Ölçülmüş: **%54 daha az kod, %20 daha ucuz, %27 daha hızlı, %100 güvenli** (Haiku 4.5, n=4, gerçek repo). MIT. Benchmarks + adversarial safety tier var.
**FinPilot'a katkısı:** Kod-üretim disiplinimizle (CLAUDE.md "smallest safe modification", "no unnecessary abstractions") tam uyumlu. `ponytail-audit` (repo çapında over-engineering taraması) ve `ponytail-debt` (ertelenen kısayolları deftere toplama) bizim audit kültürümüze uyuyor. **Bizim `agents/` ajanlarımıza bir "ponytail" davranış katmanı olarak** eklenebilir.
**Otonom-tamamlama:** Orta — doğrudan bir özellik değil ama kod üreten ajanlarımızın kalite/maliyet dengesini iyileştirir.

### 6. advaitpaliwal/feynman — CONFIRMATORY_CANDIDATE (araştırma)
**Ne:** Açık-kaynak AI araştırma ajanı. `feynman rank` (paper ranking + citation graph), `/audit` (paper vs kod uyumsuzluğu), `/replicate` (replication planı), `/autoresearch` (sınırlı deney döngüsü), `/deepresearch`. MIT. Science-database konektörleri (OpenAlex, arXiv, PubMed).
**FinPilot'a katkısı:** **Araştırma disiplinimizle neredeyse birebir örtüşüyor.** Bizim `research/` klasörümüzdeki pre-registration + matched-control + OOS disiplinini Feynman'ın `/audit` ve `/replicate` kalıpları zaten kodlaştırmış. `feynman rank` ile dış literatürü (attention/anomaly detection makaleleri) yapılandırılmış tarayabiliriz. **FinPilot'un `research/` hattına bir "dış-kanıt tarayıcı" olarak** entegre edilebilir.
**Otonom-tamamlama:** Orta — araştırma throughput'umuzu artırır ama production kodunu kendisi yazmaz.

### 7. Imbad0202/academic-research-skills — STOP (lisans)
**Ne:** Akademik araştırma skill seti (deep-research 8 mod, academic-paper 11 mod, reviewer). Çok disiplinli, "human-in-the-loop, not full automation" felsefesi.
**Sorun:** **CC BY-NC 4.0 (NONCOMMERCIAL)** — ticari kullanım yasak. FinPilot ticari bir ürün olma yolunda (grant, yatırımcı, potansiyel SaaS). Bu lisansla **entegre edemeyiz.**
**Karar:** STOP. Fikir olarak beğendiysek kendi metodolojimizi (zaten var olan pre-registration disiplinimizi) güçlendiririz, kodu/skill'i almayız.

### 8. mksglu/context-mode — CONFIRMATORY_CANDIDATE (altyapı)
**Ne:** MCP eklentisi. Ham veriyi (dosya içerikleri, grep çıktıları, API yanıtları) LLM context'inden **uzak tutar**: sandbox'ta çalıştırır, yalnızca stdout'u context'e sokar, gerisini yerel SQLite FTS5'e indeksler. "Think in Code" paradigması. 17 adaptör (Claude Code, Cursor, Copilot, Codex...). Elastic License 2.0.
**FinPilot'a katkısı:** **En pratik altyapı katkısı.** Bizim büyük scan export'larımız (7 MB JSON, 1.801 satır) ve backtest CSV'lerimiz (100K satır) context'i şişiriyor. context-mode ile "scan export'u context'e sokmadan sorgula" mümkün olur — örn. "2026-09-07 export'unda gap_pct>3 olan sembolleri say" sorusunu ham veriyi yüklemeden yanıtlarız.
**Lisans uyarısı:** ELv2 — kullanabilirsin, fork'layabilirsin ama **hosted/managed servis olarak sunamazsın.** FinPilot'u SaaS yaparsak bu bir kısıt olur — ama şu an lokal/dev kullanımı sorunsuz.
**Otonom-tamamlama:** Orta — büyük veri üzerinde ajan verimliliğini artırır.

### 9. coreyhaines31/marketingskills — HOLD (GTM aşaması)
**Ne:** Pazarlama skill kütüphanesi. CRO, SEO, copywriting, launch, pricing, churn-prevention. MIT. `product-marketing` skill'i diğer tüm skill'lerin okuduğu temel bağlam dosyası.
**FinPilot'a katkısı:** Kod değil, **GTM (go-to-market) aşamasında** değerli. `launch` ve `pricing` skill'leri FinPilot lansmanına hazırlanırken kullanılabilir. Şu an erken.
**Otonom-tamamlama:** Düşük — ürün değil, pazarlama.

### 10. lightpanda-io/browser — HOLD (lisans kısıtı)
**Ne:** Zig ile sıfırdan yazılmış başsız tarayıcı (Chromium/WebKit değil). CDP server, Puppeteer uyumlu, `--obey-robots`, proxy, network interception. AI ajanları için optimize.
**FinPilot'a katkısı:** Web scraping testimiz (FinSense/landing) için hafif bir alternatif. Ama mevcut test altyapımız çalışıyor.
**Sorun:** **AGPL-3.0** — ağ üzerinden sunulan servislerde kaynak açma zorunluluğu. FinPilot'u web üzerinden sunarsak bu bir yükümlülük.
**Karar:** HOLD — mevcut test altyapısı yeterli; AGPL yükümlülüğü gereksiz.

### 11. ruvnet/ruflo — HOLD
**Ne:** Claude-Flow enterprise ajan orkestrasyonu. 74+ ajan, swarm/hive-mind/SPARC, queen-coordinator, byzantine consensus. MIT.
**FinPilot'a katkısı:** Bizim zaten 23 ajanlık çalışan bir orkestrasyonumuz var (`agents/`). ruflo ayrı bir ekosistem (kendi MCP araçları, kendi swarm protokolü). Geçiş maliyeti yüksek, marjinal fayda düşük.
**Otonom-tamamlama:** Düşük — kendi orkestrasyonumuz çalışıyor.

---

## Hangileri "otonom olarak projeyi bitirme potansiyeli" yaratır?

**Dürüst cevap: hiçbiri tek başına.** Ama üçü birlikte anlamlı bir ivme yaratır:

| Kombinasyon | Ne sağlar | Neden |
|---|---|---|
| **feynman** (araştırma) + **ponytail** (kod disiplini) + **context-mode** (veri verimliliği) | Araştırma → doğrulama → minimal-kod döngüsünü hızlandırır | feynman dış kanıtı tarar, ponytail minimal uygulamayı zorlar, context-mode büyük veriyi yönetilebilir tutar |

Bu üçlü "projeyi kendiliğinden bitirmez" — ama **her birinin eksikliği hissedilen bir boşluğu doldurur:**
- feynman → dış literatürü yapılandırılmış tarama (şu an manuel)
- ponytail → ajan kod üretiminde şişkinliği önleme (benchmark kanıtlı)
- context-mode → 7 MB'lık scan export'ları context'i şişirmeden sorgulama (pratik)

**TimesFM** ayrı bir kategori: potansiyeli en yüksek ama kanıt yükü de en ağır. Yön tahmini 8 yoldan kapandı; TimesFM'i entegre etmeden önce EOD-only dataset'te pre-registered backtest şart. Bu bir "entegrasyon" değil, bir "doğrulama projesi".

## Governance notu

- Hiçbir production/scanner/score/publish davranışı değiştirilmedi.
- Hiçbir bağımlılık eklenmedi, hiçbir flag değiştirilmedi.
- Lisanssız veya lisanssız-uyumsuz (CC BY-NC, AGPL) repolar için entegrasyon **yapılmayacak** olarak işaretlendi.
- CONFIRMATORY_CANDIDATE olarak işaretlenenler (ponytail, feynman, context-mode) için bir sonraki adım Level B: küçük bir pilot entegrasyon + ölçüm.
