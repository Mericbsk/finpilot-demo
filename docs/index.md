# FinPilot Doküman İndeksi — "Hangi soruya hangi doküman?"
Durum: AKTİF · Sürüm: 1.0 · Güncelleme: 2026-07-24
_Bu dosya eski bir README kopyasıydı; 2026-07-24'te gerçek indekse dönüştürüldü (Bölüm 5). Kural: aynı soruya iki otorite gösteren her satır bir P0 çelişkidir._

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
