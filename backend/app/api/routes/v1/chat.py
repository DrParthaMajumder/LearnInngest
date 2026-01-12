from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import inngest

from app.inngest_app import get_result, inngest_client, new_request_id, set_pending

router = APIRouter()


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, examples=["What is the capital of France?"])
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=200, ge=1)
    clean: bool = True


class ChatEnqueueResponse(BaseModel):
    request_id: str


class ChatResultResponse(BaseModel):
    status: Literal["pending", "done", "error"]
    content: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/chat",
    response_model=ChatEnqueueResponse,
)
def chat(req: ChatRequest) -> ChatEnqueueResponse:
    try:
        request_id = new_request_id()
        set_pending(request_id)

        inngest_client.send_sync(
            inngest.Event(
                name="app/chat.requested",
                id=request_id,
                data={
                    "request_id": request_id,
                    "query": req.query,
                    "temperature": req.temperature,
                    "max_tokens": req.max_tokens,
                    "clean": req.clean,
                },
            )
        )

        return ChatEnqueueResponse(request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/chat/result/{request_id}", response_model=ChatResultResponse)
def chat_result(request_id: str) -> ChatResultResponse:
    r = get_result(request_id)
    if not r:
        raise HTTPException(status_code=404, detail="request_id not found")
    return ChatResultResponse(**r)
