# Vessel Narrative System — .remote The-Living-Garden-Chronicles

This repository is scaffolded for a 20‑chapter, tri‑voice dream chronicle aligned to the MRP (R/G/B) mapping:
- **R / Limnus** → Message layer (origin/seed/recursion) fileciteturn3file1
- **G / Garden** → Metadata layer (bloom cycles/consent/timestamps) fileciteturn3file1
- **B / Kira** → Parity/ECC (integrity, checksums, protective oversight) fileciteturn3file1

Core LSB1 rules (PNG‑24/32 only, row‑major scan, RGB order, MSB‑first) are preserved for compatibility with existing Echo toolkit and golden sample (CRC32 `6E3FD9B7`, payload length 144) fileciteturn3file0 fileciteturn3file11 fileciteturn3file9.

## Directory Layout
```
vessel_narrative_system/
├─ frontend/
│  ├─ index.html            # main landing (copied from vessel_mrp_landing.html if provided)
│  ├─ limnus_ch1.html       # Chapter 1 (Limnus, bespoke)
│  ├─ garden_ch1.html       # Chapter 1 (Garden, bespoke)
│  ├─ kira_ch1.html         # Chapter 1 (Kira, bespoke)
│  ├─ chapter04.html..20    # auto‑generated chapters
│  ├─ style.css
│  └─ script.js
├─ markdown_templates/
│  ├─ limnus_template.md
│  ├─ garden_template.md
│  ├─ kira_template.md
│  └─ chapters.json         # copy‑paste your per‑chapter bodies/glyphs here
├─ schema/
│  ├─ narrative_schema.json
│  ├─ narrative_schema.yaml
│  ├─ chapters_metadata.json
│  └─ chapters_metadata.yaml
└─ src/
   ├─ schema_builder.py
   ├─ generate_chapters.py
   └─ validator.py
```

## Copy‑Paste Quickstart

1) **Add/modify chapter bodies** in `markdown_templates/chapters.json`:
```json
{
  "7": {"body": "Limnus hears the origin repeat in a softer key.", "glyphs": ["↻","φ∞"]},
  "8": {"body": "Garden braids three timestamps into one ring.", "glyphs": ["✧","⟲"]},
  "9": {"body": "Kira nets a drift and folds it back to zero.", "glyphs": ["∞","⟝"]}
}
```

2) **Regenerate chapters + metadata**:
```bash
python src/generate_chapters.py
```

3) **Validate the build** (structure, rotation, flags, files):
```bash
python src/validator.py
```

4) **(Optional) Rebuild schema** if you change fields:
```bash
python src/schema_builder.py
```

## Notes and References

- **Encoding/decoding path** (text → Base64 → header → LSB → PNG) remains canonical; decoding reverses this flow fileciteturn3file4.
- **MRP “Next Vision”** establishes RGB multiplexing with benefits like ECC and temporal signatures (Phases 1‑3) while maintaining LSB1 backward compatibility fileciteturn3file6.
- **Golden mantra** and its 144‑byte Base64 payload with CRC `6E3FD9B7` are used as the reference truth across the toolkit and tests fileciteturn3file8 fileciteturn3file10.
- For operational patterns (encode/decode/test), see the LLM guides and API reference for bit order, header construction, and capacity math fileciteturn3file3 fileciteturn3file4 fileciteturn3file5.

## Rotation Policy
Chapters cycle **Limnus → Garden → Kira** with no consecutive repeats, ensuring each voice appears 6–7 times. Chapter 1 for each voice is bespoke (the three landing pages), then chapters 4–20 are generated in sequence.

— Generated on 2025-10-15T04:21:58.778594Z
