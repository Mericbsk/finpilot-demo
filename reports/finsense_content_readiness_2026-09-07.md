# FinSense İçerik Hazırlığı — Dış Repo Lensiyle Yeniden Değerlendirme

Tarih: 2026-09-07
Level: A (araştırma; hiçbir kod/config/içerik değiştirilmedi)
Tetikleyici: Kullanıcı düzeltmesi — "projeyi bitirmek" = FinPilot + özellikle **FinSense'in içeriğini çoğaltmak ve kullanıma hazır hale getirmek**
Önceki rapor: `reports/external_repo_review_2026-09-07.md` (teknik altyapı lensi; bu rapor içerik lensi)

---

## 1. Mevcut içerik envanteri (FACT)

| Katman | Mevcut | Hedef/Tanımlı | Doluluk |
|---|---|---|---|
| Sözlük (`distribution/glossary.py`) | **44 terim** | — (sürekli büyür) | — |
| Akademi domain'i (`academy/domains.py`) | **12 domain, 69 modül** | tanımlı | — |
| Yayınlanan ders (`web/public/academy_lessons.json`) | **1 ders** ("Likidite Oranları", financial-analysis) | 69 modül | **%1,4** |
| Akademi ajan altyapısı (`academy/agents/`) | 6 ajan (generator, quality_guard, gap_detector, updater, analytics, personalization) | çalışır durumda | — |

**Kritik bulgu:** Altyapı var, üretim yok. 69 modülün yalnızca 1'i yayınlanmış. İçerik üretim hattı (`orchestrator.run_daily` → gap_detector → content_generator → quality_guard) mevcut ama fiilen çalıştırılmıyor.

**Bottleneck analizi:**
- `content_generator.py` LLM router üzerinden ders üretiyor, JSON parse ediyor, `status="draft"` olarak kaydediyor — ama **kimse tetiklemiyor**.
- `quality_guard.py` 7 boyutlu denetim yapıyor (finansal doğruluk, seviye uygunluğu, pedagojik yapı, dil netliği, örnek kalitesi, quiz kalitesi, kavram bütünlüğü) — ama draft yok, denetlenecek bir şey yok.
- Yani sorun **orkestrasyon tetikleme eksikliği** + **içerik kalıbı zenginliği**, altyapı eksikliği değil.

---

## 2. Repoları içerik lensiyle yeniden değerlendirme

Önceki değerlendirme teknik altyapı lensiydi. Şimdi soru: **"FinSense'in 69 modülünü hızlı, doğru ve kullanıma hazır üretmesine hangi repo yardımcı olur?"**

### Yeniden sıralanmış karar tablosu (içerik lensi)

| Repo | İçerik üretimine katkısı | FinSense'e doğrudan uygunluk | Karar (güncel) |
|---|---|---|---|
| **advaitpaliwal/feynman** | **Yüksek** — `/deepresearch` + `/lit` + `/draft` kalıpları, kaynak-doğrulamalı içerik üretimi | **Yüksek** — her ders "kanıt-doğrulamalı" üretilebilir | **CONFIRMATORY_CANDIDATE** |
| **mksglu/context-mode** | **Yüksek** — 69 modül × kaynak materyal context'i şişirmeden sorgulanabilir | **Yüksek** — büyük araştırma çıktıları context'i tıkamadan ders üretimi | **CONFIRMATORY_CANDIDATE** |
| **THU-MAIC/OpenMAIC** | **Orta** — ders üretim motoru (slayt, quiz, interaktif simülasyon, PBL), LangGraph orkestrasyonu | **Orta** — pedagojik yapı zengin ama bizim `academy/` altyapımızla örtüşür; doğrudan entegrasyon yerine **pedagoji kalıbı referansı** | **HOLD (referans)** |
| **DietrichGebert/ponytail** | Düşük — kod disiplini, içerik üretimi değil | Düşük | HOLD |
| **coreyhaines31/marketingskills** | **Orta** — `content-strategy`, `ai-seo`, `copywriting` skill'leri; FinSense içeriğinin **bulunabilirliği** için | Orta — içerik üretildikten sonra | **HOLD (GTM)** |
| **affaan-m/ECC** | Düşük-orta — `content-engine` skill'i (multi-platform repurposing) var | Düşük | HOLD |
| **Imbad0202/academic-research-skills** | Orta (akademik rigorite) ama **CC BY-NC** | Kullanılamaz | **STOP (lisans)** |
| Gitlawb/openclaude | Yok (IDE aracı) | Yok | HOLD |
| lightpanda-io/browser | Yok (tarayıcı) | Yok | HOLD |
| ruvnet/ruflo | Yok (orkestrasyon) | Yok (bizde var) | HOLD |
| google-research/timesfm | Yok (tahmin modeli) | Yok | BLOCKED |

---

## 3. Değişen ana içgörü

**Teknik lens ile içerik lensi arasındaki fark:**

| Önceki (teknik) | Şimdi (içerik) |
|---|---|
| ponytail en düşük risk / en hızlı ölçüm | ponytail içerik üretmez — kod üretir |
| feynman "araştırma disiplini" | feynman **doğrudan ders içeriği üretir** — `/deepresearch` bir konuyu kaynak-doğrulamalı araştırır, `/draft` onu yazıya döker |
| context-mode "veri verimliliği" | context-mode **69 modüllük araştırma materyalini** context'i şişirmeden sorgulatır |
| OpenMAIC "domain dışı" | OpenMAIC **tam olarak bizim domain'imizde** — ders üretimi, quiz, interaktif simülasyon |

**En önemli yeniden değerlendirme: OpenMAIC.** Teknik lenste "eğitim platformu, bizim değil" demiştim. İçerik lensinde durum farklı: OpenMAIC'in **iki aşamalı üretim hattı** (outline → scene content), **ajan profili üretimi** (her ders için uygun persona), ve **28+ aksiyon tipi** (slayt, quiz, whiteboard, interaktif simülasyon) bizim `content_generator.py`'nin tekil-JSON-şablonundan çok daha zengin. Ama MIT lisanslı ve bizim mevcut `academy/` altyapımızla örtüşür — **doğrudan entegrasyon değil, pedagoji kalıbı olarak ödünç alma** doğru yol.

---

## 4. FinSense'i kullanıma hazır hale getirmek için gerçek yol

Repolar bir "sihirli değnek" değil. Gerçek darboğaz: **69 tanımlı modül, 1 yayınlanan ders, çalıştırılmayan bir orkestratör.**

### Önerilen sıra (hiçbiri dış repo gerektirmez, hepsi mevcut altyapıyı kullanır)

| Adım | Ne | Dış repo katkısı | Level |
|---|---|---|---|
| 1 | **Üretim hattını tetikle:** `AcademyOrchestrator.run_daily()`'yi bir scheduler'a bağla (şu an hiç çalışmıyor) | Yok | B |
| 2 | **Ders kalıbını zenginleştir:** OpenMAIC'in iki aşamalı üretimini (outline → content) ve çoklu bileşen tipini (quiz + flashcard + case study) `content_generator.py`'ye referans olarak al | OpenMAIC (referans) | B |
| 3 | **Kanıt-doğrulamalı üretim:** feynman'ın `/deepresearch` + kaynak-doğrulama kalıbını `quality_guard.py`'ye entegre et — her ders "kaynak: X" taşısın | feynman (kalıp) | B |
| 4 | **Toplu üretim:** 69 modülü batch olarak üret (günde 5 job = 14 gün) — mevcut `run_daily` zaten `max_jobs=5` ile tasarlanmış | Yok | B |
| 5 | **Kalite kapısı:** quality_guard'ın 7 boyutlu denetimini her derse zorunlu kıl (şu an var ama tetiklenmiyor) | Yok | B |
| 6 | **Bulunabilirlik:** marketingskills'in `ai-seo` + `content-strategy` kalıplarını FinSense landing/akademi sayfalarına uygula | marketingskills (GTM) | B |

### Otonom-tamamlama potansiyeli (düzeltilmiş)

**Evet, otonom olarak "içerik üretimi" büyük ölçüde otomatikleştirilebilir** — ama dış repolarla değil, **mevcut altyapının tetiklenmesiyle.** Dış repolar bu süreci hızlandırır ama şart değil:

- **feynman** → her dersin kaynak-doğrulamalı olmasını sağlar (kalite güveni)
- **context-mode** → 69 modülün araştırma materyalini context'i tıkamadan yönetir (ölçeklenebilirlik)
- **OpenMAIC** → ders kalıbını zenginleştirir (pedagojik derinlik)

Ama asıl iş: **orkestratörü çalıştırmak.** Şu an `run_daily` tanımlı ama hiçbir scheduler onu çağırmıyor. Bu tek satırlık bir bağlantı — ve 69 modülün üretimini başlatır.

---

## 5. Dürüst sınırlama

- **İçerik doğruluğu:** LLM-üretimi finans içeriği her zaman insan gözden geçirmesi ister. Quality Guard 7 boyutlu denetim yapıyor ama bu bir LLM denetimi — "hallucinated financial fact" riski sıfır değil. Her yayınlanan ders için insan onayı (Level C) gerekir mi, yoksa quality_guard'ın APPROVED'u yeterli mi? Bu bir governance kararı.
- **Türkçe kalite:** `quality_guard.py` kör nokta olarak "Türkçe gramer sorunlarını İngilizce LLM'ler kaçırabilir" diyor. Türkçe-native bir denetim katmanı gerekebilir.
- **Gerçek örnekler:** Dersler "gerçek piyasa örneği" içermeli diyor — ama bu örnekler LLM'in eğitim verisinden geliyor, güncel olmayabilir. Scanner verisiyle beslenen örnekler (örn. "geçen hafta X hissesi şöyle hareket etti") daha güncel olur ama bu Level B entegrasyonu.

---

## Governance

- Hiçbir production/içerik/config değiştirilmedi.
- Hiçbir ders üretilmedi, hiçbir scheduler tetiklenmedi.
- Bu rapor bir **öneri** — Level B kararlar (orkestratör tetikleme, kalıp zenginleştirme, toplu üretim) Meriç onayı gerektirir.
