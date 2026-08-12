# FinSense — Product Thesis v1
Durum: LOCKED (2026-08-11) · Belge 01 — `FinSense_System_Reality_Architecture_Contract_v1_2026-08-11.md` (Belge 00) altında durur, ona aykırı bir şey tanımlamaz.

---

## 1. Tek cümlelik tez

> **FinSense, insanların piyasalar hakkında nasıl düşündüklerini görmelerini sağlayan bir öğrenme sistemidir. Kullanıcı gerçek piyasa olayları üzerinden düşüncesini açık bir tahmine dönüştürür, confidence belirtir, tahminini commit eder ve daha sonra sonucunu gerçekle karşılaştırır. Sistem zaman içinde kullanıcının doğruluğunu değil yalnızca; confidence, calibration ve reasoning davranışını da görünür hale getirir.**

Tüketici-yüzlü kısa formül: **"Learn finance by testing your thinking against reality."**

## 2. Merkezi soru değişimi

Eski soru: *"Ne kadar finans biliyorsun?"*
Yeni soru: **"Piyasa hakkında nasıl düşünüyorsun ve düşüncen gerçekle karşılaştırıldığında ne öğreniyorsun?"**

## 3. FinSense NE DEĞİL

- BUY/SELL sinyali servisi değil.
- Kişisel yatırım danışmanı değil.
- "FinSense senin için piyasayı tahmin ediyor" değil — "FinSense senin kendi tahminini test etmeni sağlıyor."
- Klasik ders-platformu değil — temel birim Case'dir (Contract §35), Lesson değil.
- Parasal kazanç leaderboard'u değil (Contract §65 — mevcut `quiz_scores.get_leaderboard()` da bu ilkeye tabi, Calibration'a miras alınmaz).
- Psikolojik tanı sistemi değil — "bir örüntü gösteriyorsun" der, "sen busun" demez.

## 4. Core loop

```text
LEARN → THINK → PREDICT → COMMIT → REVEAL → REFLECT → CALIBRATE → LEARN AGAIN
```

(Contract §60, §92 ile birebir.)

## 5. FinPilot × FinSense ilişkisi

FinPilot = piyasada ne oldu. FinSense = kullanıcı bunu nasıl yorumladı ve ne öğrendi. Sınır ve source-of-truth matrisi: Contract §4-6.

## 6. Mevcut content factory'nin yeni rolü

Silinmiyor, kaderi değişiyor: Contract §7 — content factory artık Thinking Mirror'ın eğitim/içerik katmanı.

## 7. North Star (v0/VS-01 için)

> Kullanıcının doğru tahmin yapması değil, **prediction → outcome → reflection döngüsünü tekrar tekrar tamamlaması.**

Ölçüm: ≥1 prediction + ≥1 evaluated outcome + tekrar case başlatma oranı. (Contract §61-63.)

## 8. Şu an test etmediğimiz iddia

*"Dünyanın en iyi finansal okuryazarlık platformu"* — bu bir hedef, şimdilik bir doğrulama kriteri değil (Contract §62). Şu an yalnız 5 soruyu test ediyoruz: anlıyor mu, ilgileniyor mu, dönüyor mu, fayda görüyor mu, davranışı değişiyor mu.

---

_Bu belge Contract'ın §1-8, §60-63, §65, §91-92'sinin nesir hâlidir — yeni bir karar eklemez, sadece "neden bu ürün var"ı tek yerde toplar._
