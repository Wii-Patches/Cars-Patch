"""Build the Cars (2006) pitstop skip: Vague Rant's "Skip Pitstop Motions" code.

One branch that makes the Piston Cup pitstop minigame count its motion QTEs as
done; the same address in every release of Cars (checked against each DOL).
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
from ops import Feature, Patch

GAMES = ('cars',)
SITE = 0x80062CAC
NEW = 0x4800001C        # b +0x1C
ORIG = 0x408202BC       # bne 0x80062F68 (the same in every release)


def build(region, dol=None):
    orig = None
    if dol is not None:
        orig = dol.read(SITE, 4)
        if struct.unpack('>I', orig)[0] != ORIG:
            raise SystemExit('%s: pitstop site holds 0x%08X' % (region, struct.unpack('>I', orig)[0]))
    return Feature('pitstop', 'Skip pitstop motions', region,
                   [Patch(SITE, struct.pack('>I', NEW), orig, note='Skip pitstop motions')])
