"""
Small helpers for shaping Server-Sent Events consistently across the
post-generation, reply-draft, and weekly-report streaming endpoints.
"""

import json
from collections.abc import AsyncIterator


def sse_event(event: str, data: dict | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


async def to_sse_stream(text_chunks: AsyncIterator[str]) -> AsyncIterator[str]:
    """
    Wraps a raw text-chunk async generator into a proper SSE stream:
    one `token` event per chunk, then a final `done` event.
    """
    full_text = ""
    async for chunk in text_chunks:
        full_text += chunk
        yield sse_event("token", {"text": chunk})
    yield sse_event("done", {"full_text": full_text})
