#!/usr/bin/env python3
"""Check the patch data against real, retail main.dol files.

    CARS_DOLS=<dir with RCAE78.dol RC2E78.dol R6OE78.dol> python3 tools/verify.py

For every release whose DOL is given and every combination of its patches (the GameCube pad always brings the Classic Controller code):
  * every site holds the retail bytes before patching
  * after patching, every hook site is a branch into the injected section whose
    trampoline runs back to site+4, and every in-place patch carries its new bytes
  * patching in steps (one feature at a time) gives the same file as all at once
  * nothing outside the intended sites changed
"""
import itertools
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import features
import patcher
from dol import Dol
from layout import CAVE_BASE, CAVE_LIMIT
from ops import Hook, apply_static
from regions import REGIONS

fail = []


def check(cond, msg):
    print(('  ok   ' if cond else '  FAIL ') + msg)
    if not cond:
        fail.append(msg)


def retail(region):
    base = os.environ.get('CARS_DOLS')
    p = os.path.join(base or '.', region + '.dol')
    return p if os.path.exists(p) else None


def main():
    for region in REGIONS:
        print(region, REGIONS[region]['label'])
        path = retail(region)
        if path is None:
            print('  skipped: no %s.dol in $CARS_DOLS' % region)
            continue
        d0 = Dol(path)
        # releases whose patches are byte-identical cannot be told apart by their DOL, nor need to be
        got = patcher.detect_region(d0)
        same = got is not None and all(
            features.available(n, got) == features.available(n, region) and
            (not features.available(n, region) or
             features.load(n, got).writes() == features.load(n, region).writes())
            for n in features.FEATURES)
        check(same, 'detected as %s%s' % (got, '' if got == region else ' (identical patches)'))
        have = [n for n in features.FEATURES if features.available(n, region)]
        for name in have:
            f = features.load(name, region)
            check(not f.check_pristine(d0), '%s: every site holds the retail bytes' % name)

        everything = itertools.chain.from_iterable(
            itertools.combinations(have, n) for n in range(1, len(have) + 1))
        for combo in everything:
            combo = tuple(features.closure(combo))
            d = Dol(path)
            patcher.patch(d, region, list(combo))
            touched = []
            for name in combo:
                f = features.load(name, region)
                ok = f.is_applied(d)
                check(ok, '%s patched alone-or-together: %s' % (name, '+'.join(combo)))
                for op in f.ops:
                    if isinstance(op, Hook):
                        site = struct.unpack('>I', d.read(op.site, 4))[0]
                        tgt = (site & 0x03FFFFFC)
                        tgt = tgt - 0x04000000 if tgt & 0x02000000 else tgt
                        check((site >> 26) == 18 and not site & 3 and (op.site + tgt) == op.tramp,
                              '%s: 0x%08X branches to 0x%08X' % (name, op.site, op.tramp))
                    touched += [(a, len(b)) for a, b in f.writes()]
            # nothing else changed
            for off, va, size, idx in d0.secs:
                a = bytes(d0.data[off:off + size]); b = d.read(va, size)
                diff = [i for i in range(size) if a[i] != b[i]]
                stray = [va + i for i in diff if not any(t <= va + i < t + n for t, n in touched)]
                if stray:
                    check(False, '%s: unexpected change at 0x%08X' % ('+'.join(combo), stray[0]))
            # stepwise == all at once
            step = Dol(path)
            for name in combo:
                apply_static(step, [features.load(name, region)])
            same = all(step.read(va, sz) == d.read(va, sz) for _o, va, sz, _i in d.secs) and len(step.secs) == len(d.secs)
            check(same, 'stepwise == together for %s' % '+'.join(combo))
    print('\nFAILED: %d' % len(fail) if fail else '\nALL VERIFIED')
    sys.exit(1 if fail else 0)


if __name__ == '__main__':
    main()
