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

1. **Manual answers:** answer each question with PharmacoGx, using the PSet versions listed below. This is done once.
2. **Agent answers:** send each question to the agent in a new session. The agent reuses cached PSets or downloads them from ORCESTRA/Zenodo. Zenodo may block automated requests; report blocked downloads separately from analysis failures. Repeat as often as needed.
3. **Compare:** score each agent run against the manual answers.

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
├── procdata/psets/                    PSets downloaded from ORCESTRA
└── results/benchmark/                 all results
```

## Design

- **Agent gets its own data:** the agent reuses cached PSets or downloads them from ORCESTRA/Zenodo; finding the right dataset is part of the task. GCP download links are being prepared by Matthew and are not yet configured.
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

The questions use 12 PharmacoSets (PSets) from [ORCESTRA](https://orcestra.ca), a platform for curated pharmacogenomic datasets. The manual answers use the latest version of each PSet, listed below with a link to its dataset record.

| PSet | ORCESTRA name | Dataset | Questions |
|---|---|---|---|
| CCLE | `CCLE_2019` | [10.5281/zenodo.18759113](https://doi.org/10.5281/zenodo.18759113) | 29 |
| CTRPv2 | `CTRPv2.1_2016` | [10.5281/zenodo.21794049](https://doi.org/10.5281/zenodo.21794049) | 18 |
| GDSC2 | `GDSC_2020(v2-8.2)` | [10.5281/zenodo.5787145](https://doi.org/10.5281/zenodo.5787145) | 15 |
| gCSI | `gCSI_2019` | [10.5281/zenodo.7829857](https://doi.org/10.5281/zenodo.7829857) | 8 |
| NCI_ALMANAC | `NCI_ALMANAC` | [10.5281/zenodo.23920676](https://doi.org/10.5281/zenodo.23920676) | 8 |
| GDSC2_matrix | `GDSC²_Matrix` | [10.5281/zenodo.23921019](https://doi.org/10.5281/zenodo.23921019) | 7 |
| NCI60 | `NCI60_2026` | [10.5281/zenodo.21043047](https://doi.org/10.5281/zenodo.21043047) | 3 |
| HMCL | `HMCL` | [10.5281/zenodo.23920418](https://doi.org/10.5281/zenodo.23920418) | 3 |
| PRISM | `PRISM_2020` | [10.5281/zenodo.7826864](https://doi.org/10.5281/zenodo.7826864) | 3 |
| GDSC-SQUARE Anchor | `GDSC²_Anchor` | [10.5281/zenodo.23921232](https://doi.org/10.5281/zenodo.23921232) | 2 |
| GRAY | `GRAY_2017` | [10.5281/zenodo.7826847](https://doi.org/10.5281/zenodo.7826847) | 1 |
| GDSC1 | `GDSC_2020(v1-8.2)` | [10.5281/zenodo.7829915](https://doi.org/10.5281/zenodo.7829915) | 1 |

To see all PSets on ORCESTRA from R: `PharmacoGx::availablePSets()`.

A further 21 questions use all 12 PSets.
