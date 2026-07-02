"""
Feature 3 -- AI Post Generator.

Builds a prompt that includes 2-3 of the user's own past posts (retrieved
via embeddings.retrieve_similar_posts) as few-shot style examples, then
streams a new post via SSE so it appears word-by-word in the UI.
"""

from collections.abc import AsyncIterator

from app.core.llm_client import get_structured_completion, stream_completion
from app.models.post import Post
from app.schemas.post import HashtagSuggestion

_SYSTEM_PROMPT_TEMPLATE = """You are helping a LinkedIn user draft a new post in their own authentic voice.

Below are {n} examples of posts this exact user has written before. Study their
sentence length, formatting habits (line breaks, emoji use or lack thereof,
how they open and close posts), and tone. Match that voice closely -- do not
default to generic "LinkedIn guru" style with excessive hype or emoji unless
their own examples show that style.

--- USER'S PAST POSTS (style reference) ---
{examples}
--- END EXAMPLES ---

Write ONLY the new post text. No preamble, no explanation, no markdown fences.
"""


def _build_system_prompt(style_examples: list[Post]) -> str:
    if not style_examples:
        examples_block = "(No past posts available -- write in a clear, professional, understated LinkedIn voice.)"
        n = 0
    else:
        examples_block = "\n\n".join(f"Example {i + 1}:\n{p.content}" for i, p in enumerate(style_examples))
        n = len(style_examples)
    return _SYSTEM_PROMPT_TEMPLATE.format(n=n, examples=examples_block)


def stream_post_generation(
    *, raw_input: str, tone_hint: str | None, style_examples: list[Post]
) -> AsyncIterator[str]:
    system_prompt = _build_system_prompt(style_examples)
    user_prompt = f"Raw material to turn into a post:\n{raw_input}"
    if tone_hint:
        user_prompt += f"\n\nAdditional steering: {tone_hint}"

    return stream_completion(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.8)


async def suggest_hashtags(post_content: str) -> list[str]:
    """Runs after the post is fully generated (frontend calls this once streaming completes)."""
    try:
        result = await get_structured_completion(
            system_prompt=(
                "Suggest 3-5 relevant, non-generic LinkedIn hashtags for this post. "
                "Avoid overly broad tags like #business or #success."
            ),
            user_prompt=post_content,
            schema=HashtagSuggestion,
            temperature=0.4,
        )
        return result.hashtags
    except Exception:  # noqa: BLE001 -- hashtags are a nice-to-have, never block the post on this
        return []
