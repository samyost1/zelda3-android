#include "ra_state.h"

#include <assert.h>
#include <string.h>

static int g_reset_calls;
static int g_deserialize_calls;

size_t RaClientZelda3_SerializeProgress(uint8_t *buffer, size_t size) {
  (void)buffer;
  (void)size;
  return 0;
}

int RaClientZelda3_DeserializeProgress(const uint8_t *buffer, size_t size) {
  (void)buffer;
  (void)size;
  ++g_deserialize_calls;
  return 1;
}

void RaClientZelda3_ResetProgress(void) {
  ++g_reset_calls;
}

int main(void) {
  uint8_t footer[64];
  const uint8_t payload[] = { 1, 2, 3, 4, 5 };
  const uint8_t *decoded = NULL;
  size_t decoded_size = 0;
  size_t footer_size;

  footer_size = RaStateFooterEncode(footer, sizeof(footer), payload, sizeof(payload));
  assert(footer_size == 16 + sizeof(payload));
  assert(RaStateFooterDecode(footer, footer_size, &decoded, &decoded_size) ==
         kRaStateFooterOk);
  assert(decoded_size == sizeof(payload) && memcmp(decoded, payload, sizeof(payload)) == 0);

  assert(RaStateFooterDecode(NULL, 0, &decoded, &decoded_size) == kRaStateFooterLegacy);
  assert(RaStateFooterDecode(footer, footer_size - 1, &decoded, &decoded_size) ==
         kRaStateFooterTruncated);

  footer[12] ^= 1;
  assert(RaStateFooterDecode(footer, footer_size, &decoded, &decoded_size) ==
         kRaStateFooterChecksum);
  footer[12] ^= 1;

  footer[4] = 2;
  footer[5] = 0;
  assert(RaStateFooterDecode(footer, footer_size, &decoded, &decoded_size) ==
         kRaStateFooterVersion);
  footer[4] = 1;

  footer[8] = 1;
  footer[9] = 0;
  footer[10] = 1;
  footer[11] = 0;
  assert(RaStateFooterDecode(footer, footer_size, &decoded, &decoded_size) ==
         kRaStateFooterSize);

  assert(RaStateDeserialize(payload, sizeof(payload)) == 1);
  RaStateReset();
  assert(g_deserialize_calls == 1 && g_reset_calls == 1);
  return 0;
}
