import json, struct, subprocess, sys, zipfile, io
m = json.load(open('/home/claude/exvius-offline/data/latest.json'))
def tail(url, n):
    return subprocess.run(['curl', '-sSL', '-r', '-%d' % n, url], capture_output=True).stdout
for p in m['packs']:
    if not p['id'].startswith('data-0'): continue
    data = tail(p['url'], 8 * 1024 * 1024)
    i = data.rfind(b'PK\x05\x06')
    if i < 0: print(p['id'], 'no EOCD in tail'); continue
    cd_size, cd_off = struct.unpack_from('<II', data, i + 12)
    names = []
    j = data.find(b'PK\x01\x02')
    pos = len(data) - (p['size'] - cd_off) if cd_off != 0xFFFFFFFF else j
    pos = j if pos < 0 else pos
    while 0 <= pos < len(data) and data[pos:pos+4] == b'PK\x01\x02':
        nlen, elen, clen = struct.unpack_from('<HHH', data, pos + 28)
        names.append(data[pos+46:pos+46+nlen].decode('utf-8', 'replace'))
        pos += 46 + nlen + elen + clen
    hits = [n for n in names if 'mst_decoded' in n and ('ITEM' in n or 'UNIT' in n or 'AWAKE' in n or 'EVO' in n)]
    print(p['id'], len(names), 'entries read;', hits[:20])
