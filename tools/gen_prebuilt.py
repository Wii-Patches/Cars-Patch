#!/usr/bin/env python3
"""Regenerate tools/prebuilt/*.json from src/ (needs devkitPPC and the retail main.dol of every release).

    CARS_DOLS=/dir/with/<ID>.dol  python3 tools/gen_prebuilt.py [cc|gc|pitstop|fov ...]

Each DOL can instead be given as CARS_DOL_<ID>; without either, work/dols/<ID>.dol
(and for the USA ones work/extracted_<ID>/DATA/sys/main.dol) are used.  Every
site is read from, and checked against, the release's own DOL.  The JSON is what
the patcher ships and reads; end users need neither devkitPPC nor game files.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'src'))
from dol import Dol
from features import PREBUILT, dump
from regions import REGIONS

USA = {'cars': 'RCAE78', 'mater': 'RC2E78', 'ror': 'R6OE78'}


def usa_dol(game):
    region = USA[game]
    env = os.environ.get('CARS_DOL_' + region)
    if env:
        return Dol(env)
    base = os.environ.get('CARS_DOLS')
    for p in ((os.path.join(base, region + '.dol'),) if base else ()) + (
            os.path.join(HERE, '..', 'work', 'extracted_' + region, 'DATA', 'sys', 'main.dol'),):
        if os.path.exists(p):
            return Dol(p)
    sys.exit('set CARS_DOLS=<dir with %s.dol> or CARS_DOL_%s=<path>' % (region, region))


def region_dol(region):
    """This release's own main.dol: CARS_DOL_<ID>, $CARS_DOLS/<ID>.dol or work/dols/<ID>.dol."""
    env = os.environ.get('CARS_DOL_' + region)
    if env:
        return Dol(env)
    base = os.environ.get('CARS_DOLS')
    for p in ((os.path.join(base, region + '.dol'),) if base else ()) + (
            os.path.join(HERE, '..', 'work', 'dols', region + '.dol'),):
        if os.path.exists(p):
            return Dol(p)
    return None


def main(argv):
    which = argv or ['cc', 'gc', 'pitstop', 'fov']
    os.makedirs(PREBUILT, exist_ok=True)
    usa = {g: usa_dol(g) for g in USA}
    for name in which:
        mod = __import__('gen_' + name)
        for region, meta in REGIONS.items():
            is_usa = USA[meta['game']] == region
            dol = usa[meta['game']] if is_usa else region_dol(region)
            if meta['game'] not in getattr(mod, 'GAMES', (meta['game'],)):
                continue
            f = mod.build(region, dol, usa[meta['game']]) if name == 'gc' else mod.build(region, dol)
            path = os.path.join(PREBUILT, '%s_%s.json' % (name, region))
            with open(path, 'w') as fh:
                json.dump(dump(f), fh, indent=1)
                fh.write('\n')
            print('%-3s %s  %d ops -> %s' % (name, region, len(f.ops), os.path.relpath(path)))


if __name__ == '__main__':
    main(sys.argv[1:])
