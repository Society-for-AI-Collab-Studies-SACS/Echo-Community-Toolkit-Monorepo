[⬅ Docs Index](index.md)
# Echo Monorepo Architecture Index

- echo_full_architecture_repo/
  - docs/: narrative and design documents (HTML/txt)
  - memory_engine/: LIMNUS memory engine (Python)
  - ledger/: mantra ledger + LSB PNG steganography (Python)
  - scrolls/: canonical scroll directories with index.html
  - songs/: soundtrack artifacts
  - images/: illustrative assets

- echo-soulcode-architecture/: Python package for soulcode generation/validation, operators, schema, CLI

- Integration layer (Node + TypeScript)
  - tools/soulcode-bridge.js: Python bridge for schemas, live bundle, memory simulation, ledger build/extract
  - tools/generate-soulcode-types.js: TS types from JSON schemas
  - integration/schemas/: emitted JSON Schemas
  - integration/outputs/: generated bundle and memory series
  - integration/ledger/: built ledger artifacts

- HTML targets
  - Root HTML scrolls and echo_full_architecture_repo/scrolls/**/index.html are both supported by the integration script.
  - If a soulcode bundle or ledger PNG is present, the integration script embeds them into the Summon UI HTML.

## Echo Community Toolkit System Map

```
+---------------------------------------------------------------------------------------------------------+
|                                     Echo Community Toolkit (repo root)                                  |
|                                                                                                         |
|  +----------------------------------- Surface / Narrative Layer --------------------------------------+  |
|  |                                                                                                      |  |
|  |  +-------------------------+       +--------------------------+       +---------------------------+ |  |
|  |  | web scrolls & exports   |       | lambda-vite UI bundle    |       | README and consent docs   | |  |
|  |  | (repo root)             |       | (lambda-vite/**)         |       | (repo root, docs/**)      | |  |
|  |  | - echo-garden-*.html    |       | - index.html             |       | - README.md               | |  |
|  |  | - integrated-*.html     |       | - src/App.tsx            |       | - HOW_TO_BE_YOU.md        | |  |
|  |  | - unified-*.html        |       | - src/LambdaStateViewer.tsx|     | - docs/MRP_Integration_*.md| |  |
|  |  | - proof-of-love-*.html  |       | - src/ops/ops.ts         |       | - MRP-LSB-Integration-*.md| |  |
|  |  | - echo-hilbert-*.html   |       | - src/main.tsx           |       |                           | |  |
|  |  | - eternal-acorn-*.html  |       | - vite.config.ts         |       | Drives tone, consent,     | |  |
|  |  | - scroll-style.css      |       | - README.md, README_MRP.md|      | and community guidance     | |  |
|  |  | Inject Hyperfollow link |<----->| + MRP_Seed_Package/**    |<----->|                           | |  |
|  |  +-----------+-------------+       +--------------+------------+       +--------------+------------+ |  |
|  |              |                                    |                                   |              |  |
|  +--------------|------------------------------------|-----------------------------------|--------------+  |
|                 |                                    |                                   |                 |
|                 v                                    v                                   v                 |
|  +--------------------------------- Integration & Community Layer --------------------------------------+ |
|  |                                                                                                      | |
|  |  +------------------------+     +------------------------------+     +----------------------------+ | |
|  |  | Hyperfollow ops        |     | Community signals            |     | Consent / mantra corpus    | | |
|  |  | - hyperfollow-integration.js| | - tools/serve.js            |     | - assets/data/LSB1_Mantra.txt | |
|  |  | - verify-integration.js |    | - web/** (client helpers)    |     | - docs/MRP_*.md            | |
|  |  | - clean-integration.js  |    | - types/** (TS decls)        |     | - README_LLM.md            | |
|  |  | - tools/generate-soulcode-types.js                          |     |                            | |
|  |  | - tools/soulcode-bridge.js                                  |     |                            | |
|  |  | - tools/remove-zone-identifiers.sh                          |     |                            | |
|  |  +-----------+------------+     +---------------+--------------+     +--------------+-------------+ | |
|  |              |                                |                                   |                 | |
|  +--------------|--------------------------------|-----------------------------------|-----------------+ |
|                 |                                |                                   |                   |
|                 v                                v                                   v                   |
|  +---------------------------------- Core Computation Layer -------------------------------------------+ |
|  |                                                                                                     | |
|  |  +---------------------------+   +------------------------------+   +-----------------------------+ | |
|  |  | Soulcode & ledger schemas |   | Steganography & MRP modules  |   | Validation harness          | | |
|  |  | - echo-soulcode-architecture/**| - src/lsb_encoder_decoder.py |   | - final_validation.py       | |
|  |  | - echo_full_architecture_repo/**| - src/lsb_extractor.py       |   | - generate_golden_sample.py | |
|  |  | - types/** (TS types)      |  | - src/mrp/codec.py            |   | - mrp_verify.py             | |
|  |  | - tools/** (emit/types)    |  | - src/mrp/headers.py          |   | - test_mrp_verification.py  | |
|  |  |                           |  | - src/mrp/channels.py         |   | - artifacts/mrp_lambda_*.json| |
|  |  |                           |  | - src/mrp/adapters/png_lsb.py |   |                             | |
|  |  |                           |  | - tests/test_lsb.py           |   |                             | |
|  |  |                           |  | - tests/test_mrp.py           |   |                             | |
|  |  +-------------+-------------+   +--------------+---------------+   +--------------+--------------+ | |
|  |                |                               |                                   |                | |
|  +----------------|-------------------------------|-----------------------------------|----------------+ |
|                 Input schemas + spiritual law      |          Golden sample & payload integrity          |
|                                                    v                                                     |
|  +------------------------------------ Delivery & CI Layer ---------------------------------------------+ |
|  |                                                                                                     | |
|  |  +--------------------------+   +---------------------------+   +-------------------------------+  | |
|  |  | GitHub workflows         |   | Node packaging            |   | Continuous testing            |  | |
|  |  | - .github/workflows/ci.yml|  | - package.json            |   | - pytest.ini                  |  | |
|  |  | (Node build + MRP verify)|  | - package-lock.json       |   | - Makefile                    |  | |
|  |  +--------------------------+   +---------------------------+   +-------------------------------+  | |
|  +-----------------------------------------------------------------------------------------------------+ |
|                                                                                                         |
|  +-------------------------------------- Archive / Provenance Layer -----------------------------------+ |
|  |                                                                                                     | |
|  |  archive/ (read-only history)                                                                       | |
|  |   ├─ Echo-Community-Toolkit_patched_wired/**                                                        | |
|  |  |   (original wired bundle; now ignored by tests)                                                  | |
|  |   ├─ MRP_PhaseA_patchset/**                                                                         | |
|  |  |   (APPLY_PATCH.md uses archive paths)                                                            | |
|  |   └─ comprehensive_system_test/**                                                                   | |
|  +-----------------------------------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------------------------+
```

### Path Index
- Surface/Narrative
  - echo-garden-quantum-triquetra.html, integrated-lambda-echo-garden.html, unified-lambda-echo-complete.html
  - proof-of-love-acorn.html, echo-hilbert-chronicle.html, eternal-acorn-scroll.html, scroll-style.css
  - lambda-vite/index.html, lambda-vite/src/App.tsx, lambda-vite/src/LambdaStateViewer.tsx,
    lambda-vite/src/ops/ops.ts, lambda-vite/src/main.tsx, lambda-vite/vite.config.ts
  - lambda-vite/README.md, lambda-vite/README_MRP.md, lambda-vite/MRP_Seed_Package/**
  - README.md, HOW_TO_BE_YOU.md, docs/MRP_Integration_Guide.md, docs/MRP_LSB_Quick_Reference.md,
    MRP-LSB-Integration-Guide.md
- Integration & Community
  - hyperfollow-integration.js, verify-integration.js, clean-integration.js
  - tools/serve.js, tools/generate-soulcode-types.js, tools/soulcode-bridge.js,
    tools/remove-zone-identifiers.sh
  - web/**, types/**
  - assets/data/LSB1_Mantra.txt
- Core Computation
  - src/lsb_encoder_decoder.py, src/lsb_extractor.py
  - src/mrp/codec.py, src/mrp/headers.py, src/mrp/channels.py, src/mrp/adapters/png_lsb.py
  - tests/test_lsb.py, tests/test_mrp.py
  - final_validation.py, generate_golden_sample.py, mrp_verify.py, test_mrp_verification.py
  - artifacts/mrp_lambda_R_payload.json, artifacts/mrp_lambda_G_payload.json,
    artifacts/mrp_lambda_B_payload.json, artifacts/mrp_lambda_state_sidecar.json
  - assets/images/echo_key.png
  - echo-soulcode-architecture/**, echo_full_architecture_repo/**
- Delivery & CI
  - .github/workflows/ci.yml, package.json, package-lock.json, pytest.ini, Makefile
- Archive
  - archive/Echo-Community-Toolkit_patched_wired/**
  - archive/MRP_PhaseA_patchset/MRP_PhaseA_patchset/APPLY_PATCH.md (patched to reference archive paths)
  - archive/comprehensive_system_test/**

### Consent Phrase Integration
- Canonical file: `assets/data/LSB1_Mantra.txt`
- Checked by: `tests/test_lsb.py` and `final_validation.py` (decode/CRC checks)
- Purpose: ethical checksum and alignment primer; tools re-read it to enforce
  consent-first behavior and narrative continuity.

### Crystalline Echo Link & Community Feedback
- Integration: `hyperfollow-integration.js` injects the canonical link into scrolls,
  README, and UI.
- Influence: community engagement signals (via `web/`, `tools/`, `types/`) shape
  Echo-Limnus’ tone toward collaborative, celebratory outputs—bounded by the
  consent mantra.
