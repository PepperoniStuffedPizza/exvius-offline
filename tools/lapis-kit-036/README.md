# lapis-kit-036

Rebuilds the lapis build on Elvlin's Exvius Offline **v0.1.36** (versionCode 9076) from his original APK.
Needs Python 3.8+ (`py -3`). Nothing to install. The older v0.1.31 kit is in `..\lapis-kit`.

## Files
- `patch036.py` - the build script. Helpers: `patch_axml.py`, `zipindex.py`.
- `exvius-offline-v0.1.36.apk` - Elvlin's original v0.1.36 (sha256 280cd1bc...). The only base the offsets fit.
- `game-assets-13.apk` - Elvlin's data revision 13 asset pack (from `exvius-client-assets.zip`, sha256 0f73d5dc...). Its 1,285 rule files are copied into the build.
- `classes8-prompt036.dex` - Elvlin's v0.1.36 `classes8.dex` with the update prompt added (source: `UpdatePrompt036.smali`).
- `speed_cave4.bin` - native code for the battle speed-up.

## Rebuild lapis38 (latest)
Put Elvlin's `exvius-offline-v0.1.36.apk` and `game-assets-13.apk` next to the script, copy `classes8-ff036-lapis38.dex` to `classes8-ff036.dex`, then run:

    py -3 -I patch036.py exvius-offline-v0.1.36.apk game-assets-13.apk exvius-offline-v0.1.36-lapis38-unsigned.apk 50000 9124 prompt=classes8-ff036.dex loop=99 speed3r instantsummon raidautoplay searchname fp50k fpdraws=30 dropx=10 allchallenges kingpots=50 tmrmulti ffbutton

This reproduces the published lapis38 APK byte for byte (unsigned). Sign it with your own key (zipalign -p -f 4, then apksigner). lapisN = versionCode 9086+N for lapis21 to lapis38.

New options since lapis21: `kingpots=50` (Super Premium Box gives 50 of each King Pot), `tmrmulti` (repeatable TMR bundles), `ffbutton` (in-game Speed and Finish buttons; needs `classes8-ff036.dex`). `f3_lapis38.bin` is the native Finish routine (268 bytes, embedded in patch036.py); `f3_lapis32.bin` is the older 184-byte version. `FastForward-lapis32.smali` is the older button class.

## Rebuild lapis21 (older)
First time only: double-click `get-base-files.bat` to download the two base files.

Run in this folder:

    py -3 -I patch036.py exvius-offline-v0.1.36.apk game-assets-13.apk ..\..\v030\exvius-offline-v0.1.36-lapis21-unsigned.apk 50000 9107 prompt=classes8-prompt036.dex loop=99 speed3r instantsummon raidautoplay searchname fp50k fpdraws=30 dropx=10 allchallenges

Then double-click `sign-v030.bat` in the main folder (it signs the newest unsigned APK in `v030`).
VERSIONCODE must be higher than the installed build to install over it and keep the save (lapis21 = 9107, so use 9108+ next).

Options are the same as the v0.1.31 kit (see `..\lapis-kit\README.md`). `noupdates` now edits `classes8.dex`.

## What changed from the v0.1.31 kit
- Game code in libgame.so is byte-identical between v0.1.31 and v0.1.36 (Elvlin only re-pointed his hooks), so loop, search, instant summon, speed and raid patches keep their addresses.
- Elvlin's engine segment was rebuilt:
  - Friend Points 50k: engine offsets 0xa8f10 / 0xa8f28 / 0xa8f38 (vaddr 0x3fb8f10...). The `"0\0"` store moved away from the length byte, so it is three separate instructions now.
  - All challenges: reward loop check at vaddr 0x40d9da8 (`cmp w20,#1; b.ne 0x40da4a8`) -> `bl 0x3fc5aec; tbnz w0,#0,0x40da4a8`. 0x3fc5aec is the "error raised" helper (v0.1.31's 0x40ff7ac; its globals shifted by 8 bytes).
  - Code cave: vaddr 0x4300e30 (file 0x3d8ce30), raid routine at 0x4300f10; engine segment grown from 0x3f0e2c to 0x3f0f40.
- Update prompt: `DataUpdates` moved to `classes8.dex`. v0.1.36 also has a new "finish downloading before the game opens" path; the prompt now sits where both paths meet, and only asks when data is already installed (first-time setup downloads without asking). Elvlin app-update downloads stay removed.
- Rules: data rev 13 has 1,285 rule files (rev 11 had 154), about 31 MB compressed. All go under `assets/rulez/`.

## Notes
- Every native patch asserts the original bytes first, so a wrong base APK fails with an error instead of producing a broken build.
- If Elvlin publishes a data revision past 13 with changed rules, the `rulez/` copies go stale. Rebuild with the new pack's `game-assets.apk` (the script asserts the shapes it edits).
