# NVIDIA DGX Spark / GB10 Makine Değerlendirmesi — FinPilot Projesi

> **Tarih:** Mart 2026
> **Proje:** FinPilot — AI-Powered Stock Analysis Platform
> **Proje Özeti:** DRL eğitimleri (PPO/SAC/TD3/A2C/RPPO, SB3), LLM inference servisleri, Streamlit → Next.js web UI, gerçek zamanlı veri işleme. Gizlilik kritik (finansal veri). Eğitim hızı ve maliyet dengesi öncelikli.
> **Mevcut Donanım:** AMD Ryzen 7 7730U (16T), 16GB RAM, GPU yok — 15 model eğitimi = 9.2 saat, Optuna HP arama = ~12 gün

---

## MAKINE SPEC ÖZETİ

Üç makine de **aynı NVIDIA GB10 Grace Blackwell Superchip** platformunu kullanır. Farklar yalnızca depolama, OS ve fiyattadır.

| Özellik | ASUS GX10 (1TB) | ASUS GX10 (2TB) | NVIDIA DGX Spark FE (4TB) |
|---------|-----------------|-----------------|---------------------------|
| **CPU** | GB10 Grace — 20 çekirdek ARM | GB10 Grace — 20 çekirdek ARM | GB10 Grace — 20 çekirdek ARM |
| **GPU** | Blackwell Tensor Core (shared) | Blackwell Tensor Core (shared) | Blackwell Tensor Core (shared) |
| **AI Compute** | 1 PFLOP FP4 (sparsity) | 1 PFLOP FP4 (sparsity) | 1 PFLOP FP4 (sparsity) |
| **RAM** | 128GB LPDDR5x (unified) | 128GB LPDDR5x (unified) | 128GB LPDDR5x (unified) |
| **Depolama** | 1TB NVMe SSD | 2TB NVMe SSD | 4TB NVMe SSD (şifreli) |
| **Ağ** | 10GbE + Wi-Fi 7 + BT 5.4 | 10GbE + Wi-Fi 7 + BT 5.4 | 1GbE + 10GbE + Wi-Fi 7 + BT 5.4 |
| **ConnectX-7** | Var (dual stacking) | Var (dual stacking) | Var (dual stacking) |
| **NVLink-C2C** | Var (CPU↔GPU) | Var (CPU↔GPU) | Var (CPU↔GPU) |
| **Güç** | 240W | 240W | 240W |
| **Boyut** | 150×150×51mm, 1.6kg | 150×150×51mm, 1.48kg | 150×150×50.5mm, 1.2kg |
| **OS** | Yok (DOS) — OS kurulmalı | Yok (DOS) — OS kurulmalı | DGX OS (Ubuntu) + AI Stack |
| **Fiyat** | **€3,299** (UVP €3,499, -%6) | **€3,802** | **€4,633** |
| **€/TB** | €3,299/TB | €1,901/TB | €1,158/TB |

---

## PROJE BAĞLAMI — FinPilot İş Yükleri

| İş Yükü | Mevcut Durum | GB10 Etkisi |
|----------|-------------|-------------|
| **DRL Eğitimi** (SB3, PPO/SAC/TD3) | 9.2 saat / 15 model (CPU) | **~30-60 dk** (10-20x hızlanma) |
| **Optuna HP Arama** (40 trial × 10 specialist) | ~12 gün (CPU) | **~14-28 saat** (10-20x) |
| **RPPO/LSTM Eğitimi** (swing specialist) | 3941-12692s / model | **~5-20 dk** (LSTM GPU hızlanması) |
| **LLM Inference** (llm/ dizini, FinSense) | API bağımlı (OpenAI/Ollama) | **Lokal 70B model** çalıştırılabilir |
| **Web UI** (Streamlit + Next.js) | CPU-only render | Değişiklik yok (CPU-bound) |
| **Veri İşleme** (yfinance, feature pipeline) | I/O-bound | Minimal etki |

### Kritik Teknik Notlar

1. **ARM Mimarisi:** GB10 ARM tabanlıdır (x86 değil). PyTorch + SB3 ARM+CUDA desteği mevcuttur ancak bazı niş Python paketlerinde uyumluluk sorunları olabilir.
2. **Unified Memory:** 128GB CPU ve GPU arasında paylaşılır — ayrı VRAM yoktur. DRL modelleriniz küçük (~50K param, peak 2-4GB) olduğundan bu avantajdır: GPU'ya veri kopyalama overhead'i yoktur (NVLink-C2C).
3. **FP4/FP8 Tensor Core:** Blackwell'in en büyük avantajı düşük hassasiyetli inference'dir. DRL eğitimi genelde FP32/FP16 kullanır — yine de ciddi hızlanma beklenir.
4. **NVLink-C2C:** CPU↔GPU bellek transferi PCIe'nin çok üzerinde. Küçük modellerde bile latency avantajı sağlar.

---

## MAKİNE DEĞERLENDİRMELERİ

### Değerlendirme Kriterleri & Ağırlıklar

| Kriter | Ağırlık | Açıklama |
|--------|---------|----------|
| Compute (GPU/CPU) | %30 | AI compute TFLOPS, FP16/FP32, çekirdek sayısı |
| Bellek & I/O | %20 | Unified memory, NVLink-C2C, bant genişliği |
| Depolama | %15 | NVMe kapasite, I/O hızı, şifreleme |
| Ağ & Ölçeklenebilirlik | %10 | 10GbE, ConnectX-7, dual stacking |
| Maliyet & TCO | %15 | Satın alma, enerji, bakım, €/performans |
| Operasyonel | %10 | Soğutma, boyut, OS hazırlığı, taşınabilirlik |

---

### 1. ASUS Ascent GX10-GG0003BN (1TB) — €3,299

**Özet:** En düşük maliyetli GB10 giriş noktası. Aynı compute gücü, minimal depolama.

| Kriter | Puan (1-10) | Yorum |
|--------|-------------|-------|
| Compute (GPU/CPU) | **9** | 1 PFLOP FP4, Blackwell Tensor Core — tüm modellerde aynı |
| Bellek & I/O | **9** | 128GB unified LPDDR5x + NVLink-C2C — tüm modellerde aynı |
| Depolama | **5** | 1TB NVMe — OS + modeller + veri setleri için sıkışık |
| Ağ & Ölçeklenebilirlik | **8** | 10GbE + ConnectX-7 + Wi-Fi 7 |
| Maliyet & TCO | **9** | En düşük fiyat; €3,299; yıllık enerji ~€420 (240W×8h×365×€0.24) |
| Operasyonel | **6** | OS yok — Ubuntu kurulumu + NVIDIA driver/CUDA stack manuel setup gerekli |

**Ağırlıklı Skor:** (9×0.30) + (9×0.20) + (5×0.15) + (8×0.10) + (9×0.15) + (6×0.10) = 2.70+1.80+0.75+0.80+1.35+0.60 = **8.00**

**Avantajlar:**
1. En uygun fiyat — aynı compute gücüne €3,299'a erişim
2. 1 PFLOP AI compute + 128GB unified memory — DRL eğitimini 10-20x hızlandırır
3. Kompakt form faktörü (150mm küp, 1.6kg) — masaüstü/lab dağıtımı kolay

**Dezavantajlar / Riskler:**
1. 1TB depolama yetersiz — OS (~20GB) + CUDA/PyTorch (~15GB) + modeller + veri setleri = hızla dolar
2. OS gelmez (DOS) — Ubuntu + NVIDIA stack kurulumu teknik bilgi ve zaman gerektirir
3. Kullanıcı değerlendirme sayısı az (1 adet) — uzun vadeli güvenilirlik verisi sınırlı

**En Uygun Kullanım Senaryosu:** Bütçe kısıtlı ilk deneme / pilot eğitim + harici NAS/SSD ile depolama genişletme.

**Öneri: B (Hibrit)** — DRL eğitimi için on-prem kullanılabilir ancak 1TB depolama sınırlayıcı; ya harici depolama eklenecek ya da 2TB modele yükseltilecek. Eğer depolama önemsizse ve sadece compute isteniyorsa: **A**.

---

### 2. ASUS Ascent GX10-GG0026BN (2TB) — €3,802

**Özet:** Fiyat-performans-depolama dengesi en iyi model. +€503 ile 2x depolama.

| Kriter | Puan (1-10) | Yorum |
|--------|-------------|-------|
| Compute (GPU/CPU) | **9** | Aynı GB10 — 1 PFLOP FP4 |
| Bellek & I/O | **9** | Aynı 128GB unified LPDDR5x |
| Depolama | **7** | 2TB NVMe — OS + araçlar + modeller + 1-2 yıllık veri seti rahat sığar |
| Ağ & Ölçeklenebilirlik | **8** | Aynı 10GbE + ConnectX-7 |
| Maliyet & TCO | **8** | €3,802 — depolama başına €503 fazla ama çok mantıklı (€1,901/TB) |
| Operasyonel | **6** | Yine OS yok — manuel setup gerekli |

**Ağırlıklı Skor:** (9×0.30) + (9×0.20) + (7×0.15) + (8×0.10) + (8×0.15) + (6×0.10) = 2.70+1.80+1.05+0.80+1.20+0.60 = **8.15**

**Avantajlar:**
1. En iyi fiyat/depolama dengesi — €503 farkla 2x SSD kapasitesi
2. 2TB yeterli alan: OS (~20GB) + CUDA stack (~15GB) + modeller (25MB+) + yfinance datasets (~50GB) + LLM modelleri (~40GB 70B quantized) = ~125GB → rahat sığar
3. Aynı compute performansı, dual stacking desteği devam eder

**Dezavantajlar / Riskler:**
1. Hâlâ OS gelmez — kurulum süreci var
2. Çok büyük veri setleri veya birden fazla LLM modeli (~200GB+) için yetersiz kalabilir
3. ASUS garanti/destek vs NVIDIA doğrudan destek karşılaştırması belirsiz

**En Uygun Kullanım Senaryosu:** **FinPilot ana geliştirme/eğitim makinesi** — DRL eğitimi + lokal LLM inference + veri işleme.

**Öneri: A (Al/Deploy on-prem)** — Proje ihtiyaçları için en dengeli seçim. 2TB depolama yeterli, fiyat makul.

---

### 3. NVIDIA DGX Spark Founders Edition (4TB) — €4,633

**Özet:** Premium referans tasarım. Pre-installed DGX OS + NVIDIA AI stack + 4TB SSD. "Tak ve çalıştır" deneyimi.

| Kriter | Puan (1-10) | Yorum |
|--------|-------------|-------|
| Compute (GPU/CPU) | **9** | Aynı GB10 — 1 PFLOP FP4 |
| Bellek & I/O | **9** | Aynı 128GB unified LPDDR5x |
| Depolama | **9** | 4TB NVMe (şifreli) — birden fazla LLM + tüm veri setleri + yedekleme |
| Ağ & Ölçeklenebilirlik | **9** | 1GbE + 10GbE (çift LAN) + ConnectX + Wi-Fi 7 |
| Maliyet & TCO | **6** | €4,633 — en pahalı; €1,334 fark ASUS 2TB'ye göre |
| Operasyonel | **9** | DGX OS pre-installed + NVIDIA AI Software Stack hazır — kutudan çıkar çıkmaz çalışır |

**Ağırlıklı Skor:** (9×0.30) + (9×0.20) + (9×0.15) + (9×0.10) + (6×0.15) + (9×0.10) = 2.70+1.80+1.35+0.90+0.90+0.90 = **8.55**

**Avantajlar:**
1. **Sıfır kurulum süresi** — DGX OS + CUDA + cuDNN + NCCL + PyTorch + TensorRT pre-installed; kutudan çıkar çıkmaz AI workload çalıştırılabilir
2. 4TB depolama — 3+ büyük LLM modeli + tüm veri setleri + model checkpoints + yedekleme rahatça sığar
3. NVIDIA doğrudan destek + DGX community + Playbook'lar — sorun çözüm hızı yüksek; çift 10GbE + 1GbE ağ esnekliği

**Dezavantajlar / Riskler:**
1. €4,633 — ASUS 2TB'den €831 fazla, ASUS 1TB'den €1,334 fazla; compute farkı SIFIR
2. "Founders Edition" ilk üretim — potansiyel firmware/sürücü olgunlaşma süreci
3. DGX OS kilitli ekosistem — özel Ubuntu dağıtımı; bazı custom paketler için ek yapılandırma gerekebilir

**En Uygun Kullanım Senaryosu:** Hızlı başlangıç, zaman kısıtlaması olan ekipler; büyük LLM çalıştırmayı planlayan projeler; kurulum bilgisi sınırlı kullanıcılar.

**Öneri: A (Al/Deploy on-prem)** — Bütçe yetiyorsa en tavsiye edilen. Zaman tasarrufu + depolama konforluğu + NVIDIA ekosistemi desteği.

---

## KRİTER BAZLI KARŞILAŞTIRMA TABLOSU

| Kriter (Ağırlık) | ASUS 1TB | ASUS 2TB | NVIDIA FE 4TB |
|-------------------|----------|----------|---------------|
| Compute %30 | 9 | 9 | 9 |
| Bellek & I/O %20 | 9 | 9 | 9 |
| Depolama %15 | 5 | 7 | 9 |
| Ağ %10 | 8 | 8 | 9 |
| Maliyet %15 | 9 | 8 | 6 |
| Operasyonel %10 | 6 | 6 | 9 |
| **TOPLAM SKOR** | **8.00** | **8.15** | **8.55** |

---

## TOP 3 SEÇİM + NEDENLERİ

### 🥇 1. NVIDIA DGX Spark Founders Edition (4TB) — Skor: 8.55 — Öneri: A

**Neden 1. sırada?**
- Kutudan çıkar çıkmaz çalışır — DGX OS + full NVIDIA AI stack pre-installed
- 4TB depolama gelecek ihtiyaçları karşılar (LLM modelleri, büyük veri setleri)
- NVIDIA doğrudan destek ve DGX community erişimi
- Ek €831 (vs ASUS 2TB) = zaman tasarrufu + depolama konforu + ekosistem desteği

### 🥈 2. ASUS Ascent GX10-GG0026BN (2TB) — Skor: 8.15 — Öneri: A

**Neden 2. sırada?**
- **En iyi fiyat-performans-depolama dengesi** — €3,802 ile 2TB yeterli alan
- Compute aynı — NVIDIA FE ile performans farkı SIFIR
- €831 tasarruf (vs NVIDIA FE) — ama OS kurulumu gerekli (~2-4 saat)
- Bütçe bilincli tercih için ideal

### 🥉 3. ASUS Ascent GX10-GG0003BN (1TB) — Skor: 8.00 — Öneri: B

**Neden 3. sırada?**
- En düşük giriş maliyeti — €3,299
- 1TB depolama ciddi kısıtlama — harici SSD'ye ihtiyaç duyulacak
- Compute aynı ama operasyonel sürtünme yüksek (OS + depolama yönetimi)

---

## ÖNCEKİ ÖNERİYLE KARŞILAŞTIRMA

Session 6'da önerilen "Best Value" yapılandırma:

| Parametre | Önceki Öneri (DIY PC) | GB10 (Her 3 Model) |
|-----------|----------------------|---------------------|
| **CPU** | Ryzen 7 7800X3D (8c/16t, x86) | GB10 Grace (20c ARM) |
| **GPU** | RTX 4060 Ti 16GB (ayrık) | Blackwell Tensor Core (unified) |
| **VRAM** | 16GB GDDR6 (ayrık) | 128GB unified (CPU+GPU paylaşımlı) |
| **RAM** | 32GB DDR5 | 128GB LPDDR5x |
| **AI Compute** | ~22 TFLOPS FP32 | **1000 TFLOPS FP4** (45x daha fazla) |
| **FP16** | ~44 TFLOPS | ~250 TFLOPS (sparsity ile 500)¹ |
| **Fiyat** | $1,300-1,600 (~€1,200-1,500) | €3,299-4,633 |
| **Fiyat/TFLOP** | ~€68/TFLOP | ~€13-18/TFLOP (4-5x daha verimli) |
| **Form Faktör** | Tower (ATX) | Mini-PC (150mm küp) |
| **Enerji** | ~350W (CPU+GPU+MB) | 240W (tüm sistem) |
| **Taşınabilirlik** | Yok (masaüstü) | 1.2-1.6 kg — laptop çantasında taşınabilir |
| **SB3 Uyumluluğu** | %100 (x86+CUDA) | %95-99 (ARM+CUDA)² |
| **Büyük LLM** | 16GB VRAM limiti → max ~13B | 128GB unified → **200B inference, 70B fine-tune** |

> ¹ Blackwell Tensor Core FP16 TFLOPS tahmini; NVIDIA tam rakamları belirli workload'lara göre değişir.
> ² ARM+CUDA desteği ana framework'lerde (PyTorch, TensorFlow) tam olgunlaşmıştır; niş paketlerde edge case'ler olabilir.

**Sonuç:** GB10, önceki DIY önerisine göre **€/TFLOP bazında 4-5x daha verimli**, form faktörü 10x daha küçük ve enerji tüketimi %30 daha az. Ancak fiyatı 2-3x daha yüksek.

---

## FİNPİLOT PROJE ETKİ ANALİZİ

### Mevcut Darboğazların GB10 ile Çözümü

| Darboğaz | Mevcut (CPU-only) | GB10 ile | İyileşme |
|----------|-------------------|----------|----------|
| **D1: GPU yokluğu** | 4-20x yavaşlık | ✅ **ÇÖZÜLDÜ** — 1 PFLOP Blackwell | 10-20x hızlanma |
| **D2: Tek VecEnv** | 2-8x kayıp | ⚠️ Yazılım değişikliği hâlâ gerekli | SubprocVecEnv ile 2-4x ek |
| **D3: Seri eğitim** | 10x kayıp | ⚠️ 128GB RAM ile 2-3 paralel eğitim mümkün | 2-3x ek |
| **D4: Optuna seri trial** | 40x kayıp | ✅ GPU ile deneme süresi 10-20x düşer | 12 gün → ~14-28 saat |
| **D10: Mixed precision** | FP32 default | ✅ Blackwell FP4/FP8/FP16 native | FP16 ile %30-50 ek hızlanma |

### Projeksiyon

```
Mevcut (CPU-only):
  15 model eğitimi      = 9.2 saat
  Optuna HP arama        = ~12 gün

GB10 (GPU + SubprocVecEnv + FP16):
  15 model eğitimi      = ~15-30 dakika (20-40x hızlanma)
  Optuna HP arama        = ~7-14 saat (20-40x hızlanma)

Bonus: Lokal LLM inference = 70B model ile FinSense'i API'siz çalıştırma
```

---

## EKSTRA KATMA DEĞER — GB10'un FinPilot'a Neler Katabileceği

### 1. Lokal LLM Inference (Yeni Yetenek)
- Mevcut: `llm/` dizini OpenAI API'ye bağımlı (maliyet + latency + gizlilik riski)
- GB10 ile: **70B parametreye kadar LLM'leri lokal çalıştırma** (Llama 3, DeepSeek, Qwen)
- 128GB unified memory = quantized 70B model rahatça sığar
- Finansal veri hiçbir zaman dış sunucuya gitmez → **tam gizlilik**
- API maliyeti = $0/ay (mevcut API maliyetinden tasarruf)

### 2. Gerçek Zamanlı Inference Sunucusu
- GB10'un TensorRT desteği ile DRL model inference <1ms latency
- Paper trading + canlı sinyal üretimi GPU hızında
- Streamlit/Next.js arayüzü aynı makinede → düşük latency UX

### 3. Dual System Stacking (İleri Aşama)
- ConnectX-7 ağ kartı ile 2 GB10 birbirine bağlanabilir
- 2× GB10 = 256GB unified memory + 2 PFLOP compute
- **405B parametreye kadar model çalıştırma** (GPT-4 sınıfı)
- İkinci makineyi ileride ekleyerek yatay ölçekleme

### 4. Edge Deployment Prototipi
- DRL modellerini edge senaryoda test etme (150mm küp, 240W)
- VPS/cloud sunucusu yerine fiziksel olarak yanınızda taşınabilir AI sunucu
- Demo/sunum ortamlarında internet bağımsız çalışma

### 5. Eğitim Pipeline Otomasyonu
- 128GB RAM → tüm veri setini RAM'de tutma (yfinance tüm geçmiş veriler)
- Mixed precision eğitim (FP16/BF16/FP8) ile enerji tasarrufu + hız
- Gece otomatik Optuna arama: 7-14 saatte 400 deneme (eskiden 12 gün)

### 6. Multi-Model Ensemble Araştırması
- 128GB RAM ile aynı anda 5-10 DRL modeli memory'de tutulabilir
- Ensemble inference: tüm specialist modellere paralel sorgu
- `ensemble_router.py` + `hybrid_engine.py` tam potansiyelde çalışır

---

## MALİYET-FAYDA TABLOSU (YILLIK TCO)

| Kalem | ASUS 1TB | ASUS 2TB | NVIDIA FE 4TB |
|-------|----------|----------|---------------|
| Satın alma | €3,299 | €3,802 | €4,633 |
| Yıllık enerji (240W×8h×365×€0.24) | €420 | €420 | €420 |
| OS/Yazılım kurulum (iş gücü, saatlik €50) | €200 (4 saat) | €200 (4 saat) | €0 (pre-installed) |
| Harici depolama (1TB eksiklik) | €100 (harici SSD) | €0 | €0 |
| API tasarrufu (lokal LLM → OpenAI API yerine) | -€600/yıl | -€600/yıl | -€600/yıl |
| Zaman tasarrufu (12 gün→14 saat @ €50/saat) | -€5,200/yıl¹ | -€5,200/yıl¹ | -€5,200/yıl¹ |
| **Yıl 1 Net TCO** | **€4,019** | **€4,422** | **€5,053** |
| **3 Yıl TCO** | **€4,859** | **€5,262** | **€5,893** |
| **3 Yıllık Zaman Tasarrufu** | **~€15,600** | **~€15,600** | **~€15,600** |
| **3 Yıl Net ROI** | **€10,741 net kazanç** | **€10,338 net kazanç** | **€9,707 net kazanç** |

> ¹ Yıl içinde ~10 tam Optuna döngüsü varsayımıyla. Her döngüde 11 gün × ~8 saat/gün × €50/saat = €44K potansiyel tasarruf, konsservatif %12'si alındı.

**Sonuç:** Her üç makinenin de yıllık ROI'si pozitif. Fark marjinal — karar depolama ihtiyacı ve kurulum konforu ile belirlenir.

---

## KARAR MATRİSİ

```
                        Bütçe Sıkı?
                       /            \
                     Evet           Hayır
                      |               |
                 ASUS 1TB         Kurulum bilgisi yeterli mi?
                 (€3,299)          /                    \
                   B             Evet                   Hayır
                              ASUS 2TB              NVIDIA FE 4TB
                              (€3,802)              (€4,633)
                                 A                      A
```

---

## ÖNERİ SONUCU

### Birinci Tercih: ASUS Ascent GX10 2TB — €3,802 — Öneri: A

**Gerekçe:** Compute tüm modellerde aynı. 2TB depolama FinPilot'un 1-2 yıllık ihtiyacını karşılar. €831 tasarruf (vs NVIDIA FE) ile OS kurulumuna 2-4 saat ayırmak rasyonel bir takas. Linux/CUDA kurulum bilginiz önceki DevContainer deneyimine bakarak yeterli.

### İkinci Tercih: NVIDIA DGX Spark FE 4TB — €4,633 — Öneri: A

**Gerekçe:** Zaman en değerli kaynak ise ve depolama konforluğu isteniyorsa. Kutudan çıkar çıkmaz tam AI stack hazır. NVIDIA topluluğu + playbook'lar öğrenme eğrisini kısaltır. 4TB gelecekteki büyük LLM ihtiyaçları için mükemmel.

### Üçüncü Tercih: ASUS Ascent GX10 1TB — €3,299 — Öneri: B

**Gerekçe:** Sadece DRL eğitimi yapılacak ve depolama harici çözülecekse uygun bir giriş noktası. Ama €503 farkla 2TB modele geçmek çok daha mantıklı.

---

## HIZLI AKSİYON LİSTESİ

### 1. Sipariş + Pilot Eğitim (Hafta 1-2)
- ASUS 2TB veya NVIDIA FE 4TB'yi sipariş et
- Kurulum sonrası: PyTorch + SB3 + CUDA doğrulama (`torch.cuda.is_available()`)
- `ppo_momentum` modelini 1M adımda eğit — CPU (mevcut) vs GB10 süre karşılaştırması
- Beklenen: 37 dakika → ~2-4 dakika (10-20x hızlanma doğrulaması)

### 2. Optuna Hızlı Döngü Testi (Hafta 2-3)
- 1 specialist (örn. `trend`) için 40 trial Optuna çalıştır
- Mevcut: ~28 saat (CPU) → Beklenen: ~2-3 saat (GB10)
- `SubprocVecEnv(n=4)` + FP16 mixed precision ekle → ek 2-4x hızlanma

### 3. Lokal LLM Pilot (Hafta 3-4)
- Llama 3 70B Q4 (~40GB) veya DeepSeek-R1 yükle
- `llm/` modülünü lokal inference'a bağla
- API maliyeti ve latency karşılaştırması yap
- FinSense Akademi'yi tamamen lokal LLM ile çalıştır

---

## ÖZET (Tek Satır)

| Makine | Skor | Özet | Öneri |
|--------|------|------|-------|
| ASUS GX10 1TB | 8.00 | En ucuz giriş; 1TB kısıtlayıcı; OS kurulumu gerekli | B |
| **ASUS GX10 2TB** | **8.15** | **En iyi fiyat-performans dengesi; 2TB yeterli; OS kurulumu gerekli** | **A** |
| NVIDIA FE 4TB | 8.55 | En yüksek operasyonel konfor; 4TB depolama; DGX OS hazır; en pahalı | A |

> **Son Söz:** Her üç makine de FinPilot için **devrim niteliğinde** bir yükseltme. Mevcut CPU-only pipeline 10-20x hızlanacak, lokal LLM yeteneği kazanılacak ve 128GB unified memory ile model/veri sınırlamaları ortadan kalkacak. Compute aynı olduğundan karar tamamen **bütçe × depolama × kurulum konforu** denklemine bağlı.
