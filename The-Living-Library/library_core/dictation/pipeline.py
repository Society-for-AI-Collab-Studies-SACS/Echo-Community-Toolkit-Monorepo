"""
Orchestration helpers that bridge dictation sessions with the
vessel-narrative-MRP engine.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from .session import DictationSession


class MRPPipeline:
    """
    Executes the 20-chapter MRP build for a given dictation session.

    The pipeline coordinates the following repositories:

    - ``vessel-narrative-MRP`` (schema + chapter generation)
    - ``The-Living_Garden-Chronicles`` (templated landing pages)
    - ``echo-community-toolkit`` (supporting assets already referenced by MRP)
    - ``kira-prime`` (optional validation via ``vesselos.py``)
    """

    def __init__(self, session: DictationSession) -> None:
        self.session = session
        self.root = Path(__file__).resolve().parents[2]
        self.mrp_root = self.root / "vessel-narrative-MRP"
        self.garden_root = self.root / "The-Living_Garden-Chronicles"
        self.kira_root = self.root / "kira-prime"

    # ------------------------------------------------------------------ public

    def run(
        self,
        *,
        run_schema: bool = True,
        copy_templates: bool = True,
        run_kira_validation: bool = False,
    ) -> Path:
        """
        Execute the MRP generators and copy the resulting artefacts into the
        workspace output directory.

        Parameters
        ----------
        run_schema:
            Execute ``src/schema_builder.py`` before generating chapters.
        copy_templates:
            Copy both the MRP ``frontend`` output and The Living Garden
            Chronicles templates into the session output directory.
        run_kira_validation:
            Optionally call ``python3 vesselos.py validate`` inside
            ``kira-prime`` after generation.
        """
        output_root = (
            self.session.workspace.path / "outputs" / "mrp" / self.session.session_id
        )
        output_root.mkdir(parents=True, exist_ok=True)

        if run_schema:
            self._run_command(["python3", "src/schema_builder.py"], cwd=self.mrp_root)
        self._run_command(["python3", "src/generate_chapters.py"], cwd=self.mrp_root)

        if copy_templates:
            self._copy_directory(self.mrp_root / "frontend", output_root / "frontend")
            self._copy_directory(
                self.garden_root / "frontend",
                output_root / "garden-chronicles",
            )

        if run_kira_validation:
            # Validation is informative; do not raise on failure to keep the
            # pipeline resilient when running in lightweight environments.
            self._run_command(
                ["python3", "vesselos.py", "validate"],
                cwd=self.kira_root,
                check=False,
            )

        self.session.update_metadata(mrp_output=str(output_root))
        self.session.record_turn(
            "system",
            f"MRP cycle complete for session {self.session.session_id}",
            tags={"action": "mrp_generate"},
            metadata={"output_root": str(output_root)},
        )

        return output_root

    # ----------------------------------------------------------------- helpers

    def _run_command(
        self,
        command: list[str],
        *,
        cwd: Optional[Path] = None,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=str(cwd) if cwd else None,
            check=check,
            text=True,
            capture_output=not check,
        )

    @staticmethod
    def _copy_directory(src: Path, dst: Path) -> None:
        if not src.exists():
            return
        shutil.copytree(src, dst, dirs_exist_ok=True)
