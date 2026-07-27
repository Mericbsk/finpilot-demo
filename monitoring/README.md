# monitoring/ — PARKED (2026-07-24)

**Durum: PARK EDİLDİ / kullanımda değil.** Bu klasör (Prometheus + Grafana +
`alerts.yml`) FinPilot'un **her-zaman-açık API** mimarisinden kalmadır. Kurallar
(`APIDown`, `APIReadinessDegraded`) sürekli çalışan bir API'yi ve onu scrape eden
bir Prometheus sunucusunu varsayar.

## Neden park edildi
Mevcut operasyon modeli **manuel, tek-PC, API-opsiyonel**:
- Yayın `scripts/publish_now.py` ile elle tetikleniyor (`FINPILOT_ENABLE_DISTRIBUTION=0`).
- Kritik operasyonel uyarılar artık **Telegram `notify_admin`** üzerinden geliyor:
  - yayın başarısız / web push başarısız (`publish_now`)
  - arşiv büyümüyor (`archive_bridge.check_archive_continuity`)
  - taslak yayınlanmadan expired oldu + seri kırıldı (`broadcast.expire_stale`)
- Bu ölçüm modeli tek-PC gerçekliğine uygun; ayakta bir Prometheus/Grafana yığını yok.

Yani `APIDown` gibi kurallar bugün **anlamsız** (API zaten sürekli açık değil) ve
yanlış-pozitif üretir.

## Geri açmak istenirse
Kod hâlâ duruyor: `core/prometheus_exporter.py`, `core/monitoring.py`, `api/main.py`
`/metrics` ucu. Her-zaman-açık bir dağıtım (ör. Render'da kalıcı API) hedeflenirse:
1. API'yi kalıcı çalışır hale getir + `/metrics` ucunu doğrula.
2. Bir Prometheus örneği kur, `prometheus.yml` ile bu API'yi scrape et.
3. `alerts.yml`'i Alertmanager'a bağla; runbook yollarını (`docs/runbooks/`) doldur.

Bu karar geri-dönülebilir; kod silinmedi, yalnızca resmen "kullanımda değil" olarak
işaretlendi ki her oturum bunu yeniden keşfetmesin.
