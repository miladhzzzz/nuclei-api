#!/usr/bin/env bash
set -eu pipefail

# ────────────────────────────────────────────────
# Start Ollama server in background
# ────────────────────────────────────────────────
echo "→ Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Give the server time to become ready
sleep 3

# Optional: you can do a better wait loop like this:
# until curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; do
#     echo "  waiting for Ollama API to become ready..."
#     sleep 2
# done
# echo "→ Ollama API is ready"

# ────────────────────────────────────────────────
# Pull model(s) if MODEL or MODELS is set
# ────────────────────────────────────────────────

if [[ -n "${MODELS:-}" ]]; then
    # MODELS="llama3.1:8b deepseek-coder:6.7b nomic-embed-text"
    echo "→ Pulling multiple models from \$MODELS"
    for model in $MODELS; do
        echo "  Pulling $model ..."
        ollama pull "$model"
    done
elif [[ -n "${MODEL:-}" ]]; then
    # Single model (classic style)
    echo "→ Pulling model from \$MODEL = $MODEL"
    ollama pull "$MODEL"
else
    echo "→ No MODEL or MODELS variable set → skipping pull"
fi

echo "→ Ollama startup sequence finished"

# ────────────────────────────────────────────────
# Wait forever (keeps container alive)
# ────────────────────────────────────────────────
wait $OLLAMA_PID