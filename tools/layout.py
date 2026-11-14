"""Where the hook trampolines live in the injected low-memory section.

0x80001800-0x80003000 is the Wii's boot-time scratch area, which the games never
touch after booting. The first 0x20 bytes are skipped.
"""
CAVE_BASE = 0x80001820
CAVE_LIMIT = 0x80003000

# Classic Controller trampolines window
CC_BASE = 0x80001820
CC_END = 0x80002000

# Cars (2006) widescreen fix trampolines window
FOV_BASE = 0x80002000
FOV_END = 0x80002200

# GameCube controller hook trampolines window
GC_BASE = 0x80002200
GC_END = 0x80003000

WINDOWS = {
    'cc': (CC_BASE, CC_END),
    'gc': (GC_BASE, GC_END),
    'fov': (FOV_BASE, FOV_END),
    'pitstop': (CAVE_BASE, CAVE_BASE),
}
