from __future__ import annotations

import pytest

from pipeline.dispatcher import MRPDispatcher, PipelineContext
from pipeline.intent_parser import IntentParser
from pipeline.listener import DictationListener


@pytest.mark.asyncio
async def test_full_mrp_pipeline() -> None:
    workspace_id = "test-integration"
    user_id = "test-user"

    listener = DictationListener(workspace_id)
    parser = IntentParser()
    dispatcher = MRPDispatcher(workspace_id)

    test_input = "I want to brainstorm ideas for a new project"

    dictation = await listener.listen_text(test_input, user_id)
    intent = parser.parse(dictation.text)
    assert intent.intent_type in {"dictation", "ritual"}

    context = PipelineContext(
        input_text=dictation.text,
        user_id=user_id,
        workspace_id=workspace_id,
        intent=intent,
        timestamp=dictation.timestamp,
    )

    response = await dispatcher.dispatch(context)

    assert response["success"] is True
    assert response["ritual"]["stage"] in {"scatter", "witness", "plant", "tend", "harvest"}
    assert response["echo"]["persona"] == "squirrel"
    assert response["memory"]["cached"] is True
    assert response["validation"]["passed"] is True
