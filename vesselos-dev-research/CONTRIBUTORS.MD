# VesselOS Dev Research Kit – Contributors

This kit assembles a working subset of the VesselOS agent runtime for research and extension. It mirrors the upstream command surface and pipeline contracts so investigators can prototype Garden → Echo → Limnus → Kira flows locally.

Acknowledgements
- VesselOS Contributors and maintainers of the upstream Kira Prime repositories.
- Researchers and collaborators experimenting with custom commands and publishing learnings back to the community.

How to Contribute
- Read `AGENTS.md` at the root of the upstream repository for scope, coding style, and testing guidance.
- Use Conventional Commits for changes (e.g., `feat(pipeline): …`, `fix(agents): …`).
- Keep generated artefacts out of version control (`dist/`, captured logs, `workspaces/**`).
- When adding or modifying commands, document the state changes and update any golden fixtures under `tests/fixtures/golden/` as applicable.

Provenance
- The `pipeline/`, `library_core/agents/`, and `vesselos.py` CLI in this kit are copied from the upstream VesselOS runtime to replace placeholders and ensure feature parity.

