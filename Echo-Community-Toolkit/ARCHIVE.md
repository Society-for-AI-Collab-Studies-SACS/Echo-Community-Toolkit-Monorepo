# Archive Overview

This repository keeps every delivery of the Echo Community Toolkit intact.  
Anything under `archive/` is preserved for provenance and forensic traceability;
the active implementation lives in the top-level `src/`, `tests/`, `examples/`,
`assets/`, and supporting scripts.

## archive/Echo-Community-Toolkit_patched_wired/
- Original “patched wired” drop shared upstream. Mirrors the full toolkit as it
  existed in that bundle (scripts, tests, docs, payloads).  
- Keep for diffing against the canonical tree; do not import from it in tests.

## archive/MRP_PhaseA_patchset/
- Zip-unpacked patchset release. Contains raw patch files plus the “new files”
  directory used to stage MRP Phase-A additions.  
- Useful when you need to reconstitute the patchset exactly as shipped.

## archive/comprehensive_system_test/ and archive/comprehensive_system_test.py
- Self-contained validation harness (scripts, assets, report) that came with the
  comprehensive system test handoff.  
- Replaced in the active tree by `final_validation.py` and the maintained
  modules under `src/` / `tests/`. Run from here only when you must reproduce
  the historical flow.

## Working With the Archive
- Pytest is configured to ignore `archive/` to avoid module-name collisions.  
- To compare any archived file with the modern implementation, run commands such
  as `git diff -- archive/... src/...` or inspect the preserved patch files.
- Treat everything beneath `archive/` as read-only snapshots; stage updates only
  when you intentionally capture a new historical drop.
