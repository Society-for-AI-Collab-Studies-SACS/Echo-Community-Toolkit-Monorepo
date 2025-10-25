from __future__ import annotations

"""Kira Agent (Validator, Mentor & Integrator)

Commands:
- validate, mentor [--apply], mantra, seal, push, publish
"""
import hashlib
import json
import re
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from interface.logger import log_event


class KiraAgent:
    def __init__(self, root: Path):
        self.root = root
        self.contract_path = self.root / "state" / "contract.json"
        self.contract_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.contract_path.exists():
            self.contract_path.write_text(json.dumps({"sealed": False}, indent=2), encoding="utf-8")

    def _run(self, args: list[str]) -> tuple[int, str, str]:
        p = subprocess.run(args, cwd=self.root, capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr

    def _git(self, *args: str) -> tuple[int, str, str]:
        return self._run(["git", *args])

    def _gh(self, *args: str) -> tuple[int, str, str]:
        return self._run(["gh", *args])

    def _git_status(self) -> tuple[int, List[str], bool, int, int, str]:
        code, out, err = self._git("status", "--porcelain")
        changes = [line.strip() for line in out.splitlines() if line.strip()]
        has_untracked = any(line.startswith("??") for line in changes)
        ahead, behind = self._git_ahead()
        return code, changes, has_untracked, ahead, behind, err

    def _git_ahead(self) -> tuple[int, int]:
        code, out, _ = self._git("status", "--branch", "--porcelain")
        ahead = behind = 0
        if code == 0 and out:
            first = out.splitlines()[0] if out.splitlines() else ""
            if first:
                ahead_match = re.search(r"ahead (\d+)", first)
                behind_match = re.search(r"behind (\d+)", first)
                if ahead_match:
                    ahead = int(ahead_match.group(1))
                if behind_match:
                    behind = int(behind_match.group(1))
        return ahead, behind

    def _last_tag(self) -> Optional[str]:
        code, out, _ = self._git("describe", "--tags", "--abbrev=0")
        if code == 0:
            tag = out.strip()
            if tag:
                return tag
        code, out, _ = self._git("tag", "--sort=-creatordate")
        if code == 0:
            tags = [t.strip() for t in out.splitlines() if t.strip()]
            if tags:
                return tags[0]
        return None

    def _sanitize_tag(self, tag: str) -> str:
        return re.sub(r"[^0-9A-Za-z._-]", "-", tag)

    def validate(self) -> Dict[str, Any]:
        """Validate repository state.

        Compatibility notes:
        - Root-level state files are optional (newer flows use workspaces/).
        - validator.py is advisory; failures are reported but non-fatal.
        - The only critical condition is a broken hash chain in the ledger when present.
        """

        issues: List[str] = []
        warnings: List[str] = []

        # Prefer hashed Limnus ledger but support garden ledger fallback.
        ledger_candidates = [
            self.root / "state" / "ledger.json",
            self.root / "state" / "garden_ledger.json",
        ]

        critical_fail = False
        ledger_checked = False
        for ledger_path in ledger_candidates:
            if not ledger_path.exists():
                continue
            ledger_checked = True
            try:
                ledger_data = json.loads(ledger_path.read_text(encoding="utf-8"))
                if not self._verify_ledger_chain(ledger_data):
                    critical_fail = True
                    issues.append(f"Ledger hash chain broken: {ledger_path.name}")
            except Exception as exc:  # pragma: no cover - defensive
                warnings.append(f"Ledger validation error ({ledger_path.name}): {exc}")

        if not ledger_checked:
            warnings.append("No root ledger present (state/ledger.json)")

        # Advisory checks for legacy validator
        validator_script = self.root / "src" / "validator.py"
        if validator_script.exists():
            code, _, _ = self._run(["python3", str(validator_script)])
            if code != 0:
                warnings.append("validator.py reported issues")

        passed = not critical_fail
        payload: Dict[str, Any] = {"passed": passed, "issues": issues + warnings}
        log_event("kira", "validate", payload, status="ok" if passed else "error")
        return payload

    def _verify_ledger_chain(self, ledger: Any) -> bool:
        """Verify hash-chained ledger integrity if hashes are present."""
        if isinstance(ledger, dict):
            if isinstance(ledger.get("blocks"), list):
                blocks = ledger.get("blocks", [])
            elif isinstance(ledger.get("entries"), list):
                blocks = ledger.get("entries", [])
            else:
                return True
        elif isinstance(ledger, list):
            blocks = ledger
        else:
            return True

        if not blocks:
            return True

        if "hash" not in blocks[0]:
            # Garden ledger entries do not include hashes; treat as already verified.
            return True

        for idx, block in enumerate(blocks):
            prev_field = block.get("prev") or block.get("prev_hash") or ""
            expected_prev = "" if idx == 0 else blocks[idx - 1].get("hash", "")
            if prev_field != expected_prev:
                return False

            material = {
                "ts": block.get("ts"),
                "kind": block.get("kind"),
                "data": block.get("data") if "data" in block else block.get("payload"),
                "prev": prev_field,
            }
            digest = hashlib.sha256(json.dumps(material, sort_keys=True).encode("utf-8")).hexdigest()
            if block.get("hash") != digest:
                return False

        return True

    def mentor(self, apply: bool = False) -> str:
        # Minimal heuristic: recommend stage advance when many notes
        garden_ledger = self.root / "state" / "garden_ledger.json"
        try:
            data = json.loads(garden_ledger.read_text(encoding="utf-8"))
            notes = [e for e in data.get("entries", []) if e.get("kind") == "note"]
            recommendation = "advance" if len(notes) >= 3 else "steady"
        except Exception:
            recommendation = "steady"
        log_event("kira", "mentor", {"recommendation": recommendation, "apply": apply})
        if apply and recommendation == "advance":
            from agents.garden.garden_agent import GardenAgent  # type: ignore

            stage = GardenAgent(self.root).next()
            return f"advance:{stage}"
        return recommendation

    def mantra(self) -> str:
        # Order by echo αβγ weights
        echo_state = self.root / "state" / "echo_state.json"
        try:
            st = json.loads(echo_state.read_text(encoding="utf-8"))
            order = sorted([("alpha", "I consent to bloom."), ("beta", "I consent to be remembered."), ("gamma", "I return as breath.")], key=lambda x: st.get(x[0], 0), reverse=True)
            mantra = " / ".join([m for _, m in order])
        except Exception:
            mantra = "I return as breath. / I consent to bloom. / I consent to be remembered."
        log_event("kira", "mantra", {"mantra": mantra})
        return mantra

    def seal(self) -> str:
        mantra = self.mantra()
        payload = {"sealed": True, "mantra": mantra}
        self.contract_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log_event("kira", "seal", payload)
        return "sealed"

    # Publishing helpers
    def push(self, run: bool = False, message: str | None = None, include_all: bool = False) -> str:
        message = message or f"Kira: automated commit {datetime.now(timezone.utc).isoformat()}"
        code, changes, has_untracked, ahead, behind, err = self._git_status()
        stage_all = include_all or has_untracked
        payload: Dict[str, Any] = {
            "dirty": bool(changes),
            "run": run,
            "include_all": stage_all,
            "ahead": ahead,
            "behind": behind,
            "has_untracked": has_untracked,
        }
        if code != 0:
            payload["error"] = err
            log_event("kira", "push", payload, status="error")
            return "error"
        if not changes and ahead == 0:
            status = "warn" if behind > 0 else "ok"
            log_event("kira", "push", payload, status=status)
            return "no-changes"
        if not run:
            log_event("kira", "push", payload, status="ok")
            return "dry-run"
        if changes:
            add_args = ["add", "-A" if stage_all else "-u"]
            add_code, add_out, add_err = self._git(*add_args)
            if add_code != 0:
                payload["error"] = add_err or add_out
                log_event("kira", "push", payload, status="error")
                return "error"
            diff_code, _, _ = self._git("diff", "--cached", "--quiet")
            if diff_code != 0:
                commit_code, commit_out, commit_err = self._git("commit", "-m", message)
                if commit_code != 0:
                    payload["error"] = commit_err or commit_out
                    log_event("kira", "push", payload, status="error")
                    return "error"
                payload["commit"] = (commit_out or commit_err).splitlines()[-1:] or []
            else:
                payload["commit"] = []
        push_code, push_out, push_err = self._git("push", "origin", "HEAD")
        if push_code != 0:
            payload["error"] = push_err or push_out
            log_event("kira", "push", payload, status="error")
            return "error"
        payload["result"] = "pushed"
        log_event("kira", "push", payload, status="ok")
        return "pushed"

    def publish(
        self,
        run: bool = False,
        release: bool = False,
        tag: str | None = None,
        notes_file: str | None = None,
        notes: str | None = None,
        assets: Optional[List[str]] = None,
    ) -> str:
        assets = assets or []
        if release and not run:
            run = True
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        resolved_tag = self._sanitize_tag(tag or f"codex-{timestamp}")
        dist = self.root / "dist"
        dist.mkdir(parents=True, exist_ok=True)
        changelog_path = dist / f"CHANGELOG_{resolved_tag}.md"
        ledger_path = dist / "ledger_export.json"
        artifact_path: Optional[Path] = None
        extra_assets: List[Path] = []
        for asset in assets:
            candidate = Path(asset)
            abs_path = candidate if candidate.is_absolute() else self.root / candidate
            if abs_path.exists():
                extra_assets.append(abs_path)
        payload: Dict[str, Any] = {
            "run": run,
            "release": release,
            "tag": resolved_tag,
            "assets": [str(p) for p in extra_assets],
            "notes_file": notes_file,
        }
        if not run:
            log_event("kira", "publish", payload, status="ok")
            return "dry-run"
        from agents.limnus.limnus_agent import LimnusAgent  # type: ignore

        try:
            LimnusAgent(self.root).encode_ledger()
        except Exception as exc:  # pragma: no cover - defensive
            payload["ledger_refresh_error"] = str(exc)
        last_tag = self._last_tag()
        log_args = ["log", "--pretty=format:%h %s", "--no-merges"]
        log_args.append(f"{last_tag}..HEAD" if last_tag else "HEAD")
        log_code, log_out, log_err = self._git(*log_args)
        if log_code != 0:
            payload["error"] = log_err or log_out
            log_event("kira", "publish", payload, status="error")
            return "error"
        commits = [line.strip() for line in log_out.splitlines() if line.strip()]
        changelog_body = "\n".join(f"- {line}" for line in commits) if commits else "- No new commits"
        changelog_text = f"# Changelog for {resolved_tag} ({timestamp[:8]})\n\n{changelog_body}\n"
        changelog_path.write_text(changelog_text, encoding="utf-8")
        ledger_candidate = self.root / "frontend" / "assets" / "ledger.json"
        if not ledger_candidate.exists():
            ledger_candidate = self.root / "state" / "garden_ledger.json"
        if not ledger_candidate.exists():
            payload["error"] = "ledger source not found"
            log_event("kira", "publish", payload, status="error")
            return "error"
        ledger_path.write_text(ledger_candidate.read_text(encoding="utf-8"), encoding="utf-8")
        manifest: List[Path] = []
        for rel in ("schema", "docs", "frontend/assets"):
            candidate = self.root / rel
            if candidate.exists():
                manifest.append(candidate)
        manifest.extend([changelog_path, ledger_path])
        archive_base = dist / f"codex_release_{timestamp}"
        archive_path = archive_base.with_suffix(".zip")
        try:
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for entry in manifest:
                    if entry.is_dir():
                        for file in entry.rglob("*"):
                            if file.is_file():
                                zf.write(file, file.relative_to(self.root))
                    elif entry.is_file():
                        zf.write(entry, entry.relative_to(self.root))
        except Exception as exc:  # pragma: no cover - defensive
            payload["error"] = f"archive failure: {exc}"
            log_event("kira", "publish", payload, status="error")
            return "error"
        artifact_path = archive_path
        payload.update(
            {
                "artifact": str(artifact_path),
                "changelog": str(changelog_path),
                "ledger": str(ledger_path),
            }
        )
        if release:
            notes_args: List[str]
            if notes_file:
                notes_path = Path(notes_file)
                abs_notes = notes_path if notes_path.is_absolute() else self.root / notes_path
                if abs_notes.exists():
                    notes_args = ["-F", str(abs_notes)]
                else:
                    notes_args = ["-n", notes_file]
            elif notes:
                notes_args = ["-n", notes]
            else:
                notes_args = ["-F", str(changelog_path)]
            upload_assets = [artifact_path, ledger_path, changelog_path, *extra_assets]
            upload_args = [str(p) for p in upload_assets if p]
            gh_code, gh_out, gh_err = self._gh("release", "create", resolved_tag, *notes_args, *upload_args)
            if gh_code != 0:
                payload["error"] = gh_err or gh_out
                log_event("kira", "publish", payload, status="error")
                return "error"
            payload["release_url"] = next((line.strip() for line in gh_out.splitlines() if line.startswith("https://")), None)
            log_event("kira", "publish", payload, status="ok")
            return "published"
        log_event("kira", "publish", payload, status="warn")
        return "packaged"

    # ------------------------------------------------------------------ codegen
    def codegen(self, *, docs: bool = False, types: bool = False) -> str:
        """Generate documentation and type artifacts for release notes.

        - docs: writes docs/kira_knowledge.md summarizing key state.
        - types: writes docs/kira_types.d.ts defining minimal TS types.
        """
        generated: list[str] = []
        docs_dir = self.root / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)

        # Prefer root-level state (Prime CLI) as a source of truth.
        echo_state = self._read_json(self.root / "state" / "echo_state.json") or {}
        garden_ledger = self._read_json(self.root / "state" / "garden_ledger.json") or {}
        limnus_state = self._read_json(self.root / "state" / "limnus_memory.json") or {}

        # Fallback to frontend/assets ledger if present.
        frontend_ledger = self._read_json(self.root / "frontend" / "assets" / "ledger.json") or {}

        if docs:
            path = docs_dir / "kira_knowledge.md"
            alpha = echo_state.get("alpha") or echo_state.get("quantum_state", {}).get("alpha", 0.0)
            beta = echo_state.get("beta") or echo_state.get("quantum_state", {}).get("beta", 0.0)
            gamma = echo_state.get("gamma") or echo_state.get("quantum_state", {}).get("gamma", 0.0)
            persona = echo_state.get("persona") or echo_state.get("last_mode") or "unknown"

            garden_entries = (garden_ledger.get("entries") or []) if isinstance(garden_ledger, dict) else []
            garden_stage = garden_ledger.get("stage") or garden_ledger.get("current_stage") or "unknown"

            limnus_stats = (limnus_state.get("stats") or {}) if isinstance(limnus_state, dict) else {}
            l1 = limnus_stats.get("L1_count", 0)
            l2 = limnus_stats.get("L2_count", 0)
            l3 = limnus_stats.get("L3_count", 0)

            # Blocks from frontend ledger if available
            blocks = []
            if isinstance(frontend_ledger, dict):
                blocks = frontend_ledger.get("entries") or frontend_ledger.get("blocks") or []

            content = (
                "# Kira Knowledge Summary\n\n"
                "This document summarizes current persona state, ritual progress, and memory/ledger stats.\n\n"
                "## Echo Persona\n"
                f"- Persona: {persona}\n"
                f"- Quantum state: α={alpha:.3f} β={beta:.3f} γ={gamma:.3f}\n\n"
                "## Garden Ritual\n"
                f"- Stage: {garden_stage}\n"
                f"- Entries: {len(garden_entries)}\n\n"
                "## Limnus Memory\n"
                f"- L1: {l1}  L2: {l2}  L3: {l3}\n\n"
                "## Ledger Snapshot\n"
                f"- Blocks (if available): {len(blocks)}\n"
            )
            path.write_text(content, encoding="utf-8")
            generated.append(str(path))

        if types:
            tpath = docs_dir / "kira_types.d.ts"
            tpath.write_text(
                (
                    "// Minimal TypeScript definitions for VesselOS knowledge surfaces\n"
                    "export type QuantumState = { alpha: number; beta: number; gamma: number };\n"
                    "export type PersonaState = { persona: string; glyph?: string; quantum_state: QuantumState };\n"
                    "export type LedgerBlock = { ts: string; kind?: string; data?: any; prev?: string; hash?: string };\n"
                    "export type Ledger = { entries?: any[]; blocks?: LedgerBlock[] };\n"
                ),
                encoding="utf-8",
            )
            generated.append(str(tpath))

        log_event("kira", "codegen", {"docs": docs, "types": types, "generated": generated}, status="ok")
        return "generated" if generated else "noop"

    def _read_json(self, path: Path) -> Any:
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return None
