"""Build the GameCube controller feature for one region from src/*.s.

Three engines, three small sets of hooks (see docs/TECHNICAL.md):

  cars   -- Cars (2006)
  mater  -- Cars: Mater-National Championship
  ror    -- Cars Race-O-Rama

The sites below are the USA ones; the KPAD library is byte-identical in the
other releases of a game apart from where it is linked, so theirs are the USA
ones plus REGIONS[id]['kpad'].  Only the USA DOLs have been checked.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import asm
from layout import GC_BASE, GC_END
from ops import Feature, Hook
from regions import REGIONS

DEAD = 10           # control stick dead zone (of 128)
KMUL = 205          # 256 * 64 / 80, rounded up: full scale 80 steps past the dead zone
CDEAD = 35          # C-stick threshold for jump / map
STATE = 0x80002FC0  # gc_poll.s: probe time stamps and NOREP counters (end of the gc window)

# USA entry of KPADRead (hooked by the SI poller, gc_poll.s)
KPADREAD = {'cars': 0x802F8568, 'mater': 0x802F3868, 'ror': 0x803671D0}

# name -> (library symbols, [(source, [sites], note)])
GAMES = {
    'cars': dict(
        syms=dict(ACC_FUNC=0x802F67DC),
        hooks=[('cars_acc.s', [0x802F86E0], 'KPAD read loop: GameCube stick -> Classic Controller stick', True),
               ('cars_restore.s', [0x802F889C], 'KPAD read: put the real extension type back', False),
               ('cars_buttons.s', [0x802F64B0], 'KPAD buttons: GameCube buttons -> Wii Remote bits', False)]),
    'mater': dict(
        syms=dict(ACC_FUNC=0x802F1D24),
        hooks=[('mater_acc.s', [0x802F3F14], 'KPAD read loop: GameCube stick -> Classic Controller stick', True),
               ('mater_restore.s', [0x802F3F50], 'KPAD read loop: put the real extension type back', False),
               ('mater_buttons.s', [0x802F3E10], 'KPAD buttons: GameCube buttons -> Classic Controller bits', False)]),
    'ror': dict(
        syms=dict(ACC_FUNC=0x80364F80, LISW=0x803671F2, ADDIW=0x803671FE),
        hooks=[('ror_acc.s', [0x803677EC, 0x80367958], 'KPAD read loop: GameCube stick -> Classic Controller stick', True),
               ('ror_restore.s', [0x8036782C, 0x8036799C], 'KPAD read loop: put the real extension type back', False),
               ('ror_buttons.s', [0x803677B4, 0x80367904], 'KPAD buttons: GameCube buttons -> Classic Controller bits', False),
               ('ror_type.s', [0x8032AF18], 'controller type table: a GameCube pad counts as a Classic Controller', False)]),
}


def _read(name):
    return open(os.path.join(HERE, name)).read()


def _word(dol, a):
    return struct.unpack('>I', dol.read(a, 4))[0]


def _si(dol):
    """(si state block, SIGetType) read out of a DOL's own si library.

    SISetXY is the one `stw rX,0x6430(rY)` (SIPOLL) in the text, preceded by the
    `lis r5 / addi r5` that loads the si state block (+4 the SIPOLL shadow, +0x18
    the cached port types); SIInit calls SIGetType for the four ports with four
    `bl`s eight bytes apart."""
    w = lambda a: _word(dol, a)
    si, gettype = set(), set()
    for off, base, size, idx in dol.secs:
        if idx >= 7:
            continue
        ws = struct.unpack('>%dI' % (size // 4), bytes(dol.data[off:off + size]))
        for i, x in enumerate(ws):
            a = base + 4 * i
            if x >> 26 == 36 and x & 0xFFFF == 0x6430:
                lo = [w(a - 4 * k) for k in range(1, 12) if w(a - 4 * k) >> 16 == 0x38A5]
                hi = [w(a - 4 * k) for k in range(1, 16) if w(a - 4 * k) >> 16 == 0x3CA0]
                if lo and hi:
                    l = lo[0] & 0xFFFF
                    si.add((((hi[0] & 0xFFFF) << 16) + (l - 0x10000 if l & 0x8000 else l)) & 0xFFFFFFFF)
        for i in range(len(ws) - 8):
            if all(ws[i + 2 * j] >> 26 == 18 and ws[i + 2 * j] & 3 == 1 for j in range(4)):
                t = {_bl_target(ws[i + 2 * j], base + 4 * (i + 2 * j)) for j in range(4)}
                if len(t) == 1:
                    tgt = t.pop()
                    # SIGetType indexes the type cache: lis rX,Si@ha ... addi rY,rX,(Si+0x18)@l
                    body = [w(tgt + 4 * k) for k in range(24)]
                    if any(b >> 26 == 14 and (b & 0xFFFF) == ((min(si or {0}) + 0x18) & 0xFFFF) for b in body):
                        gettype.add(tgt)
    if len(si) != 1 or len(gettype) != 1:
        raise SystemExit('%s: si state %s / SIGetType %s not found exactly once'
                         % (dol.path, [hex(x) for x in si], [hex(x) for x in gettype]))
    return si.pop(), gettype.pop()


def _bl_target(word, at):
    li = word & 0x03FFFFFC
    li -= 0x04000000 if li & 0x02000000 else 0
    return (at + li) & 0xFFFFFFFF


def build(region, dol=None, usa_dol=None):
    """`dol`: this release's main.dol (None: unchecked); `usa_dol`: the USA one of the game."""
    meta = REGIONS[region]
    shift = meta['kpad']
    game = GAMES[meta['game']]
    ref = dol if dol is not None else usa_dol
    if ref is None:
        raise SystemExit('%s: need the USA main.dol of the game to read the displaced instructions' % region)
    syms = {k: v + shift for k, v in game['syms'].items()}
    if dol is None:
        raise SystemExit('%s: need the release\'s own main.dol (the si addresses are read from it)' % region)
    syms['SIBASE'], syms['SIGETTYPE'] = _si(dol)
    syms['STATE'] = STATE
    consts = dict(DEAD=DEAD, KMUL=KMUL, CDEAD=CDEAD)
    macros = _read('gc_macros.s')
    helpers = _read('gc_stick.s')
    ops, cur = [], GC_BASE

    site = KPADREAD[meta['game']] + shift
    orig_word = _word(dol, site)
    if usa_dol is not None and orig_word != _word(usa_dol, KPADREAD[meta['game']]):
        raise SystemExit('%s: KPADRead entry 0x%08X does not match the USA one' % (region, site))
    if orig_word >> 16 != 0x9421:
        raise SystemExit('%s: KPADRead entry 0x%08X is 0x%08X, not a stwu' % (region, site, orig_word))
    words = asm.words(asm.assemble(_read('gc_poll.s'), cur, syms, dict(ORIG=orig_word))) + [0]
    ops.append(Hook(site, orig_word, words, cur, note='KPADRead entry: keep the GameCube ports probed and polled'))
    cur += (len(words) * 4 + 15) & ~15
    for src, sites, note, needs_helpers in game['hooks']:
        for usa_site in sites:
            site = usa_site + shift
            orig_word = _word(dol, site) if dol is not None else _word(usa_dol, usa_site)
            if usa_dol is not None and (orig_word >> 26) != 18 and orig_word != _word(usa_dol, usa_site):
                raise SystemExit('%s: 0x%08X holds 0x%08X, the USA site 0x%08X holds 0x%08X'
                                 % (region, site, orig_word, usa_site, _word(usa_dol, usa_site)))
            text = macros + '\n' + _read(src)
            if needs_helpers:
                text += '\n' + helpers + '\nend:\n'
            c = dict(consts, ORIG=orig_word)
            words = asm.words(asm.assemble(text, cur, syms, c)) + [0]
            if src.endswith('_acc.s') and (orig_word >> 26) != 18:
                raise SystemExit('%s: 0x%08X is not a branch' % (region, site))
            if src.endswith('_acc.s'):
                li = orig_word & 0x03FFFFFC
                li -= 0x04000000 if li & 0x02000000 else 0
                target = (site + li) & 0xFFFFFFFF
                if target != syms['ACC_FUNC']:
                    raise SystemExit('%s: 0x%08X calls 0x%08X, not 0x%08X' % (region, site, target, syms['ACC_FUNC']))
            ops.append(Hook(site, orig_word if dol is not None else None, words, cur, note=note))
            cur += (len(words) * 4 + 15) & ~15
    if cur > STATE:
        raise SystemExit('gc code overflows its window: 0x%X > 0x%X' % (cur, STATE))
    return Feature('gc', 'GameCube controller', region, ops)
