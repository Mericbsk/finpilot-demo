# FinPilot — Bugünkü Tüm Testlerin Kontrolü, Nihai Özet ve Değişim Planı

**Tarih:** 2026-07-15
**Kapsam:** Gün boyu yapılan ~30 backtest/analiz (iki kaynak: sohbet-tabanlı + VS Code runner'ları). Doğru/hatalı ayrımı, nihai karar ve "hangi değişiklik → hangi beklenen sonuç" haritası.
**Durum:** Araştırma özeti + karar. Production ağırlık/threshold değişikliği ÖNERİLİYOR ama shadow doğrulaması şart.

---

## 1. Test Envanteri (bugün yapılanlar)

| # | Test | Kaynak / veri | Örneklem | Ana çıktı |
|---|------|---------------|----------|-----------|
| 1 | Tek-sinyal + threshold | signals_archive | 5.070 | score/rr zayıf, volatilite güçlü |
| 2 | Walk-forward IS/OOS | archive | 2.065/3.005 | score OOS'ta çöküyor (1.92→0.99) |
| 3 | Squeeze (float/short) | EODHD | 5.805 | short≥20 ≥%10 lift 2.57 |
| 4 | FINRA nokta-zamanlı short | FINRA | 6.042/6.410 | squeeze look-ahead DEĞİL (2.74) |
| 5 | Intraday stop testi | Alpaca 15dk | 800 | 1.5×ATR stop + 5×ATR TP en iyi |
| 6 | SEC catalyst | EDGAR | 6.410 | 8-K hafif (1.28), Form4 yok |
| 7 | Haber + volume | EODHD | 6.410 | haber değersiz; volume işi yapar |
| 8 | Sektör / cluster / tutma | Alpaca/EODHD | 562 | Tech/Fin tutarlı; T+10 outlier; cluster sorun değil |
| 9 | Kalibrasyon + detaylı | enriched_v3 | 6.410 | V2 skoru kalibre; short+gap tek süper-etkileşim |
| 10 | Uçtan-uca üretim config | enriched_v3 | 6.410 | 121→~5/gün, %32→%62 (favorable) |
| 11 | Eski vs V2 A/B (favorable) | full_universe | 53.859 | V2 top-10 %57 vs legacy %36 |
| 12 | full_universe backtest | full_universe | 53.859 / 1.932 sembol | ATR≥6 lift 1.54; entry_ok zayıf |
| 13 | composite_score_audit | full_universe | 53.859 | composite KIRIK (monotonluk 0.44) |
| 14 | precision_selectivity (maliyetli) | 27.386 symbol-day | — | ATR≥6 %60; düşük-vol %2.5 |
| 15 | score_formula_comparison | legacy 5 / V2 4 | locked OOS | legacy_quality %55, v2_confirmation %50 |
| 16 | phase1_7 + barrier gridleri | full_universe | 165 aday | replay=partial; execution kanıtı değil |
| 17 | factor_ablation (son 14 gün) | 249 | — | Temmuz zayıf: hit %6, beklenti −%1.1 |
| 18 | P0 telemetry + parity | kod | 3 test | reject_reason + component breakdown |
| 19 | P0 execution replay | triple-barrier | 901/62 | maliyetli gerçek P&L |
| 20 | P0 exit-sensitivity gridi | full_universe | V2 n=62 | tp5/sl1 en iyi (+%2.05) |
| 21 | common_buy_accuracy | ortak AL | locked OOS 44 | legacy %54.5, V2 %45.5 |
| 22 | v2_precision_execution | birleşik batarya | OOS 19-62 | v2+ATR+RVOL +%5.89 (küçük-n) |

---

## 2. DOĞRU Kısımlar (güvenilir, tekrar tekrar doğrulandı)

1. **Volatilite (ATR) gerçek ve en sağlam edge.** Full-universe + maliyet + cluster-bootstrap + walk-forward + 6/6 ay stabil. ATR≥4 lift 1.44, ATR≥6 lift 1.54.
2. **Legacy production composite KIRIK.** Monotonluk 0.44; composite↔ATR korelasyonu −0.06; ranking baz-altı (%33 top-10). Sıralayıcı olarak kullanılamaz.
3. **Metodoloji titiz:** gerçekçi maliyet (%0.55), cluster-bootstrap, locked-OOS, triple-barrier execution. Favorable-movement'ten çok daha doğru.
4. **P0 altyapısı doğru ve değerli:** telemetry parity, point-in-time replay, TP/SL/slippage/commission barrier. Testler geçiyor.
5. **Exit-config belirleyici (kanıtlı):** V2 P&L exit'e aşırı bağlı — tp5/sl1 = +%2.05 (PF 1.43, en iyi); tp2/sl1 = −%0.35; tp5/sl3 = −%1.18. Asıl katil YAKIN TP (2x)'di.
6. **short interest + volatilite (squeeze)** büyük hareket (>=%10) yakalamada en güçlü kombinasyon; nokta-zamanlı doğrulandı.
7. **Temkinli nihai duruş** ("ağırlığı değiştirme; shadow adayı tut; data-contract + büyük-n gerekli") — doğru ve olgun.

---

## 3. HATALI / Yanıltıcı Kısımlar (yakalandı ve düzeltildi)

1. **İlk "V2 NO-GO" başlığı** — HATALIYDI: yanlış exit (tp2/sl1) + farklı evren kıyası. Sonraki exit-sensitivity raporu doğru şekilde geri aldı.
2. **"V2 +%4.02 viable" (n=28)** — küçük-örneklem gürültüsü; n=62'de tp5/sl1.5 başabaş (−%0.005). Büyük örneklem düzeltti.
3. **Favorable-movement A/B ("V2 %57 vs %36")** — precision olarak DOĞRU ama P&L olarak YANILTICI. **En derin ders: precision ≠ realized P&L.**
4. **%81'lik "en iyi kombolar"** (ATR≥4 AND ATR≥6 AND RVOL≥2 AND composite≥70) — aday sayılması HATALIYDI: redundant aynı-aile, küçük-n, çoklu-test bias. Doğru şekilde reddedildi.
5. **"legacy" = legacy_quality karışıklığı** — P0'da kazanan "legacy" kırık composite değil, onarılmış volatilite-ağırlıklı formül. Netleştirildi.
6. **v2+ATR+RVOL OOS +%5.89** — umut verici ama validation NEGATİF (−%2.4) + n=19. Kanıt değil; shadow adayı.
7. **T+10 "ort +%21" tutma kazancı** — HATALIYDI (outlier); medyan sadece +%1.2. Medyan kontrolü yakaladı.
8. **Persistence "+3p"** — look-ahead artefaktı; doğru testte sıfır katkı.
9. **Mutlak skor eşiği** — IS→OOS %15 kayıyor; göreli seçim (top-N) doğru.

---

## 4. NİHAİ ÖZET

**KESİN olanlar:**
- Volatilite (ATR/gap/RVOL/short) gerçek edge; RSI/MACD ve risk/ödül değersiz.
- Kırık legacy composite ranking'den emekli edilmeli.
- Yerine gelen skor volatilite-farkında olmalı (V2 ya da legacy_quality).
- **Precision ≠ P&L.** V2 hareket eden isim buluyor ama execution (whipsaw + maliyet) sonrası yakalamak zor; V2 yüksek-varyans.
- V2'nin en iyi exit'i: TP 5×ATR / SL 1×ATR.

**BELİRSİZ (daha fazla veri şart):**
- V2 vs legacy_quality execution-P&L'de başa baş / sonuçsuz (V2 n=62/19 küçük, farklı evren, en iyi filtrelerde validation negatif).
- V2 OOS avantajı gerçek mi rejim-şansı mı.
- Eksik veri: spread, dollar-ADV, market cap, feature-age, tarihsel-short tazeliği.

**KARAR:**
1. Kırık legacy composite'i ranking'den çıkar (kesin).
2. V2 ağırlıklarını production'a SERT geçirme (validation negatif, küçük-n, eksik data-contract).
3. V2 + ATR/RVOL'ü shadow/paper adayı tut — kilitli exit (5×/1×).
4. Data-contract'ı genişlet + rolling walk-forward.
5. Forward paper/shadow = nihai hakem.

---

## 5. Değişim → Beklenen Sonuç Haritası

Her satır: yapılacak değişiklik, beklenen çıktı etkisi, kanıt gücü. **Güven:** ✅ kanıtlı / 🟡 muhtemel / 🔬 shadow şart.

### A. Skor / ranking değişiklikleri

| Değişiklik | Beklenen sonuç | Güven |
|---|---|---|
| **Kırık legacy composite'i ranking'den çıkar → V2/volatilite skoru** | Liste **~%93 değişir**; düşük-vol trend isimler çıkar, volatil/squeeze girer. Favorable-move top-10 precision **%36 → %57**. Realized P&L belirsiz (execution farkı). | ✅ precision / 🔬 P&L |
| **RSI/MACD raw-score ağırlığını kıs (×0.5→×0.25)** | Skorun anti-tahminci bileşeni zayıflar; monotonluk düzelir. Sinyal seçimi az değişir (score zaten kapı). | ✅ |
| **risk_reward'ı skordan çıkar** | Etki minimal (zaten negatif katsayı); temizlik. | ✅ |
| **52-hafta aşırı-uzama cezası ekle** | Zirveye yapışık (dist>0.9) isimler alta iner; onlar zaten düşük isabetli (lift 0.68). | ✅ |
| **short'u ana faktör yap (squeeze 70/30 short-ağır)** | ≥%10 büyük hareket yakalama artar; squeeze isimleri öne çıkar. | ✅ (nokta-zamanlı) |

### B. Giriş kapısı (entry_ok)

| Değişiklik | Beklenen sonuç | Güven |
|---|---|---|
| **Sıkı kapı: ATR≥4 VEYA gap≥3 VEYA RVOL≥2 (score≥2 fallback kalksın)** | Ham entry_ok **~%59 azalır** (415/gün→~170); favorable precision **%32 → %48**. | ✅ |
| **Kapıya düşük-vol elemesi (ATR<2 çıkar)** | Düşük-vol junk çıkar (precision %2.5'lik grup); az sinyal, yüksek kalite. | ✅ |
| **Eski score==3 kapısını koru** | Değişim yok; ama sadece %3.58 favorable recall (hareketlerin %96'sını kaçırır). | ✅ (mevcut zayıflık) |

### C. Çıkış (exit) — V2 için KRİTİK

| Değişiklik | Beklenen sonuç | Güven |
|---|---|---|
| **V2 exit'i TP 5×ATR / SL 1×ATR'ye kilitle** | V2 OOS execution **−%0.35 → +%2.05** (PF 0.92→1.43). Time-exit oranı artar (kazananlar koşar), SL whipsaw azalır. **En iyi profil.** | ✅ (exit grid) |
| TP 2×ATR (yakın) | V2'yi öldürür (−%0.35): büyük squeeze hareketi kesilir. **Kullanma.** | ✅ |
| SL 1.5×/2×/3× (geniş) | V2 kötüleşir (−%0.005 / −%0.46 / −%1.18): geniş stop + uzak TP bu veride kötü. | ✅ |
| Legacy exit 2×/1× | Legacy pozitif (+%2.10, PF 1.78) — sakin isimler bununla iyi. | ✅ |

### D. Filtre / seçicilik

| Değişiklik | Beklenen sonuç | Güven |
|---|---|---|
| **Günlük tavan top-5..10** | ~5-10 sinyal/gün, favorable precision ~%55-62. | ✅ |
| **V2 + ATR≥4 + RVOL≥2 ek filtre** | OOS execution **+%5.89 (PF 2.16)** — EN İYİ; AMA validation −%2.4, n=19 → zamana duyarlı. **Sadece shadow.** | 🔬 |
| **Likidite filtresi (min fiyat $3-5 + hacim) + ATR tavanı (>15-20 ele)** | Junk micro-cap'ler (CREG ATR38) çıkar; tradeable kalite artar; hafif sinyal azalır. | 🟡 |
| **Sektör tilt (Tech/Fin +, Cons.Cyc. −)** | Marjinal; IS/OOS'ta kararsız (Financials %82→%65 kaydı). **Ekleme.** | ❌ (test edildi) |
| **Persistence / haber / mutlak eşik** | Katkı yok / look-ahead. **Ekleme.** | ❌ (test edildi) |

### E. Rejim / risk yönetimi

| Değişiklik | Beklenen sonuç | Güven |
|---|---|---|
| **Rejim freni (düşük-vol / zayıf ay durdur)** | Negatif-beklenti dönemlerinden kaçınır (Temmuz −%1.1); kötü rejimde az/sıfır sinyal. | 🟡 |
| **Yüksek varyans için pozisyon küçültme** | V2 drawdown'ı −%60'a çıkabiliyor; küçük pozisyon = hayatta kalma. | ✅ (DD gözlemi) |
| **Conviction prob'ları gerçeğe çek (A=0.73, B=0.59, C=0.52)** | Sadece etiket; sinyal değişmez. Kullanıcıya dürüst olasılık. | ✅ |

### F. Altyapı (P0 — production kararı için ZORUNLU)

| Değişiklik | Beklenen sonuç | Güven |
|---|---|---|
| **reject_reason[] + score_component_breakdown telemetrisi** | Her sinyalin neden kabul/red edildiği görünür; skor bileşen katkısı denetlenebilir. | ✅ (kuruldu) |
| **Point-in-time replay + execution barrier** | Backtest yerine gerçek P&L (TP/SL/slippage/komisyon). | ✅ (kuruldu) |
| **Data-contract genişletme (feature-age, tarihsel short, spread/ADV/market cap)** | Eksik alanlar tamamlanınca ağırlık değişikliği güvenli test edilebilir. | 🔬 (yapılacak) |
| **Rolling walk-forward + forward shadow** | V2 vs legacy_quality'yi büyük-n, kilitli-exit, gerçek P&L ile ayırır → NİHAİ HAKEM. | 🔬 (yapılacak) |

---

## 6. Önerilen Uygulama Sırası

1. **Kesin ve güvenli olanlar (şimdi):** kırık composite'i ranking'den çıkar; RSI/MACD kıs; risk_reward çıkar; extension cezası; conviction prob düzelt; telemetry (kuruldu). → Kod zaten `FINPILOT_ENABLE_ALPHA_V2` arkasında.
2. **V2 exit'ini 5×/1×'e kilitle** (kanıtlı en iyi profil).
3. **Likidite + ATR tavanı koruması ekle** (junk temizliği).
4. **Shadow/paper forward test** (V2 vs legacy_quality, kilitli exit, gerçek P&L, büyük-n) — production switch'in ön koşulu.
5. **Data-contract genişlet** → V2+ATR+RVOL gibi güçlü ama küçük-n adayları rolling walk-forward ile doğrula.
6. **Production ağırlık/threshold'unu ancak forward-P&L kanıtıyla değiştir.**

**Tek cümle:** Yön kesin (volatilite-öncelikli, kırık composite gidiyor); V2 viable ama yüksek-varyans ve exit-duyarlı; kesin production switch, forward shadow-P&L kanıtına bağlı.
