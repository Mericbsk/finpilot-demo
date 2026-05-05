#!/usr/bin/env bash
# FinPilot — durdurma scripti

REPO="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO/logs"

echo "FinPilot durduruluyor..."

# PID dosyalarından kill et (watchdog dahil)
for pidfile in "$LOG_DIR/watchdog.pid" "$LOG_DIR/api.pid" "$LOG_DIR/web.pid"; do
    if [[ -f "$pidfile" ]]; then
        pid=$(cat "$pidfile" 2>/dev/null)
        if [[ -n "$pid" ]]; then
            kill -9 "$pid" 2>/dev/null && echo "  Öldürüldü: PID $pid ($(basename $pidfile .pid))" || true
        fi
        rm -f "$pidfile"
    fi
done

# Port ve pattern bazlı temizle (PID dosyası güncel değilse)
fuser -k 8000/tcp 2>/dev/null || true
fuser -k 3001/tcp 2>/dev/null || true
pkill -9 -f "uvicorn api.main" 2>/dev/null || true
pkill -9 -f "next dev" 2>/dev/null || true

echo "FinPilot durduruldu."
