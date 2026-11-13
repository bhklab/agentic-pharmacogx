# Agent setup

The agent is **Biomni** with a local model (**qwen3.8:27b**) run by **Ollama**. Everything is installed with [pixi](https://pixi.sh).

## Requirements

- **[pixi](https://pixi.sh)**: installs Python, Biomni and Ollama.
- **R**: included by Pixi on Linux. On macOS, provide R 4.5 and a compiler.
- **PharmacoGx/CoreGx**: installed from pinned GitHub commits by the setup task, not the Bioconductor PharmacoGx release.
- **At least 20 GB of free disk space** for the model, and an internet connection for the first run.
- A **GPU** is optional; it makes the agent much faster.

## Install

```bash
git clone https://github.com/bhklab/agentic-pharmacogx.git
cd agentic-pharmacogx
pixi install
pixi run setup
pixi run verify-pgx
```

## Run

```bash
pixi run agent-example Q014              # one question (test)
pixi run agent-example Q014 --skills     # one question, with our skills
pixi run agent                           # all questions
pixi run agent --skills                  # all questions, with our skills
```

Replace `Q014` with any question ID (Q001–Q100). To see the prompt without running the agent, add `--dry-run`.

The first run starts Ollama and downloads the model (about 17 GB) automatically. The single-question example can download PSets from ORCESTRA. The full-question run uses only the PSets already in `data/procdata/psets/`.

`bash workflow/scripts/benchmark/agent/run_one.sh Q014 --skills` runs one question against an existing Ollama service without restarting it or stopping other runs. It runs in the foreground. Set `OLLAMA_HOST` to use a different endpoint.

Answers are saved in `data/results/benchmark/agent/` and the agent's step-by-step log in `logs/benchmark/`.

## Notes

- **Skills** are in `skills/`. With `--skills`, the agent gets all of them.
- **Model:** set once in `pixi.toml` (`AGENT_MODEL`).
- **Repeats:** every run saves to a new folder, so running it again makes a new run.

## PharmacoGx feature branch

`pixi run setup` installs PharmacoGx `feat/mcp` at `a7aa4d7` and CoreGx
`feat/sparse-longtable-index` at `f760bc7`. Full commits are in
`workflow/scripts/setup/pharmacogx.R`. The packages live in `.pixi/r-library`,
which Pixi places first in the R library search path. The setup skips matching
installs and `verify-pgx` checks the loaded paths, commits and required functions.

Run setup before agent or manual analysis. Do not change the package environment
during a benchmark. Start a new run after setup so results record the new versions.
Other R dependencies are resolved from CRAN/Bioconductor and are not fully locked
by `pixi.lock`; the two Gx revisions are pinned. The setup may compile dependencies.

A direct Pixi Git source needs a package build configuration. Pixi's R backend
does not currently support Bioconductor dependencies, so a separate conda build
recipe is not required for this setup approach.
