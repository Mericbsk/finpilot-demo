# Çok-Boyutlu Karar Sistemi — Dört Test SONUÇ Raporu

Sürüm: 1.0 · Tarih: 2026-07-31 · Level A (araştırma) · Veri: edge_recheck (honest) + enriched sub-faktörler
Metrik: gerçekleşen (mae5=downside, mfe5=upside-range, c2c5_net=getiri, win=P(getiri>0)); rank-IC.

---

## YÖNETİCİ ÖZETİ

Dört test, "çok karar dili" sorusunu netleştirdi: **gerçek, geçerli TEK boyut volatilite/aralık (ATR).**
Getiri/yön boyutunda sinyal yok; conviction/Grade **kalibre değil, hatta TERS.**

| Boyut | Sonuç | Kullanıma uygun mu |
|---|---|---|
| **Volatilite/Aralık (ATR)** | Güçlü (IC ±0.5), monoton, **her iki rejimde de geçerli** | ✅ **Evet** — "ne kadar oynar" (yön değil) |
| Sakinlik (52-hafta konumu) | Küçük, ATR'ye kısmen bağımlı (kor −0.60) | ⚠ İkincil nüans |
| Yön/Getiri | Sinyal yok | ❌ Hayır |
| **Conviction / Grade** | **TERS kalibre** (A %23 < B %27 < C %42 kazanç) | ❌ **Yanıltıcı — düzelt/kaldır** |

---

## TEST 1 — Birleşik risk skoru vs tek ATR
Birleşik (ATR+lottery+squeeze+overnight, gün-içi z):
- mae5: birleşik IC **−0.431** vs tek ATR **−0.514** → **birleştirmek KÖTÜLEŞTİRDİ.**
- mfe5: birleşik **+0.383** vs ATR **+0.496** → yine kötü.
**Sonuç:** Risk boyutu = **tek başına ATR.** Diğer faktörler ATR'nin gürültülü/redundant versiyonu; eklemek dilue ediyor. Combo yapma.

## TEST 2 — 2D bağımsızlık (ATR × 52-hafta konumu)
- ATR ↔ dist_52w rank-kor **−0.599** → orta düzey ilişkili (yüksek ATR ~ zirveden uzak), tam bağımsız DEĞİL.
- 2×2 MAE medyan: düşükATR/uzak −2.71 · düşükATR/zirveye-yakın −1.89 · yüksekATR/uzak −5.87 · yüksekATR/zirveye-yakın −5.27.
**Sonuç:** Downside'ı **ATR yönetiyor** (düşük ~−2, yüksek ~−5.5). dist_52w her ATR kovasında küçük bir "sakinlik" katıyor (zirveye yakın = biraz az downside) ama **ATR baskın.** İki temiz bağımsız eksen değil; ATR birincil, 52w ikincil hafif tilt.

## TEST 3 — Rejim dayanıklılığı (kritik)
- mae5: ATR IC **bear −0.469 / bull −0.52** · mfe5: **bear +0.522 / bull +0.491.**
**Sonuç:** ATR'nin risk/aralık yordaması **her iki rejimde de güçlü ve AYNI işaret** → **rejim-dayanıklı, gerçek boyut.** (Yön boyutunun aksine — o rejimde işaret değiştiriyordu.) Combo yine ATR'nin altında her rejimde.

## TEST 4 — Kalibrasyon (skor/conviction → gerçek kazanç olasılığı)
- finpilot quintile P(kzn)%: [53.3, 52.5, 52.6, 54.9, 57.8] — monoton değil, sapma 1.7p → **kalibre değil.**
- composite quintile: [53.6, 50.9, 48.5, 49.8, 48.3] — **azalan** → kalibre değil.
- **conviction_tier → P(kazanç)%: A=23.1 (n13) · B=27.3 (n88) · C=42.0 (n143)** → **TERS!** En yüksek konviksiyon (A) **en düşük** kazanç oranı.
**Sonuç:** Conviction/Grade kazanç-olasılığını yansıtmıyor; **ters yönde.** "Grade A = elit/başarılı" göstermek **yanıltıcı ve compliance-riskli** (A n'i küçük ama A<B<C eğilimi B/C'de sağlam).

---

## ÜRÜN ÖNERİSİ (kanıta dayalı)

1. **Kullanıcıya gösterilecek TEK gerçek boyut: Volatilite/Beklenen-Aralık (ATR).** "Bu isim ~%X oynar (iki yönde)" — güçlü, monoton, rejim-dayanıklı. **Yön/kazanç iması YOK.**
2. **İkincil nüans: 52-hafta konumu** ("zirveye yakın = daha sakin") — küçük ek bilgi.
3. **Conviction / Grade A-B-C'yi kaldır veya dürüstçe yeniden kalibre et** — mevcut hâli TERS (A en kötü). Kazanç/kalite ima eden etiket compliance açısından da düzeltilmeli (YONERGE §12, "past performance").
4. **"Yükselecek / yüksek başarı olasılığı" iddiası desteklenmiyor** — hiçbir boyut yön/kazanç yordamıyor.

**Stratejik:** Dürüst çok-boyutlu yüzey = **1 volatilite ekseni + 1 zayıf sakinlik nüansı + açık "yön belirsiz" etiketi + kaldırılmış/yeniden-kalibre conviction.** Alfa vaat etmeyen, dürüst karar-destek — aws impact/eğitim hattıyla uyumlu.

---

## GOVERNANCE / KISIT
- Level A analiz; conviction/Grade tanımı veya boyut-yüzeyi üretim değişikliği = **Level B**.
- conviction A n=13 küçük — inversiyon eğilimi B(88)/C(143)'te sağlam ama A kesinliği için daha çok veri iyi olur.
- D4 (işlem-yapılabilirlik/fill) ve davranışsal karar-değeri hâlâ **execution/analitik veri bekliyor** (kapsam dışı).
