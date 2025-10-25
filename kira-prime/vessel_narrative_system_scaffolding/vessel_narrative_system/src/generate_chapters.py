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
