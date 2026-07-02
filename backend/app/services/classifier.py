"""
Feature 2 -- Smart Inbox classification.

Each message is classified into spam/genuine/recruiter/collaboration/general
via GPT-4o with a Pydantic-enforced output schema (see core/llm_client.py
for the validate-retry-once-then-fallback logic). On top of the LLM's
category, we compute a deterministic priority score so sorting is stable
and explainable rather than purely vibes-based from the model.
"""

import logging

from app.core.llm_client import LLMValidationError, get_structured_completion
from app.models.message import MessageCategory
from app.schemas.message import MessageClassification

logger = logging.getLogger(__name__)

# Deterministic base score per category -- this is what actually drives
# sort order. The LLM's relevance_score only nudges within a category so
# a single weird LLM call can't, say, rank a spam message above a recruiter.
_BASE_SCORE = {
    MessageCategory.RECRUITER: 75.0,
    MessageCategory.COLLABORATION: 55.0,
    MessageCategory.GENUINE: 40.0,
    MessageCategory.GENERAL: 20.0,
    MessageCategory.SPAM: 0.0,
    MessageCategory.NEEDS_REVIEW: 30.0,
}

_RELEVANCE_NUDGE_RANGE = 15.0  # LLM relevance_score (0-1) can shift score by up to +/-this within its band

_SYSTEM_PROMPT = """You are an inbox triage assistant for a LinkedIn power user.
Classify each incoming LinkedIn message into exactly one category:

- recruiter: outreach about a job opportunity, role, or hiring process
- collaboration: proposals to collaborate, partner, speak, write, or work together (not a job offer)
- genuine: a real, personal message from a real connection (catching up, asking a real question, congratulating, etc.)
- general: generic networking, non-personalized template-y messages, low-effort outreach that isn't sales/spam
- spam: cold sales pitches, course/service ads, obvious bot messages, scams

Also provide:
- relevance_score (0.0-1.0): within its category, how important/actionable is this specific message
- summary: a single tight sentence summarizing what the sender wants
- reasoning: a short justification for the category you chose
"""


async def classify_message(*, sender_name: str, content: str) -> MessageClassification | None:
    """
    Returns a validated MessageClassification, or None if the LLM failed
    validation twice in a row (caller should then flag the message as
    NEEDS_REVIEW rather than crash the import).
    """
    user_prompt = f"Sender: {sender_name}\n\nMessage:\n{content}"

    try:
        return await get_structured_completion(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=MessageClassification,
            temperature=0.1,
        )
    except LLMValidationError as exc:
        logger.error("Classification failed validation twice for message from %s: %s", sender_name, exc)
        return None


def compute_priority_score(category: MessageCategory, relevance_score: float) -> float:
    """Deterministic base score (by category) + a bounded nudge from the LLM's relevance judgment."""
    base = _BASE_SCORE.get(category, _BASE_SCORE[MessageCategory.NEEDS_REVIEW])
    nudge = (relevance_score - 0.5) * 2 * _RELEVANCE_NUDGE_RANGE  # maps [0,1] -> [-range, +range]
    return round(base + nudge, 2)
