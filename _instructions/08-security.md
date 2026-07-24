# FinPilot AI Operating Standard
## 08 — Security & Secrets

Version: 1.0 · Status: DRAFT — Meriç onayı bekliyor (CORE-006)
Authority Level: GLOBAL · Owner: Governance · Last Updated: 24 July 2026

## Kurallar

1. **Secrets asla dosyaya/rapora/commit'e açık yazılmaz.** API anahtarı, bot token'ı, SMTP şifresi, session secret — yalnız `.env` (gitignore'lu) veya Render/Vercel environment panelinde yaşar. AI raporlarında secrets maskelenir (`***`).
2. **Sızıntı protokolü:** bir secret ekran görüntüsüne, log'a veya git geçmişine girdiyse → derhal rotasyon (eski anahtar iptal) → decision-log'a kayıt → geçmiş temizliği ileri iş olarak notlanır. (Emsal: 2026-07 SMTP rotasyonu.)
3. **AI hiçbir koşulda emir/para hareketi başlatmaz** (Level C — 05-escalation). Alpaca anahtarları paper hesap bile olsa AI tarafından trade çağrısında kullanılmaz.
4. **Kullanıcı verisi** (e-posta, telegram id) rapor ve dokümanlara yalnız gerekliyse ve maskelenerek girer.
5. **Bağımlılık güvenliği:** yeni paket eklemek Level B'dir; pin'lenir (requirements.txt), bilinen-açık taraması (pip-audit/trivy) mevcut CI alışkanlığına dahildir.
6. **Yedekler** (backups/, dış ayna) DB kopyaları içerir — secrets içermez; dış ayna klasörü de OneDrive-dışı ve makine-yerel tutulur.

## Bilinen açık uçlar (takip)
- Git geçmişinde eski SMTP izleri olabilir → `git filter-repo` temizliği lansman sonrası işi (PARKING_LOT).
- `.env` dosyasının kendisi hiçbir zaman commit'lenmediği her kapıda `git status` ile teyit edilir.
