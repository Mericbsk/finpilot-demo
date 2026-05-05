#!/usr/bin/env bash
# FinPilot — başlatma scripti
# Kullanım: ./start.sh
# ─────────────────────────────────────────────────────────────
REPO="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"

API_PORT=8000
WEB_PORT=3001
API_LOG="$LOG_DIR/api.log"
WEB_LOG="$LOG_DIR/web.log"

# ── Zaten çalışıyor mu? ──────────────────────────────────────
api_ok() { curl -sf --max-time 2 http://localhost:$API_PORT/api/v1/ready >/dev/null 2>&1; }
web_ok() { curl -sf --max-time 2 http://localhost:$WEB_PORT >/dev/null 2>&1; }

if api_ok && web_ok; then
    echo "FinPilot zaten çalışıyor → http://localhost:$WEB_PORT"
    exit 0
fi

# ── Eski süreçleri temizle ───────────────────────────────────
echo "Eski süreçler temizleniyor..."
for pid_file in "$LOG_DIR/api.pid" "$LOG_DIR/web.pid" "$LOG_DIR/watchdog.pid"; do
    if [[ -f "$pid_file" ]]; then
        pid=$(cat "$pid_file" 2>/dev/null)
        [[ -n "$pid" ]] && kill -9 "$pid" 2>/dev/null || true
        rm -f "$pid_file"
    fi
done
# Port bazlı kill (PID dosyası güncel değilse)
fuser -k ${API_PORT}/tcp 2>/dev/null || true
fuser -k ${WEB_PORT}/tcp 2>/dev/null || true
# Tüm uvicorn ve next dev süreçlerini temizle
pkill -9 -f "uvicorn api.main" 2>/dev/null || true
pkill -9 -f "next dev" 2>/dev/null || true
sleep 2

# ── .next izin sorununu önle ─────────────────────────────────
if [[ -d "$REPO/web/.next" ]]; then
    # Sadece .next'i chown et (node_modules dahil etme — çok yavaş)
    sudo chown -R "$(id -u):$(id -g)" "$REPO/web/.next" 2>/dev/null || true
fi
# lock dosyasını her zaman temizle
rm -f "$REPO/web/.next/dev/lock" 2>/dev/null || true

# ── API başlat (--reload YOK → stabil PID) ───────────────────
echo "API başlatılıyor (port $API_PORT)..."
cd "$REPO"
nohup python3 -m uvicorn api.main:app \
    --host 0.0.0.0 --port $API_PORT \
    --timeout-keep-alive 75 \
    > "$API_LOG" 2>&1 &
API_PID=$!
echo $API_PID > "$LOG_DIR/api.pid"

# ── API hazır olana kadar bekle ──────────────────────────────
echo -n "  API bekleniyor"
for i in $(seq 1 30); do
    sleep 1
    if api_ok; then echo " hazır (${i}s)"; break; fi
    echo -n "."
    if [[ $i -eq 30 ]]; then
        echo ""
        echo "HATA: API 30s içinde başlamadı. Log: $API_LOG"
        tail -10 "$API_LOG"
        exit 1
    fi
done

# ── API watchdog ─────────────────────────────────────────────
(
    while true; do
        sleep 20
        if [[ ! -f "$LOG_DIR/api.pid" ]]; then exit 0; fi  # stop.sh çalıştı
        if ! api_ok; then
            echo "$(date '+%H:%M:%S') [watchdog] API çöktü, yeniden başlatılıyor..." | tee -a "$API_LOG"
            pkill -9 -f "uvicorn api.main" 2>/dev/null || true
            fuser -k ${API_PORT}/tcp 2>/dev/null || true
            sleep 3
            cd "$REPO"
            nohup python3 -m uvicorn api.main:app \
                --host 0.0.0.0 --port $API_PORT \
                --timeout-keep-alive 75 \
                >> "$API_LOG" 2>&1 &
            echo $! > "$LOG_DIR/api.pid"
        fi
    done
) &
echo $! > "$LOG_DIR/watchdog.pid"

# ── Frontend başlat ──────────────────────────────────────────
echo "Frontend başlatılıyor (port $WEB_PORT)..."
cd "$REPO/web"
nohup npm run dev -- --port $WEB_PORT > "$WEB_LOG" 2>&1 &
WEB_PID=$!
echo $WEB_PID > "$LOG_DIR/web.pid"

# ── Frontend hazır olana kadar bekle ─────────────────────────
echo -n "  Frontend bekleniyor"
for i in $(seq 1 60); do
    sleep 1
    if web_ok; then echo " hazır (${i}s)"; break; fi
    # Erken hata tespiti
    if grep -q "EACCES\|permission denied\|error\|Error" "$WEB_LOG" 2>/dev/null && [[ $i -gt 5 ]]; then
        echo ""
        echo "HATA: Frontend başlayamadı. Log: $WEB_LOG"
        tail -10 "$WEB_LOG"
        exit 1
    fi
    echo -n "."
    if [[ $i -eq 60 ]]; then
        echo ""
        echo "UYARI: Frontend 60s içinde yanıt vermedi. Log: $WEB_LOG"
    fi
done

# ── Özet ─────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════"
echo "  FinPilot hazır!"
echo "  Arayüz : http://localhost:$WEB_PORT"
echo "  API    : http://localhost:$API_PORT"
echo "  Loglar : $LOG_DIR/"
echo "  Durmak : ./stop.sh"
echo "════════════════════════════════════════"
echo ""

# Tarayıcı aç
[[ -n "$BROWSER" ]] && "$BROWSER" "http://localhost:$WEB_PORT" 2>/dev/null &
