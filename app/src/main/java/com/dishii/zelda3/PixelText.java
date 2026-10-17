package com.dishii.zelda3;

/** Pixel-font metrics and accent masks shared by drawing and host-side tests. */
final class PixelText {
    static final int LINE_HEIGHT = 15; // base 8px + 4px above + 3px below (including outline)
    static final String ACCENTED = "ÁÀÂÃÉÊÍÓÔÕÚÇ";
    private static final String BASES = "AAAAEEIOOOUC";
    private static final int[][] ACUTE = {{4,-3}, {3,-2}};
    private static final int[][] GRAVE = {{3,-3}, {4,-2}};
    private static final int[][] CIRCUMFLEX = {{3,-3}, {2,-2}, {4,-2}};
    private static final int[][] TILDE = {{2,-3}, {3,-3}, {4,-2}, {5,-2}, {6,-3}};
    private static final int[][] CEDILLA = {{4,8}, {3,9}, {4,9}};
    private static final int[][] NONE = {};

    static char base(char c) {
        int i = ACCENTED.indexOf(c);
        return i < 0 ? c : BASES.charAt(i);
    }

    static int[][] accent(char c) {
        if ("ÁÉÍÓÚ".indexOf(c) >= 0) return ACUTE;
        if (c == 'À') return GRAVE;
        if ("ÂÊÔ".indexOf(c) >= 0) return CIRCUMFLEX;
        if ("ÃÕ".indexOf(c) >= 0) return TILDE;
        return c == 'Ç' ? CEDILLA : NONE;
    }

    static boolean supports(char c) {
        char b = base(c);
        return b >= 'A' && b <= 'Z' || b >= '0' && b <= '9' || " -.".indexOf(b) >= 0;
    }

    static int advance(char c) {
        return c == ' ' ? 5 : c == '.' ? 4 : 8;
    }

    // The original atlas L has a six-pixel foot; keep four and its 8px advance.
    static void shortenLetterL(int[] pixels, int stride, int left, int top) {
        pixels[(top + 6) * stride + left + 5] = 0;
        pixels[(top + 6) * stride + left + 6] = 0;
    }

    // One transparent pixel around the 8x8 glyph prevents sampling adjacent letters.
    // Called only while loading the font, never while drawing text.
    static int[] isolateLetter(int[] atlas, int stride, int left, int top) {
        int[] pixels = new int[10 * 10];
        for (int y = 0; y < 8; y++)
            System.arraycopy(atlas, (top + y) * stride + left, pixels, (y + 1) * 10 + 1, 8);
        return pixels;
    }

    static float width(String text) {
        float width = 0;
        for (int i = 0; i < text.length(); i++) width += advance(text.charAt(i));
        return width;
    }

    static final class Layout {
        final String[] lines;
        final float scale;
        Layout(String[] lines, float scale) { this.lines = lines; this.scale = scale; }
    }

    static Layout fit(String text, float width, float height, float desired, int maxLines) {
        width = Math.max(1, width);
        height = Math.max(1, height);
        String[] lines = {text};
        float widest = width(text);
        if (maxLines > 1 && widest * desired > width) {
            for (int i = 1; i < text.length() - 1; i++) {
                if (text.charAt(i) != ' ') continue;
                String a = text.substring(0, i), b = text.substring(i + 1);
                float candidate = Math.max(width(a), width(b));
                if (candidate < widest) { widest = candidate; lines = new String[]{a, b}; }
            }
        }
        return new Layout(lines, Math.min(desired,
                Math.min(width / Math.max(1, widest), height / (LINE_HEIGHT * lines.length))));
    }
}
