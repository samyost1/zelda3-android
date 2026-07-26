# RetroAchievements Validation Report

Date: July 25, 2026

Casual unlock follow-up: July 26, 2026

## Scope

This draft integrates private RetroAchievements support into the Android port
without changing the default experience for users who do not provide a private
configuration file.

- Branch: `feature/retroachievements-private`
- Tested source commit: `918be4e7d518c68b3e2c5b6901ef077ff6698188`
- Base commit: `6fb832027a6e9b4812244e90dcc039303bd9e15b`
- Base branch: `samyost1/zelda3-android:dual-screen`
- rcheevos: official `12.4.0` snapshot at
  `2ad0b8672f68a48148620164510b963039e49eb1`
- Target device: AYN Thor, Android 13, arm64-v8a

The host and test device clocks displayed July 26 during the final run, but
both clocks were one day ahead. The actual validation date is July 25, 2026.

## Implemented

- Exact canonical US ROM verification before RetroAchievements is enabled.
- Private INI configuration with token login and password-login fallback.
- Token persistence in the app-private data directory with restrictive file
  permissions.
- Spectator mode by default; hardcore is always disabled.
- Native rcheevos client lifecycle, SNES memory mapping, logical-frame
  processing, and asynchronous HTTPS request handling.
- Pause/resume handling, disconnect/reconnect plumbing, and logout cleanup.
- RetroAchievements progress embedded in save states with version and checksum
  validation while preserving legacy save-state compatibility.
- Casual-mode integrity guards that reject replay/direct-cheat paths.
- Dual-screen companion panel with connection state, rich presence,
  achievements, scrolling, verification, and logout controls.
- Debug-only `RA_TEST` and `RA_DUMP` broadcasts for deterministic validation.
  Their action strings and diagnostic method are absent from the release APK.
- Existing Android ABI declarations remain
  `armeabi-v7a`, `arm64-v8a`, `x86`, and `x86_64`.

## Automated Validation

The final clean build used:

```sh
export JAVA_HOME=/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home
./gradlew clean :app:check :app:assembleDebug :app:assembleRelease \
  -Pandroid.injected.build.abi=arm64-v8a \
  --console=plain
```

Result: `BUILD SUCCESSFUL` in 1 minute 6 seconds, with 90 actionable tasks.

- RetroAchievements JVM tests: 3 passed.
- Native/static assertions: 16 passed.
- Android debug unit tests: passed.
- Android release unit tests: passed.
- Android lint/check: passed.
- Debug APK assembled successfully.
- Unsigned release APK assembled successfully.
- `git diff --check`: clean.

Final artifacts:

| Artifact | SHA-256 |
| --- | --- |
| `app/build/outputs/apk/debug/app-debug.apk` | `d829b70632c8ef2680de1cbe66da0e5abaecae8e3435e490230cb347870b157e` |
| `app/build/outputs/apk/release/app-release-unsigned.apk` | `71864a8ad44603909b57cfad526478875aaf17a4abbbb8ee6146dd6d1afe0a7e` |

The final release APK was scanned for `RA_TEST`, `RA_DUMP`, and
`uiModelDiagnostics`; no matches were found.

## Physical Device Validation

The final debug APK was installed on the AYN Thor with:

```sh
adb -s 6b0af897 install -r -t \
  app/build/outputs/apk/debug/app-debug.apk
```

Installation succeeded. The `-t` flag is required because this project's debug
APK is marked test-only; plain `adb install -r` is rejected by Android.

After a force-stop and fresh launch of the final APK, the debug snapshot
reported:

```text
enabled=1
mode=spectator
lifecycle=resumed
state=5
login=authenticated
game=355
console=3
hash=match
expected_hash=608c22b8ff930c62dc2de54bcd6eba72
hardcore=0
spectator=1
summary=core:109/unlocked:0/unsupported:0
rp_supported=1
rp=Getting ready to adventure
invalid_reads=0
http=2/2/0/0/0
ua=Zelda3Android/0.1.0 (Android 13; AYN Thor) rcheevos/12.4
```

No account name or credential is included in this report.

Additional physical checks:

| Check | Result |
| --- | --- |
| Canonical ROM hash and game identification | Passed: game 355, SNES console 3 |
| Private token authentication | Passed |
| Spectator mode and hardcore disabled | Passed |
| Rich Presence | Passed |
| Achievement list | Passed: 109 core achievements, zero unsupported |
| Invalid memory reads | Passed: zero |
| Gameplay on primary display | Passed |
| Map/companion UI on physical second display | Passed |
| Long achievement title/description rendering | Passed |
| Achievement list scrolling | Passed |
| Activity pause | Passed: logical frame counter stayed at 8210 for 5 seconds |
| Normal frame processing | Passed: 221 logical frames in approximately 3.7 seconds |
| Turbo frame processing | Passed: 2993 logical frames in approximately 3.8 seconds |
| Save-state progress footer | Passed: `ZRAP` footer present in the generated save |
| Save-state restore | Passed: runtime logged `progress restore=ok` |
| Setup re-verification through `onNewIntent` | Passed: current activity reauthenticated game 355 |
| Natural Casual achievement unlock | Passed: `Fighter` (ID 944) triggered and was confirmed by the server |
| Wi-Fi disable/enable recovery | Partially observed; see limitations |

The turbo test demonstrates that RetroAchievements processing follows logical
game frames before render skipping, rather than only rendered frames.

The Casual unlock follow-up restored a state immediately before receiving the
Fighter's Sword and Shield, then advanced the original dialogue through normal
game input. The live memory transition was:

```text
scene bytes 0x0AA1..0x0AA4: 01 10 4D 0A
sword 0xF359: 0 -> 1
shield 0xF35A: 0 -> 1
```

rcheevos emitted `RC_CLIENT_EVENT_ACHIEVEMENT_TRIGGERED`, the local unlocked
count increased from 2 to 3, Rich Presence changed to include
`Fighter's Sword`, all HTTP requests completed without error, and a separate
server query confirmed achievement ID 944 in the user's Casual unlock list.
No memory patch, replay, synthetic unlock, or direct award request was used.

## Security and Privacy Checks

- The ROM, private INI file, APKs, and save states are ignored by Git.
- The actual local password and token values were compared against tracked
  files; neither value was found.
- No private configuration file, ROM, APK, or newly generated save state is
  tracked by this branch.
- Existing upstream reference saves and assets were not modified.
- Logout uses a local tombstone so stale external credentials cannot silently
  reactivate the client if cleanup fails. A successful cleanup removes the
  tombstone and permits an intentional later login.

## Known Limitations

- A deterministic server reconnect event was not produced in spectator mode:
  Wi-Fi was disabled for 120 seconds and restored successfully, but the idle
  spectator client made no request while offline. Authentication remained
  valid after Android reported Wi-Fi connected and validated. The asynchronous
  reconnect path is implemented, but a real disconnected/reconnected event was
  not claimed as observed.
- The Apple-silicon validation host can execute the local NDK only for
  `arm64-v8a`. Source-level ABI declarations still preserve all four upstream
  ABIs; a complete multi-ABI release build requires a compatible Intel/Linux
  Android build host.
- The release APK is unsigned.
- Incremental builds inside the macOS synchronized Documents tree can create
  duplicate generated `* 2.class` files. A clean build is reliable and was used
  for all final artifacts.
- The NDK emits non-fatal `fcntl(): Bad file descriptor` messages and a
  deprecation warning for `ndk.dir`. The debug build also retains the existing
  unoptimized Opus warning. None caused a failed task.

## Conclusion

The private Spectator-mode integration is buildable, authenticated, ROM-bound,
frame-active, save-state-aware, and usable on both physical displays of the
AYN Thor. Automated checks, the Spectator runtime path, and one natural Casual
unlock pass. The PR remains a draft because an active-request network reconnect
should still be observed before merge.
