from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from banking_control.api.deps import get_db_connection, get_tool_engine
from banking_control.api.sse import SSE_HEADERS
from banking_control.assistant.router import answer_question_rules, starter_actions
from banking_control.assistant.stream import stream_assistant_events
from banking_control.assistant.tools import bedrock_tool_definitions
from banking_control.tools.engine import ControlToolEngine

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


@router.get("/tools")
def list_assistant_tools() -> list[dict[str, Any]]:
    return bedrock_tool_definitions()


@router.get("/starters")
def assistant_starters(
    conn: Any = Depends(get_db_connection),
) -> dict[str, Any]:
    """Preamble and grounded chips for the empty assistant state."""
    return {
        "answer": (
            "Ask about controls, alerts, exceptions, or audit activity. "
            "Shortcuts below use live warehouse data and update the dashboard without leaving this panel."
        ),
        "actions": starter_actions(conn),
    }


@router.post("/chat/stream")
def chat_stream(
    body: ChatRequest,
    conn: Any = Depends(get_db_connection),
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> StreamingResponse:
    def event_gen():
        yield from stream_assistant_events(conn, engine, message=body.message)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
