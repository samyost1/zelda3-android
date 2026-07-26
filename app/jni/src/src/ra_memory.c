#include "ra_memory.h"

#include <limits.h>
#include <string.h>

#ifndef RA_MEMORY_TEST
#include "zelda_rtl.h"
#endif

enum {
  kRaRamSize = 0x20000,
  kRaSramBase = 0x20000,
  kRaSramSize = 0x2000,
  kRaMemoryEnd = kRaSramBase + kRaSramSize,
};

static uint32_t g_invalid_read_count;

#ifdef RA_MEMORY_TEST
static uint8_t *g_test_ram;
static uint8_t *g_test_sram;
#endif

static uint8_t *RaMemoryRam(void) {
#ifdef RA_MEMORY_TEST
  return g_test_ram;
#else
  return g_zenv.ram;
#endif
}

static uint8_t *RaMemorySram(void) {
#ifdef RA_MEMORY_TEST
  return g_test_sram;
#else
  return g_zenv.sram;
#endif
}

uint32_t RaMemoryRead(uint32_t address, uint8_t *buffer, uint32_t size,
                      rc_client_t *client) {
  uint32_t ram_bytes = 0;
  uint8_t *ram;
  uint8_t *sram;

  (void)client;
  if (size == 0)
    return 0;

  if (!buffer || address > UINT32_MAX - (size - 1) ||
      address + size > kRaMemoryEnd) {
    ++g_invalid_read_count;
    return 0;
  }

  ram = RaMemoryRam();
  sram = RaMemorySram();
  if (!ram || !sram) {
    ++g_invalid_read_count;
    return 0;
  }

  if (address < kRaRamSize) {
    ram_bytes = kRaRamSize - address;
    if (ram_bytes > size)
      ram_bytes = size;
    memcpy(buffer, ram + address, ram_bytes);
    buffer += ram_bytes;
    size -= ram_bytes;
    address += ram_bytes;
  }

  if (size != 0)
    memcpy(buffer, sram + (address - kRaSramBase), size);

  return ram_bytes + size;
}

uint32_t RaMemoryGetInvalidReadCount(void) {
  return g_invalid_read_count;
}

#ifdef RA_MEMORY_TEST
void RaMemorySetTestMemory(uint8_t *ram, uint8_t *sram) {
  g_test_ram = ram;
  g_test_sram = sram;
}

void RaMemoryResetInvalidReadCount(void) {
  g_invalid_read_count = 0;
}
#endif
