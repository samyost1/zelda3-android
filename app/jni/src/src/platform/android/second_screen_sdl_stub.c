// No-op SecondScreenSDL_* hooks for the Android build (the second screen is the
// Java Presentation UI). Keeps main.c link-clean without compiling the SDL UI.
#include <SDL.h>
#include <stdbool.h>
#include <stdint.h>

bool SecondScreenSDL_Init(SDL_Window *main_window) { (void)main_window; return false; }
bool SecondScreenSDL_HandleEvent(const SDL_Event *e) { (void)e; return false; }
void SecondScreenSDL_Update(void) {}
void SecondScreenSDL_Shutdown(void) {}

// The Android letterbox stays black; the Presentation UI owns the bottom panel.
const uint32_t *LetterboxBackground(int dw, int dh, int vx, int vy, int vw, int vh) {
  (void)dw; (void)dh; (void)vx; (void)vy; (void)vw; (void)vh; return NULL;
}
