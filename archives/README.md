# Archived Toolkit Snapshots

Legacy copies of the Echo Community Toolkit have been compressed to keep the workspace light and avoid pytest import collisions.

- `echo-community-toolkit.tar.gz`
- `garden-toolkit.tar.gz`
- `kira-toolkit.tar.gz`

Extract one of these tarballs into a temporary location if you need to inspect historical assets:

```bash
mkdir -p /tmp/echo-archive && tar -xzf archives/echo-community-toolkit.tar.gz -C /tmp/echo-archive
```

Do **not** re-expand them under the repository root—the `archives/` folder is excluded from pytest recursion to prevent duplicate module discovery.
