# FinPilot — Belge Senkronizasyon Raporu

**Tarih:** 2026-06-11
**Amaç:** Kod gerçeği ile belgeler arasındaki tutarsızlıkları (drift) tespit etmek ve güncellenmesi gereken belgeleri listelemek.

> **Genel durum:** Mimari drift, April 2026 audit'ine göre **iyileşmiş**. README ve docker-compose artık Next.js + FastAPI'yi birincil, Streamlit'i "secondary/legacy" olarak doğru tanımlıyor. Kalan tutarsızlıklar daha çok **performans iddiaları** ve **yeni eklenen modüller** etrafında.

---

## 1. Belge ↔ Kod Uyum Tablosu

| Belge | İddia | Kod gerçeği | Uyum |
|-------|-------|-------------|------|
| README.md | "Next.js (:3001) + FastAPI (:8000)" birincil | docker-compose doğrular | ✅ |
| README.md | Streamlit "legacy secondary" | root Dockerfile da öyle etiketli | ✅ |
| README.md | "DRL Integration - adaptive strategies" | DRL Şubat'tan beri donmuş, Sharpe ~0.05 | ❌ Yanıltıcı |
| README.md | CI/codecov badge `yourusername/finpilot` | Repo `Mericbsk/finpilot-demo` | ❌ Placeholder |
| README.md | "Signal Generation - automated entry/exit" | profitcore: NO EDGE | ⚠️ Edge yok |
| FULL_AUDIT_REPORT (05-23) | `score_engine` üretimde çalışmıyor | Doğru | ✅ Geçerli |
| FINANZPLAN | %8 conversion, €38 ARPU | Canlı veri yok (varsayım) | ⚠️ Belirt |
| HIBE_FON | "19 trained DRL models" | Çoğu donmuş/ölü (3/5 dead) | ⚠️ Niteliklendirin |
| docs (genel) | Symbol universe / preset yok | Yeni `symbol_lists`, 9 preset | ❌ Eksik |
| docs (genel) | Alpaca entegrasyonu yok | `drl/data_sources/alpaca_provider.py` var | ❌ Eksik |
| docs (genel) | Academy 6-ajan sistemi yok | `academy/` aktif | ❌ Eksik |

---

## 2. Güncellenmesi Gereken Belgeler

### 🔴 P0 — Yanıltıcı performans iddiaları
1. **README.md** — "DRL Integration - adaptive strategies" ifadesini "DRL (deneysel, araştırma aşamasında)" olarak düzelt. "Signal Generation" satırına "edge kalibrasyon aşamasında" notu ekle.
2. **Tüm funding/pazarlama** — In-sample (Sharpe 8, S-tier) rakamları kaldır; sadece out-of-sample (profitcore hit_rate %36.8, edge yok) kullan veya "altyapı hazır, edge kalibrasyonda" çerçevesi kur.

### 🟠 P1 — Placeholder / teknik düzeltme
3. **README.md** — CI/codecov badge URL'lerini `Mericbsk/finpilot-demo` olarak güncelle.
4. **README.md** — Mimari ağaca `academy/`, `broker/`, `monitoring/`, `scripts/` ekle.

### 🟡 P2 — Eksik modül dokümantasyonu
5. **Yeni:** Symbol universe & preset consolidation dokümanı (sync_symbols, enrich_market_caps, consolidate_presets, symbol_lists tablosu).
6. **Yeni:** Alpaca entegrasyon notu (`drl/data_sources/alpaca_provider.py`, paper-only).
7. **Yeni:** Academy mimari dokümanı → [ACADEMY_SELF_EVOLVING_TASARIM.md](../../academy/ACADEMY_SELF_EVOLVING_TASARIM.md) (bu audit'le üretildi).
8. **DEPENDENCIES.md** — alpaca-py, yfinance versiyonlarını teyit et.

---

## 3. Mimari İsimlendirme Düzeltmeleri (kod, belge değil)

> Bunlar belge değil kod aksiyonu; FAZ sonrası ayrı handoff:
- `broker/` boş → ya Alpaca mantığını buraya taşı ya da klasörü kaldır
- `FinanceAcademy/academy/` vs `academy/` çift kopya → tek kaynağa indir
- DRL paketindeki `data_sources/alpaca_provider.py` → broker/ veya core/ altına taşıma değerlendirmesi

---

## 4. Sürüm Notu Önerisi

Belgeler güncellenirken her birine şu başlık eklenmeli:
```
> Son doğrulama: 2026-06-11 — Kaynak: docs/audits/2026-06-11/
> Performans iddiaları için tek doğruluk kaynağı: WIN_RATE_ANALIZI.md
```

---
*FinPilot Belge Senkron Raporu — 2026-06-11*
