# FinSense System Reality & Architecture Contract v1
**Durum:** LOCKED (2026-08-11)
**Amaç:** FinSense MVP'den Thinking Mirror tabanlı çalışan ürüne geçiş için tek ve bağlayıcı gerçeklik/mimari sözleşmesi.
**Konum:** Belge 00 — Product Thesis v1 / Calibration Specification v1 / Vertical Slice Specification v1'in üstünde durur, hepsi buna aykırı bir şey tanımlayamaz.

---

# 0. EXECUTIVE CONTRACT

## 0.1 Bu belgenin temel amacı

FinSense'in mevcut MVP'si ile hedeflenen Thinking Mirror ürününün birbirine karıştırılmasını engellemek.

Bu belge şu soruların tamamına tek bir yerde cevap verir:

* Bugün gerçekten ne var?
* Bugün ne yok?
* Hangi mevcut sistemler korunacak?
* Hangi sistemler değiştirilecek?
* Hangi mekanizmalar sıfırdan kurulacak?
* FinPilot ile FinSense arasındaki sınır nerede?
* Market outcome'ı kim hesaplayacak?
* Prediction'ın sahibi kim?
* Kullanıcı kimliği nasıl tutulacak?
* Calibration ne zaman anlamlı hale gelecek?
* Thinking Mirror hangi verilerden beslenecek?
* AI nerede kullanılacak?
* AI nerede kullanılmayacak?
* İlk çalışan vertical slice tam olarak nedir?
* Hangi şeyleri şimdilik yapmayacağız?
* Bir özelliğin "tamamlandı" kabul edilmesi için hangi koşullar gerekiyor?

---

# 1. PRODUCT REALITY — BUGÜN GERÇEKTE NE VAR?

## 1.1 FinSense'in mevcut kimliği

Mevcut Finsense repository'si kendisini esas olarak:

> Kendi kendini geliştiren, yerel-AI destekli finansal okuryazarlık sözlüğü / içerik üretim sistemi

olarak konumlandırıyor.

Mevcut sistemin güçlü tarafı:

```text
Knowledge / Content Factory
        ↓
LLM + RAG
        ↓
Lesson generation
        ↓
Quality control
        ↓
Publication
        ↓
User progress
        ↓
Personalization
```

Bu yapı çalışır durumda bir **content production system** oluşturuyor.

Ancak henüz:

```text
User reasoning
Prediction
Probability
Commitment
Outcome
Calibration
Thinking Mirror
```

mekanizmalarını içermiyor.

---

# 2. MEVCUT SİSTEMİN SINIRLARI

FinSense şu anda:

### VAR

* lesson generation
* quiz generation
* flashcard generation
* content storage
* lesson components
* user progress
* user profile
* domain scores
* weak spots alanı
* engagement/streak benzeri sinyaller
* RAG
* agent pipeline
* content jobs
* search/log sistemleri
* statik lesson export

### YOK

* gerçek Case Engine
* Prediction object
* probability
* immutable commit
* prediction history
* objective outcome linkage
* evaluation engine
* calibration engine
* reasoning profile
* reasoning error taxonomy
* Thinking Mirror
* adaptive reasoning curriculum

---

# 3. PRODUCT THESIS — YENİ ÜRÜNÜN TEMEL TANIMI

FinSense'in yeni ana tanımı:

> **FinSense, insanların piyasalar hakkında nasıl düşündüklerini görmelerini sağlayan bir öğrenme sistemidir. Kullanıcı gerçek piyasa olayları üzerinden düşüncesini açık bir tahmine dönüştürür, confidence belirtir, tahminini commit eder ve daha sonra sonucunu gerçekle karşılaştırır. Sistem zaman içinde kullanıcının doğruluğunu değil yalnızca; confidence, calibration ve reasoning davranışını da görünür hale getirir.**

Bu tanımın önemli sonucu:

FinSense'in temel çıktısı artık:

> "Ne kadar finans biliyorsun?"

değil.

Şuna dönüşür:

> **"Piyasa hakkında nasıl düşünüyorsun ve düşüncen gerçekle karşılaştırıldığında ne öğreniyorsun?"**

---

# 4. FINPILOT VE FINSENSE AYRIMI

Bu kontratın en önemli maddelerinden biri budur.

## FinPilot

**Market intelligence / market observation layer**

Sorumlulukları:

* market data
* signal generation
* signal archive
* market snapshots
* barrier logic
* objective outcome resolution
* Ledger
* market research
* methodology
* historical system performance

FinPilot'in temel sorusu:

> **"Piyasada ne oldu / ne oluyor?"**

---

## FinSense

**Learning / reasoning / reflection layer**

Sorumlulukları:

* educational framing
* case presentation
* user prediction
* probability
* reasoning input
* prediction commitment
* evaluation
* calibration
* thinking profile
* Thinking Mirror
* adaptive learning

FinSense'in temel sorusu:

> **"Kullanıcı piyasada olanı nasıl yorumladı ve bundan ne öğrendi?"**

---

# 5. SYSTEM BOUNDARY

Canonical boundary:

```text
┌──────────────────────────────────────────┐
│                FINPILOT                  │
│                                          │
│ Market Data                              │
│ Signals                                  │
│ Ledger                                   │
│ signals_archive                          │
│ Barrier Resolution                       │
│ Objective Outcome                        │
└──────────────────┬───────────────────────┘
                   │
                   │ Case / Outcome interface
                   ▼
┌──────────────────────────────────────────┐
│                FINSENSE                  │
│                                          │
│ Case Presentation                        │
│ Classroom                                │
│ Prediction                               │
│ Reasoning                                │
│ Evaluation                               │
│ Calibration                              │
│ Thinking Mirror                          │
│ Adaptive Learning                        │
└──────────────────────────────────────────┘
```

## Temel prensip

**FinSense kendi market outcome resolver'ını yeniden yazmayacak.**

FinPilot'ta zaten çalışan deterministik outcome mekanizması varsa, FinSense onu kullanacak.

---

# 6. SOURCE OF TRUTH MATRİSİ

| Veri                     | Source of Truth |
| ------------------------ | --------------- |
| Market price             | FinPilot        |
| Signal                   | FinPilot        |
| Signal timestamp         | FinPilot        |
| Barrier definition       | FinPilot        |
| Objective outcome        | FinPilot        |
| Ledger grade             | FinPilot        |
| Lesson content           | FinSense        |
| Case educational framing | FinSense        |
| User prediction          | FinSense        |
| User probability         | FinSense        |
| User reasoning           | FinSense        |
| Prediction commit        | FinSense        |
| Evaluation record        | FinSense        |
| Calibration metrics      | FinSense        |
| Thinking Profile         | FinSense        |

Bu sınır ileride çok kritik.

---

# 7. MEVCUT CONTENT FACTORY'NİN KADERİ

Mevcut content factory kaldırılmayacak.

Ancak rolü değişecek.

## Eski rol

```text
Topic
 ↓
Lesson
 ↓
Quiz
 ↓
Completion
```

## Yeni rol

```text
Market Case
 ↓
Educational context
 ↓
Concept explanation
 ↓
Reasoning exercise
 ↓
Prediction
```

Dolayısıyla content factory:

> **Thinking Mirror'ın content/education layer'ı**

olacak.

---

# 8. EDUCATION PROFILE VE THINKING PROFILE AYRIMI

Mevcut:

```text
domain_scores
weak_spots
lesson completion
quiz score
streak
engagement
```

Education Profile olarak korunabilir.

Yeni:

```text
prediction accuracy
confidence
calibration
overconfidence
underconfidence
reasoning patterns
direction bias
```

Thinking Profile oluşturur.

Sonrasında:

```text
Education Profile
        +
Thinking Profile
        ↓
Adaptive Classroom
```

---

# 9. CASE ENGINE CONTRACT

Case artık basit bir lesson component değildir.

Minimum Case:

```text
Case
├── case_id
├── source_signal_id
├── asset
├── event_timestamp
├── snapshot
├── context
├── decision_horizon
├── outcome_rule
├── evidence
└── status
```

## Case'in temel amacı

Kullanıcıya gerçek bir piyasa olayını:

> "Bundan sonra ne olacağını düşün."

sorusuna dönüştürmek.

---

# 10. CASE SOURCE

Öncelikli kaynak:

**FinPilot `signals_archive`.**

Bunun avantajları:

* gerçek market event
* gerçek timestamp
* gerçek ticker
* gerçek signal
* gerçek historical context
* deterministik resolution
* synthetic case üretme ihtiyacının azalması

---

# 11. CASE SNAPSHOT KURALI

Prediction yapıldıktan sonra kullanıcıya gösterilen geçmiş bilgi değişmemelidir.

Örneğin:

```text
Case created:
2026-08-11 09:30
Prediction:
2026-08-11 09:42
```

Prediction'dan sonra gelen yeni market bilgisi:

> geçmiş case'in evidence snapshot'ını değiştiremez.

Bu:

**look-ahead bias**

riskini azaltır.

---

# 12. PREDICTION CONTRACT

Prediction yeni sistemin temel atomudur.

Minimum:

```text
prediction_id
case_id
user_id
direction
probability
reason
created_at
committed_at
status
```

Direction:

```text
UP
DOWN
FLAT
```

Probability:

```text
0.00 – 1.00
```

---

# 13. PREDICTION IMMUTABILITY

Commit sonrası:

```text
direction
probability
reason
case_id
timestamp
```

değiştirilemez.

Kullanıcı yeni tahmin yapmak isterse:

> yeni prediction oluşturulur.

Eski prediction overwrite edilmez.

Bu özellikle calibration için zorunludur.

---

# 14. NEDEN UPSERT YAPMAYACAĞIZ?

Mevcut:

```text
user_progress
```

mantığı progress için uygundur.

Ancak Prediction için değildir.

Örneğin:

```text
Prediction 1
70% UP
↓ kullanıcı değiştiriyor
70% DOWN
```

olursa calibration geçmişi bozulur.

Bu nedenle:

> **Prediction = event**

olmalıdır.

Progress:

> state

olabilir.

Prediction:

> immutable event

olmalıdır.

---

# 15. IDENTITY CONTRACT

## Validation v0

Gerçek kullanıcı hesabı zorunlu değil.

Ancak:

> anonim kullanıcı için stabil bir identifier

gerekiyor.

Örneğin:

```text
anonymous_user_id = UUID
```

Bu ID server tarafından prediction ile ilişkilendirilir.

---

# 16. AUTHENTICATION ROADMAP

### V0

Stable anonymous identity.

### V1

FinPilot JWT / gerçek account integration.

### V2

Cross-device identity / account recovery / richer profile.

Bu nedenle:

> **Auth production requirement'tır, ancak ilk product-validation vertical slice'ının önünü kesmek zorunda değildir.**

---

# 17. PREDICTION API PRENSİBİ

Client:

```text
POST /predictions
```

gönderir.

Server:

1. user identity doğrular
2. case'in aktif olup olmadığını kontrol eder
3. snapshot'ın geçerli olduğunu kontrol eder
4. probability aralığını doğrular
5. direction doğrular
6. prediction oluşturur
7. committed_at üretir
8. prediction'ı immutable olarak kaydeder

Client'ın:

> committed_at

veya:

> outcome

belirlemesine izin verilmez.

---

# 18. OUTCOME CONTRACT

FinSense outcome üretmez.

FinPilot outcome referansını okur.

Örneğin:

```text
source_signal_id
resolution_status
resolved_outcome
resolved_at
```

FinSense'e aktarılır.

---

# 19. OUTCOME DURUMLARI

Minimum:

```text
PENDING
RESOLVED
INVALID
CANCELLED
```

Prediction outcome'a bağlandığında:

```text
PENDING → RESOLVED
```

olur.

---

# 20. OUTCOME NORMALIZATION

FinPilot'un kendi outcome terminolojisi ne olursa olsun FinSense'in internal representation'ı standartlaştırılmalıdır.

Örneğin:

```text
UP
DOWN
FLAT
```

Böylece FinPilot tarafındaki resolver değişse bile FinSense evaluation katmanı doğrudan resolver implementasyonuna bağımlı olmaz.

---

# 21. EVALUATION CONTRACT

Prediction + Outcome birleştiğinde Evaluation oluşur.

Örneğin:

```text
prediction:
UP
0.70
outcome:
DOWN
```

Evaluation:

```text
direction_correct = false
probability = 0.70
binary_outcome = 0
probability_error = ...
```

---

# 22. CALIBRATION — V0

Bugünkü UI:

```text
Guess
 ↓
Commit
 ↓
Reveal
 ↓
Session counter
```

resmi olarak:

> **Calibration Interaction v0**

olarak adlandırılacaktır.

Bu bir calibration engine değildir.

---

# 23. CALIBRATION ENGINE v1

Gerçek calibration engine şu bağımlılıklara sahiptir:

```text
Identity
+
Prediction persistence
+
Probability
+
Objective outcome
+
Evaluation
+
N ≥ meaningful sample
```

Sonrasında:

* confidence buckets
* accuracy by bucket
* calibration gap
* Brier score

hesaplanabilir.

---

# 24. CALIBRATION METRİKLERİ

Binary outcome için:

[
Brier = \frac{1}{N}\sum_{i=1}^{N}(p_i-y_i)^2
]

Burada:

* (p_i) = kullanıcının probability'si
* (y_i) = gerçekleşen binary outcome

Örneğin:

> 70% UP

ve outcome:

> DOWN

ise:

[
(0.70-0)^2=0.49
]

Ancak tek prediction'da bu metrik kullanıcıya “profil” olarak sunulmayacaktır.

---

# 25. SAMPLE SIZE RULE

Calibration profile:

### N < 5

Profile gösterme.

### N = 5–9

“Early signal” olarak değerlendir.

### N ≥ 10

Confidence bucket'ları göstermeye başlanabilir.

### N ≥ 20–30

Daha anlamlı calibration metrics.

### Daha büyük sample

Brier / reliability analysis / trend analysis daha güvenilir hale gelir.

Bu sınırlar ürün deneyiminde “istatistiksel gerçek” gibi sunulmamalı; sample-size context'i görünür olmalıdır.

---

# 26. ACCURACY ≠ CALIBRATION

Bu prensip ürünün merkezine yazılmalıdır.

Örneğin:

> 70% confidence predictions → 60% correct

kullanıcı calibration açısından farklı bir şey gösterir.

Buna karşılık:

> overall direction accuracy = 60%

başka bir metriktir.

FinSense bunları tek bir “score”a indirmemelidir.

---

# 27. THINKING MIRROR CONTRACT

Thinking Mirror:

> AI coach değildir.

İlk aşamada:

> **evidence-based reflection layer**

olacaktır.

Input:

```text
prediction
confidence
reason
outcome
evaluation
historical calibration
```

Output:

```text
What you predicted
What happened
How confident you were
How often similar predictions worked
Potential pattern
Next learning opportunity
```

---

# 28. THINKING MIRROR V0

İlk versiyon deterministik olabilir.

Örnek:

> You predicted UP with 70% confidence.
> The outcome was DOWN.
> This prediction was incorrect.
> You currently have 3 evaluated predictions in the 70–79% confidence range.

AI gerekmez.

---

# 29. THINKING MIRROR V1

Yeterli veri oluşunca:

```text
confidence pattern
direction bias
calibration pattern
repeated reasoning behavior
```

analiz edilir.

Örneğin:

> “Your high-confidence predictions have so far been less accurate than your medium-confidence predictions.”

Bu bir observation'dır.

---

# 30. THINKING MIRROR V2 — AI

AI ancak deterministic data layer sağlamlaştıktan sonra devreye girer.

AI:

* reasoning text analiz edebilir
* recurring reasoning patterns bulabilir
* concepts önerebilir
* alternative explanations üretebilir
* reflection question oluşturabilir

AI:

* outcome belirlemez
* prediction değiştirmez
* score uydurmaz
* calibration hesaplamaz
* historical fact üretmez

---

# 31. AI / DETERMINISTIC SINIRI

## Deterministic

* market data
* outcome
* prediction storage
* timestamps
* calibration metrics
* accuracy
* Brier
* bucket statistics

## AI

* reasoning interpretation
* explanation
* pedagogical framing
* reflection
* next lesson suggestion

Bu ayrım mimarinin değişmez kuralıdır.

---

# 32. CLASSROOM CONTRACT

Classroom artık:

> glossary + quiz browser

olmamalı.

Yeni minimum loop:

```text
Context
 ↓
Learn
 ↓
Think
 ↓
Predict
 ↓
Commit
 ↓
Wait
 ↓
Reveal
 ↓
Reflect
```

---

# 33. CLASSROOM'UN İLK VERSİYONU

Bir case için:

### Screen 1

**Context**

Gerçek market event.

### Screen 2

**Learn**

Gerekli tek concept.

### Screen 3

**Think**

UP / DOWN / FLAT.

### Screen 4

**Confidence**

Probability.

### Screen 5

**Reason**

Kısa gerekçe.

### Screen 6

**Commit**

Immutable.

### Later

Outcome.

### Later

Reflection.

Bu kadar.

---

# 34. MEVCUT QUIZ SİSTEMİNİN ROLÜ

Quiz sistemi silinmez.

Ancak:

> **quiz = knowledge check**

olarak kalır.

Prediction:

> **reasoning check**

olur.

Bu ikisi birbirinin yerine geçmez.

---

# 35. EDUCATION → REASONING GEÇİŞİ

Mevcut:

```text
Lesson
 ↓
Quiz
 ↓
Score
```

Yeni:

```text
Lesson
 ↓
Case
 ↓
Prediction
 ↓
Outcome
 ↓
Reflection
```

Quiz gerekiyorsa Case öncesinde küçük bir knowledge check olabilir.

---

# 36. PERSONALIZATION CONTRACT

Mevcut personalization:

```text
completion
quiz
domain
engagement
```

Yeni personalization:

```text
knowledge profile
+
reasoning profile
```

Örneğin:

```text
Knowledge:
Options basics — strong
Reasoning:
High-confidence directional predictions — weak
Calibration:
60–69% — relatively stable
80%+ — insufficient sample
```

---

# 37. ADAPTIVE CLASSROOM

Adaptive Classroom ilk aşamada olmayacak.

Önce:

```text
Prediction data
 ↓
Calibration data
 ↓
Thinking patterns
```

birikmeli.

Sonrasında:

```text
Weak reasoning pattern
 ↓
Targeted concept
 ↓
New case
 ↓
Prediction
 ↓
Outcome
```

döngüsü kurulabilir.

---

# 38. DATABASE CONTRACT

Mevcut tablolar:

```text
lessons
lesson_components
user_progress
user_profile
content_jobs
agent_logs
search_log
lesson_views
```

korunabilir.

Yeni temel tablolar:

```text
cases
predictions
outcomes / outcome_references
evaluations
calibration_snapshots
thinking_snapshots
```

Gerekirse:

```text
reasoning_events
```

sonraki aşamada.

---

# 39. CASE TABLE — MİNİMUM

```text
cases
-----
id
source_signal_id
asset
event_timestamp
snapshot
context
horizon
outcome_rule
status
created_at
```

---

# 40. PREDICTION TABLE — MİNİMUM

```text
predictions
-----------
id
case_id
user_id
direction
probability
reason
committed_at
status
created_at
```

Prediction kayıtları immutable event olarak kabul edilir.

---

# 41. EVALUATION TABLE

```text
evaluations
-----------
id
prediction_id
outcome_id
direction_correct
probability_error
evaluated_at
evaluation_version
```

`evaluation_version` ileride metodoloji değişikliklerinde historical reproducibility sağlar.

---

# 42. CALIBRATION SNAPSHOT

Calibration sonucu gerektiğinde tekrar hesaplanabilir.

Ancak performans için snapshot tutulabilir:

```text
calibration_snapshots
---------------------
id
user_id
sample_size
bucket_data
brier_score
calibration_gap
created_at
calculation_version
```

---

# 43. THINKING SNAPSHOT

```text
thinking_snapshots
------------------
id
user_id
sample_size
direction_bias
confidence_patterns
calibration_summary
reasoning_patterns
created_at
model_version
```

İlk versiyonda reasoning_patterns boş olabilir.

---

# 44. VERSIONING

Ölçüm sistemlerinde versioning zorunludur.

Örneğin:

```text
outcome_version = "tb_v1"
evaluation_version = "eval_v1"
calibration_version = "cal_v1"
thinking_version = "mirror_v1"
```

Böylece geçmiş sonuçların neden değiştiği izlenebilir.

---

# 45. DATA OWNERSHIP

## FinPilot owns

* market truth
* signal truth
* outcome truth

## FinSense owns

* learning content
* case framing
* user prediction
* reasoning
* calibration
* thinking profile

Bu sınır veri sahipliği karmaşasını önler.

---

# 46. EVENT MODEL

Prediction event:

```text
PREDICTION_COMMITTED
```

Outcome event:

```text
OUTCOME_RESOLVED
```

Evaluation:

```text
PREDICTION_EVALUATED
```

Bunlar ileride event-driven architecture'a geçiş için de temel oluşturabilir.

İlk versiyonda Kafka/event bus gibi altyapılar gerekmiyor.

DB event records yeterli.

---

# 47. INTEGRITY CONTRACT

Sistem şu hileleri engellemelidir:

* prediction sonradan değiştirme
* outcome sonradan değiştirme
* timestamp manipülasyonu
* future data kullanma
* case snapshot değiştirme
* prediction duplicate
* resolved case'i yeniden prediction'a açma

---

# 48. LOOK-AHEAD BIAS KORUMASI

Case:

```text
T0
```

snapshot'tan oluşturulur.

Prediction:

```text
T1
```

yapılır.

Outcome:

```text
T2
```

sonrasında belirlenir.

T1 ile T2 arasındaki bilgiler T0 snapshot'ına eklenmez.

Bu özellikle eğitimsel dürüstlük için zorunludur.

---

# 49. SECURITY CONTRACT

İlk v0:

* anonymous stable ID
* server-side validation
* rate limiting
* immutable prediction
* no client-defined outcome

Production:

* authenticated user
* JWT
* server-side authorization
* user-owned records
* audit logs

---

# 50. PRIVACY

Prediction reasoning kişisel davranış verisidir.

Bu nedenle:

* public olmamalı
* default private olmalı
* aggregate analytics anonimleştirilmeli
* AI reasoning analysis kullanıcıya ait veri sınırları içinde yapılmalı

---

# 51. API BOUNDARY

Minimum API:

```text
GET  /cases
GET  /cases/{id}
POST /predictions
GET  /predictions/{id}
GET  /users/me/predictions
GET  /users/me/calibration
GET  /users/me/thinking
```

Outcome için:

```text
GET /cases/{id}/outcome
```

veya internal sync mekanizması kullanılabilir.

**(Bkz. Editör Notu #2 — bu namespace Document 3'te somut bir seçimle bağlanıyor: gerçek kod bugün `/academy/*` altında yaşıyor.)**

---

# 52. FINPILOT OUTCOME INTERFACE

FinSense'in doğrudan FinPilot DB'sine bağlanması ilk tercih olmamalı.

Daha temiz:

```text
FinPilot
   ↓
Outcome API / Export Contract
   ↓
FinSense
```

Bu iki sistemi gevşek bağlı tutar.

---

# 53. STATİK JSON ENTEGRASYONUNUN ROLÜ

Mevcut:

```text
academy_lessons.json
```

kısa vadede çalışmaya devam edebilir.

Ancak yeni Thinking Mirror loop'u bunun üzerine kurulmayacak.

Çünkü:

> static lesson export

prediction persistence için yeterli değildir.

---

# 54. FIRST VERTICAL SLICE — VS-01

## Hedef

Tek bir gerçek case'in uçtan uca çalışması.

```text
FinPilot signal
 ↓
FinSense case
 ↓
Classroom
 ↓
Prediction
 ↓
Commit
 ↓
Persist
 ↓
FinPilot outcome
 ↓
Evaluation
 ↓
Result
```

---

# 55. VS-01 ACCEPTANCE CRITERIA

### Case

* [ ] gerçek FinPilot signal
* [ ] timestamp
* [ ] snapshot
* [ ] horizon
* [ ] outcome reference

### User

* [ ] stable identity

### Prediction

* [ ] direction
* [ ] probability
* [ ] reason
* [ ] commit
* [ ] server persistence

### Integrity

* [ ] commit sonrası değiştirilemiyor
* [ ] prediction timestamp server tarafından oluşturuluyor

### Outcome

* [ ] FinPilot resolver sonucu
* [ ] prediction ile eşleşiyor

### Evaluation

* [ ] correct/incorrect hesaplanıyor

### UX

* [ ] kullanıcı prediction'ını görebiliyor
* [ ] outcome geldiğinde sonucu görebiliyor

### No AI dependency

* [ ] vertical slice AI olmadan çalışabiliyor

Bu kriterler sağlanmadan VS-01 tamamlanmış sayılmayacak.

---

# 56. VS-01'DE OLMAYACAKLAR

* Brier dashboard
* AI coach
* adaptive learning
* error taxonomy
* leaderboard
* gamification
* social profile
* multi-case analytics
* advanced dashboard

---

# 57. VS-02 — CALIBRATION

VS-01 çalıştıktan sonra:

```text
10+ evaluated predictions
 ↓
confidence buckets
 ↓
accuracy per bucket
 ↓
calibration visualization
```

Bu aşamada kullanıcı ilk kez:

> “Ben confidence'ımı ne kadar doğru ayarlıyorum?”

sorusuna cevap alır.

---

# 58. VS-03 — THINKING MIRROR

VS-02 üzerine:

```text
historical predictions
+
outcomes
+
confidence
+
reasoning
```

birleştirilir.

Mirror:

```text
What you thought
What happened
How confident you were
What pattern is emerging
```

gösterir.

---

# 59. VS-04 — ADAPTIVE CLASSROOM

Mirror'ın bulduğu pattern:

```text
overconfidence
```

ise:

```text
target concept
 ↓
new case
 ↓
prediction
 ↓
outcome
```

oluşturulur.

Bu noktada gerçek öğrenme loop'u oluşur.

---

# 60. PRODUCT LOOP

Final ürün loop'u:

```text
READ
 ↓
LEARN
 ↓
THINK
 ↓
COMMIT
 ↓
WAIT
 ↓
REVEAL
 ↓
REFLECT
 ↓
CALIBRATE
 ↓
LEARN AGAIN
```

Bu FinSense'in ana product loop'udur.

---

# 61. NORTH STAR

İlk aşamada North Star:

> **Kullanıcının doğru tahmin yapması değil, prediction → outcome → reflection döngüsünü tekrar tekrar tamamlamasıdır.**

Ölçülebilir versiyon:

```text
% of users who:
make ≥ 1 prediction
AND
receive ≥ 1 evaluated outcome
AND
return for another case
```

Daha ileri:

> 5+ evaluated predictions yapan kullanıcı oranı.

---

# 62. PMF VALIDATION

Henüz:

> “Dünyanın en iyi finansal okuryazarlık platformu”

iddiasını test etmiyoruz.

Önce:

### Kullanıcı anlıyor mu?

> “FinSense ne yapıyor?”

### Kullanıcı ilgileniyor mu?

> “Bir prediction yapmak istiyor mu?”

### Kullanıcı geri dönüyor mu?

> “Sonucunu görmek istiyor mu?”

### Kullanıcı fayda görüyor mu?

> “Kendim hakkında yeni bir şey öğrendim.”

### Kullanıcı davranış değiştiriyor mu?

> “Bir sonraki prediction'da confidence'ımı farklı ayarladım.”

---

# 63. PRODUCT SUCCESS CRITERIA

İlk gerçek başarı:

```text
User sees case
 ↓
User commits
 ↓
User returns to see outcome
 ↓
User understands result
 ↓
User makes another prediction
```

Bu gerçekleşmiyorsa:

> daha fazla feature yapmayacağız.

---

# 64. PRIORITY MATRIX

## P0 — Foundation

1. Identity
2. Case schema
3. Prediction schema
4. persistence
5. FinPilot outcome interface

## P1 — Vertical Slice

6. Case ingestion
7. Classroom case
8. Think
9. Probability
10. Reason
11. Commit
12. Outcome
13. Evaluation

## P2 — Calibration

14. Confidence buckets
15. Accuracy by bucket
16. Brier
17. Calibration gap
18. Snapshot

## P3 — Thinking Mirror

19. Thinking profile
20. reasoning patterns
21. error taxonomy
22. reflection

## P4 — Adaptive Learning

23. next lesson selection
24. targeted case
25. learning loop

---

# 65. EXPLICITLY DEFERRED

Şimdilik:

* AI financial advisor
* buy/sell recommendation
* target prices
* autonomous trading
* social trading
* leaderboard
* copy trading
* portfolio management
* advanced gamification
* marketplace
* premium subscription
* massive case library
* multi-agent orchestration
* advanced mobile app
* complex dashboards

---

# 66. LANDING CONTRACT

Landing yeni mimariye uygun olmalıdır.

### Kullanılabilir

* Thinking Mirror
* market reasoning
* honest ledger
* grades
* methodology
* learning
* prediction
* reflection

### Kullanılmamalı

* unsupported buy/sell
* unsupported accuracy
* unsupported DRL claims
* unsupported calibration claims
* fake sample statistics
* mockup'ın gerçek veri gibi sunulması

---

# 67. COMPLIANCE PRINCIPLE

FinSense:

> Kullanıcıya kişisel yatırım tavsiyesi veren sistem değildir.

Prediction exercise:

> kullanıcının kendi reasoning'ini test eder.

FinPilot Ledger:

> araştırma / eğitim / market observation formatıdır.

Bu ayrım tüm UX ve copy'de korunmalıdır.

---

# 68. OBSERVABILITY

Her kritik mekanizma ölçülebilir olmalı.

Minimum events:

```text
CASE_VIEWED
CASE_STARTED
PREDICTION_STARTED
PREDICTION_COMMITTED
OUTCOME_VIEWED
PREDICTION_EVALUATED
CALIBRATION_VIEWED
THINKING_MIRROR_VIEWED
```

Bu event'ler product validation için kritik.

---

# 69. FAILURE MODES

Sistem şunları açıkça ele almalı:

### Case invalid

Prediction oluşturulmaz.

### Outcome unavailable

Prediction:

```text
PENDING
```

kalır.

### Resolver error

Evaluation yapılmaz.

### Duplicate submission

Aynı commit ikinci kez kabul edilmez.

### Client refresh

Prediction kaybolmaz.

### Anonymous ID reset

Kullanıcı geçmişi kaybolabilir; v0 limitation olarak belirtilir.

---

# 70. DATA QUALITY CONTRACT

Case oluşturulmadan önce:

* source signal mevcut
* timestamp mevcut
* snapshot mevcut
* horizon mevcut
* resolution rule mevcut

olmalı.

Eksik case:

> Classroom'a yayınlanmaz.

---

# 71. CONTENT QUALITY CONTRACT

LLM'nin ürettiği educational content:

* market truth'u değiştiremez
* outcome'u tahmin edilmiş gibi sunamaz
* future knowledge kullanamaz
* historical event'i değiştiremez
* user prediction'ını etkileyen hidden information ekleyemez

AI content layer:

> **market truth'ten sonra gelir.**

---

# 72. LLM'NİN GÖREVİ

LLM:

### Yapabilir

* lesson açıklaması
* concept simplification
* case framing
* reflection question
* reasoning text analysis
* pedagogical explanation

### Yapamaz

* market outcome belirlemek
* historical outcome üretmek
* calibration metric hesaplamak
* prediction değiştirmek
* user score uydurmak

---

# 73. ARCHITECTURAL PRINCIPLE

> **Deterministic truth first, AI interpretation second.**

Bu cümle mimarinin ana prensibidir.

---

# 74. TEST STRATEGY

## Unit tests

* probability validation
* direction validation
* outcome mapping
* Brier calculation
* calibration bucket calculation

## Integration tests

```text
Case
 ↓
Prediction
 ↓
Outcome
 ↓
Evaluation
```

## Integrity tests

Prediction commit sonrası değiştirilememeli.

## E2E

Gerçek browser:

```text
case → prediction → refresh → result
```

---

# 75. ACCEPTANCE TEST — EN KRİTİK SENARYO

Bir test kullanıcısı:

1. Case'i açar.
2. Market snapshot'ını görür.
3. UP seçer.
4. 70% probability seçer.
5. Reason yazar.
6. Commit eder.
7. Sayfayı refresh eder.
8. Prediction hâlâ vardır.
9. Prediction değiştirilemez.
10. FinPilot outcome'u resolve eder.
11. FinSense evaluation oluşturur.
12. Kullanıcı sonucu görür.

Bu senaryo çalışıyorsa:

> **FinSense'in ilk gerçek reasoning engine'i çalışıyor demektir.**

---

# 76. WHAT WE REUSE

Mevcut:

* Finsense content factory
* lessons
* lesson components
* RAG
* LLM agents
* personalization foundation
* user progress infrastructure
* FinPilot Ledger
* FinPilot signals_archive
* FinPilot outcome resolver
* existing authentication infrastructure where applicable

korunur.

---

# 77. WHAT WE MODIFY

* Finsense positioning
* onboarding
* personalization semantics
* classroom experience
* lesson → case relationship
* user profile interpretation
* FinPilot ↔ FinSense integration
* landing messaging

---

# 78. WHAT WE BUILD NEW

* Case Engine
* Prediction Engine
* Prediction persistence
* Evaluation Engine
* Calibration Engine
* Thinking Mirror
* Thinking Profile
* Case/Outcome interface
* relevant APIs

---

# 79. WHAT WE DO NOT REBUILD

Özellikle:

> **FinPilot outcome resolver**

yeniden yazılmayacak.

Ayrıca:

> mevcut content factory

gereksiz yere sıfırdan yapılmayacak.

---

# 80. ARCHITECTURAL ANTI-PATTERNS

Şunlardan kaçınılacak:

### 1. Fake calibration

1–2 prediction'dan “calibrated” demek.

### 2. AI score

LLM'nin kullanıcıya rastgele reasoning score vermesi.

### 3. Mutable prediction

Prediction'ın overwrite edilmesi.

### 4. Outcome duplication

FinSense'in FinPilot outcome engine'ini yeniden yazması.

### 5. Dashboard-first development

Data oluşmadan dashboard yapmak.

### 6. Feature-first development

User loop doğrulanmadan yeni özellik eklemek.

### 7. Greenfield drift

Mevcut sistemde olmayan şeyleri varmış gibi kabul ederek specification yazmak.

---

# 81. DEFINITION OF DONE — PRODUCT

Bir özellik ancak:

* gerçek user flow'da çalışıyor
* persistence var
* integrity test edilmiş
* analytics var
* failure state var
* acceptance criteria karşılanmış
* mevcut mimariye uyuyor

ise tamamdır.

---

# 82. DEFINITION OF DONE — DATA

Bir metric:

* deterministic
* reproducible
* versioned
* sample size visible
* source data traceable

değilse production metric değildir.

---

# 83. DEFINITION OF DONE — AI

AI özelliği:

* deterministic data layer'a dayanmalı
* hallucination boundary'si olmalı
* source data'ya erişimi sınırlı olmalı
* output'un hangi veriye dayandığı izlenebilir olmalı

---

# 84. DEVELOPMENT ORDER

Kesin sıra:

```text
STEP 1
Identity decision
        ↓
STEP 2
Case contract
        ↓
STEP 3
Prediction schema
        ↓
STEP 4
Persistence
        ↓
STEP 5
FinPilot outcome interface
        ↓
STEP 6
One real case
        ↓
STEP 7
Prediction UI
        ↓
STEP 8
Commit
        ↓
STEP 9
Outcome
        ↓
STEP 10
Evaluation
        ↓
STEP 11
First E2E test
        ↓
STEP 12
Calibration
        ↓
STEP 13
Thinking Mirror
        ↓
STEP 14
Adaptive Classroom
```

---

# 85. DEVELOPMENT RULE

Bir step çalışmadan sonraki step'e geçilmez.

Örneğin:

> Prediction persistence çalışmıyorsa Calibration dashboard yapılmaz.

Outcome çalışmıyorsa:

> Brier score yapılmaz.

20 meaningful prediction yoksa:

> AI Thinking Coach yapılmaz.

---

# 86. FIRST IMPLEMENTATION TARGET

İlk teknik hedef:

> **One Real Case / One Real User / One Immutable Prediction / One Real Outcome**

Bu dört şeyin tamamı uçtan uca çalışacak.

---

# 87. İLK CASE KÜTÜPHANESİ

20–30 case başlangıç için yeterli olabilir.

Ancak ilk sprintte:

> **yalnız 1 case**

yeterlidir.

Case #001:

* gerçek FinPilot signal
* verified snapshot
* deterministic outcome
* educational framing
* prediction horizon

olmalıdır.

---

# 88. CASE LIBRARY SONRA NASIL BÜYÜR?

İlk vertical slice çalıştıktan sonra:

```text
20 cases
 ↓
different sectors
 ↓
different market regimes
 ↓
different reasoning challenges
```

Ama sayı kaliteyi geçmemeli.

---

# 89. CASE DIVERSITY

İleride:

* momentum
* reversal
* earnings
* volatility
* macro
* sector rotation
* uncertainty
* conflicting signals

gibi farklı reasoning problemleri olabilir.

Ama bunlar **ilk sprint kapsamı değildir.**

---

# 90. FINAL ARCHITECTURE

```text
                         ┌─────────────────────┐
                         │      FINPILOT       │
                         │                     │
                         │ Market Data         │
                         │ Signals             │
                         │ Ledger              │
                         │ Signal Archive      │
                         │ Outcome Resolver    │
                         └──────────┬──────────┘
                                    │
                          Case / Outcome API
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │      FINSENSE       │
                         │                     │
                         │ Content Factory     │
                         │        │            │
                         │        ▼            │
                         │      CLASSROOM      │
                         │        │            │
                         │        ▼            │
                         │       CASE         │
                         │        │            │
                         │        ▼            │
                         │      THINK         │
                         │        │            │
                         │        ▼            │
                         │     PREDICT        │
                         │        │            │
                         │        ▼            │
                         │      COMMIT        │
                         │        │            │
                         │        ▼            │
                         │    PREDICTION      │
                         │        │            │
                         │        ▼            │
                         │    EVALUATION      │
                         │        │            │
                         │        ▼            │
                         │    CALIBRATION     │
                         │        │            │
                         │        ▼            │
                         │ THINKING MIRROR    │
                         │        │            │
                         │        ▼            │
                         │ THINKING PROFILE   │
                         │        │            │
                         │        ▼            │
                         │ ADAPTIVE CLASSROOM │
                         └─────────────────────┘
```

---

# 91. THE PRODUCT IN ONE SENTENCE

FinSense:

> **Gerçek piyasa olayları üzerinden kullanıcıya düşüncesini açıkça ifade ettiren, bu düşünceyi gerçekle karşılaştıran ve zaman içinde kullanıcının nasıl düşündüğünü görünür hale getiren bir learning system'dir.**

---

# 92. THE PRODUCT LOOP IN ONE LINE

> **Learn → Think → Predict → Commit → Reveal → Reflect → Calibrate → Learn again.**

---

# 93. THE ARCHITECTURE IN ONE LINE

> **FinPilot supplies market truth; FinSense turns that truth into learning and reasoning loops; deterministic systems measure reality, while AI interprets it.**

---

# 94. CONTRACT LOCK

Bu belge kilitlendikten sonra aşağıdaki değişiklikler **mimari karar değişikliği** sayılır:

* FinPilot outcome resolver'ın değiştirilmesi
* Prediction'ın mutable yapılması
* AI'nin deterministic truth layer'a geçirilmesi
* FinSense/FinPilot source-of-truth sınırının değiştirilmesi
* identity modelinin değiştirilmesi
* Case → Prediction → Outcome temel zincirinin değiştirilmesi

Bunlar normal feature değildir.

Architecture Decision Record gerektirir.

---

# 95. SONRAKİ 3 BELGENİN YENİ HALİ

Bu kontrattan sonra mevcut üç belgeyi şu şekilde revize edeceğiz:

### DOCUMENT 1

**FinSense Product Thesis v1**

> Neden bu ürün var?

### DOCUMENT 2

**Calibration Specification v1**

> Prediction ve outcome'dan nasıl ölçüm çıkarıyoruz?

### DOCUMENT 3

**Vertical Slice Specification v1**

> İlk çalışan loop tam olarak nasıl inşa edilecek?

Bu üç belge artık bu Architecture Contract'a aykırı bir şey tanımlayamaz.

---

# 96. EN ÖNEMLİ KARAR

Bu projede bundan sonra şu prensibi kullanıyoruz:

> **Don't build the mirror before you have something to reflect.**

Önce:

```text
REAL CASE
+
REAL USER THOUGHT
+
REAL COMMITMENT
+
REAL OUTCOME
```

Sonra:

```text
CALIBRATION
```

Sonra:

```text
THINKING MIRROR
```

Sonra:

```text
ADAPTIVE LEARNING
```

Bu sıra değiştirilmemelidir.

---

# 97. IMMEDIATE ACTION PLAN

Şu anda yapılacaklar:

### A — Contract

Bu mimari kontratı kilitle.

### B — Reality

Mevcut repository'deki gerçek yapıyı değiştirmeden önce baseline/tag oluştur.

### C — Identity

V0 için anonymous stable identity mi, mevcut FinPilot auth entegrasyonu mu kullanılacağına karar ver.

### D — Case

FinPilot `signals_archive` → ilk gerçek Case #001.

### E — Prediction

`predictions` persistence.

### F — Outcome

FinPilot resolver interface.

### G — Evaluation

Prediction → Outcome.

### H — E2E

Tek case'in tamamen çalışması.

### I — Calibration

Ancak E2E'den sonra.

### J — Thinking Mirror

Calibration verisi oluşmaya başladıktan sonra.

---

# 98. FINAL DECISION

**FinSense şu anda yeniden tasarlanmayacak.**

**Mevcut MVP'nin güçlü content factory altyapısı korunacak.**

**FinPilot'un market-truth/outcome altyapısı yeniden kullanılacak.**

Yeni geliştirilecek ana mekanizma:

```text
REAL MARKET CASE
        ↓
USER REASONING
        ↓
PREDICTION
        ↓
COMMITMENT
        ↓
REAL OUTCOME
        ↓
EVALUATION
        ↓
CALIBRATION
        ↓
THINKING MIRROR
        ↓
LEARNING
```

Ve ilk hedef bütün bu sistemi aynı anda yapmak değil:

> **Bu zincirin ilk ve en küçük gerçek halkasını uçtan uca çalıştırmak:**

```text
CASE
 ↓
PREDICTION
 ↓
COMMIT
 ↓
PERSIST
 ↓
OUTCOME
 ↓
EVALUATION
```

Bu çalışmadan **Calibration dashboard, AI Mirror, adaptive learning veya yeni büyük UI katmanları geliştirilmeyecek.**

**Architecture Contract v1'in temel kilidi budur.**

---

## EDİTÖR NOTU (Claude, 2026-08-11 — kontrat metnine dokunmadan, ek olarak)

Kontrat kilitlendi, metne müdahale etmedim. Ama iki bulgu kayıp gitmesin diye buraya not düşüyorum:

**1) Auth düzeltmesi (§15-16'yı tamamlıyor, çelişmiyor):** FinPilot'ta (Borsa) gerçek bir JWT auth sistemi zaten var (`auth/core.py`, `auth/database.py`, `/api/v1/auth/{register,login,refresh,me}`) — ama yalnız `/dashboard/*`'a bağlı, public Ledger'a değil. §16'daki "V1: FinPilot JWT / gerçek account integration" maddesi bu nedenle **yeni auth yazmak değil, var olanı public Classroom'a bağlamak** anlamına geliyor.

**2) Identity integrity ≠ prediction immutability (§13/§15'i keskinleştiriyor):** §13'teki immutability sunucu tarafında tam güvenilir (UPDATE endpoint yok). Ama §15'teki `anonymous_user_id` client tarafında üretiliyor — sunucu "bu hep aynı kişi mi" sorusunu doğrulayamaz, yalnız "bu id'nin tahmini değişti mi" sorusunu doğrulayabilir. v0 için kabul edilebilir bir sınır (validasyon aşamasında hile motivasyonu yok) ama iki farklı garanti olduğu açık yazılmalı.

**3) Kontratta olmayan, ama Document 3'te karara bağlanması gereken iki açık nokta:** (a) §51'deki API namespace (`/cases`, `/predictions`) ile bugün gerçek kodun yaşadığı `/academy/*` prefix'i arasındaki seçim, (b) `Borsa/academy/` ile `Finsense/academy/`'nin diverge olmuş iki ayrı kopyası — hangisi yeni tabloların otoritesi. İkisi de Document 3'te somut kararla kapatıldı.
