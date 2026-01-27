# FinPilot Yol Haritası (Roadmap)
## Q1 2025 - Teknik Borç Temizliği & Altyapı Güçlendirme

---

# 🎯 VİZYON

**Mevcut Durum:** MVP seviyesinde çalışan ancak teknik borç yüklü bir trading uygulaması
**Hedef:** Production-ready, güvenli, ölçeklenebilir ve bakımı kolay bir platform

---

# 📊 GENEL BAKIŞ

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FİNPİLOT YOL HARİTASI 2025                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  OCAK                    ŞUBAT                   MART                       │
│  ─────                   ─────                   ─────                      │
│  Hafta 1-2               Hafta 3-4               Hafta 5-8                  │
│  ┌──────────┐            ┌──────────┐            ┌──────────┐               │
│  │ SPRINT 1 │            │ SPRINT 2 │            │ SPRINT 3 │               │
│  │ Security │───────────▶│ Quality  │───────────▶│ Refactor │               │
│  │ Critical │            │ & Test   │            │ & Scale  │               │
│  └──────────┘            └──────────┘            └──────────┘               │
│       │                       │                       │                     │
│       ▼                       ▼                       ▼                     │
│  ✓ Pickle fix           ✓ Exception          ✓ Core migration              │
│  ✓ PyJWT/bcrypt           handling           ✓ Code split                  │
│  ✓ Secrets mgmt         ✓ Test coverage      ✓ ETL validation              │
│  ✓ Rate limiting        ✓ Input validation   ✓ Dependencies                │
│                                                                             │
│                                                     Hafta 9-12              │
│                                                     ┌──────────┐            │
│                                                     │ SPRINT 4 │            │
│                                                     │ Polish & │            │
│                                                     │ Document │            │
│                                                     └──────────┘            │
│                                                          │                  │
│                                                          ▼                  │
│                                                     ✓ Monitoring            │
│                                                     ✓ Documentation         │
│                                                     ✓ Performance           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 🚀 SPRINT 1: Security Critical
## 📅 Hafta 1-2 (27 Ocak - 9 Şubat 2025)
## 🎯 Hedef: Kritik güvenlik açıklarını kapat

### Deliverables

| ID | Task | Öncelik | Effort | Sorumlu | Durum |
|----|------|---------|--------|---------|-------|
| S1.1 | Pickle → JSON/msgpack migration | P0 | 2 gün | Backend | ⬜ |
| S1.2 | PyJWT, bcrypt, cryptography entegrasyonu | P0 | 3 gün | Security | ⬜ |
| S1.3 | Hardcoded secret'ları .env'e taşı | P0 | 1 gün | DevOps | ⬜ |
| S1.4 | .env.example + git-secrets hook | P0 | 0.5 gün | DevOps | ⬜ |
| S1.5 | Auth rate limiting implementasyonu | P1 | 2 gün | Backend | ⬜ |
| S1.6 | Subprocess shell=False + input sanitize | P1 | 1.5 gün | Backend | ⬜ |

### Acceptance Criteria
- [ ] `pickle.loads()` untrusted source'dan: 0
- [ ] Custom crypto implementasyonu: 0 (bcrypt kullanılıyor)
- [ ] Hardcoded secret: 0
- [ ] Rate limit enforced: 5 attempt / 15 min lockout
- [ ] Bandit security scan: 0 high severity

### Sprint 1 Milestone
```
🔒 SECURITY BASELINE ACHIEVED
   - Tüm kritik güvenlik açıkları kapatıldı
   - Security scan clean
```

---

# 🧪 SPRINT 2: Quality & Testing
## 📅 Hafta 3-4 (10 Şubat - 23 Şubat 2025)
## 🎯 Hedef: Test coverage artır, exception handling standardize et

### Deliverables

| ID | Task | Öncelik | Effort | Sorumlu | Durum |
|----|------|---------|--------|---------|-------|
| S2.1 | 15 kritik exception bloğunu refactor et | P1 | 3 gün | Backend | ⬜ |
| S2.2 | `@handle_errors` scanner modülüne uygula | P1 | 2 gün | Backend | ⬜ |
| S2.3 | `auth/core.py` unit tests | P1 | 3 gün | QA | ⬜ |
| S2.4 | `scanner/signals.py` unit tests | P1 | 2 gün | QA | ⬜ |
| S2.5 | Input validation framework (`core/validation.py`) | P1 | 2 gün | Backend | ⬜ |
| S2.6 | pytest-cov CI'a ekle + coverage gate %40 | P1 | 1 gün | DevOps | ⬜ |

### Acceptance Criteria
- [ ] Generic `except Exception:` sayısı: 70 → 30
- [ ] Test coverage: 9% → 35%
- [ ] Critical path (auth, scanner) coverage: 60%+
- [ ] CI'da coverage gate aktif
- [ ] Input validation: Stock symbol, numeric ranges

### Sprint 2 Milestone
```
✅ QUALITY BASELINE ACHIEVED
   - Exception handling standardize
   - Test coverage 3x artış
   - CI/CD güçlendirildi
```

---

# 🔧 SPRINT 3: Refactor & Scale
## 📅 Hafta 5-8 (24 Şubat - 23 Mart 2025)
## 🎯 Hedef: Technical debt temizliği, modüler yapı

### Deliverables

| ID | Task | Öncelik | Effort | Sorumlu | Durum |
|----|------|---------|--------|---------|-------|
| S3.1 | `scanner/` → `core.config` full migration | P2 | 3 gün | Backend | ⬜ |
| S3.2 | `drl/` → `core.*` full migration | P2 | 5 gün | Backend | ⬜ |
| S3.3 | `auth/` → `core.exceptions` birleştir | P2 | 2 gün | Backend | ⬜ |
| S3.4 | `views/` → `core.logging` ekle | P2 | 2 gün | Backend | ⬜ |
| S3.5 | `scanner.py` modüler split (5 dosya) | P2 | 5 gün | Backend | ⬜ |
| S3.6 | ETL validation framework (Great Expectations) | P2 | 5 gün | Data Eng | ⬜ |
| S3.7 | Legacy `panel.py` / `panel_new.py` merge | P2 | 2 gün | Backend | ⬜ |
| S3.8 | Test coverage → %50 hedefi | P2 | 5 gün | QA | ⬜ |
| S3.9 | Dependency pinning + lock file | P3 | 1 gün | DevOps | ⬜ |

### Acceptance Criteria
- [ ] Core migration: 4/4 modül (scanner, drl, auth, views)
- [ ] Max file size: 400 lines
- [ ] Test coverage: 35% → 50%
- [ ] ETL data quality alerts aktif
- [ ] Lock file (`requirements-lock.txt`) mevcut
- [ ] Duplicate code: %5 altı

### Sprint 3 Milestone
```
🏗️ ARCHITECTURE MODERNIZED
   - Single source of truth config
   - Modüler, maintainable kod
   - Data quality monitoring
```

---

# 📚 SPRINT 4: Polish & Documentation
## 📅 Hafta 9-12 (24 Mart - 20 Nisan 2025)
## 🎯 Hedef: Production readiness, monitoring, documentation

### Deliverables

| ID | Task | Öncelik | Effort | Sorumlu | Durum |
|----|------|---------|--------|---------|-------|
| S4.1 | Sentry error tracking entegrasyonu | P2 | 2 gün | DevOps | ⬜ |
| S4.2 | Prometheus + Grafana dashboard | P2 | 3 gün | DevOps | ⬜ |
| S4.3 | API documentation (OpenAPI/Swagger) | P3 | 2 gün | Backend | ⬜ |
| S4.4 | Architecture Decision Records (ADR) | P3 | 2 gün | Tech Lead | ⬜ |
| S4.5 | Runbook & Incident Response Guide | P3 | 2 gün | DevOps | ⬜ |
| S4.6 | Performance profiling & optimization | P3 | 3 gün | Backend | ⬜ |
| S4.7 | Security audit (external) | P2 | 5 gün | External | ⬜ |
| S4.8 | Final test coverage push → %60 | P2 | 4 gün | QA | ⬜ |

### Acceptance Criteria
- [ ] Sentry: Error rate < 1%
- [ ] Grafana: Key metrics dashboard live
- [ ] Documentation coverage: 80%
- [ ] MTTD (Mean Time to Debug): < 30 dakika
- [ ] Test coverage: 50% → 60%
- [ ] External security audit: Pass

### Sprint 4 Milestone
```
🎉 PRODUCTION READY
   - Full observability
   - Complete documentation
   - Security certified
```

---

# 📈 KPI TRACKING

## Haftalık Takip Metrikleri

| Metrik | Başlangıç | Hafta 2 | Hafta 4 | Hafta 8 | Hafta 12 | Hedef |
|--------|-----------|---------|---------|---------|----------|-------|
| Security Issues (High) | 4 | 0 | 0 | 0 | 0 | 0 |
| Test Coverage | 9% | 15% | 35% | 50% | 60% | 60% |
| Generic Exceptions | 70 | 60 | 30 | 10 | 0 | 0 |
| Core Migration | 0/4 | 0/4 | 1/4 | 4/4 | 4/4 | 4/4 |
| Max File Lines | 1200 | 1200 | 800 | 400 | 400 | 400 |
| Pinned Dependencies | 3/15 | 3/15 | 3/15 | 15/15 | 15/15 | 15/15 |
| Documentation | 20% | 25% | 40% | 60% | 80% | 80% |

## Burndown Tracking

```
ADAM/GÜN
125 ┤
    │▓▓▓▓▓▓▓▓
100 ┤        ▓▓▓▓▓▓▓▓
    │                ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 75 ┤                                ▓▓▓▓▓▓▓▓
    │                                        ▓▓▓▓▓▓▓▓
 50 ┤                                                ▓▓▓
    │
 25 ┤                                                   ▓▓▓
    │                                                      ▓▓▓
  0 ┼───────┬───────┬───────┬───────┬───────┬───────────────▶
    Hafta 1-2   3-4     5-6     7-8    9-10    11-12
    Sprint 1  Sprint 2     Sprint 3        Sprint 4
```

---

# 💰 BÜTÇE PLANI

## Effort Dağılımı

| Sprint | Süre | Adam/Gün | Tahmini Maliyet* |
|--------|------|----------|------------------|
| Sprint 1: Security | 2 hafta | 10 gün | $5,000 |
| Sprint 2: Quality | 2 hafta | 13 gün | $6,500 |
| Sprint 3: Refactor | 4 hafta | 30 gün | $15,000 |
| Sprint 4: Polish | 4 hafta | 23 gün | $11,500 |
| **Buffer (%20)** | - | 15 gün | $7,500 |
| **TOPLAM** | **12 hafta** | **91 gün** | **$45,500** |

*Hesaplama: $500/adam-gün tahmini

## Ek Maliyetler

| Kalem | Bir Kerelik | Aylık |
|-------|-------------|-------|
| External Security Audit | $3,500 | - |
| Sentry (Team Plan) | - | $26 |
| Grafana Cloud | - | $0 (free tier) |
| **TOPLAM EK** | **$3,500** | **$26** |

---

# 🚧 RİSK YÖNETİMİ

## Tanımlanan Riskler

| Risk | Olasılık | Etki | Mitigation |
|------|----------|------|------------|
| Kaynak yetersizliği | Orta | Yüksek | Sprint scope adjustment, outsource |
| Legacy kod karmaşıklığı | Yüksek | Orta | Incremental refactor, feature flag |
| Breaking changes | Orta | Yüksek | Kapsamlı test suite, staging env |
| Scope creep | Yüksek | Orta | Strict sprint boundaries |
| External dependency update | Düşük | Yüksek | Lock file, automated testing |

## Contingency Plan

```
IF Sprint gecikirse:
   → P3 task'ları bir sonraki sprint'e ertele
   → P0/P1 task'lar asla ertelenmez

IF Kaynak eksikliği:
   → Dış kaynak (contractor) için bütçe ayrıldı (%20 buffer)
   → Kritik güvenlik task'ları öncelikli

IF Major blocker:
   → Daily standup'ta escalate
   → Tech Lead + PO haftalık review
```

---

# 👥 ROLLER VE SORUMLULUKLAR

| Rol | Sorumluluk | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 |
|-----|------------|----------|----------|----------|----------|
| **Backend Dev** | Core development | 6 gün | 7 gün | 19 gün | 5 gün |
| **Security Dev** | Auth, crypto | 3 gün | 0 gün | 0 gün | 0 gün |
| **QA Engineer** | Testing | 0 gün | 5 gün | 5 gün | 4 gün |
| **DevOps** | CI/CD, infra | 1.5 gün | 1 gün | 1 gün | 7 gün |
| **Data Engineer** | ETL | 0 gün | 0 gün | 5 gün | 0 gün |
| **Tech Lead** | Review, arch | 0.5 gün | 0.5 gün | 1 gün | 2 gün |
| **External** | Security audit | 0 gün | 0 gün | 0 gün | 5 gün |

---

# ✅ CHECKLIST

## Pre-Sprint 1 Hazırlık (Bu Hafta)
- [ ] Tüm paydaşlar roadmap'i onayladı
- [ ] JIRA/Linear board hazırlandı
- [ ] Development ortamı güncel
- [ ] Git branching strategy belirlendi (gitflow)
- [ ] CI/CD pipeline çalışıyor

## Sprint Ceremonies
- **Sprint Planning**: Her sprint başı, 2 saat
- **Daily Standup**: Her gün 15 dakika
- **Sprint Review**: Her sprint sonu, 1 saat
- **Retrospective**: Her sprint sonu, 1 saat

---

# 📅 TAKVİM GÖRÜNÜMÜ

```
OCAK 2025
══════════════════════════════════════════════════════════
Pzt   Sal   Çar   Per   Cum   Cmt   Paz
                                1     2
                           ┌─────────────┐
 3     4     5     6     7 │  8     9    │
                           │             │
                           │ SPRINT 1    │
10    11    12    13    14 │ 15    16    │
                           └─────────────┘

ŞUBAT 2025
══════════════════════════════════════════════════════════
                           ┌─────────────┐
17    18    19    20    21 │ 22    23    │
                           │             │
                           │ SPRINT 2    │
24    25    26    27    28 │ 1     2     │ (Mart)
                           └─────────────┘

MART 2025
══════════════════════════════════════════════════════════
      ┌───────────────────────────────────────────────────┐
 3    │  4     5     6     7     8     9                  │
      │                                                   │
      │                   SPRINT 3                        │
10    │ 11    12    13    14    15    16                  │
      │                                                   │
17    │ 18    19    20    21    22    23                  │
      └───────────────────────────────────────────────────┘

NİSAN 2025
══════════════════════════════════════════════════════════
      ┌───────────────────────────────────────────────────┐
24    │ 25    26    27    28    29    30                  │ (Mart)
      │                                                   │
      │                   SPRINT 4                        │
 7    │  8     9    10    11    12    13                  │
      │                                                   │
14    │ 15    16    17    18    19    20    ✅ COMPLETE   │
      └───────────────────────────────────────────────────┘
```

---

# 🎯 SUCCESS CRITERIA

## Sprint 1 Çıkış Kriterleri
```
✅ Bandit security scan: 0 high severity
✅ Pickle kullanımı: 0
✅ Hardcoded secret: 0
✅ Rate limiting: Active
```

## Sprint 2 Çıkış Kriterleri
```
✅ Test coverage: ≥35%
✅ Generic exception: ≤30
✅ CI coverage gate: Active
```

## Sprint 3 Çıkış Kriterleri
```
✅ Core migration: 4/4 modül
✅ Test coverage: ≥50%
✅ Max file size: ≤400 lines
```

## Sprint 4 (Final) Çıkış Kriterleri
```
✅ Test coverage: ≥60%
✅ Documentation: ≥80%
✅ Security audit: Pass
✅ Grafana dashboard: Live
✅ Zero high-severity issues
```

---

# 📝 ONAY

| Rol | İsim | Tarih | İmza |
|-----|------|-------|------|
| Tech Lead | | | |
| Product Owner | | | |
| Engineering Manager | | | |

---

*Doküman Oluşturulma: 25 Ocak 2025*
*Son Güncelleme: 25 Ocak 2025*
*Versiyon: 1.0.0*
