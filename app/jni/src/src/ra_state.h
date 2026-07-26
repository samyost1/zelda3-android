#ifndef ZELDA3_RA_STATE_H_
#define ZELDA3_RA_STATE_H_

#include <stddef.h>
#include <stdint.h>

#define RA_STATE_MAX_PROGRESS (64 * 1024)

typedef enum RaStateFooterStatus {
  kRaStateFooterOk = 0,
  kRaStateFooterLegacy,
  kRaStateFooterTruncated,
  kRaStateFooterVersion,
  kRaStateFooterSize,
  kRaStateFooterChecksum,
} RaStateFooterStatus;

size_t RaStateSerialize(uint8_t *buffer, size_t size);
int RaStateDeserialize(const uint8_t *buffer, size_t size);
void RaStateReset(void);

size_t RaStateFooterEncode(uint8_t *buffer, size_t buffer_size,
                           const uint8_t *payload, size_t payload_size);
RaStateFooterStatus RaStateFooterDecode(const uint8_t *buffer, size_t size,
                                        const uint8_t **payload,
                                        size_t *payload_size);

#endif  // ZELDA3_RA_STATE_H_
