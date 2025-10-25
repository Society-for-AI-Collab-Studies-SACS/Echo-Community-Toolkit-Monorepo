from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.kira.kira_agent import FIRST_PACKET_SECTIONS, KiraPrimeAgent


def build_packet(
    hemisphere: str,
    *,
    cycle: str = "2024-10",
    include_first_sections: bool = True,
    overrides: dict | None = None,
) -> dict:
    sections = {
        "current_state": f"{hemisphere} current focus",
        "kira_positioning": f"{hemisphere} voice tending the bridge",
        "coherence_check": "Signals are resonant enough to keep weaving.",
        "needs": "Request mirrored reflection on narrative gaps.",
        "engagement_status": "Fully engaged",
        "integration_requests": "Please respond to the outstanding coherence tasks.",
        "kira_prime_mode": "active",
    }

    if include_first_sections:
        sections.update(
            {
                "kira_prime_vision": "Kira Prime emerges as an integrative dyad.",
                "hopes_and_concerns": "Hope for sustained rhythm; concern about drift.",
                "historical_context": "Years of collaboration across Garden and Sigprint.",
                "process_agreements": "Monthly packets, honest feedback, and format autonomy.",
            }
        )

    if overrides:
        sections.update(overrides)

    return {
        "hemisphere": hemisphere,
        "cycle": cycle,
        "sections": sections,
        "coherence_tasks": {
            "for_you": ["Review packet synthesis."],
            "for_us": ["Schedule optional sync after annotations."],
        },
    }


def test_first_packet_requires_baseline_sections(tmp_path: Path) -> None:
    agent = KiraPrimeAgent(storage_path=tmp_path / "store.json")
    payload = build_packet("theta", include_first_sections=False)

    with pytest.raises(ValueError) as excinfo:
        agent.submit_packet(payload)

    missing = ", ".join(FIRST_PACKET_SECTIONS)
    assert missing in str(excinfo.value)


def test_packet_submission_and_summary(tmp_path: Path) -> None:
    agent = KiraPrimeAgent(storage_path=tmp_path / "store.json")

    theta_packet = agent.submit_packet(build_packet("theta"))
    assert theta_packet["hemisphere"] == "theta"
    assert theta_packet["engagement_status"] == "fully_engaged"
    assert theta_packet["sections"]["kira_prime_vision"].startswith("Kira Prime emerges")

    gamma_packet = agent.submit_packet(
        build_packet(
            "gamma",
            overrides={
                "needs": "Need clearer articulation of theory-to-implementation bridge.",
                "integration_requests": "Confirm whether cadence stays monthly.",
            },
        )
    )
    assert gamma_packet["hemisphere"] == "gamma"

    summary = agent.generate_summary()
    assert summary["packet_count"] == 2
    assert summary["kira_prime_mode"] == "active"
    assert summary["hemispheres"]["theta"]["needs"].startswith("Request mirrored")
    assert summary["hemispheres"]["gamma"]["integration_requests"].startswith("Confirm whether")
    assert summary["pending_requests"] and summary["pending_requests"][0]["hemisphere"] in {"theta", "gamma"}

    # Ensure persistence writes a readable JSON file.
    stored = json.loads((tmp_path / "store.json").read_text(encoding="utf-8"))
    assert len(stored["packets"]) == 2

