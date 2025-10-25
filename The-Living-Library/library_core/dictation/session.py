"""
Dictation session management.

This module records back-and-forth turns between participants (human or
agent) so that both sides share a single source of truth.  Transcripts
are stored in JSON Lines format under the workspace logs directory.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable, Iterator, Mapping, MutableMapping, Optional

from workspace.manager import WorkspaceManager, WorkspaceRecord

ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime(ISO_FORMAT)


@dataclass(slots=True)
class DictationTurn:
    """Single utterance inside a dictation session."""

    speaker: str
    text: str
    timestamp: str = field(default_factory=_utc_now)
    tags: Mapping[str, str] | None = None
    metadata: Mapping[str, str] | None = None

    def to_dict(self) -> MutableMapping[str, object]:
        data = asdict(self)
        # Filter empty optional fields for cleaner storage.
        return {key: value for key, value in data.items() if value}


class DictationSession:
    """
    Coordinates dictation turns for a given workspace.

    A session writes to two files:
    * `<logs>/dictation_<session_id>.jsonl`   — turn-by-turn log
    * `<logs>/dictation_<session_id>.meta.json` — metadata snapshot
    """

    def __init__(
        self,
        workspace: WorkspaceRecord,
        session_id: str,
        participants: Iterable[str],
        description: str | None = None,
    ) -> None:
        self.workspace = workspace
        self.session_id = session_id
        self.participants = tuple(participants)
        self.description = description or ""

        log_filename = f"dictation_{session_id}.jsonl"
        meta_filename = f"dictation_{session_id}.meta.json"

        self._log_path = workspace.path / "logs" / log_filename
        self._meta_path = workspace.path / "logs" / meta_filename

        self._ensure_files()

    # ------------------------------------------------------------------ factory

    @classmethod
    def start(
        cls,
        manager: WorkspaceManager,
        workspace_id: str,
        session_id: Optional[str] = None,
        participants: Optional[Iterable[str]] = None,
        description: str | None = None,
    ) -> "DictationSession":
        """Create (or resume) a dictation session for a workspace."""
        record = manager.get(workspace_id)
        session_identifier = session_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        session_participants = participants or ("user", "agent")
        return cls(record, session_identifier, session_participants, description=description)

    # ----------------------------------------------------------------- operations

    def record_turn(
        self,
        speaker: str,
        text: str,
        *,
        tags: Mapping[str, str] | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> DictationTurn:
        """
        Append a new utterance to the transcript.

        Parameters
        ----------
        speaker:
            Identifier for the participant (typically ``"user"`` or ``"agent"``).
        text:
            Raw content of the utterance.
        tags:
            Optional structured hints such as ``{"stage": "scatter"}``.
        metadata:
            Additional arbitrary key/value pairs captured at logging time.
        """
        turn = DictationTurn(speaker=speaker, text=text, tags=tags, metadata=metadata)
        with self._log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(turn.to_dict(), ensure_ascii=False) + "\n")
        return turn

    def iter_turns(self) -> Iterator[DictationTurn]:
        """Iterate over the recorded turns in chronological order."""
        if not self._log_path.exists():
            return iter(())
        with self._log_path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    payload = json.loads(line)
                    yield DictationTurn(
                        speaker=payload.get("speaker", "unknown"),
                        text=payload.get("text", ""),
                        timestamp=payload.get("timestamp", _utc_now()),
                        tags=payload.get("tags"),
                        metadata=payload.get("metadata"),
                    )

    def metadata(self) -> Mapping[str, object]:
        """Return the metadata block associated with this session."""
        if self._meta_path.exists():
            return json.loads(self._meta_path.read_text(encoding="utf-8"))
        return {}

    def update_metadata(self, **fields: object) -> None:
        """Merge new metadata values into the persistent snapshot."""
        current = dict(self.metadata())
        current.update(fields)
        current.setdefault("session_id", self.session_id)
        current.setdefault("participants", list(self.participants))
        current.setdefault("description", self.description)
        current.setdefault("created_at", self.metadata().get("created_at", _utc_now()))
        self._meta_path.write_text(json.dumps(current, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------ internals

    def _ensure_files(self) -> None:
        """Create fresh log + metadata files if they do not yet exist."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._meta_path.parent.mkdir(parents=True, exist_ok=True)

        if not self._log_path.exists():
            self._log_path.touch()

        if not self._meta_path.exists():
            self.update_metadata(created_at=_utc_now())

    # ---------------------------------------------------------------- properties

    @property
    def log_path(self) -> Path:
        """Path to the JSONL transcript file."""
        return self._log_path

    @property
    def meta_path(self) -> Path:
        """Path to the metadata JSON file."""
        return self._meta_path
