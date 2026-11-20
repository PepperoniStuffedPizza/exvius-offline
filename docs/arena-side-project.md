# Side project: custom arena opponents

Status: investigation only, no patch. Goal: choose which opponent teams you fight in arena. Observed in game: every opponent is one unit the player does not own, so the engine builds a stand-in rival.

## Known (libgame.so, v0.1.36)
- Engine segment (3rd LOAD): file = vaddr - 0x3f10000 + 0x399c000. To disassemble: extract the segment, wrap it with llvm-objcopy, link with `ld.lld -Ttext=0x3f10000`, then llvm-objdump.
- Strings: `arena_match_data` 0x4196a21, `Local Arena opponent` 0x4196a3b, `arena_rival_data` 0x419b28b. Code refs: 0x4016588 (function from 0x4015c80) and 0x401fbe4.
- A large function around 0x401e4f0 to 0x4020328 builds JSON-style data with scrambled field names (UE3vKA5y, fP8Nv0KZ, IgS2Mi9Y, Bc43fupe). Readable keys: unit, level, lb_level, e_id, target, rival, name, opponent, summary, matched.
- The opponent is not a copy of the player's party, and no arena file exists in `assets/rules/`.

## To find
1. How the opponent unit is chosen and which master data it reads.
2. Where its unit id, level and equipment are set.
3. Whether a patch can force chosen ids, ideally from a file under `assets/rulez/`.

Start with a fixed opponent unit id, then a list. Assert original bytes in every native patch; use a higher versionCode per build.
