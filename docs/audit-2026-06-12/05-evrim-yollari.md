# Bölüm G — Evrim Yolları, Hızlı Nakit Akışı, SWOT, Pozisyonlama

## G.1 — 10 EVRİM YOLU

### YOL 01: B2C SaaS — Bireysel trader/yatırımcı aboneliği
**Yön:** web/ dashboard'u freemium aboneliğe açmak. **Kitle:** Aktif bireysel yatırımcı. **Hız:** Orta. **Gelir:** Orta (churn yüksek pazar).
**Teknik gereksinim:** Stripe + auth zaten var; deploy (Vercel+VPS), plan/limit katmanı, mobil uyum.
**İlk adım:** Landing+waitlist (bu hafta). **Risk:** Edge kanıtsızken "kazandıran sinyal" diye satılırsa itibar+regülasyon (P8) çarpması.
**12 ay senaryosu:** 300-800 ödeyen × $15-25/ay = $5-15k MRR; ancak ancak kanıt yayını ve niş seçimiyle.

### YOL 02: B2B API — Finansal kurumlara veri servisi
**Yön:** scan/score/inference router'larını anahtar+kota ile dışa açmak. **Kitle:** Robo-advisor, portföy uygulamaları, fintech startup'lar. **Hız:** Orta. **Gelir:** Yüksek (az müşteri, yüksek sözleşme).
**Teknik:** API key yönetimi, rate limit, SLA, dokümantasyon portalı (~2-4 hafta). **İlk adım:** 3 fintech'le keşif görüşmesi.
**Risk:** Veri kalitesi kanıtı istenir — edge sorusu burada da gelir ama "tarama altyapısı" olarak satılabilir.
**12 ay:** 3-5 müşteri × $500-2k/ay.

### YOL 03: White Label — Aracı kurum/eğitmen markasıyla
**Yön:** Dashboard+Academy'nin markalanabilir kopyası. **Kitle:** Forex/CFD broker'ları, finans eğitmenleri, RIA'lar. **Hız:** Yavaş (satış döngüsü). **Gelir:** Çok yüksek (kurulum $10-50k + aylık).
**Teknik:** Tema/tenant ayrımı (orta iş). **İlk adım:** 1 eğitmenle pilot konuşması. **Risk:** Tek-kişilik ekiple kurumsal destek taahhüdü.
**12 ay:** 1-2 pilot.

### YOL 04: Academy önce — eğitim odaklı freemium traction ⭐
**Yön:** Finance Academy'yi ürünün ön kapısı yapmak: ücretsiz öğren → kişiselleştirilmiş yol → premium'da sinyal/araçlar. **Kitle:** Öğrenmek isteyen yeni yatırımcı (P1). **Hız:** Hızlı. **Gelir:** Orta ama bileşik (retention + veri flywheel).
**Teknik:** Modül 16 entegrasyonu (router+UI+seed) — 2 hafta. **İlk adım:** FinanceAcademy duplikasyonunu çöz, seed'i çalıştır.
**Risk:** Eğitim tek başına yavaş para; sinyal tarafıyla köprü kurulmazsa "bir kurs platformu daha".
**12 ay:** 2-5k kayıtlı öğrenen, %3-5 premium dönüşüm; asıl ödül: kullanıcı-öğrenme verisi (P12'nin moat'ı).
**Neden ⭐:** Regülasyon-hafif, edge-kanıtı gerektirmez, 12 perspektifin 6'sı (P1,P5,P8,P9,P11,P12) bu yolu işaret ediyor.

### YOL 05: Newsletter/Signal servisi — haftalık rapor ⭐
**Yön:** weekly_report + agents çıktısını otomatik bültene dönüştürmek (Substack/Beehiiv). **Hız:** Çok hızlı (altyapı %90 hazır: report_generator, weekly_report.py, headroom enrichment).
**Gelir:** Düşük-orta başlar, listeyle büyür. **İlk adım:** 1 hafta — rapor şablonunu bülten formatına çevir, ilk 4 sayı ücretsiz.
**Risk:** İçerik "tavsiye" diline kayarsa P8; "piyasa karnesi + eğitim" diliyle güvenli.
**12 ay:** 3-10k abone, $1-4k/ay premium.

### YOL 06: Telegram/Discord bot — topluluk dağıtımı
**Yön:** Mevcut telegram_bot'u public kanala + premium kanala genişletmek. **Hız:** Hızlı (bot çalışıyor). **Gelir:** Orta.
**İlk adım:** Public "günlük piyasa brief" kanalı (sinyal değil, brief — uyum açısından). **Risk:** Telegram sinyal kanalı pazarı dolandırıcı dolu — itibar yönetimi şart; edge'siz sinyal burada da yasak.
**12 ay:** 1-5k üye, premium $10-20/ay × 100-300.

### YOL 07: Hibe / AR-GE yolu
**Yön:** grant_documents'ı canlandır: TÜBİTAK 1507/1512 veya AB/AWS Gründungsfonds; Academy+XAI merkezli başvuru. **Hız:** Yavaş (3-6 ay). **Gelir:** Yüksek tek seferlik ($50-500k), seyreltmesiz.
**İlk adım:** FINANZPLAN'ı güncel sistemle yenile + akademik danışman bul. **Risk:** Bürokrasi zamanı; ticari momentumu yavaşlatabilir.

### YOL 08: Accelerator yolu
**Yön:** YC/Techstars başvurusu. **Ön şart:** P6'nın dediği — kullanıcı görüşmeleri ve ilk traction olmadan başvuru zayıf. **İlk adım:** Önce Yol 04/05 ile 60 gün kanıt topla, sonra başvur. **12 ay:** Kabul halinde $125-500k + ağ.

### YOL 09: Açık kaynak + Pro (open-core)
**Yön:** indicators+data_fetcher+backtest çekirdeğini aç, skor/DRL/Academy kapalı tut. **Hız:** Orta. **Gelir:** Dolaylı (dağıtım+işe alım+güven).
**İlk adım:** Lisans kararı + 1 paketi PyPI'da dene. **Risk:** Moat erozyonu (P7); bakım yükü.

### YOL 10: Kurumsal yatırım araçları (hedge fund / family office)
**Yön:** Backtest motoru + slippage/outcome altyapısını butik fonlara araştırma aracı olarak satmak. **Hız:** Yavaş. **Gelir:** Yüksek ama erişim zor. **İlk adım:** Şimdilik izle; B2B API (Yol 02) üzerinden doğal evrim.

## G.2 — HIZLI NAKİT AKIŞI SENARYOLARI

| Senaryo | Hedef kitle | Min. hazırlık | İlk gelir | Aylık potansiyel | Ön şart / Not |
|---|---|---|---|---|---|
| Waitlist + lifetime deal | Erken adoptörler | 3 gün (landing yok — Sorun #6) | 2-3. hafta | $2-5k tek seferlik | Landing + demo videosu |
| Haftalık "Piyasa Karnesi" bülteni | Bireysel yatırımcı | 1 hafta (weekly_report hazır) | 3-4. hafta | $1-3k | Tavsiye değil karne dili (P8) |
| Telegram public→premium kanal | Trader topluluğu | 3 gün (bot çalışıyor) | 2. hafta | $0.5-2k | Track record yayını ile |
| 1-on-1 "sistemli tarama" danışmanlık | Üst segment | 0 gün | Bu hafta | $1-5k | Zaman satıyor — ölçeklenmez, köprü geliri |
| Demo günü → angel çek | Yatırımcılar | 2 hafta (memo+video) | 30-60 gün | $25-100k tek | Önce 100 waitlist kanıtı |
| Hibe başvurusu | TÜBİTAK/AWS | 3 hafta (dosyalar %60 hazır) | 3-6 ay | $50-500k tek | Academy merkezli anlatı |
| Freemium SaaS MVP | Bireysel | 4 hafta (deploy+billing) | 5-6. hafta | $1-5k | Auth fix (P0) önce |
| API beta erişimi | Fintech dev | 2 hafta | 4-6. hafta | $0.5-3k | 3 keşif görüşmesi önce |

**Gerçekçilik notu:** Bu tablolardaki ilk-ay rakamları ancak landing+dağıtım (bugün sıfır) kurulursa geçerli. Mevcut durumda tüm senaryoların ortak kritik yolu: **landing → kanıt yayını → liste.**

## G.3 — SWOT (perspektif kaynaklı)

**GÜÇLÜ:**
- Tam yığın, çalışan, test edilmiş altyapı; tek komut başlatma (P3, P10)
- Yürütme hızı: 43 commit/3 hafta, kendi audit'ini yapan kültür (P6)
- Kalibrasyon+ablation+walk-forward metodolojik olgunluk (P5)
- Çok-agent mimarisi + self-evolving Academy konsepti — hikâye değeri (P11, P3)
- Otomasyon omurgası: scheduler 10+ job, paper trading döngüsü (P12)

**ZAYIF:**
- Sinyal edge'i kanıtlanmadı; mevcut audit ters yönde (P2, P4) — **ana kısıt**
- 0 kullanıcı, 0 dağıtım, landing yok (P3, P6, P11)
- Academy entegre değil + duplicate (P9)
- Konumlandırma seçilmemiş: trader/öğrenen/B2B (P1, P4, P7)
- Tek kurucu + auth güvenlik regresyonu açık (P4, P8)
- DRL modelleri 3 ay bayat — "AI" iddiasının zayıf karnı (P2)

**FIRSATLAR:**
- "Öğrenen yatırımcı" nişi — eğitim+araç birleşimi rakipsiz (P1, P9)
- Kullanıcı-öğrenme-davranış verisi flywheel'i = 2030 moat'ı (P7, P12)
- Hibe/kamu fonu: XAI+kapsayıcılık anlatısı hazır (P5)
- Build-in-public + dürüst track record = bedava medya (P11)
- B2B API: retail churn'ünden bağımsız gelir (P4)
- MCP/agent-eklentisi olarak genel AI asistanlarına bağlanma (P12)

**TEHDİTLER:**
- Frontier modellerin tarama/analizi commodity'leştirmesi (P12)
- Regülasyon: tavsiye sınırı, performans pazarlama kuralları (P8)
- Dağıtımı güçlü rakibin fikri kopyalaması (P7)
- Edge'siz sinyal satışının itibar intiharı olması (P2, P11)
- Retail sinyal pazarının yapısal churn'ü (P4)

## G.4 — POZİSYONLAMA ÖNERİLERİ

**Yatırımcı pitch:** "FinPilot, yeni yatırımcıyı yapay zekâyla hem eğiten hem donatdan tek platform — kullanıcı öğrendikçe sistem kişiselleşiyor, kişiselleştikçe kopyalanamaz bir davranış-veri katmanı birikiyor."
**Hibe öz tanımı:** "FinPilot, açıklanabilir ve kalibre edilmiş yapay zekâ modelleriyle bireysel yatırımcıların finansal okuryazarlığını ölçülebilir biçimde artıran, kendi içeriğini otonom ajanlarla üretip denetleyen açık metodolojili bir eğitim-karar destek platformudur."
**Landing başlığı:** "FinPilot — Yatırımı öğren, piyasayı tara, kararını veriyle ver. Sana özel yapay zekâ koçun her sabah hazır."
**Developer community:** "FinPilot, çok-zaman-dilimli tarama, kalibre skor ve PPO-ensemble altyapısını tek API'de toplayan; test, audit ve walk-forward disiplinine takıntılı bir Python/Next.js fintech stack'idir."
**Medya başlığı:** "FinPilot: Tek geliştirici, kendi yapay zekâsına 'henüz kazandırmıyor' diyecek kadar dürüst — şimdi yatırımcı eğitiminde aynı şeffaflığı deniyor."
**Akademik özet:** "FinPilot, ensemble derin pekiştirmeli öğrenme sinyalleri ile Brier-kalibrasyonlu teknik skorlamayı, otonom çok-ajanlı pedagojik içerik üretimiyle birleştiren; sinyal sonuçlarını T+k ufuklarında uzlaştırarak hem finansal hem eğitsel çıktıyı ölçen bütünleşik bir sistemdir."
