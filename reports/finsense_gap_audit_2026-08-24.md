# FinSense Thinking Mirror — Kilitli Sözleşme ↔ Kod Gap Audit (Faz 1)

Durum: DENETİM · 2026-08-24 · Seviye: Level A (salt-okunur analiz; hiçbir kod/veri değişmedi)
Kapsam: `docs/strategy/FinSense_*_v1_2026-08-11.md` kilitli beşlisi (Belge 00 Contract, Belge 01 Thesis, Belge 02 Calibration, Belge 03 VS-01, Belge 04 Gap Audit) + Teknik Ek (TEKNİK TASARIM, karar bekliyor)
Yöntem: Her madde gerçek kod/DB okunarak eşleştirildi. Tahmin yok; kanıt sütunu dosya/satır veya canlı sorgu sonucu taşır.
Hiyerarşi (Belge 03 §0 notuyla): Contract > Thesis > Calibration > VS-01 > Gap Audit/Teknik Ek.
Canlı kanıt: `data/finpilot.db` sorgusu 2026-08-24 — `fs_cases=5`, `fs_outcomes=5`, `fs_predictions=2` (1 smoke + 1 gerçek anonim), `fs_evaluations=2`.

Etiketler: **KARŞILANDI** · **GAP** (sözleşme vaat ediyor, kod sağlamıyor) · **KISMEN** · **ERTELENDİ** (kilitli belgenin kendisi bilinçli ertelemiş — gap değil) · **BELGE-ÇELİŞKİSİ** (iki kilitli metin farklı şey söylüyor — CORE-005 gereği açık raporlanır, sessiz çözülmez).

---

## 0. Tek paragraf hüküm

VS-01'in teknik iskeleti (DB şeması, API, immutability, UI akışı, manipülasyon testleri) sözleşmeye **tam uyumlu ve canlıda çalışıyor**. Buna karşılık dört gerçek boşluk var: (1) **API'de look-ahead deliği** — `GET /case/{id}/outcome`, kullanıcı tahmin yapmadan önce de outcome döndürüyor; Contract §47/§48'in hile-engelleme ruhunu deliyor (§6.2'nin beş testi bunu kapsamıyor). (2) **Contract §68 observability event'lerinin hiçbiri yok** — North Star (§61) ve §63 başarı kriteri bu olmadan ölçülemez. (3) **VS-01 §6.3 black-box insan testi (8 soru) hiç yapılmadı** — belge açıkça "bu liste tamamlanmadan VS-01 bitmiş sayılmaz" diyor; VS-01 resmen hâlâ açık. (4) **Kullanıcının kendi prediction geçmişini gördüğü hiçbir yüzey yok** (Contract §51 minimum API: `/users/me/predictions`) — §28 Thinking Mirror v0'ın en basit deterministik cümlesi ("70–79% aralığında 3 değerlendirilmiş tahminin var") bile bu olmadan kurulamaz. Ek olarak bir **belge çelişkisi** (reason zorunluluğu) ve bir **discoverability gap** (homepage → /classroom linki yok, VS-01 §4) raporlanıyor. İki `academy.db` diverjansı (Teknik Ek §0) hâlâ insan kararı bekliyor — bu denetim ona dokunmuyor.

---

## 1. Contract (Belge 00) madde eşleştirmesi

| § | Vaat | Durum | Kanıt |
|---|---|---|---|
| §4–6 | FinPilot = market/outcome truth; FinSense outcome üretmez | KARŞILANDI | `api/routers/reasoning.py` hiçbir outcome hesaplamaz; `scripts/export_resolved_cases.py` `resolved_status_barrier`/`resolved_pct_barrier`'ı verbatim kopyalar; `auth/database.py:385` yorumu LOCK-02'yi kodlar |
| §9–10 | Case Engine, kaynak = `signals_archive` | KARŞILANDI | 5 case, hepsi gerçek `source_signal_id`'li; manuel registry (`CASE_REGISTRY`, §2.3 kriterleri) |
| §11 | Snapshot immutable, T0-only | KARŞILANDI (uygulama katmanı) | Export yalnız sinyal anı alanlarını yazar; hiçbir UPDATE endpoint yok. Not: DB-seviyesi trigger ile zorlama yok — garanti uygulama katmanında |
| §12–14 | Prediction atomu, immutability, event (upsert yok) | KARŞILANDI | `fs_predictions` UNIQUE(anonymous_user_id, case_id); 409; PATCH/PUT endpoint yok; testler: `test_duplicate_returns_409_and_no_second_row` |
| §15–16 | Identity v0 anonim UUID; auth roadmap V1 | KARŞILANDI / ERTELENDİ | `web/src/lib/anonymousUser.ts` (localStorage UUID, SSR-güvenli). `auth_user_id` kolonu şemada yok — VS-01 §1 notu bunu v1'e erteler; kayıt altında |
| §17 | Server doğrular; `committed_at` server üretir | KARŞILANDI | `test_client_supplied_committed_at_is_ignored`, `test_client_supplied_outcome_field_is_ignored` |
| §18–20 | Outcome referansı, durumlar (PENDING/RESOLVED/INVALID/CANCELLED), UP/DOWN/FLAT normalizasyonu | KISMEN | Normalizasyon var (CHECK constraint). Durum modeli farklı: case `status` (open/resolved/archived) + `fs_outcomes` var/yok; INVALID/CANCELLED yok. VS-01 kapsamında yeterli; Contract'ın tam durum modeli kurulmadı |
| §21 | Evaluation (direction_correct, binary_outcome, probability_error signed) | KARŞILANDI | `get_outcome` içinde hesap + `fs_evaluations` persist; `evaluation_version='eval_v1'` |
| §22–26 | Calibration v0 isimlendirmesi; engine v1 N-kapılı; accuracy≠calibration | KARŞILANDI / ERTELENDİ | v0 = `ClassroomPreview.tsx` (session-only, kopya dürüst). Engine v1 = VS-02'ye kilitli erteleme; UI'da Brier/bucket gösterilmiyor (LOCK-05) |
| §27–31 | Thinking Mirror v0 deterministik → v2 AI; AI/deterministic sınırı | ERTELENDİ | Mirror yok (VS-03). AI hiçbir yerde outcome/score'a dokunmuyor — sınır temiz |
| §32–33 | Classroom loop'u: Context→Learn→Think→Predict→Commit→Wait→Reveal→**Reflect** | KISMEN | Kodda Context→Direction→Probability→Reason→Review→Commit→Locked→Reveal var. **"Learn" (gerekli tek concept ekranı) ve "Reflect" (reveal sonrası yansıma/öğrenme adımı) yok** — reveal yalnız doğru/yanlış + reason gösteriyor |
| §34–37 | Quiz=knowledge check; personalization/adaptive | KARŞILANDI / ERTELENDİ | Quiz katmanına dokunulmadı; adaptive VS-04 |
| §38–43 | Yeni tablolar: cases/predictions/outcomes/evaluations (+calibration_snapshots, thinking_snapshots) | KISMEN | İlk dördü `fs_*` olarak var. `calibration_snapshots`/`thinking_snapshots` yok — ilgili motorlar (VS-02/03) ile birlikte ertelendi |
| §44 | Versioning (outcome/eval/cal/thinking) | KISMEN | Yalnız `evaluation_version` var; outcome_version yok (resolver metodu string olarak tutuluyor) |
| §46 | Event model: DB event records yeterli | GAP | Ne event bus ne DB event tablosu var — `PREDICTION_COMMITTED`/`OUTCOME_RESOLVED`/`PREDICTION_EVALUATED` hiçbir yerde kayıt altına alınmıyor |
| §47 | Integrity: hileleri engelle | KISMEN — **GAP içerir** | Değiştirme/duplicate/timestamp/future-data korumaları var. **Ama `GET /case/{id}/outcome` tahmin öncesi herkese açık:** kimliği bilinmeyen bir istemci önce outcome'u okuyup sonra "doğru" tahmini commit edebilir. VS-01 §3 yalnız "resolved yoksa 404" der, "predict etmeden göremez" demez — belgenin kapatmadığı delik, §47/§48 ruhuyla çelişiyor |
| §48 | Look-ahead koruması (T0/T1/T2) | KISMEN | UI akışı commit öncesi outcome göstermez; ama API seviyesinde yukarıdaki delik duruyor |
| §49 | Security v0: anon id, server validation, rate limit, immutable, no client outcome | KARŞILANDI | Global slowapi 60/dk-IP (`api/main.py:72`); router'a özel limit yok (v0 kabul edilebilir) |
| §50 | Privacy: reasoning private, public değil | KARŞILANDI (v0 sınırıyla) | Reasoning hiçbir public yüzeye çıkmıyor; `my_prediction` yalnız UUID bilen istemciye döner (tahmin-edilemez ama korumasız — v0 kabul) |
| §51 | Minimum API: `/users/me/predictions`, `/users/me/calibration`, `/users/me/thinking` | GAP | Bu üç uç da yok. Kullanıcı kendi geçmişini listeleyemiyor; "prediction history" Contract §2'nin YOK listesinden hâlâ çıkmadı |
| §52–53 | Outcome interface = export contract; statik JSON loop'un temeli değil | KARŞILANDI | Read-only `signals_archive` → JSON artifact → idempotent seed deseni |
| §54–56 | VS-01 kapsamı ve dışlananlar | KARŞILANDI | Dışlananlardan hiçbiri sızmadı (Brier dashboard/AI coach/leaderboard/gamification yok) |
| §57–59 | VS-02/03/04 sıralaması | ERTELENDİ | Kapılar: N≥10 bucket, N≥20–30 Brier (Calibration Spec §6) |
| §60–63 | Loop, North Star, PMF soruları, success criteria | KISMEN — ölçülemiyor | Loop kodda var ama **ölçüm yok** (§68 gap'i). North Star "% ≥1 prediction + ≥1 evaluated outcome + return" metriği hesaplanamıyor |
| §65 | Deferred listesi (leaderboard vs.) | KARŞILANDI | `quiz_scores.get_leaderboard()` Calibration'a miras alınmadı; parasal leaderboard yok |
| §66 | Landing contract | KARŞILANDI + GAP | Copy uyumlu (compliance testleri geçiyor). **GAP:** VS-01 §4'ün istediği homepage → `/classroom` "Try a real case" giriş linki hiçbir yerde yok (grep: yalnız classroom içi linkler). Deney 1 P5 de aynı bulguyu üretti: "keşfedilmesi zor" |
| §67 | Compliance: tavsiye değil | KARŞILANDI | UI metinleri "not investment advice" çerçevesinde; yasak dil yok |
| §68 | Observability: 8 minimum event | **GAP** | `CASE_VIEWED/CASE_STARTED/PREDICTION_STARTED/PREDICTION_COMMITTED/OUTCOME_VIEWED/PREDICTION_EVALUATED/CALIBRATION_VIEWED/THINKING_MIRROR_VIEWED` — kodda sıfır iz (grep boş). Classroom'da Plausible çağrısı da yok. Karşılaştırma: RSI-caveat deneyi bu deseni dashboard'da zaten kurdu (`indicator_caveat_shown/feedback`, `dashboard/analysis/page.tsx:300-314`) |
| §69 | Failure modes | KARŞILANDI | Invalid case → 404/400; outcome yok → 404 → "Waiting for outcome"; duplicate → 409; refresh → `my_prediction`; anon-ID reset → dokümante v0 sınırlaması |
| §70–72 | Data/content quality; LLM sınırları | KARŞILANDI | Export doğrulamaları var; bu akışta LLM yok, ihlal yok |
| §74–75 | Test stratejisi + kritik senaryo | KISMEN | Unit+integration+integrity: 31 test geçiyor (`test_reasoning.py`, `test_fs_reasoning_schema.py`). E2E: 2026-08-13 production doğrulaması yapıldı (seed/proxy/reveal). **§6.3 black-box insan testi hâlâ yok** |

---

## 2. VS-01 (Belge 03) acceptance durumu

- **§6.1 temel akış:** KARŞILANDI (kod + 31 test + canlı DB + 2026-08-13 production doğrulaması).
- **§6.2 manipülasyon testleri 1–5:** KARŞILANDI. Not: beş test §47'deki predict-öncesi-outcome deliğini kapsamıyor — yeni bir Test 6 gerekli (öneri, Level B).
- **§6.3 black-box kullanıcı testi (8 soru):** **YAPILMADI — 0 gerçek katılımcı.** Belge dili bağlayıcı: "Bu liste tamamlanmadan VS-01 bitmiş sayılmaz." → **VS-01 resmen hâlâ açık.**
- **§4 homepage giriş linki:** GAP (yukarıda §66).
- **§7 yapılmayacaklar:** ihlal yok.

## 3. Calibration Spec (Belge 02) eşleştirmesi

| § | Vaat | Durum |
|---|---|---|
| §1 isimler | "Engine" yalnız v1+ | KARŞILANDI (kopya "practice", "session only" diyor) |
| §2 probability preset 50–90% | UI uyumlu; API serbest float 0–1 | KISMEN (kabul edilebilir gevşeklik; slider preset, API geniş) |
| §2 `reason` 50–300, **opsiyonel** | Kod: zorunlu, 20–500 | **BELGE-ÇELİŞKİSİ** — VS-01 §2.1 "ZORUNLU, min 20" diyor; Calibration Spec "opsiyonel 50–300" diyor. Kod VS-01'i izliyor. CORE-005: sessiz çözülmedi; hangi metnin güncelleneceği insan kararı |
| §3–4 evaluation + Brier formülü | KARŞILANDI (ham veri; Brier UI'da yok — doğru) |
| §6 sample-size gating | KARŞILANDI (gösterilecek veri zaten yok; gating gelecek motorla birlikte) |
| §9 AI sınırı | KARŞILANDI |

## 4. Thesis (Belge 01) eşleştirmesi

Kısa: NE-DEĞİL listesine kod seviyesinde ihlal yok (sinyal servisi değil, danışman değil, leaderboard yok, psikolojik tanı yok). North Star ölçümü §68 gap'ine bağlı. Core loop'un REVEAL→REFLECT halkası eksik (Contract §32-33 ile aynı gap).

## 5. Canlı veri durumu (2026-08-24, `data/finpilot.db`)

- 5 case / 5 outcome — hepsi `finpilot_barrier`, mixed UP/DOWN, temiz resolved.
- 2 prediction: `smoke-20260811-1719` (test) + 1 gerçek anonim UUID (2026-08-11). **Gerçek kullanıcı trafiği fiilen sıfır.**
- 2 evaluation, `eval_v1`, matematik doğru (signed probability_error).
- `fs_predictions`'ta `auth_user_id` kolonu yok (bilinçli v1 ertelemesi).

## 6. Öncelikli bulgu listesi (öneri sırası — karar Meriç'te)

1. **P0 — Predict-öncesi outcome deliği (Contract §47/§48):** `GET /case/{id}/outcome`'a "önce bu kullanıcının prediction'ı olmalı" kuralı (anonim id'siz isteklere de kapalı). Küçük API değişikliği + yeni manipülasyon testi (Test 6). **Level B** — API davranışı değişir.
2. **P0 — VS-01 §6.3 black-box insan testi:** 5–10 katılımcı, 8 soru. Kod işi değil; operasyonel. Bu yapılmadan VS-01 "bitti" denemez (belgenin kendi kuralı).
3. **P1 — §68 observability:** Classroom akışına 8 event (mevcut RSI-caveat Plausible desenini tekrar kullanır). North Star ölçümünün ön koşulu. **Level B** (kullanıcı yüzüne çıkmaz ama veri toplama başlar — gizlilik metni kontrolü gerekir).
4. **P1 — Homepage → /classroom giriş linki (VS-01 §4):** `ClassroomPreview.tsx`'e "Try a real case" çıkışı. Kullanıcıya görünür metin → **onay gerekir** (Adım 3/8).
5. **P2 — `/users/me/predictions` (Contract §51):** kendi geçmişini görme; §28 Mirror v0'ın ve §33 "Reflect" adımının ön koşulu.
6. **P2 — "Learn" + "Reflect" adımları (§32–33):** reveal sonrası tek deterministik yansıma cümlesi (Mirror v0 metni §28'den). Yeni kullanıcı vaadi içerir → onaylı.
7. **Açık mimari karar (insan):** iki `academy.db` diverjansı (Teknik Ek §0 P0) — bu denetim dokunmadı; ayrı karar oturumu.
8. **Açık belge kararı (insan):** `reason` zorunluluğu — Calibration Spec §2 mi yoksa VS-01 §2.1 mi güncellenecek.

## 7. Erteleme/zincir durumu (Adım 4 gereği)

- **Deney 2 (Collision):** kapı = ≥30 gerçek RSI feedback (Plausible: `indicator_caveat_feedback`). Sayaç repo içinden okunamıyor — harici Plausible sorgusu gerekir; kapı doğrulanmadan Deney 2 ilerlemez (kilitli karar korunuyor).
- **Faz 2 (auth↔etkileşim uçtan uca gerçek kullanıcı doğrulaması):** gerçek kullanıcı trafiği sıfır — bu faz **bekliyor** olarak işaretli; §6.3 testiyle aynı insan-havuzuyla birleştirilebilir.

---

_İlgili: `docs/strategy/FinSense_System_Reality_Architecture_Contract_v1_2026-08-11.md`, `..._Vertical_Slice_Specification_v1_...`, `..._Calibration_Specification_v1_...`, `..._Product_Thesis_v1_...`, `..._MVP_Gap_Audit_2026-08-11.md`, `FinSense_Teknik_Ek_DB_API_UX_2026-08-11.md`, `api/routers/reasoning.py`, `auth/database.py:380-530`, `web/src/app/classroom/**`, `web/src/lib/finsenseApi.ts`, `web/src/lib/anonymousUser.ts`, `tests/test_reasoning.py`, `tests/test_fs_reasoning_schema.py`, `scripts/export_resolved_cases.py`, `docs/2026-08-13-finsense-reasoning-engine-research-v0.1-deney1-divergence.md`._
