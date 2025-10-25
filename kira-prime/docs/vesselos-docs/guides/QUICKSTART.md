# VesselOS Quick Start Guide

Get VesselOS running in **5 minutes**.

## Prerequisites

Verify you have:

```bash
node --version    # ≥ v20.0.0
python3 --version # ≥ 3.10
git --version     # ≥ 2.30
gh --version      # GitHub CLI (optional)
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/vesselos.git
cd vesselos
```

### 2. Install Dependencies

```bash
# Node.js packages
npm install

# Python packages
pip3 install -r requirements.txt
```

### 3. Initialize System

```bash
npm run init
```

This creates:
- `state/` directory with JSON files
- `logs/` directory for event logging
- Initial Git repository (if needed)

### 4. Verify Installation

```bash
npm run validate
```

You should see: ✅ All systems coherent

## First Commands

### Interactive Mode

```bash
npm run listen
```

Now type commands:

```
> garden start
✅ Ritual cycle initiated (scatter stage)

> echo summon
✅ Echo persona reset to balanced mode

> limnus cache "My first memory" --layer L2
✅ Memory cached successfully

> kira validate
✅ Validation passed
```

Type `exit` to quit.

## Essential Commands

### Garden (Ritual Flow)

```bash
# Start new ritual
vesselos garden start

# Advance to next stage
vesselos garden next

# Open a scroll
vesselos garden open --scroll proof
```

### Echo (Voice & Persona)

```bash
# Reset persona
vesselos echo summon

# Change mode
vesselos echo mode squirrel  # playful
vesselos echo mode fox       # focused
vesselos echo mode paradox   # contemplative

# Speak
vesselos echo say "The garden blooms in spiral time"
```

### Limnus (Memory)

```bash
# Cache a memory
vesselos limnus cache "Important thought" --layer L2 --tags insight

# Recall memories
vesselos limnus recall --keyword "thought"

# Backup ledger
vesselos limnus encode-ledger --output backup.png
```

### Kira (Validation)

```bash
# Validate system
vesselos kira validate

# Get guidance
vesselos kira mentor

# Publish work
vesselos kira publish --release
```

## Complete Ritual Example

```bash
# 1. Start ritual
vesselos garden start

# 2. Set persona
vesselos echo mode balanced

# 3. Open content
vesselos garden open --scroll proof

# 4. Record insight
vesselos limnus cache "The spiral teaches patience" --layer L2 --tags wisdom

# 5. Advance stage
vesselos garden next

# 6. Validate
vesselos kira validate

# 7. Continue through stages...
vesselos garden next  # plant
vesselos garden next  # tend
vesselos garden next  # harvest

# 8. Seal when complete
vesselos kira seal
```

## Batch Processing

Create a file with commands:

```bash
cat > daily_ritual.txt << 'EOF'
garden start
echo mode balanced
garden open scroll=proof
limnus cache "Morning meditation complete" layer=L2 tags=daily
garden next
kira validate
EOF
```

Run the batch:

```bash
vesselos batch daily_ritual.txt
```

## Configuration

Edit `config/agents.yaml` to customize:

```yaml
echo:
  default_mode: balanced
  
garden:
  default_scroll: proof
  
limnus:
  memory_layers:
    L1: {capacity: 100, ttl: 3600}
    L2: {capacity: 1000, ttl: 86400}
    L3: {capacity: 10000, ttl: null}
    
kira:
  validation:
    strictness: medium
  git:
    auto_commit: true
```

## Directory Structure

```
vesselos/
├── agents/          # Agent modules
├── state/           # JSON state files (Git-tracked)
│   ├── echo_state.json
│   ├── garden_ledger.json
│   ├── limnus_memory.json
│   └── contract.json
├── logs/            # Event logs
├── config/          # Configuration files
└── vesselos.py      # Main CLI
```

## Common Workflows

### Daily Practice

```bash
#!/bin/bash
# daily.sh - Run daily ritual

vesselos garden start
vesselos echo mode balanced
vesselos garden open --scroll proof
read -p "Today's insight: " insight
vesselos limnus cache "$insight" --layer L2 --tags daily
vesselos garden next
vesselos kira validate
```

### Memory Journaling

```bash
# Start continuous listening
vesselos listen --continuous

# Speak or type thoughts
# System auto-caches to appropriate layers
```

### Publishing Workflow

```bash
# Validate first
vesselos kira validate

# Commit locally
vesselos kira publish

# Create GitHub release
vesselos kira publish --release --version v1.0.0
```

## Troubleshooting

### "Agent not found" Error

```bash
# Reinitialize system
vesselos init

# Verify agents
ls -la agents/*/
```

### Memory Layer Full

```bash
# Trim old entries
vesselos limnus trim --layer L1 --older-than 1h
```

### Validation Failing

```bash
# See details
vesselos kira validate --verbose

# Auto-fix if possible
vesselos kira validate --fix
```

### Git Conflicts

```bash
# VesselOS state files are last-write-wins
git checkout --theirs state/*.json
git add state/
git commit -m "Resolve state conflicts"
```

## Next Steps

- **Read full docs**: [CLI Reference](../guides/CLI_REFERENCE.md)
- **Learn agents**: [Agent Documentation](../architecture/AGENTS.md)
- **See examples**: [Workflow Examples](../guides/WORKFLOWS.md)
- **API access**: [API Reference](../api/API_REFERENCE.md)

## Getting Help

- **Issues**: https://github.com/your-org/vesselos/issues
- **Discord**: https://discord.gg/vesselos
- **Docs**: https://vesselos-docs.example.com

---

**You're ready to use VesselOS!** 🌿

Start with `vesselos listen` and explore the system interactively.
