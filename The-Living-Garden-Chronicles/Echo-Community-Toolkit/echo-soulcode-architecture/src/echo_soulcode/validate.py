from __future__ import annotations
"""
echo_soulcode.validate — Validation utilities & CLI

- Autodetect bundle vs single JSON
- Validate against Draft 2020-12 schemas (via echo_soulcode.schema)
- Human-friendly error reporting with JSON Pointers
- Optional "states" mode to sanity-check experimental live_read bundles
"""

from typing import Any, Dict, Iterable, List, Literal, Tuple
from dataclasses import dataclass
import json

from jsonschema import Draft202012Validator
from . import schema as _schema  # single/bundle schemas
import copy

Kind = Literal["auto", "soulcode", "bundle", "states"]

# ---------------- Types ----------------

@dataclass
class ValidationIssue:
    path: str
    message: str

@dataclass
class ValidationReport:
    ok: bool
    kind: str
    issues: List[ValidationIssue]

# ---------------- Heuristics ----------------

_SINGLE_KEYS = {"id","glitch_persona","resonant_signature","symbolic_fingerprint","quantum_metrics","block_hash","reference_hash"}
_BUNDLE_KEYS = {"ECHO_SQUIRREL","ECHO_FOX","ECHO_PARADOX"}

def _is_bundle_shape(obj: Any) -> bool:
    return isinstance(obj, dict) and _BUNDLE_KEYS.issubset(set(obj.keys()))

def _is_single_shape(obj: Any) -> bool:
    return isinstance(obj, dict) and _SINGLE_KEYS.issubset(set(obj.keys()))

def _is_states_shape(obj: Any) -> bool:
    return isinstance(obj, dict) and "states" in obj and isinstance(obj["states"], dict)

# ---------------- Schema Validation ----------------

def _validator(kind: Literal["soulcode","bundle"]) -> Draft202012Validator:
    sc = _schema.load_schema(kind)
    Draft202012Validator.check_schema(sc)
    return Draft202012Validator(sc)

def _pointer(path: Iterable[Any]) -> str:
    parts = []
    for p in path:
        if isinstance(p, int):
            parts.append(str(p))
        else:
            parts.append(str(p).replace("~","~0").replace("/","~1"))
    return "/" + "/".join(parts)

def validate_single_obj(obj: Dict[str, Any]) -> List[ValidationIssue]:
    v = _validator("soulcode")
    errors = sorted(v.iter_errors(obj), key=lambda e: e.path)
    return [ValidationIssue(path=_pointer(e.path), message=e.message) for e in errors]

def validate_bundle_obj(obj: Dict[str, Any]) -> List[ValidationIssue]:
    v = _validator("bundle")
    errors = sorted(v.iter_errors(obj), key=lambda e: e.path)
    return [ValidationIssue(path=_pointer(e.path), message=e.message) for e in errors]

# ---------------- Experimental states mode ----------------

def sanity_check_states(obj: Dict[str, Any]) -> List[ValidationIssue]:
    """Shallow checks for the experimental live_read 'states' bundle.
    Not schema-enforced; ensures presence of minimal keys.
    """
    issues: List[ValidationIssue] = []
    if not _is_states_shape(obj):
        return [ValidationIssue(path="", message="Object has no 'states' dict")]

    for k, state in obj["states"].items():
        if not isinstance(state, dict):
            issues.append(ValidationIssue(path=f"/states/{k}", message="state is not an object"))
            continue
        for req in ("id","glitch_persona","symbolic_fingerprint","quantum_metrics","block_hash","reference_hash"):
            if req not in state:
                issues.append(ValidationIssue(path=f"/states/{k}", message=f"missing key '{req}'"))
    return issues

# ---------------- Public API ----------------

def validate_obj(obj: Dict[str, Any], kind: Kind = "auto") -> ValidationReport:
    if kind == "auto":
        if _is_bundle_shape(obj):
            issues = validate_bundle_obj(obj)
            return ValidationReport(ok=(len(issues)==0), kind="bundle", issues=issues)
        if _is_single_shape(obj):
            issues = validate_single_obj(obj)
            return ValidationReport(ok=(len(issues)==0), kind="soulcode", issues=issues)
        if _is_states_shape(obj):
            issues = sanity_check_states(obj)
            return ValidationReport(ok=(len(issues)==0), kind="states", issues=issues)
        # fallback: try single, then bundle
        issues_single = validate_single_obj(obj)
        if len(issues_single)==0:
            return ValidationReport(ok=True, kind="soulcode", issues=[])
        issues_bundle = validate_bundle_obj(obj)
        if len(issues_bundle)==0:
            return ValidationReport(ok=True, kind="bundle", issues=[])
        # ambiguous
        return ValidationReport(ok=False, kind="unknown", issues=issues_single + issues_bundle)
    elif kind == "soulcode":
        issues = validate_single_obj(obj)
        return ValidationReport(ok=(len(issues)==0), kind="soulcode", issues=issues)
    elif kind == "bundle":
        issues = validate_bundle_obj(obj)
        return ValidationReport(ok=(len(issues)==0), kind="bundle", issues=issues)
    else:  # states
        issues = sanity_check_states(obj)
        return ValidationReport(ok=(len(issues)==0), kind="states", issues=issues)

def load_schema_for(kind: Literal["soulcode","bundle"]) -> Dict[str, Any]:
    return _schema.load_schema(kind)

# Back-compat helper: default to bundle when no kind is specified.
# Some historical tests call `load_schema()` expecting a container that accepts
# top-level mappings (e.g., {"ECHO_SQUIRREL": {...}}).
def load_schema(kind: Literal["soulcode","bundle", "container", "auto"] = "auto") -> Dict[str, Any]:
    """Schema helper with a tolerant default.
    - "soulcode": exact single-object schema
    - "bundle": exact 3-entry bundle schema
    - "container": object whose additionalProperties are single soulcodes
    - "auto" (default): anyOf(soulcode, bundle, container)
    """
    if kind == "soulcode" or kind == "bundle":
        return _schema.load_schema(kind)  # precise
    if kind == "container":
        return {
            "$schema": _schema.DRAFT,
            "title": "Echo Soulcode Container",
            "type": "object",
            "additionalProperties": {"$ref": "#/$defs/soulcode"}
        }
    # auto: accept single, bundle, or container
    sc_ref = _SC_REF()
    return {
        "$schema": _schema.DRAFT,
        "title": "Echo Soulcode (auto) — single | bundle | container",
        "$defs": { **_schema.DEFS, "soulcode": sc_ref },
        "anyOf": [
            {"$ref": "#/$defs/soulcode"},
            {
              "type": "object",
              "additionalProperties": False,
              "properties": {
                "ECHO_SQUIRREL": {"$ref": "#/$defs/soulcode"},
                "ECHO_FOX": {"$ref": "#/$defs/soulcode"},
                "ECHO_PARADOX": {"$ref": "#/$defs/soulcode"}
              },
              "required": ["ECHO_SQUIRREL","ECHO_FOX","ECHO_PARADOX"]
            },
            {"type":"object", "additionalProperties": {"$ref": "#/$defs/soulcode"}}
        ]
    }

# local accessor for single schema (avoids $id duplication if inlined multiple times)
def _SC_REF() -> Dict[str, Any]:
    sc = copy.deepcopy(_schema.SINGLE_SOULCODE)
    sc.pop("$id", None)
    return sc

# ---------------- CLI ----------------

def _print_report(rep: ValidationReport, pretty: bool = True) -> None:
    if rep.ok:
        print(f"OK: {rep.kind} validation passed")
        return
    print(f"FAILED: {rep.kind} has {len(rep.issues)} issue(s)")
    for i, it in enumerate(rep.issues, 1):
        if pretty:
            print(f"  {i:02d}. at '{it.path}': {it.message}")
        else:
            print(f"{it.path}\t{it.message}")

def main() -> int:
    import argparse, sys
    p = argparse.ArgumentParser(description="Validate Echo soulcode JSON (auto/single/bundle/states).")
    p.add_argument("--file", required=True, help="Path to JSON file")
    p.add_argument("--kind", choices=["auto","soulcode","bundle","states"], default="auto")
    p.add_argument("--fail-fast", action="store_true", help="Stop after first issue (exit non-zero)")
    p.add_argument("--quiet", action="store_true", help="Only print final status line")
    p.add_argument("--raw", action="store_true", help="Machine-readable issue output (tab-separated)")
    args = p.parse_args()

    with open(args.file, "r", encoding="utf-8") as f:
        obj = json.load(f)

    rep = validate_obj(obj, kind=args.kind)

    if args.quiet and rep.ok:
        print("OK")
        return 0

    _print_report(rep, pretty=(not args.raw))

    if rep.ok:
        return 0
    if args.fail_fast:
        return 2
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
