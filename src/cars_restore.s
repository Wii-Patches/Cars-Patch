# Cars (2006) -- the dispatch on the KPAD extension type once the sample loop is
# done (`lwz r0,92(r29)`, r29 = the channel's KPAD struct, r22 = the channel).  If
# cars_acc.s faked a Classic Controller during the loop, put the real type back so
# the fetch code that compares it with WPADProbe next call, and the rest of this
# one, see the plain remote it really is.  The samples already copied out keep
# the fake.
    lwz     12, 0x5C(29)
    cmplwi  12, 2
    bne     9f
    lwz     12, 0x68(29)
    andi.   11, 12, 0xFF00
    cmplwi  11, 0x0100                  # our marker?
    bne     9f
    clrlwi  12, 12, 24
    stw     12, 0x5C(29)
    li      11, 0
    stw     11, 0x68(29)
9:
    lwz     0, 0x5C(29)                 # displaced instruction
