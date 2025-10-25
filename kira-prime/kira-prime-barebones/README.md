# Kira Prime Barebones

A minimal repository scaffold with local bare remote mirror and GitHub remote.

## Quickstart

- Clone (if not already local):
  - `git clone <this-repo-url>`
- Build (no dependencies):
  - `make build`
- Test (placeholder):
  - `make test`

## Requirements
- `git` for version control
- `gh` (GitHub CLI) to create/manage the GitHub remote (optional after creation)
- `make` (standard on most systems)

## Scripts
- `make build` — creates `dist/ok.txt` as a placeholder build artifact
- `make clean` — removes `dist/`

## Remotes
- `origin` — GitHub remote (created via `gh repo create`)
- `bare` — local bare mirror at `~/.remote/<name>.git`

Push to both mirrors:

```bash
git push origin main
git push bare main
```

## Notes
- This repo is intentionally barebones to serve as a template or starting point.
- Replace the Makefile with your actual build steps when you add code.
