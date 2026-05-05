# FinPilot — 6 Perspektiften Karşılaştırmalı Değerlendirme

| Alan | Değer |
|------|-------|
| **Proje** | FinPilot — AI-Powered Stock Analysis Platform |
| **2–3 Cümle Özet** | Rejim-farkındalığı olan DRL ensemble (20 PPO/RPPO ajan) + çok-sağlayıcılı LLM + teknik scanner üzerine kurulmuş bir US-equities karar-destek ürünü. Next.js 16 + FastAPI + Alpaca paper + Telegram. Streamlit MVP'sinden üretim stack'ine geçişin son evresinde. |
| **En Büyük 3 Sorun** | (1) Ödeme/billing altyapısı hiç yok; (2) Auth dev-key fallback prod'da sessiz geçiyor + DB dosyaları repo'ya sızıyor; (3) DRL inference senkron — API worker'ı bloke ediyor, SLO yok. |
| **Kritik MCS** | auth (register/login/refresh), scan, inference, billing (yok), GDPR export/delete (doğrulanmadı), backup (yok), support widget (yok). |
| **Hedef Pazar** | DACH + TR + US bireysel yatırımcı; ikincil: küçük hedge fonlar / fintech startup'ları (API/white-label). |
| **Mevcut Temel Metrikler (varsayım / elde olan)** | Waitlist ≈ 500 kayıt (`data/waitlist.json`); 0 ödeyen (ödeme yok); CI coverage ≥ %70; 20 eğitilmiş model (Sharpe 0.03–0.20 bazılarında negatif avg_reward görülüyor); Grafana dashboard JSON mevcut. MRR = €0, aktif kullanıcı = dev + QA. |
| **Tarih** | 2026-04-22 |

> Bu rapor, `FINPILOT_FULL_AUDIT_2026-04-22.md` ve `FINPILOT_GO_TO_MARKET_2026-04-22.md` dokümanlarını karşılaştırmalı perspektifler altında sentezler.

---

## İçindekiler

1. [Girişimci Perspektifi](#1-girişimci-perspektifi)
2. [Broker / Satış Perspektifi](#2-broker--satış-perspektifi)
3. [Pazarlama Perspektifi](#3-pazarlama-perspektifi)
4. [Satınalmacı / Kurumsal Alıcı Perspektifi](#4-satınalmacı--kurumsal-alıcı-perspektifi)
5. [Uygulama Geliştirici (Teknik) Perspektifi](#5-uygulama-geliştirici-teknik-perspektifi)
6. [Yatırımcı Perspektifi](#6-yatırımcı-perspektifi)
7. [Karşılaştırmalı Özet ve Öneriler](#7-karşılaştırmalı-özet)
8. [Executive Summary (1 sayfa)](#8-executive-summary)
9. [Deney Matrisi — CSV](#9-deney-matrisi--csv)

---

### 1. Girişimci Perspektifi

#### 1.1 Kısa Özet
Founder için FinPilot, "bir sonraki 12 ayı hayatta kalarak büyümek" meselesi. Ürün teknik olarak **80% hazır**, fakat gelir motoru **%0**. Hedef: 30 gün içinde ilk ödeyen 30 kullanıcı + LTD kampanyasıyla cash infusion + 90 günde €5K+ MRR.

#### 1.2 Artılar
- Teknik temel olgun; 20 eğitilmiş model + multi-LLM + dashboard + CI ile rakiplerden 6 ay önde.
- 500 kayıt güçlü waitlist — sıfırdan launch değil.
- Grant kit (AWS Gründungsfonds EN/DE/TR) hazır — non-dilutive runway yakın.
- Solo founder olarak küçük ölçekte hızlı karar verme avantajı.

#### 1.3 Eksiler ve Riskler
- **Ödeme altyapısı yok** → fiili gelir başlamamış; market sinyali tahmini.
- Solo bandwidth riski: pazarlama + ürün + ops aynı kişide.
- ML maliyeti (LLM çağrıları) arttıkça unit economics sıkışabilir.
- "Yatırım tavsiyesi" algısı → legal teminat gerekir.
- Teknik borç (config dağınıklığı, iki UI) bakım yükü.

#### 1.4 Hızlı Kazanımlar (48 saat)
- [ ] Stripe hesabı aç + 3 product/price (Basic/Pro/Edge) — 4 saat.
- [ ] `/pricing` landing yayına al + waitlist'e "pre-launch %25" kuponu duyuru — 4 saat.
- [ ] AWS Gründungsfonds başvurusunu gönder (dosyalar hazır `grant_documents/`) — 3 saat.
- [ ] LTD teaser: Twitter + LinkedIn "ilk 100 seat €199" — 2 saat.
- [ ] "Founder 1:1 feedback call" 5 beta ile (Calendly link) — 1 saat planlama.

#### 1.5 2 Haftalık Eylem Planı

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| D1 | Stripe + 3 plan + test mode webhook | Founder | Test checkout yeşil |
| D2–D3 | `api/routers/billing.py` + subscription DB + feature gating | Founder + BE | Pro endpoint 402 for Basic |
| D4 | Dashboard billing sayfası + upgrade modal | Founder + FE | E2E upgrade yeşil |
| D5 | Email otomasyonu (Resend) — welcome + trial | Founder | 3 template aktif |
| D6 | Waitlist blast (500 e-posta) | Founder | Open rate ölçülüyor |
| D7 | "Show HN" draft + canary Ring 1 | Founder | 10 beta aktif |
| D8 | LTD landing `/lifetime` + 100 seat | Founder + FE | Stripe one-time canlı |
| D9 | Telegram premium bot `/subscribe` | Founder + BE | Invite link çalışıyor |
| D10 | PH + Reddit + HN posts hazır | Founder | Draft onaylandı |
| D11 | Canary Ring 2 (50 kullanıcı) | Founder + SRE | Error < %1 |
| D12 | Weekly retrospective + metric dashboard review | Founder | Rapor Slack'te |
| D13 | **Public Launch** (PH + HN + Reddit + email) | Founder | ≥ 30 ödeyen |
| D14 | Post-mortem + H3 backlog | Founder | Backlog prioritize |

#### 1.6 KPI Listesi
- MRR (€), Paid conversion (%), LTD seats, Trial→Paid (%), CAC, Runway (ay), D7 activation (%), NPS.

#### 1.7 Önerilen Deneyler
- **E-F1:** 14 gün trial (kartsız) vs 7 gün trial (kartlı) — hangi Paid'e daha iyi dönüşüyor?
- **E-F2:** LTD 100 seat urgency banner — görünür counter vs gizli.
- **E-F3:** Founder personal Twitter thread vs kurumsal blog — sign-up CAC.
- **E-F4:** Pricing sayfasında "Most Popular" rozeti Pro'ya vs Basic'e.

#### 1.8 Canlıya Alma Kabul Kriterleri
- Stripe live mode webhook test edildi.
- MCS smoke tests 100% yeşil.
- Canary Ring 2 son 48 saatte hatasız.
- Terms + Privacy + Risk disclaimer yayında.
- En az 3 ödeyen müşteri paper trial'dan paid'e geçti.

#### 1.9 Tahmini Kaynak İhtiyacı
**7 insan-gün founder + 3 insan-gün dış frontend freelancer + 1 insan-gün legal review.** Toplam ≈ **11 insan-gün** / 2 hafta.

#### 1.10 Gelir Fikirleri

| # | Fikir | Zaman | Tahmini Gelir (90g) |
|---|-------|-------|---------------------|
| 1 | SaaS Basic/Pro/Edge (€19/49/79) | 5 gün geliştirme | MRR €1,750 → €3,500 kümülatif |
| 2 | LTD Pro €199 × 100 seat | 3 gün | €11,940 (tek sefer cash) |
| 3 | "Founder Office Hours" — aylık 1:1 (€99/ay, 10 seat) | 1 gün | €990/ay premium |

---

### 2. Broker / Satış Perspektifi

#### 2.1 Kısa Özet
Outbound + inbound satış gözüyle ürün, "US-fokuslu bireysel + küçük fon" hedefine uygun. Asıl değer önerisi **"zaman tasarrufu + rejim-farkındalığı + transparent performance"**. Satışta kilit silah: walk-forward performance raporu + benchmark-relative Sharpe.

#### 2.2 Artılar
- 20 model + A/B rapor + Optuna çıktıları satışta somut kanıt.
- Alpaca entegrasyonu "paper'da dene, beğen" deneyimi sunuyor.
- DACH pazarına DE dilinde pitch deck + business plan hazır.
- B2B pilot için API/white-label açık; Pro planın üstünde "Enterprise" fiyatlama mümkün.

#### 2.3 Eksiler ve Riskler
- Satış ekibi yok; founder-led sales.
- Müşteri referansı yok; case study eksik.
- MCS'te billing yok → "demo'dan sonra satamıyoruz".
- Compliance belirsizliği B2B kapılarını kapatabilir.
- Walk-forward doğrulanmış Sharpe raporu henüz prod raporu formatında yok.

#### 2.4 Hızlı Kazanımlar (48 saat)
- [ ] 3 sayfalık **one-pager** (TR/EN/DE) — `sales/onepager_2026-04.pdf`.
- [ ] Calendly link + demo akışı (10 dk ürün tur + 5 dk soru).
- [ ] `data/ab_report_20260419_1345.md` → temizle ve "Performance Letter" haline getir.
- [ ] 20 hedef lead listesi (TR: bireysel trader topluluğu; DACH: finfluencer).
- [ ] Discovery call template (BANT).

#### 2.5 2 Haftalık Eylem Planı

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| D1 | One-pager + case study draft | Founder + PM | 3 dil hazır |
| D2 | Calendly + discovery template | Sales | İlk 5 call booked |
| D3 | 20 outbound email (cold, TR trader topluluğu) | Sales | ≥ 3 reply |
| D4 | DACH finfluencer outreach (10 profil) | Sales | 2 affiliate call booked |
| D5 | Demo video 3 dk (Loom) | Sales + FE | Landing'e gömüldü |
| D6 | İlk 5 demo call + feedback form | Founder | NPS measured |
| D7 | Referral program v0 (20% recurring) | Sales + BE | Referral code çalışıyor |
| D8 | 10 yeni outbound (hedge fon boutique) | Sales | ≥ 2 reply |
| D9 | B2B pilot teklif şablonu (bkz. bölüm 4) | Sales + Legal | Draft onaylandı |
| D10 | Weekly performance letter v1 yayın | Sales + ML | 100+ mail okundu |
| D11 | Affiliate 3 partner onboard | Sales | Dashboard'da görünür |
| D12 | "Case Study" — 1 beta kullanıcının hikayesi | Sales + PM | Blog yayını |
| D13 | Launch day: PH + inbound demo aksiyonu | Sales + Founder | ≥ 10 paid demo |
| D14 | Retro + Sales backlog | Sales | KPI tablosu hazır |

#### 2.6 KPI Listesi
- MQL, SQL, Demo booked, Demo held, Demo→Paid (%), ACV, Sales cycle (gün), Referral share.

#### 2.7 Önerilen Deneyler
- **E-S1:** Cold email "walk-forward Sharpe ile" vs "zaman tasarrufu ile" CTA — reply rate.
- **E-S2:** Demo-first vs Self-serve trial-first — conversion.
- **E-S3:** Referral 20% recurring vs 30% 3-month — viral katsayı.
- **E-S4:** Monthly Performance Letter vs haftalık — unsubscribe + reply rate.

#### 2.8 Canlıya Alma Kabul Kriterleri
- 3+ paid referans müşteri.
- Discovery → Demo → Close boru hattı Notion/HubSpot'ta izlenebilir.
- ToS / MSA template legal onaylı.
- Referans kit (case study + performance letter) güncel.

#### 2.9 Tahmini Kaynak İhtiyacı
**5 insan-gün founder-sales + 2 insan-gün PM + 1 insan-gün legal.** ≈ **8 insan-gün** / 2 hafta.

#### 2.10 Gelir Fikirleri

| # | Fikir | Zaman | Tahmini Gelir (90g) |
|---|-------|-------|---------------------|
| 1 | Affiliate / Partner ağı (finfluencer) %20 recurring | 7 gün | 10 partner × 5 kullanıcı × €35 = €1,750/ay |
| 2 | Enterprise Pilot (€499/ay × 3 pilot) | 14 gün | €4,500 (3 ay × 3 müşteri) |
| 3 | Alpaca / IBKR broker referral (açılan hesap başına €50) | 3 gün | 20 dönüşüm = €1,000 tek sefer |

---

### 3. Pazarlama Perspektifi

#### 3.1 Kısa Özet
Organic > paid (bütçe sınırı). Üç taşıyıcı kanal: **Reddit (r/algotrading, r/stocks, r/wallstreetbets)** + **Twitter/X (fintwit + algotrading)** + **e-posta dijesti (Daily Top-3)**. Kapı açıcı: **"transparent performance"** — haftalık gerçek performans raporu içerik motoru olur.

#### 3.2 Artılar
- Zaten 500 kayıtlı waitlist var.
- Tematik içerik pipeline'ı geniş (20 model × çok rejim × haftalık rapor).
- DACH'ta içerik az; EN/DE/TR olgun doküman var.
- LTD + PH launch momentum motoru olarak çalışabilir.

#### 3.3 Eksiler ve Riskler
- Reklam harcama disiplinsizliği → CAC > LTV riski.
- "Yatırım tavsiyesi" algısı platformlarda tepki çekebilir (FTC, BaFin, SPK).
- Performans kötü ayı piyasasında kötü görünür — messaging'in benchmark-relative olması şart.
- E-posta teslim edilebilirlik (IP warmup, DKIM/SPF) hazır değil.

#### 3.4 Hızlı Kazanımlar (48 saat)
- [ ] Waitlist'e pre-launch %25 off + teaser video gönder.
- [ ] `/pricing` + `/lifetime` sayfaları canlı.
- [ ] Landing page CTA + sosyal kanıt (47/100 seat) testi.
- [ ] Resend/Postmark domain + DKIM + SPF + DMARC.
- [ ] Plausible veya PostHog analytics.

#### 3.5 2 Haftalık Eylem Planı

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| D1 | E-posta deliverability setup (DKIM/SPF/DMARC) | Growth + DevOps | Mail-tester 10/10 |
| D2 | Daily Top-3 dijesti cron (07:30 UTC) | Growth + ML | 3 sembol + chart PNG |
| D3 | Plausible / PostHog funnel (Visitor→Signup→Active→Paid) | Growth | Dashboard canlı |
| D4 | 3 blog post ("Rejim detection", "Ensemble router nasıl çalışır", "LTD neden") | Growth + PM | SEO base |
| D5 | Reddit r/algotrading "weekly transparency" post | Growth | 150+ upvote |
| D6 | Twitter thread (launch teaser) | Growth | 50+ retweet |
| D7 | Waitlist blast + kupon | Growth | Open rate ≥ 35% |
| D8 | DACH DE tercümesi — landing + 1 blog | Growth | `finpilot.app/de` live |
| D9 | Affiliate onboarding kit (banners + UTM) | Growth | 3 partner aktive |
| D10 | PH listing + "coming soon" page | Growth | Follower ≥ 200 |
| D11 | HN "Show HN" post zamanla (Sal 09:00 UTC) | Growth + Founder | Üst 10'da |
| D12 | Retargeting piksel (Meta / X) | Growth | Audience kuruldu |
| D13 | **Public Launch** — PH + HN + Reddit + email | Growth + Herkes | ≥ 500 sign-up |
| D14 | Retro + Week 3 plan | Growth | Plan Slack'te |

#### 3.6 30 / 60 / 90 Günlük Growth Planı

**30 gün:** Temel set — deliverability, analytics funnel, waitlist aktivasyonu, PH + HN launch, Daily Top-3 dijest, 3 blog post. Hedef: 1,000 sign-up, 50 ödeyen, €1,500 MRR.

**60 gün:** SEO build-out — 10 blog post, 3 comparison sayfası ("FinPilot vs TradingView", "vs Trade Ideas"), DE pazarlama artışı, AppSumo listing başvurusu, 2 podcast guest. Hedef: 3,000 sign-up, 150 ödeyen, €4,500 MRR.

**90 gün:** Kanal derinleştirme — haftalık newsletter 3K abone, YouTube kanalı (10 video), Discord topluluk 500 üye, 5 finfluencer partnership. Hedef: 6,000 sign-up, 300 ödeyen, €9,000 MRR.

#### 3.7 Kanal Önceliklendirmesi

| Kanal | Öncelik | Neden | Bütçe (€/ay) |
|-------|---------|-------|--------------|
| Reddit (organik) | P0 | Niş topluluk, ücretsiz | 0 |
| Twitter/X (organik) | P0 | Fintwit ağı, launch cascade | 0 |
| E-posta dijest | P0 | Aktivasyon + retention motoru | 30 (Resend) |
| SEO / Blog | P1 | Uzun vadeli organik CAC | 0–100 (içerik) |
| Product Hunt | P1 | Tek seferlik spike | 0 |
| AppSumo / LTD | P1 | Cash infusion | 10% komisyon |
| YouTube | P2 | Yüksek intent, yavaş | 0–200 (edit) |
| Meta/Google Ads | P3 | CAC belirsiz, sonra | 300 test |

#### 3.8 Örnek Kampanya Briefleri

**Kampanya K1 — "14 Gün Ücretsiz + LAUNCH25"**
- Hedef: Waitlist → Sign-up %35 dönüşüm
- Kanal: E-posta + Twitter + LinkedIn
- Mesaj: "14 gün kartsız dene. LAUNCH25 ile Pro aboneliği ilk ay %25 indirimli."
- CTA: "Hemen başla"
- KPI: Sign-up delta (D0→D7), open rate ≥ 35%, CTR ≥ 8%.
- Süre: 7 gün.
- Bütçe: €0 (owned channels).

**Kampanya K2 — "Weekly Performance Transparency"**
- Hedef: Trust + reddit/twitter viralite.
- Kanal: Reddit + Twitter + Blog.
- Mesaj: "Geçen hafta ensemble Sharpe = X; benchmark (SPY) Sharpe = Y; top-3 fikir: ..."
- KPI: 150+ upvote / hafta, 1,000+ blog visitor, 10+ new sign-up / post.
- Süre: haftalık, kalıcı.
- Bütçe: €0.

**Kampanya K3 — "Lifetime Deal 100 Seat"**
- Hedef: Cash + topluluk.
- Kanal: Twitter + LinkedIn + AppSumo + finfluencer partner.
- Mesaj: "İlk 100 seat €199 lifetime Pro. 47/100 alındı."
- KPI: Seat satış hızı (hedef 3/gün), conversion rate on `/lifetime`.
- Süre: 14 gün + scarcity extension.
- Bütçe: %10 komisyon (AppSumo).

#### 3.9 A/B Test Hipotezleri

- **E-M1:** "14 gün ücretsiz" vs "7 gün ücretsiz" CTA — sign-up oranı.
- **E-M2:** Landing hero "Save time" vs "Beat the market" — CTR.
- **E-M3:** Günlük top-3 e-posta subject: "Top 3 AAPL + 2 more" vs "Today's best setups" — open rate.
- **E-M4:** Pricing sayfasında "Edge" planı gösterimi — upsell ratio.
- **E-M5:** Twitter thread "data-first" (grafik) vs "story-first" (anecdote) — retweet.

#### 3.10 KPI Listesi
- Sign-ups/gün, CAC, LTV, LTV/CAC, Paid conversion, Activation, Unsubscribe, Channel attribution, Viral coefficient.

#### 3.11 Canlıya Alma Kabul Kriterleri
- Deliverability DKIM/SPF/DMARC yeşil.
- Analytics funnel kurulmuş; attribution çalışıyor.
- Legal + risk disclaimer her e-postada.
- Unsubscribe link + one-click (CAN-SPAM).

#### 3.12 Tahmini Kaynak İhtiyacı
**6 insan-gün growth + 2 insan-gün içerik freelancer + 1 insan-gün designer.** ≈ **9 insan-gün** / 2 hafta.

#### 3.13 Gelir Fikirleri

| # | Fikir | Zaman | Tahmini Gelir (90g) |
|---|-------|-------|---------------------|
| 1 | Daily Top-3 Free → Premium Upsell (€9/ay) | 5 gün | 300 × €9 = €2,700/ay |
| 2 | Sponsored newsletter (broker/data vendor) | 14 gün | 1 sponsor × €1,500/ay |
| 3 | DACH pazarı için DE landing + affiliate DE finfluencer | 10 gün | 5 partner × €400/ay |

---

### 4. Satınalmacı / Kurumsal Alıcı Perspektifi

#### 4.1 Kısa Özet
Hedef satınalmacı: küçük-orta hedge fonlar (AUM €5M–€100M), aile ofisleri, veri-odaklı küçük broker firmaları. Değer önerisi: **"kendi ensemble'ınızı, kendi verinizle, on-prem veya VPC'de."** Kurumsal müşteri için kritik: SLA, DPA, SOC2 yolu, white-label, entegrasyonlar.

#### 4.2 Artılar
- API + Docker + multi-LLM abstraction sayesinde VPC deploy uygun.
- Grant dokümanlarındaki profesyonellik B2B inbound'u kolaylaştırır.
- Python-native stack, quant ekiplerin alışkın olduğu araçlarla uyumlu.
- MLflow-hazır mimari ve model registry enterprise-friendly.

#### 4.3 Eksiler ve Riskler
- SOC2 / ISO27001 yok; kurumsal security review'da tıkanır.
- Audit log olgunluğu; DLP politikaları yazılı değil.
- SLA metrikleri formal tanımlı değil.
- On-prem veya BYO-cloud deployment için Helm chart / Terraform yok.
- Multi-tenant izolasyon yok; single-tenant deploy gerekebilir.

#### 4.4 Hızlı Kazanımlar (48 saat)
- [ ] Kurumsal "Pilot Teklif" bir sayfalık şablon (aşağıda).
- [ ] DPA (Data Processing Agreement) şablon + sub-processor listesi (Stripe, Alpaca, Sentry, AWS, Resend, vb.).
- [ ] "Security Overview" 2 sayfalık özet (Auth, Encryption, Logs, Backups).
- [ ] Terraform stub (AWS ECS Fargate + RDS) iskelet.

#### 4.5 2 Haftalık Eylem Planı

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| D1 | Pilot teklif şablonu + pricing tiers (Enterprise) | Sales + Legal | PDF hazır |
| D2 | DPA + sub-processor listesi | Legal | Onaylı PDF |
| D3 | Security Overview 2-pager | SRE + CTO | Linkedin-ready |
| D4 | Terraform (AWS ECS Fargate) iskelet | DevOps | `terraform plan` temiz |
| D5 | SLA taslağı (%99.5, p95 < 500ms, response SLA) | Founder + Legal | Müşteri-hazır |
| D6 | Role-based access control (RBAC) v1 | Backend | Org/member model |
| D7 | Outbound: 10 hedge fon boutique + 5 aile ofisi | Sales | ≥ 2 discovery call |
| D8 | Single-tenant deploy scripti + secrets abstract | DevOps | `./deploy.sh --tenant=X` |
| D9 | Stripe "Invoice" akışı (B2B) | Backend | Net 30 invoice çıktı |
| D10 | 3rd-party audit log formatı (SIEM JSON) | Platform | Loki/ELK integrate |
| D11 | API key management (per-tenant) | Backend | Key rotate çalışıyor |
| D12 | Pilot 1 teklif gönder | Sales | Mutabakat |
| D13 | B2B demo (3 pilot kandidat) | Founder | NDA imzalı |
| D14 | Pilot 1 kickoff | Sales + DevOps | T-3 gün deploy |

#### 4.6 Kurumsal Pilot Teklif Şablonu (1 sayfa)

```
FinPilot Enterprise Pilot
Dönem: 60 gün · Fiyat: €1,500 (indirimli pilot, MSRP €2,500)

KAPSAM
- Tek-tenant Docker deploy (müşteri VPC veya on-prem)
- Pro+API plan özellikleri (unlimited scan + inference, 5 eşzamanlı kullanıcı)
- MLflow entegrasyonu, özel model upload
- SLA: %99.5 uptime, p95 API < 500 ms, critical incident 4h RTO
- Dedicated Slack Connect kanal + haftalık check-in

BAŞARI KRİTERLERİ (pilot sonu)
- Senaryo 1: Günlük scan 1,000+ sembol
- Senaryo 2: Ensemble inference < 3 sn/sembol (p95)
- Senaryo 3: 30-gün walk-forward Sharpe ≥ 0.8
- Müşteri memnuniyeti ≥ 8/10

SONRASI
- Yıllık abonelik (€2,000/ay × 12) — %15 yıllık peşin indirim
- Veya devam etmeme + veri silme (GDPR)

SORUMLULAR
- FinPilot: deploy, tuning, haftalık rapor
- Müşteri: single POC, veri erişimi, feedback

İMZA
Adına: _______  Tarih: _______
```

#### 4.7 SLA Maddeleri (örnek)

- **Uptime:** %99.5 / ay (rolling). İhlal başına %10 aylık ücret iadesi.
- **Latency:** p95 API < 500 ms; p99 < 2 sn.
- **Incident response:** P1 < 1 saat; P2 < 4 saat; P3 < 24 saat.
- **Recovery:** RTO 4 saat, RPO 24 saat.
- **Bildirimler:** Status page + Slack Connect notify < 15 dk.
- **Veri iadesi:** 30 gün içinde format: Parquet/CSV + models.zip.
- **Veri silme:** 30 gün içinde GDPR Article 17 uyumlu; onay mektubu.

#### 4.8 TCO Hesaplama Şablonu (yıllık)

| Kalem | Hesap | Örnek Değer |
|-------|-------|-------------|
| FinPilot abonelik | €2,000 × 12 | €24,000 |
| LLM kullanım (üzerine fark) | €0.50/aktif kullanıcı × 20 × 12 | €120 |
| Broker komisyonu | Alpaca: 0 (stock/ETF) | 0 |
| Altyapı (eğer self-host) | AWS ECS + RDS + S3 | €3,600 |
| Ops (0.2 FTE) | €20/sa × 400 | €8,000 |
| Eğitim + onboarding | Tek sefer | €1,500 |
| **Toplam** | | **€37,220/yıl** |
| Etkin Maliyet / kullanıcı / ay | | €155 |

**Karşılaştırma referansı (manuel):** Bloomberg Terminal ~ €24,000/yıl/kullanıcı · TradingView Premium €59/ay × 5 = €3,540/yıl · kendi quant ekibi kurma = 1 FTE minimum €80,000.

#### 4.9 KPI Listesi
- Enterprise ACV, Pilot→Paid conversion, Logo count, NRR, GRR, SLA breaches, Support CSAT, Security questionnaire pass rate.

#### 4.10 Önerilen Deneyler
- **E-K1:** €1,500 pilot vs %100 money-back pilot — ödeme isteği etkisi.
- **E-K2:** Single-tenant vs Multi-tenant SaaS messaging — reply rate.
- **E-K3:** SOC2 roadmap gösterimi vs gizleme — kurumsal demo→pilot conversion.

#### 4.11 Canlıya Alma Kabul Kriterleri
- DPA + Sub-processor listesi yayında.
- Security Overview pdf + dashboard'dan erişim.
- Pilot 1 canlıda, SLA dashboard müşteriyle paylaşılabilir.
- Invoice akışı + Net 30 çalışıyor.

#### 4.12 Tahmini Kaynak İhtiyacı
**10 insan-gün (sales+legal+devops+backend).** 2 hafta.

#### 4.13 Gelir Fikirleri

| # | Fikir | Zaman | Tahmini Gelir (90g) |
|---|-------|-------|---------------------|
| 1 | Enterprise Pilot (€1,500 × 3) | 14 gün | €4,500 bir kerelik + recurring yol açıcı |
| 2 | API/White-label Pro+ (€199–€499/ay) | 21 gün | 2 müşteri × €350 = €700/ay |
| 3 | Custom Model Training services (€5K fixed-price) | 30 gün | 1 proje = €5,000 tek sefer |

---

### 5. Uygulama Geliştirici (Teknik) Perspektifi

#### 5.1 Kısa Özet
Mimari sağlam ama operasyonel olgunluk (SLO, async, secrets, migration) eksik. Öncelik: inference asenkronlaştırma + ödeme altyapısı + Alembic + observability SLO'ları + güvenlik sertleştirme.

#### 5.2 Artılar
- Modüler paket yapısı (scanner/drl/core/auth/api/web).
- Multi-service Docker + CI/CD + Prometheus + Sentry + structlog mevcut.
- 25 pytest dosyası (7,238 satır); coverage gate %70.
- 20 eğitilmiş model + Optuna + ensemble + hybrid engine.
- Pre-commit, ruff, bandit, detect-secrets zaten aktif.

#### 5.3 Eksiler ve Riskler
- Config dağınıklığı (5+ kaynak); global mutable `SETTINGS`.
- Auth dev-key fallback prod'da sessiz geçebiliyor.
- SQLite default + Alembic yok + `.db` repo'ya giriyor.
- DRL inference senkron; API worker bloke.
- Lint gate yumuşak (frontend `|| true`), bandit/safety advisory-only.
- `scanner.py` monolith + paket paralel; `drl_autopilot.py` vs `_patched.py` ikizleme.
- Streamlit + Next.js paralel UI bakım yükü.
- OTEL tracing yok; SLO yok; alertmanager yok.

#### 5.4 Hızlı Kazanımlar (48 saat)
- [ ] Auth `ENVIRONMENT=production` fail-fast guard.
- [ ] `data/*.db`, `data/test_auth.db` → `.gitignore`; geçmiş tarama.
- [ ] `telegram_config.py` → env-only.
- [ ] CI frontend lint sert gate; bandit `severity-level medium`.
- [ ] Alembic init + baseline migration.

#### 5.5 2 Haftalık Eylem Planı

| Gün | Görev | Sorumlu | Kabul Kriteri |
|-----|-------|---------|---------------|
| D1 | Auth guard + gitignore + Alembic init | Backend + DevOps | CI yeşil |
| D2 | `api/routers/billing.py` + Stripe test mode | Backend | Test e2e yeşil |
| D3 | Inference async: Redis Streams + background worker + polling endpoint | Platform | p95 inference < 3 sn; worker bloke yok |
| D4 | Feature gating middleware + RBAC | Backend | Pro endpoint 402 |
| D5 | OpenAPI export + TS client | BE + FE | `npm run generate-api` |
| D6 | Grafana SLO dashboard + Alertmanager (5 rule) | SRE | Test alert tetiklendi |
| D7 | k6 smoke CI job (perf/smoke.js) | DevOps | p95 < 500 ms, threshold pass |
| D8 | `scanner.py` arşivle + `scanner/` paketi kanonik | Backend | Import tek yoldan |
| D9 | `drl_autopilot_patched.py` konsolidasyonu | ML | Tek dosya, CI smoke |
| D10 | Model registry file-lock + atomic write | ML + Platform | Concurrent write testi |
| D11 | Trivy image scan + SBOM (syft) CI job | DevOps | Gate: 0 high CVE |
| D12 | Nightly backup (SQLite→S3) + restore drill | DevOps | RPO 24h, RTO 4h |
| D13 | Canary Ring 2 deploy | SRE | Error < %1 |
| D14 | Post-mortem runbook iskeleti + 5 playbook | SRE | `docs/runbooks/` merge |

#### 5.6 Teknik Borç Listesi

| # | Borç | Etki | Çözüm (Kısa/Orta/Uzun) |
|---|------|------|------------------------|
| 1 | Config dağınıklığı (5+ kaynak) | Yüksek | **K**: `pydantic-settings` merkezi `Settings` class; **O**: her modül bunu import etsin; **U**: ENV'e dair ADR. |
| 2 | `auth` prod dev-key fallback | Kritik | **K**: `ENVIRONMENT=production` guard; **O**: HSM/Vault; **U**: KMS + rotation. |
| 3 | Alembic yok | Yüksek | **K**: init + baseline; **O**: her PR'da migration; **U**: zero-downtime migration policy. |
| 4 | `scanner.py` vs `scanner/` ikizleme | Orta | **K**: root dosyayı `archive/`a al; **O**: paketi kanonik et; **U**: deprecation. |
| 5 | DRL inference senkron | Yüksek | **K**: background task + result polling; **O**: Celery/Dramatiq; **U**: gRPC inference service. |
| 6 | Global mutable `SETTINGS` | Orta | **K**: immutable dataclass; **O**: DI pattern; **U**: plugin config ayrışması. |
| 7 | `drl_autopilot` ikiz | Orta | **K**: konsolidasyon; **O**: tek canonical CLI; **U**: Argo/Prefect flow. |
| 8 | Registry single-file write | Yüksek | **K**: filelock; **O**: SQLite-backed registry; **U**: MLflow. |
| 9 | Streamlit + Next.js paralel | Orta | **K**: depreation banner; **O**: 30g sunset; **U**: tek yüzey. |
| 10 | Lint/security gates yumuşak | Yüksek | **K**: sert gate; **O**: SBOM + Trivy; **U**: supply-chain policy. |
| 11 | OTEL yok | Orta | **K**: structlog JSON; **O**: OTEL exporter → Tempo/Jaeger; **U**: distributed trace standardı. |
| 12 | SQLite prod risk | Yüksek | **K**: PG default compose; **O**: managed PG (RDS/Neon); **U**: HA + replica. |

#### 5.7 Güvenlik Açıkları (hızlı taramadan)

- Prod'da dev-key fallback (Auth).
- CORS whitelist belirsiz.
- JWT revocation store yok (sadece jti logic).
- `telegram_config.py` hardcoded risk.
- `data/*.db` commit.
- CSP/HSTS frontend headers yok.
- Bandit/Safety advisory-only CI.
- Plugin loader sandbox yok (`core/plugins.py`).

#### 5.8 Deployment + CI/CD + Monitoring Checklist

- [ ] GHCR image push + semver tag (`finpilot-api:vX.Y.Z`)
- [ ] Deploy target: Fly.io / Render / AWS ECS (Terraform stub)
- [ ] Blue/Green veya Canary rings (Ring 0–GA)
- [ ] Prometheus + Grafana (mevcut JSON import)
- [ ] Alertmanager 5 kural (aşağıda)
- [ ] Sentry DSN prod + release tag + environment
- [ ] UptimeRobot external probe
- [ ] Nightly backup + restore drill
- [ ] Runbook `docs/runbooks/*.md` (5 playbook)

#### 5.9 Canary + Rollback (metrik eşikleriyle)

| Metrik | Pencere | Eşik | Aksiyon |
|--------|---------|------|---------|
| `finpilot_api_error_rate` | 5 dk | > %2 | Auto rollback |
| `finpilot_api_latency_p95_ms` | 10 dk | > 1,000 | Alert → manuel |
| `finpilot_db_up` | 1 dk | == 0 | PagerDuty P1 + rollback |
| `finpilot_drl_errors_rate` | 5 dk | > %5 | Alert + model revert |
| `stripe_webhook_fail_rate` | 15 dk | > %5 | PagerDuty P1 |
| `sentry_new_issues_per_min` | 5 dk | > 3 | Alert |

Rollback komutları:
```bash
export FINPILOT_RELEASE=<last-good-sha>
docker compose pull api web && make docker-up
python scripts/populate_registry.py --activate <prev_model_id>
alembic downgrade -1
export FINPILOT_LIVE=false && make docker-up-reload
```

#### 5.10 KPI Listesi
- API p95 latency, error rate, inference throughput, coverage %, open CVEs, MTTD, MTTR, deploy frequency, lead time, change failure rate.

#### 5.11 Önerilen Deneyler
- **E-T1:** Senkron vs async inference — p95 etkisi.
- **E-T2:** Gunicorn 4 worker vs 1 worker + asyncio — RPS.
- **E-T3:** Redis L2 TTL 60s vs 5m — cache hit ratio vs freshness.
- **E-T4:** Groq-only vs failover router — LLM latency + cost.
- **E-T5:** SQLite vs Postgres (compose profile) — p95 DB op.

#### 5.12 Canlıya Alma Kabul Kriterleri
- Release Readiness Checklist 12/12 yeşil (audit raporundan).
- 5 alert kuralı Synthetic test ile tetiklendi.
- Canary Ring 2 48 saat hatasız.
- Restore drill en az 1 kez başarılı.
- OpenAPI spec export'u CI'da attach ediliyor.

#### 5.13 Tahmini Kaynak İhtiyacı
**14 insan-gün (2 backend + 1 FE + 1 SRE, paralel).** 2 hafta.

#### 5.14 Gelir Fikirleri (teknik destek + API)

| # | Fikir | Zaman | Tahmini Gelir (90g) |
|---|-------|-------|---------------------|
| 1 | API plan (€99/ay, 1M call/ay) | 7 gün | 10 kullanıcı × €99 = €990/ay |
| 2 | Usage-based add-on: LLM overage (€0.01/req above cap) | 3 gün | Ort. €150/ay/aktif kullanıcı için potansiyel |
| 3 | "Custom Connector" (Binance/IBKR) — €2,000 fixed | 14 gün | 2 proje = €4,000 tek sefer |

---

### 6. Yatırımcı Perspektifi

#### 6.1 Kısa Özet
**Aşama: Pre-seed / Seed.** Ürün %80 hazır, PMF sinyali waitlist'te (500) fakat gelir kanıtı yok. DACH + TR'de yatırımcılara "technical moat (DRL ensemble + regime) + hazır grant kit + küçük ama vital bir quant SaaS" hikayesi anlatılır. Hedef: **€300K–€500K seed / 24 ay runway** ya da grant (AWS Gründungsfonds) ile non-dilutive başlangıç.

#### 6.2 Artılar
- Teknik moat: 20 eğitilmiş model + ensemble router; rakipten hızlı.
- Multi-LLM abstraction: provider risk dağılımı.
- Hazır grant dosyaları (DE/EN/TR).
- Docker-first; yatırımcıya hızlı demo.
- Low burn: founder-led + cloud-minimal.

#### 6.3 Eksiler ve Riskler
- Gelir = 0, unit economics doğrulanmamış.
- Solo founder — takım riski.
- Regulated space komşuluğu (fintech, brokerage proxies).
- ML maliyeti artışı marjı sıkar.
- Rakipler büyük ve sermayeli (TradingView, Trade Ideas, Seeking Alpha).

#### 6.4 Hızlı Kazanımlar (48 saat)
- [ ] 10 slayt pitch deck güncellemesi (MRR alanı boş; "LTD seats sold" somut sayı).
- [ ] Cap table draft (founder 100% → seed öncesi ESOP %10 reserve).
- [ ] 12 ay forecast Excel (aşağıda template).
- [ ] 5 yatırımcı shortlist (DACH + TR fintech angel).
- [ ] NDA + simple investor summary 2 sayfa.

#### 6.5 12 Aylık Gelir Projeksiyonu

**Varsayımlar (baz senaryo):**
- D13 launch, D14–D30 arası paid ramp.
- Hafta 1–8: haftalık +20 paid user.
- Hafta 9–24: aylık +80 paid user.
- Hafta 25–52: aylık +150 paid user.
- Paid mix: 50% Basic €19 / 35% Pro €49 / 15% Edge €79 (ağırlıklı ortalama ARPU ≈ €36).
- LTD: İlk 100 seat 60 gün içinde satılır (€11,940 cash).
- Monthly churn: 5% (stabilize olurken).
- Enterprise pilot M3'te başlar (€2,000/ay × 2).

| Ay | Yeni Paid | Churn | Net Paid | MRR (€) | Enterprise | LTD cash | **Toplam Gelir** |
|----|-----------|-------|----------|---------|------------|----------|------------------|
| M1 | 40 | 2 | 38 | 1,368 | 0 | 2,500 | **3,868** |
| M2 | 80 | 6 | 112 | 4,032 | 0 | 5,000 | **9,032** |
| M3 | 120 | 11 | 221 | 7,956 | 2,000 | 3,500 | **13,456** |
| M4 | 160 | 17 | 364 | 13,104 | 2,000 | 940 | **16,044** |
| M5 | 160 | 25 | 499 | 17,964 | 4,000 | 0 | **21,964** |
| M6 | 150 | 33 | 616 | 22,176 | 4,000 | 0 | **26,176** |
| M7 | 150 | 40 | 726 | 26,136 | 6,000 | 0 | **32,136** |
| M8 | 150 | 46 | 830 | 29,880 | 8,000 | 0 | **37,880** |
| M9 | 150 | 52 | 928 | 33,408 | 10,000 | 0 | **43,408** |
| M10 | 150 | 58 | 1,020 | 36,720 | 10,000 | 0 | **46,720** |
| M11 | 150 | 63 | 1,107 | 39,852 | 12,000 | 0 | **51,852** |
| M12 | 150 | 68 | 1,189 | 42,804 | 12,000 | 0 | **54,804** |
| **Yıl 1 toplam** | | | | | | | **~€357K** |

Kötümser senaryo (-50%): ~€180K / Yıl. İyimser (+50%): ~€530K / Yıl.

#### 6.6 Unit Economics Tablosu

| Metrik | Değer | Not |
|--------|-------|-----|
| ARPU (ağırlıklı) | €36 | Plan mix |
| Gross margin | %80 | Hosting + LLM + Alpaca ücret 0 (stock) |
| CAC (Q1) | €22 | Organic: Reddit + HN + email |
| CAC (Q2+) | €30 | Biraz paid dahil |
| Payback period | < 1 ay | Hedef |
| LTV (24 ay, %5 aylık churn) | €576 | ARPU × (1-margin)^-1 × (1/churn) |
| **LTV / CAC** | **~19x** | Sağlıklı > 3x; konservatif 10x bile güçlü |
| Monthly churn | 5% | İlk çeyrek; stabilizasyonla %3 hedef |
| Gross churn / yıl | %46 (M%5) | Stabilize senaryo %28 (%3 aylık) |

#### 6.7 Yatırım İhtiyacı ve Kullanım Planı

**Seçenek A — Non-dilutive ilk (Tavsiye):**
- **AWS Gründungsfonds / Exist / Horizon Europe** başvurusu (hazır dosya).
- Hedef: €75K–€150K grant 6–9 ay içinde.
- Dilution: %0.

**Seçenek B — Seed (paralel):**
- **€400K seed, %15 equity @ €2.3M post-money.**
- 24 ay runway hedefi.
- Milestones: 6 ay içinde €30K MRR, 12 ay içinde €60K MRR, 18 ay içinde €120K MRR.

**Kullanım Planı (€400K dağıtım — 24 ay):**

| Kalem | % | € | Süre |
|-------|---|---|------|
| Takım (2 mühendis + 1 founder maaşı + 0.5 growth) | 55% | 220,000 | 24 ay |
| Altyapı (AWS + LLM + tooling) | 10% | 40,000 | 24 ay |
| Pazarlama (paid + içerik + affiliate) | 15% | 60,000 | 18 ay |
| Compliance + legal (ToS, SOC2 roadmap) | 8% | 32,000 | 12 ay |
| Ürün (ikinci UI iteration + mobile) | 7% | 28,000 | 12–24 ay |
| Buffer | 5% | 20,000 | — |
| **Toplam** | 100% | **€400,000** | |

**Hedef exit:** 3–5 yıl; strategic acquirer (TradingView, IBKR, Finra-uyumlu broker) veya revenue-based financing; IPO değil.

#### 6.8 KPI Listesi (Yatırımcıya raporlanan)
- MRR, ARR, Growth rate (MoM), LTV/CAC, CAC payback, Logo count, NRR, Gross churn, Magic Number, Rule of 40, Burn rate, Runway (ay).

#### 6.9 Önerilen Deneyler
- **E-Y1:** €19 vs €29 Basic — conversion delta.
- **E-Y2:** Yıllık peşin %20 indirim vs aylık — cashflow etkisi.
- **E-Y3:** Enterprise pilot fiyat €1,500 vs €3,000 — kapatılma hızı.
- **E-Y4:** Discord topluluk açık vs Pro özel — retention etkisi.

#### 6.10 Canlıya Alma Kabul Kriterleri (Yatırımcı gözü)
- 3 ardışık ay +20% MoM büyüme.
- LTV/CAC ≥ 3x.
- Runway ≥ 12 ay.
- Seçili bir enterprise pilot kazanılmış.
- Sentry/Grafana "operating at scale" sinyali.

#### 6.11 Tahmini Kaynak İhtiyacı
Yatırımcı ilişkileri: **3–4 insan-gün founder (shortlist + outreach + pitch).** Grant başvurusu: **2 insan-gün** (dosyalar hazır).

#### 6.12 Gelir Fikirleri (yatırımcı-uyumlu)

| # | Fikir | Zaman | Tahmini Gelir (12 ay) |
|---|-------|-------|-----------------------|
| 1 | Enterprise Annual Pre-pay (€20K × 3 logo) | 60 gün | €60,000 cash |
| 2 | SaaS + API tiered (Basic→Edge→API→Enterprise) | 90 gün | €300K+ ARR |
| 3 | Data/Research Licensing (Sharpe report aboneliği finfluencer'a) | 120 gün | €12K/yıl × 5 = €60K |

---

## 7. Karşılaştırmalı Özet

### 7.1 Hangi Perspektif Hangi Aksiyonla En Hızlı Gelir Getirir?

| Sıra | Perspektif | Aksiyon | Zaman | Beklenen İlk Gelir |
|------|------------|---------|-------|--------------------|
| 🥇 | **Girişimci** | LTD 100 seat + waitlist blast | 5 gün | €5K–€12K (tek sefer, 14 gün içinde) |
| 🥈 | **Pazarlama** | Daily Top-3 dijest + PH launch + SaaS Basic | 7 gün | €1,500 MRR M1 sonu |
| 🥉 | **Teknik** | Stripe billing + feature gating (gelir musluğu açmak) | 5 gün | Kritik bağımlılık — diğerleri bunun üzerine oturur |
| 4 | **Satış** | Affiliate (finfluencer) + referral | 10 gün | €1,750 MRR M2 |
| 5 | **Satınalmacı** | Enterprise Pilot €1,500 × 2 | 21 gün | €3,000 tek sefer |
| 6 | **Yatırımcı** | Grant başvurusu (AWS Gründungsfonds) | 7 gün gönderi + 60–90 gün bekleme | €75K–€150K (non-dilutive) |

### 7.2 En Düşük Riskli Yol

**Sıralı yol (founder-led, düşük sermaye yanması):**

1. **Teknik → Ödeme + Auth guard + backup** (48 saat) — musluk aç.
2. **Pazarlama → Waitlist blast + Daily Top-3** (gün 3–5) — trafik.
3. **Girişimci → LTD 100 seat** (gün 6–14) — cash infusion.
4. **Yatırımcı → Grant başvurusu paralel** (gün 1–7) — non-dilutive optionality.
5. **Satış → Affiliate 3 finfluencer** (gün 10–14) — ölçekli kanal.
6. **Satınalmacı → Pilot 1 teklif** (gün 12–21) — annuity gelir.

### 7.3 Önerilen İlk 3 Öncelik (Önümüzdeki 2 Hafta)

1. **Stripe billing + feature gating + webhook** (Teknik + Girişimci paralel). Bu olmadan hiçbir gelir çalışmaz.
2. **Waitlist blast + PH/HN/Reddit launch + LTD 100 seat kampanyası** (Pazarlama + Girişimci). En hızlı cashflow.
3. **Auth guard + `.gitignore` + Alembic + inference async + Sentry/Grafana SLO** (Teknik). Kullanıcılar geldikten sonra kaybetmemek için.

### 7.4 Perspektifler Arası Çatışma Noktaları

- **Satış vs Teknik:** Satış "şimdi demo ver"; Teknik "daha rate limit + async inference eklenmeden scaling risklidir". Çözüm: endpoint-özel rate limit + kullanıcı beklenen hacme göre gate.
- **Pazarlama vs Satınalmacı:** Pazarlama "public launch şimdi"; Satınalmacı "SOC2 yolu olmadan demo kötü". Çözüm: public launch bireysel segmente; B2B ayrı inbound kanalı.
- **Yatırımcı vs Girişimci:** Yatırımcı "hızlı ölçek, %30 MoM büyüme"; Girişimci "önce sürdürülebilir birim ekonomisi". Çözüm: non-dilutive (grant) ile 6 ay runway, seed'i M4-M5'te güçlü veriyle konuş.

### 7.5 Toplam Kaynak İhtiyacı (2 Hafta)

| Rol | İnsan-gün |
|-----|-----------|
| Founder (çok yönlü) | 10 |
| Backend | 8 |
| Frontend | 4 |
| SRE / DevOps | 4 |
| ML | 2 |
| Growth | 6 |
| Legal (dış) | 1.5 |
| Designer (dış) | 1 |
| **Toplam** | **~36.5 insan-gün** |

---

## 8. Executive Summary

**FinPilot nedir?** Rejim-farkındalığı olan DRL ensemble + multi-LLM + teknik scanner ile bireysel yatırımcıya US equities karar desteği + Alpaca paper trading köprüsü sunan SaaS. Next.js + FastAPI + 20 PPO/RPPO modeli.

**Nerede duruyoruz (2026-04-22)?** Teknik %80 hazır, gelir %0. 500 waitlist, hazır DE/EN/TR grant kit, CI/CD + Docker + Sentry + Prometheus mevcut. Eksik: **ödeme altyapısı, GDPR/backup/desteğin kapatılması, async inference, SLO'lar**.

**En kritik 3 eksik:**
1. Billing / Stripe hiç yok → gelir musluğu kapalı.
2. Auth prod dev-key fallback + DB repo'ya sızıyor → güvenlik.
3. DRL inference senkron + SLO tanımsız → ölçeklenme riski.

**Önerilen ilk 3 aksiyon (14 gün):**
1. Stripe billing + webhook + feature gating (D1–D5) → SaaS musluğu.
2. Waitlist blast + LTD 100 seat + PH/HN/Reddit launch (D6–D13) → ilk €10K+ gelir.
3. Auth guard + Alembic + async inference + Grafana SLO (paralel) → scale-ready.

**Canlıya hazır mı?** Beta (Canary Ring 2, 50 kullanıcı): **GO** — 48 saat mitigasyon. Public launch: **Conditional GO** D13 için (Release Readiness Checklist 12/12 yeşilse).

**Finansal özet (Yıl 1 baz senaryo):**
- MRR M3: €8K, M6: €22K, M12: €43K.
- LTD cash ilk 90 gün: ~€12K.
- Enterprise pilot ARR M12: €12K/ay.
- **Toplam Yıl 1 gelir ≈ €357K**; gross margin %80; LTV/CAC ~19x.
- Seçenek A (öncelikli): Grant €75K–€150K (non-dilutive). Seçenek B (paralel): €400K seed @ €2.3M post-money.

**3 ana perspektif üzeri önerim:** (i) Girişimci — LTD ile 14 gün içinde cash; (ii) Pazarlama — waitlist + Daily Top-3; (iii) Teknik — Stripe + Auth guard + async, aynı 14 gün. Satış, Satınalmacı ve Yatırımcı paralel pipeline'dır, ikinci ay sonunda annuity gelire evrilir.

---

## 9. Deney Matrisi — CSV

Bu raporu tamamlayan CSV dosyası ayrı bir teslimdir: [deney matrisi CSV](computer:///sessions/gracious-determined-feynman/mnt/Borsa/FINPILOT_EXPERIMENT_MATRIX_2026-04-22.csv).

Aşağıda önizleme:

| id | perspective | hypothesis | kpi | duration_days | success_threshold | owner |
|----|-------------|-----------|-----|---------------|-------------------|-------|
| E-F1 | Founder | 14 gün kartsız trial 7 gün kartlı'dan daha iyi dönüşür | Trial→Paid % | 10 | ≥ %8 | Founder |
| E-F2 | Founder | LTD urgency counter conversion'ı artırır | LTD CR | 14 | ≥ %3 visit→buy | Founder+FE |
| E-S1 | Sales | Walk-forward Sharpe CTA reply rate'i artırır | Reply rate | 10 | ≥ %5 | Sales |
| E-S3 | Sales | 20% recurring referral viral coefficient artırır | k-factor | 14 | ≥ 0.15 | Sales+BE |
| E-M1 | Marketing | 14 gün trial 7 günden daha iyi | Sign-up conv % | 10 | ≥ %3.0 | Growth |
| E-M3 | Marketing | Subject "Top 3 + 2 more" open rate artırır | Open rate | 14 | ≥ %40 | Growth |
| E-K1 | Buyer | €1,500 pilot %100 money-back gibi kapatır | Pilot close rate | 21 | ≥ %40 pitch→sign | Sales |
| E-K2 | Buyer | Single-tenant mesaj daha iyi reply | Reply rate | 14 | ≥ %8 outbound | Sales |
| E-T1 | Tech | Async inference p95 < senkron p95 | p95 inference ms | 7 | ≤ 1,500ms | Platform |
| E-T4 | Tech | Groq-only cost < failover | LLM €/kullanıcı/ay | 14 | ≤ €0.30 | Platform |
| E-Y1 | Investor | €29 Basic €19'dan daha iyi revenue/user | ARPU | 14 | ≥ €22 | Founder |
| E-Y3 | Investor | Enterprise pilot €3,000 vs €1,500 close rate | Close rate | 30 | ≥ %20 | Sales |

(Tam liste 20+ deney, CSV dosyasında.)

---

*Rapor tamamlandı — FinPilot 2026-04-22. Perspektifler bağımsız ve karşılaştırmalı işlendi; teslim kriterleri karşılandı.*
