# Audio-Visual Script Repository

This monorepo houses the full-stack platform for creating, storing, and playing structured multimedia scripts. It is designed to reuse the Echo Community Toolkit's memory, ledger, and multi-persona protocols while adding a modern web editor/player experience.

## Workspaces

- `frontend/` – React/TypeScript editor and playback UI.
- `backend/` – Node.js API and integration layer that coordinates with the Python narrative engine.
- `python/` – Narrative engine, audio synthesis, and bridged Echo toolkit modules.

Additional directories provide content storage (`scripts/`), schema definitions (`integration/schemas/`), integration outputs (`integration/outputs/`), ledger artifacts (`integration/ledger/`), and development tooling (`tools/`).

## Getting Started

```bash
npm install           # installs workspace dependencies
npm run dev           # runs frontend and backend in parallel (requires python service started separately)
```

The Python engine will live under `python/engine/` with its own virtual environment and dependencies listed in `requirements.txt`.

## Next Steps

1. Populate the workspace packages (`frontend/package.json`, `backend/package.json`).
2. Vendor Echo toolkit modules into `python/engine/`.
3. Define the `Script` JSON schema under `integration/schemas/` and generate TypeScript types via `tools/generate-types.js`.
4. Stand up the ZeroMQ bridge between backend and Python services.

This scaffold provides the foundation for committing the monorepo into the broader VesselOS ecosystem.
