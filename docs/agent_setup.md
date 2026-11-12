# Agent setup

The agent is **Biomni** with a local model (**qwen3:8b**) run by **Ollama**. Everything is installed with [pixi](https://pixi.sh).

## Requirements

- **[pixi](https://pixi.sh)**: installs Python, Biomni and Ollama.
- **R with PharmacoGx**: included by pixi on Linux; on macOS, install it yourself.
- **About 6 GB of free disk space** for the model, and an internet connection for the first run.
- A **GPU** is optional; it makes the agent much faster.

## Install

```bash
git clone https://github.com/bhklab/agentic-pharmacogx.git
cd agentic-pharmacogx
pixi install
```

## Run

```bash
pixi run agent-example Q014              # one question (test)
pixi run agent-example Q014 --skills     # one question, with our skills
pixi run agent                           # all questions
pixi run agent --skills                  # all questions, with our skills
```

Replace `Q014` with any question ID (Q001–Q100). To see the prompt without running the agent, add `--dry-run`.

The first run starts Ollama and downloads the model (about 5 GB) automatically. The agent downloads the data it needs from ORCESTRA itself.

Answers are saved in `data/results/benchmark/agent/` and the agent's step-by-step log in `logs/benchmark/`.

## Notes

- **Skills** are in `skills/`. With `--skills`, the agent gets all of them.
- **Model:** set once in `pixi.toml` (`AGENT_MODEL`).
- **Repeats:** every run saves to a new folder, so running it again makes a new run.
