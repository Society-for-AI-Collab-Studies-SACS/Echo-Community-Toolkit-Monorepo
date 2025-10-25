# RHZ Stylus – Install & Use

This guide covers building and flashing the ESP32‑S3 firmware and running the host tools.

## Prerequisites
- PlatformIO Core (CLI): `pip install platformio` or use the VS Code extension
- Board: ESP32‑S3 DevKitC or Adafruit Feather ESP32‑S3 (USB‑C)
- Python 3.10+ (for host tools)

## Firmware (PlatformIO)
- Build
  - `cd firmware/stylus_maker_esp32s3`
  - `pio run`
- Flash
  - Connect ESP32‑S3 via USB‑C
  - `pio run -t upload`
- Monitor
  - `pio device monitor -b 115200`
  - On boot you should see a JSON line with the embedded version, for example:
    - `{"boot":"rhz_stylus_maker","ver":"vX.Y.Z"}`

Notes
- Version is injected automatically in CI from a tag (e.g., `v0.1.1`) or `git describe`; local builds default to `"dev"`.
- The build generates `src/version_auto.h` at compile time with `RHZZ_VERSION_STR`.

## Firmware (esptool.py, optional)
If you prefer manual flashing, download the release assets from GitHub (`bootloader.bin`, `partitions.bin`, `firmware.bin`) and run:

```
esptool.py --chip esp32s3 --port /dev/ttyACM0 --baud 460800 \
  write_flash 0x0000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin
```

Adjust `--port` for your system (e.g., `/dev/ttyUSB0`, `COM5`).

## Host Tools
- Install dependencies
  - `pip install numpy pandas scipy pyserial flake8`
- PSD quicklook on a CSV
  - `python host/psd_quicklook.py sample.csv`
- Serial logging (requires hardware)
  - `python host/logger_serial.py --port /dev/ttyACM0 --baud 115200`

Troubleshooting
- If PlatformIO installs toolchains each run in CI, that’s expected on fresh runners; caching is enabled in the workflow.
- If flashing fails, press and hold BOOT (or reset into download mode) on your ESP32‑S3 board, then retry upload.

