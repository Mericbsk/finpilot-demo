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
AI öneri hazırlar, UYGULAMAZ; Meriç açıkça onaylayıp kendisi çalıştırır veya yazılı onay verir.
Kapsam: yayın/publish kararının kendisi · para veya emir hareketi (Alpaca dahil — mevcut politika: AI asla emir iletmez) · governance/authority doküman değişikliği · sözleşme alanı silme/yeniden adlandırma · geri dönüşsüz veri işlemleri (silme, tarihsel kayıt değiştirme) · secrets rotasyonu.

## Belirsizlik kuralı
Seviye belirsizse bir ÜST seviye uygulanır. "Level A sanmıştım" geçerli mazeret değildir.
