"""Build the Classic Controller feature: Vague Rant's Gecko codes, as ops.

The codes in src/cc/<ID>.txt are his (see README credits); this only parses
them into Patch/Hook ops so the same data can become a patched DOL, a Gecko
list or a Riivolution patch.  `dol` is the release's own main.dol, or None when
none is at hand (then the retail bytes are left unchecked).
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from layout import CC_BASE, CC_END
from ops import Feature, Hook, Patch


def parse(text):
    lines = [l.split()[:2] for l in text.splitlines() if l.strip() and not l.lstrip().startswith(('*', '$', '#'))]
    i, out = 0, []
    while i < len(lines):
        a, b = lines[i]
        kind, addr = int(a[:2], 16), 0x80000000 | (int(a[2:], 16) & 0x01FFFFFF)
        if kind == 0x04:
            out.append(('04', addr, [int(b, 16)]))
            i += 1
        elif kind == 0x06:
            n = int(b, 16)
            nl = (n + 7) // 8
            raw = b''.join(bytes.fromhex(x) for ln in lines[i + 1:i + 1 + nl] for x in ln)
            out.append(('06', addr, raw[:n]))
            i += 1 + nl
        elif kind == 0xC2:
            n = int(b, 16)
            ws = [int(x, 16) for ln in lines[i + 1:i + 1 + n] for x in ln]
            out.append(('C2', addr, ws))
            i += 1 + n
        else:
            raise ValueError('unsupported code line: %s %s' % (a, b))
    return out


def build(region, dol=None):
    text = open(os.path.join(HERE, 'cc', region + '.txt')).read()
    ops, cur = [], CC_BASE
    for kind, addr, body in parse(text):
        if kind == '04':
            new = struct.pack('>I', body[0])
            ops.append(Patch(addr, new, dol.read(addr, 4) if dol else None, note='Classic Controller patch'))
        elif kind == '06':
            ops.append(Patch(addr, body, dol.read(addr, len(body)) if dol else None, note='Classic Controller patch'))
        else:
            orig = struct.unpack('>I', dol.read(addr, 4))[0] if dol else None
            assert body[-1] == 0, 'C2 body does not end in the branch-back slot'
            ops.append(Hook(addr, orig, body, cur, note='Classic Controller hook'))
            cur += (len(body) * 4 + 15) & ~15
    if cur > CC_END:
        raise SystemExit('cc code overflows its window')
    return Feature('cc', 'Classic Controller', region, ops)
