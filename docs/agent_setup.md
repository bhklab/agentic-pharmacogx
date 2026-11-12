# Agent setup

The agent is **Biomni 0.0.8 (A1)**, running a local language model (**qwen3.8:27b**) through **Ollama**.

```python
from biomni.config import default_config
from biomni.agent import A1

model = "qwen3.8:27b"
default_config.llm = model
default_config.source = "Ollama"

agent = A1(path="./data", llm=model, source="Ollama", expected_data_lake_files=[])
agent.go("your question")
```

## Environment

The project uses a single pixi environment. It contains:

| Component | Version | Source |
|---|---|---|
| Python | 3.12 | conda-forge |
| Biomni | 0.0.8 | PyPI |
| R + PharmacoGx | 4.5 + 3.14 | bioconda (Linux only) |

Exact versions of all packages are recorded in `pixi.lock`.

R and PharmacoGx are installed by pixi on Linux only, because bioconda provides PharmacoGx 3.14 for Linux only. On macOS, use a local R installation with PharmacoGx 3.14.

## Requirements

- **[pixi](https://pixi.sh)**
- **[Ollama](https://ollama.com)**, installed separately, with the model pulled: `ollama pull qwen3.8:27b`
- A **GPU** large enough to run the model

## Usage

```bash
# 1. Get the code and install the environment
git clone https://github.com/bhklab/agentic-pharmacogx.git
cd agentic-pharmacogx
pixi install

# 2. Check the installation
pixi run python -c "import biomni; print('Biomni OK')"
ollama list                                   # should list qwen3.8:27b

# 3. Place the 12 PSets in data/procdata/psets/

# 4. Send one question to the agent
pixi run agent-example                        # Q013 -> data/results/benchmark/agent/example/

# 5. Send all questions
pixi run agent-run --run run01                # -> data/results/benchmark/agent/run01/
```

To update the code later, run `git pull`, then `pixi install`.

## Notes

- **Without pixi:** `pip install -r workflow/scripts/benchmark/requirements.txt` installs the same Python packages. R and PharmacoGx must then be installed separately.
- **Another model:** set `model` in `agent_example.py` and `agent.py` to any model available in Ollama.
- **Restarts and repeats:** an interrupted run is resumed with the same command, and completed questions are skipped. Use `--run run02`, `--run run03`, … for repeated runs.
- **Settings:** Biomni defaults are used (temperature 0.7; 600 s timeout per code execution). Each run records its settings in `run_info.json`.
