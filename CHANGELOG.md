# Lapis builds: change log

Unofficial patched builds of Elvlin's Exvius Offline (https://github.com/Elvlin/exvius-offline). Elvlin allows modification and redistribution. All changes are binary patches to his finished APK plus edited rule files; the engine source is not public. Each native patch asserts the original bytes, so a wrong base fails instead of producing a broken build. Versions marked "not tested" were built but not confirmed on a phone.

## v0.1.36-lapis54 (versionCode 9140) - latest
- New shop bundle "Super Trust Moogle x10": 10 Super Trust Moogles (ALL 100%) for 1 gil, buy as often as you like.

## v0.1.36-lapis53 (versionCode 9139)
- Lapis Chest bundle gives 500,000 Lapis (was 50,000). Daily quest rewards unchanged.

## v0.1.36-lapis52 (versionCode 9138)
- New-unit reveal now checks every rarity form: owning a unit's 6 star or NV form (in your box or reserves) stops its 5 star copy counting as new. Units used in fusion or sold leave no record, so they still count as new.

## v0.1.36-lapis51 (versionCode 9137)
- New-unit reveal in multi-summons: units you did not own before now get the full "Obtained" screen and the NEW badge on the results grid. Elvlin's engine never sends the game's "new unit ids" field, so this was missing in every earlier build (only NeoVision units and single summons showed it). The game now decides on its own: new = first copy in this summon and you owned none before. Confirmed working.
- Everything from lapis47, with the 7x summon speed restored.

## v0.1.36-lapis48 to lapis50 (9134-9136, diagnostic)
- Tried to fix the missing reveal by reducing (lapis48), removing (lapis49) and fully disabling (lapis50) the summon speed-up. None helped; the speed-up was not the cause (see lapis51).

## v0.1.36-lapis44 to lapis47 (9130-9133): Bulk Fusion 5 star and NV base
- lapis44: 5 star Base button added (button appeared but found nothing).
- lapis45: lifted the game's hidden "4 star max" filter so 5 star bases are found. Confirmed working.
- lapis46: 6th button (blank picture: the game has no "6 star base" image).
- lapis47: the 6th button is the game's own "NV base" filter (units whose family starts at NV), with its own picture; the "Units to Select" row moves down to make room.

## v0.1.36-lapis43 (9129): 15-unit multi-summons
- Every 11-unit multi-summon (buttons, step-ups, campaigns) gives 15 units at the same cost; the Friend Point multi gives 15. The button art still says 11.

## v0.1.36-lapis39 to lapis42 (9125-9128): summon speed
- `instantsummon` removed (it cut the single-summon reveal short).
- lapis41: summon animation runs at 7x. lapis42: the "Units Obtained" crystal screen runs at 7x too. Battle Speed button unchanged (3x).

## v0.1.36-lapis38 (versionCode 9124)
- Same contents as lapis35, rebuilt with a higher version code so it installs over lapis37 and keeps saves.
- Known limit: the Finish button still goes through each wave (see lapis30 to lapis35 below).

## v0.1.36-lapis37 (9123)
- Same contents as lapis32, rebuilt with a higher version code so it installs over lapis33 to lapis35.

## v0.1.36-lapis36 (9122, diagnostic, never released)
- Finish button shows wave flag, scene state and wave phase while running. Dropped before release.

## v0.1.36-lapis30 to lapis35: Finish button
- New "Finish" button next to the Speed button, shown only in battles. Tap it, then tap "Sure?" within 3 seconds.
- lapis30: completed the battle by forcing the result. Crashed in multi-wave battles (stale lock-target pointers). Fixed by killing enemies instead.
- lapis31: crashed when the enemy party was missing. lapis32 adds null checks and kills every enemy about every 1.5 seconds until the battle is idle (sticky finish mode). Safe, but you still go through each wave.
- lapis33 to lapis35: tried to make the game treat the last wave as already reached (set the wave phase at the wave-clear state; lapis34 compared the wrong state, lapis35 fixed it). Still goes through each wave in story/event quests. Cause not found.

## v0.1.36-lapis25 to lapis29: Speed button
- In-game Speed (FF) button below the Auto button, shown only in battles; labels "Speed: X1" / "Speed x3"; setting persists across battles.
- Native Auto/Repeat speed-up reverted; speed now only applies while the button flag is set.
- Native code cave and flags in libgame's engine segment; Java side is the `com.exvius.local.FastForward` class in classes8.dex.

## v0.1.36-lapis21 to lapis24: port to Elvlin's v0.1.36
- Rebuilt on v0.1.36 (versionCode 9076) and data revision 13 (1,285 rule files, copied under `assets/rulez/`).
- Super Premium Box gives 50 of each King Pot (`kingpots=50`).
- TMR bundles purchasable repeatedly, no duplicates (`tmrmulti`, data in `tmr_rewards.json`).
- Update prompt moved to classes8.dex (asks before data updates; first-time setup downloads without asking).
- Friend Points 50k, all-challenges and raid auto-play addresses re-found for the rebuilt engine segment.

## v0.1.31-lapis to lapis20 (base v0.1.31, versionCode 9071)
- Lapis Chest bundle (990000114): 50,000 Lapis for 1 gil, no purchase limit; Super Premium Box (990000113) unlimited.
- Daily quests and milestones pay Lapis.
- Update prompt (`prompt=`): asks before data updates; Elvlin app updates skipped.
- `loop=99`: quest auto-play limit raised to 99.
- `speed3r`: 3x on Auto, 2.5x on Repeat (later replaced by the Speed button).
- `instantsummon`: summon animation skipped.
- `raidautoplay`: auto-play button in raids.
- `searchname`: unit search fixed (offline library registration check skipped; search matches names).
- `fp50k`: Friend Points bundle gives 50,000.
- `fpdraws=30`: friend point multi-summon gives 30 units for 6,000 points.
- `dropx=10`: enemy item drops x10 (unit drops unchanged).
- `allchallenges`: all mission challenges count as met on clear.
- Rule files redirected to `assets/rulez/` so edits override the downloaded data pack.
- lapis2: unit search fix attempt; lapis15: unit search fixed; lapis17: 30-unit friend summon confirmed; lapis20: challenge auto-complete confirmed.

## v0.1.30-lapis to lapis15 (base v0.1.30)
- First lapis builds (Lapis Chest, daily quest payouts, loop limit, speed-up). v0.1.30-lapis2 was broken; lapis3 fixed it. Individual builds before v0.1.31 are not itemised here.

## Not built / open
- Arena opponent teams: opponents are generated by the engine (one unit you may not own). See `docs/arena-side-project.md`.
- Story challenge template, Bundle of Riches 10,000,000 gil, rebuild on Elvlin's 9072 re-upload: see `docs/lapis-notes.md`.
- Lapis Chest name shows as `MST_BUNDLE_NAME_990000114` (cosmetic).

## lapis55
- All multi-summons are 30 units (`multidraws=30`), and the lapis, ticket and friend-point prices are scaled to match (`multiprice`, 5000 -> 15000; friend points 6000). versionCode 9141.

## lapis58
- Multi-summons are 15 units (the result screen grid is 5x3; counts above 15 fell back to 11 in tests of 20 and 30) with prices scaled x1.5 (`multiprice`, 5000 -> 7500; friend points 3000). versionCode 9144.

## lapis59
- Fix: the 0.1.36 engine reads summons from `rules/summon/index.json` and `rules/summon/full/<id>.json`; the `gacha_*.json` files are legacy and unread, so `multidraws`/`fpdraws` never took effect in lapis43-58 (summons stayed 11, friend 10). The edits now apply to the summon files. 30-unit multi-summons, prices x3 (5000 -> 15000), friend multi 30 for 6000. versionCode 9145. Untested on phone.

## v0.1.90-lapis60 (9146): rebased on Elvlin beta v0.1.90 (data r34)
- Fixes the crash opening Awaken for 5-star units (Elvlin beta fix), adds the beta's other fixes and 5-star Select Summon.
- All lapis features carried over; game data frozen at r34. Untested on phone.
