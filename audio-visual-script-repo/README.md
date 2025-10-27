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


## Validation & Integration Harness

Adapt Echo's `integration-validator` into an automated end-to-end test harness so every layer stays in sync:

- **Full pipeline simulation:** drive the frontend → Node API → Python engine flow by generating a sample script, persisting it, invoking audio synthesis, and requesting a ledger embed. Assert that each hop returns valid payloads and that ZeroMQ queues are responsive.
- **Schema conformance:** reuse the shared JSON schemas plus AJV (Node) / `jsonschema` (Python) to validate request/response bodies after every major step, ensuring persona IDs, timestamps, audio metadata, and ledger fields match the contract.
- **Ledger integrity:** plug in the Echo mantra ledger verification to extract the stego payload, confirming magic header, CRC32, Base64 envelope, and decoded mantra/script metadata. Treat any mismatch as a regression.
- **Audio verification:** confirm every generated clip exists, has non-zero duration, and matches the reported timing. Lightweight duration checks (ffprobe or `pydub`) help guarantee the TTS layer stays honest.
- **Automation:** wire the harness into CI (and optionally a `npm run validate:e2e` dev command) so regressions in schema, audio, or ledger handling surface immediately. Emit a structured report detailing which stages passed or failed.

## Harmonizer Consistency Pass

Bring Echo's Harmonizer concept into the new stack as a final consistency gate before publishing:

- **Multi-role alignment:** run MRP channel checks to verify persona dialogue, cues, and parity bits line up with the shared timeline and remain lossless across serialization boundaries.
- **Playback sanity:** simulate timeline playback (audio durations + cue metadata) to guarantee sequential delivery without gaps/overlaps and to ensure the frontend can safely highlight lines in sync with audio.
- **Scroll fidelity:** render the draft scroll (HTML/Markdown) and validate that persona glyphs, scene wrappers, and embedded media follow Echo's canonical structure. Flag any missing icons or malformed sections.
- **Publishing hook:** integrate the Harmonizer into the publish/deploy workflow so a script is only released after ledger payloads, memory logs, and distributed assets all pass verification. Persist the Harmonizer approval as part of the ledger/memory entry for traceability.

Together, the integration-validator and Harmonizer provide the safety net needed to ensure the Node backend, Python engine, and Echo-derived modules stay harmonized as the stack evolves.
