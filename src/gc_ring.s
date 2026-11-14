# Newer KPAD (Mater-National, Race-O-Rama): KPADRead's "how many samples are
# queued?" load, `lbz r0,RCOUNT(KREG)` (KREG = the channel's KPAD struct, CREG
# = the channel).  KPAD keeps its own ring of 16 0x38-byte WPAD samples (at
# RBASE, next-write index RIDX, count RCOUNT) filled by its WPAD sampling
# callback, which a missing remote never calls.  For a pad-only channel (see
# gc_probe.s) queue two fresh, blank Classic Controller samples every read
# (Race-O-Rama only reads with two or more queued, and the games take the
# sticks from the second-newest one, as City Folk does); the pad hooks fill in
# the buttons and sticks as KPAD reads them.
    cmplwi  CREG, 3
    bgt     9f
    PADREAD CREG, 9, 8, 10, 9f
    lis     12, WPCB@ha
    addi    12, 12, WPCB@l
    slwi    11, CREG, 2
    lwzx    12, 12, 11
    lwz     0, WPSTAT(12)
    cmpwi   0, -1
    bne     9f                      # a real remote: its samples are real
    lbz     10, RIDX(KREG)
    li      7, 2                    # samples to write
1:  clrlwi  10, 10, 28
    mulli   11, 10, 0x38
    add     11, 11, KREG
    addi    11, 11, RBASE - 1
    li      8, 0x38
    mtctr   8
    li      0, 0
2:  stbu    0, 1(11)
    bdnz    2b
    addi    11, 11, -0x37           # back to the sample
    li      0, 2
    stb     0, 0x28(11)             # extension: Classic Controller
    li      0, 8
    stb     0, 0x36(11)             # format: classic + accelerometer + pointer
    addi    10, 10, 1
    addic.  7, 7, -1
    bne     1b
    clrlwi  10, 10, 28
    stb     10, RIDX(KREG)
    li      0, 2
    stb     0, RCOUNT(KREG)
9:
    .long   ORIG                    # displaced instruction
