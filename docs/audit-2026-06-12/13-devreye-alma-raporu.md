# Devreye-Alma Raporu — Erken-Tier Canlıya Bağlandı + Edge Report Yapı Taşı

**Tarih:** 2026-06-12 · **Önceki:** `12-uygulama-raporu-erken-yakalama.md` (yapı taşları) · **Bu rapor:** o yapı taşlarının `evaluate.py`'ye env-gated bağlanması + ölçüm katmanı.

> **Uyarı:** Sistem-tasarımı uygulamasıdır, yatırım tavsiyesi değildir. Tier'lar kanıtlanmış edge değildir; gölge-modda Edge Report ile ölçülmeden hiçbiri pozisyon kararını etkilememeli.

---

## 1. NE YAPILDI

`12-...` raporundaki §4 "Nasıl devreye alınır (henüz kapalı)" adımı **uygulandı**: erken-yakalama merdiveni scanner'ın canlı değerlendirme akışına bağlandı — **env-gated, varsayılan KAPALI.** Ayrıca tier'ları dürüstçe ölçecek **Edge Report** yapı taşı eklendi. **28/28 birim testi yeşil, tüm dosyalar derleniyor.**

| Değişiklik | Dosya | Tür |
|---|---|---|
| Erken-tier canlıya bağlandı (env-gated) | `scanner/evaluate.py` (+30 satır) | M |
| `FINPILOT_ENABLE_EARLY_TIER` flag dokümante edildi | `.env.example` | M |
| Edge Report builder (`build_edge_report`, `format_edge_report_md`) | `scanner/edge_report.py` | yeni |
| Edge Report testleri (6) | `tests/test_edge_report.py` | yeni |

Önceki oturumdan gelen ve hâlâ geçerli: `scanner/features.py` (contraction + rvol-accel), `scanner/watch_tier.py` (merdiven + glue), `scanner/labeling.py` (triple-barrier), `tests/test_early_detection.py` (22 test).

---

## 2. evaluate.py'ye NE EKLENDİ (tam diff özeti)

Üç nokta, başka hiçbir şeye dokunulmadan (git diff ile doğrulandı):

1. **`import os`** — modül başına (gated kontrol için).
2. **Gated hesaplama bloğu** — `return` ifadesinin hemen öncesinde:
   ```python
   _early_tier = { "tier": "NONE", ... }          # güvenli varsayılan
   if os.environ.get("FINPILOT_ENABLE_EARLY_TIER", "0") == "1":
       try:
           from scanner.watch_tier import compute_early_tier
           _early_tier = compute_early_tier(
               df_1d, catalyst_factor=..., volume_multiple=..., entry_ok=...)
       except Exception:
           pass    # best-effort: hata taramayı asla kırmaz
   ```
3. **Return dict'e 7 additive alan** — `overnight_gap_factor`'ın hemen ardına: `tier`, `tier_score`, `tier_reasons`, `tier_size_fraction`, `contraction_factor`, `rvol_acceleration`, `range_expansion`.

**Davranış garantisi:** Flag `0` (varsayılan) iken `compute_early_tier` hiç çağrılmaz; tüm alanlar güvenli varsayılana (`NONE`/0.0) düşer. `entry_ok`, `composite_score`, sinyal üretimi ve pozisyon boyutu **bit-bazında değişmez.** Flag `1` iken yalnızca yeni alanlar dolar — mevcut hiçbir alan etkilenmez. `tier_size_fraction` **tavsiye**dir, hiçbir emir/boyut hesabına girmez.

---

## 3. NASIL TEST EDİLDİ

**28/28 birim testi geçti** (22 erken-yakalama + 6 Edge Report). `.venv` bu ortamda kırık + `pip` engelli olduğundan, testler sistem python'ında (pandas 2.3 / numpy 2.2), paketin kırık `__init__`'ini atlayan saf-modül koşucusuyla yürütüldü.

Edge Report test kapsamı: genel sayımlar (tp/sl/time oranları), tier'a göre gruplama (SETUP vs WATCH ayrı istatistik), beklenti işareti (hep kazanan → pozitif; hep kaybeden → negatif), bozuk kayıt atlanır (fatal değil), boş girdi, Markdown render.

**Derleme:** `scanner/{features,watch_tier,labeling,edge_report,evaluate}.py` + iki test dosyası — hepsi `py_compile`'dan temiz.

**Canlı import testi neden yapılamadı:** bu sandbox'ın kabuk-mount görünümü büyük dosyaları **okurken kesiyor** (`data_fetcher.py` 1201→1183, `evaluate.py` benzer). Bu yüzden `scanner` paketi sandbox'ta import edilemiyor; `evaluate_symbol`'ün canlı çağrısı test edilemedi. **Senin ortamında bu sorun yok** (kanonik dosyalar tam). Entegrasyon py_compile + zaten 28/28 test edilmiş `compute_early_tier` çağrısıyla doğrulandı.

**Önemli olay ve düzeltme:** İşlem sırasında kabuk-mount'un kesik-okuma davranışı yüzünden `evaluate.py` ve `data_fetcher.py` çalışma-ağacı kopyaları kısaldı. İkisi de **git object-store'dan tam sürümle geri yüklendi** (561 ve 1201 satır); sonrasında `evaluate.py` düzenlemesi git'in tam içeriği üzerinden yeniden uygulandı. Son `git status` yalnızca amaçlanan değişiklikleri gösteriyor; `data_fetcher.py` artık temiz (değişiklik yok).

---

## 4. NASIL AÇILIR (gölge-mod)

```bash
# .env içine (veya ortam değişkeni olarak)
FINPILOT_ENABLE_EARLY_TIER=1
```
Açıldığında her scanner sonucu artık `tier` (NONE/WATCH/SETUP/TRIGGER/CONFIRM) + skor + gerekçe + öncü feature'ları taşır. **Önerilen kullanım: gölge-mod** — yani tier'ları üret ve KAYDET, ama henüz hiçbir karar/boyut tier'a bağlanmasın. Birkaç hafta veri biriktikten sonra Edge Report ile ölç.

---

## 5. EDGE REPORT — TİER'LARI ÖLÇMEK

`scanner/edge_report.py`, kapanan sinyalleri triple-barrier ile etiketleyip tier'a göre dilimler:

```python
from scanner.edge_report import build_edge_report, format_edge_report_md
rep = build_edge_report(records, tp_pct=0.10, sl_pct=0.05, max_horizon=10, group_by="tier")
print(format_edge_report_md(rep, title="Haftalık Edge Report"))
```
Her `record`: `entry_price` + `forward_closes` (+ opsiyonel `forward_highs/lows`, `side`, `tier`). Çıktı: genel + tier başına hit-rate / stop-rate / time-rate / ortalama getiri / beklenti. Bu, "WATCH/SETUP gerçekten pozitif beklenti taşıyor mu?" sorusunu cevaplayan tablodur.

**Henüz bağlanmadı (kasıtlı):** `outcomes_horizon`/`signals_archive`'den kapanan sinyalleri çekip forward-OHLC ekleyen scheduler job'u ayrı bir adım — canlı DB + tam ortam gerektirir, bu oturumun saf-birim test kapsamı dışında. Yapı taşı hazır ve test edildi; bağlama tek bir job fonksiyonu.

---

## 6. SONRAKİ ADIMLAR (sıra)

1. **Gölge-mod aç:** `FINPILOT_ENABLE_EARLY_TIER=1`, sadece kaydet — birkaç hafta tier dağılımını ve sonuçlarını topla.
2. **Edge Report job'u:** scheduler'da haftalık — `outcomes_horizon`'dan kapanan sinyaller → `build_edge_report(group_by="tier")` → haftalık rapora + dashboard'a.
3. **Karar:** Edge Report bir tier'ın (örn. SETUP) pozitif maliyet-sonrası beklentisini gösterirse → o tier'ı UI'da öne çıkar + kademeli boyut önerisini yüzeye çıkar. Göstermezse → eşikleri ayarla veya tier'ı sessiz tut. **Kanıtlamadan canlı karara bağlama.**
4. **P1 (sonra):** DTW analog + meta-labeling + ayrı pre-event (mikro-kap) modu.

---

## 7. DEĞİŞEN DOSYALAR (git status)

```
 M .env.example                      # FINPILOT_ENABLE_EARLY_TIER=0 (dokümante)
 M scanner/evaluate.py               # erken-tier env-gated bağlandı (+30)
 M scanner/features.py               # contraction + rvol-accel (önceki oturum)
?? scanner/edge_report.py            # YENİ — Edge Report builder
?? scanner/labeling.py               # YENİ — triple-barrier (önceki oturum)
?? scanner/watch_tier.py             # YENİ — merdiven + glue (önceki oturum)
?? tests/test_early_detection.py     # YENİ — 22 test
?? tests/test_edge_report.py         # YENİ — 6 test
```
`data_fetcher.py` mount artefaktından geri yüklendi → temiz. Commit edilmedi (senin incelemen için bırakıldı).

**Tek cümle:** Erken-yakalama merdiveni artık scanner'a env-gated bağlı (varsayılan kapalı, canlı davranış değişmedi) ve onu dürüstçe ölçecek Edge Report yapı taşı hazır + test edildi; sıradaki iş gölge-modda açıp ölçmek, edge kanıtlanırsa karara bağlamak — kanıtlamadan değil.
