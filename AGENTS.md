# AGENTS.md — FinPilot AI Bootstrap (tüm ajanlar)

Version: 1.0 · Status: DRAFT — Meriç onayı bekliyor (CORE-006)
Owner: Governance · Applies to: Claude Code, Cowork, Copilot, Cursor ve diğer tüm AI ajanları

Bu dosya CLAUDE.md'nin Startup Sequence 1. adımının işaret ettiği bootstrap'tır.

## Açılış sırası (her görevde)

1. `_instructions/00-core.md` — GLOBAL kurallar (CORE-001…012). Çelişkide bu kazanır.
2. `docs/INDEX.md` — "hangi soruya hangi doküman" otorite haritası.
3. `docs/governance/decision-log.md` — bu konuda geçmiş karar var mı?
4. Göreve uygun otorite doküman: ops → `YONERGE.md` · durum → `LAUNCH_CHECKLIST.md` · plan → aktif Uygulama Planı.
5. Ancak bundan sonra üret. Çıktının hangi dosyaya/klasöre gireceğini belirt.

## Escalation (özet — detay: _instructions/05-escalation.md)

- **Level A (otonom):** salt-okunur analiz, rapor, test yazımı, yeni izole dosya.
- **Level B (öneri+onay):** üretim-kritik dosya değişikliği (publish zinciri, scanner sözleşmesi, web canlı yüzeyi) — değişiklik yapılır, kapı raporunda diff ile sunulur, Meriç onayı olmadan bölüm kapanmaz.
- **Level C (insan zorunlu):** yayın kararı, para/işlem hareketi, governance değişikliği, sözleşme alanı silme, geri dönüşsüz veri işlemi.

## Kırmızı çizgiler (kısa)

- Yasak dil (al/sat/hedef fiyat) hiçbir yüzeye — mock dahil — giremez (YONERGE §12).
- Secrets hiçbir dosyaya/rapora açık yazılmaz (08-security.md).
- Karar, decision-log'a yazılmadan "verilmiş" sayılmaz.
- Uygulanmayan karar çelişki üretir: her kararda uygulama sahibi + tarih + kanıt zorunlu.
