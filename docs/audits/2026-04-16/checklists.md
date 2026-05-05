# FinPilot Kontrol Şablonları ve Otomatik Test Senaryoları

## 1. Smoke Checklist

```text
[ ] start.sh ile frontend ve API birlikte ayağa kalkıyor
[ ] GET /api/v1/health -> 200
[ ] GET /ready -> 200
[ ] GET /metrics -> Prometheus text output
[ ] GET / -> 200
[ ] GET /dashboard -> 200
[ ] GET /api/quotes?symbols=AAPL,MSFT -> JSON dönüyor
[ ] /py-api/models -> JSON dönüyor
[ ] /py-api/user/settings -> auth beklentisine uygun davranıyor
```

### Örnek Komutlar

```bash
cd /workspaces/Borsa
bash start.sh
curl -sf http://localhost:8000/api/v1/health
curl -sf http://localhost:8000/ready
curl -sf http://localhost:8000/metrics | head
curl -I http://localhost:3001
curl -s "http://localhost:3001/api/quotes?symbols=AAPL,MSFT"
```

## 2. Integration Checklist

```text
[ ] Frontend -> /py-api rewrite doğru hosta gidiyor
[ ] /py-api/scan -> scanner modülünü çalıştırıyor
[ ] /py-api/models -> model registry verisini dönüyor
[ ] /py-api/user/settings -> DB'ye yazıp tekrar okuyabiliyor
[ ] /api/quotes -> Yahoo batch cache ile çalışıyor
[ ] logs/api.log ve logs/web.log hata üretmiyor
```

### Örnek Komutlar

```bash
curl -s http://localhost:3001/ | head
curl -s http://localhost:8000/api/v1/scan/shortlist/status
curl -s http://localhost:8000/api/v1/user/settings
curl -s -X PUT http://localhost:8000/api/v1/user/settings \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"audit-user","settings":{"market":"US"}}'
curl -s 'http://localhost:8000/api/v1/user/settings?user_id=audit-user'
```

## 3. Contract Checklist

```text
[ ] OpenAPI dokümanı runtime ile aynı endpointleri listeliyor
[ ] Auth gerekli endpointler gerçekten 401/403 veriyor
[ ] Scan request schema ile response schema sabit
[ ] User settings schema backward-compatible
[ ] LLM analyze response section formatı sabit
```

### Örnek Contract Test Komutları

```bash
python3 -m pytest tests/test_auth.py tests/test_prometheus.py -q
python3 -m pytest tests/test_views_smoke.py -q
cd /workspaces/Borsa/web && npx vitest run --pool=threads
```

## 4. Performance Checklist

```text
[ ] /api/quotes p95 latency hedefi tanımlı
[ ] /py-api/scan için timeout ve worker limiti doğrulandı
[ ] İlk dashboard yüklenmesi ölçüldü
[ ] Rate limit davranışı test edildi
[ ] Cache TTL ve stale fallback doğrulandı
```

### Örnek Performans Komutları

```bash
time curl -s 'http://localhost:3001/api/quotes?symbols=AAPL,MSFT,GOOGL,META,AMZN'
time curl -s http://localhost:8000/api/v1/health
grep 'GET /api/quotes' /workspaces/Borsa/logs/web.log | tail -20
```

## 5. Security Checklist

```text
[ ] FINPILOT_SECRET_KEY zorunlu ve default fallback yok
[ ] Protected route'lar anon erişime kapalı
[ ] CORS allowlist prod domainleriyle sınırlı
[ ] `.env` repo dışında tutuluyor / secret manager politikası var
[ ] Hardcoded secret scan CI'da aktif
[ ] Sentry PII gönderimi kapalı ya da kontrollü
[ ] User settings çok kiracılı izolasyona uygun
```

### Örnek Güvenlik Komutları

```bash
git grep -n 'FINPILOT_SECRET_KEY\|POSTGRES_PASSWORD\|API_KEY' -- . ':!.env.example'
curl -i http://localhost:8000/api/v1/user/settings
curl -i http://localhost:8000/api/v1/trade/account
```

## 6. Frontend Checklist

```text
[ ] Build pipeline çalışıyor
[ ] Critical UI path smoke testleri geçiyor
[ ] API contract uyumu doğrulandı
[ ] Error boundary ve fallback var
[ ] E2E coverage planı var
```

### Frontend Komutları

```bash
cd /workspaces/Borsa/web
npm test
npm run build
```

## 7. Backend Checklist

```text
[ ] Liveness endpoint var
[ ] Readiness endpoint var
[ ] API latency ölçülüyor
[ ] Error rate ölçülüyor
[ ] Secrets management yapılandırıldı
[ ] DB connection pooling stratejisi net
[ ] Structured logging ve tracing aktif
```

### Backend Komutları

```bash
cd /workspaces/Borsa
curl -sf http://localhost:8000/api/v1/health
curl -sf http://localhost:8000/ready
curl -sf http://localhost:8000/metrics | head -20
python3 -m pytest tests/test_prometheus.py tests/test_sentry.py -q
```

## 8. Data Pipeline Checklist

```text
[ ] Kaynak endpoint erişilebilir
[ ] Timestamp / sequence kontrolü var
[ ] Transform adımları idempotent
[ ] Cache TTL ve stale fallback var
[ ] Schema contract testleri var
```

### Data Pipeline Komutları

```bash
curl -s http://localhost:8000/api/v1/scan/shortlist/status
python3 -m pytest tests/test_data_fetcher.py tests/test_indicators.py tests/test_signals.py -q
```

## 9. MPC / ML Checklist

```text
[ ] Model versiyonlama var
[ ] Reproducibility manifest var
[ ] Test datasetleri mevcut
[ ] Edge case senaryoları tanımlı
[ ] Performance benchmark var
```

### ML Komutları

```bash
python3 -m pytest tests/test_drl_integration.py tests/test_evaluate.py -q
curl -s http://localhost:8000/api/v1/models
```

## 10. Infra Checklist

```text
[ ] IaC ve compose sözleşmesi güncel
[ ] Backup / recovery prosedürü yazılı
[ ] Monitoring / alerting kurulu
[ ] Cost / quota alarmı var
[ ] Canary / rollback runbook hazır
```

### Infra Komutları

```bash
docker compose config
docker build -f api/Dockerfile -t finpilot-api-audit .
docker build -f web/Dockerfile -t finpilot-web-audit ./web
```

## 11. Örnek CI Job Tanımları

### Runtime Contract Job

```yaml
name: runtime-contract
on: [push, pull_request]
jobs:
  contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -m pip install --upgrade pip && pip install -r requirements.txt
      - run: bash start.sh
      - run: curl -sf http://localhost:8000/api/v1/health
      - run: curl -sf http://localhost:8000/ready
      - run: curl -sf http://localhost:8000/metrics | head
```

### Frontend Contract Job

```yaml
name: frontend-contract
on: [push, pull_request]
jobs:
  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: web
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
      - run: npm ci
      - run: npm test
      - run: npm run build
```

### Security Gate Job

```yaml
name: security-gate
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install bandit safety
      - run: bandit -r api auth core scanner drl -ll -ii --skip B101
      - run: safety check --full-report || true
```

## 12. Tekrarlama Notu

- **Ne nedir:** Bu dosya operasyon, QA ve geliştirici ekip için kopyala-yapıştır kontrol paketidir.
- **Nasıl çalışır:** smoke, integration, contract, performance ve security kontrolleri aynı sırayla koşturulur.
- **Nasıl test edilir:** tek bir run id altında bütün komutlar çalıştırılır ve sonuçlar immutable artefact olarak saklanır.
- **Bir sonraki değerlendirme için not:** bu checklist CI pipeline’ına ve release runbook’a aynen taşınmalıdır.
