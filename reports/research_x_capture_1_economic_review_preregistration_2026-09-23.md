# RESEARCH-X / RX-CAPTURE-1-ECON — Economic & Robustness Review (Pre-Registration Draft)

**Research ID:** RX-CAPTURE-1-ECON
**Version:** v0.1-DRAFT
**Date:** 2026-09-23
**Research Level:** B (economic/robustness evaluation of a CAPTURE_SUPPORTED result)
**Status:** DRAFT — NOT LOCKED. Requires Meriç approval.
**Production Impact:** NONE
**Parent:** RX-CAPTURE-1 (CLOSED/VERIFIED) — this is a NEW Level B line, not a reopening.
**H4:** FROZEN / UNTOUCHED

---

## 0. SCOPE — bu bir Level B ekonomik/robustness değerlendirmesidir, production kararı değil

RX-CAPTURE-1'de E1 +3% ve +5% sabit-hedef çıkışlar kilitli tarihsel kohortta
maliyet-sonrası pozitif medyan capture üretti (CAPTURE_SUPPORTED, bağımsız
doğrulama PASS). Bu hat şu soruyu sorar:

> **CAPTURE_SUPPORTED bulgusu, gerçekçi maliyet/likidite/yürütme ve temporal
> sağlamlık altında ekonomik ve operasyonel olarak uygulanabilirliği test etmeye
> değer mi?**

Bu hat şu soruyu SORMAZ ve cevaplamaz:

> "+3/+5% production'da kullanılmalı mı?" — bu ayrı ve daha sonraki bir Level B/C
> karardır.

**Do-not-infer (kilitli):** `CAPTURE_SUPPORTED ≠ production approval`;
`VERIFICATION_PASS ≠ strategy approval`. Bu hat production çıkış kuralı önermez.

---

## 1. Araştırma sorusu

> Önceden kilitlenmiş E1 +3%/+5% çıkış adayları, (a) gerçekçi maliyet/slippage
> senaryoları, (b) temporal robustness (yeni/ek dönem), ve (c) likidite/kapasite
> kısıtları altında pozitif net capture'ı koruyor mu?

Secondary: E1_t3'ün medyan dejenerasyonu ve E1_t5'in late-period zayıflaması
(1.556→0.117) daha geniş maliyet/zaman koşullarında nasıl davranıyor?

## 2. Neden şimdi / mevcut kanıt
- E1_t3: medyan net +2.45pp (0.55%), stress +2.0pp (1.00%); hit %61.5; medyan dejenere.
- E1_t5: medyan net +1.136pp, stress +0.686pp; hit %42.9; dejenere değil; early 1.556 / late 0.117.
- Bağımsız doğrulama VERIFICATION_PASS. Determinism byte-stabil.

## 3. Bilinen eksiklikler (audit'ten; bunlar bu hattın test ettiği sınırlar)
- Spread/slippage gözlemi %0 (veri borcu — CRITICAL).
- Tek tarihsel pencere (54 gün, 2026-05→08); OOS kapalı.
- Likidite/ADV/kapasite tarihsel verisi yok.
- Corporate-action / survivorship sınırları.

## 4. Tasarlanan ölçüm eksenleri (DRAFT — kilitlenecek)
1. **Maliyet sağlamlığı:** net capture'ı bir dizi maliyet seviyesinde (örn. 0.25%→2.0%)
   yeniden hesapla; pozitifliğin hangi maliyet eşiğinde kırıldığını ölç (breakeven cost).
   NOT: bu yeni bir sinyal arama değil; kilitli E1 parametreleriyle yalnızca maliyet
   duyarlılığıdır.
2. **Temporal robustness:** mevcut pencerede alt-dönem dayanıklılığı + (varsa) yeni
   birikmiş veri üzerinde replikasyon. E1_t5'in zayıflamasını ayrıca incele.
3. **Likidite/kapasite proxy:** mevcut veriyle mümkün olan en iyi proxy (örn.
   fiyat×hacim) ile capture'ın likidite koşullu davranışı; veri yoksa `NOT_MEASURABLE`
   raporla, impute etme.
4. **Kuyruk/tail:** medyan dejenere olduğunda (E1_t3) mean + dağılım + big-loss
   davranışını ayrı raporla.

## 5. Estimand / ambiguity (NS-1 + RX-CAPTURE-1 dersleri)
- Primary estimand: net capture breakeven maliyet eşiği ve temporal işaret istikrarı.
- Her eksen için exact mathematical definition lock öncesi yazılacak.
- Same-day ambiguity konvansiyonu RX-CAPTURE-1 ile aynı (EXCLUDE) — değişmez.
- Missing cost/liquidity data → `NOT_MEASURABLE`, asla impute edilmez.
- Temporal: yeni veri kullanılacaksa yeni input SHA + ayrı pre-reg eki.

## 6. Governance sınırları
- H4 FROZEN; RX-CAPTURE-1 CLOSED kalır; bu hat onları yeniden açmaz.
- Production impact NONE. Hiçbir çıkış kuralı üretime alınmaz.
- Herhangi bir shadow/paper/live geçiş ayrı Level C insan kararıdır.
- Bu DRAFT lock'lanmadan runner yazılmaz.

## 7. Açık kararlar (Meriç)
- Maliyet ekseni aralığı ve adımı (örn. 0.25%→2.0% hangi adımla).
- Temporal için yeni veri var mı / yalnızca alt-dönem mi.
- Likidite proxy kabul edilebilir mi, yoksa `NOT_MEASURABLE` olarak mı kalsın.
- Verdict kriterleri (breakeven eşiği neyi "uygulanabilirlik adayı" sayar — ama bu
  production onayı DEĞİL).

---

**Status:** DRAFT — Level B proposal. Awaiting Meriç review. No runner, no execution,
no production change.
