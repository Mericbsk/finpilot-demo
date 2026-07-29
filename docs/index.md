# FinPilot Doküman İndeksi — "Hangi soruya hangi doküman?"
Durum: AKTİF · Sürüm: 1.1 · Güncelleme: 2026-07-29
_Bu dosya eski bir README kopyasıydı; 2026-07-24'te gerçek indekse dönüştürüldü (Bölüm 5). Kural: aynı soruya iki otorite gösteren her satır bir P0 çelişkidir._
_2026-07-29: aşağıya makine-okunur bir manifest eklendi (`scripts/lint_authority_map.py` bunu ağaçla karşılaştırır) — Level B, Meriç onayı bekliyor; bkz. `docs/2026-07-29-otorite-haritasi-gocu-plani.md` ve decision-log._

## Otorite haritası

| Soru | Tek otorite doküman | Rol |
|---|---|---|
| AI ajanları hangi kurallarla çalışır? | `_instructions/00-core.md` | GLOBAL kural seti (CORE-001…012) |
| Ajan açılış sırası / hangi dosyalar okunur? | `AGENTS.md` (kökte) | Bootstrap |
| Günlük operasyon nasıl yürür? (yayın ritüeli, sözleşme, kırmızı çizgiler) | `YONERGE.md` | OPS anayasası |
| Şu an neredeyiz? (DoD, kapılar, seri sayacı) | `LAUNCH_CHECKLIST.md` | DURUM panosu |
| Hangi karar ne zaman, neden verildi? | `docs/governance/decision-log.md` | Karar sicili |
| Bölüm kapıları ve kanıtları | `docs/reports/BOLUM-*_raporu_*.md` | Kapı kayıtları |
| Genel sağlık / audit geçmişi | `docs/audits/` + kökteki tarihli audit dosyaları | Tarihsel denetim |
| Uygulama sırası (0→6 bölüm planı) | `FinPilot_UcaUca_Uygulama_Plani_2026-07-24.md` | Aktif plan |
| Lansmana kadar dokunulmayacak fikirler | `PARKING_LOT.md` | Kapsam kilidi |
| Sözlük içeriği (landing/Telegram) | `distribution/glossary.py` | TEK kaynak — `terms.ts` ve concepts türevdir (`python scripts/gen_terms_ts.py`) |
| Akademi ders içeriği | FinSense repo (`academy/`) → `web/public/academy_lessons.json` | Üretici → türev |
| Eski dashboard sözlüğü | `web/public/dictionary.json` | LEGACY — yalnız dashboard/finsense sayfaları; landing BUNU KULLANMAZ |
| Strateji/GTM | `docs/strategy/` + kök GTM/Funnel dosyaları (taşınacak) | Yön |

## Emekli / bayat kayıtlar
- DB tabloları `signals`, `scan_results`, `buy_signals`, `execution_*` → **EMEKLİ** (Karar C, 2026-07-24, decision-log). Şema durur, yeni kod kullanmaz.
- `FinPilot_Hafta1_Yonerge_2026-07-05.md` cron bölümü → SUPERSEDED (07-17 manuel karar; YONERGE geçerli).
- `FinPilot_Tam_Sistem_Audit_2026-07-03.md`, `YAYIN_P0_ADIM_PLANI.md`, MorningLedger/Master-Tasarım/WebMVP/TgBot/3x-şablon planları → tarihî değer, arşive taşınacak (taşıma listesi: BOLUM-5 raporu).

## Audit log formatı
`tarih · ne denetlendi · bulgu (P0/P1) · ne değişti · onaylayan` — her kapı raporunun sonunda.

| Tarih | Denetim | P0/P1 | Sonuç |
|---|---|---|---|
| 2026-07-23 | Tam sistem ReAudit | 5 P0 | Skor 54/100 |
| 2026-07-24 | Ön-tarama + teşhis paketi | 2 yeni P0 (NUL, degraded-run) | Skor ~60/100; Bölüm 0-1-3-4 kapıları |

## Makine-okunur otorite manifesti (CI: `scripts/lint_authority_map.py` doğrular)

Durum: **Level B — DRAFT, Meriç onayı bekliyor.** Bu blok, yukarıdaki insan-okunur
tabloyla aynı gerçeği tek bir makine-ayrıştırılabilir yapıda tutar (CORE-003: tek
kaynak, iki okuyucu — insan ve CI). `status` alanı: `active` (gerçek ve zorunlu),
`draft` (kendisi henüz onaylanmamış `_instructions/` dosyası), `gap` (referans
verilen otorite dokümanı repoda yok — icat edilmedi, açıkça işaretlendi, CORE-004),
`external` (başka bir repoda yaşıyor).

```json
{
  "version": 1,
  "updated": "2026-07-29",
  "entries": [
    {
      "id": "core-rules",
      "concept": "AI ajan calisma kurallari (GLOBAL, celiskide kazanir)",
      "authority_path": "_instructions/00-core.md",
      "status": "active",
      "owner": "governance",
      "applies_to": ["**/*"]
    },
    {
      "id": "governance-doc-authority",
      "concept": "Dokuman otorite hiyerarsisi ve versiyonlama standardi",
      "authority_path": "_instructions/01-governance.md",
      "status": "draft",
      "owner": "governance",
      "applies_to": ["_instructions/**/*", "docs/governance/**/*"],
      "note": "Dosyanin kendi basligi Status: DRAFT diyor (CORE-006 onayi bekliyor)."
    },
    {
      "id": "escalation",
      "concept": "Level A/B/C siniflandirmasi",
      "authority_path": "_instructions/05-escalation.md",
      "status": "draft",
      "owner": "governance",
      "applies_to": ["**/*"],
      "note": "Dosyanin kendi basligi Status: DRAFT diyor (CORE-006 onayi bekliyor)."
    },
    {
      "id": "security",
      "concept": "Secrets ve guvenlik kurallari",
      "authority_path": "_instructions/08-security.md",
      "status": "draft",
      "owner": "governance",
      "applies_to": ["**/*"],
      "note": "Dosyanin kendi basligi Status: DRAFT diyor (CORE-006 onayi bekliyor)."
    },
    {
      "id": "ops-charter",
      "concept": "Gunluk operasyon, yayin ritueli, scanner<->distribution sozlesmesi, kirmizi cizgiler",
      "authority_path": "YONERGE.md",
      "status": "active",
      "owner": "governance",
      "applies_to": ["scanner/**/*", "distribution/**/*", "api/**/*", "web/**/*"]
    },
    {
      "id": "decision-log",
      "concept": "Karar sicili",
      "authority_path": "docs/governance/decision-log.md",
      "status": "active",
      "owner": "governance",
      "applies_to": ["**/*"]
    },
    {
      "id": "launch-status",
      "concept": "Lansman durum panosu (yalnizca durum, kural koymaz)",
      "authority_path": "LAUNCH_CHECKLIST.md",
      "status": "active",
      "owner": "governance",
      "applies_to": []
    },
    {
      "id": "strategy",
      "concept": "Mission / roadmap / growth-grant stratejisi",
      "authority_path": null,
      "status": "gap",
      "owner": "governance",
      "applies_to": ["docs/strategy/**/*"],
      "note": "Tek bir mission.md/roadmap.md yok; docs/strategy/ sadece 2 dagitik dosya icerir. Otorite dokuman olusturulmasi ayri bir Level B karari gerektirir."
    },
    {
      "id": "product-rules",
      "concept": "Composite score, scanner filtreleri, entry/exit esikleri",
      "authority_path": null,
      "status": "gap",
      "owner": "governance",
      "applies_to": ["scanner/**/*", "distribution/**/*"],
      "note": "composite-score.md / entry-exit-rules.md yok; kural su an yalnizca kodda (scanner/, distribution/) ve YONERGE.md SS2 sozlesme alanlarinda yasiyor."
    },
    {
      "id": "engineering-architecture",
      "concept": "Mimari, execution sistemi, event akisi",
      "authority_path": null,
      "status": "gap",
      "owner": "governance",
      "applies_to": ["api/**/*", "core/**/*", "web/src/**/*"],
      "note": "architecture.md yok; en yakin karsilik YONERGE.md SS2 (sozlesme) + kodun kendisi."
    },
    {
      "id": "risk-policy",
      "concept": "Risk & Compliance politikasi (Layer 2, her seyi veto edebilir)",
      "authority_path": null,
      "status": "gap",
      "owner": "governance",
      "applies_to": ["docs/governance/**/*"],
      "note": "risk-policy.md yok; en yakin karsilik YONERGE.md SS12 (Kirmizi Cizgiler) + _instructions/00-core.md CORE-002."
    },
    {
      "id": "research",
      "concept": "Backtest, akademik ve GitHub kanit arastirmasi",
      "authority_path": "reports",
      "status": "active",
      "owner": "research",
      "applies_to": ["research/**/*", "reports/**/*"]
    },
    {
      "id": "content-glossary",
      "concept": "Sozluk / kullanici-yuzu terminoloji (landing + Telegram)",
      "authority_path": "distribution/glossary.py",
      "status": "active",
      "owner": "content",
      "applies_to": ["distribution/glossary.py", "web/src/app/academy/**/*", "web/public/dictionary.json"],
      "note": "web/public/dictionary.json LEGACY'dir (yalnizca dashboard/finsense); landing bunu kullanmaz."
    },
    {
      "id": "academy-content",
      "concept": "Finance Academy ders icerigi",
      "authority_path": "academy",
      "status": "active",
      "owner": "content",
      "applies_to": ["web/public/academy_lessons.json"]
    },
    {
      "id": "releases",
      "concept": "Yayin notlari, rollout log, test sonuclari",
      "authority_path": null,
      "status": "gap",
      "owner": "governance",
      "applies_to": ["docs/reports/BOLUM-*"],
      "note": "Ayri bir 06-releases konsepti yok; en yakin karsilik docs/reports/BOLUM-*_raporu_*.md kapi kayitlari. 'Live/shipped' iddiasi her zaman Level C (05-escalation.md)."
    }
  ]
}
```
