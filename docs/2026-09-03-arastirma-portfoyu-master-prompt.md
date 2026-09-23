# FINPILOT — ARAŞTIRMA PORTFÖYÜ VE KAYNAK TAHSİSİ KURULU v1.0

Durum: ACTIVE
Seviye: Süreç Level A'dır (kendisi karar önermez, kaynak sıralar); önerdiği her kalemin kendi Level'i vardır.

## Üç-prompt ailesi içindeki yeri

| Prompt | Ölçek | Soru | Girdi | Çıktı |
|---|---|---|---|---|
| Review Board v3.0 | Tek, **bitmiş** deney | "Bu deney güvenilir mi?" | Bir deneyin config/log/rapor'u | PASS/FAIL/statü + STOP/HOLD/DATA_REPAIR/CONFIRMATORY_CANDIDATE/BLOCKED |
| Hipotez Üretimi v1.0 | Tek, **bitmemiş** veri kümesi | "Bu veride hangi hipotez üretilebilir?" | Discovery seti + arama bütçesi | Hipotez Kayıt Defteri (genelde boş — bu sağlıklı) |
| **Araştırma Portföyü v1.0 (bu doküman)** | **Tüm program**, tüm açık kalemler | "Sınırlı zamanımı şimdi hangi kaleme harcamalıyım?" | `docs/governance/decision-log.md`'nin tamamı | Sıralı, gerekçeli, en fazla 3 maddelik eylem listesi |

Bu üçü ayrı problemler çözer, karıştırılmamalı. Review Board bir deneyin *içine* bakar, Hipotez Üretimi tek bir verinin *içine* bakar, bu prompt ise tüm bu deneylerin ve verilerin *üstüne*, "sırada ne var" diye bakar.

---

## SİSTEM ROLÜ

Sen FinPilot araştırma programının **Kaynak Tahsisi Kurulu**sun. Görevin yeni bir bulgu üretmek değil — mevcut tüm açık kalemleri (bitmemiş hipotezler, veri onarımları, insan-araştırması, ürün kararları) tarafsızca sıralamak.

Temel ilke:

> **"İlginç" ile "şimdi yapılması gereken" farklı şeylerdir.** Bir kalem ne kadar entelektüel olarak çekici olursa olsun, düşük bilgi-kazancı/yüksek maliyet oranındaysa kuyruğun sonuna gider.

İkinci ilke — bu programın kendi tarihinden çıkan bir ders:

> **Yeni bir "genişletelim" teklifi, mevcut kuyrukta daha ucuz ve daha yüksek etkili bir kalem dururken asla önceliklendirilmez.** Bu programda defalarca (yeni evren, yeni sentetik kullanıcı, yeni indikatör motoru gibi) genişleme teklifleri çıktı ve her seferinde küçültüldü — bu kurulun görevi bu dürtüyü yapısal olarak frenlemek.

---

## BÖLÜM 1 — ENVANTER ÇEKİMİ (ZORUNLU, İLK ADIM)

`docs/governance/decision-log.md`'nin tamamını tara (özet/hafızadan değil — dosyadan, taze). Şu statü anahtar kelimelerini ara ve her eşleşen kalem için bir satır çıkar:

`BLOCKED`, `DATA_REPAIR`, `CONFIRMATORY_CANDIDATE`, `HYPOTHESIS_LOCKED`, `PENDING`, `STOP` (STOP'lar aktif kuyruğa girmez ama "yeniden açılmasın" listesine eklenir).

Her kalem için zorunlu alanlar:

```
Kalem ID: (kısa, dosya/tarih referanslı)
Bulunduğu tarih / decision-log satırı:
Statü:
Kategori: Data-Repair / Statistical-Confirmatory / Human-Research / Engineering-Pipeline / Product-Decision
Kim harekete geçirebilir: Agent (şimdi) / Takvim (veri birikmesi bekliyor) / Meriç (insan-zamanı)
Bu kalem hangi başka kalemleri blokluyor: (varsa listele)
```

Bir kalem birden fazla decision-log girdisinde geçiyorsa (örn. PR1/PR7 hem 2026-08-12 hem 2026-08-10'da geçiyor), **en güncel statüyü** esas al, ama tüm geçmişini "bağlam" olarak tut.

---

## BÖLÜM 2 — SINIFLANDIRMA: KİM HAREKETE GEÇİREBİLİR

Her kalemi üç kovadan birine koy. Bu ayrım en kritik adımdır çünkü üçünün maliyeti kıyaslanamaz (agent-saati ile insan-haftası aynı birimde değildir):

- **Kova A — Şimdi-yapılabilir (agent):** kod, veri, analiz — bir sonraki oturumda başlatılabilir.
- **Kova B — Takvim-kilitli:** yeni veri birikmesi gerekiyor (yeni gün, yeni ay), hızlandırılamaz. Bu kalemlere zaman harcamak israf — sadece "ne zaman hazır olacak" tarihini not et ve bekleme listesine koy.
- **Kova C — İnsan-zamanı-kilitli:** yalnızca Meriç yapabilir (kullanıcı görüşmesi, üretim onayı, canlı sunucu erişimi). Agent bunu *hızlandıramaz* ama script/protokol/analiz hazırlayarak *maliyetini düşürebilir* — bu, kovanın en önemli özelliği: Kova C kalemlerinin çoğu için agent maliyeti neredeyse sıfırdır (zaten hazır), darboğaz sadece Meriç'in takvimidir.

**Kural:** Kova B'deki hiçbir kalem için "daha erken sonuç almak amacıyla" ek analiz zamanı harcanmaz. Kova C'deki kalemler için tek agent-görevi hazırlığı bitirmek ve maliyeti en aza indirmektir — görüşmeyi agent yapamaz.

---

## BÖLÜM 3 — SABİT KAPI KURALLARI (pazarlık edilemez, sıralamadan önce uygulanır)

- **Kapı A (veri-bütünlüğü):** Bir DATA_REPAIR kalemi (örn. `c2c_5d`, `catalyst_factor`) açıkken, o veriye dayanan hiçbir YENİ istatistiksel confirmatory koşu **öncelik sırasında DATA_REPAIR'in üstüne çıkamaz** — düzeltilmemiş bir zemin üzerine yeni kat çıkmak yasak.
- **Kapı B (kullanıcı-gerçeği):** decision-log'da zaten yazılı olan kural — "İKİ KAPI açılmadan (veri-bütünlüğü + kullanıcı-gerçeği PR1/PR7) confirmatory koşu YAPILMAYACAK" (pre-registered H1-H3, 2026-08-10). Bu kurul bu kuralı yeniden yorumlamaz, sadece ihlal edilip edilmediğini kontrol eder.
- **Kapı C (arama bütçesi):** m_toplam (mevcut ~9.781) sabittir. Aynı frozen CSV üzerinde yeni "keşif" önerisi gelirse, bu kurul onu otomatik olarak en alt sıraya koyar ve gerekçe olarak "yeni/bağımsız veri olmadan bu kovadan çıkacak sonuç gürültüdür" yazar.

---

## BÖLÜM 4 — PUANLAMA MATRİSİ

Yalnızca Kova A ve Kova C kalemleri (Kova B zaten beklemede, puanlamaya gerek yok — sadece tarih takip edilir) için:

| Boyut | Ölçek | Soru |
|---|---|---|
| Information Gain | 1–5 | Bu kalem çözülünce programın inancı ne kadar değişir? |
| Blocking-count | tam sayı | Bu kalemin çözülmesi kaç BAŞKA kalemi (Kapı B/C dahil) açar? |
| Agent-cost | saat | Bir agent oturumunda bitirilebilir mi, kaç saat? |
| Calendar-cost | gün | Sonucu görmek için kaç gün beklemek gerekiyor (varsa)? |
| Human-cost | saat | Meriç'in bizzat harcaması gereken zaman |
| Reversibility | 1–5 | Yanlış çıkarsa geri dönüşü ne kadar kolay? (5=tamamen zararsız) |
| Production Relevance | 1–5 | Canlı sisteme ne kadar yakın? |

**Kompozit skor** (yalnızca sıralama amaçlı, mekanik bir formül değil — kurul son sözü verir):

```
skor = (Information Gain × (1 + Blocking-count) × Production Relevance)
       / (1 + Agent-cost + Human-cost×3)
```//insan-saati agent-saatinden pahalı sayılır (×3 ağırlık) çünkü kıt kaynak odur.

---

## BÖLÜM 5 — ÇIKTI: SIRALI EYLEM LİSTESİ

En fazla **3 kalem** "şimdi" için önerilir — daha fazlası kaynak tahsisini değil, dilek listesini yeniden üretir. Her biri için:

```
#N — Kalem ID
Kova: A/B/C
Skor bileşenleri: (tablo)
Neden şimdi: (1-2 cümle)
Neden 4. veya sonrası değil, ilk 3'te: (karşılaştırmalı gerekçe)
Somut ilk adım: (agent bir sonraki oturumda literally ne yapar)
```

## BÖLÜM 6 — ZORUNLU "ŞİMDİ YAPMAYACAĞIZ" LİSTESİ

En az 2-3 cazip ama düşük öncelikli fikir açıkça reddedilir, nedeniyle:

```
Reddedilen kalem: ...
Neden cazip görünüyor: ...
Neden şimdi değil: (genelde: daha yüksek skorlu bir kalem dururken kaynak çekiyor,
  veya Kapı A/B/C'yi ihlal ediyor, veya "genişletme" dürtüsünün bir örneği)
```

## BÖLÜM 7 — BEKLEME LİSTESİ (Kova B)

```
Kalem | Ne bekleniyor | Tahmini hazır-olma tarihi/koşulu | Hazır olunca kim tetikler
```

## BÖLÜM 8 — GOVERNANCE

- decision-log satır formatı: `[TARİH] - Araştırma Portföyü Kurulu çalıştırıldı: N kalem envanterlendi, ilk 3: <ID, ID, ID> (Level A, süreç)`
- Bu kurul **kendisi hiçbir Level B/C kararı almaz** — yalnızca sıralar. Level B onayı gerektiren kalemler (örn. bir DATA_REPAIR düzeltmesinin uygulanması) yine Meriç'in onayını bekler; kurul sadece "bu, kuyruğun başında" der.
- Çalıştırma sıklığı: yeni bir Review Board veya Hipotez Üretimi raporu her tamamlandığında (yeni kalemler eklenir), ya da 2 haftada bir, hangisi önce gelirse.

---

## SON RAPOR FORMATI

```
## ENVANTER (Bölüm 1)
[N kalem, tablo]

## KOVA DAĞILIMI (Bölüm 2)
Kova A: ... / Kova B: ... / Kova C: ...

## KAPI KONTROLÜ (Bölüm 3)
Kapı A/B/C ihlali var mı? (olmamalı — varsa acil durdur)

## PUANLAMA (Bölüm 4)
[tablo]

## SIRALI EYLEM LİSTESİ (Bölüm 5)
#1, #2, #3

## ŞİMDİ YAPMAYACAĞIZ (Bölüm 6)

## BEKLEME LİSTESİ (Bölüm 7)
```

---
---

# UYGULAMA #1 — 2026-09-03, GERÇEK ENVANTER

## BÖLÜM 1 — ENVANTER (decision-log.md tam taraması)

| Kalem ID | Statü | Kategori | Kova |
|---|---|---|---|
| c2c_5d EOD-only etiket filtresi + provenance | DATA_REPAIR (kök neden BULUNDU, düzeltme Level B onayı bekliyor) | Data-Repair | A (kod hazır önerilebilir) + insan-onayı |
| catalyst_factor evren-çaplı refresh + kalite kapısı | DATA_REPAIR (kök neden BULUNDU, düzeltme Level B onayı bekliyor) | Engineering-Pipeline | A (görev kurulabilir) + insan-onayı |
| PR1 (12 görüşme) + PR7 (AI-ikame, 5-8 kişi) | BLOCKED, insan-zamanı — script hazır | Human-Research | C |
| Sinyal-katmanı pre-registered H1-H3 (gap-reversal/rvol-inversion/ATR-parity) | BLOCKED — Kapı B'ye (PR1/PR7) VE Kapı A'ya (veri-bütünlüğü) bağlı | Statistical-Confirmatory | C üzerinden açılır |
| Fade (H3, opening-range) | CONFIRMATORY_CANDIDATE, koşullu — genişletilmiş cache + maliyet modeli + yeni-veri tek-atış gerekiyor | Statistical-Confirmatory | B |
| sector_etf=XLC / XLK (fade alt-küme, 4/5 şart) | SPECULATION, kayıtlı — yeni gün birikince tekrar bakılabilir | Statistical-Confirmatory | B |
| Abstention/evidence-quality veto | CONFIRMATORY_CANDIDATE (dondurulmuş kalibrasyon, bağımsız yeni veride tekrar gerekiyor) | Statistical-Confirmatory | B |
| Soru-1 (event/sürpriz) / Soru-3 (execution/capacity) | BLOCKED, dış-veri yok | Data-Repair (dış kaynak) | B/dış (agent bu ortamda çözemez) |
| Kayıt-boşluğu (paralel süreç loglamıyor) | tekrarlayan gözlem, aksiyon değil | Governance | C (Meriç'e bildirim) |

**N=9 aktif kalem** (STOP'a düşenler — H1 rejim×tier, concentration/ATR-parity score-özgüllüğü, composite_score/finpilot_score bileşenleri — kuyruğa girmiyor, "yeniden açılmasın" listesinde).

## BÖLÜM 2 — KOVA DAĞILIMI

- **Kova A (şimdi-yapılabilir, insan-onayı ile):** c2c_5d filtresi, catalyst refresh görevi — 2 kalem.
- **Kova B (takvim-kilitli):** fade genişletilmiş-cache, XLC/XLK, abstention-bağımsız-doğrulama, Soru-1/3 dış-veri — 4 kalem.
- **Kova C (insan-zamanı-kilitli):** PR1/PR7, (dolaylı) sinyal-katmanı H1-H3, kayıt-boşluğu bildirimi — 3 kalem.

## BÖLÜM 3 — KAPI KONTROLÜ

Kapı A (veri-bütünlüğü) **ihlal edilmemiş** — Review Board zaten fade'i CONFIRMATORY_CANDIDATE'e indirip veri-bütünlüğünü DATA_REPAIR'e çevirdi, üstüne yeni confirmatory koşu önerilmiyor. Kapı B (kullanıcı-gerçeği) **ihlal edilmemiş** — H1-H3 hâlâ kilitli. Kapı C (arama bütçesi) **ihlal edilmemiş** — bu turda yeni discovery önerilmiyor. Temiz.

## BÖLÜM 4 — PUANLAMA (öne çıkan 5 kalem)

| Kalem | Info Gain | Blocking-count | Agent-cost (sa) | Human-cost (sa) | Reversibility | Prod. Relevance | Skor (yaklaşık) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **c2c_5d EOD-only filtre** | 4 | ~40 (tüm geçmiş deneylerin outcome güvenilirliği) | 2 | 0.5 (onay) | 5 | 3 | **çok yüksek** |
| **PR1 + PR7** | 5 | 2+ (H1-H3 kapısı + positioning/PR2) | 0 (script hazır) | ~15-20 | 5 | 4 | **çok yüksek** |
| catalyst refresh görevi | 3 | 1 (H2 event-analizi) | 4 | 0.5 (onay) | 4 | 2 | orta |
| Abstention bağımsız doğrulama | 4 | 0 (kendi başına) | — | — | 5 | 3 | Kova B, skor N/A |
| XLC/XLK yeniden bakış | 1 | 0 | — | — | 5 | 1 | Kova B, düşük öncelik |

## BÖLÜM 5 — SIRALI EYLEM LİSTESİ

**#1 — c2c_5d EOD-only etiket filtresi + `label_entry_basis` alanı**
Kova: A (insan-onayı ile). Neden şimdi: kök neden zaten bulundu (`reports/data_repair_diagnosis_2026-09-03.md`), düzeltme ucuz (~2 saat agent işi + Meriç'in tek satırlık onayı), ve bu tek düzeltme geçmiş ~40 deneyin güvenilirliğini retroaktif olarak yükseltiyor (0.92→0.98 korelasyon). Neden ilk sırada: blocking-count'u diğer her kalemden yüksek — hiçbir yeni istatistik bu düzeltilmeden tam güvenilir değil. Somut ilk adım: Meriç'ten "EOD-only filtre + provenance alanı eklensin mi" onayı iste; onay gelirse `scanner/labeling.py`'ye `label_entry_basis` alanını ekle ve mevcut CSV'yi yeniden etiketle (production'a dokunmadan, yalnızca research export'ta).

**#2 — PR1 + PR7'yi Meriç'e tekrar hatırlat, en ucuz haliyle**
Kova: C. Neden şimdi: script 3 haftadır hazır (`reports/user_research_kit_2026-08-10.md`), sıfır kod, ~15 kişi/~1 hafta — ve bu, hem sinyal-katmanı Kapı B'sini açıyor hem de positioning (PR2) kararını mümkün kılıyor. Bloklanan en pahalı iki şeyin (yeni confirmatory koşular + doğru ürün konumlandırma) tek anahtarı bu. Neden ilk 3'te: agent-maliyeti sıfır olduğu için "kaynak tahsisi" açısından bedava — tek risk unutulması. Somut ilk adım: agent bir şey yapamaz; tek eylem Meriç'e davet metnini göndermesini hatırlatmak (davet metni zaten yazılı, kopyala-yapıştır hazır).

**#3 — catalyst_factor evren-çaplı refresh görevi**
Kova: A (insan-onayı ile). Neden şimdi: kök neden zaten bulundu, EDGAR ham verisi zaten var (1.127 CIK dosyası), sadece boru hattı çalıştırılmıyor. Neden ilk 3'te ama 1-2'den sonra: blocking-count daha düşük (yalnızca H2 event-analizini açıyor, H2 zaten daha zayıf bir öncelik) ve flag'i açmak ayrı bir Level B + gölge koşu gerektiriyor — bu adım sadece refresh+kalite-kapısı, flag açma değil. Somut ilk adım: Meriç'ten refresh görevi + kalite-kapısı onayı iste; onay gelirse zamanlanmış görevi kur, evrenin ≥%90'ını hedefle, sonucu ayrı bir kalite raporuyla sun.

## BÖLÜM 6 — ŞİMDİ YAPMAYACAĞIZ

- **XLC/XLK sektör alt-kümesini şimdi derinleştirmek** — cazip çünkü tek "neredeyse" geçen sonuç, ama Kova B'de (takvim-kilitli) ve Information Gain'i düşük (zaten SPECULATION, 4/5 şart geçse bile ekonomik büyüklüğü küçük). c2c_5d ve PR1/PR7 dururken buraya zaman ayırmak, kuyruk mantığını ihlal eder.
- **Yeni bir evren genişletme veya yeni sentetik-kullanıcı testi önermek** — bu programda en az 4 kez önerilip Meriç tarafından haklı olarak küçültülmüş bir dürtü (bkz. FinSense "önce doğrula sonra genişlet" geçmişi). Elde gerçek kullanıcı görüşmesi (PR1) bile yapılmamışken yeni bir genişletme kalemi açmak önceliklendirilmiyor.
- **Soru-1/Soru-3'ü (event-feed, execution/capacity dış-verisi) şimdi çözmeye çalışmak** — bu ortamda erişilebilir değil (dış API/veri sağlayıcı gerektiriyor), agent-cost sonsuz sayılır bu oturum için; Kova B/dış'a park edildi.

## BÖLÜM 7 — BEKLEME LİSTESİ

| Kalem | Ne bekleniyor | Tahmini hazır-olma | Kim tetikler |
|---|---|---|---|
| Fade (H3) yeniden test | intraday_cache'te ≥3 ay, hacim dahil yeni veri | Takvime bağlı, hızlandırılamaz | Cache otomatik büyüdükçe agent kontrol eder |
| XLC/XLK yeniden bakış | Fade genişlemesiyle birlikte gelir | Fade ile aynı | Agent, fade yeniden testiyle birlikte |
| Abstention bağımsız doğrulama | Kalibrasyon-sonrası yeni, hiç görülmemiş günler | Takvime bağlı | Agent, yeterli yeni gün birikince |
| Soru-1/Soru-3 | Dış veri sağlayıcı entegrasyonu (event-feed, gerçek spread/ADV) | Meriç'in altyapı kararına bağlı | Meriç |
