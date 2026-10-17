from ..base import TtsProfile

PROFILE = TtsProfile(
    id="irodori-tts",
    label="Irodori-TTS v4.1 Small (Japanese)",
    repo="mlx-community/Irodori-TTS-v4.1-Small-8bit",
    engine="generic",
    aliases=("irodori",),
    ram_gb=3,
    disk_gb=1,
    quality="Japanese",
    note="Japanese-only flow-matching TTS with voice design.",
    params=dict(
        ref_needs_text=False,
        generate_kwargs=dict(
            instruct="明るくやさしい女性の声で、ゆっくり自然に読み上げてください。",
        ),
    ),
    cue_style=None,
    language_prompt="Respond only in natural, spoken Japanese, never in English or romaji.",
    soft_limit=80,
    first_chunk_soft_limit=50,
    batch_target_chars=120,
    batch_max_chars=160,
)
