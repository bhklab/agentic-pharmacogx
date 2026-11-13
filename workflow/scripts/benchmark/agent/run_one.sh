#!/bin/bash
# Run ONE benchmark question on the lab server, with a bigger model memory (context).
#   bash workflow/scripts/benchmark/run_one.sh Q014            without skills
#   bash workflow/scripts/benchmark/run_one.sh Q014 --skills   with skills
# Watch it:
#   tail -f logs/benchmark/example/Q014_qwen3-8b_skills.log

Q=$1
mkdir -p logs

# our own Ollama on port 11435, so it does not clash with the shared one on the server (port 11434)
export OLLAMA_HOST=127.0.0.1:11435

# 1. stop OUR old runs and OUR old Ollama (not other users' processes)
pkill -u $USER -f agent_example
pkill -u $USER -f "ollama serve"

# 2. start Ollama with more memory (qwen3:8b max = 40960)
#    use the server's own Ollama (/usr/local/bin/ollama, it can use the GPU); pixi's Ollama has no GPU support
if [ -x /usr/local/bin/ollama ]; then OLLAMA="/usr/local/bin/ollama"; else OLLAMA="pixi run ollama"; fi
OLLAMA_CONTEXT_LENGTH=40960 nohup $OLLAMA serve > logs/ollama.out 2>&1 &

# 3. wait for Ollama, then run the question (downloads the model the first time)
sleep 10
PYTHONUNBUFFERED=1 nohup pixi run agent-example "$@" > logs/$Q.out 2>&1 &

echo "Started $Q. Screen output: logs/$Q.out   Ollama output: logs/ollama.out"
