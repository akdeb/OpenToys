import re
from typing import Literal, Optional, Sequence

from model_profiles.base import CUE_DELIMS, DEFAULT_CUES

CueStyle = Literal["brackets", "parentheses", "angle"]


def sanitize_spoken_text(
    text: str,
    *,
    allow_paralinguistic: bool = True,
    cue_style: CueStyle = "brackets",
    cues: Optional[Sequence[str]] = None,
) -> str:
    """Strip markdown and any paralinguistic cue the active TTS model can't voice.

    `cues` is the model's allowed set and `cue_style` its delimiter. Cues written in
    another delimiter are rewritten into the model's own; anything else is dropped.
    """
    if not text:
        return text

    allowed_cues = set(cues if cues is not None else DEFAULT_CUES)
    # Cue words the LLM might emit in any delimiter, so they can be converted or removed.
    known = "|".join(sorted((re.escape(c) for c in allowed_cues | set(DEFAULT_CUES)), key=len, reverse=True))
    open_, close = CUE_DELIMS.get(cue_style, CUE_DELIMS["brackets"])

    text = text.replace("`", "")
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("__", "")
    text = text.replace("_", "")

    if allow_paralinguistic:
        def keep_or_drop(match: re.Match) -> str:
            tag_norm = " ".join((match.group(1) or "").strip().lower().split())
            if tag_norm in allowed_cues:
                return f"{open_}{tag_norm}{close}"
            return ""

        text = re.sub(r"\[([^\]]+)\]", keep_or_drop, text)
        text = re.sub(rf"\(({known})\)", keep_or_drop, text, flags=re.IGNORECASE)
        text = re.sub(rf"<({known})>", keep_or_drop, text, flags=re.IGNORECASE)
    else:
        text = re.sub(r"\[[^\]]+\]", "", text)
        text = re.sub(rf"\(({known})\)", "", text, flags=re.IGNORECASE)
        text = re.sub(rf"<({known})>", "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s{2,}", " ", text).strip()
    return text
