# Repository Guidelines

## Project Structure & Module Organization
- `firmware/stylus_maker_esp32s3/`: PlatformIO project for the ESP32-S3 stylus; Arduino sources in `src/`, headers in `include/`, shared helpers in `lib/`, and build flags inside `platformio.ini`.
- `host/`: Python utilities for serial capture (`logger_serial.py`) and PSD inspection (`psd_quicklook.py`); add fixtures under `host/fixtures/` when prototyping pipelines.
- `docs/`: MkDocs content for bring-up, CI notes, and template guidance (`TEMPLATE_NOTES.md`); run `mkdocs serve` while editing.
- `hardware/`: Bills of materials, wiring notes, and enclosure references that ship with firmware releases.
- `templates/`: Copy-once scaffolds—firmware configs, calibration CSVs, or BOM shells—that keep new stages consistent.
- `packages/rhz-stylus-arch/`: npm workspace exporting the ASCII system architecture and LLM usage guide (CLI + ESM).

## Build, Test, and Development Commands
- Firmware build: `cd firmware/stylus_maker_esp32s3 && pio run -v` (verifies dependencies, emits verbose logs).
- Firmware flash: `pio run -t upload` followed by `pio device monitor -b 115200` for bring-up logs.
- PlatformIO diagnostics: `pio check` to run static analysis once modules solidify.
- Host tooling: `python3 -m py_compile host/logger_serial.py host/psd_quicklook.py` and `flake8 host/ --max-line-length=120`.
- PSD smoke test: reuse CI’s synthetic CSV snippet or `python3 host/psd_quicklook.py data/<capture>.csv` to validate spectra.
- npm workspace sanity: `npm run ws:list`, `npm run ws:pack`, and `node packages/rhz-stylus-arch/bin/cli.js arch`.
- Docs preview: `mkdocs serve --dev-addr 0.0.0.0:8000`.

## Coding Style & Naming Conventions
- Python: 4-space indent, `snake_case` functions/variables, CapWords classes, module-level constants in `ALL_CAPS`. Import blocks order: stdlib → third-party → local, separated by blank lines. Lint with `flake8` before commits.
- C++ (PlatformIO): 2-space indents within blocks, brace-on-same-line, descriptive `snake_case` functions, `ALL_CAPS` compile-time constants. Add brief comments for timing-critical hardware interactions only.
- JavaScript/Node: prefer `const`/`let`, keep CLI entrypoints executable (`chmod +x`), and export ESM-friendly APIs.

## Testing Guidelines
- Firmware: compile via `pio run` every change; add Unity tests under `firmware/.../test/` as modules grow; treat warnings as failures.
- Host: stage pytest smoke tests in `tests/` using fixtures in `tests/fixtures/`; run with `python3 -m pytest -q`.
- PSD validation: ensure synthetic inputs show a dominant 444 Hz peak when running the quicklook script; capture logs for regressions.
- CI (`.github/workflows/ci.yml`) mirrors these steps, uploads `pio_build.log`, and publishes firmware artifacts for tagged releases.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat(firmware):`, `fix(host):`, `docs:`). One logical change per commit; include updated docs/configs alongside code.
- PRs should outline intent, enumerate major edits, reference issues, and list verification (`pio run`, `flake8`, PSD sample). Attach artifacts or screenshots for analysis/UI changes.
- Before tagging, update `CHANGELOG.md` and drop release notes (`RELEASE_NOTES_vX.Y.Z.md`), then `git tag vX.Y.Z` to trigger automated publishing.

## Security & Configuration Tips
- Store secrets (Wi-Fi credentials, PATs) in PlatformIO environments or GitHub Actions secrets; never hard-code them.
- Sanitize lab captures before committing; strip GPS, operator metadata, or customer identifiers.
- Required Actions secrets: `NPM_TOKEN` for GitHub Packages, plus any project-specific tokens referenced in workflows.
- Keep `.env` files out of version control; copy a sanitized example to `templates/`.

## Use Cases & Snippet Examples
- **Bench bring-up:** flash firmware, open the serial console, and capture boot diagnostics.
  ```bash
  cd firmware/stylus_maker_esp32s3
  pio run -t upload
  pio device monitor -b 115200 | tee boot.log
  ```
- **Synthetic PSD regression:** create a test CSV in-line and confirm the 444 Hz peak remains dominant.
  ```bash
  python3 - <<'PY' > sample.csv
  from math import sin, pi
  fs, freq = 1000, 444
  print("t_ms,stage,emit,tx_f,ads_raw,cap_raw,lux,mag_x,mag_y,mag_z")
  for i in range(2048):
      val = sin(2*pi*freq*(i/fs))
      emit = int(i > 1847)  # last ~200 samples mark the emit window
      print(f"{i},S3,{emit},{freq},{int(1000*val)},32768,50.0,0,0,0")
  PY
  python3 host/psd_quicklook.py sample.csv
  ```
- **Architecture export:** publish docs snippets for downstream teams via the npm CLI.
  ```bash
  node packages/rhz-stylus-arch/bin/cli.js arch > docs/output/architecture.txt
  node packages/rhz-stylus-arch/bin/cli.js llm  > docs/output/llm-guide.txt
  ```

## Future Potential
- Add hardware-in-the-loop smoke tests that replay CSV captures through `logger_serial.py`.
- Expand npm workspaces with calibration wizards or bill-of-material generators.
- Integrate `pio check` and clang-tidy into CI once firmware modules stabilize.
- Publish versioned MkDocs sites per release tag to snapshot lab procedures over time.
