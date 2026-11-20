# exvius-offline lapis builds: technical notes (updated 2026-11-15)

Current build: **v0.1.31-lapis20**, versionCode 9106, published on GitLab as release `v0.1.31-lapis20`.
Rebuild kit: `C:\Users\Suumy\Documents\exvius-offline\tools\lapis-kit` (see README.md there). The kit rebuilds lapis20 byte for byte.

## Background
- The public repo source is the OLD Python/Frida engine (v0.1.24 design). From v0.1.25 on, Elvlin's offline engine is compiled into `lib/arm64-v8a/libgame.so` (stripped, no source). So every change is a patch to Elvlin's finished APK, never a source build.
- Base: Elvlin's **v0.1.31, versionCode 9071** (sha256 7dfedd2e...). He later re-uploaded v0.1.31 as versionCode 9072 ("Fix for S2 banner"). That is a different binary; all offsets below are for 9071 and must be re-checked before switching.
- Data: Elvlin's data revision 11. Its `client-assets` pack contains `game-assets.apk`, whose `assets/rules/` (154 files) overrides the APK's rules. Fix: patch the single `\0rules/\0` string in libgame to `\0rulez/\0` and ship edited copies under `assets/rulez/`. If Elvlin changes rules in a later data revision, the `rulez/` copies go stale and need rebuilding from the new pack.

## Build and sign workflow
- `patch031.py <orig.apk> <game-assets-11.apk> <out-unsigned.apk> <lapis> <versionCode> [options]`: rewrites the zip keeping compression types, drops META-INF signatures, patches the binary manifest versionCode (attr 0x0101021b), applies the options.
- Signing happens on the PC only: `sign-v030.bat` signs the newest `v030\*-unsigned.apk` (zipalign -p -f 4 + apksigner, build-tools 36.0.0, key `tools\vendor\my-exvius.jks`, alias my-exvius, password file `tools\vendor\keystore-password.txt`). Output drops "-unsigned". The key never leaves the PC.
- New builds need a higher versionCode to install over the old one and keep the save.
- Publishing: edit `$version`, `$tag`, `$apk` and the notes in `upload-release.ps1`, run `upload-release.bat` (token from `tools\vendor\gitlab-token.txt`). GitLab project StuffedPepperoniPizza/exvius-offline, id 88853703.
- The user prefers no adb/USB debugging. Computer use has only click access to File Explorer and Command Prompt (double-click .bat files). Never paste tokens or passwords into chat.

## Address conversion (libgame.so, 9071)
- Original game code: file offset == vaddr (e.g. 0x19c0398).
- Offline engine segment (3rd LOAD, R E): file = vaddr - 0x3f10000 + 0x399c000. Its size was extended to 0x40e000 so a code cave fits at file 0x3da9ef0 (vaddr 0x431def0) up to vaddr 0x431e000.
- Every native patch asserts the original bytes before writing.

## Features and where they live
| Option | What | Where |
|---|---|---|
| (always) | Lapis Chest 990000114: 50,000 Lapis for 1 gil, no limit | rulez/global_bundles.json |
| (always) | Super Premium Box 990000113 unlimited | rulez/global_bundles.json |
| (always) | Daily quests and milestone pay `50:1:<lapis>` | rulez/daily_quests.json |
| `prompt=` | Asks before data updates; Elvlin app updates skipped | classes6.dex replaced (built from UpdatePrompt.smali with apktool 3.0.3) |
| `loop=99` | Quest auto-play limit | getLoopLimit 0x19c0398 -> `mov w0,#99; ret` |
| `speed3r` | 3x on Auto, 2.5x on Repeat | Scheduler::update call 0x2ae40cc -> bl cave (speed_cave4.bin); flags BattleState isAutoBattle 0x39f08cc, isAutoRepeatBattle 0x39f0994; Director page 0x3efd000, scheduler at +0xa0; extra logic step via BaseScene::update call 0x1e3a23c |
| `instantsummon` | Summon animation skipped | GachaEffectScene 0x2125780, 0x2125860 |
| `raidautoplay` | Auto-play in raids | ReadyForMissionScene::enableMissionRepeat 0x236f07c: branch at 0x236f0bc to cave vaddr 0x431dfd0 (skips world-id and isRaidMission checks); allow-list mask at 0x236f3c8 0x481 -> 0x485 |
| `searchname` | Unit search fixed | getSearchLibraryItemList 0x19fe4b4 `tbnz` -> `b 0x19fe3ec` (skip LibraryUnitScene::isRegistered, empty offline; this was the real cause); getSearchUnitMstList 0x1a0036c matches name instead of phonetic reading |
| `fp50k` | Friend Points bundle 990000001 gives 50,000 | string "51:1:2000" and inline std::string build at file 0x3b525ac / 0x3b525c0 -> "51:1:50000"; name "2,000 Friend Points" -> "50,000 Friend Point" (same length) |
| `fpdraws=30` | Friend point multi-summon gives 30 units, 6,000 points | rulez/gacha_authored.json banner id 1 type friend, secondary_offer draws and cost |
| `dropx=10` | Enemy item drop quantities x10 | rulez/content/battle/F_MONSTER_PARTS_MST.tsv columns 3frn4ILX, IRf10dwx, 9BetM2Ds, MZn8LC6H (`type:id:qty:chance`). Unit drops (Vf5DGw07) untouched |
| `allchallenges` | All mission challenges count as met on clear | complete_attempt vaddr 0x40f0c38 (file 0x3b7cc38): `cmp w0,#1; b.ne` -> `bl 0x40ff7ac; tbnz w0,#0,skip` (only an evaluator error still skips) |

## Confirmed on the phone
Lapis Chest and daily quests, Super Premium Box, unit search (lapis15), friend summon with 30 units and a scroll bar (lapis17), mission challenges auto-complete (lapis20).
Not explicitly confirmed: raid auto-play button (lapis13), 50,000 Friend Points bundle, x10 drops, update prompt, speed values.

## Open issues
- Once, a 30-unit friend summon charged 6,000 points but gave 10 units, and later the summon showed 2,000/10 again. After reinstalling lapis17 it showed 30 with a scroll bar. Cause unknown; possibly a stale install or a data update replacing the rules. Watch for it.
- Lapis Chest shows as `MST_BUNDLE_NAME_990000114`: bundle names come from a built-in name list that lacks the new id. Cosmetic.
- Summon button image may still say 10 (fixed picture).

## Ideas not built
- **Story challenge template** (Complete the quest / No items / No continues / No ally KO'd): challenge rows come from `F_CHALLENGE_MST.ndjson` in Elvlin's downloaded data, not the APK. Plan: find how the engine loads it (strings at vaddr 0x41cda7a, xrefs 0x3f7754c, 0x4083494), copy the four condition codes from missions that already use them, rewrite story missions' rows keeping IDs and rewards, redirect the load path like `rulez/` and ship the edited copy in the APK, and drop `allchallenges`. Risks: unsupported codes are skipped; rewards stay with their slot; missions with fewer than four rows need new IDs; display text may come from elsewhere.
- Bundle of Riches to 10,000,000 gil and unlimited (rule edit in global_bundles.json).
- Rebuild on Elvlin's 9072 re-upload (needs offset re-verification).

## Saves
- Native engine save: `<files>/exvius/state/campaign.json` (UTF-8 JSON, atomic write via .tmp). The APK has allowBackup=false and debuggable=false, so it can't be pulled without root or an in-app export.
- Fresh-save trick: patch libgame `/campaign.json\0` -> `/campaig2.json\0`.
