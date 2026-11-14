"""Apply the selected patches to one main.dol."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features
from dol import Dol
from ops import apply_static
from regions import REGIONS

ORDER = features.FEATURES


def detect_region(dol):
    """Which release this main.dol is, from its own bytes (None if unknown).

    Only releases whose retail bytes have been checked can be told apart; the
    others need `--region` (or a disc image, which names its own release).
    """
    for region in REGIONS:
        f = features.load('cc', region)
        if f.verified and (not f.check_pristine(dol) or f.is_applied(dol)):
            return region
    return None


def status(dol, region):
    """{feature: 'clean' | 'patched' | 'mismatch'} for each feature on this DOL."""
    out = {}
    for name in ORDER:
        if not features.available(name, region):
            continue
        f = features.load(name, region)
        if f.is_applied(dol):
            out[name] = 'patched'
        elif not f.check_pristine(dol):
            out[name] = 'clean'
        else:
            out[name] = 'mismatch'
    return out


def patch(dol, region, which):
    """Patch `dol` (a dol.Dol) in place with the features named in `which`
    (plus the Classic Controller code the GameCube pad depends on)."""
    names = [n for n in features.closure(which) if features.available(n, region)]
    if not names:
        raise ValueError('nothing selected')
    apply_static(dol, [features.load(n, region) for n in names])
    return [features.TITLES[n] for n in names]


def patch_file(src, dst, region, which):
    dol = Dol(src)
    done = patch(dol, region, which)
    dol.save(dst)
    return done


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Patch a Cars / Cars: Mater-National / Cars Race-O-Rama main.dol')
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--region', choices=sorted(REGIONS), help='default: detect')
    for n in ORDER:
        ap.add_argument('--' + n, action='store_true', help=features.TITLES[n])
    a = ap.parse_args()
    d = Dol(a.src)
    reg = a.region or detect_region(d)
    if not reg:
        sys.exit('could not identify this main.dol; pass --region')
    which = [n for n in ORDER if getattr(a, n)] or list(ORDER)
    print(reg, REGIONS[reg]['label'], '->', ', '.join(patch_file(a.src, a.dst, reg, which)))
