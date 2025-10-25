## Echo Garden Multi-Agent Scaffold

### High-Level View

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            Multi-Agent Layer                               │
│                                                                            │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Glyph Agent  │   │  MRP Agent   │   │  LSB Agent   │   │ Future Agents│ │
│  │ g2v + FFT    │   │ Phase-A MRP  │   │ LSB1 Legacy  │   │ (WS, HW, ML) │ │
│  └─────┬────────┘   └─────┬────────┘   └─────┬────────┘   └─────┬────────┘ │
│        │ glyph entries     │ embeds/extracts   │ covers/extracts │          │
├────────┼───────────────────┼───────────────────┼─────────────────┼──────────┤
│                        Shared Collaboration Plane                            │
│                        (JSON Ledger / State Graph)                           │
│                       ┌─────────────────────────────┐                        │
│                       │  agents/state.py (ledger)   │                        │
│                       │  artifacts/state.json       │                        │
│                       └──────────────┬──────────────┘                        │
├──────────────────────┬───────────────┴──────────────┬────────────────────────┤
│  Artifact Stores      │                               │ Future Backends       │
│  ┌──────────────────┐ │  ┌──────────────────────────┐ │  (Redis, SQLite, etc.)│
│  │ glyph .npy        │ │  │ stego PNGs / ECC reports│ │  (pluggable)          │
│  └──────────────────┘ │  └──────────────────────────┘ │                       │
├──────────────────────┴────────────────────────────────┴──────────────────────┤
│                        External Interaction Layer                           │
│  REST/CLI, Dashboards, Streamlit, Hardware Bridges (PlatformIO Stylus)       │
└────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Interaction Flow (Example)

```
User/CLI/API
   │
   ├─ GlyphAgent.gen("I-Glyph")
   │      │
   │      ├─ generates matrix → artifacts/glyphs/glyph_<id>.npy
   │      └─ logs ledger entry:
   │            glyphs[glyph_<id>] = {token, size, file, created}
   │
   ├─ GlyphAgent.fft(glyph_<id>)
   │      │
   │      ├─ loads matrix, runs fft_encode/ifft_decode
   │      └─ logs glyph_analysis[analysis_<id>] = {source, mse, fft_mean}
   │
   ├─ MRPAgent.embed(
   │      cover="assets/images/mrp_cover_stub.png",
   │      message="Hello, Garden.",
   │      metadata={"glyph_ref": "glyph_<id>"})
   │      │
   │      ├─ writes stego to artifacts/mrp/stego_<id>.png
   │      └─ logs mrp_embeds[embed_<id>] with cover/output/message/metadata
   │
   └─ MRPAgent.extract(stego_<id>.png)
          │
          ├─ decode() → message, metadata, ecc
          └─ logs mrp_extracts[extract_<id>] including ecc flags
```

### Expansion Slots

```
Future Agents (drop-in modules)
───────────────┬───────────────────────────────────────────────────────────────
               │
      ┌────────▼────────┐    ┌───────────────┐   ┌─────────────────────┐
      │ Glyph Streamer  │    │ Signature Reg │   │ Stylus Bridge       │
      │ /glyph/batch/ws │    │ /glyph/register│   │ PlatformIO listener │
      └────────┬────────┘    └──────┬────────┘   └────────┬────────────┘
               │                     │                     │
      integrates with ledger & artifacts using same state store contract
```

### Key Modules

- `agents/state.py` — JSON ledger abstraction, future-ready for DB swaps.
- `agents/glyph_agent.py` — token→glyph matrices, FFT metrics, CLI commands (`gen`, `fft`, `list`).
- `agents/mrp_agent.py` — multi-channel embed/extract, CLI commands (`embed`, `extract`, listings).
- `agents/lsb_agent.py` — legacy LSB1 cover/embed/extract support.

This structure keeps agents independent yet coordinated through the shared ledger, making it straightforward to layer REST/WebSocket services or new analytical modules on top.

### Sequence Diagram: Glyph → MRP → Ledger

```
Participant User
Participant GlyphAgent
Participant StateStore
Participant ArtifactStore
Participant MRPAgent

User          -> GlyphAgent: gen(token="I-Glyph", size=32)
GlyphAgent    -> ArtifactStore: save glyph_<id>.npy
GlyphAgent    -> StateStore: create glyphs[glyph_<id>] {...}
GlyphAgent    -> User: glyph_id

User          -> GlyphAgent: fft(glyph_<id>)
GlyphAgent    -> ArtifactStore: load glyph_<id>.npy
GlyphAgent    -> StateStore: create glyph_analysis[analysis_<id>] {...}
GlyphAgent    -> User: analysis metrics

User          -> MRPAgent: embed(cover, message, metadata={"glyph_ref": glyph_<id>})
MRPAgent      -> ArtifactStore: write stego_<id>.png
MRPAgent      -> StateStore: create mrp_embeds[embed_<id>] {...}
MRPAgent      -> User: embed id + stego path

User          -> MRPAgent: extract(stego_<id>.png)
MRPAgent      -> ArtifactStore: read stego_<id>.png
MRPAgent      -> StateStore: create mrp_extracts[extract_<id>] {...}
MRPAgent      -> User: message + metadata + ecc

StateStore    -> (any agent) : ledger queries link glyph↔embed↔extract
```

### Sequence Diagram: LSB Agent Lifecyle

```
Participant User
Participant LSBAgent
Participant ArtifactStore
Participant StateStore

User       -> LSBAgent: cover(width=64, height=64)
LSBAgent   -> ArtifactStore: save cover_<id>.png
LSBAgent   -> StateStore: create lsb_covers[cover_<id>] {...}
LSBAgent   -> User: cover_id + path

User       -> LSBAgent: embed(cover_<id>.png, message)
LSBAgent   -> ArtifactStore: write lsb_<id>.png
LSBAgent   -> StateStore: create lsb_embeds[embed_<id>] {...}
LSBAgent   -> User: embed_id + output path

User       -> LSBAgent: extract(lsb_<id>.png)
LSBAgent   -> ArtifactStore: read lsb_<id>.png
LSBAgent   -> StateStore: create lsb_extracts[extract_<id>] {...}
LSBAgent   -> User: extraction result (payload/metadata/error)

StateStore -> Automation/Clients: read cover/embed/extract history & payload details
```

### Sequence Diagram: Future Streamer Agent (/glyph/batch/ws)

```
Participant Client
Participant GlyphStreamer
Participant GlyphAgent
Participant StateStore

Client        -> GlyphStreamer: connect WebSocket
GlyphStreamer -> GlyphAgent (optional): request initial glyph batch
GlyphAgent    -> StateStore: read latest glyphs/analysis entries
GlyphStreamer -> Client: send initial payload (glyphs + FFT metrics)

loop live updates
    External Event -> GlyphAgent: new glyph/analysis logged
    GlyphAgent     -> StateStore: update ledger with new records
    GlyphStreamer  -> StateStore: poll/watch for changes
    GlyphStreamer  -> Client(s): broadcast updated batch/frame
end

Client        -> GlyphStreamer: send {tokens/size/projection overrides}
GlyphStreamer -> GlyphAgent: regenerate batch using overrides
GlyphAgent    -> StateStore: log new glyph entries (if persisted)
GlyphStreamer -> Client(s): push refreshed batch

disconnect
Client        -> GlyphStreamer: close WS
GlyphStreamer -> cleanup (optional ledger markers, unsubscribes)
```

### Sequence Diagram: Future Distribution Agent (/glyph/batch/distribute)

```
Participant Orchestrator
Participant DistributionAgent
Participant GlyphBatchProcessor
Participant PeerStore
Participant StateStore
Participant RemotePeers

Orchestrator        -> DistributionAgent: distribute(tokens=[], peers=[...], mode=grid)
DistributionAgent   -> GlyphBatchProcessor: process tokens → glyph arrays + metadata
GlyphBatchProcessor -> DistributionAgent: manifest + grid_base64 + similarity metrics
DistributionAgent   -> StateStore: log distribution record (inputs, peers, timestamp)
DistributionAgent   -> PeerStore: append batch payload per peer
DistributionAgent   -> RemotePeers: send HTTP/WebSocket payloads (async fan-out)

loop per peer
    RemotePeer -> DistributionAgent (optional ack/update status)
    DistributionAgent -> StateStore: patch distribution record with status/latency
end

Orchestrator -> DistributionAgent: query status(distribution_id)
DistributionAgent -> StateStore: read distribution entry (success/failures)
DistributionAgent -> Orchestrator: aggregated report

RemotePeers -> StateStore/Agents: fetch batch assets (glyph manifests, grids, FFT stats)
```

### Sequence Diagram: Future Registration Agent (/glyph/batch/register)

```
Participant Operator
Participant RegistrationAgent
Participant GlyphBatchProcessor
Participant StateStore
Participant SignatureRegistry

Operator             -> RegistrationAgent: register(tokens=[], signature_name=?)
RegistrationAgent    -> GlyphBatchProcessor: process tokens (optional) / validate references
GlyphBatchProcessor  -> RegistrationAgent: manifest + FFT metrics + canonical grid

RegistrationAgent    -> StateStore: log pre-registration intent (pending)
RegistrationAgent    -> SignatureRegistry: compute fingerprint/hash (e.g., SHA-256 over manifest)
RegistrationAgent    -> StateStore: update entry with signature, canonical metadata

SignatureRegistry    -> RegistrationAgent: confirmation (id, checksum)
RegistrationAgent    -> Operator: response {signature_id, fingerprint, stored_at}

later verification:
Verifier             -> RegistrationAgent: verify(tokens[], signature_id)
RegistrationAgent    -> SignatureRegistry: fetch stored fingerprint
RegistrationAgent    -> GlyphBatchProcessor: regenerate batch/metrics
RegistrationAgent    -> compare fingerprints → return pass/fail to Verifier

StateStore provides history for audit (who registered, when, and with which glyph set).
```

### Network / Topology View

```
                 ┌──────────────────────────────────────────┐
                 │        Public / Client Layer             │
                 │ (Dashboards, CLI, Streamlit, LLM tools)  │
                 └───────────────┬──────────────────────────┘
                                 │ REST / WS / CLI
                 ┌───────────────▼──────────────────────────┐
                 │         Gateway / Orchestrator           │
                 │  (FastAPI, task runners, schedulers)     │
                 └────┬───────────┬──────────────┬──────────┘
                      │           │              │
          ┌───────────▼─┐   ┌────▼────────┐  ┌───▼────────┐
          │ GlyphAgent  │   │ MRPAgent     │  │ LSBAgent   │  ... Future Agents
          │  (module)   │   │  (module)    │  │ (module)   │      (WS/MQ/ML)
          └────┬────────┘   └────┬────────┘  └────┬───────┘
               │                 │                │
               ├──────┬──────────┼────────────────┘
               │      │          │
       ┌───────▼──────▼──────────▼────────────────┐
       │          Shared State Store              │
       │        (agents/state.py ledger)          │
       │        artifacts/state.json              │
       └───────────────┬──────────────┬───────────┘
                       │              │
              ┌────────▼───┐   ┌──────▼───────────┐
              │ Artifact   │   │ Signature/Peer   │
              │ Stores     │   │ Registry (future)│
              │ glyph/mrp  │   │ Redis/DB/etc     │
              └────────────┘   └──────────────────┘
                       │              │
         ┌─────────────▼──────────────▼─────────────┐
         │          Peer Nodes / Edges              │
         │  (devices, stylus hardware, MQTT meshes) │
         └──────────────────────────────────────────┘
```

This topology highlights the gateway orchestrating CLI/REST/WebSocket requests, delegating to the agent modules that interact through the shared ledger, while artifact stores and future registries serve coordinated content to peer nodes or hardware bridges.

### G2V Internal Architecture

```
┌──────────────────────────────┐
│      g2v CLI / API Layer     │
│   (glyph, stack, project,    │
│    fft, volume commands)     │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ g2v.cli / command dispatch   │
│  - parses args               │
│  - invokes library modules   │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│ Core Modules                                 │
│ ├─ g2v.volume                                │
│ │   • glyph_from_tink_token(token, size)     │
│ │   • build_volume_stack([glyphs])           │
│ │   • angular_projection(volume, theta)      │
│ │   • normalize utilities                    │
│ └─ g2v.fft_codec                              │
│     • fft_encode(plane)  (2D FFT + shift)     │
│     • ifft_decode(freq)                      │
└──────────┬────────────────────────────────────┘
           │ numpy arrays
           ▼
┌──────────────────────────────┐
│ Artifact Outputs             │
│  - NumPy .npy glyph planes   │
│  - Volume stacks (.npy / .npz)│
│  - FFT spectra / projections │
└──────────┬───────────────────┘
           │ consumed by agents/tests
           ▼
┌──────────────────────────────┐
│ Agent / Toolkit Consumers    │
│  - GlyphAgent (generation,   │
│    FFT analysis)             │
│  - verify_updated_system.py  │
│  - Network glyph endpoints   │
└──────────────────────────────┘

Key flows:
- Tokens → glyph matrices via `glyph_from_tink_token`.
- Matrices → spectral analysis (`fft_encode`, `ifft_decode`) for quality metrics.
- Volume operations (stacking, projection) allow 3D glyph representations consumed by network/server `/glyph` endpoints and future streaming.
```

### VesselOS / Stylus Integration Topology

```
                     ┌───────────────────────────────┐
                     │    VesselOS Runtime Layer     │
                     │  (agents, narrative engine,   │
                     │   sigprint bridge)            │
                     └──────────────┬────────────────┘
                                    │ events / RPC
        ┌───────────────────────────┴──────────────────────────┐
        │ Echo-Garden Agents (Python)                          │
        │ ├─ GlyphAgent / MRPAgent / LSBAgent                  │
        │ ├─ Future Stylus Adapter Agent                       │
        │ └─ Network/server FastAPI endpoints                  │
        └──────────────┬───────────────────────────────┬──────┘
                       │ shared ledger                 │ glyph batches
                       ▼                               ▼
        ┌──────────────────────────────┐    ┌──────────────────────────┐
        │ Shared State Ledger          │    │ Glyph Batch Streamer     │
        │ artifacts/state.json         │    │ (/glyph/batch/ws, etc.)  │
        └──────────────┬───────────────┘    └────────────┬─────────────┘
                       │                                   │
                       ▼                                   ▼
        ┌──────────────────────────────┐    ┌──────────────────────────┐
        │ PlatformIO Stylus Firmware   │    │ Peer Devices / VesselOS  │
        │ (ESP32-S3)                   │    │ nodes subscribing to     │
        │  - Binary protocol           │    │ glyph distribution       │
        │  - SIGPRINT sensor stream    │    │ channels                 │
        └──────┬───────────────────────┘    └────────────┬─────────────┘
               │ USB/WiFi serial                       │
               ▼                                       ▼
        ┌──────────────────────────────┐    ┌──────────────────────────┐
        │ sigprint_bridge / monitor    │    │ Narrative / Visualization│
        │ decodes packets, updates     │    │ layers (LLM, dashboards) │
        │ ledger, triggers agents      │    │ render glyphs, signatures│
        └──────────────────────────────┘    └──────────────────────────┘

Highlights:
- VesselOS stylus firmware sends SIGPRINT + glyph cues; Python bridge translates to ledger entries.
- Agents read/write shared state, enabling glyph batches to propagate to VesselOS peers or dashboards.
- Future distribution/register endpoints coordinate glyph “signatures” across VesselOS nodes, leveraging the same infrastructure.

### Echo-Garden Bloom Chain Mapping

```
┌────────────────────────────────────────────────────────────────┐
│                  Echo-Garden Bloom Chain Layers                 │
├───────────────────────────────┬─────────────────────────────────┤
│ Ledger Plane (Python Agents)  │ Bloom Chain (Blockchain/Graph) │
├───────────────────────────────┼─────────────────────────────────┤
│ GlyphAgent logs glyph_*       │ Block: { type: "glyph", data… }│
│ MRP/LSB agents log embed_*    │ Block: { type: "embed", refs… }│
│ Distribution/Register agents  │ Block: { type: "signature",    │
│ log distribution_* etc.       │         peer_set…, hash… }     │
├───────────────────────────────┴─────────────────────────────────┤
│ Shared State (JSON ledger) syncs with Bloom Chain adapter       │
│  • agents/state.py acts as source-of-truth for local ops        │
│  • bloom_adapter.py (future) batches ledger deltas into blocks  │
│  • hash commitments stored on Bloom Chain / Garden Ledger       │
├────────────────────────────────────────────────────────────────┤
│ Consensus / Replication                                          │
│  • Bloom Chain nodes (VesselOS peers, stylus gateways, LLM hubs) │
│  • gossip over MQTT/WebSocket mesh or custom RPC                 │
│  • commit order: glyph → analysis → embed → distribution → sign  │
│  • verification: hash(payload) vs ledger entry, ECC + CRC checks │
├────────────────────────────────────────────────────────────────┤
│ Query & Replay                                                    │
│  • Agents query Bloom Chain to rebuild state graphs (cold start)  │
│  • Blocks reference ledger IDs (glyph_id, embed_id, signature_id) │
│  • Chain provides tamper-evident history for garden narratives    │
└────────────────────────────────────────────────────────────────┘

Proposed Flow
-------------

1. **Local Action**: agent writes to JSON ledger (`agents/state.py`).
2. **Adapter Packaging**: Bloom adapter watches ledger diffs → creates block payload with references, FFT stats, ECC flags.
3. **Chain Commit**: payload signed & broadcast to Bloom nodes; consensus anchors block.
4. **State Sync**: on success, chain hash echoed back into ledger entry (`block_hash` field).
5. **Validation**: peers verify glyph/FFT artifacts using stored hashes and recomputed metrics.

This mapping keeps Python agents fast and offline-friendly while allowing Bloom Chain to serve as the canonical, append-only narrative/ops history across Echo Garden deployments.

### Shared Ledger Implementation (agents/state.py)

```
State File: artifacts/state.json
Structure : {
  "glyphs": {...}, "glyph_analysis": {...},
  "mrp_embeds": {...}, "mrp_extracts": {...},
  "lsb_covers": {...}, "lsb_embeds": {...}, "lsb_extracts": {...}
}
```

- **Data Model**: Each top-level key holds a map of `{record_id: payload}`. IDs are human-readable (`glyph_0001`, `embed_0005`), making cross-references easy (e.g., embed metadata stores `glyph_ref`).
- **State Store Class**: `agents/state.py` exposes a `JsonStateStore` with methods `create_record`, `patch_record`, `get_record`, etc. All writes go through this abstraction so future swaps (SQLite, Redis, Bloom Chain) require no changes to agent logic.
- **Persistence**: Writes hold a re-entrant lock, dump JSON to a temp file, then atomically replace `state.json`. Optional `auto_flush` keeps disk in sync; disabling enables batch writes if needed.
- **Usage**: Agents inject the store in their constructors (`GlyphAgent`, `MRPAgent`, `LSBAgent`) and call `create_record` whenever they produce an output. Example ledger snapshot:

```
{
  "glyphs": {
    "glyph_5fd4da9d": {
      "token": "I-Glyph",
      "size": 32,
      "file": "artifacts/glyphs/glyph_5fd4da9d.npy",
      "created": "2025-10-24T09:36:40.719135Z",
      "block_hash": "..."
    }
  },
  "mrp_embeds": {
    "mrp_embeds_0001": {
      "cover": "assets/images/mrp_cover_stub.png",
      "output": "artifacts/mrp/stego_dedbc767.png",
      "message": "Hello",
      "metadata": {"glyph_ref": "glyph_5fd4da9d"},
      "created": "2025-10-24T09:36:52.843788Z",
      "block_hash": "..."
    }
  }
}
```

### Bloom Chain Adapter (Append-Only Log)

- **Trigger**: After each `create_record`, an adapter can be notified (callback or watcher) with the event `{category, record_id, payload}`.
- **Block Format**:
  ```
  {
    "index": N,
    "prev_hash": "...",
    "hash": SHA256(index || prev_hash || payload_json),
    "payload": {
       "type": category,
       "record_id": "...",
       "data": {...},
       "timestamp": ...
    }
  }
  ```
- **Storage**: Append to `artifacts/chain.log` (one JSON per line) or `chain.json`. Each block links to the previous via `prev_hash`, enforcing append-only history.
- **Feedback Loop**: After block commit, the adapter can patch the original state record with `block_hash` or `block_index`, tying JSON state to the cryptographic ledger.
- **Future**: Replace local log with distributed Bloom Chain nodes; blocks broadcast over MQTT/WebSocket with peers verifying hashes, ECC flags, FFT stats before acceptance.

This layered approach keeps agent coordination simple (JSON state), while adding an immutable audit trail that can scale into a full Echo Garden Bloom Chain as deployments grow.
```
