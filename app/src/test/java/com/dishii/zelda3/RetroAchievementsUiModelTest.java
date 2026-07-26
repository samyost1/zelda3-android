package com.dishii.zelda3;

/** Runnable parser regression check for long native records and malformed input. */
public final class RetroAchievementsUiModelTest {

    public static void main(String[] args) {
        String longText = repeat("LONG FIELD ", 180);
        RetroAchievementsUiModel model = RetroAchievementsUiModel.parse(
                "V\t1\nM\tcasual\tready\t" + longText + "\t" + longText
                + "\t355\t1\t2\t3\t4\t" + longText + "\t" + longText + "\t0\t0\t0\n"
                + "A\tACTIVE\t1\t" + longText + "\t" + longText + "\t5\t0\t99/100\n"
                + "A\tBROKEN\tnot-a-number\tx\ty\t1\t0\t\n"
                + "M\tcasual\tready\tpartial\tbad\tbad\t0\t0\t0\t0\t\t\t0\t0\t0\n");
        check(model.username.equals(longText), "long username must survive");
        check(model.gameTitle.equals(longText), "long game title must survive");
        check(model.richPresence.equals(longText), "long Rich Presence must survive");
        check(model.lastEvent.equals(longText), "long event must survive");
        check(model.achievements.size() == 1, "malformed achievement must be ignored");
        check(model.achievements.get(0).title.equals(longText), "long title must survive");
        check(model.achievements.get(0).description.equals(longText), "long description must survive");
    }

    private static String repeat(String value, int count) {
        StringBuilder out = new StringBuilder(value.length() * count);
        for (int i = 0; i < count; i++) out.append(value);
        return out.toString();
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
