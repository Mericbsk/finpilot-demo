#!/usr/bin/env bash
# FinPilot hızlı yönetim aracı
# Kullanım: ./fp start | stop | restart | status | log
REPO="$(cd "$(dirname "$0")" && pwd)"

api_ok() { curl -sf --max-time 2 http://localhost:8000/api/v1/health >/dev/null 2>&1; }
web_ok() { curl -sf --max-time 2 http://localhost:3001 >/dev/null 2>&1; }

case "${1:-status}" in
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
    echo "────────────────────────────────────────"
    ;;
  log)
    tail -f "$REPO/logs/api.log" "$REPO/logs/web.log" 2>/dev/null
    ;;
  *)
    echo "Kullanım: ./fp [start|stop|restart|status|log]"
    ;;
esac
