#!/bin/sh
set -eu

python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
api_pid=$!

cleanup() {
    kill "$api_pid" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

python telegram_bot_runner.py &
bot_pid=$!

while kill -0 "$api_pid" 2>/dev/null && kill -0 "$bot_pid" 2>/dev/null; do
    sleep 1
done

if ! kill -0 "$api_pid" 2>/dev/null; then
    wait "$api_pid"
fi
if ! kill -0 "$bot_pid" 2>/dev/null; then
    wait "$bot_pid"
fi
