# PR: VesselOS Unified Architecture Scaffold + Integration

This PR integrates a working VesselOS scaffold with four agents (Echo, Garden, Limnus, Kira), orchestration (dispatcher + logger), and a unified CLI. It also links the local repo to `kira-prime-barebones` and prepares compatibility shims expected by alternate scaffolds.

## Changes
- Agents implemented
  - `agents/echo/echo_agent.py` – persona state, `summon|mode|say|learn|status|calibrate`
  - `agents/garden/garden_agent.py` – ritual ledger `start|next|open|resume|log|ledger`
  - `agents/limnus/limnus_agent.py` – memory + hash‑chained ledger, `cache|recall|commit_block|encode_ledger|decode_ledger`
  - `agents/kira/kira_agent.py` – `validate|mentor|mantra|seal|push|publish`
- Orchestration + logging
  - `interface/dispatcher.py` – free‑form Garden→Echo→Limnus→Kira; explicit routing
  - `interface/logger.py` – JSONL voice log; now mirrors to both `pipeline/state/voice_log.json` and `state/voice_log.json`
  - `common/logger.py` – compatibility shim exposing `Logger.log(...)`
- CLI and wrappers
  - `vesselos.py` – top‑level CLI with namespaces: `generate|listen|validate|mentor|publish|echo|garden|limnus|kira`
  - `pipeline/dispatcher.py`, `interface/listener.py`, `interface/vesselos.py` – wrappers for alternate file layouts
- Narrative build + validation
  - `src/schema_builder.py`, `src/generate_chapters.py`, `src/validator.py`, `src/stego.py`, `src/soulcode.py`
  - Generates `schema/*`, embeds soulcode bundle in `frontend/index.html`, validates 20 chapters + flags + provenance
- Artifacts
  - `frontend/assets/chapter*.png` (stego payloads when Pillow available)
  - `frontend/assets/ledger.json|png` (from publish dry‑run)

## Commands Run
Repository wiring
```bash
# set remotes
git -C kira-prime remote add kira https://github.com/AceTheDactyl/kira-prime.git
git -C kira-prime remote add barebones /home/turne/.remote/kira-prime-barebones.git

# merge barebones into unified main
git -C kira-prime fetch barebones
git -C kira-prime merge --allow-unrelated-histories barebones/main -m "chore(sync): merge barebones upstream into unified repo"

# push
git -C kira-prime push -u barebones main
git -C kira-prime push -u kira main
```

Scaffold verification
```bash
# rebuild schema + chapters (+ embed soulcode bundle)
python3 kira-prime/vesselos.py generate

# validate narrative (chapters, flags, provenance, stego when available)
python3 kira-prime/vesselos.py validate

# control‑panel demo (freeform Garden→Echo→Limnus→Kira)
python3 kira-prime/vesselos.py listen --text "Always."

# publish dry‑run (writes ledger artifact)
python3 kira-prime/vesselos.py publish
```

Selected outputs
```text
Validation OK: 20 chapters, rotation clean, files present, flags consistent, stego payloads match.
DispatchResult(garden='note:…', echo='[mix] Always.', limnus='<hash>', kira='valid')
(frontend/assets/) ledger.json, ledger.png created
```

## Notes
- Voice log is mirrored to both `pipeline/state/voice_log.json` and `state/voice_log.json` for tool compatibility.
- Default orchestration order is enforced for free‑form inputs (Garden→Echo→Limnus→Kira), per repo guidelines.
- Node CLI remains available at `tools/codex-cli/bin/codex.js` as an optional interface.

## Next Steps
- Optional: prune legacy remotes and open follow‑up PRs to refine docs.
- Optional: wire CI to run `generate` + `validate` on PRs.
