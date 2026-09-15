"""Duration-preserving muting for YuE2's monophonic Vocal voice.

No ComfyUI or model dependencies. Unsupported pitched constructs fail rather
than silently producing a score with incorrect timing.
"""

import re


NOTE = re.compile(r"(?:\^{1,2}|_{1,2}|=)?[A-Ga-g][,']*(?P<length>(?:\d+(?:/+\d*)?|/+\d*)?)-?")
FIELD = re.compile(r"^\s*([A-Za-z]):(.*)")
INLINE = re.compile(r"\[([A-Za-z]):([^\]]*)\]")


def _voice(value):
    parts = value.strip().split()
    return parts[0] if parts else None


def _music(line, active_voice):
    output = []
    count = 0
    i = 0
    while i < len(line):
        char = line[i]
        if char == "%":
            output.append(line[i:])
            break
        if char in ('"', '!', '+'):
            end = i + 1
            while end < len(line):
                if line[end] == "\\":
                    end += 2
                    continue
                if line[end] == char:
                    break
                end += 1
            if end >= len(line):
                raise ValueError("Unclosed ABC annotation or decoration.")
            output.append(line[i:end + 1])
            i = end + 1
            continue
        inline = INLINE.match(line, i)
        if inline:
            if inline[1] == "V":
                active_voice = _voice(inline[2])
            output.append(inline[0])
            i = inline.end()
            continue
        if active_voice == "Vocal":
            if char == "{" or (char == "[" and i + 1 < len(line)
                               and line[i + 1] in "ABCDEFGabcdefg^_=z"):
                raise ValueError("Vocal grace notes and polyphonic note stacks are unsupported; use monophonic YuE2 ABC.")
            note = NOTE.match(line, i)
            if note:
                output.append("z" + note["length"])
                count += 1
                i = note.end()
                continue
            # A tie separated from its note by whitespace also becomes invalid
            # once that note is a rest.
            if char == "-":
                i += 1
                continue
        output.append(char)
        i += 1
    return "".join(output), count, active_voice


def mute_vocal_notes(abc):
    """Return (converted ABC, number of muted note tokens).

    Keep all original line endings, fields, annotations, and non-Vocal music.
    Voice IDs are exact and case-sensitive, as in the native YuE2 exporter.
    """
    if not isinstance(abc, str):
        raise TypeError("abc must be a string")
    output = []
    active_voice = None
    count = 0
    for number, line in enumerate(abc.splitlines(keepends=True), 1):
        field = FIELD.match(line)
        if field:
            if field[1] == "X":
                active_voice = None
            elif field[1] == "V":
                active_voice = _voice(field[2])
            output.append(line)
            continue
        try:
            converted, muted, active_voice = _music(line, active_voice)
        except ValueError as error:
            raise ValueError(f"ABC line {number}: {error}") from error
        output.append(converted)
        count += muted
    return "".join(output), count
