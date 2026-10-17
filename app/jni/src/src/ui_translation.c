#include "ui_translation.h"
#include <string.h>

static const uint8 *ui_package;
static bool ui_deferred;
// Packed language entries need not be aligned. Copy once at selection so all
// uint16 resources are safe on ARM as well as desktop architectures.
static uint32 ui_storage[(UI_PACKAGE_SIZE + 3) / 4];

static uint32 UiRead32(const uint8 *p) {
  return p[0] | (uint32)p[1] << 8 | (uint32)p[2] << 16 | (uint32)p[3] << 24;
}

static uint32 UiCrc32(const uint8 *p, size_t size) {
  uint32 crc = 0xffffffffu;
  while (size--) {
    crc ^= *p++;
    for (int i = 0; i < 8; i++) crc = (crc >> 1) ^ ((crc & 1) * 0xedb88320u);
  }
  return crc ^ 0xffffffffu;
}

bool UiTranslation_Select(const char *language, MemBlk package) {
  static const uint8 kRomSha1[20] = {
    0xd0,0xd0,0x9e,0xd4,0x1f,0x9c,0x37,0x3f,0xe6,0xaf,
    0xdc,0xca,0xfb,0xf0,0xda,0x8c,0x88,0xd3,0xd9,0x0d,
  };
  ui_package = NULL;
  ui_deferred = false;
  if (!language || strcmp(language, "pt-br") || !package.ptr || package.size != UI_PACKAGE_SIZE)
    return false;
  const uint8 *p = package.ptr;
  if (memcmp(p, "Z3UIBR01", 8) || UiRead32(p + 8) != 1 ||
      UiRead32(p + 12) != countof(kUiResourceLayout) ||
      memcmp(p + 16, kRomSha1, 20) || UiRead32(p + 36) != package.size)
    return false;
  for (size_t i = 0; i < countof(kUiResourceLayout); i++) {
    for (int j = 0; j < 3; j++)
      if (UiRead32(p + 40 + i * 12 + j * 4) != kUiResourceLayout[i][j]) return false;
    // The generated layout is fixed for the recognized ROM and independently
    // pins every offset and length, including alignment for uint16 access.
    if ((size_t)kUiResourceLayout[i][1] + kUiResourceLayout[i][2] > package.size - 4)
      return false;
  }
  if (UiRead32(p + package.size - 4) != UI_PACKAGE_CRC ||
      UiCrc32(p, package.size - 4) != UI_PACKAGE_CRC) return false;
  for (size_t i = 0; i < package.size; i++) ((uint8 *)ui_storage)[i] = p[i];
  ui_package = (const uint8 *)ui_storage;
  return true;
}

bool UiTranslation_Active(void) { return ui_package != NULL && !ui_deferred; }

void UiTranslation_Defer(void) { ui_deferred = true; }

bool UiTranslation_Resume(void) {
  bool changed = ui_package && ui_deferred;
  ui_deferred = false;
  return changed;
}

MemBlk UiTranslation_Block(uint32 id, MemBlk original) {
  if (UiTranslation_Active()) {
    int lo = 0, hi = countof(kUiResourceLayout);
    while (lo < hi) {
      int mid = (lo + hi) >> 1;
      const uint32 *entry = kUiResourceLayout[mid];
      if (id == entry[0]) return (MemBlk){ui_package + entry[1], entry[2]};
      if (id < entry[0]) hi = mid; else lo = mid + 1;
    }
  }
  return original;
}

const void *UiTranslation_Get(uint32 id, const void *original) {
  return UiTranslation_Block(id, (MemBlk){original, 0}).ptr;
}

uint16 UiTranslation_NameTile(uint16 character, bool bottom) {
  if (!UiTranslation_Active()) return character + (bottom ? 16 : 0);
  uint8 c = (character & 15) | ((character >> 1) & 0xf0);
  if (c >= 0x76) c -= 0x42;
  else if (c == 0x5f) c = 8;
  else if (c == 0x60) c = 0x22;
  else if (c == 0x61) c = 0x3e;
  if (c >= 121) c = 0x59;
  const uint8 *map = UiTranslation_Get(kUi_NameFontMap, NULL);
  return map[c * 3 + (bottom ? 1 : 0)];
}

bool UiTranslation_RestoreTiles(uint8 *loaded, const uint8 *original,
                               const uint8 *translated, size_t size) {
  if (!UiTranslation_Active() || !size || (size & 15)) return false;
  size_t mismatches = 0;
  for (size_t i = 0; i < size; i += 16)
    if (memcmp(loaded + i, original + i, 16) && ++mismatches > 8) return false;
  bool changed = false;
  for (size_t i = 0; i < size; i += 16) {
    if (!memcmp(loaded + i, original + i, 16) && memcmp(original + i, translated + i, 16)) {
      for (int j = 0; j < 16; j++) loaded[i + j] = translated[i + j];
      changed = true;
    }
  }
  return changed;
}

bool UiTranslation_OriginalTiles(const uint8 *loaded, const uint8 *original,
                                 const uint8 *translated, size_t size) {
  size_t us = 0, pt = 0;
  if (!size || (size & 15)) return false;
  for (size_t i = 0; i < size; i += 16) {
    if (!memcmp(original + i, translated + i, 16)) continue;
    if (!memcmp(loaded + i, original + i, 16)) us++;
    if (!memcmp(loaded + i, translated + i, 16)) pt++;
  }
  return us > pt;
}
