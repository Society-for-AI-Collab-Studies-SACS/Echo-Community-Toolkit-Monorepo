# RHZ Stylus v0.1.3 – CI Matrix, CLI/API Tests, Monorepo

Docs: https://acethedactyl.github.io/PlatformIO/

## Highlights
- Added Node matrix (18/20) to test the npm CLI/API across versions.
- Added CLI (arch/llm) and ESM API tests for `@AceTheDactyl/rhz-stylus-arch`.
- Hardened CI path handling and added debug-on-failure steps around CLI tests.
- Monorepo workspaces added at root; npm package manifest tracked.

## Details
- CI
  - Node matrix job validates CLI/API on Node 18 and 20
  - Workspace `npm pack` dry-run ensures packability each run
  - Debug steps list package layout if a CLI test fails
- npm / Monorepo
  - Root `package.json` with workspaces (`packages/*`)
  - `@AceTheDactyl/rhz-stylus-arch`: ASCII architecture + LLM guide (CLI + API)

## Firmware & Release Flow
- Firmware version prints `RHZZ_VERSION_STR` from tag/describe
- On tag `vX.Y.Z`, CI builds firmware and uploads release assets

