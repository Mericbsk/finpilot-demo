# Donanım Analizi — ASUS Ascent GX10 (NVIDIA GB10 / DGX Spark) FinPilot + FinSense için
Durum: DEĞERLENDİRME · 2026-08-03 · Eskalasyon: Level A (analiz; satın alma kararı senin — Level C)
Soru: Bu ürün, FinPilot + FinSense'i **yerelde canlı çalışan** bir sisteme çevirmeye yeter mi? Bileşen bileşen.

---

## 0. Tek paragraf hüküm

İki farklı soruyu ayırmak şart. **(A) Yerel bir AI FABRİKASI + özel trading beyni + FinSense içerik
üretimi için mi?** → **Fazlasıyla yeter, hatta mükemmel eşleşme.** 128GB birleşik bellek, bugünkü
qwen2.5:3b'nin çok ötesinde (30B–70B, hatta 200B fine-tune) modelleri yerelde koşturur; FinSense'in
CPU'da yaşadığı timeout'u bitirir. **(B) Halka açık, canlı web ürününün production sunucusu için mi?**
→ **Kısmen, ciddi çekincelerle.** Tek mini-PC (yedeksiz, ev interneti, 7/24, ARM'a göç, OS kurulumu);
küçük kullanıcı kitlesine kendi-barındırma olur ama bulut serving'in yerini tutmaz. **Ve en önemlisi:
bu kutu, senin bugünkü asıl darboğazlarını (edge kanıtlanmadı, traction ~0, lansman 2/10) ÇÖZMEZ** —
onlar donanım değil, kanıt/kullanıcı/odak problemi. Yani "harika alet, ama yanlış zamanda alınırsa
yine kapsam-genişlemesinin bir başka yüzü."

---

## 1. Ürün künyesi (Cyberport AT — kanıt)

| Alan | Değer |
|---|---|
| Ürün | ASUS Ascent GX10-GG0003BN (NVIDIA DGX Spark platformu) |
| **Fiyat** | **€4.099** (128GB/1TB). 2TB = +€900 (€4.999) · 4TB = +€2.300 (€6.399) |
| İşlemci | NVIDIA **GB10** Grace Blackwell — 20 ARM çekirdek (10× Cortex-X925 + 10× Cortex-A725) |
| GPU | Blackwell, 48 SM, 6.144 CUDA çekirdek, ~**1 PFLOP** seyrek FP4 |
| Bellek | **128 GB LPDDR5X birleşik** (CPU+GPU paylaşımlı), **273 GB/s**, 256-bit |
| Depolama | 1 TB NVMe (bu SKU) |
| **İşletim sistemi** | **YOK (DOS)** — DGX OS / Ubuntu ARM elle kurulacak |
| Ağ | 1× 10GbE, Wi-Fi 7, Bluetooth 5.4 |
| Bağlantı | 4× USB-C, 4× USB 3.2, 1× HDMI 2.1b |
| Güç / boyut | 240 W · 150×51×150 mm · 1.6 kg (mini-PC) |

Not: NVIDIA'nın kendi "DGX Spark Founders Edition" versiyonu **DGX OS (Ubuntu) kurulu** ve 4TB gelir;
bu ASUS SKU daha ucuz ama **OS'siz**. İki GX10 ConnectX-7 ile birbirine bağlanabilir (stacking).

---

## 2. Gerçek performans — kapasite vs hız (kritik nüans)

Pazarlama "1 PFLOP / 200B model" der; gerçek kullanımı belirleyen **273 GB/s bellek bant genişliği**:

| İş | Ölçülen (bağımsız testler) |
|---|---|
| Büyük model **yükleme kapasitesi** | 70B–120B rahat; **200B'e kadar fine-tune** (128GB sayesinde) |
| 8B model (tek akış) | ~20 tps decode; **batch 32'de ~368 tps** (eşzamanlılıkla ölçekleniyor) |
| 70B Q4 | ~35–45 tps |
| 200B | ~35–80 tps |
| Kıyas | Aynı modelde ayrık GPU (RTX Pro 6000) decode'da ~**4× daha hızlı** — fark = bant genişliği |

**Okuma:** DGX Spark'ın gücü **kapasite ve eşzamanlılık** (aynı anda çok istek/batch), tek bir isteği
en hızlı yanıtlamak değil. Bu, **batch içerik üretimi (FinSense)** ve **çok-ajan/çok-istek** için ideal;
tek kullanıcının anlık düşük-gecikme sohbeti için "yeterince iyi ama en hızlı değil."

---

## 3. Bileşen bileşen eşleştirme — FinPilot + FinSense

| Bileşen | Bugün | GB10'da | Fit | Not |
|---|---|---|---|---|
| **FinSense academy (içerik fabrikası)** | Ollama qwen2.5:3b + nomic-embed, CPU'da timeout | 30B–70B model + GPU embedding | ✅✅ **En güçlü fit** | Daha iyi model = daha az olgusal hata; timeout biter; RAG hızlanır |
| **FinPilot scanner** | CPU/IO; darboğaz = **yfinance ağ** | ARM 20 çekirdek yardım eder ama... | ⚠️ **Çözmez** | Darboğaz ağ/veri-kaynağı; donanım hızlandırmaz (bkz. scanner audit) |
| **FinPilot agents (23) / rationale / bull-bear** | LLM çağrıları (bulut/CPU/mock) | Yerel GPU'da hızlı | ✅ İyi fit | Ama CTO-DD: 23→5 ajan kes; donanım ajan şişkinliğini "meşrulaştırmasın" |
| **FinBERT / sentiment** | Uykuda (HF token yok) | Yerelde trivial koşar | ✅ Kolay | Ayrı FinBERT raporundaki doğrulama kapısı hâlâ geçerli |
| **DRL (45 dosya, PARK)** | Park | GB10 gerçek RL eğitimi yapar | ✅ (koşullu) | Güçlü fit AMA parked; açmak Level B/kapsam kararı |
| **Özel trading beyni (A sistemi)** | Kavram | 7/24 yerel, özel, GPU inference | ✅✅ **İdeal fit** | "Kendin için" gizli otonom beyin — tam bu kutunun amacı |
| **Web / API / distribution (serving)** | Render/Vercel bulut | ARM sunucu olur ama... | ⚠️ Çekinceli | Tek kutu, ev interneti, 7/24, TLS/DDoS/yedek — bkz. §5 |

---

## 4. "Yerelde canlı sistem" — iki net cevap

**Cevap 1 — Yerel AI fabrikası + özel beyin olarak: EVET, yeter (mükemmel).**
Projenin kendi mimarisi zaten bunu söylüyor (CTO-DD §5/§7): **"Yerel LLM = fabrika, bulut = serving."**
GB10, FinSense içerik üretimini, FinPilot LLM zenginleştirmesini, FinBERT'i ve (istenirse) DRL/özel
trading beynini yerelde, gizli ve maliyetsiz (bulut faturası yok) koşturur. Bugünkü qwen 3B'nin çok
ötesi kalite. Bu senaryoda kutu **fazlasıyla yeterli**.

**Cevap 2 — Halka açık canlı ürünün production sunucusu olarak: KISMEN, çekinceyle.**
Küçük kitleye (onlarca–düşük yüzlerce kullanıcı) kendi-barındırma teknik olarak mümkün (batching ile
throughput iyi). Ama tek mini-PC = **bus factor 1, yedeksiz, ev interneti/elektrik, 7/24 uptime,
TLS/DDoS/güvenlik, ARM64 göçü, OS kurulumu**. CTO-DD kamu ölçeği için açıkça **bulut serving** öneriyor
(~1000 eşzamanlıda kırılır). Yani halka açık yüz için **bulut kalmalı; GB10 arkada fabrika/beyin olmalı.**
Önerilen mimari: **hibrit** — GB10 = yerel fabrika + özel A-sistemi; bulut (Render/Vercel) = halka açık serving.

---

## 5. Riskler / dikkat edilecekler (dürüst)

1. **OS yok (DOS).** DGX OS / Ubuntu-ARM elle kurulacak; Founders Edition OS'li gelir (kıyasla).
2. **ARM64 göçü.** Tüm yığın (FastAPI, Next.js, Postgres/SQLite, Ollama, PyTorch) ARM64'te çalışmalı.
   Ollama/PyTorch'un CUDA-ARM yapıları var (kutunun amacı bu) ama kurulum/uyum emeği gerçek.
3. **273 GB/s tavanı.** Tek-akış decode hızı ayrık GPU'nun ~1/4'ü. Anlık düşük-gecikme UX için sınır.
4. **7/24 + 240W.** Sürekli açık, ~240W; ev ortamında ısı/gürültü/elektrik + kesinti riski.
5. **Tek düğüm.** Yedek yok; disk/güç arızası = tüm sistem durur. Yedekleme/DR planı şart.
6. **Ev barındırma = güvenlik/hukuk.** Kullanıcı verisini evden servis etmek: GDPR/veri-yeri,
   saldırı yüzeyi (para+LLM = yüksek değer, CTO-DD §9). Halka açık serving için önerilmez.
7. **Garanti/iade.** Cyberport 30 gün iade; ama açılıp kurulan bir "supercomputer"da iade pratiği zor.

---

## 6. Alternatifler (kısa)

- **NVIDIA DGX Spark Founders (128GB/4TB, DGX OS kurulu):** aynı çip, OS+4TB dahil — kurulum derdi az.
- **HP Z2 Mini G1a — Ryzen AI MAX+ 395, 128GB birleşik (x86):** aynı sayfada listeli; **x86 = ARM göçü YOK**,
  128GB unified LPDDR5X (~256 GB/s), genelde daha ucuz. Tom's Hardware: DGX Spark onu geçiyor ama fark
  iş yüküne bağlı. **x86 kalmak istiyorsan güçlü aday.**
- **Bulut GPU kiralama (ihtiyacı önce doğrula):** €4k'lık kalıcı yatırımdan önce, bir aylık bulut GPU
  ile "daha büyük model FinSense kalitesini gerçekten artırıyor mu?" testi çok daha ucuz.

---

## 7. Zamanlama — projenin gerçek darboğazlarıyla dürüst yüzleşme

Bu kutu **hiçbir bugünkü darboğazı çözmüyor:** (1) sinyal edge'i kanıtlanmadı (yol haritası §0),
(2) traction ~0, (3) lansman 2/10, (4) scanner yavaşlığı = ağ/veri-kaynağı (donanım değil). Az önce
birlikte koyduğumuz proje-yönetimi disiplini tam da "yeni sistem/yatırım açmadan önce hangi problemi
çözüyor?" diye soruyor. Dürüst cevap: **€4k'lık donanım, ölçüm/kullanıcı/odak problemini çözmez.**

**Ne zaman mantıklı olur:**
- FinSense içerik kalitesi (olgusal doğruluk) ölçülen bir öncelik hâline gelirse **ve** daha büyük yerel
  model bunu kanıtlanmış biçimde artırıyorsa (önce bulut GPU ile test et).
- Özel trading beyni (A sistemi) ciddi bir hedefe dönüşürse — 7/24 gizli yerel inference için ideal.
- Lansman + edge kanıtı geçildikten sonra, "yerel-fabrika" vizyonuna kalıcı yatırım olarak.

**Şimdi değilse:** parayı/enerjiyi beklet; bulut serving + lansman + edge kanıtı önce gelir. Kutu kaçmaz.

---

## 8. Karar çerçevesi (senin için, tek bakışta)

| Amacın şu ise… | GB10 uygun mu? | Öneri |
|---|---|---|
| Halka açık web ürününü yerelde barındırmak | ⚠️ Hayır (tek kutu, ev, ARM) | Bulut serving kalsın |
| FinSense içerik fabrikasını güçlendirmek | ✅ Evet | Ama önce bulut GPU ile ihtiyacı doğrula |
| Özel/gizli otonom trading beyni (kendin için) | ✅✅ İdeal | Edge kanıtından sonra |
| DRL/araştırmayı canlandırmak | ✅ Evet | Ama DRL parked — kapsam kararı |
| "Bugünkü darboğazı çözmek" | ❌ Hayır | Darboğaz donanım değil |

**Tek cümle:** Teknik olarak muhteşem ve projenin "yerel-fabrika" vizyonuna birebir; ama bugünkü
problemlerin (edge, traction, lansman) hiçbirini çözmediği için **şimdi almak erken** — ihtiyacı önce
ucuz bulut GPU ile doğrula, lansman/edge sonrası kalıcı fabrika/özel-beyin yatırımı olarak düşün.

---

Sources: [Cyberport ürün sayfası](https://www.cyberport.at/pc-und-zubehoer/server-workstations/workstations/asus/pdp/1k07-008/asus-ascent-gx10-gg0003bn-supercomputer-blackwell-superchip-nvidia-gb10-128gb-1tb-dos-dgx-spark.html) · [LMSYS DGX Spark in-depth](https://www.lmsys.org/blog/2025-10-13-nvidia-dgx-spark/) · [Tom's Hardware review](https://www.tomshardware.com/pc-components/gpus/nvidia-dgx-spark-review) · [ServeTheHome review](https://www.servethehome.com/nvidia-dgx-spark-review-the-gb10-machine-is-so-freaking-cool/2/) · [Dendro concurrency benchmark](https://dendro-logic.com/engineering/nvidia-dgx-spark-concurrency-benchmark/)
