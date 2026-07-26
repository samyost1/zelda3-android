#include "../../ra_client_zelda3.h"

#include <jni.h>
#include <string.h>

static const char *JniGetString(JNIEnv *env, jstring value) {
  return value ? (*env)->GetStringUTFChars(env, value, NULL) : NULL;
}

static jstring JniNewStringFromUtf8(JNIEnv *env, const char *value) {
  jbyteArray bytes;
  jclass string_class;
  jmethodID constructor;
  jstring charset;
  jstring result;
  jsize length = value ? (jsize)strlen(value) : 0;

  bytes = (*env)->NewByteArray(env, length);
  if (!bytes)
    return NULL;
  if (length)
    (*env)->SetByteArrayRegion(env, bytes, 0, length, (const jbyte *)value);
  string_class = (*env)->FindClass(env, "java/lang/String");
  charset = (*env)->NewStringUTF(env, "UTF-8");
  if (!string_class || !charset)
    return NULL;
  constructor = (*env)->GetMethodID(env, string_class, "<init>",
                                    "([BLjava/lang/String;)V");
  if (!constructor)
    return NULL;
  result = (jstring)(*env)->NewObject(env, string_class, constructor, bytes,
                                     charset);
  (*env)->DeleteLocalRef(env, charset);
  (*env)->DeleteLocalRef(env, string_class);
  (*env)->DeleteLocalRef(env, bytes);
  return result;
}

JNIEXPORT void JNICALL
Java_com_dishii_zelda3_RetroAchievementsBridge_nativeConfigure(
    JNIEnv *env, jclass clazz, jboolean enabled, jboolean spectator, jboolean verified,
    jstring client_name, jstring client_version, jstring username, jstring secret,
    jboolean secret_is_token, jstring android_release, jstring android_model) {
  const char *native_client_name = JniGetString(env, client_name);
  const char *native_client_version = JniGetString(env, client_version);
  const char *native_username = JniGetString(env, username);
  const char *native_secret = JniGetString(env, secret);
  const char *native_android_release = JniGetString(env, android_release);
  const char *native_android_model = JniGetString(env, android_model);

  (void)clazz;
  RaClientZelda3_QueueConfigure(enabled == JNI_TRUE, spectator == JNI_TRUE,
                                verified == JNI_TRUE,
                                native_client_name, native_client_version,
                                native_username, native_secret,
                                secret_is_token == JNI_TRUE,
                                native_android_release, native_android_model);
  if (native_client_name)
    (*env)->ReleaseStringUTFChars(env, client_name, native_client_name);
  if (native_client_version)
    (*env)->ReleaseStringUTFChars(env, client_version, native_client_version);
  if (native_username)
    (*env)->ReleaseStringUTFChars(env, username, native_username);
  if (native_secret)
    (*env)->ReleaseStringUTFChars(env, secret, native_secret);
  if (native_android_release)
    (*env)->ReleaseStringUTFChars(env, android_release, native_android_release);
  if (native_android_model)
    (*env)->ReleaseStringUTFChars(env, android_model, native_android_model);
}

JNIEXPORT void JNICALL
Java_com_dishii_zelda3_RetroAchievementsBridge_nativeLogout(
    JNIEnv *env, jclass clazz) {
  (void)env;
  (void)clazz;
  RaClientZelda3_QueueLogout();
}

JNIEXPORT void JNICALL
Java_com_dishii_zelda3_RetroAchievementsBridge_nativeSetPaused(
    JNIEnv *env, jclass clazz, jboolean paused) {
  (void)env;
  (void)clazz;
  RaClientZelda3_SetPaused(paused == JNI_TRUE);
}

JNIEXPORT jstring JNICALL
Java_com_dishii_zelda3_RetroAchievementsBridge_nativeSnapshot(
    JNIEnv *env, jclass clazz) {
  char snapshot[2048];

  (void)clazz;
  RaClientZelda3_SnapshotCached(snapshot, sizeof(snapshot));
  return JniNewStringFromUtf8(env, snapshot);
}

JNIEXPORT jstring JNICALL
Java_com_dishii_zelda3_RetroAchievementsBridge_nativeUiModel(
    JNIEnv *env, jclass clazz) {
  static char ui_model[64 * 1024];

  (void)clazz;
  RaClientZelda3_UiModelCached(ui_model, sizeof(ui_model));
  return JniNewStringFromUtf8(env, ui_model);
}
