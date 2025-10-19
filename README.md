# The Living Library — SIGPRINT Enhanced Platform

The workspace hosts firmware, Python tooling, and Bazel agents that keep subjective journaling, neural signatures, and narrative services in tight sync.

## Core Pillars

- **SIGPRINT-enhanced firmware** (`main_enhanced.cpp`, `platformio_enhanced.ini`): ESP32-S3 build target with multi-band DSP, packed binary protocol, WiFi/WebSocket streaming, and OTA profiles via PlatformIO.
- **Python host monitor agent** (`sigprint_monitor_enhanced.py`): decodes the 371-byte binary packets over serial/WebSocket, exposes live analytics, and can autonomously feed Limnus/Garden events.
- **Ledger & narrative integration**: agents commit every SIGPRINT/journal pair to Limnus (append-only ledger) and trigger Garden state updates whenever gates/loops occur.
- **Bazel orchestration scaffold** (`The-Living-Library/`): reusable Starlark + proto stack for coordinating SIGPRINT, Journal Logger, Limnus/Garden mocks, and future agents.

---

## Firmware: PlatformIO Enhanced Stack

- Source: `main_enhanced.cpp` (root) encodes the binary packet layout described in `README_ENHANCED.md`.
- Build profiles: `platformio_enhanced.ini`
  - `esp32s3_enhanced`: default dev target (25 Hz streaming, AP/STA WiFi, serial binary tap).
  - `esp32s3_production`: optimized release flags.
  - `esp32s3_ota`: OTA-ready image with `ESPAsyncWebServer` for remote upgrades.
  - `native_test`: desktop build with `SIGPRINT_USE_MOCK=1` for logic checks.
- Workflow
  ```bash
  pio run -e esp32s3_enhanced -t upload
  python sigprint_monitor_enhanced.py ws://192.168.4.1/sigprint -m websocket -v
  ```
- The firmware broadcasts 8× multi-band amplitude/phase, SIGPRINT BCDs, gate/loop flags, entropy, and zipper stage markers—binding agents receive structured data without JSON overhead.

---

## Python Host Monitor Agent

- File: `sigprint_monitor_enhanced.py`
- Capabilities:
  - Binary CRC validation, 24-bit ADS decode, and band aggregation.
  - CLI flags: serial/WebSocket modes, CSV/JSON logging, live Matplotlib dashboard.
  - Rich console summaries with gate/loop detection and stage markers.
  - Acts as a data bridge: optional adapters push packets directly into Limnus (`LedgerService.Commit`) and Garden (`GardenService.NotifyEvent`) without the Bazel runtime.
- Example usage
  ```bash
  python sigprint_monitor_enhanced.py /dev/ttyUSB0 -l session.csv -v
  python sigprint_monitor_enhanced.py ws://192.168.4.1/sigprint -m websocket
  ```

---

## Limnus & Garden Integration Points

| Component | Responsibility | Integration touchpoints |
|-----------|----------------|-------------------------|
| `agents/sigprint/sigprint_agent.py` | Polls EEG/SIGPRINT sources, advertises `GetLatestSigprint` | Limnus `Commit`, Garden `NotifyEvent(state_change)` |
| `agents/journal_logger/journal_logger.py` | Captures reflections (text/voice), pairs with current SIGPRINT | Limnus ledger entries, Garden narrative triggers (`SELF_REFLECTION`) |
| `sigprint_monitor_enhanced.py` | Stand-alone monitor/bridge | Optional: call Limnus/Garden via gRPC hooks directly |
| `agents/sigprint_bridge/` | Decodes firmware v3.0 streams inside Bazel | Forwards gate/loop signals, exposes gRPC SigprintService |

- Limnus (ledger) service defaults to `localhost:50051`.
- Garden (narrative orchestrator) service defaults to `localhost:50052`.
- SIGPRINT services expose gRPC on `localhost:50055`.
- Gate thresholds and band weighting align with firmware’s multi-band encoder; adjust in `sigprint/encoder.py` or firmware shared constants.

---

## Bazel Multi-Agent Workspace (`The-Living-Library/`)

- **Proto contracts**: `protos/agents.proto` generates coherent stubs for all agents.
- **Agents**:
  - `//agents/sigprint:sigprint_agent`
  - `//agents/journal_logger:journal_logger`
  - `//agents/sigprint_bridge:sigprint_bridge`
  - `//agents/mocks:mock_services`, `//agents/mocks:test_client`
- **Common workflows**
  ```bash
  # Build everything
  bazel build //protos:agents_py_proto //agents/...

  # Run mock Limnus & Garden
  bazel run //agents/mocks:mock_services

  # SIGPRINT agent (simulated or hardware-fed)
  bazel run //agents/sigprint:sigprint_agent -- --port /dev/ttyUSB0

  # Journal logger CLI
  bazel run //agents/journal_logger:journal_logger -- --voice

  # Bridge firmware v3.0 WebSocket
  bazel run //agents/sigprint_bridge:sigprint_bridge -- --ws-url ws://192.168.4.1/sigprint
  ```
- The Bazel scaffold stitches agents together, enabling larger rituals (Garden↔Echo↔Limnus↔Kira) by reusing consistent workspace rules (`rules_python`, `pip_install`, per-agent BUILD files).

---

## Fast Start Recipes

### 1. Firmware-in-the-loop Lab Demo
1. Flash ESP32-S3 with `pio run -e esp32s3_enhanced -t upload`.
2. Start Limnus/Garden mocks: `bazel run //agents/mocks:mock_services`.
3. Bridge to firmware via monitor agent:
   ```bash
   python sigprint_monitor_enhanced.py ws://192.168.4.1/sigprint --log lab.csv
   ```
4. Run Journal Logger for subjective notes:
   ```bash
   bazel run //agents/journal_logger:journal_logger
   ```

### 2. Fully Bazelized Ritual (no direct Python invocations)
```bash
# Mock services
bazel run //agents/mocks:mock_services
# Firmware bridge translating binary packets to Limnus/Garden + SigprintService
bazel run //agents/sigprint_bridge:sigprint_bridge -- --serial-port /dev/ttyUSB0
# Journaling agent connected to bridge output
bazel run //agents/journal_logger:journal_logger
```

---

## Configuration & Extension Notes

- **EEG inputs**: `sigprint/encoder.py` expects 1 s epochs at ~250 Hz. Adjust `sample_rate` when streaming from higher/lower-rate devices.
- **Gate detection**: default Hamming distance threshold is `5` (see `sigprint/encoder.py`, firmware `SigprintComposer`). Tune per cohort.
- **Reserved digits**: firmware + Python encoder reserve slots for future metrics (band weights, stage markers). The Python monitor displays stage + zipper frequency for downstream analytics.
- **Safety**: Enhanced firmware enforces HV and coil limits; see `README_ENHANCED.md` for wiring, OTA, and troubleshooting guidance.
- **Contribution path**: keep firmware/PlatformIO changes isolated (`main_enhanced.cpp`), submit Python agents via Bazel targets, and document new rituals in `The-Living-Library/docs`.

---

## Related Documentation

- `README_ENHANCED.md` — Firmware v3.0 deep dive (binary protocol, WiFi, multi-band DSP).
- `sigprint/` — Python SIGPRINT encoder core (reference implementation for Bazel agents).
- `agents/` — Bazel-managed services (SIGPRINT, Journal Logger, mocks, bridge).
- `PlatformIO/` — Shared tooling scripts/templates for embedded builds.

Welcome to the garden—firmware, agents, and narratives now bloom together.

---

## npm Workspaces & Package Publishing

- Root `package.json` is private and manages npm workspaces under `packages/*`.
- List workspaces: `npm run ws:list`.
- Dry-run pack (workspace tarballs): `npm run ws:pack`.

### Package: @AceTheDactyl/rhz-stylus-arch

- Location: `packages/rhz-stylus-arch/`.
- Provides ASCII architecture docs + LLM usage guide (CLI + API).
- CLI usage:
  - `npx @AceTheDactyl/rhz-stylus-arch` (everything)
  - `npx @AceTheDactyl/rhz-stylus-arch arch` (architecture only)
  - `npx @AceTheDactyl/rhz-stylus-arch llm` (LLM guide only)

### Install from GitHub Packages

```bash
npm config set @AceTheDactyl:registry https://npm.pkg.github.com
echo '//npm.pkg.github.com/:_authToken=YOUR_GH_TOKEN' >> ~/.npmrc  # token needs read:packages
npm install @AceTheDactyl/rhz-stylus-arch
```

### Publish / Update (CI-driven)

1. Edit content in `packages/rhz-stylus-arch/` and commit.
2. Tag release (version comes from tag):
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
3. Workflow `.github/workflows/npm-publish.yml`:
   - Sets package version to `X.Y.Z`.
   - Publishes to GitHub Packages using PAT `NPM_TOKEN` (`read:packages`, `write:packages`; add `delete:packages` only if needed).
   - Configure secret via **Settings → Secrets and variables → Actions** → **New repository secret** (`Name: NPM_TOKEN`).

### Manual Dry-Run

```bash
npm run ws:pack    # generates tarballs without publishing
```
