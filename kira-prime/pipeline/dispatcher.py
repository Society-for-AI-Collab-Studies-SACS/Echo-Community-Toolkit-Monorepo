"""
Compatibility wrapper for dispatcher.

Provides a Dispatcher class with a dispatch_user_input method, delegating to
the core interface.dispatcher functions, while enforcing the
Garden → Echo → Limnus → Kira pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from agents.garden.garden_agent import GardenAgent
from agents.echo.echo_agent import EchoAgent
from agents.limnus.limnus_agent import LimnusAgent
from agents.kira.kira_agent import KiraAgent
from common.logger import Logger


@dataclass
class _Result:
    narrative: str
    status: str


class Dispatcher:
    def __init__(self) -> None:
        self.garden = GardenAgent(__import__('pathlib').Path(__file__).resolve().parents[1])
        self.echo = EchoAgent(__import__('pathlib').Path(__file__).resolve().parents[1])
        self.limnus = LimnusAgent(__import__('pathlib').Path(__file__).resolve().parents[1])
        self.kira = KiraAgent(__import__('pathlib').Path(__file__).resolve().parents[1])
        self.logger = Logger()

    def dispatch_user_input(self, user_text: str) -> Dict[str, Any]:
        # 1) Garden logs intention
        start_ref = self.garden.log(user_text)
        self.logger.log("Garden", "log", {"text": user_text, "ref": start_ref})
        # 2) Echo responds
        narrative = self.echo.say(user_text)
        self.logger.log("Echo", "say", {"text": user_text, "response": narrative})
        # 3) Limnus commits
        commit_ref = self.limnus.commit_block("input", {"text": user_text, "echo": narrative})
        self.logger.log("Limnus", "commit_block", {"hash": commit_ref})
        # 4) Kira validates
        status = self.kira.validate()
        self.logger.log("Kira", "validate", {"status": status})
        return {"narrative": narrative, "status": status}
