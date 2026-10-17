from ..base import TtsProfile

PROFILE = TtsProfile(
    id="breeze-blue",
    label="BreezeBlue TTS 2 4bit",
    repo="mlx-community/Breeze-TTS-2-mlx-4bit",
    engine="breeze",
    aliases=("breeze", "breeze_blue", "breeze-tts", "breeze_tts"),
    ram_gb=8,
    disk_gb=3,
    quality="Expressive",
    note="Expressive voice design and cloning, heavier than Qwen3",
    params=dict(temperature=0.9, top_k=50, top_p=1.0, repetition_penalty=1.0, cfg_scale=4.0),
    cue_style="parentheses",
    expressivity_prompt=(
        "To add expressivity, you may occasionally use ONLY these paralinguistic cues in parentheses: "
        "(laugh), (chuckle), (sigh), (gasp), (cough), (clear throat), (sniff), (groan), (shush). "
        "Use only these cues naturally in context to enhance the conversational flow. "
        "Examples: (chuckle) That is funny. (sigh) That was a long day."
    ),
    conversation_prompt="If you use paralinguistic cues, use ONLY parenthesized tags from the allowed list.",
)
