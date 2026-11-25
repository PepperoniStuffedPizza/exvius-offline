"""Lapis build of Elvlin's Exvius Offline v0.1.36 (versionCode 9076).

Port of patch031.py. The original game code in libgame.so is byte-identical between v0.1.31 and v0.1.36,
so every game-code patch keeps its address. Elvlin's offline engine segment was rebuilt, so the Friend Points
and mission-challenge patches and the code cave moved. The update prompt now hooks classes8.dex.
"""
import os, json, os, re, struct, sys, zipfile
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
FUSION6 = 'fusion6' in EXTRA
GACHA8 = 'gacha8' in EXTRA
NEWUNIT = 'newunit' in EXTRA
STMR = next((int(a[5:]) for a in EXTRA if a.startswith('stmr=')), None)
CRYSTS = next((int(a[7:]) for a in EXTRA if a.startswith('crysts=')), None)
CHEST = next((int(a[6:]) for a in EXTRA if a.startswith('chest=')), None)
FUSION5 = 'fusion5' in EXTRA or FUSION6
TMR_ALL = 'tmr' in EXTRA or 'tmrmulti' in EXTRA
TMR_LIMIT = None if 'tmrmulti' in EXTRA else 'once'
KING_POTS = next((int(a[9:]) for a in EXTRA if a.startswith('kingpots=')), None)
DROP_X = next((int(a[6:]) for a in EXTRA if a.startswith('dropx=')), None)
MULTI_DRAWS = next((int(a[11:]) for a in EXTRA if a.startswith('multidraws=')), None)
MULTI_PRICE = 'multiprice' in EXTRA
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
    if MULTI_DRAWS and (name.startswith('gacha_') or name.startswith('summon/')) and name.endswith('.json'):
        # every 11-draw multi-summon (button offers, step-up steps, campaigns) -> MULTI_DRAWS units; costs unchanged
        txt = data.decode('utf8')
        if MULTI_PRICE:
            # 10+1 summons are priced for 10 pulls: scale the amount to MULTI_DRAWS/10 x (e.g. 5000 -> 15000 for 30)
            txt, k = re.subn(r'("cost":\s*\{[^{}]*?"amount":\s*)(\d+)(\s*\}\s*,\s*"draws":\s*)11\b',
                             lambda m: m.group(1) + str(int(m.group(2)) * MULTI_DRAWS // 10) + m.group(3) + '11', txt)
            if k and not name.startswith('summon/full/'): log.append('rules: %s: %d eleven-draw prices scaled x%d/10' % (name, k, MULTI_DRAWS))
        txt, n = re.subn(r'("draws":\s*)11\b', lambda m: m.group(1) + str(MULTI_DRAWS), txt)
        if n:
            data = txt.encode('utf8')
            if not name.startswith('summon/full/'): log.append('rules: %s: %d eleven-draw summons -> %d units' % (name, n, MULTI_DRAWS))
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
        r['bundles'].append({'id': '990000114', 'name': 'Lapis Chest (%s Lapis)' % format(CHEST or lapis, ','),
                             'icon': '3197_20230905013503.png', 'gil': 1, 'limit': None, 'contents': ['50:1:%d' % (CHEST or lapis)]})
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
        if STMR:
            # Super Trust Moogle (ALL 100%) is unit 906000105 (raid_archive.json's own reward)
            assert not any(b['id'] == '990000119' for b in r['bundles'])
            r['bundles'].append({'id': '990000119', 'name': 'Super Trust Moogle x%d' % STMR, 'icon': '3197_20230905013503.png',
                                 'gil': 1, 'limit': None, 'contents': ['10:906000105:%d' % STMR]})
            log.append('rules: bundle 990000119 Super Trust Moogle x%d (1 gil, repeatable)' % STMR)
        if CRYSTS:
            ids = set(b['id'] for b in r['bundles'])
            groups = [('Crysts (8 elements)', range(201000100, 201000900, 100)),
                      ('Megacrysts (8 elements)', range(201000900, 201001700, 100)),
                      ('Esper, Sacred, Holy and Divine Crystals', range(290050200, 290050600, 100))]
            # ability awakening crysts: 5 tiers (Alcryst, Milcryst, Heavicryst, Giancryst, Purecryst) per family
            for fam, base in (('White', 100), ('Black', 600), ('Green', 1100), ('Power', 2600), ('Guard', 3100),
                              ('Healing', 3600), ('Support', 4100), ('Tech', 4600)):
                groups.append(('%s Alcryst to Purecryst' % fam, range(270000000 + base, 270000000 + base + 500, 100)))
            for k, (lab, rg) in enumerate(groups):
                bid = str(990000300 + k); assert bid not in ids
                r['bundles'].append({'id': bid, 'name': '%s x%d' % (lab, CRYSTS), 'icon': '3197_20230905013503.png',
                                     'gil': 1, 'limit': None, 'contents': ['20:%d:%d' % (i, CRYSTS) for i in rg]})
            log.append('rules: %d cryst bundles from 990000300 (x%d each, 1 gil, repeatable)' % (len(groups), CRYSTS))
        return json.dumps(r, ensure_ascii=False, indent=1).encode()
    if FP_DRAWS and name in ('summon/index.json', 'summon/full/1.json'):
        # 0.1.36 reads summons from summon/ (gacha_*.json are legacy and unread); friend multi = 10 for 2000
        r = json.loads(data)
        bs = [x for x in r['banners'] if x['id'] == '1'] if 'banners' in r else [r]
        assert len(bs) == 1 and bs[0]['type'] == 'friend'
        so = bs[0]['secondary_offer']; assert so['draws'] == 10 and so['cost']['amount'] == 2000
        so['draws'] = FP_DRAWS; so['cost']['amount'] = 200 * FP_DRAWS
        log.append('rules: %s friend multi-summon -> %d units for %d points' % (name, FP_DRAWS, 200 * FP_DRAWS))
        data = json.dumps(r, ensure_ascii=False, separators=(',', ':') if name != 'summon/index.json' else None, indent=None if name != 'summon/index.json' else 1).encode()
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
        fields = json.loads(lines[0][1:])['fields']
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
            # flag 0 = normal, 1 = battle button (3x), 7 = summon scene (7x: time scale 7 and 6 extra logic steps)
            w = lambda v: struct.pack('<I', v)
            ff1 = adrp(FF_VA, 11, fp) + ldrb(10, 11, fo) + BC0(FF_VA + 8, CAVE_VA + 0x88, 10) + w(0x52800054) + w(0x528000cc) + w(0x71001d5f) + w(0x1a940194) + B(FF_VA + 0x1c, CAVE_VA + 0x20)
            if GACHA8:
                # flag 8 (summon animation scene): time scale 7x but no extra logic steps; flag 7 (result screen): both
                ff1 = adrp(FF_VA, 11, fp) + ldrb(10, 11, fo) + BC0(FF_VA + 8, CAVE_VA + 0x88, 10) + w(0x7100215f) + BC(FF_VA + 0x10, CAVE_VA + 0x88, 0) \
                    + w(0x52800054) + w(0x528000cc) + w(0x71001d5f) + w(0x1a940194) + B(FF_VA + 0x24, CAVE_VA + 0x20)
            FF2 = FF_VA + 0x1c0
            ff2 = adrp(FF2, 17, fp) + ldrb(17, 17, fo) + w(0x1e2e1001) + BC0(FF2 + 0xc, FF2 + 0x20, 17) + w(0x1e211001) + w(0x71001e3f) \
                + BC(FF2 + 0x18, FF2 + 0x20, 1) + w(0x1e239001) + w(0xd65f03c0)
            if GACHA8:
                ff2 = ff2[:0x18] + BC(FF2 + 0x18, FF2 + 0x20, 3) + ff2[0x1c:]     # b.lo: scale 7x for flag >= 7
            assert data[CAVE_OFF + 0x18:CAVE_OFF + 0x1c] == bytes.fromhex('2a316339'), 'unexpected speed cave (auto load 1)'
            assert data[CAVE_OFF + 0xa4:CAVE_OFF + 0xa8] == bytes.fromhex('11326339'), 'unexpected speed cave (auto load 2)'
            assert set(data[eng_file(FF_VA):eng_file(FF_VA) + 0x40]) == {0}, 'ff cave not empty'
            assert set(data[eng_file(FF2):eng_file(FF2) + 0x24]) == {0}, 'ff2 cave not empty'
            data[eng_file(FF_VA):eng_file(FF_VA) + len(ff1)] = ff1
            data[eng_file(FF2):eng_file(FF2) + len(ff2)] = ff2
            data[CAVE_OFF + 0x18:CAVE_OFF + 0x1c] = B(CAVE_VA + 0x18, FF_VA)
            data[CAVE_OFF + 0xa4:CAVE_OFF + 0xa8] = B(CAVE_VA + 0xa4, FF2)
            # battle detection: dynamic_cast<BattleBaseScene*>(this) != null -> bump the counter at flag+2 (Java shows the button while it moves)
            # battle detection (dynamic_cast<BattleBaseScene*>(this) != null -> bump the counter at flag+2; Java shows the buttons while it moves)
            # + finish request (flag+4): put every living enemy into the game's own dying state (0xd) after zeroing its HP, so the
            # normal death/drop/win flow runs. Assembled from f3.s (kept in the kit) at F3 = 0x4300f90, returns to cave+0x18.
            F3 = FF_VA + 0x40
            assert FF_VA == 0x4300f50 and F3 == 0x4300f90 and CAVE_VA == 0x4300e30, 'finish routine is position dependent'
            ff3 = bytes.fromhex('e00313aa019effb021c00991e29fffb042a004910300809218e5aa97800700b4812100b02208653942040011220825392310653983060034e00313aa019effb021c00991a2a0ffd042e00891030080920ae5aa97e00000b408e445b91f0501718100005493c34097e8ff8f5208c000b9812100902414653984000034840400512414253920000014440b805224142539f55bbea987c34097ee554197200300b44fa85f97e00200b4081840f9150140f9160940f9bf0600f14b020054c08640f8b50600d180ffffb4f40300aa081043b91f35007100ffff541f390071c0feff54e00314aae1031faa27106397e00314aaa1018052e2031f2a10386297eeffff17f55bc2a869b7fff06cffff17e00313aa019eff9021c0099102a3fff042200f9103008092d5e4aa97800100b5e00313aa019eff9021c0099182a3ffb042e0079103008092cde4aa97800000b5812100903f002539ecffff1781210090e200805222002539e8ffff17')
            if GACHA8: ff3 = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'f3_lapis47.bin'), 'rb').read()
            assert len(ff3) == (376 if GACHA8 else 360)
            assert data[CAVE_OFF + 0x14:CAVE_OFF + 0x18] == adrp(CAVE_VA + 0x14, 9), 'unexpected adrp in speed cave'
            assert set(data[eng_file(F3):eng_file(F3) + 0x180]) == {0}
            data[eng_file(F3):eng_file(F3) + len(ff3)] = ff3
            data[CAVE_OFF + 0x14:CAVE_OFF + 0x18] = B(CAVE_VA + 0x14, F3)
            grow_bss(data)
            log.append('libgame: Auto/Repeat speed-up removed; speed 3x only while the FF button flag is set')
        call = 0x1e3a23c   # BaseScene::update
        assert data[call:call+4] == bytes.fromhex('00013fd6'); data[call:call+4] = bl(call, CAVE_VA)
        ts = 0x2ae40cc     # Scheduler::update time scale
        assert data[ts:ts+4] == bytes.fromhex('012440bd'); data[ts:ts+4] = bl(ts, CAVE_VA + c2)
        grow_engine_segment(data, FF_VA + 0x1e4 if FF_BUTTON else CAVE_VA + len(cave))
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
    if FUSION5:
        # Bulk Fusion (UnitMixAutoSelectScene::setLayoutFilterStartRare) builds its base-rarity button list as {1,2,4,8}.
        # Jump out before the "8" push, push 8, 16 (5 star) and, with fusion6, 32 (6 star), then rejoin.
        # Layout wraps at 5 buttons per row, so a 6th wraps to a second row: setLayoutFilterRange (the "Units to Select"
        # section) is called through a stub that moves its three layout entries down one row (104) and back afterwards.
        TOP = 5
        FV = 0x4301200; FO = eng_file(FV)
        PB = 0x1309480; HOOK = 0x26b414c; BACK = 0x26b4174
        assert data[HOOK:HOOK+4] == bytes.fromhex('0a018052') and data[0x26b4168:0x26b4170] == bytes.fromhex('e0630191e1c30291'), 'unexpected bulk fusion code'
        assert set(data[FO:FO + 0x240]) == {0}, 'fusion cave not empty'
        w = lambda x: struct.pack('<I', x)
        code = b''
        for val in ((8, 16, 32) if FUSION6 else (8, 16)):
            code += w(0x5280000a | (val << 5)) + w(0xb900b3ea) + w(0x910163e0) + w(0x9102c3e1)
            code += bl(FV + len(code), PB)
        code += B(FV + len(code), BACK)
        assert len(code) <= 0x50
        data[FO:FO + len(code)] = code
        data[HOOK:HOOK+4] = B(HOOK, FV)
        # createFilteredUnitList skipped any unit above 4 star and any unit whose family's lowest form is above 4 star.
        # Raise the unit cap to TOP and let the family limit be max(4, the unit's own rarity) so 4 star behaviour is unchanged.
        CV = FV + 0x50; CO = eng_file(CV); LIM1 = 0x26ae888; SKIP = 0x26ae794; AFTER = 0x26ae890; LIM2 = 0x26ae894
        assert data[LIM1:LIM1+8] == bytes.fromhex('5f1100714cf8ff54') and data[AFTER:AFTER+4] == bytes.fromhex('e8124239') and data[LIM2:LIM2+4] == bytes.fromhex('1f110071'), 'unexpected fusion filter code'
        if FUSION6:
            # families whose lowest form is NV/6 star or above (the 6th button, the game's own "NV start" filter) skip both limits
            NVOK = 0x26ae89c
            c2 = w(0x394212e8) + w(0x7100195f)
            c2 += BC(CV + len(c2), CV + len(c2) + 8, 0xb)     # b.lt over the long branch
            c2 += B(CV + len(c2), NVOK)
            c2 += w(0x52800089) + w(0x7100111f) + w(0x1a898109) + w(0x6b09015f)
        else:
            c2 = w(0x394212e8) + w(0x52800089) + w(0x7100111f) + w(0x1a898109) + w(0x6b09015f)
        c2 += BC(CV + len(c2), CV + len(c2) + 8, 0xd)     # b.le over the long branch (b.cond reaches only 1 MB)
        c2 += B(CV + len(c2), SKIP)
        c2 += B(CV + len(c2), AFTER)
        assert len(c2) <= 0x30
        data[CO:CO + len(c2)] = c2
        data[LIM1:LIM1+4] = B(LIM1, CV)
        data[LIM2:LIM2+4] = w(0x7100001f | (TOP << 10) | (8 << 5))
        end = CV + 0x20
        if FUSION6:
            SV = CV + 0x30; SO = eng_file(SV)
            stub = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fusion6_stub.bin'), 'rb').read()
            assert len(stub) == 352
            data[SO:SO + len(stub)] = stub
            CALL = 0x26b34e0
            assert data[CALL:CALL+4] == bl(CALL, 0x133eb90), 'unexpected setLayoutFilterRange call'
            data[CALL:CALL+4] = bl(CALL, SV)
            end = SV + len(stub)
            # the 6th button's picture: the game has no "6 star start" image, so use its NV start one (sort_label_nvstart_s<state>.png)
            DV = end; DO = eng_file(DV)
            dcode = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fusion6_label.bin'), 'rb').read()
            assert len(dcode) == 80 and DV == 0x43013e0
            assert data[0x26b42e4:0x26b42e8] == bytes.fromhex('e20319aa') and data[0x26b42f8:0x26b42fc] == bytes.fromhex('e20319aa')
            data[DO:DO + len(dcode)] = dcode
            data[0x26b42e4:0x26b42e8] = B(0x26b42e4, DV)
            data[0x26b42f8:0x26b42fc] = B(0x26b42f8, DV + 0x18)
            end = DV + len(dcode)
        grow_engine_segment(data, end)
        log.append('libgame: Bulk Fusion gets %s star base buttons' % ('5 and 6' if FUSION6 else '5'))
    if NEWUNIT:
        # Elvlin's engine never sends the gacha "new unit ids" field (uR70J6Lr), so GachaResultScene::isNewUnit is always
        # false and multi-summons never show the new-unit reveal (UnitGetScene) or NEW icon. Replace the one call in
        # GachaResultScene::setLayout with newunit.bin: a result is new if it is the first of its unit id in this summon
        # and the player owns no more copies of that unit than this summon gave (i.e. owned none before).
        NV_ = 0x4301430; NO_ = eng_file(NV_); CALLN = 0x217dd3c
        code = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'newunit.bin'), 'rb').read()
        assert data[CALLN:CALLN+4] == bl(CALLN, 0x13278e0), 'unexpected isNewUnit call'
        assert set(data[NO_:NO_ + len(code)]) == {0}, 'newunit cave not empty'
        data[NO_:NO_ + len(code)] = code
        data[CALLN:CALLN+4] = bl(CALLN, NV_)
        grow_engine_segment(data, NV_ + len(code))
        log.append('libgame: multi-summon new-unit reveal (new = owned no copy before)')
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
