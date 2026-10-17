from ..base import TtsProfile

PROFILE = TtsProfile(
    id="voxtral-tts",
    label="Voxtral TTS 4B",
    repo="mlx-community/Voxtral-4B-TTS-2603-mlx-bf16",
    engine="generic",
    aliases=("voxtral",),
    ram_gb=12,
    disk_gb=9,
    quality="Natural",
    note="Mistral's 4B TTS, 20 voices across 9 languages. Non-commercial license.",
    params=dict(
        use_ref=False,
        generate_kwargs=dict(voice="casual_female"),
    ),
    cue_style=None,
    soft_limit=220,
    first_chunk_soft_limit=100,
    batch_target_chars=320,
    batch_max_chars=420,
)
