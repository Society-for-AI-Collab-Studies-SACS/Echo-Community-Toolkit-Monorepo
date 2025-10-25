# Continuous Integration (CI)

The repository uses GitHub Actions to build firmware, run host checks, and publish releases.

## What CI Does
- Build firmware via PlatformIO (`pio run`) for ESP32‑S3 to catch compile errors.
- Install Python deps and lint host scripts (`flake8 host/`).
- Run a synthetic PSD quicklook test to validate the analysis path.
- Upload build logs and firmware artifacts on every run.
- On tags `v*`, publish a GitHub Release with the binaries.

## Release Assets
- `firmware.bin` (application)
- `firmware.elf` (symbolized build)
- `bootloader.bin`, `partitions.bin`

## Docs Site
- MkDocs + Material theme built on push to `main` and deployed to GitHub Pages.
- Enable in Settings → Pages → Source: GitHub Actions.

