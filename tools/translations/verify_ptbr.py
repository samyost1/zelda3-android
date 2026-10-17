#!/usr/bin/env python3
"""Check real PT-BR imports with the production Java classes, without Android.

Requires a JDK (javac/java on PATH) and the user's own US and translated ROMs.
ROMs, classes and generated test data are kept in a temporary directory.
"""

import argparse
from pathlib import Path
import subprocess
import tempfile
import struct

from build_ptbr_patch import ROOT, read_rom, US_SHA1
from map_ui import lorom, decompress
import hashlib


def write_second_screen_fixture(us):
    """Keep real baseline graphics for native regression checks outside Git."""
    if hashlib.sha1(us).hexdigest().upper() != US_SHA1:
        raise ValueError('Unsupported baseline ROM')
    data = bytearray(us[lorom(0x9bd660):lorom(0x9bd660)+128])
    for index in (0x6a, 0x6b, 0x69):
        offset = lorom(us[0x51b1+index] | us[0x50d2+index] << 8 | us[0x4ff3+index] << 16)
        _, size = decompress(us, offset)
        data.extend(struct.pack('<I', size))
        data.extend(us[offset:offset+size])
    (ROOT / 'build/ui-second-screen-base.bin').write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--us-rom", required=True)
    parser.add_argument("--translated-rom", required=True)
    args = parser.parse_args()
    sources = ROOT / "app/src/main/java/com/dishii/zelda3"
    with tempfile.TemporaryDirectory(prefix="zelda3-ptbr-tests-") as temporary:
        directory = Path(temporary)
        pt, us = directory / "pt.sfc", directory / "us.sfc"
        pt.write_bytes(read_rom(args.translated_rom))
        us.write_bytes(read_rom(args.us_rom))
        subprocess.run([
            "javac", "--release", "8", "-Xlint:-options", "-d", str(directory),
            str(sources / "BpsPatcher.java"), str(sources / "TranslationExtractor.java"),
            str(sources / "UiTranslationPackage.java"), str(sources / "UiTranslationResources.java"),
            str(ROOT / "tools/tests/TranslationImportTest.java"),
            str(ROOT / "tools/tests/UiTranslationPackageTest.java"),
        ], cwd=ROOT, check=True)
        subprocess.run([
            "java", "-cp", str(directory), "com.dishii.zelda3.UiTranslationPackageTest", str(pt), str(us),
            str(ROOT / 'build/ui-package.bin'),
        ], cwd=ROOT, check=True)
        subprocess.run([
            "java", "-cp", str(directory), "com.dishii.zelda3.TranslationImportTest", str(pt), str(us),
        ], cwd=ROOT, check=True)
        write_second_screen_fixture(us.read_bytes())


if __name__ == "__main__":
    main()
