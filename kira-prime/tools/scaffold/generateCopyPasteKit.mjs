/**
 * Generated from generateCopyPasteKit.ts
 * Run with: node tools/scaffold/generateCopyPasteKit.mjs
 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

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

const MODULE_PATH_OVERRIDES = {
  Garden: 'agents/garden/AGENT.md',
  Echo: 'agents/echo/AGENT.md',
  Limnus: 'agents/limnus/AGENT.md',
  Kira: 'agents/kira/AGENT.md',
  'Codex CLI': 'tools/codex-cli/README.md',
};

function readFile(relPath) {
  const abs = path.join(VESSEL_DIR, relPath);
  return fs.readFileSync(abs, 'utf8');
}

function formatCodeBlock(lang, content) {
  const trimmed = content.trimEnd();
  return ['```' + lang, trimmed, '```', ''].join('\n');
}

function listDirTree(baseDir, maxDepth = 3) {
  const lines = [];
  function walk(current, depth, prefix) {
    if (depth > maxDepth) return;
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

function extractModuleSummaries() {
  const vesselAgent = fs.readFileSync(path.join(ROOT, 'agents', 'vessel', 'AGENT.md'), 'utf8');
  const regex = /-\s+\*\*(.+?)\*\*\s+—\s+([\s\S]+?)\s+CLI verbs/gi;
  const modules = [];
  let match;
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
  modules.sort((a, b) => a.name.localeCompare(b.name));
  return modules;
}

function buildModuleIndexTable(modules) {
  const headers = ['Module', 'Summary', 'Agent Path'];
  const rows = modules.map((mod) => `| ${mod.name} | ${mod.description} | \`${mod.agentPath}\` |`);
  return ['| ' + headers.join(' | ') + ' |', '| --- | --- | --- |', ...rows, ''].join('\n');
}

function generateDocument() {
  const parts = [];
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
