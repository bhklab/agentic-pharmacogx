#!/bin/bash
# Run one question using the existing Ollama service. Does not stop other runs.
#   bash workflow/scripts/benchmark/agent/run_one.sh Q014 --skills
set -euo pipefail
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 QUESTION_ID [--skills]" >&2
    exit 2
fi
cd "$(dirname "$0")/../../../.."
export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
if ! curl --fail --silent --show-error "$OLLAMA_HOST/api/version" >/dev/null; then
    echo "Ollama is not reachable at $OLLAMA_HOST. Start it before running this script." >&2
    exit 1
fi
exec pixi run agent-example "$@"
