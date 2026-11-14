# Cars: Mater-National -- the `bl ACC_FUNC` in the KPAD read loop (r31 = the
# channel's KPAD struct, r19 = the sample, r27 = the channel; the byte at 0x5C is
# the extension type).  Same idea as cars_acc.s: while a GameCube pad answers on
# this channel and the remote has no extension, the struct claims extension type
# 2 (Vague Rant's Classic Controller patch makes a Classic Controller pass as a
# Nunchuk) for this sample, the original runs, then the sticks are written where
# a Classic Controller's would be.  The marker in word 0x68 tells mater_restore.s
# that the type is ours to take back.
    stwu    1, -0x30(1)
    PADREAD 27, 9, 8, 10, call
    lbz     0, 0x5C(31)
    cmplwi  0, 0
    bne     call                        # a real extension: leave it alone
    li      0, 0x100                    # marker
    stw     0, 0x68(31)
    li      0, 2
    stb     0, 0x5C(31)
call:
    lis     12, ACC_FUNC@ha
    addi    12, 12, ACC_FUNC@l
    mtctr   12
    bctrl                               # displaced instruction: bl ACC_FUNC
    lbz     0, 0x5C(31)
    cmplwi  0, 2
    bne     out
    PADREAD 27, 9, 8, 10, out
    lwz     10, 0x6408(8)
    mr      3, 31
    bl      sticks
out:
    addi    1, 1, 0x30
    b       end
