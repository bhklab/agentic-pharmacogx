---
name: data-retrieval
description: >-
  Retrieve and audit molecular, sample, monotherapy, dose-level and combination
  response data from existing PharmacoGx/CoreGx PharmacoSet (PSet) objects.
  Use for any question involving ORCESTRA PSets after a separate skill has
  downloaded/loaded the object. Enforce exact assay/metric/identifier selection,
  experimental-unit matching, version checks, provenance and coverage QC before
  handing data to downstream PharmacoGx analyses.
---

# PharmacoGx data retrieval skill

**Audience:** an R-capable research agent analyzing pharmacogenomic datasets.
**Updated:** 2026-11-13 (integrated user-requested retrieval defaults and fixes).
**Primary task:** locate and retrieve the *correct pre-existing measurement* from
an already loaded `PharmacoSet`, verify it, and return analysis-ready data without
silently changing the scientific question.

## 0. Authority, environment, and non-negotiable rules

### 0.1 Target environment

The intended installations are:

```r
remotes::install_github(
  "bhklab/CoreGx@f760bc7c230f892722d72634001054adad2ea0f0",
  upgrade = "never"
)
remotes::install_github(
  "bhklab/PharmacoGx@a7aa4d727e521ab63f68f2dbfc16697e5e4764cc",
  upgrade = "never"
)
```

The project identifies its PharmacoGx version as **3.14.1**. Do **not** replace
these pins with current Bioconductor release or GitHub `devel` while following
this skill. The user's supplied Bioconductor 3.23 manual is for **PharmacoGx
3.16.0**, *not* the pinned 3.14.1 build. A closer historical public manual is
Bioconductor 3.22 / PharmacoGx **3.14.0**. Documentation describes an API, but
**the actually installed, pinned methods are the ultimate authority**.

```r
library(PharmacoGx)
library(CoreGx)
library(SummarizedExperiment)
library(S4Vectors)
library(data.table)

print(packageVersion("PharmacoGx"))
print(packageVersion("CoreGx"))
print(utils::packageDescription("PharmacoGx")$RemoteSha)  # may be NULL
print(utils::packageDescription("CoreGx")$RemoteSha)      # may be NULL
sessionInfo()
```

If the requested behavior is not documented or obviously version-dependent,
verify at run time, e.g. `args(PharmacoGx::summarizeSensitivityProfiles)`,
`methods("drugSensitivitySig")`,
`methods::getMethod("drugSensitivitySig", "PharmacoSet")`, or
`?PharmacoGx::drugSensitivitySig`. Do not assert that an argument is supported
just because a newer manual or one case-study script uses it. When the R
runtime or specific PSet is unavailable, mark the code **illustrative / not
executed** rather than claiming that the code or results were validated.

### 0.2 Scope boundary

- **IN SCOPE:** inspect a loaded PSet; discover response and molecular assays;
  retrieve stored metrics or raw measurements; subset; identify drug, sample,
  gene and study provenance; match experiments; construct correct input matrices
  for *explicitly requested* downstream PharmacoGx methods; report QC.
- **OUT OF SCOPE:** discovering/downloading PSets from ORCESTRA, modifying
  ORCESTRA, rebuilding PSets, or inventing missing assays. A separate agent skill
  already handles downloading and loading. The object may be loaded by `readRDS`
  or (when legitimately supplied in that format) `qs::qread`.
- **DEFAULT:** retrieval, **not recalculation**. Never refit dose-response
  curves, reconstruct Bliss/HSA/ZIP, recompute stored AUC/AAC, or recreate a
  metric merely to answer a question about a stored measurement.
- **DERIVATION ONLY WHEN REQUESTED:** use `computeAUC()`, `computeBliss()`,
  `computeHSA()`, `computeZIP()`, `computeLoewe()`, `computeZIPdelta()`,
  `estimateProjParams()`, and `drugSensitivitySig()` only when the user has
  explicitly requested a new calculated analysis (or the task unambiguously
  requires a non-stored result), with inputs and scales verified.
- **DO NOT MUTATE SOURCE DATA:** never modify a canonical PSet in place to make
  an analysis work; create a named temporary copy and document the exact patch.
- **DO NOT SILENTLY FALL BACK:** if a specifically requested metric is absent,
  say it is absent. Do not replace it with a different metric, assay, biological
  model, cutoff, tissue, screen, or synergy model without saying so.
- **DEFAULT UNSPECIFIED MONOTHERAPY SENSITIVITY:** select stored
  `aac_recomputed` if usable for the requested drug/sample cohort. If not,
  select a valid stored IC50 metric (prefer `ic50_recomputed` when suitable).
  Never select `aa_recomputed`: that was a typo, not an approved metric.
  Report the exact automatically selected metric and its sensitivity direction
  in the answer. See Section 5.2.1.
- **DEFAULT BLISS SYNERGY:** prefer *observed* stored Bliss (`*_obs`) rather
  than `*_fit`; do not silently substitute fitted Bliss if observed Bliss is
  unavailable. For unsuffixed columns (e.g., `Bliss_score`), verify that the
  stored measurement is observed before treating it as such. See 7.2.1.
- **CCLE MOLECULAR FALLBACK:** for any cell-line PSet with no suitable
  molecular assay, gene feature, or coverage for the cell lines of interest,
  check available CCLE PSets for a verified biological match. Keep response
  values from the originally requested PSet, document both sources, and do
  not use CCLE for unverified patient/organoid identities. See Section 9.
- **ERRORS ARE DATA:** do not turn `sensitivityMeasures()` errors into an
  unexplained empty metric list. Inspect the exception; for the specifically
  reported GDSC Matrix `matrix_completeness` error, apply Section 10.2 on
  the working in-memory object and retry.

### 0.3 Source hierarchy and evidence labels

1. **Installed package function, S4 method, and loaded PSet inspection**:
   authoritative for an actual run.
2. **Pinned GitHub commits** (above): intended source for exact code.
3. **PharmacoGx 3.14.0 reference manual**: close published baseline; not proof
   of 3.14.1-specific behavior.
4. **User-supplied Bioconductor 3.16.0 reference manual**: secondary reference.
5. **User-supplied scripts**: demonstrated analysis conventions, *not* a
   guarantee that a helper is exported or that a local patch is universally
   necessary. The scripts contain exploratory TODOs and historical examples.

Use these evidence labels in notes: `PACKAGE_API`, `PSET_INSPECTED`,
`SCRIPT_PATTERN`, `EXTERNAL_ANNOTATION`, `DERIVED`, `UNVERIFIED`.

### 0.4 Mandatory decision sequence

For **every** user question involving PSet data:

1. Parse requested **PSet(s), drugs, sample(s), tissue, molecular feature,
   metric, dose granularity, experimental context**, and desired output.
2. Inspect each loaded PSet **before** choosing functions or column names.
3. Decide **stored summary vs stored raw vs genuinely new computation**.
4. Resolve identifiers **without guessing**; record exact matches and aliases.
5. Pick the exact assay and metric from **actual** inventory: honor an
   explicitly named metric; otherwise follow the required `aac_recomputed`
   → valid stored IC50 rule for monotherapy sensitivity (Section 5.2.1), or
   observed → never silently fitted for Bliss (Section 7.2.1).
6. Filter sample/drug/experiment keys, preserving orientation and provenance.
   If a required molecular measurement is missing, check the CCLE fallback
   eligibility and validated cell-line overlap before concluding it is absent.
7. Define the **biological unit** (cell line, patient, organoid, independent
   culture) and the **technical unit** (plate, replicate, dose combination).
8. Check missingness, duplicates, dose/measurement scales, and matched N.
9. Return the requested data/summary, with R code and a retrieval manifest.
10. Only then hand off the validated data to an analysis function when needed.

Do not perform step 10 while steps 2–8 remain unresolved.

---

## 1. Function selection: explicit decision table

| User requests | Primary function / accessor | Inspect or specify | Do **not** do by default |
|---|---|---|---|
| Which PSets or assays are loaded? | `class()`, `dim()`, `mDataNames()`, `treatmentResponse()`, `assays()` | PSet name/version; actual assay names | Assume fixed ORCESTRA schema |
| Samples, tissue, patient fields | `sampleInfo()`, `sampleNames()` | `sampleid`, `tissueid`, source/patient IDs | Treat missing tissue as a negative diagnosis |
| Drugs and identifiers | `treatmentInfo()`, `treatmentNames()` or available `drugNames()`, `curation()` | exact ID/alias and treatment orientation | Fuzzy-match names and assume identity |
| Molecular assay inventory | `mDataNames()`, `molecularProfilesSlot()` | assay metadata and measurement technology | Assume `rna` exists or means RNA-seq |
| Gene feature mapping | `featureInfo()`, `fNames()` | Ensembl/gene symbol/variant IDs | Assume gene symbols equal matrix rownames |
| Molecular values | `molecularProfiles()`, `phenoInfo()` | feature × molecular column, biological `sampleid` | Assume columns are unique cell lines |
| Available sensitivity metrics | `sensitivityMeasures()`, `sensitivityProfiles()`, `treatmentResponse()` | actual assay and column names; diagnose errors | Assume a metric name implies its scale or silence errors |
| Unspecified monotherapy sensitivity | Inspect stored profiles, then `aac_recomputed` → validated stored IC50 | exact selected column; usable N; response direction | Choose AUC, `aa_recomputed`, or recalculate a metric by guesswork |
| Unspecified Bliss synergy | Inspect stored response assay; observed `*_obs` preferred | whether observed/fit; `Bliss_score` only if provenance verifies observed | Choose `Bliss_*_fit` merely because available |
| Missing molecular data in a cell-line PSet | `mDataNames()`, `molecularProfiles()`, `featureInfo()`, `phenoInfo()` on native PSet **then CCLE** | proven sample crosswalk and feature identity, CCLE source/version | Treat all CCLE samples as matching by name or substitute CCLE drug response |
| Monotherapy metric matrix | `summarizeSensitivityProfiles()` when schema compatible | `profiles_assay`, `treatment_col`, `sample_col`, summary rule | Refit a curve |
| One stored monotherapy experiment | `treatmentResponse()` + assay extraction / `sensitivityProfiles()` | exact drug and sample, repetitions | Replace stored AAC with AUC |
| Raw monotherapy dose measurements | `treatmentResponse()` + correct `raw` assay; legacy `sensitivityRaw()` | concentration, viability, replicate, units | Infer missing doses |
| Drug pair synergy (summarized) | `treatmentResponse()` + `profiles` or other actual summary assay | stored Bliss/HSA/ZIP column, aggregation level | Reconstruct synergy from monotherapy |
| Drug pair synergy at dose level | `treatmentResponse()` + `synergy` / `combo_viability` assay | both doses, sample, model score, replicates | Treat doses as biological samples |
| Subset a whole monotherapy PSet | `subsetTo()` on a copy, **after verifying semantics** | `cells`, `drugs`, `molecular.data.cells` | Use blindly for oriented combinations |
| Summarize repeated molecular profiles | `summarizeMolecularProfiles()` when appropriate | datatype, feature, repeat policy | Average mutation strings or pooled platforms |
| Association after retrieval | `drugSensitivitySig()` | `sProfiles`, `mProfiles`, orientation and matched cells | Use a score without checking its meaning |
| Compare across PSets | Repeat retrieval **independently** in each PSet | dataset-specific metric mappings and units | Pool non-equivalent measurements |

`data.table`, `dplyr`, and base R can filter, join, pivot, or summarize **data
already extracted using the package accessors**. They are not substitutes for
package discovery, and a manual aggregation is not itself a PharmacoGx
function. `SummarizedExperiment::assay()` / `assays()` and
`S4Vectors::metadata()` are Bioconductor functions, not PharmacoGx functions.

---

## 2. The PSet: what is actually stored

### 2.1 Conceptual anatomy

A `PharmacoSet` commonly contains:

- **Sample metadata:** `sampleInfo(p)`; potentially sample ID, tissue/disease,
  identifiers, patient mapping, model type, batch, treatment history.
- **Treatment metadata:** `treatmentInfo(p)`, treatment names and curation.
- **Molecular profiles:** one or more `SummarizedExperiment` objects;
  `mDataNames(p)` gives molecular data types; `molecularProfiles(p, type)`
  gives a **feature × molecular-measurement** matrix, `featureInfo(p, type)`
  feature metadata, `phenoInfo(p, type)` its molecular-column metadata.
- **Treatment response:** `treatmentResponse(p)` can expose multiple named
  assays with experiment-level keys and measured/derived response columns.
- **Legacy sensitivity views:** `sensitivityProfiles(p)`,
  `sensitivityRaw(p)`, `sensitivityMeasures(p)` where supported.
- **Curation/provenance:** `curation(p)`, `annotation(p)`, plus metadata
  attached to individual assays.

**Critical:** PSet objects are not guaranteed to have the same assays, the
same matrix layout, the same identifiers, or the same meaning of a column.
Some objects use a `TreatmentResponseExperiment` (TRE), a `LongTable`, or
another package-compatible response layout. Interrogate the object, not a
schema remembered from another dataset.

### 2.2 Minimal preflight (run on every PSet)

```r
library(PharmacoGx)
library(CoreGx)
library(data.table)
library(SummarizedExperiment)

# `p` is a previously loaded PharmacoSet; PSet download is handled elsewhere.
stopifnot(methods::is(p, "PharmacoSet"))

cat("PSet class:", paste(class(p), collapse = ", "), "\n")
print(dim(p))
print(tryCatch(PharmacoGx::name(p), error = function(e) NA_character_))
print(tryCatch(PharmacoGx::datasetType(p), error = function(e) NA_character_))

samples <- as.data.table(PharmacoGx::sampleInfo(p))
print(names(samples))
print(head(samples, 3))

print(tryCatch(PharmacoGx::sampleNames(p), error = function(e) NULL))
print(tryCatch(PharmacoGx::mDataNames(p), error = function(e) NULL))
print(tryCatch(
  PharmacoGx::sensitivityMeasures(p),
  error = function(e) {
    message("sensitivityMeasures() ERROR (not an empty metric list): ",
            conditionMessage(e))
    message("For GDSC Matrix character matrix_completeness: see Section 10.2")
    NULL
  }
))

tr <- PharmacoGx::treatmentResponse(p)
cat("Treatment response class:", paste(class(tr), collapse = ", "), "\n")
print(tryCatch(names(SummarizedExperiment::assays(tr)),
               error = function(e) NULL))
print(tryCatch(names(tr), error = function(e) NULL))
```

Some introspection calls are **optional diagnostics**. A failure to print
legacy `sensitivityMeasures` does not mean the treatment response is empty.
Avoid printing huge raw matrices. Inspect `names()`, `dim()`, `head()`, and
small keyed subsets first.

### 2.3 Safe assay retrieval helper

The following helper is **local R code**, not an exported PharmacoGx
function. It tries the two extraction styles demonstrated in the scripts and
**stops** if neither applies. It does not rewrite the PSet.

```r
pgx_get_response_assay <- function(p, assay_name) {
  tr <- PharmacoGx::treatmentResponse(p)
  x <- tryCatch(tr[[assay_name]], error = function(e) NULL)
  if (is.null(x)) {
    x <- tryCatch(SummarizedExperiment::assay(tr, assay_name),
                  error = function(e) NULL)
  }
  if (is.null(x)) {
    stop("Assay '", assay_name, "' not retrievable in this PSet; ",
         "inspect treatmentResponse() and assays() first")
  }
  data.table::copy(data.table::as.data.table(x))
}

# Always print these before choosing a metric:
# x <- pgx_get_response_assay(p, "profiles")
# names(x); head(x); unique(x$treatment1id)
```

**Assay names are dataset-specific.** `profiles`, `mono_profiles`, `raw`,
`synergy`, and `combo_viability` are **observed examples**, not a required
set. If the getter is unsuccessful, inspect the TRE's method dispatch and the
S4 structure. Direct `@slot` access is a read-only diagnostic fallback,
not the default interface.

### 2.4 Compact PSet inventory

```r
pgx_inventory <- function(p) {
  stopifnot(methods::is(p, "PharmacoSet"))
  tr <- PharmacoGx::treatmentResponse(p)
  a <- tryCatch(names(SummarizedExperiment::assays(tr)),
                error = function(e) character())
  if (!length(a)) a <- tryCatch(names(tr), error = function(e) character())
  a <- unique(a[!is.na(a) & nzchar(a)])

  # Inspect only the assay metadata here: do not copy huge dose-level tables.
  assays <- lapply(a, function(nm) {
    x <- tryCatch(tr[[nm]], error = function(e) NULL)
    if (is.null(x)) x <- tryCatch(
      SummarizedExperiment::assay(tr, nm), error = function(e) NULL)
    if (is.null(x)) return(data.table::data.table(
      assay = nm, nrows = NA_integer_, columns = "NOT ACCESSIBLE"))
    data.table::data.table(assay = nm, nrows = nrow(x),
                           columns = paste(colnames(x), collapse = "; "))
  })
  list(
    sample_columns = names(PharmacoGx::sampleInfo(p)),
    molecular_assays = PharmacoGx::mDataNames(p),
    sensitivity_measures = tryCatch(
      PharmacoGx::sensitivityMeasures(p),
      error = function(e) {
        message("sensitivityMeasures() failed: ", conditionMessage(e),
                " (see Section 10.2 for GDSC Matrix)")
        NULL
      }),
    response_assays = data.table::rbindlist(assays, fill = TRUE)
  )
}

# inv <- pgx_inventory(p)
# print(inv$response_assays)
```

The inventory returns **observed columns only**, not an ontology of which
column should be used. If a TRE exposes a huge number of assays, inventory
only likely relevant ones to avoid memory pressure.

---

## 3. Resolve sample identity and biological models first

### 3.1 Sample metadata: `sampleInfo()`, `sampleNames()`

```r
si <- data.table::as.data.table(PharmacoGx::sampleInfo(p))
stopifnot("sampleid" %in% names(si))  # else inspect its actual identifier fields
si[, sampleid := as.character(sampleid)]

# Only apply this filter when tissueid exists and its coding has been inspected.
if ("tissueid" %in% names(si)) {
  print(si[, .N, by = tissueid][order(-N)])
}
```

`sampleNames(p)` reflects IDs stored in the PSet, not necessarily the
clinical **patient** count. Different samples from one patient may be
biologically non-independent. Ex vivo primary-sample screens and established
cell-line screens must not be labeled identically.

### 3.2 Tissue/disease restrictions

1. Check exact `tissueid`, histology, disease and project fields. A request
   for *colorectal cancer* should not be implemented as a blind `tissueid ==
   "Bowel"` test without confirming that those entries are the intended cohort.
2. Use source-supported mappings for synonyms (e.g., colorectal/colon/bowel);
   log every mapping, do not silently apply broad regexes.
3. Where a PSet is known from **verified provenance** to be disease-specific,
   consider it even if `tissueid` is missing; validate against sample annotations.
4. Separate tissue-matched from molecular-matched and response-matched counts.

The user's dataset inventory groups models into established cell lines,
primary patient samples, patient-derived xenograft cultures and patient-derived
GBM cultures. In particular, **BeatAML_2018 and Tavor_2020 are primary AML
specimens**, while **PDTX_2019** represents patient-derived xenograft-derived
cultures. **GBM_scr2 / GBM_scr3** are patient-derived glioblastoma cultures.
These descriptions are supplied project metadata; verify actual study labels
in the relevant loaded PSets before using them for inclusion/exclusion.

Relevant single-disease datasets to consider alongside multi-tissue PSets:

| Indication | User-supplied candidate PSets | QC before use |
|---|---|---|
| Breast | `GRAY_2017`, `UHNBreast_2019`, `PDTX_2019` | model type; histology; drug availability |
| AML | `BeatAML_2018`, `Tavor_2020` | patient independence; disease status |
| GBM | `GBM_scr2`, `GBM_scr3` | derived-culture identity and assay names |
| T-cell malignancy | `TCL38` | exact malignancy; **not** automatically AML |
| Sarcoma | `NCISarcoma_2015` | sarcoma subtype |

Multi-tissue examples include CCLE, CTRPv2, GDSC, PRISM, gCSI, FIMM and NCI60.
Never omit a disease-specific candidate solely because it was not returned by
an exact match on its `tissueid` string.

### 3.3 IDs must be joined on a **validated identity**

- `sampleid`: canonical PSet treatment-response sample, when present.
- `cellid`: may denote a biological cell line in molecular column metadata.
- `PatientId` or equivalent: may define a stronger independence unit.
- Molecular **column name**: may represent a measurement or replicate, not a
  unique cell line; use `phenoInfo()` to establish its biological identity.
- COSMIC / DepMap / Cellosaurus IDs: mapping keys, **not** assumed equal to
  a PSet's `sampleid`.

For two tables, do not merge until you have checked duplicate keys:

```r
stopifnot("sampleid" %in% names(response_dt),
          "sampleid" %in% names(marker_dt))

print(response_dt[, .N, by = sampleid][N > 1L])
print(marker_dt[, .N, by = sampleid][N > 1L])

# Aggregate only after determining WHY duplicates exist and selecting a
# biologically justified rule, *then* join using sampleid.
```

---

## 4. Resolve treatments, drug aliases, and pair orientation

### 4.1 Inspect actual treatments and curation

```r
print(head(PharmacoGx::treatmentInfo(p)))
print(tryCatch(head(PharmacoGx::treatmentNames(p)),
               error = function(e) NULL))
print(tryCatch(head(PharmacoGx::drugNames(p)),
               error = function(e) NULL))
print(names(PharmacoGx::curation(p)))
```

Historical PharmacoGx manuals describe `drugNames()` and modern interfaces
may expose `treatmentNames()`; inspect what is exported by the installed
package rather than requiring both. Curation keys may be `drug`, `treatment`
or something else. Do not hard-code the curation table name.

**Resolution algorithm**:

1. Try exact treatment ID from assay records.
2. If absent, consult validated treatment curation / synonym fields.
3. If several IDs map to one name, determine whether they are distinct
   formulations, salts, exposures or duplicate aliases; **do not choose the
   first**.
4. Record `{requested_name, matched_treatmentid, alias_source}`.
5. For drug combinations, retain **original `treatment1id`, `treatment2id`**
   and dose orientation even if also constructing an unordered comparison key.

### 4.2 Pair retrieval (orientation-invariant *selection*)

```r
# `x` must already be a response assay with these columns.
required <- c("sampleid", "treatment1id", "treatment2id")
stopifnot(all(required %in% names(x)))

drug_a <- "AZD5991"
drug_b <- "Venetoclax"

pair <- x[
  (treatment1id == drug_a & treatment2id == drug_b) |
  (treatment1id == drug_b & treatment2id == drug_a)
]
stopifnot(nrow(pair) > 0L)

# Keep original orientation for per-drug doses and 1/2-specific metrics:
print(unique(pair[, .(treatment1id, treatment2id)]))
```

For comparing combinations across datasets, use an **unordered standardized
pair key only after validating each drug's mapping**:

```r
# Do NOT use this simple normalization to establish a drug's identity.
# This is a grouping key AFTER identity has already been verified.
valid_pairs <- pair[!is.na(treatment1id) & !is.na(treatment2id)]
valid_pairs[, `:=`(drug_A = pmin(treatment1id, treatment2id),
                  drug_B = pmax(treatment1id, treatment2id))]
```

Ordering-free keys must never swap `aac_recomputed_1` and `_2`, potency,
`treatment1dose` and `treatment2dose`, or monotherapy references without also
reorienting the associated values.

---

## 5. Monotherapy: retrieve stored measurements first

### 5.1 Discover actual measures and source assays

```r
sm <- tryCatch(
  PharmacoGx::sensitivityMeasures(p),
  error = function(e) {
    message("sensitivityMeasures() failed: ", conditionMessage(e))
    message("If this is the GDSC Matrix matrix_completeness error, ",
            "apply the exact Section 10.2 workaround and retry")
    NULL
  }
)
print(sm)

sp <- tryCatch(data.table::as.data.table(
  PharmacoGx::sensitivityProfiles(p)),
  error = function(e) NULL)
if (!is.null(sp)) {
  print(names(sp))
  print(head(sp, 3))
}

# Independently inspect the TRE `profiles` and, if present, `mono_profiles`:
# names(pgx_get_response_assay(p, "profiles"))
# names(pgx_get_response_assay(p, "mono_profiles"))
```

**Key distinction:** `sensitivityMeasures()` is a useful index but can fail
to enumerate all custom score columns, especially in modified combination
PSets. Inspect the actual `treatmentResponse()` assays too. Do not interpret
missing **from one accessor** as absent **from the whole PSet**.

### 5.2 Metric selection is scientific, not alphabetical

Examples of *observed* fields in the scripts:

| Family | Example column(s) | What must be verified |
|---|---|---|
| AUC | `auc_published`, `auc_recomputed` | area definition; normalization; lower/higher sensitivity |
| AAC | `aac_recomputed`, `aac_recomputed_1`, `_2` | area above viability curve; components and scale |
| Potency | `ic50_recomputed`, `ic50_recomputed_1`, `combo_ic50_observed` | concentration units, fit status, on/off-range |
| Shape / efficacy | `HS_1`, `EC50_1`, `E_inf_1` | orientation; parameter units; fit quality |
| Other | `auc_ptc`, `ic50_reached`, `n_dose1` | project-specific definitions |

**Never encode a universal rule such as “all AUC columns increase with
resistance.”** The PharmacoGx `computeAUC()` manual describes an inhibition /
response-area AUC whose **higher value implies higher sensitivity**; other
stored, published, or custom AUC implementations can use the opposite
convention. Inspect the actual definition and data provenance. Similarly,
AAC usually denotes activity area, but verify rather than assume a scale.
Do not multiply by 100, invert, negate, standardize, or mix metrics without
an explicit scientific reason.

### 5.2.1 MANDATORY default when sensitivity/resistance is asked without a metric

This is an **agent decision rule**, not a claim that PharmacoGx defines a
universal default. For questions like “Which models are most sensitive to
Gemcitabine?”, “Compare drug sensitivity across tissues”, or “Find a gene
associated with response”, when the user **has not specified a response
metric**, proceed as follows:

1. **Explicit request overrides this section.** If the user says AUC, AAC,
   IC50, or another measure, retrieve that precise requested measure or
   explain its absence. Do not substitute by default.
2. **First choice: stored `aac_recomputed`.** Check the *actual* monotherapy
   response assay, and confirm that it is available and has finite values for
   the requested drug and eligible samples. Prefer it over IC50 when both
   are usable. This rule does **not** designate `aac_recomputed_1` from a
   combination record as generic monotherapy response; investigate its
   orientation and context first.
3. **Fallback: a suitable stored IC50.** If `aac_recomputed` is absent or
   entirely unusable for the requested drug/cohort, inspect `ic50_recomputed`
   first, then other genuine, documented **stored** monotherapy IC50 columns
   when necessary. Check concentration units, transformations, upper/lower
   bounds, fit success, and finite coverage. Do not mistake a missing or
   out-of-range IC50 for measured resistance.
4. **Do not use `aa_recomputed`.** It was a spelling error in the drafting
   discussion. Do not silently substitute `auc_recomputed` or a fitted
   synergy/combination IC50 as another fallback. If neither AAC nor a valid
   stored IC50 is available, explain the available metrics and limitation;
   request a metric choice only if needed for further analysis.
5. **Tell the user the exact choice every time.** Include the PSet, assay,
   exact column name, direction of sensitivity, matched sample count, and
   whether this was a default choice. For a usual activity-area AAC, higher
   values indicate greater activity/sensitivity; for **untransformed IC50**,
   lower concentrations indicate greater potency/sensitivity. Confirm the
   precise dataset-specific convention before stating a ranking.
6. **Across PSets**, apply this rule independently and disclose when one
   dataset uses AAC and another uses IC50. Do not pool raw AAC and IC50
   values into one numerical sensitivity ranking or treat these as equivalent
   outcomes for a meta-analysis.

Example: inspect the **already selected and monotherapy-filtered** rows
(`mono_rows`, including the requested drug/cohort) *after retrieving them*
with the accessors in Sections 5.1 and 5.3–5.4:

```r
# Local selection helper, NOT a PharmacoGx export. Select a stored measure;
# never calculate AAC or IC50. `mono_rows` must contain only the requested
# eligible monotherapy records, with sample and treatment identities verified.
select_default_sensitivity_metric <- function(mono_rows) {
  for (nm in c("aac_recomputed", "ic50_recomputed",
               "ic50_published", "ic50")) {
    if (!nm %in% names(mono_rows)) next
    v <- mono_rows[[nm]]
    if (is.numeric(v) && any(is.finite(v))) {
      return(list(column = nm,
                  default_used = TRUE,
                  family = if (nm == "aac_recomputed") "AAC" else "IC50"))
    }
  }
  stop("Neither usable stored aac_recomputed nor suitable IC50 is present; ",
       "inspect available metrics and report the limitation")
}

# metric_choice <- select_default_sensitivity_metric(mono_rows)
# message("Default metric: ", metric_choice$column)
# Then extract ONLY that named, stored column; validate metric-specific units.
```

**Required final-answer language (adapt exact names):** “No sensitivity
metric was specified, so I used the stored `aac_recomputed` metric from
`profiles` in [PSet]. Higher AAC indicates greater sensitivity under this
PSet's verified definition (N = ... eligible cell lines).” If IC50 was
selected instead, explicitly say it was the fallback **because a usable
`aac_recomputed` was unavailable**, and explain the IC50 direction.

### 5.3 Preferred package function for a sample × drug matrix

`PharmacoGx::summarizeSensitivityProfiles()` is designed to summarize
stored response profiles into a **cell lines in rows × treatments in columns**
matrix. Key arguments in the 3.14.0 manual:

- `object`: the PSet.
- `sensitivity.measure`: exact stored metric column.
- `cell.lines`: requested sample IDs (use actual PSet IDs).
- `drugs`: requested treatment IDs.
- `profiles_assay`: actual assay name (default `"profiles"`).
- `treatment_col`, `sample_col`: actual column names (documented defaults
  `"treatmentid"`, `"sampleid"`; some PSets use `"treatment1id"`).
- `summary.stat`: `"mean"`, `"median"`, `"first"`, `"last"`, `"max"`, `"min"`.
- `fill.missing`: whether to fill missing combinations as NA.

```r
# EXAMPLE: only after inspecting `profiles` and confirming these columns.
profiles <- pgx_get_response_assay(p, "profiles")
stopifnot(all(c("sampleid", "treatment1id", "aac_recomputed") %in%
              names(profiles)))

my_drug <- "Gemcitabine"  # substitute a confirmed exact ID
my_cells <- unique(as.character(profiles$sampleid))

# Conservative stop: this method must not accidentally include drug pairs.
# If present, inspect a monotherapy-specific assay or use explicit records.
if ("treatment2id" %in% names(profiles)) {
  mixed <- profiles[treatment1id == my_drug &
    !is.na(treatment2id) & nzchar(trimws(as.character(treatment2id)))]
  if (nrow(mixed)) stop("Mixed mono/combo profiles: select monotherapy explicitly")
}

m <- PharmacoGx::summarizeSensitivityProfiles(
  object = p,
  sensitivity.measure = "aac_recomputed",
  cell.lines = my_cells,
  drugs = my_drug,
  profiles_assay = "profiles",
  treatment_col = "treatment1id",
  sample_col = "sampleid",
  summary.stat = "median",
  fill.missing = TRUE,
  verbose = FALSE
)

# Documented orientation: cell lines ROWS, treatments COLUMNS.
stopifnot(is.matrix(m), my_drug %in% colnames(m))
response <- data.table::data.table(
  sampleid = rownames(m), treatmentid = my_drug,
  metric = "aac_recomputed", value = as.numeric(m[, my_drug])
)
```

**Before this call:** verify rows represent **monotherapy** for the intended
metric; do not select combinations because `treatment1id == my_drug` while
`treatment2id` is another active drug. Verify the assay's treatment column
captures monotherapy IDs. If an assay cannot be unambiguously treated as a
one-treatment profile, retrieve and filter the records explicitly instead.

### 5.4 Explicit record extraction when summary function does not fit

```r
# `profiles` is a copy extracted with pgx_get_response_assay().
# Adapt the schema after checking names(profiles), never before.
required <- c("sampleid", "treatment1id", "aac_recomputed")
stopifnot(all(required %in% names(profiles)))

mono <- profiles[treatment1id == my_drug,
  .(sampleid, treatment1id, aac_recomputed)]
mono <- mono[is.finite(aac_recomputed) & !is.na(sampleid)]

# If `treatment2id` is present, verify whether NA/blank represents a true
# monotherapy or whether this assay stores combo components differently.
# Inspect duplicate experiments BEFORE collapsing them:
print(mono[, .N, by = .(sampleid, treatment1id)][N > 1])
```

For a user request such as “which samples have the strongest sensitivity to
Gemcitabine?”, define metric direction first; rank **stored** values, keeping
PSet, metric, dose range, and cohort as provenance. Do not run curve fitting.

### 5.5 Missing data versus measured inactivity

- **Drug absent:** no verified treatment ID.
- **Assay absent:** specific stored assay missing.
- **Metric absent:** exact requested column missing.
- **No matched sample:** drug and sample exist separately but not together.
- **Metric NA/nonfinite:** experiment exists but measurement unusable.
- **Measured no response:** a finite measurement indicating low activity.

These have different meanings. Never replace the first five with “resistant”.

---

## 6. Raw monotherapy dose-response data

Use raw measurements only if asked for a curve, actual measured viability,
fit quality, concentration range, or a genuinely new metric. For standard
summary questions, **do not descend to dose-level data**.

### 6.1 TRE-style raw response

```r
# Determine whether this PSet actually has a `raw` assay.
raw <- pgx_get_response_assay(p, "raw")
print(names(raw))
print(head(raw, 3))

# Select by its ACTUAL key columns: may include experiment ID,
# sampleid, treatment1id, treatment1dose, replicate, and viability.
# Preserve every measured dose/replicate; do not `unique()` indiscriminately.
```

A sample's experimental unit may be `(sampleid, treatmentid, replicate,
plate, timepoint)` rather than merely `(sampleid, treatmentid)`. A zero drug
dose (control) is not interchangeable with missing dose. Do not take `log10(0)`
without an explicit plotting convention.

### 6.2 Legacy sensitivity representation

```r
raw_legacy <- tryCatch(PharmacoGx::sensitivityRaw(p),
                       error = function(e) NULL)
if (!is.null(raw_legacy)) {
  print(dim(raw_legacy))
  print(dimnames(raw_legacy))
}
```

The documented legacy structure is a three-dimensional array indexed by
experiment, dose position and measurement type (`Dose`, `Viability`).
Inspect corresponding `sensitivityInfo(p)` to link an experiment to a
sample and treatment. **Never** assume that array row index equals `sampleid`.

### 6.3 Visualization without recalculating

For supported historical sensitivity PSets, package function
`drugDoseResponseCurve(drug, cellline, pSets = list(...),
plot.type = "Actual")` displays stored doses and viabilities. Use
`plot.type = "Actual"` if the user requests measured points rather than a
new fitted curve; `"Fitted"` or `"Both"` invokes a fitting/display path.
Inspect `sample_col`, `treatment_col`, `viability_as_pct`, and
`conc_as_log` arguments and confirm actual units before plotting.

`curve_fitting_pgx()` in `case_study_1.R` is **sourced from a local helper
script** (`pgx3_cruve_fitting.R`), not demonstrated as an exported
`PharmacoGx::` function. Likewise `zFactor`, `ssmd`, `zhang_thresh`, and
`outlier_remove` in PRISM scripts are sourced from local files. **Never call
these as `PharmacoGx::...` without verifying their export.**

---

## 7. Combination screens: canonical retrieval rules

### 7.1 First determine the requested level of evidence

A combination response may have:

1. **Dose-level observed viability**, one observation for each drug1 × drug2
   dose and technical replicate.
2. **Dose-level stored synergy score** (Bliss, HSA, ZIP, Loewe; observed/fit).
3. **Pre-computed within-experiment summary** (mean/max/aggregate synergy,
   combination efficacy, quality-control metrics).
4. **Per-sample × pair analysis-ready value** made by a documented aggregation
   of multiple observations, only if the question requires it.

**Default for an unspecified Bliss variant: observed (`*_obs`), not fitted
(`*_fit`).** “Bliss synergy” by itself does *not* authorize choosing a fitted
score. See the mandatory selection protocol in Section 7.2.1.

**Use the most directly stored level that answers the question.** For a
cell-line biomarker, a well-defined sample-level pair summary is usually
needed; for a synergy heatmap, return actual dose-level records. Do not count
multiple doses as independent cell lines or patients.

### 7.2 Combination inventory, with stop conditions

```r
tr <- PharmacoGx::treatmentResponse(p)
possible <- c("profiles", "synergy", "combo_viability", "raw", "mono_profiles")
for (nm in possible) {
  x <- tryCatch(pgx_get_response_assay(p, nm), error = function(e) NULL)
  if (is.null(x)) next
  cat("\nAssay:", nm, "nrows:", nrow(x), "\n")
  print(names(x))
  print(head(x, 2))
}
```

Before filtering, identify: `sampleid`, `treatment1id`, `treatment2id`,
`treatment1dose`, `treatment2dose`, replicate/time/batch, score family,
`_obs` vs `_fit` vs `recomputed`, and fit-quality fields. A column containing
`Bliss` is **not** necessarily a synergy-excess score; a Bliss *null expected
viability* and an observed *Bliss excess* are different quantities.

### 7.2.1 MANDATORY selection: observed Bliss wins over fitted Bliss

When the user requests **Bliss synergy** without specifying observed versus
fitted, the agent **must select stored observed Bliss**, not `bliss_fit` or
other fitted equivalents. This is a retrieval policy, not a claim that every
PSet uses the same column name.

1. **If observed is explicitly requested**, retrieve only an observed metric.
   If fitted is explicitly requested, retrieve that fitted metric, with the
   model/fit provenance stated. An explicit choice overrides this default.
2. **If the variant is unspecified**, first look for observed score columns
   such as `mean_Bliss_score_obs`, `Bliss_synergy_score_obs`, or another
   clearly documented observed (`*_obs`) field in the relevant *summary*
   or *dose-level* assay. Choose the assay/aggregation level appropriate to
   the question, not merely the first column containing `Bliss`.
3. **Exclude fitted alternatives from default eligibility:** examples
   include `Bliss_synergy_score_fit`, `mean_Bliss_score_fit`, `bliss_fit`,
   and similar `_fit` scores. A fitted value must never replace observed
   Bliss merely because the observed values are missing or NA.
4. **Unsuffixed fields require verification.** Some NCI-ALMANAC scripts
   retrieve `Bliss_score` and GDSC Anchor scripts show `mean_Bliss_score`.
   These may be usable as observed scores **only if assay documentation,
   metadata, or measurement provenance demonstrates that interpretation**.
   Do not automatically equate an unsuffixed `Bliss_score` with `_obs`, and
   do not exclude it solely because the naming convention differs.
5. **If observed Bliss cannot be identified or has no eligible finite
   values**, report `OBSERVED_BLISS_ABSENT` and the actually available
   candidate fields. Do **not** silently switch to fitted, HSA, ZIP, or
   recalculated Bliss; do not reconstruct a score from raw viability.
6. **Every result must state** the exact source assay/column, whether it is
   observed or fitted, measurement level, any aggregation across stored
   scores, units/direction, and number of eligible biological samples.

**Example response:** “I used the stored observed Bliss metric
`mean_Bliss_score_obs` in the GDSC Matrix `profiles` assay. I did not use
fitted Bliss (`*_fit`).” For an NCI-ALMANAC `Bliss_score`, replace this
language only once its observed provenance has been verified.

### 7.3 GDSC-SQUARE Matrix: stored per-sample Bliss

Observed script pattern (`pgxagent_cs_gdsc_mtrx.R`,
`pgxagent_cs_emerg_bcl2.R`): the `profiles` assay includes
`mean_Bliss_score_obs`, and a dose-level `synergy` assay can contain
`HSA_synergy_score_fit`, `combo_viability`, and drug-specific fit parameters.
These are **dataset-specific examples**; confirm every field exists.

```r
x <- pgx_get_response_assay(gdsc_matrix, "profiles")
required <- c("sampleid", "treatment1id", "treatment2id",
              "mean_Bliss_score_obs")
stopifnot(all(required %in% names(x)))

pair <- x[
  ((treatment1id == "AZD5991" & treatment2id == "Venetoclax") |
   (treatment1id == "Venetoclax" & treatment2id == "AZD5991")) &
  is.finite(mean_Bliss_score_obs)
]
stopifnot(nrow(pair) > 0)

# QC: identify independent samples and repeated profile records.
pair[, .(n_records = .N,
         n_finite = sum(is.finite(mean_Bliss_score_obs))),
     by = sampleid][order(-n_records)]

# Only IF a per-sample pair value is required and repeats have been audited:
by_sample <- pair[, .(Bliss = mean(mean_Bliss_score_obs)), by = sampleid]
stopifnot(!anyDuplicated(by_sample$sampleid))
```

This example *summarizes existing stored scores*; it **does not recompute
Bliss**. Report `source_assay="profiles"`,
`source_column="mean_Bliss_score_obs"`, `aggregation="mean across
eligible profile records per sample"`, and the row count. **Never substitute
`mean_Bliss_score_fit` or another fitted Bliss value by default.**

### 7.4 GDSC-SQUARE Matrix: dose-specific response

```r
x <- pgx_get_response_assay(gdsc_matrix, "synergy")
stopifnot(all(c("sampleid", "treatment1id", "treatment2id") %in%
              names(x)))

slice <- x[sampleid == "NOMO-1" &
  ((treatment1id == "Selumetinib" & treatment2id == "AZD5991") |
   (treatment1id == "AZD5991" & treatment2id == "Selumetinib"))]

stopifnot(nrow(slice) > 0)
print(names(slice))
# Then select the requested *stored* observed viability or HSA/Bliss field.
# Re-orient dose 1 and dose 2 explicitly if displaying axes by drug name.
```

The GDSC Matrix case study uses `lib1_dose`, `lib2_dose` as library-level
indices and `treatment1dose`, `treatment2dose` as concentrations. **Do not
confuse dose indices with physical concentration values.** The same script
uses a 0.3 µM fixed-drug illustration and precomputed HSA; estimating a
projected curve with `estimateProjParams()` is a **separate requested
analysis**, not retrieval.

### 7.5 GDSC-SQUARE Anchor: oriented anchor design

The user's GDSC-anchor scripts use an asymmetric **7 × 2** library/anchor
design. Example fields in `profiles`: `n_dose1`, `treatment2dose`,
`ic50_recomputed_1`, `combo_ic50_observed`, `mean_Bliss_score`; in some
objects `mean_Bliss_score_obs` may instead be used. **Inspect actual columns**.
An unsuffixed `mean_Bliss_score` is **not automatically** confirmed to be
observed; apply Section 7.2.1 before using it as the default Bliss metric.

```r
x <- pgx_get_response_assay(gdsc_anchor, "profiles")
print(names(x))

pair <- x[
  (treatment1id == "Camptothecin" & treatment2id == "AZD7762") |
  (treatment1id == "AZD7762" & treatment2id == "Camptothecin")
]
print(pair[, .N, by = .(treatment1id, treatment2id)])

# Examine whether treatment1 is the variable 7-dose series in each record.
# Validate n_dose1, treatment2dose, and fitted vs observed measures before
# pooling orientations or comparing potency shifts.
```

**Important monotherapy trap:** in anchor profiles, an `aac_recomputed_1`
column can pertain to the first/variable drug, while a similarly named
`aac_recomputed_2` may be absent. That does **not** establish that the second
component lacks a separate monotherapy response. Inspect the PSet's actual
monotherapy records and source design, retrieve each component independently,
then join by sample if scientifically valid. Never fabricate `aac_2` from
`aac_1`, swap orientations blindly, or assume the anchor drug has the same
measurement context as the library drug.

**Scientific-equivalence trap:** the anchor script calculates a monotherapy-
relative `log2(ic50_recomputed_1 / combo_ic50_observed)`. Its comments state
that exact equivalence to a published Bliss-relative ΔIC50 is **unverified**.
Keep that distinction; never label the two measures identical.

### 7.6 NCI-ALMANAC: stored dose-level synergy

Observed scripts use either:

- `SummarizedExperiment::assay(tr, "synergy")` with columns
  `Bliss_score`, `HSA_score`, `ZIP_score`;
- `assay(tr, "combo_viability")` with `Bliss_score`, `ZIP_delta`
  and fit-QC columns; or
- `"mono_profiles"` for monotherapy summaries such as `aac_recomputed`.

The layouts depend on the **particular curated NCI-ALMANAC PSet**, not on its
name alone. Inspect availability and do **not** conclude there is one
universal `synergy` table. For an unsuffixed `Bliss_score`, verify that it
represents observed synergy in this curated PSet before applying the
observed-Bliss default (Section 7.2.1).

```r
tr <- PharmacoGx::treatmentResponse(nci_almanac)
x <- pgx_get_response_assay(nci_almanac, "synergy")
stopifnot(all(c("sampleid", "treatment1id", "treatment2id") %in%
              names(x)))

pair <- x[
  (treatment1id == "Paclitaxel" & treatment2id == "Nilotinib") |
  (treatment1id == "Nilotinib" & treatment2id == "Paclitaxel")
]
stopifnot(nrow(pair) > 0)
print(names(pair))

# The paper-reproduction script restricts to doses >0 and reports
# 9 dose pairs per selected breast-cancer cell line; establish that from
# actual dose columns before computing/reporting a mean score.
```

If a derived **per-sample** mean is requested, group by sample, unordered
pair, synergy model, and all necessary experimental context; retain
`n_doses`, distinct dose pairs, technical replicates, and missingness.
Do not use `na.rm=TRUE` to hide groups with no finite measurements.

### 7.7 Using TRE-native aggregation (when the method works)

The NCI biomarker case study demonstrates a TRE-aware aggregation syntax:

```r
# This is a SCRIPT-PATTERN example. Confirm that the pinned TRE method
# supports this call and that the `combo_viability` assay contains Bliss_score.
tr <- PharmacoGx::treatmentResponse(nci_almanac)
mean_bliss <- tr |>
  aggregate(Mean_Bliss = mean(Bliss_score),
            assay = "combo_viability",
            by = c("treatment1id", "treatment2id", "sampleid"))
```

Use the TRE's method only after checking its actual dispatch and keys. The
fallback is to retrieve the relevant assay using `treatmentResponse()` and
summarize **stored** scores with `data.table` or `dplyr`. Label the
aggregation as derived, retain the number of dose observations, and ensure
identical scientific inclusion rules in both implementations.

---

## 8. Molecular profile retrieval: features, columns, sample mapping

### 8.1 Inventory a molecular datatype

```r
print(PharmacoGx::mDataNames(p))

assay_name <- "rna"  # select only if actually available
stopifnot(assay_name %in% PharmacoGx::mDataNames(p))

fi <- as.data.frame(CoreGx::featureInfo(p, assay_name))
pi <- as.data.frame(CoreGx::phenoInfo(p, assay_name))
print(names(fi)); print(head(fi, 2))
print(names(pi)); print(head(pi, 2))

mp <- CoreGx::molecularProfilesSlot(p)[[assay_name]]
print(names(SummarizedExperiment::assays(mp)))
print(S4Vectors::metadata(mp))

# Note: this may be large, so subset features early:
print(dim(PharmacoGx::molecularProfiles(p, assay_name)))
```

`mDataNames()` lists **profile names**; an assay named `mutation`, `cnv`,
`rna`, `rnaseq.comp`, `Kallisto_0.46.1.rnaseq`, or `mutation_exome` may have
special annotation requirements. Check its metadata (`annotation`), assay
units and format. Do not classify it solely from a regex matching its name.

`PharmacoGx::molecularProfiles(p, assay_name)` returns a matrix in the
common access path. The matrix columns need not correspond 1-to-1 with
biological sample IDs; `phenoInfo()` maps molecular measurements back to
samples. `featureInfo()` maps feature rows back to gene identifiers.

### 8.2 Resolve a gene symbol to feature identifier(s)

```r
find_gene_features <- function(p, assay_name, gene_symbol) {
  fi <- as.data.frame(CoreGx::featureInfo(p, assay_name))
  stopifnot(nrow(fi) > 0L, !is.null(rownames(fi)))
  sym_cols <- grep("symbol|hugo|hgnc|gene.?name|^gene$",
                   names(fi), ignore.case = TRUE, value = TRUE)
  exact_rows <- toupper(rownames(fi)) == toupper(gene_symbol)
  for (k in sym_cols) {
    exact_rows <- exact_rows | (!is.na(fi[[k]]) &
      toupper(as.character(fi[[k]])) == toupper(gene_symbol))
  }
  ids <- rownames(fi)[which(exact_rows)]
  ids <- ids[!is.na(ids) & nzchar(ids)]
  unique(ids)
}

# e.g. IDs <- find_gene_features(p, "rna", "ERCC1")
```

- The true feature may be `ENSG00000012061` (ERCC1 in one GDSC RNA
  example), even when the user requested `ERCC1`.
- If multiple probes/transcripts/rows map to a symbol, report the ambiguity
  and the available levels. Do not silently pick lexicographically first.
- Do not aggregate *across technologies* or across distinct genomic features
  unless a predefined rule is justified.
- If no feature matches, report `FEATURE_ABSENT` or `UNMAPPED`; don't invent a
  row by changing its name.

### 8.3 Extract a feature and map each molecular column to sample ID

```r
get_feature_long <- function(p, assay_name, feature_id) {
  m <- PharmacoGx::molecularProfiles(p, assay_name)
  stopifnot(feature_id %in% rownames(m))

  fi <- as.data.frame(CoreGx::featureInfo(p, assay_name))
  stopifnot(feature_id %in% rownames(fi))

  pi <- as.data.frame(CoreGx::phenoInfo(p, assay_name))
  stopifnot(nrow(pi) == ncol(m))

  # Align colData to assay columns when the identifier match is explicit.
  if (!is.null(colnames(m)) &&
      all(colnames(m) %in% rownames(pi))) {
    pi <- pi[match(colnames(m), rownames(pi)), , drop = FALSE]
  } else {
    # Positional ordering is only acceptable after inspecting the SE
    # alignment; stop when there is no reliable mapping.
    se <- CoreGx::molecularProfilesSlot(p)[[assay_name]]
    stopifnot(ncol(se) == ncol(m), nrow(pi) == ncol(se))
    # SE colData and assay columns are positionally aligned by construction.
  }

  id_col <- if ("sampleid" %in% names(pi)) "sampleid"
            else if ("cellid" %in% names(pi)) "cellid"
            else stop("No validated sampleid/cellid in phenoInfo")

  data.table::data.table(
    sampleid = as.character(pi[[id_col]]),
    molecular_column = if (!is.null(colnames(m))) colnames(m)
                       else as.character(seq_len(ncol(m))),
    feature_id = feature_id,
    value = as.vector(m[feature_id, , drop = TRUE])
  )
}

# rna <- get_feature_long(p, "rna", "ENSG00000012061")
# print(rna[, .N, by = sampleid][N > 1])
```

If `molecularProfiles()` is too large, fetch one row after confirming the
feature identifier; avoid converting an entire multi-gigabyte assay to a
data frame. Multiple molecular columns per sample are technical or biological
replicates until proven otherwise. For RNA, a median across replicates may be
reasonable with a documented rationale; for mutations, conflicting calls are
not resolved by averaging numeric encodings.

### 8.4 Mutation, CNV, RNA: **different semantics**

- **RNA:** determine normalization and scale (microarray, log-normalized
  expression, RNA-seq gene level, etc.). Do not assume Z scores or counts.
- **Mutation:** determine whether the assay is any-variant, nonsynonymous,
  specific variant, or a specialized binary assay. `BRAF V600E` is **not**
  equivalent to `BRAF mutated`; `FLT3-ITD` is not generic `FLT3 mutated`.
- **CNV:** determine log2 copy ratio, gene-level continuous score, absolute
  copy number, or amplification/deletion calls before thresholding.
- **Missing mutation calls** are **unknown**, not wild type; distinguish `wt`,
  negative and no-call strings. For categorical calls, retain raw strings and
  exact definition of binary coding.

The monotherapy benchmark script contains a custom `classify_mutation()`
function with special-case BRAF V600E, EGFR sensitizing/secondary variants,
TP53, and FLT3-ITD rules. **That helper is not a PharmacoGx export** and its
rules are hypothesis-specific. Apply only to the corresponding exact
biomarker question, with missingness retained.

### 8.5 Matching response to molecular data

After establishing a single **independent sample** and a valid feature:

```r
# response_dt must contain unique sampleid, stored response value.
# marker_dt must contain unique sampleid, measured gene value.
stopifnot(!anyDuplicated(response_dt$sampleid))
stopifnot(!anyDuplicated(marker_dt$sampleid))

matched <- merge(response_dt, marker_dt,
                 by = "sampleid", all = FALSE)
matched <- matched[!is.na(sampleid)]

cat("Response N:", nrow(response_dt), "\n")
cat("Molecular N:", nrow(marker_dt), "\n")
cat("Matched N:", nrow(matched), "\n")
```

Do not interpret `nrow(matched)` as independent **patients** without checking
patient IDs. Do not cross-join unmatched sample names. In PRISM/CCLE,
molecular and drug screens may share biological samples but have different
experimental provenance.

---

## 9. PRISM drug-response + CCLE molecular profiles: fallback for ANY eligible cell-line PSet

**Mandatory, general rule:** If the requested PSet does not contain the
molecular assay, requested gene/feature, or **matched molecular observations
for the cell line(s) of interest**, the agent must **check CCLE** before
stating the analysis is impossible. This includes—but is **not limited to**—
PRISM. The purpose is to retrieve **CCLE molecular values for genuinely
matching cell lines**, while keeping drug-response measurements from the
**originally requested response PSet**. CCLE is a separate molecular-data
source, **not** a reason to switch the drug-response dataset.

**Eligibility boundary:** CCLE is appropriate only for biological cell lines
whose identities can be validated. Do not treat patient biopsies, PDOs,
primary cultures, or models with a merely similar label as CCLE lines. If
sample identity cannot be verified, report `MAPPING_UNVERIFIED` or
`CCLE_CHECKED_NO_MATCH` rather than assuming the match.

**Established user example:** PRISM_2020 provides drug response; CCLE_2015
provides compatible molecular assays for matched cells. The user's scripts
transfer `rna`, `Kallisto_0.46.1.rnaseq`, `mutation`, and `cnv` from CCLE_2015
into a **copy** of PRISM. Other response PSets can use the same *decision
workflow* but their IDs/metadata may require a different crosswalk and assay
selection. Check actual CCLE content instead of assuming profiles in every
release.

### 9.1 Mandatory retrieval and integration decision

1. **Inspect the requested response PSet first:** `mDataNames(p)`,
   `molecularProfiles(p, type)`, `featureInfo(p, type)`, and
   `phenoInfo(p, type)`. Check whether the assay, particular feature and
   **requested cell-line coverage** are all usable. Missing coverage for the
   target subset is a reason to check CCLE even if the assay itself exists.
2. **Establish the model type.** Inspect `sampleInfo(p)` and sample/model
   metadata. Only try CCLE as a molecular source when the underlying model
   is a cell line that could genuinely exist in CCLE; do not equate model
   types based on a similar tissue name.
3. **Check CCLE via the existing discovery/loading skill:** examine
   available CCLE PSets (e.g., CCLE_2015 and CCLE_2019 where available),
   then inspect `mDataNames(ccle)`, assay metadata, `featureInfo()`,
   `phenoInfo()`, technology and normalization. Verify the **requested
   feature** is represented and nonmissing.
4. **Verify sample overlap:** compare curated sample IDs/aliases or a
   reliable cell-line crosswalk (e.g., vetted DepMap/Cellosaurus IDs), with
   stable one-to-one biological identity where possible. A case-insensitive
   string or similar-looking line name alone is **not** sufficient. Report
   `n_requested_response_lines`, `n_validated_CCLE_matches`, and `n_with_usable_feature`.
5. **Choose source conservatively:** prefer suitable native molecular data
   for its covered models. If CCLE supplements missing models, retain
   `molecular_source_pset` at **row level** and do not silently pool
   incompatible molecular platforms or scales. Do not treat different
   normalization schemes as interchangeable.
6. **Retrieve CCLE molecular measurements using package accessors:**
   `molecularProfiles(ccle, assay)`, `featureInfo(ccle, assay)`,
   `phenoInfo(ccle, assay)`; join to the original PSet's **stored drug
   responses** using the validated biological mapping. Prefer a non-mutating
   matched table if only one/few features are required.
7. **If a downstream PharmacoGx method needs an integrated PSet**, create
   a **copy** and transfer the compatible CCLE `SummarizedExperiment` only
   after verifying column-to-sample IDs, annotation, and method behavior.
   Never alter the original stored response, sample annotation or curation.
8. **Report provenance and coverage:** original response PSet and assay;
   CCLE release, assay/platform, feature ID, matching method, match counts,
   unmatched line counts, and the final independent biological N. Explicitly
   state that molecular values came from CCLE.
9. **If CCLE cannot supply a validated match**, explain that the CCLE check
   was performed, list candidates and verified overlap, and do not claim
   molecular association based on unmatched measurements.
10. **Never double-count** PRISM and PRISM+CCLE as independent screens;
    CCLE molecular data reused in different response PSets do not establish
    independent molecular validation.

### 9.2 Direct-match example (only for harmonized sample IDs)

```r
# Both are previously loaded canonical PSets. Adapt names after inventory.
prism_updated <- prism  # work on a copy
profiles_to_copy <- c("rna", "Kallisto_0.46.1.rnaseq", "mutation", "cnv")

prism_ids <- as.character(PharmacoGx::sampleNames(prism))
for (nm in profiles_to_copy) {
  stopifnot(nm %in% PharmacoGx::mDataNames(ccle))
  se <- CoreGx::molecularProfilesSlot(ccle)[[nm]]
  col_meta <- as.data.frame(SummarizedExperiment::colData(se))
  stopifnot("sampleid" %in% names(col_meta))

  ids <- as.character(col_meta$sampleid)
  keep <- !is.na(ids) & nzchar(ids) & ids %in% prism_ids
  se <- se[, keep, drop = FALSE]
  stopifnot(ncol(se) > 0)

  md <- S4Vectors::metadata(se)
  md$source_pset <- "CCLE_2015"
  md$source_profile <- nm
  md$import_note <- "Molecular data from CCLE; response from PRISM_2020"
  S4Vectors::metadata(se) <- md

  prism_updated@molecularProfiles[[nm]] <- se  # controlled mutation of COPY
}

stopifnot(
  identical(prism_updated@sample, prism@sample),
  identical(prism_updated@treatmentResponse, prism@treatmentResponse),
  identical(prism_updated@curation, prism@curation),
  isTRUE(methods::validObject(prism_updated))
)
```

**Important:** the direct assignment works for the user script's PSet
structure; another object could require the appropriate
`CoreGx::molecularProfilesSlot()` replacement setter. `validObject()` does
**not** prove that IDs refer to the same biological lines. Verify mappings
independently; if no validated crosswalk exists, mark `MAPPING_UNVERIFIED` and
stop. Prefer a non-mutating matched-table workflow when the agent only needs
one molecular feature.

### 9.3 Non-mutating CCLE fallback for any validated response PSet

Once the original PSet's drug-response cohort has been retrieved and the
specific CCLE assay/feature are verified, a targeted join is usually enough.
The helper functions below were defined in Section 8; neither helper is a
package export. **Do not run this example until the ID equivalence has been
validated** (direct harmonized IDs or a vetted crosswalk applied first).

```r
# response_dt: stored drug-response values from the originally requested PSet;
#             one eligible biological sample per row, columns sampleid/value.
# ccle:        loaded CCLE PharmacoSet, NOT the response PSet.
# gene:        requested symbol; choose a suitable observed CCLE assay first.
ccle_assay <- "rna"  # only after confirming mDataNames(ccle) and metadata
gene <- "ERCC1"
stopifnot(ccle_assay %in% PharmacoGx::mDataNames(ccle))
feature_ids <- find_gene_features(ccle, ccle_assay, gene)
if (length(feature_ids) != 1L) {
  stop("CCLE feature absent or ambiguous; inspect featureInfo()")
}
ccle_long <- get_feature_long(ccle, ccle_assay, feature_ids)

# This simple example is ONLY for an independently verified 1:1 direct-ID
# match. For different IDs, first join through a vetted crosswalk that maps
# source sampleid to target sampleid, and check its uniqueness.
stopifnot(all(c("sampleid", "value") %in% names(response_dt)))
stopifnot(!anyDuplicated(response_dt$sampleid))
stopifnot(!anyDuplicated(ccle_long$sampleid))
matched <- merge(
  response_dt,
  ccle_long[, .(sampleid, feature_id, molecular_value = value)],
  by = "sampleid", all = FALSE
)
stopifnot(!anyDuplicated(matched$sampleid))
message("Response-model N: ", data.table::uniqueN(response_dt$sampleid),
        "; validated CCLE + response matched N: ",
        data.table::uniqueN(matched$sampleid))

# Keep response_source = original PSet; molecular_source = exact CCLE release.
# Avoid silently replacing native molecular values or mixing expression scales.
```

When a sample has **multiple** valid CCLE molecular columns, first inspect
replicate/platform and do not use the simple direct-join example until a
scientifically justified replicate policy produces one eligible observation
per biological sample. For a biomarker association, pass data to the installed
PharmacoGx method only after verifying how an external molecular matrix can
be supplied (Section 11.2); otherwise use a transparent, explicitly requested
analysis on the validated matched data.

---

## 10. Dataset-specific quirks: audit, do not blindly patch

| Dataset | Script-observed condition | Required agent behavior |
|---|---|---|
| GDSC Matrix | `sensitivityMeasures(gdsc_mtrx)` can raise `gmean(matrix_completeness, na.rm = TRUE)` because `matrix_completeness` is a character column in `profiles`. The user also removed this column before some `drugSensitivitySig()` runs. | For **this exact error**, apply the specified copy-and-reassign fix in Section 10.2 to the local in-memory working object, then retry `sensitivityMeasures()`; never overwrite the original `.rds` file. |
| NCI-ALMANAC/NCI60 | `rnaseq.comp` was annotated incompatibly for some signature functions; gene identifiers required mapping. | Inspect actual `S4Vectors::metadata(se)$annotation`; do not relabel measurement types blindly; retain original feature IDs when mapping to Ensembl. |
| BeatAML | FLT3-ITD status was in `sampleInfo()` but lacked an assay in some user PSets. | Read original field; derive an appropriately annotated binary assay **only when explicitly needed**, in a copy; do not equate absence with negative. |
| GDSC Anchor | Oriented anchor/library metrics and a supplementary MSI annotation matched by COSMIC IDs. | Keep orientation; verify external annotation source and one-to-one COSMIC mapping; distinguish unannotated from MSS. |
| PRISM | Often lacks native molecular characterization. | Evaluate validated CCLE molecular matching before excluding from biomarker analysis. |
| NCI-ALMANAC | Different curated variants provide `synergy`, `combo_viability`, `mono_profiles`, `profiles`. | Inspect each PSet's actual response assays, never hard-code one. |

**Do not promote exploratory code into a universal workaround.** A script's
`TODO`, commented-out alternative, or a one-off `@slot` mutation is an
observation, not part of the package's general retrieval contract.

### 10.1 Example: inspect RNA annotation without changing it

```r
for (nm in PharmacoGx::mDataNames(p)) {
  se <- CoreGx::molecularProfilesSlot(p)[[nm]]
  cat(nm, ": annotation = ",
      paste(S4Vectors::metadata(se)$annotation, collapse = ","), "\n")
}
```

If an annotation such as `rnaseq.comp` needs correction for a specific
method, first verify its actual measurement type, copy the PSet, set the
annotation on the copy using S4Vectors metadata accessors, and document why.
Never change a categorical assay into continuous RNA by renaming metadata.

### 10.2 REQUIRED GDSC Matrix `sensitivityMeasures()` error workaround

**Trigger: only when** `sensitivityMeasures(gdsc_mtrx)` on the **GDSC Matrix**
PSet produces this error (the full message may include a `data.table`
optimization suggestion):

```text
Error in gmean(matrix_completeness, na.rm = TRUE) :
  Type 'character' not supported by GForce mean (gmean).
```

**Observed explanation:** this PSet's `profiles` response assay has a
character-valued `matrix_completeness` column that is being included in a
mean aggregation inside `sensitivityMeasures()`. It is a compatibility
issue for this call, not evidence that the PSet lacks sensitivity data.

**Do exactly this for the in-memory working `gdsc_mtrx` object, then retry.**
The assignment back into the S4 `treatmentResponse` slot is necessary;
merely editing an indirectly retrieved object may not change the assay used
by `sensitivityMeasures()`.

```r
tr <- gdsc_mtrx@treatmentResponse

prof <- data.table::copy(tr@assays[["profiles"]])
prof[, matrix_completeness := NULL]

tr@assays[["profiles"]] <- prof
gdsc_mtrx@treatmentResponse <- tr

sensitivityMeasures(gdsc_mtrx)
```

**Safety/verification rules for the agent:**

1. First verify that the loaded object is the intended GDSC Matrix PSet and
   that `profiles` actually includes a `matrix_completeness` column. If not,
   do not execute a guessed patch; report the observed structure and error.
2. This code patches the **local in-memory object**. Do not `saveRDS()` it
   over the downloaded/canonical file or remove additional columns. When
   retaining an unmodified working value is important, use an appropriately
   named working copy (`gdsc_mtrx <- original_gdsc_mtrx` before the snippet).
3. The fix **removes only one nonnumeric metadata column**; it must not
   recalculate AAC, IC50, or other stored values. Confirm the rest of the
   profile fields, row count and important keys are still present.
4. Retry the exact call `sensitivityMeasures(gdsc_mtrx)`. If it works,
   continue with normal metric discovery and explicitly record the patch in
   the retrieval manifest. If it still fails, report the new error and do
   not randomly coerce numeric scores, disable `data.table` optimizations,
   delete unrelated fields, or invent measurements.
5. This is **not** a general rule to remove `matrix_completeness` from
   unrelated PSets, nor a general instruction to mutate every GDSC Matrix
   PSet before inspection. Trigger the workaround on the specified error.

### 10.3 Error handling in inventory helpers

The `tryCatch()` wrappers in Sections 2 and 5 report the actual exception;
they must **not** return `character()` silently as if no sensitivity metrics
exist. If the GDSC Matrix error matches Section 10.2, patch the working
object and rerun the inventory. Do not diagnose this failure as
`METRIC_ABSENT` until the accessor and actual assays have both been checked.

---

## 11. From retrieval to PharmacoGx statistical methods

**This section is a downstream handoff, not an instruction to analyze every
retrieval request.** `drugSensitivitySig()` is appropriate when the user asks
for molecular-response associations; it is not a data-retrieval primitive.

### 11.1 Standard package-defined association interface

The 3.14.0 manual documents the `PharmacoSet` S4 method:

```r
# Signature concept (not runnable without a matching PSet and assay):
# PharmacoGx::drugSensitivitySig(
#   object = p,
#   mDataType = "rna",
#   drugs = confirmed_drug,
#   features = confirmed_feature,
#   cells = matched_sample_ids,
#   sensitivity.measure = confirmed_stored_metric,
#   molecular.summary.stat = "median",
#   sensitivity.summary.stat = "median",
#   modeling.method = "pearson",  # or "anova" as scientifically appropriate
#   standardize = "SD",
#   nthread = 1,
#   verbose = FALSE
# )
```

Important documented arguments: `mDataType`, `drugs`, `features`, `cells`,
`tissues`, `sensitivity.measure`, `molecular.summary.stat`,
`sensitivity.summary.stat`, `returnValues`, `sensitivity.cutoff`,
`molecular.cutoff`, `molecular.cutoff.direction`, `standardize`, `nthread`,
`parallel.on`, `modeling.method` (`"anova"`, `"pearson"`), and
`inference.method`. The 3.14.0 manual says `"pearson"` uses partial
correlations accounting for tissue of origin and `"anova"` uses nested
models. **Select method for the research question; do not change it to obtain
significance.**

### 11.2 User-script pattern with supplied matrices: verify runtime support

The uploaded monotherapy, combination and NCI scripts supply custom matrices
using `sProfiles=` and sometimes `mProfiles=` through the method's `...`.
**These arguments are not listed as formal parameters in the public 3.14.0
manual**. Thus the observed user-script pattern is informative, **but must
be checked against the pinned method implementation before relying on it**.

```r
# SCRIPT_PATTERN, conditional on installed pinned-method compatibility.
# Both matrices must be carefully aligned and their row/column names checked.
# s_profiles: treatment (or pair) x sample
# m_profiles: molecular feature x molecular sample
#
# sig <- PharmacoGx::drugSensitivitySig(
#   object = p, mDataType = confirmed_assay,
#   sProfiles = s_profiles, mProfiles = m_profiles,
#   drugs = confirmed_label, cells = matched_sample_ids,
#   features = confirmed_feature,
#   sensitivity.measure = confirmed_measure,
#   modeling.method = "pearson", nthread = 1
# )
```

For a combination, `sProfiles` often has one row per **drug pair** and one
column per **sample**, populated from the stored pair-level synergy score.
For RNA, the molecular matrix should be **feature × sample**. The sample IDs
must refer to the same independent biological units. The label supplied in
`drugs=` must match the row name of the custom response matrix. Do not call
this with `sProfiles` built for Bliss but a different `sensitivity.measure`
without an explicitly verified method contract.

### 11.3 Check the 3D output instead of assuming success

```r
# After successful run only:
stopifnot(length(dim(sig)) == 3L)
print(dim(sig))
print(dimnames(sig))
stopifnot(all(c("estimate", "pvalue") %in% dimnames(sig)[[3]]))

# Example when one feature and one treatment/pair were tested:
# sig[1, 1, "estimate"]
# sig[1, 1, "pvalue"]
```

Require valid matched N and sufficient variability before modeling. For
mutation-group analyses, report mutant/WT sample counts and missing calls;
check cohort-specific minimum N. **If there are zero or extremely few
independent samples, no significance claim is valid even when the method
returns a number.** Respect multiple testing and record the FDR universe.

### 11.4 Summary methods vs custom matrices

`PharmacoGx::summarizeMolecularProfiles()` is useful for one profile per
sample under an appropriate aggregation policy; it is **not** always
appropriate for unprocessed mutation strings or different assays.
`PharmacoGx::summarizeSensitivityProfiles()` produces a stored-metric
sample × drug matrix; it is **not automatically a drug pair × sample synergy
matrix**. Combination matrices generally must be built from the actual
pair-specific response assay. Keep the two concepts separate.

---

## 12. Cross-dataset retrieval and comparison

### 12.1 Repeat source retrieval **inside each PSet**

For each PSet independently, record:

- Exact PSet and build/commit, biological model type, source response screen.
- Confirmed drug ID or drug pair; aliases and curation source.
- Stored assay and **exact score column**, version/scale/direction.
- Monotherapy vs combination; dose-level vs profile summary.
- Tissue/disease, perturbation context, treatment time, and experimental unit.
- Response N, molecular N, matched independent N, missingness.
- Feature ID, molecular assay/platform, external molecular-profile source.
- Technical-replicate handling and any derived aggregate.
- Any data patch, mapping or exclusion; `UNVERIFIED` when appropriate.

Do not treat the same response screen under two PSet names as independent
evidence. CCLE molecular data used with PRISM responses does not establish
independent molecular replication.

### 12.2 Metric equivalence is a prerequisite, not an assumption

User-script examples of *observed column spellings*:

| PSet family | Example stored profile score | Extra checks |
|---|---|---|
| NCI-ALMANAC | dose `Bliss_score`; some profiles `Mean_Bliss` derived from these | observed vs fitted, units, eligible doses |
| GDSC SQUARE Matrix | `mean_Bliss_score_obs` | observed score, mean definition, dose coverage |
| GDSC SQUARE Anchor | `mean_Bliss_score` | anchor orientation and anchor concentrations |

Columns with similar names are not necessarily interchangeable because of
normalization, modeling, dose coverage or scoring convention. Compare raw
units and signs with actual PSet provenance **before** pooling or ranking
across datasets. Report non-comparable outcomes separately.

### 12.3 Sample-set overlap and independence

For two response screens, compute overlap using **validated sample crosswalks**.
Shared sample IDs do not imply independent biological samples, and different
sample IDs do not prove that samples are distinct. For reproducibility,
report the number of matched cell lines, shared drugs/pairs, shared tissues
and the response measure analyzed, plus screens' independence and molecular
source reuse.

### 12.4 When no common drug pair exists

Report `NO_SHARED_PAIR` with per-PSet pair coverage; do not substitute a
similar drug, pool variants, or silently choose another combination.
Cross-dataset combo-biomarker exploration in `pgxagent_cs_emerg_all.R` is
**explicitly labeled abandoned due to very weak synergy reproducibility**.
Do not present that script as evidence that a biomarker replicated across
all three combination PSets.

---

## 13. Strict rules for score calculation and fitted curves

The public manual documents these *computation* functions. Their existence
does **not** authorize recalculating a stored metric.

| Function | Purpose; use only on explicit request | Input or output trap |
|---|---|---|
| `computeAUC()` | New area from concentration/viability | Manual defines response-area AUC; check percent/decimal and log concentration flags. |
| `computeIC50()`, `computeICn()` | New fitted potency | Out-of-range/failed fits do not equal measured potency. |
| `logLogisticRegression()` / `hillCurve()` | Fit/evaluate Hill curve | Check dose log transform, viability scale, fit method. |
| `drugDoseResponseCurve()` | Visualization of actual or fitted curve | Choose `"Actual"` when fit is not requested. |
| `computeBliss(viability_1, viability_2)` | Bliss expected viability | **Expected viability** is not stored Bliss *excess synergy*. |
| `computeHSA(viability_1, viability_2)` | HSA expected viability | HSA expected viability is not HSA synergy-excess score. |
| `computeZIP()` / `computeLoewe()` | ZIP/Loewe null predicted viability | Requires matching dose and monotherapy model parameters. |
| `computeZIPdelta()` | Calculate dose-level ZIP delta | Do not overwrite `ZIP_delta` already stored. |
| `estimateProjParams()` | Fixed-dose projected curve | Analysis extension, not a retrieval method. |

For explicit synergy reconstruction, an agent must separately validate
observed combination viability, matched single-drug viability at the same
biological sample/doses, the precise null model, and the definition of
`observed - expected` vs `expected - observed`. Do **not** guess sign by the
word `Bliss`. Never fabricate zero-dose monotherapy profiles or infer missing
curve values by interpolation unless that modeling choice was requested.

---

## 14. Required data-retrieval manifest and statuses

Every successful answer with actual values must accompany a compact
machine-readable or plain-text manifest. Suggested fields:

```text
pset_name:
pset_version_or_source:
package_version_and_commit:
biological_model:
response_source_screen:
requested_drug_or_pair:
resolved_treatment_ids:
id_mapping_source:
response_assay:
exact_metric_column:
measurement_level: profile | dose | experiment | replicate
units_and_scale:
response_direction:
source_rows:
unique_samples:
independent_biological_units:
repeated_measurement_rule:
tissue_and_context_filters:
molecular_source_pset:
molecular_assay_and_feature_ids:
metric_specified_by_user: true | false
metric_default_rule_applied: none | aac_recomputed | stored_ic50 | observed_bliss
metric_selection_reason:
observed_or_fitted: observed | fitted | not_applicable | unverified
ccle_checked_for_missing_molecular_data: true | false | not_eligible
ccle_release_and_sample_crosswalk:
ccle_validated_overlap_n:
local_workaround_applied: none | gdsc_matrix_matrix_completeness | other_documented
molecular_measurement_type:
matched_independent_n:
source_data_unchanged: true | false
calculated_anything: no | named_aggregation | named_model
assumptions_and_limitations:
status:
```

Allowed main statuses (use meaningful, distinguishable flags):

- `OK_STORED`: exact requested stored data retrieved and validated.
- `OK_AGGREGATED`: existing stored values aggregated with documented rule.
- `PSET_UNAVAILABLE`: object not loaded; hand off to ORCESTRA loading skill.
- `ASSAY_ABSENT`: required assay does not exist.
- `METRIC_ABSENT`: exact score column not present.
- `OBSERVED_BLISS_ABSENT`: no verified usable observed Bliss despite
  searching appropriate stored assays; fitted Bliss was **not** substituted.
- `CCLE_CHECKED_NO_MATCH`: eligible CCLE PSet(s) were inspected but the
  requested cell line/feature had no verified usable match.
- `DRUG_ABSENT`: no validated drug match.
- `AMBIGUOUS_DRUG`: multiple potentially different ID matches.
- `NO_MATCHED_SAMPLE`: no joint response/molecular sample coverage.
- `FEATURE_ABSENT`: requested molecular feature unavailable.
- `MAPPING_UNVERIFIED`: gene/sample/drug crosswalk not validated.
- `INCOMPATIBLE_SCALE`: scores/datasets cannot be compared directly.
- `INSUFFICIENT_N` / `NO_VARIATION`: statistical handoff ineligible.
- `METHOD_UNVERIFIED`: intended version-dependent API not confirmed.
- `SOURCE_CONFLICT`: conflicting identifiers or assay metadata.

For any non-OK status, return the evidence (available assay names, actual
columns, mapped IDs, counts) and the smallest justified next step. Never
change the question to make it produce a numeric result.

---

## 15. Worked agent recipes

### Recipe A — “Get the stored Gemcitabine response in PSet X”

1. Confirm PSet loaded; run Sections 2–4 inventory.
2. Resolve exact Gemcitabine treatment ID via `treatmentInfo()` and assay IDs.
3. Identify actual stored metrics using `sensitivityMeasures()` **and**
   source assay inspection. If the user names a metric, use exactly that.
   If none was specified, **default to usable `aac_recomputed`, else a valid
   stored IC50** (Section 5.2.1). If the accessor raises the GDSC Matrix
   `matrix_completeness` error, first use Section 10.2 and retry.
4. Verify monotherapy-only records, dose range and assay keys.
5. Use `summarizeSensitivityProfiles()` if compatible, otherwise retrieve
   stored profile rows through `treatmentResponse()`.
6. Validate unique sample counts, repetition rules, scale/direction.
7. Return stored values and manifest. **No curve fit.** Always explicitly
   disclose the selected metric and explain AAC/IC50 direction, especially
   when the choice was the default rather than user-specified.

### Recipe B — “Which cell lines show strongest synergy for two drugs?”

1. Resolve both drug IDs; inspect available score families.
2. If the user specified Bliss observed/fitted, follow that exact request.
   Otherwise use **observed stored Bliss** (`*_obs`, e.g.
   `mean_Bliss_score_obs` in GDSC Matrix `profiles`); never default to
   `*_fit`. Verify provenance for unsuffixed `Bliss_score` (Section 7.2.1).
3. Filter pair in either orientation; retain original orientation metadata.
4. Exclude `NA` scores *only with missingness reported*.
5. Check repeated profiles and summarize by **biological cell line** only if
   needed, with a predeclared rule.
6. Rank in the verified synergy direction and return pair/sample/metric/N.
7. **Never** recompute Bliss or treat multiple doses as replicates of the
   biological sample count.

### Recipe C — “Show Bliss/HSA/ZIP at every tested dose in NCI-ALMANAC”

1. Inspect `treatmentResponse()` and locate a **dose-level** `synergy` or
   `combo_viability` assay that actually has all requested scores.
2. Filter both drug orientations and requested cell line(s).
3. Preserve `treatment1dose` / `treatment2dose`, exact score columns, and
   technical replicate identifiers.
4. Check number of unique tested dose pairs and missing values per model.
5. Return stored dose-level records or a heatmap; document scales and model
   names. **Do not compute score values from raw viability.**

### Recipe D — “Compare a molecular biomarker across multiple monotherapy PSets”

1. Identify all eligible tissue-specific and multi-tissue PSets; do not limit
   discovery to those with identical tissue strings.
2. In **each** PSet: verify drug name; choose an interpretable stored response
   metric; inspect molecular assays and gene feature mappings.
3. **For every eligible cell-line response PSet** (not just PRISM), if
   the required native assay, gene, or target-cell coverage is missing,
   inspect CCLE for the requested feature and cell lines. Require validated
   biological identity; keep response from the original PSet and report
   the exact CCLE molecular source. See Section 9.
4. Match response and molecular data on validated biological IDs; check
   independent patient/sample N, marker and response variation.
5. Provide one retrieval manifest per PSet. Only when analysis is requested,
   run an appropriate version-verified `drugSensitivitySig()` or supported
   association method and report FDR scope.
6. Different dose ranges, platforms, and response metrics can prevent direct
   meta-analysis; report incompatibility instead of forcing a common ranking.

### Recipe E — “Compare synergy for the same pair across NCI-ALMANAC,
GDSC Anchor and GDSC Matrix”

1. Enumerate and validate candidate pair IDs **in each PSet** independently.
2. Record score columns and whether each score is observed/fitted/dose-level/
   summary; test equivalence, sign and scale before comparison.
3. Extract stored scores, aggregate at most once per independent biological
   sample, separately per dataset, with dose-context QC.
4. Compare in matched tissue and, where requested, overlapping cell lines
   using verified crosswalks.
5. Explicitly distinguish “pair absent”, “cell absent”, “score absent”, and
   “measured score not significant.”
6. Document that weak between-dataset synergy reproducibility was reported in
   the user's exploratory cross-dataset script; do not claim replication
   without new evidence.

### Recipe F — “Is a marker available in primary AML patient samples?”

1. Include BeatAML_2018 and Tavor_2020 if loaded, despite nonstandard
   `tissueid` coding.
2. Check `sampleInfo()` for patient IDs and mutation/FLT3-ITD fields.
3. Inspect `mDataNames()`, `featureInfo()`, and assay metadata for a valid
   molecular marker.
4. If the marker is in sample annotations only, retrieve the **annotation**;
   do not manufacture a molecular assay merely to answer availability.
5. For associations, choose one independent patient unit as appropriate and
   audit repeat specimens/timepoints. Return `PATIENT_N`, not only row count.

---

## 16. Adversarial retrieval checklist (run before answering)

Use these tests to catch frequent agent failures:

1. The request says **AAC**; does the code call `computeAUC()`? **Fail.**
2. The request says **stored Bliss**; does code call `computeBliss()`? **Fail.**
3. A `profiles` row has two treatments; was it counted as monotherapy for
   treatment1? **Fail unless assay semantics explicitly establish otherwise.**
4. A pair was reordered; were `_1` and `_2`-specific doses/metrics also
   reoriented? **Fail if not.**
5. The score column contains `_fit` but the question says observed? **Fail.**
6. `sensitivityMeasures()` lacks a score but the TRE assay has it; did the
   agent declare it absent? **Fail.**
7. `molecularProfiles()` has columns whose names differ from `sampleid`; did
   agent join on column name without `phenoInfo()`? **Fail.**
8. A mutation is `NA`/no call; did the agent classify it WT? **Fail.**
9. Multiple probes map to a symbol; did the agent select the first without
   reporting its choice? **Fail.**
10. A cell-line response PSet (PRISM **or any other**) lacks the needed
    molecular feature/coverage; did the agent declare failure without checking
    eligible CCLE and validating overlap? **Fail.**
11. `matrix_completeness` was removed from the original GDSC PSet rather than
    a copy? **Fail.**
12. A data table is at nine dose pairs per cell line; did the agent report
    `N=9` independent cell lines? **Fail.**
13. A direct treatment/sample join has duplicated keys; did the agent perform
    many-to-many merging without reporting it? **Fail.**
14. An anchor drug was assigned `aac_2 = aac_1` because AAC_2 was absent?
    **Fail.**
15. The agent says `curve_fitting_pgx()` is exported by PharmacoGx because it
    appears in `case_study_1.R`? **Fail.**
16. A PSet is patient-derived, but the plot legend calls all samples immortalized
    cell lines? **Fail.**
17. Agent uses manual 3.16.0's signature as proof of pinned 3.14.1 runtime
    support? **Fail; check method in installed environment.**
18. A cross-dataset biomarker claim reuses CCLE molecular data but calls it
    independent molecular validation? **Fail.**
19. A script says a comparison was abandoned for weak reproducibility but
    agent reports it as a validated finding? **Fail.**
20. No observed data or package execution exists, but agent reports numerical
    values or successful execution? **Fail.**
21. The user asked an unspecified monotherapy sensitivity question; did the
    agent pick `auc_recomputed`, `aa_recomputed`, or IC50 while usable stored
    `aac_recomputed` existed for the requested cohort? **Fail.**
22. An IC50 fallback was used without explaining why AAC was unavailable,
    specifying the exact IC50 field/units, or checking its direction? **Fail.**
23. The user asked for unspecified Bliss and the agent chose `bliss_fit` or
    `Bliss_synergy_score_fit` over usable observed Bliss—or silently used fit
    when observed Bliss was absent? **Fail.**
24. An unsuffixed `Bliss_score` was called observed without provenance, or
    was automatically rejected despite verified observed provenance? **Fail.**
25. GDSC Matrix produced `gmean(matrix_completeness, ...)` and the agent
    reported no metrics, changed an unrelated column, or failed to retry
    after the specified in-memory workaround? **Fail.**
26. CCLE RNA/mutation/CNV was linked to a response PSet by superficial name
    similarity or a non-cell-line model, or CCLE drug response silently
    replaced the requested response source? **Fail.**
27. A result used a default metric/CCLE fallback/workaround but did not
    identify the precise metric, source, matched N, and modification in the
    final answer/manifest? **Fail.**

---

## 17. Source map and verification limits

### 17.1 Primary references

- User-supplied manual, Bioconductor 3.23 / **PharmacoGx 3.16.0**:
  https://bioconductor.org/packages/3.23/bioc/manuals/PharmacoGx/man/PharmacoGx.pdf
- Closer historical manual, Bioconductor 3.22 / **PharmacoGx 3.14.0**:
  https://bioconductor.statistik.tu-dortmund.de/packages/3.22/bioc/manuals/PharmacoGx/man/PharmacoGx.pdf
- PharmacoGx devel tests provided by user:
  https://github.com/bhklab/PharmacoGx/tree/devel/tests/testthat
- Pinned PharmacoGx code:
  https://github.com/bhklab/PharmacoGx/tree/a7aa4d727e521ab63f68f2dbfc16697e5e4764cc
- Pinned CoreGx code:
  https://github.com/bhklab/CoreGx/tree/f760bc7c230f892722d72634001054adad2ea0f0

**Verification limit of this authored skill:** the publicly accessible
3.14.0 and 3.16.0 manuals and user-supplied scripts were inspected. The
pinned commit's source/test contents and the user's actual R session/PSets
were **not executable/fully retrievable in this authoring environment**;
therefore no runnable code in this file should be represented as having
passed `testthat` or an end-to-end R execution on those pinned versions.
The linked **moving `devel` tests are not a substitute** for pinned tests.
The skill mandates runtime checks for any uncertain method or PSet layout.

### 17.2 Uploaded source scripts used to derive retrieval patterns

| Uploaded file | Relevant pattern or caution |
|---|---|
| `pgxagent_dataskills.Rmd` | Existing data-aware rules, tissue/model classifications, assay vigilance |
| `prism-ccle.Rmd`, `pgxagentic_prismccle.R` | PRISM response and validated CCLE molecular source, provenance, integrity QC |
| `pgxagent_cs_monobiom.R` | sensitivity measure selection, per-PSet molecular matching, mutation-specific calls, `drugSensitivitySig` handoff; custom helpers |
| `pgxagent_cs_combobiom.R` | cross-dataset combination biomarkers, gene mutation features, custom `sProfiles`/`mProfiles` |
| `pgxagent_cs_emerg_bcl2.R` | GDSC Matrix stored Bliss + monotherapy AAC orientation, feature-to-sample mapping |
| `pgxagent_cs_emerg_all.R` | assay-specific synergy columns, cross-dataset checks; **abandoned exploratory replication** |
| `pgxagent_cs_gdsc_mtrx.R` | matrix `profiles` vs dose `synergy`, fixed-dose extension, observed vs fit |
| `pgxagent_cs_gdsc_anchor.R` | 7×2 design, `profiles`, external COSMIC/MSI match, potency-ratio caveat |
| `pgxagent_cs_ncalmanac.R` | NCI `synergy` with Bliss/HSA/ZIP at tested dose pairs |
| `case_study3_nci_almanac_biomarkers.R` | `mono_profiles`, TRE aggregate, drug pair response matrix, association |
| `case_study3_nci_almanac_synergy_vis.R` | NCI `combo_viability`, `ZIP_delta`, fit-QC, heatmap |
| `case_study_1.R` | custom sourced `curve_fitting_pgx`—**not package export** |
| `case_study_2_prisme_primary.R` | PRISM primary-screen QC; local helper functions |
| `case_study_2_prism_secondary.R` | PRISM secondary-screen QC, controls, local helper functions |
| `case_study_2_prism_comparison.R` | primary/secondary hit comparison—custom derived metrics, not PSet accessors |

**User-requested additions incorporated in this revision:** (1) the exact
GDSC Matrix `sensitivityMeasures()`/`matrix_completeness` in-memory repair;
(2) `aac_recomputed` default and stored IC50 fallback for unspecified
monotherapy sensitivity, with mandatory disclosure; (3) observed Bliss over
fitted Bliss unless fit is explicitly requested; (4) mandatory CCLE molecular
coverage check for any eligible cell-line response PSet, not just PRISM.

**Operating principle:** *Inspect → identify the exact stored metric →
retrieve with the appropriate accessor → validate mapping and experimental
unit → report provenance → analyze only if requested.*
