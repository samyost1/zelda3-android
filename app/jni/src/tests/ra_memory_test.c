#include "src/ra_memory.h"

#include <assert.h>
#include <limits.h>
#include <stdint.h>
#include <string.h>

enum {
  kRamSize = 0x20000,
  kSramSize = 0x2000,
};

int main(void) {
  uint8_t ram[kRamSize];
  uint8_t sram[kSramSize];
  uint8_t buffer[4];
  uint32_t invalid_reads;

  for (uint32_t i = 0; i < kRamSize; ++i)
    ram[i] = (uint8_t)i;
  for (uint32_t i = 0; i < kSramSize; ++i)
    sram[i] = (uint8_t)(0x80 + i);

  RaMemorySetTestMemory(ram, sram);
  RaMemoryResetInvalidReadCount();

  assert(RaMemoryRead(0, buffer, 1, NULL) == 1 && buffer[0] == ram[0]);
  assert(RaMemoryRead(0x1ffff, buffer, 1, NULL) == 1 &&
         buffer[0] == ram[0x1ffff]);
  assert(RaMemoryRead(0x20000, buffer, 1, NULL) == 1 &&
         buffer[0] == sram[0]);
  assert(RaMemoryRead(0x100, buffer, 4, NULL) == 4 &&
         memcmp(buffer, ram + 0x100, sizeof(buffer)) == 0);
  assert(RaMemoryRead(0x1fffe, buffer, 4, NULL) == 4);
  assert(buffer[0] == ram[0x1fffe] && buffer[1] == ram[0x1ffff] &&
         buffer[2] == sram[0] && buffer[3] == sram[1]);

  assert(RaMemoryRead(0x21fff, buffer, 2, NULL) == 0);
  assert(RaMemoryRead(0x22000, buffer, 1, NULL) == 0);
  assert(RaMemoryRead(0, NULL, 1, NULL) == 0);
  assert(RaMemoryRead(0, NULL, 0, NULL) == 0);
  assert(RaMemoryRead(UINT_MAX, buffer, 2, NULL) == 0);
  invalid_reads = RaMemoryGetInvalidReadCount();
  assert(invalid_reads == 4);

  return 0;
}
