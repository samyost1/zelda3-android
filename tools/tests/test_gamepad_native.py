"""Run production gamepad mapping/input functions with fake I/O on Windows.

Uses the Android NDK's host Clang and LLD, without a C runtime or game assets.
The harness extracts functions verbatim so it exercises the actual engine rules.
"""
from pathlib import Path
import os
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'app/jni/src/src'


def toolchain():
    ndk = os.environ.get('ANDROID_NDK_HOME')
    props = ROOT / 'local.properties'
    if not ndk and props.exists():
        match = re.search(r'^ndk.dir=(.*)$', props.read_text(), re.M)
        if match:
            ndk = match[1].strip().replace('\\:', ':').replace('\\\\', '\\')
    return Path(ndk) / 'toolchains/llvm/prebuilt/windows-x86_64/bin' if ndk else None


class NativeGamepadTests(unittest.TestCase):
    def test_mapping_capture_and_press_edges(self):
        tc = toolchain()
        if os.name != 'nt' or not tc or not (tc / 'clang.exe').exists():
            self.skipTest('Requires Windows and Android NDK (local.properties or ANDROID_NDK_HOME)')
        config = (SRC / 'config.c').read_text()
        header = (SRC / 'config.h').read_text()
        main = (SRC / 'main.c').read_text()
        enums = header[header.index('enum {'):header.index('enum {\n  kOutputMethod')]
        buttons = header[header.index('enum {\n  kGamepadBtn_'):]
        buttons = buttons[:buttons.index('};') + 2]
        mapping = config[config.index('typedef struct GamepadMapEnt'):config.index('static void RegisterDefaultKeys')]
        defaults = config[config.index('  if (!has_quick_binding[0]'):config.index('\n#endif', config.index('  if (!has_quick_binding[0]'))]
        quick = config[config.index('    if (StringEqualsNoCase(key, "QuickSave")'):config.index('    for (int i = 0; i < countof(kKeyNameId); i++)', config.index('  } else if (section == 5)'))]
        inputs = main[main.index('static void HandleGamepadInput(int button, bool pressed) {'):main.index('\nstatic void HandleVolumeAdjustment', main.index('static void HandleGamepadInput(int button, bool pressed) {'))]
        axes = main[main.index('static void HandleGamepadAxisInput(int gamepad_id, int axis, int value) {'):main.index('static bool LoadRom', main.index('static void HandleGamepadAxisInput(int gamepad_id, int axis, int value) {'))]
        prelude = r'''
typedef unsigned char uint8;
typedef unsigned short uint16;
typedef unsigned int uint32;
typedef unsigned long long size_t;
typedef _Bool bool;
#define true 1
#define false 0
#define NULL ((void*)0)
#define countof(a) (sizeof(a)/sizeof((a)[0]))
static unsigned char heap[65536];
void *realloc(void *p, size_t n) { return heap; }
void Die(const char *s) { __builtin_trap(); }
int fprintf(void *f, const char *s, ...) { return 0; }
#define stderr NULL
static int lower(int c) { return c >= 'A' && c <= 'Z' ? c + 32 : c; }
const char *StringStartsWithNoCase(const char *s, const char *prefix) {
  while (*prefix) if (lower(*s++) != lower(*prefix++)) return NULL;
  return s;
}
bool StringEqualsNoCase(const char *s, const char *p) {
  const char *end = StringStartsWithNoCase(s, p); return end && !*end;
}
char *NextDelim(char **value, char delim) {
  char *s = *value; if (!s) return NULL;
  char *p = s; while (*p && *p != delim) p++;
  if (*p) { *p = 0; *value = p + 1; } else *value = NULL;
  return s;
}
'''
        harness = r'''
volatile int g_ss_capture_button = -1;
static uint32 g_gamepad_modifiers;
static uint8 g_gamepad_buttons;
static bool g_gamepad_stick_wait_neutral;
int _fltused;
enum { SDL_CONTROLLER_AXIS_LEFTX, SDL_CONTROLLER_AXIS_LEFTY,
       SDL_CONTROLLER_AXIS_TRIGGERLEFT, SDL_CONTROLLER_AXIS_TRIGGERRIGHT };
float ApproximateAtan2(int a, int b) { return 0; }
static uint16 g_gamepad_last_cmd[kGamepadBtn_Count];
static int saves, loads, releases;
void HandleCommand(int command, bool pressed) {
  if (!pressed) { releases++; return; }
  if (command == kKeys_QuickSave) saves++;
  if (command == kKeys_QuickLoad) loads++;
}
'''
        checks = r'''
#define CHECK(x) if (!(x)) return __LINE__;
static void reset_map(void) {
  for (int b = 0; b < kGamepadBtn_Count; b++) joymap_first[b] = 0;
  joymap_size = joymap_free = 0; has_quick_binding[0] = has_quick_binding[1] = false;
}
int tests(void) {
  uint8 bindings[14];
  init_defaults(); GamepadMap_GetBindings(bindings);
  CHECK(bindings[12] == kGamepadBtn_R2 && bindings[13] == kGamepadBtn_L2);
  HandleGamepadInput(kGamepadBtn_R2, true);
  HandleGamepadInput(kGamepadBtn_R2, true);
  CHECK(saves == 1);
  HandleGamepadInput(kGamepadBtn_R2, false);
  HandleGamepadInput(kGamepadBtn_R2, true);
  CHECK(saves == 2);
  HandleGamepadInput(kGamepadBtn_R2, false);
  g_ss_capture_button = -2;
  HandleGamepadInput(kGamepadBtn_L2, true);
  CHECK(g_ss_capture_button == -2 && loads == 0);
  HandleGamepadInput(kGamepadBtn_L2, true);
  HandleGamepadInput(kGamepadBtn_L2, false);
  CHECK(g_ss_capture_button == kGamepadBtn_L2 && loads == 0);
  HandleGamepadInput(kGamepadBtn_R2, true);
  HandleGamepadInput(kGamepadBtn_R2, false);
  CHECK(saves == 2);
  g_ss_capture_button = -1;
  HandleGamepadInput(kGamepadBtn_L2, true);
  CHECK(loads == 1);
  HandleGamepadInput(kGamepadBtn_L2, false);
  g_ss_capture_button = -3;
  HandleGamepadInput(kGamepadBtn_R2, true);
  g_ss_capture_button = -1;
  HandleGamepadInput(kGamepadBtn_R2, true);
  HandleGamepadInput(kGamepadBtn_R2, false);
  CHECK(saves == 2);
  HandleGamepadInput(kGamepadBtn_R2, true);
  CHECK(saves == 3);
  HandleGamepadInput(kGamepadBtn_R2, false);
  HandleGamepadAxisInput(1, SDL_CONTROLLER_AXIS_LEFTX, 20000);
  CHECK(g_gamepad_buttons != 0);
  g_ss_capture_button = -2;
  HandleGamepadAxisInput(1, SDL_CONTROLLER_AXIS_LEFTX, 21000);
  CHECK(g_gamepad_buttons == 0);
  g_ss_capture_button = -1;
  HandleGamepadAxisInput(1, SDL_CONTROLLER_AXIS_LEFTX, 22000);
  CHECK(g_gamepad_buttons == 0);
  HandleGamepadAxisInput(1, SDL_CONTROLLER_AXIS_LEFTX, 0);
  HandleGamepadAxisInput(1, SDL_CONTROLLER_AXIS_LEFTX, 20000);
  CHECK(g_gamepad_buttons != 0);
  g_ss_capture_button = -3;
  HandleGamepadAxisInput(1, SDL_CONTROLLER_AXIS_LEFTX, 22000);
  CHECK(g_gamepad_buttons == 0);
  g_ss_capture_button = -1;
  bindings[12] = kGamepadBtn_R3; bindings[13] = 0xff;
  for (int i = 0; i < 200; i++) GamepadMap_SetBindings(bindings);
  CHECK(FindCmdForGamepadButton(kGamepadBtn_R2, 0) == 0);
  CHECK(FindCmdForGamepadButton(kGamepadBtn_R3, 0) == kKeys_QuickSave);
  CHECK(FindCmdForGamepadButton(kGamepadBtn_L2, 0) == 0);
  reset_map();
  char empty[] = ""; parse_quick("QuickSave", empty); init_defaults();
  GamepadMap_GetBindings(bindings);
  CHECK(bindings[12] == 0xff && bindings[13] == kGamepadBtn_L2);
  reset_map();
  GamepadMap_Add(kGamepadBtn_R2, 0, kKeys_Controls);
  GamepadMap_Add(kGamepadBtn_A, 1u << kGamepadBtn_L2, kKeys_Save + 4);
  init_defaults(); GamepadMap_GetBindings(bindings);
  CHECK(bindings[12] == 0xff && bindings[13] == 0xff);
  CHECK(GamepadMap_ProtectedButtons() & (1u << kGamepadBtn_L2));
  CHECK(GamepadMap_ProtectedButtons() & (1u << kGamepadBtn_A));
  GamepadMap_SetBindings(bindings);
  CHECK(FindCmdForGamepadButton(kGamepadBtn_A, 1u << kGamepadBtn_L2) == kKeys_Save + 4);
  reset_map();
  char r3[] = "R3"; parse_quick("QuickSave", r3); init_defaults();
  CHECK(FindCmdForGamepadButton(kGamepadBtn_R3, 0) == kKeys_QuickSave);
  return 0;
}
'''
        source = prelude + enums + buttons + mapping
        source += '\nvoid init_defaults(void) {\n' + defaults + '\n}\n'
        source += 'bool parse_quick(const char *key, char *value) {\n' + quick + '\nreturn false; }\n'
        source += harness + inputs + axes + checks
        with tempfile.TemporaryDirectory(prefix='zelda3-native-tests-') as directory:
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
