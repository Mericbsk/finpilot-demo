> **SUPERSEDED** — kilitli versiyon: `reports/b2_0_flag_user_facing_impact_preregistration_2026-09-23.md` (LOCKED v2, SHA-256 `fe4ceab1294a2799f034e4d4cc1c0f27b55ef1378d8ff577960c181f7a2133c0`). Bu taslak otorite değildir.

# B2-0 — FLAG USER-FACING IMPACT & FLAG-CONFIGURATION PROVENANCE GATE — PREREGISTRATION

**Status:** DRAFT v2 — KİLİTLİ DEĞİL. Kilit = Meriç onayı + bu dosyanın SHA-256'sının execution'dan ÖNCE decision-log'a yazılması. Kilitten sonra değişiklik = yeni versiyon + yeni SHA.
**Level:** A (read-only forensic measurement)
**Parent:** B2 — Flag Authorization & User-Facing Impact Reconciliation
**Production impact:** NONE
**Hazırlanma:** 2026-09-23

**v1 → v2 değişiklikleri (Meriç review, 2026-09-23):**
- `MATERIAL_USER_FACING_IMPACT` → `USER_FACING_IMPACT`; büyüklük ayrı alanda.
- Q2, `FINPILOT_ENABLE*` + git commit provenance'ına daraltıldı.
- `CONFIG_RECOVERED_BY_ENUMERATION` → `CONFIG_HASH_MATCH_BY_ENUMERATION`.
- Q3 ikiye ayrıldı: Q3A Snapshot Fidelity, Q3B Leave-One-Out Reconstructibility.
- ROW_ORDER_INTEGRITY eklendi.
- "f'ye atfedilen" yerine "f çıkarıldığında gözlenen".
- Ticker bazında rank tablosu zorunlu.
- Q1 yalnız bağlam bilgisi.
- Birincil gün seçim kuralı eklendi.
- 4-nesneli provenance discrepancy kaydı eklendi.
- PROVENANCE_GAP kaydı eklendi.
- SHA hard gate (MATCH / MISMATCH / MISSING) eklendi.
- Verdict öncelik sırası eklendi.
- Yetki (authorization) koşulu B2-0 verdict'inden çıkarıldı.
- Girdi SHA'ları prereg'e kilitlendi.
- Commit düzeltmesi (§2.6).

---

## §0 Amaç ve sınır

B2-0 yalnızca iki şeyi cevaplar:

1. Açık flag'lerden biri, diğer koşullar sabitken çıkarıldığında, **kullanıcıya gösterilen liste** değişiyor mu?
2. Yayınlanan snapshot'ı üreten `FINPILOT_ENABLE*` flag konfigürasyonu ve git commit'i hangi provenance kanıtıyla belirlenebilir?

B2-0 hiçbir flag için predictive, ekonomik, faydalı ya da zararlı yargısı üretmez. Hiçbir flag'in açılması ya da kapatılması gerektiği sonucuna varmaz. Yetki (authorization) değerlendirmesi yapmaz; o iş B2-full'undur.

`USER_FACING_IMPACT` = davranışsal fark gözlendi. Başka bir anlam taşımaz.
`NO_OBSERVED_USER_FACING_IMPACT` = bu snapshot'ta fark gözlenmedi. "Flag'in değeri yok" anlamına gelmez.

---

## §1 Sorular

| # | Soru | Rol |
|---|---|---|
| Q0 | Tüm beyan edilmiş girdi artifact'ları §2.7 manifestindeki SHA'larla eşleşiyor mu? | Integrity precondition (hard gate) |
| Q1 | Son kullanıcıya dönük yayın ne zaman? | Yalnız bağlam bilgisi. Q2/Q3/Q4 uygunluğunu değiştirmez, tarihi bir snapshot'ı geçersiz kılmaz |
| Q2 | Yayınlanan snapshot'ı üreten `FINPILOT_ENABLE*` konfigürasyonu ve git commit'i hangi provenance kanıtıyla belirlenebilir? | Flag-config provenance |
| Q3A | Snapshot, export + snapshot kodu ile birebir yeniden üretilebiliyor mu? | Q4'ün kapısı |
| Q3B | Her flag için flag kapalı durumdaki upstream alanlar güvenilir biçimde yeniden hesaplanabiliyor mu? | Flag bazında Q4 uygunluğu |
| Q4 | Leave-one-out'ta kullanıcıya dönük nesnelerde değişiklik gözleniyor mu? | Birincil ölçüm |

---

## §2 Execution öncesi gözlenmiş olgular (2026-09-23, salt-okuma)

Bu bölümdekiler olgudur, hipotez ya da verdict değildir. Agent her birini dosya:satır ya da komut çıktısıyla yeniden doğrular. Tutmayan her madde §9 CONFLICT kontrolüne girer.

**1. Kullanıcıya dönük sözleşme** (`distribution/snapshot_builder.py`):
- `FREE_CANDIDATES = 2`, `WEB_CONTEXT_CANDIDATES = 10`, `MAX_CANDIDATES = 50` (satır 33–35).
- Filtre `_public_candidate` (satır 123–131).
- Sıralama `_sort_key` = `(grade, execution_confidence, −conviction_prob, −ranking_score|legacy_quality_score|composite_score|score)` (satır 99–116). Skor 4. anahtardır.
- Web context listesi graded isimleri dışlar (satır 166–180).
- `_public_candidate` ve `_sort_key` yalnızca export'ta saklı alanları okur. Snapshot katmanı flag'lerden doğrudan etkilenmez; flag etkisi upstream alanlar üzerinden gelir.

**2. `config_sha()`** = sha256(`git_short|` + sıralı `FINPILOT_ENABLE*=v` çiftleri `;` ile)[:12] + `@git` (satır 38–52). Snapshot JSON'a yazılır (satır 523). Git bileşeni yalnızca HEAD commit'ini tanımlar. Commit edilmemiş (dirty) çalışma ağacı değişiklikleri hash'te görünmez.

**3. PROVENANCE_GAP:** `broadcast_queue` config_sha saklamıyor (snapshot_id, candidate_hash, scan_id saklıyor). Snapshot provenance'ı broadcast provenance'ından güçlüdür. B2-0 bunu yalnız kaydeder, çözmez → B4 provenance borcu.

**4. Birincil snapshot:** `snapshot_2026-09-09.json` (= `snapshot_latest.json`).
- `config_sha = a5e0d8b7c9d5@ff9658a`
- `universe = 1812`, `scan_result_count = 1801`, `eligible_candidate_count = 10`
- `generated_at = 2026-09-09T11:42:17Z`

**5. Export envanteri:** Son tam export ve son `_published` export 2026-09-09. 09-10 → 09-23 arası yalnızca `_partial_` dosyalar var. `_published` + snapshot çifti olan günler: 07-29, 07-30, 08-03, 08-11, 08-14, 08-24, 08-27, 09-09.

**6. Commit ilişkisi** (v1'deki "farklı commit" endişesinin düzeltmesi):
- `ff9658a` = 2026-09-03 "chore(web): daily snapshot 2026-09-03".
- `a242b06` = 2026-09-09T11:44:05Z "chore(web): daily snapshot 2026-09-09". Snapshot'tan 2 dakika sonra commit edilmiş.
- `ff9658a..a242b06` farkı yalnızca `web/public/demo_snapshot.json`. **Hiçbir .py dosyası değişmemiş.**
- `snapshot_builder.py`'nin `ff9658a`'daki SHA'sı bugünkü çalışma ağacındakiyle aynı.
- Yani 09-10 flag-impact ölçümü (a242b06) ile snapshot (ff9658a) aynı Python kodunu kullanır. Snapshot anındaki dirty-tree durumu ise bilinmiyor (§2.2).

**7. Konfigürasyon provenance nesneleri** — `CONFIGURATION_PROVENANCE_DISCREPANCY`. Bu bir "hata" olarak kaydedilmez; dört ayrı zaman/provenance nesnesi birbirine eşitlenmez:

| Nesne | İçerik | Tür |
|---|---|---|
| (a) `meta_validation_audit_2026-09-08` | "9+ flag ON" | Sayım iddiası, alt sınır |
| (b) `flag_impact_report` 2026-09-10 | 5 skor flag'i ölçülmüş | Ölçüm |
| (c) `snapshot_2026-09-09` config_sha | Yalnızca hash | Runtime damgası |
| (d) Bugünkü yerel `.env` | 14 ON / 4 OFF | Bugünkü dosya durumu |

"14 flag production'da açıktı" demek bu nesnelerden hiçbirine dayanarak mümkün değildir. Q2 yalnız (c)'yi açıklamaya çalışır.

**8. Gözlem (verdict değil, Q1/Q2'de doğrulanacak):** `data/distribution.db` son değişiklik zamanı 2026-09-09 13:42:18 +02:00 (= 11:42Z, snapshot `generated_at` ile aynı dakika).

**9. §2.7 — INPUT MANIFEST (kilitli SHA-256, 2026-09-23)**

| Artifact | SHA-256 |
|---|---|
| `data/distribution/scan_export_2026-09-09_published.json` | `454dd92835201b5c019067ffd9945f6de531d07776a94b8b65164798312b2074` |
| `data/distribution/snapshot_2026-09-09.json` | `e1f26abaa1aa066a5d80818bfb2c8e729498ca062dd460346e9c9eaf8f7d0a34` |
| `git show ff9658a:distribution/snapshot_builder.py` | `47b92eaa8115b500b13f4023f0cc27afbc60a206610f5f86a2cb8268ca292552` |
| `data/distribution.db` | `97fe4dd0c66920c921a67a15cadbe53f5069351907cf0253f9edc8d4a5023a10` |
| Yerel flag extract (aşağıdaki kural) | `e6a840f275b954488d45c5ee6694efc9e6ef21e63c954e175a0a8914304a2c93` |
| `data/distribution/scan_export_2026-07-29_published.json` | `020da1f07fba1112ae9809ac01c2cea4ea1474c6d589e0107e49b058eee032a3` |
| `data/distribution/snapshot_2026-07-29.json` | `c350ab9df56353f94ef918cbb2bbc7806ca2a9623f09e14d19daeab95ed7e251` |
| `data/distribution/scan_export_2026-07-30_published.json` | `7e32c1480cf19c9ae7da54f575a1c944e89bb0db99453aee5c9c390edbc2c08b` |
| `data/distribution/snapshot_2026-07-30.json` | `c6ae0bf93374c127691942c67294b2d301ffa7a824c3ea4c07e69dbaaba7ea5a` |
| `data/distribution/scan_export_2026-08-03_published.json` | `309430725f9bedf97271521c1240e9af1899cc2fb9aae1bfffd982ef94688d21` |
| `data/distribution/snapshot_2026-08-03.json` | `a6670b546600a2468d993142b5f0d00d160944e1b73127e0e19c9d304e79ba5d` |
| `data/distribution/scan_export_2026-08-11_published.json` | `33976ba897e52bb0b628fe52312695d90a05a217e92dd3f115618609cd6b578c` |
| `data/distribution/snapshot_2026-08-11.json` | `70d32522aeec71d49d861021c090868202028fb6ad1cf056d80a1f7136223a56` |
| `data/distribution/scan_export_2026-08-14_published.json` | `ba0679eefc96b9de86a8e2b406f06bb2a318495951b2b9e390d566612605be7b` |
| `data/distribution/snapshot_2026-08-14.json` | `92ad0b89a8531a7cc8ac5bfba50674af9f2138313fcf61794e1660efabd08875` |
| `data/distribution/scan_export_2026-08-24_published.json` | `559efe9c4b59039c0b297c22040ac0be8ad07fa3b77ae4c20a83545f4c3d682b` |
| `data/distribution/snapshot_2026-08-24.json` | `dc131e29e74d61babbbef183481bc82e3203b4f21a411cfc3b65a310aebd7bb4` |
| `data/distribution/scan_export_2026-08-27_published.json` | `8d5f39d0998c8b12bb2cbb111367a7bf7359f23dd462491554e950c0e7093b8a` |
| `data/distribution/snapshot_2026-08-27.json` | `45d11a72910ac7f559e0f661bb284a1c42dc53ec163b0d5267d2bb46d0a5b774` |

**Flag extract kuralı:**
- `.env` içindeki `^\s*FINPILOT_ENABLE[A-Z0-9_]*\s*=` ile başlayan, yorum olmayan satırlar alınır.
- CR karakteri silinir, `=` etrafındaki boşluk kırpılır.
- Satırlar leksikografik sıralanır, `\n` ile birleştirilir, sonda `\n` bırakılır.
- Sonuç: 18 satır. `.env` dosyasının kendisi hash'lenmez ve yazılmaz (secret içerir).

`distribution.db` Q1'de doğrudan açılmaz. Lock anında salt-okuma bir kopyası alınır, kopyanın SHA'sı manifestle eşleşmelidir, Q1 bu kopyayı okur.

---

## §3 Kapsam kilidi

### §3.1 Birim
- **Birincil gün seçim kuralı (sonuçlara göre değiştirilemez):** Lock tarihi itibarıyla, hem `scan_export_<D>_published.json` hem `snapshot_<D>.json` bulunan en son D. → **2026-09-09.**
- **Birincil:** 09-09 → Q0, Q1, Q2, Q3A, Q3B, Q4.
- **Tarihi yayınlanmış günler (7 gün):** Yalnızca Q0, Q2 bağlamı ve opsiyonel Q3A. **Q4 YOK.** Zamansal etki ayrı bir çalışma olabilir (B2-1), B2-0'ın parçası değildir.
- `_partial_` dosyaları hiçbir soruda kullanılmaz.

### §3.2 Flag kapsamı (F) — Q4'ten ÖNCE kilitlenir
F = şu iki koşulu birlikte sağlayan flag'ler:
- (i) Q2 ile belirlenen konfigürasyonda (Q2 doğrulanamazsa: yerel extract'ta, koşullu etiketle) ON,
- (ii) `ff9658a` kodunda, `snapshot_builder`'ın okuduğu alanlara giden yolda erişilebilir. Bu alanlar: `conviction_tier`, `tier`, `selection_eligible`, `execution_feasible`, `position_cap_reject_reason`, `execution_confidence`, `conviction_prob`, `ranking_score` / `legacy_quality_score` / `composite_score` / `score` ve web context alanları.

**Başlangıç aday listesi** (trace ile teyit/red; dosya:satır kanıtlı):
CONVICTION_TIERS, EXECUTION_POLICY, PORTFOLIO_ADV_LIMIT, EARLY_TIER, ALPHA_V2, SQUEEZE_FACTOR, LOTTERY_FADE, OVERNIGHT_GAP, EDGAR_CATALYST, FRED_MACRO, FUNDAMENTALS, NEWS.

- Listeden çıkarılan her flag için erişilemezlik kanıtı yazılır.
- SCAN_LLM_SUMMARY ve SHADOW_SCORECARD liste üyeliği dışında kalır; "kullanıcıya dönük metin/izleme" olarak B2-full envanterine not düşülür.
- Trace dosyası ve SHA'sı Q4'ten önce yazılır.

---

## §4 Nesneler ve N (koddan)

| Nesne | Tanım | N | Ölçülen |
|---|---|---|---|
| O1 — Graded public list | `_public_candidate` → `_sort_key` → `[:50]` | Gerçekleşen L (09-09: 10) | Üyelik |
| O2 — Free tier | O1[:2] | 2 | Üyelik + sıra (ayrı raporlanır) |
| O3 — Web context | `_build_web_context` | 10 | Üyelik |

Başka N kullanılmaz.

---

## §5 Q0 — Integrity precondition (HARD GATE)

Manifestteki her artifact için sonuç `SHA_MATCH`, `SHA_MISMATCH` veya `SHA_MISSING` olur.

```
if any(status != SHA_MATCH):
    total_verdict = CONFLICT
    Q3A, Q3B, Q4 = NOT_EXECUTED
```

- `SHA_MISSING`, beklenen dosya yoksa ya da manifestte SHA boşsa oluşur ve başarısızlıktır.
- Durumlar makine-okunur `integrity` bloğuna yazılır. Metadata olarak bırakılamaz; verdict'i doğrudan belirler.

Ek kontrol, **ROW_ORDER_INTEGRITY:** C_full ve her leave-one-out yeniden kurulumunda export satır kimliği ve sırası (sembol dizisinin SHA-256'sı) birebir aynı olmalıdır. Aynı sembol evreni, aynı satır kimliği, stable-sort öncesi aynı sıra. İhlal → ilgili karşılaştırma `CONFLICT`.

---

## §6 Q1 — Yayın aktivitesi (bağlam)

- Kaynaklar: `distribution.db` kopyası (`broadcast_queue`, `tg_delivery_log`), web public snapshot dosyası, `snapshot_*.json`.
- Çıktı: kanal bazında `last_publication_date` ve `ACTIVE` / `DORMANT` / `UNKNOWN` (ACTIVE = son 5 işlem gününde yayın var).
- Q1 contextual metadata'dır. Tarihi snapshot'ı geçersiz kılmaz, Q2/Q3/Q4 uygunluğunu ve toplam verdict'i değiştirmez.

---

## §7 Q2 — `FINPILOT_ENABLE*` + commit provenance

- **2a.** Her snapshot'ın `config_sha`'sı kaydedilir.
- **2b.** Yerel flag extract + snapshot `@git` ekiyle `config_sha` yeniden hesaplanır. İki yolla yapılır: bağımsız implementasyon ve repo fonksiyonunun kontrollü env ile alt süreçte çağrılması. İkisi eşleşmelidir. Runtime'ın `.env` loader'ı dosya:satır ile belirtilir.
- **2c.** 2b eşleşmezse: yerel extract'taki tam 18 anahtar üzerinde, değerler {"0","1"} olmak üzere 2^18 atama denenir. Anahtar kümesi ve değer uzayı genişletilmez.
- **2d.** Üretim yeri kanıtı (commit zaman damgaları, dosya mtime'ları, deploy script'leri) raporlanır; belirlenemiyorsa UNKNOWN.

**Çıktılar:**
- `CONFIG_HASH_MATCH_LOCAL`
- `CONFIG_HASH_MATCH_BY_ENUMERATION` (yerel ile fark tablosu)
- `NO_MATCH`

**Yorum sınırı (zorunlu metin):**
> A hash match establishes a `FINPILOT_ENABLE*` configuration consistent with the snapshot stamp under the locked hash function and candidate value space. It does not independently prove the physical/runtime origin of the snapshot, the state of non-`FINPILOT_ENABLE*` configuration, or the absence of uncommitted code changes.

**Yasak çıkarım:** "Yerel `.env` X diyor → production X'ti."

---

## §8 Q3A / Q3B / Q4

### Q3A — Snapshot Fidelity
- `ff9658a` ayrı, salt-okuma bir worktree'de kullanılır. Repo fonksiyonları çağrılır, yeniden yazılmaz.
- Export'taki saklı alanlarla O1/O2/O3 kurulur.
- Karşılaştırılanlar: `candidate_hash`, sıralı `candidates` listesi, O2.
- Q3A flag konfigürasyonundan bağımsızdır (§2.1), bu yüzden Q2 sonucundan bağımsız koşulur.

### Q3B — Flag Leave-One-Out Reconstructibility (flag başına)
F'deki her f için:
- Flag kapalıyken upstream alanlar export'ta saklı girdilerle (ör. `score_input`) yeniden hesaplanabiliyor mu?
- **Ön koşul:** Tam konfigürasyonla yeniden hesaplanan alanlar saklı değerleri birebir üretmeli. Tolerans: skor 0,01; kategorik alanlarda tam eşitlik.
- Yeni veri, scan veya ağ çağrısı gerekiyorsa ya da ön koşul tutmuyorsa → f = `NOT_RECONSTRUCTIBLE`. Tahminle doldurulmaz.

### Gating
| Durum | Sonuç |
|---|---|
| Q3A FAIL | Q4 BLOCKED → `NOT_RECONSTRUCTIBLE` |
| Q3A PASS + f Q3B PASS | f, Q4'e uygun |
| Q3A PASS + f Q3B FAIL | f = `NOT_RECONSTRUCTIBLE` |

### Q4 — Tasarım
- **Birincil:** C_full ve C_full − {f}. Diğer her şey sabit.
- **İkincil (betimsel):** C_full ve all-OFF (F tamamı kapalı).
- Pairwise veya başka kombinasyon yok.
- **Tie kuralı:** Stable sort + `_sort_key`; kalan eşitlikler export satır sırasıyla çözülür (ROW_ORDER_INTEGRITY şartı altında). Her N için N sınırını kesen tuple-eşit grubun boyutu raporlanır. Yalnızca bu grup içindeki yeniden sıralanmadan doğan değişiklikler işaretlenir.

### Zorunlu raporlama (f × nesne)
- `impact_scope`: O1_membership, O2_membership, O2_order, O3_membership (her biri true/false)
- `impact_magnitude`: changed_count, overlap_N, max_rank_displacement, L_full, L_f
- **Ticker tablosu (zorunlu):** O1/O2/O3 birleşimindeki her ticker için `ticker | rank_full | rank_without_f | delta_rank | entered | exited | grade_full | grade_without_f | public_full | public_without_f`. Rank, truncation öncesi tam graded sıralamadaki pozisyondur.
- `_public_candidate` durumu değişen satır sayısı.

---

## §9 Sınıflandırma (kilitli; sayısal eşik YOK)

### Flag başına
| Sınıf | Tanım |
|---|---|
| `USER_FACING_IMPACT` | f çıkarıldığında ve diğer koşullar sabitken, O1 üyeliği, O2 üyeliği, O2 sırası veya O3 üyeliğinde, yalnızca tie-yeniden-sıralamasından kaynaklanmayan en az bir değişiklik gözlendi |
| `TIE_ONLY` | Tüm değişiklikler N sınırını kesen tuple-eşit grup içinde |
| `NO_OBSERVED_USER_FACING_IMPACT` | Değişiklik gözlenmedi |
| `NOT_RECONSTRUCTIBLE` | Q3B FAIL |

"Gözlenen" = counterfactual konfigürasyon farkı altında gözlenen. Nedensel kanıt iddiası taşımaz.

### Toplam verdict — öncelik sırası (ilk eşleşen kazanır)
| # | Verdict | Koşul |
|---|---|---|
| 1 | `CONFLICT` | Q0'da herhangi bir SHA ≠ MATCH, ya da ROW_ORDER_INTEGRITY ihlali, ya da §2 olgularından biri tutmuyor, ya da kanıtlar çelişiyor (ör. Q2 yerel eşleşmesi var ama Q3A FAIL) |
| 2 | `NOT_RECONSTRUCTIBLE` | Q3A FAIL |
| 3 | `PRODUCTION_ENV_NOT_VERIFIABLE` | Q2 = NO_MATCH. Q3B/Q4 yerel konfigürasyon altında koşulur ve "koşullu" etiketiyle raporlanır, ama 4–6'yı üretemez |
| 4 | `USER_FACING_IMPACT` | En az bir f = `USER_FACING_IMPACT` |
| 5 | `INCOMPLETE` | Hiçbir f etki göstermedi ve en az bir f = `NOT_RECONSTRUCTIBLE` |
| 6 | `NO_OBSERVED_USER_FACING_IMPACT` | F'nin tamamı `NO_OBSERVED` veya `TIE_ONLY` |

Büyüklük sınıfı etkilemez; `impact_magnitude` alanında raporlanır. Flag-seviyesi sınıf ile toplam verdict JSON'da ayrı alanlardadır (`flags[f].class` / `total_verdict`).

### Sonraki adım eşlemesi
| Verdict | Sonraki adım |
|---|---|
| `USER_FACING_IMPACT` | B2-full (yetki + reconciliation) → B4. Q1 = DORMANT ise distribution, B2-full tamamlanmadan yeniden açılmaz |
| `NO_OBSERVED_USER_FACING_IMPACT` | B4 |
| `INCOMPLETE` / `PRODUCTION_ENV_NOT_VERIFIABLE` / `NOT_RECONSTRUCTIBLE` / `CONFLICT` | Kapsamlı bir provenance çözüm adımı. B2-full ve B4 sırası Meriç kararı |

---

## §10 Kapsam dışı / yasak

- Yeni predictive test, getiri karşılaştırması, optimizasyon, eşik ayarı, ağırlık değişikliği
- Flag enable/disable, `.env` değişikliği
- Yeni cohort, yeni veri, yeni scan, ağ çağrısı
- Production DB'ye yazma
- Kullanıcıya dönük değişiklik
- Tarihi yeniden yazma
- PROVENANCE_GAP'i çözmeye çalışmak (B4)
- Yetki değerlendirmesi (B2-full)

**Durma koşulu:** Bir adım bunlardan birini gerektiriyorsa durulur ve raporlanır.

**Gizlilik:** Artifact'lara yalnızca `FINPILOT_ENABLE*` çiftleri yazılır; secret yazılmaz.

---

## §11 Artifact'lar
- `research/b2_0_flag_user_facing_impact_<YYYY_MM_DD>.py`
- `data/backtest_out/b2_0_flag_scope_trace_<date>.json` (Q4 öncesi, SHA'lı)
- `data/backtest_out/b2_0_flag_user_facing_impact_<date>.json` — `integrity`, `q1`, `q2`, `q3a`, `q3b`, `flags`, `total_verdict`, `provenance_gap`, `configuration_provenance_discrepancy`
- `reports/b2_0_flag_user_facing_impact_report_<date>.md`
- decision-log: kilit kaydı (execution öncesi) + sonuç kaydı (sonra); salt-eklemeli

---

## §12 Bilinen sınırlamalar
- Q4 tek güne (09-09) dayanır.
- F, kod trace'inin doğruluğuna bağlıdır.
- `config_sha` tek yönlüdür, HEAD dışındaki kod durumunu ve `FINPILOT_ENABLE*` dışındaki konfigürasyonu görmez.
- Export upstream girdilerin tamamını taşımayabilir.
- Davranışsal fark ≠ predictive değer ≠ ekonomik değer ≠ yetki durumu.

---

## §13 Verdict sözlüğü
- **Toplam:** `CONFLICT` | `NOT_RECONSTRUCTIBLE` | `PRODUCTION_ENV_NOT_VERIFIABLE` | `USER_FACING_IMPACT` | `INCOMPLETE` | `NO_OBSERVED_USER_FACING_IMPACT`
- **Flag:** `USER_FACING_IMPACT` | `TIE_ONLY` | `NO_OBSERVED_USER_FACING_IMPACT` | `NOT_RECONSTRUCTIBLE`
- **Q0:** `SHA_MATCH` | `SHA_MISMATCH` | `SHA_MISSING`
- **Q1:** `ACTIVE` | `DORMANT` | `UNKNOWN`
- **Q2:** `CONFIG_HASH_MATCH_LOCAL` | `CONFIG_HASH_MATCH_BY_ENUMERATION` | `NO_MATCH`
- **Kayıt etiketleri:** `PROVENANCE_GAP`, `CONFIGURATION_PROVENANCE_DISCREPANCY`
