package com.dishii.zelda3;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/** Canonical source-ROM checks used before enabling RetroAchievements. */
final class RomVerification {

    static final int ROM_SIZE = 1048576;
    private static final int COPIER_HEADER = 512;
    static final String CANONICAL_US_MD5 = "608c22b8ff930c62dc2de54bcd6eba72";

    private RomVerification() {}

    static byte[] stripCopierHeader(byte[] rom) {
        if (rom.length == ROM_SIZE + COPIER_HEADER && (rom.length % 1024) == COPIER_HEADER) {
            byte[] trimmed = new byte[ROM_SIZE];
            System.arraycopy(rom, COPIER_HEADER, trimmed, 0, ROM_SIZE);
            return trimmed;
        }
        return rom;
    }

    static boolean isCanonicalOriginal(byte[] rom, byte[] bps) {
        return BpsPatcher.matchesSource(rom, bps)
                && rom.length == ROM_SIZE
                && CANONICAL_US_MD5.equals(md5Hex(rom));
    }

    static String md5Hex(byte[] data) {
        try {
            byte[] digest = MessageDigest.getInstance("MD5").digest(data);
            StringBuilder hex = new StringBuilder(digest.length * 2);
            for (byte b : digest) {
                hex.append(Character.forDigit((b >>> 4) & 0xf, 16));
                hex.append(Character.forDigit(b & 0xf, 16));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new AssertionError("MD5 unavailable", e);
        }
    }
}
