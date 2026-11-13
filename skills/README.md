# Skills

Instructions that teach an agent to work with PharmacoGx and ORCESTRA. Each skill is a folder with a `SKILL.md` and, optionally, reference files the agent reads when needed.

- **ORCESTRA discovery:** finds which datasets and PSets have the data a question needs.
- **Data retrieval:** selects and checks molecular, sample and response data from loaded PSets.
- **PharmacoGx analysis:** plans and runs PharmacoGx analyses in R.
- **Setup:** installs and checks PharmacoGx and its dependencies.
- **PSet curation:** builds or checks a PSet from source data.

In the benchmark, `--skills` gives the agent all skills in this folder (see `docs/agent_setup.md`).
