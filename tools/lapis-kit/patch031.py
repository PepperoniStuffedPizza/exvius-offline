import json, os, re, struct, sys, zipfile
src, rules_apk, dst, lapis, new_code = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
SIG = re.compile(r'^META-INF/([^/]+\.(SF|RSA|DSA|EC)|MANIFEST\.MF)$', re.I)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from patch_axml import patch_version_code

EXTRA = sys.argv[6:]
NO_UPDATES = 'noupdates' in EXTRA
PROMPT_DEX = next((a[7:] for a in EXTRA if a.startswith('prompt=')), None)
LOOP_LIMIT = next((int(a[5:]) for a in EXTRA if a.startswith('loop=')), None)
INSTANT_SUMMON = 'instantsummon' in EXTRA
RAID_AUTOPLAY = 'raidautoplay' in EXTRA
SEARCH_NAME = 'searchname' in EXTRA
FP50K = 'fp50k' in EXTRA
ALL_CHALLENGES = 'allchallenges' in EXTRA
DROP_X = next((int(a[6:]) for a in EXTRA if a.startswith('dropx=')), None)
FP_DRAWS = next((int(a[8:]) for a in EXTRA if a.startswith('fpdraws=')), None)
SPEED = 4 if 'speed3r' in EXTRA else 3 if 'speed3' in EXTRA else 2 if 'speed2' in EXTRA else 0
SPEED2 = SPEED > 0
GET_LOOP_LIMIT = 0x19c0398  # MissionRepeatUtil::getLoopLimit() in v0.1.31 libgame.so (file offset == vaddr)
def disable_updates(d):
    import hashlib, zlib
    old = b'https://raw.githubusercontent.com/Elvlin/exvius-offline/main/data/latest.json'
    assert d.count(old) == 1
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
        for b in r['bundles']:
            if b['id'] == '990000113': b['limit'] = None
        r['bundles'].append({'id': '990000114', 'name': 'Lapis Chest (%s Lapis)' % format(lapis, ','),
                             'icon': '3197_20230905013503.png', 'gil': 1, 'limit': None, 'contents': ['50:1:%d' % lapis]})
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

zin, zr = zipfile.ZipFile(src), zipfile.ZipFile(rules_apk)
log = []
with zipfile.ZipFile(dst, 'w') as zout:
    for info in zin.infolist():
        if SIG.match(info.filename): continue
        data = zin.read(info.filename)
        if info.filename == 'lib/arm64-v8a/libgame.so':
            assert data.count(b'\x00rules/\x00') == 1
            data = data.replace(b'\x00rules/\x00', b'\x00rulez/\x00'); log.append('libgame: rules/ -> rulez/')
            if LOOP_LIMIT:
                assert data[GET_LOOP_LIMIT:GET_LOOP_LIMIT+4] == bytes.fromhex('fd7bbfa9'), 'unexpected getLoopLimit prologue'
                code = struct.pack('<II', 0x52800000 | (LOOP_LIMIT << 5), 0xd65f03c0)  # mov w0,#N ; ret
                data = data[:GET_LOOP_LIMIT] + code + data[GET_LOOP_LIMIT+8:]
                log.append('libgame: quest auto-play limit -> %d' % LOOP_LIMIT)
            if SEARCH_NAME:
                # GameUtils::getSearchUnitMstList only matches UnitMst::getSearchPhonetic() (Japanese reading, empty in this data).
                # Make it match the unit name instead: copy the name string (sp+0x118) into the phonetic slot (sp+0x100).
                S = 0x1a0036c
                assert data[S:S+12] == bytes.fromhex('e8030491e00317aa5b52e597'), 'unexpected search code'
                def bl(pc, tgt): return 0x94000000 | (((tgt - pc) >> 2) & 0x3ffffff)
                ctor = 0x1a00368 + 4 * (((0x97e47036 & 0x3ffffff) ^ 0x2000000) - 0x2000000)
                code = struct.pack('<III', 0x910403e0, 0x910463e1, bl(0x1a00374, ctor))
                data = bytearray(data); data[S:S+12] = code; data = bytes(data)
                # getSearchLibraryItemList (type 10 = units) keeps only LibraryUnitScene::isRegistered() units; this offline data
                # has no library registrations, so everything is filtered out. Always accept: tbnz w0,#0,ADD -> b ADD.
                R = 0x19fe4b4
                assert data[R:R+4] == bytes.fromhex('c0f90737'), 'unexpected isRegistered branch'
                data = bytearray(data); data[R:R+4] = struct.pack('<I', 0x14000000 | (((0x19fe3ec - R) >> 2) & 0x3ffffff)); data = bytes(data)
                log.append('libgame: unit search matches name, ignores library registration')
            if FP50K:
                # Built-in bundle 990000001 "2,000 Friend Points": reward string "51:1:2000" is built inline as a short std::string
                # (8 bytes from rodata + "0\0" immediate). Make it "51:1:50000".
                data = bytearray(data)
                assert data.count(b'\x0051:1:2000\x00') == 1
                i = data.index(b'\x0051:1:2000\x00'); data[i:i+11] = b'\x0051:1:5000\x00'
                assert data[0x3b525ac:0x3b525b0] == bytes.fromhex('48028052') and data[0x3b525c0:0x3b525c8] == bytes.fromhex('0806805208930f78')
                data[0x3b525ac:0x3b525b0] = struct.pack('<I', 0x52800288)   # mov w8,#20 (length 10)
                data[0x3b525c0:0x3b525c8] = struct.pack('<II', 0x52860608, 0xb80f9308)  # mov w8,#0x3030 ; stur w8,[x24,#0xf9] -> "00\0\0"
                assert data.count(b'2,000 Friend Points\x00') == 2
                data = bytes(data).replace(b'2,000 Friend Points\x00', b'50,000 Friend Point\x00')
                log.append('libgame: Friend Points bundle gives 50,000')
            if ALL_CHALLENGES:
                # complete_attempt (vaddr 0x40f0c38): after evaluating each mission challenge condition it does
                # cmp w0,#1 ; b.ne SKIP. Replace with: bl raised_check ; tbnz w0,#0,SKIP  -> every recognized
                # condition counts as met unless the evaluator raised an error (which keeps its original error path).
                C = 0x40f0c38 - 0x3f10000 + 0x399c000
                assert data[C:C+8] == struct.pack('<II', 0x7100041f, 0x54000941), 'unexpected challenge code'
                blw = 0x94000000 | (((0x40ff7ac - 0x40f0c38) >> 2) & 0x3ffffff)
                data = bytearray(data); data[C:C+8] = struct.pack('<II', blw, 0x37000940); data = bytes(data)
                log.append('libgame: mission challenges all count as met on clear')
            if INSTANT_SUMMON:
                # GachaEffectScene: skip the summon animation and go straight to the results.
                data = bytearray(data)
                # updateEvent: instead of waiting for taps/animation ends, jump to the end on the first frame,
                # then (once 0x604 'finished' is set) go to the result screen.
                assert data[0x2125780:0x2125788] == bytes.fromhex('681e583928020034')
                data[0x2125780:0x2125788] = bytes.fromhex('68125839') + struct.pack('<I', 0x35000000 | (((0x212576c - 0x2125784) >> 2 & 0x7ffff) << 5) | 8)
                # setNextAnime: always take the 'no more animations' branch
                assert data[0x2125860:0x2125864] == bytes.fromhex('c9000054')
                data[0x2125860:0x2125864] = struct.pack('<I', 0x14000000 | ((0x2125878 - 0x2125860) >> 2))
                data = bytes(data)
                log.append('libgame: summon animation skipped')
            if SPEED2:
                # 2x speed only while the battle's Auto is on (BattleState::isAutoBattle, byte at 0x39f0868+0x64).
                data = bytearray(data)
                cave_off, cave_va = 0x3da9ef0, 0x431def0          # padding after the last code segment
                cave = bytearray(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'speed_cave%d.bin' % SPEED), 'rb').read())
                c2 = {2: 0x60, 3: 0x70, 4: 0xa0}[SPEED]  # offset of the time-scale routine
                flag_page = 0x39f08cc & ~0xfff
                def adrp(pc, rd, page=flag_page):
                    imm = (page - (pc & ~0xfff)) >> 12
                    return struct.pack('<I', 0x90000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7ffff) << 5) | rd)
                cave[0x14:0x18] = adrp(cave_va + 0x14, 9)
                cave[c2:c2+4] = adrp(cave_va + c2, 16)
                if SPEED == 4:  # speed3r: second adrp -> Director singleton page (s_SharedDirector at 0x3efd320)
                    cave[0x30:0x34] = adrp(cave_va + 0x30, 9, 0x3efd000)
                assert set(data[cave_off:cave_off + 0x100]) == {0}
                data[cave_off:cave_off + len(cave)] = cave
                def bl(pc, target): return struct.pack('<I', 0x94000000 | (((target - pc) >> 2) & 0x3ffffff))
                # BaseScene::update: run per-frame logic (updateEvent) a second time when Auto is on
                call = 0x1e3a23c
                assert data[call:call+4] == bytes.fromhex('00013fd6'); data[call:call+4] = bl(call, cave_va)
                # Scheduler::update: time scale = 2.0 when Auto is on, else 1.0 (replaces ldr s1,[x0,#0x24])
                ts = 0x2ae40cc
                assert data[ts:ts+4] == bytes.fromhex('012440bd'); data[ts:ts+4] = bl(ts, cave_va + c2)
                ph = struct.unpack_from('<Q', data, 0x20)[0] + 56 * 3   # grow the 3rd LOAD (R E) to cover the routines
                assert struct.unpack_from('<QQQ', data, ph + 8) == (0x399c000, 0x3f10000, 0x3f10000)
                struct.pack_into('<QQ', data, ph + 32, 0x40dfe0, 0x40dfe0)
                data = bytes(data)
                log.append('libgame: game speed 3x on Auto, 2.5x on Repeat' if SPEED == 4 else 'libgame: %dx game speed while battle Auto is on' % SPEED)
            if RAID_AUTOPLAY:
                # ReadyForMissionScene::enableMissionRepeat refuses raids twice: world id must be 2, and
                # isRaidMission() (sub type 2) bails out. Route the first checks through a small routine that
                # lets raids skip both, and leaves every other mission on the original path.
                data = bytearray(data)
                def B(pc, t): return struct.pack('<I', 0x14000000 | (((t - pc) >> 2) & 0x3ffffff))
                def BC(pc, t, cond): return struct.pack('<I', 0x54000000 | ((((t - pc) >> 2) & 0x7ffff) << 5) | cond)
                RC, ROFF = 0x431dfd0, 0x3da9fd0
                FAIL, NORMAL, RAID = 0x236f120, 0x236f0d4, 0x236f0dc
                assert data[0x236f0bc:0x236f0d4] == bytes.fromhex('082c40b91f090071e102005408f040391f09007180020054')
                assert set(data[ROFF:ROFF + 0x30]) == {0}
                code = bytes.fromhex('084040b9') + bytes.fromhex('1f090071') + BC(RC+0x08, RC+0x28, 0x0) \
                     + bytes.fromhex('082c40b9') + bytes.fromhex('1f090071') + BC(RC+0x14, RC+0x2c, 0x1) \
                     + bytes.fromhex('08f04039') + bytes.fromhex('1f090071') + BC(RC+0x20, RC+0x2c, 0x0) \
                     + B(RC+0x24, NORMAL) + B(RC+0x28, RAID) + B(RC+0x2c, FAIL)
                assert RC + len(code) <= 0x431e000
                data[ROFF:ROFF + len(code)] = code
                data[0x236f0bc:0x236f0c0] = B(0x236f0bc, RC)
                ph = struct.unpack_from('<Q', data, 0x20)[0] + 56 * 3
                assert struct.unpack_from('<QQQ', data, ph + 8) == (0x399c000, 0x3f10000, 0x3f10000)
                struct.pack_into('<QQ', data, ph + 32, 0x40e000, 0x40e000)   # cover up to vaddr 0x431e000
                data = bytes(data)
                # ...and the final allow-list of mission sub types (bit mask 0x481 = types 0, 7, 10): add type 2 (raid)
                assert data[0x236f3c8:0x236f3cc] == bytes.fromhex('29908052')
                data = data[:0x236f3c8] + struct.pack('<I', 0x52800000 | (0x485 << 5) | 9) + data[0x236f3cc:]
                log.append('libgame: quest auto-play allowed in raids')
        elif info.filename == 'classes6.dex' and PROMPT_DEX:
            data = open(PROMPT_DEX, 'rb').read(); log.append('classes6.dex: data updates ask first, Elvlin app updates skipped')
        elif info.filename == 'classes6.dex' and NO_UPDATES:
            data = disable_updates(data); log.append('classes6.dex: update check URL -> unreachable host (.cox)')
        elif info.filename == 'AndroidManifest.xml':
            data = patch_version_code(data, 9071, new_code); log.append('versionCode 9071 -> %d' % new_code)
        out = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        out.compress_type, out.external_attr = info.compress_type, info.external_attr
        zout.writestr(out, data)
    n = 0
    for info in zr.infolist():
        if not info.filename.startswith('assets/rules/') or info.is_dir(): continue
        rel = info.filename[len('assets/rules/'):]
        data = edit_rule(rel, zr.read(info.filename))
        out = zipfile.ZipInfo('assets/rulez/' + rel, date_time=info.date_time)
        out.compress_type = zipfile.ZIP_DEFLATED
        zout.writestr(out, data); n += 1
    log.append('added %d rule files under assets/rulez/ (daily quests %d Lapis, + Lapis Chest, Super Premium Box unlimited)' % (n, lapis))
print('\n'.join(log))
