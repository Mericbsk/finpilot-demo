# FinPilot AI Operating Standard
## 05 — Escalation Levels

Version: 1.0 · Status: DRAFT — Meriç onayı bekliyor (CORE-006)
Authority Level: GLOBAL · Owner: Governance · Last Updated: 24 July 2026

Referans: CORE-007 (Escalation First). Her görev, yürütülmeden önce sınıflandırılır.

## Level A — Autonomous
AI kendisi yapar, kapı raporunda kaydeder.
Kapsam: salt-okunur analiz/audit · rapor ve dokümantasyon yazımı · test yazımı ve koşumu · yeni izole dosya (mevcut davranışı değiştirmeyen) · scratch/deneme kodu.

## Level B — Proposal + Approval
AI değişikliği yapar ve test eder, ama bölüm KAPISI Meriç onayı olmadan kapanmaz; diff/kanıt kapı raporunda sunulur.
Kapsam: üretim-kritik dosyalar (publish zinciri, scanner sözleşmesi, distribution, canlı web yüzeyi) · şema/konfig değişiklikleri · yeni bağımlılık eklenmesi · governance-dışı doküman reorganizasyonu.

## Level C — Human Approval Required (önceden)
## Level C — Human Decision; Narrow Web-Publish Delegation

Human approval remains mandatory. AI must never approve, create, infer,
or broaden its own authorization.

Default: AI prepares a preview and report; a human operator performs
the publication.

Narrow exception: A human may delegate execution of ONE web-only
publication to an AI agent by approving an exact release manifest in
writing. The approval must bind all of:
- export date and run_id
- scan_id and snapshot_id
- SHA-256 of the generated web artifact
- destination (the named production web deployment)
- the approving human and approval timestamp

The approval expires after that release attempt. Any changed artifact,
snapshot identity, destination, or failed preflight requires a new
human approval.

This exception covers only publishing the approved web snapshot. It
does not authorize Telegram sends, trading or broker actions, changes
to scoring/risk/position sizing, secret access, force-bypassing gates,
or governance changes.

Before execution, every release gate in YONERGE.md must pass:
full-scan and freshness/quality checks; approved public wording;
same snapshot identity across projections; clean `main` branch and
clean Git index/worktree before artifact generation; exact artifact
diff; post-deploy smoke test.

If a gate fails, stop. Do not use `--force`, substitute another export,
include unrelated staged files, or retry against a different artifact.

## Belirsizlik kuralı
Seviye belirsizse bir ÜST seviye uygulanır. "Level A sanmıştım" geçerli mazeret değildir.
