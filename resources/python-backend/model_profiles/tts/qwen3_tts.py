from ..base import TtsProfile

PROFILE = TtsProfile(
    id="qwen3-tts",
    label="Qwen3-TTS 4bit",
    repo="mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit",
    engine="qwen3",
    aliases=("qwen3_tts", "qwen3"),
    ram_gb=4,
    disk_gb=2,
    quality="Balanced",
    note="Best default for most Apple Silicon Macs",
    params=dict(temperature=0.9, top_k=50, top_p=1.0, repetition_penalty=1.05),
    cue_style=None,
    # Handles longer passages well.
    soft_limit=260,
    first_chunk_soft_limit=110,
    batch_target_chars=360,
    batch_max_chars=460,
)
