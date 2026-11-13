# Usage Guide

## Install

Everything (Python, Biomni, Ollama, and R with PharmacoGx on Linux) is installed with [pixi](https://pixi.sh). pixi pins every version in `pixi.lock`, so each computer gets the same setup.

```bash
git clone https://github.com/bhklab/agentic-pharmacogx.git
cd agentic-pharmacogx
pixi install
```

On macOS, install R and PharmacoGx yourself (pixi provides them on Linux only).

## Ask the agent

```bash
pixi run agent-example Q014 --dry-run   # show the prompt only, no agent
pixi run agent-example Q014             # one question, no skills
pixi run agent-example Q014 --skills    # one question, with the skills in skills/
pixi run agent                          # all 100 questions, no skills
pixi run agent --skills                 # all 100 questions, with skills
```

Replace `Q014` with any question ID (Q001–Q100). The model is set by `AGENT_MODEL` in `pixi.toml`. Each full run saves to a new folder, so running it again adds a repeat.

The agent needs a free GPU. If another model is using most of the GPU memory, it runs on the CPU and is very slow. Check with `nvidia-smi` before a long run. On the lab server, use `bash workflow/scripts/benchmark/agent/run_one.sh Q014 --skills`.

More details: [Agent Setup](agent_setup.md).

## Manual answers

The reference answers are computed with PharmacoGx in R:

```bash
Rscript workflow/scripts/benchmark/manual/manual.R        # all 100 questions
Rscript workflow/scripts/benchmark/manual/manual_tier1.R  # or one tier at a time (tier1, tier2, tier3)
```

Each question has its own block with notes on what was done and any problem found. The notes at the end of `manual.R` list the problems and the questions they affect.

## Where things are saved

| What | Where |
|---|---|
| Questions | `metadata/benchmark_questions.csv` |
| Prompt template | `metadata/benchmark_prompt_template.txt` |
| Skills | `skills/` |
| PSets from ORCESTRA | `data/procdata/psets/` |
| Agent answers | `data/results/benchmark/agent/` |
| Agent step-by-step logs | `logs/benchmark/` |
| Manual answers | `data/results/benchmark/manual/answers.csv` (+ `figures/`) |

How the benchmark is designed and scored: [Benchmark](benchmark.md).
