
package com.dishii.zelda3;
import org.libsdl.app.SDLActivity;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.ActivityInfo;
import android.hardware.display.DisplayManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.view.Display;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.RelativeLayout;
import android.widget.Toast;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.FileOutputStream;
import android.util.Log;

//This class is the main SDLActivity and just sets up a bunch of default files
public class MainActivity extends SDLActivity {

    private static final String TAG = "Zelda3SecondScreen";

    private SecondScreenPresentation secondScreen;
    private DisplayManager displayManager;
    // True while we've deliberately dismissed the presentation because the
    // activity left the foreground; tells the dismiss-recovery logic not to
    // re-show it until onStart.
    private boolean secondScreenHidden;

    private MinimapView fullMapOverlay;
    private boolean fullMapVisible = false;
    private int mapToggleKeyCode = -1; // resolved from ini at startup; -1 = disabled

    private final DisplayManager.DisplayListener displayListener =
            new DisplayManager.DisplayListener() {
        @Override
        public void onDisplayAdded(int displayId) {
            showSecondScreenIfPresent();
        }

        @Override
        public void onDisplayRemoved(int displayId) {
            if (secondScreen != null && secondScreen.getDisplay().getDisplayId() == displayId) {
                dismissSecondScreen();
                // fall over to any remaining external display
                showSecondScreenIfPresent();
            }
        }

        @Override
        public void onDisplayChanged(int displayId) {}
    };

    // Debug: `adb shell am broadcast -a com.dishii.zelda3.DUMP` writes the
    // second screen's current frame to the app's external files dir.
    private final BroadcastReceiver dumpReceiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            if (secondScreen != null) {
                secondScreen.dumpToFile(new File(getExternalFilesDir(null), "second_screen.png"));
            } else if (CompanionActivity.instance != null) {
                CompanionActivity.instance.dumpToFile(new File(getExternalFilesDir(null), "second_screen.png"));
            }
            byte[] b = new byte[256];
            try {
                GameState.readSram(b);
                Log.i(TAG, String.format("pendants=0x%02x crystals=0x%02x", b[0x74], b[0x7A]));
            } catch (UnsatisfiedLinkError ignored) {}
        }
    };

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

        // None of the second-screen setup is worth dying for: if any of it
        // throws on unfamiliar hardware (issue #19: instant close at launch on
        // the Thor Max), run the game single-screen instead of crashing.
        try {
            displayManager = (DisplayManager) getSystemService(DISPLAY_SERVICE);
            displayManager.registerDisplayListener(displayListener, null);
            showSecondScreenIfPresent();

            IntentFilter dumpFilter = new IntentFilter("com.dishii.zelda3.DUMP");
            if (Build.VERSION.SDK_INT >= 33) {
                registerReceiver(dumpReceiver, dumpFilter, 2 /* Context.RECEIVER_EXPORTED */);
            } else {
                registerReceiver(dumpReceiver, dumpFilter);
            }
        } catch (Throwable e) {
            Log.e(TAG, "Second screen setup failed", e);
            CrashLog.report(this, "second screen setup", e);
            Toast.makeText(this, "Second screen disabled: " + e, Toast.LENGTH_LONG).show();
        }

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

    // Show the companion Presentation on the first display the game itself is
    // not running on. When the activity lives on the default display (normal
    // case) that's the Thor's bottom screen; when the game is launched onto a
    // secondary display, the companion falls back to the main panel instead.
    private void showSecondScreenIfPresent() {
        if (secondScreen != null || secondScreenHidden) {
            return;
        }
        int gameDisplayId = getWindowManager().getDefaultDisplay().getDisplayId();
        for (Display display : displayManager.getDisplays()) {
            if (display.getDisplayId() == gameDisplayId) {
                continue;
            }
            // The framework refuses Presentation windows on the default display,
            // so when the game itself runs on a secondary display (SecondScreenSwap)
            // the companion UI is hosted by a plain activity there instead.
            if (display.getDisplayId() == Display.DEFAULT_DISPLAY) {
                startCompanionActivity(display.getDisplayId());
                return;
            }
            try {
                secondScreen = new SecondScreenPresentation(this, display);
                // If the system dismisses the Presentation behind our back (display
                // config change etc.), drop the stale reference and try to re-show,
                // otherwise the bottom screen is gone until the app restarts.
                secondScreen.setOnDismissListener(new android.content.DialogInterface.OnDismissListener() {
                    @Override
                    public void onDismiss(android.content.DialogInterface dialog) {
                        if (secondScreen == dialog) {
                            secondScreen = null;
                            if (!isFinishing() && !secondScreenHidden) {
                                getWindow().getDecorView().post(new Runnable() {
                                    @Override
                                    public void run() {
                                        showSecondScreenIfPresent();
                                    }
                                });
                            }
                        }
                    }
                });
                secondScreen.show();
                Log.i(TAG, "Showing second screen on display " + display.getDisplayId()
                        + " (" + display.getName() + ")");
            } catch (RuntimeException e) {
                // InvalidDisplayException, or whatever else this firmware's
                // WindowManager throws for a display it won't hand out
                // (SecurityException on some builds); try the next display
                Log.w(TAG, "Display " + display.getDisplayId() + " rejected Presentation", e);
                secondScreen = null;
                continue;
            }
            return;
        }
    }

    private void dismissSecondScreen() {
        if (secondScreen != null) {
            secondScreen.dismiss();
            secondScreen = null;
        }
        CompanionActivity companion = CompanionActivity.instance;
        if (companion != null) {
            companion.finish();
        }
    }

    // Companion UI on the main display for the swapped-screens layout. Launched
    // in its own task (required to target another display); the window is
    // non-focusable so gamepad input stays with the game, mirroring the
    // Presentation's behavior on the bottom screen.
    private void startCompanionActivity(int displayId) {
        if (CompanionActivity.instance != null || Build.VERSION.SDK_INT < 26) {
            return;
        }
        Intent intent = new Intent(this, CompanionActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        android.app.ActivityOptions options = android.app.ActivityOptions.makeBasic();
        options.setLaunchDisplayId(displayId);
        try {
            startActivity(intent, options.toBundle());
        } catch (RuntimeException e) {
            // launching on another display can be refused outright; the game
            // itself is already up, so just go without the companion screen
            Log.w(TAG, "Companion launch on display " + displayId + " refused", e);
            return;
        }
        Log.i(TAG, "Launching companion activity on display " + displayId);
    }

    // Use onStop/onStart rather than onPause/onResume: onPause also fires for
    // transient interruptions (permission dialogs, display config changes) where
    // tearing down the bottom screen would just cause flicker, and SDLActivity
    // itself only pauses the native thread in onStop on API 24+. onStop means
    // the user actually left the app, so the bottom screen should go back to
    // whatever the system shows there instead of keeping the mod UI up.
    @Override
    protected void onStop() {
        secondScreenHidden = true;
        dismissSecondScreen();
        super.onStop();
    }

    @Override
    protected void onStart() {
        super.onStart();
        secondScreenHidden = false;
        showSecondScreenIfPresent();
    }

    @Override
    protected void onDestroy() {
        try {
            unregisterReceiver(dumpReceiver);
        } catch (IllegalArgumentException ignored) {}
        dismissSecondScreen();
        if (displayManager != null) {
            displayManager.unregisterDisplayListener(displayListener);
        }
        super.onDestroy();
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
