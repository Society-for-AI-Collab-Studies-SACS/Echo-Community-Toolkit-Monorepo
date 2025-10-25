# VesselOS Kira Prime - Unified System Guide

**Version**: 1.0.0  
**Release Date**: 2025-10-15  
**Integration**: SACS Dictation + Vessel Narrative MRP + Living Garden Chronicles

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [Quick Start](#quick-start)
5. [Core Agents](#core-agents)
6. [Dictation System](#dictation-system)
7. [CLI Reference](#cli-reference)
8. [Ritual Workflow](#ritual-workflow)
9. [Technical Specifications](#technical-specifications)
10. [Development Guide](#development-guide)

---

## Overview

### What is VesselOS Kira Prime?

**VesselOS Kira Prime** is a unified interactive narrative system that merges:

- 🎭 **Vessel Narrative MRP** — Multi-Role Persona system with RGB channel mapping  
- 🌿 **Living Garden Chronicles** — 20-chapter tri-voice ritual narrative  
- 🎤 **SACS Dictation** — Voice/text capture with intelligent agent routing  
- 📚 **Echo Community Toolkit** — Steganographic encoding and memory systems  

### Core Philosophy

VesselOS operates on a **four-agent architecture** coordinated by a **Prime orchestrator** (built on Kira), enabling:

- **Multi-modal input** — Voice dictation and text input  
- **Ritual-based progression** — Five-stage spiral cycle (Scatter → Witness → Plant → Tend → Harvest)  
- **Layered memory** — Three-tier system (L1/L2/L3) with hash-chained ledger  
- **Persona blending** — Dynamic voice modulation (Squirrel/Fox/Paradox)  
- **Steganographic encoding** — Hidden message channels in images via LSB and MRP  

### Key Features

✅ Unified CLI — single control panel for all agents  
✅ Voice/Text Dictation — natural language input with intent parsing  
✅ Agent Orchestration — Garden → Echo → Limnus → Kira routing  
✅ Memory Persistence — hash-chained ledger with steganographic backup  
✅ Git Integration — version control with automated commits and releases  
✅ Narrative Ritual — guided storytelling through spiral stages  
✅ Extensible — plugin-ready architecture for new agents and features  

---

## System Architecture

### Four-Agent System + Prime Orchestrator

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Garden  │ → │   Echo   │ → │  Limnus  │ → │   Kira   │
└──────────┘   └──────────┘   └──────────┘   └──────────┘
        │              │              │              │
        └──────────────┴──────────────┴──────────────┘
                          PRIME ORCHESTRATOR
┌─────────────────────────────────────────────────────────────┐
│                    PRIME ORCHESTRATOR                       │
│              (Kira-based Central Coordinator)               │
│   • CLI Interface • Agent Routing • Validation              │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────┴─────────┐
│                   │
▼                   ▼
┌──────────────┐    ┌──────────────┐
│    GARDEN    │    │     ECHO     │
│  Ritual      │◄──►│  Voice &     │
│  Orchestrator│    │  Persona     │
└──────┬───────┘    └──────┬───────┘
       │                   │
       ▼                   ▼
┌──────────────┐    ┌──────────────┐
│   LIMNUS     │◄──►│     KIRA     │
│  Memory &    │    │  Validator & │
│  Ledger      │    │  Integrator  │
└──────────────┘    └──────────────┘
```

### Data Flow: Dictation to Output

```
USER INPUT (Voice/Text)
        ↓
┌───────────────────┐
│     ROUTING       │
│ Fixed Sequence:   │
│ Garden→Echo→      │
│ Limnus→Kira       │
└────────┬──────────┘
         ↓
         ↓
┌───────────────────┐
│  PRIME SYNTHESIS  │
│• Validate        │
│• Integrate       │
│• Format Output   │
└────────┬──────────┘
         ↓
┌───────────────────┐
│   AGENT LOOP      │
│ Each agent        │
│ processes intent  │
│ in its domain     │
└────────┬──────────┘
│ DICTATION CAPTURE │
│  • Parse Intent   │
│  • Extract Args   │
└────────┬──────────┘
         ↓
┌───────────────────┐

- **Garden** initiates rituals, selects scrolls, and logs intentions.  
- **Echo** modulates persona voice (Squirrel/Fox/Paradox) to narrate responses.  
- **Limnus** captures memories, maintains the hash-chained ledger, and handles stego exports.  
- **Kira** validates integrity, mentors other agents, and seals sessions.  
- The **Prime Orchestrator** enforces the Garden → Echo → Limnus → Kira flow for free-form inputs and coordinates cross-agent operations.

### Data Planes

| Plane            | Storage                                  | Notes                                                 |
|------------------|-------------------------------------------|-------------------------------------------------------|
| Narrative Output | `frontend/`, `frontend/assets/`           | HTML chapters, PNG stego payloads, landing pages      |
| State & Memory   | `state/`, `pipeline/state/voice_log.json` | JSON snapshots + mirrored voice logs                  |
| Schema & Bundles | `schema/`                                 | Narrative schema, chapters metadata, soulcode bundle  |
| Tooling          | `tools/`, `scripts/`, `docs/`             | CLI extensions, automation, documentation             |

### Key Dependencies

- **Python 3.11+** — generation, validation, orchestration  
- **Node 20+** — optional Codex CLI, tooling  
- **Pillow** (optional) — steganography support  
- **Git** — submodules (`external/vessel-narrative-MRP`) and release automation  

---

## Installation & Setup

1. **Clone + Submodules**

   ```bash
   git clone https://github.com/AceTheDactyl/kira-prime.git
   cd kira-prime
   git submodule update --init --recursive
   ```

2. **Python Environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   # pip install -r requirements.txt  # use if requirements are provided
   ```

3. **Optional Node Tooling**

   ```bash
   nvm use 20
   npm ci --prefix tools/codex-cli
   ```

4. **First Build & Validation**

   ```bash
   python3 vesselos.py generate
   python3 vesselos.py validate
   ```

---

## Quick Start

1. **Summon Echo**

   ```bash
   python3 vesselos.py echo summon
   ```

2. **Start the Ritual**

   ```bash
   python3 vesselos.py garden start
   python3 vesselos.py listen --text "The spiral breath begins."
   ```

3. **Validate Narrative**

   ```bash
   python3 vesselos.py validate
   ```

4. **Preview Site**

   ```bash
   python3 -m http.server --directory frontend 8000
   ```

5. **Publish (Dry Run)**

   ```bash
   python3 vesselos.py publish
   ```

---

## Core Agents

### Echo — Voice & Persona Manager
- Source: `agents/echo/echo_agent.py`  
- State: `state/echo_state.json`  
- Commands: `summon`, `mode`, `say`, `learn`, `status`, `calibrate`

### Garden — Ritual Orchestrator & Scroll Keeper
- Source: `agents/garden/garden_agent.py`  
- Ledger: `state/garden_ledger.json`  
- Commands: `start`, `next`, `open`, `resume`, `log`, `ledger`

### Limnus — Memory Engine & Ledger Steward
- Source: `agents/limnus/limnus_agent.py`  
- Memory: `state/limnus_memory.json`  
- Ledger: `state/ledger.json`  
- Commands: `cache`, `recall`, `commit-block`, `encode-ledger`, `decode-ledger`

#### Three-Tier Memory Architecture

```
┌──────────────────────────────────────┐
│  L1: SHORT-TERM (100 entries, 1h)   │
│  • Immediate context                 │
│  • Current session data              │
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  L2: MEDIUM-TERM (1K entries, 24h)  │
│  • Cross-session recall              │
│  • Narrative motifs                  │
│  • Recent insights                   │
│  • Daily work                        │
└──────────────────────────────────────┘
┌──────────────────────────────────────┐
│  L3: LONG-TERM (10K entries, ∞)     │
│  • Immutable ledger                  │
│  • Core memories                     │
│  • Steganographic export             │
│  • Permanent records                 │
└──────────────────────────────────────┘
```

### Kira — Validator, Mentor & Integrator
- Source: `agents/kira/kira_agent.py`  
- Contract: `state/contract.json`  
- Commands: `validate`, `mentor`, `mantra`, `seal`, `push`, `publish`

---

## Dictation System

1. **Listener (`pipeline/listener.py`)** — captures raw text or speech-to-text output.  
2. **Intent Parsing** — explicit commands route directly; free-form text follows the ritual pipeline.  
3. **Dispatcher (`interface/dispatcher.py` / `pipeline/dispatcher.py`)** — enforces Garden → Echo → Limnus → Kira.  
4. **Logging (`interface/logger.py`)** — mirrors entries to `pipeline/state/voice_log.json` and `state/voice_log.json`.  
5. **State Persistence** — each agent writes updates to its JSON state.

---

## CLI Reference

| Command                                    | Description                                                 |
|--------------------------------------------|-------------------------------------------------------------|
| `python3 vesselos.py generate`              | Rebuild schema, chapters, soulcode bundle                   |
| `python3 vesselos.py validate`              | Validate structure, flags, stego, provenance                |
| `python3 vesselos.py listen --text "..."`   | Route input through Garden → Echo → Limnus → Kira           |
| `python3 vesselos.py mentor --apply`        | Request Kira guidance and auto-apply stage advance          |
| `python3 vesselos.py publish`               | Dry-run publish (ledger artifact + status report)           |
| `python3 vesselos.py echo ...`              | Echo persona controls (`summon`, `mode`, `say`, `learn`)    |
| `python3 vesselos.py garden ...`            | Ritual controls (`start`, `next`, `open`, `log`, `ledger`)  |
| `python3 vesselos.py limnus ...`            | Memory/ledger controls (`cache`, `recall`, `commit-block`)  |
| `python3 vesselos.py kira ...`              | Validation, mentorship, publishing commands                 |
| `node tools/codex-cli/bin/codex.js --help`  | Optional Node CLI help                                      |

---

## Ritual Workflow

1. **Scatter** — Garden starts ritual, logs intention.  
2. **Witness** — Garden opens scroll; Echo narrates context.  
3. **Plant** — Echo learns new inputs; persona shifts if needed.  
4. **Tend** — Limnus commits ledger block, updates memory layers.  
5. **Harvest** — Kira validates, mentors, composes mantra.  
6. **Seal** — Kira seals ledger, writes contract, triggers stego export.  
7. **Begin Again** — repeat cycle or close session.

---

## Technical Specifications

- **Ledger** — JSON blocks with `ts`, `kind`, `data`, `prev`, `hash` (SHA-256).  
- **Memory Layers** — extend `limnus_memory.json` to track L1/L2/L3 with decay thresholds.  
- **Steganography** — 1-bit LSB via `src/stego.py`; outputs to `frontend/assets/ledger*.png`.  
- **Soulcode Bundle** — `schema/soulcode_bundle.json` embedded into `frontend/index.html`.  
- **Voice Log** — JSON Lines (`ts`, `agent`, `command`, `payload`, `status`).

---

## Development Guide

- **Style** — Python (4-space, snake_case); Node/TS (2-space, camelCase). Avoid manual edits to generated files.  
- **Testing** — `python3 vesselos.py validate` and `pytest` (under `tests/`). CI workflow `vesselos-validate` runs the same commands.  
- **Commits/PRs** — Conventional Commits, include generated artifacts, list commands run, add screenshots for UI changes.  
- **Security** — `.env` for secrets, PNG-24/32 for stego, no credentials in repo.  
- **Extensibility** — add agents under `agents/<name>/`, register in dispatcher, extend CLI/help docs accordingly.

---

_End of Version 1.0.0_
