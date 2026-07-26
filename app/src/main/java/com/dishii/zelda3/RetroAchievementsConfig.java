package com.dishii.zelda3;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.Locale;

/** Parses the optional external RetroAchievements configuration file. */
final class RetroAchievementsConfig {

    enum Mode {
        DISABLED, SPECTATOR, CASUAL
    }

    static final String FILE_NAME = "retroachievements.ini";
    static final String DEFAULT_CLIENT_NAME = "Zelda3AndroidRA";
    static final String DEFAULT_CLIENT_VERSION = "0.1.0";

    static final class Credentials {
        final String username;
        final String secret;
        final boolean token;
        final boolean externalPassword;

        Credentials(String username, String secret, boolean token, boolean externalPassword) {
            this.username = username;
            this.secret = secret;
            this.token = token;
            this.externalPassword = externalPassword;
        }
    }

    final boolean enabled;
    final Mode mode;
    final String username;
    final String password;
    final String token;
    final String clientName;
    final String clientVersion;

    private RetroAchievementsConfig(boolean enabled, Mode mode, String username, String password,
            String token, String clientName, String clientVersion) {
        this.enabled = enabled;
        this.mode = mode;
        this.username = username;
        this.password = password;
        this.token = token;
        this.clientName = clientName;
        this.clientVersion = clientVersion;
    }

    static RetroAchievementsConfig load(File file) throws IOException {
        String enabled = null, mode = null, username = null, password = null, token = null;
        String clientName = null, clientVersion = null;
        if (file.isFile()) {
            try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    String trimmed = line.trim();
                    if (trimmed.length() == 0 || trimmed.startsWith("#") || trimmed.startsWith(";")) {
                        continue;
                    }
                    int equals = trimmed.indexOf('=');
                    if (equals < 1) {
                        continue;
                    }
                    String key = trimmed.substring(0, equals).trim().toLowerCase(Locale.US);
                    String value = trimmed.substring(equals + 1).trim();
                    if ("enabled".equals(key)) enabled = value;
                    else if ("mode".equals(key)) mode = value;
                    else if ("username".equals(key)) username = value;
                    else if ("password".equals(key)) password = value;
                    else if ("token".equals(key)) token = value;
                    else if ("clientname".equals(key)) clientName = value;
                    else if ("clientversion".equals(key)) clientVersion = value;
                }
            }
        }

        String selectedToken = nonEmpty(token);
        return new RetroAchievementsConfig(parseBoolean(enabled), parseMode(mode),
                nonEmpty(username), selectedToken == null ? nonEmpty(password) : null, selectedToken,
                validClientName(clientName) ? clientName.trim() : DEFAULT_CLIENT_NAME,
                validClientVersion(clientVersion) ? clientVersion.trim() : DEFAULT_CLIENT_VERSION);
    }

    static void createDefaultIfMissing(File file) throws IOException {
        if (file.exists()) {
            return;
        }
        File parent = file.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            throw new IOException("couldn't create RetroAchievements config directory");
        }
        try (Writer writer = new OutputStreamWriter(new FileOutputStream(file), "UTF-8")) {
            writer.write("# Optional RetroAchievements settings\n");
            writer.write("Enabled = false\n");
            writer.write("Mode = Spectator\n");
            writer.write("ClientName = " + DEFAULT_CLIENT_NAME + "\n");
            writer.write("ClientVersion = " + DEFAULT_CLIENT_VERSION + "\n");
        }
    }

    static void clearExternalPassword(File file) throws IOException {
        clearExternalLines(file, false);
    }

    static void clearExternalCredentials(File file) throws IOException {
        clearExternalLines(file, true);
    }

    private static void clearExternalLines(File file, boolean allCredentials) throws IOException {
        if (!file.isFile()) {
            return;
        }
        StringBuilder updated = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new FileReader(file))) {
            String line;
            while ((line = reader.readLine()) != null) {
                int equals = line.indexOf('=');
                if (equals >= 0 && (allCredentials
                        ? isCredentialKey(line.substring(0, equals))
                        : "password".equalsIgnoreCase(line.substring(0, equals).trim()))) {
                    line = line.substring(0, equals + 1);
                }
                updated.append(line).append('\n');
            }
        }
        try (FileOutputStream output = new FileOutputStream(file);
                Writer writer = new OutputStreamWriter(output, "UTF-8")) {
            writer.write(updated.toString());
            writer.flush();
            output.getFD().sync();
        }
    }

    Credentials resolveCredentials(String privateUsername, String privateToken) {
        return resolveCredentials(privateUsername, privateToken, true);
    }

    Credentials resolveCredentials(String privateUsername, String privateToken,
            boolean allowExternalCredentials) {
        String storedUsername = nonEmpty(privateUsername);
        String storedToken = nonEmpty(privateToken);
        if (allowExternalCredentials && username != null && token != null) {
            return new Credentials(username, token, true, false);
        }
        if (storedUsername != null && storedToken != null) {
            return new Credentials(storedUsername, storedToken, true, false);
        }
        if (allowExternalCredentials && username != null && password != null) {
            return new Credentials(username, password, false, true);
        }
        return null;
    }

    private static boolean isCredentialKey(String key) {
        return "username".equalsIgnoreCase(key.trim())
                || "password".equalsIgnoreCase(key.trim())
                || "token".equalsIgnoreCase(key.trim());
    }

    private static boolean parseBoolean(String value) {
        return "1".equals(value) || "true".equalsIgnoreCase(value) || "yes".equalsIgnoreCase(value);
    }

    private static Mode parseMode(String value) {
        if (value != null) {
            for (Mode mode : Mode.values()) {
                if (mode.name().equalsIgnoreCase(value.trim())) {
                    return mode;
                }
            }
        }
        return Mode.SPECTATOR;
    }

    private static String nonEmpty(String value) {
        return value == null || value.trim().length() == 0 ? null : value.trim();
    }

    private static boolean validClientName(String value) {
        return value != null && value.trim().matches("[A-Za-z0-9][A-Za-z0-9._-]{0,63}");
    }

    private static boolean validClientVersion(String value) {
        return value != null && value.trim().matches("[0-9]+\\.[0-9]+\\.[0-9]+");
    }
}
