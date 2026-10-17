"""Synthetic BPS tests; no ROM or game assets required."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "translations"))
from build_ptbr_patch import apply_bps, crc, create_bps, encode_int


class BpsTests(unittest.TestCase):
    def test_roundtrip_copies_literals_and_backward_seeks(self):
        source = bytes(range(256)) * 4
        target = source[500:900] + b"new data" + source[100:400] + b"tail"
        patch = create_bps(source, target)
        self.assertEqual(apply_bps(source, patch), target)
        self.assertEqual(create_bps(source, target), patch)

    def test_empty_small_and_repetitive_targets(self):
        for source, target in [(b"", b""), (b"", b"new"), (b"abc", b""),
                               (b"a" * 500, b"a" * 1200), (b"xyz", b"123")]:
            with self.subTest(source_size=len(source), target_size=len(target)):
                self.assertEqual(apply_bps(source, create_bps(source, target)), target)

    def test_source_and_patch_corruption_rejected(self):
        source = b"input ROM" * 20
        patch = create_bps(source, b"output assets" * 20)
        with self.assertRaisesRegex(ValueError, "checksum"):
            apply_bps(b"x" + source[1:], patch)
        corrupt = bytearray(patch)
        corrupt[len(corrupt) // 2] ^= 1
        with self.assertRaisesRegex(ValueError, "checksum"):
            apply_bps(source, corrupt)

    def test_reader_supports_overlapping_targetcopy(self):
        # TargetRead "ab", then TargetCopy 6 bytes from output position zero.
        source, target = b"", b"abababab"
        patch = bytearray(b"BPS1")
        for value in (0, 8, 0, ((2 - 1) << 2) | 1):
            patch.extend(encode_int(value))
        patch.extend(b"ab")
        patch.extend(encode_int(((6 - 1) << 2) | 3))
        patch.extend(encode_int(0))
        patch.extend(struct.pack("<II", crc(source), crc(target)))
        patch.extend(struct.pack("<I", crc(patch)))
        self.assertEqual(apply_bps(source, bytes(patch)), target)


if __name__ == "__main__":
    unittest.main()
