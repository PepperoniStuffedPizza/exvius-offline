package com.exvius.local;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/** First-install data download, then a small launcher page with local save tools. */
public final class DataDownloadActivity extends Activity implements DataUpdates.Progress {
    private static final int LAPIS_AMOUNT = 1000;
    private static final int EXPORT_SAVE = 4101, IMPORT_SAVE = 4102;
    private static final int IMPORT_MAX_BYTES = 128 * 1024 * 1024;
    private TextView status;
    private ProgressBar progress;
    private Button retry;
    private boolean repairAssets;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (DataUpdates.ready(this)) {
            // A running game is resumed as before. The save tools only appear before the game opens,
            // so the client never holds a save that changed underneath it.
            if (DataUpdates.gameOpened()) openGame(true);
            else showLauncherPage();
            return;
        }
        if (DataUpdates.hasPending(this) && DataUpdates.gameOpened()) {
            showDownloadPage();
            failed("An update is ready. Fully close Exvius, then open it again to apply the update.");
            return;
        }
        repairAssets = DataUpdates.clientAssetsMissing(this);
        showDownloadPage();
        DataUpdates.prepare(this, this, repairAssets);
    }

    private void showDownloadPage() {
        if (status != null) return;
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setGravity(Gravity.CENTER);
        int padding = (int) (24 * getResources().getDisplayMetrics().density);
        page.setPadding(padding, padding, padding, padding);
        TextView title = new TextView(this);
        title.setText("Exvius Offline");
        title.setTextSize(28);
        title.setGravity(Gravity.CENTER);
        page.addView(title);
        status = new TextView(this);
        status.setText("Preparing the complete game data download.\nAfter setup, you can play offline.");
        status.setTextSize(17);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0, padding, 0, padding);
        page.addView(status);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(1000);
        page.addView(progress, new LinearLayout.LayoutParams(-1, -2));
        retry = new Button(this);
        retry.setText("Retry");
        retry.setVisibility(View.GONE);
        retry.setOnClickListener(view -> {
            retry.setVisibility(View.GONE);
            DataUpdates.prepare(this, this, repairAssets);
        });
        page.addView(retry);
        setContentView(page);
    }

    // --- launcher page: Play, +Lapis, back up and restore the local save ----------------------------
    private TextView toolStatus;
    private Button[] toolButtons;

    private void showLauncherPage() {
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setGravity(Gravity.CENTER);
        int padding = (int) (24 * getResources().getDisplayMetrics().density);
        page.setPadding(padding, padding, padding, padding);
        TextView title = new TextView(this);
        title.setText("Exvius Offline");
        title.setTextSize(28);
        title.setGravity(Gravity.CENTER);
        page.addView(title);
        toolStatus = new TextView(this);
        toolStatus.setText("Save tools work on your local save before the game opens.");
        toolStatus.setTextSize(15);
        toolStatus.setGravity(Gravity.CENTER);
        toolStatus.setPadding(0, padding / 2, 0, padding / 2);
        page.addView(toolStatus);
        Button play = toolButton(page, "Play");
        Button lapis = toolButton(page, "Add " + LAPIS_AMOUNT + " Lapis");
        Button backup = toolButton(page, "Back up save to a file");
        Button restore = toolButton(page, "Restore save from a file");
        toolButtons = new Button[]{play, lapis, backup, restore};
        play.setOnClickListener(view -> openGame(true));
        lapis.setOnClickListener(view -> runTool("Adding Lapis...", () -> {
            org.json.JSONObject result = new org.json.JSONObject(LocalGameBridge.grantLapis(LAPIS_AMOUNT));
            return "Added " + result.getInt("added") + " Lapis. Balance: " +
                (result.getInt("free") + result.getInt("paid")) + ".";
        }));
        backup.setOnClickListener(view -> {
            Intent pick = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            pick.addCategory(Intent.CATEGORY_OPENABLE);
            pick.setType("application/json");
            pick.putExtra(Intent.EXTRA_TITLE, "exvius-save-" +
                new SimpleDateFormat("yyyyMMdd-HHmm", Locale.US).format(new Date()) + ".json");
            startPicker(pick, EXPORT_SAVE);
        });
        restore.setOnClickListener(view -> {
            Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            pick.addCategory(Intent.CATEGORY_OPENABLE);
            pick.setType("*/*");
            startPicker(pick, IMPORT_SAVE);
        });
        setContentView(page);
    }

    private Button toolButton(LinearLayout page, String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        page.addView(button, new LinearLayout.LayoutParams(-1, -2));
        return button;
    }

    private void startPicker(Intent pick, int code) {
        try {
            startActivityForResult(pick, code);
        } catch (android.content.ActivityNotFoundException error) {
            toolStatus.setText("This device has no file picker for saves.");
        }
    }

    private interface Tool { String run() throws Exception; }

    private void runTool(String working, Tool tool) {
        setToolsEnabled(false);
        toolStatus.setText(working);
        new Thread(() -> {
            String message;
            try {
                message = tool.run();
            } catch (Exception error) {
                android.util.Log.e("ExviusSaveTools", "Save tool failed", error);
                message = readable(error);
            }
            final String shown = message;
            runOnUiThread(() -> {
                if (isFinishing()) return;
                toolStatus.setText(shown);
                setToolsEnabled(true);
            });
        }, "ExviusSaveTools").start();
    }

    private void setToolsEnabled(boolean enabled) {
        if (toolButtons == null) return;
        for (Button button : toolButtons) {
            button.setEnabled(enabled);
            button.setAlpha(enabled ? 1f : 0.4f);
        }
    }

    // Chaquopy reports a Python error as "ValueError: message"; show only the message.
    private static String readable(Throwable error) {
        while (error.getCause() != null && (error.getMessage() == null || error.getMessage().isEmpty()))
            error = error.getCause();
        String text = error.getMessage() == null ? "Something went wrong." : error.getMessage();
        int line = text.indexOf('\n');
        if (line > 0) text = text.substring(0, line);
        int colon = text.indexOf(": ");
        if (colon > 0 && text.substring(0, colon).matches("[A-Za-z_.]+(Error|Exception)")) text = text.substring(colon + 2);
        return text;
    }

    @Override protected void onActivityResult(int code, int result, Intent data) {
        super.onActivityResult(code, result, data);
        if (result != RESULT_OK || data == null || data.getData() == null || toolStatus == null) return;
        Uri file = data.getData();
        if (code == EXPORT_SAVE) {
            runTool("Backing up your save...", () -> {
                byte[] save = LocalGameBridge.exportSave().getBytes(StandardCharsets.UTF_8);
                try (OutputStream out = getContentResolver().openOutputStream(file, "wt")) {
                    if (out == null) throw new java.io.IOException("Could not open that file for writing.");
                    out.write(save);
                }
                return "Save backed up (" + (save.length / 1024) + " KB).";
            });
        } else if (code == IMPORT_SAVE) {
            new AlertDialog.Builder(this)
                .setTitle("Restore this save?")
                .setMessage("Your current save will be replaced. A copy of it is kept inside the app. " +
                            "Exvius closes afterwards; open it again to play the restored save.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Restore", (dialog, which) -> restoreSave(file))
                .show();
        }
    }

    private void restoreSave(Uri file) {
        runTool("Restoring your save...", () -> {
            String text;
            try (InputStream input = getContentResolver().openInputStream(file);
                 ByteArrayOutputStream output = new ByteArrayOutputStream()) {
                if (input == null) throw new java.io.IOException("Could not open that file.");
                byte[] buffer = new byte[65536];
                int count;
                while ((count = input.read(buffer)) != -1) {
                    if (output.size() + count > IMPORT_MAX_BYTES)
                        throw new java.io.IOException("That file is too large to be an Exvius save.");
                    output.write(buffer, 0, count);
                }
                text = new String(output.toByteArray(), StandardCharsets.UTF_8);
            }
            org.json.JSONObject restored = new org.json.JSONObject(LocalGameBridge.importSave(text));
            runOnUiThread(() -> new AlertDialog.Builder(this)
                .setTitle("Save restored")
                .setMessage(restored.optString("name") + "  |  Rank " + restored.optInt("rank") +
                            "\n\nExvius will now close. Open it again to play.")
                .setCancelable(false)
                .setPositiveButton("Close Exvius", (dialog, which) -> {
                    // Restart from scratch so the engine loads the new save through its normal start-up.
                    finishAffinity();
                    android.os.Process.killProcess(android.os.Process.myPid());
                })
                .show());
            return "Save restored.";
        });
    }

    private void openGame(boolean checkForUpdates) {
        try {
            GameAssets.attach(getApplicationContext());
        } catch (IllegalStateException error) {
            android.util.Log.e("ExviusUpdates", "Could not open downloaded client assets", error);
            repairAssets = true;
            showDownloadPage();
            failed("The game assets could not be opened. Connect to the internet and tap Retry to repair them.");
            return;
        }
        if (checkForUpdates) DataUpdates.checkInBackground(this);
        Intent game = new Intent();
        game.setClassName(getPackageName(), "com.square_enix.android_googleplay.FFBEWW.Lapis");
        startActivity(game);
        finish();
    }
    @Override public void onDestroy() {
        DataUpdates.detach(this);
        super.onDestroy();
    }
    @Override public void onResume() {
        super.onResume();
        DataUpdates.installerReturned();
    }

    @Override public void update(String message, long done, long total) {
        runOnUiThread(() -> {
            if (isFinishing()) return;
            status.setText(message);
            progress.setIndeterminate(total <= 0);
            if (total > 0) progress.setProgress((int) Math.min(1000, done * 1000 / total));
        });
    }
    @Override public void complete() { runOnUiThread(() -> { if (!isFinishing()) openGame(false); }); }
    @Override public void failed(String message) {
        runOnUiThread(() -> {
            if (isFinishing()) return;
            status.setText(message);
            progress.setIndeterminate(false);
            retry.setVisibility(View.VISIBLE);
        });
    }
}
