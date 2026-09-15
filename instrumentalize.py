"""Strict, standard-library-only editing of monophonic YuE2 ABC."""

from dataclasses import dataclass, field
from fractions import Fraction
import re

from .abc_mute import mute_vocal_notes


TOKEN = re.compile(
    r'(?P<quote>"(?:\\.|[^"\\])*")'
    + r'|(?P<key>\[K:[^\]]+\])'
    + r'|(?P<note>(?P<acc>\^{1,2}|_{1,2}|=)?(?P<pitch>[A-Ga-g])(?P<oct>[,\']*)(?P<len>\d+(?:/+\d*)?|/+\d*)?(?P<tie>-?))'
    + r'|(?P<rest>z(?P<rlen>\d+(?:/+\d*)?|/+\d*)?)'
    + r'|(?P<multi>Z(?P<bars>\d+)?)'
    + r'|(?P<bar>\|\]|\|\||\|)'
)


def _length(text):
    if not text:
        return Fraction(1)
    if '/' not in text:
        return Fraction(text)
    numerator, tail = text.split('/', 1)
    slashes = len(tail) - len(tail.lstrip('/')) + 1
    denominator = tail.lstrip('/')
    if slashes > 1 and denominator:
        raise ValueError('Use a single slash with an explicit denominator.')
    return Fraction(int(numerator or 1), int(denominator) if denominator else 2 ** slashes)


def _key(text):
    match = re.fullmatch(r'([A-G])([#b]?)(maj(?:or)?|m|min(?:or)?)?', text.strip())
    if not match:
        raise ValueError(f'Unsupported key: {text!r}; use a major or minor key.')
    root, accidental, mode = match.groups()
    fifths = dict(C=0, G=1, D=2, A=3, E=4, B=5, F=-1)[root]
    fifths += {'': 0, '#': 7, 'b': -7}[accidental]
    if mode in ('m', 'min', 'minor'):
        fifths -= 3
    if abs(fifths) > 7:
        raise ValueError('Keys with more than seven accidentals are unsupported.')
    result = dict.fromkeys('ABCDEFG', '')
    for letter in ('FCGDAEB' if fifths >= 0 else 'BEADGCF')[:abs(fifths)]:
        result[letter] = '^' if fifths >= 0 else '_'
    return result


@dataclass
class Event:
    start: int
    end: int
    kind: str
    text: str
    onset: Fraction
    duration: Fraction = Fraction(0)
    melody: str = ''
    tied: bool = False


@dataclass
class Bar:
    events: list
    meter: Fraction
    unit: Fraction
    key: str
    compressed: bool = False

    @property
    def sounding(self):
        return any(e.kind == 'note' for e in self.events)

    @property
    def keys(self):
        return [(e.onset, e.text) for e in self.events if e.kind == 'key']


@dataclass
class Voice:
    meter: object = None
    unit: object = None
    key: object = None
    bars: list = field(default_factory=list)
    events: list = field(default_factory=list)
    elapsed: Fraction = Fraction(0)
    accidentals: dict = field(default_factory=dict)
    pending_tie: object = None
    bar_key: object = None


def _parse(abc):
    voices = {name: Voice() for name in ('Vocal', 'Ins')}
    active = None
    started = False
    offset = 0
    tune_count = 0
    for number, line in enumerate(abc.splitlines(keepends=True), 1):
        try:
            stripped = line.strip()
            header = re.match(r'^\s*([A-Za-z]):(.*)', line)
            if header:
                name, value = header.groups()
                value = value.split('%', 1)[0].strip()
                if name == 'X':
                    tune_count += 1
                    if tune_count > 1 or started:
                        raise ValueError('Process one ABC tune at a time.')
                if name == 'V':
                    active = value.split()[0] if value else None
                    if active not in voices:
                        raise ValueError('V2 supports only Vocal and Ins voice IDs.')
                    if any(v.events for v in voices.values()):
                        raise ValueError('Voice changes must occur at a bar boundary.')
                elif name in ('M', 'L', 'K'):
                    targets = [voices[active]] if started and active else voices.values()
                    for voice in targets:
                        if voice.events:
                            raise ValueError('M/L/K fields must occur at a bar boundary.')
                        if name == 'K':
                            _key(value)
                            voice.key = value
                        else:
                            fraction = Fraction({'C': '4/4', 'C|': '2/2'}.get(value, value))
                            if fraction <= 0:
                                raise ValueError('M and L must be positive.')
                            setattr(voice, 'meter' if name == 'M' else 'unit', fraction)
                elif name in ('w', 'U'):
                    raise ValueError(f'{name}: fields are unsupported in V2.')
            elif stripped and not stripped.startswith('%'):
                if active not in voices:
                    raise ValueError('Music requires V: Vocal or V: Ins.')
                voice = voices[active]
                if None in (voice.meter, voice.unit, voice.key):
                    raise ValueError('V2 requires explicit M:, L:, and K: headers.')
                started = True
                pos = 0
                while pos < len(line):
                    if line[pos].isspace():
                        pos += 1
                        continue
                    if line[pos] == '%':
                        break
                    match = TOKEN.match(line, pos)
                    if not match:
                        raise ValueError(f'Unsupported ABC syntax near {line[pos:pos + 20]!r}.')
                    kind = next(k for k in ('quote', 'key', 'note', 'rest', 'multi', 'bar') if match[k] is not None)
                    text = match[0]
                    event = Event(offset + pos, offset + match.end(), kind, text, voice.elapsed)
                    if kind == 'bar':
                        if not voice.events:
                            raise ValueError('Empty bars are unsupported.')
                        if len(voice.events) == 1 and voice.events[0].kind == 'multi':
                            multi = voice.events[0]
                            for _ in range(int(multi.text[1:] or 1)):
                                voice.bars.append(Bar([multi], voice.meter, voice.unit, voice.key, True))
                        else:
                            if voice.elapsed != voice.meter:
                                raise ValueError(f'{active} bar {len(voice.bars) + 1} has duration {voice.elapsed}, expected {voice.meter}.')
                            voice.bars.append(Bar(voice.events, voice.meter, voice.unit, voice.bar_key))
                        voice.events = []
                        voice.elapsed = Fraction(0)
                        voice.accidentals = {}
                        voice.bar_key = None
                    else:
                        if not voice.events:
                            voice.bar_key = voice.key
                        if kind == 'quote' and active == 'Ins':
                            raise ValueError('Keep chord annotations in Vocal; Ins annotations are unsupported in V2.')
                        if kind == 'multi':
                            if voice.events or int(match['bars'] or 1) < 1 or voice.pending_tie:
                                raise ValueError('A multi-bar rest must be alone and cannot continue a tie.')
                        elif any(e.kind == 'multi' for e in voice.events):
                            raise ValueError('A multi-bar rest must be alone before its barline.')
                        if kind == 'key':
                            voice.key = text[3:-1].strip()
                            _key(voice.key)
                            voice.accidentals = {}
                        if kind in ('note', 'rest'):
                            event.duration = _length(match['len'] if kind == 'note' else match['rlen']) * voice.unit
                            if event.duration <= 0:
                                raise ValueError('Note/rest duration must be positive.')
                            voice.elapsed += event.duration
                            if kind == 'rest' and voice.pending_tie:
                                raise ValueError('A rest cannot continue a tie.')
                            if kind == 'note':
                                pitch = match['pitch'] + match['oct']
                                letter = match['pitch'].upper()
                                acc = match['acc']
                                resolved = acc or voice.accidentals.get(letter, _key(voice.key)[letter]) or '='
                                if voice.pending_tie:
                                    previous_pitch, previous_acc = voice.pending_tie
                                    if pitch != previous_pitch or (acc and acc != previous_acc):
                                        raise ValueError('A tie must connect equal pitches.')
                                    resolved = previous_acc
                                if acc:
                                    voice.accidentals[letter] = acc
                                event.melody = resolved + pitch + (match['len'] or '')
                                event.tied = bool(match['tie'])
                                voice.pending_tie = (pitch, resolved) if event.tied else None
                        voice.events.append(event)
                    pos = match.end()
        except (ValueError, ZeroDivisionError) as error:
            raise ValueError(f'ABC line {number}: {error}') from error
        offset += len(line)
    for name, voice in voices.items():
        if voice.events:
            raise ValueError(f'{name}: end the final measure with a barline.')
        if voice.pending_tie:
            raise ValueError(f'{name}: unresolved final tie.')
    vocal, ins = voices['Vocal'].bars, voices['Ins'].bars
    if not vocal or len(vocal) != len(ins):
        raise ValueError('Vocal and Ins must have the same nonzero number of bars.')
    for index, (left, right) in enumerate(zip(vocal, ins), 1):
        if (left.meter, left.unit, left.key, left.keys) != (right.meter, right.unit, right.key, right.keys):
            raise ValueError(f'Bar {index}: Vocal/Ins meter, unit length, or key changes do not match.')
    return vocal, ins


def instrumentalize(abc):
    """Return ABC, muted note tokens, moved bars, and a short report."""
    vocal, ins = _parse(abc)
    selected = [v.sounding and not i.sounding for v, i in zip(vocal, ins)]
    edits = []
    index = 0
    while index < len(ins):
        target = ins[index]
        end = index + 1
        if target.compressed:
            while end < len(ins) and ins[end].events[0] is target.events[0]:
                end += 1
        if any(selected[index:end]):
            melodies = []
            for bar_index in range(index, end):
                if not selected[bar_index]:
                    melodies.append('Z')
                    continue
                pieces = []
                events = vocal[bar_index].events
                for n, event in enumerate(events):
                    if event.kind == 'quote':
                        continue
                    if event.kind == 'note':
                        later_notes = any(e.kind == 'note' for e in events[n + 1:])
                        keep_tie = event.tied and (later_notes or (bar_index + 1 < len(ins) and selected[bar_index + 1]))
                        pieces.append(event.melody + ('-' if keep_tie else ''))
                    else:
                        pieces.append(event.text)
                melodies.append(''.join(pieces))
            replacement = '|'.join(melodies)
            # Edit only music tokens; comments, whitespace, fields, barlines,
            # and the surrounding section structure remain at their positions.
            for n, event in enumerate(target.events):
                edits.append((event.start, event.end, replacement if n == 0 else ''))
        index = end
    result = abc
    for start, end, replacement in sorted(edits, reverse=True):
        result = result[:start] + replacement + result[end:]
    result, muted = mute_vocal_notes(result)
    # Validate the actual serialized output as well as the input.
    _parse(result)
    moved = sum(selected)
    occupied = sum(v.sounding and i.sounding for v, i in zip(vocal, ins))
    return result, muted, moved, f'Moved {moved} bars; preserved existing Ins in {occupied} Vocal melody bars; muted {muted} note tokens.'
