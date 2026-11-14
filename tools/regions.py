"""The retail releases of the Disney-Pixar Cars trilogy on Wii.

Cars (2006), Cars: Mater-National Championship (2007) and Cars Race-O-Rama
(2009) share one input library (the SDK's KPAD) and one engine, so one
patch design covers all of them; only the addresses differ.  All are disc
version 0.

`kpad` is how far the KPAD library sits from the USA release of the same game
(the library is byte-identical apart from where it is linked); the
GameCube-controller hooks are carried over by that offset.
"""
REGIONS = {
    # Cars (2006)
    'RCAE78': dict(game='cars', label='Cars (USA)', short='USA', version=0, kpad=0x000),
    'RCAP78': dict(game='cars', label='Cars (Europe: UK, Australia)', short='Europe', version=0, kpad=0x070),
    'RCAX78': dict(game='cars', label='Cars (Europe: Fr, Nl)', short='Europe', version=0, kpad=0x070),
    'RCAY78': dict(game='cars', label='Cars (Europe: De, It)', short='Europe', version=0, kpad=0x070),
    'RCAJ78': dict(game='cars', label='Cars (Japan)', short='Japan', version=0, kpad=0x760),
    # Cars: Mater-National Championship (2007)
    'RC2E78': dict(game='mater', label='Cars: Mater-National (USA)', short='USA', version=0, kpad=0),
    'RC2P78': dict(game='mater', label='Cars: Mater-National (Europe: UK, Australia)', short='Europe', version=0, kpad=0x130),
    'RC2X78': dict(game='mater', label='Cars: Mater-National (Europe: Fr, Nl)', short='Europe', version=0, kpad=0x130),
    'RC2Y78': dict(game='mater', label='Cars: Mater-National (Europe: De, It)', short='Europe', version=0, kpad=0x130),
    # Cars Race-O-Rama (2009)
    'R6OE78': dict(game='ror', label='Cars Race-O-Rama (USA)', short='USA', version=0, kpad=0),
    'R6OP78': dict(game='ror', label='Cars Race-O-Rama (Europe: UK, Australia)', short='Europe', version=0, kpad=0x050),
    'R6OX78': dict(game='ror', label='Cars Race-O-Rama (Europe: Fr, De)', short='Europe', version=0, kpad=0x050),
}
