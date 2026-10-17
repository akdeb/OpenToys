from ..base import TtsProfile

PROFILE = TtsProfile(
    id="higgs-audio-v3",
    label="Higgs Audio v3 4B",
    repo="bosonai/higgs-audio-v3-tts-4b",
    engine="generic",
    aliases=("higgs", "higgs-v3"),
    ram_gb=12,
    disk_gb=9,
    quality="Conversational",
    note="4B conversational TTS, 100 languages. Research and non-commercial license.",
    params=dict(
        generate_kwargs=dict(temperature=1.0, max_new_tokens=2048),
    ),
    # Higgs has its own control tokens (<|emotion:..|>, <|sfx:..|>); we keep the
    # LLM off them until their sanitiser rules are defined.
    cue_style=None,
    soft_limit=200,
    first_chunk_soft_limit=100,
    batch_target_chars=300,
    batch_max_chars=380,
)
