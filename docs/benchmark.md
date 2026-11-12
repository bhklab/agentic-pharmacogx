# Benchmark

Can an agent answer pharmacogenomic questions as well as an expert using PharmacoGx?

We answer 100 questions twice, once **manually** with PharmacoGx (the reference) and once by the **agent**, and measure how often the answers agree.

```
              100 questions  +  12 PSets
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
        MANUAL                       AGENT
   PharmacoGx code in R       question in plain English
           │                           │
           └─────────────┬─────────────┘
                         ▼
                      COMPARE
                   % agreement
```

## How it works

1. **Get the data:** download the 12 PSets from ORCESTRA.
2. **Manual answers:** answer each question with PharmacoGx. This is done once.
3. **Agent answers:** send each question to the agent in a new session. Repeat as often as needed.
4. **Compare:** score each agent run against the manual answers.

## Files

```
metadata/
├── benchmark_questions.csv            the 100 questions
└── benchmark_prompt_template.txt      prompt sent to the agent

workflow/
├── scripts/benchmark/
│   ├── manual.R                       manual answers
│   └── agent.py                       agent answers (see Agent setup)
└── notebooks/benchmark/
    └── compare.Rmd                    comparison and figures

data/                                  not in git
├── procdata/psets/                    the 12 PSets
└── results/benchmark/                 all results
```

## Design

- **Same data:** both sides use the same PSet files.
- **PharmacoGx only:** the manual answers use PharmacoGx functions, not custom code.
- **Blind:** the agent never sees the manual answers.
- **Independent:** each question runs in a new agent session.
- **Same format:** both sides answer as `qid | answer | method`.

## Runs

A **run** is the agent answering all 100 questions once. Each run is saved in its own folder, with its settings (agent, model, parameters) recorded automatically. Runs can be added at any time:

- **repeat a run** to test reproducibility;
- **change the model or agent** to test an improvement.

## Scoring

An answer is correct if it matches the manual answer in **data, endpoint, method and result** (within tolerance). We report % agreement per tier and overall, with 95% confidence intervals, and how consistent the results are across runs.

## Questions

The 100 questions get harder in three tiers:

- **Tier 1 – Data retrieval** (Q001–Q020): find cell lines, drugs and measurements.
- **Tier 2 – One PharmacoGx function** (Q021–Q050): pick and run the right function.
- **Tier 3 – Multi-step analysis** (Q051–Q100): combine several functions to answer a question.

## Datasets

The 12 PSets are downloaded from ORCESTRA. The table shows the version used and how many questions use each one.

| PSet | ORCESTRA name | Questions |
|---|---|---|
| CCLE | `CCLE_2015` | 29 |
| CTRPv2 | `CTRPv2_2015` | 18 |
| GDSC2 | `GDSC_2020(v2-8.2)` | 15 |
| gCSI | `gCSI_2019` | 8 |
| NCI_ALMANAC | `NCI_ALMANAC` | 8 |
| GDSC2_matrix | `GDSC²_Matrix` | 7 |
| NCI60 | `NCI60_2021` | 3 |
| HMCL | `HMCL` | 3 |
| PRISM | `PRISM_2020` | 3 |
| GDSC-SQUARE Anchor | `GDSC²_Anchor` | 2 |
| GRAY | `GRAY_2017` | 1 |
| GDSC1 | `GDSC_2020(v1-8.2)` | 1 |

A further 21 questions use all 12 PSets.
