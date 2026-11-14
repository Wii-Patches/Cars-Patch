# Cars: Mater-National -- `cmplwi r9,65535` right before the Classic Controller
# patch's button hook (r9 = the Classic Controller buttons, r4 = the extension
# type, r27 = the channel).  That hook turns Classic Controller buttons into the Wii
# Remote bits the game wants (and knows which of its two mappings the current
# mode needs), so hand it the pad's buttons as Classic Controller bits.
    PADREAD 27, 5, 6, 11, 9f
    srwi    3, 5, 16                    # PAD buttons
    CCBITS  9, 3, 6
    li      4, 2                        # type: Classic Controller
9:
    cmplwi  9, 65535                    # displaced instruction
