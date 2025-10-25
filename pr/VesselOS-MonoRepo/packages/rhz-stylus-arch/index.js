// RHZ Stylus architecture ASCII and LLM usage guide (exported API)

export const architecture = `
System Architecture (ASCII)

+----------------------------------------------------------------------------------------------------+
|                                        RHZ Stylus System                                           |
+----------------------------------------------------------------------------------------------------+
|                                         Data/Control Flow                                          |
|                                                                                                    |
|  [Sensors/Actuators] --> [Drivers] --> [Stage/Control] --> [Aggregator/Logger] --> SD | USB Serial |
|          ^                                                                                 |       |
|          |                                                                                 v       |
|       [PPS/EXT TRIG] <------------------------------------------------------------- [Host Tools]   |
+----------------------------------------------------------------------------------------------------+

Firmware (ESP32‑S3, PlatformIO)
+----------------------------------------------------------------------------------------------------+
| Board I/O                                                                                          |
|  - SPI: ADS1220 (24‑bit ADC), microSD                                                              |
|  - I2C: AD7746 (CDC), LIS3MDL (mag), OPT3001 (lux)                                                 |
|  - PWM: DRV8833 coil driver                                                                        |
|  - PPS/Trigger GPIO, LED                                                                           |
+-------------------+--------------------------+----------------------+------------------------------+
| Sensor Drivers    | Stage/Emit Controller    | Aggregator & Logger  | Build/Version                |
|  - ADS1220 (SPI)  |  - 6x stages (S1..S6)    |  - CSV to SD         |  - platformio.ini            |
|  - AD7746 (I2C)   |  - Emit window duty/PWM  |  - JSON to USB CDC   |  - version.py ->             |
|  - LIS3MDL (I2C)  |  - PPS/TRIG pulses       |  - 1 Hz snapshots    |    src/version_auto.h        |
|  - OPT3001 (I2C)  |  - LED status            |  - Ring of latest    |  - RHZZ_VERSION_STR printed  |
+-------------------+--------------------------+----------------------+------------------------------+
| Key Files                                                                                          |
|  - firmware/stylus_maker_esp32s3/src/main.cpp                                                      |
|  - firmware/stylus_maker_esp32s3/platformio.ini                                                    |
|  - firmware/stylus_maker_esp32s3/version.py (pre: extra_script)                                    |
|  - firmware/stylus_maker_esp32s3/lib/Adafruit_OPT3001/... (minimal stub for CI)                    |
+----------------------------------------------------------------------------------------------------+

USB/SD Interface
+----------------------------------------------------------------------------------------------------+
|  - USB CDC: JSON lines (boot/version, sensor snapshots)                                            |
|  - microSD: CSV logs (t_ms, stage, emit, ads_raw, cap_raw, lux, mag_x, mag_y, mag_z)              |
+----------------------------------------------------------------------------------------------------+

Host Tools (Python)
+----------------------------------------------------------------------------------------------------+
| logger_serial.py              | psd_quicklook.py                                                   |
|  - Capture USB JSON           |  - Compute PSD from CSV                                            |
|  - Optional CSV persistence   |  - Validate presence of known lines (e.g., ~444 Hz in S3)         |
+----------------------------------------------------------------------------------------------------+
| Key Files:                                                                                         |
|  - host/logger_serial.py                                                                            |
|  - host/psd_quicklook.py                                                                            |
+----------------------------------------------------------------------------------------------------+

CI, Docs, Releases
+----------------------------------------------------------------------------------------------------+
| GitHub Actions: ci.yml                                                                             |
|  - Checkout, cache pip/PIO  - Build firmware (pio run)  - Lint Python (flake8)                     |
|  - py_compile host scripts   - Synthetic CSV + PSD test  - Upload build logs & artifacts           |
|  - On tags v*: GitHub Release (bin/elf/bootloader/partitions)                                      |
+----------------------------------------------------------------------------------------------------+
| Docs Site (MkDocs): docs.yml + mkdocs.yml                                                          |
|  - Builds docs/ to Pages (Material theme)                                                          |
|  - Nav: Firmware, Host Tools, CI & Releases, Changelog                                             |
+----------------------------------------------------------------------------------------------------+
`;

export const llmGuide = `
LLM Usage Guide (How to Work With Modules)

- Principles
  - Keep edits within module scope; minimal, documented changes.
  - C++ (Arduino): 2-space indent, brace on same line. Python: 4-space indent; stdlib → third-party → local imports.
  - Use Conventional Commits and update docs/CI when behavior changes.

- Common Tasks
  - Add/modify sensor: edit firmware/stylus_maker_esp32s3/src/main.cpp and platformio.ini; extend CSV/JSON outputs; pio run.
  - Change stages/PWM: edit main.cpp (stage array, emit window, coilSet); rebuild.
  - Host analysis: edit host/*.py; ensure flake8 + py_compile pass; document usage under docs/host_*.md and add to mkdocs.yml nav.
  - Releases: tag vX.Y.Z; CI builds and attaches artifacts; version injected via src/version_auto.h.
  - Docs: add pages in docs/; update mkdocs.yml; Pages deploy on push to main.

- Contracts
  - CSV header: t_ms,stage,emit,ads_raw,cap_raw,lux,mag_x,mag_y,mag_z
  - USB JSON: t_ms, stage, emit, tx.f, rx.ads_raw, cap_raw, lux, mag_uT[3]

- Quick Validation
  - Firmware: cd firmware/stylus_maker_esp32s3; pio run
  - Lint: flake8 host/ --max-line-length=120
  - Syntax: python -m py_compile host/logger_serial.py host/psd_quicklook.py
  - PSD sample: python host/psd_quicklook.py sample.csv
`;

export function getArchitecture() { return architecture; }
export function getLlmGuide() { return llmGuide; }

