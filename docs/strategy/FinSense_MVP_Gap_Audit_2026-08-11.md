# FinSense MVP → Thinking Mirror — Gap Audit (STEP 4, gerçek kod okunarak)
Durum: DENETİM · 2026-08-11 · Kaynak: `C:\Users\meric\Finsense` (gerçek repo, ZIP gerekmedi — zaten mount'lu) + `Borsa/web/src/components/ledger/` (bugün değiştirilen Calibration v0)
Girdi: Kullanıcının "FinSense Product Thesis v1 / Calibration v0 Spec / Vertical Slice Spec" 3-belgelik taslağı + STEP 4 (MVP Gap Audit) talebi.
Yöntem: Tahmin yürütülmedi — her satır gerçek dosya okunarak dolduruldu (kanıt sütunu).

---

## 0. Tek paragraf hüküm

Bugün üretilen 3 belge **iyi bir düşünce çerçevesi**, ama Vertical Slice spesifikasyonu bir **greenfield ürün** tasarlıyor — mevcut Finsense'i bilmeden. Gerçek repo şunu gösteriyor: Finsense bugün bir **ders üretim fabrikası** (LLM+RAG ile otomatik ders/quiz üreten, kendi kendini besleyen bir content pipeline), **Classroom/Case/Prediction/Outcome/Calibration katmanlarının hiçbiri yok** — tek istisna: bugün *Borsa* web'inde attığımız Calibration v0 adımı (oturum-içi, kalıcı değil). Matristeki 8 katmandan **6'sı NEW**, 2'si (Positioning, kısmen Thinking Profile) MODIFY. En kritik, plan taslağında hiç bahsi geçmeyen bulgu: **hiçbir sistemde kullanıcı hesabı/auth yok** — `user_id` sunucuya güvensiz, doğrulanmamış bir string. Bu, calibration/prediction geçmişini kalıcı kılmanın **önkoşulu** ve şu an eksik.

---

## 1. Kanıt: Finsense bugün ne

`README.md`, `app.py`, `academy/models.py`, `academy/api.py`, `academy/agents/*` okundu.

- **Kendi tanımı** (`README.md:3`): *"Kendi kendini geliştiren, yerel-AI destekli **finansal okuryazarlık sözlüğü**"* — literacy-course çerçevesi kodun kendi belgesinde de yazılı.
- **Mimari**: Offline fabrika (scheduler: boşluk tespiti → üretim → kalite denetimi → yayın) + Online servis (hazır içeriği sunan API). Standalone; FinPilot'a "sert bağımlılığı yok."
- **Veri modeli** (`academy/models.py:41-143`): `lessons`, `lesson_components` (quiz/flashcard/case_study/glossary/cheat_sheet — ama yalnız quiz+flashcard gerçekten üretiliyor, bkz. §4), `user_progress` (quiz_score, feedback, scroll_depth), `user_profile` (domain_scores, weak_spots, streak, engagement_score), `content_jobs`, `agent_logs`, `search_log`, `lesson_views`.
- **Kullanıcı kimliği**: `user_id` her yerde çıplak `TEXT` — ne `academy/api.py`'de ne `models.py`'de doğrulama/oturum/parola var. `grep -ri "auth|login|session|jwt|password"` yalnız 2 RAG kaynak dosyası + şema yorumlarını buluyor — gerçek bir auth katmanı yok.
- **Entegrasyon Borsa web ile**: Tek bağlantı `academy/export_lessons.py` → `web/public/academy_lessons.json` (statik export). Bugün değiştirdiğim `ClassroomPreview.tsx`/`DailyDouble.tsx` bu API'yi **hiç çağırmıyor** — yalnız FinPilot'un kendi `ledgerSnapshot`'ını kullanıyor. Yani şu an **iki ayrı sistem**, tek bağı statik JSON dosyası.

---

## 2. 8 Katman — gerçek koda göre matris

| # | Katman | Mevcut MVP (kanıt) | Thesis'e uygun mu? | Karar | Gerekçe |
|---|---|---|---|---|---|
| 1 | **Positioning** | README: "financial literacy sözlüğü" (`README.md:3`); onboarding soruları da deneyim-seviyesi/hedef odaklı, reasoning değil (`personalization.py:33-64`) | Hayır | **MODIFY** (ucuz) | Yalnız metin/pozisyonlandırma; mekanizma değişmiyor. Bugün Borsa web'de "The Thinking Mirror" başlığını + Classroom kopyasını zaten bu yönde güncelledik — Finsense tarafında README + onboarding metni eşleşmeli. |
| 2 | **Classroom (UI)** | Finsense'te yok. `/academy/browse` var ama statik, salt-okunur HTML liste (`api.py:128-156`). Borsa web'deki "Classroom" bugüne kadar Finsense'e hiç bağlanmadı. | Hayır | **NEW** | Case→Think→Commit→Reveal akışını render edecek gerçek bir arayüz hiçbir yerde yok. Bugünkü Calibration v0 (Borsa web, `ClassroomPreview.tsx`) bunun ilk, küçük, kalıcı-olmayan örneği. |
| 3 | **Case Engine** | Şemada `case_study` bir component type olarak *anılıyor* (`models.py:65`) ama üretim kodunda (`content_generator.py`) yalnız `quiz`+`flashcard` gerçekten yazılıyor — case_study hiç üretilmiyor. `real_example` alanı var ama yalnız statik `{ticker, context}` tek cümlesi (`seed_content_en.py` örnekleri) — zaman damgası, ufuk, çözülme kuralı yok. | Hayır | **NEW** | Case = context + decision_timestamp + horizon + outcome_rule + evidence_snapshot. Hiçbiri yok. **Fırsat:** FinPilot'un kendi `signals_archive`'ı (bariyer-çözümlü, gerçek ticker/tarih/sonuç) muhtemelen sıfırdan vaka yazmaktan çok daha güçlü bir kaynak — kurgusal değil, gerçek. |
| 4 | **Prediction Layer** | `quiz_questions`: tek doğru şıklı çoktan seçmeli (`content_generator.py:69` — `"correct":"A"`), olgusal hatırlama testi. Direction/probability/reason/alternative alanları yok. Commit/immutability yok — `user_progress` yalnız `UPSERT` (`models.py:404-436`, tekrar yazılabilir). | Hayır | **NEW** (REBUILD değil — paradigma farklı: doğru/yanlış vs. olasılıksal tahmin) | Quiz altyapısı (component tablosu, API deseni) iskelesi olarak yeniden kullanılabilir ama veri modeli baştan kurulmalı. **Bugün atılan ilk adım:** Borsa web Calibration v0 — A/B/C tahmin + reveal, ama persist edilmiyor (React state, sayfa yenilenince sıfırlanıyor). |
| 5 | **Outcome / Evaluation** | Finsense'te yok — hiçbir case'in "sonradan ne oldu"su hesaplanmıyor. | Hayır | **NEW için Finsense — ama YENİDEN İCAT ETME** | FinPilot zaten çalışan, deterministik bir outcome engine'e sahip: triple-barrier resolver (`signals_archive`, bariyer-tabanlı resolved_win/resolved_loss — bu oturumun hafızasında da doğrulanan sağlam mekanizma). FinPilot kaynaklı case'ler için Finsense kendi outcome engine'ini yazmak yerine bu resolver'ı okumalı. |
| 6 | **Calibration** | Hiçbir yerde probability alanı, Brier score, confidence bucket yok. | Hayır | **NEW** | Kullanıcının önerdiği spesifikasyon (Belge 2) doğru hedef ama tam hali (Brier + bucket + error taxonomy + AI evaluation) — Prediction (#4) ve Outcome (#5) olmadan inşa edilemez, onlara **gated**. Bugünkü v0 (guess/reveal, oturum-içi sayaç) gerçek "v0" — belgedeki spesifikasyon aslında bizim tanımladığımız v0'dan çok daha ağır, ona **v1 hedefi** demek daha doğru. |
| 7 | **Thinking Mirror / Profile** | `user_profile.weak_spots` şemada var (`models.py:90`) ama `personalization.py` içinde **hiçbir yerde doldurulmuyor** — `_find_weak_domains()` yalnız ders-tamamlama yüzdesine bakıyor (`personalization.py:295-302`), akıl yürütme kalitesine değil. `domain_scores` = tamamlanan ders %'si + eski skorun ağırlıklı ortalaması (`personalization.py:163-180`) — içerik-tüketim profili, reasoning profili değil. | Hayır | **MODIFY şema / NEW sinyal** | Tablo kolonları (weak_spots, domain_scores) yeniden kullanılabilir kabuk; ama besleyen sinyal tamamen yanlış kaynaktan geliyor (tamamlama %'si, tahmin doğruluğu değil). #4+#5+#6 tamamlanmadan bu katman anlamsız kalır. |
| 8 | **Architecture / Data** | İki ayrı, birbirinden habersiz sistem: (a) Borsa/FinPilot — Next.js + FastAPI + kendi DB'si, gerçek piyasa verisi, gerçek bariyer-çözümü, auth yok; (b) Finsense — standalone FastAPI + SQLite `academy.db`, içerik fabrikası, auth yok. Tek bağ: statik `academy_lessons.json`. | — | **KRİTİK BULUNAN GAP** | Hiçbir yerde kullanıcı hesabı yok. `user_id` sunucuya güvenilmeden gönderilen çıplak string (`api.py` — `OnboardRequest.user_id: str`). Plandaki hiçbir doküman bunu önkoşul olarak işaretlememiş; ama kalıcı Prediction/Calibration geçmişi bu olmadan **kimin tahmin ettiğini bile güvenilir şekilde bilemeyiz**. |

---

## 3. En büyük 3 bulgu (planın kaçırdığı)

**1) Auth yok — ve bu, üç belgenin de sessizce varsaydığı bir önkoşul.**
`Prediction.user_id`, `ThinkingProfile.user_id` her yerde var ama kimlik doğrulama hiçbir katmanda yok. Vertical Slice'ı inşa etmeden önce bu ya çözülmeli ya da bilinçli olarak "validasyon için yeterli, üretim için değil" diye kayda geçirilmeli (örn. tarayıcı-yerel anonim id / Telegram user id — mevcut `user_id: str` deseniyle uyumlu, gerçek hesap sistemi değil ama dürüst bir v0 kısıtı).

**2) Outcome Engine'i iki kere yazma riski.**
FinPilot'ta zaten gerçek, kanıtlanmış bir deterministik resolver var (bariyer metodolojisi). Vertical Slice spesifikasyonu (Belge 3, §11) "Outcome Engine" i sıfırdan tasarlıyor — ama FinPilot kaynaklı case'ler için bu engine zaten **var**. En ucuz ve en güvenilir yol: Finsense'in Case'leri FinPilot'un `signals_archive`'ından türetmek, kendi resolver'ını yazmamak.

**3) Belge 2'nin "v0"ı aslında v1.**
Brier score + confidence bucket + error taxonomy + AI evaluation pipeline — hepsi doğru hedefler ama backend + persistence + auth gerektiriyor. Bugün gerçekten sıfır altyapıyla kurabildiğimiz şey (Borsa web, oturum-içi, A/B/C guess/reveal) çok daha küçük. Numaralandırmayı öneriyorum:
- **v0 (bugün canlı):** oturum-içi, kalıcı değil, tek kullanıcı-tek oturum, FinPilot Grade'i tahmin et.
- **v1 (Belge 2'nin tarif ettiği):** persist edilen Prediction/Outcome/Evaluation, Brier score, calibration gap — auth + Case Engine + Outcome Engine önkoşullu.
- **v2+:** AI evaluation, error taxonomy, adaptive Classroom — Belge 1 §10'daki AI/deterministic ayrımı doğru, ama bu iş v1 hacmi biriktikten sonra anlamlı.

---

## 4. Implementation Backlog (P0→P3, gerçek gap'lere göre)

**P0 — Önkoşul (hiçbir vertical slice bunlar olmadan çalışmaz):**
1. Kullanıcı kimliği kararı: gerçek auth mu, yoksa bilinçli-sınırlı anonim id mi (v1 için) — Level B/C karar, şimdi netleştirilmeli.
2. Case veri modeli tasarımı + FinPilot `signals_archive`'ından ilk 20-30 case'in türetilebilirliğinin doğrulanması (gerçek veri var mı, yeterli mi).

**P1 — Prediction + Outcome iskeleti:**
3. Finsense'e `predictions` tablosu (direction/probability/reason/alternative/status) — Belge 3 §9 şeması temel alınabilir.
4. FinPilot bariyer-resolver'ının Finsense'in okuyabileceği bir arayüze (API/export) açılması — yeni resolver yazılmıyor, var olan okunuyor.

**P2 — Calibration v1 + Thinking Snapshot:**
5. Brier score + calibration gap hesaplama (Belge 2 §6-7).
6. `user_profile` şemasının gerçek reasoning sinyalleriyle beslenmesi (bugünkü weak_spots'un yerini alacak).

**P3 — Sonra (validasyon olmadan başlanmaz):**
AI evaluation pipeline, error taxonomy, adaptive Classroom, 20-30 case kütüphanesinin tamamı — Belge 1 §14'ün "explicitly out of scope" listesiyle zaten uyumlu, değiştirmiyorum.

---

## 5. Vertical Slice Readiness (ölçülebilir)

Belge 3 §25'teki teknik acceptance kriterlerinin 8 alt-bölümünden (Case/Prediction/Integrity/Resolution/Evaluation/AI/Thinking Mirror/Classroom/Persistence — 9 madde) gerçek MVP kaç tanesini karşılıyor:

**0/9 tam karşılanıyor.** En yakın olan: Prediction'ın "commit" adımı — bugünkü Calibration v0'da var ama **kalıcı değil** (persistence maddesi başarısız). Case/Outcome/Evaluation/AI/Thinking-Mirror/Adaptive-Classroom sıfırdan.

Bu, kötü bir haber değil — **doğru** haber: üç belge iyi bir hedef tarifi, ama "bugün ne kodlayalım" sorusuna cevap P0 listesindeki 2 önkoşuldan başlıyor, Belge 3'ün 30 ekranından değil.

---

_İlgili: `FinSense_Product_Thesis_v1` (bu oturumda taslak, henüz ayrı dosya değil), `Landing_Denetimi_2026-08-06`, bugünkü `ClassroomPreview.tsx` Calibration v0 değişikliği, `Finsense/academy/models.py`, `Finsense/academy/agents/personalization.py`, `Finsense/academy/agents/content_generator.py`._

**Not (2026-08-11, sonradan düzeltme):** §3.8'deki "hiçbir sistemde auth yok" bulgusu kısmen yanlıştı — FinPilot'ta (Borsa) gerçek bir JWT auth sistemi var, yalnız public Ledger'a değil `/dashboard/*`'a bağlı. Ayrıntı ve düzeltme: `FinSense_Teknik_Ek_DB_API_UX_2026-08-11.md` §0.
