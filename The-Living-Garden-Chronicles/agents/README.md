# Agents Index

Concise briefs for each module agent. See the per‑agent `AGENT.md` for details.

- Vessel — `vessel/AGENT.md`
  - Index & conductor: enforces the Garden → Echo → Limnus → Kira runtime loop and keeps shared contracts/mantras aligned.
  - Workflow: `codex garden start|open` → `codex echo say|learn` → `codex limnus commit-block|encode-ledger` → `codex kira validate|mentor|seal`

- Echo — `echo/AGENT.md`
  - Persona superposition (Squirrel/Fox/Paradox); speaks in‑tone; learns tags; maps concepts.
  - CLI: `echo mode|say|learn|map|status|calibrate`

- Garden — `garden/AGENT.md`
  - Ritual orchestrator; pages scroll sections; logs completions; persona‑styled mantras.
  - CLI: `garden start|next|open [--prev|--reset]|resume|learn|ledger|log`

- Limnus — `limnus/AGENT.md`
  - Memory (L1/L2/L3) + hash‑chained ledger; stego I/O; aggregates knowledge for Kira.
  - CLI: `limnus state|update|cache|recall|memories|export/import-memories|commit-block|view/export/import-ledger|rehash-ledger|encode/decode/verify-ledger`

- Kira — `kira/AGENT.md`
  - Validation & integrations; learns from Limnus; mentors Echo/Garden; seals persona‑ordered mantra.
  - CLI: `kira validate|sync|setup|pull|push|publish|test|assist|learn-from-limnus|codegen|mentor|mantra|seal`
