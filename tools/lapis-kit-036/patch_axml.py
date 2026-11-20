import struct
def patch_version_code(axml, old, new):
    # Binary AndroidManifest: find attribute versionCode (android res id 0x0101021b) in the <manifest> start tag.
    assert struct.unpack_from('<HHI', axml, 0)[0] == 0x0003
    pos = 8; resmap = []
    while pos < len(axml):
        ctype, hsize, csize = struct.unpack_from('<HHI', axml, pos)
        if ctype == 0x0180:  # resource map
            resmap = list(struct.unpack_from('<%dI' % ((csize - 8) // 4), axml, pos + 8))
        elif ctype == 0x0102:  # start element
            attr_start, attr_size, attr_count = struct.unpack_from('<HHH', axml, pos + 16 + 8)
            base = pos + 16 + attr_start
            for i in range(attr_count):
                a = base + i * attr_size
                ns, name, raw, size, res0, dtype, data = struct.unpack_from('<IIiHBBI', axml, a)
                if name < len(resmap) and resmap[name] == 0x0101021b:
                    assert dtype == 0x10 and data == old, (dtype, data)
                    out = bytearray(axml); struct.pack_into('<I', out, a + 16, new)
                    return bytes(out)
        pos += csize
    raise ValueError('versionCode not found')

