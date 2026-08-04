# Otorite-Haritası Göçü — Uçtan-Uca Plan

Sürüm: 1.0 · Durum: **DRAFT — Meriç onayı bekliyor (CORE-006)** · Owner: Governance
Kapsam: AI talimat dosyalarını "sabit klasör varsayımı"ndan "dinamik otorite-haritası" modeline geçirmek.
Otorite: `_instructions/00-core.md` (CORE-003 Tek Kaynak, CORE-009 Minimal Değişim) · Harita: `docs/INDEX.md`

---

## 1. Değerlendirme (öneri bize uygun mu?)

**Uygun — ve büyük kısmı zaten uygulanmış.** Öneri: "talimatlar repo'ya uyar, repo talimata değil;
ajan klasör ismi varsaymaz, önce haritayı okur." Bu, `AGENTS.md` v1.0'da hâlihazırda var:
`00-core → docs/INDEX.md → decision-log → göreve uygun otorite`. Eksik olan yeni mimari değil;
**yarım kalmış bir göç.**

### Kök sorun: iki governance nesli çatışıyor

| Nesil | Dosyalar | Model | Durum |
|---|---|---|---|
| **Gen-2 (doğru)** | `AGENTS.md`, `docs/INDEX.md`, `docs/governance/decision-log.md`, `YONERGE.md`, `LAUNCH_CHECKLIST.md`, `_instructions/*` | Dinamik harita (INDEX.md) | Canlı, tutarlı |
| **Gen-1 (kırık)** | `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md` (7), `CLAUDE.md` (kısmen) | Sabit numaralı klasörler (`00-strategy…06-releases`) | **Hayalet — o klasörler hiç yok** |

### Kanıt (mevcut durum)

- Var: `AGENTS.md`, `CLAUDE.md`, `_instructions/{00-core,01-governance,05-escalation,08-security}.md`,
  `YONERGE.md`, `LAUNCH_CHECKLIST.md`, `docs/INDEX.md`, `docs/governance/decision-log.md`.
- `00-core.md` CORE-001…015 tanımlı (CORE-003 Single Source of Truth, CORE-012 Authority Before Memory dahil).
- **Yok / kırık:** `/00-strategy … /06-releases` (7 klasör), `_instructions/core-rules.yaml`,
  `.github/copilot-instructions.md`'deki `/00-core.md` kök yolu (gerçeği `_instructions/00-core.md`).
- `.github/instructions/*` içindeki **7 `applyTo` glob'unun hepsi** olmayan klasörlere bakıyor → hiçbiri tetiklenmiyor.

**Sonuç:** AI'ın çelişkiyi bildirmesi doğruydu (CORE-005). Düzeltme = Gen-1'i Gen-2 modeline göçürmek.

---

## 2. Tasarım ilkeleri (dinamik yaklaşımın kendi riskini de kapat)

1. **Tek değişmez anchor.** `AGENTS.md` her ajanın ilk okuduğu, yeri asla değişmeyen boot dosyası.
   Tüm ajanlar (Claude, Copilot, Cursor, VS Code Agent) buradan başlar. Anchor sabit; gerisi dinamik.
2. **Tek harita.** `docs/INDEX.md` = "hangi soru → hangi otorite dosyası" tek kaynağı (CORE-003).
   Kimse klasör ismi varsaymaz; buraya bakar.
3. **Harita da kayabilir → guard şart.** "Klasör varsayma, haritayı oku" yaklaşımı, varsayım sorununu
   bir kat yukarı taşır: artık INDEX.md drift ederse aynı sorun oluşur. Bu yüzden **INDEX.md makine-okunur
   ve CI ile doğrulanır** olmalı (aşağıda Faz 5).
4. **Kopyalama yok (CORE-003).** Talimat dosyaları kuralı tekrarlamaz, otorite dosyasına **referans verir.**
   CLAUDE.md/copilot'un governance felsefesini kopyalaması bu ilkeye aykırı → kırpılır.
5. **Minimal, versiyonlu, onaylı (CORE-006/009).** Governance dosyaları overwrite edilmez; `vX.Y` +
   changelog ile versiyonlanır; Level B/C değişiklik Meriç onayı olmadan kapanmaz.

---

## 3. Hedef mimari (tüm ajanlar için tek boot)

```
Boot (her görev, her ajan)
  ↓
1. AGENTS.md            ← sabit anchor (yeri değişmez)
  ↓
2. _instructions/00-core.md   ← GLOBAL kurallar (çelişkide kazanır)
  ↓
3. docs/INDEX.md        ← otorite haritası (klasör varsayma; buradan bul)
  ↓
4. docs/governance/decision-log.md  ← bu konuda geçmiş karar?
  ↓
5. Göreve uygun otorite dosyası (INDEX.md'nin gösterdiği)
  ↓
6. Üret; Level (A/B/C) + hedef dosya belirt; kararı logla
```

---

## 4. Uçtan-uca adımlar (fazlar; her adımda Level ve sahip)

### Faz 0 — `docs/INDEX.md`'yi kanonik + lintable harita yap  · Level B · Governance
- INDEX.md'ye **yapısal bir manifest** ekle: her otorite için `path · authority · owner · precedence`.
  İnsan-okunur tablo + CI'ın parse edeceği fenced ```yaml``` blok (tek dosya, iki okuyucu; CORE-003).
- Alan-adı → **gerçek** kod yolu eşlemesini buraya yaz (örn. product→`scanner/**`, engineering→`api/**,core/**`,
  distribution→`distribution/**`, web→`web/**`). Hayalet numaralı klasör YOK; gerçek ağaç.
- Manifeste dahil: `AGENTS.md, _instructions/00-core.md, 01-governance.md, 05-escalation.md, 08-security.md,
  YONERGE.md, LAUNCH_CHECKLIST.md, docs/governance/decision-log.md`.

### Faz 1 — `.github/copilot-instructions.md` yeniden yaz  · Level B · Governance
- **Sil:** "Repository map" bloğundaki `/00-strategy … /06-releases`; `/00-core.md` kök yolu;
  `/_instructions/core-rules.yaml` referansı (Faz 4 kararına göre).
- **Koy:** kısa boot yönergesi —
  ```
  Read AGENTS.md first. Then _instructions/00-core.md.
  Locate the authority document from docs/INDEX.md.
  Do NOT assume folder names or repository structure.
  Follow the map; if the map and the tree disagree, STOP and report (CORE-005).
  ```
- Governance felsefesini **kopyalama**; `_instructions/00-core.md`'ye referans ver (CORE-003).

### Faz 2 — `.github/instructions/*.instructions.md` (7 dosya) düzelt  · Level B · Governance
- Her dosyanın `applyTo` glob'unu **gerçek** yola çevir (INDEX.md alan→yol eşlemesinden), örn.
  `applyTo: "02-engineering/**"` → `applyTo: "api/**,core/**"`. Karşılığı olmayan alan varsa dosyayı
  sadeleştir veya kaldır (Level B, gerekçeyle).
- İçerikte otorite dosyasına **referans**, kural tekrarı değil.

### Faz 3 — `CLAUDE.md` Startup Sequence'i hizala  · Level B · Governance
- Startup'a `docs/INDEX.md` ve `decision-log` adımlarını ekle (AGENTS.md ile aynı zincir).
- Sabit isim varsayımı yok. Governance felsefesi tekrarını kırp → AGENTS.md + 00-core'a referans.
- Versiyonla (v3.0 → v3.1, changelog).

### Faz 4 — Eksik referansları çöz  · Level B · Governance
- `_instructions/core-rules.yaml`: ya **oluştur** (CORE-001…015'in makine-okunur özeti) ya da tüm
  referansları kaldır. Öneri: oluştur — CI guard'ın da işine yarar.

### Faz 5 — Guardrail: harita ↔ ağaç senkron doğrulaması  · Level A · Engineering
- Yeni izole script `scripts/lint_authority_map.py`:
  1. INDEX.md manifestindeki her `path` diskte var mı?
  2. Her mevcut otorite dosyası manifeste listeli mi?
  3. Hiçbir talimat dosyası (CLAUDE.md, AGENTS.md, .github/**) olmayan bir path'e referans veriyor mu?
  4. `.github/instructions/*` `applyTo` glob'ları en az bir gerçek dizinle eşleşiyor mu?
- CI'a ekle (pre-commit + PR check). Kırmızıysa merge yok. Bu, "dinamik harita" modelini drift'e karşı korur.

### Faz 6 — Karar + onay  · Level C · Human (Meriç)
- `decision-log.md`'ye kayıt: "Governance talimatları dinamik otorite-haritası modeline göçürüldü;
  hayalet numaralı-klasör referansları kaldırıldı." (uygulama sahibi + tarih + kanıt: lint yeşil).
- `AGENTS.md` DRAFT → APPROVED (CORE-006).

---

## 5. Dokunulacak dosyalar

| Dosya | Eylem | Level | Sahip |
|---|---|---|---|
| `docs/INDEX.md` | manifest + alan→yol eşlemesi ekle (versiyonla) | B | Governance |
| `.github/copilot-instructions.md` | yeniden yaz (hayalet harita sil, boot yönergesi) | B | Governance |
| `.github/instructions/*.instructions.md` (7) | `applyTo` gerçek yola; içerik referansa | B | Governance |
| `CLAUDE.md` | Startup'a INDEX.md/decision-log; tekrar kırp; v3.1 | B | Governance |
| `_instructions/core-rules.yaml` | oluştur (ya da referansları kaldır) | B | Governance |
| `scripts/lint_authority_map.py` | yeni guard script + CI | A | Engineering |
| `docs/governance/decision-log.md` | göç kaydı | C | Human |
| `AGENTS.md` | DRAFT→APPROVED | C | Human |

---

## 6. Kabul kriterleri (doğrulama)

1. Repo genelinde **hiçbir** talimat dosyası olmayan bir path/klasöre referans vermiyor (`lint_authority_map.py` yeşil).
2. Dört ajan da (Claude/Copilot/Cursor/VS Code Agent) **aynı** boot zincirini izliyor: AGENTS.md → 00-core → INDEX.md → decision-log → otorite.
3. `docs/INDEX.md` her otorite dosyasını listeliyor; her `applyTo` en az bir gerçek dizinle eşleşiyor.
4. Governance kuralı hiçbir talimat dosyasında **kopyalanmıyor**, referansla veriliyor (CORE-003).
5. Değişiklikler versiyonlu; decision-log kaydı var; AGENTS.md APPROVED.

---

## 7. Rollout sırası ve onay kapıları

```
Faz 0 (INDEX.md manifest)  →  Faz 5 (lint script; önce guard'ı kur, sonra göç et)
      →  Faz 1–4 (talimatları göçür, her biri lint'e karşı)  →  Faz 6 (karar + onay)
```
- Guard'ı (Faz 5) **göçten önce** kur ki her fazı yeşil lint'e karşı doğrulayabilelim.
- Her Level B fazı kapı raporunda diff ile sunulur; Meriç onayı olmadan bölüm kapanmaz (AGENTS.md Level B).
- Faz 6 Level C — yalnız Meriç.

---

## 8. Kapsam dışı (bilinçli)

- Kod klasörlerini yeniden adlandırmak/taşımak YOK — plan talimatları **gerçek ağaca** uydurur, tersi değil.
- Yeni numaralı-klasör mimarisi kurmak YOK — o, sorunun kaynağıydı.
- İş kuralı/formül içeriği değişmiyor — yalnız "hangi ajan nereye bakar" yönlendirmesi düzeliyor.
