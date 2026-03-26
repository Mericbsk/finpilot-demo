#!/bin/bash
# Train swing + conservative sequentially with 3M steps
# Momentum 3M already completed

set -e
cd /workspaces/Borsa

echo "=== [1/2] Swing 3M Training ==="
echo "Started: $(date)"

# Check if swing is already training
if pgrep -f "train_sprint18.*swing" > /dev/null; then
    echo "Swing training already running, waiting for completion..."
    while pgrep -f "train_sprint18.*swing" > /dev/null; do
        sleep 60
    done
    echo "Swing training finished: $(date)"
else
    echo "Starting swing training..."
    python3 scripts/train_sprint18.py --agent swing --timesteps 3000000 --symbol-set broad 2>&1 | tee logs/swing_3m_training.log
    echo "Swing training finished: $(date)"
fi

echo ""
echo "=== [2/2] Conservative 3M Training ==="
echo "Started: $(date)"
python3 scripts/train_sprint18.py --agent conservative --timesteps 3000000 --symbol-set broad 2>&1 | tee logs/conservative_3m_training.log
echo "Conservative training finished: $(date)"

echo ""
echo "=== ALL DONE ==="
echo "Finished: $(date)"
