import os
from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()

# Prefer explicit env var from CI, else fall back to a descriptive value
version = os.getenv("RHZZ_VERSION")
if not version:
    # Fallbacks: try common CI vars, then 'dev'
    version = os.getenv("GITHUB_REF_NAME") or os.getenv("GITHUB_SHA", "dev")[:7]
    if not version:
        version = "dev"

# Write an auto-generated header with the version string
hdr_path = os.path.join(env.subst("$PROJECTSRC_DIR"), "version_auto.h")
try:
    with open(hdr_path, "w", encoding="utf-8") as fp:
        fp.write("#pragma once\n")
        fp.write(f"#define RHZZ_VERSION_STR \"{version}\"\n")
    print(f"[version.py] Wrote {hdr_path} with RHZZ_VERSION_STR=\"{version}\"")
except Exception as e:
    print(f"[version.py] Failed to write version header: {e}")
