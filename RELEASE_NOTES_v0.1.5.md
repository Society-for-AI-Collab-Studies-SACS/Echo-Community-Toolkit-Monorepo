# RHZ Stylus v0.1.5 – MkDocs Navigation Fix for Pages

Docs: https://acethedactyl.github.io/PlatformIO/

## Highlights
- Fixes MkDocs navigation so GitHub Pages build picks up actual docs files.

## Details
- Docs
  - Navigation entries now reference repo-relative paths (no duplicate `docs/` prefix).
  - Quick link sections refreshed to match the new nav layout.

## Firmware & Release Flow
- No firmware or host changes in this release.
- Pushing the tag re-runs the Docs workflow to republish the site.
