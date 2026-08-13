# FinPilot Araştırma Programı — Bağımsız Bilimsel Red-Team İncelemesi

Tarih: 2026-08-12
Rol: Research Red Team + Scientific Review Board (bağımsız)
Seviye: Level A — araştırma/metodoloji değerlendirmesi. Bu rapor hiçbir üretim kuralı, score ağırlığı, TP/SL, entry/exit, sizing veya yatırım tavsiyesi önermez.

## Kapsam ve dürüst sınırlama (Kural 7 — INSUFFICIENT_DATA yerine susma)

Bu inceleme aşağıdaki ham materyale dayanıyor:
- `docs/governance/decision-log.md` (734 satır, tam okundu).
- Bu oturumun kendi bu-hafta üretimi: `rigor_upgrade_concentration_atr.py`, `lottery_gap_reweight_test.py`, `catastrophe_subset_test.py`, `extension_cap_test.py`, `reverse_ranking_closure.py` ve bunların çıktıları (tam okundu / bağımsızca yeniden çalıştırıldı).
- Paralel süreç (repo üzerinde eşzamanlı çalışan başka bir ajan/oturum) tarafından 2026-08-04→08-12 arası üretilen `reports/` altındaki ~55 dosyadan şu 6'sı TAM okundu ve kısmen bağımsız doğrulandı: `master_audit_application_2026-08-12.md`, `research_program_end_to_end_2026-08-12.md`, `production_candidate_validation_2026-08-12.md`, `high_rvol_deep_audit_2026-08-12.md`, `correct_order_protocol_2026-08-10.md`, `winner_anatomy_2026-08-11.md` (kısmi).
- CSV/JSON şeması: `data/backtest_out/full_universe_enriched.csv`, `edge_recheck.csv`, `price_cache_adjusted_integrity_audit_2026-08-07.json`, `price_cache_integrity_audit_2026-08-11.json` (485 flagged sembol), `master_audit_battery_2026-08-12.json`.
- Üretim sözleşmesi: `scanner/features.py` (lottery_factor, overnight_gap_factor tanımları), `scanner/evaluate.py` (score bileşenleri).

**Dürüstçe İTİRAF edilen sınır:** repo'da bugüne kadar 60+ rapor dosyası, 60+ araştırma script'i ve 90+ JSON artifact üretilmiş. Bu incelemede TÜMÜ tek tek ham veriden yeniden türetilmedi — bu, tek oturumda gerçekçi değil. Bunun yerine üç kaynak çapraz-doğrulandı: (1) bu oturumun kendi bağımsız rigor-testleri (gün-kümeli + blok-bootstrap + matched-random + null-kontrol standardıyla YENİDEN HESAPLANDI), (2) paralel sürecin en yeni (2026-08-12) kendi-kendini-denetim raporları (okundu, iki tanesinin sayısal iddiası — D20 %86.9, E22 null-kalibrasyon — bağımsız kodla yeniden üretildi ve TEYİT edildi), (3) 2026-08-04→10 arası eski bataryalar (memory + decision-log üzerinden, ÖNCEDEN bu programda bağımsızca doğrulanmış). Aşağıdaki her tablo satırında kaynak ve doğrulama-durumu ayrı sütunda belirtilmiştir. Bağımsızca yeniden koşulmamış hiçbir iddia "FACT" etiketiyle sunulmuyor.

---

## 1. EXECUTIVE VERDICT

1. **İlk soru muhtemelen yanlış kuruldu.** "Score hangi hisse yükselecek tahmin ediyor mu" sorusu artık en az **7 bağımsız yoldan** negatif (R1, Mirror L4, P0-P3, bu oturumun c2c_5d testi, entry_ok root-backtest %42,5 vs %41,6 lift 1.021, bu raporun kendi B5 çapraz-testi, production_candidate_validation). Sekizinci bir tekrar sıfır yeni bilgi üretir.
2. **En güvenilir negatif bulgu:** score, gelecek getiriyi değil GEÇMİŞ extension'ı ölçüyor (past-5g ρ=0,376 vs forward ρ=0,013-0,011 arası, 4 bağımsız ölçümde tutarlı; `dist_52w_high` ile ρ=0,667). Bu artık EVIDENCE seviyesinde, tartışmaya açık değil.
3. **İkinci en güvenilir negatif bulgu:** seçim katmanı (`entry_ok`) rastgeleden istatistiksel olarak ayrışamıyor — ama DİKKAT: "seçim zarar veriyor" (kanıtlanmış-negatif) ile "seçim bilgi taşımıyor" (kanıtlanmamış-sıfır) arasındaki fark bu hafta İKİ KEZ yanlış çizildi (aşağıda Madde 4/5) ve doğru çizgi hâlâ "geniş-tabanlı sıfıra-yakın negatif, tek bir mekanizmaya indirgenemez"dir.
4. **Kendi hatam, alenen düzeltildi:** dün "felaket alt-kümesi (148/485 flagged sembol) eligible-negatifliğini açıklıyor" dedim — bu, ince örneklemde (n=28 satır) ORTALAMAnın tek bir aşırı-uca (EDBL +154.445%) karşı hassasiyetinden kaynaklanan bir artefakttı. MEDYANa geçince ters çıktı: flagged alt-küme medyanı sıfıra yakın, temiz kısım daha negatif. Paralel sürecin C15 bulgusu ("geniş tabanlı") doğru çıktı, benimki yanlıştı. Bu, bu raporun kendi metodolojik ilkesini (mean'i tek başına edge kanıtı kabul etme) ihlal ederek düşülen bir hataydı — ders: BUNDAN SONRA medyan birincil, ortalama ikincil istatistik olsun.
5. **Concentration-limit ve ATR-parity artık İKİ BAĞIMSIZ YÖNTEMLE aynı sonuca ulaştı:** benim matched-random-kontrollü/permütasyon-kontrollü testim VE paralel sürecin production_candidate_validation'ındaki 100-rastgele-kontrol testi — ikisi de "kısıtlama/ATR-ağırlıklandırma HERHANGİ bir portföyde (rastgele dahil) aynı yönde iş görüyor, score'a/seçime özgü değil" sonucuna ayrı ayrı ulaştı. Bu, programın en sağlam çift-teyitli metodoloji-bulgusu.
6. **Tek hayatta kalan zayıf pozitif sinyal:** `lottery_factor` (gün-içi rank-korelasyon ρ=-0,204, null-kontrol≈0, blok-bootstrap CI 0'ı dışlıyor) — ama onu kullanarak düzeltilmiş score bile RASTGELE seçimden anlamlı derecede kötü kalıyor. Yani "gerçek ama yetersiz-güçte-tek-başına" kategorisinde.
7. **En büyük metodolojik risk çözülmedi:** veri-bütünlüğü. 2.047 sembolün 485'i (%23,7) `>%50` fiyat-sıçraması flag'i taşıyıyor (medyan sıçrama %173,58). Bu, corporate-action/reverse-split/veri-hatası ayrımı yapılmadan HER "full-universe" ortalama-tabanlı sonucu kirletme riski taşır (bu hafta somut örnek: high-RVOL "$10.000→$147.297" sonucu 4 tarihin %103'ü açıklamasıyla çöktü).
8. **Yönetişim disiplini hâlâ tekrarlayan bir zayıflık:** bugünkü (2026-08-12) muazzam hacimli çalışma (10+ yeni script, 10+ yeni rapor — high-RVOL serisi, production-candidate-validation, decision-context, budget-battery, research-program-end-to-end, master-audit — TÜMÜ) decision-log.md'ye HİÇ girmemiş (bu raporun kendi 2 girdisi hariç, grep ile doğrulandı). Bu, en az 6. kez tekrarlanan aynı örüntü.
9. **En dürüst ve en iyi-yapılmış artifact bu hafta bulundu:** `high_rvol_deep_audit_2026-08-12.md` — kendi "pozitif" bulgusunu 5 farklı stres-testiyle (en-büyük-4-günü-çıkar, her-5.-günü-al, ±%50/±%20 winsorize) kendi eliyle çökertti. Bu, programın metodolojik olarak ÖRNEK ALINMASI gereken tek belgesi.
10. **Ürün-kimliği sorusu (alpha vs recognition vs reasoning) hâlâ VERİYLE değil VARSAYIMLA yanıtlanıyor** — PR1/PR7 (gerçek kullanıcı görüşmesi) kapısı hâlâ sıfır görüşmeyle kapalı; bu, tüm quant bulgularından bağımsız olarak, bugün programın en ucuz ve en yüksek-bilgi-değerli açık kapısı.

---

## 2. RESEARCH EVIDENCE MAP (kısaltılmış — tam envanter 60+ dosya, aşağıda karar-kritik olanlar)

| # | Deney/dosya | Tarih | Veri kimliği | Örneklem birimi | Hipotez | Pre-reg? | Outcome | Zaman ayrımı | Multi-test riski | Ana sonuç | Robustness | Nihai durum | Doğrulama |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E1 | Strategic Lab R1 | 08-10 | full_universe_enriched (27.386 dedup) | symbol-day | score↔geçmiş/gelecek getiri | Hayır | c2c_5d | tarih-blok bootstrap | Orta | past ρ=0,376, forward ρ=0,013 | 1000-çekiliş bootstrap | **Supported (negatif)** | Bağımsız 2. kez teyit (bu oturum) |
| E2 | root backtest 08-12 | 08-12 | backtest_full_universe-e2e | trade | entry_ok hit-rate | Hayır | hit-rate/lift | yok | Orta | %42,5 vs %41,6, lift 1,021 | yok | **Inconclusive (zayıf)** | Rapor-kaynaklı, bağımsız yeniden-üretilmedi |
| E3 | reverse_ranking_closure.py | 08-10 | full_universe_enriched | symbol-day | alt-%20 composite ranking geri-döner mi | Hayır | c2c/MFE karışık | 4 çeyrek + matched-random | Yüksek | Q1 anlamlı, Q2-Q4 anlamsız/ters | matched-random 3-seed | **Rejected (artefakt)** | Bu oturumda bağımsız kapatıldı |
| E4 | extension_cap_test.py | 08-10 | full_universe_enriched (25.037 tam-pop) | symbol-day | extension→entry_ok nedensel mi | Hayır | c2c5_net | gün-kümeli | Orta | decile monoton değil, cap iyileştirmiyor | tam-popülasyon | **Rejected (hipoteze düştü)** | Bu oturumda bağımsız kapatıldı |
| E5 | rigor_upgrade_concentration_atr.py | 08-12 (bu oturum) | edge_recheck (dedup, felaket-filtreli) | portföy-günü | concentration-limit/ATR-parity score'a özgü mü | Hayır | c2c5_net | blok-bootstrap(5) | Orta | interaksiyon CI 0'ı içeriyor → özgü DEĞİL | matched-random + permütasyon | **Rejected (score'a özgü değil)** | Bu oturumda üretildi, taze |
| E6 | production_candidate_validation 08-12 | 08-12 | full_universe_enriched (43.279 canonical) | portföy-günü | ATR-parity risk-konstrüksiyonu | Hayır | c2c_5d | yok (tüm dönem) | Orta | random-kontrolde de aynı iyileşme (0,365→0,801) | 100 rastgele-kontrol | **Rejected (score'a özgü değil) — E5 ile bağımsız teyit** | Rapor-kaynaklı, yöntem sağlam, spot-check tutarlı |
| E7 | lottery_gap_reweight_test.py | 08-12 (bu oturum) | full_universe_enriched (26.024) | symbol-day | lottery/gap negatif-ağırlık düzeltmesi | Hayır | c2c_5d | gün-içi Fama-MacBeth | Düşük (2 feature) | lottery ρ=-0,204 (CI hariç-0), gap anlamsız | null-shuffle kontrol + blok-bootstrap | **Supported (zayıf, tek)** | Bu oturumda üretildi, taze |
| E8 | catastrophe_subset_test.py (benim) | 08-12 (bu oturum) | full_universe_enriched (43.323) | symbol-day | felaket-alt-kümesi eligible-negatifliğini açıklıyor mu | Hayır | c2c_5d, ORTALAMA-bazlı | blok-bootstrap(5) | Orta | mean-bazlı: evet göründü | HAYIR — outlier'a dirençsiz | **Rejected (kendi hatam, geri çekildi)** | Bu oturumda ÜRETİLDİ ve AYNI GÜN GERİ ÇEKİLDİ |
| E9 | master_audit_battery C15 (paralel) | 08-12 | full_universe_enriched, 485-flagged | symbol-day | aynı hipotez, MEDYAN-bazlı | Hayır | c2c_5d, medyan | leave-one-group-out (8 grup) | Orta | en büyük LOO etkisi +0,33pp — geniş-tabanlı | 8-grup LOO + eşleşik-kontrol | **Supported (geniş-tabanlı)** | Bu oturumda D20 sayısı (%86,9) bağımsız yeniden üretilerek TEYİT edildi |
| E10 | high_rvol_deep_audit | 08-12 | full_universe_enriched | portföy-günü | high-RVOL $10.000 senaryosu robust mu | Hayır | dolar-yolu | 5 stres-testi | Yüksek (bütçe-taraması) | 4 gün %103 açıklıyor, tüm stres-testleri $10.000'in altında | 4 farklı stres senaryosu | **Rejected (tail-driven, robust değil)** | Rapor tam okundu, metodoloji sağlam, iç-tutarlı |
| E11 | Mirror Analysis L4 | 08-10 | full_universe_enriched | symbol-day | en iyi score-quintile içinde eligible vs not | Hayır | c2c_5d | yok | Orta | eligible -%0,20 vs not-eligible +%1,08 | yok | **Supported (negatif, dar)** | Rapor-kaynaklı, yön 3 farklı ölçümle tutarlı |
| E12 | Global FDR hesabı (bu oturum) | 08-12 (bu oturum) | m≈9.754 geçmiş konfig | — | multiple-testing düzeltmesi hiç uygulanmadı | — | — | — | — | Bonferroni |t|>4,56; beklenen şans-pozitifi ~488 | analitik | **FACT (hesap)** | Bu oturumda hesaplandı, doğrulanabilir |
| E13 | Fixed-target grid (3.120 konfig) | 08-05/07 | full_universe | symbol-day | TP/SL grid'de robust kazanan var mı | Hayır | c2c/barrier | WRC/SPA/PBO | Çok yüksek | WRC p=0,74, SPA p=0,78, PBO=0,6 | White RC + Hansen SPA + CPCV | **Rejected (robust kazanan yok)** | Rapor-kaynaklı |
| E14 | Abstention (calibration-frozen) | 08-12 | full_universe_enriched | symbol-day | evidence-quality veto | Hayır (kalibrasyon dondurulmuş) | c2c_5d | train/calib/valid 50/20/30 | Düşük-orta | aktif -%0,047 vs abstain -%3,185 | temporal holdout | **Exploratory candidate (en güçlü aday)** | Rapor tam okundu, double-dip önlenmiş, metodoloji iyi |

**Not:** Bu tablo karar-kritik 14 satırla sınırlı; tam envanter (60+ dosya) `docs/governance/decision-log.md` + `reports/scanner_research_complete_inventory_2026-08-11.md`'de dağınık haldedir ve TEK bir merkezi kayıt-defteri hâlâ yok (bkz. Madde 8, Executive Verdict).

---

## 3. CONTRADICTIONS AND INVALIDATIONS

**Ç1 — Benim "felaket alt-kümesi" bulgum (E8) vs paralel sürecin C15'i (E9): ÇÖZÜLDÜ, benimki geçersiz.** Kök neden: ortalama vs medyan, ve bayat (148) vs güncel (485) flagged-liste. Ders: ince örneklemde (n<30 gün, n<50 satır) ortalama TEK BAŞINA kullanılmamalı.

**Ç2 — İki farklı ATR-parity sayısı, AYNI YÖNDE ama farklı büyüklükte:** Big-Bet-1 (08-10, edge_recheck.csv, dedup'siz): maxDD -%24,3→-%15,9. production_candidate_validation (08-12, full_universe_enriched, dedup'lü): maxDD -%65,26→-%51,70. Büyüklükler tutarsız (farklı veri/dedup/dönem) ama YÖN (ATR-parity drawdown'ı azaltır) ve NİTELİK-SONUCU (score'a özgü değil, generic) iki bağımsız yöntemle AYNI. Çelişki değil — farklı-örneklem, aynı-nitel-sonuç.

**Ç3 — "Eligible kaybediyor" büyüklüğü 5 farklı ölçümde 5 farklı sayı verdi:** P1 battery (-2,01pp), Mirror L4 (-0,20% vs +1,08%), bu oturumun eski c2c_5d testi (-2,39% vs +0,06%, SONRADAN anlamsız bulundu), entry_ok root-backtest (lift 1,021, hemen-hemen-sıfır), master_audit N3 (medyan -0,834%, geniş-tabanlı). YÖN her zaman aynı (eligible ≤ rejected/random), BÜYÜKLÜK hiçbir zaman aynı değil ve çoğu spesifik-sayı kendi rigor-testinde erimiş. **Doğru okuma: yön-tutarlılığı gerçek bir sinyal, ama "kaç puan" sorusu şu an CEVAPLANAMAZ (INSUFFICIENT_DATA) — farklı export/dedup/dönem/outlier-politikası karşılaştırılamaz sayılar üretiyor.**

**Ç4 — "V0" (resolved_pct_t5↔cache-korelasyonu) tarihsel olarak 3 farklı sayı verdi (0,86/0,325/0,55) — hâlâ tek-doğru-değere dondurulmadı.** Bu, E2/V0 kapısının resmen hâlâ açık olmasının nedeni; MFE tanımı (FACT) çözüldü ama "MFE'nin cache'e göre ne kadar şiştiği" sayısı çözülmedi.

**Ç5 — Aynı hipotez en az 4 farklı isimle test edildi:** "score/entry_ok geleceği tahmin ediyor mu" → R1, P0-P3, Mirror L4, entry_ok-root-backtest, bu oturumun c2c_5d testi, master_audit B5 — 6+ tekrar, hepsi aynı yönde negatif, sıfır yeni bilgi 4. tekrardan sonra.

**Ç6 — Eski export ile yeni export kıyaslanamaz:** `full_universe_enriched.csv` bu programın ortasında en az 2 kez sessizce büyüdü (53.859→100.496 satır, 66→85→81/85 gün — decision-log'da 3 farklı satır-sayısı görülüyor). `edge_recheck.csv` (2026-07-31'de dondurulmuş, hâlâ eski) ile `full_universe_enriched.csv` (sürekli büyüyen) üzerinde çalışan testler ASLA doğrudan kıyaslanamaz — Ç2'nin büyüklük-farkının bir nedeni de bu.

---

## 4. WHAT WE ACTUALLY KNOW

**Kanıtlanmış (EVIDENCE, ≥2 bağımsız yöntemle):**
- Score geçmişi ölçüyor, geleceği ölçmüyor (past ρ=0,376 vs forward ρ~0,01-0,013; 4+ bağımsız ölçüm).
- Score `dist_52w_high`'ı (extension) kodluyor (ρ=0,667).
- Concentration-limit ve ATR-parity score/seçime özgü değil, generic portföy-matematiği (E5+E6, iki bağımsız yöntem).
- lottery_factor gerçek, zayıf, negatif ileri-korelasyon taşıyor (ρ=-0,204, null-kontrollü).
- Fixed-target/TP-SL grid'de (3.120 konfig) robust hayatta kalan kazanan yok (WRC/SPA/PBO üçü de reddediyor).
- 2.047 sembolün 485'i ciddi fiyat-sıçraması taşıyor — bu, full-universe ortalama-tabanlı her sonucu kirletme riski taşır (high-RVOL örneğinde fiilen kirletti).
- catalyst_factor tam-evrende ölü feature (sabit '' veya '0.0').

**Kanıtlanmamış ama makul (HYPOTHESIS):**
- Evidence-quality/abstention ayrımı (aktif -%0,05 vs abstain -%3,19) — temporal-holdout'la ilk kez double-dip'siz test edildi, ama bağımsız/harici veri yok.
- Data-quality veto/uyarı katmanı faydalı olabilir — ama corporate-action/provider sınıflandırması yapılmadan "hangi 485 sembolü ne yapacağız" sorusu açık.

**Bilinmeyenler (UNKNOWN/BLOCKED):**
- "Eligible-rejected farkı kaç puan" — Ç3 nedeniyle şu an cevaplanamaz.
- V0/resolved_pct_t5↔cache korelasyonunun tek-doğru-değeri (Ç4).
- Gerçek execution: spread/slippage/impact/ADV/fill-order — hiç gözlenmedi (P2 BLOCKED).
- PIT sembol evreni, delisting, corporate-action provenance — hiç yok (P1 BLOCKED).
- Sektör etiketi gerçek mi proxy mi (%24-doğru corr-tabanlı proxy) — gerçek EODHD fundamentals hiç entegre edilmedi.

**Yanıtlanamaz sorular (mevcut veriyle):**
- "148/485 flagged sembolün her biri corporate-action mı, veri-hatası mı, gerçek mi" — provider-seviyesi doğrulama olmadan cevaplanamaz.
- "ATR-parity/concentration gerçek bir yatırımcı için tradeable mı" — execution-katmanı sıfır olduğu için cevaplanamaz.

---

## 5. ROOT-CAUSE DIAGNOSIS

- **Problem tanımı:** "hangi hisse yükselecek" sorusu artık 6+ bağımsız negatif sonuçtan sonra düşük-bilgi-değerli. Cross-sectional aynı-gün ayrıştırma da (Mirror L4, en iyi quintile İÇİNDE bile eligible<not-eligible) aynı şekilde negatif — yani sorun sadece "mutlak getiri" çerçevesi değil, cross-sectional ranking çerçevesinde de score bilgi taşımıyor.
- **Veri:** iki ayrı, çözülmemiş bütünlük sorunu var: (a) fiyat-sıçraması/corporate-action (%23,7 sembol), (b) export'un kendi içinde tarih-boyunca sessizce büyümesi (Ç6) — ikisi birlikte, geçmiş "kanıtlanmış" sayıların çoğunun neden birbiriyle kıyaslanamaz olduğunu açıklıyor.
- **Outcome:** MFE↔c2c ayrımı artık kod-seviyesinde FACT (çözüldü). Ama "hangi outcome birincil olmalı" sorusu hâlâ AÇIK — c2c_5d (overlap'li, portföy-P&L değil) şu an fiili birincil ama bu, Ç3'ün büyüklük-tutarsızlığının bir nedeni.
- **Score tasarımı:** tek bir sayıda trend/extension/gap/likidite/risk/event karışıyor (kullanıcının orijinal prompt'unun A/C bölümünde önerdiği ayrıştırma doğru bir teşhis) — extension bileşeni DOMİNANT (ρ=0,667 ile dist_52w_high) ve bu, score'un "yeni bilgi" değil "eski hareketin özeti" olduğunu açıklıyor.
- **Benchmark:** SPY-relative, matched-random ve sector-relative testlerin HEPSİ var ama farklı deneylerde farklı alt-kümelerde uygulanıyor; TEK bir standart benchmark-seti hiçbir zaman tüm programa tutarlı uygulanmadı.
- **Execution:** sıfır. Spread/slippage/impact/ADV/fill-order hiç gözlenmedi — P2 kalıcı olarak BLOCKED.
- **İstatistik:** gün-kümeleme + blok-bootstrap + matched-random artık STANDART hale geldi (bu oturumun ve paralel sürecin ikisi de kullanıyor) — bu programın gerçek ilerlemesi. Ama global multiple-testing (m≈9.754) hiçbir zaman tek bir eşik olarak resmileşmedi (E12, hesaplandı ama uygulanmadı).
- **Ürün varsayımı:** "alpha motoru" kimliği veriyle DESTEKLENMİYOR (6+ negatif). "Risk-intelligence/recognition" kimliği kısmen destekleniyor (ATR-parity, abstention, data-quality veto). "Reasoning platform" kimliği hiç TEST EDİLMEDİ (PR1/PR7 sıfır görüşme).

---

## 6. WHY SOME STOCKS APPEAR TO OUTPERFORM — nedensel açıklama ağacı

| Aile | Mevcut veri yeterli mi? | Yetersiz proxy | Gereken yeni veri | En düşük-maliyetli test | Bu bir alpha mı, risk mi, yoksa veri-sorunu mu? |
|---|---|---|---|---|---|
| A. Gerçek bilgi/beklenti değişimi (earnings, guidance, M&A) | Hayır | catalyst_factor ölü feature | Event/haber feed, analyst-revision verisi | catalyst_factor'ü canlı bir event-feed'le yeniden inşa et, tek-değişkenli matched-control test | Muhtemelen alpha (test edilemedi) |
| B. Market/sektör etkisi (beta, rotation, factor) | Kısmen | Sektör etiketi %24-doğru proxy | Gerçek EODHD/GICS sektör verisi | Mevcut proxy ile SPY/IWM/sector-ETF-relative testi (zaten kısmen yapıldı — sektör-trend bulgusu ~58%vs44%, ayrıştırılamadı çünkü n_eff çok küçük) | Risk/context |
| C. Mikro-yapı (liquidity vacuum, gap mechanics, short-covering) | Hayır | rvol/gap_pct zayıf proxy, float/ADV yok | Float, ADV, short-interest (FINRA), spread verisi | float/ADV entegrasyonu + gap-mekaniği alt-küme testi | Risk + kısmen alpha, test edilemedi |
| D. Veri/anomali (split, corporate action, bad print) | **En güçlü kanıtlı aile** | — | Corporate-action feed, immutable snapshot | Zaten kanıtlandı: %23,7 sembol flag'li, high-RVOL sonucunun 4 günü %103 açıklaması | **Veri-kalitesi problemi — bu ailenin payı programın "pozitif" sonuçlarının çoğunda büyük** |
| E. Şans/seçim etkisi (multiple testing, winner selection, overlap-compounding) | Evet, kısmen ölçüldü | — | — | E12 (global FDR) zaten hesaplandı; overlap-compounding high-RVOL denetiminde (E10) somut gösterildi | **Kanıtlanmış — programın "pozitif" bulgularının çoğunun kaynağı** |

**Özet:** Mevcut kanıt, "bazı hisseler daha iyi sonuç veriyor" görüntüsünün BÜYÜK KISMININ D (veri-anomalisi) ve E (şans/seçim/overlap) ailelerinden geldiğini gösteriyor — bu iki aile TEST EDİLDİ ve doğrulandı. A/B/C aileleri (gerçek bilgi, market-beta, mikro-yapı) HİÇ yeterli veriyle test edilmedi; "gerçek alpha yok" sonucu değil, "test edilemedi" sonucu — bu ayrım kritik ve genellikle karıştırılıyor.

---

## 7. NEW QUESTION SET (≤12, kill criterion zorunlu)

| Öncelik | Soru | Neden yüksek bilgi değeri | Gereken veri | Başarı ölçütü | Kill criterion | Etki |
|---|---|---|---|---|---|---|
| 1 | 485 flagged sembolün her biri corporate-action/reverse-split/veri-hatası/gerçek-hareket olarak sınıflandırılabilir mi? | Programın TÜM full-universe ortalama-sonuçlarının güvenilirliği buna bağlı | Provider corporate-action feed veya manuel doğrulama | %90+ sembol sınıflandırılırsa | %50'den azı sınıflandırılabiliyorsa → "temizlenemez veri" kabul edilip flag'li semboller kalıcı dışlanır | Data repair |
| 2 | Eligible-rejected farkının TEK bir tutarlı büyüklüğü nedir (Ç3'ü çöz)? | Şu an 5 farklı sayı var, hiçbiri diğerine indirgenemiyor | Dondurulmuş TEK export, TEK dedup kuralı, TEK outcome tanımı | Blok-bootstrap CI 0'ı dışlayan tek bir sayı üretilirse | CI her zaman 0'ı içeriyorsa → "yön var, büyüklük belirsiz" resmi sonuç olur | Confirmatory candidate |
| 3 | Abstention/evidence-quality ayrımı bağımsız (yeni tarih aralığı) veride korunuyor mu? | Programın en güçlü kalan pozitif aday | Yeni scan-dönemi (mevcut olmayan) verisi | Aktif-abstain farkı yeni dönemde de CI hariç-0 | Fark kaybolursa → temporal-overfitting, ölür | Confirmatory candidate |
| 4 | ATR-parity'nin execution-sonrası (gözlenen spread/slippage ile) net etkisi pozitif mi kalıyor? | Şu an "risk azaltıyor" biliniyor, "net-pozitif" bilinmiyor | Gözlenen spread/ADV/fill verisi | maxDD iyileşmesi cost-adjusted korunursa | Cost-adjusted'da kaybolursa → sadece "teorik" risk-azaltma kalır | Data repair + confirmatory |
| 5 | Gerçek (proxy olmayan) sektör etiketiyle sektör-trend sinyali (~58%vs44%) hayatta kalıyor mu? | Tek OOS'ta hayatta kalan ilk getiri-koşullayan sinyal, ama proxy-sektörle | EODHD/gerçek GICS sektör verisi | Etkin-n≥30 gün, CI hariç-0 | n_eff hâlâ <15 ise → "test edilemez," ölmez ama kilitli kalır | Confirmatory candidate (kilitli) |
| 6 | catalyst_factor canlı bir event-feed'le yeniden inşa edilirse forward-getiriyle ilişkisi var mı? | Şu an ölü feature; hiç gerçek event verisiyle test edilmedi | Haber/earnings/guidance event feed | ρ, null-kontrolden anlamlı ayrışırsa | Ayrışmazsa → "event-farkındalığı olmayan bir scanner" resmi teşhis olur | Yeni veri gerekli |
| 7 | Score'un tek-sayı yapısı (trend/extension/gap/likidite/risk/event) ayrıştırılınca hangi bileşen(ler) gerçekten forward-bilgi taşıyor? | Şu an "score kötü" deniyor ama HANGİ bileşen kötü bilinmiyor (lottery_factor tek istisna) | Mevcut veri yeterli (component-level veri zaten var) | Her bileşen için ayrı Fama-MacBeth + null-kontrol | Hiçbir bileşen CI hariç-0 vermezse → "score'un TÜMÜ gürültü" resmi sonuç | Mevcut veriyle hesaplanabilir |
| 8 | High-RVOL/gap-up/gap-down bulguları corporate-action-temizlenmiş alt-kümede korunuyor mu? | E10 tail-driven olduğunu gösterdi ama TEMİZ alt-kümede henüz test edilmedi | Madde-1'in çıktısı (temizlenmiş sembol listesi) | Temiz alt-kümede robustness-testleri (E10'daki 5 stres-testi) geçilirse | Geçmezse → "sadece veri-anomalisi" kesin teşhis | Madde-1'e bağımlı |
| 9 | Kullanıcı (gerçek, ≥5 kişi) bu listeyi/score'u "faydalı" buluyor mu — tahmin çerçevesi olmadan? | A2 (dikkat-haritası kimliği) hiç test edilmedi; tüm quant sonuçlarından bağımsız en ucuz test | PR1/PR7 görüşme script'i zaten hazır, sadece insan zamanı gerekli | ≥5 görüşmede tekrarlayan olumlu-değer teması çıkarsa | Çıkmazsa → "reasoning platform" tezi de zayıflar | Product MVP |
| 10 | Global FDR eşiği (|t|>4,56) geriye uygulanınca programın "hayatta kalan" bulgu sayısı kaç kalıyor? | E12 hesaplandı ama hiçbir geçmiş bulguya SİSTEMATİK uygulanmadı | Mevcut t-istatistikleri (çoğu zaten kayıtlı) | Tek bir tabloda tüm t-istatistikleri toplanıp eşik uygulanırsa | Sıfır bulgu kalırsa → "programın 2 yıllık pozitif-bulgu envanteri boş" resmi kabul | Mevcut veriyle hesaplanabilir |
| 11 | V0 (resolved_pct_t5↔cache) korelasyonunun 3 çelişen sayısı (0,86/0,325/0,55) hangi metodoloji-farkından kaynaklanıyor? | E2/V0 kapısı bu çözülmeden resmen kapanamaz | Üç ölçümün kodu yan yana (biri zaten izlenemez durumda) | Tek bir dondurulmuş implementasyon + tek sayı üretilirse | Üçü de yeniden üretilemezse → V0 kapısı "kalıcı-belirsiz" olarak kapatılır (BLOCKED, çözülmez değil) | Data repair |
| 12 | Overlap-compounding'in (5-günlük pencerelerin örtüşmesi) programın TÜM "mean" tabanlı sonuçlarına etkisi ne kadar? | E10 tek bir örnekte gösterdi ($147K→$8-10K); genelleşmiş bir düzeltme hiç yapılmadı | Mevcut veri yeterli | Non-overlapping event-portföy metodolojisi standart hale getirilirse | Sonuçlar örtüşmeyen versiyonda da benzer kalırsa → overlap küçük bir risk, ölçüm rahatlar | Mevcut veriyle hesaplanabilir |

---

## 8. 90-DAY RESEARCH RESET

**Durdurulacak çalışmalar:**
- Yeni score-ağırlığı/feature/TP-SL grid araması (fixed-target, barrier-grid, weight-search ailesi) — WRC/SPA/PBO üçü de reddetti, m≈9.754 ışığında yeni tur beklenen-şans-pozitifinden ayrışamaz.
- "Score'u tersine çevirme" veya "score'u başka bir score ile değiştirme" — Mirror Analysis zaten bunu test etti ve reddetti.
- High-RVOL/gap/ATR-rejimi üzerine YENİ full-universe ortalama-tabanlı keşif — veri temizlenmeden (Madde 1) her yeni tur aynı tail-driven-artefakt riskini taşıyor.

**Data repair işleri (öncelik sırayla):**
1. 485 flagged sembolün corporate-action/veri-hatası/gerçek sınıflandırması (Soru 1).
2. PIT sembol evreni + delisting kaydı.
3. Immutable prior-cache snapshot + restatement detector'ın canlıya alınması (kod zaten yazılı, `research/restatement_detector.py`).
4. V0/resolved_pct_t5↔cache korelasyonunun tek-sayıya dondurulması (Soru 11).

**Sadece 1-2 confirmatory aday:**
1. Abstention/evidence-quality veto (Soru 3) — en güçlü, temporal-holdout'la double-dip'siz test edildi.
2. ATR-parity risk-konstrüksiyonu (Soru 4) — ama SADECE execution-verisi eklendikten sonra, "score'a özgü değil" bulgusu (Madde 5) kabul edilerek "generic risk-azaltma aracı" olarak, "alpha kaynağı" olarak DEĞİL.

**Forward shadow tasarımı:** yukarıdaki 1-4. data-repair işleri tamamlanana ve PR1/PR7 kullanıcı-gerçeği netleşene kadar hiçbir pre-registered hipotez (H1 gap-reversal, H2 rvol-inversion, H3 ATR-parity) açılmamalı — bu karar zaten Meriç tarafından onaylanmış protokolle (4-kapı) tutarlı, DEĞİŞMİYOR.

**Ürün MVP deneyi:** PR1 (≥5-8 gerçek kullanıcı görüşmesi, script hazır) — quant bulgularından tamamen bağımsız, en ucuz, en yüksek-bilgi-değerli tek iş.

---

## 9. PRODUCT STRATEGY RECOMMENDATION

| Tez | Bugünkü kanıt desteği | Gereken veri | En büyük risk | En düşük-maliyetli MVP | Dürüst vaat | Ölçülebilir metrik | Yanlış-vaat riski | Savunulabilirlik |
|---|---|---|---|---|---|---|---|---|
| 1. Alpha Engine | **Çok zayıf** — 6+ bağımsız negatif sonuç | Execution + PIT + yeni pre-registered hipotez | Yanlış vaatle kullanıcı zararı | Yok (kanıt yetersiz MVP'ye bile) | Verilemez şu an | — | **Yüksek** | Düşük |
| 2. Market Recognition System | **Kısmi destek** — data-quality veto + ATR-parity + abstention hepsi bu çerçeveye uyuyor | Corporate-action sınıflandırması | "Fark ediyor" ile "tahmin ediyor" karışması | Data-quality flag'i + evidence-quality etiketi kullanıcıya gösterilir | "Olağandışı/riskli yapıları işaretleriz, getiri vaat etmeyiz" | Kullanıcının flag'li durumları doğru tanıması | Orta | Orta-yüksek |
| 3. Market Reasoning Platform | **Hiç test edilmedi** (PR1/PR7 sıfır) | Kullanıcı görüşmesi (veri değil) | Ölçülmesi zor, "daha iyi karar" sübjektif | PR1 görüşme turu | "Belirsizliği ve alternatif açıklamaları görünür kılarız" | Kullanıcının alternatif-açıklama üretme/belirsizlik-ifade-etme davranışı | Düşük (vaat mütevazı) | Bilinmiyor, test edilmeli |

**Bugün için önerilen konumlandırma:** Tez 2 (Recognition) + Tez 3'ün MVP-testi paralel. Tez 1 (Alpha) bugünkü kanıtla YASAKLANMALI.

**Yasaklanması gereken iddialar:** "score gelecekteki getiriyi tahmin eder"; "entry_ok edge sağlar"; "yüksek RVOL/gap fırsat işaretidir"; "MFE gerçekleşen kâr gibi sunulabilir"; "ATR-parity/concentration alpha kaynağıdır" (risk-azaltma aracı olarak sunulabilir, alpha olarak SUNULAMAZ).

**Test edilmesi gereken dürüst vaat:** "FinPilot, piyasada olağandışı/riskli/veri-kalitesi-şüpheli durumları fark eder ve işaretler; hangi hissenin yükseleceğini tahmin etmez." Bu vaadin kullanıcı-değeri PR1/PR7 ile ölçülmeli, quant kanıtla değil.

---

## 10. FINAL DECISION LEDGER

| Başlık | Karar |
|---|---|
| Composite score / finpilot_score, yön-tahmin aracı olarak | **STOP** |
| entry_ok, mevcut haliyle production edge | **STOP** |
| Yeni TP/SL/barrier/weight-search grid araması | **STOP** |
| Concentration-limit / ATR-parity, "score'a özgü edge" iddiası | **STOP** |
| Concentration-limit / ATR-parity, generic risk-konstrüksiyon aracı olarak | **HOLD** (execution verisi gerekli) |
| High-RVOL / gap / ATR-rejimi full-universe keşifleri | **DATA_REPAIR** (Madde 1 çözülmeden HOLD) |
| lottery_factor tek-başına score-düzeltmesi | **EXPLORATORY_ONLY** |
| Abstention / evidence-quality veto | **CONFIRMATORY_CANDIDATE** (bağımsız veri ile) |
| Veri-bütünlüğü (485 flagged sembol sınıflandırması) | **DATA_REPAIR** |
| V0/resolved_pct_t5↔cache tek-sayı dondurma | **DATA_REPAIR** |
| Sektör-trend sinyali (proxy-sektörle) | **BLOCKED** (n_eff yetersiz, gerçek sektör verisi gerekli) |
| Pre-registered H1/H2/H3 confirmatory koşusu | **BLOCKED** (Kapı 1-3 + PR1/PR7 kapanmadan) |
| PR1/PR7 kullanıcı-gerçeği pilotu | **PRODUCT_MVP** — bugün başlatılabilir, veri-bağımsız |
| Alpha Engine ürün tezi | **STOP** |
| Recognition System ürün tezi | **EXPLORATORY_ONLY** → PRODUCT_MVP'ye aday |
| Reasoning Platform ürün tezi | **PRODUCT_MVP** (test edilmemiş, en düşük riskli başlangıç) |
| Decision-log kayıt disiplini (bugünkü 10+ rapor) | **DATA_REPAIR** (governance, acil — Meriç'e bildirilmeli) |

---

*Bu rapor bir üretim onayı değildir. Hiçbir scanner, score, entry/exit, risk, portfolio, publication, broker veya locked-OOS davranışı bu raporla değişmemiştir. Level B/C onayı gerektiren her karar için ayrı, açık Meriç onayı gereklidir.*
