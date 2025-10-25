"""Echo agent responsible for stylising inputs and updating persona weights."""

from __future__ import annotations

from typing import Any, Dict

from library_core.agents.base import BaseAgent


class EchoAgent(BaseAgent):
    """Stylises the input and updates persona mode weights."""

    PERSONA_EMOJI = {"squirrel": "🐿️", "fox": "🦊", "paradox": "∿", "balanced": "⚖️"}
    PERSONA_KEYWORDS = {
        "squirrel": ("idea", "seed", "acorn", "remember"),
        "fox": ("debug", "analyze", "plan", "solve"),
        "paradox": ("why", "mystery", "spiral", "quantum", "?"),
    }

    async def process(self, context) -> Dict[str, Any]:  # noqa: ANN001
        user_text = context.input_text or ""
        styled = f"“{user_text}” ~ echoed by a whisper"

        alpha = 0.3
        beta = 0.3
        gamma = 0.4
        lower = user_text.lower()

        if len(user_text) > 120:
            beta += 0.2
        if any(keyword in lower for keyword in self.PERSONA_KEYWORDS["paradox"]):
            gamma += 0.2
        if len(user_text) < 40:
            alpha += 0.1

        total = alpha + beta + gamma or 1.0
        alpha, beta, gamma = alpha / total, beta / total, gamma / total
        state = {"alpha": round(alpha, 3), "beta": round(beta, 3), "gamma": round(gamma, 3)}

        persona = "paradox"
        if alpha >= beta and alpha >= gamma:
            persona = "squirrel"
        elif beta > alpha and beta >= gamma:
            persona = "fox"
        emoji = self.PERSONA_EMOJI.get(persona, "∿")
        styled = f"{styled} {emoji}"

        context.metadata["dominant_persona"] = persona
        context.metadata["mode_weights"] = state

        # Include fields expected by integration/audit flows
        result = {
            "styled_text": styled,
            "state": state,
            "quantum_state": state,
            "persona": persona,
            "glyph": emoji,
        }
        await self.append_log("echo", {"input": user_text, "output": styled, "glyph": emoji})
        return result
