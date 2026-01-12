from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.utils.helpers import clean_text, env

load_dotenv()


def chat_completion(
    *,
    query: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    clean: bool = True,
) -> str:
    api_key = env("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    model = env("OPENROUTER_MODEL", "google/gemini-3-flash-preview") or "google/gemini-3-flash-preview"

    default_headers = {}
    site_url = env("OPENROUTER_SITE_URL")
    app_name = env("OPENROUTER_APP_NAME")
    if site_url:
        default_headers["HTTP-Referer"] = site_url
    if app_name:
        default_headers["X-Title"] = app_name

    llm = ChatOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        default_headers=default_headers or None,
    )

    if clean:
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Reply in plain text only. Be concise. Do not use markdown, code blocks, or bullet points unless explicitly asked.",
                ),
                ("human", "{query}"),
            ]
        )
        messages = prompt.format_messages(query=query)
    else:
        messages = [HumanMessage(content=query)]

    result = llm.invoke(messages)
    content = getattr(result, "content", None)
    if content is None:
        content = str(result)
    if not clean:
        return content

    return clean_text(content)
