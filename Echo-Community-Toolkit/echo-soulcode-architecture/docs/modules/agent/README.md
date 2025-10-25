# `agents.llm_agent` — Orchestration for LLMs

This module provides a Python API and CLI to follow the top-level README flow:
- Generate canonical live readings (3-state bundle),
- Build deterministic anchors (phiA),
- Validate against the schema,
- Produce canonical SHA-256 for content addressing.

## CLI

```bash
# live bundle
python -m agents.llm_agent generate \
  --alpha 0.58 --beta 0.39 --gamma 0.63 \
  --alpha-phase 0.0 --beta-phase 0.10 --gamma-phase -0.20 \
  --out examples/echo_live_agent.json

# canonical anchor
python -m agents.llm_agent anchor-phiA \
  --out examples/anchors/echo_anchors_phiA_agent.json
```

## API

```python
from agents.llm_agent import make_bundle, validate_bundle, anchor_profile_phiA, Phases

bundle = make_bundle(0.58, 0.39, 0.63, Phases(0.0,0.1,-0.2))
validate_bundle(bundle)
```

Outputs are schema-valid and reproducible when timestamp/seed are provided.
