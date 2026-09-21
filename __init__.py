from .nodes import YuE2MuteVocalABC, YuE2InstrumentalizeABC, AudioDuration

NODE_CLASS_MAPPINGS = {
    "YuE2MuteVocalABC": YuE2MuteVocalABC,
    "YuE2InstrumentalizeABC": YuE2InstrumentalizeABC,
    "AudioDuration": AudioDuration,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "YuE2MuteVocalABC": "YuE2 Mute Vocal ABC",
    "YuE2InstrumentalizeABC": "YuE2 Instrumentalize ABC",
    "AudioDuration": "Audio Duration",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
