# Cars Race-O-Rama -- where the game settles the controller type it has recorded for
# a channel (r26 = the channel, r29 = its byte in the game's own table: 1 = a
# Wii Remote on its own, 2 = with a Nunchuk, 3 = with a Classic Controller).  The
# game picks its race controls from that byte, not from the KPAD samples, so a
# GameCube pad on a bare remote's channel is recorded as a Classic Controller, the
# controls the Classic Controller patch makes work.
    lbz     0, 0(29)                    # displaced instruction
    cmplwi  0, 1
    bne     9f
    cmplwi  26, 3
    bgt     9f
    PADREAD 26, 5, 4, 6, 9f
    li      0, 2
    stb     0, 0(29)
9:
