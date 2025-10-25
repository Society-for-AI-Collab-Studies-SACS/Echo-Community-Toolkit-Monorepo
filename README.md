# VesselOS Unified Monorepo (Package)

This package contains the unified VesselOS scaffold, scripts, CI, and Docker config to generate a consolidated monorepo with preserved history via git subtree (when run online). It also supports an offline mode that scaffolds a ready structure for local iteration.

## Quick Start

1) Enter the package directory

```
cd vesselos_unified_monorepo
```

2) Generate the monorepo (offline, no network)

```
./scripts/vesselos_monorepo_consolidation.sh --offline --force
```

This creates `vesselos_unified_monorepo/vesselos-monorepo/` with:
- agents/ (sigprint, journal, stubs for limnus/garden)
- firmware/esp32s3 (original + enhanced targets)
- shared/ (protocols + utils)
- docker/ (Dockerfile + compose)
- scripts/ (verification and helpers)
- .github/workflows/monorepo-ci-enhanced.yml

3) Verify the structure

```
cd vesselos-monorepo
./scripts/verify_integration_enhanced.sh --tests
```

Note: In environments without Docker, verification will report Docker-related failures; this is expected and non-destructive.

## Online (History-Preserving) Imports

Run without `--offline` and set `GITHUB_ORG` to your org; the script will add remotes and import each repo to the target path via `git subtree add`, tagging each import (`import/<name>`).

```
GITHUB_ORG=your-org ./scripts/vesselos_monorepo_consolidation.sh --force
```

## Helper

To perform an isolated dry run and verification without touching the source tree:

```
./scripts/run_local_setup_and_verify.sh --tests
```

Artifacts are created under `../.local-checks/` and preserved unless `--cleanup` is provided.
