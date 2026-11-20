"""Lapis build of Elvlin's Exvius Offline v0.1.36 (versionCode 9076).

Port of patch031.py. The original game code in libgame.so is byte-identical between v0.1.31 and v0.1.36,
so every game-code patch keeps its address. Elvlin's offline engine segment was rebuilt, so the Friend Points
and mission-challenge patches and the code cave moved. The update prompt now hooks classes8.dex.
"""
import json, os, re, struct, sys, zipfile
src, rules_apk, dst, lapis, new_code = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
SIG = re.compile(r'^META-INF/([^/]+\.(SF|RSA|DSA|EC)|MANIFEST\.MF)$', re.I)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from patch_axml import patch_version_code

BASE_VERSION_CODE = 9076
EXTRA = sys.argv[6:]
NO_UPDATES = 'noupdates' in EXTRA
PROMPT_DEX = next((a[7:] for a in EXTRA if a.startswith('prompt=')), None)
LOOP_LIMIT = next((int(a[5:]) for a in EXTRA if a.startswith('loop=')), None)
INSTANT_SUMMON = 'instantsummon' in EXTRA
RAID_AUTOPLAY = 'raidautoplay' in EXTRA
SEARCH_NAME = 'searchname' in EXTRA
FP50K = 'fp50k' in EXTRA
ALL_CHALLENGES = 'allchallenges' in EXTRA
FF_BUTTON = 'ffbutton' in EXTRA
TMR_ALL = 'tmr' in EXTRA or 'tmrmulti' in EXTRA
TMR_LIMIT = None if 'tmrmulti' in EXTRA else 'once'
KING_POTS = next((int(a[9:]) for a in EXTRA if a.startswith('kingpots=')), None)
DROP_X = next((int(a[6:]) for a in EXTRA if a.startswith('dropx=')), None)
FP_DRAWS = next((int(a[8:]) for a in EXTRA if a.startswith('fpdraws=')), None)
SPEED = 4 if 'speed3r' in EXTRA else 3 if 'speed3' in EXTRA else 2 if 'speed2' in EXTRA else 0
SPEED2 = SPEED > 0

# libgame.so layout (v0.1.36). Game code: file offset == vaddr. Engine segment (3rd LOAD): file = vaddr - ENG_VA + ENG_OFF.
ENG_OFF, ENG_VA, ENG_SIZE = 0x399c000, 0x3f10000, 0x3f0e2c
def eng_file(va): return va - ENG_VA + ENG_OFF
GET_LOOP_LIMIT = 0x19c0398           # MissionRepeatUtil::getLoopLimit() (unchanged from v0.1.31)
CAVE_VA = 0x4300e30                  # zero padding after the engine segment (segment ends at vaddr 0x4300e2c)
CAVE_OFF = eng_file(CAVE_VA)         # 0x3d8ce30
RAID_VA = CAVE_VA + 0xe0             # raid routine, after the speed routines (speed_cave4 is 0xd4 bytes)
CAVE_END = RAID_VA + 0x30
NEXT_LOAD_OFF = 0x3d90000            # next segment's file offset: the cave must stay below it

def bl(pc, tgt): return struct.pack('<I', 0x94000000 | (((tgt - pc) >> 2) & 0x3ffffff))
def B(pc, t): return struct.pack('<I', 0x14000000 | (((t - pc) >> 2) & 0x3ffffff))
def BC0(pc, t, rt): return struct.pack('<I', 0x34000000 | ((((t - pc) >> 2) & 0x7ffff) << 5) | rt)   # cbz w<rt>
def BC(pc, t, cond): return struct.pack('<I', 0x54000000 | ((((t - pc) >> 2) & 0x7ffff) << 5) | cond)

def grow_engine_segment(data, end_va):
    ph = struct.unpack_from('<Q', data, 0x20)[0] + 56 * 3
    off, va, pa, fsz, msz = struct.unpack_from('<QQQQQ', data, ph + 8)
    assert (off, va, pa) == (ENG_OFF, ENG_VA, ENG_VA) and fsz == msz and fsz >= ENG_SIZE, 'unexpected engine segment'
    size = max(fsz, end_va - ENG_VA)
    assert ENG_OFF + size <= NEXT_LOAD_OFF
    struct.pack_into('<QQ', data, ph + 32, size, size)

FF_FLAG_VA = 0x4731940                # 16 new bytes at the end of Elvlin's .bss (4th LOAD); byte 0 = fast-forward flag
FF_VA = CAVE_VA + 0x120               # fast-forward trampolines, after the raid routine
def grow_bss(data):
    ph = struct.unpack_from('<Q', data, 0x20)[0] + 56 * 4
    off, va, pa, fsz, msz = struct.unpack_from('<QQQQQ', data, ph + 8)
    assert (off, va, pa, fsz, msz) == (0x3d90000, 0x4710000, 0x4710000, 0x74, 0x21940), 'unexpected bss segment'
    struct.pack_into('<Q', data, ph + 40, msz + 0x10)

def disable_updates(d):
    import hashlib, zlib
    old = b'https://raw.githubusercontent.com/Elvlin/exvius-offline/main/data/latest.json'
    assert d.count(old) >= 1
    d = bytearray(d.replace(old, old.replace(b'githubusercontent.com', b'githubusercontent.cox')))
    d[12:32] = hashlib.sha1(bytes(d[32:])).digest()
    d[8:12] = struct.pack('<I', zlib.adler32(bytes(d[12:])) & 0xffffffff)
    return bytes(d)

def edit_rule(name, data):
    if name == 'daily_quests.json':
        r = json.loads(data)
        for q in r['quests']: q['reward_info'] = '50:1:%d' % lapis
        r['_meta']['milestone_reward'] = '50:1:%d' % lapis
        return json.dumps(r, ensure_ascii=False, indent=1).encode()
    if name == 'global_bundles.json':
        r = json.loads(data)
        assert not any(b['id'] == '990000114' for b in r['bundles'])
        for b in r['bundles']:
            if b['id'] == '990000113':
                b['limit'] = None
                if KING_POTS:
                    KP = {'10:%s:1' % i for i in (900000301, 900001301, 900002301, 900003301, 900004301, 900005301)}
                    assert sum(c in KP for c in b['contents']) == 6, 'king pots not found in Super Premium Box'
                    b['contents'] = [c[:-1] + str(KING_POTS) if c in KP else c for c in b['contents']]
                    log.append('rules: Super Premium Box King Pots (Tough/Magi/Power/Shield/Smart/Soul) x%d each' % KING_POTS)
        r['bundles'].append({'id': '990000114', 'name': 'Lapis Chest (%s Lapis)' % format(lapis, ','),
                             'icon': '3197_20230905013503.png', 'gil': 1, 'limit': None, 'contents': ['50:1:%d' % lapis]})
        if TMR_ALL:
            T = json.load(open(os.path.join(HERE, 'tmr_rewards.json')))
            parts = [('1-3', T['1'] + T['2'] + T['3']), ('4', T['4']), ('5 (1/2)', T['5'][:195]), ('5 (2/2)', T['5'][195:])]
            allc = [x for _, c in parts for x in c]
            assert len(allc) == 783 and len(set(allc)) == 783, 'duplicate TMRs'
            for n, (lab, c) in enumerate(parts):
                bid = str(990000115 + n)
                assert not any(b['id'] == bid for b in r['bundles'])
                r['bundles'].append({'id': bid, 'name': 'All TMR %s star (%d)' % (lab, len(c)), 'icon': '3197_20230905013503.png',
                                     'gil': 1, 'limit': TMR_LIMIT, 'contents': list(c)})
            log.append('rules: 4 TMR bundles 990000115-118 (783 TMRs from 1-6 star units, 1 gil, %s)' % ('repeatable' if TMR_LIMIT is None else 'once'))
        return json.dumps(r, ensure_ascii=False, indent=1).encode()
    if name == 'gacha_authored.json' and FP_DRAWS:
        r = json.loads(data)
        b = [x for x in r['banners'] if x['id'] == '1' and x.get('type') == 'friend']
        assert len(b) == 1 and b[0]['secondary_offer']['draws'] == 10 and b[0]['cost']['amount'] == 200
        b[0]['secondary_offer']['draws'] = FP_DRAWS
        b[0]['secondary_offer']['cost']['amount'] = 200 * FP_DRAWS
        log.append('rules: friend point multi-summon -> %d units for %d points' % (FP_DRAWS, 200 * FP_DRAWS))
        return json.dumps(r, ensure_ascii=False, indent=1).encode()
    if name.endswith('F_MONSTER_PARTS_MST.tsv') and DROP_X:
        lines = data.decode('utf8').split('\n')
        fields = json.loads(lines[0][2:])['fields']
        cols = [fields.index(f) for f in ('3frn4ILX', 'IRf10dwx', '9BetM2Ds', 'MZn8LC6H')]
        pat = re.compile(r'^(\d+:\d+:)(\d+)(:\d+\s*)$')
        changed = 0
        for li in range(1, len(lines)):
            if not lines[li]: continue
            r = lines[li].split('\t')
            for c in cols:
                if not r[c]: continue
                parts = r[c].split(',')
                for k, x in enumerate(parts):
                    m = pat.match(x)
                    assert m, (li, c, x)
                    parts[k] = m.group(1) + str(int(m.group(2)) * DROP_X) + m.group(3); changed += 1
                r[c] = ','.join(parts)
            lines[li] = '\t'.join(r)
        log.append('rules: enemy item drop quantities x%d (%d entries)' % (DROP_X, changed))
        return '\n'.join(lines).encode('utf8')
    return data

def patch_libgame(data):
    data = bytearray(data)
    hdr = struct.unpack_from('<Q', data, 0x20)[0] + 56 * 3
    assert struct.unpack_from('<QQQQ', data, hdr + 8) == (ENG_OFF, ENG_VA, ENG_VA, ENG_SIZE), 'not the v0.1.36 (9076) libgame.so'
    assert data.count(b'\x00rules/\x00') == 1
    i = data.index(b'\x00rules/\x00'); data[i:i+8] = b'\x00rulez/\x00'; log.append('libgame: rules/ -> rulez/')
    if LOOP_LIMIT:
        assert data[GET_LOOP_LIMIT:GET_LOOP_LIMIT+4] == bytes.fromhex('fd7bbfa9'), 'unexpected getLoopLimit prologue'
        data[GET_LOOP_LIMIT:GET_LOOP_LIMIT+8] = struct.pack('<II', 0x52800000 | (LOOP_LIMIT << 5), 0xd65f03c0)  # mov w0,#N ; ret
        log.append('libgame: quest auto-play limit -> %d' % LOOP_LIMIT)
    if SEARCH_NAME:
        # GameUtils::getSearchUnitMstList matches only the (empty) phonetic reading: copy the name string into that slot.
        S = 0x1a0036c
        assert data[S:S+12] == bytes.fromhex('e8030491e00317aa5b52e597'), 'unexpected search code'
        ctor = 0x1a00368 + 4 * (((0x97e47036 & 0x3ffffff) ^ 0x2000000) - 0x2000000)
        data[S:S+12] = struct.pack('<II', 0x910403e0, 0x910463e1) + bl(0x1a00374, ctor)
        # getSearchLibraryItemList keeps only library-registered units (none offline): tbnz w0,#0,ADD -> b ADD.
        R = 0x19fe4b4
        assert data[R:R+4] == bytes.fromhex('c0f90737'), 'unexpected isRegistered branch'
        data[R:R+4] = B(R, 0x19fe3ec)
        log.append('libgame: unit search matches name, ignores library registration')
    if FP50K:
        # Built-in bundle 990000001 "2,000 Friend Points": reward "51:1:2000" is built inline as a short std::string
        # (len byte 18, 8 bytes from rodata, then "0\0" via sturh). Make it "51:1:50000" (len 20, "00\0\0" via stur).
        assert data.count(b'\x0051:1:2000\x00') == 1
        i = data.index(b'\x0051:1:2000\x00'); data[i:i+11] = b'\x0051:1:5000\x00'
        L, M, S = eng_file(0x3fb8f10), eng_file(0x3fb8f28), eng_file(0x3fb8f38)   # engine offsets 0xa8f10/28/38
        assert data[L:L+4] == bytes.fromhex('48028052') and data[M:M+4] == bytes.fromhex('08068052') \
            and data[S:S+4] == bytes.fromhex('28130978'), 'unexpected Friend Points code'
        data[L:L+4] = struct.pack('<I', 0x52800288)   # mov w8,#20
        data[M:M+4] = struct.pack('<I', 0x52860608)   # mov w8,#0x3030
        data[S:S+4] = struct.pack('<I', 0xb8091328)   # stur w8,[x25,#0x91]
        assert data.count(b'2,000 Friend Points\x00') == 2
        data = bytearray(bytes(data).replace(b'2,000 Friend Points\x00', b'50,000 Friend Point\x00'))
        log.append('libgame: Friend Points bundle gives 50,000')
    if ALL_CHALLENGES:
        # Mission-challenge reward loop (engine offset 0x1c9da8): after evaluating each condition it does
        # cmp w20,#1 ; b.ne SKIP. Replace with: bl raised_check ; tbnz w0,#0,SKIP -> every condition counts as met
        # unless the evaluator raised an error. raised_check (engine 0xb5aec) = v0.1.31's 0x1ef7ac.
        CV, SKIP, RAISED = 0x40d9da8, 0x40da4a8, 0x3fc5aec
        C = eng_file(CV)
        assert data[C:C+8] == struct.pack('<I', 0x7100069f) + BC(CV + 4, SKIP, 0x1), 'unexpected challenge code'
        assert data[eng_file(RAISED):eng_file(RAISED)+20] == bytes.fromhex('483b00f0082541f91f0100f1e0079f1ac0035fd6'), 'unexpected raised_check'
        imm14 = (SKIP - (CV + 4)) >> 2
        data[C:C+8] = bl(CV, RAISED) + struct.pack('<I', 0x37000000 | ((imm14 & 0x3fff) << 5))
        log.append('libgame: mission challenges all count as met on clear')
    if INSTANT_SUMMON:
        assert data[0x2125780:0x2125788] == bytes.fromhex('681e583928020034')
        data[0x2125780:0x2125788] = bytes.fromhex('68125839') + struct.pack('<I', 0x35000000 | (((0x212576c - 0x2125784) >> 2 & 0x7ffff) << 5) | 8)
        assert data[0x2125860:0x2125864] == bytes.fromhex('c9000054')
        data[0x2125860:0x2125864] = B(0x2125860, 0x2125878)
        log.append('libgame: summon animation skipped')
    if SPEED2 or RAID_AUTOPLAY:
        assert set(data[CAVE_OFF:eng_file(CAVE_END)]) == {0}, 'cave not empty'
    if SPEED2:
        cave = bytearray(open(os.path.join(HERE, 'speed_cave%d.bin' % SPEED), 'rb').read())
        assert CAVE_VA + len(cave) <= RAID_VA
        c2 = {2: 0x60, 3: 0x70, 4: 0xa0}[SPEED]
        flag_page = 0x39f08cc & ~0xfff        # BattleState flags (game .bss, unchanged)
        def adrp(pc, rd, page=flag_page):
            imm = (page - (pc & ~0xfff)) >> 12
            return struct.pack('<I', 0x90000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7ffff) << 5) | rd)
        cave[0x14:0x18] = adrp(CAVE_VA + 0x14, 9)
        cave[c2:c2+4] = adrp(CAVE_VA + c2, 16)
        if SPEED == 4:
            cave[0x30:0x34] = adrp(CAVE_VA + 0x30, 9, 0x3efd000)   # Director singleton page
        data[CAVE_OFF:CAVE_OFF + len(cave)] = cave
        if FF_BUTTON:
            assert SPEED == 4
            fp = FF_FLAG_VA & ~0xfff; fo = FF_FLAG_VA & 0xfff
            ldrb = lambda rt, rn, imm: struct.pack('<I', 0x39400000 | (imm << 10) | (rn << 5) | rt)
            # Auto/Repeat no longer speed anything up: only the button's flag does (3x). ff1 replaces the Auto-flag load; ff2 replaces the time scale choice.
            ff1 = adrp(FF_VA, 11, fp) + ldrb(10, 11, fo) + BC0(FF_VA + 8, CAVE_VA + 0x88, 10) + B(FF_VA + 0xc, CAVE_VA + 0x1c)
            ff2 = adrp(FF_VA + 0x20, 17, fp) + ldrb(17, 17, fo) + struct.pack('<I', 0x1e211001) + struct.pack('<I', 0x35000000 | (2 << 5) | 17) \
                + struct.pack('<I', 0x1e2e1001) + B(FF_VA + 0x34, CAVE_VA + 0xd0)
            assert data[CAVE_OFF + 0x18:CAVE_OFF + 0x1c] == bytes.fromhex('2a316339'), 'unexpected speed cave (auto load 1)'
            assert data[CAVE_OFF + 0xa4:CAVE_OFF + 0xa8] == bytes.fromhex('11326339'), 'unexpected speed cave (auto load 2)'
            assert set(data[eng_file(FF_VA):eng_file(FF_VA) + 0x40]) == {0}, 'ff cave not empty'
            data[eng_file(FF_VA):eng_file(FF_VA) + len(ff1)] = ff1
            data[eng_file(FF_VA + 0x20):eng_file(FF_VA + 0x20) + len(ff2)] = ff2
            data[CAVE_OFF + 0x18:CAVE_OFF + 0x1c] = B(CAVE_VA + 0x18, FF_VA)
            data[CAVE_OFF + 0xa4:CAVE_OFF + 0xa8] = B(CAVE_VA + 0xa4, FF_VA + 0x20)
            # battle detection: dynamic_cast<BattleBaseScene*>(this) != null -> bump the counter at flag+2 (Java shows the button while it moves)
            # battle detection (dynamic_cast<BattleBaseScene*>(this) != null -> bump the counter at flag+2; Java shows the buttons while it moves)
            # + finish request (flag+4): put every living enemy into the game's own dying state (0xd) after zeroing its HP, so the
            # normal death/drop/win flow runs. Assembled from f3.s (kept in the kit) at F3 = 0x4300f90, returns to cave+0x18.
            F3 = FF_VA + 0x40
            assert FF_VA == 0x4300f50 and F3 == 0x4300f90 and CAVE_VA == 0x4300e30, 'finish routine is position dependent'
            ff3 = bytes.fromhex('e00313aa019effb021c00991e29fffb042a004910300809218e5aa97400700b4812100b02208653942040011220825392310653983060034e00313aa019effb021c00991a2a0ffd042e00891030080920ae5aa97e00000b408e445b91f0501718100005493c34097e8ff8f5208c000b9812100902414653984000034840400512414253920000014440b805224142539f55bbea987c34097ee554197200300b44fa85f97e00200b4081840f9150140f9160940f9bf0600f14b020054c08640f8b50600d180ffffb4f40300aa081043b91f35007100ffff541f390071c0feff54e00314aae1031faa27106397e00314aaa1018052e2031f2a10386297eeffff17f55bc2a869b7fff06cffff17')
            assert len(ff3) == 268
            assert data[CAVE_OFF + 0x14:CAVE_OFF + 0x18] == adrp(CAVE_VA + 0x14, 9), 'unexpected adrp in speed cave'
            assert set(data[eng_file(F3):eng_file(F3) + 0x120]) == {0}
            data[eng_file(F3):eng_file(F3) + len(ff3)] = ff3
            data[CAVE_OFF + 0x14:CAVE_OFF + 0x18] = B(CAVE_VA + 0x14, F3)
            grow_bss(data)
            log.append('libgame: Auto/Repeat speed-up removed; speed 3x only while the FF button flag is set')
        call = 0x1e3a23c   # BaseScene::update
        assert data[call:call+4] == bytes.fromhex('00013fd6'); data[call:call+4] = bl(call, CAVE_VA)
        ts = 0x2ae40cc     # Scheduler::update time scale
        assert data[ts:ts+4] == bytes.fromhex('012440bd'); data[ts:ts+4] = bl(ts, CAVE_VA + c2)
        grow_engine_segment(data, FF_VA + 0x14c if FF_BUTTON else CAVE_VA + len(cave))
        log.append('libgame: game speed 3x on Auto, 2.5x on Repeat' if SPEED == 4 else 'libgame: %dx game speed while battle Auto is on' % SPEED)
    if RAID_AUTOPLAY:
        RC, ROFF = RAID_VA, eng_file(RAID_VA)
        FAIL, NORMAL, RAID = 0x236f120, 0x236f0d4, 0x236f0dc
        assert data[0x236f0bc:0x236f0d4] == bytes.fromhex('082c40b91f090071e102005408f040391f09007180020054')
        code = bytes.fromhex('084040b9') + bytes.fromhex('1f090071') + BC(RC+0x08, RC+0x28, 0x0) \
             + bytes.fromhex('082c40b9') + bytes.fromhex('1f090071') + BC(RC+0x14, RC+0x2c, 0x1) \
             + bytes.fromhex('08f04039') + bytes.fromhex('1f090071') + BC(RC+0x20, RC+0x2c, 0x0) \
             + B(RC+0x24, NORMAL) + B(RC+0x28, RAID) + B(RC+0x2c, FAIL)
        assert RC + len(code) <= CAVE_END
        data[ROFF:ROFF + len(code)] = code
        data[0x236f0bc:0x236f0c0] = B(0x236f0bc, RC)
        grow_engine_segment(data, CAVE_END)
        assert data[0x236f3c8:0x236f3cc] == bytes.fromhex('29908052')
        data[0x236f3c8:0x236f3cc] = struct.pack('<I', 0x52800000 | (0x485 << 5) | 9)
        log.append('libgame: quest auto-play allowed in raids')
    return bytes(data)

zin, zr = zipfile.ZipFile(src), zipfile.ZipFile(rules_apk)
assert not any(n.startswith('assets/rulez/') for n in zin.namelist())
log = []
with zipfile.ZipFile(dst, 'w') as zout:
    for info in zin.infolist():
        if SIG.match(info.filename): continue
        data = zin.read(info.filename)
        if info.filename == 'lib/arm64-v8a/libgame.so':
            data = patch_libgame(data)
        elif info.filename == 'classes8.dex' and PROMPT_DEX:
            assert b'Lcom/exvius/local/DataUpdates;' in data
            data = open(PROMPT_DEX, 'rb').read(); log.append('classes8.dex: data updates ask first, Elvlin app updates skipped')
        elif info.filename == 'classes8.dex' and NO_UPDATES:
            data = disable_updates(data); log.append('classes8.dex: update check URL -> unreachable host (.cox)')
        elif info.filename == 'AndroidManifest.xml':
            data = patch_version_code(data, BASE_VERSION_CODE, new_code); log.append('versionCode %d -> %d' % (BASE_VERSION_CODE, new_code))
        out = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        out.compress_type, out.external_attr = info.compress_type, info.external_attr
        zout.writestr(out, data)
    n = 0
    for info in zr.infolist():
        if not info.filename.startswith('assets/rules/') or info.is_dir(): continue
        rel = info.filename[len('assets/rules/'):]
        data = edit_rule(rel, zr.read(info.filename))
        out = zipfile.ZipInfo('assets/rulez/' + rel, date_time=info.date_time)
        out.compress_type = info.compress_type if info.filename.lower().endswith('.png') else zipfile.ZIP_DEFLATED
        zout.writestr(out, data); n += 1
    log.append('added %d rule files under assets/rulez/ (daily quests %d Lapis, + Lapis Chest, Super Premium Box unlimited)' % (n, lapis))
print('\n'.join(log))
