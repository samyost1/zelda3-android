package com.dishii.zelda3;

import java.io.IOException;
import java.io.InputStream;
import java.net.URL;

/** Runnable JVM check for the HTTPS-only request boundary. */
public final class RetroAchievementsHttpTest {

    public static void main(String[] args) throws Exception {
        check(RetroAchievementsHttp.isHttpsUrl("https://retroachievements.org/API"));
        check(!RetroAchievementsHttp.isHttpsUrl("http://retroachievements.org/API"));
        check(!RetroAchievementsHttp.isHttpsUrl("ftp://retroachievements.org/API"));
        check(!RetroAchievementsHttp.isHttpsUrl("not a url"));
        check(RetroAchievementsHttp.sameOrigin(
                new URL("https://retroachievements.org/a"),
                new URL("https://RETROACHIEVEMENTS.org:443/b")));
        check(!RetroAchievementsHttp.sameOrigin(
                new URL("https://retroachievements.org/a"),
                new URL("https://media.retroachievements.org/b")));
        check(!RetroAchievementsHttp.sameOrigin(
                new URL("https://retroachievements.org/a"),
                new URL("https://retroachievements.org:444/b")));
        check(RetroAchievementsHttp.queueCapacityForTest() == 8);
        testOversizedResponseIsClientError();
    }

    private static void testOversizedResponseIsClientError() throws Exception {
        InputStream oversized = new InputStream() {
            private int remaining = 1024 * 1024 + 1;

            @Override
            public int read() {
                return remaining-- > 0 ? 0 : -1;
            }

            @Override
            public int read(byte[] buffer, int offset, int length) {
                if (remaining <= 0) return -1;
                int count = Math.min(length, remaining);
                remaining -= count;
                return count;
            }
        };
        try {
            RetroAchievementsHttp.readBody(oversized);
            throw new AssertionError("oversized response accepted");
        } catch (IOException e) {
            check(RetroAchievementsHttp.classifyIOException(e, 200) == -1);
        }
    }

    private static void check(boolean condition) {
        if (!condition) {
            throw new AssertionError("unexpected URL validation result");
        }
    }
}
