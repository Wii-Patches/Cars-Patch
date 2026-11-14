# Cars: Mater-National -- `addic. r15,r15,-1` once a sample has been copied out of
# the KPAD struct.  If mater_acc.s faked the extension type, put the plain
# remote's back before the next sample compares it with the raw one.  r0, r4 and
# r5 are the copy's and must survive.
    lwz     12, 0x68(31)
    cmplwi  12, 0x100                   # our marker?
    bne     9f
    lbz     12, 0x5C(31)
    cmplwi  12, 2
    bne     9f
    li      12, 0
    stb     12, 0x5C(31)
    stw     12, 0x68(31)
9:
    addic.  15, 15, -1                  # displaced instruction
