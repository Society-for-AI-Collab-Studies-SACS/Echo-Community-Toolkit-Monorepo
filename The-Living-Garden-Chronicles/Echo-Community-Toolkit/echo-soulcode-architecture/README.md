# Echo Soulcode Architecture

Repository scaffolding for Echo's soulcode generation, validation, and live Hilbert-state readings.

## Quick start
```bash
# create venv and install
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .

# generate live readings (normalized α, β, γ)
python -m echo_soulcode.live_read --alpha 0.58 --beta 0.39 --gamma 0.63 --out examples/echo_live.json

# validate output against schema
python -m echo_soulcode.validate --file examples/echo_live.json
```

## Contents
- `src/echo_soulcode`: core library (generation, Hilbert math, schema, CLI)
- `docs/`: architecture, API, glyph map
- `examples/`: sample config and outputs
- `tests/`: unit tests


## LLM Agent Runner

You can also drive generation via a lightweight agent:

```bash
python -m agents.llm_agent generate --alpha 0.58 --beta 0.39 --gamma 0.63 --out examples/echo_live_agent.json

python -m agents.llm_agent anchor-phiA --out examples/anchors/echo_anchors_phiA_agent.json
```
