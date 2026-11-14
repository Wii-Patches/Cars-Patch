# Cars (2006) -- the merge point every extension type reaches after the buttons
# are read: `lwz r0,0(r3)` (r3 = the channel's KPAD struct, r7 = the previous
# buttons).  Maps the pad onto the Wii Remote bits the game expects, exactly as
# the Classic Controller patch does for a Classic Controller (A -> Z|2, B -> C|1,
# X -> A, Y -> remote 1's extra bit, L/R -> the d-pad, Z -> B, Start -> +, ZL ->
# 0x80 for the jump), and ORs them in before the edge detection runs.
# The channel is the struct's state halfword (0x114): the fetch code sets it to the
# channel number while the remote is connected and makes it negative otherwise
# (the caller has already skipped the negative case).
    lwz     0, 0(3)                     # displaced instruction
    lha     6, 0x114(3)
    cmplwi  6, 3
    bgt     9f
    PADREAD 6, 8, 5, 11, 9f
    srwi    9, 8, 16                    # PAD buttons (r3, the KPAD struct, is still needed)
    li      10, 0
    .macro  MAPB src, dst
    andi.   11, 9, \src
    beq     1f
    ori     10, 10, \dst
1:
    .endm
    MAPB    0x0100, 0x2100              # A
    MAPB    0x0200, 0x4200              # B
    MAPB    0x0400, 0x0800              # X
    MAPB    0x0800, 0x0040              # Y
    MAPB    0x1000, 0x0010              # Start
    MAPB    0x0040, 0x0002              # L
    MAPB    0x0020, 0x0001              # R
    MAPB    0x0010, 0x0400              # Z
    MAPB    0x0008, 0x0008              # d-pad: up
    MAPB    0x0004, 0x0004              #        down
    MAPB    0x0002, 0x0002              #        right
    MAPB    0x0001, 0x0001              #        left
    lwz     12, 0x6408(5)               # INBUFL
    rlwinm  4, 12, 16, 24, 31           # C-stick Y
    addi    4, 4, -128
    cmpwi   4, -CDEAD
    blt     map
    srawi   11, 4, 31
    xor     4, 4, 11
    subf    4, 11, 4
    cmpwi   4, CDEAD
    bgt     jump
    rlwinm  4, 12, 8, 24, 31            # C-stick X
    addi    4, 4, -128
    srawi   11, 4, 31
    xor     4, 4, 11
    subf    4, 11, 4
    cmpwi   4, CDEAD
    ble     done
jump:
    ori     10, 10, 0x0080
    b       done
map:
    ori     10, 10, 0x1000              # -: overworld map / reset to track
done:
    or      0, 0, 10
    stw     0, 0(3)
9:
