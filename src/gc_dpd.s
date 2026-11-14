# WPADIsDpdEnabled(chan) entry.  KPAD re-runs its remote setup every frame
# while the pointer (DPD) it wants on (KPAD struct +KDPD) and what WPAD
# reports disagree; a pad-only channel (see gc_probe.s) has no camera to turn
# on, so report exactly what KPAD wants.
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
    lis     12, KBASE@ha
    addi    12, 12, KBASE@l
    mulli   11, 3, KSTRIDE
    add     12, 12, 11
    lwz     3, KDPD(12)
    blr
9:
    .long   ORIG
