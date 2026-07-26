LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE := main

SDL_PATH := ../SDL2
SDL_MIXER_PATH := ../SDL2_mixer

LOCAL_C_INCLUDES := $(LOCAL_PATH)/$(SDL_PATH)/include $(LOCAL_PATH)/$(SDL_MIXER_PATH)/include \
    $(LOCAL_PATH)/third_party/rcheevos/include

# Keep this list explicit: rc_client builds without RC_CLIENT_SUPPORTS_HASH.
RCHEEVOS_CLIENT_SRC := \
    third_party/rcheevos/src/rc_client.c \
    third_party/rcheevos/src/rc_compat.c \
    third_party/rcheevos/src/rc_util.c \
    third_party/rcheevos/src/rc_version.c \
    third_party/rcheevos/src/rapi/rc_api_common.c \
    third_party/rcheevos/src/rapi/rc_api_info.c \
    third_party/rcheevos/src/rapi/rc_api_runtime.c \
    third_party/rcheevos/src/rapi/rc_api_user.c \
    third_party/rcheevos/src/rcheevos/alloc.c \
    third_party/rcheevos/src/rcheevos/condition.c \
    third_party/rcheevos/src/rcheevos/condset.c \
    third_party/rcheevos/src/rcheevos/consoleinfo.c \
    third_party/rcheevos/src/rcheevos/format.c \
    third_party/rcheevos/src/rcheevos/lboard.c \
    third_party/rcheevos/src/rcheevos/memref.c \
    third_party/rcheevos/src/rcheevos/operand.c \
    third_party/rcheevos/src/rcheevos/richpresence.c \
    third_party/rcheevos/src/rcheevos/runtime.c \
    third_party/rcheevos/src/rcheevos/runtime_progress.c \
    third_party/rcheevos/src/rcheevos/trigger.c \
    third_party/rcheevos/src/rcheevos/value.c \
    third_party/rcheevos/src/rhash/md5.c

LOCAL_SRC_FILES := $(wildcard $(LOCAL_PATH)/src/*.c $(LOCAL_PATH)/src/platform/android/*.c $(LOCAL_PATH)/snes/*.c) \
    third_party/gl_core/gl_core_3_1.c \
    third_party/opus-1.3.1-stripped/opus_decoder_amalgam.c \
    $(RCHEEVOS_CLIENT_SRC)

LOCAL_SHARED_LIBRARIES := SDL2 SDL2_mixer

LOCAL_LDLIBS := -lGLESv1_CM -lGLESv2 -lOpenSLES -llog -landroid

include $(BUILD_SHARED_LIBRARY)
