#!/usr/bin/env python3
"""
Validate the generated Vessel Narrative structure without external libs.
Checks:
- 20 chapters present
- No two consecutive narrators are the same
- Each narrator appears >= 6 times and <= 7 times
- Files referenced in metadata exist
- Flags in chapter HTML footers match the metadata flags (for chapters we generated plus the three bespoke)
"""
import json, re, sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent
FRONTEND = ROOT / "frontend"
SCHEMA_DIR = ROOT / "schema"

def parse_flags_line(text: str):
    """Parse a [Flags: ...] line into dict like {'R':'active','G':'latent','B':'latent'}"""
    m = re.search(r"\[Flags:\s*([^\]]+)\]", text, flags=re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1)
    # tokens like "R active", "G latent", or "R & B active, G latent"
    # We'll normalize by checking for each channel individually.
    flags = {"R":"latent","G":"latent","B":"latent"}
    # If it contains 'R active' (even within R & B active), set active
    if re.search(r"\bR\b.*active|\bactive.*\bR\b", raw, flags=re.IGNORECASE):
        flags["R"] = "active"
    if re.search(r"\bG\b.*active|\bactive.*\bG\b", raw, flags=re.IGNORECASE):
        flags["G"] = "active"
    if re.search(r"\bB\b.*active|\bactive.*\bB\b", raw, flags=re.IGNORECASE):
        flags["B"] = "active"
    # If explicit 'latent' markers appear like "G latent", we keep latent unless active found
    return flags

def main():
    meta_path = SCHEMA_DIR / "chapters_metadata.json"
    if not meta_path.exists():
        print("❌ Missing schema/chapters_metadata.json")
        sys.exit(1)
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    # Basic size check
    if len(metadata) != 20:
        print(f"❌ Metadata has {len(metadata)} entries, expected 20")
        sys.exit(1)

    # No consecutive narrator duplicates
    narrators = [m["narrator"] for m in metadata]
    for i in range(1, len(narrators)):
        if narrators[i] == narrators[i-1]:
            print(f"❌ Consecutive narrator violation at chapters {i} and {i+1}: {narrators[i]}")
            sys.exit(1)

    # Appearance counts
    counts = Counter(narrators)
    ok_counts = all(6 <= counts[v] <= 7 for v in ("Limnus","Garden","Kira"))
    if not ok_counts:
        print(f"❌ Unbalanced narrator counts: {counts}")
        sys.exit(1)

    # Files exist
    for m in metadata:
        fp = ROOT / m["file"]
        if not fp.exists():
            print(f"❌ Missing file: {fp}")
            sys.exit(1)

    # Flags match footer
    for m in metadata:
        fp = ROOT / m["file"]
        txt = fp.read_text(encoding="utf-8", errors="ignore")
        found = parse_flags_line(txt)
        if not found:
            print(f"❌ No [Flags: ...] line in {fp.name}")
            sys.exit(1)
        # Compare with metadata
        want = m["flags"]
        if found != want:
            print(f"❌ Flags mismatch in {fp.name}. Found {found}, expected {want}")
            sys.exit(1)

    print("✅ Validation OK: 20 chapters, rotation valid, files present, flags consistent.")
    print(f"   Counts: {counts}")

if __name__ == "__main__":
    main()
