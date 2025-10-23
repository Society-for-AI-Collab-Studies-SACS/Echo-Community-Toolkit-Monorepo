# RHZ Stylus Firmware
[![Docs](https://img.shields.io/badge/docs-site-blue.svg)](https://acethedactyl.github.io/PlatformIO/)
[![CI](https://github.com/AceTheDactyl/PlatformIO/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AceTheDactyl/PlatformIO/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/AceTheDactyl/PlatformIO)](https://github.com/AceTheDactyl/PlatformIO/releases/latest)

[View Docs →](https://acethedactyl.github.io/PlatformIO/)

Initial scaffold for the RHZ Stylus maker firmware and supporting assets. This repository starts light so you can grow it alongside hardware bring-up and lab workflows.

## Minimum Specs
- **Toolchain:** PlatformIO CLI 6.x (with Espressif32 platform installed)
- **Board:** ESP32-S3 DevKitC or Adafruit Feather ESP32-S3 (USB-C, native USB CDC)
- **Python:** 3.10+ for host utilities and analysis notebooks
- **Storage:** 8 GB microSD (formatted FAT32) and SPI breakout with 33 Ohm series resistor on CLK

## Repository Layout
- `firmware/` — PlatformIO projects (add `stylus_maker_esp32s3/` or variants here)
- `docs/` — Architecture notes, bring-up checklists, and EMC/Safety references
- `hardware/` — BOMs, wiring tables, and PCB fabrication files
- `templates/` — Config examples for logging, calibration, or CI pipelines

Each directory currently contains placeholders to keep the structure under version control; replace them with real assets as you iterate.

## Getting Started
1. Install PlatformIO: `pip install platformio` or use the VS Code extension.
2. Copy the provided project template from `templates/` into `firmware/` and adjust board pins and logging paths.
3. Document wiring and calibration results under `docs/` so your bench notes travel with the code.
4. Track hardware revisions and sourcing in `hardware/` (BOM, layout, enclosure).

## How to Start
**Use this repo as a template (recommended)**
- Click `Use this template` on GitHub → pick a new name (e.g., `my-stylus-firmware`) and set visibility.
- Clone your new repo, then run from the project root:
  - `pip install --upgrade platformio` (or install the VS Code extension)
  - `python3 -m pip install --user numpy pandas scipy pyserial flake8`
  - `pio run` inside `firmware/stylus_maker_esp32s3` to confirm the toolchain.

**Clone directly**
- `git clone https://github.com/AceTheDactyl/PlatformIO.git` (or SSH equivalent).
- Rename the remote: `git remote rename origin upstream` so you can track upstream changes.
- Create your own repository and push to it when ready.

**Things to rename/customize immediately**
- `mkdocs.yml` → update `site_name`/`site_description` and verify the `repo_url`.
- `firmware/stylus_maker_esp32s3/platformio.ini` → set the default environment name, board, and upload baud.
- `.github/workflows/*.yml` → adjust badge links/secrets (e.g., `NPM_TOKEN`, Pages URL) for your org.
- `packages/rhz-stylus-arch/package.json` → change the npm scope (`@AceTheDactyl`) to yours or remove the package if unused.

For a fuller checklist of files to touch when cloning this as a template, see [docs/TEMPLATE_NOTES.md](docs/TEMPLATE_NOTES.md).

## Install & Use
[Full install guide → docs/INSTALL.md](docs/INSTALL.md)
- Build (PlatformIO CLI)
  - `cd firmware/stylus_maker_esp32s3`
  - `pio run`
- Flash (PlatformIO CLI)
  - Connect ESP32-S3 over USB-C, then: `pio run -t upload`
  - Monitor: `pio device monitor -b 115200`
  - On boot, you should see: `{"boot":"rhz_stylus_maker","ver":"vX.Y.Z"}`
- Flash (esptool.py direct, optional)
  - Download release assets (`bootloader.bin`, `partitions.bin`, `firmware.bin`).
  - Example for ESP32-S3 (check your serial port and chip variant):
    - `esptool.py --chip esp32s3 --port /dev/ttyACM0 --baud 460800 write_flash 0x0000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin`
- Host tools (Python 3.10+)
  - Install deps: `pip install numpy pandas scipy pyserial flake8`
  - Quick PSD check on a CSV: `python host/psd_quicklook.py sample.csv`
  - Serial logger (requires hardware): `python host/logger_serial.py --port /dev/ttyACM0 --baud 115200`

## Next Steps
- Flesh out the maker firmware skeleton (ADS1220 + AD7746 acquisition, LIS3MDL/OPT3001 polling, microSD logging).
- Add host-side scripts for serial capture, PSD checks, and VesselOS ingestion.
- Wire in CI hooks (lint, unit tests, hardware-in-the-loop smoke runs) as the project matures.

## Monorepo Workspaces & npm Package
- Workspaces
  - Root uses npm workspaces to manage packages under `packages/*`.
  - Root file: `package.json` (private, workspaces enabled).
  - List workspaces: `npm run ws:list` (from `RHZ Stylus firmware/`).

- Package: `@AceTheDactyl/rhz-stylus-arch`
  - Path: `packages/rhz-stylus-arch/`
  - Contents: ASCII architecture + LLM usage guide (CLI + API)
  - CLI examples:
    - `npx @AceTheDactyl/rhz-stylus-arch` (all)
    - `npx @AceTheDactyl/rhz-stylus-arch arch` (architecture only)
    - `npx @AceTheDactyl/rhz-stylus-arch llm` (LLM guide only)

- Install from GitHub Packages
  - Configure scope registry once:
    - `npm config set @AceTheDactyl:registry https://npm.pkg.github.com`
  - If prompted for auth, use a GitHub token with `read:packages` in `~/.npmrc`:
    - `//npm.pkg.github.com/:_authToken=YOUR_GH_TOKEN`
  - Install:
    - `npm install @AceTheDactyl/rhz-stylus-arch`

- Publish/Update (via CI)
  - Edit package content under `packages/rhz-stylus-arch/` and commit.
  - Create a tag to publish (version is read from the tag):
    - `git tag vX.Y.Z && git push origin vX.Y.Z`
  - GitHub Actions workflow `.github/workflows/npm-publish.yml` will:
    - Set package version to `X.Y.Z`
    - Publish to GitHub Packages using a Personal Access Token (classic) stored as repo secret `NPM_TOKEN`.
      - Required PAT scopes: `read:packages`, `write:packages` (add `delete:packages` only if you need to yank).
      - Add under: Settings → Secrets and variables → Actions → New repository secret → Name: `NPM_TOKEN`.

- Manual dry-run
  - From root: `npm run ws:pack` (creates dry-run tarballs for workspaces)
