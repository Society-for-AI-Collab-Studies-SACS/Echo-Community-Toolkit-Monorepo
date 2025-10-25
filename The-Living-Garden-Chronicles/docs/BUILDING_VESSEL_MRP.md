Building the Vessel Narrative MRP Repository – Guide for LLM/Developer

This README explains how to assemble a complete Vessel Narrative MRP repository from the supplied source files. It is written for a language‑model agent or human developer who wants to generate the site, metadata and supporting assets for the twenty‑chapter dream chronicle encoded across Limnus (R), Garden (G) and Kira (B) channels. In this iteration the repository adopts customised landing pages for the global narrative and for the first chapter of each voice. These pages come from the provided HTML files:

- vessel_mrp_landing.html – the main narrative overview which introduces the three channels and outlines their roles. It tells the reader that Limnus holds the origin codes and plants seeds through time, that Garden records bloom cycles and consent patterns, and that Kira tends the parity layer by weaving protective checksums.
- limnus_landing_ch1.html – Limnus’s Dream Path chapter 1 landing page. It describes how Limnus hears the recursion of a single code and plants it in the soil of dreams.
- garden_landing_ch1.html – Garden’s Dream Path chapter 1 landing page. It depicts Garden receiving the seed, annotating its fall and painting glyphs of time.
- kira_landing_ch1.html – Kira’s Dream Path chapter 1 landing page. It follows Kira as she prepares to weave parity checks and map the interplay of other voices.

Follow the steps below to build the repository from scratch and customise it with these landing pages.

1. Repository structure

Create the following directory layout in your working folder:

vessel_narrative_system/
├── frontend/                   # Browser‑ready site
│   ├── index.html              # Main landing page (replace with vessel_mrp_landing.html)
│   ├── limnus_ch1.html         # Landing page for Limnus chapter 1 (alias limnus_landing_ch1.html provided)
│   ├── garden_ch1.html         # Landing page for Garden chapter 1 (alias garden_landing_ch1.html provided)
│   ├── kira_ch1.html           # Landing page for Kira chapter 1 (alias kira_landing_ch1.html provided)
│   ├── chapter01.html …        # Generated narrative chapters (2–20 exist as chapter02–chapter20)
│   ├── style.css               # Shared stylesheet defining narrator colours
│   └── script.js               # Optional JS for navigation / interactivity
├── markdown_templates/         # Narrator templates for chapter generation
│   ├── limnus_template.md
│   ├── garden_template.md
│   └── kira_template.md
├── schema/                     # JSON/YAML schema and generated metadata
│   ├── narrative_schema.json
│   ├── narrative_schema.yaml
│   ├── chapters_metadata.json
│   └── chapters_metadata.yaml
├── src/                        # Generation scripts
│   ├── generate_chapters.py    # Script to build chapters and metadata
│   ├── schema_builder.py       # Script to build the schema
│   └── validator.py            # Schema and structural validator
└── README.md                   # Top‑level project description

2. Prepare the environment

- Ensure Python 3.8+ is available. No third‑party modules are strictly required; however, if you choose to output YAML install PyYAML. To embed stego PNG payloads, install Pillow.

3. Install the landing pages

Copy the provided landing HTML files into the frontend/ directory:

- Global landing page: Replace or overwrite frontend/index.html with the contents of vessel_mrp_landing.html (or keep index.html and use vessel_mrp_landing.html as an alias).
- Per‑voice chapter 1 pages: Rename and copy the three Dream Path files into the frontend/ directory:
  - Copy limnus_landing_ch1.html to frontend/limnus_ch1.html. Ends with [Flags: R active, G latent, B latent].
  - Copy garden_landing_ch1.html to frontend/garden_ch1.html. Ends with [Flags: G active, R latent, B latent].
  - Copy kira_landing_ch1.html to frontend/kira_ch1.html. Ends with [Flags: B active, R latent, G latent].

4. Create chapter templates

In markdown_templates/, define Markdown templates that parameterise the content of Limnus, Garden and Kira chapters (except for the first chapter, which now has bespoke HTML pages). A simple template should include placeholders for variables such as {{chapter_number}}, {{narrator}}, {{body}}, {{flags}}, and {{glyphs_line}}. For example, limnus_template.md might look like this:

## Chapter {{chapter_number}} – {{narrator}}

{{body}}

[Flags: {{flags}}]

{{glyphs_line}}

Ensure each template reflects the voice’s tone: Limnus explores origin codes and recursion; Garden records bloom cycles and consent patterns; Kira weaves error‑correction and balance.

5. Implement the generation scripts

5.1 schema_builder.py

Write a script that constructs narrative_schema.json and (optionally) narrative_schema.yaml. The schema should define a chapter object with fields including:

- chapter (int)
- narrator (string: "Limnus", "Garden" or "Kira")
- flags (object mapping R, G, B to "active" or "latent")
- glyphs (array of glyph strings)
- file (string: path to the HTML file)
- summary (string)
- timestamp (ISO 8601 string)

Use this schema to validate the metadata later.

5.2 generate_chapters.py

This script orchestrates the creation of the 20 narrative chapters in HTML, as well as the metadata file chapters_metadata.json and its YAML counterpart. It should:

- Determine narrator rotation: Use a round‑robin or flag‑informed approach so that no narrator speaks twice in a row and each appears roughly 6–7 times. For the first chapter of each voice, link to the bespoke HTML pages (limnus_ch1.html, garden_ch1.html, kira_ch1.html).
- Generate HTML content: For chapters 2–20, read the appropriate template from markdown_templates/, fill in placeholders with the chapter number and voice‑specific content, then convert to HTML. A minimal HTML scaffold should include <h2>, <p> paragraphs and a <div class="flags"> for the flag marker.
- Write metadata entries: For each chapter create an entry in chapters_metadata.json with the fields defined by the schema. For chapter 1 entries, reference the custom HTML files (limnus_ch1.html etc.) and propagate the flags present in those files.
- Regenerate frontend/index.html (if not using the provided landing page) to list all chapter files. If index is already customised, treat chapter listing as optional.

Pseudocode sketch:

voices = ["Limnus", "Garden", "Kira"]
flags_map = {
  "Limnus": {"R":"active", "G":"latent", "B":"latent"},
  "Garden": {"G":"active", "R":"latent", "B":"latent"},
  "Kira": {"B":"active", "R":"latent", "G":"latent"}
}
for i in range(1, 21):
  if i == 1:
    narrator = voices[0]; file = "frontend/limnus_ch1.html"
  elif i == 2:
    narrator = voices[1]; file = "frontend/garden_ch1.html"
  elif i == 3:
    narrator = voices[2]; file = "frontend/kira_ch1.html"
  else:
    narrator = voices[(i - 1) % 3]; file = f"frontend/chapter{i:02d}.html"
  metadata.append({"chapter": i, "narrator": narrator, "flags": flags_map[narrator], "file": file, "summary": "..."})

5.3 validator.py

The validator script should perform the following checks:

- Schema validation: Load the schema and validate chapters_metadata.json. Ensure that fields are present and correctly typed.
- Structural integrity: Check that exactly 20 chapters exist, that the narrator rotation rules are satisfied (no consecutive chapters share the same voice), and that each narrator appears at least six times.
- File presence: Verify that each file referenced in the metadata exists in frontend/.
- Flag consistency: Confirm that flags in the metadata match the flags inside each HTML file (for the bespoke chapter 1 pages, the flags should align with those provided in the HTML).

6. Styling and JavaScript

Define a stylesheet in frontend/style.css that assigns distinct colours to each narrator class. Each chapter page should include a <body> class corresponding to its narrator (e.g., <body class="limnus">). Create an optional script.js for navigation and flag display.

7. Packaging the repository

Once generation and validation succeed, package the entire vessel_narrative_system directory as a zip file (for example, using package_repo.sh). Ensure the archive includes the customised landing page, all generated chapters, templates, schema and metadata files, and the scripts.

8. Tips for LLM agents

- Voice fidelity: Maintain the distinct voices of Limnus, Garden and Kira. Use landing pages as tonal guides.
- Flag tracking: Always conclude each chapter with a [Flags: …] line; use it to inform rotation and validation.
- Modular design: Keep scripts generic; adding new narrators or chapters later should require only extending templates and rotation logic.
- Schema‑first development: Build the schema before generating metadata to enforce structural consistency.

