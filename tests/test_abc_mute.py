import importlib.util
from pathlib import Path
import unittest

_spec = importlib.util.spec_from_file_location('abc_mute_test', Path(__file__).resolve().parents[1] / 'abc_mute.py')
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
mute_vocal_notes = _module.mute_vocal_notes


class MuteTests(unittest.TestCase):
    def test_proposal(self):
        source = 'V: Vocal\n"Bbmaj7"z2f2f2c2"C"g3a3g2-|\n"Dm7"g2f2z2c2"Am7"e2f2e2d2|\n\nV: Ins\nZ2|\n'
        expected = 'V: Vocal\n"Bbmaj7"z2z2z2z2"C"z3z3z2|\n"Dm7"z2z2z2z2"Am7"z2z2z2z2|\n\nV: Ins\nZ2|\n'
        self.assertEqual(mute_vocal_notes(source), (expected, 13))

    def test_lengths_and_protected_text(self):
        source = 'V: Vocal\r\n"F#m7/C#"^^F,3/2-_B\'/4=c//d/!accent!e2 % ABC comment\r\n'
        expected = 'V: Vocal\r\n"F#m7/C#"z3/2z/4z//z/!accent!z2 % ABC comment\r\n'
        self.assertEqual(mute_vocal_notes(source), (expected, 5))

    def test_voice_switches_and_fields(self):
        source = 'T: ABC\nV: Vocal name="Vocal Melody"\nC[K:D]D[V:Ins]EF[V:Vocal]G|\nw: face\nV: Bass\nAB|\nV: VocalExtra\nCD|'
        expected = 'T: ABC\nV: Vocal name="Vocal Melody"\nz[K:D]z[V:Ins]EF[V:Vocal]z|\nw: face\nV: Bass\nAB|\nV: VocalExtra\nCD|'
        self.assertEqual(mute_vocal_notes(source), (expected, 3))

    def test_repeated_groups(self):
        source = '% verse\nV: Vocal\nC8-|C8z8|\nV: Ins\nD16|Z|\n% chorus\nV: Vocal\nE16|\nV: Ins\nZ|'
        result, count = mute_vocal_notes(source)
        self.assertIn('z8|z8z8|', result)
        self.assertIn('V: Ins\nD16|Z|', result)
        self.assertEqual(count, 3)
        self.assertEqual(mute_vocal_notes(result), (result, 0))

    def test_unsupported_constructs_fail(self):
        for music in ('[CEG]2|', '{c}C2|', '"broken C'):
            with self.subTest(music=music), self.assertRaises(ValueError):
                mute_vocal_notes('V: Vocal\n' + music)

    def test_empty_and_missing_voice(self):
        for source in ('', 'K:C\nCDEF|', 'V: Ins\nCDEF|'):
            self.assertEqual(mute_vocal_notes(source), (source, 0))

    def test_comfy_registration(self):
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('yue2_test_plugin', root / '__init__.py', submodule_search_locations=[str(root)])
        module = importlib.util.module_from_spec(spec)
        import sys
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        node = module.NODE_CLASS_MAPPINGS['YuE2MuteVocalABC']()
        self.assertEqual(node.process('V: Vocal\nC2|'), ('V: Vocal\nz2|', 1))
        self.assertEqual(node.RETURN_TYPES, ('STRING', 'INT'))


if __name__ == '__main__':
    unittest.main()
