package com.dishii.zelda3;

import java.util.Map;

/** Host-side catalog, font coverage and layout checks; no game data required. */
public final class SecondScreenTextTest {
    private static void check(boolean b, String message) {
        if (!b) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        SecondScreenText pt = new SecondScreenText(" PT-BR ");
        check(SaveStateUi.slot(0) == 1, "quick save is native slot 1");
        for (int i = 1; i <= 4; i++) check(SaveStateUi.slot(i) == i + 1, "manual files never shift");
        check(SaveStateUi.title(0, new SecondScreenText("pt-br")).equals("ESTADO RÁPIDO"), "quick title");
        check(SaveStateUi.title(1, new SecondScreenText("pt-br")).equals("ESPAÇO 1"), "manual numbering");
        int[] bindings = new int[14];
        java.util.Arrays.fill(bindings, -1); bindings[6] = 0; bindings[12] = 16;
        check(SaveStateUi.conflict(bindings, 12, 0) == 6, "find occupied button");
        SaveStateUi.assign(bindings, 12, 0);
        check(bindings[6] == -1 && bindings[12] == 0, "confirmed transfer clears previous command");
        SaveStateUi.assign(bindings, 12, -1);
        check(bindings[12] == -1, "clear disables command");
        check(SaveStateUi.mergeControls("Back+A, B", new String[]{"X", "Y"}).equals("Back+A, Y"),
                "custom combination survives writing other commands");

        check(PixelText.supports('.'), "abbreviated tab needs a period glyph");
        check(PixelText.width("EQUIP.") == 44, "period uses four pixels of advance");
        check(pt.gearTab().equals("EQUIP."), "short Portuguese tab");
        check(pt.get("GEAR").equals("EQUIPAMENTOS"), "full panel title preserved");
        check(new SecondScreenText("en").gearTab().equals("GEAR"), "English tab unchanged");
        check(new SecondScreenText(null).gearTab().equals("GEAR"), "default tab unchanged");
        check(pt.get("WIDESCREEN").equals("TELA CHEIA"), "updated fullscreen wording");
        check(pt.get("CRT THIS SCREEN").equals("CRT NA TELA INFERIOR"), "lower screen wording");
        check(pt.get("X ITEM RING").equals("ITENS DO X"), "item shortcut wording");
        check(pt.get("TURN WHILE DASH").equals("MUDAR DIREÇÃO NA CORRIDA"), "dash wording");
        check(pt.get("MIRROR TO DARK").equals("ESPELHO PARA O MUNDO SOMBRIO"), "mirror wording");
        check(pt.get("MAX ITEMS YELLOW").equals("ITENS NO MÁXIMO EM AMARELO"), "yellow wording preserved");
        int[] sheet = new int[128 * 16];
        java.util.Arrays.fill(sheet, 0xfff8f8f8);
        PixelText.shortenLetterL(sheet, 128, 88, 0);
        for (int y = 0; y < 16; y++) for (int x = 0; x < 128; x++)
            check(sheet[y * 128 + x] == (y == 6 && (x == 93 || x == 94) ? 0 : 0xfff8f8f8),
                    "only the final two pixels of the L foot change");
        check(PixelText.advance('L') == 8, "L keeps original advance");
        // Distinct neighboring cells make accidental atlas reads visible to this test.
        int[] atlas = new int[128 * 16];
        for (int y = 0; y < 16; y++) for (int x = 0; x < 128; x++)
            atlas[y * 128 + x] = (x + y) % 3 == 0 ? 0 : 0xff000000 | (y * 128 + x);
        PixelText.shortenLetterL(atlas, 128, 88, 0);
        for (int letter = 0; letter < 26; letter++) {
            int left = (letter % 16) * 8, top = (letter / 16) * 8;
            int[] isolated = PixelText.isolateLetter(atlas, 128, left, top);
            check(isolated.length == 100, "10x10 padded bitmap");
            for (int y = 0; y < 10; y++) for (int x = 0; x < 10; x++) {
                int expected = x == 0 || y == 0 || x == 9 || y == 9 ? 0
                        : atlas[(top + y - 1) * 128 + left + x - 1];
                check(isolated[y * 10 + x] == expected, "exact glyph copy and transparent border");
            }
        }
        for (String label : new String[]{"TELA CHEIA", "TROCAR TELAS", "COM L R",
                "TELA SUPERIOR", "DESLIGADO"}) {
            for (float scale : new float[]{0.75f, 1.25f, 1.7f, 2.4f, 3f}) {
                PixelText.Layout layout = PixelText.fit(label, 640, 64, scale, 1);
                check(layout.scale == scale, "isolation preserves label metrics at fractional scales");
            }
        }

        for (SecondScreenText language : new SecondScreenText[]{pt, new SecondScreenText("en")}) {
            String[][] cases = {{"TURN WHILE DASH", "ON", "OFF"},
                    {"SWAP SCREENS", "ON", "OFF", "RESTART"},
                    {"MSU-1 MUSIC", "ON", "OFF", "RESTART", "NO PACK"},
                    {"SAVE STATE", "", "SAVED"}, {"LOAD STATE", "", "EMPTY", "LOADED"}};
            for (String[] values : cases) {
                float reserve = language.settingValueWidth(values[0]);
                for (int i = 1; i < values.length; i++)
                    check(reserve >= PixelText.width(language.get(values[i])), "all states fit fixed reservation");
                for (float width : new float[]{240, 320, 480, 640, 960}) {
                    float valueWidth = Math.min(width * .4f, reserve * 2.4f);
                    PixelText.Layout label = PixelText.fit(language.get(values[0]), width - valueWidth - 16, 64, 3, 2);
                    for (String line : label.lines)
                        check(PixelText.width(line) * label.scale <= width - valueWidth - 16 + .001f,
                                "label never overlaps fixed value column");
                }
            }
        }
        PixelText.Layout accented = PixelText.fit("CONFIGURAÇÕES DA TELA", 180, 64, 3, 2);
        check(accented.lines.length == 2, "accented two-line label");
        check(accented.lines.length * PixelText.LINE_HEIGHT * accented.scale <= 64,
                "accented label stays inside a full row");
        check(pt.get("SETTINGS").equals("CONFIGURAÇÕES"), "saved locale selection");
        for (String locale : new String[]{null, "", "en", "es", "pt", "pt-pt"})
            check(new SecondScreenText(locale).get("SETTINGS").equals("SETTINGS"), "English fallback");
        check(pt.get("A").equals("A") && pt.get("START").equals("START"), "physical button identifiers");
        check(pt.get("SecondScreenSwap").equals("SecondScreenSwap"), "INI keys not translated");
        check(pt.get("FEB").equals("FEV") && pt.get("OCT").equals("OUT"), "localized dates");
        for (char c : PixelText.ACCENTED.toCharArray()) {
            check(PixelText.base(c) >= 'A' && PixelText.base(c) <= 'Z', "accent base " + c);
            check(PixelText.accent(c).length > 0, "accent pixels " + c);
            for (int[] point : PixelText.accent(c)) {
                check(point[0] - 1 >= 0 && point[0] + 2 <= 8, "accent horizontal bounds");
                check(point[1] - 1 >= -4 && point[1] + 2 <= 11, "accent vertical bounds");
            }
        }
        int tested = 0;
        for (Map.Entry<String, String> entry : SecondScreenText.PORTUGUESE.entrySet()) {
            for (String text : new String[]{entry.getKey(), entry.getValue()}) {
                for (char c : text.toCharArray()) check(PixelText.supports(c), "missing glyph " + c + " in " + text);
                // Logical row widths cover the narrow companion pane through landscape/tablets.
                for (float width : new float[]{240, 320, 480, 640, 960}) {
                    PixelText.Layout fit = PixelText.fit(text, width, 64, 3, 2);
                    check(fit.lines.length <= 2, "at most two lines");
                    check(String.join(" ", fit.lines).equals(text), "no words lost");
                    check(fit.scale > 0 && fit.scale <= 3, "bounded scale");
                    check(fit.lines.length * PixelText.LINE_HEIGHT * fit.scale <= 64.001f, "vertical fit");
                    for (String line : fit.lines)
                        check(PixelText.width(line) * fit.scale <= width + 0.001f, "horizontal fit");
                }
                tested++;
            }
        }
        check(PixelText.fit("CONFIGURAÇÕES", 120, 38, 3, 1).lines.length == 1, "single-line title");
        System.out.println("PASS: locale selection, catalog/font coverage and layouts for " + tested + " labels.");
    }
}
