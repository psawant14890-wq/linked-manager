"""
Feature 6 -- Weekly AI Activity Report.

On-demand only (button trigger), since without a live LinkedIn data feed
there's nothing for a cron job to poll. Synthesizes inbox + post stats
for the period into a short, conversational streamed report.
"""

from collections.abc import AsyncIterator
from datetime import datetime

from app.core.llm_client import stream_completion

_SYSTEM_PROMPT = """You are a sharp, friendly LinkedIn activity analyst writing a short weekly
summary for the user. Use a conversational, direct tone -- like a smart
colleague giving you the highlights over coffee, not a corporate report.

Cover, briefly:
1. Inbox activity (volume, and how many were high-priority recruiter/collaboration messages)
2. Post performance (what was published, how it did)
3. 2-3 specific, actionable suggestions for next week

Keep it tight -- a few short paragraphs, not a wall of text. No headers or
bullet-heavy formatting; write it as flowing prose someone would actually
enjoy reading.
"""


def stream_weekly_report(
    *,
    period_start: datetime,
    period_end: datetime,
    message_count: int,
    high_priority_count: int,
    category_counts: dict[str, int],
    posts_published: int,
    avg_views: float | None,
    top_post_excerpt: str | None,
) -> AsyncIterator[str]:
    stats_block = f"""
Period: {period_start.date()} to {period_end.date()}
Total messages received: {message_count}
High-priority messages (recruiter/collaboration): {high_priority_count}
Category breakdown: {category_counts}
Posts published: {posts_published}
Average views per post: {avg_views if avg_views is not None else "N/A"}
Top performing post (excerpt): {top_post_excerpt or "N/A"}
"""
    return stream_completion(system_prompt=_SYSTEM_PROMPT, user_prompt=stats_block, temperature=0.7)
