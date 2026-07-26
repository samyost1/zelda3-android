#include "ra_state.h"

#include "ra_client_zelda3.h"

#include <string.h>

enum {
  kRaStateFooterHeaderSize = 16,
  kRaStateFooterFormatVersion = 1,
};

static const uint8_t kRaStateMagic[] = { 'Z', 'R', 'A', 'P' };

static void RaStateWriteU16(uint8_t *buffer, uint16_t value) {
  buffer[0] = (uint8_t)value;
  buffer[1] = (uint8_t)(value >> 8);
}

static void RaStateWriteU32(uint8_t *buffer, uint32_t value) {
  buffer[0] = (uint8_t)value;
  buffer[1] = (uint8_t)(value >> 8);
  buffer[2] = (uint8_t)(value >> 16);
  buffer[3] = (uint8_t)(value >> 24);
}

static uint16_t RaStateReadU16(const uint8_t *buffer) {
  return (uint16_t)(buffer[0] | ((uint16_t)buffer[1] << 8));
}

static uint32_t RaStateReadU32(const uint8_t *buffer) {
  return (uint32_t)(buffer[0] | ((uint32_t)buffer[1] << 8) |
                    ((uint32_t)buffer[2] << 16) |
                    ((uint32_t)buffer[3] << 24));
}

static uint32_t RaStateChecksum(const uint8_t *data, size_t size) {
  uint32_t crc = 0xFFFFFFFF;
  size_t i;

  for (i = 0; i < size; ++i) {
    uint32_t bit;
    crc ^= data[i];
    for (bit = 0; bit < 8; ++bit)
      crc = (crc >> 1) ^ (0xEDB88320U & (uint32_t)-(int32_t)(crc & 1));
  }
  return ~crc;
}

size_t RaStateSerialize(uint8_t *buffer, size_t size) {
  return RaClientZelda3_SerializeProgress(buffer, size);
}

int RaStateDeserialize(const uint8_t *buffer, size_t size) {
  return RaClientZelda3_DeserializeProgress(buffer, size);
}

void RaStateReset(void) {
  RaClientZelda3_ResetProgress();
}

size_t RaStateFooterEncode(uint8_t *buffer, size_t buffer_size,
                           const uint8_t *payload, size_t payload_size) {
  size_t total_size;

  if ((!payload && payload_size) || payload_size > RA_STATE_MAX_PROGRESS)
    return 0;
  total_size = kRaStateFooterHeaderSize + payload_size;
  if (!buffer || buffer_size < total_size)
    return 0;

  buffer[0] = kRaStateMagic[0];
  buffer[1] = kRaStateMagic[1];
  buffer[2] = kRaStateMagic[2];
  buffer[3] = kRaStateMagic[3];
  RaStateWriteU16(buffer + 4, kRaStateFooterFormatVersion);
  RaStateWriteU16(buffer + 6, 0);
  RaStateWriteU32(buffer + 8, (uint32_t)payload_size);
  RaStateWriteU32(buffer + 12, RaStateChecksum(payload, payload_size));
  if (payload_size)
    memcpy(buffer + kRaStateFooterHeaderSize, payload, payload_size);
  return total_size;
}

RaStateFooterStatus RaStateFooterDecode(const uint8_t *buffer, size_t size,
                                        const uint8_t **payload,
                                        size_t *payload_size) {
  uint32_t stored_size;
  const uint8_t *stored_payload;

  if (payload)
    *payload = NULL;
  if (payload_size)
    *payload_size = 0;
  if (size == 0)
    return kRaStateFooterLegacy;
  if (!buffer || size < kRaStateFooterHeaderSize)
    return kRaStateFooterTruncated;
  if (memcmp(buffer, kRaStateMagic, sizeof(kRaStateMagic)) != 0)
    return kRaStateFooterLegacy;
  if (RaStateReadU16(buffer + 4) != kRaStateFooterFormatVersion)
    return kRaStateFooterVersion;
  stored_size = RaStateReadU32(buffer + 8);
  if (stored_size > RA_STATE_MAX_PROGRESS)
    return kRaStateFooterSize;
  if (size != kRaStateFooterHeaderSize + (size_t)stored_size)
    return kRaStateFooterTruncated;
  stored_payload = buffer + kRaStateFooterHeaderSize;
  if (RaStateReadU32(buffer + 12) !=
      RaStateChecksum(stored_payload, stored_size))
    return kRaStateFooterChecksum;
  if (payload)
    *payload = stored_payload;
  if (payload_size)
    *payload_size = stored_size;
  return kRaStateFooterOk;
}
