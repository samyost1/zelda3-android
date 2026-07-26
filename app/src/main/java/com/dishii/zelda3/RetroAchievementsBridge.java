package com.dishii.zelda3;

import android.content.Context;
import android.os.Build;
import java.io.File;
import java.io.IOException;

/** Java ownership boundary for RA configuration and private credentials. */
final class RetroAchievementsBridge {

    private static Context applicationContext;
    private static File externalConfigFile;
    private static File passwordConfigFile;

    private RetroAchievementsBridge() {}

    static void configure(Context context, File configFile, RetroAchievementsConfig config,
            RetroAchievementsStorage storage, boolean verified) {
        applicationContext = context.getApplicationContext();
        externalConfigFile = configFile;
        boolean enabled = verified && config.enabled
                && config.mode != RetroAchievementsConfig.Mode.DISABLED;
        RetroAchievementsConfig.Credentials credentials = enabled
                ? config.resolveCredentials(storage.getUsername(), storage.getReturnedToken(),
                        !storage.isLoggedOut())
                : null;
        nativeConfigure(enabled, config.mode == RetroAchievementsConfig.Mode.SPECTATOR, verified,
                config.clientName, config.clientVersion,
                credentials == null ? null : credentials.username,
                credentials == null ? null : credentials.secret,
                credentials != null && credentials.token,
                Build.VERSION.RELEASE, Build.MODEL);
        passwordConfigFile = credentials != null && credentials.externalPassword ? configFile : null;
    }

    static void logout(Context context) {
        RetroAchievementsStorage storage = new RetroAchievementsStorage(context);
        storage.logout();
        File configFile = externalConfigFile;
        try {
            if (configFile != null) {
                RetroAchievementsConfig.clearExternalCredentials(configFile);
            }
            storage.clearLoggedOut();
        } catch (IOException ignored) {
            // Keep the tombstone so stale external credentials cannot log in again.
        }
        passwordConfigFile = null;
        nativeLogout();
    }

    static void setPaused(boolean paused) {
        nativeSetPaused(paused);
    }

    static String snapshot() {
        return nativeSnapshot();
    }

    static RetroAchievementsUiModel uiModel() {
        return RetroAchievementsUiModel.parse(nativeUiModel());
    }

    static void persistReturnedToken(String username, String token) {
        Context context = applicationContext;
        if (context != null && username != null && token != null) {
            if (new RetroAchievementsStorage(context).saveCredentials(username, token)) {
                File configFile = passwordConfigFile;
                passwordConfigFile = null;
                if (configFile != null) {
                    try {
                        RetroAchievementsConfig.clearExternalPassword(configFile);
                    } catch (IOException ignored) {
                        // The returned token is durable; external cleanup retries on next launch.
                    }
                }
            }
        }
    }

    private static native void nativeConfigure(boolean enabled, boolean spectator, boolean verified,
            String clientName, String clientVersion, String username, String secret,
            boolean secretIsToken, String androidRelease, String androidModel);
    private static native void nativeLogout();
    private static native void nativeSetPaused(boolean paused);
    private static native String nativeSnapshot();
    private static native String nativeUiModel();
}
