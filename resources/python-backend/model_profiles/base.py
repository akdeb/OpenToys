"""Profile dataclasses: one profile file per model, grouped by kind.

A profile holds everything that changes when the user swaps a model: the repo to
download, engine tuning, and the prompt scheme the LLM is given so that its output
suits that model. To add a model, drop a file next to its siblings and register it
in the kind's __init__.py. Nothing else in the backend branches on a model name.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

CueStyle = Literal["brackets", "parentheses", "angle"]

CUE_DELIMS: dict[str, tuple[str, str]] = {
    "brackets": ("[", "]"),
    "parentheses": ("(", ")"),
    "angle": ("<", ">"),
}

DEFAULT_CUES: tuple[str, ...] = (
    "laugh", "chuckle", "sigh", "gasp", "cough", "clear throat", "sniff", "groan", "shush",
)


def cue_prompts(style: CueStyle, cues: tuple[str, ...]) -> tuple[str, str]:
    """Build the (expressivity, conversation) prompt pair for a cue syntax."""
    open_, close = CUE_DELIMS[style]
    words = {"brackets": "brackets", "parentheses": "parentheses", "angle": "angle brackets"}[style]
    listed = ", ".join(f"{open_}{c}{close}" for c in cues)
    first, second = cues[0], cues[min(1, len(cues) - 1)]
    expressivity = (
        f"To add expressivity, you may occasionally use ONLY these paralinguistic cues in {words}: "
        f"{listed}. Use only these cues naturally in context to enhance the conversational flow. "
        f"Examples: {open_}{first}{close} That is funny. {open_}{second}{close} That was a long day."
    )
    conversation = f"If you use paralinguistic cues, use ONLY the {words} tags from the allowed list."
    return expressivity, conversation


@dataclass(frozen=True)
class TtsProfile:
    id: str
    label: str
    repo: str
    engine: str  # key into the engine classes in tts.py
    aliases: tuple[str, ...] = ()
    ram_gb: int = 0
    disk_gb: int = 0
    quality: str = ""
    note: str = ""
    # Constructor kwargs for the engine (temperature, top_k, ...).
    params: dict = field(default_factory=dict)

    # Paralinguistic cues the model can voice, e.g. [laugh] or (laugh). None means
    # the model reads tags aloud, so the LLM must not write any.
    cue_style: Optional[CueStyle] = None
    cues: tuple[str, ...] = DEFAULT_CUES
    # Prompt scheme: appended to every system prompt / to conversation mode.
    expressivity_prompt: str = ""
    conversation_prompt: str = (
        "Do not use any paralinguistic cues or tags (no bracketed cues like [laugh])."
    )
    # Language the model speaks, when it is not general English.
    language_prompt: str = ""

    # Text chunking tuned to how much text the model handles well per call.
    soft_limit: int = 140
    first_chunk_soft_limit: int = 90
    batch_target_chars: int = 240
    batch_max_chars: int = 320

    @property
    def allows_cues(self) -> bool:
        return self.cue_style is not None


@dataclass(frozen=True)
class SttProfile:
    id: str
    label: str
    repo: str
    aliases: tuple[str, ...] = ()
    ram_gb: int = 0
    disk_gb: int = 0
    note: str = ""


@dataclass(frozen=True)
class LlmProfile:
    id: str
    label: str
    # A model belongs to this family when any fragment appears in its repo id.
    match: tuple[str, ...] = ()
    # Extra system-prompt text for this family (empty for most).
    prompt_addendum: str = ""
    note: str = ""


@dataclass(frozen=True)
class RealtimeProfile:
    id: str
    label: str
    repo: str
    aliases: tuple[str, ...] = ()
    note: str = ""
    # Realtime (speech-to-speech) models replace the STT -> LLM -> TTS chain, so
    # they carry their own system prompt scheme.
    prompt_scheme: str = ""
