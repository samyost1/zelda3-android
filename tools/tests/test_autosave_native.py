"""Exercise the production Android autosave lifecycle without SDL or a ROM."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest
from test_gamepad_native import SRC, toolchain


class AutosaveLifecycleTests(unittest.TestCase):
    def test_lifecycle_and_live_preference(self):
        tc = toolchain()
        if os.name != 'nt' or not tc or not (tc / 'clang.exe').exists():
            self.skipTest('Requires Windows and Android NDK')
        header = (SRC / 'android_autosave.h').read_text()
        production = (SRC / 'android_autosave.c').read_text()
        header = '\n'.join(line for line in header.splitlines() if not line.startswith('#'))
        production = '\n'.join(line for line in production.splitlines() if not line.startswith('#include'))
        source = r'''
typedef _Bool bool;
#define true 1
#define false 0
typedef struct { int value; } SDL_atomic_t;
int SDL_AtomicSet(SDL_atomic_t *a, int v) { int old=a->value; a->value=v; return old; }
int SDL_AtomicGet(SDL_atomic_t *a) { return a->value; }
enum { kSaveLoad_Save, kSaveLoad_Load };
static int saves, loads, logs, locks, lock_error, next_result = 1;
void ZeldaApuLock(void) { locks++; }
void ZeldaApuUnlock(void) { locks--; }
int SaveLoadSlotChecked(int cmd, int slot) {
  if (slot != 0 || locks != 1) lock_error++;
  if (cmd == kSaveLoad_Save) saves++; else loads++;
  return next_result;
}
void SDL_Log(const char *fmt, ...) { logs++; }
'''
        source += header + '\n' + production
        source += r'''
#define CHECK(x) if (!(x)) return __LINE__;
int tests(void) {
  AndroidAutosave_Init(false);
  AndroidAutosave_Handle(kAutosaveStart);
  AndroidAutosave_Handle(kAutosaveBackground);
  AndroidAutosave_Handle(kAutosaveForeground);
  AndroidAutosave_Handle(kAutosaveExit);
  CHECK(saves == 0 && loads == 0);
  AndroidAutosave_Init(true);
  next_result=2;
  AndroidAutosave_Handle(kAutosaveStart);
  CHECK(loads == 1 && saves == 0);
  next_result=1;
  AndroidAutosave_Handle(kAutosaveBackground);
  CHECK(saves == 1); // synchronous: completed before event handler returns
  AndroidAutosave_Handle(kAutosaveBackground);
  CHECK(saves == 1);
  AndroidAutosave_Handle(kAutosaveForeground);
  CHECK(loads == 1); // a resume never reloads the file
  AndroidAutosave_Handle(kAutosaveBackground);
  CHECK(saves == 2);
  AndroidAutosave_Handle(kAutosaveExit);
  CHECK(saves == 3); // normal exit remains an extra protection
  AndroidAutosave_Init(false);
  AndroidAutosave_SetEnabled(true); // UI change immediately before leaving
  AndroidAutosave_Handle(kAutosaveBackground);
  CHECK(saves == 4);
  AndroidAutosave_Handle(kAutosaveForeground);
  AndroidAutosave_SetEnabled(false);
  AndroidAutosave_Handle(kAutosaveBackground);
  AndroidAutosave_Handle(kAutosaveExit);
  CHECK(saves == 4);
  AndroidAutosave_Init(true);
  next_result=4;
  AndroidAutosave_Handle(kAutosaveBackground);
  AndroidAutosave_Handle(kAutosaveBackground);
  CHECK(saves == 5);
  AndroidAutosave_Handle(kAutosaveForeground);
  next_result=1;
  AndroidAutosave_Handle(kAutosaveBackground);
  CHECK(saves == 6); // retry on next background transition
  next_result=3;
  AndroidAutosave_Init(true);
  AndroidAutosave_Handle(kAutosaveStart); // absent / empty: continue normally
  next_result=4;
  AndroidAutosave_Init(true);
  AndroidAutosave_Handle(kAutosaveStart); // invalid / I/O error: continue normally
  CHECK(loads == 3 && logs == 9 && locks == 0 && lock_error == 0);
  return 0;
}
'''
        with tempfile.TemporaryDirectory(prefix='zelda3-autosave-tests-') as directory:
            folder = Path(directory)
            (folder / 'test.c').write_text(source)
            subprocess.run([str(tc / 'clang.exe'), '--target=x86_64-pc-windows-msvc', '-O1',
                            '-ffreestanding', '-fno-stack-protector', '-c', str(folder / 'test.c'),
                            '-o', str(folder / 'test.obj')], check=True)
            subprocess.run([str(tc / 'ld.lld.exe'), '-flavor', 'link', '/entry:tests', '/subsystem:console',
                            '/nodefaultlib', '/out:' + str(folder / 'test.exe'), str(folder / 'test.obj')], check=True)
            result = subprocess.run([str(folder / 'test.exe')])
            self.assertEqual(result.returncode, 0, f'Native assertion at generated C line {result.returncode}')


if __name__ == '__main__':
    unittest.main()
