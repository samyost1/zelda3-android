#pragma once
#include <stdbool.h>

enum AndroidAutosaveEvent {
  kAutosaveStart,
  kAutosaveBackground,
  kAutosaveForeground,
  kAutosaveExit,
};

// Init and Handle run on the game thread. SetEnabled may run on the Android UI thread.
void AndroidAutosave_Init(bool enabled);
void AndroidAutosave_SetEnabled(bool enabled);
void AndroidAutosave_Handle(enum AndroidAutosaveEvent event);
