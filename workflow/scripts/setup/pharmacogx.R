# Run from the repository root through `pixi run setup`.
pins <- c(
  CoreGx = "f760bc7c230f892722d72634001054adad2ea0f0",
  PharmacoGx = "a7aa4d727e521ab63f68f2dbfc16697e5e4764cc"
)
lib <- file.path(getwd(), ".pixi", "r-library")
check_only <- "--check" %in% commandArgs(trailingOnly = TRUE)
if (!dir.exists(lib) && !check_only) dir.create(lib, recursive = TRUE)
if (!dir.exists(lib)) stop("Run pixi run setup first")
lib <- normalizePath(lib)
.libPaths(c(lib, .libPaths()))
if (any(names(pins) %in% loadedNamespaces())) stop("Start a fresh R process")

matches <- function(pkg) {
  desc <- suppressWarnings(utils::packageDescription(pkg, lib.loc = lib))
  !is.na(desc)[1L] && identical(desc$RemoteSha, unname(pins[[pkg]]))
}
if (!check_only) {
  if (!requireNamespace("remotes", quietly = TRUE) ||
      !requireNamespace("BiocManager", quietly = TRUE)) {
    stop("Install the Pixi environment first; remotes and BiocManager are required")
  }
  options(repos = BiocManager::repositories(), Ncpus = 2L)
  for (pkg in names(pins)) {
    if (!matches(pkg)) {
      remotes::install_github(
        paste0("bhklab/", pkg, "@", pins[[pkg]]), lib = lib,
        dependencies = NA, upgrade = "never", build_vignettes = FALSE,
        force = TRUE
      )
    }
  }
}
if (!all(vapply(names(pins), matches, logical(1)))) {
  stop("Package pins missing or mismatched; run pixi run setup")
}
# Load before the reporting loop so package startup runs at top level.
loadNamespace("CoreGx")
loadNamespace("PharmacoGx")
for (pkg in names(pins)) {
  namespace <- loadNamespace(pkg)
  path <- normalizePath(getNamespaceInfo(namespace, "path"))
  if (!identical(dirname(path), lib)) stop("Wrong library loaded for ", pkg)
  desc <- utils::packageDescription(pkg, lib.loc = lib)
  cat(pkg, desc$Version, desc$RemoteSha, path, "\n")
}
required <- c("PharmacoSet2", "sampleInfo", "treatmentInfo", "mDataNames", "computeAAC")
missing <- setdiff(required, getNamespaceExports("PharmacoGx"))
if (length(missing)) stop("Missing PharmacoGx exports: ", paste(missing, collapse = ", "))
cat("Pinned package provenance and required APIs verified.\n")
