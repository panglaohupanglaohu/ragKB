#!/bin/bash
# Start GPT-SoVITS TTS API server
# Usage: bash scripts/start_tts.sh

GPT_SOVITS_DIR="$HOME/GPT-SoVITS"
VENV_DIR="$GPT_SOVITS_DIR/venv"
CONFIG="GPT_SoVITS/configs/tts_infer.yaml"
HOST="127.0.0.1"
PORT="9880"
FAST_LANGDETECT_DIR="$GPT_SOVITS_DIR/GPT_SoVITS/pretrained_models/fast_langdetect"
export MPLCONFIGDIR="$HOME/.cache/matplotlib"
export PYTHONUNBUFFERED=1

if [ ! -d "$GPT_SOVITS_DIR" ]; then
    echo "[ERROR] GPT-SoVITS not found at $GPT_SOVITS_DIR"
    exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "[ERROR] Virtual environment not found at $VENV_DIR"
    exit 1
fi

cd "$GPT_SOVITS_DIR" || exit 1
mkdir -p "$FAST_LANGDETECT_DIR"
source "$VENV_DIR/bin/activate"

echo "[INFO] Starting GPT-SoVITS API on $HOST:$PORT ..."
echo "[INFO] Config: $CONFIG"
echo "[INFO] Device: cpu (Apple M2 MPS fallback)"
echo "[INFO] Matplotlib cache: $MPLCONFIGDIR"

exec python api_v2.py -a "$HOST" -p "$PORT" -c "$CONFIG"
