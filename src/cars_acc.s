# Cars (2006) -- the `bl ACC_FUNC` that turns a Wii Remote sample into acceleration
# data in the KPAD read loop, for a remote with no extension (r3 = the channel's
# KPAD struct, r4 = the sample, r6 = the channel; r5 and r6 must reach the call
# unchanged).
#
# The game steers with the Nunchuk stick, and Vague Rant's Classic Controller
# patch makes a Classic Controller pass as one (extension type 2, stick floats
# at 0x60/0x64, jump on button 0x80), so the GameCube pad does the same: while a
# pad answers on this channel the KPAD struct claims extension type 2 for the rest
# of this call, the original runs (so the Classic Controller patch's jump and
# pointer code see it), then the sticks are written where the Classic Controller's
# would be.  The real type is parked in word 0x68, unused for a plain remote, and
# put back by cars_restore.s before the call ends.
    stwu    1, -0x30(1)
    stw     3, 0x08(1)
    PADREAD 6, 9, 8, 10, call
    lwz     0, 0x5C(3)
    cmplwi  0, 2
    beq     call                        # already ours (second sample of this call)
    cmplwi  0, 0
    beq     fake
    cmplwi  0, 251
    blt     call                        # a real Nunchuk / Classic Controller: leave it alone
fake:
    ori     0, 0, 0x100                 # marker | real type
    stw     0, 0x68(3)
    li      0, 2
    stw     0, 0x5C(3)
call:
    lis     12, ACC_FUNC@ha
    addi    12, 12, ACC_FUNC@l
    mtctr   12
    bctrl                               # displaced instruction: bl ACC_FUNC
    lwz     3, 0x08(1)
    lwz     0, 0x5C(3)
    cmplwi  0, 2
    bne     out
    lha     6, 0x114(3)                 # the channel (see cars_buttons.s)
    PADREAD 6, 9, 8, 10, out
    lwz     10, 0x6408(8)
    bl      sticks
out:
    addi    1, 1, 0x30
    b       end
