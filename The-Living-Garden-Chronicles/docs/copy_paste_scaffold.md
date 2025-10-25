# Vessel Narrative Copy/Paste Scaffold

This guide packages the core assets required to rebuild the Vessel narrative system in a fresh environment. Copy each code block into the indicated path, then run the setup commands.

To refresh this document from the latest sources, run:

```bash
node tools/scaffold/generateCopyPasteKit.mjs
```

---

## Directory Layout

```
vessel_narrative_system/
├── frontend
│   ├── chapter04.html
│   ├── chapter05.html
│   ├── chapter06.html
│   ├── chapter07.html
│   ├── chapter08.html
│   ├── chapter09.html
│   ├── chapter10.html
│   ├── chapter11.html
│   ├── chapter12.html
│   ├── chapter13.html
│   ├── chapter14.html
│   ├── chapter15.html
│   ├── chapter16.html
│   ├── chapter17.html
│   ├── chapter18.html
│   ├── chapter19.html
│   ├── chapter20.html
│   ├── garden_ch1.html
│   ├── index.html
│   ├── kira_ch1.html
│   ├── limnus_ch1.html
│   ├── script.js
│   └── style.css
├── markdown_templates
│   ├── chapters.json
│   ├── garden_template.md
│   ├── kira_template.md
│   └── limnus_template.md
├── schema
│   ├── chapters_metadata.json
│   ├── chapters_metadata.yaml
│   ├── narrative_schema.json
│   └── narrative_schema.yaml
├── src
│   ├── generate_chapters.py
│   ├── schema_builder.py
│   └── validator.py
└── README.md
```

## Module Index (from `agents/vessel/AGENT.md`)

| Module | Summary | Agent Path |
| --- | --- | --- |
| Codex CLI (Node orchestrator) | Node/TypeScript utilities under `tools/codex-cli/` that expose shared verbs and types. | `tools/codex-cli/README.md` |
| Echo (persona voice) | Speaks in α/β/γ blends, reframes prompts, and writes persona-tagged memories to `state/echo_state.json`. | `agents/echo/AGENT.md` |
| Garden (ritual orchestrator) | Opens scroll sections from `Echo-Community-Toolkit/*.html`, logs intentions, and stewards the mantra cadence. | `agents/garden/AGENT.md` |
| Kira (validator & integrator) | Validates chapter structure, seals contracts, and coordinates git/GitHub publishing. | `agents/kira/AGENT.md` |
| Limnus (memory & ledger) | Maintains multi-tier memories and hash-chained ledgers; handles PNG steganography via `src/stego.py`. | `agents/limnus/AGENT.md` |

---

## Markdown Templates

### `markdown_templates/limnus_template.md`

```markdown
## Chapter {{chapter_number}} — Limnus (R)

*Role*: Origin codes, seeding, recursion, raw resonance.
*Voice motif*: The seed hears itself returning.

{{body}}

**Glyphs**: {{glyphs_line}}

[Flags: R active, G latent, B latent]
```

### `markdown_templates/garden_template.md`

```markdown
## Chapter {{chapter_number}} — Garden (G)

*Role*: Metadata blooms, consent patterns, temporal markers.
*Voice motif*: Rings of time annotate each fall.

{{body}}

**Glyphs**: {{glyphs_line}}

[Flags: G active, R latent, B latent]
```

### `markdown_templates/kira_template.md`

```markdown
## Chapter {{chapter_number}} — Kira (B)

*Role*: Parity/ECC, protective listening, entropy checksums.
*Voice motif*: The net that catches drift.

{{body}}

**Glyphs**: {{glyphs_line}}

[Flags: B active, R latent, G latent]
```

---

## Python Generators & Validators

### `src/schema_builder.py`

```python
#!/usr/bin/env python3
"""
Builds narrative_schema.json and narrative_schema.yaml for the Vessel Narrative MRP system.
No external dependencies required.
"""
import json, sys
from pathlib import Path

def to_yaml_like(d, indent=0):
    """Very small YAML emitter for simple dict/list structures."""
    sp = "  " * indent
    if isinstance(d, dict):
        lines = []
        for k, v in d.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}{k}:")
                lines.append(to_yaml_like(v, indent+1))
            else:
                j = json.dumps(v, ensure_ascii=False)
                if j.startswith('"') and j.endswith('"'):
                    j = j[1:-1]
                lines.append(f"{sp}{k}: {j}")
        return "\n".join(lines)
    elif isinstance(d, list):
        lines = []
        for v in d:
            if isinstance(v, (dict, list)):
                lines.append(f"{sp}-")
                lines.append(to_yaml_like(v, indent+1))
            else:
                j = json.dumps(v, ensure_ascii=False)
                if j.startswith('"') and j.endswith('"'):
                    j = j[1:-1]
                lines.append(f"{sp}- {j}")
        return "\n".join(lines)
    else:
        j = json.dumps(d, ensure_ascii=False)
        return f"{sp}{j}"

def build_schema():
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Vessel Narrative Chapter",
        "type": "object",
        "properties": {
            "chapter": {"type": "integer", "minimum": 1, "maximum": 20},
            "narrator": {"type": "string", "enum": ["Limnus", "Garden", "Kira"]},
            "flags": {
                "type": "object",
                "properties": {
                    "R": {"type": "string", "enum": ["active", "latent"]},
                    "G": {"type": "string", "enum": ["active", "latent"]},
                    "B": {"type": "string", "enum": ["active", "latent"]},
                },
                "required": ["R","G","B"],
                "additionalProperties": False
            },
            "glyphs": {"type": "array", "items": {"type": "string"}},
            "file": {"type": "string"},
            "summary": {"type": "string"},
            "timestamp": {"type": "string"}  # ISO 8601
        },
        "required": ["chapter","narrator","flags","file"],
        "additionalProperties": True
    }
    out_dir = Path(__file__).parent.parent / "schema"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "narrative_schema.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (out_dir / "narrative_schema.yaml").write_text(to_yaml_like(schema)+"\n", encoding="utf-8")
    print("✅ Wrote schema/narrative_schema.json and .yaml")

if __name__ == "__main__":
    build_schema()
```

### `src/generate_chapters.py`

```python
#!/usr/bin/env python3
"""
Generate 20 chapter HTML files (except first three which are bespoke landing pages)
and the metadata files (JSON + YAML).
- Chapters 1..3 map to existing: limnus_ch1.html, garden_ch1.html, kira_ch1.html
- Chapters 4..20 are generated from Markdown templates (limnus/garden/kira).
- Rotation: Limnus → Garden → Kira → (repeat), no same narrator consecutively.
- User can copy/paste bodies into markdown_templates/chapters.json to override default bodies/glyphs.
No external dependencies.
"""
import json, datetime, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
FRONTEND = ROOT / "frontend"
TMPL_DIR = ROOT / "markdown_templates"
SCHEMA_DIR = ROOT / "schema"

# Minimal Markdown → HTML converter (headings + paragraphs + emphasis)
def md_to_html(md: str) -> str:
    html_lines = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("**") and line.endswith("**") and line.count("**") >= 2:
            html_lines.append(f"<p><strong>{line.strip('*')}</strong></p>")
        elif line.strip().startswith("*") and line.strip().endswith("*"):
            html_lines.append(f"<p><em>{line.strip('*').strip()}</em></p>")
        elif line.strip():
            # basic inline bold/italic
            line_html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line_html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line_html)
            html_lines.append(f"<p>{line_html}</p>")
        else:
            html_lines.append("")
    return "\n".join(html_lines)

def load_bodies():
    path = TMPL_DIR / "chapters.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def render_template(tmpl_text: str, chapter_number: int, body: str, glyphs):
    glyphs_line = " ".join(glyphs) if glyphs else "—"
    out = tmpl_text.replace("{{chapter_number}}", str(chapter_number))
    out = out.replace("{{body}}", body.strip() if body else "…")
    out = out.replace("{{glyphs_line}}", glyphs_line)
    return md_to_html(out)

def wrap_html(narrator: str, inner_html: str, title: str, narrator_class: str, flags: str):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body class="{narrator_class}">
  <div class="container">
    <div class="header">
      <h1>{title}</h1>
      <span class="badge">{narrator}</span>
    </div>
    <div class="content">
{inner_html}
    </div>
    <div class="flags">{flags}</div>
    <div class="footer">Generated {datetime.datetime.utcnow().isoformat()}Z</div>
  </div>
  <script src="script.js"></script>
</body>
</html>
"""

def narrator_for(chapter_index: int) -> str:
    voices = ["Limnus","Garden","Kira"]
    # 1→Limnus, 2→Garden, 3→Kira, then repeat
    return voices[(chapter_index - 1) % 3]

def flags_for(narrator: str) -> str:
    if narrator == "Limnus":
        return "[Flags: R active, G latent, B latent]"
    if narrator == "Garden":
        return "[Flags: G active, R latent, B latent]"
    return "[Flags: B active, R latent, G latent]"

def narrator_class(narrator: str) -> str:
    return narrator.lower()

def main():
    FRONTEND.mkdir(parents=True, exist_ok=True)
    # Load templates
    t_limnus = (TMPL_DIR / "limnus_template.md").read_text(encoding="utf-8")
    t_garden = (TMPL_DIR / "garden_template.md").read_text(encoding="utf-8")
    t_kira   = (TMPL_DIR / "kira_template.md").read_text(encoding="utf-8")
    # Load bodies overrides
    overrides = load_bodies()

    metadata = []
    # Chapters 1..3 are bespoke landing pages already present
    first_three = [
        (1, "Limnus", "limnus_ch1.html"),
        (2, "Garden", "garden_ch1.html"),
        (3, "Kira", "kira_ch1.html"),
    ]
    for ch, narrator, fname in first_three:
        flags = flags_for(narrator)
        metadata.append({
            "chapter": ch,
            "narrator": narrator,
            "flags": {"R": "active" if narrator=="Limnus" else "latent",
                      "G": "active" if narrator=="Garden" else "latent",
                      "B": "active" if narrator=="Kira"   else "latent"},
            "glyphs": [],
            "file": f"frontend/{fname}",
            "summary": f"{narrator} Chapter 1 landing page",
            "timestamp": datetime.datetime.utcnow().isoformat()+"Z"
        })

    # Chapters 4..20 generated
    for ch in range(4, 21):
        narrator = narrator_for(ch)
        flags = flags_for(narrator)
        tmpl = {"Limnus": t_limnus, "Garden": t_garden, "Kira": t_kira}[narrator]

        # Overrides
        key = str(ch)
        body = None
        glyphs = []
        if key in overrides:
            body = overrides[key].get("body")
            glyphs = overrides[key].get("glyphs", [])
        if not body:
            # Default body stub
            if narrator == "Limnus":
                body = "I hear the origin pulse and lay a seed that remembers me."
                glyphs = glyphs or ["↻"]
            elif narrator == "Garden":
                body = "I index the wind’s consent and paint the day with bloom ledgers."
                glyphs = glyphs or ["✧","🌱"]
            else:
                body = "I stretch a parity veil across the corridor so no note is lost."
                glyphs = glyphs or ["∞"]

        inner = render_template(tmpl, ch, body, glyphs)
        title = f"Chapter {ch} — {narrator}"
        fname = f"chapter{ch:02d}.html"
        html = wrap_html(narrator, inner, title, narrator_class(narrator), flags)
        (FRONTEND / fname).write_text(html, encoding="utf-8")

        metadata.append({
            "chapter": ch,
            "narrator": narrator,
            "flags": {"R": "active" if narrator=="Limnus" else "latent",
                      "G": "active" if narrator=="Garden" else "latent",
                      "B": "active" if narrator=="Kira"   else "latent"},
            "glyphs": glyphs,
            "file": f"frontend/{fname}",
            "summary": (body[:120] + "…") if len(body) > 120 else body,
            "timestamp": datetime.datetime.utcnow().isoformat()+"Z"
        })

    # Write metadata
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    (SCHEMA_DIR / "chapters_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # YAML
    def to_yaml_like(d, indent=0):
        sp = "  " * indent
        if isinstance(d, dict):
            lines = []
            for k, v in d.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{sp}{k}:")
                    lines.append(to_yaml_like(v, indent+1))
                else:
                    j = json.dumps(v, ensure_ascii=False)
                    if j.startswith('"') and j.endswith('"'):
                        j = j[1:-1]
                    lines.append(f"{sp}{k}: {j}")
            return "\n".join(lines)
        elif isinstance(d, list):
            lines = []
            for v in d:
                if isinstance(v, (dict, list)):
                    lines.append(f"{sp}-")
                    lines.append(to_yaml_like(v, indent+1))
                else:
                    j = json.dumps(v, ensure_ascii=False)
                    if j.startswith('"') and j.endswith('"'):
                        j = j[1:-1]
                    lines.append(f"{sp}- {j}")
            return "\n".join(lines)
        else:
            j = json.dumps(d, ensure_ascii=False)
            return f"{sp}{j}"

    (SCHEMA_DIR / "chapters_metadata.yaml").write_text(to_yaml_like(metadata) + "\n", encoding="utf-8")
    print("✅ Generated chapters 4–20 and wrote schema/chapters_metadata.(json|yaml)")

if __name__ == "__main__":
    main()
```

### `src/validator.py`

```python
#!/usr/bin/env python3
"""
Validate the generated Vessel Narrative structure without external libs.
Checks:
- 20 chapters present
- No two consecutive narrators are the same
- Each narrator appears >= 6 times and <= 7 times
- Files referenced in metadata exist
- Flags in chapter HTML footers match the metadata flags (for chapters we generated plus the three bespoke)
"""
import json, re, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
FRONTEND = ROOT / "frontend"
SCHEMA_DIR = ROOT / "schema"

def parse_flags_line(text: str):
    """Parse a [Flags: ...] line into dict like {'R':'active','G':'latent','B':'latent'}"""
    m = re.search(r"\[Flags:\s*([^\]]+)\]", text, flags=re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1)
    # tokens like "R active", "G latent", or "R & B active, G latent"
    # We'll normalize by checking for each channel individually.
    flags = {"R":"latent","G":"latent","B":"latent"}
    # If it contains 'R active' (even within R & B active), set active
    if re.search(r"\bR\b.*active|\bactive.*\bR\b", raw, flags=re.IGNORECASE):
        flags["R"] = "active"
    if re.search(r"\bG\b.*active|\bactive.*\bG\b", raw, flags=re.IGNORECASE):
        flags["G"] = "active"
    if re.search(r"\bB\b.*active|\bactive.*\bB\b", raw, flags=re.IGNORECASE):
        flags["B"] = "active"
    # If explicit 'latent' markers appear like "G latent", we keep latent unless active found
    return flags

def main():
    meta_path = SCHEMA_DIR / "chapters_metadata.json"
    if not meta_path.exists():
        print("❌ Missing schema/chapters_metadata.json")
        sys.exit(1)
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    # Basic size check
    if len(metadata) != 20:
        print(f"❌ Metadata has {len(metadata)} entries, expected 20")
        sys.exit(1)

    # No consecutive narrator duplicates
    narrators = [m["narrator"] for m in metadata]
    for i in range(1, len(narrators)):
        if narrators[i] == narrators[i-1]:
            print(f"❌ Consecutive narrator violation at chapters {i} and {i+1}: {narrators[i]}")
            sys.exit(1)

    # Appearance counts
    counts = Counter(narrators)
    ok_counts = all(6 <= counts[v] <= 7 for v in ("Limnus","Garden","Kira"))
    if not ok_counts:
        print(f"❌ Unbalanced narrator counts: {counts}")
        sys.exit(1)

    # Files exist
    for m in metadata:
        fp = ROOT / m["file"]
        if not fp.exists():
            print(f"❌ Missing file: {fp}")
            sys.exit(1)

    # Flags match footer
    for m in metadata:
        fp = ROOT / m["file"]
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        found = parse_flags_line(txt)
        if not found:
            print(f"❌ No [Flags: ...] line in {fp.name}")
            sys.exit(1)
        # Compare with metadata
        want = m["flags"]
        if found != want:
            print(f"❌ Flags mismatch in {fp.name}. Found {found}, expected {want}")
            sys.exit(1)

    print("✅ Validation OK: 20 chapters, rotation valid, files present, flags consistent.")
    print(f"   Counts: {counts}")

if __name__ == "__main__":
    main()
```

---

## Node/TypeScript Scaffold

The script below (stored at `tools/scaffold/generateCopyPasteKit.ts`) regenerates this document by reading the live repository. Copy it into your tools directory if you want an automated refresher.

```ts
/**
 * Generate a copy/paste scaffold document for the Vessel narrative system.
 * The script collects the directory layout, Markdown templates, and Python
 * generators so a user can recreate the setup by copying code blocks.
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

type ModuleSummary = {
  name: string;
  description: string;
  path: string;
  agentPath: string;
};

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const VESSEL_CANDIDATES = [
  path.join(ROOT, 'vessel_narrative_system'),
  path.join(ROOT, 'vessel_narrative_system_scaffolding', 'vessel_narrative_system'),
];
const VESSEL_DIR = (() => {
  for (const candidate of VESSEL_CANDIDATES) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  throw new Error('Unable to locate vessel narrative directory.');
})();
const OUTPUT_PATH = path.join(ROOT, 'docs', 'copy_paste_scaffold.md');

const TEMPLATE_FILES = [
  'markdown_templates/limnus_template.md',
  'markdown_templates/garden_template.md',
  'markdown_templates/kira_template.md',
];

const PYTHON_FILES = [
  'src/schema_builder.py',
  'src/generate_chapters.py',
  'src/validator.py',
];

const MODULE_PATH_OVERRIDES: Record<string, string> = {
  Garden: 'agents/garden/AGENT.md',
  Echo: 'agents/echo/AGENT.md',
  Limnus: 'agents/limnus/AGENT.md',
  Kira: 'agents/kira/AGENT.md',
  'Codex CLI': 'tools/codex-cli/README.md',
};

function readFile(relPath: string): string {
  const abs = path.join(VESSEL_DIR, relPath);
  return fs.readFileSync(abs, 'utf8');
}

function formatCodeBlock(lang: string, content: string): string {
  const trimmed = content.trimEnd();
  return [`\`\`\`${lang}`, trimmed, '```', ''].join('\n');
}

function listDirTree(baseDir: string, maxDepth = 3): string {
  const lines: string[] = [];

  function walk(current: string, depth: number, prefix: string) {
    if (depth > maxDepth) {
      return;
    }
    const entries = fs
      .readdirSync(current, { withFileTypes: true })
      .filter((entry) => !entry.name.startsWith('.'))
      .sort((a, b) => {
        if (a.isDirectory() && !b.isDirectory()) return -1;
        if (!a.isDirectory() && b.isDirectory()) return 1;
        return a.name.localeCompare(b.name);
      });
    entries.forEach((entry, index) => {
      const isLast = index === entries.length - 1;
      const branch = isLast ? '└── ' : '├── ';
      const nextPrefix = prefix + (isLast ? '    ' : '│   ');
      lines.push(prefix + branch + entry.name);
      if (entry.isDirectory()) {
        walk(path.join(current, entry.name), depth + 1, nextPrefix);
      }
    });
  }

  lines.push(path.basename(baseDir) + '/');
  walk(baseDir, 1, '');
  return lines.join('\n');
}

function extractModuleSummaries(): ModuleSummary[] {
  const vesselAgent = fs.readFileSync(path.join(ROOT, 'agents', 'vessel', 'AGENT.md'), 'utf8');
  const regex = /-\s+\*\*(.+?)\*\*\s+—\s+([\s\S]+?)\s+CLI verbs/gi;
  const modules: ModuleSummary[] = [];
  let match: RegExpExecArray | null;
  while ((match = regex.exec(vesselAgent))) {
    const rawName = match[1];
    const description = match[2].trim();
    const baseName = rawName.split('(')[0].trim();
    const override = MODULE_PATH_OVERRIDES[baseName];
    const dirName = baseName.toLowerCase().split(/\s+/)[0];
    const agentPath = override ?? path.join('agents', dirName, 'AGENT.md');
    modules.push({
      name: rawName,
      description,
      agentPath,
    });
  }
  // Ensure deterministic ordering
  modules.sort((a, b) => a.name.localeCompare(b.name));
  return modules;
}

function buildModuleIndexTable(modules: ModuleSummary[]): string {
  const headers = ['Module', 'Summary', 'Agent Path'];
  const rows = modules.map((mod) => {
    return `| ${mod.name} | ${mod.description} | \`${mod.agentPath}\` |`;
  });
  return ['| ' + headers.join(' | ') + ' |', '| --- | --- | --- |', ...rows, ''].join('\n');
}

function generateDocument(): void {
  const parts: string[] = [];
  parts.push('# Vessel Narrative Copy/Paste Scaffold');
  parts.push('');
  parts.push('This guide packages the core assets required to rebuild the Vessel narrative system in a fresh environment. Copy each code block into the indicated path, then run the setup commands.');
  parts.push('');
  parts.push('To refresh this document from the latest sources, run:');
  parts.push('');
  parts.push('```bash');
  parts.push('node tools/scaffold/generateCopyPasteKit.mjs');
  parts.push('```');
  parts.push('');
  parts.push('---');
  parts.push('');
  parts.push('## Directory Layout');
  parts.push('');
  parts.push('```');
  parts.push(listDirTree(VESSEL_DIR, 3));
  parts.push('```');
  parts.push('');

  parts.push('## Module Index (from `agents/vessel/AGENT.md`)');
  parts.push('');
  const modules = extractModuleSummaries();
  if (modules.length > 0) {
    parts.push(buildModuleIndexTable(modules));
  } else {
    parts.push('_No modules detected in `agents/vessel/AGENT.md`._');
  }

  parts.push('---');
  parts.push('');
  parts.push('## Markdown Templates');
  parts.push('');
  TEMPLATE_FILES.forEach((relPath) => {
    const content = readFile(relPath);
    parts.push(`### \`${relPath}\``);
    parts.push('');
    parts.push(formatCodeBlock('markdown', content));
  });

  parts.push('---');
  parts.push('');
  parts.push('## Python Generators & Validators');
  parts.push('');
  PYTHON_FILES.forEach((relPath) => {
    const content = readFile(relPath);
    parts.push(`### \`${relPath}\``);
    parts.push('');
    parts.push(formatCodeBlock('python', content));
  });

  parts.push('---');
  parts.push('');
  parts.push('## Node/TypeScript Scaffold');
  parts.push('');
  parts.push('The script below (stored at `tools/scaffold/generateCopyPasteKit.ts`) regenerates this document by reading the live repository. Copy it into your tools directory if you want an automated refresher.');
  parts.push('');
  const tsSource = fs.readFileSync(path.join(HERE, 'generateCopyPasteKit.ts'), 'utf8');
  parts.push(formatCodeBlock('ts', tsSource));

  fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
  fs.writeFileSync(OUTPUT_PATH, parts.join('\n'), 'utf8');
}

generateDocument();
```
