package com.dishii.zelda3;

import java.util.ArrayList;
import java.util.List;

/** Parses the tab-separated native RA snapshot without Android dependencies. */
final class RetroAchievementsUiModel {

    static final class Achievement {
        final String bucket;
        final int id;
        final String title;
        final String description;
        final int points;
        final boolean unlocked;
        final String progress;

        Achievement(String bucket, int id, String title, String description,
                int points, boolean unlocked, String progress) {
            this.bucket = bucket;
            this.id = id;
            this.title = title;
            this.description = description;
            this.points = points;
            this.unlocked = unlocked;
            this.progress = progress;
        }
    }

    String mode = "disabled";
    String status = "disabled";
    String username = "";
    String gameTitle = "";
    int gameId;
    int unlocked;
    int core;
    int points;
    int rp;
    String richPresence = "";
    String lastEvent = "";
    boolean disconnected;
    boolean spectator;
    final List<Achievement> achievements = new ArrayList<>();

    static RetroAchievementsUiModel parse(String raw) {
        RetroAchievementsUiModel model = new RetroAchievementsUiModel();
        if (raw == null) return model;
        for (String line : raw.split("\n")) {
            String[] field = line.split("\t", -1);
            if (field.length >= 15 && "M".equals(field[0])) {
                try {
                    int gameId = Integer.parseInt(field[5]);
                    int unlocked = Integer.parseInt(field[6]);
                    int core = Integer.parseInt(field[7]);
                    int points = Integer.parseInt(field[8]);
                    int rp = Integer.parseInt(field[9]);
                    model.mode = field[1];
                    model.status = field[2];
                    model.username = field[3];
                    model.gameTitle = field[4];
                    model.gameId = gameId;
                    model.unlocked = unlocked;
                    model.core = core;
                    model.points = points;
                    model.rp = rp;
                    model.richPresence = field[10];
                    model.lastEvent = field[11];
                    model.disconnected = "1".equals(field[12]);
                    model.spectator = "1".equals(field[14]);
                } catch (NumberFormatException ignored) {
                    // Keep the previous complete model record.
                }
            } else if (field.length >= 8 && "A".equals(field[0])) {
                try {
                    model.achievements.add(new Achievement(field[1], Integer.parseInt(field[2]),
                            field[3], field[4], Integer.parseInt(field[5]),
                            "1".equals(field[6]), field[7]));
                } catch (NumberFormatException ignored) {
                    // Keep complete achievement records.
                }
            }
        }
        return model;
    }
}
