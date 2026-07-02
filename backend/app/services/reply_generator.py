"""
Feature 4 -- Reply Draft Generator.

Generates a contextual reply draft for a given inbox message, using the
user's bio_context to steer tone and relevance (e.g. "not interested in
sales pitches"). Output is always streamed and always a draft -- this
module has no concept of "sending," only generating text.
"""

from collections.abc import AsyncIterator

from app.core.llm_client import stream_completion

_SYSTEM_PROMPT = """You are drafting a reply to a LinkedIn message on behalf of the user.

Use the user's own context below to tailor tone, relevance, and boundaries.
Write a reply that sounds like a real professional person, not a corporate
bot -- concise, warm where appropriate, direct where needed.

This is a DRAFT ONLY. The user will review and send it manually themselves.
Do not include any meta-commentary about it being a draft in the reply text
itself -- just write the reply as if the user is about to send it.

User's context about themselves:
{bio_context}
"""


def stream_reply_draft(*, message_sender: str, message_content: str, bio_context: str) -> AsyncIterator[str]:
    system_prompt = _SYSTEM_PROMPT.format(bio_context=bio_context or "(no context provided)")
    user_prompt = f"Message from {message_sender}:\n\n{message_content}\n\nDraft a reply."
    return stream_completion(system_prompt=system_prompt, user_prompt=user_prompt, temperature=0.6)
