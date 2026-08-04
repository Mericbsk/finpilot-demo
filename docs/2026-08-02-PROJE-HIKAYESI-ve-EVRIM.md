# FinPilot — Projenin Hikâyesi ve Evrimi
### Nasıl başladı, nasıl gelişti, şu an nereye evriliyor (kanıta dayalı çalışma)

Tarih: 2026-08-02 · Kaynaklar: git geçmişi (277 commit, 2025-12-01 → 2026-07-30), tarihli plan/audit dokümanları, `docs/governance/decision-log.md`, iki reponun (Borsa=FinPilot, Finsense=FinSense) yapısal taraması. Bu bir ANLAMA çalışmasıdır — reçete değil; senin paylaşacağın hedef yapı üzerinden planlamaya zemin olması için.

## 0. Bir bakışta zaman çizgisi (git-kanıtlı)
| Ay | Commit | Faz |
|---|---:|---|
| 2025-12 | 13 | Doğuş — demo/prototip |
| 2026-01 | 7 | Sakin dönem |
| 2026-02 | 34 | İlk inşa |
| 2026-03 | 7 | Duraklama |
| 2026-04 | 0 | Ara (commit yok) |
| 2026-05 | 117 | **Büyük inşa patlaması** |
| 2026-06 | 40 | Derinleşme |
| 2026-07 | 59 | Ürünleşme + otonomi + denetim |
| 2026-08 | (henüz) | Meta-katmana evrilme (plan dokümanları) |

## 1. Doğuş — Aralık 2025
Proje bir **Streamlit demosu** olarak başladı: basit bir hisse tarama arayüzü + LLM destekli "insights/terms" (Gemini 1.5→2.0-flash). İlk commit'ler dağıtım (Docker, Streamlit Cloud), çeviri, API anahtarı hata yönetimi. Yani başlangıç: **"AI destekli hisse tarama demosu."** Kimlik henüz yok, ürün henüz demo.

## 2. İnşa patlaması — Şubat–Mayıs 2026 (zirve: Mayıs 117 commit)
Nisan'da hiç commit yok (bir ara), ardından Mayıs'ta 117 commit'lik devasa bir sprint. Bu dönemde demo, **gerçek bir tarama/sinyal motoruna** dönüştü. README bugünkü kimliği yansıtıyor: çok-zaman-dilimli analiz (15d/1s/4s/günlük), teknik göstergeler, sinyal üretimi, Telegram uyarıları, PilotShield risk kontrolü, DRL entegrasyonu.

## 3. Derinleşme — Haziran 2026 (40 commit)
Sinyal **kalitesi ve kapsamı** dönemi: score_engine + evaluate + scheduler; faktör zenginliği (squeeze, EDGAR catalyst, FRED makro rejim); kapsam %12→%80+, 1812 sembol; EODHD fundamentals + canlı haber katalizörü; erken-tespit tier. Aynı ay **FinSense Academy doğdu** (`academy router` commit'i) — eğitim katmanı buradan filizlendi. Auth/oturum sağlamlaştırma da bu dönemde.

## 4. Ürün kimliği + ürünleşme — Temmuz başı 2026
Ürün burada bir **kimlik** kazandı: **"The Morning Ledger × The Open Classroom"** (07-05 Master Tasarım). Gazete metaforu: her sayı hem haber hem ders; arşiv = geçmiş sayılar = vaka dosyaları; **FinSense = gazetenin okul eki**. Compliance omurgası netleşti: **BUY/SELL yok, hedef fiyat yok, getiri vaadi yok — "Grade" dili** ve her ekranda disclaimer. 13 Temmuz'da landing + `/demo` canlıya çıktı (Morning Ledger dönüşümü).

## 5. Otonomi + denetim + governance — Temmuz ortası–sonu 2026
Üç şey aynı anda:
- **Otonomi (Labs):** Alpaca paper-trading otonom execution mimarisi (07-23) — kullanıcıya ASLA çıkmayan iç doğrulama motoru; amaç karne/doğruluk zincirine dürüst outcome verisi üretmek.
- **Denetim yoğunluğu:** 07-15 skor/scanner audit kümesi, 07-23 ReAudit, 07-24 Bölüm 2/3/4 (derin/stabilite/performans) — sistemi ölçme ve sağlamlaştırma.
- **Governance:** AGENTS.md, decision-log, otorite haritası, operasyonel hazırlık; yayın hattı (Telegram brief + karne) sağlamlaştırma; ve **LAUNCH_CHECKLIST** — odak resmen **lansman**a çevrildi (10 ardışık gün brif).

## 6. Şu an: meta-katmana evrilme — Ağustos 2026
Son hareket (bu hafta, henüz commit değil, plan dokümanları): **ortak-beyin/handoff protokolü**, **Buzz → FinPilot-native Control Center**, **FinSense'in yeniden canlandırılması**, ajan orkestrasyonu. Yani enerji, çekirdek üründen **dışarı, "sistemi yöneten bir meta-katman"a** doğru akıyor.

---

## 7. Evrim yönü — okuma
İki şey net görünüyor:

**(a) Değişmeyen omurga (kimlik sabitleri):** compliance-first (Grade dili, BUY/SELL yok), gazete+okul metaforu (Ledger×Classroom), karne/doğruluk zinciri, sabah brief ritüeli, "iç motor karmaşık / dış yüzey sade ve uyumlu" ilkesi. Bunlar Aralık'tan beri güçlenerek sürüyor.

**(b) Kayan yerçekimi merkezi:** Proje sürekli **dışa doğru bir halka daha** ekledi — tarama → faktör zenginliği → otonom execution → academy/eğitim → governance → şimdi control plane/ajan orkestrasyonu. Her halka değerli; ama merkez "tek odaklı ürünü çıkar"dan "giderek büyüyen sistemi + onu yöneten meta-sistemi kur"a kaydı. Somut kanıt: Temmuz'da tanımlanan asıl hedef (lansman, 10 günlük brif serisi) hâlâ ~2/10 iken, enerji en yeni dış halkalara (FinSense, Control Center) akıyor. Bu, tek kişilik bir operasyon için klasik kapsam-genişleme deseni ve muhtemelen yaşanan bunaltının kaynağı.

**Özet cümle:** FinPilot, "AI destekli bir hisse tarama demosu"ndan, compliance-first bir "okuyan gazete" (Morning Ledger × Open Classroom) ürününe olgunlaştı; şimdi ise bu ürünün etrafında bir ajan-orkestrasyon/meta-yönetim katmanına doğru genişliyor. Çekirdek kimlik sağlam; risk, çekirdeği bitirmeden dış halkaların çoğalması.

---

_Sıradaki adım: Meriç'in hedeflediği ANA YAPIYI paylaşması → bu hikâye ve mevcut envanter üzerinden birlikte planlama._
