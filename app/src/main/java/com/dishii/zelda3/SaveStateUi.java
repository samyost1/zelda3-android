package com.dishii.zelda3;

/** Stable save-file mapping and controller assignment rules, independent of Android. */
final class SaveStateUi {
    static final int SLOT_COUNT = 5;
    static int slot(int card) { return card + 1; }
    static String title(int card, SecondScreenText text) {
        return card == 0 ? text.get("QUICK STATE") : text.get("SLOT") + " " + card;
    }
    static int conflict(int[] bindings, int command, int button) {
        if (button < 0) return -1;
        for (int i = 0; i < bindings.length; i++)
            if (i != command && bindings[i] == button) return i;
        return -1;
    }
    static void assign(int[] bindings, int command, int button) {
        if (button >= 0) for (int i = 0; i < bindings.length; i++)
            if (i != command && bindings[i] == button) bindings[i] = -1;
        bindings[command] = button;
    }
    static String mergeControls(String previous, String[] values) {
        String[] old = previous == null ? new String[0] : previous.split(",", -1);
        StringBuilder out = new StringBuilder();
        for (int i = 0; i < values.length; i++) {
            if (i > 0) out.append(", ");
            out.append(i < old.length && old[i].contains("+") ? old[i].trim() : values[i]);
        }
        return out.toString();
    }
}
