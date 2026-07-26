package com.dishii.zelda3;

import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;

/** Runnable JVM check: no Android runtime or test dependency required. */
public final class RetroAchievementsConfigTest {

    public static void main(String[] args) throws Exception {
        testHeaderStripAndHash();
        testConfigValidationAndCredentialPairs();
        testExternalCredentialClearIsDurable();
        testLogoutTombstoneBlocksStaleExternalCredentials();
    }

    private static void testLogoutTombstoneBlocksStaleExternalCredentials() throws Exception {
        File file = File.createTempFile("ra-config-", ".ini");
        try {
            write(file, "Enabled=true\nUsername=external\nToken=stale-token\n");
            RetroAchievementsConfig config = RetroAchievementsConfig.load(file);
            check(config.resolveCredentials(null, null, false) == null,
                    "logout tombstone must block stale external credentials after cleanup failure");
            check(config.resolveCredentials("private-user", "fresh-token", false).token,
                    "logout tombstone must allow a newly persisted private token");

            RetroAchievementsConfig.clearExternalCredentials(file);
            write(file, "Enabled=true\nUsername=new-user\nToken=new-token\n");
            config = RetroAchievementsConfig.load(file);
            RetroAchievementsConfig.Credentials credentials =
                    config.resolveCredentials(null, null, true);
            check(credentials != null && credentials.token
                            && "new-user".equals(credentials.username),
                    "successful cleanup must allow intentional new external credentials");
        } finally {
            file.delete();
        }
    }

    private static void testHeaderStripAndHash() {
        byte[] headered = new byte[RomVerification.ROM_SIZE + 512];
        headered[512] = 42;
        byte[] stripped = RomVerification.stripCopierHeader(headered);
        check(stripped.length == RomVerification.ROM_SIZE, "header must be removed");
        check(stripped[0] == 42, "ROM bytes must remain aligned");
        check("900150983cd24fb0d6963f7d28e17f72".equals(
                RomVerification.md5Hex("abc".getBytes(StandardCharsets.US_ASCII))), "MD5 must be lowercase");
    }

    private static void testConfigValidationAndCredentialPairs() throws Exception {
        File file = File.createTempFile("ra-config-", ".ini");
        try {
            write(file, "Enabled = true\nMode = Hardcore\nUsername = player\n"
                    + "Password = ignored-password\nToken = selected-token\n"
                    + "ClientName = invalid name\nClientVersion = 1.2.3\n");
            RetroAchievementsConfig config = RetroAchievementsConfig.load(file);
            check(config.enabled, "Enabled must parse");
            check(config.mode == RetroAchievementsConfig.Mode.SPECTATOR, "invalid mode must be safe");
            check(config.password == null, "token must take precedence over password");
            check("selected-token".equals(config.token), "token must be selected");
            check(RetroAchievementsConfig.DEFAULT_CLIENT_NAME.equals(config.clientName),
                    "invalid product name must fall back");
            check("1.2.3".equals(config.clientVersion), "valid product version must survive");

            RetroAchievementsConfig.Credentials credentials =
                    config.resolveCredentials("private-user", "private-token");
            check(credentials.token && "player".equals(credentials.username)
                            && "selected-token".equals(credentials.secret),
                    "external token and username pair must win");
        } finally {
            file.delete();
        }
    }

    private static void testExternalCredentialClearIsDurable() throws Exception {
        File file = File.createTempFile("ra-config-", ".ini");
        try {
            write(file, "Enabled=true\nUsername=external\nPassword=password\n"
                    + "ClientName=Zelda3AndroidRA\nClientVersion=version-two\n");
            RetroAchievementsConfig config = RetroAchievementsConfig.load(file);
            RetroAchievementsConfig.Credentials credentials =
                    config.resolveCredentials("private-user", "private-token");
            check(credentials.token && "private-token".equals(credentials.secret),
                    "private token must win only with private username");
            check("private-user".equals(credentials.username),
                    "private token must not mix with external username");
            check(RetroAchievementsConfig.DEFAULT_CLIENT_VERSION.equals(config.clientVersion),
                    "invalid version must fall back");

            credentials = config.resolveCredentials("private-user", null);
            check(!credentials.token && credentials.externalPassword,
                    "external password must be final fallback");
            check("external".equals(credentials.username),
                    "external password must retain external username");

            write(file, "Enabled=true\nToken=orphaned\nPassword=password\n");
            config = RetroAchievementsConfig.load(file);
            check(config.resolveCredentials("private-user", null) == null,
                    "orphaned external credentials must not mix with private credentials");

            write(file, "Enabled=true\nUsername=external\nPassword=password\nToken=token\nOther=value\n");
            RetroAchievementsConfig.clearExternalPassword(file);
            String passwordCleared = new String(java.nio.file.Files.readAllBytes(file.toPath()),
                    StandardCharsets.UTF_8);
            check(passwordCleared.contains("Username=external\n")
                            && passwordCleared.contains("Password=\n")
                            && passwordCleared.contains("Token=token\n"),
                    "returned-token cleanup must clear only the external password");

            RetroAchievementsConfig.clearExternalCredentials(file);
            String cleared = new String(java.nio.file.Files.readAllBytes(file.toPath()),
                    StandardCharsets.UTF_8);
            check(cleared.contains("Username=\n") && cleared.contains("Password=\n")
                            && cleared.contains("Token=\n") && cleared.contains("Other=value\n"),
                    "logout cleanup must clear every external credential line");
        } finally {
            file.delete();
        }
    }

    private static void write(File file, String text) throws Exception {
        try (FileOutputStream out = new FileOutputStream(file)) {
            out.write(text.getBytes(StandardCharsets.UTF_8));
        }
    }

    private static void check(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
