# FinPilot — Manuel Yayın Akışı + Web Zenginleştirme Planı

> Sürüm 1.0 · 2026-07-17 · YONERGE ile uyumlu ("tek tarama → tek snapshot → tüm yüzeyler")

---

# BÖLÜM A — Otomatikten Elle Tek-Tarama Yayınına Geçiş

## Neden
Cron zinciri (07:15 tarama · 07:50 taslak · 08:30 yayın) kırılgan:
- Sabah geç başlayınca **yetişmiyor**.
- Yayın ve web için **ayrı ayrı, çakışan bildirimler** geliyor.
- Timing baskısı + kısmi çalışma = tutarsız sonuç.

## Çözüm: bir env + bir komut (scheduler'a dokunmadan)

**1) Tüm otomatik dağıtım job'larını sustur.** `.env`:
```
FINPILOT_ENABLE_DISTRIBUTION=0
```
Bu, scheduler'daki 07:15/07:50/08:30 job'larının hepsini no-op yapar (çünkü hepsi `distribution_enabled()` kontrol eder). Artık istenmeyen/çakışan DM yok.

**2) Elle çalışan tek komut ekle** — `scripts/publish_now.py`:
```python
"""Tek komut: taze export → snapshot(tr+en) → WEB + TELEGRAM. Cron yok, timing yok.

Kullanım (repo kökünde, önce tam taramanı yap):
    python scripts/publish_now.py --yes      # onayı atla (sen çalıştırdın = onay)
    python scripts/publish_now.py            # yayından önce Enter ile onayla
"""
from __future__ import annotations
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass

# Auto job'lar kapalı olsa bile bu MANUEL koşu için dağıtımı aç (yalnız bu process'te):
os.environ["FINPILOT_ENABLE_DISTRIBUTION"] = "1"

from distribution import broadcast
from distribution.jobs import job_draft, job_publish

def main() -> int:
    auto_yes = "--yes" in sys.argv
    d = job_draft()                       # snapshot (tr+en) + kuyruk + admin DM
    print("draft:", json.dumps(d, ensure_ascii=False, default=str))
    qid = d.get("free_queue_id")
    if not qid:
        print("❌ Taslak üretilemedi — büyük olasılıkla export taze değil. Önce tam tarama yap.")
        return 1
    if not auto_yes:
        try:
            input(f"#{qid} yayınlansın mı? Onaylamak için Enter, iptal için Ctrl+C...")
        except KeyboardInterrupt:
            print("\nİptal edildi."); return 1
    broadcast.decide(qid, approve=True, decided_by="manual")
    p = job_publish()                     # kanala gönder + web'e push
    print("publish:", json.dumps(p, ensure_ascii=False, default=str))
    print("✅ Bitti — Telegram kanalı + web (demo_snapshot.json) güncellendi.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

## Günlük akışın (2 adım, timing baskısı yok)
```
1) İstediğin saatte tam evren taramasını çalıştır (dashboard ya da POST /scan).
   → scan_export_latest.json taze yazılır.
2) python scripts/publish_now.py --yes
   → snapshot üretilir, Telegram'a gönderilir, web güncellenir. Tek çıktı, tek kaynak.
```

## Neden bu güvenli
- **Tek snapshot:** draft + publish aynı `build_snapshot` koşusundan → web ve Telegram **aynı adaylar** (YONERGE §5).
- **Onay = sen:** komutu sen çalıştırdın; `--yes` ile onay adımı sende. Bot runner'a gerek yok.
- **Çakışan bildirim yok:** cron kapalı; yalnız senin komutun konuşur.
- **Lint korunur:** `job_draft` içindeki metin lint'i aynen çalışır.

> Not: `telegram_bot_runner.py` artık zorunlu değil (onay komutta). İstersen tamamen kapat.

---

# BÖLÜM B — Web Zenginleştirme Planı

## Mevcut durum (dürüst tespit)
Web **UI'ı zaten sofistike**: "Ledger" (finans gazetesi) teması, zengin bileşen seti —
`Masthead · EditionArticle · DailyDouble · Newsroom · LedgerStrip (karne) · GradeSeal ·
HowItsMade · ClassroomPreview · EditorialStance · LanguageSwitcher + i18n`.

**Zayıf görünmesinin sebebi UI değil, VERİ:** sözleşme regresyonu yüzünden canlıda
`badges:[]`, `company:""`, `grade` hep "B", `prob_band:"—"`, `karne.by_grade:{}`.
Yani bileşenler var ama besleyecek veri boş → jenerik/tekdüze görünüyor.

## En büyük kazanç: kod değil, VERİ (P0)
**Sözleşmeyi geri yükle → temiz tam tarama →** aşağıdakiler mevcut UI'da otomatik canlanır:
- `badges` → aday kartlarında **spesifik rozet çipleri** (squeeze, gap, RVOL, momentum…)
- `grade A/B/C` → **GradeSeal** mührü farklılaşır (şu an hepsi B)
- `company` → şirket adları (şu an boş)
- `prob_band` → olasılık bandı
- `karne.by_grade` → **LedgerStrip** gerçek skor kartıyla dolar

Bu, **hiç yeni kod yazmadan** en büyük görsel sıçramadır.

## Katman katman zenginleştirme (öncelikli)

### P1 — Güven ve okunabilirlik (impact yüksek)
1. **Karne (track record) şeridi — en kritik güven öğesi.** `by_grade` gerçek veriyle
   doldur: grade bazında isabet oranı, ortalama getiri, örneklem sayısı. Dürüst,
   şeffaf skor kartı = ikna edici tek şey. (LedgerStrip'i gerçek veriyle besle.)
2. **Aday kartı zenginliği:** rozet çipleri + GradeSeal + risk notu (var) + tek-cümle
   gerekçe (var). Ekle: **mini spark-line** (son 5-10 gün fiyat, PriceChart mevcut).
3. **"İts" düzeltmesi (küçük ama görünür):** rationale motorundaki `_cap`, Türkçe i→İ
   kuralını EN/DE'ye de uyguluyor → "İts composite". Dil-farkında yap:
   ```python
   def _cap(s, lang="tr"):
       if not s: return s
       if lang == "tr":
           if s[0]=="i": return "İ"+s[1:]
           if s[0]=="ı": return "I"+s[1:]
       return s[0].upper()+s[1:]
   ```
   (Çağrı yerlerine `lang` geçir.)

### P2 — Derinlik ve keşif
4. **Metodoloji sayfası** (DoD Hafta 2): "nasıl üretiliyor, ne DEĞİL" — `config_sha`,
   barrier audit, skor mantığı. `HowItsMade` bileşenini tam sayfaya genişlet. Güven + SEO.
5. **Sözlük entegrasyonu (Classroom):** 30 terim, çok dilli, tıkla-öğren (TermCard +
   GlossaryTooltip mevcut). Gerekçe içindeki terimleri tooltip'le bağla → eğitim değeri.
6. **Dil anahtarı doğrulama:** JSON'da `rationale_i18n` var, `LanguageSwitcher` var —
   UI'ın gerçekten `rationale_i18n[locale]`'i gösterdiğini test et (TR/EN/DE geçişi).
7. **Arşiv / geçmiş sayılar:** "dünün baskısı" kavramı zaten var; geçmiş snapshot'ları
   gezilebilir yap → içerik derinliği + geri-gel sebebi.

### P3 — Cila ve büyüme
8. **Mobil 3-cihaz testi** (DoD #3) + tipografi/boşluk cilası (Ledger teması güçlü,
   tutarlılık şart).
9. **Gözlemlenebilirlik:** Plausible (analytics) + Sentry (hata) — hangi bölüm ilgi
   çekiyor, nerede kopuyor.
10. **Build-in-public anlatısı:** `EditorialStance` + `Newsroom` ile şeffaf hikaye;
    sosyal kanıt (kanal takipçi sayısı, karne yaşı).
11. **PWA:** `PWAInstallButton` var — "ana ekrana ekle" ile geri-dönüş.
12. **Premium teaser:** `FullEditionTeaser` — ücretsiz top-3 + "tam sürüm" merakı.

## Öncelik özeti (impact × emek)

| Öncelik | İş | Emek | Etki |
|---------|----|----|----|
| P0 | Sözleşme geri → veri dolar → UI canlanır | Orta | **Çok yüksek** |
| P1 | Karne şeridi gerçek veri · rozet çipleri · spark-line · "İts" fix | Orta | Yüksek |
| P2 | Metodoloji sayfası · sözlük tooltip · dil anahtarı testi · arşiv | Orta-yüksek | Yüksek |
| P3 | Mobil cila · Plausible/Sentry · PWA · premium teaser | Düşük-orta | Orta |

## Tek cümle
Web'in "daha zengin/güzel" olmasının **%80'i yeni tasarım değil, mevcut zengin bileşenleri
gerçek veriyle beslemek**tir (sözleşme + karne). Kalan %20 = metodoloji sayfası, sözlük
entegrasyonu, mobil cila ve dürüst track-record görselleştirmesi.
