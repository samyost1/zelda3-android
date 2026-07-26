#ifndef ZELDA3_RA_MEMORY_H_
#define ZELDA3_RA_MEMORY_H_

#include <rc_client.h>

uint32_t RaMemoryRead(uint32_t address, uint8_t *buffer, uint32_t size,
                      rc_client_t *client);
uint32_t RaMemoryGetInvalidReadCount(void);

#ifdef RA_MEMORY_TEST
void RaMemorySetTestMemory(uint8_t *ram, uint8_t *sram);
void RaMemoryResetInvalidReadCount(void);
#endif

#endif  // ZELDA3_RA_MEMORY_H_
