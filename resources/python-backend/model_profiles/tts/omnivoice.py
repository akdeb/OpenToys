from ..base import TtsProfile, cue_prompts

CUES = ("laughter", "sigh")
_EXPRESSIVITY, _CONVERSATION = cue_prompts("brackets", CUES)

PROFILE = TtsProfile(
    id="omnivoice",
    label="OmniVoice",
    repo="mlx-community/OmniVoice-bf16",
    engine="generic",
    aliases=("omni-voice",),
    ram_gb=4,
    disk_gb=2,
    quality="Multilingual",
    note="646+ languages with zero-shot voice cloning. Small and fast.",
    params=dict(
        ref_needs_text=False,
        generate_kwargs=dict(language="en", duration_s=12.0, num_steps=16),
    ),
    cue_style="brackets",
    cues=CUES,
    expressivity_prompt=_EXPRESSIVITY,
    conversation_prompt=_CONVERSATION,
    soft_limit=200,
    first_chunk_soft_limit=100,
    batch_target_chars=280,
    batch_max_chars=360,
)
