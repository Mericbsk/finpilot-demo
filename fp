#!/usr/bin/env bash
# FinPilot hızlı yönetim aracı
# Kullanım: ./fp <komut>
#   start / stop / restart / status / log  — yerel dev (bash start.sh)
#   up / down / ps / logs                  — docker compose (production)
REPO="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose"

api_ok()  { curl -sf --max-time 2 http://localhost:8000/api/v1/health >/dev/null 2>&1; }
web_ok()  { curl -sf --max-time 2 http://localhost:3001 >/dev/null 2>&1; }
dc_check(){ command -v docker >/dev/null 2>&1 || { echo "docker not found"; exit 1; }; }
env_check(){
  if [[ ! -f "$REPO/.env" ]]; then
    echo "HATA: .env dosyası bulunamadı. Önce: cp .env.example .env"
    exit 1
  fi
}

# ── Sentry uyarısı ────────────────────────────────────────────
warn_sentry(){
  if ! grep -q "^SENTRY_DSN=" "$REPO/.env" 2>/dev/null || \
     grep -q "^SENTRY_DSN=$" "$REPO/.env" 2>/dev/null; then
    echo "UYARI: .env içinde SENTRY_DSN tanımlı değil — hata izleme devre dışı."
  fi
}

case "${1:-status}" in
  # ── Yerel dev komutları ──────────────────────────────────────
  start)
    bash "$REPO/start.sh"
    ;;
  stop)
    bash "$REPO/stop.sh"
    ;;
  restart)
    bash "$REPO/stop.sh"
    sleep 2
    bash "$REPO/start.sh"
    ;;
  status)
    echo "── FinPilot Durum ──────────────────────"
    api_ok && echo "  API      : ÇALIŞIYOR  http://localhost:8000" \
           || echo "  API      : DURDU"
    web_ok && echo "  Frontend : ÇALIŞIYOR  http://localhost:3001" \
           || echo "  Frontend : DURDU"
    for svc in api web watchdog; do
      pid_file="$REPO/logs/${svc}.pid"
      if [[ -f "$pid_file" ]]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
          echo "  ${svc} PID  : $pid (aktif)"
        else
          echo "  ${svc} PID  : $pid (çökmüş!)"
        fi
      fi
    done
    # Docker container durum bilgisi (varsa)
    if command -v docker >/dev/null 2>&1; then
      echo ""
      echo "── Docker Containers ───────────────────"
      docker ps --filter "name=finpilot" --format "  {{.Names}}\t{{.Status}}" 2>/dev/null || true
    fi
    echo "────────────────────────────────────────"
    ;;
  log)
    tail -f "$REPO/logs/api.log" "$REPO/logs/web.log" 2>/dev/null
    ;;

  # ── Docker Compose komutları ─────────────────────────────────
  up)
    dc_check; env_check; warn_sentry
    echo "FinPilot başlatılıyor (docker compose)..."
    cd "$REPO"
    $COMPOSE --profile scanner --profile telegram up -d --build
    echo ""
    echo "════════════════════════════════════════"
    echo "  FinPilot hazır!"
    echo "  Arayüz : http://localhost:3001"
    echo "  API    : http://localhost:8001"
    echo "  Durmak : ./fp down"
    echo "  Loglar : ./fp logs"
    echo "════════════════════════════════════════"
    ;;
  down)
    dc_check
    cd "$REPO"
    $COMPOSE --profile scanner --profile telegram down --remove-orphans
    echo "FinPilot durduruldu."
    ;;
  ps)
    dc_check
    cd "$REPO"
    $COMPOSE ps
    ;;
  logs)
    dc_check
    cd "$REPO"
    $COMPOSE logs -f --tail=200 "${@:2}"
    ;;

  *)
    cat <<EOF
Kullanim: ./fp <komut>

  Yerel dev:
    start     — API + Frontend baslatir (bash start.sh)
    stop      — Durdurur
    restart   — Yeniden baslatir
    status    — Calisma durumunu goster
    log       — Log takibi

  Docker Compose (production):
    up        — Tum servisleri docker ile baslatir
    down      — Tum docker servislerini durdurur
    ps        — Docker container listesi
    logs      — Docker log takibi
EOF
    ;;
esac
