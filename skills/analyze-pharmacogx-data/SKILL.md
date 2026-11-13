
---
name: analyze-pharmacogx-data
description: Use when analyzing PharmacoGx or ORCESTRA PharmacoSets, including monotherapy, drug combinations, biomarker discovery, and cross-dataset analyses. Inspect dataset structure and apply validated data-specific handling before performing statistical analyses. For PRISM_2020 molecular biomarker questions, use validated CCLE molecular profiles when the required measurements are unavailable in PRISM.
---

# PharmacoGx Data-Aware Analysis

## Core principles

1. Never assume that different PharmacoSets share identical
   data structures, assay names, response metrics, or
   experimental designs.

2. Inspect the relevant PSet before constructing an
   analytical workflow.

3. Prefer validated PharmacoGx and CoreGx accessors.

4. Apply dataset-specific adjustments only when the
   structure and intended interpretation justify them.

5. Preserve the original data and document any changes.

## Before each analysis

- Identify relevant PSets and their versions.
- Inspect sample and treatment annotations.
- Identify available molecular assays and feature IDs.
- Inspect treatment-response assays and metrics.
- Determine the appropriate experimental unit.
- Check sample, drug, and molecular-profile mappings.
- Record available and missing measurements.

## Monotherapy response

- Inspect `sensitivityMeasures()` and relevant profiles.
- Identify available AUC, AAC, IC50 and other metrics.
- Select the metric appropriate for the question.
- Verify its scale and direction.
- Check drug-specific and sample-specific coverage.
- Handle repeated experiments consistently.

## Combination response

Always inspect `treatmentResponse()` before selecting
a synergy measurement.

1. Check whether a `synergy` assay exists.
2. Inspect its score columns and dose information.
3. Check the `profiles` assay for aggregated scores.
4. Identify available synergy models and variants.
5. Select the score appropriate for the research question.
6. Record the source assay and exact score column.

### Synergy measurement selection

- When dose-level synergy measurements are available,
  prefer them when appropriate for the research question.
- Use dose-level scores for dose-specific investigations.
- For sample-level analyses, derive a documented summary
  from dose-level measurements when scientifically justified.
- If only aggregated synergy scores are available,
  use those scores and report their provenance.
- Never treat individual doses as independent biological
  samples.

For cell-line-level associations, obtain a defined summary
per cell line and drug pair.

Do not assume that identically named synergy metrics have
identical scales, signs, or computation methods.

## GDSC-anchor

Recognize its 7 x 2 anchor-library design.

Do not assume that the absence of `aac_recomputed_2`
means the second drug lacks monotherapy AAC.

Inspect drug-specific records and identify the available
monotherapy measurements for each combination component.

Retrieve the corresponding AAC separately for both drugs
and match measurements to the relevant cell lines.

Verify the response metric's provenance before use.

## Molecular profiles

- Inspect `mDataNames()`, `featureInfo()`, and `phenoInfo()`.
- Check assay metadata and compatibility.
- Match gene symbols and stable feature identifiers.
- Resolve duplicate features using a documented rule.
- Never interpret missing mutation calls as wild type.
- Use mutation definitions appropriate to the hypothesis.
- Check consistency of sample and cell-line identifiers.

### PRISM molecular-profile integration

For molecular biomarker analyses involving PRISM_2020:

- Check whether the required molecular profile is available
  within PRISM.
- If unavailable, read `references/prism-ccle.md`
  before excluding PRISM from the analysis.
- Use PRISM drug-response measurements with validated,
  matched CCLE molecular profiles.
- Preserve the exact molecular-data source and version.
- Distinguish shared molecular measurements from
  independent drug-response experiments.
- Do not count original and CCLE-augmented PRISM PSets
  as independent studies.

Follow the complete integration, matching, quality-control,
and reporting requirements in `references/prism-ccle.md`.

## Dataset-specific technical adjustments

### BeatAML

- Inspect FLT3-ITD annotations in `sampleInfo`.
- Add a derived mutation assay only when necessary.

### NCI60 / NCI-ALMANAC

- Check RNA-seq assay annotations.
- Correct incompatible metadata only after confirming
  the underlying measurement type.
- Validate gene identifier mappings.

### GDSC-matrix

- Inspect profile columns for incompatibilities
  before running association functions.
- Do not remove columns from the original object.

## Statistical analysis

- Define the biological hypothesis and eligible cohort.
- Match independent observations across data types.
- Choose statistical tests appropriate to marker type.
- Check marker and response variability.
- Verify sufficient complete-case observations.
- For categorical markers, check adequate group sizes.
- Report sample sizes and group counts.
- Specify multiple-testing correction and its scope.
- Preserve effect direction and measurement interpretation.

Successful sample matching does not establish statistical
eligibility. Do not report unreliable association estimates
when sample size or marker variation is insufficient.

## Cross-dataset comparison

For every relevant PSet, report:

- Dataset and version
- Drug or combination availability
- Molecular assay and feature
- Response or synergy measurement
- Sample and tissue restrictions
- Number of independent matched observations
- Statistical method, estimate and significance
- Reasons for exclusion, if applicable

Never treat an unavailable or unevaluable association
as a negative biological finding.

Distinguish reproducibility across drug-response experiments
from independent molecular-profile validation when multiple
datasets reuse the same molecular measurements.

## Validation

Before returning results:

- Verify identifier mappings and data alignment.
- Check measurement direction and units.
- Check for unintended duplicate observations.
- Compare computed summaries with available source data.
- Validate output structure and numerical values.
- Provide reproducible code and analytical provenance.

Never silently change the assay, metric, cohort, or
statistical method solely to obtain significance.

## Biological models and tissue-specific datasets

### Biological sample types

Do not assume that every PharmacoSet (PSet) contains
established cancer cell lines.

Identify the biological model used for drug screening
before performing analyses or generating plots.

Use the following classifications for canonical ORCESTRA
PSets:

**1. Established cancer cell lines**

- CCLE_2015
- CTRPv2_2015
- GDSC_2020(v1-8.2)
- GDSC_2020(v2-8.2)
- PRISM_2020
- gCSI_2019
- NCI60_2021
- FIMM_2016
- GRAY_2017
- UHNBreast_2019
- NCISarcoma_2015
- TCL38

**2. Primary patient samples screened ex vivo**

- BeatAML_2018: Primary AML cells obtained from patient
  blood or bone marrow.
- Tavor_2020: Primary AML cells obtained at diagnosis
  or relapse.

These are primary patient specimens, not established
or immortalized cell lines.

**3. Patient-derived xenograft cultures**

- PDTX_2019: Short-term cultures of breast cancer cells
  isolated from patient-derived tumor xenografts (PDTCs).

These are not established cell lines.

**4. Patient-derived GBM cell cultures**

- GBM_scr2: Patient-derived GBM cultures, Phase 2
  drug screen.
- GBM_scr3: Patient-derived GBM cultures, Phase 3
  drug screen.

Source: Johansson et al., Cell Reports (2020).
https://doi.org/10.1016/j.celrep.2020.107897

These datasets contain patient-derived glioblastoma
cell cultures from the Human Glioma Cell Culture
(HGCC) collection.

They are cultured cell models established from patient
tumors, not freshly isolated patient specimens.

Distinguish them from both conventional established
cancer cell-line panels and primary patient samples
screened ex vivo.

### Plotting requirements

When generating cross-dataset plots:

1. Distinguish established cancer cell lines from primary
   patient samples and other patient-derived experimental
   models using different colors.

2. Use distinct colors for each biological sample type,
   ensuring that established cell lines, primary patient
   samples, and patient-derived cultures are visually
   distinguishable.

3. Include a legend identifying the biological model types.

4. Keep the color mapping consistent across figures.

5. When dataset identity must also be displayed, use
   shapes, labels, or facets to distinguish PSets.

6. Do not label all samples as "cell lines" when
   patient-derived models are included.

### Analysis considerations

- Report the biological model type alongside each dataset.
- Do not combine established cell lines and patient-derived
  models without acknowledging their different experimental
  contexts.

### Tissue- and disease-specific datasets

Some canonical PSets contain samples from only one cancer
type or disease lineage.

Always consider these datasets automatically when performing
analyses relevant to that tissue or disease, even if their
tissue annotations are missing or use different terminology.

**Breast cancer**

- GRAY_2017
- UHNBreast_2019
- PDTX_2019

**Acute myeloid leukemia (AML)**

- BeatAML_2018
- Tavor_2020

**Glioblastoma (GBM; brain/CNS)**

- GBM_scr2
- GBM_scr3

**T-cell leukemia/lymphoma**

- TCL38

**Sarcoma**

- NCISarcoma_2015

**Multi-tissue datasets**

- CCLE_2015
- CTRPv2_2015
- GDSC_2020(v1-8.2)
- GDSC_2020(v2-8.2)
- PRISM_2020
- gCSI_2019
- FIMM_2016
- NCI60_2021

### Tissue-specific analysis requirements

1. When a user specifies a tissue or cancer type,
   automatically consider all relevant tissue- or
   disease-specific PSets alongside eligible samples
   from multi-tissue PSets.

2. Do not rely exclusively on exact matches in `tissueid`.
   Account for equivalent terminology and known dataset
   provenance (e.g., Breast/breast cancer, Brain/CNS/GBM,
   AML/Myeloid).

3. For datasets known to contain only one tissue or disease
   type, use that information to establish eligibility
   when tissue annotations are missing or inconsistent
   in naming. Do not override contradictory sample-level
   evidence without verification.

4. For multi-tissue PSets, filter samples using their tissue
   and disease annotations. Do not assume that all samples
   in these datasets are relevant.

5. Distinguish broad tissue categories from specific
   diagnoses. For example:

   - Include GBM_scr2 and GBM_scr3 in relevant brain/CNS
     cancer analyses, while recognizing that they
     specifically represent glioblastoma.

   - Include BeatAML_2018 and Tavor_2020 in AML analyses.

   - Include TCL38 in relevant T-cell malignancy or broader
     hematologic analyses, but not automatically in
     AML-specific analyses.

   - Include NCISarcoma_2015 in sarcoma analyses, while
     checking individual sarcoma subtypes when a specific
     histology is requested.

6. After identifying relevant datasets, verify drug
   availability, molecular measurements, sample counts,
   and other analysis-specific requirements before
   inclusion in the final analysis.

7. Preserve the biological sample-type classifications
   when combining datasets or generating plots.
