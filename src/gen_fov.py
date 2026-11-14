"""Build the Cars (2006) widescreen fix: Vague Rant's "Fix Widescreen FOV" codes, as ops.

The game renders 16:9 by cropping the 4:3 view vertically (vert-); his two hooks
widen the horizontal field of view instead (hor+) when the console is set to
16:9.  src/fov/<ID>.txt are his codes, one per release (his EUR (En,Es) / (De,It)
code serves RCAP78 and RCAY78).  Each carries two function addresses of its own
release; those are checked against the DOL to be function entries.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from gen_cc import parse
from layout import FOV_BASE, FOV_END
from ops import Feature, Hook

GAMES = ('cars',)


def build(region, dol=None):
    ops, cur = [], FOV_BASE
    for kind, addr, body in parse(open(os.path.join(HERE, 'fov', region + '.txt')).read()):
        assert kind == 'C2' and body[-1] == 0, 'unexpected code in fov/%s.txt' % region
        orig = None
        if dol is not None:
            orig = struct.unpack('>I', dol.read(addr, 4))[0]
            # the `bl 1f` after the first few words is followed by two function pointers
            for i, w in enumerate(body[:-1]):
                if w == 0x48000019:
                    for fp in body[i + 1:i + 3]:
                        if struct.unpack('>I', dol.read(fp, 4))[0] >> 16 != 0x9421:
                            raise SystemExit('%s: fov code points at 0x%08X, not a function entry' % (region, fp))
        ops.append(Hook(addr, orig, body, cur, note='Widescreen fix (hor+) hook'))
        cur += (len(body) * 4 + 15) & ~15
    if cur > FOV_END:
        raise SystemExit('fov code overflows its window')
    return Feature('fov', 'Widescreen fix', region, ops)
