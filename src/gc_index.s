# The WPAD call that returns the newest entry of a channel's auto-sampling
# ring (r3 = chan).  For a pad-only channel (see gc_probe.s) return the index
# gc_poll.s last wrote, so KPAD reads the samples written there.
    cmplwi  3, 3
    bgt     9f
    PADREAD 3, 9, 8, 10, 9f
    lis     12, WPCB@ha
    addi    12, 12, WPCB@l
    slwi    11, 3, 2
    lwzx    12, 12, 11
    lwz     0, WPSTAT(12)
    cmpwi   0, -1
    bne     9f
    lis     12, STATE@ha
    addi    12, 12, STATE@l + 0x14
    lbzx    3, 12, 3
    blr
9:
    .long   ORIG
