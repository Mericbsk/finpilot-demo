# RESEARCH GOVERNANCE CONTROLLER — Spec v0.2 (DRAFT)

**Version:** v0.2-LOCKED
**Date:** 2026-09-23
**Status:** APPROVED / LOCKED — Meriç approval 2026-09-23 (Level B, research
  process authority for the READ-ONLY controller spec). Implementation is a
  separate step; this lock authorizes no tool/script/state file by itself.
**Layer:** Governance / Research process
**Production Impact:** NONE (first version is READ-ONLY)

> Bu belge bir Level B tekliftir. Onaylanmadan hiçbir araç/script/state dosyası
> oluşturulmaz, hiçbir hat açılmaz, hiçbir production davranışı değişmez.
> **Tasarım cümlesi (kilitli):** Controller state üretir; authority üretmez.
> Evidence'ı reconcile eder; conflict'i çözmez. Geçmişin provenance'ını varsaymaz;
> mevcut provenance'ı korur.

---

## 0. PURPOSE
FinPilot'ın problemi artık deney üretmek değil; **hangi deneyin bittiğini, hangi
bulgunun hangi kararı açtığını ve hangi production riskinin mevcut olduğunu**
tek bir makine-okunur yaşam döngüsünde yönetmek. Bu controller:

- bir experiment runner DEĞİLDİR,
- bir prediction engine DEĞİLDİR,
- bir decision maker DEĞİLDİR.

Görevi: **kararın hangi state'te olduğunu ve hangi evidence ile desteklendiğini
doğru göstermek.**

Tasarım ilkesi (kilitli):

> Controller geçmiş araştırmayı yönetmez; geçmiş araştırmanın state'ini korur.
> Gelecek araştırmanın lifecycle'ını yönetir.

---

## 1. SCOPE (kilitli, dar) — iki ayrı katman
İlk sürüm iki farklı katmanı asla karıştırmaz:

**FULL-STATE LINES (controller tam state modeller ve doğrular):**
- H4 (H4A/H4B/H4C/H4D-definition/H4D-measure) — FROZEN/CLOSED
- NS-1 — CLOSED / VERIFIED
- RX-CAPTURE-1 — CLOSED / VERIFIED

**POINTER-ONLY HISTORICAL LINES (controller yalnızca pointer tutar; CLOSED
iddiası `known_status` olarak geçer, `controller_verified_status` DEĞİL):**
- RX-H2, direction battery, S1, high-RVOL, TP/SL grid, reverse-ranking,
  ranking-score backtest, V2 path-aware

Pointer inventory minimum metadata: experiment_id, title, artifact_path,
artifact_type, date, `known_status` (yalnızca açıkça belgelenmişse). Eski
exploratory raporlar (90+) tam state'e KATILMAZ; yalnızca pointer.

## 2. YAPMAYACAKLARI (kilitli)
Controller asla: yeni hypothesis üretmez, experiment sonucu hesaplamaz,
score/feature/flag değiştirmez, production'a geçiş yapmaz, kapalı hattı yeniden
açmaz, locked artifact'ı değiştirmez, "positive → production" cascade yapmaz,
insan Level-B/C kararını otomatik vermez.

## 3. STATE MODEL — beş ayrı boyut (tek sepete değil)
Her FULL-STATE hat için:

```
EXPERIMENT
  ├── lifecycle_state    (LOCKED / FROZEN / CLOSED)
  ├── scientific_verdict (örn. CAPTURE_SUPPORTED; hat başına çok-olabilir)
  ├── verification_state (PASS / DISCREPANCY / INCONCLUSIVE / PENDING / NONE)
  ├── governance_state   (decision-log authority durumu)
  ├── production_impact  (NONE / ...)
  ├── decision_state     (açık Level B/C karar varsa)
  ├── provenance         (input/prereg/result/report/verification SHA'ları)
  ├── protocol_deviation (varsa, documented)
  └── state_permitted_actions (§7; RECOMMENDATION değil)
```
`scientific verdict`, `lifecycle_state` ve `governance_state` aynı alan DEĞİLDİR;
birbirine ezdirilmez.

## 4. İLK SÜRÜM YETKİLERİ (READ-ONLY)
Yalnızca: **state reconciliation** (registry↔artifact↔decision-log),
**provenance check** (SHA bütünlüğü, lock-before-result sırası — §5),
**decision-log integrity** (kayıt var mı; stale pending; çelişki
sınıflandırması), ve **authoritative-state answer** (bir ajan "X yapılmadı"
dediğinde registry üzerinden kanıtlanmış cevap; kanıt yoksa UNKNOWN).

## 5. LOCK / PROVENANCE — dosya zamanı governance kanıtı DEĞİLDİR
"Lock-before-result" dosya `mtime` ile KANITLANMAZ. Controller yalnızca explicit
governance evidence kullanır: `preregistration_locked_at`, `result_generated_at`,
`verification_at` ve/veya `lock_artifact`+`lock_sha` (decision-log kaydı veya
artifact metadata'sı). Bunlar yoksa lock-order `UNVERIFIABLE` raporlanır —
`VIOLATION` varsayılmaz.

## 5. GOVERNANCE BOUNDARY
- Controller'ı repo'ya eklemek: **Level B** (kalıcı governance aracı).
- Controller'ı governance *authority* yapmak (karar verebilen): ayrı ve daha
  yüksek bir karar; bu spec kapsamında DEĞİL.
- PROGRAM_STATE değerleri hardcode EDİLMEZ; decision-log + artifact'lerden
  TÜRETİLİR (aksi halde controller kendisi borç üretir).

## 6. AUTHORITY PRECEDENCE (kilitli)
Registry **authoritative source DEĞİLDİR; derived view'dur** (Seçenek C):

```
SCIENTIFIC TRUTH   ← locked prereg / result artifact / verification artifact
GOVERNANCE TRUTH   ← decision-log / explicit human approval
DERIVED STATE      ← controller (registry + report)  [en alt; asla üsttekileri ezmez]
```
Authoritative evidence (artifact/verification/decision-log) → controller parser
→ derived registry/state. Registry'nin kendisi governance truth değildir. Bir
ajan gözlemi hiçbir zaman verified artifact'ın üstünde otorite değildir.

## 7. CONFLICT SEMANTICS — reconcile eder, çözmez (kilitli)
İki authoritative kaynak çelişirse controller kendi seçtiği değeri DÖNDÜRMEZ.
Örn. artifact=CLOSED ama decision-log=OPEN ise:

```
STATE = CONFLICT
RESOLUTION = REQUIRED
AUTHORITY_ACTION = NONE   (controller hiçbir şeyi ezmez/değiştirmez)
```
Conflict sınıfları: SUPERSEDED / UNRESOLVED / GOVERNANCE_CONFLICT /
DATASET_VERSION_CONFLICT / DEFINITION_CONFLICT. Conflict asla sessizce çözülmez;
yüzeye çıkarılır ve insan kararına bırakılır.

## 8. STATE-PERMITTED ACTIONS (öneri değil)
Controller `NEXT_ALLOWED_ACTION` veya `RECOMMEND` üretmez. Yalnızca
derived-state'in izin verdiğini gösterir:

```
STATE_PERMITTED_ACTIONS: MAY_OPEN / MUST_WAIT / BLOCKED
REQUIRED_APPROVAL: HUMAN_LEVEL_B / HUMAN_LEVEL_C / NONE
```
"X açılabilir" (state-derived) ile "X açılmalıdır" (decision) asla karışmaz.
Cascade yok: her geçiş kendi insan onayını gerektirir.

## 9. ABSENCE SEMANTICS (zorunlu invariant — RX-CAPTURE-1 dersi)
Controller şu üçünü asla birbirine karıştırmaz:

```
NOT_FOUND        ≠ NOT_PERFORMED
NOT_REGISTERED   ≠ NOT_PERFORMED
NOT_FOUND        ≠ FALSE
```
`FALSE — CLOSED/VERIFIED` yalnızca gerçek authoritative evidence varsa verilir.
Kanıt yoksa cevap `UNKNOWN — INSUFFICIENT_PROVENANCE`. Eksik provenance
kesinliği düşürür; negatif bulgu ÜRETMEZ.

## 10. CONTROLLER INVARIANTS (kilitli)
```
1.  UNKNOWN asla FALSE'a çevrilmez.
2.  NOT_FOUND asla NOT_PERFORMED olarak yorumlanmaz.
3.  Scientific verdict asla production authorization'a çevrilmez.
4.  Controller-derived state asla locked evidence'ın üstünde otorite olmaz.
5.  Conflict yüzeye çıkarılır, sessizce çözülmez.
6.  Historical provenance inference ile reconstruct edilmez.
7.  Locked research asla mutate edilmez / yeniden açılmaz.
8.  Agent observation asla verified artifact'ın üstünde değildir.
9.  Eksik provenance kesinliği azaltır; negatif bulgu üretmez.
10. READ-ONLY execution hiçbir governance mutation üretmez.
```

## 11. KARAR SINIFLANDIRMASI — §6 ayrımı
İki tür karar birbirinden ayrılır:

**GOVERNANCE DECISIONS (Meriç onayı gerekli — Level B ve üstü):**
- (G1) Controller'ın repo'ya kalıcı governance aracı olarak eklenmesi — Level B.
- (G2) Controller'ın ileride authority yapılıp yapılmayacağı — ayrı, daha yüksek
  karar; bu spec kapsamında DEĞİL.

**IMPLEMENTATION DECISIONS (teknik tasarım; spec'te default önerisi olarak durur,
Meriç geçersiz kılabilir ama onay GEREKTİRMEZ — Level A kapsamı):**
- (I1) Form: tekrarlanabilir read-only CLI/script (gerektiğinde modül import).
  DEFAULT.
- (I2) Registry: derived manifest; authoritative source değil. DEFAULT.
- (I3) Output: read-only rapor + makine-okunur artifact. DEFAULT.
- (I4) Pointer inventory: locked/closed hatlarla ilişkili bilinen işler + mevcut
  decision-log kayıtları; tüm 90+ rapor zorunlu değil. DEFAULT.

## 12. İLİŞKİ (mevcut otoritelerle)
- `_instructions/00-core.md` ve `docs/INDEX.md` üstte kalır; bu spec onları ezmez.
- Master Orchestrator v2 deney yaşam döngüsünü yönetir (deney NASIL koşulur); bu
  controller state'i yönetir (durum NE). Farklı katmanlar.
- H4 FROZEN kalır; controller H4'ü yalnızca okur.

## 13. CURRENT STATUS
```
STATUS: APPROVED / LOCKED (Meriç, 2026-09-23) — Level B process authority.
        Implementation is a separate, subsequent step.
SCOPE: locked lines full-state; historical lines pointer-only
MUTATION: NONE (read-only first version)
PRODUCTION IMPACT: NONE
```
