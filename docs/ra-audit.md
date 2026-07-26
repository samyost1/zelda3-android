# RetroAchievements Build Checkpoint

## Vendored upstream

`app/jni/src/third_party/rcheevos` is the official rcheevos `v12.4.0`
snapshot at commit `2ad0b8672f68a48148620164510b963039e49eb1`. The upstream MIT
text is byte-for-byte in `third_party/rcheevos/LICENSE`; `VERSION` records
the tag, commit, source repository, and license.

## Audited insertion points

- `app/jni/src/Android.mk`: `LOCAL_C_INCLUDES` adds the public rcheevos
  headers. `RCHEEVOS_CLIENT_SRC` is an explicit ndk-build list for the
  rc_client path, then `LOCAL_SRC_FILES` appends that list.
- `app/jni/src/Makefile`: `RCHEEVOS_CLIENT_SRCS` mirrors that same source
  set and adds the public headers, so the existing Linux executable still
  links with the vendored client.
- `app/build.gradle`: keeps the upstream ABI declarations unchanged. The
  Apple-silicon validation command injects `arm64-v8a` and uses local NDK
  `25.2.9519653`; this target-only host workaround is not a product constraint.
- `app/jni/src/src/ra_client_zelda3.*`, `ra_memory.*`, `ra_http.*`, and
  `ra_state.*`: future integration boundaries. They are compiled but have
  no callers, no network implementation, no login, no frame hook, no UI,
  and no submission behavior. Their platform-neutral stubs keep the Linux
  build linkable as well as Android.

The explicit rcheevos list includes `rc_client.c`, compatibility/util/version,
the required `rapi` and runtime parser sources, and `rhash/md5.c`. It does
not define `RC_CLIENT_SUPPORTS_HASH`, and it intentionally omits the hash
backend, libretro integration, RAIntegration bridge, and external-client
adapter.

## Toolchain and ABI

The verified target is `arm64-v8a` using local NDK `25.2.9519653`, matching the
AYN Thor and Apple-silicon Android build environment. The project continues to
declare `armeabi-v7a`, `arm64-v8a`, `x86`, and `x86_64`. NDK r21 cannot run
reliably on this arm64 macOS host even through Rosetta, while newer NDKs no
longer support the declared API 16 for all legacy ABIs. Target builds therefore
use `-Pandroid.injected.build.abi=arm64-v8a`; multi-ABI release validation still
requires a compatible Intel/Linux Android build host.
