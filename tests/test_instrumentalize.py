import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('instrumental_test_plugin', ROOT / '__init__.py', submodule_search_locations=[str(ROOT)])
PLUGIN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PLUGIN
SPEC.loader.exec_module(PLUGIN)
convert = PLUGIN.NODE_CLASS_MAPPINGS['YuE2InstrumentalizeABC']().process


def score(vocal, ins, header='M:4/4\nL:1/8\nK:C\n'):
    return header + 'V: Vocal\n' + vocal + '\nV: Ins\n' + ins + '\n'


class InstrumentalTests(unittest.TestCase):
    def test_compressed_rest_and_chords(self):
        result, muted, moved, report = convert(score('"C"C4"G"G4|D8|', 'Z2|'))
        self.assertIn('"C"z4"G"z4|z8|', result)
        self.assertIn('V: Ins\n=C4=G4|=D8|', result)
        self.assertEqual((muted, moved), (3, 2))

    def test_existing_ins_priority(self):
        result, _, moved, _ = convert(score('C8|D8|E8|', 'Z|g4a4|z4z4|'))
        self.assertIn('V: Ins\n=C8|g4a4|=E8|', result)
        self.assertEqual(moved, 2)

    def test_partial_compressed_rest(self):
        result, _, moved, _ = convert(score('z8|D8|z8|', 'Z3|'))
        self.assertIn('V: Ins\nZ|=D8|Z|', result)
        self.assertEqual(moved, 1)
        self.assertEqual(convert(result)[:3], (result, 0, 0))

    def test_tie_into_occupied_bar(self):
        result, _, _, _ = convert(score('^F8-|F8|', 'Z|G8|'))
        self.assertIn('V: Ins\n^F8|G8|', result)

    def test_tie_from_occupied_bar_carries_accidental(self):
        result, _, _, _ = convert(score('^F8-|F4F4|', 'G8|Z|'))
        self.assertIn('V: Ins\nG8|^F4=F4|', result)

    def test_preserved_tie(self):
        result, _, _, _ = convert(score('^F8-|F8|', 'Z2|'))
        self.assertIn('V: Ins\n^F8-|^F8|', result)

    def test_key_signature_and_octave_accidentals(self):
        result, _, _, _ = convert(score('F2=F2f2F2|', 'Z|', 'M:4/4\nL:1/8\nK:D\n'))
        self.assertIn('V: Ins\n^F2=F2=f2=F2|', result)

    def test_inline_key_change(self):
        result, _, _, _ = convert(score('C4[K:G]F4|', 'z4[K:G]z4|'))
        self.assertIn('V: Ins\n=C4[K:G]^F4|', result)

    def test_comments_and_repeated_groups(self):
        source = score('C8|', 'Z|') + '% chorus\nV: Vocal\nM:3/4\nE6|\nV: Ins\nM:3/4\nz3 % keep ABC\nz3|\n'
        result, _, moved, _ = convert(source.replace('\n', '\r\n'))
        self.assertIn('% chorus\r\n', result)
        self.assertIn('% keep ABC\r\n', result)
        self.assertEqual(moved, 2)

    def test_fractional_duration(self):
        result, muted, moved, _ = convert(score('C3/2D/2E2F4|', 'z8|'))
        self.assertIn('=C3/2=D/2=E2=F4|', result)
        self.assertEqual((muted, moved), (4, 1))

    def test_note_onsets_and_pitch_invariants(self):
        parse = sys.modules['instrumental_test_plugin.instrumentalize']._parse
        source = score('"D"F2^G2g2A2-|A4"G"B4|z8|C8|', 'Z2|E8|Z|', 'M:4/4\nL:1/8\nK:D\n')
        before_v, before_i = parse(source)
        result, _, moved, _ = convert(source)
        after_v, after_i = parse(result)
        self.assertEqual(moved, 3)
        def notes(bar):
            return [(e.onset, e.duration, e.melody, e.tied) for e in bar.events if e.kind == 'note']
        for i in range(4):
            self.assertFalse(after_v[i].sounding)
            expected = before_i[i] if before_i[i].sounding else before_v[i]
            self.assertEqual(notes(after_i[i]), notes(expected))
            chords = lambda bar: [(e.onset, e.text) for e in bar.events if e.kind == 'quote']
            self.assertEqual(chords(before_v[i]), chords(after_v[i]))

    def test_multirests_in_both_voices(self):
        result, muted, moved, _ = convert(score('Z2|', 'Z2|'))
        self.assertEqual((muted, moved), (0, 0))
        self.assertEqual(result, score('Z2|', 'Z2|'))

    def test_invalid_input_fails(self):
        cases = [score('C7|', 'Z|'), score('C8|D8|', 'Z|'),
                 score('C8|', 'Z|', ''), score('(3CDE F6|', 'Z|'),
                 score('C8-|', 'Z|'), score('C8|', 'z4[K:D]z4|'),
                 score('C8|', '"C"z8|'), score('C8|', 'Z0|'),
                 score('C8|', 'Z|') + 'X:2\n' + score('C8|', 'Z|') + 'X:3\n']
        for source in cases:
            with self.subTest(source=source), self.assertRaises(ValueError):
                convert(source)


if __name__ == '__main__':
    unittest.main()
