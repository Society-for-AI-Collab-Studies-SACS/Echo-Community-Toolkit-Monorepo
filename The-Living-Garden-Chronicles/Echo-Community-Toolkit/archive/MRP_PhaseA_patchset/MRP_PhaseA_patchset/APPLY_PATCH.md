# MRP Phase A Patchset (Diff-Ready)

Generated: 2025-10-13T05:14:22.138385Z
Repo root detected in zip: `Echo-Community-Toolkit/`

## Contents
- `patches/` — git-format patches (each file as an additive patch; plus verify script extension if present)
- `new_files/` — drop-in copies of the same files, arranged under the repo root
- `APPLY_PATCH.md` — this file

## Apply (Option A: git apply)
```bash
cd <your-clone-of-repo>
git checkout -b feat/mrp-phase-a
# Apply new-file patches (use git-am if you want commit metadata)
for p in archive/MRP_PhaseA_patchset/patches/*.patch; do git am "$p" || git apply "$p"; done
```

## Apply (Option B: copy files)
```bash
rsync -av archive/MRP_PhaseA_patchset/new_files/ ./
```

## Notes
- Adapters are **stubs** and raise `NotImplementedError` until wired to your LSB plane I/O.
- `tests/test_mrp.py` covers header and parity checks; carrier tests can be added once adapter is implemented.
- See `docs/MRP_Spec.md` for Phase A details.
