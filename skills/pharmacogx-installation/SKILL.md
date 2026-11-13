---
name: pharmacogx-installation
description: Install and verify PharmacoGx from BHKLab's feat/mcp GitHub branch with a compatible CoreGx GitHub revision. Use for hosted Biomni R setup, exact-commit reproduction, branch updates, or diagnosing package provenance and load failures; do not substitute the standard Bioconductor PharmacoGx release.
---

# PharmacoGx MCP-branch installation

## This repository

For this repository, use `pixi run setup` followed by `pixi run verify-pgx`.
The current package pins and checks live in
`workflow/scripts/setup/pharmacogx.R`; see `docs/agent_setup.md`.
Do not install packages during a benchmark run. The older hosted reproduction
recipe below is a separate historical environment, not this repository setup.

Prepare a verified R environment for the companion pharmacogenomic skills.
Prefer the user's hosted Biomni R workspace when that is their chosen host;
this workflow does not require installing software on their workstation.
Read [cloud installation and verification](references/cloud-install.md) before
installing. It contains the exact package specifications, dependency order,
namespace/API checks and troubleshooting steps.

## Select the intended source

The intended package source is **`bhklab/PharmacoGx@feat/mcp`**.
Do not install an unqualified PharmacoGx package or substitute its Bioconductor
release. Required other dependencies can still come from CRAN/Bioconductor.

Choose the route matching the request:

- **Reproduce the verified environment:** use PharmacoGx commit
  `28c58707eece80086bee75d8ef0e8afae96389ca` with CoreGx commit
  `bf6d814abd3dc0fc98f9f419f430cc6473046cb2` and R 4.5.3.
- **Install the latest published MCP branch:** resolve `feat/mcp` to a full
  public GitHub SHA at execution time. On 2026-10-30 it matched the frozen
  PharmacoGx commit above. If it advances, inspect that revision's dependency
  requirements and validate its matching CoreGx target before analysis. Record
  the new pins and actual package versions; a moving branch name is insufficient.

The local development branch at the same check was
`84e8099fa508805f2f62d1e618458c9b78364ca5`, nine commits ahead, with uncommitted
skill changes. These are distinct from the installable public branch. Never
claim a remote install contains unpushed changes or push them as a setup step.

## Execute within the requested environment

1. Confirm R execution, a new process, a writable task-owned library, package
   retrieval and required compilation are supported by the host. Uploaded
   instructions alone do not establish these capabilities. Reuse an existing
   environment only after verifying the actual loaded package provenance.
2. When setup is authorized by the user's task, follow the reference recipe
   in a fresh process. Constrain both GitHub packages in the dependency solve:
   dependencies and CoreGx must be available before PharmacoGx. Keep installation
   out of shared system libraries; do not install OS packages or change R
   automatically. A prior setup request need not be reconfirmed merely because
   this skill is now loaded.
3. Restart R after installation. Select the recorded library before loading
   either Gx package. Verify namespace paths, package versions, GitHub owner/repo,
   RemoteSha, required exports and method signatures using the reference checks.
4. Save the executed installation/verification code, dependency inventory,
   sessionInfo, stdout, stderr and exit status as downloadable task artifacts.
   Confirm output retrieval and library availability in subsequent processes.

R 4.5.3 is a tested baseline, not a universal minimum. A requested trial on a
different supported R version must be reported and validated separately; do not
represent it as exact reproduction. The reference explains this distinction.

## Completion and failure

Report the resolved branch/commit, CoreGx target, actual loaded paths and
versions, successful API checks, warnings and remaining host restrictions.
Distinguish code merely generated, installation attempted, and a verified usable
environment. Do not claim a hosted pass from local verification alone.

If provenance, dependencies, compilation, permissions, runtime restart or
artifact export blocks the task, preserve the concrete error and stop that
operation. Do not silently fall back to stable packages or hide failure by
changing the requested analysis. No dataset download or scientific analysis is
part of this installation skill.
