# FinPilot "Dikkat Haritası" (Attention Map) — İçerik Paketi (Taslak)

Durum: **TASLAK — canlı hiçbir yüzeye bağlanmadı.**
Tarih: 2026-08-24
Kapsam: methodology sayfası metni, demo kart metni, Telegram brif örneği, EN varyant notu.

Bu paket, `docs/2026-08-15-master-prompt-finpilot-attention-map.md`'nin Adım 4'ünde
listelenen "kullanıcıya-görünür yüzeyleri yeni çerçeveye göre güncelle" işinin somut
içerik tarafını karşılar. Kod/wiring değişikliği İÇERMEZ — sadece metin.

**Neden henüz canlıya bağlanmadı:** `docs/governance/decision-log.md`'deki en güncel
kayıt (2026-08-14, Faz 1c) göre export-formülü (§1.1) ile üretim-formülünün (§1.3)
gerçekten aynı şeyi ölçtüğü hâlâ kanıtlanmadı — `data/price_cache/`'in shortlist
sembollerini kapsayacak şekilde gerçek ağ erişimiyle çekilmesi ve
`research/attention_score_formula_overlap_2026_08_14.py`'nin o veriyle yeniden
çalıştırılması gerekiyor. Bu metin, o kanıt tamamlanmadan hiçbir kullanıcıya
gösterilmemeli (bkz. master prompt Adım 3.8: "kullanıcıya-görünen her yeni vaat açık
onay gerektirir").

**Yan bulgu — mevcut lint kuralında yanlış-pozitif:** `distribution/lint.py`'nin kendi
`DISCLAIMER_EN` sabiti (`"...does not guarantee future results."`) kendi `guarantee`
kuralına takılıyor — regex negasyonu ("does not guarantee") ayırt etmiyor. Bu, canlı
`methodology/page.tsx`'in mevcut İngilizce disclaimer satırında da aynı şekilde var
(bu paketin yazarı tarafından düzeltilmedi — sadece raporlanıyor, CLAUDE.md "hiçbir
çelişkiyi sessizce çözme" kuralı gereği). `DISCLAIMER_TR` bu sorunu yaşamıyor.

Tüm metinler `distribution/lint.py::check_text` ile test edildi — al/sat dili, hedef
fiyat, garanti, FOMO, kişiselleştirilmiş tavsiye, getiri vaadi kalıpları yok
(doğrulama bu dokümanın sonunda).

---

## 1) Methodology sayfası — taslak İngilizce metin

`web/src/app/methodology/page.tsx`'in mevcut yapısını (H2/P bileşenleri, "Ledger"
editoryal tonu, madde 1-6 düzeni) birebir korur; içerik "yön tahmini" çerçevesinden
"olağan dışılık tespiti" çerçevesine geçirilmiştir. Mevcut dosya DEĞİŞTİRİLMEDİ — bu,
o dosyanın yerini alacak bir taslaktır.

```
How FinPilot works

Transparency is the product. This page explains how we scan, flag and verify —
and why we show our misses, not just our wins.

1 · The daily scan
Every trading day we scan a broad universe of US equities. A multi-factor engine
evaluates each name against a strict data contract, with integrity gates that block
any signal without clear provenance. Market data comes from institutional bar
sources with a per-symbol fallback; missing or invalid data is skipped — never
guessed or filled in.

2 · Attention Tiers
FinPilot does not predict which way a stock will move. It measures how unusual a
stock's current behavior is relative to its own history — gap size, volatility,
relative volume, distance from recent highs, and related factors combine into a
single Attention Score, which is grouped into a tier. A higher tier means more
unusual signals are aligned on the same name at the same time. It does not mean
"this will go up." Most days produce a small shortlist of flagged names, and some
days produce none — "nothing unusual today" is a valid, honest outcome.
An Attention Tier is an educational label describing behavior, not a
recommendation. We publish research context only: no transaction instructions and
no performance claims.

3 · Research models
Three PPO research models explore momentum, trend and conservative scenarios. They
are maintained as research artifacts, validated before use, and are not
represented as active inputs to the current daily Attention Score.

4 · How we verify
Locked out-of-sample: parameters are frozen before evaluation — no hindsight
fitting. Matched-control comparison: flagged names are compared against
similar, unflagged names from the same period, not against a naive market
average. Magnitude, not direction: we measure how much a flagged name's behavior
deviated from its own norm, not whether it went up.

5 · The open scorecard
Every flagged name is tracked — including the ones where nothing further happened.
We report how often flagged behavior coincided with a further outsized move,
against the matched-control baseline, not a cherry-picked win-rate. A maturity
gate means a flag only counts once its observation window has resolved, so fresh,
still-open flags never flatter the record. See the live scorecard on the demo
page.

6 · Education, not advice
FinPilot provides education and analysis only — it is not investment advice and
not portfolio management. Our lessons are generated from cited sources and passed
through a factual-consistency and compliance check before publishing.

Past performance does not guarantee future results. FinPilot is a research and
education tool and does not provide investment advice.
```

---

## 2) Demo/landing kart metni — taslak (İngilizce, mevcut `CandidateCard` yapısına göre)

`web/src/app/demo/page.tsx`'teki `Candidate`/`CandidateCard` bileşenleri temel alınmıştır.
`grade`/`prob_band` alanları yerine `attention_tier`/`attention_score` ve `flags`
(eski `badges`) kullanılır. Mevcut dosya DEĞİŞTİRİLMEDİ.

Örnek kart metni (gerçek bir sembolle DEĞİL, format örneği olarak):

```
$XYZ  Example Co.
Unusual behavior detected — Tier 2 of 3

Flags: Big Gap · Volume Spike · Far From High

Why flagged: XYZ opened well outside its typical gap range on volume more
than 3x its 20-day average, while trading meaningfully below its 52-week high.

[ Why this tier? ]
```

Not: "Tier 2 of 3" ifadesi tier sayısını örnek olarak gösterir; gerçek tier sayısı
Faz 1c'nin sonucuna göre (kaç ayrı bayrağın anlamlı biçimde ayrıştığına göre)
belirlenmeli, burada varsayılmamalıdır.

---

## 3) Telegram brif örneği — taslak (Türkçe, mevcut `templates.py` kalıbına göre)

`distribution/templates.py::_candidate_line` / `_grade_prob_explainer` / `_karne_line`
kalıpları temel alınmıştır. `distribution/glossary.py`'ye eklenen yeni terimler
(`attention_score`, `attention_tier`, `big_gap`, `volatility_spike`, `far_from_high`,
`high_lottery`) ve mevcut terimler (`squeeze`, `volume`) kullanılır. Mevcut
`templates.py` DEĞİŞTİRİLMEDİ.

```
📊 FinPilot Dikkat Haritası — 24 Ağustos 2026

Bugün sabah 105 hisse tarandı.

ℹ️ Dikkat Skoru, bir hissenin şu anki davranışının kendi geçmiş normaline göre
ne kadar olağan dışı olduğunu ölçer — yön tahmini içermez.

🟡 XYZ — Dikkat Katmanı 2 · geçmişte bu profildekiler eşleşen-kontrol grubuna
göre daha sık olağan dışı hareket etti
Bugün neden burada? Öne çıkaran nedenler: normalin belirgin üzerinde bir gap ile
açtı, hacmi 20 günlük ortalamasının 3 katını aştı, 52 haftalık zirvesinden
belirgin uzakta.
🔎 İzlemeye değer ayrıntı: Büyük Gap · Hacim Sıçraması · 52 Haftalık Zirveden Uzaklık
📌 Veriler: Fiyat $42.10 · hacim ortalamanın 3.2 katı

🎯 Sistemin açık karnesi: [link]

📚 Günün kavramı: Dikkat Skoru, gap/volatilite/hacim/zirve-mesafesi gibi
sinyalleri tek bir sayıda birleştirir. Yüksek skor "olağan dışı davranıyor"
demektir — "yükselecek" demek değildir.

Bu içerik araştırma ve eğitim amaçlıdır; yatırım tavsiyesi değildir. Geçmiş
performans gelecek sonuçların garantisi değildir.
```

---

## 4) EN Telegram varyant notu

Glossary şeması zaten iki dilli (`line_tr`/`line_en`, `card_en`) olduğundan, İngilizce
brif aynı `_candidate_line`/`_grade_prob_explainer` fonksiyonlarının `lang="en"`
parametresiyle çalıştırılmasıyla üretilebilir — ayrı bir metin taslağı gerekmez, sadece
`_BADGE_LABELS` sözlüğüne yeni bayraklar için İngilizce karşılıkların eklenmesi gerekir
(bkz. Faz 2 iş listesi). Bu paket şu an sadece TR kalıbını örnekliyor çünkü mevcut
canlı `templates.py` da öncelikle TR üretiyor.

---

## 5) Canlıya bağlanmadan önce gereken adımlar (checklist)

1. Faz 1c: export-formülü (§1.1) ile üretim-formülünün (§1.3) eşdeğerliği gerçek
   üretim verisiyle kanıtlanmalı (`research/attention_score_formula_overlap_2026_08_14.py`
   gerçek shortlist verisiyle yeniden çalıştırılarak).
2. Tier sayısı ve eşikleri (kaç tier, hangi Dikkat Skoru aralıkları) kanıta dayalı
   belirlenmeli — bu taslakta varsayılan "3 tier" yer tutucudur, kanıtlanmamıştır.
3. `_BADGE_LABELS`'a yeni bayraklar (`big_gap`, `volatility_spike`, `far_from_high`,
   `high_lottery`) eklenmeli — bu paket henüz `templates.py`'yi düzenlemedi.
4. Yukarıdaki methodology/kart/Telegram metinleri gerçek dosyalara uygulanmadan önce
   Meriç onayı gerekir (Level B — kullanıcıya görünür yeni vaat).
5. Onaydan sonra bile: eski "Grade/prob_band" dilinin hiçbir yerde kalmadığından
   emin olunmalı (rollback planı hazır tutularak, feature flag ile).

---

## 6) Lint doğrulama sonucu (bu turda çalıştırıldı)

`distribution/lint.py::check_text` her metin bloğuna ayrı ayrı uygulandı:

| Blok | İhlal | Disclaimer var mı |
|------|-------|--------------------|
| Methodology (EN) | 1 — `guarantee` kuralı, "does not guarantee" negasyonunu ayırt etmiyor (§ yukarıdaki yan bulgu) | Evet |
| Demo kart metni (EN) | Yok | Hayır — kart kendi başına disclaimer taşımaz, sayfa altbilgisi taşır (mevcut demo sayfasındaki `DISCLAIMER` sabitiyle aynı desen) |
| Telegram brifi (TR) | Yok | Evet |

Methodology bloğundaki tek ihlal, yeni yazılan cümlelerden değil, zorunlu disclaimer
cümlesinin kendisinden (`"does not guarantee future results"`) kaynaklanıyor — aynı
cümle canlı `methodology/page.tsx`'te de var ve muhtemelen aynı şekilde lint'e
sokulmuyor (bu dosya bir web sayfası, `assert_publishable` çağrısı yalnızca
Telegram broadcast kuyruğunda kullanılıyor gibi görünüyor — bu paket bunu koddan
doğrulamadı, gözlem düzeyinde bir not).
