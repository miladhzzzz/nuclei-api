#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Pause for Ollama to start.
sleep 5

echo "🔴 Retrieve deepseek-coder model..."
ollama pull deepseek-coder:6.7b
echo "🟢 Done!"

# Wait for Ollama process to finish.
wait $pid