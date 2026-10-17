package com.dishii.zelda3;

import java.nio.file.*;
import java.util.Arrays;

public final class UiTranslationPackageTest {
    private static void check(boolean ok, String what) {
        if (!ok) throw new AssertionError(what);
    }
    public static void main(String[] args) throws Exception {
        byte[] pt = Files.readAllBytes(Paths.get(args[0]));
        byte[] us = Files.readAllBytes(Paths.get(args[1]));
        byte[] ui = UiTranslationPackage.extract(pt);
        check(UiTranslationPackage.valid(ui), "real package");
        byte[] headered = new byte[pt.length + 512];
        System.arraycopy(pt, 0, headered, 512, pt.length);
        check(Arrays.equals(ui, UiTranslationPackage.extract(headered)), "copier header");
        for (int[] e : UiTranslationResources.ENTRIES) {
            check(Arrays.equals(UiTranslationPackage.resource(ui, e[0]),
                    Arrays.copyOfRange(pt, e[1], e[1]+e[2])), "ROM resource " + e[0]);
        }
        check(!UiTranslationPackage.valid(null), "missing package");
        check(!UiTranslationPackage.valid(new byte[0]), "empty package");
        check(!UiTranslationPackage.valid(Arrays.copyOf(ui, ui.length-1)), "truncation");
        for (int p : new int[] {0, 8, 12, 16, 36, 40, 44, 48, 600, ui.length-1}) {
            byte[] bad = ui.clone(); bad[p] ^= 1;
            check(!UiTranslationPackage.valid(bad), "corruption at " + p);
        }
        for (byte[] rom : new byte[][] {us, Arrays.copyOf(pt, pt.length-1)}) {
            try { UiTranslationPackage.extract(rom); throw new AssertionError("accepted unsupported ROM"); }
            catch (TranslationExtractor.RomException expected) { }
        }
        byte[] badRom = pt.clone(); badRom[0] ^= 1;
        try { UiTranslationPackage.extract(badRom); throw new AssertionError("accepted changed ROM"); }
        catch (TranslationExtractor.RomException expected) { }
        TranslationExtractor.Language lang = TranslationExtractor.extract(pt);
        check(Arrays.equals(lang.uiBlk, ui), "PT import includes interface");
        check(TranslationExtractor.extract(us).uiBlk == null, "other languages unchanged");
        if (args.length > 2) Files.write(Paths.get(args[2]), ui);
        System.out.println("PASS: PT-BR UI resources, checksum, headers and invalid packages");
    }
}
