from .nodes import YuE2MuteVocalABC, YuE2InstrumentalizeABC

NODE_CLASS_MAPPINGS = {
    "YuE2MuteVocalABC": YuE2MuteVocalABC,
    "YuE2InstrumentalizeABC": YuE2InstrumentalizeABC,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "YuE2MuteVocalABC": "YuE2 Mute Vocal ABC",
    "YuE2InstrumentalizeABC": "YuE2 Instrumentalize ABC",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
