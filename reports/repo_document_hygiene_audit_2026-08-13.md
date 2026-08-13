# FinPilot / FinSense Repository and Documentation Hygiene Audit

**Tarih:** 2026-08-13
**Kapsam:** `C:\Users\meric\Borsa` ve kardeş `C:\Users\meric\Finsense` depoları
**Mod:** Salt-okunur denetim ve öneri
**Layer:** Governance / Engineering / Content / Research
**Level:** A (audit ve öneri); önerilen taşıma/yeniden yapılandırma işlemleri Level B; silme veya geri dönüşsüz işlem Level C
**Durum:** Taslak; hiçbir dosya taşınmadı, silinmedi veya yeniden adlandırılmadı.

## 1. Yönetici özeti

Denetim, iki ayrı sorunu birbirinden ayırmaktadır:

1. **Authority belirsizliği:** `docs/INDEX.md` insan-okunur tabloda Akademi kaynağını Finsense `academy/` olarak gösteriyor; aynı dosyanın makine-okunur manifestinde ise `authority_path: "academy"` yazıyor ve yalnız `web/public/academy_lessons.json` için uygulanıyor. Bu, hangi `academy/` klasörünün içerik otoritesi olduğunu makine tarafından açıkça söylemiyor.
2. **Kod ve doküman sprawl'ı:** Borsa kökünde 81 Python ve 30 Markdown dosyası var. Root Python yüzeyi ağırlıkla araştırma/backtest laboratuvarlarından oluşuyor; bu dosyaların tümünü üretim kodu veya ölü kod saymak için kanıt yok. Finsense daha küçük ve bağımsız: hariç tutulan yerel ortam/cache dizinleri sonrası 83 dosya, 33 Python ve 37 Markdown dosyası ölçüldü.

En güvenli öneri, lansman sırasında taşıma yapmamak; önce authority kararını ve dosya sınıflandırmasını onaylamak; ardından yalnız kanıtlanmış araştırma ve tarihsel dokümanları `git mv` ile, import/path/test/CI kanıtı eşliğinde taşımaktır.

## 2. Ölçülen envanter

### 2.1 Borsa

| Ölçüm | Sonuç | Not |
|---|---:|---|
| Kök Python dosyası | 81 | Büyük bölümü backtest/research/test laboratuvarı |
| Kök Markdown dosyası | 30 | Plan, audit, runbook ve durum dokümanları karışık |
| Kök diğer dosyalar | 42 | Veri/konfigürasyon/çıktı dahil |
| Git ile izlenen dosya | 2.645 | `.git` dışı, tracked yüzey |
| Kök deney/research adayı | 37 | İsim desenine dayalı ön sınıflandırma; “ölü” kanıtı değildir |
| Hariç tutulan yerel ağaçla toplam dosya | 43.286 | Cache, dependency, veri ve build çıktıları nedeniyle mimari ölçü olarak kullanılmamalı |

### 2.2 Finsense

`.git`, `.venv`, `__pycache__`, cache ve benzeri yerel ortam dizinleri hariç:

| Ölçüm | Sonuç |
|---|---:|
| Toplam dosya | 83 |
| Python | 33 |
| Markdown | 37 |
| Kök dosya | 18 |
| Kök klasör | 6 |
| Academy modülü | 18 Python dosyası |
| Agent modülü | 6 |
| RAG modülü | 5 |
| Root entrypoint | `app.py`, `run.py` |

Bu sayımlar dosya sistemi snapshot'ıdır; çalışma zamanı kullanımını tek başına kanıtlamaz.

## 3. Academy iki-repo sınırı

### 3.1 Kanıtlanmış akış

| Katman | Yol | Kanıtlanan rol | Durum |
|---|---|---|---|
| Finsense üretici | `C:\Users\meric\Finsense\academy/` | Domain, agent, RAG, SQLite lesson üretimi ve standalone FastAPI/CLI | **Üretici** |
| Finsense export | `Finsense/academy/export_lessons.py` | SQLite derslerini HTML veya JSON'a çeviriyor; JSON varsayılanı `published` | **Export köprüsü** |
| Borsa statik türev | `web/public/academy_lessons.json` | Web `/academy` sayfasının okuduğu yayın çıktısı | **Türev** |
| Borsa internal runtime | `Borsa/academy/` | `api/routers/academy.py` ve scheduler tarafından import edilen yerel Academy runtime'ı | **Runtime köprü/yerel servis** |
| Borsa arşiv kopyası | `archive/FinanceAcademy/academy/` | Aynı adlandırma ailesinin tarihsel kopyası; mevcut kullanım kanıtı bulunmadı | **Belirsiz/tarihsel aday** |

Finsense README'si servisin standalone olduğunu ve FinPilot'a sert bağımlılığı olmadığını söylüyor. Finsense `run.py` gerçek üretim ve servis giriş noktalarını tanımlıyor; `app.py` `academy.api` router'ını FastAPI'ye bağlıyor. Borsa tarafında `api/main.py` scheduler ve router wiring'i yapıyor; `api/routers/academy.py` doğrudan `academy.orchestrator` import ediyor. Dolayısıyla bugün tek bir Academy runtime'ı yok; içerik üreticisi ile Borsa iç runtime'ı ayrı kod ve veri sınırlarında yaşıyor.

### 3.2 Authority çatışması

`docs/INDEX.md` tablosu “Akademi ders içeriği” için `FinSense repo (academy/) → web/public/academy_lessons.json` diyor. Aynı dosyanın manifestinde `academy-content` kaydının `authority_path` alanı yalnızca `academy` ve `applies_to` alanı yalnızca `web/public/academy_lessons.json`. Bu değer Borsa `academy/` ile Finsense `academy/` arasında repo kimliği belirtmediği için makine-okunur authority haritası eksik/ambiguous'tır.

**Sonuç:** Bu audit, Borsa `academy/` klasörünü “legacy” ya da Finsense `academy/` klasörünü “tek runtime otoritesi” ilan etmiyor. Önce insan tarafından şu karar verilmelidir: Borsa `academy/` üretim runtime bridge olarak kalacak mı, yoksa Finsense standalone API/export katmanına mı geçilecek? Bu karar verilmeden taşıma yapılmamalıdır.

### 3.3 Duplicate ve orphan bulguları

- `Borsa/academy/seed_content.py` ile `Borsa/archive/FinanceAcademy/academy/seed_content.py` aynı isim ailesinde iki kopyadır. Arşiv kopyası için mevcut import/call kanıtı yok; yine de tarihçe kontrolü yapılmadan silinmemelidir.
- Finsense `academy/seed_content.py` ve `seed_content_en.py` çalışma akışında farklı olası başlangıç yollarına bağlıdır. `run.py seed` generator/orchestrator yolunu, `run.py seed-en` ise küratörlü İngilizce seed'i çağırır. Bu nedenle “ölü” yerine **aktif ama ayrı workflow** sınıfı kullanılmalıdır.
- Finsense `academy/export_lessons.py` Borsa web JSON çıktısını açıkça hedefleyebilen export aracıdır. Web sayfası aynı aracı üretici olarak dokümante eder. Export'un CI veya günlük operasyon kancasıyla otomatik çalıştığı kanıtlanmadı; bu, migration öncesi doğrulanacak bir bağımlılıktır.
- `web/public/academy_lessons.json` publish script'inde `demo_snapshot.json` ile birlikte izlenen çıktı olarak stage edilir. Bu dosya source değil, release artifact'idir.

## 4. Root-sprawl ve doküman sprawl'ı

### 4.1 Borsa root script sınıfları

| Sınıf | Örnekler | Önerilen hedef | Öncelik |
|---|---|---|---|
| Üretim/runtime entrypoint | `scanner.py`, `streamlit_app.py`, `telegram_bot_runner.py`, `telegram_alerts.py` | Kökte veya mevcut sahip modülünde kalmalı; launch öncesi taşınmamalı | P0/P1 koruma |
| Araştırma/backtest | `backtest_*.py`, `*_research_runner.py`, `score_lab_*.py`, `v2_*_runner.py` | `research/` altında tarih/konu bazlı paketleme | P2, Level B |
| One-off veri/diagnostic | `fetch_*.py`, `refresh_price_cache.py`, `*_audit.py`, `*_recheck.py` | `scripts/` veya `research/` sınıfı; her dosya için owner/README | P2 |
| Test adı taşıyan laboratuvar | `test3_exit.py`, `test4_horizon.py`, `test5_sector.py`, `test6_cluster.py` | `tests/` yalnız pytest sözleşmesine uyuyorsa; aksi halde `research/` | P2 |
| Entegrasyon/operasyon | `telegram_config.py`, `telegram_test.py`, `demo_standalone.py` | Operasyon sahipliği netleşene kadar yerinde | P1 |

Bu sınıflandırma ad desenine dayalıdır. Bir dosyanın taşınabilir olması için import graph, CI/Makefile çağrısı, cron/manuel runbook çağrısı, çıktı yolu ve git geçmişi ayrıca doğrulanmalıdır.

### 4.2 Doküman bulguları

- Kök dokümanları arasında tarihli planlar, auditler, GTM belgeleri, operasyon planları ve durum dosyaları aynı düzlemde duruyor.
- `docs/INDEX.md` bazı tarihsel dokümanların arşive taşınacağını zaten söylüyor; ancak bu kararın uygulanmış bir hareket planı ve her dosya için source→target listesi bu audit kapsamında mevcut değil.
- Eski web/Academy bulguları güncel durumla çelişebilir: 2026-07-29 auditlerinde `academy_lessons.json` tek ders olarak geçiyor; mevcut dosyanın güncel sayısı için bu auditte içerik tekrar sayılmadı. Bu nedenle eski sayılar “tarihsel kanıt” olarak etiketlenmeli, mevcut durum diye kullanılmamalıdır.
- `docs/strategy/FinSense_*` belgeleri, mevcut Finsense üretim fabrikası ile Borsa'daki Thinking Mirror runtime'ını ayırıyor; bu ayrım migration planının temel bağımlılığıdır.

## 5. P0-P3 risk matrisi

| Öncelik | Bulgu | Kanıt | Öneri | İşlem seviyesi |
|---|---|---|---|---|
| P0 | Academy authority map iki repo sınırını açıkça belirtmiyor | `docs/INDEX.md` tablo/manifest; Borsa API importları; Finsense standalone entrypoint | Authority kaydına repo-qualified source, export owner ve runtime bridge alanları için onaylı düzeltme önerisi hazırla | Level B |
| P0 | Export ve runtime davranışları iki ayrı Academy sistemine bölünmüş | `Finsense/academy/export_lessons.py` ve `Borsa/api/routers/academy.py` | Taşıma öncesi tek hedef mimariyi ve DB sahipliğini kararlaştır; üretim dosyalarını şimdi değiştirme | Level B/C etkili |
| P1 | Publish artifact ile source içerik ayrımı yeterince görünür değil | `scripts/publish_web.py`, `web/public/academy_lessons.json` | Artifact header/README ve export provenance belgesi öner; dosyanın kendisini değiştirme | Level A/B |
| P1 | Root research scriptleri production surface ile karışıyor | 81 root Python; 37 research adayı | Import/call inventory sonrası konu bazlı `research/` migration batch'i planla | Level B |
| P2 | Tarihli/legacy dokümanlar root ve docs altında dağınık | 30 root Markdown; `docs/INDEX.md` tarihsel listesi | Önce manifest ve supersession tablosu; sonra `git mv` | Level B |
| P2 | Cache/generated/temp dosya yoğunluğu ölçümü yanıltıyor | 43.286 hariç tutulmuş tree dosyası; `.mypy_cache`, `.next`, data vb. | Gitignore/cleanliness audit'i ayrı iş olarak yap; silme yapma | Level A/B |
| P3 | İsimlendirme standardı karışık | `test3_*`, `v2_*`, tarihli/datesiz kök scriptler | Yeni dosya standardı ve migration checklist'i belirle | Level A/B |

## 6. Hedef yapı önerisi

Bu bölüm hedef mimari önerisidir; uygulanmış yapı değildir.

```text
Borsa/
  api/                 # FinPilot API + reasoning/runtime adapters
  distribution/        # scan/publication contracts
  scanner/             # production scanner
  web/                 # frontend and release artifacts
  scripts/             # operational/reproducible commands
  research/            # dated experiments and research runners
  reports/             # findings, evidence, and audit outputs
  docs/                # authority-linked documentation
  archive/             # reversible historical material
  academy/             # only if explicitly retained as runtime bridge

Finsense/
  academy/             # content factory and standalone API owner
  data/                # local DB/corpus state, never source authority by itself
  tests/
  docs-or-root-plans/  # one approved documentation authority after decision
```

`Borsa/academy/` için iki kabul edilebilir hedef vardır ve seçim yapılmadan taşıma önerilmez:

- **Bridge retained:** Borsa `academy/` yalnız FinPilot iç API/runtime adapter'ı olarak kalır; ders üretimi ve içerik otoritesi Finsense'te kalır.
- **Bridge retired after cutover:** Borsa API'si Finsense servis/export sözleşmesine bağlanır; parity, auth, timeout, fallback ve rollback kanıtlandıktan sonra yerel kopya arşivlenir. Bu, production yüzeyi olduğu için Level B/C kapıları gerektirir.

## 7. Fazlı migration planı

### Faz 0 — lansman sırasında yalnız hijyen ve karar hazırlığı

1. `docs/INDEX.md` için repo-qualified Academy authority kararı taslağını onaya sun.
2. Borsa ve Finsense için dosya sınıflandırma manifesti üret: `active-runtime`, `source`, `export-artifact`, `research`, `historical`, `unknown`.
3. `git grep`/CI/Makefile/runbook/import graph ile her adayın çağrı kanıtını kaydet.
4. Export provenance kontrolü eklenmesini öner: source repo commit, generated-at, status filter ve schema bilgisi; bunu uygulama kararı ayrıca onaylanmalı.
5. `.env`, DB, cache, model ve log yüzeylerinde yalnız gitignore/status denetimi yap; secret değerlerini rapora alma.

**Faz 0'da yapılmayacaklar:** production scanner/distribution/execution/web dosyalarının taşınması, Academy runtime cutover'ı, dosya silme veya rename, generated artifact'in elle düzenlenmesi.

### Faz 1 — launch sonrası, onaylı migration batch'leri

Her batch için `git mv` varsayımı, import/path/docs güncellemesi, focused test, rollback commit'i ve owner/date kaydı zorunludur.

| Batch | Source → target | Güncellenecek yüzeyler | Risk | Rollback |
|---|---|---|---|---|
| R1 | Root research/backtest scriptleri → `research/<topic>/` | importlar, Makefile, CI, runbook ve output paths | Orta | Tek migration commit'ini geri al; `git mv` tersine çevir |
| R2 | Root historical plans/audits → `docs/archive/` veya mevcut authority'nin onayladığı hedef | `docs/INDEX.md`, cross-links, mkdocs nav | Orta | Link doğrulaması sonrası ters `git mv` |
| R3 | Borsa archive Academy copy → `archive/` altı tarihsel konumda tutma veya mevcut konumu koruma | import graph, git history, docs references | Düşük/Orta | Arşiv taşınmasını tersine çevir; silme yok |
| A1 | Finsense export contract → açık release/export boundary | Finsense exporter, Borsa artifact consumer, publish script, tests | Yüksek | Önceki artifact + önceki commit'e dön; runtime cutover yapma |
| A2 | Borsa Academy bridge → kararlaştırılmış adapter konumu | `api/main.py`, `api/routers/academy.py`, scheduler, deployment config | Yüksek | Feature flag/önceki adapter; production rollback runbook |

## 8. Ucuz doğrulama kontrolleri

Migration kararından önce şu kontroller raporlanmalıdır:

- `git grep` ile her root script için import/call/CI/runbook referansı.
- `python -m compileall` veya ilgili focused test ile taşınacak Python package sınırı.
- `web` TypeScript check ve static artifact schema check.
- Finsense export → Borsa artifact round-trip: published lesson count, schema, disclaimer ve source commit.
- API contract check: Borsa `/api/v1/academy/*` beklentileri ile Finsense standalone `/academy/*` yüzeylerinin eşleşmesi.
- DB ownership check: Finsense `academy.db` ile Borsa `data/academy.db` aynı veri kaynağı olarak varsayılmamalı.

## 9. Açık sorular ve belirsizlikler

1. `docs/INDEX.md` manifestindeki `authority_path: "academy"` hangi repo ve hangi çalışma zamanını ifade ediyor?
2. Borsa `academy/` uzun vadeli runtime bridge olarak tutulacak mı?
3. `export_lessons.py` CI/daily publish dışında harici bir çağırıcı tarafından çalıştırılıyor mu?
4. Root research scriptlerinin hangileri yeniden üretilebilir sonuç ve test sahibine sahip?
5. Finsense `data/academy.db` için mevcut bozulma yedeği yalnız tarihsel artifact mi, yoksa operasyonel kurtarma girdisi mi?

## 10. Decision-log taslağı — uygulanmadı

Aşağıdaki metin `docs/governance/decision-log.md` içine henüz eklenmemiştir. İnsan incelemesi ve özellikle Academy authority kararından sonra uygun kayda dönüştürülmelidir.

```text
[2026-08-13] - FinPilot/Finsense repo ve doküman hijyeni denetimi tamamlandı (Level A; migration pending)
Layer: Governance / Engineering / Content / Research
Level: A (salt-okunur audit ve öneri); taşıma/rename Level B, silme veya geri dönüşsüz işlem Level C
Context: Borsa kökünde 81 Python ve 30 Markdown; Finsense'te hariç tutulan yerel ortam/cache dizinleri sonrası 83 dosya, 33 Python ve 37 Markdown ölçüldü. Finsense academy üretici/export fabrikası, Borsa web/public/academy_lessons.json türev artifact'i, Borsa academy ise API tarafından import edilen ayrı runtime yüzeyi olarak kanıtlandı.
Finding: docs/INDEX.md insan tablosu Finsense repo -> web/public/academy_lessons.json zincirini gösterirken makine manifestindeki academy-content authority_path repo-qualified değildir. İki Academy runtime/DB sınırı nedeniyle authority ve ownership belirsizliği P0 olarak kaydedildi. Root research/doc sprawl'ı migration adayıdır ancak dosyalar “dead” ilan edilmedi.
Change: Bu auditte hiçbir dosya taşınmadı, silinmedi veya yeniden adlandırılmadı. Rapor ve fazlı migration önerisi hazırlandı. Faz 0'da authority kararı, dosya sınıflandırma manifesti ve call-graph kanıtı; Faz 1'de yalnız onaylı git mv batch'leri önerildi.
Impact: Üretim scanner, distribution, execution, broker, web runtime ve publish davranışı değiştirilmedi. Academy cutover kararı verilmedi. `web/public/academy_lessons.json` release artifact'i olarak kabul edildi; kaynak otoritesi kararı pending.
Status: pending - Meriç onayı bekliyor; bu kayıt migration veya authority değişikliği değildir.
Evidence: reports/repo_document_hygiene_audit_2026-08-13.md; docs/INDEX.md; Borsa/api/main.py; Borsa/api/routers/academy.py; Finsense/app.py; Finsense/run.py; Finsense/academy/export_lessons.py; scripts/publish_web.py.
```

## 11. Sonuç

Bu çalışma plan ve kanıt raporudur. En yüksek öncelik dosya taşımak değil, Academy authority'sini repo-qualified biçimde netleştirmektir. Bu karar alınmadan Borsa `academy/`, Finsense `academy/` veya `academy_lessons.json` üzerinde yapısal migration uygulanmamalıdır.
