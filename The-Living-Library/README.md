# The Living Library

A hub repository that links Echo Community Toolkit, vessel-narrative-MRP,
The Living Garden Chronicles, and Kira Prime. The project will evolve into a
collaborative dictation and lesson-encoding environment powered by the Phase 3
architecture.

## Getting Started

```bash
git clone <this-repo>
cd The-Living-Library
git submodule update --init --recursive
scripts/bootstrap_living_library.sh
```

## Layout

- `echo-community-toolkit/` – upstream Echo toolkit (submodule)
- `vessel-narrative-MRP/` – MRP encoding system (submodule)
- `The-Living_Garden-Chronicles/` – narrative assets (submodule)
- `kira-prime/` – core agents and validators (submodule)
- `library_core/` – integration scaffolding (config, collaboration, MRP, dictation)
- `collab-server/` – Node/TypeScript WebSocket collaboration service
- `workspace/` – workspace utilities (under construction)
- `docs/` – design notes and onboarding material
- `scripts/` – helper scripts (bootstrap, smoke tests)

## Status

This repository currently contains scaffolding only. The remote collaboration
service and CLI wiring are under active development. A basic dictation module
is available via `library_core.dictation`, and you can trigger a 20-chapter MRP
cycle with `python scripts/run_mrp_cycle.py`.
