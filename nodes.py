from .abc_mute import mute_vocal_notes
from .instrumentalize import instrumentalize


class YuE2MuteVocalABC:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"abc": ("STRING", {"multiline": True, "default": ""})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("abc", "muted_notes")
    FUNCTION = "process"
    CATEGORY = "YuE2/ABC"
    DESCRIPTION = "Mute Vocal notes while preserving durations, chord symbols, and the Ins voice."

    def process(self, abc):
        return mute_vocal_notes(abc)


class YuE2InstrumentalizeABC:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"abc": ("STRING", {"multiline": True, "default": ""})}}

    RETURN_TYPES = ("STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("abc", "muted_notes", "moved_bars", "report")
    FUNCTION = "process"
    CATEGORY = "YuE2/ABC"
    DESCRIPTION = "Move Vocal melody into fully resting Ins bars, preserve existing Ins melody, then mute Vocal. Requires M/L/K headers."

    def process(self, abc):
        return instrumentalize(abc)
