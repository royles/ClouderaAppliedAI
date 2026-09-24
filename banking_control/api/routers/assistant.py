from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from banking_control.api.deps import get_db_connection, get_tool_engine
from banking_control.api.sse import SSE_HEADERS
from banking_control.assistant.stream import stream_assistant_events
from banking_control.assistant.tools import bedrock_tool_definitions
from banking_control.tools.engine import ControlToolEngine

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


@router.get("/tools")
def list_assistant_tools() -> list[dict[str, Any]]:
    return bedrock_tool_definitions()


@router.post("/chat/stream")
def chat_stream(
    body: ChatRequest,
    conn: Any = Depends(get_db_connection),
    engine: ControlToolEngine = Depends(get_tool_engine),
) -> StreamingResponse:
    def event_gen():
        try:
            yield from stream_assistant_events(conn, engine, message=body.message)
        finally:
            conn.close()

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
