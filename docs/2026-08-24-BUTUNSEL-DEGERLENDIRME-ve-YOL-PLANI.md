# FinPilot + FinSense — Bütünsel Değerlendirme ve Yol Planı
### Tüm proje (tek oturum değil) · 2026-08-24 · kanıt: taze repo taraması

---

## 0. Manşet: iki büyük bulgu

**🎉 BULGU 1 — Lansmanın en zor teknik şartı TAMAMLANDI.**
`LAUNCH_CHECKLIST.md:6` → **Şart 1: 10 ardışık işlem günü kesintisiz brif yayını — TAMAMLANDI** (14 Ağu doğrulama, `broadcast_queue` DB sorgusu; 3-7 Ağu + 10-14 Ağu). Git'te 14 `daily snapshot` commit'i, sonuncusu 2026-08-24. Yani **yayın makinesi gerçekten çalışıyor.** Aylardır peşinde olduğun metrik düştü.

**⚠️ BULGU 2 — FinSense sürüm kontrolü DIŞINDA (kritik risk).**
`Finsense/.git` klasörü var ama **`objects/` dizini YOK** → `git` onu repo olarak tanımıyor ("fatal: not a git repository"). Sonuç: **FinSense'in hiç commit geçmişi, hiç yedeği yok.** 33 py + 37 md + 29 korpus dosyası + bu oturumda yapılan tüm düzeltmeler yalnız diskte duruyor. Hatırla: `academy.db` bu projede **zaten bir kez bozuldu**. Aynı şey kod tarafında olursa geri dönüş yok.

---

## 1. Bugünkü envanter (taze ölçüm)

### FinPilot (Borsa) — 319 commit, Ara 2025 → 24 Ağu 2026
| Alan | Büyüklük | Not |
|---|---:|---|
| tests | 109 py | Test kültürü gerçek (66→109 büyümüş) |
| scripts | 67 py | Operasyon |
| research | **57 py** | 12→57: araştırma temposu çok yüksek |
| drl | 45 py | Araştırma, muhtemelen park |
| api | 36 py | Backend |
| core | 34 py | Orkestrasyon |
| scanner | 24 py | Sinyal motoru (çekirdek) |
| agents | 23 py | Ürün ajanları |
| distribution | 19 py | Yayın hattı (lansmanın kalbi) |
| academy | 14 py | FinPilot-içi runtime köprü |
| auth / llm / execution / migrations | 9 / 9 / 6 / 4 | |
| web | 92 ts/tsx | Next.js 16 + React 19 |
| **kök py** | **81** | Dağınıklığın ana kaynağı |
| **dokümanlar** | **354** | 30 kök md + 190 docs + 134 reports |

### FinSense — git YOK
| Alan | Büyüklük |
|---|---:|
| academy py | 17 (+7 agents, +6 rag) |
| RAG korpus | 29 md |
| toplam py / md | 33 / 37 |

---

## 2. Ne başardın (dürüst bilanço)

**Gerçekten çalışan, kanıtlı varlıklar:**
1. **Yayın makinesi** — 10 günlük kesintisiz seri + günlük snapshot commit'leri. Otomasyon ayakta.
2. **Gerçek karne** — bariyer-tabanlı beklenti **+%0.40**, isabet **%30.1**, asimetri **3.36x**, **n=5206**. Bu uydurma değil, ölçülmüş bir geçmiş performans. Sektörde nadir bir dürüstlük varlığı.
3. **Compliance-first kimlik** — Grade dili, BUY/SELL yasağı, her yüzeyde disclaimer, prepublish gate, audit log.
4. **Governance katmanı** — AGENTS.md, _instructions, docs/INDEX.md, decision-log; Level A/B/C disiplini. Tek kişi için olağanüstü.
5. **Canlı web** — finpilot.at + /demo, Morning Ledger tasarımı, TR/EN/DE, güvenlik başlıkları.
6. **FinSense içerik fabrikası** — RAG + atıf + kalite kapısı + otomatik revizyon (bu oturumda onarıldı/geliştirildi).
7. **Araştırma disiplini** — Evidence Pipeline doktrini, PIT/SEC altyapısı, 134 rapor, negative-control farkındalığı.
8. **Ortak beyin (.finpilot)** — Work Item/Handoff/Evidence + handoff.py + HITL kapıları.

**Bu oturumda eklenenler:** web compliance P0/P1 (metadata Grade diline, sahte rating silindi, guard test, lang senkronu, prod CSP), methodology tema, sitemap, ortak-beyin iskeleti, DURUM.md, 6 denetim/strateji dokümanı.

---

## 3. Asıl teşhis: ne eksik?

### 3.1 Kalan lansman blokörleri ÇOĞUNLUKLA TEKNİK DEĞİL
`LAUNCH_CHECKLIST` durumu: Şart 1 ✅ · Şart 3/4/5 ~kısmi · Şart **2, 6, 7, 8, 9, 10 açık**.
Bunlardan **7 (≥25 takipçi + ≥10 beta) ve 8 (≥15 feedback + 2 Cuma ritüeli)** saf **dağıtım ve kullanıcı** işi. 6 (içerik kalitesi: 3 dış okuyucu) ve 10 (kırmızı-gün tatbikatı) da insan işi.
→ **Sonuç: Kod yazarak lansmanı bitiremezsin. Kalan yol insan/dağıtım yolu.** Bu, projenin bugünkü en önemli stratejik gerçeği.

### 3.2 Sıfır kullanıcı = doğrulanmamış ürün
Mühendislik 8/10, ticari doğrulama 0/10. Kimse kullanmıyor, kimse ödemiyor, geri bildirim yok. Tüm kalite iddiaları henüz **iç kanıt**.

### 3.3 Analiz katmanı üretimden hızlı büyüyor
354 doküman, 134 rapor, 57 research py. Kıyas: distribution 19 py, scanner 24 py. **Düşünme/denetleme, inşa etmeyi geçti.** Bu oturum bile 6 doküman ekledi. Sağlıklı bir refleksin (kanıt kültürü) aşırı-uzamış hali.

### 3.4 Yapısal borçlar (bilinen, planlı)
81 kök script, iki Academy runtime (drift riski), 23 ajan, tek-kişi bus factor, gerçek CI şüphesi, web'de düşük test kapsamı.

### 3.5 FinSense'in git'sizliği (yeni, kritik)
Yedeksiz, geçmişsiz, geri alınamaz. En ucuz düzeltilebilecek en büyük risk.

---

## 4. Beyin fırtınası: hangi yol?

Üç gerçekçi rota var. Kaynak tek kişi olduğu için **aynı anda yalnız biri** seçilebilir.

| Rota | Ne demek | Artı | Eksi |
|---|---|---|---|
| **A. Dağıtım/kullanıcı** | Kalan lansman şartlarını insan işiyle kapat: kanal büyüt, beta kullanıcı, 15 geri bildirim, 3 dış okuyucu | Lansmanı gerçekten bitirir; ürünü doğrular; yatırım tezini (disiplin+traction) kurar | Kod değil; konfor alanının dışı |
| **B. Teknik borç temizliği** | 81 script arşivi, Academy authority kararı, CI, doküman göçü | Bakım maliyetini düşürür; 6 ay sonraki seni kurtarır | Kullanıcı getirmez; lansmanı ilerletmez |
| **C. Araştırma derinleşmesi** | Evidence Pipeline omurgası, negative control, locked OOS, A-sistemi paper trading | Entelektüel olarak en çekici; uzun vadeli hendek | En pahalı; kullanıcı getirmez; kendi park kuralına aykırı |

**Önerim: A → (kısa B) → C.** Gerekçe: teknik en zor şart (Şart 1) bitti; kalanlar insan işi. Kod yazmaya devam etmek, bitmiş bir işi tekrar bitirmeye çalışmak olur. B'nin yalnız **acil parçası** (git!) hemen yapılmalı.

---

## 5. YOL PLANI

### 🔴 BUGÜN — 30 dakika (pazarlıksız)
1. **FinSense'i git altına al.** `git init` + `.gitignore` (.venv, __pycache__, data/*.db, .env) + ilk commit + uzak yedek (GitHub private). *Sebep: tek geri-dönüşsüz risk bu.*
2. Bu oturumun web değişikliklerini commit+push et; canlıda metadata'yı doğrula.

### 🟡 ÖNÜMÜZDEKİ 2 HAFTA — "Lansmanı bitir" (Rota A)
Tek hedef: kalan 6 şart. Kod yok, insan var.
- **Şart 7:** kanal büyütme (≥25 takipçi) + ≥10 beta kullanıcı daveti. Günde 30 dk dağıtım.
- **Şart 8:** ≥15 geri bildirim + 2 Cuma ritüeli.
- **Şart 6:** 3 dış okuyucuya brif kalitesi okut (variety raporu zaten var).
- **Şart 2:** sabah operasyonunu ölç (≤15 dk/gün) — süre logu.
- **Şart 3:** mobil 3-cihaz testi.
- **Şart 9:** premium mekaniği test modunda uçtan uca.
- **Şart 10:** kırmızı-gün tatbikatı (1 kez).
- **Kural:** bu 2 hafta içinde yeni sistem, yeni ajan, yeni araştırma **YOK**.

### 🟢 LANSMAN SONRASI — 1 hafta "Büyük Temizlik" (Rota B)
- 81 kök script → `research/<konu>/` + `experiments/` (git mv, hygiene raporundaki batch planı).
- **Academy authority kararı**: bridge kalsın mı, Finsense'e cutover mı (decision-log'da pending).
- 354 doküman → taksonomi (`docs/audits/`, `docs/plans/`, `archive/`), supersession tablosu.
- Gerçek CI (test+lint her push) + web smoke testleri.
- Ajan sayısını lansman-çekirdeğine indir.

### 🔵 3-6 AY — Ürün + Araştırma (Rota C, kontrollü)
- Geri bildirime göre ürün iterasyonu (kullanıcı verisiyle, tahminle değil).
- **Evidence Pipeline ince omurgası**: registry (write-once) + negative-control preflight + tek adayın uçtan uca yürütülmesi.
- A-sistemi (özel trading beyni) **paper modda** uzun koşu + karne. Gerçek paraya geçiş yok.
- FinSense kalitesi: korpus büyütme, eval harness.

### ⚫ 1-3 YIL — Kuzey Yıldızı
Kişiselleştirme → çok dil/mobil → (regülasyon ve ekiple) danışmanlık katmanı → ölçek. Bunlar **hedef**, bugünün listesi değil.

---

## 6. Tek cümlelik hüküm
**Teknik olarak hazırsın, ticari olarak doğrulanmamışsın.** En zor şartı (10 günlük seri) bitirdin ve elinde gerçek bir karne var; kalan lansman yolu kod değil, insan yolu. Tek acil teknik iş: FinSense'i git altına almak. Sonra 2 hafta boyunca tek iş: **kullanıcı**.
