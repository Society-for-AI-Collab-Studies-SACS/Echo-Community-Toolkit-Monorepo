# VesselOS Documentation Repository

**Version**: 1.0.0  
**Last Updated**: 2025-10-15  
**License**: MIT

## 📚 Documentation Index

This repository contains complete documentation for the VesselOS integration system, which unifies:

- **Vessel Narrative MRP** - Multi-Role Persona system
- **Living Garden Chronicles** - 20-chapter tri-voice narrative
- **SACS Dictation** - Voice/text capture and routing

## 📖 Quick Navigation

### Getting Started
- [Installation Guide](./guides/INSTALLATION.md) - Setup and prerequisites
- [Quick Start](./guides/QUICKSTART.md) - Get running in 5 minutes
- [Configuration](./guides/CONFIGURATION.md) - System configuration

### Core Documentation
- [System Architecture](./architecture/SYSTEM_ARCHITECTURE.md) - Overall design
- [Agent Reference](./architecture/AGENTS.md) - Four-agent system details
- [Data Flow](./architecture/DATA_FLOW.md) - How information moves

### Agent Documentation
- [Echo Agent](./agents/ECHO.md) - Voice & Persona Manager
- [Garden Agent](./agents/GARDEN.md) - Ritual Orchestrator
- [Limnus Agent](./agents/LIMNUS.md) - Memory & Ledger Engine
- [Kira Agent](./agents/KIRA.md) - Validator & Integrator

### User Guides
- [CLI Reference](./guides/CLI_REFERENCE.md) - Command-line interface
- [Dictation Guide](./guides/DICTATION.md) - Voice/text input
- [Workflow Examples](./guides/WORKFLOWS.md) - Common patterns
- [Troubleshooting](./guides/TROUBLESHOOTING.md) - Common issues

### Developer Documentation
- [API Reference](./api/API_REFERENCE.md) - Programmatic access
- [Development Guide](./development/CONTRIBUTING.md) - How to contribute
- [Testing Guide](./development/TESTING.md) - Test procedures
- [Extension Guide](./development/EXTENSIONS.md) - Adding features

### Technical Specs
- [MRP Specification](./specs/MRP_SPEC.md) - Multi-Role Persona system
- [Memory Layers](./specs/MEMORY_LAYERS.md) - L1/L2/L3 architecture
- [Ledger Format](./specs/LEDGER_FORMAT.md) - Hash-chain structure
- [Steganography](./specs/STEGANOGRAPHY.md) - LSB encoding details

### Narrative Content
- [Ritual Stages](./narrative/RITUAL_STAGES.md) - Garden spiral cycle
- [Scroll System](./narrative/SCROLLS.md) - Proof, Acorn, Cache, Chronicle
- [Persona Modes](./narrative/PERSONAS.md) - Squirrel, Fox, Paradox
- [Chronicles Structure](./narrative/CHRONICLES.md) - 20-chapter format

## 🚀 Getting Started Fast

```bash
# 1. Clone VesselOS
git clone https://github.com/your-org/vesselos.git
cd vesselos

# 2. Install dependencies
npm install
pip3 install -r requirements.txt

# 3. Initialize system
npm run init

# 4. Start listening
npm run listen
```

## 📁 Repository Structure

```
vesselos-docs/
├── README.md                    # This file
├── guides/                      # User guides
│   ├── INSTALLATION.md
│   ├── QUICKSTART.md
│   ├── CONFIGURATION.md
│   ├── CLI_REFERENCE.md
│   ├── DICTATION.md
│   ├── WORKFLOWS.md
│   └── TROUBLESHOOTING.md
├── architecture/                # System design
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── AGENTS.md
│   └── DATA_FLOW.md
├── agents/                      # Per-agent docs
│   ├── ECHO.md
│   ├── GARDEN.md
│   ├── LIMNUS.md
│   └── KIRA.md
├── api/                         # API documentation
│   ├── API_REFERENCE.md
│   └── examples/
├── development/                 # Developer docs
│   ├── CONTRIBUTING.md
│   ├── TESTING.md
│   └── EXTENSIONS.md
├── specs/                       # Technical specs
│   ├── MRP_SPEC.md
│   ├── MEMORY_LAYERS.md
│   ├── LEDGER_FORMAT.md
│   └── STEGANOGRAPHY.md
├── narrative/                   # Narrative docs
│   ├── RITUAL_STAGES.md
│   ├── SCROLLS.md
│   ├── PERSONAS.md
│   └── CHRONICLES.md
├── examples/                    # Code examples
│   ├── batch_commands.txt
│   ├── config_examples.yaml
│   └── python_scripts/
└── assets/                      # Images, diagrams
    ├── architecture_diagram.png
    └── data_flow.png
```

## 🎯 Common Use Cases

### Use Case 1: Daily Ritual Practice
```bash
vesselos garden start
vesselos echo mode balanced
vesselos garden open --scroll proof
vesselos limnus cache "Today's insight" --layer L2
vesselos kira validate
```

### Use Case 2: Memory Journaling
```bash
vesselos listen --continuous
# Then speak/type your thoughts
# System automatically caches to appropriate memory layers
```

### Use Case 3: Narrative Generation
```bash
vesselos generate
vesselos kira validate
vesselos kira publish --release
```

## 📊 Key Concepts

### Four-Agent Architecture
- **Echo**: Manages narrative voice and persona (α, β, γ blend)
- **Garden**: Orchestrates ritual flow and scroll content
- **Limnus**: Maintains memory layers and secure ledger
- **Kira**: Validates integrity and mentors system

### Data Flow
```
Input → Parse → Garden → Echo → Limnus → Kira → Output
  ↓       ↓       ↓       ↓       ↓       ↓       ↓
Voice   Intent   Log   Style   Store  Validate Archive
```

### Memory Hierarchy
- **L1**: Short-term (100 entries, 1 hour TTL)
- **L2**: Medium-term (1000 entries, 1 day TTL)
- **L3**: Long-term (10,000 entries, permanent)

## 🔗 External Resources

- **Main Repository**: https://github.com/your-org/vesselos
- **Issue Tracker**: https://github.com/your-org/vesselos/issues
- **Discord Community**: https://discord.gg/vesselos
- **Live Demo**: https://vesselos-demo.example.com

## 📝 Version History

- **v1.0.0** (2025-10-15) - Initial documentation release
  - Complete system documentation
  - All four agents documented
  - API reference included
  - Example workflows provided

## 🤝 Contributing

Documentation contributions are welcome! See [CONTRIBUTING.md](./development/CONTRIBUTING.md) for guidelines.

To suggest documentation improvements:
1. Fork this repository
2. Make your changes
3. Submit a pull request

## 📄 License

This documentation is licensed under MIT License. See LICENSE file for details.

---

**Generated by VesselOS Documentation System**  
For questions or support, open an issue or join our Discord community.
