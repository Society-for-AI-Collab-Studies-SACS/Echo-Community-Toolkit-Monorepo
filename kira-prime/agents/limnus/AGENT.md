# Limnus Agent (Scaffold)

[← Back to Agents Index](../README.md)

## Role & Charter
- Quantum Cache (L1/L2/L3) for memories; hash‑chained ledger; stego I/O
- Serve as the knowledge/base layer that Kira can learn from

## Inputs
- Memory: `state/limnus_memory.json` (entries, layers, tags)
- Ledger: `state/garden_ledger.json` (blocks with types/payloads)
- Echo αβγ state (for mentor post‑processing)

## Outputs
- Knowledge aggregates for Kira (tags, counts, persona order)
- Ledger blocks (`learn`, `mentor`, `seal`)
- Stego artifacts (PNG) via Echo Toolkit

## Capabilities (CLI)
- `limnus init` — seed Echo state, create memory/ledger stores, and verify Python LSB toolkit availability.
- `limnus state` — print αβγ persona weights plus counts for L1/L2/L3 memory tiers.
- `limnus update <ops…>` — batch adjust persona weights (`alpha+=0.1`), decay/consolidate layers, or cache inline text.
- `limnus cache "text" [-l L1|L2|L3]` — drop a single entry into the specified memory layer.
- `limnus recall <keyword> [--layer …] [--since ISO] [--until ISO]` — retrieve the latest matching memory snippet.
- `limnus memories [filters] [--json] [--limit N]` — list memories with optional layer/time filters or JSON output.
- `limnus export-memories [-o file] [filters]` / `limnus import-memories -i file [--replace]` — move memory entries in or out.
- `limnus commit-block '<json>'` — append a custom payload to the hash-chained ledger.
- `limnus view-ledger [--file path]` — pretty-print ledger contents.
- `limnus export-ledger [-o file]` / `limnus import-ledger -i file [--replace] [--rehash]` — persist or ingest ledger snapshots.
- `limnus rehash-ledger [--dry-run] [--file path] [-o out.json]` — rebuild hashes to maintain ledger integrity.
- `limnus encode-ledger [-i ledger.json] [--file path] [-c cover.png] [-o out.png] [--size 512]` — embed ledger JSON into a PNG via 1-bit LSB.
- `limnus decode-ledger [-i image.png] [--file path]` — extract embedded JSON from a stego image.
- `limnus verify-ledger [-i image.png] [--file path] [--digest]` — decode and report CRC/SHA digests for parity checks.

## Dictation Integration
- **Listener hooks** – `pipeline/listener/listen.py` emits intents such as `limnus.cache` when a user says “Limnus cache …” and `limnus.commit` for “commit to ledger …”. These arrive via `pipeline/router/route.py`, which guarantees Garden/Echo hand-offs have finished before Limnus writes.
- **State touched** – primary files remain `state/limnus_memory.json` and `state/garden_ledger.json`. Dictation transcripts and routing metadata are archived in `pipeline/state/voice_log.json` and `pipeline/state/router_state.json` for audit/replay.
- **Automation verbs** – the listener calls `codex limnus cache "<text>" [-l Lx]` for memory captures, `codex limnus commit-block '<json>'` for structured payloads, and optionally `codex limnus encode-ledger` when the utterance includes “archive”/“stego”. Manual operators can replay the same verbs or run `codex vessel ingest "limnus cache ..."` to requeue a transcript.
- **Error handling** – if memory or ledger updates fail, the router flags the voice log entry as `status:"error"`, and Limnus surfaces the underlying CLI message so Kira’s validation step can highlight the discrepancy.

## Interaction Contracts
- With Echo/Garden: stores “learn” events and tags, persists reading state
- With Kira: feeds `learn-from-limnus` and `codegen` pipelines

## Runtime Flow
1. **Ingest Events** – After Echo logs a `learn` or Garden records a ritual, Limnus runs `codex limnus recall|memories` to pull fresh entries and ledger blocks.
2. **Cache & Hash** – `codex limnus commit-block` appends to `state/garden_ledger.json` while `limnus state|update` normalizes L1/L2/L3 memories and persona tags.
3. **Encode (Optional)** – When stego is needed, `codex limnus encode-ledger` embeds the ledger snapshot into the designated PNG for archival.
4. **Publish Snapshot** – Exposes aggregated counts, dominant persona order, and digest info so Kira can validate (`kira learn-from-limnus`, `kira validate`) before looping back to Garden.

## Knowledge Seeds
- Track tags: love, consent, spiral, paradox, fox, squirrel, etc.
- Digest: `ledger_sha256` for parity (verify‑ledger `--digest`)

## Readiness Checklist
- Memory/ledger read/write OK; hash chain validates
- Stego encode/decode round‑trip OK; CRC32 validated
- Knowledge aggregation produces persona order and tags

## TODO
- Enrich tags with chapter/scroll provenance
- Add JSON‑schema for memory entries and ledger payloads

## Cross‑Navigation
- Vessel agent: `../vessel/AGENT.md`
