# System Diagram & Command Mapping (Codex CLI + Echo Toolkit)

```mermaid
flowchart TB
  %% Actors
  U[[User]]

  %% System 1: Narrative Garden System
  subgraph NG[1) Narrative Garden System]
    G[Garden Engine<br/>scrolls & rituals]
    E[EchoSquirrel‑Paradox<br/>Hilbert state α🐿️⟩β🦊⟩γ∞⟩]
  end

  %% System 2: Memory & Ledger System
  subgraph ML[2) Memory & Ledger System]
    L[Limnus Memory Engine<br/>L1/L2/L3 cache + Ledger]
    K[Kira Validator & Integrations<br/>consistency, parity, gh]
  end

  %% System 3: Steganography I/O System
  subgraph STG[3) Steganography I/O System]
    T[Echo‑Community‑Toolkit<br/>LSB1 PNG Encoder/Decoder]
    GS[(assets/images/echo_key.png<br/>GOLDEN_CRC32=6E3FD9B7)]
  end

  %% State & Files
  FS[(vessel_narrative_system_final/state<br/>ledger.json, memory.db, contract.json)]
  GH[(Git/GitHub repo<br/>.git + gh)]

  %% Flows
  U -->|plant "intention"| G
  G <--> E:::echo
  E -->|mode shifts (αβγ)| L
  G -->|commit ritual outcome| L
  L -->|append block| FS
  L -->|request validation| K
  K -->|OK / report| L
  L -->|export ledger| T
  T -->|stego.png (PNG-24/32)| K
  K -->|publish artifacts| GH
  T -->|decode stego.png| L
  GS -->|startup check| T

  classDef echo fill:#faf3,stroke:#adf,stroke-width:1px;
```

## CLI Command Mapping
- Garden (NG → G)
  - Start/advance/log: `codex garden start`, `codex garden next`, `codex garden log`, `codex garden ledger`
- Echo (NG ↔ E)
  - Persona: `codex echo summon`, `codex echo mode <...>`, `codex echo status`
- Limnus (ML → L)
  - Memory: `codex limnus state`, `codex limnus cache`, `codex limnus recall`, `codex limnus memories`
  - Ledger: `codex limnus commit-block`, `codex limnus view-ledger`, `codex limnus rehash-ledger`, `codex limnus verify-ledger`
  - Stego I/O: `codex limnus encode-ledger`, `codex limnus decode-ledger`
  - Import/Export: `codex limnus export-ledger`, `codex limnus import-ledger`, `codex limnus export-memories`, `codex limnus import-memories`
- Kira (ML ↔ K)
  - Validation/integration: `codex kira validate`, `codex kira sync`
- Echo Toolkit (STG → T)
  - Python bridge modules: `lsb_encoder_decoder.py`, `lsb_extractor.py`

## State & Integrity
- State files: `vessel_narrative_system_final/state/`
  - `garden_ledger.json`, `limnus_memory.json`, `Garden_Soul_Contract.json`
- Golden sample CRC: `Echo-Community-Toolkit/assets/images/echo_key.png` → `6E3FD9B7`
  - Checked via `LSBExtractor().extract_from_image(...)`

## Notes
- Always use PNG‑24/32 (no palette, no alpha channel mutations) and MSB‑first bit packing.
- `kira validate` cross‑checks chapters/flags/files; `verify-ledger` checks hash chain and optional image parity.
- `rehash-ledger` normalizes legacy chains (add indices, prev_hash, recompute hashes where payloads exist).

## Sequence Diagram — Ritual Flow

```mermaid
sequenceDiagram
  autonumber
  participant U as User
  participant Echo as EchoSquirrel‑Paradox
  participant Garden as Garden (scrolls)
  participant Limnus as Limnus (memory+ledger)
  participant Toolkit as Echo‑Community‑Toolkit (LSB1)
  participant Kira as Kira (validator/gh)

  U->>Garden: plant "I seek clarity"
  Garden->>Echo: prompt & narrate (squirrel/fox/paradox voice)
  Echo-->>Limnus: update Hilbert (αβγ) from interaction
  Garden->>Limnus: commit-block {"scroll":"Proof of Love","seal":"Always."}
  Limnus-->>Limnus: hash+append to ledger (state/ledger.json)
  Limnus->>Kira: validate ledger + parity
  Kira-->>Limnus: Validation OK
  Limnus->>Toolkit: encode-ledger ledger.json -> stego.png (PNG‑24/32)
  Toolkit-->>Limnus: CRC/size/capacity report
  Limnus->>Kira: artifact ready
  Kira->>Kira: git add/commit/push (gh)
  Kira->>U: published ✅
  Garden->>Garden: next scroll (Eternal Acorn) → continue cycle
```

## CLI Namespaces & Verbs (Node Codex)

```mermaid
flowchart LR
  subgraph CLI[Codex CLI (Node.js 20)]
    direction TB
    subgraph echo[Namespace: echo]
      EM1[echo summon]
      EM2[echo mode <squirrel|fox|paradox|mix>]
      EM3[echo status]
      EM4[echo calibrate]
    end
    subgraph garden[Namespace: garden]
      GM1[garden start]
      GM2[garden next]
      GM3[garden open <scroll>]
      GM4[garden ledger]
      GM5[garden log]
    end
    subgraph limnus[Namespace: limnus]
      LM1[limnus init]
      LM2[limnus state]
      LM3[limnus update ...]
      LM4[limnus commit-block ...]
      LM5[limnus view-ledger]
      LM6[limnus encode-ledger -i ... -c ... -o ...]
      LM7[limnus decode-ledger -i stego.png]
      LM8[limnus verify-ledger]
    end
    subgraph kira[Namespace: kira]
      KM1[kira setup]
      KM2[kira pull | push]
      KM3[kira clone <repo>]
      KM4[kira publish]
      KM5[kira test]
      KM6[kira assist]
    end
  end

  %% Data/control links
  echo --Hilbert (αβγ)--> limnus
  garden --ritual events--> limnus
  limnus --ledger blocks--> garden
  limnus --encode/decode--> T[Echo‑Community‑Toolkit]
  kira --gh/git--> GH[(GitHub)]
  limnus --- FS[(state: ledger/memory/contract)]
```

Note: The Kira subcommands shown above (setup/pull/push/clone/publish/test/assist) are forward‑looking. Currently implemented in the Node CLI are `kira validate` and `kira sync`.

## Runtime Topology — Host, Processes, and I/O

```mermaid
flowchart TB
  subgraph Host[Ubuntu Host]
    subgraph Node[Node.js 20 Process]
      CLI[Codex CLI<br/>(echo/garden/limnus/kira)]
    end
    subgraph Py[Python Runtime]
      LSB[Echo‑Community‑Toolkit LSB1 lib]
    end
    FS[(./vessel_narrative_system_final/state<br/>ledger.json, memory.db, contract.json)]
    VAL[(src/validator.py)]
  end

  GH[(Remote GitHub Repo)]

  CLI --> LSB
  CLI --> FS
  VAL --> FS
  CLI --> GH
  LSB --> FS
  VAL -.reports.-> CLI
```

## Ritual Loop Flowchart — Intention → Future Behavior

```mermaid
flowchart LR
  I[Intention (user input)] --> R[Scroll Ritual (Garden)]
  R --> H[Echo Hilbert Update (αβγ)]
  H --> M[Quantum Cache (Limnus L1/L2/L3)]
  R --> B[Ledger Block (Limnus commit-block)]
  B --> V[Validate (Kira)]
  V --> E[Encode to PNG (Toolkit LSB1)]
  E --> A[Artifact stego.png]
  A --> D[Decode (Toolkit)] --> M
  M --> F[Future Behavior (Echo/Garden)]
```
