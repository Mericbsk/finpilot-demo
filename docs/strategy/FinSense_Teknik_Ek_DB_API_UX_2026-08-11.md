# FinSense Thinking Mirror — Teknik Ek: DB Şema + API Sözleşmesi + Ekran Akışı
Durum: TEKNİK TASARIM (karar bekliyor) · 2026-08-11 · Önceki: `FinSense_MVP_Gap_Audit_2026-08-11.md`
Kaynak: `Borsa/auth/*`, `Borsa/api/routers/*`, `Borsa/web/src/lib/auth.tsx`, `Finsense/academy/*` — hepsi gerçek kod okunarak.

---

## 0. Önce bir düzeltme (dürüstlük)

Bir önceki denetimde *"hiçbir sistemde kullanıcı hesabı/auth yok"* dedim. Bu **yanlıştı** — daha derin baktığımda düzeltiyorum:

- **FinPilot'ta (Borsa) gerçek, üretim-kalitesinde bir auth sistemi var**: `auth/core.py` + `auth/database.py` — `users`/`sessions` tabloları, şifre hash+salt, JWT access/refresh token, `FINPILOT_SECRET_KEY` (dev fallback'i bile var, `auth/core.py:24-44`). API: `/api/v1/auth/{register,login,refresh,me}` (`api/routers/auth.py:82-157`).
- **Web tarafında da çalışan bir React auth katmanı var**: `web/src/lib/auth.tsx` — `useAuth()`, `AuthUser` tipi, localStorage-backed session. Ama yalnız **`/dashboard/*`** sayfalarında kullanılıyor (`profile`, `ai-lab`, `drl` — legacy/premium alan). **Public Ledger sayfası (`page.tsx`, Classroom, DailyDouble) bu auth'u hiç çağırmıyor — tamamen anonim.**

Yani gerçek soru "auth inşa edelim mi" değil: **"Calibration v1, mevcut login'in arkasına mı girsin, yoksa Ledger'ın geri kalanı gibi anonim mi kalsın?"** Aşağıda bunu bir tasarım kararı olarak öneriyorum (§3).

**İkinci düzeltme/yeni bulgu — akademi kodu ikiye bölünmüş:**
`Borsa/academy/` ve `Finsense/academy/` **aynı kodun iki farklı kopyası, ve diverge olmuşlar** — `diff` gösterdi: Finsense'in kopyasında `search_log`/`lesson_views` tabloları var, Borsa'nınkinde yok. Yani **iki ayrı `academy.db` var, biri diğerinden geride**. `api/routers/academy.py` Borsa'nın **kendi** yerel `academy` paketini import ediyor (`from academy.orchestrator import AcademyOrchestrator`) — Finsense'in standalone servisine HTTP ile bağlanmıyor. Bu bir governance-conflict: hangisi otorite? Aşağıda P0 kararı olarak işaretledim, kendim çözmüyorum (CLAUDE.md: "çatışmayı sessizce çözme").

**Üçüncü bulgu — mevcut bir leaderboard mekanizması var, Thesis'le çelişiyor:**
`auth/database.py:867-892` — `QuizRepository.get_leaderboard()` zaten kodlanmış (Sprint 4 E1). Belge 1 §5.5 açıkça *"leaderboard of who makes the most money"* istemiyor — bu quiz-doğruluk leaderboard'ı parasal değil ama yine de "en yüksek skor" çerçevesi. Calibration'a bunu **miras almamalıyız** — bilinçli ayrı tutulmalı.

---

## 1. DB Şema — yeni tablolar (Finsense `academy.db`'de)

Neden Finsense'te: lessons/user_profile zaten orada, concept↔lesson bağı oradan kuruluyor. Case/Prediction bu şemaya eklenir; FinPilot'a yeni bir DB açılmaz.

```sql
-- Case: gerçek veya kurgusal bir karar-anı. FinPilot kaynaklı olanlar üretilmez, İTHAL edilir (bkz. §2).
CREATE TABLE IF NOT EXISTS cases (
    id                   TEXT PRIMARY KEY,        -- "CASE-2026-08-11-NVDA-01"
    source               TEXT NOT NULL,            -- 'finpilot_signal' | 'authored'
    source_ref           TEXT,                     -- FinPilot signals_archive id/ticker+date (source='finpilot_signal' ise)
    concept_slug         TEXT,                     -- terms.ts slug ile gevşek eşleşme (cross-repo, FK değil)
    title                TEXT NOT NULL,
    context              TEXT NOT NULL,            -- markdown: karar anındaki anlatı
    evidence_snapshot    TEXT NOT NULL,            -- JSON: karar anında bilinen veri (hindsight sızıntısı yok)
    decision_timestamp   TEXT NOT NULL,
    horizon_days         INTEGER NOT NULL,
    outcome_rule         TEXT NOT NULL,            -- JSON: {"type":"finpilot_barrier","signal_id":...} | {"type":"direction","threshold_pct":...}
    resolution_timestamp TEXT,
    status               TEXT DEFAULT 'open',      -- open|resolved|archived
    difficulty           TEXT DEFAULT 'intermediate',
    created_at           TEXT NOT NULL
);

-- Prediction: commit sonrası immutable. UPDATE/PATCH endpoint YOK — immutability API katmanında zorlanır.
CREATE TABLE IF NOT EXISTS predictions (
    id             TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,                  -- anonim device-id VEYA auth.users.id (opak string, bkz. §3)
    case_id        TEXT NOT NULL REFERENCES cases(id),
    direction      TEXT NOT NULL,                  -- UP|DOWN|FLAT
    probability    REAL NOT NULL,                  -- 0.0-1.0
    reason         TEXT NOT NULL,
    alternative    TEXT NOT NULL,
    status         TEXT DEFAULT 'committed',        -- committed|evaluated
    committed_at   TEXT NOT NULL,
    UNIQUE(user_id, case_id)
);

-- Outcome: her case için tek satır, FinPilot barrier-resolver'dan İTHAL (yeniden hesaplanmaz).
CREATE TABLE IF NOT EXISTS outcomes (
    case_id            TEXT PRIMARY KEY REFERENCES cases(id),
    actual_direction   TEXT NOT NULL,
    actual_return_pct  REAL,
    resolution_method  TEXT NOT NULL,               -- 'finpilot_barrier' | 'price_horizon'
    resolved_at        TEXT NOT NULL
);

-- Evaluation: deterministik skor + (opsiyonel) AI yorum. AI outcome'ı ASLA belirlemez, yalnız yorumlar.
CREATE TABLE IF NOT EXISTS evaluations (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id        TEXT NOT NULL REFERENCES predictions(id),
    direction_correct    INTEGER NOT NULL,          -- 0/1
    brier_score          REAL NOT NULL,
    error_types          TEXT DEFAULT '[]',         -- JSON, Belge 2 §13 taksonomisi
    ai_feedback          TEXT,
    reflection_question  TEXT,
    evaluation_version   TEXT DEFAULT 'v0',
    created_at           TEXT NOT NULL
);

-- user_profile'a EKLENEN kolonlar (var olan tabloyu genişletiyoruz, yeni tablo değil):
ALTER TABLE user_profile ADD COLUMN direction_accuracy   REAL;
ALTER TABLE user_profile ADD COLUMN avg_confidence       REAL;
ALTER TABLE user_profile ADD COLUMN calibration_gap      REAL;
ALTER TABLE user_profile ADD COLUMN resolved_predictions INTEGER DEFAULT 0;
```

**Neden `user_profile`'ı genişletiyoruz, yeni tablo açmıyoruz:** Gap Audit §2/7'de zaten var olan `weak_spots`/`domain_scores` kabuğunu yeniden kullanma kararına sadıkız — sinyal kaynağı değişiyor (tamamlama % → reasoning doğruluğu), tablo kalıyor.

---

## 2. Case kaynağı — yeniden icat etmeden

FinPilot'un kendi bariyer-resolver'ı (`signals_archive`, triple-barrier) zaten var ve kanıtlanmış. Case'leri Finsense içinde sıfırdan üretmek yerine:

1. Yeni script: `Borsa/scripts/export_resolved_cases.py` — `signals_archive`'dan çözülmüş sinyalleri okur, `evidence_snapshot` (karar anındaki veri) + `outcome` (gerçekleşen) çifti olarak JSON'a yazar.
2. **Aynı desen** zaten var: `academy/export_lessons.py` → `web/public/academy_lessons.json`. Case export'u bu desenin bir kopyası — yeni bir entegrasyon şekli icat etmiyoruz.
3. Finsense tarafında bir `ingest_cases` komutu (mevcut `run.py ingest-sources`'a kardeş) bu JSON'u `cases`+`outcomes` tablolarına yazar.
4. **Canlı HTTP çağrısı YOK** — istek anında FinPilot'a bağımlılık yaratmıyoruz (Finsense'in kendi "FinPilot'a sert bağımlılığı yok" ilkesiyle de uyumlu, `README.md:5`).

---

## 3. Kullanıcı kimliği kararı (öneri, karar bekliyor)

Public Ledger anonim kalmalı (bugünkü ürün de öyle — waitlist var, zorunlu login yok). Öneri:

- **v1 varsayılan:** tarayıcıda üretilen anonim `device_id` (localStorage UUID) — Finsense'in bugünkü çıplak `user_id: str` deseniyle bire bir uyumlu, yeni bir kimlik modeli değil.
- **Opsiyonel yükseltme:** birkaç tahmin sonrası *"Thinking Snapshot'ını hesabına kaydet"* daveti → mevcut `/api/v1/auth/register`+`login` akışına yönlendir (yeni auth YAZMA, var olanı çağır). `POST /academy/predictions/claim` (anon_id → auth.users.id merge) — **P2, v1'e gerekmez.**
- Bu, "signup duvarı görmeden dene, değer görünce kaydol" deseni — bugünkü waitlist/Ledger felsefesiyle tutarlı.

---

## 4. API Sözleşmesi (`Finsense/academy/api.py`'ye eklenecek)

| Yöntem | Yol | İş | Not |
|---|---|---|---|
| GET | `/academy/case/today` | Bugünün Case'i — **outcome/grade alanı YOK** | "Observe" ekranının verisi |
| POST | `/academy/case/{case_id}/predict` | `{user_id, direction, probability, reason, alternative}` | Aynı user+case için ikinci istek **409** (immutability — UPDATE endpoint yok, olmayacak) |
| GET | `/academy/case/{case_id}/outcome` | Sonuç + (varsa) kullanıcının kişisel değerlendirmesi | `resolution_timestamp` geçmeden **404** |
| GET | `/academy/thinking-snapshot/{user_id}` | Agregat profil: direction_accuracy, avg_confidence, calibration_gap, `sample_size_label` (Belge 2 §8 kuralı) | |
| POST | `/academy/predictions/claim` | anon→auth id birleştirme | **P2, deferred** |

**Değişmeden kalanlar:** `/academy/lesson/{id}`, `/academy/dashboard/{user_id}`, `/academy/onboard`, `/academy/status` — quiz/ders katmanı dokunulmuyor.

**Web tarafı proxy:** yeni bir proxy kurmuyoruz — `web/src/app/py-api/[...path]` zaten backend'e genel bir passthrough (`api/quotes` ve benzer yerlerde kullanılan desen); yeni uçlar otomatik bu yoldan geçer.

---

## 5. Ekran akışı → gerçek bileşen eşlemesi

Belge 3'ün 9 ekranı, mevcut Borsa web'e şöyle oturur:

| # | Ekran | Yeni mi / mevcut mu | Kanıt / not |
|---|---|---|---|
| 1 | Classroom Home | **NEW** `web/src/app/classroom/page.tsx` | Bugünkü `ClassroomPreview.tsx` (homepage) buraya link veren bir teaser'a döner — `FullEditionTeaser`'ın `/demo`'ya link verdiği desenin aynısı |
| 2 | Case Context (Observe) | **NEW** `CaseContext.tsx` | `/academy/case/today`'i `py-api` proxy üzerinden çeker |
| 3 | Probability | **NEW ama desen VAR** | Bugünkü Calibration v0'daki A/B/C buton grubu (`ClassroomPreview.tsx` `GRADES.map`) — aynı etkileşim deseni, farklı veri |
| 4-5 | Reasoning + Alternative | **NEW** form adımları | — |
| 6 | Commit | **NEW ama desen VAR** | Bugünkü `revealed`/kilitleme state mantığı (`ClassroomPreview.tsx` `handleReveal`) doğrudan taşınabilir |
| 7 | Outcome (Reveal) | **NEW** route, `case_id` parametreli | `/academy/case/{id}/outcome`'u polling/refresh ile çeker |
| 8 | Thinking Mirror | **NEW ama mantık VAR** | Bugünkü `verdict` karşılaştırma metni (eşleşti/daha-iyimser/daha-temkinli, `ClassroomPreview.tsx`) — persist edilen versiyona aynen taşınır |
| 9 | Thinking Snapshot | **NEW** `web/src/app/classroom/snapshot/page.tsx` | `/academy/thinking-snapshot/{user_id}` |

**Önemli ayrım — karıştırmayalım:** Bugünkü Calibration v0 (homepage, FinPilot Grade'ini tahmin et) ile bu yeni Case akışı (çok-günlük ufuklu yön tahmini) **iki farklı ürün.** Görsel "commit→reveal→verdict" bileşen deseni ortak (`useCommitReveal` gibi paylaşılan bir hook'a çıkarılabilir), ama semantik olarak ayrı — biri FinPilot'un kendi çıktısını tahmin ediyor (anlık), diğeri piyasanın ne yapacağını tahmin ediyor (ufuklu, çözülmesi zaman alıyor). İkisini tek ekranda birleştirmeye çalışmak kafa karıştırır.

---

## 6. Güncellenmiş P0 listesi (önceki denetimin §4'ünü değiştiriyor)

Önceki dokümanda P0 "auth kararı + case türetilebilirliği" idi. Netleştirdim:

**P0:**
1. Kimlik modeli kararı — §3'teki anonim-varsayılan öneriyi onayla/değiştir (Level B, ucuz karar).
2. `Borsa/academy/` vs `Finsense/academy/` diverjansı — hangisi otorite, nasıl senkron kalacak (Level B/C — mevcut governance sürecine uygun, ben tek başıma çözmüyorum).
3. `export_resolved_cases.py` ile ilk 20-30 case'in gerçekten `signals_archive`'dan üretilebilir olduğunu doğrula (veri var mı, evidence_snapshot hindsight-temiz kurulabiliyor mu).

**P1:** `cases`/`predictions`/`outcomes`/`evaluations` tabloları + 3 yeni endpoint + Case Context/Probability/Reasoning/Alternative/Commit ekranları.

**P2:** Outcome/Thinking-Mirror/Snapshot ekranları, `predictions/claim` (anon→auth merge), AI evaluation katmanı.

---

_İlgili: `FinSense_MVP_Gap_Audit_2026-08-11.md`, `auth/core.py`, `auth/database.py`, `api/routers/auth.py`, `web/src/lib/auth.tsx`, `web/src/components/ledger/ClassroomPreview.tsx` (bugünkü Calibration v0)._
