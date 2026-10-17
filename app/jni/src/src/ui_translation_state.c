#include "ui_translation.h"
#include "assets.h"
#include "zelda_rtl.h"
#include "variables.h"
#include "load_gfx.h"
#include "hud.h"
#include <string.h>

static void ExpandHalfSprite(uint8 *dst, const uint8 *src) {
  for (int tile = 0; tile < 32; tile++, src += 24, dst += 32) {
    for (int row = 0; row < 8; row++) {
      uint8 a = src[row * 2], b = src[row * 2 + 1], c = src[16 + row];
      dst[row * 2] = a;
      dst[row * 2 + 1] = b;
      dst[16 + row * 2] = c;
      dst[17 + row * 2] = a | b | c;
    }
  }
}

// Old snapshots contain their own graphics. Refresh identified UI banks without
// touching progress, custom controller glyphs, dialogue pixels or other banks.
void UiTranslation_RestoreAfterLoad(void) {
  UiTranslation_Resume(); // A newly loaded PT snapshot can replace an old one.
  if (!UiTranslation_Active()) return;
  static uint8 original[4096], translated[4096];
  int module = main_module_index;
  if (module == 18 && submodule_index >= 7 && submodule_index <= 9) {
    const uint8 *us = FindInAssetArray(64, 5).ptr;
    ExpandHalfSprite(original, us);
    ExpandHalfSprite(translated, UiTranslation_Get(kUi_sprite_05, us));
    bool migrated = UiTranslation_RestoreTiles((uint8 *)&g_zenv.vram[0x4400], original, translated, 1024);
    UiTranslation_RestoreTiles(&g_ram[0x11000], original, translated, 1024);
    if (migrated && ancilla_type[0] == 1) {
      ancilla_x_lo[8] = ancilla_x_lo[7];
      ancilla_x_hi[8] = ancilla_x_hi[7];
    }
    if (ancilla_type[0] == 3) {
      const uint8 *x = UiTranslation_Get(kUi_GameOverUnfurl, NULL);
      flag_for_boomerang_in_place = 8;
      for (int i = 0; i < 9; i++) { ancilla_x_lo[i] = x[i]; ancilla_x_hi[i] = 0; }
    }
  }
  if ((module >= 1 && module <= 4) || module == 26) {
    const uint8 *font = FindIndexInMemblk(kDialogueFont(0), 0).ptr;
    const uint8 *pt_font = UiTranslation_Get(kUi_InterfaceFont, font);
    // These snapshots also contain their existing header/credits tilemaps.
    // Keep font and table encoding together until a complete screen redraw.
    if (UiTranslation_OriginalTiles((uint8 *)&g_zenv.vram[0x7000], font, pt_font, 4096))
      UiTranslation_Defer();
  } else if (module >= 5 && module <= 25 && module != 20) {
    const int packs[3] = {0x6a, 0x6b, 0x69};
    if (module == 14 && submodule_index == 1 && overworld_map_state >= 8 && overworld_map_state <= 11) {
      if (Decompress(original, FindInAssetArray(64, 0x6a).ptr) == 2048 &&
          Decomp_spr(translated, 0x6a) == 2048 &&
          UiTranslation_OriginalTiles((uint8 *)&g_zenv.vram[0x7000], original, translated, 2048)) {
        UiTranslation_Defer();
        return;
      }
    }
    for (int i = 0; i < 3; i++) {
      MemBlk us = FindInAssetArray(64, packs[i]);
      if (Decompress(original, us.ptr) != 2048 || Decomp_spr(translated, packs[i]) != 2048)
        continue;
      UiTranslation_RestoreTiles((uint8 *)&g_zenv.vram[0x7000 + i * 0x400], original, translated, 2048);
      UiTranslation_RestoreTiles(&g_ram[0x14000], original, translated, 2048);
    }
  }
  // Opening/closing scroll the completed canvas; redraw its labels together
  // with the graphics. Bottle expansion retains its partially erased canvas.
  if (module == 14 && submodule_index == 1 &&
      ((overworld_map_state >= 2 && overworld_map_state <= 7) || overworld_map_state == 12)) {
    Hud_DrawYButtonItems();
    Hud_DrawAbilityBox();
    Hud_DrawEquipmentBox();
    Hud_DrawSelectedYButtonItem();
    memcpy(&g_zenv.vram[0x6800], &g_ram[0x1000], 0x800);
  }
}
