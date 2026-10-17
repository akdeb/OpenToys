from typing import Optional

from ..base import SttProfile
from . import whisper_large_v3_turbo

DEFAULT_ID = whisper_large_v3_turbo.PROFILE.id

STT_PROFILES: tuple[SttProfile, ...] = (whisper_large_v3_turbo.PROFILE,)

_BY_ALIAS = {name: p for p in STT_PROFILES for name in (p.id, *p.aliases)}


def get_stt_profile(backend: Optional[str]) -> SttProfile:
    value = (backend or "").strip().lower()
    return _BY_ALIAS.get(value) or _BY_ALIAS[DEFAULT_ID]
