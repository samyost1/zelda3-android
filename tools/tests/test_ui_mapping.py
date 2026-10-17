"""ROM-free checks for the PT-BR interface mapping tools."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'translations'))


class UiMappingTests(unittest.TestCase):
    def test_generated_metadata_is_current(self):
        import json
        import generate_ui_sources
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root / 'tools/translations/ptbr_ui_manifest.json').read_text())
        for name, expected in generate_ui_sources.outputs(manifest).items():
            self.assertEqual((root / name).read_text(), expected)

    def test_bounded_graphics_decoder(self):
        import map_ui
        self.assertEqual(map_ui.decompress(bytes([2, 1, 2, 3, 0xff]), 0), (b'\1\2\3', 5))
        self.assertEqual(map_ui.decompress(bytes([0x22, 7, 0xff]), 0), (b'\7\7\7', 3))
        self.assertEqual(map_ui.decompress(bytes([0, 9, 0x82, 0, 0, 0xff]), 0), (b'\11'*4, 6))
        for bad in [b'', b'\x02\x01', b'\x80\x00\x00\xff', b'\xe0']:
            with self.assertRaises(ValueError):
                map_ui.decompress(bad, 0)

    def test_stripes_end_and_bounds(self):
        import map_ui
        self.assertEqual(map_ui.stripe_size(bytes([0x61, 0, 0, 1, 0, 0x18, 0xff]), 0), 7)
        for bad in [b'', b'\x61\0\0\x01\0', b'\x61\0\0\0\0\xff']:
            with self.assertRaises(ValueError):
                map_ui.stripe_size(bad, 0)
