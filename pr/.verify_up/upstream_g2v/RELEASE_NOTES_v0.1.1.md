# RHZ Stylus v0.1.1 – Install & Use

Docs: https://acethedactyl.github.io/PlatformIO/

## Install (Firmware)
- PlatformIO (recommended)
  - `cd firmware/stylus_maker_esp32s3`
  - `pio run`
  - Flash: `pio run -t upload`
  - Monitor: `pio device monitor -b 115200`
  - On boot you should see: `{"boot":"rhz_stylus_maker","ver":"v0.1.1"}`
- Esptool (manual flash)
  - Download release assets: `bootloader.bin`, `partitions.bin`, `firmware.bin`.
  - Example (adjust serial port):
    - `esptool.py --chip esp32s3 --port /dev/ttyACM0 --baud 460800 write_flash 0x0000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin`

## Host Tools
- Install deps: `pip install numpy pandas scipy pyserial flake8`
- PSD quicklook: `python host/psd_quicklook.py sample.csv`
- Serial logging (with hardware): `python host/logger_serial.py --port /dev/ttyACM0 --baud 115200`

## Changelog (v0.1.1)
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
