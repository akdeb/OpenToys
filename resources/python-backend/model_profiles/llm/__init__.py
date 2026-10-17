from typing import Optional

from ..base import LlmProfile
from . import default, gemma4, gpt_oss, llama, ministral, muse_glimmer, qwen3

LLM_PROFILES: tuple[LlmProfile, ...] = (
    gemma4.PROFILE,
    qwen3.PROFILE,
    muse_glimmer.PROFILE,
    ministral.PROFILE,
    llama.PROFILE,
    gpt_oss.PROFILE,
)


def get_llm_profile(repo_id: Optional[str]) -> LlmProfile:
    """Pick the family profile for a repo id, e.g. mlx-community/Qwen3-4B-4bit."""
    value = (repo_id or "").lower()
    for profile in LLM_PROFILES:
        if any(fragment in value for fragment in profile.match):
            return profile
    return default.PROFILE
