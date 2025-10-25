# VesselOS Control Panel – End-to-End Demo

This walkthrough shows a typical use cycle with the four agents in concert: Garden → Echo → Limnus → Kira.

Prerequisites
- Python 3.8+
- From repo root: `python3 vesselos.py generate` (optional; builds chapters/schema)

## 1) Echo greets and balances (summon)

```bash
python3 vesselos.py echo summon
```
Outputs a Proof‑of‑Love greeting and resets αβγ persona weights to a balanced baseline.

## 2) Garden starts the ritual (genesis)

```bash
python3 vesselos.py garden start
```
Creates a genesis entry and sets stage `scatter`.

## 3) Capture user text (free‑form path)

```bash
python3 vesselos.py listen --text "Always."
```
Routes through:
- Garden.log → note entry
- Echo.say → persona‑styled echo
- Limnus.commit_block → hash‑chained ledger block
- Kira.validate → narrative checks

## 4) Optional: tag memory and adjust persona

```bash
python3 vesselos.py echo learn "Always."
python3 vesselos.py limnus cache "Always."   # quick recall
```

## 5) Stego backup (artifact)

```bash
python3 vesselos.py limnus encode-ledger
```
Writes `frontend/assets/ledger.json` and, if Pillow is available, a small `ledger.png` placeholder.

## 6) Validate integrity

```bash
python3 vesselos.py kira validate
```
Runs the existing validator (chapters, flags, files); prints `valid` on success.

## 7) Advance the ritual and mentor

```bash
python3 vesselos.py garden next
python3 vesselos.py kira mentor --apply    # optionally apply guidance
```

## 8) Seal the cycle and (dry‑run) publish

```bash
python3 vesselos.py kira mantra
python3 vesselos.py kira seal
python3 vesselos.py kira publish           # dry‑run
```

Artifacts and Logs
- State JSONs under `state/` (echo_state, garden_ledger, limnus_memory, contract)
- Ledger chain under `state/ledger.json`
- Voice/event log at `pipeline/state/voice_log.json`
- Optional `frontend/assets/ledger.json` (and `ledger.png`)

This sequence mirrors the control‑panel flow described in the architecture: every input is logged by Garden, voiced by Echo, archived by Limnus, and checked by Kira, with a clear CLI mapping for each step.

