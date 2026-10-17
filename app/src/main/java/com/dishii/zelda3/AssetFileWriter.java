package com.dishii.zelda3;

import android.os.Build;
import java.io.File;
import java.io.IOException;

/** Publish one complete container without deleting its previous version first. */
final class AssetFileWriter {
    static void replace(File temporary, File destination) throws IOException {
        if (Build.VERSION.SDK_INT >= 21) {
            Api21.replace(temporary, destination);
        } else if (!temporary.renameTo(destination)) {
            // Android's File.renameTo uses the same-filesystem rename syscall.
            // A failed replacement leaves the old file intact.
            throw new IOException("couldn't save the assets file");
        }
    }

    // Isolate unavailable classes so API16-20 never need to resolve them.
    private static final class Api21 {
        static void replace(File temporary, File destination) throws IOException {
            try {
                android.system.Os.rename(temporary.getAbsolutePath(), destination.getAbsolutePath());
            } catch (android.system.ErrnoException e) {
                throw new IOException("couldn't save the assets file", e);
            }
        }
    }
    private AssetFileWriter() {}
}
