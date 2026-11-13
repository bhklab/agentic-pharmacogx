
# PRISM–CCLE Molecular Profile Integration

This reference was provided by Nikta on 2026-11-03. Its CCLE_2015 examples
are not a validated recipe for the updated CCLE object. For updated CCLE,
verify sample mapping through stable identifiers before transferring profiles.
Do not assume primary sample names match PRISM.

## 1. Background

PRISM_2020 contains drug-response measurements, but its
canonical PharmacoSet may lack integrated molecular profiles.

CCLE provides molecular characterization of many of the
same cancer cell lines.

For molecular biomarker questions involving PRISM,
CCLE molecular profiles can be combined with PRISM
drug-response measurements through validated cell-line
matching.

**Core principle:**

- Drug-response source: PRISM_2020
- Molecular-data source: CCLE, when required
- Unit of analysis: matched cell lines
- Resulting analysis: PRISM drug sensitivity associated
  with matched molecular measurements

The absence of molecular profiles in PRISM must not
automatically make PRISM ineligible for biomarker analysis.

## 2. Workflow

When analyzing a molecular biomarker using PRISM:

1. Load PRISM_2020 from the available canonical PSets.
2. Inspect its drug-response metrics and molecular-profile
   availability.
3. If the required molecular profile is missing, identify
   a suitable CCLE source.
4. Inspect the CCLE molecular assays and their feature
   annotations.
5. Harmonize sample identifiers using validated mappings.
6. Restrict the analysis to cell lines with both molecular
   and drug-response measurements.
7. Apply any requested tissue or disease restrictions.
8. Verify statistical eligibility.
9. Perform an appropriate PharmacoGx association analysis.
10. Report the molecular source, assay, sample coverage,
    and statistical results.

Do not substitute CCLE drug-response values for PRISM
measurements.


### Selection criteria

Select the molecular source based on:

- Validated sample overlap
- Availability of the requested assay
- Feature annotation quality
- Measurement technology and normalization
- Missingness and coverage
- Data version and provenance

Do not automatically prefer newer datasets solely based
on their publication year.

Do not automatically select the assay with the greatest
sample coverage if its measurement type or annotation
is unsuitable for the hypothesis.

If the initially selected source cannot be matched,
evaluate another suitable available CCLE source before
declaring the analysis unevaluable.

## 4. Molecular profiles

The following profiles were identified in the
CCLE_2015 integration workflow:

- `rna`
- `Kallisto_0.46.1.rnaseq`
- `mutation`
- `cnv`

Inspect actual assay availability before using these names.

### RNA-expression questions

- Prefer appropriately normalized, gene-level measurements.
- Check feature identifiers and gene-symbol annotations.
- Distinguish microarray expression from RNA-seq.
- Do not automatically select `rna` over RNA-seq because
  of its name.
- Do not combine values across expression platforms
  without justified harmonization.

### Mutation questions

- Inspect the representation of mutations.
- Distinguish gene-level mutation status from
  specific variants.
- For example, BRAF V600E must not be replaced with
  generic BRAF mutation status.
- Do not interpret missing mutation information as
  evidence of wild-type status.

### Copy-number questions

- Inspect whether values represent continuous copy
  number, relative copy number, or categorical
  alteration calls.
- Use a statistical model appropriate for the
  measurement.

## 5. Sample harmonization

Molecular-profile sample identifiers must map to
the PRISM sample identifiers used in drug-response
analysis.

For directly harmonized identifiers:

```r
prism_samples = rownames(prism@sample)

se = ccle@molecularProfiles[[profile]]

sample_ids = as.character(
  SummarizedExperiment::colData(se)$sampleid
)

keep = !is.na(sample_ids) &
       sample_ids %in% prism_samples

se = se[, keep, drop = FALSE]
```

This direct-matching example is appropriate only when
the identifiers are already harmonized.

If identifiers differ, construct a validated crosswalk
using available sample-curation metadata.

For CCLE_2019, inspect fields such as:

- Cellosaurus accession
- DepMap identifier
- CCLE sample identifier
- PRISM sample identifier

### Requirements

- Validate one-to-one biological sample mappings.
- Detect ambiguous or duplicate mappings.
- Preserve original source identifiers.
- Map molecular sample IDs to PRISM identifiers before
  integrating molecular profiles.
- Do not rely on fuzzy name matching without validation.
- Do not treat multiple molecular measurements from
  the same cell line as independent biological samples.

One-to-one mapping refers to unique biological sample
identities. Multiple technical measurements of the same
cell line may be retained when appropriately summarized.

## 6. Integration into PharmacoGx

Molecular profiles can be integrated into a temporary
copy of the PRISM PharmacoSet or matched directly
during analysis.

When constructing an augmented PSet:

```r
prism_updated = prism
```

Transfer only validated molecular profiles.

Preserve:

- PRISM sample annotations
- PRISM drug-response measurements
- PRISM drug annotations
- PRISM curation

Do not modify the canonical PRISM PSet unless
explicitly requested.

### Molecular-data provenance

Record molecular provenance using
SummarizedExperiment metadata.

At minimum, record:

```r
md = S4Vectors::metadata(se)

md$source_pset = source_pset
md$source_profile = profile

md$import_note =
  "Molecular profiles from CCLE; drug responses from PRISM."

S4Vectors::metadata(se) = md
```

Use the exact source PSet name and version rather than
the generic label "CCLE".

When possible, record original assay-level provenance,
including measurement platform and source release.

Preserve existing assay annotations when adding
provenance metadata.

## 7. Required quality control

Before performing association analysis, verify:

1. The requested molecular profile exists.
2. The requested molecular feature is available.
3. At least one sample is successfully matched.
4. Molecular features and samples have nonzero coverage.
5. All retained molecular sample IDs map to valid
   PRISM samples.
6. Mapping does not introduce ambiguous biological
   sample identities.
7. Drug-response measurements remain unchanged.
8. Sample and curation information remain unchanged.
9. The resulting PSet is structurally valid.

For augmented PSets, use checks such as:

```r
stopifnot(
  identical(prism_updated@sample, prism@sample),
  identical(
    prism_updated@treatmentResponse,
    prism@treatmentResponse
  ),
  identical(prism_updated@curation, prism@curation),
  isTRUE(validObject(prism_updated))
)
```

Also verify nonzero assay coverage and valid
sample matching.

Passing `validObject()` alone does not establish the
biological correctness of sample mappings.

### Statistical eligibility

Successful sample matching does not establish
statistical eligibility.

Before association testing:

- Verify sufficient complete-case observations.
- Check marker and response variability.
- For categorical biomarkers, verify adequate
  group sizes.
- Determine the number of independent biological
  samples after accounting for repeated measurements.
- Apply a sample-size threshold appropriate for
  the statistical method and research question.

Do not perform or report unreliable association
estimates when the number of observations or marker
variation is insufficient.

If integration cannot be validated, report PRISM as
unevaluable for that biomarker rather than silently
forcing a match.

## 8. Association analysis

Use the requested PRISM drug-response measurement
and the selected molecular assay.

For each analysis:

- Select the appropriate response metric.
- Verify the direction of drug sensitivity.
- Match molecular and response measurements.
- Apply tissue restrictions before association testing.
- Aggregate repeated measurements appropriately.
- Use the correct independent observation count.
- Run a suitable association model using PharmacoGx.
- Report effect sizes, significance, and sample coverage.

When using `drugSensitivitySig()`, verify that the
supplied matrices, molecular assay, response metric,
and sensitivity orientation are consistent.

Do not infer association significance or direction
without executing the analysis.

## 9. Cross-dataset interpretation

PRISM and CCLE may contain different drug-response
experiments on overlapping cell lines.

When the same CCLE molecular measurements are used
for both PRISM and CCLE drug-response analyses:

- They can provide evidence of reproducibility
  across drug-screening experiments.
- They do not constitute independent molecular-profile
  validation.
- Do not present the molecular measurements as
  independently generated in each dataset.
- Do not count original PRISM and CCLE-augmented
  PRISM as separate studies.
- Do not count the same PRISM experiment twice.

For cross-dataset summaries, distinguish:

- Independent drug-response experiments
- Independent molecular profiling
- Shared biological samples

Keep PSet-specific association results separate unless
an explicit cross-dataset harmonization or meta-analysis
is requested.

## 10. Reporting requirements

For every PRISM biomarker analysis, report:

- Response dataset: PRISM_2020
- Molecular source: exact PSet and version
  (PRISM-native or external CCLE, as applicable)
- Molecular profile name and measurement technology
- Gene or molecular feature identifier
- Drug and response metric
- Tissue or disease restriction
- Number of matched independent cell lines
- Association method
- Effect size and p-value
- Confidence interval when applicable
- Direction and biological interpretation
- Sample-mapping limitations
- Reproducible analysis code

### Example provenance statement

When CCLE_2015 is the molecular source:

"Drug-response measurements were obtained from
PRISM_2020 and gene-expression measurements from
CCLE_2015. The association was evaluated in cell
lines with matched molecular and drug-response data."

Adapt this statement to the actual molecular source,
assay, and version used.

## 11. Important restrictions

Never:

- Interpret missing PRISM molecular profiles as absence
  of the biological marker.
- Assume CCLE and PRISM identifiers are directly
  interchangeable.
- Replace PRISM drug responses with CCLE responses.
- Pool molecular measurements from different platforms
  without justification.
- Count original and augmented PRISM PSets as
  independent studies.
- Claim independent molecular validation when the
  molecular measurements are shared.
- Modify or overwrite canonical PSets without
  authorization.

If integration cannot be validated, explain the
limitation and exclude the analysis.
