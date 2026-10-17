"""Realtime (speech-to-speech) model profiles.

No realtime model is wired into the pipeline yet. Add one file per model here,
define a RealtimeProfile in it, and list it in REALTIME_PROFILES.
"""

from ..base import RealtimeProfile

REALTIME_PROFILES: tuple[RealtimeProfile, ...] = ()
