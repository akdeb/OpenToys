from ..base import SttProfile

PROFILE = SttProfile(
    id="whisper-large-v3-turbo",
    label="Whisper Large v3 Turbo",
    repo="mlx-community/whisper-large-v3-turbo-asr-fp16",
    aliases=("whisper",),
    note="Default speech recognition",
)
