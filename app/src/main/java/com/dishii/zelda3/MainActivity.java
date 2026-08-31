
package com.dishii.zelda3;
import org.libsdl.app.SDLActivity;
import android.content.pm.ActivityInfo;
import android.os.Bundle;
import android.os.Environment;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.RelativeLayout;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.FileOutputStream;
import android.util.Log;

//This class is the main SDLActivity and just sets up a bunch of default files
public class MainActivity extends SDLActivity {

    private static final String TAG = "Zelda3MainActivity";

    private MinimapView fullMapOverlay;
    private boolean fullMapVisible = false;
    private int mapToggleKeyCode = -1; // resolved from ini at startup; -1 = disabled

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        CrashLog.install(this);

        fullMapOverlay = new MinimapView(this);
        fullMapOverlay.setVisibility(View.GONE);
        // Don't let the overlay steal input focus from the SDL surface.
        fullMapOverlay.setFocusable(false);
        fullMapOverlay.setFocusableInTouchMode(false);
        ViewGroup root = (ViewGroup) SDLActivity.getContentView();
        root.addView(fullMapOverlay, new RelativeLayout.LayoutParams(
                RelativeLayout.LayoutParams.MATCH_PARENT,
                RelativeLayout.LayoutParams.MATCH_PARENT));

        // Check if external storage is available
        if (isExternalStorageWritable()) {
            // Get the root directory of the external storage
            File externalDir = getExternalFilesDir(null);

            if (externalDir != null) {

                // Create a file object for the config file
                File configFile = new File(externalDir, "zelda3.ini");

                File saves_folder = new File(externalDir+ File.separator + "saves");

                File saves_ref_folder = new File(saves_folder + File.separator + "ref");

                // Check if the folder doesn't exist, then create it
                saves_folder.mkdirs();

                saves_ref_folder.mkdirs();


                //copy reference saves and config to external data dir so user can change if needed.

                try {
                    AssetCopyUtil.copyAssetsToExternal(this, "saves/ref", getExternalFilesDir(null).getAbsolutePath() + "/saves/ref");
                    if (configFile.createNewFile()) {
                        InputStream inputStream;
                        try {
                            inputStream = getAssets().open("zelda3.ini");  // Replace with your actual asset file name
                        } catch (IOException e) {
                            e.printStackTrace();
                            return;
                        }
                        // Write configuration data to configFile
                        writeDataToFile(configFile,inputStream);
                    }
                } catch (Exception e) {
                    // missing defaults are recoverable; the game creates its
                    // own ini and saves, so don't let this kill the launch
                    Log.e(TAG, "Copying default config/saves failed", e);
                }

            }
        }

        mapToggleKeyCode = resolveMapToggleButton();
    }

    @Override
    public void setOrientationBis(int w, int h, boolean resizable, String hint) {
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
    }

    private void writeDataToFile(File file,InputStream inputStream) {
        try {
            // Copy the content from the asset InputStream to the target file
            FileOutputStream outputStream = new FileOutputStream(file);
            byte[] buffer = new byte[1024];
            int length;
            while ((length = inputStream.read(buffer)) > 0) {
                outputStream.write(buffer, 0, length);
            }
            outputStream.close();
            inputStream.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    // Check if external storage is available and writable
    private boolean isExternalStorageWritable() {
        String state = Environment.getExternalStorageState();
        return Environment.MEDIA_MOUNTED.equals(state);
    }

    @Override
    public boolean dispatchKeyEvent(KeyEvent event) {
        if (mapToggleKeyCode >= 0
                && event.getKeyCode() == mapToggleKeyCode
                && event.getAction() == KeyEvent.ACTION_DOWN
                && event.getRepeatCount() == 0) {
            toggleFullMap();
            return true; // consume — don't let this reach the game
        }
        return super.dispatchKeyEvent(event);
    }

    /**
     * Read MapToggleButton from [Android] in zelda3.ini and return the
     * corresponding Android KeyEvent keycode, or -1 if absent/unrecognised.
     */
    private int resolveMapToggleButton() {
        String name = readIniValue("[Android]", "MapToggleButton");
        if (name == null || name.isEmpty()) return -1;
        switch (name.trim()) {
            case "A":         return KeyEvent.KEYCODE_BUTTON_A;
            case "B":         return KeyEvent.KEYCODE_BUTTON_B;
            case "X":         return KeyEvent.KEYCODE_BUTTON_X;
            case "Y":         return KeyEvent.KEYCODE_BUTTON_Y;
            case "Back":      return KeyEvent.KEYCODE_BUTTON_SELECT;
            case "Guide":     return KeyEvent.KEYCODE_BUTTON_MODE;
            case "Start":     return KeyEvent.KEYCODE_BUTTON_START;
            case "L3":        return KeyEvent.KEYCODE_BUTTON_THUMBL;
            case "R3":        return KeyEvent.KEYCODE_BUTTON_THUMBR;
            case "L1": case "Lb": return KeyEvent.KEYCODE_BUTTON_L1;
            case "R1": case "Rb": return KeyEvent.KEYCODE_BUTTON_R1;
            case "L2":        return KeyEvent.KEYCODE_BUTTON_L2;
            case "R2":        return KeyEvent.KEYCODE_BUTTON_R2;
            case "DpadUp":    return KeyEvent.KEYCODE_DPAD_UP;
            case "DpadDown":  return KeyEvent.KEYCODE_DPAD_DOWN;
            case "DpadLeft":  return KeyEvent.KEYCODE_DPAD_LEFT;
            case "DpadRight": return KeyEvent.KEYCODE_DPAD_RIGHT;
            default:          return -1;
        }
    }

    /** Read one key = value from a section of the user's zelda3.ini. */
    private String readIniValue(String section, String key) {
        try {
            java.io.File dir = getExternalFilesDir(null);
            if (dir == null) return null;
            java.io.File f = new java.io.File(dir, "zelda3.ini");
            java.io.BufferedReader in = new java.io.BufferedReader(new java.io.FileReader(f));
            String line, cur = "", v = null;
            while ((line = in.readLine()) != null) {
                String t = line.trim();
                if (t.startsWith("[")) cur = t;
                else if (cur.equalsIgnoreCase(section)
                        && t.toLowerCase().startsWith(key.toLowerCase())
                        && t.length() > key.length()
                        && t.substring(key.length()).trim().startsWith("=")) {
                    v = t.substring(t.indexOf('=') + 1).trim();
                }
            }
            in.close();
            return v;
        } catch (java.io.IOException e) {
            return null;
        }
    }

    private void toggleFullMap() {
        fullMapVisible = !fullMapVisible;
        fullMapOverlay.setVisibility(fullMapVisible ? View.VISIBLE : View.GONE);
    }
}
