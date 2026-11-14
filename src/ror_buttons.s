# Cars Race-O-Rama -- `mr r3,r26` right before the call that turns the buttons the
# samples carried into the KPAD struct's (r4 = the extension type, r8 = the
# Classic Controller buttons; r6 / r7 are the others' and stay put).  The
# Classic Controller patch hooks that function to turn Classic Controller buttons
# into the Wii Remote bits the game wants, so hand it the pad's buttons as
# Classic Controller bits.
    RORCHAN 3, 5, 9
    cmplwi  3, 3
    bgt     9f
    PADREAD 3, 5, 9, 11, 9f
    srwi    3, 5, 16                    # PAD buttons
    CCBITS  8, 3, 9
    li      4, 2                        # type: Classic Controller
9:
    mr      3, 26                       # displaced instruction
