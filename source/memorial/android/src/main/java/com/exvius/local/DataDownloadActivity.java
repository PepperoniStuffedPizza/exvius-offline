package com.exvius.local;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

/** First-install data download, then a small launcher page (Play, add Lapis). */
public final class DataDownloadActivity extends Activity implements DataUpdates.Progress {
    private static final int LAPIS_AMOUNT = 50000;
    private TextView status;
    private ProgressBar progress;
    private Button retry;
    private boolean repairAssets;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (DataUpdates.ready(this)) {
            // A running game is resumed as before. The Lapis tool only appears before the game opens,
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

    // --- launcher page: Play and +Lapis ------------------------------------------------------------
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
        toolStatus.setText("Lapis is added to your local save before the game opens.");
        toolStatus.setTextSize(15);
        toolStatus.setGravity(Gravity.CENTER);
        toolStatus.setPadding(0, padding / 2, 0, padding / 2);
        page.addView(toolStatus);
        Button play = toolButton(page, "Play");
        Button lapis = toolButton(page, String.format(java.util.Locale.US, "Add %,d Lapis", LAPIS_AMOUNT));
        toolButtons = new Button[]{play, lapis};
        play.setOnClickListener(view -> openGame(true));
        lapis.setOnClickListener(view -> runTool("Adding Lapis...", () -> {
            org.json.JSONObject result = new org.json.JSONObject(LocalGameBridge.grantLapis(LAPIS_AMOUNT));
            return String.format(java.util.Locale.US, "Added %,d Lapis. Balance: %,d.",
                result.getInt("added"), result.getInt("free") + result.getInt("paid"));
        }));
        setContentView(page);
    }

    private Button toolButton(LinearLayout page, String label) {
        Button button = new Button(this);
        button.setText(label);
        button.setAllCaps(false);
        page.addView(button, new LinearLayout.LayoutParams(-1, -2));
        return button;
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
                android.util.Log.e("ExviusLauncher", "Launcher tool failed", error);
                message = readable(error);
            }
            final String shown = message;
            runOnUiThread(() -> {
                if (isFinishing()) return;
                toolStatus.setText(shown);
                setToolsEnabled(true);
            });
        }, "ExviusLauncherTool").start();
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
