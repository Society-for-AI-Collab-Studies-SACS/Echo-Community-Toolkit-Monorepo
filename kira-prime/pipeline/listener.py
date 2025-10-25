from __future__ import annotations

"""Simple listener that reads a line of input and dispatches it.

Usage:
  python -m pipeline.listener "free text or 'kira validate'" 
"""
import sys
from interface.dispatcher import dispatch_freeform, dispatch_explicit


def main(argv: list[str]) -> None:
    if len(argv) < 2:
        print("Provide input text or explicit 'agent command ...'")
        return
    text = " ".join(argv[1:]).strip()
    parts = text.split()
    if len(parts) >= 2 and parts[0].lower() in {"garden", "echo", "limnus", "kira"}:
        agent, command, *args = parts
        res = dispatch_explicit(agent.lower(), command.lower(), *args)
        print(res)
    else:
        res = dispatch_freeform(text)
        print(res)


if __name__ == "__main__":
    main(sys.argv)

