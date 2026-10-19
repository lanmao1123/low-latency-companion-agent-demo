from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

from .agent import CompanionAgent
from .memory import MemoryStore
from .schemas import ChatRequest
from .tools import TOOL_SCHEMAS

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
memory_store = MemoryStore(DATA_DIR / "long_term_memory.json")
agent = CompanionAgent(memory_store)


async def health(request: Request):
    return JSONResponse({"status": "ok", "service": "companion-agent-demo"})


async def list_tools(request: Request):
    return JSONResponse({"tools": TOOL_SCHEMAS})


async def chat_stream(request: Request):
    try:
        body = await request.json()
        payload = ChatRequest.model_validate(body)
    except (json.JSONDecodeError, ValidationError) as exc:
        return JSONResponse({"error": "invalid_request", "detail": str(exc)}, status_code=400)

    async def event_source():
        try:
            async for event in agent.chat_stream(
                user_id=payload.user_id,
                session_id=payload.session_id,
                query=payload.query,
                memory_top_k=payload.memory_top_k,
            ):
                yield f"event: {event['type']}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as exc:
            error = {"type": "error", "message": str(exc)}
            yield f"event: error\ndata: {json.dumps(error, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/v1/tools", list_tools, methods=["GET"]),
    Route("/v1/chat/stream", chat_stream, methods=["POST"]),
]

app = Starlette(routes=routes)
