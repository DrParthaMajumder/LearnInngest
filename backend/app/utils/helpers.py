from __future__ import annotations

import os
import re
from typing import Optional


def env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value


def clean_text(text: str) -> str:
    t = text.strip()
    t = re.sub(r"```[\s\S]*?```", "", t)
    t = re.sub(r"^#{1,6}\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"\*\*(.*?)\*\*", r"\1", t)
    t = re.sub(r"\*(.*?)\*", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()
