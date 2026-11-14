# Macros shared by the GameCube pad hooks (prepended to each routine).
#
# The SI hardware polls the pads and mirrors each answer into SICnINBUFH / SICnINBUFL
# (0xCD006404 / 0xCD006408 + 12*chan):
#   INBUFH  [31] error  [23] always 1 in a real pad's answer  [29:16] the PAD buttons
#           [15:8] control stick X  [7:0] control stick Y
#   INBUFL  [31:24] C-stick X  [23:16] C-stick Y
# PAD buttons: A 0x100 B 0x200 X 0x400 Y 0x800 Start 0x1000 L 0x40 R 0x20 Z 0x10
#              Up 8 Down 4 Right 2 Left 1

# PADREAD chan, hi, base, tmp, fail: hi <- INBUFH of pad `chan`, base <- its register
# block; branches to `fail` unless a pad answers (clobbers `tmp` and cr0).
#
# Only a port that si's type cache (SIBASE+0x18) marks as a confirmed standard
# pad counts: gc_poll.s stops polling a port once it reports NOREP, and its
# result registers then keep the last answer.
    .macro  PADREAD chan, hi, base, tmp, fail
    slwi    \base, \chan, 2
    addis   \base, \base, SIBASE@ha
    lwz     \hi, SIBASE@l + 0x18(\base)
    andi.   \tmp, \hi, 0x80
    bne     \fail                       # probe pending
    rlwinm  \tmp, \hi, 0, 3, 4
    addis   \tmp, \tmp, -0x0800
    cmpwi   \tmp, 0
    bne     \fail                       # not a standard pad
    mulli   \base, \chan, 12
    .ifdef DEBUG_FEED
    # test builds only: the pad answer comes from RAM at DEBUG_FEED (+4 INBUFH,
    # +8 INBUFL, 12 per port), written by a debugger
    addis   \base, \base, (DEBUG_FEED - 0x6400)@ha
    addi    \base, \base, (DEBUG_FEED - 0x6400)@l
    .else
    addis   \base, \base, 0xCD00
    .endif
    lwz     \hi, 0x6404(\base)
    cmpwi   \hi, 0
    blt     \fail                       # error / no pad
    andis.  \tmp, \hi, 0x0080
    beq     \fail                       # not a pad response
    .endm

# CCBITS out, btn, base: `out` <- the pad's buttons as the raw Classic Controller button
# halfword; btn = the PAD buttons, base = the pad's register block.  Clobbers
# r10-r12 and cr0.
# Classic Controller: Up 1 Left 2 ZR 4 X 8 A 0x10 Y 0x20 B 0x40 ZL 0x80 R 0x200
# + 0x400 Home 0x800 - 0x1000 L 0x2000 Down 0x4000 Right 0x8000.
# The C-stick stands in for ZL (jump) in every direction but down, which is Minus.
    .macro  MAP out, btn, src, dst
    andi.   10, \btn, \src
    beq     1f
    ori     \out, \out, \dst
1:
    .endm

    .macro  CCBITS out, btn, base
    li      \out, 0
    MAP     \out, \btn, 0x0100, 0x0010   # A     -> A
    MAP     \out, \btn, 0x0200, 0x0040   # B     -> B
    MAP     \out, \btn, 0x0400, 0x0008   # X     -> X
    MAP     \out, \btn, 0x0800, 0x0020   # Y     -> Y
    MAP     \out, \btn, 0x1000, 0x0400   # Start -> +
    MAP     \out, \btn, 0x0040, 0x2000   # L     -> L
    MAP     \out, \btn, 0x0020, 0x0200   # R     -> R
    MAP     \out, \btn, 0x0010, 0x0004   # Z     -> ZR
    MAP     \out, \btn, 0x0008, 0x0001   # up
    MAP     \out, \btn, 0x0004, 0x4000   # down
    MAP     \out, \btn, 0x0002, 0x8000   # right
    MAP     \out, \btn, 0x0001, 0x0002   # left
    lwz     12, 0x6408(\base)              # INBUFL
    rlwinm  10, 12, 16, 24, 31             # C-stick Y
    addi    10, 10, -128
    cmpwi   10, -CDEAD
    blt     8f
    srawi   11, 10, 31
    xor     10, 10, 11
    subf    10, 11, 10
    cmpwi   10, CDEAD
    bgt     7f
    rlwinm  10, 12, 8, 24, 31              # C-stick X
    addi    10, 10, -128
    srawi   11, 10, 31
    xor     10, 10, 11
    subf    10, 11, 10
    cmpwi   10, CDEAD
    ble     6f
7:  ori     \out, \out, 0x0080            # ZL
    b       6f
8:  ori     \out, \out, 0x1000            # -
6:
    .endm

# RORCHAN dst, s1, s2 (Race-O-Rama): dst <- the channel of the KPAD struct in r26.  The
# struct array's base is not stored anywhere handy, so it is read back out of
# the `lis` / `addi` pair at the top of KPADRead that loads it (LISW / ADDIW are
# the addresses of those two instructions' immediates); the structs are 0x570 apart.
    .macro  RORCHAN dst, s1, s2
    lis     \s1, LISW@ha
    lhz     \dst, LISW@l(\s1)
    slwi    \dst, \dst, 16
    lis     \s1, ADDIW@ha
    lha     \s2, ADDIW@l(\s1)
    add     \dst, \dst, \s2
    subf    \dst, \dst, 26
    srwi    \dst, \dst, 4
    mulli   \dst, \dst, 754                # x / 0x570 for the four multiples of 0x570
    srwi    \dst, \dst, 16
    .endm

