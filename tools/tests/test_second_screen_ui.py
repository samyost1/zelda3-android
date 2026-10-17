"""Run the production catalog/font/layout behavior tests without Android or ROMs."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class SecondScreenBehavior(unittest.TestCase):
    @unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'Requires a JDK on PATH')
    def test_catalog_font_and_layout(self):
        sources = ROOT / 'app/src/main/java/com/dishii/zelda3'
        with tempfile.TemporaryDirectory(prefix='zelda3-ui-tests-') as directory:
            subprocess.run(['javac', '-encoding', 'UTF-8', '--release', '8', '-Xlint:-options',
                            '-d', directory, str(sources / 'SecondScreenText.java'),
                            str(sources / 'PixelText.java'), str(sources / 'SaveStateUi.java'),
                            str(ROOT / 'tools/tests/SecondScreenTextTest.java')], check=True)
            subprocess.run(['java', '-cp', directory, 'com.dishii.zelda3.SecondScreenTextTest'], check=True)


if __name__ == '__main__':
    unittest.main()
