# RHZ Stylus v0.1.2 – Docs Site + Nav + Badges

Docs: https://acethedactyl.github.io/PlatformIO/

## Highlights
- MkDocs + Material docs site scaffolded and deployed via GitHub Pages.
- Expanded navigation (Firmware, Host Tools, CI & Releases) with new pages:
  - Install & Use, PSD Quicklook, Serial Logger, CI overview, Changelog.
- README now includes Docs, CI status, and Latest Release badges.

## Firmware & CI
- Version string is auto-injected from tags; firmware boot prints e.g. `{"boot":"rhz_stylus_maker","ver":"v0.1.2"}`.
- Tag-triggered releases upload firmware artifacts (bin/elf/bootloader/partitions).

