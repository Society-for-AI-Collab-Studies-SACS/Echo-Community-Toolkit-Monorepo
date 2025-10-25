# VesselOS Kira Prime - Architectural Analysis & Self-Instruction Guide

**Version**: 1.0.0  
**Purpose**: Strategic analysis, use cases, and architectural improvements  
**Audience**: AI agents implementing and extending the system  
**Last Updated**: 2025-10-15

---

## 📋 Executive Summary

VesselOS Kira Prime unifies the Garden, Echo, Limnus, and Kira agents into a Prime-orchestrated ritual pipeline that powers interactive narrative authoring, semantic memory recall, and release automation. This guide equips autonomous agents with architectural awareness, improvement heuristics, and decision frameworks so they can extend the system safely. Key takeaways:

- The Prime orchestrator mediates a fixed Garden → Echo → Limnus → Kira sequence for free-form inputs while providing escape hatches for explicit subcommands.
- Limnus’ vector store now supports FAISS with SBERT embeddings; correctness hinges on maintaining both vector and embedder backends.
- Release automation (`scripts/checklist_phase2.sh`) bundles validation, UI builds, FAISS index refresh, and Kira packaging. Network constraints and platform-managed Python must be respected via user installs and environment exports.
- Frontend telemetry, persona routing, and soulcode embeddings are tightly coupled with the CLI; reflecting new event types requires TypeScript-safe telemetry emissions.

---

## 🎯 Core Use Cases Analysis

### 1. Interactive Narrative Authoring

**Current Implementation**: ✅ Functional  
Garden governs ritual stages; Echo provides persona-styled narration; Limnus stores narrative memories; Kira validates closure.

**Use Case Flow**

```
Author → "Let's brainstorm character ideas"
  ↓
Prime detects: squirrel persona (brainstorm keyword)
  ↓
Garden: remains in Scatter stage (status stays open for ideation)
  ↓
Echo: styles output with playful Squirrel energy, emitting brainstorm prompts and glyph hooks
  ↓
Prime orchestrator routes context toward Limnus with semantic indexing enabled
  ↓
Limnus: caches ideation snippets with L2 TTL, tags as `brainstorm`, and indexes them semantically
  ↓
Kira: surfaces validation checks (memory counts, glyph parity) and summarizes actionable next steps
  ↓
Author receives persona-aligned brainstorm draft plus memory ledger entry link
```

**Status Output Example**

```
🟡 [scatter] What if the protagonist fears vulnerability?
```

**Gaps Identified**
- ❌ No character sheet management  
- ❌ No plot thread tracking  
- ❌ No conflict/resolution detection

**Improvement Opportunities**
1. `garden.entities` – Track characters, locations, and motifs throughout the ritual.
2. `limnus.thread_tracking` – Link related memories by narrative arc or glyph path.
3. `echo.voice_consistency` – Maintain persona continuity across sessions.
4. `kira.flag_conflicts` – Highlight lore clashes when new entries contradict prior canon.

### 2. Personal Knowledge Management

**Current Implementation**: ⚠️ Partial  
Semantic search via hash or SBERT vectorization; three-tier memory (L1/L2/L3); ledger provides audit trail.

**Use Case Flow**

```
User → "Remember: Project deadline is Oct 20"
  ↓
Garden: logs intent as Witness stage note
  ↓
Echo: acknowledges with neutral tone, confirms capture
  ↓
Prime orchestrator routes the reminder toward Limnus for semantic caching
  ↓
Limnus: stores memory in L1 with TTL=7 days, tags `project,deadline`
  ↓
User later → "When is the project due?"
  ↓
Prime orchestrator routes the query toward Limnus with semantic index enabled
  ↓
Prime routes → Limnus recalls relevant memories
  ↓
Limnus: semantic recall locates the stored entry
  ↓
Limnus: returns deadline details; if FAISS available, also provides semantic proximity matches
  ↓
Output: returns cached memory with contextual metadata
```

**Observations**
- ⚠️ Without SBERT weights cached, recall quality drops to hash baseline.
- ✅ Ledger ensures audit trail, but manual review is required for expired entries.

**Gaps Identified**
- ❌ No time-based retrieval ("when did I learn X?")
- ❌ No explicit relationships between related memories
- ❌ No memory decay simulation to model forgetting
- ❌ No contradiction detection between old and new information

**Improvement Opportunities**
- Automate promotions (`limnus promote --tag project --layer L2`) when reminders recur.
- Add `kira summarize --scope project` for briefing exports.
- Introduce temporal indexing (`limnus.temporal_index`) for chronological queries.
- Build a lightweight knowledge graph (`limnus.memory_graph`) to connect entries.
- Enhance Kira to detect contradictions (`kira.validate_consistency`).
- Score memory importance to auto-promote L1→L2→L3 based on utility frequency.

### 3. Collaborative Research & Synthesis

**Current Implementation**: ❌ Not supported  
No multi-source ingestion, citation tracking, or synthesis tooling exists today.

**Desired Use Case Flow**

```
Researcher → "Synthesize findings on memory consolidation"
  ↓
Prime orchestrator gathers recent memories, external notes, and referenced sources
  ↓
Garden structures synthesis (Scatter → Witness → Plant → Tend → Harvest) to manage research phases
  ↓
Echo provides integrative narration tying together gathered insights
  ↓
Limnus: clusters related memories, assembles supporting evidence, and flags contradictions
  ↓
Kira validates no contradictions across the assembled evidence
  ↓
Kira: compiles synthesis with citations, open questions, and recommended next steps
  ↓
Output: research summary with provenance and action items
```

**Gaps Identified**
- ❌ No ingestion pipeline for research notes or external references
- ❌ No provenance/citation tracking in Limnus or Kira outputs
- ❌ No thematic clustering or synthesis primitives
- ❌ No collaborative workspace for multiple researchers

**Improvement Opportunities**
1. Extend Limnus with research corpus loading and clustering (`limnus.research_cluster`).
2. Add `limnus.source_tracking` to retain provenance for each memory entry.
3. Enable `garden.synthesis_mode` — a dedicated ritual for integration tasks.
4. Provide Echo with `echo.synthesis_voice` (neutral academic persona).
5. Introduce `prime.synthesis_workflow` to orchestrate multi-step synthesis.
6. Add collaborative session syncing so multiple operators can contribute safely.

### 4. Code Development Assistant

**Current Implementation**: ⚠️ Possible but not optimized  
Supports code snippet capture and ritual-based stage tracking but lacks language-aware helpers.

**Use Case Flow**

```
Developer → "prime route 'Debug the authentication bug'"
  ↓
Prime detects: fox persona (debug keyword)
  ↓
Garden: advances to Tend stage (fixing/refining)
  ↓
Echo: adopts engineer persona to summarize current context
  ↓
Echo: provides focused, analytical output
  ↓
Limnus: recalls related code memories and stores new reproducible steps; tags `auth,bugfix`
  ↓
Kira: validates progress, proposes next diagnostic steps
  ↓
Output: structured debugging plan with linked memory entries
```

**Gaps Identified**
- ❌ No code-aware parsing (stack traces, diffs)
- ❌ No integration with unit test runners or linters
- ❌ No snippet versioning or diff history
- ❌ No explicit bug tracker linkage

**Improvement Opportunities**
1. Add `limnus.code_index` for language-aware embeddings and snippet retrieval.
2. Introduce `prime.dev_workflow` to manage test/lint execution steps.
3. Provide Echo with `echo.dev_voice` for concise technical narration.
4. Extend Kira with `kira.dev_validate` to run smoke tests and summarize results.
5. Integrate Garden with issue trackers (`garden.ticket_bridge`) for status sync.

### 3. Phase 2 Release Automation

**Current Implementation**: ✅ Scripted  
`./scripts/checklist_phase2.sh` stitches Python dependency sync, pytest, FAISS index rebuild, UI build/tests, changelog assembly, and Kira packaging.

**Use Case Flow**

```
Agent → export PATH="$HOME/.local/bin:$PATH"
  ↓
Agent → ./scripts/checklist_phase2.sh
  ↓
Python deps install with --user when outside venv (PEP 668 safe)
  ↓
Pytest + FAISS rebuild + Vite build/test succeed
  ↓
Kira emits package artifact + CHANGELOG_RELEASE.md
```

**Observations**
- ✅ Script adapts to managed Python by forcing `--user` installs.
- ⚠️ Generated artifacts (`lambda-vite-dist.tar.gz`, `state/limnus.faiss*`) must be staged or cleaned.
- ⚠️ npm advisories remain (moderate severity); track and assess.

**Improvement Opportunities**
- Add `--clean` flag removing artifacts when release packaging isn’t needed.
- Cache npm dependencies or commit `package-lock.json` to reduce rebuild time.

---

## 🧭 Architectural Assessment

### Components & Responsibilities

| Component | Language | Responsibilities | Critical Dependencies |
|-----------|----------|------------------|-----------------------|
| Garden Agent (`agents/garden/`) | Python | Ritual stage management, ledger logging | `schema/`, `state/` |
| Echo Agent (`agents/echo/`) | Python | Persona modulation (Squirrel/Fox/Paradox), narration generation | Persona templates |
| Limnus Agent (`agents/limnus/`) | Python | Semantic memory, FAISS indexing, stego ledger ops | `sentence-transformers`, `faiss-cpu`, `Pillow` |
| Kira Agent (`agents/kira/`) | Python | Validation, mentoring, Git packaging | Git CLI, repo metadata |
| Lambda Vite UI (`lambda-vite/`) | TypeScript | Control panel dashboards, telemetry display | Vite, Vitest, Telemetry bus |
| Prime CLI (`vesselos.py`) | Python | Orchestration, routing, command parsing | `click`, agent interfaces |

### Strengths
- Deterministic Garden → Echo → Limnus → Kira orchestration ensures consistent side effects.
- VectorStore abstraction isolates backend choice (hash → TF-IDF → SBERT → FAISS) with fallbacks.
- Release script consolidates cross-language tooling, reducing manual steps.
- Documentation coverage is strong, with system diagrams and workflow guides.

### Gaps & Risks
- SBERT downloads impede offline usage; fallback embeddings reduce recall quality.
- Telemetry bus expansions must remain type-safe to avoid runtime inconsistencies.
- Generated artifacts can clutter long-lived branches without clean-up conventions.
- Persona detection heuristics reside in Echo; centralizing rules would simplify auditing.

---

## 🚀 Improvement Roadmap

| Priority | Area | Proposal | Expected Impact |
|----------|------|----------|-----------------|
| High | Limnus Embeddings | Ship offline SBERT bundle with version pin; add `limnus preload` command | Reliable recall without network access |
| High | Release Automation | Add `--clean` & `--keep-artifacts` to checklist; persist logs under `dist/logs/` | Cleaner worktrees, auditable outputs |
| Medium | Persona Routing | Move keyword map to Prime config (`config/persona_rules.yaml`) | Central governance, runtime adjustability |
| Medium | Telemetry | Add typed registry & schema validation for events | Prevents emitter/listener drift |
| Low | Stego Ops | Provide CLI to decode PNG payloads | Eases QA verification |

---

## 🧠 Decision Frameworks for Autonomous Agents

### Modifying Agent Routing
1. Confirm the feature crosses agent boundaries.
2. Update Prime orchestrator; never bypass Garden → Echo → Limnus → Kira flow unless the command targets a specific agent.
3. Mirror changes in documentation and automated tests.

### Choosing a Vector Backend

| Condition | Backend | Action |
|-----------|---------|--------|
| Offline, minimal deps | `hash` | Accept lower recall quality; skip FAISS |
| Sklearn available, SBERT absent | `tfidf` | Deterministic search without heavy models |
| SBERT cached | `sbert` | CPU embeddings; reindex periodically |
| SBERT + FAISS | `faiss` | Ensure index paths configured; monitor status |

### Adding Telemetry Events
1. Extend `lambda-vite/src/types/telemetry.ts`.
2. Emit via typed `telemetry.emit`.
3. Cover with Vitest suites.

### Running Release Checklist
1. Export user `PATH` if pip scripts installed to `~/.local/bin`.
2. Run `./scripts/checklist_phase2.sh` (override `PYTHON_BIN` if needed).
3. Review artifacts and stage/clean intentionally.

---

## 🔧 Self-Instruction Checklist for AI Maintainers

- [ ] Confirm SBERT weights cached or run `limnus preload`.
- [ ] Use `--user` installs when venv unavailable; respect PEP 668.
- [ ] Align persona keywords with ritual stages before modifying Echo.
- [ ] Run `python3 -m pytest` and `npm test -- --run` for relevant changes.
- [ ] Update docs alongside CLI or release modifications.
- [ ] Log key decisions in PR templates or changelogs.

---

## 📚 Reference Links

- Prime CLI reference: `docs/VesselOS_Command_Reference.md`
- Ritual workflow: `docs/VesselOS_Kira_Prime_Guide.md`
- System diagrams: `docs/SYSTEM_DIAGRAM_API_REFERENCE.md`
- Release automation: `scripts/checklist_phase2.sh`
- Telemetry types: `lambda-vite/src/types/telemetry.ts`
- Limnus vector store: `memory/vector_store.py`

---

## 🧾 Appendix: Debug Recipes

| Scenario | Recipe |
|----------|--------|
| SBERT download blocked | `python3 -m sentence_transformers.download_models all-MiniLM-L6-v2 --cache-dir state/models/` |
| FAISS index corrupted | Delete `state/limnus.faiss*`, rerun `vesselos.py limnus reindex --backend faiss` |
| Telemetry build error | Ensure emissions use `TelemetryEventType`; rerun `npm run build` |
| Checklist clean-up | `rm -f lambda-vite-dist.tar.gz state/limnus.faiss*` |

---

This guide is a living document. Autonomous agents should append new patterns, pitfalls, and mitigation strategies after each significant VesselOS Kira Prime change.
