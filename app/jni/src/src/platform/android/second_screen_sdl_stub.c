// No-op SecondScreenSDL_* hooks for the Android build (the second screen is the
// Java Presentation UI). Keeps main.c link-clean without compiling the SDL UI.
#include <SDL.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include "../linux/ss_textures.h"   // baked theme background tiles (menu/stone)

bool SecondScreenSDL_Init(SDL_Window *main_window) { (void)main_window; return false; }
bool SecondScreenSDL_HandleEvent(const SDL_Event *e) { (void)e; return false; }
void SecondScreenSDL_Update(void) {}
void SecondScreenSDL_Shutdown(void) {}

// --- Main-window letterbox chrome ----

// SS_* core - indoor/dungeon state drives the theme.
bool SS_IsIndoors(void);
int  SS_GetDungeon(void);

// palette
#define COL(r,g,b) (0xff000000u | ((r) << 16) | ((g) << 8) | (b))
enum {
  COL_GOLD      = COL(232, 194, 96),
  COL_GOLD_DARK = COL(122, 88, 30),
  COL_BOX       = COL(12, 12, 12),
};
#undef COL

static uint32_t *g_lb_buf;
static int g_lb_dw, g_lb_dh, g_lb_vx, g_lb_vy, g_lb_vw, g_lb_vh, g_lb_theme = -1;

static void lb_fill(uint32_t *buf, int dw, int dh, int x, int y, int w, int h, uint32_t c) {
  if (x < 0) { w += x; x = 0; }
  if (y < 0) { h += y; y = 0; }
  if (x + w > dw) w = dw - x;
  if (y + h > dh) h = dh - y;
  for (int yy = 0; yy < h; yy++) {
    uint32_t *row = &buf[(size_t)(y + yy) * dw + x];
    for (int xx = 0; xx < w; xx++) row[xx] = c;
  }
}

// One frame band of thickness t hugging the outside of (rx,ry,rw,rh); grows it.
static void lb_ring(uint32_t *buf, int dw, int dh, int *rx, int *ry, int *rw, int *rh, int t, uint32_t c) {
  lb_fill(buf, dw, dh, *rx - t, *ry - t, *rw + 2 * t, t, c);   // top
  lb_fill(buf, dw, dh, *rx - t, *ry + *rh, *rw + 2 * t, t, c); // bottom
  lb_fill(buf, dw, dh, *rx - t, *ry, t, *rh, c);              // left
  lb_fill(buf, dw, dh, *rx + *rw, *ry, t, *rh, c);            // right
  *rx -= t; *ry -= t; *rw += 2 * t; *rh += 2 * t;
}

const uint32_t *LetterboxBackground(int dw, int dh, int vx, int vy, int vw, int vh) {
  bool indoors = SS_IsIndoors();
  int dungeon_info = SS_GetDungeon();
  bool in_house = indoors && (dungeon_info & 0xFF) == 0xFF;
  int theme = (indoors && !in_house) ? 1 : 0;  // 1 = dungeon stone, 0 = menu cloth

  if (g_lb_buf && dw == g_lb_dw && dh == g_lb_dh && vx == g_lb_vx && vy == g_lb_vy &&
      vw == g_lb_vw && vh == g_lb_vh && theme == g_lb_theme)
    return NULL;  // unchanged: the renderer reuses its texture

  if (!g_lb_buf || dw != g_lb_dw || dh != g_lb_dh) {
    free(g_lb_buf);
    g_lb_buf = malloc((size_t)dw * dh * 4);
    if (!g_lb_buf) return NULL;
  }
  g_lb_dw = dw, g_lb_dh = dh, g_lb_vx = vx, g_lb_vy = vy, g_lb_vw = vw, g_lb_vh = vh, g_lb_theme = theme;

  const uint32_t *tile = theme ? (const uint32_t *)kSSTexStone : (const uint32_t *)kSSTexMenu;
  int tw = theme ? kSSTexStone_W : kSSTexMenu_W;
  int th = theme ? kSSTexStone_H : kSSTexMenu_H;
  int zoom = dh / 360; if (zoom < 2) zoom = 2;
  for (int y = 0; y < dh; y++) {
    const uint32_t *srow = &tile[(y / zoom % th) * tw];
    uint32_t *drow = &g_lb_buf[(size_t)y * dw];
    for (int x = 0; x < dw; x++) drow[x] = srow[x / zoom % tw];
  }

  // Frame the play area with the map panel's gold double border.
  int u = dh / 240; if (u < 1) u = 1;
  int rx = vx, ry = vy, rw = vw, rh = vh;
  lb_ring(g_lb_buf, dw, dh, &rx, &ry, &rw, &rh, 1 * u, COL_BOX);        // shadow gap
  lb_ring(g_lb_buf, dw, dh, &rx, &ry, &rw, &rh, 2 * u, COL_GOLD);       // inner gold
  lb_ring(g_lb_buf, dw, dh, &rx, &ry, &rw, &rh, 2 * u, COL_GOLD_DARK);  // outer dark gold
  return g_lb_buf;
}
