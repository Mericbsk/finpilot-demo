# FinPilot 2 Haftalık Onarım ve Test Planı

**Amaç:** No-Go yaratan kritik eksikleri 10 iş günü içinde kapatmak
**Varsayılan sorumlu:** Ibrahim Meriç Başak
**Çalışma modeli:** P0 önce release blocker, ardından kalite ve sadeleştirme

| ID | Öncelik | İş | Sahip | Tahmini İş Gücü (gün) | Kabul Kriteri | Canary / Rollback |
|----|---------|----|-------|------------------------|----------------|-------------------|
| T1 | P0 | Resmi runtime sözleşmesini belirle | Platform | 1.0 | README, `start.sh`, Docker, OpenAPI, CI aynı port ve giriş noktalarını kullanır | Canary: yeni doküman ve start script ayrı branch. Rollback: eski script korunur |
| T2 | P0 | `requirements.txt` ve API bağımlılıklarını düzelt | Platform | 1.0 | Temiz venv içinde `pip install -r requirements.txt` hatasız | Canary: yeni lock denemesi ayrı job. Rollback: önceki requirements kopyası |
| T3 | P0 | API için `/ready` ve `/metrics` rotalarını expose et | Platform / Ops | 1.0 | `curl /ready` ve `curl /metrics` başarılı | Canary: staging route ekle. Rollback: route feature flag kapat |
| T4 | P0 | Auth middleware’ini route bazında uygula | Security / Backend | 1.5 | Anonymous user protected route’lara erişemez; user settings anon yazılamaz | Canary: sadece settings ve trade route’larında başlat. Rollback: dependency revert |
| T5 | P1 | Frontend test komutunu stabilize et | Frontend | 1.0 | `npm test` default koşuda timeout vermeden geçer | Canary: test config branch. Rollback: eski config |
| T6 | P1 | Frontend contract smoke testleri ekle | Frontend / Backend | 1.0 | `/py-api/health`, `/py-api/models`, `/py-api/user/settings` smoke suite CI’de geçer | Canary: non-blocking CI step. Rollback: allow-failure |
| T7 | P1 | Observability wiring: startup logging + Sentry + request metrics | Ops / Backend | 1.5 | startup log, latency metric ve error capture görülebilir | Canary: dev/staging env only. Rollback: env flag off |
| T8 | P1 | Legacy Streamlit destek kararını ver | Product / Platform | 0.5 | “aktif / pasif / internal-only” kararı dokümante edilir | Canary: deprecation warning. Rollback: legacy keep |
| T9 | P2 | Docker smoke testini yeni mimariye taşı | DevOps | 1.0 | CI docker smoke 3001 + 8000 için geçer | Canary: ayrı `docker-modern` job. Rollback: legacy job saklanır |
| T10 | P2 | E2E/critical path taslağı kur | QA / Frontend | 1.5 | login/settings/scanner health için en az 3 uçtan uca senaryo | Canary: nightly only. Rollback: non-blocking mark |

## Gün Bazlı Öneri

| Gün | Hedef |
|-----|-------|
| 1 | T1, T2 |
| 2 | T3 |
| 3-4 | T4 |
| 5 | T5 |
| 6 | T6 |
| 7-8 | T7 |
| 9 | T8, T9 |
| 10 | T10 + yeniden denetim |

## Kabul Test Paketi

```bash
cd /workspaces/Borsa
python3 -m venv .venv-audit && source .venv-audit/bin/activate
pip install -r requirements.txt
bash start.sh
curl -sf http://localhost:8000/api/v1/health
curl -sf http://localhost:8000/ready
curl -sf http://localhost:8000/metrics | head
curl -I http://localhost:3001
python3 -m pytest tests/test_auth.py tests/test_prometheus.py tests/test_sentry.py -q
cd web && npm test && npm run build
```

## Canary Prosedürü

1. Yeni runtime contract değişikliklerini tek feature branch altında topla.
2. Docker + start script + README + OpenAPI birlikte güncellensin.
3. Önce staging/local canary’de 1 gün çalıştır.
4. Health, ready, metrics, auth smoke sonuçlarını kaydet.
5. Ancak sonra ana branch’e merge et.

## Rollback Prosedürü

1. Son bilinen çalışan `start.sh` ve frontend build çıktısını koru.
2. Auth enforcement kırarsa geçici olarak yalnızca settings/trade route’larında revert et.
3. Metrics/ready wiring servis başlatmayı bozarsa env flag ile kapat.
4. Docker modern smoke başarısızsa legacy job block etmeyecek şekilde ayrı tutulur.

## Tekrarlama Notu

- **Ne nedir:** Bu dosya, No-Go’yu kaldırmak için yapılacak 10 günlük operasyon planıdır.
- **Nasıl çalışır:** P0 işleri prod blocker’ları kaldırır, P1 işleri güvenilirliği artırır, P2 işleri sürdürülebilirliği sağlar.
- **Nasıl test edilir:** her görevin kabul kriteri smoke/contract/build/test ile doğrulanır.
- **Bir sonraki değerlendirme için not:** 10. gün sonunda ana audit raporu yeniden koşulmalı ve Go/No-Go kararı güncellenmelidir.
