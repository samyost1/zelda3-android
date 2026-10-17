# zelda3-android
A port of Zelda3 to Android with a second screen mod for dual screen devices like the AYN Thor.

Original Repository: https://github.com/snesrev/zelda3 <br>
Based on: https://github.com/Waterdish/zelda3-android

The dual-screen mod was made with the help of Claude Code and opencode.

The bottom screen shows a live world map, a dungeon map with the rooms you visited, and a touch inventory where you can tap an item to equip it. On the title screen and during cutscenes it just shows a triforce.

The second screen graphics are made from your ROM while the game runs, so there is no extra setup and the app contains no game assets.

This branch also builds the second screen for desktop/handheld Linux (SDL2), so the same UI runs on dual-screen Linux handhelds.

![](showcase.png)

# Instructions

1. Install the APK from the releases page. Android 13 users: check the releases tab for the Android 13 version of the app.
2. Launch the app and tap "Select ROM" when asked, then pick your "Legend of Zelda, The - A Link to the Past (USA)" rom file.
3. That's it. The app extracts the game assets once and boots straight into the game. Every launch after that goes directly to the game.

**Brazilian Portuguese:** select the already translated `.sfc` or `.smc` ROM
from the spyblack/Denim translation (SHA-1
`D0D09ED41F9C373FE6AFDCCAFBF0DA8C88D3D90D`, 2 MiB without copier header).
The app recognizes it automatically, builds the game data and selects `pt-br`.
The Android second screen and its settings also use Brazilian Portuguese when
`Language = pt-br` is saved, including existing installations. Restart the app
after updating to see the translated interface, with accented pixel lettering.
Only this translated ROM is needed; the IPS patch and original US ROM are not
required on the device. Unzip the ROM before selecting it. New imports also
include the ROM's translated in-game interface: file menus, inventory, HUD,
game-over lettering, graphics and ending text. It follows the translation's
original wording; elements left unchanged by the ROM remain unchanged.

**Other fan translations:** select the translated ROM first, then the original
US ROM when prompted. Spanish, Polish, Dutch, Swedish and Redux are recognized
by checksum; other hacks retaining the US text layout can also be imported.

Setup runs only when `zelda3_assets.dat` is absent. To switch an existing install
to PT-BR, back up and remove that file from the app's files directory, then launch
the app and select the supported translated ROM. Keep your save files and
`zelda3.ini`. Existing PT-BR imports also need this one-time reimport to extract
the new in-game interface. Updating the APK alone updates the Android second
screen, but cannot extract graphics from a ROM the app no longer has.

The rom is only read to build the assets (zelda3_assets.dat) — it is never copied or kept, and the app ships no game assets of its own.

The game itself is controller only, but the bottom screen has full touch controls (map, inventory, equipping items).

## Settings

Common options can be changed from the settings screen on the bottom panel. Everything else is in Android/data/com.dishii.zelda3/files/zelda3.ini — edit it with a text editor.

Default settings:
- L3 Turbo button
- 16:9 aspect ratio
- Fullscreen (no android on-screen controls)

## Optional: providing zelda3_assets.dat yourself

If you'd rather extract the assets on a computer, drop your zelda3_assets.dat into Android/data/com.dishii.zelda3/files and the app will use it and skip the ROM prompt. You can create it with the manual instructions on the original repository, or on-device as follows if you don't have access to a computer:

1. Download PyDroid: https://play.google.com/store/apps/details?id=ru.iiec.pydroid3&hl=en_US. Choose to skip any options that ask for money, you can do all of the following steps without paying.
2. Open the hamburger menu at the top left of the app and select Pip.
3. Type in "Pillow" without the quotes and it will have you install the repository app from the app store.
4. Once the repository app is installed, you can install "Pillow" and "pyyaml"
5. Download the **source code** zip file for zelda3 at https://github.com/snesrev/zelda3/releases/tag/v0.3. The zip file with the exe file in it will not work.
6. Extract the zip file.
7. Place your rom file in the main zelda3 directory that you extracted, the same one as extract_assets.bat, and rename it to zelda3.sfc
8. Open PyDroid again, open the hamburger menu, and select Terminal.
9. Navigate to where you placed the rom file. (If you are unfamiliar with terminal commands, "ls" lists the folders and files and "cd Foldername" changes the directory. An example using the 0.3 release of zelda3 above would be "cd Download" "cd zelda3-0.3" "cd zelda3-0.3" or simply "cd Download/zelda3-0.3/zelda3-0.3")
10. Paste in this command `python3 assets/restool.py --extract-from-rom`
11. It should pause for a while and when it finishes you should be able to see zelda3_assets.dat in the same folder as your rom. You can go ahead and copy that to the Android/data/com.dishii.zelda3/files location.

# Building

The native code lives in `app/jni/src` and builds two ways; pick the one for your target. `second_screen.c` is the shared, platform-free core (game-state reads + art generation); each target compiles only its own frontend from `src/platform/`:

- `src/platform/android/` — JNI bridge (`second_screen_jni.c`) + no-op SDL stubs
- `src/platform/linux/` — the SDL UI (`second_screen_sdl.c`) + its generated tables

**Android:** open the project in Android Studio and build/run, or `./gradlew assembleDebug`. The NDK build (`jni/Android.mk`) compiles `src/*.c` + `src/platform/android/*.c`.

The PT-BR BPS is committed, so normal builds need no ROMs or generation step.
See [translation tooling](tools/translations/README.md) to reproduce the patch
or run local import checks with your own ROMs.

**Linux (desktop / handheld):**
```
cd app/jni/src
make zelda3          # needs SDL2 dev headers (libsdl2-dev / SDL2-devel / sdl2)
```
This compiles `src/*.c` + `src/platform/linux/*.c` into the `zelda3` binary. Enable the second screen with `ZELDA3_SECOND_SCREEN=1` (env knobs are documented at the top of `second_screen_sdl.c`).

The generated tables (`src/platform/linux/ss_sheets.h`, `ss_textures.h`) come from `app/src/main/assets/secondscreen/` and are committed, so a normal build doesn't regenerate them. If those assets change, run `python tools/secondscreen/gen_linux_tables.py` from the repo root (needs Pillow).

# MSU-1 music (custom soundtracks)

To use an MSU-1 audio pack instead of the built-in music:

1. Copy the pack files (`alttp_msu-1.pcm`, `alttp_msu-2.pcm`, ...) into `Android/data/com.dishii.zelda3/files/msu/`.
2. In `Android/data/com.dishii.zelda3/files/zelda3.ini`, set `EnableMSU = true`, `MSUPath = msu/alttp_msu-`, and `AudioFreq = 44100` (use `48000` for OPUZ packs).
3. Relaunch the game.

### Quick states and controller shortcuts (Android)

The first card in **SAVE STATES** is **QUICK STATE** (PT-BR: **ESTADO RÁPIDO**).
It shares `saves/save1.sav` with the settings **SAVE STATE / LOAD STATE** buttons
and the controller shortcuts. Existing manual slots 1–4 still use `save2.sav`
through `save5.sav`; autosave remains separate in `save0.sav`.
Old quick states without a preview remain loadable and show **NO IMAGE**.

**REMAP BUTTONS** now includes **SAVE** and **LOAD**, initially R2 and L2 when
those buttons are unused. Select a command and press/release a controller button,
or select **CLEAR** to disable its binding. Moving an occupied button requires
confirmation. Custom INI combinations are protected and must be edited in the INI.
`[GamepadMap] QuickSave` and `QuickLoad` store these assignments; an empty value
means disabled. Saving/loading happens once per press and reports its result on
the second screen. The autosave lifecycle behavior is unchanged by this feature.

Host verification: `python -m unittest discover -s tools/tests -p 'test_*.py' -v`.
Native mapping and save-failure tests run on Windows with the configured Android
NDK (or `ANDROID_NDK_HOME`); they compile production functions with fake I/O and
require no ROM. Device verification should cover R2/L2, reassignment to R3/L3,
clearing a binding, transfer/cancel, and saving/loading from all three entry points.

### Automatic resume (Android)

With **AUTOSAVE** enabled, the game saves `saves/save0.sav` when it enters the
background (Home, Recents or screen lock), before SDL suspends the game thread.
A normal engine exit also saves. Opening a new session loads that file; returning
to a session still in memory does not reload it. Disabling the option disables
both automatic saving and loading, without deleting the previous file.

Autosaves are written to a temporary file and replace the previous state only
after a successful write and close. Missing/empty or invalid automatic states do
not prevent startup. Logs prefixed `Autosave:` report load/save results. Quick
and manual state files remain independent. There is no periodic saving, and a
crash, abrupt termination or power loss can still prevent the latest save.

On-device acceptance: enable autosave, play to a recognizable point, open
Recents, swipe the app away, and relaunch. Verify `save0.sav` was updated and the
same point resumes. Repeat using Home, screen lock, and swapped screens; also
verify that simply returning from the background continues the live session.
