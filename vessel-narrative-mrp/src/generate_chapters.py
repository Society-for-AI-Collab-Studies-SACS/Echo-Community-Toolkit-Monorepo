#!/usr/bin/env python3
"""
Generates chapter HTML (2–20) and metadata JSON/YAML.
Chapter 1 pages are bespoke and already present in `frontend/`.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Dict, List

try:
    from stego import encode_chapter_payload, is_available as stego_is_available
except Exception:  # pragma: no cover - fallback when stego module missing
    encode_chapter_payload = None  # type: ignore[assignment]

    def stego_is_available() -> bool:  # type: ignore[return-value]
        return False

from soulcode import build_bundle, write_bundle


VOICES = ["Limnus", "Garden", "Kira"]
FLAGS_MAP: Dict[str, Dict[str, str]] = {
    "Limnus": {"R": "active", "G": "latent", "B": "latent"},
    "Garden": {"G": "active", "R": "latent", "B": "latent"},
    "Kira": {"B": "active", "R": "latent", "G": "latent"},
}
CANONICAL_SCROLLS: Dict[str, List[str]] = {
    "Limnus": [
        "Echo-Community-Toolkit/echo-hilbert-chronicle.html",
        "Echo-Community-Toolkit/echo-garden-quantum-triquetra.html",
    ],
    "Garden": [
        "Echo-Community-Toolkit/eternal-acorn-scroll.html",
        "Echo-Community-Toolkit/proof-of-love-acorn.html",
    ],
    "Kira": [
        "Echo-Community-Toolkit/quantum-cache-algorithm.html",
        "Echo-Community-Toolkit/integrated-lambda-echo-garden.html",
    ],
}
PARAGRAPH_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
MAX_EXCERPT_LENGTH = 420
SOULCODE_SCRIPT_RE = re.compile(r'<script id="soulcode-state"[^>]*>.*?</script>', re.DOTALL)


@dataclass(frozen=True)
class ScrollExcerpt:
    scroll: Path
    paragraph_index: int
    text: str
    label: str


def ts_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_template(root: Path, narrator: str) -> str:
    tpath = root / "markdown_templates" / f"{narrator.lower()}_template.md"
    return tpath.read_text(encoding="utf-8")


def base_voice_statement(narrator: str, chapter: int) -> str:
    if narrator == "Limnus":
        return (
            "Limnus listens for the origin code and its gentle recursion. "
            "Patterns settle into soil and remember themselves in cycles."
        )
    if narrator == "Garden":
        return (
            "Garden annotates the fall of each seed, mapping bloom cycles and consent. "
            "Glyphs line the margins with patient timing."
        )
    return (
        "Kira weaves parity across the weave, balancing the ledger of signal. "
        "Errors soften under a net of blue care."
    )


def glyphs_for(narrator: str, chapter: int) -> List[str]:
    base = {
        "Limnus": "⟡R",
        "Garden": "⟢G",
        "Kira": "⟣B",
    }[narrator]
    # Deterministic sequence of 3 glyphs per chapter
    return [f"{base}{chapter:02d}-{i}" for i in range(1, 4)]


def canonical_label(path: Path) -> str:
    stem = path.stem.replace("_", " ").replace("-", " ")
    return stem.title()


def strip_tags(fragment: str) -> str:
    no_tags = TAG_RE.sub("", fragment)
    collapsed = re.sub(r"\s+", " ", unescape(no_tags))
    return collapsed.strip()


def clean_excerpt_text(fragment: str) -> str:
    text = strip_tags(fragment)
    if len(text) > MAX_EXCERPT_LENGTH:
        trimmed = text[:MAX_EXCERPT_LENGTH].rsplit(" ", 1)[0]
        text = trimmed.rstrip(",;:") + "..."
    return text


def load_scroll_excerpts(root: Path) -> Dict[str, List[ScrollExcerpt]]:
    excerpts: Dict[str, List[ScrollExcerpt]] = {voice: [] for voice in VOICES}
    for voice, rel_paths in CANONICAL_SCROLLS.items():
        for rel in rel_paths:
            path = root / rel
            if not path.exists():
                continue
            raw = path.read_text(encoding="utf-8", errors="ignore")
            for idx, fragment in enumerate(PARAGRAPH_RE.findall(raw)):
                cleaned = clean_excerpt_text(fragment)
                if len(cleaned) < 60:
                    continue
                excerpts[voice].append(
                    ScrollExcerpt(
                        scroll=path,
                        paragraph_index=idx,
                        text=cleaned,
                        label=canonical_label(path),
                    )
                )
    for voice, items in excerpts.items():
        if not items:
            fallback = ScrollExcerpt(
                scroll=root / f"markdown_templates/{voice.lower()}_template.md",
                paragraph_index=0,
                text=base_voice_statement(voice, 0),
                label=f"{voice} Template",
            )
            items.append(fallback)
    return excerpts


def relativize(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:  # pragma: no cover - defensive
        return str(path)


def select_excerpt(
    narrator: str,
    chapters_seen: Dict[str, int],
    excerpts_by_voice: Dict[str, List[ScrollExcerpt]],
) -> ScrollExcerpt:
    pool = excerpts_by_voice.get(narrator, [])
    if not pool:
        return ScrollExcerpt(
            scroll=Path(f"{narrator.lower()}_fallback"),
            paragraph_index=0,
            text=base_voice_statement(narrator, 0),
            label=f"{narrator} Fallback",
        )
    idx = chapters_seen[narrator] % len(pool)
    chapters_seen[narrator] += 1
    return pool[idx]


def compose_body_markdown(
    narrator: str,
    chapter: int,
    excerpt: ScrollExcerpt,
    glyphs: List[str],
) -> str:
    intro = base_voice_statement(narrator, chapter)
    glyph_line = (
        f"Glyph resonance aligns {glyphs[0]}, {glyphs[1]}, and {glyphs[2]} "
        f"with the scroll memory."
    )
    blockquote = f"> {excerpt.text}"
    provenance_line = (
        f"Source Scroll: {excerpt.label} · paragraph {excerpt.paragraph_index + 1}"
    )
    return "\n\n".join([intro, glyph_line, blockquote, provenance_line])


def embed_soulcode_bundle(index_path: Path, bundle: dict) -> None:
    payload = json.dumps(bundle, ensure_ascii=False, separators=(",", ":"))
    script_tag = f'  <script id="soulcode-state" type="application/json">{payload}</script>'
    html = index_path.read_text(encoding="utf-8")
    if SOULCODE_SCRIPT_RE.search(html):
        html = SOULCODE_SCRIPT_RE.sub(script_tag + "\n", html)
    else:
        insertion = "\n" + script_tag + "\n"
        marker = "</body>"
        if marker in html:
            html = html.replace(marker, insertion + marker, 1)
        else:  # pragma: no cover - defensive fallback
            html = html + insertion
    index_path.write_text(html, encoding="utf-8")


def fill_placeholders(
    tpl: str,
    narrator: str,
    chapter: int,
    flags: Dict[str, str],
    glyphs: List[str],
    body_md: str,
) -> str:
    flags_line = f"R {flags['R']}, G {flags['G']}, B {flags['B']}"
    glyphs_line = "Glyphs: " + " · ".join(glyphs)
    out = (
        tpl.replace("{{chapter_number}}", f"{chapter}")
        .replace("{{narrator}}", narrator)
        .replace("{{body}}", body_md)
        .replace("{{flags}}", flags_line)
        .replace("{{glyphs_line}}", glyphs_line)
    )
    return out


def render_markdown_min(md: str) -> str:
    lines = md.strip().splitlines()
    html_lines: List[str] = []
    paragraph: List[str] = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            html_lines.append(f"<p>{' '.join(paragraph).strip()}</p>")
            paragraph = []

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_paragraph()
            continue
        if line.startswith("## "):
            flush_paragraph()
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("[Flags:") and line.endswith("]"):
            flush_paragraph()
            html_lines.append(f"<div class=\"flags\">{line}</div>")
        elif line.lower().startswith("glyphs:"):
            flush_paragraph()
            html_lines.append(f"<div class=\"glyphs\">{line}</div>")
        elif line.startswith(">"):
            flush_paragraph()
            html_lines.append(f"<blockquote>{line.lstrip('> ').strip()}</blockquote>")
        else:
            paragraph.append(line)
    flush_paragraph()
    return "\n".join(html_lines)


def wrap_html(narrator: str, chapter: int, body_html: str) -> str:
    lower = narrator.lower()
    fname = f"chapter{chapter:02d}.html"
    prev_link = f"chapter{chapter-1:02d}.html" if chapter > 2 else "kira_ch1.html"
    next_link = f"chapter{chapter+1:02d}.html" if chapter < 20 else "index.html"
    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Chapter {chapter:02d} – {narrator}</title>
    <link rel=\"stylesheet\" href=\"style.css\" />
  </head>
  <body class=\"{lower}\">
    <nav class=\"top-nav\"><a href=\"index.html\">⟵ Back to Overview</a></nav>
    <article class=\"chapter\">
{body_html}
    </article>
    <footer class=\"chapter-footer\">
      <a class=\"prev\" href=\"{prev_link}\">⟵ Previous</a>
      <span>·</span>
      <a class=\"next\" href=\"{next_link}\">Next ⟶</a>
    </footer>
    <script src=\"script.js\"></script>
  </body>
</html>"""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def try_write_yaml(path: Path, data) -> bool:
    try:
        import yaml  # type: ignore
    except Exception:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
    return True


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frontend = root / "frontend"
    assets_dir = frontend / "assets"
    excerpts_by_voice = load_scroll_excerpts(root)
    chapters_seen = {voice: 0 for voice in VOICES}

    stego_notice_emitted = False
    stego_error_emitted = False

    metadata: List[dict] = []

    for i in range(1, 21):
        if i == 1:
            narrator = VOICES[0]  # Limnus
            rel_file = "frontend/limnus_ch1.html"
        elif i == 2:
            narrator = VOICES[1]  # Garden
            rel_file = "frontend/garden_ch1.html"
        elif i == 3:
            narrator = VOICES[2]  # Kira
            rel_file = "frontend/kira_ch1.html"
        else:
            narrator = VOICES[(i - 1) % 3]
            rel_file = f"frontend/chapter{i:02d}.html"
        flags = FLAGS_MAP[narrator]
        glyphs = glyphs_for(narrator, i)
        excerpt = select_excerpt(narrator, chapters_seen, excerpts_by_voice)

        if i > 3:
            tpl = read_template(root, narrator)
            body_md = compose_body_markdown(narrator, i, excerpt, glyphs)
            filled = fill_placeholders(tpl, narrator, i, flags, glyphs, body_md)
            body_html = render_markdown_min(filled)
            html = wrap_html(narrator, i, body_html)
            write_text(frontend / f"chapter{i:02d}.html", html)

        meta_entry = {
            "chapter": i,
            "narrator": narrator,
            "flags": flags,
            "glyphs": glyphs,
            "file": rel_file,
            "summary": f"{narrator} – Chapter {i:02d} · {excerpt.label}",
            "timestamp": ts_now(),
            "provenance": {
                "scroll": relativize(excerpt.scroll, root),
                "label": excerpt.label,
                "paragraph_index": excerpt.paragraph_index,
                "excerpt": excerpt.text,
                "glyph_refs": list(glyphs),
            },
        }

        stego_rel: str | None = None
        if stego_is_available() and encode_chapter_payload is not None:
            try:
                assets_dir.mkdir(parents=True, exist_ok=True)
                out_name = f"chapter{i:02d}.png"
                out_path = assets_dir / out_name
                encode_chapter_payload(meta_entry, out_path)
                stego_rel = f"frontend/assets/{out_name}"
            except Exception as exc:  # pragma: no cover - runtime notice
                if not stego_error_emitted:
                    print(f"(Stego) Failed to embed payload: {exc}")
                    stego_error_emitted = True
        else:
            if not stego_notice_emitted:
                print("(Stego) Pillow not available; skipping PNG embedding.")
                stego_notice_emitted = True

        if stego_rel:
            meta_entry["stego_png"] = stego_rel

        metadata.append(meta_entry)

    meta_doc = {"chapters": metadata}
    schema_dir = root / "schema"
    schema_dir.mkdir(parents=True, exist_ok=True)
    (schema_dir / "chapters_metadata.json").write_text(
        json.dumps(meta_doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    wrote_yaml = try_write_yaml(schema_dir / "chapters_metadata.yaml", meta_doc)
    bundle_generated_at = ts_now()
    soulcode_bundle = build_bundle(metadata, bundle_generated_at)
    write_bundle(schema_dir / "soulcode_bundle.json", soulcode_bundle)
    embed_soulcode_bundle(frontend / "index.html", soulcode_bundle)
    print("Wrote:", schema_dir / "chapters_metadata.json")
    if wrote_yaml:
        print("Wrote:", schema_dir / "chapters_metadata.yaml")
    else:
        print("(YAML not written; install PyYAML to enable)")
    print("Wrote:", schema_dir / "soulcode_bundle.json")
    print("Embedded soulcode bundle into frontend/index.html")


if __name__ == "__main__":
    main()
