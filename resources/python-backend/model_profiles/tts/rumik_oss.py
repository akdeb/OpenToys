from ..base import TtsProfile, cue_prompts

CUES = ("laugh", "chuckle", "sigh")
_EXPRESSIVITY, _CONVERSATION = cue_prompts("angle", CUES)

PROFILE = TtsProfile(
    id="rumik-oss-1",
    label="rumik-oss 1 4bit (Indic)",
    repo="rumik-ai/rumik-oss-1-mlx-4bit",
    engine="generic",
    aliases=("rumik", "rumik-oss"),
    ram_gb=3,
    disk_gb=2,
    quality="Indic",
    note="3B TTS for 22 Indic languages plus English. Non-commercial license, 4bit is experimental.",
    params=dict(
        streams=True,
        use_ref=False,
        generate_kwargs=dict(voice="Ira", instruct="happy, steady pace"),
    ),
    voice_cloning=False,
    cue_style="angle",
    cues=CUES,
    expressivity_prompt=_EXPRESSIVITY,
    conversation_prompt=_CONVERSATION,
    language_prompt=(
        "Reply in the language the user speaks (Hindi or another Indic language, or English), "
        "written in that language's native script."
    ),
    soft_limit=160,
    first_chunk_soft_limit=90,
    batch_target_chars=260,
    batch_max_chars=340,
)
