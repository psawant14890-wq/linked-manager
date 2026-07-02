"""
Feature: Job Opportunity Tracker

Extracts structured fields from a recruiter message via GPT-4o.
The Pydantic schema enforces exactly what the model must return, and the
standard validate-retry-once logic in llm_client applies.

Only called for messages already classified as `recruiter` -- running it
on every message would be expensive and pointless.
"""

import logging

from pydantic import BaseModel, ConfigDict, Field

from app.core.llm_client import LLMValidationError, get_structured_completion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are parsing a LinkedIn recruiter message to extract structured job opportunity data.

Extract only what is explicitly stated or clearly implied. Use null for anything not mentioned.
remote_policy must be one of: "remote", "hybrid", "onsite", or null.
seniority should be a short label like "junior", "mid", "senior", "staff", "principal", "director", or null.
is_genuine: false if this reads like a mass-blast template with no real role details; true if it describes a specific role.
"""


class JobExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company: str | None = Field(default=None, description="Company name offering the role")
    role_title: str | None = Field(default=None, description="Job title or role name")
    seniority: str | None = Field(default=None, description="Seniority level of the role")
    location: str | None = Field(default=None, description="Office location(s) if mentioned")
    remote_policy: str | None = Field(default=None, description="remote | hybrid | onsite | null")
    salary_range: str | None = Field(default=None, description="Salary/compensation if mentioned, raw string")
    is_genuine: bool = Field(description="True if this describes a specific real opportunity")


async def extract_job_opportunity(*, sender_name: str, content: str) -> JobExtractionResult | None:
    """
    Returns a JobExtractionResult or None if extraction fails validation twice.
    Callers should skip persisting if is_genuine=False or result is None.
    """
    user_prompt = f"Recruiter: {sender_name}\n\nMessage:\n{content}"

    try:
        return await get_structured_completion(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema=JobExtractionResult,
            temperature=0.1,
        )
    except LLMValidationError as exc:
        logger.error("Job extraction failed validation for message from %s: %s", sender_name, exc)
        return None
