package com.dishii.zelda3;

import android.content.Context;
import android.content.SharedPreferences;

/** Private storage for RA state that must not be exposed in external files. */
final class RetroAchievementsStorage {

    private static final String PREFS = "retroachievements";
    private static final String VERIFIED_ROM_MD5 = "verified_rom_md5";
    private static final String USERNAME = "username";
    private static final String TOKEN = "token";
    private static final String LOGGED_OUT = "logged_out";

    private final SharedPreferences preferences;

    RetroAchievementsStorage(Context context) {
        preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    void saveVerifiedRomHash(String hash) {
        preferences.edit().putString(VERIFIED_ROM_MD5, hash).apply();
    }

    String getVerifiedRomHash() {
        return preferences.getString(VERIFIED_ROM_MD5, null);
    }

    void saveUsername(String username) {
        preferences.edit().putString(USERNAME, username).apply();
    }

    String getUsername() {
        return preferences.getString(USERNAME, null);
    }

    void saveReturnedToken(String token) {
        preferences.edit().putString(TOKEN, token).apply();
    }

    String getReturnedToken() {
        return preferences.getString(TOKEN, null);
    }

    boolean saveCredentials(String username, String token) {
        return preferences.edit().putString(USERNAME, username).putString(TOKEN, token)
                .remove(LOGGED_OUT).commit();
    }

    boolean logout() {
        return preferences.edit().remove(USERNAME).remove(TOKEN).putBoolean(LOGGED_OUT, true).commit();
    }

    boolean isLoggedOut() {
        return preferences.getBoolean(LOGGED_OUT, false);
    }

    boolean clearLoggedOut() {
        return preferences.edit().remove(LOGGED_OUT).commit();
    }
}
