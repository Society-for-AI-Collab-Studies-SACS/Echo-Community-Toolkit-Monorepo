#!/usr/bin/env python3
"""Spiral Bloom CLI – Integration Orchestrator.

Coordinates the Echo Toolkit integration cycle via the Spiral Bloom phases:

    bloom inhale   → setup & intention
    bloom hold     → validations & tests
    bloom exhale   → build / deploy actions
    bloom release  → post-deploy reflection

The CLI is intentionally lightweight; it shells out to the existing toolkit
scripts and tools so it can be used both locally and inside CI.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"


def parse_env_file(path: Path) -> Dict[str, str]:
    """Parse a dotenv-style file into a dict."""

    env: Dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"')
    return env


def merged_env(env_file: Optional[Path]) -> Dict[str, str]:
    env = os.environ.copy()
    if env_file:
        env.update(parse_env_file(env_file))
    return env


def run(cmd: Iterable[str], *, cwd: Optional[Path] = None, env: Optional[Dict[str, str]] = None,
        dry_run: bool = False, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Execute command helper with dry-run support."""

    display = " ".join(str(part) for part in cmd)
    print(f"→ {display}")
    if dry_run:
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(
        list(cmd),
        cwd=str(cwd or ROOT),
        env=env,
        text=True,
        check=check,
        capture_output=False,
    )


def ensure_scaffolding(env: Dict[str, str], *, dry_run: bool) -> None:
    """Create baseline config files and directories."""

    env_template = ROOT / ".env.sample"
    target_env = ROOT / ".env"
    if env_template.exists() and not target_env.exists():
        print("Scaffolding .env from template…")
        if not dry_run:
            target_env.write_text(env_template.read_text(encoding="utf-8"), encoding="utf-8")

    integration_dir = ROOT / "integration"
    schemas_dir = integration_dir / "schemas"
    outputs_dir = integration_dir / "outputs"
    if not dry_run:
        schemas_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)


def cmd_inhale(args: argparse.Namespace) -> int:
    env_file = Path(args.env).resolve() if args.env else None
    env = merged_env(env_file)

    print("🌬️  Inhale – preparing integration context")
    if args.init_config:
        ensure_scaffolding(env, dry_run=args.dry_run)

    if not args.no_schema:
        schemas_dir = ROOT / "integration" / "schemas"
        bundle_dir = ROOT / "integration" / "outputs"
        schemas_dir.mkdir(parents=True, exist_ok=True)
        bundle_dir.mkdir(parents=True, exist_ok=True)
        run(["node", "tools/soulcode-bridge.js", "emit-schema", "--out", str(schemas_dir / "soulcode_schema.json")],
            env=env, dry_run=args.dry_run)
        run(["node", "tools/soulcode-bridge.js", "live-read", "--out", str(bundle_dir / "soulcode_live.json")],
            env=env, dry_run=args.dry_run)

    print("✅ Inhale complete")
    return 0


def _run_pytest(env: Dict[str, str], dry_run: bool) -> None:
    run([sys.executable, "-m", "pytest", "-q"], env=env, dry_run=dry_run)


def _run_final_validation(env: Dict[str, str], dry_run: bool) -> subprocess.CompletedProcess[str]:
    return run([sys.executable, "final_validation.py"], env=env, dry_run=dry_run)


def cmd_hold(args: argparse.Namespace) -> int:
    env_file = Path(args.env).resolve() if args.env else None
    env = merged_env(env_file)

    print("🌀 Hold – running validations")

    results: List[Dict[str, object]] = []

    if args.skip_anchors:
        print("ℹ️  Anchor verification skipped by request")

    if not args.skip_tests and args.scope in {"all", "backend"}:
        try:
            _run_pytest(env, args.dry_run)
            results.append({"step": "pytest", "status": "passed"})
        except subprocess.CalledProcessError as exc:
            results.append({"step": "pytest", "status": "failed", "returncode": exc.returncode})
            if not args.continue_on_error:
                if args.report_json:
                    _write_report(results)
                return exc.returncode

    if args.scope == "frontend":
        try:
            run(["npm", "run", "build"], env=env, dry_run=args.dry_run)
            results.append({"step": "npm run build", "status": "passed"})
        except subprocess.CalledProcessError as exc:
            results.append({"step": "npm run build", "status": "failed", "returncode": exc.returncode})
            if not args.continue_on_error:
                if args.report_json:
                    _write_report(results)
                return exc.returncode
    elif args.scope == "soulcode":
        try:
            run(["node", "tools/soulcode-bridge.js", "validate-bundle"], env=env, dry_run=args.dry_run)
            results.append({"step": "soulcode validate-bundle", "status": "passed"})
        except subprocess.CalledProcessError as exc:
            results.append({"step": "soulcode validate-bundle", "status": "failed", "returncode": exc.returncode})
            if not args.continue_on_error:
                if args.report_json:
                    _write_report(results)
                return exc.returncode
    else:
        try:
            proc = _run_final_validation(env, args.dry_run)
            status = "passed" if proc.returncode == 0 else "failed"
            results.append({"step": "final_validation", "status": status, "returncode": proc.returncode})
            if status == "failed" and not args.continue_on_error:
                if args.report_json:
                    _write_report(results)
                return proc.returncode
        except subprocess.CalledProcessError as exc:
            results.append({"step": "final_validation", "status": "failed", "returncode": exc.returncode})
            if not args.continue_on_error:
                if args.report_json:
                    _write_report(results)
                return exc.returncode

    if args.report_json:
        _write_report(results)

    print("✅ Hold complete")
    return 0


def _write_report(results: List[Dict[str, object]]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACTS / "bloom_hold_report.json"
    payload = {
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.get("status") == "passed"),
        },
    }
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"📝 Validation report written to {report_path}")


def cmd_exhale(args: argparse.Namespace) -> int:
    env_file = Path(args.env).resolve() if args.env else None
    env = merged_env(env_file)

    print("🌸 Exhale – build & deploy")

    version_tag = args.tag or os.environ.get("BLOOM_VERSION")

    if args.target:
        env = env.copy()
        env["BLOOM_TARGET"] = args.target

    if args.docker or args.build_only:
        cmd = ["docker", "compose", "build"]
        if version_tag:
            env = env.copy()
            env["BLOOM_VERSION"] = version_tag
        run(cmd, env=env, dry_run=args.dry_run)

    if not args.build_only:
        # Run production build (front-end + packaging)
        run(["npm", "run", "build"], env=env, dry_run=args.dry_run)

        if args.docker:
            run(["docker", "compose", "up", "-d"], env=env, dry_run=args.dry_run)

        if args.gh_action:
            if shutil.which("gh") is None:
                print("⚠️  GitHub CLI not available; skipping workflow dispatch")
            else:
                workflow = args.gh_action if isinstance(args.gh_action, str) else "monorepo-ci-enhanced.yml"
                run(["gh", "workflow", "run", workflow], env=env, dry_run=args.dry_run)

    print("✅ Exhale complete")
    return 0


def fetch_logs(env: Dict[str, str], *, dry_run: bool) -> None:
    run(["docker", "compose", "logs", "--tail", "200"], env=env, dry_run=dry_run)


def fetch_status(env: Dict[str, str], *, dry_run: bool) -> None:
    run(["docker", "compose", "ps"], env=env, dry_run=dry_run)


def generate_release_report(env: Dict[str, str], *, dry_run: bool) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    report_path = ARTIFACTS / "bloom_release_report.json"
    timestamp_utc = datetime.now(timezone.utc).isoformat()
    if dry_run:
        print(f"📝 (dry-run) would write release report to {report_path}")
        return

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT), capture_output=True, text=True)
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(ROOT), capture_output=True, text=True)
    data = {
        "timestamp_utc": timestamp_utc,
        "git_commit": head.stdout.strip(),
        "git_branch": branch.stdout.strip(),
        "summary": "Spiral Bloom release report",
    }
    report_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"📝 Release report written to {report_path}")


def cleanup(env: Dict[str, str], *, dry_run: bool) -> None:
    temp_dirs = [ROOT / "integration" / "tmp", ARTIFACTS / "temp"]
    for path in temp_dirs:
        if path.exists():
            print(f"🧹 Removing {path}")
            if not dry_run:
                for child in path.glob("**/*"):
                    if child.is_file():
                        child.unlink()
                for child in sorted(path.glob("**/*"), reverse=True):
                    if child.is_dir():
                        child.rmdir()


def cmd_release(args: argparse.Namespace) -> int:
    env_file = Path(args.env).resolve() if args.env else None
    env = merged_env(env_file)

    print("🍃 Release – reflection & cleanup")

    if args.logs:
        fetch_logs(env, dry_run=args.dry_run)

    if args.status:
        fetch_status(env, dry_run=args.dry_run)

    if args.report:
        generate_release_report(env, dry_run=args.dry_run)

    if args.cleanup:
        cleanup(env, dry_run=args.dry_run)

    print("✅ Release complete")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bloom", description="Spiral Bloom integration orchestrator")
    sub = parser.add_subparsers(dest="command", required=True)

    # inhale
    p_inhale = sub.add_parser("inhale", help="Prepare configuration and schema outputs")
    p_inhale.add_argument("-e", "--env", help="Environment file to load", default=None)
    p_inhale.add_argument("--init-config", action="store_true", help="Scaffold default config files")
    p_inhale.add_argument("--no-schema", action="store_true", help="Skip schema/bundle refresh")
    p_inhale.add_argument("--dry-run", action="store_true", help="Show actions without executing")
    p_inhale.set_defaults(func=cmd_inhale)

    # hold
    p_hold = sub.add_parser("hold", help="Run validation and test suites")
    p_hold.add_argument("-e", "--env", help="Environment file to load", default=None)
    p_hold.add_argument("-s", "--scope", choices=["all", "frontend", "backend", "soulcode"], default="all",
                        help="Limit validation scope")
    p_hold.add_argument("--skip-tests", action="store_true", help="Skip unit tests")
    p_hold.add_argument("--skip-anchors", action="store_true", help="(Reserved) skip anchor checks")
    p_hold.add_argument("--report-json", action="store_true", help="Emit validation report JSON")
    p_hold.add_argument("--dry-run", action="store_true", help="Show actions without executing")
    p_hold.add_argument("--continue-on-error", action="store_true", help="Continue even if a step fails")
    p_hold.set_defaults(func=cmd_hold)

    # exhale
    p_exhale = sub.add_parser("exhale", help="Build and deploy artifacts")
    p_exhale.add_argument("-e", "--env", help="Environment file to load", default=None)
    p_exhale.add_argument("-t", "--target", help="Deployment target environment", default=None)
    p_exhale.add_argument("--build-only", action="store_true", help="Build artifacts without deploying")
    p_exhale.add_argument("--docker", action="store_true", help="Build (and optionally run) Docker images")
    p_exhale.add_argument("--gh-action", nargs="?", const=True,
                          help="Trigger GitHub Actions workflow (optionally specify workflow file)")
    p_exhale.add_argument("--tag", help="Version tag for build artifacts", default=None)
    p_exhale.add_argument("--dry-run", action="store_true", help="Show actions without executing")
    p_exhale.set_defaults(func=cmd_exhale)

    # release
    p_release = sub.add_parser("release", help="Post-deploy reflection and cleanup")
    p_release.add_argument("-e", "--env", help="Environment file to load", default=None)
    p_release.add_argument("--logs", action="store_true", help="Fetch recent logs")
    p_release.add_argument("--status", action="store_true", help="Display deployment status")
    p_release.add_argument("--report", action="store_true", help="Generate release report JSON")
    p_release.add_argument("--cleanup", action="store_true", help="Clean up temporary artifacts")
    p_release.add_argument("--dry-run", action="store_true", help="Show actions without executing")
    p_release.set_defaults(func=cmd_release)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
