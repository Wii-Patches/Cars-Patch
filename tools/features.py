"""Load and manage prebuilt feature definitions (tools/prebuilt/<feature>_<region>.json)."""
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ops import Blob, Feature, Hook, Patch

if getattr(sys, 'frozen', False):
    PREBUILT = os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(sys.executable)), 'prebuilt')
else:
    PREBUILT = os.path.join(HERE, 'prebuilt')

FEATURES = ('cc', 'gc', 'pitstop', 'fov')
TITLES = {
    'cc': 'Classic Controller Support',
    'gc': 'GameCube Controller Support (Standalone)',
    'pitstop': 'Skip Pitstop Motions',
    'fov': 'Fix Widescreen FOV (hor+)',
}
DESCRIPTIONS = {
    'cc': 'Full analog Classic Controller and Classic Controller Pro support with native camera toggle.',
    'gc': 'Native GameCube Controller support (standard controls, ports 1-4, no Wii Remote required).',
    'pitstop': 'Automatically pass motion-controlled pitstop QTEs in Piston Cup races.',
    'fov': 'Correct anamorphic 16:9 vertical cropping (vert-) to proper horizontal expansion (hor+).',
}


def dump(feature):
    ops = []
    for op in feature.ops:
        if isinstance(op, Patch):
            ops.append(dict(t='patch', addr=op.addr, new=op.new.hex(), orig=op.orig.hex(), note=op.note))
        elif isinstance(op, Blob):
            ops.append(dict(t='blob', addr=op.addr, data=op.data.hex(), note=op.note))
        elif isinstance(op, Hook):
            ops.append(dict(t='hook', site=op.site, orig=op.orig, payload=op.payload, tramp=op.tramp, note=op.note))
    return dict(feature=feature.name, title=feature.title, region=feature.region, ops=ops)


def load_dict(j):
    ops = []
    for o in j['ops']:
        if o['t'] == 'patch':
            ops.append(Patch(o['addr'], bytes.fromhex(o['new']), bytes.fromhex(o['orig']), o.get('note', '')))
        elif o['t'] == 'blob':
            ops.append(Blob(o['addr'], bytes.fromhex(o['data']), o.get('note', '')))
        elif o['t'] == 'hook':
            ops.append(Hook(o['site'], o['orig'], o['payload'], o['tramp'], o.get('note', '')))
    return Feature(j['feature'], j['title'], j['region'], ops)


def load(name, region):
    path = os.path.join(PREBUILT, '%s_%s.json' % (name, region))
    if not os.path.exists(path):
        raise FileNotFoundError('Prebuilt definition not found: %s' % path)
    with open(path) as f:
        return load_dict(json.load(f))


def available(name, region):
    return os.path.exists(os.path.join(PREBUILT, '%s_%s.json' % (name, region)))

