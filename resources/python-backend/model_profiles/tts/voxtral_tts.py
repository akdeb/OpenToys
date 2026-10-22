from ..base import TtsProfile

_LANGS = {
    "ar": "Arabic", "de": "German", "es": "Spanish", "fr": "French", "hi": "Hindi",
    "it": "Italian", "nl": "Dutch", "pt": "Portuguese",
}
_GENDER = {"female": "F", "male": "M"}


def _label(voice_id: str) -> str:
    style, gender = voice_id.rsplit("_", 1)
    return f"{_LANGS.get(style, style.capitalize())} ({_GENDER[gender]})"


PRESET_VOICES = tuple(
    (v, _label(v))
    for v in (
        "casual_female", "casual_male", "cheerful_female", "neutral_female", "neutral_male",
        "ar_male", "de_female", "de_male", "es_female", "es_male", "fr_female", "fr_male",
        "hi_female", "hi_male", "it_female", "it_male", "nl_female", "nl_male",
        "pt_female", "pt_male",
    )
)

PROFILE = TtsProfile(
    id="voxtral-tts",
    label="Voxtral TTS 4B",
    repo="mlx-community/Voxtral-4B-TTS-2603-mlx-4bit",
    engine="generic",
    aliases=("voxtral",),
    ram_gb=5,
    disk_gb=3,
    quality="Natural",
    note="Mistral's 4B TTS, 20 voices across 9 languages. Non-commercial license.",
    params=dict(
        use_ref=False,
        generate_kwargs=dict(voice="casual_female"),
    ),
    voice_cloning=False,
    preset_voices=PRESET_VOICES,
    cue_style=None,
    soft_limit=220,
    first_chunk_soft_limit=100,
    batch_target_chars=320,
    batch_max_chars=420,
)
