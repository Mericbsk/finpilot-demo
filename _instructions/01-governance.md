# FinPilot AI Operating Standard
## 01 — Governance & Document Authority

Version: 1.0 · Status: DRAFT — Meriç onayı bekliyor (CORE-006)
Authority Level: GLOBAL · Owner: Governance · Last Updated: 24 July 2026

## Otorite hiyerarşisi (çelişkide üstteki kazanır)

1. `_instructions/00-core.md` — değişmez çekirdek kurallar
2. `_instructions/` diğer standartlar (05-escalation, 08-security)
3. `YONERGE.md` — operasyon anayasası (nasıl çalışırız)
4. `docs/governance/decision-log.md` — verilmiş kararlar
5. `LAUNCH_CHECKLIST.md` — durum panosu (neredeyiz)
6. Aktif Uygulama Planı — sıradaki işler
7. Diğer tüm dokümanlar — referans/tarihsel

## Rol ayrımı (SSoT çatışması önleyici)

- `_instructions/` = AI'ların ÇALIŞMA KURALLARI. Operasyon detayı içermez.
- `YONERGE.md` = operasyonun TEK otoritesi. AI kuralı içermez, _instructions'a atıf verir.
- `LAUNCH_CHECKLIST.md` = yalnız DURUM. Kural koymaz.
- Bir kavramın otoritesi `docs/INDEX.md` haritasında bulunmuyorsa, önce haritaya eklenir.

## Doküman standartları

- Her otorite doküman başında: `Version · Status (DRAFT/ACTIVE/SUPERSEDED/ARŞİV) · Owner · Last Updated`.
- Supersede eden doküman, eskisinin başına `Superseded-by:` satırı ekletir — eski dosya silinmez.
- Aynı konuda ikinci doküman açmak yasak; mevcuda bölüm eklenir (CORE-003).
- Kararlar yalnız decision-log'da yaşar; formatı: bağlam · değişiklik · etki alanı · durum.
