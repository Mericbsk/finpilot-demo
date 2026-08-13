# FinPilot — Kullanıcı Araştırma Kiti (PR1 / PR7 / PR2)

Date: 2026-08-10
Level: A (research content; running these requires Meriç + real users)
Layer: Product research
Status: ready-to-run kit — no code, no production change

Bu kit, Strategic Thinking Lab'in en yüksek bilgi-değerli ama ajan tarafından
çalıştırılamayan deneylerini (PR1, PR7, PR2) hazır protokollere çevirir.
Amaç: Meriç'in tek yapması gerekenin "davet göndermek" olması.

---

## PR1 — Problem-Doğrulama Görüşmeleri (12 kişi)

### Hedef
Kullanıcının FinPilot'tan gerçekte ne satın aldığını bulmak: sinyal mi,
araştırma mı, eğitim mi, güven mi, alışkanlık mı, zaman tasarrufu mu?

### Kimler (12 kişi)
- 4 beginner (borsada < 1 yıl)
- 4 aktif bireysel yatırımcı (haftada en az 1 işlem düşünen)
- 4 "meraklı" (waitlist'te ama aktif kullanmayan)

Kaynak: waitlist + Telegram kanalı. Davet metni aşağıda.

### Davet metni (TR)
> Merhaba! FinPilot'u daha iyi hale getirmek için 20 dakikalık kısa bir
> görüşme yapıyoruz. Doğru ya da yanlış cevap yok — sadece sizin deneyiminizi
> anlamak istiyoruz. Katılmak ister misiniz? (Yazılı form da mümkün.)

### Görüşme scripti (20–25 dk, JTBD formatı)

**Isınma (2 dk)**
1. Borsayla ilişkinizi kısaca anlatır mısınız? (ne zamandır, ne sıklıkla)

**Son-kullanım anı (8 dk)** — en önemli bölüm
2. FinPilot'u en son ne zaman açtınız? O an ne oluyordu, ne arıyordunuz?
3. Açtığınızda ilk neye baktınız?
4. O gün FinPilot size ne sağladı — somut olarak ne yaptınız ya da yapmaktan
   vazgeçtiniz?
5. O gün FinPilot olmasaydı ne yapardınız? (bu soru kritik — ikameyi bulur)

**Değer haritası (6 dk)**
6. FinPilot'un size en değerli gelen yanı ne? En gereksiz gelen yanı ne?
7. Bir arkadaşınıza anlatsanız, "FinPilot şu işe yarıyor" diye nasıl
   bitirirdiniz?
8. FinPilot'u hayatınızdan çıkarsak neyi özlerdiniz? (hiçbir şey de geçerli
   cevap)

**Kapanış (4 dk)**
9. FinPilot için para öder miydiniz? Ne için öderdiniz?
10. Şu an en büyük yatırım/piyasa probleminiz ne — FinPilot'la ilgili olsun
    ya da olmasın?

### Analiz şablonu
Her görüşme için: (a) tetikleyici an, (b) aranan çıktı, (c) ikame, (d) değer
kelimesi, (e) ödeme sinyali. 12 görüşme sonunda tekrarlayan örüntü aranır.
**Kill criterion:** 12 görüşmede tekrarlayan net bir problem çıkmazsa mevcut
positioning ölür, pivot değerlendirilir.

---

## PR7 — Genel-AI İkame Testi (5–8 kişi)

### Hedef
Kullanıcı aynı soruyu ChatGPT/Claude'a sorarak aynı değeri alıyor mu?
Alıyorsa FinPilot'un B2C değer önerisi ölür.

### Protokol
Katılımcıya aynı 3 soru verilir. Her soruyu önce genel AI asistanına, sonra
FinPilot edition'ına sorar/uygular. Sıra katılımcılar arasında dengelenir
(yarısı önce AI, yarısı önce FinPilot).

**3 standart soru:**
1. "Bugün ABD piyasasında dikkat çekici ne oldu ve neden önemsemeliyim?"
2. "NVDA hakkında ne düşünmeliyim — güçlü ve zayıf yönler ne?"
3. "Bu hafta portföyümde neye dikkat etmeliyim?"

### Karşılaştırma formu (her soru için)
| Soru | Hangisi daha kullanışlıydı? | Neden? (tek cümle) |
|---|---|---|
| 1 | AI / FinPilot / fark yok | |
| 2 | AI / FinPilot / fark yok | |
| 3 | AI / FinPilot / fark yok | |

Son soru: "İkisinden yalnızca birini kullanabilecek olsanız hangisini
seçerdiniz? Neden?"

**Kill criterion:** Katılımcıların çoğunluğu 3 sorunun 2'sinde "fark yok" veya
"AI" derse → mevcut B2C değer önerisi ölür.

---

## PR2 — Positioning A/B (5 varyant)

### Hedef
Hangi tek cümle "bunu istiyorum" dedirtiyor?

### 5 varyant (TR + EN)

1. **Daily Market Reasoning** (mevcut yön)
   - TR: "Her gün yayınlanan piyasa araştırması: ne öne çıktı, neden önemliydi,
     sonra ne oldu."
   - EN: "A daily market research edition: what stood out, why it mattered,
     what happened next."

2. **Open Research Ledger**
   - TR: "Her piyasa iddiasını açıkça test eden, sonucu — olumlu ya da olumsuz —
     yayınlayan araştırma günlüğü."
   - EN: "An open research ledger that tests every market claim and publishes
     the result — good or bad."

3. **Sorgulama Günlüğü**
   - TR: "Size ne alacağınızı söylemeyiz; bir piyasa iddiasını nasıl
     sorgulayacağınızı gösteririz."
   - EN: "We don't tell you what to buy; we show you how to question a market
     claim."

4. **Kanıt Kartı**
   - TR: "Her gün bir piyasa gözlemi, kanıtı, karşı-tezi ve belirsizliğiyle."
   - EN: "One market observation a day — with its evidence, counter-thesis and
     uncertainty."

5. **Karar Antrenmanı**
   - TR: "Piyasayı tahmin etmeyi değil, daha iyi düşünmeyi öğrenin — her gün
     bir gerçek vaka."
   - EN: "Learn to think better, not predict better — one real market case a
     day."

### Yöntem (en ucuz)
Waitlist'e 5 ayrı kısa anket linki veya Telegram'da 5 gün üst üste tek
cümlelik anket. Metrik: "Bunu isterim" oranı (evet/hayır). 30+ cevap yeterli.

**Not:** PR2'yi PR1'den önce koşmayın — varyantlar PR1'den çıkan kullanıcı
diliyle güncellenmeli.

---

## Sıralama ve bağımlılık

```
PR1 (12 görüşme) ──→ PR2 varyantlarını kullanıcı diliyle güncelle ──→ PR2
     │
     └──→ PR7 (AI ikame) — PR1 ile paralel koşabilir
```

**Minimum başlangıç:** PR1 + PR7. Toplam ~15 kişi, ~1 hafta, sıfır kod.

## Governance
Bu kit içerik üretimidir (Level A). Deneylerin kendisi gerçek kullanıcılarla
Meriç tarafından yürütülür. Sonuçlar decision-log'a Level A kanıt olarak
girer; ürün değişikliği ancak Level B onayıyla.
