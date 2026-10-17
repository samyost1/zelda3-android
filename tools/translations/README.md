# PT-BR import tooling

The Android app recognizes the exact translated ROM by SHA-1 and applies
`zelda3_assets_ptbr.bps` to reconstruct baseline assets. It then extracts and
converts the PT-BR dialogue, dictionary and font from that same ROM and sets
`Language = pt-br`. Other translations retain the two-ROM setup flow.

Supported inputs, after stripping an optional 512-byte copier header:

| Input | Bytes | SHA-1 |
| --- | ---: | --- |
| Original US ROM | 1,048,576 | `6D4F10A8B10E10DBE624CB23CF03B88BB8252973` |
| spyblack/Denim PT-BR ROM | 2,097,152 | `D0D09ED41F9C373FE6AFDCCAFBF0DA8C88D3D90D` |

## Reproduce the BPS

Run from the repository root, using Python 3 and your own ROMs. The tools accept
raw `.sfc`/`.smc` files or a ZIP containing exactly one ROM. The Android picker
accepts the raw ROM; extract ZIPs before selecting them on the device.

```powershell
python tools/translations/build_ptbr_patch.py --us-rom "path/to/us.sfc" --translated-rom "path/to/ptbr.sfc"
```

The script validates both input hashes, applies the existing US BPS in memory,
builds a deterministic BPS using the translated ROM as its source, and verifies
the result byte for byte before writing the new patch. It saves no ROM or `.dat`.
Regenerate it whenever `zelda3_assets.bps` changes.

For the current US BPS:

- PT-BR BPS: 113,157 bytes, SHA-256 `3411ff12d40b7f06017ca9251503a4fa4791bf75f0f69f14da3ca196cb9b68e7`.
- Baseline output: 683,888 bytes, SHA-256 `0fe2e4bd75d70f06fb9a74cd3a9cb336c838149b831b56e8792114a89292c793`.

## Verify

```powershell
python -m unittest discover -s tools/tests -p "test_*.py" -v
python tools/translations/verify_ptbr.py --us-rom "path/to/us.sfc" --translated-rom "path/to/ptbr.sfc"
```

The first command needs no ROM. The second needs a JDK 9+ (`javac`/`java` on
PATH); it compiles the production Java code for Java 8 and checks all 397
messages, the 97-entry dictionary, font remapping and widths against golden
values independently computed using the upstream PT tools. It also checks
single-ROM/two-ROM output equivalence, preservation of non-language assets,
generic US-layout extraction, and rejection of modified inputs/corrupt patches.
Temporary ROM copies and compiled classes are automatically removed.

Reference rules:

- [Upstream PT text decoder and alternative encoder](https://github.com/snesrev/zelda3/blob/master/assets/text_compression.py).
- [Upstream font remapper](https://github.com/snesrev/zelda3/blob/master/assets/sprite_sheets.py).
- Font tiles start at file offset `0x70000`. The table at `0x77C09` has 121
  records of `[top tile, bottom tile, width]`.
- Text starts at `0xE0000`, continues at `0x75F40` and stops after 397 messages.
  Escape `0x62` introduces a character index. Dictionary pointers start at
  `0x74703`; dictionary escapes are normalized too.
- Commands are converted to the engine's alternative encoding; language flags
  are `3`. Reserved bytes `0x81..0x87`, `Sound 64`, `Window 0` and `ScrollSpd 0`
  are omitted as in upstream.

## Android acceptance checks

On an installation without `zelda3_assets.dat`, select only the supported PT-BR
ROM. The game should start without asking for the US ROM, write `Language = pt-br`
and retain that setting after a restart. Also check a copy with a 512-byte copier
header. Verify accented dialogue, player-name insertion, numeric substitutions,
choices and scrolling in game. Verify that selecting a US ROM still starts in
English on a clean install and other translations still request the US ROM.

The import tests do not replace these device checks. PT-BR imports now include
a separately versioned UI package inside the PT-BR language entry of the assets
container. It stores only the recognized ROM's graphics, font and text tables;
the app does not execute the hack's code. The engine adapts name rendering,
game-over animation and the ending row format. The original asset entries remain
intact, and absent or invalid UI packages fall back to the original interface.
Existing imports require reimporting the ROM to obtain these extra resources.
Separately, the Android second screen uses a built-in PT-BR catalog
whenever `Language = pt-br` is saved. Updating an existing PT-BR installation
and restarting the app is enough to activate this UI translation.

## In-game interface mapping and verification

See [the mapping and device checklist](../../docs/ptbr-ui-mapping.md).
`ptbr_ui_manifest.json` records offsets, lengths and hashes, never extracted
graphics. Reproduce it with `map_ui.py --us-rom <us> --translated-rom <ptbr>`,
then run `generate_ui_sources.py` to update the Java/C metadata. No upstream
checkout is needed to run either tool.

`verify_ptbr.py` verifies all 42 resources using the production Java importer
and writes ignored `build/ui-package.bin` and `build/ui-second-screen-base.bin`
fixtures for the native tests. Run it before
`python -m unittest discover -s tools/tests -p "test_*.py" -v` to include the
native package, graphics, state refresh, game-over and credits checks. These
tests need the Windows NDK configured in `local.properties` as before.

The second-screen atlas regression renders the production letter, counter and
icon sheets from real US graphics, then compares every pixel with PT-BR active,
both with a warm cache and a fresh atlas. The second screen deliberately reads
the original banks because its fixed tile positions differ from the PT-BR HUD.
The game's HUD continues to use the translated resources.

For resource previews, run `preview_ui.py --us-rom <us> --translated-rom <ptbr>`
with Pillow installed. Generated PNGs stay under ignored `build/`; they are
grayscale resource previews, not device screenshots or a replacement for them.

The test suite also compiles `SecondScreenTextTest` when a JDK is on PATH. It
checks language selection, English fallback, catalog/font coverage and text
layout across five available widths. Device checks should cover tabs, settings,
button remapping (physical button names remain unchanged), save/load states,
dungeon headings and accented lettering after an app restart.
