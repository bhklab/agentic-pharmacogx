#!/bin/bash
# Run ONE benchmark question on the lab server, with a bigger model memory (context).
#   bash workflow/scripts/benchmark/run_one.sh Q014            without skills
#   bash workflow/scripts/benchmark/run_one.sh Q014 --skills   with skills
# Watch it:
#   tail -f logs/benchmark/example/Q014_qwen3-8b_skills.log

Q=$1

# 1. stop old runs and the old Ollama
pkill -f agent_example
pkill -f "ollama serve"

# 2. start Ollama with more memory (qwen3:8b max = 40960)
OLLAMA_CONTEXT_LENGTH=40960 nohup pixi run ollama serve > logs/ollama.out 2>&1 &

# 3. wait for Ollama, then run the question
sleep 10
PYTHONUNBUFFERED=1 nohup pixi run agent-example "$@" > logs/$Q.out 2>&1 &

echo "Started $Q. Screen output: logs/$Q.out"
