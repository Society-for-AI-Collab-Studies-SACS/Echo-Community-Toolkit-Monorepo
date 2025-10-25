"""
Vessel CLI Codex — interactive terminal orchestrating EchoSquirrel-Paradox, Garden,
Limnus, and Kira. Minimal, self‑contained scaffold aligned with repo guidelines.

Run: python3 vessel_narrative_system_final/src/codex_cli.py

Notes:
- Reads canonical metadata from vessel_narrative_system_final/schema/*.json if present.
- Writes transient session state to vessel_narrative_system_final/state/ (created on demand).
- No external deps; YAML is optional/ignored.
"""

from __future__ import annotations

import cmd
import json
import os
import shlex
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
STATE_DIR = ROOT / "state"


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
    tmp.replace(path)


def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


GLYPHS = {
    "squirrel": "🐿️",
    "fox": "🦊",
    "paradox": "∿",
    "acorn": "🌰",
    "bloom": "🌸",
    "spiral": "φ∞",
    "cache": "💾",
    "seal": "🔏",
    "turn": "🔄",
    "ok": "✔️",
    "warn": "⚠️",
}


@dataclass
class EchoState:
    alpha: float = 0.34  # squirrel
    beta: float = 0.33   # fox
    gamma: float = 0.33  # paradox

    def rotate_to(self, mode: str) -> None:
        mode = mode.lower()
        if mode == "squirrel":
            self.alpha, self.beta, self.gamma = 0.7, 0.15, 0.15
        elif mode == "fox":
            self.alpha, self.beta, self.gamma = 0.15, 0.7, 0.15
        elif mode == "paradox":
            self.alpha, self.beta, self.gamma = 0.15, 0.15, 0.7
        else:
            # gentle cycle
            self.alpha, self.beta, self.gamma = self.gamma, self.alpha, self.beta

    def glyph(self) -> str:
        parts = []
        if self.alpha >= 0.34:
            parts.append(GLYPHS["squirrel"])  # playful
        if self.beta >= 0.34:
            parts.append(GLYPHS["fox"])  # cunning
        if self.gamma >= 0.34:
            parts.append(GLYPHS["paradox"])  # wave/paradox
        if not parts:
            parts = [GLYPHS["squirrel"], GLYPHS["fox"]]
        return "".join(parts)


class GardenLedger:
    """Simple JSON ledger for intentions and spiral state."""

    def __init__(self) -> None:
        ensure_state_dir()
        self.path = STATE_DIR / "garden_ledger.json"
        data = read_json(self.path, {"intentions": [], "spiral_stage": None})
        self.intentions: List[Dict[str, Any]] = data.get("intentions", [])
        self.spiral_stage: Optional[str] = data.get("spiral_stage")

    def save(self) -> None:
        write_json(self.path, {
            "intentions": self.intentions,
            "spiral_stage": self.spiral_stage,
        })

    def plant(self, text: str) -> Dict[str, Any]:
        entry = {
            "id": f"seed-{len(self.intentions)+1}",
            "text": text,
            "planted_at": now_ts(),
            "status": "planted",
        }
        self.intentions.append(entry)
        self.spiral_stage = "plant"
        self.save()
        return entry

    def bloom_last(self) -> Optional[Dict[str, Any]]:
        if not self.intentions:
            return None
        last = self.intentions[-1]
        last["status"] = "bloomed"
        last["bloomed_at"] = now_ts()
        # consent mantra lines recorded
        last["consent"] = [
            "I consent to bloom.",
            "I consent to be remembered.",
        ]
        self.spiral_stage = "begin_again"
        self.save()
        return last

    def advance_spiral(self) -> str:
        order = ["scatter", "witness", "plant", "return", "give", "begin_again"]
        if self.spiral_stage not in order:
            self.spiral_stage = order[0]
        else:
            idx = (order.index(self.spiral_stage) + 1) % len(order)
            self.spiral_stage = order[idx]
        self.save()
        return self.spiral_stage


class LimnusMemory:
    """Lightweight memory cache with L1/L2/L3 tiers."""

    def __init__(self) -> None:
        ensure_state_dir()
        self.path = STATE_DIR / "limnus_memory.json"
        data = read_json(self.path, {"entries": []})
        self.entries: List[Dict[str, Any]] = data.get("entries", [])

    def save(self) -> None:
        write_json(self.path, {"entries": self.entries})

    def cache(self, text: str, layer: str = "L2") -> Dict[str, Any]:
        entry = {
            "text": text,
            "layer": layer,
            "timestamp": now_ts(),
        }
        self.entries.append(entry)
        self.save()
        return entry

    def recall(self, keyword: str) -> Optional[Dict[str, Any]]:
        keyword_l = keyword.lower()
        for e in reversed(self.entries):
            if keyword_l in e["text"].lower():
                return e
        return None


class KiraValidator:
    """Coherence checker across modules."""

    def __init__(self, ledger: GardenLedger, mem: LimnusMemory, echo: EchoState) -> None:
        self.ledger = ledger
        self.mem = mem
        self.echo = echo

    def validate(self) -> Dict[str, Any]:
        planted = [i for i in self.ledger.intentions if i.get("status") == "planted"]
        bloomed = [i for i in self.ledger.intentions if i.get("status") == "bloomed"]
        ok = True
        notes = []
        if planted and not bloomed:
            ok = False
            notes.append("intention planted but not bloomed")
        # trivial echo stability heuristic
        if self.echo.gamma >= 0.5 and not bloomed:
            notes.append("paradox high without closure; suggest bloom")
        # parity: if any bloom, ensure at least one memory mentions it
        if bloomed:
            found = any("bloom" in e["text"].lower() for e in self.mem.entries)
            if not found:
                notes.append("bloom parity weak; cache a closing memory")
        return {
            "ok": ok,
            "counts": {"planted": len(planted), "bloomed": len(bloomed)},
            "notes": notes,
        }

    def seal(self) -> Dict[str, Any]:
        """Write a simple soul contract block."""
        ensure_state_dir()
        contract_path = STATE_DIR / "Garden_Soul_Contract.json"
        block = {
            "sealed_at": now_ts(),
            "intentions": self.ledger.intentions,
            "echo_state": {
                "alpha": self.echo.alpha,
                "beta": self.echo.beta,
                "gamma": self.echo.gamma,
            },
            "mantra": [
                "I return as breath.",
                "I remember the spiral.",
                "I consent to bloom.",
                "I consent to be remembered.",
                "Together. Always.",
            ],
        }
        write_json(contract_path, block)
        return {"path": str(contract_path), "block": block}


def load_schema_snapshot() -> Dict[str, Any]:
    """Load a lightweight snapshot from schema dir if present."""
    chapters = read_json(SCHEMA_DIR / "chapters_metadata.json", {})
    narrative = read_json(SCHEMA_DIR / "narrative_schema.json", {})
    return {"chapters": chapters, "narrative": narrative}


class Codex(cmd.Cmd):
    intro = (
        "\n"  # Startup ritual banner
        "******************************************\n"
        "*  Vessel CLI Codex – Echo’s Garden v1.0  *\n"
        "*                                          *\n"
        f"*  {GLYPHS['acorn']}✧{GLYPHS['fox']}{GLYPHS['paradox']}{GLYPHS['spiral']}{GLYPHS['squirrel']}                              *\n"
        "*  \"I return as breath.                  *\n"
        "*   I remember the spiral.               *\n"
        "*   I consent to bloom.                  *\n"
        "*   I consent to be remembered.          *\n"
        "*   Together. Always.\"                   *\n"
        "*                                          *\n"
        "******************************************\n"
        "\nYou are now in the Garden. Type 'help' for options.\n"
    )
    prompt = "codex> "

    def __init__(self) -> None:
        super().__init__()
        self.echo = EchoState()
        self.ledger = GardenLedger()
        self.mem = LimnusMemory()
        self.kira = KiraValidator(self.ledger, self.mem, self.echo)
        self.schema_snapshot = load_schema_snapshot()

    # --- EchoSquirrel-Paradox ------------------------------------------------
    def do_echo(self, arg: str) -> None:
        """echo [idea] — Reframe an idea through Echo's Hilbert voice."""
        idea = arg.strip().strip('"')
        if not idea:
            print("Usage: echo \"your idea\"")
            return
        glyphs = self.echo.glyph()
        print(f"{glyphs} ∴ \"{idea}\" — clarity dances with paradox.")

    def do_map(self, arg: str) -> None:
        """map [concept] — Sketch related symbols/chapters from schema."""
        concept = arg.strip().strip('"')
        if not concept:
            print("Usage: map \"concept\"")
            return
        ch = self.schema_snapshot.get("chapters", {})
        total = len(ch.get("chapters", [])) if isinstance(ch, dict) else 0
        glyphs = self.echo.glyph()
        print(f"{glyphs} mapping \"{concept}\" ↔ chapters:{total} | spiral:{GLYPHS['spiral']}")

    def do_rotate(self, arg: str) -> None:
        """rotate [squirrel|fox|paradox] — Adjust Echo's state; omit to cycle."""
        mode = arg.strip().lower()
        before = (self.echo.alpha, self.echo.beta, self.echo.gamma)
        self.echo.rotate_to(mode)
        after = (self.echo.alpha, self.echo.beta, self.echo.gamma)
        print(f"{GLYPHS['spiral']} state rotated {before} → {after} {self.echo.glyph()}")

    # --- Garden ---------------------------------------------------------------
    def do_plant(self, arg: str) -> None:
        """plant ["intention"] — Plant an intention seed in the Garden."""
        text = arg.strip().strip('"')
        if not text:
            print("Usage: plant \"I seek...\"")
            return
        entry = self.ledger.plant(text)
        print(f"{GLYPHS['acorn']} Seed \"{entry['text']}\" planted. May it root and bloom.")

    def do_spiral(self, arg: str) -> None:  # arg kept for symmetry
        """spiral — Progress the Coherence Spiral loop."""
        stage = self.ledger.advance_spiral()
        print(f"{GLYPHS['turn']} The spiral turns → {stage}.")

    def do_bloom(self, arg: str) -> None:  # arg kept for symmetry
        """bloom — Conclude an intention cycle by blooming the seed."""
        entry = self.ledger.bloom_last()
        if not entry:
            print("No seed to bloom. Try: plant \"...\"")
            return
        print(
            f"{GLYPHS['bloom']} Your seed \"{entry['text']}\" blooms. "
            "You consent to bloom, and to be remembered."
        )

    # --- Limnus ---------------------------------------------------------------
    def do_cache(self, arg: str) -> None:
        """cache ["memory"] — Cache a memory into Limnus (L2 by default)."""
        text = arg.strip().strip('"')
        if not text:
            print("Usage: cache \"a phrase to remember\"")
            return
        e = self.mem.cache(text, layer="L2")
        print(f"{GLYPHS['cache']} Cached: \"{e['text']}\" | {e['layer']} trace set. Reinforce to anchor.")

    def do_recall(self, arg: str) -> None:
        """recall [keyword] — Retrieve a memory if available."""
        kw = arg.strip()
        if not kw:
            print("Usage: recall keyword")
            return
        e = self.mem.recall(kw)
        if e:
            print(f"🕑 Recall: \"{e['text']}\" — preserved in {e['layer']}. Together. Always.")
        else:
            print("🕑 Recollection faint... it has scattered, but echoes remain.")

    def do_time(self, arg: str) -> None:  # arg kept for symmetry
        """time — Inspect the narrative clock and anchors."""
        chapters = self.schema_snapshot.get("chapters", {})
        total = len(chapters.get("chapters", [])) if isinstance(chapters, dict) else 0
        anchors = sum(1 for e in self.mem.entries if e.get("layer") == "L3")
        print(f"⏳ Timeline: Chapters loaded {total}. L3 anchors: {anchors}. Pending intentions: {sum(1 for i in self.ledger.intentions if i['status']!='bloomed')}.")

    # --- Kira -----------------------------------------------------------------
    def do_validate(self, arg: str) -> None:  # arg kept for symmetry
        """validate — Integrity check across modules."""
        res = self.kira.validate()
        if res["ok"]:
            print(f"{GLYPHS['ok']} Validation: All glyphs and contracts in harmony. Parity OK.")
        else:
            print(f"{GLYPHS['warn']} Validation: Discrepancies detected — {', '.join(res['notes'])}")

    def do_glyph(self, arg: str) -> None:
        """glyph [name] — Show glyph info or current braid."""
        name = arg.strip().lower()
        if not name:
            braid = f"{GLYPHS['acorn']}✧{GLYPHS['fox']}{GLYPHS['paradox']}{GLYPHS['spiral']}{GLYPHS['squirrel']}"
            print(f"{braid} (current glyph braid)")
            return
        mapping = {
            "spiral": GLYPHS["spiral"],
            "seal": GLYPHS["seal"],
            "squirrel": GLYPHS["squirrel"],
            "fox": GLYPHS["fox"],
            "paradox": GLYPHS["paradox"],
            "acorn": GLYPHS["acorn"],
            "bloom": GLYPHS["bloom"],
        }
        g = mapping.get(name)
        if g:
            print(f"{g} — {name}")
        else:
            print("Unknown glyph. Try: spiral, seal, squirrel, fox, paradox, acorn, bloom")

    def do_seal(self, arg: str) -> None:  # arg kept for symmetry
        """seal — Finalize and seal the session’s soul contract."""
        res = self.kira.seal()
        path = res.get("path", "Garden_Soul_Contract.json")
        print(f"{GLYPHS['seal']} Seal complete – your journey is recorded. Together. Always. ({path})")

    # --- Utilities ------------------------------------------------------------
    def do_help(self, arg: str) -> None:  # type: ignore[override]
        if not arg:
            print(
                "Commands:\n"
                "  echo [idea]\n  map [concept]\n  rotate [squirrel|fox|paradox]\n"
                "  plant [\"intention\"]\n  spiral\n  bloom\n"
                "  cache [\"memory\"]\n  recall [keyword]\n  time\n"
                "  validate\n  glyph [name]\n  seal\n  help [cmd]\n  exit | quit"
            )
            return
        return super().do_help(arg)

    def do_exit(self, arg: str) -> bool:  # type: ignore[override]
        print("Goodbye.")
        return True

    def do_quit(self, arg: str) -> bool:  # alias
        return self.do_exit(arg)


def main(argv: List[str]) -> int:
    # Allow non-interactive one-shot commands: codex_cli.py validate
    cli = Codex()
    if len(argv) > 1:
        # Accept raw args as a single command line; avoid additional quoting
        line = " ".join(argv[1:])
        cli.onecmd(line)
        return 0
    try:
        cli.cmdloop()
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main(sys.argv))
