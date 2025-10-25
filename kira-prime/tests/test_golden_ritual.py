import json
import uuid
from datetime import datetime, timezone

from pipeline.intent_parser import IntentParser
from pipeline.dispatcher_enhanced import (
    DispatcherConfig,
    EnhancedMRPDispatcher,
    PipelineContext,
)


def test_golden_ritual_progression():
    fixture_path = "tests/fixtures/golden/ritual_progression.json"
    data = json.loads(open(fixture_path, "r", encoding="utf-8").read())

    workspace = f"golden-ritual-{uuid.uuid4().hex[:6]}"
    parser = IntentParser()
    dispatcher = EnhancedMRPDispatcher(workspace, DispatcherConfig())

    last_cycle = 0
    for step in data["steps"]:
        user_text = step["input"]
        intent = parser.parse(user_text)
        ctx = PipelineContext(
            input_text=user_text,
            user_id="golden-user",
            workspace_id=workspace,
            intent=intent,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        result = __import__("asyncio").get_event_loop().run_until_complete(dispatcher.dispatch(ctx))

        ritual = result.get("ritual", {})
        stage = ritual.get("stage")
        assert stage == step["expect_stage"], f"stage mismatch for '{user_text}': {stage} != {step['expect_stage']}"

        # Kira validation should pass at each step
        kira = result.get("validation", {})
        assert kira.get("passed") is True

        cycle = ritual.get("cycle", 0)
        # On explicit cycle start, cycle should increase
        if user_text.strip().lower() in {"begin"}:
            assert cycle > last_cycle
        last_cycle = cycle

    # Final snapshot expectations
    final = result  # from last loop iteration
    garden = final.get("ritual", {})
    assert garden.get("consent_count", 0) >= data["final_expectations"]["min_consents"]
