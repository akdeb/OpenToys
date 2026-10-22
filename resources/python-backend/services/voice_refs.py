import os
import json
import logging
from pathlib import Path
from typing import Optional

VOICE_TRANSCRIPT_CACHE: dict[str, str] | None = None
logger = logging.getLogger(__name__)

def _default_app_data_dir() -> Path:
    db_path = os.environ.get("ELATO_DB_PATH")
    if db_path:
        return Path(db_path).expanduser().resolve().parent
    try:
        from db.paths import default_db_path
        return Path(default_db_path()).expanduser().resolve().parent
    except Exception:
        return Path.cwd()


def _voices_dir() -> Path:
    return Path(os.environ.get("ELATO_VOICES_DIR") or _default_app_data_dir().joinpath("voices"))


def _assets_dir() -> Path:
    if os.environ.get("ELATO_ASSETS_DIR"):
        return Path(os.environ["ELATO_ASSETS_DIR"]).expanduser().resolve()
    return Path(__file__).resolve().parents[3] / "app" / "src" / "assets"


def _cache_voice_transcripts_from_payload(payload: object) -> None:
    if not isinstance(payload, list):
        return
    for item in payload:
        if not isinstance(item, dict):
            continue
        vid = str(item.get("voice_id") or "").strip()
        transcript = str(item.get("transcript") or "").strip()
        if vid and transcript:
            VOICE_TRANSCRIPT_CACHE[vid] = transcript


def resolve_voice_ref_audio_path(voice_id: Optional[str]) -> Optional[str]:
    if not voice_id:
        return None
    try:
        path = _voices_dir().joinpath(f"{voice_id}.wav")
        if path.exists() and path.is_file():
            return str(path)
    except Exception:
        return None
    return None


def resolve_voice_ref_text(voice_id: Optional[str]) -> Optional[str]:
    if not voice_id:
        return None

    # Deterministic source of truth: DB (covers both global and user-created voices).
    try:
        import db_service

        v = db_service.db_service.get_voice(voice_id)
        t = (getattr(v, "transcript", None) or "").strip() if v else ""
        if t:
            return t
    except Exception:
        pass

    global VOICE_TRANSCRIPT_CACHE
    if VOICE_TRANSCRIPT_CACHE is None:
        VOICE_TRANSCRIPT_CACHE = {}
        voices_json = _assets_dir() / "voices.json"
        try:
            if voices_json.exists():
                _cache_voice_transcripts_from_payload(json.loads(voices_json.read_text(encoding="utf-8")))
        except Exception as e:
            logger.warning("Failed to load local voice transcripts (%s): %s", voices_json, e)
    return VOICE_TRANSCRIPT_CACHE.get(voice_id)


def preset_voice_key(tts_backend: str, personality_id: str) -> str:
    return f"preset_voice:{tts_backend}:{personality_id}"


def resolve_preset_voice(tts_backend: Optional[str], personality_id: Optional[str]) -> Optional[str]:
    """The built-in voice the user picked for this character, if valid for the active TTS model."""
    if not personality_id:
        return None
    from model_profiles import get_tts_profile

    profile = get_tts_profile(tts_backend)
    if not profile.preset_voices:
        return None
    try:
        import db_service

        chosen = db_service.db_service.get_setting(preset_voice_key(profile.id, personality_id))
    except Exception:
        return None
    return chosen if chosen in {v for v, _ in profile.preset_voices} else None


def record_tts_capabilities(tts_backend: Optional[str]) -> None:
    """Persist whether the selected TTS model can clone voices (app_state: tts_voice_cloning)."""
    from model_profiles import get_tts_profile

    try:
        import db_service

        profile = get_tts_profile(tts_backend)
        db_service.db_service.set_setting("tts_voice_cloning", "1" if profile.voice_cloning else "0")
    except Exception as e:
        logger.warning("Failed to record TTS voice cloning capability: %s", e)
