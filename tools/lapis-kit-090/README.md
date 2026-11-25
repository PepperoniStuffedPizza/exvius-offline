# lapis kit for Elvlin's beta v0.1.90 (lapis60+)

Installs over the lapis app (package `com.exvius.offline.test`) and keeps the save. Includes Elvlin's beta fixes (5-star awakening crash, 5-star Select Summon, ...).

1. Build the v0.1.36 lapis libgame with `../lapis-kit-036/patch036.py` (same options) and extract `lib/arm64-v8a/libgame.so`.
2. `python3 port090.py <libgame 0.1.36 original> <libgame 0.1.36 lapis> <libgame beta 0.1.90 original> <out libgame>`
   Copies the client-code patches (the game code is identical at every patched site), moves the code cave to 0x4334100
   (after the beta's larger engine segment) re-encoding its PC-relative references, moves the fast-forward flag to
   0x4731c20, and re-applies rules/ -> rulez/, Friend Points 50,000 and mission challenges at beta addresses.
3. `python3 build090.py <beta.apk> <v0.1.36.apk> <game-assets.apk from data r34 client-assets> <out libgame> classes8-beta090-lapis.dex <out-unsigned.apk> 50000 9146 fpdraws=30 multidraws=30 multiprice dropx=10 kingpots=50 tmrmulti chest=500000 stmr=10`
4. Sign on the PC with `sign-v030.bat`.

classes8 changes (`smali/`): FastForward button (flag 0x4731c20) attached in onActivityResumed; game data frozen at
revision 34 (the rulez/ copies are r34), so newer data needs a rebuild. App updates never trigger (versionCode > beta's).
