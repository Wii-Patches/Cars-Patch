# Helpers appended after a hook's own code (the hook ends with `b end`; `end:`
# follows them).
#
# sticks:  r3 = a KPAD struct, r9 = INBUFH, r10 = INBUFL -> the control stick as
#          floats at 0x60 / 0x64 and the C-stick at 0x74 / 0x78 (right and up are
#          positive), where a Classic Controller's would be once the Classic
#          Controller patch has moved its left stick next to the Nunchuk's.
#          Needs the caller's 0x30-byte frame; clobbers r0, r4, r5, r11, r12, f0-f2.
sticks:
    mflr    5
    rlwinm  4, 9, 24, 24, 31            # stick X (u8)
    addi    4, 4, -128
    bl      axis
    bl      tofloat
    stfs    0, 0x60(3)
    rlwinm  4, 9, 0, 24, 31             # stick Y
    addi    4, 4, -128
    bl      axis
    bl      tofloat
    stfs    0, 0x64(3)
    rlwinm  4, 10, 8, 24, 31            # C-stick X
    addi    4, 4, -128
    bl      axis
    bl      tofloat
    stfs    0, 0x74(3)
    rlwinm  4, 10, 16, 24, 31           # C-stick Y
    addi    4, 4, -128
    bl      axis
    bl      tofloat
    stfs    0, 0x78(3)
    mtlr    5
    blr

# axis:    r4 = signed stick offset (stick byte - 128) -> r4 = normalised value * 256,
#          clamped to +/-256.  Dead zone DEAD, full scale at DEAD + 80
#          (KMUL = 256 * 64 / 80, rounded up).  Clobbers r11, r12.
axis:
    srawi   11, 4, 31                   # -1 if negative
    xor     12, 4, 11
    subf    12, 11, 12                  # |v|
    cmpwi   12, DEAD
    ble     zero
    addi    12, 12, -DEAD
    mulli   12, 12, KMUL
    srawi   12, 12, 6
    cmpwi   12, 256
    ble     1f
    li      12, 256
1:  xor     12, 12, 11
    subf    4, 11, 12                   # signed again
    blr
zero:
    li      4, 0
    blr

# tofloat: r4 = int in 1/256ths -> f0 = r4 / 256.0.  Clobbers r0, f1, f2 and the
#          0x18..0x2c(r1) scratch words of the caller's frame.
tofloat:
    lis     0, 0x4330
    stw     0, 0x18(1)
    xoris   4, 4, 0x8000
    stw     4, 0x1c(1)
    lfd     0, 0x18(1)
    stw     0, 0x20(1)
    lis     0, 0x8000
    stw     0, 0x24(1)
    lfd     1, 0x20(1)
    fsub    0, 0, 1
    lis     0, 0x3b80
    stw     0, 0x28(1)
    lfs     2, 0x28(1)
    fmul    0, 0, 2
    blr
