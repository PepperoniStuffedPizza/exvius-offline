"""Build a lapis APK on Elvlin's beta v0.1.90 (versionCode 9130).

build090.py <beta.apk> <v0.1.36.apk> <game-assets-r34.apk> <libgame-lapis.so> <classes8-lapis.dex> <out-unsigned.apk>
            <lapis> <versionCode> [patch036 rule options...]
- libgame: made by port090.py from a patch036.py build with the same options
- AndroidManifest.xml: the v0.1.36 app's (package com.exvius.offline.test, so it installs over the lapis app);
  identical to the beta's apart from the package-derived names; versionCode patched, versionName -> offline.90
- rules: rulez/ copies of data r34 rules, edited by patch036.py's edit_rule()
"""
import os, re, sys, zipfile
beta, old, rules_apk, lib, dex, dst, lapis, code = sys.argv[1:9]
opts = sys.argv[9:]
KIT = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(KIT, 'patch036.py')).read()
src = src[:src.index('\nzin, zr =')]
g = {'__file__': os.path.join(KIT, 'patch036.py'), '__name__': 'p036'}
sys.argv = ['patch036.py', 'x', 'x', 'x', lapis, code] + opts
exec(compile(src, 'patch036.py', 'exec'), g)
edit_rule, log = g['edit_rule'], []
g['log'] = log
from patch_axml import patch_version_code
SIG = re.compile(r'^META-INF/([^/]+\.(SF|RSA|DSA|EC)|MANIFEST\.MF)$', re.I)
zb, zo, zr = zipfile.ZipFile(beta), zipfile.ZipFile(old), zipfile.ZipFile(rules_apk)
man = zo.read('AndroidManifest.xml')
a, b = '9.0.0-offline.36'.encode('utf-16le'), '9.0.0-offline.90'.encode('utf-16le')
assert man.count(a) == 1; man = man.replace(a, b)
man = patch_version_code(man, 9076, int(code))
with zipfile.ZipFile(dst, 'w') as z:
    for info in zb.infolist():
        if SIG.match(info.filename): continue
        data = zb.read(info.filename)
        if info.filename == 'lib/arm64-v8a/libgame.so': data = open(lib, 'rb').read()
        elif info.filename == 'classes8.dex':
            assert b'exvius-offline-beta/main/data/latest.json' in data; data = open(dex, 'rb').read()
        elif info.filename == 'AndroidManifest.xml': data = man
        out = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        out.compress_type, out.external_attr = info.compress_type, info.external_attr
        z.writestr(out, data)
    n = 0
    for info in zr.infolist():
        if not info.filename.startswith('assets/rules/') or info.is_dir(): continue
        rel = info.filename[len('assets/rules/'):]
        data = edit_rule(rel, zr.read(info.filename))
        out = zipfile.ZipInfo('assets/rulez/' + rel, date_time=info.date_time)
        out.compress_type = info.compress_type if info.filename.lower().endswith('.png') else zipfile.ZIP_DEFLATED
        z.writestr(out, data); n += 1
    log.append('%d rule files (data r34) under assets/rulez/; versionCode %s; package com.exvius.offline.test' % (n, code))
print('\n'.join(log))
