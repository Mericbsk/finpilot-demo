# İdeas / Parked Backlog

> Faz 1 (Stabilizasyon) bitene kadar buradaki hiçbir iş aktif sprint'e alınmaz.
> Yeni fikir geldiğinde önce buraya yaz, sonra konuş.

## Sprint 2 — UI (DONDURULDU, Faz 1 sonrasına)

- **S2-T1**: Quick Take strip (watchlist üstü tek satır özet)
- **S2-T2**: Trade Plan PriceProgressBar (entry/stop/target görseli)
- **S2-T3**: AI Summary "So What" bloku
- **S2-T4**: Hızlı AI Analiz butonu
- **S2-T5**: FinPilot Edge accordion

## Faz 1'den Ertelendi (Faz 2 başında değerlendir)

- **Step 7 — Pydantic response schema + TS codegen**: API↔frontend tip sözleşmesi. Riskli, geniş; Faz 2'de FE ölçümleriyle birlikte ele al.
- **Step 10 — Tek `fp` entry point**: `start.sh`, `finpilot.bat`, `fp` farklı bağlamlara hizmet ediyor (devcontainer/dev/docker). Birleştirme riskli, mevcut yapı çalışıyor. Faz 2'de doc ile netleştir, gerekirse birleştir.

## Faz 3 İçin — DRL Kararı

- Gerçek DRL serving (vLLM / KAITO / basit FastAPI inference)
  - VEYA
- DRL'i tamamen kaldır, `finpilot_score = composite_score` kalıcı

## Faz 4 İçin — Otomasyon

- GitHub Actions CI (pytest + ruff + docker build)
- Otomatik release notes
- Data retention job (`data/*_2026*` eski dosya temizliği)

## Şimdilik Dokunma

- Cross-process async scan paralelizasyonu
- Streamlit app revival (canonical Next.js)
- Yeni dependency / yeni requirements dosyası
