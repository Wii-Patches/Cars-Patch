# SI poller -- hook at the entry of KPADRead (r3 = channel), which the game
# calls once per channel per frame, before any of the other pad hooks read
# SICnINBUFH.  The displaced instruction (the function's `stwu`) follows.
#
# None of the three games links the SDK's PAD library: si's SIInit probes the
# four ports once at boot and nothing ever enables auto-polling or probes
# again.  Dolphin refreshes the result registers regardless, so the pad hooks
# work there without this; a real Wii needs the poll driven by hand, the way
# PADRead / SIEnablePolling would (same design as the console-tested Barrel
# Blast poller):
#
#   - probe a port whose cached type (Si+0x18 + 4*chan) is not a confirmed
#     standard pad with SIGetType, at most every 0.25 s per port (probing every
#     frame collides with the polling of the other ports on hardware);
#   - copy a NOREP that persists (~10 frames) into the type cache as 8 ("no
#     response"), the only value that makes SIGetType send a fresh probe, so a
#     re-plugged pad is found again;
#   - poll command 0x00400300 into every SICnOUTBUF, then SISR = WR | the
#     error nibbles (write-1-to-clear) to latch it;
#   - SIPOLL enable + copy-on-vblank bits for the confirmed pads only (a port
#     can only be probed while it is not polled), and the same byte in si's
#     shadow copy (Si+4), which the VI retrace writes back to SIPOLL.
#
# At function entry only r3-r5 and LR are live; the rest of the volatile
# registers are free.  STATE: +0 four probe time stamps, +0x10 four NOREP
# counters (bytes).  Garbage there at boot costs at most one delayed probe.

    stwu    1, -0x20(1)
    mflr    0
    stw     0, 0x24(1)
    stw     3, 0x08(1)
    stw     4, 0x0C(1)
    stw     5, 0x10(1)

    lis     6, SIBASE@ha
    addi    6, 6, SIBASE@l              # si state: +4 SIPOLL shadow, +0x18 types
    cmplwi  3, 3
    bgt     done
    slwi    4, 3, 2
    add     7, 6, 4
    lwz     8, 0x18(7)                  # cached type of this port
    andi.   9, 8, 0x80
    bne     probe                       # pending: let SIGetType follow it up
    rlwinm  9, 8, 0, 3, 4
    lis     10, 0x0800
    cmpw    9, 10
    beq     probed                      # confirmed standard pad
probe:
    lis     9, STATE@ha
    addi    9, 9, STATE@l
    mftb    10
    lwzx    11, 9, 4
    subf    11, 11, 10
    lis     12, 0x00E7
    ori     12, 12, 0xBE2C              # 0.25 s of time base
    cmplw   11, 12
    blt     probed
    stwx    10, 9, 4
    lis     12, SIGETTYPE@ha
    addi    12, 12, SIGETTYPE@l
    mtctr   12
    bctrl                               # SIGetType(chan)
probed:
    lis     6, SIBASE@ha
    addi    6, 6, SIBASE@l
    lis     3, 0xCD00
    lwz     4, 0x6438(3)                # SISR

    lis     12, STATE@ha
    addi    12, 12, STATE@l + 0x10      # NOREP counters
    li      8, 0
norep:
    slwi    10, 8, 3
    lis     11, 0x0800                  # port 0's NOREP bit
    srw     11, 11, 10
    lbzx    7, 12, 8
    and.    11, 11, 4
    beq     1f
    cmplwi  7, 40
    bge     2f
    addi    7, 7, 1
    stbx    7, 12, 8
    b       3f
2:  slwi    10, 8, 2
    add     10, 10, 6
    li      9, 8
    stw     9, 0x18(10)                 # type = no response: re-probe it
    b       3f
1:  li      7, 0
    stbx    7, 12, 8
3:  addi    8, 8, 1
    cmpwi   8, 4
    blt     norep

    lis     0, 0x0040
    ori     0, 0, 0x0300
    stw     0, 0x6400(3)                # SICnOUTBUF = poll, analog mode 3
    stw     0, 0x640C(3)
    stw     0, 0x6418(3)
    stw     0, 0x6424(3)
    lis     0, 0x0F0F
    ori     0, 0, 0x0F0F
    and     4, 4, 0
    oris    4, 4, 0x8000                # WR
    stw     4, 0x6438(3)

    li      7, 0                        # enable mask
    li      8, 0
en:
    slwi    10, 8, 2
    add     10, 10, 6
    lwz     10, 0x18(10)
    andi.   11, 10, 0x80
    bne     1f
    rlwinm  11, 10, 0, 3, 4
    lis     12, 0x0800
    cmpw    11, 12
    bne     1f
    li      11, 0x88                    # EN | VBCPY for port 0
    srw     11, 11, 8
    or      7, 7, 11
1:  addi    8, 8, 1
    cmpwi   8, 4
    blt     en

    lwz     0, 0x6430(3)                # SIPOLL
    rlwinm  0, 0, 0, 0, 23
    andi.   4, 0, 0xFF00
    bne     1f
    ori     0, 0, 0x0100                # Y = 1 poll per frame if unset
1:  or      0, 0, 7
    stw     0, 0x6430(3)
    lwz     11, 4(6)                    # si's SIPOLL shadow
    rlwinm  11, 11, 0, 0, 23
    or      11, 11, 7
    stw     11, 4(6)


    # A pad-only channel (no Wii Remote, see gc_probe.s): KPAD has asked WPAD
    # to set the "remote" up and waits for callbacks a missing remote never
    # sends, so drop those waits, then put one blank sample (no buttons, no
    # pointer) into the ring KPAD registered with WPAD and advance the index
    # gc_index.s reports.  The pad hooks fill the sample in as KPAD reads it.
    lwz     3, 0x08(1)
    cmplwi  3, 3
    bgt     done
    PADREAD 3, 9, 8, 10, done
    lis     12, WPCB@ha
    addi    12, 12, WPCB@l
    slwi    11, 3, 2
    lwzx    12, 12, 11
    lwz     0, WPSTAT(12)
    cmpwi   0, -1
    bne     done
    lis     12, KBASE@ha
    addi    12, 12, KBASE@l
    mulli   11, 3, KSTRIDE
    add     12, 12, 11              # this channel's KPAD struct
    li      0, 0
    stw     0, KWAIT1(12)
    stw     0, KWAIT2(12)
    lis     9, STATE@ha
    addi    9, 9, STATE@l + 0x14
    lbzx    10, 9, 3
    addi    10, 10, 1
    cmplwi  10, RINGN
    blt     1f
    li      10, 0
1:  mulli   11, 10, SSIZE
    add     11, 11, 12
    addi    11, 11, RINGOFF - 1     # this sample - 1
    li      8, SSIZE
    mtctr   8
2:  stbu    0, 1(11)
    bdnz    2b
    stbx    10, 9, 3                # publish the index last

done:
    lwz     0, 0x24(1)
    mtlr    0
    lwz     3, 0x08(1)
    lwz     4, 0x0C(1)
    lwz     5, 0x10(1)
    addi    1, 1, 0x20
    .long   ORIG                        # displaced instruction: the stwu
