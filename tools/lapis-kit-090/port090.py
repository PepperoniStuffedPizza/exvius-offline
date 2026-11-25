"""Transplant the lapis libgame patches from a patched v0.1.36 libgame onto Elvlin's beta v0.1.90 libgame.

Inputs: original v0.1.36 libgame, lapis-patched v0.1.36 libgame (from patch036.py), original beta v0.1.90 libgame.
The original game code (first LOAD) is identical at every patched site, so client patches are copied as-is, except
branches into the code cave, which are re-targeted. The cave block (0x4300e30..0x4301534 in 0.1.36) is moved to
just after the beta's (larger) engine segment and its PC-relative references to the outside are re-encoded.
Engine-side patches (rules path, Friend Points, mission challenges) are re-applied at their beta addresses.
"""
import struct, sys
o36, p36, b90, out = [open(a, 'rb').read() for a in sys.argv[1:4]] + [sys.argv[4]]
ENG_OFF, ENG_VA = 0x399c000, 0x3f10000
def ef(va): return va - ENG_VA + ENG_OFF
OLD_CAVE, OLD_END = 0x4300e30, 0x4301534
B90_ENG_SIZE, B90_NEXT = 0x4240f8, 0x3dc4000
NEW_CAVE = 0x4334100
D = NEW_CAVE - OLD_CAVE
OLD_FLAG, NEW_FLAG = 0x4731940, 0x4731c20      # fast-forward flag block (16 bytes after the .bss end)
DATA = [(0x4301394, 0x43013e0), (0x4301410, 0x4301430)]   # strings inside the cave
log = []
d = bytearray(b90)

def sx(v, bits): return v - (1 << bits) if v & (1 << (bits - 1)) else v
def retarget(w, pc, newpc, inside):
    """Re-encode a PC-relative instruction at pc so it reaches the same target from newpc. Returns new word or None."""
    if (w & 0x7c000000) == 0x14000000:                        # B / BL
        t = pc + 4 * sx(w & 0x3ffffff, 26)
        if inside(t): t += newpc - pc
        return (w & 0xfc000000) | (((t - newpc) >> 2) & 0x3ffffff)
    if (w & 0xff000010) == 0x54000000 or (w & 0x7e000000) == 0x34000000:   # B.cond / CBZ / CBNZ
        t = pc + 4 * sx((w >> 5) & 0x7ffff, 19)
        if inside(t): t += newpc - pc
        r = (t - newpc) >> 2; assert -(1 << 18) <= r < (1 << 18)
        return (w & ~(0x7ffff << 5)) | ((r & 0x7ffff) << 5)
    if (w & 0x7e000000) == 0x36000000:                        # TBZ / TBNZ
        t = pc + 4 * sx((w >> 5) & 0x3fff, 14)
        if inside(t): t += newpc - pc
        r = (t - newpc) >> 2; assert -(1 << 13) <= r < (1 << 13)
        return (w & ~(0x3fff << 5)) | ((r & 0x3fff) << 5)
    if (w & 0x9f000000) == 0x90000000:                        # ADRP
        imm = sx((((w >> 5) & 0x7ffff) << 2) | ((w >> 29) & 3), 21)
        t = (pc & ~0xfff) + (imm << 12)
        if inside(t): t += newpc - pc                          # (no adrp into the cave exists)
        if t == OLD_FLAG & ~0xfff: t = NEW_FLAG & ~0xfff
        imm = (t - (newpc & ~0xfff)) >> 12
        return (w & 0x9f00001f) | ((imm & 3) << 29) | (((imm >> 2) & 0x7ffff) << 5)
    if (w & 0x9f000000) == 0x10000000:                        # ADR
        imm = sx((((w >> 5) & 0x7ffff) << 2) | ((w >> 29) & 3), 21)
        t = pc + imm
        assert inside(t), 'adr to outside the cave'
        return w                                               # relative to inside: unchanged
    return None

inside = lambda t: OLD_CAVE <= t < OLD_END
# 1. client patches
for i in range(0x1000, ENG_OFF, 4):
    if o36[i:i+4] == p36[i:i+4]: continue
    assert b90[i:i+4] == o36[i:i+4], 'beta differs at patched site %x' % i
    w = struct.unpack_from('<I', p36, i)[0]
    if (w & 0x7c000000) == 0x14000000 and inside(i + 4 * sx(w & 0x3ffffff, 26)):
        t = i + 4 * sx(w & 0x3ffffff, 26) + D
        w = (w & 0xfc000000) | (((t - i) >> 2) & 0x3ffffff); log.append('client %x: branch into cave -> %x' % (i, t))
    struct.pack_into('<I', d, i, w)
# 2. cave block
blk = bytearray(p36[ef(OLD_CAVE):ef(OLD_END)])
assert set(o36[ef(OLD_CAVE):ef(OLD_END)]) == {0}
flagpages = 0
for k in range(0, len(blk), 4):
    pc = OLD_CAVE + k
    if any(a <= pc < b for a, b in DATA): continue
    w = struct.unpack_from('<I', blk, k)[0]
    if (w & 0x9f000000) == 0x90000000:
        imm = sx((((w >> 5) & 0x7ffff) << 2) | ((w >> 29) & 3), 21)
        page = (pc & ~0xfff) + (imm << 12)
        if inside(page):                                       # adrp+add to a string in the cave
            a = struct.unpack_from('<I', blk, k + 4)[0]
            assert (a & 0xffc00000) == 0x91000000 and (a & 31) == (w & 31) == ((a >> 5) & 31)
            t = page + ((a >> 10) & 0xfff) + D
            imm = (t & ~0xfff) - ((pc + D) & ~0xfff) >> 12
            struct.pack_into('<II', blk, k, (w & 0x9f00001f) | ((imm & 3) << 29) | (((imm >> 2) & 0x7ffff) << 5),
                             (a & ~(0xfff << 10)) | ((t & 0xfff) << 10))
            continue
    nw = retarget(w, pc, pc + D, inside)
    if nw is not None: struct.pack_into('<I', blk, k, nw)
    # byte loads/stores off the flag page base: ldrb/strb wN,[xM,#0x94x]
    if (w & 0xffc00000) in (0x39400000, 0x39000000):
        imm = (w >> 10) & 0xfff
        if 0x940 <= imm < 0x950:
            struct.pack_into('<I', blk, k, (w & ~(0xfff << 10)) | ((imm - 0x940 + (NEW_FLAG & 0xfff)) << 10)); flagpages += 1
assert flagpages == 10, flagpages
assert set(d[ef(NEW_CAVE) - 8:ef(NEW_CAVE) + len(blk)]) == {0}
assert ef(NEW_CAVE) + len(blk) <= B90_NEXT
d[ef(NEW_CAVE):ef(NEW_CAVE) + len(blk)] = blk
log.append('cave block %d bytes moved %x -> %x' % (len(blk), OLD_CAVE, NEW_CAVE))
# 3. program headers: engine segment covers the cave; .bss grows by the 16-byte flag block
ph = struct.unpack_from('<Q', d, 0x20)[0]
off, va, pa, fsz, msz = struct.unpack_from('<QQQQQ', d, ph + 56 * 3 + 8)
assert (off, va, fsz, msz) == (ENG_OFF, ENG_VA, B90_ENG_SIZE, B90_ENG_SIZE)
size = NEW_CAVE + len(blk) - ENG_VA
struct.pack_into('<QQ', d, ph + 56 * 3 + 32, size, size)
off, va, pa, fsz, msz = struct.unpack_from('<QQQQQ', d, ph + 56 * 4 + 8)
assert (off, va, fsz, msz) == (B90_NEXT, 0x4710000, 0x80, 0x21c18), 'unexpected beta bss'
struct.pack_into('<Q', d, ph + 56 * 4 + 40, NEW_FLAG + 0x10 - 0x4710000)
# 4. engine patches
assert d.count(b'\x00rules/\x00') == 1
i = d.index(b'\x00rules/\x00'); d[i:i+8] = b'\x00rulez/\x00'; log.append('rules/ -> rulez/')
if p36.count(b'\x0051:1:5000\x00'):
    assert d.count(b'\x0051:1:2000\x00') == 1
    i = d.index(b'\x0051:1:2000\x00'); d[i:i+11] = b'\x0051:1:5000\x00'
    L, M, S = ef(0x3fbe76c), ef(0x3fbe784), ef(0x3fbe794)
    assert d[L:L+4] == bytes.fromhex('48028052') and d[M:M+4] == bytes.fromhex('08068052') and d[S:S+4] == bytes.fromhex('28130978')
    d[L:L+4] = struct.pack('<I', 0x52800288); d[M:M+4] = struct.pack('<I', 0x52860608); d[S:S+4] = struct.pack('<I', 0xb8091328)
    assert d.count(b'2,000 Friend Points\x00') == 2
    d = bytearray(bytes(d).replace(b'2,000 Friend Points\x00', b'50,000 Friend Point\x00'))
    log.append('Friend Points bundle gives 50,000')
if p36[ef(0x40d9da8):ef(0x40d9da8)+4] != o36[ef(0x40d9da8):ef(0x40d9da8)+4]:
    CV, SKIP, RAISED = 0x40e5818, 0x40e5f18, 0x3fcb348
    C = ef(CV)
    bc = 0x54000001 | ((((SKIP - (CV + 4)) >> 2) & 0x7ffff) << 5)
    assert d[C:C+8] == struct.pack('<II', 0x7100069f, bc), 'unexpected challenge code'
    w = d[ef(RAISED)+4:ef(RAISED)+20]; assert w == bytes.fromhex('081542f91f0100f1e0079f1ac0035fd6'), w.hex()
    imm14 = (SKIP - (CV + 4)) >> 2
    d[C:C+4] = struct.pack('<I', 0x94000000 | (((RAISED - CV) >> 2) & 0x3ffffff))
    d[C+4:C+8] = struct.pack('<I', 0x37000000 | ((imm14 & 0x3fff) << 5))
    log.append('mission challenges all count as met on clear')
open(out, 'wb').write(d)
print('\n'.join(log))
