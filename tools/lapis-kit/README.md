# lapis-kit

Rebuilds the lapis builds of Elvlin's Exvius Offline v0.1.31 from his original APK.
Needs Python 3.8+ (`py -3`). Nothing to install.

## Files
- `patch031.py` - the build script. Helpers: `patch_axml.py`, `zipindex.py`.
- `exvius-offline-v0.1.31.apk` - Elvlin's original v0.1.31 (versionCode 9071). The only base the offsets fit.
- `game-assets-11.apk` - Elvlin's data revision 11 asset pack. Its rule files are copied into the build.
- `classes6-prompt.dex` - Java code for the update prompt (built from `UpdatePrompt.smali`).
- `speed_cave*.bin` - native code for the battle speed-up.

## Rebuild lapis20 (exactly)
Run in this folder:

    py -3 -I patch031.py exvius-offline-v0.1.31.apk game-assets-11.apk ..\..\v030\exvius-offline-v0.1.31-lapisNN-unsigned.apk 50000 VERSIONCODE prompt=classes6-prompt.dex loop=99 speed3r instantsummon raidautoplay searchname fp50k fpdraws=30 dropx=10 allchallenges

Then double-click `sign-v030.bat` in the main folder (it signs the newest unsigned APK in `v030`).
VERSIONCODE must be higher than the installed build to install over it and keep the save (lapis20 = 9106, so use 9107+).

## Arguments
Positional: original APK, asset pack, output APK, Lapis per daily quest, new versionCode.

| Option | Effect |
|---|---|
| `prompt=<dex>` | Asks before data updates; Elvlin app updates skipped |
| `noupdates` | Blocks all update checks (instead of `prompt=`) |
| `loop=N` | Quest auto-play limit |
| `speed2` / `speed3` / `speed3r` | 2x Auto / 3x Auto / 3x Auto + 2.5x Repeat |
| `instantsummon` | Skip summon animation |
| `raidautoplay` | Auto-play allowed in raids |
| `searchname` | Unit search fix |
| `fp50k` | Friend Points bundle gives 50,000 |
| `fpdraws=N` | Friend point multi-summon gives N units (200 points each) |
| `dropx=N` | Enemy item drop quantities x N |
| `allchallenges` | Mission challenges all count as met on clear |

Always on: Lapis Chest (50,000 Lapis for 1 gil, unlimited), unlimited Super Premium Box,
daily quests pay the Lapis amount, and edited rules read from `assets/rulez/` so downloads can't override them.

## Notes
- Native patches assert the original bytes first, so a wrong base APK fails with an error instead of producing a broken build.
- Elvlin's re-uploaded v0.1.31 (versionCode 9072) is a different binary; the offsets would need re-checking before using it as the base.
