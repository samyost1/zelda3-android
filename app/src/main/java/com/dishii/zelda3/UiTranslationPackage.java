package com.dishii.zelda3;

import java.util.Arrays;
import java.util.zip.CRC32;

/** A versioned, self-contained interface package for the recognized PT-BR ROM. */
final class UiTranslationPackage {
    private static final byte[] MAGIC = {'Z','3','U','I','B','R','0','1'};

    static byte[] extract(byte[] input) throws TranslationExtractor.RomException {
        byte[] rom = input;
        if (rom.length % 32768 == 512) rom = Arrays.copyOfRange(rom, 512, rom.length);
        if (!TranslationExtractor.isPtBrRom(rom))
            throw new TranslationExtractor.RomException("Unsupported Portuguese interface ROM.");
        int[][] entries = UiTranslationResources.ENTRIES;
        byte[] out = new byte[UiTranslationResources.SIZE];
        System.arraycopy(MAGIC, 0, out, 0, 8);
        put(out, 8, 1); put(out, 12, entries.length); put(out, 36, out.length);
        for (int i = 0; i < 20; i++)
            out[16+i] = (byte) Integer.parseInt(UiTranslationResources.SHA1.substring(i*2, i*2+2), 16);
        int p = 40 + entries.length*12;
        for (int i = 0; i < entries.length; i++) {
            int[] e = entries[i]; p = (p+3) & ~3;
            put(out, 40+i*12, e[0]); put(out, 44+i*12, p); put(out, 48+i*12, e[2]);
            System.arraycopy(rom, e[1], out, p, e[2]);
            p += e[2];
        }
        CRC32 crc = new CRC32(); crc.update(out, 0, out.length-4);
        put(out, out.length-4, (int) crc.getValue());
        if (!valid(out)) throw new TranslationExtractor.RomException("Invalid Portuguese interface resources.");
        return out;
    }

    static boolean valid(byte[] data) {
        if (data == null || data.length != UiTranslationResources.SIZE) return false;
        for (int i = 0; i < MAGIC.length; i++) if (data[i] != MAGIC[i]) return false;
        if (get(data, 8) != 1 || get(data, 12) != UiTranslationResources.ENTRIES.length
                || get(data, 36) != data.length) return false;
        for (int i = 0; i < 20; i++)
            if ((data[16+i] & 255) != Integer.parseInt(UiTranslationResources.SHA1.substring(i*2, i*2+2),16)) return false;
        int p = 40 + UiTranslationResources.ENTRIES.length*12;
        for (int i = 0; i < UiTranslationResources.ENTRIES.length; i++) {
            int[] e = UiTranslationResources.ENTRIES[i]; p = (p+3) & ~3;
            if (get(data,40+i*12) != e[0] || get(data,44+i*12) != p || get(data,48+i*12) != e[2]) return false;
            p += e[2];
        }
        CRC32 crc = new CRC32(); crc.update(data, 0, data.length-4);
        return p == data.length-4 && crc.getValue() == UiTranslationResources.CRC
                && (get(data, data.length-4) & 0xffffffffL) == crc.getValue();
    }

    // Test/tool accessor; callers must validate once before reading resources.
    static byte[] resource(byte[] data, int id) {
        if (!valid(data)) throw new IllegalArgumentException("Invalid interface package");
        for (int i=0; i<UiTranslationResources.ENTRIES.length; i++) {
            if (get(data,40+i*12) == id) {
                int p=get(data,44+i*12), n=get(data,48+i*12);
                return Arrays.copyOfRange(data,p,p+n);
            }
        }
        return null;
    }

    private static void put(byte[] out, int p, int value) {
        for (int i=0;i<4;i++) out[p+i]=(byte)(value >>> (i*8));
    }
    private static int get(byte[] in, int p) {
        return (in[p]&255) | (in[p+1]&255)<<8 | (in[p+2]&255)<<16 | (in[p+3]&255)<<24;
    }
    private UiTranslationPackage() {}
}
