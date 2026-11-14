# Cars Race-O-Rama -- the `addic. CNT,CNT,-1` once a sample has been copied out of
# the KPAD struct (r26).  If ror_acc.s faked the extension type, put the plain
# remote's back.  The copy's registers must survive.
    lwz     12, 0x68(26)
    cmplwi  12, 0x100                   # our marker?
    bne     9f
    lbz     12, 0x5C(26)
    cmplwi  12, 2
    bne     9f
    li      12, 0
    stb     12, 0x5C(26)
    stw     12, 0x68(26)
9:
    .long   ORIG                        # displaced instruction (addic. CNT,CNT,-1)
