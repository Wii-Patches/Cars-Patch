# WPADProbe(chan, &type) entry.  A channel with no Wii Remote (WPAD status -1)
# but a GameCube pad on the matching port answers "connected" with type
# PROBETYPE (Cars: 0, a bare Wii Remote, which the pad hooks turn into a Classic
# Controller; Mater-National / Race-O-Rama: 2, a Classic Controller, whose
# samples gc_ring.s writes), so KPAD and the game take the pad's channel as a
# player.
# Everything else falls through to the real WPADProbe.
    cmplwi  3, 3
    bgt     9f
    PADREAD 3, 9, 8, 10, 9f
    lis     12, WPCB@ha
    addi    12, 12, WPCB@l
    slwi    11, 3, 2
    lwzx    12, 12, 11              # this channel's WPAD control block
    lwz     0, WPSTAT(12)
    cmpwi   0, -1
    bne     9f                      # a real remote (or one connecting)
    cmplwi  4, 0
    beq     1f
    li      0, PROBETYPE
    stw     0, 0(4)
1:  li      3, 0
    blr
9:
    .long   ORIG                    # displaced instruction (stwu)
