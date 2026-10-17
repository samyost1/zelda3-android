package com.dishii.zelda3;

import java.nio.file.Files;
import java.nio.file.Paths;
import java.io.ByteArrayOutputStream;
import java.security.MessageDigest;
import java.util.Arrays;

/** Local integration checks; ROMs stay outside the repository. No Android SDK needed. */
public final class TranslationImportTest {
    public static void main(String[] args) throws Exception {
        byte[] pt = Files.readAllBytes(Paths.get(args[0]));
        check(TranslationExtractor.isPtBrRom(pt), "single-ROM route must recognize the exact PT-BR ROM");
        TranslationExtractor.Language lang = TranslationExtractor.extract(pt);
        check("pt-br".equals(lang.code), "Portuguese must be recognized");
        byte[] dialogue = entry(lang.dialogueBlk, 1);
        check(count(dialogue) == 397, "Portuguese has exactly 397 messages");
        byte[] dictionary = entry(lang.dialogueBlk, 0);
        check(count(dictionary) == 97, "Portuguese has 97 dictionary entries");
        byte[] font = entry(lang.fontBlk, 0), widths = entry(lang.fontBlk, 1);
        check(font.length == 4096 && widths.length == 121, "Portuguese font dimensions");
        // Golden values independently computed with snesrev/zelda3's PT decoder,
        // new encoder and font remapper. Dialogue hash ignores dictionary token choices.
        check(hex(MessageDigest.getInstance("SHA-256").digest(font)).equals(
                "89dddaceb78ca7ad97526b306545cfce27824184c210ce1781b561c972334bd9"), "font remapping");
        check(hex(MessageDigest.getInstance("SHA-256").digest(widths)).equals(
                "7c70c7d998f193f6f3bbe32ce216e54039df17a5e6668f83eb2448e5d6a8d2f2"), "font widths");
        MessageDigest textHash = MessageDigest.getInstance("SHA-256");
        for (int i = 0; i < count(dialogue); i++) {
            byte[] msg = entry(dialogue, i);
            ByteArrayOutputStream expanded = new ByteArrayOutputStream();
            for (int p = 0; p < msg.length; p++) {
                int c = msg[p] & 255;
                if (c >= 0x88) {
                    byte[] word = entry(dictionary, c - 0x88);
                    expanded.write(word, 0, word.length);
                } else {
                    expanded.write(c);
                    if (c == 0x87) expanded.write(msg[++p]);
                }
            }
            byte[] bytes = expanded.toByteArray();
            for (int shift = 0; shift < 32; shift += 8) textHash.update((byte) (bytes.length >> shift));
            textHash.update(bytes);
        }
        check(hex(textHash.digest()).equals(
                "f410e6c3d38dfbad65944e4f0df98af015d309b7e2b243f9553da82bca714e13"),
                "all 397 messages must match upstream text and commands");

        byte[] us = Files.readAllBytes(Paths.get(args[1]));
        check(!TranslationExtractor.isPtBrRom(us), "US ROM must keep the default route");
        byte[] usPatch = Files.readAllBytes(Paths.get("app/src/main/assets/zelda3_assets.bps"));
        byte[] ptPatch = Files.readAllBytes(Paths.get("app/src/main/assets/zelda3_assets_ptbr.bps"));
        byte[] base = BpsPatcher.apply(us, usPatch);
        byte[] restored = BpsPatcher.apply(pt, ptPatch);
        check(Arrays.equals(base, restored), "PT-BR patch must reproduce the exact US base assets");
        byte[] singleRom = TranslationExtractor.addLanguage(restored, lang);
        check(Arrays.equals(singleRom, TranslationExtractor.addLanguage(base, lang)),
                "single-ROM and two-ROM imports must be byte-identical");
        byte[] installedMap = asset(singleRom, 96);
        byte[] ptEntry = entry(installedMap, count(installedMap) - 1);
        check(Arrays.equals(entry(ptEntry, 0), "pt-br".getBytes("UTF-8")), "installed language name");
        byte[] conf = entry(ptEntry, 1);
        check(count(ptEntry) == 3, "PT-BR entry includes a separate UI package");
        check(Arrays.equals(entry(ptEntry, 2), lang.uiBlk), "atomic assets container includes UI package");
        check(conf[2] == 3, "Portuguese needs new command encoding and translated-text flags");
        check(Arrays.equals(entry(asset(singleRom, 94), conf[0] & 255), lang.dialogueBlk), "installed dialogue");
        check(Arrays.equals(entry(asset(singleRom, 95), conf[1] & 255), lang.fontBlk), "installed font");
        for (int i = 0; i < u32(base, 80); i++) {
            if (i < 94 || i > 96) check(Arrays.equals(asset(base, i), asset(singleRom, i)),
                    "non-language asset must remain unchanged: " + i);
        }
        TranslationExtractor.Language generic = TranslationExtractor.extract(us);
        check("mod".equals(generic.code), "generic US-layout extraction remains available");
        check(count(entry(generic.dialogueBlk, 1)) == 397, "US messages remain aligned");
        byte[] genericDat = TranslationExtractor.addLanguage(base, generic);
        byte[] genericMap = asset(genericDat, 96);
        check(entry(entry(genericMap, count(genericMap) - 1), 1)[2] == 2, "generic flags unchanged");
        pt[0] ^= 1;
        check(!TranslationExtractor.isPtBrRom(pt), "unknown PT-BR variants must not use the dedicated patch");
        try {
            BpsPatcher.apply(pt, ptPatch);
            throw new AssertionError("Modified ROM must be rejected");
        } catch (BpsPatcher.BpsException expected) { /* source CRC validation */ }
        pt[0] ^= 1;
        ptPatch[ptPatch.length / 2] ^= 1;
        try {
            BpsPatcher.apply(pt, ptPatch);
            throw new AssertionError("Corrupt patch must be rejected");
        } catch (BpsPatcher.BpsException expected) { /* patch CRC validation */ }
        System.out.println("PASS: PT-BR text/font match upstream; single-ROM import matches two-ROM import;"
                + " base assets preserved; generic import and checksum checks pass.");
    }

    private static String hex(byte[] bytes) {
        StringBuilder out = new StringBuilder();
        for (byte b : bytes) out.append(String.format("%02x", b & 255));
        return out.toString();
    }

    private static byte[] asset(byte[] dat, int index) {
        int n = u32(dat, 80), pos = 88 + n * 4 + u32(dat, 84);
        for (int i = 0; i < n; i++) {
            pos = (pos + 3) & ~3;
            int size = u32(dat, 88 + i * 4);
            if (i == index) return Arrays.copyOfRange(dat, pos, pos + size);
            pos += size;
        }
        throw new AssertionError("missing asset " + index);
    }

    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static int u16(byte[] b, int p) {
        return (b[p] & 255) | ((b[p + 1] & 255) << 8);
    }

    private static int u32(byte[] b, int p) {
        return u16(b, p) | (u16(b, p + 2) << 16);
    }

    private static int count(byte[] b) {
        return (u16(b, b.length - 2) % 8192) + 1;
    }

    private static byte[] entry(byte[] b, int i) {
        int trailer = u16(b, b.length - 2);
        int n = (trailer % 8192) + 1, width = trailer >= 8192 ? 4 : 2;
        check(i < n, "packed entry out of bounds");
        int base = (n - 1) * width;
        int start = i == 0 ? 0 : width == 2 ? u16(b, (i - 1) * width) : u32(b, (i - 1) * width);
        int end = i == n - 1 ? b.length - 2 - base : width == 2 ? u16(b, i * width) : u32(b, i * width);
        return Arrays.copyOfRange(b, base + start, base + end);
    }
}
