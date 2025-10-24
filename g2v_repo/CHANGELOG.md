# Changelog

All notable changes to this project will be documented in this file.
This project adheres to Conventional Commits.

## v0.1.5 — 2025-10-18

- Docs
  - docs(site): fix MkDocs navigation to use repo-relative paths for GitHub Pages build

## v0.1.3 — 2025-10-18

- CI / Tests
  - ci(test): add Node matrix for CLI/API tests (Node 18, 20)
  - ci(test): add CLI and ESM API tests for `@AceTheDactyl/rhz-stylus-arch`
  - ci(test): robust path handling for space-containing directories
  - ci(test): add workspace-level `npm pack` dry-run
  - ci(test): add debug-on-failure steps around CLI tests (print package layout)

- npm / Monorepo
  - feat(npm): scaffold `@AceTheDactyl/rhz-stylus-arch` (CLI + API)
  - chore(monorepo): add root `package.json` with workspaces (`packages/*`)
  - chore(npm): ensure `packages/rhz-stylus-arch/package.json` is tracked

- Docs
  - docs(monorepo): add README section documenting workspaces and publish flow

## v0.1.2 — 2025-10-18

- Docs
  - docs(site): scaffold MkDocs + Material theme and GitHub Pages deployment
  - docs(site): expand navigation (Firmware, Host Tools, CI & Releases)
  - docs: add Install & Use guide under docs/INSTALL.md and link from README
  - docs: add host tool pages (PSD quicklook, Serial logger)
  - docs(site): add docs/CHANGELOG.md page mirroring repo changelog
  - docs: badges in README (Docs, CI, Release) and explicit View Docs link

## v0.1.1 — 2025-10-18

- Features
  - feat(ci+fw): auto-inject RHZZ_VERSION from tag or `git describe` via PlatformIO `extra_scripts` (defaults to "dev" locally)
  - feat(ci): upload firmware artifacts and publish GitHub Release on `v*` tags

- Fixes
  - fix(firmware): print version safely (avoid `F()` with macros; use generated header `version_auto.h`)
  - fix(ci): correctly propagate `pio run` exit status when tee-ing logs
  - fix(ci+fw): ensure quoted version string by generating `src/version_auto.h` in pre-build

- CI
  - ci: fetch tags for accurate `git describe`
  - ci: attach verbose PlatformIO logs as artifacts for debugging

## v0.1.0 — 2025-10-18

Initial public release of the RHZ Stylus maker firmware scaffold and CI.

- Fixes
  - fix(firmware): include Adafruit_Sensor.h to satisfy sensors_event_t with LIS3MDL/OPT3001
  - fix(firmware): avoid F() + macro concat for RHZZ_VERSION; stringify and print safely
  - fix(firmware): depend on Adafruit Unified Sensor; switch LIS3MDL to GitHub source
  - fix(firmware): use ESP32 core SD; remove external SD lib dep
  - fix(firmware): stabilize OPT3001 usage for CI; vendor a minimal stub to unblock builds

- CI
  - ci: add GitHub Actions workflow to build firmware, lint host scripts, run PSD quicklook
  - ci: cache pip and PlatformIO dependencies for faster runs
  - ci: upload verbose PlatformIO build logs and firmware artifacts (.bin/.elf)
  - ci: ensure pio run exit code is propagated when tee-ing logs
  - ci(release): on v* tags, publish a GitHub Release and attach firmware assets

- Docs/Chore
  - docs: resolve README merge and preserve RHZ Stylus content
  - chore: bootstrap RHZ Stylus firmware repo structure
