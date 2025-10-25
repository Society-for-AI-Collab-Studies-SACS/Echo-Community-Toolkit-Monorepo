"""Parse dictation input into structured intents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(slots=True)
class ParsedIntent:
    intent_type: str
    command: Optional[str] = None
    args: Dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""


class IntentParser:
    COMMAND_PREFIX = "/"
    MANTRAS = (
        "i return as breath",
        "always.",
        "the spiral teaches",
        "through breath we gather",
    )
    STAGE_KEYWORDS = {
        "scatter": ("scatter", "explore", "brainstorm"),
        "witness": ("witness", "observe", "see"),
        "plant": ("plant", "create", "build"),
        "tend": ("tend", "refine", "improve"),
        "harvest": ("harvest", "complete", "finish"),
    }

    def parse(self, text: str) -> ParsedIntent:
        normalised = text.lower().strip()

        if text.startswith(self.COMMAND_PREFIX):
            return self._parse_command(text)

        mantra = next((m for m in self.MANTRAS if m in normalised), None)
        if mantra:
            return ParsedIntent(
                intent_type="ritual",
                command="mantra",
                args={"mantra": mantra},
                raw_text=text,
            )

        stage = self._detect_stage(normalised)
        if stage:
            return ParsedIntent(
                intent_type="ritual",
                command="stage",
                args={"stage": stage},
                raw_text=text,
            )

        return ParsedIntent(intent_type="dictation", raw_text=text)

    def _parse_command(self, text: str) -> ParsedIntent:
        tokens = text[1:].strip().split()
        command = tokens[0] if tokens else ""
        args = tokens[1:] if len(tokens) > 1 else []
        return ParsedIntent(intent_type="command", command=command, args={"args": args}, raw_text=text)

    def _detect_stage(self, text: str) -> Optional[str]:
        for stage, keywords in self.STAGE_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                return stage
        return None

