from ..base import TtsProfile

PRESET_VOICES = (
    ("Zoey", "Zoey (F)"), ("Juniper", "Juniper (F)"), ("Harper", "Harper (F)"),
    ("Everly", "Everly (F)"), ("Hadley", "Hadley (F)"), ("Delia", "Delia (F)"),
    ("Easton", "Easton (M)"), ("Micah", "Micah (M)"), ("Miles", "Miles (M)"),
    ("Russell", "Russell (M)"), ("Trevor", "Trevor (M)"), ("Preston", "Preston (M)"),
)

PROFILE = TtsProfile(
    id="phonon-31m-en",
    label="Phonon 31M (English)",
    repo="gradium/phonon-31m-en",
    engine="phonon",
    aliases=("phonon",),
    ram_gb=1,
    disk_gb=1,
    quality="Fast",
    note="Gradium's 31M on-device TTS, runs on CPU with streaming. Apache 2.0.",
    params=dict(lang="en", quant="q8", voice="Zoey"),
    voice_cloning=False,
    preset_voices=PRESET_VOICES,
    cue_style=None,
    soft_limit=200,
    first_chunk_soft_limit=100,
    batch_target_chars=300,
    batch_max_chars=400,
)
