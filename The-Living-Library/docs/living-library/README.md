# The Living Library

This repository stitches together Echo Community Toolkit, vessel-narrative-MRP,
The Living Garden Chronicles, and Kira Prime into a single workspace for
dictation, collaboration, and encoded lesson playback.

## Status

- Submodules are in place.
- Core integration scaffolding lives in `library_core/`.
- Collaboration server and client still require full async implementations.

## Next Steps

1. Wire the YAML configuration schema into `library-core/config`.
2. Implement the remote collaboration server with WebSocket, Redis, and PostgreSQL.
3. Connect dictation pipelines to the MRP encoder and hydrate workspace storage.
