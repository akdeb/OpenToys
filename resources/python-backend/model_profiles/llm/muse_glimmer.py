from ..base import LlmProfile

PROFILE = LlmProfile(
    id="muse_glimmer",
    label="Muse Glimmer",
    match=("muse-glimmer",),
    # The template ends at "<|start|>assistant", and Muse then picks a recipient.
    # Left alone it opens with "to=self", an analysis channel that ignores
    # reasoning_strength=none and burns the token budget (measured: 120 of 120 tokens
    # on analysis, nothing audible, on an M4 Pro). Naming the recipient up front makes
    # it write the reply to the user straight away.
    generation_prefix=" to=user<|message|>",
)
