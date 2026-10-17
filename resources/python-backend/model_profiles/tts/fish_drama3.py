from ..base import TtsProfile, cue_prompts

CUES = ("laughs", "sighs", "whispers")
_EXPRESSIVITY, _CONVERSATION = cue_prompts("brackets", CUES)

PROFILE = TtsProfile(
    id="fish-drama3",
    label="Fish Audio Drama 3 4bit",
    repo="mlx-community/fish-audio-drama-3-4bit",
    engine="generic",
    aliases=("fish", "fish-drama-3", "drama3"),
    ram_gb=26,
    disk_gb=22,
    quality="Studio",
    note="35B MoE, multi-speaker, 83 languages. Needs a 32 GB+ Mac and mlx-audio newer than 0.5.9.",
    params=dict(
        streams=True,
        generate_kwargs=dict(temperature=0.7, top_p=0.7, top_k=30),
    ),
    cue_style="brackets",
    cues=CUES,
    expressivity_prompt=_EXPRESSIVITY,
    conversation_prompt=_CONVERSATION,
    soft_limit=200,
    first_chunk_soft_limit=100,
    batch_target_chars=300,
    batch_max_chars=380,
)
