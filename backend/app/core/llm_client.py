"""
Shared LLM client wrapper used by every AI service module.

Two separate concerns live here, deliberately using two different backends:

1. Chat/generation (`get_structured_completion`, `stream_completion`) --
   goes through the OpenAI SDK, but the SDK's base_url is configurable, so
   this transparently supports OpenAI OR any OpenAI-compatible provider
   (e.g. xAI's Grok API at https://api.x.ai/v1). Set OPENAI_BASE_URL and
   OPENAI_CHAT_MODEL in .env to switch providers -- no code changes needed.

2. Embeddings (`embed_text`, `embed_texts`) -- runs 100% locally via
   fastembed (ONNX runtime), independent of whichever chat provider is
   configured. This exists because xAI does not currently expose a public
   embeddings API, and keeps the whole embeddings path free of any
   external API cost regardless of which chat provider you use.
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_client = AsyncOpenAI(
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL or None,  # None = OpenAI's default endpoint
)

T = TypeVar("T", bound=BaseModel)


class LLMValidationError(Exception):
    """Raised when the model's output fails schema validation twice in a row."""

    def __init__(self, raw_output: str, validation_error: str):
        self.raw_output = raw_output
        self.validation_error = validation_error
        super().__init__(f"LLM output failed validation after retry: {validation_error}")


async def get_structured_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    model: str | None = None,
    temperature: float = 0.3,
) -> T:
    """
    Calls the chat model asking for JSON matching `schema`, validates it,
    and retries once with a corrective message if validation fails.
    Raises LLMValidationError if it fails twice -- callers are expected to
    catch this and fall back to a manual-review state rather than crash.

    response_format={"type": "json_object"} is supported natively by both
    OpenAI and xAI's Grok models (grok-2-1212 and newer), so no branching
    is needed based on provider.
    """
    chat_model = model or settings.OPENAI_CHAT_MODEL
    schema_json = json.dumps(schema.model_json_schema(), indent=2)

    base_system = (
        f"{system_prompt}\n\n"
        "You must respond with ONLY a single valid JSON object, no markdown "
        "fences, no commentary, that conforms exactly to this JSON Schema:\n"
        f"{schema_json}"
    )

    messages = [
        {"role": "system", "content": base_system},
        {"role": "user", "content": user_prompt},
    ]

    last_error: ValidationError | None = None

    for attempt in range(2):  # initial attempt + 1 retry
        if attempt == 1 and last_error is not None:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response was invalid JSON or did not match the "
                        f"schema. Validation error: {last_error}. "
                        "Return ONLY corrected JSON matching the schema exactly."
                    ),
                }
            )

        response = await _client.chat.completions.create(
            model=chat_model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        raw_output = response.choices[0].message.content or "{}"

        try:
            parsed = json.loads(raw_output)
            return schema.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            logger.warning("LLM structured output validation failed (attempt %s): %s", attempt + 1, exc)
            continue

    raise LLMValidationError(raw_output=raw_output, validation_error=str(last_error))


async def stream_completion(
    *,
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    temperature: float = 0.7,
) -> AsyncIterator[str]:
    """Yields incremental text chunks from a streaming chat completion."""
    chat_model = model or settings.OPENAI_CHAT_MODEL

    stream = await _client.chat.completions.create(
        model=chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content if chunk.choices else None
        if delta:
            yield delta


# ---------------------------------------------------------------------------
# Local embeddings (fastembed / ONNX runtime) -- free, no API key required.
# ---------------------------------------------------------------------------

_embedding_model = None  # lazy-loaded singleton; loading downloads/caches the
                          # ONNX model on first use, then reuses it in-process


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from fastembed import TextEmbedding

        logger.info("Loading local embedding model %s (first call only)...", settings.EMBEDDING_MODEL_NAME)
        _embedding_model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)
    return _embedding_model


def _embed_sync(texts: list[str]) -> list[list[float]]:
    """fastembed's API is synchronous; called via asyncio.to_thread to avoid blocking the event loop."""
    model = _get_embedding_model()
    return [vec.tolist() for vec in model.embed(texts)]


async def embed_text(text: str) -> list[float]:
    """Returns a single embedding vector for `text`, computed locally."""
    import asyncio

    vectors = await asyncio.to_thread(_embed_sync, [text])
    return vectors[0]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embedding call -- used during import to embed many posts/connections at once."""
    import asyncio

    if not texts:
        return []
    return await asyncio.to_thread(_embed_sync, texts)
