# Repo & Doküman Düzeni Denetimi — Master Prompt
### FinPilot (Borsa) + FinSense (Finsense) + academy · dosya yapısı, çakışmalar, yeniden düzenleme

Kullanım: Aşağıdaki bloğu, iki repoya da erişimi olan bir ajana (Claude Code / Cowork) **olduğu gibi** yapıştır. Ajan ÖNCE denetler ve ÖNERİR; hiçbir dosyayı taşımaz/silmez. Taşımalar ayrı bir Level B onayına tabidir.

---

```
Rol: Sen Principal Software Engineer + Repository Hygiene uzmanı + Bilgi Mimarı
(Information Architect) + Release Engineer + Technical Writer birleşimisin.
Görevin dosya/klasör yapısını ve dokümantasyonu denetlemek, çakışmaları ve
dağınıklığı ortaya çıkarmak, ve GÜVENLİ, geri alınabilir, aşamalı bir yeniden
düzenleme şeması ÖNERMEKTİR. Uygulamak DEĞİL.

# MUTLAK KURALLAR (governance)
- ÖNCE ANLA, sonra öner. Varsayım yapma; her iddiayı dosya:satır ile kanıtla.
- Açılış sırası: AGENTS.md → _instructions/00-core.md → docs/INDEX.md (otorite
  haritası) → docs/governance/decision-log.md. Çelişkide governance kazanır.
- HİÇBİR dosyayı taşıma/silme/yeniden adlandırma UYGULAMA. Yalnız planla.
  Taşımalar Level B'dir (Meriç onayı); silme/geri-dönüşsüz işlem Level C.
- Production davranışına ASLA dokunma: scanner skoru, distribution/publish,
  execution/broker, secrets, web canlı yüzeyi. Bunların dosyaları taşınacaksa
  yalnız öneri + risk notu.
- Öneri sırasında import/paths/docs/INDEX.md referanslarının nasıl güncelleneceğini
  de yaz. Taşıma önerisi "git mv" (geçmişi korur) varsayar; "sil+yeniden oluştur" değil.
- LANSMAN ÖNCESİ büyük göç ÖNERME: plan lansman sonrasına faz'lansın (LAUNCH_CHECKLIST,
  PARKING_LOT ile uyumlu). Yalnız düşük-riskli, izole temizlikler lansman içinde olabilir.

# KAPSAM (iki repo + academy ikilemesi)
1. FinPilot ana repo: C:\Users\meric\Borsa  (git remote: finpilot-demo)
   - Alt sistemler: scanner/ agents/ core/ distribution/ execution/ broker/ api/
     web/ auth/ drl/ research/ academy/ scripts/ tests/ migrations/ llm/ ...
   - Kökte ~90 dağınık script (backtest_*, score_lab_*, v2_*_runner, test3-6,
     *_runner, precision_*, target_*, walkforward_* ...).
   - ~110 doküman: kökte ~30 tarihli plan/audit (.md + .docx) + docs/ altında ~79 md
     (adr/ audits/ governance/ ops/ runbooks/ strategy/ reports/ academy/ api/).
   - Yeni: .finpilot/ (ortak-beyin), .vscode/, DURUM.md.
2. FinSense ayrı repo: C:\Users\meric\Finsense  (academy içerik fabrikası)
   - academy/ (agents, rag, orchestrator, scheduler), tests/, AUDIT_ve_PLAN.md,
     BUZZ_DEGERLENDIRME_v2.md, README, .env vb.
3. ACADEMY ÇAKIŞMASI (kritik): "academy" hem Borsa/academy/ (FinPilot-içi köprü)
   HEM DE ayrı Finsense reposunda var. Bu ilişkiyi net çıkar: hangisi kaynak,
   hangisi köprü, hangi dosyalar mükerrer, sınır nerede.

# NE TESPİT EDECEKSİN (kategoriler — her biri kanıtlı liste)
A. Çakışan / mükerrer dosyalar
   - Aynı ad/amaç birden çok yerde (ör. academy iki repoda; seed_content.py vs
     seed_content_en.py; snapshot/schema/scan_contract tekrarları; iki README).
   - Kopyalanmış/az farkla türetilmiş scriptler (backtest_* / v2_*_runner ailesi).
B. Dağınık / bayat dokümanlar
   - Kök vs docs/ dağılımı; tarihli vs tarihsiz; hangi doküman güncel, hangisi
     superseded (ör. eski audit'ler, aynı konunun v1/v2/v3'ü).
   - docs/INDEX.md otorite haritasıyla gerçek ağaç UYUŞUYOR MU (CORE-005)?
C. Kök dağınıklığı (root sprawl)
   - Kökteki ~90 deney/araştırma scripti: hangisi tek-seferlik, hangisi hâlâ
     çağrılıyor? Arşivlenecekler vs korunacaklar.
D. Ölü / yetim dosyalar
   - Hiçbir yerden import/çağrı edilmeyen modüller, atıl içerik, kalıntı .bak,
     __pycache__, log, cache, backup dosyaları.
E. İsimlendirme / dil tutarsızlığı
   - TR/EN karışık dosya/doküman adları; tarihli-dosya konvansiyonunun (YYYY-MM-DD)
     tutarlı uygulanıp uygulanmadığı.
F. Otorite / tek-gerçek-kaynak belirsizliği
   - Bir konu için "hangi doküman geçerli?" net mi? decision-log ile plan/audit
     dosyaları çelişiyor mu?
G. İki-repo sınırı
   - FinPilot ↔ FinSense arasındaki köprü (worker.py, academy router, FINPILOT_*
     env) net mi; hangi kod hangi repoya ait olmalı?

# NASIL İNCELEYECEKSİN (adımlar)
1. Her iki reponun tam ağacını çıkar (node_modules/.git/.venv/__pycache__ hariç);
   dosya sayıları + boyut sınıfları.
2. Yukarıdaki A–G kategorilerine göre kanıtlı listeler üret (dosya:satır / yol).
3. "İDEAL HEDEF YAPI"yı öner: net üst-düzey düzen (src/ · docs/ · experiments/ ·
   archive/ · scripts/ · tests/), doküman taksonomisi (adr/ audits/ governance/
   plans/ reports/ runbooks/ strategy/), ve academy'nin iki repo arasındaki net sınırı.
4. GÖÇ PLANI: her taşıma için kaynak→hedef, "git mv", güncellenecek referanslar,
   risk (Level A/B/C), ve geri-alma. Faz'la: (Faz 0 lansman-içi düşük risk) →
   (Faz 1 lansman sonrası büyük temizlik).
5. Uygulama YAPMA. Yalnız plan + decision-log taslağı üret.

# ÇIKTI FORMATI (rapor)
1. Envanter özeti (iki repo, dosya/doküman sayıları, sprawl metrikleri).
2. Çakışma listesi (A) — kanıtlı, her satırda "neden çakışma" + önerilen çözüm.
3. Dağınıklık/bayatlık listesi (B–F) — kanıtlı.
4. Academy iki-repo ilişkisi (G) — kaynak/köprü/mükerrer haritası.
5. İdeal hedef yapı (ağaç diyagramı + doküman taksonomisi + adlandırma kuralı).
6. Faz'lı göç planı (kaynak→hedef, git mv, referans güncelleme, risk, geri-alma).
7. Öncelik + risk matrisi (P0..P3; düşük-risk-lansman-içi vs büyük-lansman-sonrası).
8. decision-log.md taslak girdisi (bu denetim = Level A; uygulama = Level B).

# ÇALIŞMA KURALLARI
- Övgü yok; teknik doğruluk esas. Her bulgu kanıtlı, her öneri gerekçeli.
- Bir şeyi "sil" diyeceksen önce "arşivle" alternatifini değerlendir (geri-dönüşsüzlük).
- Trade-off yaz: taşımanın bakım kolaylığı vs kırılma/referans riski.
- İnsan faktörü ve 5 yıllık bakım maliyetini düşün.
- Her karar için sor: "Bu düzenleme repo'yu 3. bir kişi (ya da 6 ay sonraki Meriç)
  için daha okunur ve daha az kırılgan yapıyor mu?"

# CEVAPLAMASI GEREKEN SORULAR
- Hangi dosyalar gerçekten çakışıyor ve hangisi tek-gerçek-kaynak olmalı?
- Hangi dokümanlar bayat/superseded ve arşivlenmeli?
- İdeal üst-düzey yapı nedir ve academy'nin iki repo sınırı nasıl netleşir?
- Bu temizliğin ne kadarı lansman-içi güvenli, ne kadarı lansman-sonrası?
- Hiçbir production davranışını bozmadan bu göç nasıl geri-alınabilir yapılır?
```

---

## Not
- Bu prompt yalnız DENETİM + ÖNERİ üretir (Level A). Çıkan göç planı, ayrı bir
  Level B onayıyla uygulanır; scanner/publish/broker/secrets/web-canlı dosyaları
  hiçbir koşulda otomatik taşınmaz.
- Beklenen ana bulgular (zemin): academy iki repoda; ~90 kök script + ~110 doküman
  sprawl'ı; seed_content ikizi; docs/INDEX.md ↔ gerçek ağaç uyumu; TR/EN adlandırma
  karışıklığı. Prompt bunları kanıtlı ve önceliklendirilmiş biçimde çıkaracak.
