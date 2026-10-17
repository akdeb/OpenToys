from ..base import TtsProfile

PROFILE = TtsProfile(
    id="chatterbox-multilingual-v3",
    label="Chatterbox Multilingual v3",
    repo="mlx-community/chatterbox-multilingual-v3",
    engine="generic",
    aliases=("chatterbox-v3", "chatterbox-multilingual"),
    ram_gb=6,
    disk_gb=4,
    quality="Expressive",
    note="Chatterbox in 23 languages, MIT license.",
    params=dict(
        ref_needs_text=False,
        generate_kwargs=dict(lang_code="en"),
    ),
    cue_style=None,
    soft_limit=140,
    first_chunk_soft_limit=90,
    batch_target_chars=240,
    batch_max_chars=320,
)
