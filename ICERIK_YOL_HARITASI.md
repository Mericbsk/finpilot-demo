# FinPilot — Web İçerik Zenginleştirme Yol Haritası

> Amaç: **time-on-site** ve içerik derinliğini artırmak. Yöntem: bu konuşmada kurduğumuz
> iki içerik motorunu web'e taşımak — **FinSense akademi** + **yerel-AI enricher** — eğitim
> öncelikli, tavsiye değil. Sürüm 1.0 · 2026-07-17 · YONERGE ile uyumlu.

---

## 0. Stratejik çerçeve

**İki motor var ama web'e bağlı değil:**
1. **FinSense akademi** (standalone repo): dersler (Para, Borsa, Risk, Mum, Davranışsal) + 30-terim çok dilli sözlük. → eğitim yapışkandır.
2. **Yerel-AI enricher** (`ShortlistEnricherAgent`): her aday için açıklama + katalizör gücü + boğa/ayı tezi + sosyal okuma. → derin açıklama keşfe davet eder.

**İlkeler:** eğitim ≠ tavsiye (lint korunur) · her iddia veriden (uydurma yok) · çok dilli (TR/EN/DE) · dürüstlük (kaybedenleri de göster).

**Başarı ölçütü:** time-on-site · sayfa/oturum · terim-tıklama · ders tamamlama · geri-dönüş oranı (Plausible ile ölçülür — Hafta 2).

---

## 1. Zengin Hisse Açıklaması (candidate deep-dive)

### Şu an → olabilecek
**Şu an:** tek jenerik cümle ("strong profile, mix of factors").
**Olabilecek — katmanlı kart:**

| Katman | İçerik | Kaynak motor |
|--------|--------|--------------|
| Neden listede | Spesifik faktörler + rozet çipleri (squeeze/gap/RVOL) | scanner sözleşmesi (badges) |
| Boğa / Ayı tezi | Dengeli iki taraflı kısa argüman | **enricher** (bull_point/bear_point) |
| Katalizör | Haber/earnings bağlamı + güç (3/10) | **enricher** (catalyst_summary/strength) |
| Sosyal okuma | Organik mi / pump mı | **enricher** (social_read) |
| Ne izlemeli | Kritik seviye, teyit/iptal koşulu (eğitim) | scanner + kural |
| Terimler | "short squeeze" → 60-kelime tooltip | **sözlük** (GlossaryTooltip) |
| Tarihsel bağlam | "bu profil geçmişte 5 günde %X hareket etti" | outcome verisi (dürüst) |

### Snapshot candidate şeması (eklenecek alan)
```json
"enrichment": {
  "explanation": "…", "catalyst_strength": 6, "catalyst_summary": "…",
  "bull_point": "…", "bear_point": "…", "social_read": "organic",
  "watch_levels": {"support": null, "resistance": null}
}
```
(TR/EN/DE için `enrichment_i18n` — mevcut `rationale_i18n` deseniyle aynı.)

### Nasıl bağlanır
`build_snapshot` her aday için `ShortlistEnricherAgent` çıktısını (yereldeki `qwen2.5:3b`)
`enrichment` alanına yazar → web aday kartı katmanları açılır-kapanır gösterir (mevcut
`EditionArticle`/kart bileşeni genişletilir). Enricher zaten yazıldı; kalan: snapshot'a
yazmak + kartta render.

**Kabul:** her yayınlanan adayda ≥3 katman dolu · lint temiz · TR/EN/DE · "tavsiye değil" ibaresi.

---

## 2. FinSense Akademi Entegrasyonu (education library)

| Parça | İçerik | Hangi bileşen |
|-------|--------|---------------|
| Gezilebilir mini-kurslar | Dersler → çok dilli kartlar, kütüphane sayfası | Yeni `/academy` + ClassroomPreview |
| Günün terimi → mini-ders | Kısa tanım + "tam dersi oku" | DailyDouble genişletme |
| Bağlamsal öğrenme | Rozet → ilgili derse link ("squeeze → öğren") | Aday kartı + TermCard |
| Sözlük tooltip'leri | Her brief'te terimler tıklanabilir | GlossaryTooltip (mevcut) |
| Quiz / pekiştirme | Ders sonu quiz → geri-dönüş | Akademi quiz verisi |
| Haftalık uzun-form | Editör yazısı, tema uyumlu | EditionArticle / Newsroom |

### Nasıl bağlanır
Akademi zaten yayınlanmış dersleri + sözlüğü üretiyor. Bunları web'e **statik JSON export**
et (`academy_web_export.json`) → web `/academy` sayfası + tooltip'ler tüketir. Snapshot'taki
`concept` (günün terimi) sözlükle eşlenir. Çok dilli (akademi zaten TR/EN, DE eklenebilir).

**Kabul:** ≥8 ders web'de çok dilli · günün terimi mini-ders · en az 5 rozet→ders bağlantısı · terim tooltip'leri brief'te çalışıyor.

---

## 3. Güven + Geri-Dönüş İçeriği

| Parça | İçerik | Kaynak |
|-------|--------|--------|
| Track record (karne) | Dürüst skor kartı: kazanan VE kaybeden, grade bazında | kpi/outcome → snapshot.karne → LedgerStrip |
| Post-mortem | "İşaretledik → ne oldu" (5-10 gün sonra) | outcome_reconciler → otomatik "izleme sonucu" kartı |
| Arşiv | Geçmiş baskılar gezilebilir | geçmiş snapshot'lar |
| Metodoloji sayfası | "Nasıl üretiliyor / ne DEĞİL", config_sha | HowItsMade → tam sayfa |

Bunlar güvenin gerçek kaynağı: sistem kendi sonuçlarını dürüstçe gösteriyor → kredibilite + geri gelme sebebi.

---

## 4. Uygulama sırası (impact × emek)

| Faz | İş | Emek | Etki | Neden |
|-----|----|----|----|-------|
| **1** | enricher → snapshot.enrichment → web kartı (zengin açıklama) | Orta | **Çok yüksek** | Motor hazır; en hızlı görünür içerik sıçraması |
| **2** | Karne track-record (dürüst) + sözlük tooltip'leri | Orta | Yüksek | Güven + öğrenme, her ikisi sticky |
| **3** | Akademi `/academy` kütüphanesi + günün terimi mini-ders | Orta-yüksek | Yüksek | Asıl time-on-site kaynağı |
| **4** | Post-mortem + arşiv + quiz + haftalık uzun-form | Yüksek | Orta-yüksek | Geri-dönüş motoru |

Not: **Faz 1 için ön koşul = scanner sözleşmesinin geri yüklenmesi** (badges/grade dolmadan enricher da zayıf bağlam alır). Yani sıra: sözleşme → enricher → web.

---

## 5. İçerik ilkeleri (kalite + uyumluluk)

- **Tavsiye değil eğitim:** al/sat/hedef-fiyat/garanti yok — `distribution.lint` her metni geçirir.
- **Her olgusal iddia veriden** gelir (snapshot alanları / outcome); model uydurmaz.
- **Çok dilli tutarlılık:** TR/EN/DE aynı kalite; kanonik EN'den çeviri.
- **Dürüstlük:** track record kaybedenleri de gösterir; "geçmiş gelecek garantisi değildir".

---

## 6. Ölçüm

Plausible (Hafta 2) ile: ortalama oturum süresi · sayfa/oturum · terim-tıklama oranı ·
akademi ders açılma/tamamlama · 7-gün geri-dönüş. Her fazdan önce/sonra ölç; artmıyorsa geri al.

---

## 7. Her şeyi bağlayan resim

```
Yerel scanner ──► sözleşmeli export ──► build_snapshot
                                            │
        ┌─── enricher (boğa/ayı/katalizör) ─┤
        ├─── akademi (ders + sözlük) ───────┤
        └─── karne/outcome (track record) ──┤
                                            ▼
                    tek çok-dilli snapshot ──► WEB (zengin içerik) + Telegram
```
Bu konuşmada kurduğumuz akademi + enricher + çok dilli katman → web'de **tek, öğretici,
güvenilir ürün**. Dağınık parçalar değil.

---

_İlk somut adım: Faz 1 — enricher çıktısını snapshot'a bağlamak (sözleşme geri geldikten sonra)._
