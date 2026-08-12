# FinSense — Vertical Slice Specification v1 (VS-01)
Durum: LOCKED (2026-08-11, Implementation Gate ile son hâli) · Belge 03 — Belge 00 (Architecture Contract) altında durur.
Soru: **İlk çalışan loop tam olarak nasıl inşa edilecek?** Case #001'i gerçek FinPilot outcome'una kadar götüren dosya/API/DB/UX/acceptance-criteria seviyesinde mühendislik spesifikasyonu.

**VS-01'in kanıtlamaya çalıştığı şey (kilitli çerçeve):** FinSense'in bir kavram öğretmekten öte, kullanıcının gerçek bir piyasa olayı karşısında kendi düşüncesini açıkça ortaya koymasını, bunu ölçülebilir kaydetmesini ve sonradan gerçek sonuçla karşılaştırmasını sağlayabildiği. Başarı ölçütü "ekran güzel mi" değil, zincirin uçtan uca çalışıp çalışmadığı. **Calibration burada hesaplanmaz — VS-01'in işi kalibrasyon için ham veri üretmek.**

---

## LOCK-01..07 — bu belgeye aykırı olamayacak 7 madde

1. **LOCK-01** FinPilot market truth sahibidir.
2. **LOCK-02** FinSense kendi FinPilot-originated outcome resolver'ını yazmaz.
3. **LOCK-03** Case snapshot immutable ve yalnız T0'da bilinen veriyi taşır (canlı fiyat/RSI değil).
4. **LOCK-04** Prediction immutable'dır; ikinci commit `409`.
5. **LOCK-05** VS-01 calibration üretmez; yalnız raw evaluation üretir.
6. **LOCK-06** VS-01 AI'siz tamamlanabilmelidir.
7. **LOCK-07** VS-01'in başarı koşulu UI kalitesi değil, gerçek uçtan uca loop'un çalışmasıdır.

---

## 0. İki açık kararın çözümü

### 0.1 Neden yeni tablolar `academy.db`'de DEĞİL

Gerçek istek yolu: **Tarayıcı → `web/src/app/py-api/[...path]` proxy → Borsa FastAPI (`api/main.py`, `/api/v1/*`) →** router'lar. Web hiçbir zaman Finsense'in standalone servisine (port 8100) doğrudan bağlanmıyor. Borsa'nın kendi `api/routers/academy.py`'si de kendi **yerel, diverge olmuş** `academy` paketini import ediyor (Contract Editör Notu #3).

**Karar:** Yeni tablolar Borsa'nın kendi, üretimde çalışan DB'sine eklenir — `auth/database.py`'nin yönettiği DB'ye. Gerekçe: (a) zaten network-erişilebilir, (b) identity v1 zaten `users.id`'ye referans verecek, (c) academy.db divergence sorununu **çözmeden bypass eder** — o karar ayrı, kendi P0 maddesinde kalır, VS-01'i beklemez.

### 0.2 API namespace

Yeni dosya: **`api/routers/reasoning.py`**, prefix `/api/v1/finsense/*`. `academy.py`'ye dokunulmuz.

---

## 1. DB Şema (Borsa `auth/database.py` — `Database.initialize()`'a eklenecek)

```sql
CREATE TABLE IF NOT EXISTS fs_cases (
    id                   TEXT PRIMARY KEY,
    source_signal_id     TEXT,                     -- FinPilot signals_archive referansı — provenance, salt referans değil
    asset                TEXT NOT NULL,
    event_timestamp      TEXT NOT NULL,
    snapshot             TEXT NOT NULL,             -- JSON, T0-only (bkz. §2.2) — immutable, hiçbir UPDATE endpoint yok
    context              TEXT NOT NULL,             -- markdown anlatı
    horizon_days         INTEGER NOT NULL,
    outcome_rule         TEXT NOT NULL,             -- JSON
    resolution_method    TEXT NOT NULL DEFAULT 'finpilot_barrier',
    status               TEXT DEFAULT 'open',       -- open|resolved|archived — VS-01'de yalnız open→resolved kullanılır
    created_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fs_predictions (
    id                    TEXT PRIMARY KEY,
    case_id               TEXT NOT NULL REFERENCES fs_cases(id),
    anonymous_user_id     TEXT NOT NULL,            -- BİLİNÇLİ İSİM: user_id DEĞİL. v1'de ayrı bir auth_user_id
                                                      -- kolonu eklenecek (nullable, claim akışıyla doldurulur) —
                                                      -- iki kavram baştan karışmasın diye şimdiden ayrı isimlendirildi.
    direction             TEXT NOT NULL,             -- UP|DOWN|FLAT
    probability           REAL NOT NULL,             -- 0.0-1.0 — "seçtiğim direction'ın gerçekleşme olasılığı"
                                                      -- (her zaman "UP olasılığı" değil — bkz. §3.1)
    reason                TEXT NOT NULL,             -- ZORUNLU (aşağıda §2.1 gerekçesi), min 20 karakter
    status                TEXT DEFAULT 'committed',  -- VS-01'de tek değer; ileride evaluated/invalidated eklenebilir, şimdi kullanılmaz
    committed_at          TEXT NOT NULL,             -- sunucu üretir, client asla göndermez
    created_at            TEXT NOT NULL,
    UNIQUE(anonymous_user_id, case_id)
);

CREATE TABLE IF NOT EXISTS fs_outcomes (
    case_id            TEXT PRIMARY KEY REFERENCES fs_cases(id),
    actual_direction   TEXT NOT NULL,                -- FinPilot resolver'dan DOĞRUDAN kopyalanır, FinSense hesaplamaz (LOCK-02)
    actual_return_pct  REAL,
    resolution_method  TEXT NOT NULL,                -- 'finpilot_barrier'
    resolved_at        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fs_evaluations (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id        TEXT NOT NULL REFERENCES fs_predictions(id),
    direction_correct    INTEGER NOT NULL,           -- 1 eğer actual_direction == predicted direction
    binary_outcome       INTEGER NOT NULL,           -- direction_correct ile aynı değer, 0/1 — Brier'in y'si (Belge 02 §3-4)
    probability_error    REAL NOT NULL,              -- SIGNED: probability - binary_outcome (mutlak değer değil — ham veri, yorum yok)
    evaluation_version   TEXT DEFAULT 'eval_v1',
    created_at            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_fs_predictions_user ON fs_predictions(anonymous_user_id);
CREATE INDEX IF NOT EXISTS idx_fs_predictions_case ON fs_predictions(case_id);
```

`fs_` öneki: mevcut `signals`/`quiz_scores` gibi genel isimlerle çakışmasın diye.

**İlişki:** 1 Case → 1 Outcome, N Prediction → N Evaluation. VS-01 pratikte 1 case + 1 (anonim) kullanıcı + 1 prediction ile sınırlı ama şema çoklu kullanıcıyı baştan destekliyor.

---

## 2. Prediction ve Case kontratı — netleştirmeler

### 2.1 `reason` neden zorunlu

VS-01'in amacı yalnız "UP %70" değil, "neden UP %70 düşündün" — Thinking Mirror'ın ham maddesi reasoning metni. Min 20 karakter, gereksiz ağırlaştırmadan (300 karakter üst sınır, opsiyonel).

### 2.2 `snapshot` gerçekten snapshot olmalı — T0-only

**Yanlış** (canlı veri referansı taşır):
```json
{"ticker": "NVDA", "price": "current_price", "rsi": "current_rsi"}
```

**Doğru** (T0 anında donmuş, sabit değerler):
```json
{
  "asset": "NVDA",
  "event_timestamp": "2026-06-12T14:30:00Z",
  "price_at_event": 123.45,
  "signal_score": 71,
  "volume_context": "...",
  "technical_context": "...",
  "market_regime": "...",
  "available_features": {}
}
```

Case oluşturulduktan sonra `snapshot` hiçbir API ile değiştirilemez (LOCK-03) — bu, Thinking Mirror'ın gelecekte "prediction, T0'da bilinenlere dayandı" iddiasını güvenilir kılan tek şey.

### 2.3 Case #001 seçim kriterleri (rastgele seçilmez)

**Zorunlu:** gerçek FinPilot signal · outcome kesin çözülmüş · snapshot mevcut · event timestamp mevcut · outcome rule biliniyor · barrier resolution temiz · veri eksikliği yok · kullanıcıya anlatılabilir.
**Tercih:** aşırı karmaşık olmayan · net bir piyasa olayı · tek asset · orta düzey reasoning gerektiren · hindsight bias yaratmayacak.

Case #001 aynı zamanda ürünün ilk deneysel laboratuvarı — seçim `export_resolved_cases.py`'de elle yapılır, scheduler/otomasyon yok (§6.2 sıra kuralına göre: 1 case → vertical slice → human test → 5 → 10 → automation).

---

## 3. API Sözleşmesi (`api/routers/reasoning.py`, yeni)

| Yöntem | Yol | Body/Params | Davranış |
|---|---|---|---|
| GET | `/api/v1/finsense/case/today` | — | Açık case'i döner. **outcome/grade alanı yok.** Case yoksa `204`. |
| POST | `/api/v1/finsense/case/{case_id}/predict` | `{anonymous_user_id, direction, probability, reason}` | Sunucu: case açık mı, probability 0-1, direction geçerli, `reason`≥20 karakter → `fs_predictions` satırı, `committed_at` **sunucu üretir**. Aynı user+case ikinci istekte **409**. |
| GET | `/api/v1/finsense/case/{case_id}/outcome` | — | `resolved_at` yoksa **404**. Varsa outcome + evaluation. |

### 3.1 `probability`'nin semantiği (kilitli tanım)

> "Bu case'in tanımlanan outcome horizon'unda, **benim seçtiğim direction'ın** gerçekleşeceğine dair subjektif olasılık tahminim X%."

Yani direction=DOWN, probability=0.70 ise bu "DOWN olasılığı %70" demektir, "UP olasılığı %70" değil. `binary_outcome = 1` eğer `actual_direction == direction` (kullanıcının seçtiği), yoksa `0`. Bu tanım UP/DOWN/FLAT'ın hepsinde simetrik çalışır — Belge 02'deki Brier formülünün `y_i`'si budur.

**probability ŞU DEĞİLDİR:** %70 getiri, FinPilot Score, model probability, kazanma garantisi. Bu tanım Belge 01/02'ye de aynen bağlı kalır.

Client asla `committed_at` veya outcome değeri göndermez — sunucu bunları reddeder.

---

## 4. Ekran akışı

| Ekran | Dosya | Not |
|---|---|---|
| Classroom Home | `web/src/app/classroom/page.tsx` (YENİ) | Bugünkü homepage `ClassroomPreview.tsx` **bozulmuyor** — ona "Try a real case" linkiyle giriş noktası eklenir. Eski Calibration v0'ın çalışıyor olması değerli, komple değiştirilmiyor. |
| Context → Think → Probability → Reason → Commit | `web/src/app/classroom/case/[id]/page.tsx` (YENİ) | STEP A-E aşağıda §4.1 |
| Outcome | aynı sayfa, case `resolved` olunca | `/finsense/case/{id}/outcome` |

`Landing → Classroom Preview → Try a real case → /classroom/case/[id]` — eski ve yeni sistemin yan yana karşılaştırılabilirliğini de sağlar.

### 4.1 Ekran detayı

- **STEP A — Context:** "CASE #001 — What happened? [asset]. At [event_timestamp]... Market context: ..." → "What do you think happens next?"
- **STEP B — Direction:** UP / DOWN / FLAT, tek seçim.
- **STEP C — Probability:** slider (50-100%), "How likely is your prediction?"
- **STEP D — Reason:** "Why? Write the main reason behind your prediction." (zorunlu, §2.1)
- **STEP E — Commit:** özet + *"Once committed, this prediction cannot be changed."* + **Commit Prediction** CTA. Bu cümle kritik — kullanıcı commit'in ne anlama geldiğini anlamalı.
- **Commit sonrası:** "Prediction locked — UP · 70% · Committed: 11 Aug 2026 · 15:42" — outcome gösterilmez, henüz çözülmemiş.

---

## 5. Identity (v0)

`anonymous_user_id`: `crypto.randomUUID()` → `localStorage`. Mevcut `useAuth()` (`web/src/lib/auth.tsx`) dokunulmuyor. Şema/API'de baştan `anonymous_user_id` adı kullanılıyor (`user_id` değil) — v1'de `auth_user_id` ayrı bir kolon olarak eklenecek, kavramlar baştan karışmasın diye.

---

## 6. VS-01 Acceptance Criteria

### 6.1 Temel akış
- [ ] `fs_cases`'te gerçek 1 kayıt (`export_resolved_cases.py`, gerçek `signals_archive` sinyalinden, §2.3 kriterleriyle seçilmiş).
- [ ] `GET /case/today` case'i döner, outcome alanı yok.
- [ ] `/classroom/case/{id}` context'i gösterir, direction+probability+reason alır (reason zorunlu).
- [ ] Commit → `POST /predict` → 200 + `fs_predictions` satırı, `committed_at` sunucuda üretilmiş.
- [ ] **Refresh testi:** F5 sonrası prediction hâlâ görünür ve kilitli — frontend state'e güvenilmiyor, gerçek persistence doğrulanmış.
- [ ] `fs_outcomes`'a outcome yazıldığında `GET /outcome` sonucu + evaluation döner.
- [ ] Kullanıcı outcome ekranında tahminini, gerçek sonucu ve doğru/yanlış durumunu görür.
- [ ] Bütün akış AI'siz çalışıyor (LOCK-06).
- [ ] Hiçbir adımda calibration/Brier/bucket gösterilmiyor (LOCK-05, N=1 kuralı).

### 6.2 Manipülasyon testleri (bağlayıcı, atlanamaz)
- [ ] **Test 1:** Client `committed_at` gönderirse backend kabul etmiyor (sunucu üretimi geçersiz kılıyor).
- [ ] **Test 2:** Client `outcome`/`actual_direction` gönderirse backend kabul etmiyor.
- [ ] **Test 3:** Aynı case'e ikinci `POST /predict` → `409 Conflict`.
- [ ] **Test 4:** Uygulama API'sinde prediction'ı değiştirecek hiçbir UPDATE/PATCH endpoint yok (kod incelemesiyle doğrulanır).
- [ ] **Test 5:** Outcome unresolved iken `GET /outcome` → `404`, frontend "Outcome pending" gösteriyor.

### 6.3 Black-box kullanıcı testi (teknik testlerden sonra, geliştirici olmayan biri gibi)
Kullanıcı arayüze bakınca şu 8 soruyu kendi kendine cevaplayabiliyor mu — hepsi UI'da açık olmalı:
1. Bu bir ders mi? 2. Bir vaka mı? 3. Benden ne isteniyor? 4. Probability ne demek? 5. Commit ne demek? 6. Sonradan sonucu görecek miyim? 7. Tahminim değiştirilebilir mi? 8. Bu bana yatırım tavsiyesi veriyor mu?

Bu liste tamamlanmadan VS-01 bitmiş sayılmaz.

### 6.4 DONE değildir eğer
Sadece frontend çalışıyorsa · prediction yalnız React state'teyse · refresh sonrası kayboluyorsa · outcome frontend tarafından belirleniyorsa · case canlı veriden tekrar oluşturuluyorsa · user identity her refresh'te değişiyorsa · ikinci prediction kabul ediliyorsa · calibration gösteriliyorsa · AI sonucu etkiliyorsa · mock outcome kullanılıyorsa.

---

## 7. VS-01'de kesinlikle yapılmayacaklar

Brier dashboard · AI coach · adaptive learning · error taxonomy · leaderboard · gamification · multi-case analytics · gelişmiş dashboard · `useCommitReveal` soyutlaması (erken abstraction yok) · `alternative` alanı · `predictions/claim` (anon→auth merge) · `academy.db` divergence çözümü · günlük otomatik case üretimi (scheduler).

---

## 8. Implementation sırası (Phase 0 tamamlandı — bu belge onunla kilitleniyor)

**PHASE 0 — Contract Gate (TAMAMLANDI):** Architecture Contract v1 → Product Thesis v1 → Calibration Spec v1 → MVP Gap Audit → bu belge.

**PHASE 1 — Data foundation:** `fs_cases/fs_predictions/fs_outcomes/fs_evaluations` → `auth/database.py`'ye migration, index, FK, constraint.
**PHASE 2 — Case #001:** `signals_archive` → §2.3 kriterleriyle seçim → snapshot doğrulama → `export_resolved_cases.py`.
**PHASE 3 — API:** `GET /case/today` → `POST /predict` → `GET /outcome`, her biri happy-path + invalid-input + duplicate + unresolved + tampered-payload testleriyle.
**PHASE 4 — Identity:** `anonymous_user_id` helper, persistence, refresh testi.
**PHASE 5 — Classroom UI:** `/classroom` (case discovery) → `/classroom/case/[id]` (context→think→probability→reason→commit→locked).
**PHASE 6 — Outcome:** case çözüldüğünde prediction↔actual→evaluation, kullanıcıya göster.
**PHASE 7 — E2E:** browser → Next proxy → Borsa API → DB → (FinPilot outcome) → DB → browser, gerçek uçtan uca.

Bir phase bitmeden sonrakine geçilmez (Contract §85).

---

## 9. VS-01 teknik başarı ≠ ürün doğrulama metriği

**Teknik:** Case → Prediction → Outcome loop completion.
**Ürün (ilk gerçek kullanıcı testinde ayrıca ölçülür):** case started → prediction committed → reason written → outcome returned → user understands what happened → user wants another case.

Henüz DAU/retention/Brier/leaderboard/AI-coach/adaptive-learning başarı kriteri değil.

---

_Bu belge Contract §9-21, §33, §38-43, §51-55 + 2026-08-11 Implementation Gate düzeltmelerinin birleşik, uygulanabilir hâlidir. Phase 0 tamamlandı sayılıyor; Phase 1'e (gerçek migration kodu) geçiş onay bekliyor._
