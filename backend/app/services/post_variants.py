"""
Feature: Post Variant Generator

Generates 3 stylistic variants of a post (professional, casual, storytelling)
from the same raw input and style examples. Each variant is streamed
independently via SSE with a `variant_index` field so the frontend can
route tokens to the right column while all three stream in parallel.

The three streams are started concurrently with asyncio.gather so the
wall-clock time is approximately max(stream_1, stream_2, stream_3) rather
than their sum.
"""

import asyncio
from collections.abc import AsyncGenerator

from app.models.post import Post
from app.services.post_generator import _build_system_prompt

VARIANT_STYLES = [
    {
        "index": 0,
        "name": "professional",
        "instruction": "Write in a confident, polished professional tone. Clear structure, no fluff.",
    },
    {
        "index": 1,
        "name": "casual",
        "instruction": "Write conversationally, like you're talking to a colleague. Contractions fine, a little personality.",
    },
    {
        "index": 2,
        "name": "storytelling",
        "instruction": "Open with a micro-story or scene. Build to the point. Warmer, more personal.",
    },
]


async def _collect_variant(
    raw_input: str,
    style_examples: list[Post],
    style: dict,
) -> tuple[int, str]:
    """Runs one variant to completion and returns (index, full_text)."""
    from app.core.llm_client import stream_completion  # local to avoid circular

    system_prompt = _build_system_prompt(style_examples)
    user_prompt = (
        f"Raw material:\n{raw_input}\n\n"
        f"Style instruction: {style['instruction']}\n\n"
        "Write ONLY the post text. No preamble, no labels."
    )

    full = ""
    async for chunk in stream_completion(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.85):
        full += chunk
    return style["index"], full


async def generate_variants_concurrent(
    raw_input: str,
    style_examples: list[Post],
) -> AsyncGenerator[dict, None]:
    """
    Yields SSE-ready dicts as all three variants complete.
    Uses asyncio.gather so generation happens in parallel -- total latency
    is ~1x a single call rather than 3x.

    Yields:
      {"event": "variant_done", "index": 0|1|2, "name": str, "text": str}
      {"event": "all_done"}
    """
    tasks = [_collect_variant(raw_input, style_examples, style) for style in VARIANT_STYLES]
    results = await asyncio.gather(*tasks)

    style_map = {s["index"]: s["name"] for s in VARIANT_STYLES}
    for index, full_text in sorted(results, key=lambda r: r[0]):
        yield {"event": "variant_done", "index": index, "name": style_map[index], "text": full_text}

    yield {"event": "all_done"}
