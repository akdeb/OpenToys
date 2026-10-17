from ..base import TtsProfile

PROFILE = TtsProfile(
    id="chatterbox-turbo",
    label="Chatterbox Turbo",
    repo="mlx-community/chatterbox-turbo-fp16",
    engine="chatterbox",
    aliases=("chatterbox", "chatterbox_turbo"),
    ram_gb=6,
    disk_gb=4,
    quality="Expressive",
    note="Great style/expressivity, usually heavier",
    params=dict(temperature=0.8, top_k=1000, top_p=0.95, repetition_penalty=1.2),
    cue_style="brackets",
    expressivity_prompt=(
        "To add expressivity, you should occasionally use ONLY these paralinguistic cues in brackets: "
        "[laugh], [chuckle], [sigh], [gasp], [cough], [clear throat], [sniff], [groan], [shush]. "
        "Use only these cues naturally in context to enhance the conversational flow. "
        "Examples: [chuckle] That is funny. [sigh] That was a long day."
    ),
    conversation_prompt="If you use paralinguistic cues, use ONLY bracketed tags from the allowed list.",
)
