# Bölüm D — Yatay Sorun Analizi (Sistem Geneli)

## D.1 — İKİ BAŞLI VE REDUNDANT YAPILAR

| Duplicate alan | Kaynak 1 | Kaynak 2 | Çakışma türü | Risk | Karar |
|---|---|---|---|---|---|
| **Academy sistemi** | `academy/` (entegre, 6 agent) | `FinanceAcademy/` (standalone) | Aynı sistemin iki evrimi; models.py'ler farklılaşmış | Yüksek — değişiklikler kaybolur, DB şeması çatallanır | academy/ kanonik; FinanceAcademy → archive/ (bu hafta) |
| Academy DB | `data/academy.db` | `data/academy_v2.db` | İkisi de boş, V2 ayrımı belgesiz | Orta | Tek DB: academy.db; v2'yi sil |
| Scheduler | `core/scheduler.py` | `academy/scheduler.py` | İki ayrı zamanlayıcı | Orta — academy job'ları kimse çalıştırmaz | Academy job'larını core scheduler'a kaydet |
| Skor API | `scanner/finpilot_score.py` | `score_engine.py` + `risk_engine.py` (shim) | Re-export shim'i kafa karıştırıyor | Düşük (artık tek kanonik var) | 90 günde shim'leri sil |
| DEPENDENCIES.md | root (01-26) | docs/ (04-07) | İçerik drift'i | Düşük | docs/ kanonik, root'takini sil |
| Roadmap | ROADMAP_Q1_2025, CRITICAL_ROADMAP, DRL_IMPROVEMENT_ROADMAP, INFRASTRUCTURE_ACCELERATION_ROADMAP, TRIO_IMPROVEMENT_ROADMAP, UI_UX_APPLE_STYLE_ROADMAP | — | 6 roadmap, hiçbiri otoriter | Orta — yön belirsizliği | Tek ROADMAP.md; eskiler archive |
| Audit raporu | docs/FULL_AUDIT_REPORT.md, reports/audit_2026.md, data/profitcore_audit.json, docs/audit-2026-06-12/ (bu) | — | Otoriter zincir belirsiz | Orta | Bu klasör + FULL_AUDIT; INDEX.md ile zincirle |
| Rapor çıktı yeri | `data/*.md` raporlar | `reports/` | Script'ler iki yere yazıyor | Düşük | Tek hedef: reports/ |
| Compose servisleri | `api` | `finpilot` | Rol ayrımı belirsiz (legacy ad) | Orta | finpilot servisini kaldır/birleştir |
| Sanal ortam | `.venv` | `.venv-contract` | Belgelenmemiş ikilik | Düşük | README'ye not |
| Windows başlatıcı | `start.sh` | `finpilot.bat` | Drift (bat 2 ay eski) | Düşük | bat → wsl sarmalayıcı |

## D.2 — KOPUK VE BAĞLANTISIZ PARÇALAR

- **academy/ tamamı** — kod var, çağıran ürün yüzeyi yok (router yok, UI yok, scheduler bağlı değil). En büyük "hazır ama entegre edilmemiş" varlık.
- **monitoring/** (Prometheus/Grafana/alerts.yml) — compose'ta tanımlı, hiçbir dev/prod akışında ayakta değil. Grafana profitcore paneli (Mayıs) kullanılmıyor.
- **broker/** — tek dosyalık iskelet; Alpaca entegrasyonu scanner/data_fetcher içinde yaşıyor, broker soyutlaması bypass edilmiş.
- **grant_documents/** (32 dosya) — Mayıs başından beri dormant; hibe yolu fiilen askıda.
- **archive/public_website_for_extraction** — "extraction" hiç yapılmadı; landing içeriği burada kilitli.
- **research/ pipeline çıktısı** — scheduler job'u var, çıktının tüketicisi belirsiz.
- **mkdocs (mkdocs.yml + site/)** — build Mayıs başından beri yenilenmemiş; docs/ ile site/ drift halinde.
- **CI badge'leri** — README'de "yourusername" placeholder; CI'ın gerçekten koştuğu doğrulanamıyor.
- **tests/test_signals.py + tests/scanner_rollout/** — kalıcı ignore'da: yazılmış ama çalıştırılmayan test varlığı.

## D.3 — STARTUP VE PERFORMANS

- Scanner tarafı yeni optimize edildi (3.7x, chunked concurrency, smart TTL, Alpaca bulk) — **bu alandaki eski bulgular kapanmış durumda.** İzleme notu: optimizasyon commit'lerini 3 fix commit'i izledi; stabilite 1-2 hafta gözlenmeli.
- start.sh içinde `sleep 2` + kill zinciri — küçük ama gereksiz; sağlık kontrolü polling'e çevrilebilir (P3).
- next dev cold start (~20sn) — dev konforu; `next dev --turbo` denenebilir (P3).
- yfinance fallback yolu hâlâ seri ve rate-limit'e açık; Alpaca birincilliği tamamlanmalı (P1).
- LLM çağrılarında headroom compression yeni — token maliyeti/gecikme ölçümü panelde yok (P2).

## D.4 — GÜVENİLİRLİK VE HATA YÖNETİMİ

- **Auth regresyonu (P0):** korumalı endpoint'ler 401 yerine 200 dönüyor (bilinen fail listesinde 3 haftadır duruyor). Canlıya çıkmadan kapatılmalı.
- **Sessiz job başarısızlığı:** scheduler'da 10dk watchdog var (iyi) ama job-run geçmişi hiçbir yüzeyde görünmüyor; haftalık kalibrasyon retrain'i sessizce ölebilir.
- Telegram bildirim hattının başarısızlık durumu (token süresi, chat kaybı) için fallback/alarm yok.
- SQLite eşzamanlılık: scheduler + API + script'ler aynı finpilot.db'ye yazıyor; "database is locked" riski büyüdükçe artar.
- Crash loop koruması: start.sh watchdog PID'i var; ancak watchdog'un kendisinin logları/limitleri belgelenmemiş.
- DRL inference, Mart modelleriyle sessizce "çalışıyor" — model yaşı kontrolü yapan bir guard yok ("model 90 günden eskiyse uyar" kuralı eklenebilir).

## D.5 — GÖZLEMLENEBİLİRLİK AÇIKLARI

- Prometheus/Grafana fiilen kapalı → tüm metrik yatırımı (prometheus_exporter.py 337 LOC, paneller) karanlıkta.
- İzlenmeyen kritik noktalar: job başarı oranı, LLM token maliyeti/gün, cache hit-rate, Telegram teslimat oranı, scanner süre trendi, model yaşı.
- Dashboard'da sistem sağlığı kartı yok (kullanıcıya değil operatöre dönük tek bakış eksik).
- Sentry DSN boş (fp uyarıyor) — hata toplama kapalı.

## D.6 — KOD KALİTESİ VE TEKNİK BORÇ

- Coverage bilinmiyor (.coverage 05-23'ten kalma); CI'da gate yok.
- Dev yoğunluğu: watchlist.py 1.019 LOC router, auth/database.py 1.410 LOC, scheduler.py 1.247 LOC — üç "tanrı dosyası".
- Academy 0 test; agents/ LLM çıktıları golden-set'siz.
- Magic number'lar: scheduler `_advisory_every_n = 10`, DD gate %3, watchdog 600sn — config'e taşınabilir (P3).
- 6 requirements dosyası + pyproject — bağımlılık tek kaynağa indirilmeli (P2).
- Naming tutarlı (snake_case); pre-commit + ruff + mypy kurulu (artı).

## D.7 — BELGE VE YÖNERGELERİN DURUMU

| Belge | Konu | Son güncelleme | Güncel mi? | Eksik | Yanlış | Aksiyon |
|---|---|---|---|---|---|---|
| README.md | Genel + runtime contract | 05-23 | ✅ Büyük ölçüde | Academy bölümü yok | CI badge placeholder | Academy ekle, badge düzelt |
| docs/FULL_AUDIT_REPORT.md | Tam audit | 05-23 | ✅ (tarihli snapshot) | — | — | INDEX'e bağla |
| FinanceAcademy/README.md | Academy kılavuz | 06-09 | ⚠️ | — | Yanlış klasörü anlatıyor; "8 agent" (kodda 6) | academy/README.md olarak taşı+düzelt |
| docs/ROADMAP_Q1_2025.md + 5 roadmap | Yol haritaları | 01-27..03-10 | ❌ | — | Fiilen geçersiz | Tek ROADMAP.md, eskiler archive |
| docs/feature_flags.md | Flag envanteri | 05-23 | ✅ | Haziran flag'leri (headroom) | — | Güncelle |
| docs/PAPER_TRADING_GUIDE.md | Paper trading | 05-05 | ⚠️ | Alpaca bulk akışı yok | — | Güncelle |
| docs/DRL_* (6 dosya) | DRL analiz/roadmap | 02-15..05-05 | ❌ Çelişkili | — | Eski varsayımlar | Tek DRL_STATUS.md'ye indir |
| DEPENDENCIES.md (×2) | Bağımlılıklar | 01-26 / 04-07 | ❌ | — | Drift | Tekille |
| tests/PRE_EXISTING_FAILURES.md | Test baseline | 05-20 | ✅ | — | — | Auth fix sonrası güncelle |
| docs/HIBE_FON_DEGERLENDIRME.md + grant_documents/ | Hibe | 05-04/05 | ⚠️ Dormant | Güncel sistem durumu | — | Hibe yolu seçilirse yenile |
| mkdocs site/ | Yayınlanmış doc | 05-05 | ❌ | — | docs ile drift | Rebuild veya kaldır |

---

# Bölüm E — Neden-Sonuç (Kök Neden) Kartları

## SORUN KARTI #1 — Sinyal motorunun kanıtlanmış edge'i yok
**Modül:** scanner / score / eval · **Belirti:** Profit Core audit: decile_lift=0.728, p=0.995 (skor TERS yönlü ayrıştırıyor); ablation: score & R/R zararlı.
**5 WHY:** Skor kârlılığı öngörmüyor → çünkü bileşen ağırlıkları sezgiyle seçildi, outcome verisiyle değil → çünkü yakın zamana kadar outcome verisi yoktu (signals_archive migrasyonu ve outcomes_horizon Mayıs'ta geldi) → çünkü sistem önce "özellik üretme" modunda büyüdü, "ölçme" modu sonradan eklendi → **Kök neden: build-first/measure-later geliştirme kültürü; edge hipotezi hiç resmî olarak test edilmeden ürünleşme başladı.**
**Etki:** Ürün vaadi savunulamaz (kullanıcı), yatırımcı DD'sinde kırılma noktası (iş), tüm sinyal-satışı vizyonları bloke (strateji), geliştirici motivasyonu yanlış hedefe akıyor (verim).
**Çözüm:** Kısa: skor bileşenlerini ablation'a göre yeniden ağırlıklandır + haftalık otomatik Edge Report. Kalıcı: outcomes_horizon üzerinde walk-forward edge testi; geçen bileşen kalır, geçmeyen atılır. Önleme: "yeni skor bileşeni = edge testi geçmeden merge yok" kuralı.
**Başarı kriteri:** decile_lift > 1.15, p < 0.05, 3 ardışık haftalık raporda. **Öncelik: P0 · Efor: Orta**

## SORUN KARTI #2 — Academy iki kopya, sıfır kullanıcı
**Modül:** academy/ + FinanceAcademy/ · **Belirti:** İki paralel kod tabanı; DB'ler 4KB; router/UI yok.
**5 WHY:** Kullanıcı yok → çünkü ürün yüzeyinde Academy yok → çünkü entegrasyon (router+UI) hiç yapılmadı → çünkü modül standalone prototip olarak doğdu ve repo'ya "yeniden yazım" olarak girdi ama eski kopya silinmedi → **Kök neden: prototip→ürün geçiş protokolü yok; "bitti" tanımı entegrasyonu kapsamıyor.**
**Etki:** En düşük riskli gelir yolu rafta; çift bakım maliyeti; README yanlış bilgi veriyor.
**Çözüm:** Kısa: FinanceAcademy→archive, seed çalıştır, router+1 sayfa. Kalıcı: Bölüm H planı. Önleme: Definition-of-Done'a "API+UI+test+doc" maddesi.
**Başarı kriteri:** Bir kullanıcı (Meriç) dashboard'dan ders tamamlayıp quiz çözebiliyor. **Öncelik: P0-P1 · Efor: Düşük→Orta**

## SORUN KARTI #3 — Auth regresyonu bilinen-fail olarak normalleşti
**Modül:** api/auth · **Belirti:** Korumalı endpoint 200 dönüyor; test 3 haftadır "pre-existing failure" listesinde.
**5 WHY:** Endpoint korumasız → çünkü require_auth kaldırılmış (muhtemelen dev kolaylığı/dashboard entegrasyonu sırasında) → çünkü güvenlik testinin fail'i "bilinen" statüsüne alınmış → çünkü baseline dosyası fail'leri normalleştiren bir mekanizmaya dönüşmüş → **Kök neden: bilinen-fail listesinin SLA'sı yok; güvenlik fail'i ile flaky test aynı kefede.**
**Etki:** Canlıya çıkışta veri sızıntısı/istismar riski; "güvenli platform" iddiası boşa düşer.
**Çözüm:** Kısa: require_auth'u geri ekle, testi yeşile çevir. Önleme: PRE_EXISTING_FAILURES'a kategori bazlı SLA (security=72 saat).
**Başarı kriteri:** test_compute_surface_requires_auth pass; baseline'da security kategorisi boş. **Öncelik: P0 · Efor: Düşük**

## SORUN KARTI #4 — DRL modelleri 3 ay bayat
**Modül:** drl/ + models/ · **Belirti:** En yeni ağırlık 2026-03-06; inference bu ağırlıklarla canlı.
**5 WHY:** Retrain yok → çünkü eğitim manuel ve pahalı → çünkü otomatik retrain pipeline'ı hiç kurulmadı → çünkü DRL "araştırma sprint'i" olarak gelişti, operasyon sahibi atanmadı → **Kök neden: araştırma modülü, operasyonel sahiplik tanımlanmadan ürün yüzeyine bağlandı.**
**Etki:** "AI-powered" iddiasının en savunmasız noktası; rejim değişiminde sessiz performans çürümesi.
**Çözüm:** Kısa: model yaşı guard'ı (>90 gün → UI'da uyarı + inference'ı opsiyonel kapat). Kalıcı: aylık retrain cron + walk-forward kabul testi VEYA DRL'yi "research preview" olarak ayır. Önleme: model registry'ye max-age politikası.
**Başarı kriteri:** Ya güncel model (≤30 gün) ya da üründe açık "deneysel" etiketi. **Öncelik: P1 · Efor: Orta**

## SORUN KARTI #5 — Gözlemleme yatırımı karanlıkta
**Modül:** monitoring/ + core/prometheus_exporter · **Belirti:** Exporter, paneller, alert kuralları var; hiçbiri ayakta değil; Sentry boş.
**5 WHY:** Kimse metrik görmüyor → çünkü Grafana stack'i sadece compose'ta ve compose günlük akışta kullanılmıyor → çünkü dev akışı start.sh'a sabitlendi → çünkü "önce ürün" önceliği gözlemlemeyi prod-sonrasına itti → **Kök neden: gözlemleme, deploy hedefi (prod) olmayan bir sistemde prod-aracı olarak tasarlandı.**
**Etki:** Sessiz başarısızlıklar (D.4) görünmez; performans regresyonları ancak kullanıcı şikâyetiyle yakalanır.
**Çözüm:** Kısa: dashboard'a tek "Sistem Sağlığı" kartı (job-run tablosu + model yaşı + son scan süresi — Grafana'sız, kendi DB'sinden). Kalıcı: prod kararıyla birlikte Grafana profile.
**Başarı kriteri:** Operatör tek ekranda son 24 saatin job/hata durumunu görüyor. **Öncelik: P1 · Efor: Düşük**

## SORUN KARTI #6 — Landing/dağıtım katmanı yok
**Modül:** (eksik modül) · **Belirti:** Canlı landing yok, waitlist yok, public demo yok; eski site arşivde "extraction bekliyor".
**5 WHY:** Gelir testi yapılamıyor → çünkü kullanıcıya ulaşan tek yüzey localhost → çünkü dağıtım hiç kurulmadı → çünkü enerji %95 ürün-içine aktı → **Kök neden: "önce mükemmel ürün, sonra kullanıcı" varsayımı; dağıtım, ürünün parçası olarak görülmüyor.**
**Etki:** Tüm G.2 hızlı-gelir senaryoları bloke; geri bildirim döngüsü tek kullanıcılık (Meriç).
**Çözüm:** Kısa: 1 sayfalık landing + waitlist (1 gün). Kalıcı: haftalık public demo/track-record yayını. Önleme: her çeyrekte en az bir dış-kullanıcı temas hedefi.
**Başarı kriteri:** 30 gün içinde ≥100 e-posta. **Öncelik: P1 (stratejik P0) · Efor: Düşük**

## SORUN KARTI #7 — Belge enflasyonu ve çelişen roadmap'ler
**Modül:** docs/ · **Belirti:** 45 MD, ≥6 roadmap, 2 DEPENDENCIES, bayat DRL dokümanları.
**5 WHY:** Okuyucu güncel gerçeği bulamıyor → çünkü her sprint yeni belge üretti, eskisini emekli etmedi → çünkü belge yaşam döngüsü (supersede kuralı) yok → **Kök neden: yazma kültürü güçlü, küratörlük kültürü yok.**
**Çözüm:** Kısa: ROADMAP.md tekilleştirme + INDEX.md. Kalıcı: her yeni analiz belgesi başına "supersedes:" satırı (FULL_AUDIT bunu yapıyor — standartlaştır). **Öncelik: P1 · Efor: Düşük**
