from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, Optional

import inngest

from app.services.chat_service import chat_completion


inngest_client = inngest.Inngest(
    app_id="learninngest_backend",
    logger=logging.getLogger("uvicorn"),
)


CHAT_RESULTS: Dict[str, Dict[str, Any]] = {}


def new_request_id() -> str:
    return uuid.uuid4().hex


def set_pending(request_id: str) -> None:
    CHAT_RESULTS[request_id] = {"status": "pending"}


def set_done(request_id: str, content: str) -> None:
    CHAT_RESULTS[request_id] = {"status": "done", "content": content}


def set_error(request_id: str, error: str) -> None:
    CHAT_RESULTS[request_id] = {"status": "error", "error": error}


def get_result(request_id: str) -> Optional[Dict[str, Any]]:
    return CHAT_RESULTS.get(request_id)


@inngest_client.create_function(
    fn_id="chat_worker",
    trigger=inngest.TriggerEvent(event="app/chat.requested"),
)
async def chat_worker(ctx: inngest.Context) -> str:
    data = getattr(ctx.event, "data", {}) or {}

    request_id = str(data.get("request_id", "")).strip()
    query = str(data.get("query", "")).strip()
    temperature = data.get("temperature")
    max_tokens = data.get("max_tokens")
    clean = bool(data.get("clean", True))

    if not request_id:
        request_id = new_request_id()

    try:
        if not query:
            raise ValueError("Missing 'query'")

        content = chat_completion(
            query=query,
            temperature=temperature,
            max_tokens=max_tokens,
            clean=clean,
        )
        set_done(request_id, content)
        return "done"
    except Exception as e:
        set_error(request_id, str(e))
        return "error"
