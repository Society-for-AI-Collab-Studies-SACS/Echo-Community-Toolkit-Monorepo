# VesselOS Base Structure Reference

This repository mirrors the minimum directory expectations for running VesselOS agent commands in a research environment. Populate these directories before invoking `python3 vesselos.py <agent> <command>`.

```
vesselos-dev-research/
|-- README.md
|-- docs/
|   |-- IN_DEV_SPECS.md
|   `-- BASE_STRUCTURE.md
|-- library_core/
|   |-- agents/
|   `-- __init__.py
|-- pipeline/
|   `-- dispatcher_enhanced.py
|-- scripts/
|   `-- bootstrap.sh
|-- requirements.txt
|-- requirements-dev.txt
|-- vesselos.py
`-- workspaces/
    `-- example/
        |-- state/
        |   |-- garden_state.json
        |   |-- echo_state.json
        |   |-- limnus_memory.json
        |   `-- ledger.json
        `-- logs/
            |-- voice_log.json
            |-- garden.jsonl
            |-- echo.jsonl
            |-- limnus.jsonl
            `-- kira.jsonl
```

## Required Files

- `library_core/agents/`: Copy agent implementations from the upstream VesselOS project.
- `pipeline/dispatcher_enhanced.py`: Bring over the enhanced dispatcher or adapt it to custom commands.
- `requirements*.txt`: Mirror dependency pins from upstream to keep parity.
- `vesselos.py`: Unified CLI entry point; ensure it proxies to the Prime CLI and audit commands.

## Workspace Seed Templates

Sample JSON files under `workspaces/example/state/` are intentionally empty. When seeding a new workspace:

1. Duplicate `workspaces/example/` to `workspaces/<workspace_id>/`.
2. Run `python3 vesselos.py garden start` to create the genesis ledger block.
3. Execute `python3 vesselos.py echo summon` to initialize persona state.

Logs are append-only; keep `.gitkeep` files to preserve directory structure when cloning freshly.
