# Level C karar notu — Grade olasılık metinleri (C1, C2 + C3 bayrağı)

**Tarih:** 2026-09-23 · **Karar sahibi:** Meriç (Level C, ürün metni) · **Statü:** KARAR BEKLİYOR
**Bağlam:** P0 Conviction/Grade Probability Closure Audit'ten **bağımsız** kararlar. Bu kararlar ne audit sonucunu bekler ne de audit'i etkiler, çünkü seçim fonksiyonu değişmez. Sayısal değerler (73/59/52) bu notun konusu değildir; o karar audit sonrasında ayrıca verilecek.
**Aciliyet:** Brif yeniden başladığında bu metinler tekrar kullanıcıya gidecek.

---

## C1 — "recalibrated as outcomes accumulate" (olgusal uyumsuzluk)
**Mevcut metin:** `distribution/glossary.py:25` (prob_band kartı, EN)
> "It is derived from past data, recalibrated as outcomes accumulate, and can be wrong for any single case…"

**Olgu:** Olasılıklar `scanner/features.py:179` içinde sabit bir sözlükte duruyor (`_CONV_PROB`). Production kodunda hiçbir yeniden-kalibrasyon mekanizması tespit edilmedi.

**Seçenekler:**
- **(a) Cümleyi kaldır.**
- **(b) Doğru ifadeyle değiştir.** Örnek EN: "It is a fixed estimate from a July 2026 internal study and is not yet updated with new outcomes." Örnek TR: "Temmuz 2026 iç çalışmasından gelen sabit bir tahmindir; yeni sonuçlarla henüz güncellenmemektedir."
- **(c) Yeniden-kalibrasyon mekanizmasını gerçekten uygula.** Bu bir mühendislik işi ve Level B; bu notun kapsamı dışında. Uygulanana kadar (a) veya (b) gerekir.

## C2 — "kalibre olasılık / calibrated probability" etiketi
**Mevcut metinler:**
- `glossary.py:23-24` — "kalibre aralık … tarihsel bir taban oranıdır" / "A calibrated range … a historical base rate"
- `glossary.py:151-153` — "FinPilot'un tek kalite etiketi: kalibre olasılık + hizalanan faktör sayısı"
- Brif başlığı bu satırı kullanıyor.

**Olgu:** 12 Haziran denetimi iddiayı "doğrulanmadı" olarak işaretledi. 3 Temmuz'daki P0 doğrulaması yapılmadı. Kaynak in-sample bir laboratuvar çalışması. `glossary.py:161` ise "calibrated" kelimesini "'60%' should come true about 60% of the time" diye tanımlıyor. Bu, şu an sahip olmadığımız bir kanıt standardı.

**Seçenekler:**
- **(a) Etiketi olduğu gibi bırak.** Metin kanıttan güçlü bir iddia taşımaya devam eder.
- **(b) "tarihsel sıklık (bağımsız doğrulanmamış)" olarak değiştir.** Örnek TR: "Benzer profillerin geçmişte bu sıklıkla ≥%5'e ulaştığını gösteren tarihsel oran — bağımsız olarak doğrulanmamıştır, olasılık tahmini değildir." Örnek EN: "Historical frequency among similar past setups — not independently validated; not a probability forecast."
- **(c) Audit sonucuna kadar olasılık bandını yayından kaldır.** Grade harfi kalır.

## C3 — BAYRAK (onaylanan iki maddenin dışında; karar senin)
**Mevcut metin:** `glossary.py:153` (EN) — "Grade A is rare (~1/day) and historically hit large moves most often."

**Olgu (sayım, sonuç değil):** 2026-07-05 → 09-09 arasındaki 39 tarihli tam export'ta toplam 9 Grade A satırı var. Bu günde yaklaşık 0,23 eder. "Historically hit large moves most often" ifadesi de C2 ile aynı in-sample kaynağa dayanıyor.

**Seçenekler:**
- (a) Olduğu gibi bırak.
- (b) "~1/day" ifadesini kaldır.
- (c) Ölçülen sıklıkla ve tarih aralığıyla değiştir. "Most often" iddiasını C2 kararına bağla.

---

**Not:** Metinlerin TR/EN/DE karşılıkları aynı kararla birlikte güncellenmeli. DE için `rationale.py` / glossary dil havuzları kontrol edilmeli. Karar verildiğinde decision-log'a Level C kaydı düşülür. Uygulama `distribution/` altında yapılır; bu publish zinciri olduğu için Level B diff sunumu gerekir.
