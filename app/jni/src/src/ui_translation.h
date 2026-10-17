#pragma once
#include "types.h"
#include "ui_translation_data.h"

// Package memory belongs to the loaded assets container and lives for the game.
bool UiTranslation_Select(const char *language, MemBlk package);
bool UiTranslation_Active(void);
const void *UiTranslation_Get(uint32 id, const void *original);
MemBlk UiTranslation_Block(uint32 id, MemBlk original);
// SRAM keeps US character codes; only the displayed tile changes.
uint16 UiTranslation_NameTile(uint16 character, bool bottom);
bool UiTranslation_RestoreTiles(uint8 *loaded, const uint8 *original,
                               const uint8 *translated, size_t size);
void UiTranslation_RestoreAfterLoad(void);
bool UiTranslation_OriginalTiles(const uint8 *loaded, const uint8 *original,
                                 const uint8 *translated, size_t size);
void UiTranslation_Defer(void);
bool UiTranslation_Resume(void);
