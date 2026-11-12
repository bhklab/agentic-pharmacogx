# Install the latest published MCP branch in hosted R

Use this when the user requests cloud package setup. Install into a fresh
task-owned R library inside Biomni; no local workstation setup is needed.
Biomni documents R execution, but permission to install packages, compiler/system
dependencies, network access and library persistence are not verified. If any
are unavailable, return the exact error and ask the workspace administrator for
this environment. Do not use sudo, alter the shared system library, or replace
the requested package with a Bioconductor release.

## Which source to install

Verified directly against the public GitHub branches on 2026-10-30:

| Role | Branch | Frozen latest published commit | Version |
| --- | --- | --- | --- |
| PharmacoGx package | `bhklab/PharmacoGx` `feat/mcp` | `28c58707eece80086bee75d8ef0e8afae96389ca` | 3.14.1 |
| Matched CoreGx dependency | `bhklab/CoreGx` `main` | `bf6d814abd3dc0fc98f9f419f430cc6473046cb2` | 2.7.3 |

Install these GitHub commits. They are the reproducible snapshot of the latest
published MCP branch at packaging time, not `BiocManager::install("PharmacoGx")`
or an unqualified `install.packages("PharmacoGx")`.
The moving branch reference is `bhklab/PharmacoGx@feat/mcp`; resolve it to a full
SHA before future updates. For an explicitly requested latest-branch install,
resolve the current public feat/mcp SHA first and record it. If it has advanced,
inspect that revision's dependency requirements, establish the corresponding
CoreGx target, and update both the installation specs and verification targets
for that run. Do not call an untested pair validated or silently mix a new
PharmacoGx revision with an old dependency. If compatible dependency provenance
cannot be established, report the exact uncertainty and stop. For reproduction
of the dated verified environment, use the frozen pair above unchanged.

At the 2026-10-30 check, the local PharmacoGx branch was at
`84e8099fa508805f2f62d1e618458c9b78364ca5`, nine commits ahead of public feat/mcp,
with additional uncommitted skill edits. Those local changes are not installed
by the public GitHub branch. This skill collection includes local workflow
instructions separately. Do not substitute that local SHA in a GitHub install,
claim the public branch contains it, or push code as part of installation.
Verify the installed APIs before using features described by newer instructions.

PharmacoGx's published DESCRIPTION requires CoreGx without a minimum version;
CoreGx main requires R >= 4.1 and Bioconductor dependencies including
SummarizedExperiment, MultiAssayExperiment and BumpyMatrix. The matched pair
above was locally verified on R 4.5.3. A generic newer CoreGx (including the
separate sparse-LongTable feature branch) is not a tested replacement.
R 4.5.3 is the tested reproduction baseline, not the package's declared minimum.
For exact reproduction, require it. For a requested compatibility trial on another
hosted R version, verify the declared requirements and appropriate Bioconductor
dependency repositories, record the deviation, and validate the installed APIs.
Do not claim that such a trial reproduces the tested environment. Never change
R itself automatically. The recipe below selects the exact-reproduction route;
adapt the R guard only when the task calls for a different-runtime trial.

## Cloud installation recipe

Use a NEW R process without PharmacoGx/CoreGx already loaded, a new task-owned
working directory, and a host-approved writable persistent location. Save the
exact code and full stdout/stderr first. Run this inspected code through Biomni's
supported R tool only after cloud package setup is requested. This recipe is not
executed by uploading or reading the skills.

```r
stopifnot(getRversion() == "4.5.3")
if (any(c("PharmacoGx", "CoreGx") %in% loadedNamespaces())) {
  stop("Start a fresh R process before setup")
}
pgx_lib <- file.path(getwd(), "pgx-cloud-library")
if (file.exists(pgx_lib)) stop("Choose a new task directory; do not overwrite")
stopifnot(dir.create(pgx_lib))
pgx_lib <- normalizePath(pgx_lib)
.libPaths(c(pgx_lib, .libPaths()))
options(Ncpus = 1L)
Sys.setenv(PKG_SYSREQS = "false", PKG_USE_BIOCONDUCTOR = "true")
if (!requireNamespace("pak", quietly = TRUE)) {
  install.packages("pak", lib = pgx_lib, repos = "https://cloud.r-project.org")
}
pak::pkg_install(
  c(
    "bhklab/CoreGx@bf6d814abd3dc0fc98f9f419f430cc6473046cb2",
    "bhklab/PharmacoGx@28c58707eece80086bee75d8ef0e8afae96389ca",
    "digest", "curl", "jsonlite"
  ),
  lib = pgx_lib, dependencies = NA, upgrade = FALSE, ask = FALSE
)
writeLines(pgx_lib, "pgx-library-path.txt")
```

The joint request constrains both GitHub packages in the same dependency solve;
pak installs prerequisites before their dependents, including CoreGx before
PharmacoGx. CRAN/Bioconductor are still legitimate sources for required OTHER
dependencies; neither pinned Gx package may be silently replaced by a release.
Automatic OS-package installation is disabled. If building fails because a
compiler or system library is absent, retain the error and stop. Dependency
versions other than the two Gx pins are not fully locked; capture the resulting
installed package inventory and session information before scientific use.

Restart the hosted R process after installation. At the start of EVERY fresh
analysis process, select the same library before loading either package:

```r
pgx_lib <- normalizePath(readLines("pgx-library-path.txt", warn = FALSE), mustWork = TRUE)
.libPaths(c(pgx_lib, .libPaths()))
expected_version <- c(CoreGx = "2.7.3", PharmacoGx = "3.14.1")
expected <- c(
  CoreGx = "bf6d814abd3dc0fc98f9f419f430cc6473046cb2",
  PharmacoGx = "28c58707eece80086bee75d8ef0e8afae96389ca"
)
for (pkg in names(expected)) {
  ns <- loadNamespace(pkg)
  path <- normalizePath(getNamespaceInfo(ns, "path"))
  stopifnot(identical(dirname(path), pgx_lib))
  desc <- utils::packageDescription(pkg, lib.loc = pgx_lib)
  stopifnot(identical(desc$RemoteSha, unname(expected[[pkg]])),
    identical(desc$Version, unname(expected_version[[pkg]])),
    identical(desc$RemoteUsername, "bhklab"),
    identical(desc$RemoteRepo, pkg))
  print(desc[c("Package", "Version", "RemoteUsername", "RemoteRepo", "RemoteRef", "RemoteSha")])
}
required <- list(
  PharmacoGx = c("PharmacoSet2", "sampleInfo", "treatmentInfo", "mDataNames",
    "molecularProfiles", "treatmentResponse", "summarizeSensitivityProfiles"),
  CoreGx = "TreatmentResponseExperiment"
)
for (pkg in names(required)) {
  for (fn in required[[pkg]]) {
    value <- getExportedValue(pkg, fn)
    stopifnot(is.function(value))
    print(list(package = pkg, api = fn, arguments = names(formals(value))))
  }
}
print(sessionInfo())
```

The checks above verify loaded namespaces, package versions/commits and required
constructors/accessors. Inspect their signatures and relevant methods before
use. Exact SHA verification is authoritative even if RemoteRef records a commit
rather than feat/mcp. For a user-supplied PSet, separately verify its declared
checksum, read it with readRDS, confirm PharmacoSet class and run validObject;
report missing inputs or checksum/provenance mismatches before analysis. No
example data is required to load these skills.

Save the executed code, sessionInfo, installed package inventory, stdout/stderr
and exit status as downloadable task artifacts. Test a small artifact download
before the main analysis. If the runtime loses its library between tasks or
hides outputs, report that hosted limitation; installation alone is not a
successful analysis. Do not assume uploaded Markdown files are registered as
native Biomni Skills; explicitly read the relevant SKILL.md and references.

Sources:
- https://github.com/bhklab/PharmacoGx/tree/feat/mcp
- https://github.com/bhklab/PharmacoGx/blob/28c58707eece80086bee75d8ef0e8afae96389ca/DESCRIPTION
- https://github.com/bhklab/CoreGx/blob/bf6d814abd3dc0fc98f9f419f430cc6473046cb2/DESCRIPTION
- https://pak.r-lib.org/reference/pkg_install.html
- https://pak.r-lib.org/reference/pak_package_sources.html
- https://pak.r-lib.org/reference/pak-config.html

Recipe syntax and the pinned installed package APIs were checked on 2026-10-30.
This does not establish successful installation or execution in a hosted workspace.

## Troubleshooting

- If setup cannot create a task-owned persistent library, do not use the shared
  system library as a fallback; report the denied path or host limitation.
- If a namespace was loaded before installation, restart the hosted R process;
  changing .libPaths cannot replace an already loaded package.
- If the host changes working directories, use the recorded actual library
  location rather than guessing where pgx-library-path.txt moved. Verify the
  namespace path again in every new process.
- If package compilation, GitHub retrieval or dependency solving fails, preserve
  the first substantive error. Do not replace either pinned Gx package with a
  Bioconductor release, change the package pair without recording it, add API
  credentials to the instructions, or repeatedly reinstall without diagnosis.
- A different RemoteSha, missing provenance, unexpected namespace path or missing
  required API means verification failed. Keep installation success separate
  from verified package usability and from scientific correctness.
- Keep native loading warnings in stderr. The verified local pair has emitted a
  stack-imbalance warning; successful API checks do not establish that it is harmless.
