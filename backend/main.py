from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import inngest.fast_api

from app.api.routes.v1.chat import router as chat_router
from app.inngest_app import chat_worker, inngest_client

app = FastAPI(title="OpenRouter LangChain Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],   # allows OPTIONS, POST, etc.
    allow_headers=["*"],
)

# Routers
app.include_router(chat_router, prefix="/api/v1", tags=["Chat"])

# Inngest endpoint (default: /api/inngest)
inngest.fast_api.serve(app, inngest_client, [chat_worker])

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
