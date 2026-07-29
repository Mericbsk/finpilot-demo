# FinPilot — İÇERİK/YAYIN KALİTESİ: Ön-Araştırma Raporu (Web + Telegram)
Durum: AKTİF · 2026-07-28 · Tür: kalite keşif raporu (→ sonra detaylı yol planı)

## 0. Özet
Yapı iyi: Telegram brifi eğitici ve tavsiye-dışı; web landing 10+ bölümlü "gazete" mimarisi. **Zayıf nokta yapı değil, DERİNLİK ve TUTARLILIK:** akademi içeriği ölçeksiz, metodoloji sayfası yok, mesaj hâlâ "AI stock", teslim serisi kırılgan. **En yüksek fayda: eğitim içeriğini (akademi + metodoloji) derinleştirmek** — hem kullanıcı güveni hem hibe (etki) anlatısı tek hamlede güçlenir.

---

## 1. TELEGRAM YAYIN KALİTESİ
### Mevcut (kanıt: templates.py)
Brief = başlık + "N hisse tarandı" + market bağlamı + **aday satırları** (emoji + ticker + Grade + "geçmişte bu profildekilerin %X'i 5 günde ≥%5 hareket etti" + "Bugün neden burada: {rationale}" + "İzlemeye değer: {badges}" + risk notu) + karne + günün kavramı + web CTA + disclaimer.
### Güçlü
- Eğitici çerçeve, "al/sat" değil; her aday bir mini-ders.
- Karne + günün kavramı = güven + öğretme.
- Disclaimer + tavsiye-dışı dil (compliance).
### Hatalar / riskler
- **Rationale havuz-tabanlı (deterministik varyant), LLM değil** → zamanla formülleşme riski; per-hisse gerçek "içgörü" sığ kalabilir.
- **Olasılık-bandı istatistiği prob_band verisine bağlı** — boşsa "veri birikiyor" der (zayıf görünür). Karne olgunlaşınca güçlenir.
- **Tek-yönlü:** etkileşim yok (anket/oylama/soru yok) → geri bildirim düşük.
- **Tutarlılık = kalitenin parçası:** "expired" geçmişi (kaçan günler) markayı zayıflatır. Kesintisiz teslim bir kalite metriğidir.
### Geliştirmeler (öncelikli)
1. **Per-hisse "neden" derinliği:** mevcut ShortlistEnricher/agent hattını (bear/bull/risk) — **compliance lint kapısıyla** — brife 1 "karşı-görüş/risk" satırı olarak ekle. Farklılaştırıcı.
2. **Etkileşim:** haftada 1 mini-anket ("hangi kavramı işleyelim?") → feedback + topluluk hissi.
3. **Ritim & ses:** sabit yayın saati + tutarlı editoryal ses (gazete gibi). Kesintisiz seri.
4. **Kavram serisi:** "günün kavramı"nı 30-günlük müfredata bağla (akademiyle köprü).

---

## 2. WEB YAYIN KALİTESİ
### Mevcut (kanıt: page.tsx)
Landing = Masthead · Yesterday's Edition · Daily Double (kavram+aday) · Inside the Newsroom · **Ledger Strip (karne)** · How It's Made · **Classroom Preview** · Editorial Stance · Full Edition Teaser · Colophon. Zengin "gazete" mimarisi.
### Güçlü
- Yapısal derinlik + özgün metafor (Ledger/gazete) = farklılaşma.
- **Açık karne** (track record: 5719, +0.40%/işlem) = radikal şeffaflık, güven.
- Disclaimer'lar + tavsiye-dışı çerçeve.
### Hatalar / riskler
- **Metodoloji sayfası YOK** — Colophon ona link vermeye çalışıyor (kırık iç referans, TODO). Güven+hibe için kritik (trustworthy AI kanıtı).
- **Classroom sığ:** `academy_lessons.json` ~1 örnek / 5 published; akademi bölümü boş görünüyor (39 draft bekliyor).
- **Mesaj eski:** `<title>` "AI-Powered Stock Intelligence" — repositioning'e aykırı + compliance-riskli.
- **Yasal sayfalar yok** (ayrı kırmızı bayrak; kod eklendi, doldurma+onay bekliyor).
- **EN/DE tüketimi** belirsiz; dil erken bölünmemeli.
- **Erişilebilirlik** (alt-text, kontrast) doğrulanmadı — EU/hibe önemser.
### Geliştirmeler (öncelikli)
1. **Metodoloji sayfasını yayınla** (kırık linki kapatır + "nasıl doğruluyoruz" güveni + trustworthy-AI kanıtı).
2. **Classroom'u doldur:** akademi 5→20+ yayın → gerçek eğitim yüzeyi + SEO + retention.
3. **Mesajı literacy-önce yap** (title/description/OG).
4. **SEO evergreen:** günlük brief geçicidir; **akademi dersleri + sözlük + metodoloji** = kalıcı, aranan içerik (organik trafik).

---

## 3. "GENİŞ İÇERİK DEMOYU/ŞANSI ARTIRIR MI?" → Evet, AMA seçici
- **Kullanıcı/traction için:** Derinlik = güven + retention + paylaşılabilirlik. Sığ demo = "bir sinyal botu daha"; zengin+dürüst-karneli+eğitici demo = farklı, güvenilir.
- **Hibe (aws/EU) için:** Şansı artıran içerik ÖZELLİKLE **EĞİTİM** içeriğidir (akademi, metodoloji, okuryazarlık) — "social/societal impact" + "digital skills" kriterine bire-bir. Trading adayları hibe için ikincil.
- **Tuzak:** "geniş" ≠ "gürültülü". Derinlik + netlik + dürüstlük > hacim. Doldurma içerik güveni AZALTIR. Az ama gerçek/atıflı içerik, çok ama sığ içerikten iyidir.
- **Sonuç:** En yüksek kaldıraçlı içerik yatırımı = **akademi ölçeği + metodoloji sayfası** (ikisi de eğitim = hem güven hem hibe). Daha fazla trading süsü değil.

---

## 4. HEDEFLER DOĞRULTUSUNDA EN YÜKSEK FAYDA (öncelik)
| # | Hamle | Fayda | Efor |
|---|---|---|---|
| 1 | Metodoloji sayfası yayınla | Güven + hibe (trustworthy AI) + kırık link kapanır | Düşük |
| 2 | Akademi 5→20+ yayın (Classroom dolu) | SEO + retention + hibe (impact) | Orta |
| 3 | Mesajı literacy-önce çevir (title/OG) | Compliance + repositioning tutarlılığı | Düşük |
| 4 | Kesintisiz teslim serisi (kalite=tutarlılık) | Güven + lansman anlatısı | Orta (ritüel) |
| 5 | Brife karşı-görüş/risk satırı (lint kapılı) | İçerik farklılaşması | Orta |
| 6 | Yasal + erişilebilirlik | Yasal + EU uyumu | Düşük-Orta |

---

## 5. GÖZDEN KAÇMIŞ OLABİLECEKLER (benim önerilerim)
- **İçerik takvimi & editoryal ses:** gazete bir ritim + tutarlı ses ister; rastgele değil planlı içerik.
- **Evergreen > günlük:** organik büyüme akademiden/metodolojiden gelir, günlük briften değil. SEO stratejisini buraya kur.
- **Paylaşılabilir an:** çarpıcı bir karne/istatistik ("5.719 pick açıkça izlendi") → sosyal paylaşım kancası.
- **Kalite ölçümü:** yayın SAYISI değil, ETKİLEŞİM (feedback, web'e tıklama, ders tamamlama) ölç.
- **Dil disiplini:** önce TR kitlesini kanıtla; EN/DE'yi erken açma (içerik ikiye/üçe bölünür, kalite düşer).
- **Tek ses/insan riski:** solo üretimde tutarlılık zor; şablon+akademi motoru bunu ölçekler ama editoryal kontrol sende kalmalı.
- **"Karne dürüstlüğü" bir pazarlama varlığı:** rakipler kazananları seçerken sen kaçıranları da gösteriyorsun — bunu açıkça anlat (güven farklılaştırıcısı).

---
_Durum: AKTİF · Kalite keşif raporu. Bir sonraki adım: bu bulgulara göre içerik/yayın yol planı (öncelik 1-2-3 ile başlar)._
