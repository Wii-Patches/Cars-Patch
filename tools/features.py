"""Load the prebuilt feature definitions (tools/prebuilt/<feature>_<region>.json)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ops import Blob, Feature, Hook, Patch

if getattr(sys, 'frozen', False):
    PREBUILT = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), 'prebuilt')
else:
    PREBUILT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prebuilt')

FEATURES = ('cc', 'gc', 'pitstop', 'fov')
TITLES = {
    'cc': 'Classic Controller',
    'gc': 'GameCube controller',
    'pitstop': 'Skip pitstop motions',
    'fov': 'Widescreen fix (hor+)',
}
# the GameCube pad rides on the Classic Controller code: selecting gc selects cc too
REQUIRES = {'gc': 'cc'}
# features that exist for some games only (the rest exist for every release)
GAMES = {'pitstop': ('cars',), 'fov': ('cars',)}


def applies(name, region):
    """Does `name` exist for this release's game at all?"""
    from regions import REGIONS
    return REGIONS[region]['game'] in GAMES.get(name, (REGIONS[region]['game'],))


def dump(feature):
    ops = []
    for op in feature.ops:
        if isinstance(op, Patch):
            ops.append(dict(t='patch', addr=op.addr, new=op.new.hex(),
                            orig=None if op.orig is None else op.orig.hex(), note=op.note))
        elif isinstance(op, Blob):
            ops.append(dict(t='blob', addr=op.addr, data=op.data.hex(), note=op.note))
        elif isinstance(op, Hook):
            ops.append(dict(t='hook', site=op.site, orig=op.orig, payload=op.payload, tramp=op.tramp, note=op.note))
    return dict(feature=feature.name, title=feature.title, region=feature.region, ops=ops)


def load_dict(j):
    ops = []
    for o in j['ops']:
        if o['t'] == 'patch':
            orig = None if o['orig'] is None else bytes.fromhex(o['orig'])
            ops.append(Patch(o['addr'], bytes.fromhex(o['new']), orig, o.get('note', '')))
        elif o['t'] == 'blob':
            ops.append(Blob(o['addr'], bytes.fromhex(o['data']), o.get('note', '')))
        elif o['t'] == 'hook':
            ops.append(Hook(o['site'], o['orig'], o['payload'], o['tramp'], o.get('note', '')))
    return Feature(j['feature'], j['title'], j['region'], ops)


def load(name, region):
    with open(os.path.join(PREBUILT, '%s_%s.json' % (name, region))) as f:
        return load_dict(json.load(f))


def available(name, region):
    return os.path.exists(os.path.join(PREBUILT, '%s_%s.json' % (name, region)))


def closure(which):
    """`which` plus what it needs, in application order."""
    want = set(which)
    for n in list(want):
        if n in REQUIRES:
            want.add(REQUIRES[n])
    return [n for n in FEATURES if n in want]
