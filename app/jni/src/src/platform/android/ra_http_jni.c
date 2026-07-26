#include "../../ra_http.h"

#include <SDL.h>
#include <jni.h>

#include <limits.h>
#include <string.h>

static jclass g_http_class;
static jmethodID g_enqueue_method;

static int RaHttpEnsureJavaBridge(JNIEnv *env) {
  jclass local_class;

  if (g_http_class)
    return 1;

  local_class = (*env)->FindClass(env,
      "com/dishii/zelda3/RetroAchievementsHttp");
  if (!local_class || (*env)->ExceptionCheck(env)) {
    (*env)->ExceptionClear(env);
    return 0;
  }
  g_http_class = (jclass)(*env)->NewGlobalRef(env, local_class);
  (*env)->DeleteLocalRef(env, local_class);
  if (!g_http_class)
    return 0;

  g_enqueue_method = (*env)->GetStaticMethodID(env, g_http_class, "enqueue",
      "(JLjava/lang/String;[BLjava/lang/String;Ljava/lang/String;)Z");
  if (!g_enqueue_method || (*env)->ExceptionCheck(env)) {
    (*env)->ExceptionClear(env);
    (*env)->DeleteGlobalRef(env, g_http_class);
    g_http_class = NULL;
    return 0;
  }
  return 1;
}

int RaHttpPlatformEnqueue(uint64_t request_id, const char *url,
                          const char *post_data, const char *content_type,
                          const char *user_agent) {
  JNIEnv *env = (JNIEnv *)SDL_AndroidGetJNIEnv();
  jstring jurl = NULL;
  jbyteArray jpost_data = NULL;
  jstring jcontent_type = NULL;
  jstring juser_agent = NULL;
  jboolean accepted;
  size_t post_size;

  if (!env || !RaHttpEnsureJavaBridge(env))
    return 0;

  jurl = (*env)->NewStringUTF(env, url);
  if (post_data) {
    post_size = strlen(post_data);
    if (post_size > INT_MAX)
      goto failed;
    jpost_data = (*env)->NewByteArray(env, (jsize)post_size);
    if (!jpost_data)
      goto failed;
    (*env)->SetByteArrayRegion(env, jpost_data, 0, (jsize)post_size,
                               (const jbyte *)post_data);
  }
  if (content_type)
    jcontent_type = (*env)->NewStringUTF(env, content_type);
  juser_agent = (*env)->NewStringUTF(env, user_agent);
  if (!jurl || !juser_agent || (*env)->ExceptionCheck(env))
    goto failed;

  accepted = (*env)->CallStaticBooleanMethod(
      env, g_http_class, g_enqueue_method, (jlong)request_id, jurl,
      jpost_data, jcontent_type, juser_agent);
  if ((*env)->ExceptionCheck(env))
    goto failed;

  (*env)->DeleteLocalRef(env, jurl);
  if (jpost_data) (*env)->DeleteLocalRef(env, jpost_data);
  if (jcontent_type) (*env)->DeleteLocalRef(env, jcontent_type);
  (*env)->DeleteLocalRef(env, juser_agent);
  return accepted == JNI_TRUE;

failed:
  if ((*env)->ExceptionCheck(env))
    (*env)->ExceptionClear(env);
  if (jurl) (*env)->DeleteLocalRef(env, jurl);
  if (jpost_data) (*env)->DeleteLocalRef(env, jpost_data);
  if (jcontent_type) (*env)->DeleteLocalRef(env, jcontent_type);
  if (juser_agent) (*env)->DeleteLocalRef(env, juser_agent);
  return 0;
}

JNIEXPORT void JNICALL
Java_com_dishii_zelda3_RetroAchievementsHttp_nativeComplete(
    JNIEnv *env, jclass clazz, jlong request_id, jint http_status,
    jbyteArray body) {
  jsize body_size = 0;
  jbyte *body_bytes = NULL;

  (void)clazz;
  if (body) {
    body_size = (*env)->GetArrayLength(env, body);
    if (body_size > kRaHttpMaxResponseBytes) {
      RaHttpComplete((uint64_t)request_id,
                     RC_API_SERVER_RESPONSE_CLIENT_ERROR, NULL, 0);
      return;
    }
    if (body_size != 0) {
      body_bytes = (*env)->GetByteArrayElements(env, body, NULL);
      if (!body_bytes)
        return;
    }
  }

  RaHttpComplete((uint64_t)request_id, http_status,
                 (const uint8_t *)body_bytes, (size_t)body_size);
  if (body_bytes)
    (*env)->ReleaseByteArrayElements(env, body, body_bytes, JNI_ABORT);
}
