#include "android_autosave.h"
#include "zelda_rtl.h"
#include <SDL.h>

static SDL_atomic_t autosave_enabled;
static bool autosave_background;

void AndroidAutosave_Init(bool enabled) {
  SDL_AtomicSet(&autosave_enabled, enabled);
  autosave_background = false;
}

void AndroidAutosave_SetEnabled(bool enabled) {
  // No frame queue: an immediately following background event must see this value.
  SDL_AtomicSet(&autosave_enabled, enabled);
}

void AndroidAutosave_Handle(enum AndroidAutosaveEvent event) {
  if (event == kAutosaveForeground) {
    autosave_background = false;
    return; // The running session is already in memory; never reload on resume.
  }
  if (event == kAutosaveBackground) {
    if (autosave_background) return;
    autosave_background = true;
  }
  if (!SDL_AtomicGet(&autosave_enabled)) return;

  int command = event == kAutosaveStart ? kSaveLoad_Load : kSaveLoad_Save;
  // Complete in this event handler, before SDL suspends the game thread.
  ZeldaApuLock();
  int result = SaveLoadSlotChecked(command, 0);
  ZeldaApuUnlock();
  const char *status = result == 1 ? "saved" : result == 2 ? "loaded"
      : result == 3 ? "missing or empty" : "error";
  SDL_Log("Autosave: %s save0.sav: %s", command == kSaveLoad_Save ? "save" : "load", status);
}
