# Template Notes

Guidance for adapting this repository when you create a new project (via **Use this template** or manual clone).

## 1. Update Identifiers & Branding
- `mkdocs.yml` — change `site_name`, `site_description`, and `repo_url` to match your project.
- `README.md` — replace badges/links with your repository slug.
- `.github/workflows/*.yml` — ensure workflow names, badge URLs, and artifact names align with your org.

## 2. PlatformIO Project
- `firmware/stylus_maker_esp32s3/platformio.ini`
  - Set the correct `default_envs`, board (`board = esp32s3-devkitc-1`, etc.), and upload speed.
  - Adjust `build_flags` and monitor settings for your hardware.
- `firmware/stylus_maker_esp32s3/src/` — replace placeholder source with your firmware.
- Remove unused environments or libraries to keep builds lean.

## 3. Host Tools & Python Packaging
- `host/` — update script entry points, default serial ports, and CSV expectations.
- `requirements*.txt` — pin versions if you publish tooling.
- `tests/` — add fixtures and smoke tests so CI can run without hardware.

## 4. npm Workspace (optional)
- If you plan to publish the `packages/rhz-stylus-arch` package:
  - Update `name` (scope) and `author` in `packages/rhz-stylus-arch/package.json`.
  - Replace the CLI/API content (`bin/cli.js`, `index.js`) with your own docs.
- If you do **not** need the npm package:
  - Delete `packages/rhz-stylus-arch/` and remove workspace commands from `package.json`.
  - Clean up related CI steps in `.github/workflows/ci.yml`.

## 5. Secrets & GitHub Actions
- Create repo secrets under **Settings → Secrets and variables → Actions**:
  - `NPM_TOKEN` — PAT (classic) with `read:packages`, `write:packages` if you keep npm publishing.
  - Add any additional tokens (e.g., Wi-Fi credentials) via `.env` or PlatformIO `extra_scripts`.
- Review the workflows (`ci.yml`, `docs.yml`, `npm-publish.yml`, `jekyll-gh-pages.yml`) and disable jobs you do not use.

## 6. Documentation
- Audit everything under `docs/`:
  - Remove placeholder headings you do not plan to fill.
  - Add hardware-specific wiring images, calibration steps, and bring-up notes.
- Run `mkdocs serve` locally while editing to preview changes.

## 7. Final Checks
- Run `pio run` and `pio test` (if configured) to ensure firmware builds cleanly.
- Execute `python3 -m py_compile host/*.py` and `flake8 host/ --max-line-length=120`.
- Trigger the Docs workflow (`mkdocs build`) before opening your repo to the public.
- Update `CHANGELOG.md` and create a release tag (`git tag vX.Y.Z`) when you are ready to publish artifacts.
