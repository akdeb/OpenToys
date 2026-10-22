from typing import Optional

from ..base import TtsProfile
from . import (
    breeze_blue,
    chatterbox_multilingual_v3,
    chatterbox_turbo,
    fish_drama3,
    higgs_audio_v3,
    irodori_tts,
    omnivoice,
    phonon,
    qwen3_tts,
    rumik_oss,
    voxtral_tts,
)

DEFAULT_ID = qwen3_tts.PROFILE.id

# Order here is the order users see in the model picker.
TTS_PROFILES: tuple[TtsProfile, ...] = (
    qwen3_tts.PROFILE,
    chatterbox_turbo.PROFILE,
    breeze_blue.PROFILE,
    chatterbox_multilingual_v3.PROFILE,
    omnivoice.PROFILE,
    voxtral_tts.PROFILE,
    higgs_audio_v3.PROFILE,
    fish_drama3.PROFILE,
    rumik_oss.PROFILE,
    irodori_tts.PROFILE,
    phonon.PROFILE,
)

_BY_ALIAS = {
    name: p for p in TTS_PROFILES for name in (p.id, *p.aliases)
}


def get_tts_profile(backend: Optional[str]) -> TtsProfile:
    """Resolve an id or alias to a profile; unknown or empty falls back to the default."""
    value = (backend or "").strip().lower()
    return _BY_ALIAS.get(value) or _BY_ALIAS[DEFAULT_ID]
