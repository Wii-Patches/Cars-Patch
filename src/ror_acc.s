# Cars Race-O-Rama -- the `bl ACC_FUNC` in the KPAD read loops (r26 = the channel's
# KPAD struct, r3 / r4 = the struct and the sample, which must reach the call
# unchanged).  Same idea as mater_acc.s: while a GameCube pad answers on this
# channel and the remote has no extension, the struct claims extension type 2 for
# this sample, the original runs, then the sticks are written where a Classic
# Controller's would be.  The marker in word 0x68 tells ror_restore.s that the
# type is ours to take back.
    stwu    1, -0x30(1)
    RORCHAN 7, 5, 6
    cmplwi  7, 3
    bgt     call
    PADREAD 7, 9, 8, 10, call
    lbz     0, 0x5C(26)
    cmplwi  0, 0
    bne     call                        # a real extension: leave it alone
    li      0, 0x100                    # marker
    stw     0, 0x68(26)
    li      0, 2
    stb     0, 0x5C(26)
call:
    lis     12, ACC_FUNC@ha
    addi    12, 12, ACC_FUNC@l
    mtctr   12
    bctrl                               # displaced instruction: bl ACC_FUNC
    lbz     0, 0x5C(26)
    cmplwi  0, 2
    bne     out
    RORCHAN 7, 5, 6
    cmplwi  7, 3
    bgt     out
    PADREAD 7, 9, 8, 10, out
    lwz     10, 0x6408(8)
    mr      3, 26
    bl      sticks
out:
    addi    1, 1, 0x30
    b       end
